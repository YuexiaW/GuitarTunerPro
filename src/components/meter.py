"""音分偏差条（参数驱动、流体宽度）：轨道 + 「准了」绿区 + 指针

指针位置由传入的音分算出来（声明式：状态变了就重渲染，不用手工改控件）。

**不写死宽度**：整条就是一个 Row ——
    [左轨道 expand][左半绿区 expand][指针 22px][右半绿区 expand][右轨道 expand]
权重直接取自音分（±50 音分 = 100 份，两侧各 5 份绿区），容器多宽都能自己铺满：
大屏拉宽、手机收窄都不用改代码，也不会再出现「指针只在中间一小段里挪」的问题。

绿区被指针分成左右两半是同轴摆放的：指针停在中间时看上去就是「指针骑在绿区上」。
"""

import flet as ft

from app.theme import ACCENT, METER_RANGE, pointer_glow
from core.constants import IN_TUNE_CENTS

_POINTER = 22                 # 指针直径（固定尺寸，不参与权重分配）


def cents_meter(p: dict, *, cents: float, color: str) -> ft.Control:
    display = max(-METER_RANGE, min(METER_RANGE, cents))
    left = max(1, round(METER_RANGE - IN_TUNE_CENTS + display))    # 左轨道权重
    right = max(1, round(METER_RANGE - IN_TUNE_CENTS - display))   # 右轨道权重
    zone_units = round(IN_TUNE_CENTS)                              # 每侧绿区权重（±5 音分）

    def track(weight: int, radius) -> ft.Container:
        return ft.Container(expand=weight, height=10, bgcolor=p["track_bg"],
                            border_radius=radius)

    zone = ft.Container(expand=zone_units, height=10,
                        bgcolor=ft.Colors.with_opacity(0.55, ACCENT))

    return ft.Row(
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            track(left, ft.BorderRadius.only(top_left=5, bottom_left=5)),
            zone,
            ft.Container(
                width=_POINTER, height=_POINTER,
                bgcolor=color,
                border_radius=_POINTER / 2,
                border=ft.Border.all(2, ft.Colors.WHITE),
                shadow=pointer_glow(color),
                animate_offset=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
            ),
            zone,
            track(right, ft.BorderRadius.only(top_right=5, bottom_right=5)),
        ],
    )
