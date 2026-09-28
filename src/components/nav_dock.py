"""底部悬浮毛玻璃导航条（响应式）

路由是真的：每项对应一个 route，选中项由当前 location 推出来（不在组件里缓存索引，
否则多份 View 实例之间会不同步）。点未实现的项进对应路由的占位页。

响应式做法：4 项各占 ResponsiveRow 12 格里的 3 格（1/4），宽度由网格按可用宽度算，
不写死项宽 —— 窄屏不会被切掉，宽屏由 `width` 上限（bottom_bar_width）保证不拉成通栏。
"""

import flet as ft

from app.theme import ACCENT, glass, item_style

# (路由, 标签, 图标, 说明)
NAV_ITEMS = [
    ("/", "调音", ft.Icons.TUNE_ROUNDED, "实时音高检测"),
    ("/metronome", "节拍器", ft.Icons.TIMER_ROUNDED, "速度与拍号训练"),
    ("/chords", "和弦", ft.Icons.LIBRARY_MUSIC_ROUNDED, "和弦指法查询"),
    ("/mine", "我的", ft.Icons.PERSON_ROUNDED, "个人中心与调音偏好"),
]

TUNER_ROUTE = NAV_ITEMS[0][0]

NAV_COL = 3                    # 12 格网格里占 3 格 = 1/4（4 项一行）
DOCK_SPACING = 6               # 项间距


def nav_index(location: str) -> int:
    """当前路由 → 导航项下标（识别不出时落在「调音」）"""
    loc = (location or "/").rstrip("/") or "/"
    for i, (route, *_rest) in enumerate(NAV_ITEMS):
        if route == loc:
            return i
    return 0


def nav_dock(p: dict, *, index: int, on_select,
             width: float | None = None) -> ft.Control:
    row = ft.ResponsiveRow(
        controls=[_item(p, i, i == index, on_select) for i in range(len(NAV_ITEMS))],
        spacing=DOCK_SPACING,
        run_spacing=DOCK_SPACING,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Container(
        left=0, right=0, bottom=0,          # 贴底定位（Stack 内 expand 无效）
        alignment=ft.Alignment(0, 0),
        content=ft.SafeArea(
            # bottom= 在 1.x 里是内边距不是开关，安全区开关是 avoid_intrusions_bottom
            avoid_intrusions_bottom=True,
            minimum_padding=ft.Padding.only(left=12, right=12, bottom=8),
            content=ft.Container(
                **glass(p, 24),
                width=width,                # 宽度上限（宽屏对齐内容卡片，窄屏随窗口）
                padding=ft.Padding.symmetric(vertical=4, horizontal=8),
                content=row,
            ),
        ),
    )


def _item(p: dict, i: int, selected: bool, on_select) -> ft.Container:
    route, label, icon, desc = NAV_ITEMS[i]
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(icon, size=18, color=ACCENT if selected else p["text_dim"]),
                ft.Text(label, size=10,
                        color=p["text"] if selected else p["text_dim"],
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400,
                        no_wrap=True),
            ],
            spacing=1,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        col=NAV_COL,                        # 宽度由网格算，不写死
        alignment=ft.Alignment(0, 0),
        padding=ft.Padding.symmetric(vertical=3, horizontal=2),
        border_radius=ft.BorderRadius.all(18),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        ink=True,
        tooltip=f"{label} · {desc}",
        on_click=lambda e, r=route: on_select(r),
        **item_style(p, selected),
    )
