"""六弦条（响应式）：6 个可点的弦名胶囊，点一下锁定该弦、再点取消

未锁定时高亮自动识别到的那根弦；高亮规则在 services/tuner.py，这里只负责画。

响应式做法：胶囊不写死宽度，用 ResponsiveRow 的 12 格网格 —— 每个占 2 格（1/6），
6 个正好一行；窗口再窄也各占 1/6，不会顶出屏幕被裁。`width` 只用来限上限（宽屏别拉满）。
"""

import flet as ft

from app.theme import CHIP_ROW_SPACING, chip_style, selected_text

CHIP_COL = 2                  # 12 格网格里占 2 格 = 1/6（6 个一行）


def string_chips(p: dict, strings: dict, *, active: str | None, on_pick,
                 width: float | None = None) -> ft.Control:
    row = ft.ResponsiveRow(
        controls=[_chip(p, note, freq, note == active, on_pick)
                  for note, freq in strings.items()],
        spacing=CHIP_ROW_SPACING,
        run_spacing=CHIP_ROW_SPACING,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Container(width=width, content=row) if width else row


def _chip(p: dict, note: str, freq: float, selected: bool, on_pick) -> ft.Container:
    return ft.Container(
        **chip_style(p, selected),         # 平铺胶囊：未选中只描边，选中填淡绿
        col=CHIP_COL,                      # 宽度由网格算，不写死
        alignment=ft.Alignment(0, 0),
        padding=ft.Padding.symmetric(vertical=8, horizontal=4),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        ink=True,
        tooltip=f"{note} · {freq:.2f} Hz（点一下锁定该弦）",
        on_click=lambda e, n=note: on_pick(n),
        content=ft.Column(
            controls=[
                ft.Text(note, size=15, color=selected_text(p, selected, p["text_dim"]),
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400),
                ft.Text(f"{freq:.2f}", size=10,
                        color=p["text_dim"] if selected else p["text_faint"]),
            ],
            spacing=1,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
