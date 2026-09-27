"""壳布局（路由的 outlet 宿主）

一个 View 承载所有底部导航页（同级菜单 = 一层 View），点导航只换 outlet 子树：
  背景：View.decoration 渐变 + 三个模糊光斑
  顶部：AppBar 三段槽（logo / 应用名 + 实时状态 / 使用说明 + 主题切换）
  底部：自绘悬浮毛玻璃层（导航条 + 开始·停止胶囊），内容从玻璃底下滑过被糊掉

订阅规则（踩过的坑）：组件**只对作为参数传入**的 observable 订阅 ——
Router 是零参调用 `route.component()`，所以这里写成「零参入口 + 把状态当参数传给内层组件」，
内层 _Shell 收到 theme/pitch/tuner 三个 observable，它们一变就会重渲染。
"""

import flet as ft

from app.theme import BOTTOM_RESERVE, CONTROL_PILL_BOTTOM, blobs, palette_of
from components.app_bar import top_bar
from components.control_pill import control_pill
from components.nav_dock import TUNER_ROUTE, is_tuner, nav_dock, nav_index
from models.state import PitchState, ThemeState, TunerState, pitch_state, theme_state, tuner_state
from services.tuner import start_capture, stop_capture

HELP_TEXT = ("拨动单根弦、靠近麦克风；指针停在中间绿区（±5 音分）就是准了。"
             "点内容区那排弦名可锁定该弦。")


@ft.component
def Layout():
    """零参入口（Router 用）：取路由信息，把可观察状态传给内层"""
    outlet = ft.use_route_outlet()
    location = ft.use_route_location()
    return _Shell(outlet, location, theme_state, pitch_state, tuner_state)


@ft.component
def _Shell(outlet: ft.Control, location: str,
           theme: ThemeState, pitch: PitchState, tuner: TunerState):
    p = palette_of(theme.name)               # 参数里的 observable：读它 = 订阅
    page = ft.context.page

    def show_help(e=None):
        page.show_dialog(ft.SnackBar(content=ft.Text(HELP_TEXT),
                                      duration=ft.Duration(seconds=4)))

    def on_nav_select(route: str):
        """切页：离开调音页先停采集（麦克风别留在后台跑）"""
        if route != TUNER_ROUTE and tuner.running:
            page.run_task(stop_capture)
        if route != location:
            page.navigate(route)

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
        appbar=top_bar(p, status_text=pitch.status_text, status_level=pitch.status_level,
                       on_help=show_help),
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
                                ft.Container(height=16),
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
                    ft.Container(                    # [4] 按钮胶囊（只属于调音页）
                        left=0, right=0, bottom=CONTROL_PILL_BOTTOM,
                        alignment=ft.Alignment(0, 0),
                        visible=is_tuner(location),
                        content=control_pill(p, on_start=start_capture,
                                             on_stop=stop_capture),
                    ),
                    nav_dock(p, index=nav_index(location), on_select=on_nav_select),  # [5]
                ],
            ),
        ],
    )
