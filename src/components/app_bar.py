"""顶部栏（参数驱动）：leading 渐变 logo / title 应用名 + 实时状态 / actions 帮助 + 主题切换

Material AppBar 槽位的老问题：leading 会把子控件拉成 leading_width × toolbar_height，
所以外面套一层居中容器；elevation 必须为 0，否则 M3 会用 surfaceTint 掺色，半透明底就不透了。
"""

import flet as ft

from constants import APP_NAME
from theme import ACCENT, status_color


def top_bar(p: dict, *, status_text: str, status_level: str, is_dark: bool,
            on_help, on_toggle_theme) -> ft.AppBar:
    logo = ft.Container(
        width=36, height=36,
        border_radius=ft.BorderRadius.all(12),
        alignment=ft.Alignment(0, 0),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
            colors=[ACCENT, "#0EA5E9"],
        ),
        content=ft.Text("🎸", size=18),
    )
    title = ft.Column(
        controls=[
            ft.Text(APP_NAME, size=16, weight=ft.FontWeight.W_600, color=p["text"]),
            ft.Text(status_text, size=12, color=status_color(status_level, p),
                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
        ],
        spacing=0,
        tight=True,
    )
    # 主题切换：图标表示「点了会切到哪」（暗色时显示月亮）
    theme_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE,
        icon_color=p["appbar_fg"],
        icon_size=22,
        tooltip="切换浅色主题" if is_dark else "切换深色主题",
        on_click=lambda e: on_toggle_theme(),
    )
    help_btn = ft.IconButton(
        icon=ft.Icons.HELP_OUTLINE, icon_color=p["appbar_fg"],
        icon_size=22, tooltip="使用说明", on_click=on_help,
    )

    return ft.AppBar(
        leading=ft.Container(content=logo, alignment=ft.Alignment(0, 0)),
        leading_width=56,
        automatically_imply_leading=False,      # 自己给了 leading，别自动塞返回键
        title=title,
        center_title=False,
        actions=[help_btn, theme_btn],          # 右侧：使用说明 + 主题切换（最右）
        actions_padding=ft.Padding.only(right=8),
        bgcolor=p["appbar_bg"],
        color=p["appbar_fg"],
        toolbar_height=64,
        elevation=0,
    )
