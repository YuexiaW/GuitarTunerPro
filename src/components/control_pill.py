"""底部悬浮按钮胶囊（参数驱动）：开始调音 / 停止（叠在导航条上方）"""

import flet as ft

from theme import ACCENT, glass


def control_pill(p: dict, *, on_start, on_stop) -> ft.Control:
    start_btn = ft.Button(
        "开始调音", icon=ft.Icons.MIC,
        on_click=on_start,              # 直接透传：Flet 自己会 await 异步回调
        style=ft.ButtonStyle(
            color="#04231A", bgcolor=ACCENT,
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.Padding.symmetric(horizontal=22, vertical=14),
        ),
    )
    stop_btn = ft.Button(
        "停止", icon=ft.Icons.STOP,
        on_click=on_stop,
        style=ft.ButtonStyle(
            color=p["stop_fg"],
            bgcolor=p["stop_bg"],
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.Padding.symmetric(horizontal=20, vertical=14),
        ),
    )
    return ft.Container(
        **glass(p, 26),
        padding=ft.Padding.symmetric(vertical=8, horizontal=12),
        content=ft.Row(
            controls=[start_btn, stop_btn],
            spacing=10,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
