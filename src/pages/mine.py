"""我的页：个人资料（头像框 + 昵称）+ 调音偏好（参考音 A4）+ 关于

- 参考音存进 models.settings（落盘），并且真的影响调音：services 按 a4 缩放每根弦的目标频率
- 主题切换不在这里 —— 全应用只在 components/app_bar.py，这里只按 palette_of(theme.name) 取色
- 版式**平铺**：内容直接落在渐变底上，用留白 + 细分隔线分区，不套透明卡片
  （毛玻璃只属于底部导航条那一层）；订阅靠参数：MinePage 是零参入口，把状态传给内层 _Mine。
"""

import flet as ft

from app.theme import (
    ACCENT,
    CHIP_ROW_SPACING,
    chip_style,
    content_width,
    hairline,
    palette_of,
    selected_text,
)
from core.constants import (
    APP_REPO,
    APP_VERSION,
    A4_OPTIONS,
    A4_STANDARD,
    AVATAR_CHOICES,
    HELP_TEXT,
    NICKNAME_MAX,
)
from models.settings import SettingsState, settings_state
from models.state import ThemeState, theme_state

A4_COL = 2                      # 五个参考音排一行：5 × 2/12 = 10/12，窄屏也放得下
AVATAR_COL = 4                  # 头像候选：对话框里一行 3 个
PROFILE_TEXT = "实时音高检测 · 六弦指板 · 可换参考音"


@ft.component
def MinePage():
    """零参入口（Router 用）"""
    return _Mine(theme_state, settings_state)


@ft.component
def _Mine(theme: ThemeState, settings: SettingsState):
    p = palette_of(theme.name)
    page = ft.context.page
    col_w = content_width(page)

    return ft.Column(
        spacing=20,
        tight=True,
        width=col_w,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        controls=[
            _profile(p, settings, page),
            hairline(p, col_w),
            _prefs(p, settings),
            hairline(p, col_w),
            _about(p, page),
        ],
    )


# ============================================================
# 分节（平铺：标题 + 内容，分区靠细线）
# ============================================================
def _section_title(p: dict, icon: str, text: str) -> ft.Row:
    return ft.Row(
        spacing=8,
        controls=[
            ft.Icon(icon, size=16, color=ACCENT),
            ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=p["text_dim"]),
        ],
    )


def _profile(p: dict, settings: SettingsState, page) -> ft.Row:
    """头部：头像框（渐变描边环 + 内圈）+ 昵称（点一下改）+ 版本/简介"""
    ring = ft.Container(
        width=88, height=88,
        border_radius=ft.BorderRadius.all(44),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
            colors=[ACCENT, "#0EA5E9"],
        ),
        padding=ft.Padding.all(3),          # 渐变描边环：外圈渐变、内圈纯色
        ink=True,
        tooltip="换头像",
        on_click=lambda e: _pick_avatar(page, p, settings),
        content=ft.Container(
            bgcolor=p["avatar_bg"],
            border_radius=ft.BorderRadius.all(41),
            alignment=ft.Alignment(0, 0),
            content=ft.Text(settings.avatar, size=36),
        ),
    )
    name = ft.Container(
        ink=True,
        border_radius=ft.BorderRadius.all(10),
        padding=ft.Padding.symmetric(vertical=2, horizontal=6),
        tooltip="改昵称",
        on_click=lambda e: _edit_nickname(page, p, settings),
        content=ft.Row(
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(settings.nickname, size=20, weight=ft.FontWeight.W_600,
                        color=p["text"], no_wrap=True),
                ft.Icon(ft.Icons.EDIT_ROUNDED, size=14, color=p["text_faint"]),
            ],
        ),
    )
    return ft.Row(
        spacing=16,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ring,
            ft.Column(
                spacing=4, tight=True, expand=True,
                controls=[
                    name,
                    ft.Text(f"v{APP_VERSION} · {PROFILE_TEXT}", size=11, color=p["text_faint"]),
                ],
            ),
        ],
    )


