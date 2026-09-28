"""六弦圆钮：弦号 + 音名，点一下锁定该弦、再点取消

一排六个（手机每行 3 个、宽屏一行 6 个），跟着容器把宽度铺满；
读数已经挪到页面顶部，这里就只管弦钮本身。
未锁定时高亮自动识别到的那根弦（规则在 services/tuner.py，这里只负责画）。
"""

import flet as ft

from app.theme import COL_STRING_BTN, chip_style, selected_text

BUTTON_SIZE = 46        # 圆钮直径（固定尺寸：圆形按钮不吃网格宽度）


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


def string_row(p: dict, strings: dict, numbers: dict, notes: tuple, *,
               active: str | None, on_pick) -> ft.ResponsiveRow:
    """一排弦钮（notes 是这一排从左到右的音名顺序），按断点自动每行几个"""
    return ft.ResponsiveRow(
        spacing=8,
        run_spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                col=COL_STRING_BTN,
                alignment=ft.Alignment(0, 0),
                content=string_button(p, note, numbers[note], freq=strings[note],
                                      selected=note == active, on_pick=on_pick),
            )
            for note in notes
        ],
    )
