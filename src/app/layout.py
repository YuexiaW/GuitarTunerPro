"""壳布局（路由的 outlet 宿主）

一个 View 承载所有底部导航页（同级菜单 = 一层 View），点导航只换 outlet 子树：
  背景：View.decoration 渐变 + 三个模糊光斑
  顶部：AppBar 三段槽（logo / 应用名 + 实时状态 / 使用说明 + 主题切换）
  底部：自绘悬浮毛玻璃层（只有导航条 —— 它才是全局的），内容从玻璃底下滑过被糊掉

调音页的「开始/停止」按钮**不在这里**：那是调音页自己的操作，归 pages/tuner.py 内容区。

订阅规则（踩过的坑）：组件**只对作为参数传入**的 observable 订阅 ——
Router 是零参调用 `route.component()`，所以这里写成「零参入口 + 把状态当参数传给内层组件」，
内层 _Shell 收到 theme 这个 observable，主题一变整棵重渲染。
"""

import flet as ft

from app.theme import BOTTOM_RESERVE, blobs, bottom_bar_width, palette_of
from components.app_bar import top_bar
from components.nav_dock import nav_dock, nav_index
from core.constants import HELP_TEXT
from models.state import ThemeState, theme_state
from services.tuner import go


@ft.component
def Layout():
    """零参入口（Router 用）：取路由信息，把可观察状态传给内层"""
    outlet = ft.use_route_outlet()
    location = ft.use_route_location()
    return _Shell(outlet, location, theme_state)


@ft.component
def _Shell(outlet: ft.Control, location: str, theme: ThemeState):
    p = palette_of(theme.name)               # 参数里的 observable：读它 = 订阅
    page = ft.context.page

    def show_help(e=None):
        page.show_dialog(ft.SnackBar(content=ft.Text(HELP_TEXT),
                                      duration=ft.Duration(seconds=4)))

    def on_nav_select(route: str):
        """切页：离开调音页先停采集（逻辑在 services.tuner.go，「我的」页快捷入口共用）"""
        go(page, route, location)

    return ft.View(
        route="/",                           # 同级菜单共用一层 View（Router manage_views）
        padding=0,
        spacing=0,
        bgcolor=ft.Colors.TRANSPARENT,
        decoration=ft.BoxDecoration(
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=p["gradient"],
            )
        ),
        appbar=top_bar(p, on_help=show_help),
        controls=[
            ft.Stack(
                expand=True,
                controls=[
                    *blobs(p),                       # [0..2] 背景光斑（在内容与玻璃之下）
                    ft.Container(                    # [3] 内容层（Stack 内 expand 无效 → 四边定位）
                        left=0, right=0, top=0, bottom=0,
                        content=ft.Column(
                            expand=True,
                            scroll=ft.ScrollMode.AUTO,
                            spacing=14,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(height=8),      # 顶栏与内容之间留一点气口
                                ft.AnimatedSwitcher(
                                    outlet,
                                    duration=300,
                                    reverse_duration=200,
                                    transition=ft.AnimatedSwitcherTransition.FADE,
                                    switch_in_curve=ft.AnimationCurve.EASE_IN_OUT,
                                    switch_out_curve=ft.AnimationCurve.EASE_IN_OUT,
                                ),
                                # 末尾留白：卡片滚到玻璃下面被糊掉（留白要放在滚动内容里）
                                ft.Container(height=BOTTOM_RESERVE),
                            ],
                        ),
                    ),
                    nav_dock(p, index=nav_index(location), on_select=on_nav_select,
                             width=bottom_bar_width(page)),   # [4] 宽屏对齐卡片，窄屏随窗口
                ],
            ),
        ],
    )
