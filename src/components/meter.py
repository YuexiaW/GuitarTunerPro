"""音分偏差条（参数驱动）：轨道 + 「准了」绿区 + 指针

指针位置由传入的音分算出来（声明式：状态变了就重渲染，不用手工改控件）。
指针以自身尺寸为单位偏移（320 宽量表上 ±50 音分走 ±132px）。
"""

import flet as ft

from app.theme import (
    ACCENT, METER_POINTER_TRAVEL, METER_RANGE, METER_WIDTH,
    pointer_glow,
)
from core.constants import IN_TUNE_CENTS


def cents_meter(p: dict, *, cents: float, color: str,
                width: int = METER_WIDTH) -> ft.Control:
    display = max(-METER_RANGE, min(METER_RANGE, cents))
    pointer = ft.Container(
        width=22, height=22,
        bgcolor=color,
        border_radius=11,
        border=ft.Border.all(2, ft.Colors.WHITE),
        shadow=pointer_glow(color),
        offset=ft.Offset(display / METER_RANGE * METER_POINTER_TRAVEL, 0),
        animate_offset=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
    )
    return ft.Container(
        width=width,
        height=44,
        content=ft.Stack(
            alignment=ft.Alignment.CENTER,
            controls=[
                ft.Container(width=width, height=10, border_radius=5,
                             bgcolor=p["track_bg"]),
                # 「准了」绿区 ±5 音分（量程 ±50 → 32px）
                ft.Container(width=int(width * IN_TUNE_CENTS / METER_RANGE), height=10,
                             border_radius=5, bgcolor=ft.Colors.with_opacity(0.55, ACCENT)),
                ft.Container(width=2, height=22, border_radius=1, bgcolor=p["tick"]),
                pointer,
            ],
        ),
    )