def _edit_nickname(page, p: dict, settings: SettingsState):
    field = ft.TextField(
        value=settings.nickname,
        max_length=NICKNAME_MAX,
        autofocus=True,
        text_size=14,
        dense=True,
        border_radius=ft.BorderRadius.all(12),
        border_color=p["chip_border"],
        bgcolor=p["chip_bg"],
        on_submit=lambda e: _save_nickname(page, settings, field.value),
    )

    def save(e=None):
        _save_nickname(page, settings, field.value)

    page.show_dialog(ft.AlertDialog(
        title=ft.Text("修改昵称", size=16),
        content=field,
        actions=[
            ft.TextButton("取消", on_click=lambda e: page.pop_dialog()),
            ft.Button("保存", on_click=save),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    ))


def _save_nickname(page, settings: SettingsState, value: str):
    settings.set_nickname(value)        # 空值会被退回默认昵称
    page.pop_dialog()


def _pick_avatar(page, p: dict, settings: SettingsState):
    def pick(e, emoji: str):
        settings.set_avatar(emoji)
        page.pop_dialog()

    options = [
        ft.Container(
            col=AVATAR_COL,
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding.symmetric(vertical=10, horizontal=6),
            border_radius=ft.BorderRadius.all(16),
            ink=True,
            on_click=lambda e, m=emoji: pick(e, m),
            **chip_style(p, emoji == settings.avatar),
            content=ft.Text(emoji, size=26),
        )
        for emoji in AVATAR_CHOICES
    ]
    page.show_dialog(ft.AlertDialog(
        title=ft.Text("选择头像", size=16),
        content=ft.ResponsiveRow(spacing=8, run_spacing=8, controls=options),
        actions=[ft.TextButton("取消", on_click=lambda e: page.pop_dialog())],
        actions_alignment=ft.MainAxisAlignment.END,
    ))


def _prefs(p: dict, settings: SettingsState) -> ft.Column:
    a4 = settings.a4
    standard = settings.is_standard_a4()
    return ft.Column(
        spacing=12,
        tight=True,
        controls=[
            _section_title(p, ft.Icons.GRAPHIC_EQ_ROUNDED, "调音偏好"),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("参考音 A4", size=14, color=p["text"]),
                    ft.Text(f"{a4:g} Hz" + ("　标准" if standard else ""),
                            size=13, weight=ft.FontWeight.W_600,
                            color=ACCENT if standard else p["text_dim"]),
                ],
            ),
            ft.ResponsiveRow(
                spacing=CHIP_ROW_SPACING,
                run_spacing=CHIP_ROW_SPACING,
                controls=[_a4_chip(p, v, a4) for v in A4_OPTIONS],
            ),
            ft.Text("调音时按这个 A4 换算每根弦的目标频率：440 Hz 为标准音高，"
                    "442/435 给合奏，432/415 用于老录音与古典音高。",
                    size=11, color=p["text_faint"]),
        ],
    )


def _a4_chip(p: dict, value: float, current: float) -> ft.Container:
    selected = abs(value - current) < 0.01
    standard = abs(value - A4_STANDARD) < 0.01
    return ft.Container(
        col=A4_COL,
        alignment=ft.Alignment(0, 0),
        padding=ft.Padding.symmetric(vertical=8, horizontal=4),
        border_radius=ft.BorderRadius.all(16),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        ink=True,
        on_click=lambda e, v=value: settings_state.set_a4(v),
        **chip_style(p, selected),
        content=ft.Column(
            spacing=0, tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(f"{value:g}", size=14,
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400,
                        color=selected_text(p, selected)),
                ft.Text("标准" if standard else "Hz", size=9, color=p["text_faint"]),
            ],
        ),
    )


def _about(p: dict, page) -> ft.Column:
    return ft.Column(
        spacing=2,
        tight=True,
        controls=[
            _section_title(p, ft.Icons.INFO_OUTLINE_ROUNDED, "关于"),
            _row(p, ft.Icons.NEW_RELEASES_ROUNDED, "版本", f"v{APP_VERSION}"),
            _row(p, ft.Icons.HELP_OUTLINE_ROUNDED, "使用说明",
                 on_click=lambda e: page.show_dialog(
                     ft.SnackBar(ft.Text(HELP_TEXT), duration=6000))),
            _row(p, ft.Icons.LINK_ROUNDED, "项目地址", "GitHub", on_click=_open_repo),
        ],
    )


async def _open_repo(e):
    """打开项目地址：0.90 起 page.launch_url 废弃，改用 UrlLauncher（协程，必须 await）"""
    await ft.UrlLauncher().launch_url(APP_REPO)


def _row(p: dict, icon: str, label: str, value: str = "", on_click=None) -> ft.Container:
    """一行可点/不可点的信息行（可点的带右箭头 + 水波）"""
    tappable = on_click is not None
    return ft.Container(
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=18, color=p["text_dim"]),
                ft.Text(label, size=13, color=p["text"], expand=True),
                ft.Text(value, size=12, color=p["text_faint"]),
                ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16,
                        color=p["text_faint"], visible=tappable),
            ],
        ),
        padding=ft.Padding.symmetric(vertical=10, horizontal=4),
        border_radius=ft.BorderRadius.all(12),
        ink=tappable,
        on_click=on_click,
    )
