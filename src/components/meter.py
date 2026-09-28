"""音分表盘（线性、带刻度；宽度流体）

版式参考目标图：一条水平基线 + 等距刻度（每 5 音分一根、每 25 音分一根长的）
+ 中央准音区（半透明绿胶囊盖住 ±5 音分）+ 一根细竖线指针，两端标 -50 / +50。
刻度骑在基线上（主刻度长、次刻度短），指针随音分左右走。

**不写死宽度**：指针位置由权重决定 ——
    [左轨道 expand][左半绿区 expand][指针 2px][右半绿区 expand][右轨道 expand]
（±50 音分 = 100 份，两侧各 5 份绿区），容器多宽都自己铺满：手机窄、桌面宽都不用改代码。
刻度那条用「刻度 + 弹簧」交替摆（20 个弹簧把刻度摊满），两端正好顶到边。
"""

import flet as ft

from app.theme import ACCENT, METER_MAJOR_EVERY, METER_RANGE, METER_TICK_STEP, pointer_glow
from core.constants import IN_TUNE_CENTS

_NEEDLE_W = 2        # 指针宽（细竖线，固定尺寸，不参与权重分配）
_GAUGE_H = 32        # 表盘条带高度（基线在正中间，刻度骑在上面）
_TICK_TALL = 13      # 主刻度长
_TICK_SHORT = 7      # 次刻度长


def cents_meter(p: dict, *, cents: float, color: str) -> ft.Control:
    """音分表盘：cents 正 = 偏高（指针右移），超出量程就贴在端点"""
    display = max(-METER_RANGE, min(METER_RANGE, cents))
    left = max(1, round(METER_RANGE - IN_TUNE_CENTS + display))    # 左轨道权重
    right = max(1, round(METER_RANGE - IN_TUNE_CENTS - display))   # 右轨道权重
    zone_units = round(IN_TUNE_CENTS)                              # 每侧绿区权重（±5 音分）
    tick_count = int(round(2 * METER_RANGE / METER_TICK_STEP)) + 1

    def baseline(weight: int, *, first: bool) -> ft.Container:
        radius = (ft.BorderRadius.only(top_left=1, bottom_left=1) if first
                  else ft.BorderRadius.only(top_right=1, bottom_right=1))
        return ft.Container(
            expand=weight,
            content=ft.Row(controls=[
                ft.Container(height=2, expand=True, bgcolor=p["track_bg"], border_radius=radius)
            ]),
        )

    zone = ft.Container(
        expand=zone_units, height=16,
        bgcolor=ft.Colors.with_opacity(0.34, ACCENT),
        border_radius=ft.BorderRadius.all(8),
        animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
    )
    needle = ft.Container(
        width=_NEEDLE_W, height=_GAUGE_H,
        bgcolor=color,
        border_radius=ft.BorderRadius.all(1),
        shadow=pointer_glow(color),
        animate=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
    )
    gauge = ft.Row(
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[baseline(left, first=True), zone, needle, zone, baseline(right, first=False)],
    )

    marks: list[ft.Control] = []
    for i in range(tick_count):
        if i:
            marks.append(ft.Container(expand=1))        # 弹簧：把刻度摊到整条上
        major = i % METER_MAJOR_EVERY == 0
        marks.append(ft.Container(
            width=2,
            height=_TICK_TALL if major else _TICK_SHORT,
            bgcolor=p["text_faint"] if major else p["track_bg"],
            border_radius=ft.BorderRadius.all(1),
        ))
    mark_row = ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=marks)

    labels = ft.Row(
        spacing=0,
        controls=[
            ft.Container(expand=1, alignment=ft.Alignment(-1, 0),
                         content=ft.Text(f"-{METER_RANGE:g}", size=9, color=p["text_faint"])),
            ft.Container(expand=1, alignment=ft.Alignment(0, 0),
                         content=ft.Text("0", size=9, color=p["text_faint"])),
            ft.Container(expand=1, alignment=ft.Alignment(1, 0),
                         content=ft.Text(f"+{METER_RANGE:g}", size=9, color=p["text_faint"])),
        ],
    )

    return ft.Column(
        spacing=2,
        tight=True,
        controls=[
            ft.Stack(
                height=_GAUGE_H,
                controls=[
                    ft.Container(left=0, right=0, top=0, content=gauge),
                    # 刻度骑在基线上：上下各留半个主刻度，中心 = 基线
                    ft.Container(left=0, right=0, top=(_GAUGE_H - _TICK_TALL) / 2, content=mark_row),
                ],
            ),
            labels,
        ],
    )
