"""
tuner_engine.py
音高检测：优先用 audioFlux 0.1.9 的 PitchYIN；安卓/iOS 没有 audioFlux 二进制，
自动回退到纯 numpy 自相关实现（实测对真实麦克风音频可用）。
"""

import numpy as np

try:
    import audioflux as af
    HAS_AUDIOFLUX = True
except ImportError:  # 安卓/iOS 打包不含 audioflux（无对应平台二进制）
    af = None
    HAS_AUDIOFLUX = False

# ─────────────────────────────────────────────
# 吉他标准调音 (E2 A2 D3 G3 B3 E4)
# ─────────────────────────────────────────────
GUITAR_STRINGS = {
    "E2": {"freq": 82.41,  "string": 6, "color": "#FF4444"},
    "A2": {"freq": 110.00, "string": 5, "color": "#FF8800"},
    "D3": {"freq": 146.83, "string": 4, "color": "#FFCC00"},
    "G3": {"freq": 196.00, "string": 3, "color": "#44CC44"},
    "B3": {"freq": 246.94, "string": 2, "color": "#4488FF"},
    "E4": {"freq": 329.63, "string": 1, "color": "#AA44FF"},
}

SAMPLE_RATE = 44100
CENTS_TOLERANCE = 10  # 音分容差，±10 cents 视为准确


def freq_to_cents(detected: float, target: float) -> float:
    """将频率差转换为音分 (cents)"""
    if detected <= 0 or target <= 0:
        return 0.0
    return 1200.0 * np.log2(detected / target)


def find_nearest_string(freq: float) -> tuple[str, dict, float]:
    """找到最接近检测频率的吉他弦"""
    best_name = None
    best_info = None
    best_cents = float("inf")

    for name, info in GUITAR_STRINGS.items():
        cents = abs(freq_to_cents(freq, info["freq"]))
        if cents < best_cents:
            best_cents = cents
            best_name = name
            best_info = info

    raw_cents = freq_to_cents(freq, best_info["freq"]) if best_info else 0.0
    return best_name, best_info, raw_cents


# ─────────────────────────────────────────────
# 纯 numpy 回退实现（audioFlux 不可用的平台：安卓 / iOS）
# ─────────────────────────────────────────────
SIG_GATE = 0.005      # 噪声门限：低于此 rms 的帧不做检测，避免底噪误报音符
CONF_GATE = 0.3       # 自相关峰值门限


def lowpass(x, taps: int = 25, passes: int = 2) -> np.ndarray:
    """吉他频段前置低通（两级滑动平均 FIR，约 320Hz @16kHz）。

    含高频噪声的信号会让 YIN/自相关失败或把二次谐波当基频，先滤掉再用。
    """
    kernel = np.ones(taps, dtype=np.float64) / taps
    y = np.asarray(x, dtype=np.float64)
    for _ in range(passes):
        y = np.convolve(y, kernel, mode="same")
    return y


class AcfDetector:
    """自相关 + 抛物线插值测基频（无 audioFlux 时使用）。

    抛物线顶点：freq_peak = pk - 0.5*(a-g)/(2b-a-g)，符号写反会系统性偏差。
    """

    def __init__(self, sample_rate: int, low_freq: float = 60.0,
                 high_freq: float = 500.0, conf_gate: float = CONF_GATE):
        self.sample_rate = sample_rate
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.conf_gate = conf_gate

    def detect(self, frame) -> tuple[float, float]:
        """返回 (频率 Hz, 置信度)；无有效基频时返回 (0.0, 0.0)。"""
        x = np.asarray(frame, dtype=np.float64)
        n = x.size
        if n < 64:
            return 0.0, 0.0
        if float(np.sqrt(np.mean(x ** 2))) < SIG_GATE:
            return 0.0, 0.0

        x = lowpass(x)
        x = x - float(x.mean())

        acf = np.correlate(x, x, mode="full")[n - 1:]
        if acf[0] <= 0:
            return 0.0, 0.0
        acf = acf / acf[0]

        lag_lo = max(2, int(self.sample_rate / self.high_freq))
        lag_hi = min(n - 2, int(self.sample_rate / self.low_freq))
        if lag_hi <= lag_lo + 1:
            return 0.0, 0.0

        pk = int(np.argmax(acf[lag_lo:lag_hi + 1])) + lag_lo
        conf = float(acf[pk])
        if conf < self.conf_gate or pk <= 0 or pk + 1 >= n:
            return 0.0, 0.0

        a, b, g = float(acf[pk - 1]), float(acf[pk]), float(acf[pk + 1])
        denom = 2 * b - a - g
        refined = pk - 0.5 * (a - g) / denom if abs(denom) > 1e-12 else float(pk)
        freq = self.sample_rate / refined
        if not (self.low_freq <= freq <= self.high_freq):
            return 0.0, 0.0
        return float(freq), conf


