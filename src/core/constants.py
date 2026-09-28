""""core 层：纯 Python（不认识 flet）—— 运行时参数、检测算法、自相关引擎

运行时参数（采集与检测共用，改参数只改这里）
"""

import os
import tempfile

# --- 应用信息 ---
APP_TITLE = "🎸 吉他调音器"
APP_NAME = "吉他调音器"
APP_VERSION = "0.1.2"                     # 跟 tag/pyproject 对齐
APP_REPO = "https://github.com/YuexiaW/GuitarTunerPro"
HELP_TEXT = ("拨动单根弦、靠近麦克风；指针停在中间绿区（±5 音分）就是准了。"
             "点内容区那排弦名可锁定该弦。")

# --- 调音判定 ---
IN_TUNE_CENTS = 5.0      # 「准了」绿区 ±5 音分（检测与偏差条共用）
DEFAULT_THEME = "dark"   # 启动主题："dark" / "light"

# --- 参考音（A4）：影响所有弦的目标频率 ---
A4_STANDARD = 440.0
A4_OPTIONS = (440.0, 442.0, 435.0, 432.0, 415.0)

# --- 个人资料（「我的」页头部）---
DEFAULT_NICKNAME = "吉他手"
NICKNAME_MAX = 12
DEFAULT_AVATAR = "🎸"
AVATAR_CHOICES = ("🎸", "🎵", "🎤", "🎧", "🥁", "🎹")

# --- 设置文件 ---
SETTINGS_FILE = "settings.json"

# --- 采集参数 ---
SAMPLE_RATE = 16000      # 16kHz 足以覆盖吉他最高弦 E4 (329Hz) 及其泛音，且计算延迟更低
CHANNELS = 1
BYTES_PER_SAMPLE = 2
FRAME_SIZE = 4096        # audioflux PitchYIN 至少需要 4096 个采样才出结果(2048 返回空数组)
FRAME_BYTES = FRAME_SIZE * BYTES_PER_SAMPLE
POLL_INTERVAL = 0.05     # 桌面端轮询间隔（从 WAV 文件增量读取）
UPDATE_INTERVAL = 0.1    # UI 刷新节流：每 100ms 更新一次界面，防止卡顿
SIG_GATE = 0.005         # 噪声门限(原始信号 rms)：低于此值不做检测，避免底噪误报音符

# 录音临时文件：flet_audio_recorder 写 WAV，我们从文件尾增量读取 PCM16
CAPTURE_FILE = os.path.join(tempfile.gettempdir(), "guitar_tuner_capture.wav")
