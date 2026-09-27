"""占位页（节拍器 / 和弦 / 设置）

路由、切换、高亮都是真的，页内功能后续换成真实实现：把对应组件替换即可。
（订阅靠参数：零参入口 → 把 theme_state 传给内层 _Placeholder。）
"""

import flet as ft

from components.nav_dock import NAV_ITEMS
from state import ThemeState, theme_state
from theme import ACCENT, content_width, glass


@ft.component
def MetronomePage():
    return _Placeholder(1, theme_state)


@ft.component
def ChordsPage():
    return _Placeholder(2, theme_state)


@ft.component
def SettingsPage():
    return _Placeholder(3, theme_state)


@ft.component
def _Placeholder(index: int, theme: ThemeState):
    p = theme.palette()
    _route, label, icon, desc = NAV_ITEMS[index]
    return ft.Container(
        **glass(p, 28),
        width=content_width(ft.context.page),
        padding=ft.Padding.symmetric(vertical=44, horizontal=24),
        content=ft.Column(
            spacing=12,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=46, color=ACCENT),
                ft.Text(f"{label}（开发中）", size=20,
                        weight=ft.FontWeight.W_600, color=p["text"]),
                ft.Text(desc, size=12, color=p["text_dim"]),
                ft.Text("底部导航已经是真实路由：入口、切换、高亮都接好了，后续直接换实现",
                        size=11, color=p["text_faint"], text_align=ft.TextAlign.CENTER),
            ],
        ),
    )
