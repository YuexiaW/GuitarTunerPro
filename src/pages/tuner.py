"""调音页：数字读数（音名 + 频率）→ 音分刻度表盘 → 操作提示 → 「左三弦 | 琴头 | 右三弦」→ 开始/停止

版式参考目标图：读数放大放在最上（音名 + 频率，偏差交给下面的表盘），
下面接带刻度的横向表盘（基线 + 每 5 音分刻度 + 中央固定容错区 + 细竖线指针 + -50/0/+50 标注），
再下面是操作提示、**识别模式切换**（自动识别 / 精准识别），
然后**固定两列弦钮夹着中间的琴头**，最后是本页的采集按钮。
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
from components.capture_buttons import capture_buttons
from components.headstock import headstock
from components.meter import cents_meter
from components.mode_switch import mode_switch
from components.string_buttons import button_pitch, button_size, column_height, string_column
from core.pitch import GUITAR_STRINGS, string_freqs
from models.settings import SettingsState, settings_state
from models.state import PitchState, ThemeState, TunerState, pitch_state, theme_state, tuner_state
from services.tuner import pick_string, set_mode, start_capture, stop_capture

NOTES = tuple(GUITAR_STRINGS)                                      # 从第 6 弦到第 1 弦
STRING_NO = {note: len(NOTES) - i for i, note in enumerate(NOTES)}  # E2 → 6 … E4 → 1
LEFT_NOTES = tuple(reversed(NOTES[:3]))                            # 左列：4 / 5 / 6 弦（6 弦在最下）
RIGHT_NOTES = NOTES[3:]                                            # 右列：3 / 2 / 1 弦（1 弦在最下）
# 顺序照真实 3+3 琴头：越靠近琴枕（下面）的旋钮，弦越粗的那一侧依次是 6/5/4 与 1/2/3
# （原来左列是 E2 在最上，和右边 1 弦在最下对不上，所以 E2 挪到最下面）
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
    # 精准模式下还没拨弦也先把目标音名显示出来（知道自己在调哪根）
    shown_note = pitch.note if has_pitch else (tuner.locked or "?")
    if has_pitch:
        note_color = color
    else:
        note_color = p["text_dim"] if tuner.locked else p["text_faint"]

    # 数字读数放大，放在刻度表盘的上面（先看数、再对照刻度）
    # 只留音名 + 频率：偏差看下面表盘的指针/绿区就够了，不再单列一行音分数值
    readout = ft.Column(
        spacing=0,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(shown_note, size=118, weight=ft.FontWeight.BOLD, color=note_color),
            ft.Text(f"{pitch.freq:.1f} Hz" if has_pitch else "-- Hz",
                    size=26, color=p["text_dim"]),
        ],
    )

    body = ft.Column(
        spacing=10,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            readout,
            cents_meter(p, cents=pitch.cents, color=color),
            _prompt(p, pitch, has_pitch, tuner),
            # 模式切换放在弦钮上方：它决定这排钮怎么工作
            mode_switch(p, mode=tuner.mode, scale=scale, on_pick=set_mode),
            # 固定两列弦钮 + 中间琴头（尺寸都由 scale 推导，随窗口缩放）
            ft.Row(
                spacing=BASE_HEAD_GAP * scale,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    string_column(p, strings, STRING_NO, LEFT_NOTES, scale=scale,
                                  active=active, on_pick=pick_string),
                    headstock(p, height=column_height(scale),
                              row_pitch=button_pitch(scale),
                              first_center=button_size(scale) / 2),
                    string_column(p, strings, STRING_NO, RIGHT_NOTES, scale=scale,
                                  active=active, on_pick=pick_string),
                ],
            ),
            # 采集按钮属于本页操作，放内容区里（不再叠在全局导航条上）
            capture_buttons(p, scale=scale, on_start=start_capture, on_stop=stop_capture),
        ],
    )
    # 不自己算宽度：表盘是流体宽度，Container 只托一层；
    # 对齐用「顶部居中」—— 内容贴顶，别在可用高度里垂直居中（读数会离顶栏很远）
    return ft.Container(alignment=ft.Alignment(0, -1), content=body)


def _prompt(p: dict, pitch: PitchState, has_pitch: bool, tuner: TunerState) -> ft.Column:
    """提示两行：大字给「该做什么」，小字给当前状态（参考图也是这个层次）

    两种模式的措辞不同：自动识别不用选弦，精准识别要先知道在调哪根。
    """
    target = tuner.locked if tuner.precise() else None
    if not has_pitch:
        if target:
            main = f"轻拨 {STRING_NO[target]} 弦 {target}"
            sub = "精准识别：偏差只相对这根弦算"
        else:
            main, sub = "轻拨任意一根琴弦", "自动识别：自己找最近的那根弦"
        color = p["text"]
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
