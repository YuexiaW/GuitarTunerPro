"""六弦圆钮：弦号 + 音名，点一下锁定该弦、再点取消

固定分两列（左 6/5/4、右 3/2/1），中间留给琴头 —— 一列的总高 `COLUMN_HEIGHT`
与琴头体一致，旁边琴头上的旋钮正好对着弦钮。
未锁定时高亮自动识别到的那根弦（规则在 services/tuner.py，这里只负责画）。
"""

import flet as ft

from app.theme import chip_style, selected_text

BUTTON_SIZE = 46                                        # 圆钮直径
COLUMN_SPACING = 8                                      # 同列相邻圆钮的间距
BUTTON_PITCH = BUTTON_SIZE + COLUMN_SPACING             # 相邻两颗钮的中心距
COLUMN_HEIGHT = BUTTON_SIZE * 3 + COLUMN_SPACING * 2    # 一列的总高（琴头照这个高度做）


def string_button(p: dict, note: str, number: int, *, freq: float, selected: bool,
                  on_pick) -> ft.Container:
    """一个圆钮：上行弦号、下行音名；选中 = 淡绿底 + 绿描边 + 绿字"""
    return ft.Container(
        width=BUTTON_SIZE,
        height=BUTTON_SIZE,
        border_radius=ft.BorderRadius.all(BUTTON_SIZE / 2),
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
                ft.Text(str(number), size=17,
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400,
                        color=selected_text(p, selected)),
                ft.Text(note, size=9, color=selected_text(p, selected, p["text_dim"])),
            ],
        ),
    )


def string_column(p: dict, strings: dict, numbers: dict, notes: tuple, *,
                  active: str | None, on_pick) -> ft.Column:
    """一列弦钮；notes 是这一列从上到下的音名顺序"""
    return ft.Column(
        spacing=COLUMN_SPACING,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            string_button(p, note, numbers[note], freq=strings[note],
                          selected=note == active, on_pick=on_pick)
            for note in notes
        ],
    )
