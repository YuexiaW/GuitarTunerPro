"""应用入口：路由表 + 页面初始化

Router manage_views=True（View 由 Layout 产出，支持系统返回手势与 AppBar 返回键），
底部导航切换 = 同级路由，路径如下：
    /            调音（PitchPage）
    /metronome   节拍器（占位）
    /chords      和弦（占位）
    /mine        我的
"""

import asyncio
import os

import flet as ft

from app.layout import Layout
from components.app_bar import apply_theme
from core.constants import APP_TITLE
from models.settings import settings_state
from pages.mine import MinePage
from pages.placeholder import ChordsPage, MetronomePage
from pages.tuner import PitchPage
from services.tuner import attach, start_capture


@ft.component
def App():
    return ft.Router(
        [
            ft.Route(
                component=Layout,
                outlet=True,
                children=[
                    ft.Route(index=True, component=PitchPage),        # "/"
                    ft.Route(path="metronome", component=MetronomePage),
                    ft.Route(path="chords", component=ChordsPage),
                    ft.Route(path="mine", component=MinePage),
                ],
            ),
        ],
        manage_views=True,
    )


def main(page: ft.Page):
    page.title = APP_TITLE
    page.padding = 0                     # 默认 10 会顶开四周
    page.spacing = 0
    page.bgcolor = ft.Colors.TRANSPARENT  # 底色交给 View 的渐变
    apply_theme(page)                     # 初始主题（切换逻辑在 components/app_bar.py）

    def show_message(text: str):
        page.show_dialog(ft.SnackBar(content=ft.Text(text),
                                      duration=ft.Duration(seconds=4)))

    attach(page, on_message=show_message)
    page.render_views(App)               # manage_views=True 必须用 render_views
    settings_state.load(page)            # 读取上次的偏好（参考音 A4）；读不到就用默认值

    # 本地调试：TUNER_AUTOSTART=1 启动后自动开麦
    if os.environ.get("TUNER_AUTOSTART"):
        async def _auto_start():
            await asyncio.sleep(2.0)
            print("[dbg] autostart", flush=True)
            await start_capture()

        page.run_task(_auto_start)
