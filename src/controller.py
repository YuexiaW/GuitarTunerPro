"""编排层：采集 → 检测 → 状态（UI 只读状态，不认识采集/检测细节）

对应参考骨架里的 services + core：main() 里 attach(page) 一次，
之后组件通过 start_capture / stop_capture / toggle_lock 触发动作。
"""

import time

import flet as ft

from audio import PERMISSION_DENIED, RecorderService
from constants import SAMPLE_RATE, UPDATE_INTERVAL
from pitch import GUITAR_STRINGS, PitchAnalyzer, nearest_string
from state import pitch_state, tuner_state
from theme import IN_TUNE_CENTS

_analyzer: PitchAnalyzer | None = None
_recorder: RecorderService | None = None
_message = None                      # 由 attach 注入的提示回调（SnackBar）


def attach(page: ft.Page, on_message):
    """在 main() 里调用一次：建立检测器与采集服务"""
    global _analyzer, _recorder, _message
    _analyzer = PitchAnalyzer(SAMPLE_RATE)
    _message = on_message
    _recorder = RecorderService(page, tuner_state, on_frame=_on_frame,
                               on_status=set_status,
                               is_mobile=page.platform.is_mobile())


# ---------- 对外动作（组件直接当回调传） ----------
def toggle_lock(note: str):
    """点弦 = 锁定该弦（偏差相对它算）；再点一次 = 取消锁定回到自动识别"""
    tuner_state.locked = None if tuner_state.locked == note else note


async def start_capture():
    """开始采集：失败原因直接写状态栏（安卓看不到 stdout，必须上屏）"""
    if tuner_state.running:
        return
    result = await _recorder.start()
    if result == PERMISSION_DENIED:
        _message("需要麦克风权限才能调音。")
        return
    if result:
        set_status(f"❌ 无法打开麦克风！{result}", "bad")
        return
    set_status("🎤 正在监听音频...")


async def stop_capture():
    await _recorder.stop()
    tuner_state.detected = None
    pitch_state.reset("⏸️ 已停止监听")


def set_status(text: str, level: str = "dim"):
    pitch_state.status_text = text
    pitch_state.status_level = level


# ---------- 内部：一帧 PCM16 → 状态 ----------
def _on_frame(frame: bytes):
    _rms, freq = _analyzer.analyze(frame)
    if freq is None:                 # 静音/无效帧：界面保持上一屏不动
        return

    # 渲染节流：状态赋值 = 重渲染，所以按 UPDATE_INTERVAL 推，别每帧都推
    now = time.time()
    if now - tuner_state.last_update < UPDATE_INTERVAL:
        return
    tuner_state.last_update = now

    note, _target, cents = nearest_string(freq, tuner_state.locked)
    in_tune = abs(cents) <= IN_TUNE_CENTS
    if not tuner_state.locked:       # 弦条跟随自动识别（锁定时不覆盖）
        tuner_state.detected = note
    pitch_state.show(note, freq, cents, in_tune,
                     pitch_status_text(cents, in_tune),
                     "accent" if in_tune else "bad")


def pitch_status_text(cents: float, in_tune: bool) -> str:
    """顶栏状态文案"""
    if in_tune:
        return "✅ 音准完美！"
    arrow = "⬆️ 偏高" if cents > IN_TUNE_CENTS else "⬇️ 偏低"
    return f"{arrow} {abs(cents):.0f} 音分"


__all__ = ["attach", "start_capture", "stop_capture", "toggle_lock", "set_status",
           "pitch_status_text"]