class GuitarTunerEngine:
    """
    使用 audioFlux PitchYIN 检测吉他音高
    支持 PCM16 字节流输入
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._buffer = np.array([], dtype=np.float32)

        if HAS_AUDIOFLUX:
            # audioflux 0.1.9 没有通用 af.Pitch，只有 PitchYIN/PitchSTFT 等具体实现；
            # auto_length 必须 >= 4096，否则 pitch() 直接返回空数组
            self._pitch_obj = af.PitchYIN(
                samplate=sample_rate,
                low_fre=60.0,      # 低于 E2(82Hz) 的安全下限
                high_fre=400.0,    # 高于 E4(330Hz) 的安全上限
                slide_length=512,
                auto_length=4096,
            )
            self._acf = None
            self._frame_size = self._pitch_obj.auto_length  # 4096
        else:
            # 回退：自相关帧长取 ~190ms（PitchYIN 类算法低于 4096 采样无输出）
            self._pitch_obj = None
            self._acf = AcfDetector(sample_rate)
            self._frame_size = max(4096, int(sample_rate * 0.19))

    def feed_pcm16(self, raw_bytes: bytes) -> dict | None:
        """
        输入 PCM16LE 字节流，返回调音结果字典
        返回 None 表示数据不足，继续缓冲
        """
        # PCM16 → float32 归一化
        pcm = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        self._buffer = np.concatenate([self._buffer, pcm])

        if len(self._buffer) < self._frame_size:
            return None  # 数据不足

        # 取最新一帧
        frame = self._buffer[-self._frame_size:]
        self._buffer = self._buffer[-self._frame_size:]  # 滑动保留

        # 检测音高
        if self._acf is not None:
            detected_freq, confidence = self._acf.detect(frame)
            if detected_freq <= 0 or confidence < 0.4:
                return {"status": "silent", "freq": 0.0}
        else:
            try:
                # PitchYIN.pitch 返回 (频率数组, 周期误差, 周期误差)；
                # 检测不到时频率为 0（安静房间的底噪会出现 0.2 左右的周期误差）
                fre_arr, err_a, err_b = self._pitch_obj.pitch(frame)
            except Exception:
                return None

            valid_mask = fre_arr > 0
            if not np.any(valid_mask):
                return {"status": "silent", "freq": 0.0}

            detected_freq = float(np.median(fre_arr[valid_mask]))
            # 周期误差越小置信度越高（注意：该值在好信号上≈0，不能写成 "> 0.4 才算有效"）
            err = float(np.mean(np.maximum(np.abs(err_a), np.abs(err_b))[valid_mask]))
            confidence = float(min(1.0, max(0.0, 1.0 - err)))

        # 匹配最近琴弦
        string_name, string_info, cents = find_nearest_string(detected_freq)

        status = (
            "in_tune" if abs(cents) <= CENTS_TOLERANCE
            else "too_low" if cents < 0
            else "too_high"
        )

        return {
            "status": status,
            "freq": round(detected_freq, 2),
            "string_name": string_name,
            "string_info": string_info,
            "cents": round(cents, 1),
            "confidence": round(confidence, 3),
        }