"""六弦胶囊（参数驱动）：一排可点的弦名（点一下锁定该弦，再点取消）

未锁定时高亮自动识别到的那根弦；高亮规则在 controller 里，这里只负责画。
"""

import flet as ft

from app.theme import ACCENT, STRING_CHIP_WIDTH, chip_style, glass


def string_chips(p: dict, strings: dict, *, active: str | None, on_pick) -> ft.Control:
    return ft.Row(
        controls=[_chip(p, note, freq, note == active, on_pick)
                  for note, freq in strings.items()],
        spacing=0,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _chip(p: dict, note: str, freq: float, selected: bool, on_pick) -> ft.Container:
    # 玻璃给底色/描边/半径/投影，选中态只覆盖前三项（两个 dict 直接 ** 叠加会重复关键字）
    style = glass(p, 18, soft=True)
    style.update({k: v for k, v in chip_style(p, selected).items()
                  if k in ("bgcolor", "border", "shadow")})
    return ft.Container(
        **style,
        width=STRING_CHIP_WIDTH,
        alignment=ft.Alignment(0, 0),
        padding=ft.Padding.symmetric(vertical=8, horizontal=4),
        margin=ft.Margin.symmetric(horizontal=3),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        ink=True,
        tooltip=f"{note} · {freq:.2f} Hz（点一下锁定该弦）",
        on_click=lambda e, n=note: on_pick(n),
        content=ft.Column(
            controls=[
                ft.Text(note, size=15, color=ACCENT if selected else p["text_dim"],
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400),
                ft.Text(f"{freq:.2f}", size=10,
                        color=p["text_dim"] if selected else p["text_faint"]),
            ],
            spacing=1,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
