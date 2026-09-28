"""调音页：六弦胶囊 → 大音符/频率卡 → 音分偏差卡 → 提示

声明式：只读 pitch_state / tuner_state，采集那边一改状态，这里自己重渲染。
（订阅靠参数：PitchPage 是零参入口，把两个 observable 传给内层 _Tuner。）
"""

import flet as ft

from app.theme import ACCENT, BAD, content_width, glass, palette_of
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

    note_card = ft.Container(
        **glass(p, 28),
        width=card_w,
        padding=ft.Padding.symmetric(vertical=22, horizontal=24),
        content=ft.Column(
            spacing=2,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(pitch.note, size=88, weight=ft.FontWeight.BOLD, color=note_color),
                ft.Text(f"{pitch.freq:.1f} Hz" if has_pitch else "-- Hz",
                        size=22, color=p["text_dim"]),
            ],
        ),
    )
    meter_card = ft.Container(
        **glass(p, 24),
        width=card_w,
        padding=ft.Padding.symmetric(vertical=20, horizontal=20),
        content=ft.Column(
            spacing=10,
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
        ),
    )
    hint_card = ft.Container(
        **glass(p, 20, soft=True),
        width=card_w,
        padding=ft.Padding.symmetric(vertical=14, horizontal=18),
        content=ft.Text(HINT_TEXT, size=11, color=p["text_dim"]),
    )

    return ft.Column(
        spacing=14,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            string_chips(p, string_freqs(settings.a4), active=tuner.active_string(),
                         on_pick=toggle_lock, width=card_w),
            note_card,
            meter_card,
            hint_card,
        ],
    )
