"""
tuner_engine.py
使用 audioFlux 0.1.9 的 PitchYIN 算法进行吉他音高检测
"""

import numpy as np
import audioflux as af
from audioflux.type import PitchType

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


class GuitarTunerEngine:
    """
    使用 audioFlux PitchYIN 检测吉他音高
    支持 PCM16 字节流输入
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        # PitchYIN：基于时域差分自相关，适合吉他等乐器
        self._pitch_obj = af.Pitch(
            pitch_type=PitchType.YIN,
            samplate=sample_rate,
            low_fre=60.0,    # 低于 E2(82Hz) 的安全下限
            high_fre=400.0,  # 高于 E4(330Hz) 的安全上限
            slide_length=512,
        )
        self._buffer = np.array([], dtype=np.float32)
        self._frame_size = self._pitch_obj.auto_length  # 自动最优帧长

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
        try:
            fre_arr, val_arr, _ = self._pitch_obj.pitch(frame)
        except Exception:
            return None

        # 过滤无效帧（频率为 0 或置信度极低）
        valid_mask = (fre_arr > 0) & (val_arr > 0.4)
        if not np.any(valid_mask):
            return {"status": "silent", "freq": 0.0}

        detected_freq = float(np.median(fre_arr[valid_mask]))

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
            "confidence": round(float(np.mean(val_arr[valid_mask])), 3),
        }