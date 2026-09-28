"""app.theme —— UI 主题：暗/浅两套调色板 + 毛玻璃配方 + 尺寸常量

状态层（models.state.ThemeState）只存主题名，取色用这里的 palette_of(name)；
声明式组件按参数订阅状态，主题一变就自己重渲染，没有「登记表刷属性」那套东西了。

布局与配方取自 MiluMusic/tests/appbar_nav.py：渐变底 + 模糊光斑 + 毛玻璃卡片。
"""

import flet as ft

# --- 点缀色（两套主题通用） ---
ACCENT = "#3DD68C"
BAD = "#FF6B6B"
WARN = "#FFB020"

_WHITE = ft.Colors.WHITE
_BLACK = ft.Colors.BLACK

PALETTES = {
    "dark": dict(
        is_dark=True,
        gradient=["#06120F", "#0A0A14", "#0C1A24"],
        blobs=[("#3DD68C", 0.22), ("#0EA5E9", 0.18), ("#7C3AED", 0.14)],
        glass_alpha=0.16,                                   # 玻璃底色（白 tint）
        glass_alpha_soft=0.10,                              # 提示条/胶囊那种更淡的玻璃
        glass_border=ft.Colors.with_opacity(0.35, _WHITE),  # 玻璃高光边
        glass_shadow=ft.Colors.with_opacity(0.35, _BLACK),  # 玻璃投影
        text=_WHITE,
        text_dim=ft.Colors.with_opacity(0.72, _WHITE),
        text_faint=ft.Colors.with_opacity(0.55, _WHITE),
        appbar_bg=ft.Colors.with_opacity(0.45, _BLACK),
        appbar_fg=_WHITE,
        chip_bg=ft.Colors.TRANSPARENT,                      # 平铺胶囊：不填色，只描边
        chip_border=ft.Colors.with_opacity(0.22, _WHITE),
        sel_bg=ft.Colors.with_opacity(0.16, ACCENT),        # 选中态：绿点缀的淡色块
        sel_border=ft.Colors.with_opacity(0.70, ACCENT),
        sel_text=ACCENT,
        line=ft.Colors.with_opacity(0.12, _WHITE),          # 分隔细线
        avatar_bg=ft.Colors.with_opacity(0.30, _BLACK),      # 头像内圈（平铺，不模糊）
        surface="#161B22",                                   # 实心卡片底（不透明，不是毛玻璃）
        surface_border=ft.Colors.with_opacity(0.10, _WHITE),
        track_bg=ft.Colors.with_opacity(0.16, _WHITE),      # 偏差条轨道
        stop_bg=ft.Colors.with_opacity(0.18, _WHITE),
        stop_fg=_WHITE,
    ),
    "light": dict(
        is_dark=False,
        gradient=["#F2FBF6", "#F5F5F7", "#E8F1FA"],
        blobs=[("#3DD68C", 0.30), ("#38BDF8", 0.24), ("#A78BFA", 0.22)],
        glass_alpha=0.55,
        glass_alpha_soft=0.40,
        glass_border=ft.Colors.with_opacity(0.65, _WHITE),
        glass_shadow=ft.Colors.with_opacity(0.10, _BLACK),
        text="#1A1A1A",
        text_dim=ft.Colors.with_opacity(0.62, _BLACK),
        text_faint=ft.Colors.with_opacity(0.45, _BLACK),
        appbar_bg=ft.Colors.with_opacity(0.55, _WHITE),
        appbar_fg="#1A1A1A",
        chip_bg=ft.Colors.TRANSPARENT,
        chip_border=ft.Colors.with_opacity(0.18, _BLACK),
        sel_bg=ft.Colors.with_opacity(0.16, ACCENT),
        sel_border=ft.Colors.with_opacity(0.70, ACCENT),
        sel_text="#0F8A56",                                 # 浅色底下绿字要压深才看得清
        line=ft.Colors.with_opacity(0.12, _BLACK),
        avatar_bg=ft.Colors.with_opacity(0.55, _WHITE),
        surface=_WHITE,                                      # 参考图里的白卡
        surface_border=ft.Colors.with_opacity(0.08, _BLACK),
        track_bg=ft.Colors.with_opacity(0.10, _BLACK),
        stop_bg=ft.Colors.with_opacity(0.06, _BLACK),
        stop_fg="#1A1A1A",
    ),
}

# ============================================================
# 尺寸 / 行为常量（用户说「再大一点 / 改回去」时一行能改）
# ============================================================
BOTTOM_RESERVE = 200          # 底部悬浮层预留高度：内容滚到底不被玻璃压住
CONTROL_PILL_BOTTOM = 72      # 按钮胶囊贴底偏移（叠在导航条上方，随导航条高度收小）

METER_RANGE = 50.0            # 偏差条量程 ±50 音分

CONTENT_MAX_WIDTH = 1080      # 内容区上限：宽屏把宽度用起来，不缩成窄窄一条
CONTENT_MIN_WIDTH = 280       # 内容区最窄宽度
WINDOW_GUTTER = 40            # 宽屏时内容两侧留白
WINDOW_GUTTER_SMALL = 24      # 窄屏（<600）时留白收窄，别浪费手机宽度

BAR_MAX_WIDTH = 560           # 底部悬浮条上限：导航条不跟着大屏拉满

CHIP_ROW_SPACING = 6          # 六弦条的列间距（ResponsiveRow 的 spacing，按 col 自动分宽度）
BOTTOM_BAR_MARGIN = 12        # 底部悬浮条左右安全边距

