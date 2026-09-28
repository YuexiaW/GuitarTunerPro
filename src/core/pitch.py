"""音高：吉他标准调弦表 + 音分换算 + 一帧 PCM16 → 基频

检测器两条路（与采集路径对应）：
  - 桌面：audioflux PitchYIN（精度 ≤0.3 音分）
  - 安卓/iOS：audioflux 没有对应二进制，回退纯 numpy 自相关 AcfDetector（≤0.9 音分）
"""

import math
import os

import numpy as np

from core.constants import A4_STANDARD, SIG_GATE
from core.tuner_engine import HAS_AUDIOFLUX, AcfDetector

if HAS_AUDIOFLUX:
    import audioflux as af
else:
    af = None

# 吉他标准调音：弦名 → 基频 (Hz)（顺序 = 从最粗的第 6 弦到最细的第 1 弦）
GUITAR_STRINGS = {
    "E2": 82.41,
    "A2": 110.00,
    "D3": 146.83,
    "G3": 196.00,
    "B3": 246.94,
    "E4": 329.63,
}

# 有效基频范围：吉他基频 80~330Hz，放宽到 60~500Hz 容纳泛音与弦未上紧的情况
FREQ_MIN = 60.0
FREQ_MAX = 500.0
# 自相关路径的置信度门限
ACF_MIN_CONFIDENCE = 0.4


def cents_from(freq: float, ref: float) -> float:
    """相对参考频率的音分偏差（正 = 偏高）"""
    return 1200.0 * math.log2(freq / ref)


def string_freqs(a4: float = A4_STANDARD) -> dict[str, float]:
    """按参考音缩放的标准调弦（A4=432 时所有目标频率 ×432/440）"""
    k = a4 / A4_STANDARD
    return {note: freq * k for note, freq in GUITAR_STRINGS.items()}


def nearest_string(freq: float, locked: str | None = None,
                   a4: float = A4_STANDARD) -> tuple[str, float, float]:
    """返回 (弦名, 该弦目标频率, 音分偏差)

    锁定了某根弦就相对它算偏差（允许超出 ±50 音分，显示时再截断），
    否则取频率上最接近的那根弦。目标频率按参考音 A4 缩放。
    """
    targets = string_freqs(a4)

    if locked:
        target = targets[locked]
        return locked, target, cents_from(freq, target)

    best_note, target_freq, min_diff = "?", 0.0, float("inf")
    for note, ref_freq in targets.items():
        diff = abs(freq - ref_freq)
        if diff < min_diff:
            min_diff = diff
            best_note = note
            target_freq = ref_freq
    return best_note, target_freq, cents_from(freq, target_freq)


def lowpass(x, taps: int = 25, passes: int = 2):
    """吉他频段前置低通(~320Hz)：两级滑动平均 FIR

    PitchYIN 对「弱基频 + 高频噪声」的信号会整段返回 0.0(判为无声)，
    滤掉几百 Hz 以上的噪声后同一段信号就能稳定测出基频；
    顺带压掉强二次谐波，避免把 220Hz 当成 110Hz。
    """
    kernel = np.ones(taps, dtype=np.float64) / taps
    y = x.astype(np.float64)
    for _ in range(passes):
        y = np.convolve(y, kernel, mode="same")
    return y


class PitchAnalyzer:
    """一帧 PCM16 → 基频(Hz)"""

    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate
        self.detector = (
            af.PitchYIN(samplate=sample_rate) if HAS_AUDIOFLUX else AcfDetector(sample_rate)
        )

    def analyze(self, pcm: bytes) -> tuple[float, float | None]:
        """返回 (rms, freq)；freq 为 None 表示这一帧判为无声/无效"""
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(audio ** 2)))

        if HAS_AUDIOFLUX:
            # 噪声门限：安静房间的底噪会让 PitchYIN 偶尔吐出 200~330Hz 的杂散值
            if rms < SIG_GATE:
                if os.environ.get("TUNER_DEBUG"):
                    print(f"[dbg] rms={rms:.4f} 低于门限，跳过", flush=True)
                return rms, None
            # 前置低通：PitchYIN 对含高频噪声的弱基频信号会返回 0.0(判为无声)
            filtered = lowpass(audio)
            fre_arr, _, _ = self.detector.pitch(
                np.ascontiguousarray(filtered.astype(np.float32))
            )
            valid = [float(f) for f in fre_arr if FREQ_MIN < float(f) < FREQ_MAX]
        else:
            # 回退路径：门限与低通在 AcfDetector 内部完成
            freq, conf = self.detector.detect(audio)
            valid = [freq] if freq > 0 and conf >= ACF_MIN_CONFIDENCE else []

        if os.environ.get("TUNER_DEBUG"):
            print(f"[dbg] rms={rms:.4f} freqs={valid[:5]}", flush=True)

        if not valid:
            return rms, None
        return rms, float(np.median(valid))
