"""models 层：可观察状态（模块级单例）—— UI 读它、services 写它

state.py     运行时状态（音符/音分、是否在采集、锁定弦、主题名）
settings.py  持久化偏好（参考音 A4），落 JSON 文件

状态类不写 `__init__`、不用 `@dataclass`/`@property`（见 models/state.py 顶部说明）。
"""

from models.settings import SettingsState, settings_state
from models.state import (
    PitchState,
    ThemeState,
    TunerState,
    pitch_state,
    theme_state,
    tuner_state,
)

__all__ = [
    "PitchState",
    "SettingsState",
    "ThemeState",
    "TunerState",
    "pitch_state",
    "settings_state",
    "theme_state",
    "tuner_state",
]
