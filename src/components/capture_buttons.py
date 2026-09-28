"""开始 / 停止采集按钮（属于调音页自己的内容区）

以前它是叠在底部导航条上的全局悬浮胶囊 —— 导航条是所有页面共用的「全局」层，
调音页的操作按钮不该混在那一层里，现在改成调音页内容的一部分（平铺，不套玻璃）。
尺寸跟着 `scale`（app.theme.control_scale）走，和旁边的弦钮一起缩放。
"""

import flet as ft

from app.theme import ACCENT

BASE_HEIGHT = 38      # 基准按钮高（scale = 1.0 时，宽屏上限 1.2 → 45.6）
BASE_GAP = 10         # 两个按钮之间的基准间距


def capture_buttons(p: dict, *, scale: float, on_start, on_stop) -> ft.Row:
    """开始调音（主）/ 停止（次）；回调直接透传，Flet 自己会 await 异步回调"""
    height = BASE_HEIGHT * scale
    radius = height * 0.42
    text = height * 0.32

    start = ft.Button(
        "开始调音",
        icon=ft.Icons.MIC,
        height=height,
        on_click=on_start,
        style=ft.ButtonStyle(
            color="#04231A",
            bgcolor=ACCENT,
            shape=ft.RoundedRectangleBorder(radius=radius),
            padding=ft.Padding.symmetric(horizontal=height * 0.42),
            text_style=ft.TextStyle(size=text, weight=ft.FontWeight.W_600),
        ),
    )
    stop = ft.Button(
        "停止",
        icon=ft.Icons.STOP,
        height=height,
        on_click=on_stop,
        style=ft.ButtonStyle(
            color=p["stop_fg"],
            bgcolor=p["stop_bg"],
            shape=ft.RoundedRectangleBorder(radius=radius),
            padding=ft.Padding.symmetric(horizontal=height * 0.36),
            text_style=ft.TextStyle(size=text),
        ),
    )
    return ft.Row(
        spacing=BASE_GAP * scale,
        tight=True,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[start, stop],
    )
