"""应用入口：路由表 + 页面初始化

Router manage_views=True（View 由 Layout 产出，支持系统返回手势与 AppBar 返回键），
底部导航切换 = 同级路由，路径如下：
    /            调音（PitchPage）
    /metronome   节拍器（占位）
    /chords      和弦（占位）
    /settings    设置（占位）
"""

import asyncio
import os

import flet as ft

from constants import APP_TITLE
from controller import attach, start_capture
from layout import Layout
from pages.placeholder import ChordsPage, MetronomePage, SettingsPage
from pages.tuner import PitchPage
from state import theme_state


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
                    ft.Route(path="settings", component=SettingsPage),
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
    page.theme_mode = ft.ThemeMode.DARK if theme_state.is_dark() else ft.ThemeMode.LIGHT

    def show_message(text: str):
        page.show_dialog(ft.SnackBar(content=ft.Text(text),
                                      duration=ft.Duration(seconds=4)))

    attach(page, on_message=show_message)
    page.render_views(App)               # manage_views=True 必须用 render_views

    # 本地调试：TUNER_AUTOSTART=1 启动后自动开麦
    if os.environ.get("TUNER_AUTOSTART"):
        async def _auto_start():
            await asyncio.sleep(2.0)
            print("[dbg] autostart", flush=True)
            await start_capture()

        page.run_task(_auto_start)
