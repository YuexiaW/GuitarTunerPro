"""services/tuner.py —— 调音编排：采集 → 检测 → 状态（UI 只读状态，不认识采集/检测细节）

main() 里 attach(page) 一次；之后组件把 start_capture / stop_capture / toggle_lock 当回调传。
检测算法在 pitch.py（纯 Python、不认识 flet），采集在 services/recorder.py。
"""

import time

import flet as ft

from core.constants import IN_TUNE_CENTS, ROUTE_TUNER, SAMPLE_RATE, UPDATE_INTERVAL
from core.pitch import PitchAnalyzer, nearest_string
from models.settings import settings_state
from models.state import pitch_state, tuner_state
from services.recorder import PERMISSION_DENIED, RecorderService

_analyzer: PitchAnalyzer | None = None
_recorder: RecorderService | None = None
_message = None                      # 由 attach 注入的提示回调（SnackBar）


def attach(page: ft.Page, on_message):
    """在 main() 里调用一次：建立检测器与采集服务"""
    global _analyzer, _recorder, _message
    _analyzer = PitchAnalyzer(SAMPLE_RATE)
    _message = on_message
    _recorder = RecorderService(page, tuner_state, on_frame=_on_frame,
                                on_message=_message,
                                is_mobile=page.platform.is_mobile())


# ---------- 对外动作（组件直接当回调传） ----------
def toggle_lock(note: str):
    """点弦 = 锁定该弦（偏差相对它算）；再点一次 = 取消锁定回到自动识别"""
    tuner_state.locked = None if tuner_state.locked == note else note


async def start_capture():
    """开始采集：失败原因弹 SnackBar 上屏（安卓看不到 stdout，必须让用户看见）"""
    if tuner_state.running:
        return
    result = await _recorder.start()
    if result == PERMISSION_DENIED:
        _message("需要麦克风权限才能调音。")
        return
    if result:
        _message(f"❌ 无法打开麦克风！{result}")
        return
    _message("🎤 正在监听音频...")
    settings_state.add_session()     # 计数：这次开始调音记一笔（「我的」页数据行）


async def stop_capture():
    await _recorder.stop()
    tuner_state.detected = None
    pitch_state.reset()


def go(page, route: str, current: str | None = None):
    """统一切页：离开调音页先停采集（导航条与「我的」页快捷入口共用这一处）

    直接 page.navigate 会绕过停采集，麦克风就留在后台跑了。
    """
    if route != ROUTE_TUNER and tuner_state.running:
        page.run_task(stop_capture)
    if route != current:
        page.navigate(route)


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

    note, _target, cents = nearest_string(freq, tuner_state.locked, settings_state.a4)
    if not tuner_state.locked:       # 弦条跟随自动识别（锁定时不覆盖）
        tuner_state.detected = note
    in_tune = abs(cents) <= IN_TUNE_CENTS
    was_in_tune = pitch_state.in_tune
    pitch_state.show(note, freq, cents, in_tune)
    if in_tune and not was_in_tune:  # 跨进绿区那一下记一次「调准」（计数用在「我的」页）
        settings_state.add_in_tune_hit()


__all__ = ["attach", "go", "start_capture", "stop_capture", "toggle_lock"]
