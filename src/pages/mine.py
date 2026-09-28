"""我的页：应用信息 + 调音偏好（参考音 A4）+ 关于

- 参考音存进 models.settings（落盘），并且真的影响调音：services 按 a4 缩放每根弦的目标频率
- 主题切换不在这里 —— 全应用只在 components/app_bar.py，这里只按 palette_of(theme.name) 取色
- 布局沿用调音页的配方：玻璃卡片 + ResponsiveRow（窄屏自动换行，不写死宽度）
  （订阅靠参数：MinePage 是零参入口，把 theme/settings 传给内层 _Mine。）
"""

import flet as ft

from app.theme import ACCENT, CHIP_ROW_SPACING, chip_style, content_width, glass, palette_of
from core.constants import (
    APP_NAME,
    APP_REPO,
    APP_VERSION,
    A4_OPTIONS,
    A4_STANDARD,
    HELP_TEXT,
)
from models.settings import SettingsState, settings_state
from models.state import ThemeState, theme_state

A4_COL = 2                      # 五个参考音排一行：5 × 2/12 = 10/12，窄屏也放得下
PROFILE_TEXT = "实时音高检测 · 六弦指板 · 可换参考音"


@ft.component
def MinePage():
    """零参入口（Router 用）"""
    return _Mine(theme_state, settings_state)


@ft.component
def _Mine(theme: ThemeState, settings: SettingsState):
    p = palette_of(theme.name)
    page = ft.context.page
    card_w = content_width(page)

    return ft.Column(
        spacing=14,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            _profile_card(p, card_w),
            _prefs_card(p, card_w, settings),
            _about_card(p, card_w, page),
        ],
    )


# ============================================================
# 卡片
# ============================================================
def _card(p: dict, width: float, controls: list) -> ft.Container:
    return ft.Container(
        **glass(p, 28),
        width=width,
        padding=ft.Padding.symmetric(vertical=18, horizontal=20),
        content=ft.Column(spacing=12, tight=True, controls=controls),
    )


def _card_title(p: dict, icon: str, text: str) -> ft.Row:
    return ft.Row(
        spacing=8,
        controls=[
            ft.Icon(icon, size=16, color=ACCENT),
            ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=p["text_dim"]),
        ],
    )


def _profile_card(p: dict, width: float) -> ft.Container:
    avatar = ft.Container(
        width=56, height=56,
        border_radius=ft.BorderRadius.all(20),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
            colors=[ACCENT, "#0EA5E9"],
        ),
        alignment=ft.Alignment(0, 0),
        content=ft.Text("🎸", size=26),
    )
    return _card(p, width, [
        ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                avatar,
                ft.Column(
                    spacing=2, tight=True, expand=True,
                    controls=[
                        ft.Text(APP_NAME, size=18, weight=ft.FontWeight.W_600, color=p["text"]),
                        ft.Text(f"v{APP_VERSION}", size=11, color=p["text_faint"]),
                        ft.Text(PROFILE_TEXT, size=11, color=p["text_dim"]),
                    ],
                ),
            ],
        ),
    ])


def _prefs_card(p: dict, width: float, settings: SettingsState) -> ft.Container:
    a4 = settings.a4
    chips = ft.ResponsiveRow(
        spacing=CHIP_ROW_SPACING,
        run_spacing=CHIP_ROW_SPACING,
        controls=[_a4_chip(p, v, a4) for v in A4_OPTIONS],
    )
    return _card(p, width, [
        _card_title(p, ft.Icons.GRAPHIC_EQ_ROUNDED, "调音偏好"),
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("参考音 A4", size=14, color=p["text"]),
                ft.Text(f"{a4:g} Hz" + ("　标准" if settings.is_standard_a4() else ""),
                        size=13, weight=ft.FontWeight.W_600,
                        color=ACCENT if settings.is_standard_a4() else p["text_dim"]),
            ],
        ),
        chips,
        ft.Text("调音时按这个 A4 换算每根弦的目标频率：440 Hz 为标准音高，"
                "442/435 给合奏，432/415 用于老录音与古典音高。",
                size=11, color=p["text_faint"]),
    ])


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
                        color=ACCENT if selected else p["text"]),
                ft.Text("标准" if standard else "Hz", size=9,
                        color=p["text_faint"]),
            ],
        ),
    )


def _about_card(p: dict, width: float, page) -> ft.Container:
    return _card(p, width, [
        _card_title(p, ft.Icons.INFO_OUTLINE_ROUNDED, "关于"),
        _row(p, ft.Icons.NEW_RELEASES_ROUNDED, "版本", f"v{APP_VERSION}"),
        _row(p, ft.Icons.HELP_OUTLINE_ROUNDED, "使用说明",
             on_click=lambda e: page.show_dialog(
                 ft.SnackBar(ft.Text(HELP_TEXT), duration=6000))),
        _row(p, ft.Icons.LINK_ROUNDED, "项目地址", "GitHub",
             on_click=lambda e: page.launch_url(APP_REPO)),
    ])


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
