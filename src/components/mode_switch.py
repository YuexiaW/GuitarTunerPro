"""识别模式切换：自动识别 / 精准识别（两片胶囊）

它决定下面那排弦钮怎么工作：
  自动识别：不用选弦 —— 按测到的频率自己找最近的那根，弦钮只做「现在听到的是这根」的高亮；
  精准识别：先认准一根弦 —— 偏差只相对它算（点弦钮就是认准它，也会自动切到精准）。

尺寸同样由 `scale`（app.theme.control_scale）推导，和弦钮、采集按钮一套缩放。
"""

import flet as ft

from app.theme import chip_style, selected_text
from core.constants import MODE_AUTO, MODE_PRECISE

BASE_HEIGHT = 34        # 基准胶囊高（scale = 1.0 时）
BASE_GAP = 6            # 两片之间的基准间距

_OPTIONS = (
    (MODE_AUTO, "自动识别", ft.Icons.AUTO_AWESOME, "不用选弦，自己识别你在拨哪根"),
    (MODE_PRECISE, "精准识别", ft.Icons.CENTER_FOCUS_STRONG, "先认准一根弦，偏差只相对它算"),
)


def mode_switch(p: dict, *, mode: str, scale: float, on_pick) -> ft.Row:
    """两片胶囊：on_pick(mode) 交给 services.tuner.set_mode 处理"""
    height = BASE_HEIGHT * scale
    return ft.Row(
        spacing=BASE_GAP * scale,
        tight=True,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            _option(p, key, label, icon, tip, height=height,
                    selected=key == mode, on_pick=on_pick)
            for key, label, icon, tip in _OPTIONS
        ],
    )


def _option(p: dict, key: str, label: str, icon, tip: str, *,
            height: float, selected: bool, on_pick) -> ft.Container:
    """一片胶囊：图标 + 文字，选中 = 主色描边/底 + 绿字"""
    return ft.Container(
        height=height,
        border_radius=ft.BorderRadius.all(height / 2),
        padding=ft.Padding.symmetric(horizontal=height * 0.42),
        **chip_style(p, selected),
        alignment=ft.Alignment(0, 0),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        ink=True,
        tooltip=tip,
        on_click=lambda e, k=key: on_pick(k),
        content=ft.Row(
            spacing=height * 0.18,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=height * 0.46,
                        color=selected_text(p, selected, p["text_dim"])),
                ft.Text(label, size=height * 0.38, no_wrap=True,
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
                        color=selected_text(p, selected)),
            ],
        ),
    )
