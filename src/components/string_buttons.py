"""六弦圆钮：弦号 + 音名，点一下锁定该弦、再点取消

固定分两列（左 6/5/4、右 3/2/1），中间留给琴头。
**尺寸不写死**：全部由 `scale`（`app.theme.control_scale(page)` 给的系数）推导 ——
手机竖屏宽度下 scale≈1、宽屏上限 1.2，圆钮、字号、间距一起跟着变大变小。
一列的总高 `column_height()` 与琴头体一致，旁边琴头上的旋钮正好对着弦钮。
未锁定时高亮自动识别到的那根弦（规则在 services/tuner.py，这里只负责画）。
"""

import flet as ft

from app.theme import chip_style, selected_text

BASE_BUTTON = 46        # 基准圆钮直径（scale = 1.0 时）
BASE_SPACING = 8        # 基准间距
BUTTON_ROWS = 3         # 每列三颗钮


def button_size(scale: float) -> float:
    """圆钮直径"""
    return BASE_BUTTON * scale


def button_pitch(scale: float) -> float:
    """相邻两颗钮的中心距"""
    return button_size(scale) + BASE_SPACING * scale


def column_height(scale: float) -> float:
    """一列的总高（琴头照这个高度做，两者才对得齐）"""
    return button_size(scale) * BUTTON_ROWS + BASE_SPACING * scale * (BUTTON_ROWS - 1)


def string_button(p: dict, note: str, number: int, *, size: float, freq: float,
                  selected: bool, on_pick) -> ft.Container:
    """一个圆钮：上大行弦号、下小行音名（E2/A2/D3/G3/B3/E4）；选中 = 淡绿底 + 绿描边 + 绿字"""
    return ft.Container(
        width=size,
        height=size,
        border_radius=ft.BorderRadius.all(size / 2),
        **chip_style(p, selected),
        alignment=ft.Alignment(0, 0),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        ink=True,
        tooltip=f"{number} 弦 {note} · {freq:.2f} Hz（点一下锁定该弦）",
        on_click=lambda e, n=note: on_pick(n),
        content=ft.Column(
            spacing=0,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(str(number), size=size * 0.38, no_wrap=True,
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
                        color=selected_text(p, selected)),
                # 音名：够醒目的字号 + 选中时用主色，未选中也别做成灰到底的小字
                ft.Text(note, size=size * 0.26, no_wrap=True,
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
                        color=selected_text(p, selected, p["text_dim"])),
            ],
        ),
    )


def string_column(p: dict, strings: dict, numbers: dict, notes: tuple, *,
                  scale: float, active: str | None, on_pick) -> ft.Column:
    """一列弦钮；notes 是这一列从上到下的音名顺序"""
    size = button_size(scale)
    return ft.Column(
        spacing=BASE_SPACING * scale,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            string_button(p, note, numbers[note], size=size, freq=strings[note],
                          selected=note == active, on_pick=on_pick)
            for note in notes
        ],
    )
