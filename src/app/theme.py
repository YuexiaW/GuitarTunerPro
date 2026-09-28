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
        chip_bg=ft.Colors.with_opacity(0.08, _WHITE),       # 未选中的琴弦胶囊
        chip_border=ft.Colors.with_opacity(0.18, _WHITE),
        sel_bg=ft.Colors.with_opacity(0.30, _WHITE),        # 选中态
        sel_border=ft.Colors.with_opacity(0.45, _WHITE),
        sel_glow=ft.Colors.with_opacity(0.28, _WHITE),
        track_bg=ft.Colors.with_opacity(0.16, _WHITE),      # 偏差条轨道
        tick=ft.Colors.with_opacity(0.75, _WHITE),          # 正中刻度
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
        chip_bg=ft.Colors.with_opacity(0.45, _WHITE),
        chip_border=ft.Colors.with_opacity(0.55, _WHITE),
        # 浅色下白调高亮区分不出来，选中态改用绿色描边 + 绿色柔光
        sel_bg=ft.Colors.with_opacity(0.90, _WHITE),
        sel_border=ft.Colors.with_opacity(0.55, ACCENT),
        sel_glow=ft.Colors.with_opacity(0.20, ACCENT),
        track_bg=ft.Colors.with_opacity(0.10, _BLACK),
        tick=ft.Colors.with_opacity(0.55, _BLACK),
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
METER_WIDTH = 320             # 偏差条轨道宽度
METER_POINTER_TRAVEL = 5.5    # 指针位移上限（以自身宽度为单位 → ±50 音分 ≈ ±132px）

CONTENT_MAX_WIDTH = 520       # 内容卡片最大宽度（宽窗口下居中限宽，避免横着拉满整屏）
CONTENT_MIN_WIDTH = 280       # 卡片最窄宽度
WINDOW_GUTTER = 40            # 卡片两侧留白

CHIP_ROW_SPACING = 6          # 六弦条的列间距（ResponsiveRow 的 spacing，按 col 自动分宽度）
BOTTOM_BAR_MARGIN = 12        # 底部悬浮条左右安全边距

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

    soft=True 用更淡的底色（提示条 / 琴弦胶囊那种轻薄玻璃）
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
    """底部导航项 / 琴弦胶囊的选中态"""
    if selected:
        return dict(
            bgcolor=p["sel_bg"],
            border=ft.Border.all(1, p["sel_border"]),
            shadow=ft.BoxShadow(blur_radius=14, offset=ft.Offset(0, 0),
                                color=p["sel_glow"]),
        )
    return dict(
        bgcolor=ft.Colors.TRANSPARENT,
        # 透明边占位：选中/未选中宽度一致，过渡才不抖
        border=ft.Border.all(1, ft.Colors.TRANSPARENT),
        shadow=ft.BoxShadow(blur_radius=14, offset=ft.Offset(0, 0),
                            color=ft.Colors.TRANSPARENT),
    )


def chip_style(p: dict, selected: bool) -> dict:
    """琴弦胶囊：未选中也留一层淡玻璃（底色/描边比导航项更轻）"""
    style = item_style(p, selected)
    if not selected:
        style["bgcolor"] = p["chip_bg"]
        style["border"] = ft.Border.all(1, p["chip_border"])
    return style


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
    """内容宽度上限：min(上限, 窗口宽 - 两侧留白) —— 只做「宽屏别拉满」的约束，
    窄屏下横向自适应交给 ResponsiveRow 的 col 分配，不在这里算每个控件的宽度"""
    return max(CONTENT_MIN_WIDTH, min(CONTENT_MAX_WIDTH, window_width(page) - WINDOW_GUTTER))


def bottom_bar_width(page) -> float:
    """底部悬浮条宽度：不超过内容上限，也不超过窗口（给窄屏留出安全区左右各 12）"""
    return min(content_width(page), window_width(page) - 24)
