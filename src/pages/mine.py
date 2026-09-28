"""我的页（骨架对齐用户给的目标效果图）

    头像 / 昵称 / 编辑个人资料 → 数据行 → 主行动卡 → 快捷入口四宫格 → 单行入口 → 设置列表
条目**全部换成吉他调音器自己的东西**，不照搬参考图里的会员计划 / 兑换码 / 粉丝关注那类条目。

- 宽屏（md 起）左「身份 + 数据 + 主行动」、右「快捷入口 + 设置」两栏；手机单列
- 数据行是真实计数（services 里累加），不是写死的假数据
- 主题切换不在这里 —— 全应用只在 components/app_bar.py，这里只 palette_of(theme.name) 取色
  （订阅靠参数：MinePage 是零参入口，把状态传给内层 _Mine。）
"""

import flet as ft

from app.theme import (
    ACCENT,
    CHIP_ROW_SPACING,
    COL_NARROW,
    COL_WIDE,
    card,
    chip_style,
    content_width,
    hairline,
    palette_of,
    selected_text,
)
from components.nav_dock import NAV_ITEMS
from core.constants import (
    APP_REPO,
    APP_VERSION,
    A4_OPTIONS,
    A4_STANDARD,
    AVATAR_CHOICES,
    HELP_TEXT,
    NICKNAME_MAX,
    ROUTE_TUNER,
)
from models.settings import SettingsState, settings_state
from models.state import ThemeState, theme_state
from services.tuner import go

A4_COL = {"xs": 4}              # 参考音候选：对话框里每行 3 个
AVATAR_COL = {"xs": 4}          # 头像候选：每行 3 个
STAT_COL = {"xs": 4}            # 数据行：三等分
SHORTCUT_COL = {"xs": 3}        # 快捷入口：四等分


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
        spacing=16,
        tight=True,
        width=col_w,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.ResponsiveRow(
                spacing=16,
                run_spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(col=COL_NARROW, content=ft.Column(
                        spacing=16, tight=True,
                        controls=[
                            # 左让 16px：和下面卡片里的图标对齐，别贴着内容区左边缘
                            ft.Container(padding=ft.Padding.only(left=16),
                                         content=_identity(p, settings, page)),
                            _stats(p, settings),
                            _cta(p, page),
                        ],
                    )),
                    ft.Container(col=COL_WIDE, content=ft.Column(
                        spacing=16, tight=True,
                        controls=[
                            _shortcuts(p, settings, page),
                            _tip(p, page),
                            _settings(p, settings, page),
                        ],
                    )),
                ],
            ),
        ],
    )


# ============================================================
# 身份区：头像框 + 昵称 + 编辑入口
# ============================================================
def _identity(p: dict, settings: SettingsState, page) -> ft.Row:
    ring = ft.Container(
        width=64, height=64,
        border_radius=ft.BorderRadius.all(32),
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
            border_radius=ft.BorderRadius.all(29),
            alignment=ft.Alignment(0, 0),
            content=ft.Text(settings.avatar, size=26),
        ),
    )
    return ft.Row(
        spacing=16,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ring,
            ft.Container(
                ink=True,
                border_radius=ft.BorderRadius.all(12),
                padding=ft.Padding.symmetric(vertical=4, horizontal=6),
                tooltip="改昵称",
                on_click=lambda e: _edit_nickname(page, p, settings),
                content=ft.Column(
                    spacing=4, tight=True,
                    controls=[
                        ft.Text(settings.nickname, size=20, weight=ft.FontWeight.W_600,
                                color=p["text"], no_wrap=True),
                        ft.Text("编辑个人资料", size=11, color=p["text_faint"]),
                    ],
                ),
            ),
        ],
    )


# ============================================================
# 数据行：真实计数（点开始调音 / 跨进绿区 / 首次使用至今）
# ============================================================
def _stats(p: dict, settings: SettingsState) -> ft.Container:
    items = (
        ("调音次数", str(settings.sessions)),
        ("调准次数", str(settings.in_tune_hits)),
        ("使用天数", str(settings.days_used())),
    )
    return ft.Container(
        **card(p, 20, padding=(14, 8)),
        content=ft.ResponsiveRow(
            spacing=6,
            run_spacing=6,
            controls=[
                ft.Container(
                    col=STAT_COL,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        spacing=0, tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(value, size=20, weight=ft.FontWeight.W_600, color=p["text"]),
                            ft.Text(label, size=10, color=p["text_faint"]),
                        ],
                    ),
                )
                for label, value in items
            ],
        ),
    )


# ============================================================
# 主行动卡：去调音
# ============================================================
def _cta(p: dict, page) -> ft.Container:
    badge = ft.Container(
        width=40, height=40,
        border_radius=ft.BorderRadius.all(14),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
            colors=[ACCENT, "#0EA5E9"],
        ),
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=22, color=ft.Colors.WHITE),
    )
    return ft.Container(
        **card(p, 20),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                badge,
                ft.Column(
                    spacing=2, tight=True, expand=True,
                    controls=[
                        ft.Text("开始调音", size=15, weight=ft.FontWeight.W_600, color=p["text"]),
                        ft.Text("打开麦克风，实时看音高与音分偏差",
                                size=11, color=p["text_faint"]),
                    ],
                ),
                ft.Button(
                    "去调音",
                    height=36,
                    bgcolor=ACCENT,
                    color="#04231A",
                    on_click=lambda e: go(page, ROUTE_TUNER, page.route),
                ),
            ],
        ),
    )


