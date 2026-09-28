"""占位页（节拍器 / 和弦）

路由、切换、高亮都是真的，页内功能后续换成真实实现：把对应组件替换即可。
（订阅靠参数：零参入口 → 把 theme_state 传给内层 _Placeholder。）
"""

import flet as ft

from app.theme import ACCENT, palette_of
from components.nav_dock import NAV_ITEMS
from models.state import ThemeState, theme_state


@ft.component
def MetronomePage():
    return _Placeholder(1, theme_state)


@ft.component
def ChordsPage():
    return _Placeholder(2, theme_state)


@ft.component
def _Placeholder(index: int, theme: ThemeState):
    p = palette_of(theme.name)
    _route, label, icon, desc = NAV_ITEMS[index]
    body = ft.Column(
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
    )
    # 不写宽度：Container 的 alignment 让它撑满可用宽度，内部文字照旧居中
    return ft.Container(alignment=ft.Alignment(0, 0), content=body)
