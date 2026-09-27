"""services 层：编排（采集 → 检测 → 状态推送）

页面只渲染、只调这里的函数；采集与检测的细节不外泄给 UI（UI 只读 state）。
    recorder.py  麦克风采集：桌面「写 WAV + 增量轮询」/ 移动 on_stream，含启动诊断与看门狗
    tuner.py     调音编排：attach / start_capture / stop_capture / toggle_lock / set_status
"""

from services.recorder import PERMISSION_DENIED, RecorderService
from services.tuner import (
    attach,
    pitch_status_text,
    set_status,
    start_capture,
    stop_capture,
    toggle_lock,
)

__all__ = [
    "PERMISSION_DENIED",
    "RecorderService",
    "attach",
    "pitch_status_text",
    "set_status",
    "start_capture",
    "stop_capture",
    "toggle_lock",
]