# ============================================================
# 快捷入口四宫格 + 单行入口
# ============================================================
def _shortcuts(p: dict, settings: SettingsState, page) -> ft.Container:
    cells = [
        _shortcut(p, label, icon, lambda e, r=route: go(page, r, page.route))
        for route, label, icon, _desc in NAV_ITEMS[:3]      # 调音 / 节拍器 / 和弦
    ]
    cells.append(_shortcut(p, "参考音", ft.Icons.GRAPHIC_EQ_ROUNDED,
                           lambda e: _pick_a4(page, p, settings)))
    return ft.Container(
        **card(p, 20, padding=(12, 8)),
        content=ft.ResponsiveRow(spacing=6, run_spacing=6, controls=cells),
    )


def _shortcut(p: dict, label: str, icon: str, on_click) -> ft.Container:
    return ft.Container(
        col=SHORTCUT_COL,
        ink=True,
        border_radius=ft.BorderRadius.all(16),
        padding=ft.Padding.symmetric(vertical=12, horizontal=4),
        tooltip=label,
        on_click=on_click,
        content=ft.Column(
            spacing=6, tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=22, color=ACCENT),
                ft.Text(label, size=11, color=p["text_dim"], no_wrap=True),
            ],
        ),
    )


def _tip(p: dict, page) -> ft.Container:
    return ft.Container(
        **card(p, 20, padding=(6, 8)),
        content=_row(p, ft.Icons.HELP_OUTLINE_ROUNDED, "使用说明",
                     on_click=lambda e: page.show_dialog(
                         ft.SnackBar(ft.Text(HELP_TEXT), duration=6000))),
    )


# ============================================================
# 设置列表：行间细线 + 右箭头
# ============================================================
def _settings(p: dict, settings: SettingsState, page) -> ft.Container:
    rows = [
        _row(p, ft.Icons.GRAPHIC_EQ_ROUNDED, "参考音 A4", f"{settings.a4:g} Hz",
             on_click=lambda e: _pick_a4(page, p, settings)),
        _row(p, ft.Icons.LINK_ROUNDED, "项目地址", "GitHub", on_click=_open_repo),
        _row(p, ft.Icons.NEW_RELEASES_ROUNDED, "版本", f"v{APP_VERSION}"),
    ]
    controls: list = []
    for i, row in enumerate(rows):
        if i:
            controls.append(hairline(p))        # 行与行之间一条细线
        controls.append(row)
    return ft.Container(
        **card(p, 20, padding=(6, 8)),
        content=ft.Column(spacing=0, tight=True, controls=controls),
    )


def _row(p: dict, icon: str, label: str, value: str = "", on_click=None) -> ft.Container:
    """一行「彩色圆角图标 + 标题 + 右值 + 箭头」（可点的带水波）"""
    tappable = on_click is not None
    return ft.Container(
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=34, height=34,
                    border_radius=ft.BorderRadius.all(12),
                    bgcolor=p["sel_bg"],
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icon, size=18, color=ACCENT),
                ),
                ft.Text(label, size=14, color=p["text"], expand=True),
                ft.Text(value, size=12, color=p["text_faint"]),
                ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16,
                        color=p["text_faint"], visible=tappable),
            ],
        ),
        padding=ft.Padding.symmetric(vertical=8, horizontal=4),
        border_radius=ft.BorderRadius.all(12),
        ink=tappable,
        on_click=on_click,
    )


# ============================================================
# 对话框：改昵称 / 换头像 / 换参考音
# ============================================================
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


def _pick_a4(page, p: dict, settings: SettingsState):
    def pick(e, value: float):
        settings.set_a4(value)
        page.pop_dialog()

    options = [
        ft.Container(
            col=A4_COL,
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding.symmetric(vertical=8, horizontal=4),
            border_radius=ft.BorderRadius.all(16),
            ink=True,
            on_click=lambda e, v=value: pick(e, v),
            **chip_style(p, abs(value - settings.a4) < 0.01),
            content=ft.Column(
                spacing=0, tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(f"{value:g}", size=14,
                            weight=ft.FontWeight.W_600 if abs(value - settings.a4) < 0.01
                            else ft.FontWeight.W_400,
                            color=selected_text(p, abs(value - settings.a4) < 0.01)),
                    ft.Text("标准" if abs(value - A4_STANDARD) < 0.01 else "Hz",
                            size=9, color=p["text_faint"]),
                ],
            ),
        )
        for value in A4_OPTIONS
    ]
    page.show_dialog(ft.AlertDialog(
        title=ft.Text("参考音 A4", size=16),
        content=ft.Column(
            spacing=12, tight=True,
            controls=[
                ft.ResponsiveRow(spacing=CHIP_ROW_SPACING, run_spacing=CHIP_ROW_SPACING,
                                 controls=options),
                ft.Text("调音时按这个 A4 换算每根弦的目标频率：440 Hz 是标准音高，"
                        "442/435 给合奏，432/415 用于老录音与古典音高。",
                        size=11, color=p["text_faint"]),
            ],
        ),
        actions=[ft.TextButton("取消", on_click=lambda e: page.pop_dialog())],
        actions_alignment=ft.MainAxisAlignment.END,
    ))


async def _open_repo(e):
    """打开项目地址：0.90 起 page.launch_url 废弃，改用 UrlLauncher（协程，必须 await）"""
    await ft.UrlLauncher().launch_url(APP_REPO)
