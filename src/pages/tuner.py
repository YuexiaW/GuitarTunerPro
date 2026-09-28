"""调音页：数字读数 → 音分刻度表盘 → 操作提示 → 「左三弦 | 琴头 | 右三弦」

版式参考目标图：读数（音符/频率/音分）放大放在最上，下面接带刻度的横向表盘
（基线 + 每 5 音分刻度 + 中央固定容错区 + 细竖线指针 + -50/0/+50 标注），
再下面是操作提示，最后是**固定两列弦钮夹着中间的琴头**。
内容平铺在渐变底上，不套卡片 —— 毛玻璃只属于底部导航条。

**整页响应式**：页面自己不写宽度 —— 返回 `ft.Container`（托一层）里放内容，
表盘是流体宽度、刻度自带左右留白；弦钮与琴头由同一套尺寸函数按 `control_scale(page)` 缩放
（手机竖屏 ≈1.0、宽屏上限 1.2），圆钮、琴头、字号、间距一起变。
全页没有一个写死的「容器宽度」，也没有固定中间那一条。

声明式：只读 pitch_state / tuner_state / settings_state，采集那边一改状态这里自己重渲染。
（订阅靠参数：PitchPage 是零参入口，把 observable 传给内层 _Tuner。）
"""

import flet as ft

from app.theme import ACCENT, BAD, control_scale, palette_of
from components.headstock import headstock
from components.meter import cents_meter
from components.string_buttons import button_pitch, button_size, column_height, string_column
from core.pitch import GUITAR_STRINGS, string_freqs
from models.settings import SettingsState, settings_state
from models.state import PitchState, ThemeState, TunerState, pitch_state, theme_state, tuner_state
from services.tuner import toggle_lock

NOTES = tuple(GUITAR_STRINGS)                                      # 从第 6 弦到第 1 弦
STRING_NO = {note: len(NOTES) - i for i, note in enumerate(NOTES)}  # E2 → 6 … E4 → 1
LEFT_NOTES = NOTES[:3]                                             # 左列：6 / 5 / 4 弦
RIGHT_NOTES = NOTES[3:]                                            # 右列：3 / 2 / 1 弦
BASE_HEAD_GAP = 12                                                 # 弦钮列与琴头的基准间距（乘 scale）


@ft.component
def PitchPage():
    """零参入口（Router 用）"""
    return _Tuner(theme_state, pitch_state, tuner_state, settings_state)


@ft.component
def _Tuner(theme: ThemeState, pitch: PitchState, tuner: TunerState,
           settings: SettingsState):
    p = palette_of(theme.name)              # 读参数里的 observable = 订阅
    scale = control_scale(ft.context.page)  # 弦钮/琴头随内容区宽度缩放（带上下限）
    strings = string_freqs(settings.a4)
    active = tuner.active_string()

    has_pitch = pitch.has_pitch()
    color = ACCENT if pitch.in_tune else BAD
    note_color = color if has_pitch else p["text_faint"]
    cents_color = color if has_pitch else p["text_faint"]

    # 数字读数放大，放在刻度表盘的上面（先看数、再对照刻度）
    readout = ft.Column(
        spacing=0,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(pitch.note, size=104, weight=ft.FontWeight.BOLD, color=note_color),
            ft.Text(f"{pitch.freq:.1f} Hz" if has_pitch else "-- Hz",
                    size=24, color=p["text_dim"]),
            ft.Text(f"{pitch.cents:+.1f} 音分" if has_pitch else "0.0 音分",
                    size=17, color=cents_color),
        ],
    )

    body = ft.Column(
        spacing=20,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            readout,
            cents_meter(p, cents=pitch.cents, color=color),
            _prompt(p, pitch, has_pitch),
            # 固定两列弦钮 + 中间琴头（尺寸都由 scale 推导，随窗口缩放）
            ft.Row(
                spacing=BASE_HEAD_GAP * scale,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    string_column(p, strings, STRING_NO, LEFT_NOTES, scale=scale,
                                  active=active, on_pick=toggle_lock),
                    headstock(p, height=column_height(scale),
                              row_pitch=button_pitch(scale),
                              first_center=button_size(scale) / 2),
                    string_column(p, strings, STRING_NO, RIGHT_NOTES, scale=scale,
                                  active=active, on_pick=toggle_lock),
                ],
            ),
        ],
    )
    # 不自己算宽度：表盘是流体宽度，Container 只托一层（alignment 让它撑满可用宽度）
    return ft.Container(alignment=ft.Alignment(0, 0), content=body)


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