# 断点别名（ResponsiveRow 的 col 用；手机单列、平板/桌面分栏都靠它）
COL_FULL = {"xs": 12}
COL_HALF = {"xs": 12, "md": 6}
COL_WIDE = {"xs": 12, "md": 7, "lg": 8}
COL_NARROW = {"xs": 12, "md": 5, "lg": 4}
COL_PHONE_3 = {"xs": 4, "sm": 2}      # 手机上每行 3 个，≥576 每行 6 个

# 背景光斑的几何（位置/大小固定，颜色与透明度跟着调色板走）
BLOB_SPEC = [
    (360, dict(left=-90, top=-70)),
    (460, dict(right=-140, top=150)),
    (400, dict(left=160, bottom=-150)),
]


# ============================================================
# 取色 / 配方
# ============================================================
def palette_of(name: str) -> dict:
    """主题名 → 调色板（状态层只存名字，取色留在 UI 层，models 不用反向依赖 app）"""
    return PALETTES[name]


def blobs(p: dict) -> list[ft.Container]:
    """背景光斑：内容滑过悬浮玻璃时背后颜色会变，玻璃才看得出来"""
    return [
        ft.Container(
            width=size, height=size,
            border_radius=ft.BorderRadius.all(size / 2),
            bgcolor=color,
            blur=ft.Blur(60, 60),
            opacity=opacity,
            **pos,
        )
        for (color, opacity), (size, pos) in zip(p["blobs"], BLOB_SPEC)
    ]


def glass(p: dict, radius: int = 24, soft: bool = False) -> dict:
    """毛玻璃：半透明底 + BackdropFilter + 高光边 + 投影

    **只给底部悬浮层用**（导航条、它上面的控制胶囊）—— 用户明确说过毛玻璃只是导航栏的设计，
    页面内容一律平铺在渐变底上，不要拿这个把整页内容包成一堆透明框。
    soft=True 用更淡的底色。
    """
    return dict(
        bgcolor=ft.Colors.with_opacity(
            p["glass_alpha_soft"] if soft else p["glass_alpha"], _WHITE
        ),
        blur=ft.Blur(24, 24),
        border_radius=ft.BorderRadius.all(radius),
        border=ft.Border.all(1, p["glass_border"]),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=24,
            color=p["glass_shadow"],
            offset=ft.Offset(0, 6),
        ),
    )


def item_style(p: dict, selected: bool) -> dict:
    """选中态：绿点缀的淡色块 + 绿描边（平铺，不带玻璃/投影）"""
    if selected:
        return dict(
            bgcolor=p["sel_bg"],
            border=ft.Border.all(1, p["sel_border"]),
        )
    # 透明边占位：选中/未选中宽度一致，过渡才不抖
    return dict(
        bgcolor=ft.Colors.TRANSPARENT,
        border=ft.Border.all(1, ft.Colors.TRANSPARENT),
    )


def chip_style(p: dict, selected: bool) -> dict:
    """平铺胶囊（弦名 / 参考音）：未选中只描一圈细边，不填色"""
    if selected:
        return item_style(p, True)
    return dict(
        bgcolor=p["chip_bg"],
        border=ft.Border.all(1, p["chip_border"]),
    )


def selected_text(p: dict, selected: bool, default: str | None = None) -> str:
    """胶囊文字色：选中用绿点缀，未选中给默认色"""
    return p["sel_text"] if selected else (default or p["text"])


def card(p: dict, radius: int = 20, padding=(16, 16)) -> dict:
    """实心卡片：**不透明**底 + 一圈细描边，没有模糊/投影（不是毛玻璃那种透明框）

    深色主题是近黑的实色块，浅色主题是白块 —— 对应参考图里「浅灰底 + 白卡」的层次。
    """
    return dict(
        bgcolor=p["surface"],
        border_radius=ft.BorderRadius.all(radius),
        border=ft.Border.all(1, p["surface_border"]),
        padding=ft.Padding.symmetric(vertical=padding[0], horizontal=padding[1]),
    )


def hairline(p: dict, width=None) -> ft.Container:
    """细分隔线：行与行、分节之间用它，比卡片描边更淡"""
    return ft.Container(height=1, width=width, bgcolor=p["line"])


def pointer_glow(color: str) -> ft.BoxShadow:
    """偏差条指针的柔光"""
    return ft.BoxShadow(blur_radius=16, offset=ft.Offset(0, 0),
                        color=ft.Colors.with_opacity(0.55, color))


def window_width(page) -> float:
    """窗口宽度；拿不到（早期/移动端首帧）时按默认窗口给"""
    try:
        w = page.window.width
    except Exception:
        w = None
    if not w or w < 240:
        return CONTENT_MAX_WIDTH + WINDOW_GUTTER
    return float(w)


def content_width(page) -> float:
    """内容区宽度：窗口宽 - 两侧留白（窄屏留白收窄），上限 CONTENT_MAX_WIDTH。

    这里只决定「容器多宽」；页面内部按 ResponsiveRow 断点回流（手机单列、宽屏分栏），
    所以大屏是把宽度用起来，不是缩成中间一条。
    """
    avail = window_width(page)
    gutter = WINDOW_GUTTER if avail >= 600 else WINDOW_GUTTER_SMALL
    return max(CONTENT_MIN_WIDTH, min(CONTENT_MAX_WIDTH, avail - gutter))


def bottom_bar_width(page) -> float:
    """底部悬浮条宽度：导航条不跟着大屏拉满（上限 BAR_MAX_WIDTH），窄屏随窗口"""
    return min(BAR_MAX_WIDTH, content_width(page), window_width(page) - 24)
