"""调音页：六弦胶囊 → 大音符/频率 → 音分偏差条 → 提示

声明式：只读 pitch_state / tuner_state，采集那边一改状态，这里自己重渲染。
（订阅靠参数：PitchPage 是零参入口，把 observable 传给内层 _Tuner。）

版式是**平铺**的：内容直接落在渐变底上，靠留白和字号分层，不套透明卡片
—— 毛玻璃只属于底部导航条那一层（见 app/theme.py 的 glass 说明）。
"""

import flet as ft

from app.theme import ACCENT, BAD, content_width, palette_of
from components.meter import cents_meter
from components.string_chips import string_chips
from core.pitch import string_freqs
from models.settings import SettingsState, settings_state
from models.state import PitchState, ThemeState, TunerState, pitch_state, theme_state, tuner_state
from services.tuner import toggle_lock

HINT_TEXT = "拨动单根弦并靠近麦克风 · 点上面那排弦名可锁定该弦 · 指针停在中间绿区即准"


@ft.component
def PitchPage():
    """零参入口（Router 用）"""
    return _Tuner(theme_state, pitch_state, tuner_state, settings_state)


@ft.component
def _Tuner(theme: ThemeState, pitch: PitchState, tuner: TunerState, settings: SettingsState):
    p = palette_of(theme.name)              # 读参数里的 observable = 订阅
    card_w = content_width(ft.context.page)

    has_pitch = pitch.has_pitch()
    color = ACCENT if pitch.in_tune else BAD
    note_color = color if has_pitch else p["text_faint"]
    cents_color = color if has_pitch else p["text_dim"]

    note = ft.Column(
        spacing=2,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(pitch.note, size=96, weight=ft.FontWeight.BOLD, color=note_color),
            ft.Text(f"{pitch.freq:.1f} Hz" if has_pitch else "-- Hz",
                    size=20, color=p["text_dim"]),
        ],
    )
    meter = ft.Column(
        spacing=12,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            cents_meter(p, cents=pitch.cents, color=color),
            ft.Row(
                controls=[
                    ft.Text("-50", size=10, color=p["text_faint"]),
                    ft.Text(f"{pitch.cents:+.1f} cents" if has_pitch else "0.0 cents",
                            size=16, weight=ft.FontWeight.W_500, color=cents_color),
                    ft.Text("+50", size=10, color=p["text_faint"]),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
    )

    return ft.Column(
        spacing=28,
        tight=True,
        width=card_w,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            string_chips(p, string_freqs(settings.a4), active=tuner.active_string(),
                         on_pick=toggle_lock, width=card_w),
            note,
            meter,
            ft.Text(HINT_TEXT, size=11, color=p["text_faint"], text_align=ft.TextAlign.CENTER),
        ],
    )
