"""models.state —— 可观察状态（模块级单例）

写法（Flet 的 Observable 实现 + 项目约定）：
  - 类级字段 + 默认值，**不写 `__init__`**、**不用 `@dataclass`**、**不用 `@property`**；
  - 变化靠**赋值**触发通知（`self.note = ...`）；list/dict/bytearray 的原地改动不通知；
  - 派生值写成方法（`has_pitch()` / `active_string()`），只在渲染时调用；
  - 组件要收到变化 = 把实例**作为参数**传进去（订阅按参数建立），模块级 import 读不算；
  - 本层不认识 flet 界面：这里只存裸状态，配色查表在 app.theme.palette_of(name)，
    主题**切换**逻辑在 components/app_bar.py。
"""

import flet as ft

from core.constants import DEFAULT_THEME


@ft.observable
class ThemeState:
    """当前主题名（纯数据：取色 app.theme.palette_of，切换在 components/app_bar.py）"""

    name: str = DEFAULT_THEME           # "dark" / "light"


@ft.observable
class TunerState:
    """调音过程状态（锁定弦 / 识别弦 / 是否采集 / 采集缓冲）"""

    locked: str | None = None           # 手动锁定的弦（None = 自动识别）
    detected: str | None = None         # 当前自动识别到的弦
    running: bool = False               # 是否正在采集
    stream_bytes: int = 0               # 流式收到的字节数（判断 on_stream 是否真在推数据）
    last_update: float = 0.0            # 上次推给 UI 的时间（渲染节流用）
    buffer: bytearray = bytearray()     # 未凑满一帧的剩余 PCM16（原地改，不参与渲染）

    def active_string(self):
        """当前高亮的弦：手动锁定优先，其次自动识别"""
        return self.locked or self.detected

    def reset_capture(self):
        self.buffer.clear()
        self.stream_bytes = 0
        self.last_update = 0.0


@ft.observable
class PitchState:
    """一次检测结果（调音页读它：音符 / 频率 / 音分 / 是否准了）"""

    note: str = "?"
    freq: float = 0.0
    cents: float = 0.0
    in_tune: bool = False

    def has_pitch(self) -> bool:
        return self.note != "?"

    def show(self, note: str, freq: float, cents: float, in_tune: bool):
        self.note = note
        self.freq = freq
        self.cents = cents
        self.in_tune = in_tune

    def reset(self):
        self.note = "?"
        self.freq = 0.0
        self.cents = 0.0
        self.in_tune = False


theme_state = ThemeState()
tuner_state = TunerState()
pitch_state = PitchState()
