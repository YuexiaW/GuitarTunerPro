"""调音页：音分表盘 → 操作提示 → 「左三弦 | 读数 | 右三弦」

版式参考目标图：表盘在最上（带刻度与 -50/+50 标注），中间是提示文字，
下面六个弦钮分两列夹住中间读数（不再是一排横胶囊）。
内容平铺在渐变底上，不套卡片 —— 毛玻璃只属于底部导航条（见 app/theme.py）。

声明式：只读 pitch_state / tuner_state / settings_state，采集那边一改状态这里自己重渲染。
（订阅靠参数：PitchPage 是零参入口，把 observable 传给内层 _Tuner。）
"""

import flet as ft

from app.theme import ACCENT, BAD, TUNER_CLUSTER_MAX, content_width, palette_of
from components.meter import cents_meter
from components.string_buttons import string_column
from core.pitch import GUITAR_STRINGS, string_freqs
from models.settings import SettingsState, settings_state
from models.state import PitchState, ThemeState, TunerState, pitch_state, theme_state, tuner_state
from services.tuner import toggle_lock

NOTES = tuple(GUITAR_STRINGS)                                      # 从第 6 弦到第 1 弦
STRING_NO = {note: len(NOTES) - i for i, note in enumerate(NOTES)}  # E2 → 6 … E4 → 1
LEFT_NOTES = NOTES[:3]                                             # 左列：6 / 5 / 4 弦
RIGHT_NOTES = NOTES[3:]                                            # 右列：3 / 2 / 1 弦


@ft.component
def PitchPage():
    """零参入口（Router 用）"""
    return _Tuner(theme_state, pitch_state, tuner_state, settings_state)


@ft.component
def _Tuner(theme: ThemeState, pitch: PitchState, tuner: TunerState,
           settings: SettingsState):
    p = palette_of(theme.name)              # 读参数里的 observable = 订阅
    row_w = content_width(ft.context.page)
    strings = string_freqs(settings.a4)
    active = tuner.active_string()

    has_pitch = pitch.has_pitch()
    color = ACCENT if pitch.in_tune else BAD
    note_color = color if has_pitch else p["text_faint"]
    cents_color = color if has_pitch else p["text_faint"]

    readout = ft.Column(
        spacing=2,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(pitch.note, size=76, weight=ft.FontWeight.BOLD, color=note_color),
            ft.Text(f"{pitch.freq:.1f} Hz" if has_pitch else "-- Hz",
                    size=15, color=p["text_dim"]),
            ft.Text(f"{pitch.cents:+.1f} 音分" if has_pitch else "0.0 音分",
                    size=13, color=cents_color),
        ],
    )

    cluster = ft.Container(
        width=min(row_w, TUNER_CLUSTER_MAX),      # 只限上限：手机上自动收窄
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                string_column(p, strings, STRING_NO, LEFT_NOTES,
                              active=active, on_pick=toggle_lock),
                ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=readout),
                string_column(p, strings, STRING_NO, RIGHT_NOTES,
                              active=active, on_pick=toggle_lock),
            ],
        ),
    )

    return ft.Column(
        spacing=20,
        tight=True,
        width=row_w,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            cents_meter(p, cents=pitch.cents, color=color),
            _prompt(p, pitch, has_pitch),
            cluster,
        ],
    )


def _prompt(p: dict, pitch: PitchState, has_pitch: bool) -> ft.Column:
    """提示两行：大字给「该做什么」，小字给当前状态（参考图也是这个层次）"""
    if not has_pitch:
        main, sub, color = "轻拨一根琴弦", "等待拨弦…", p["text"]
    elif pitch.in_tune:
        main, sub, color = "音准完美", f"{pitch.note} 已校准", ACCENT
    elif pitch.cents > 0:
        main = "音偏高，把弦拧松一点"
        sub = f"比 {pitch.note} 高 {abs(pitch.cents):.1f} 音分"
        color = p["text"]
    else:
        main = "音偏低，把弦拧紧一点"
        sub = f"比 {pitch.note} 低 {abs(pitch.cents):.1f} 音分"
        color = p["text"]

    return ft.Column(
        spacing=4,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(main, size=18, weight=ft.FontWeight.W_600, color=color),
            ft.Text(sub, size=12, color=p["text_faint"]),
        ],
    )
