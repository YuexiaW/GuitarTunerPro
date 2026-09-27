"""底部悬浮毛玻璃导航条（参数驱动）

路由是真的：每项对应一个 route，选中项由当前 location 推出来（不在组件里缓存索引，
否则多份 View 实例之间会不同步）。点未实现的项进对应路由的占位页。
"""

import flet as ft

from theme import ACCENT, NAV_ITEM_GAP, NAV_ITEM_WIDTH, glass, item_style

# (路由, 标签, 图标, 说明)
NAV_ITEMS = [
    ("/", "调音", ft.Icons.TUNE_ROUNDED, "实时音高检测"),
    ("/metronome", "节拍器", ft.Icons.TIMER_ROUNDED, "速度与拍号训练"),
    ("/chords", "和弦", ft.Icons.LIBRARY_MUSIC_ROUNDED, "和弦指法查询"),
    ("/settings", "设置", ft.Icons.SETTINGS_ROUNDED, "调音偏好与标准音"),
]

TUNER_ROUTE = NAV_ITEMS[0][0]


def nav_index(location: str) -> int:
    """当前路由 → 导航项下标（识别不出时落在「调音」）"""
    loc = (location or "/").rstrip("/") or "/"
    for i, (route, *_rest) in enumerate(NAV_ITEMS):
        if route == loc:
            return i
    return 0


def is_tuner(location: str) -> bool:
    return nav_index(location) == 0


def dock_width() -> float:
    """导航条宽度 = 项数 × (项宽 + 间隙) + 内边距；不给宽度会被 SafeArea 拉成通栏"""
    return len(NAV_ITEMS) * (NAV_ITEM_WIDTH + NAV_ITEM_GAP) + 20


def nav_dock(p: dict, *, index: int, on_select) -> ft.Control:
    row = ft.Row(
        controls=[_item(p, i, i == index, on_select) for i in range(len(NAV_ITEMS))],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Container(
        left=0, right=0, bottom=0,          # 贴底定位（Stack 内 expand 无效）
        alignment=ft.Alignment(0, 0),
        content=ft.SafeArea(
            # bottom= 在 1.x 里是内边距不是开关，安全区开关是 avoid_intrusions_bottom
            avoid_intrusions_bottom=True,
            minimum_padding=ft.Padding.only(left=12, right=12, bottom=12),
            content=ft.Container(
                **glass(p, 28),
                width=dock_width(),
                padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                content=row,
            ),
        ),
    )


def _item(p: dict, i: int, selected: bool, on_select) -> ft.Container:
    route, label, icon, desc = NAV_ITEMS[i]
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(icon, size=22, color=ACCENT if selected else p["text_dim"]),
                ft.Text(label, size=11,
                        color=p["text"] if selected else p["text_dim"],
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400),
            ],
            spacing=2,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=NAV_ITEM_WIDTH,
        alignment=ft.Alignment(0, 0),
        padding=ft.Padding.symmetric(vertical=6, horizontal=4),
        margin=ft.Margin.symmetric(horizontal=3),
        border_radius=ft.BorderRadius.all(22),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        ink=True,
        tooltip=f"{label} · {desc}",
        on_click=lambda e, r=route: on_select(r),
        **item_style(p, selected),
    )
