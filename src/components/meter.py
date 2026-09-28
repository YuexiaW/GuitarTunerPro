"""音分表盘（线性、带刻度；宽度流体）

版式参考目标图：一条水平基线 + 等距刻度（每 5 音分一根、每 25 音分一根长的）
+ 中央容错区（半透明绿胶囊盖住 ±5 音分）+ 一根细竖线指针，两端标 -50 / +50。
刻度骑在基线上（主刻度长、次刻度短）。

**绿区钉在中间、指针自己在走**（两层叠着画，互不影响）：
    轨道层 [左轨道 expand][绿区 expand][右轨道 expand]   权重固定 45 : 10 : 45
    指针层 [左弹簧 expand][细指针 2px][右弹簧 expand]     权重 50±音分
两层都用权重表达位置，所以容器多宽都自己铺满：手机窄、桌面宽都不用改代码，
也不会有「指针只在中间一小段里挪」这种写死像素的老问题。
刻度那条用「刻度 + 弹簧」交替摆（20 个弹簧把刻度摊满），两端正好顶到边。
"""

import flet as ft

from app.theme import ACCENT, METER_MAJOR_EVERY, METER_RANGE, METER_TICK_STEP, pointer_glow
from core.constants import IN_TUNE_CENTS

_UNITS = 10          # 权重份数的放大倍数（expand 只收 int，放大后端点处指针更贴边）
_NEEDLE_W = 2        # 指针宽（细竖线，固定尺寸，不参与权重分配）
_GAUGE_H = 32        # 表盘条带高度（基线在正中间，刻度骑在上面）
_TICK_TALL = 13      # 主刻度长
_TICK_SHORT = 7      # 次刻度长


def cents_meter(p: dict, *, cents: float, color: str) -> ft.Control:
    """音分表盘：cents 正 = 偏高（指针右移），超出量程就贴在端点

    分两层画：
      轨道层 —— [左轨道][绿区][右轨道]，权重固定（45 : 10 : 45），
                **绿区永远钉在正中间**（容错范围就是 ±5 音分，它不该跟着指针跑）；
      指针层 —— [左弹簧][细指针][右弹簧]，权重按音分算（50±音分），指针自己在轨道上走。
    两层都是流体宽度，容器多宽都自己铺满。
    """
    display = max(-METER_RANGE, min(METER_RANGE, cents))
    side_units = round((METER_RANGE - IN_TUNE_CENTS) * _UNITS)   # 绿区两侧各占多少份
    zone_units = round(IN_TUNE_CENTS * 2 * _UNITS)               # 绿区份数（±5 音分 → 10 份）
    left = max(1, round((METER_RANGE + display) * _UNITS))       # 指针左侧份数
    right = max(1, round((METER_RANGE - display) * _UNITS))      # 指针右侧份数
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
    )
    needle = ft.Container(
        width=_NEEDLE_W, height=_GAUGE_H,
        bgcolor=color,
        border_radius=ft.BorderRadius.all(1),
        shadow=pointer_glow(color),
        animate=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
    )

    track = ft.Row(
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[baseline(side_units, first=True), zone, baseline(side_units, first=False)],
    )
    pointer = ft.Row(
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[ft.Container(expand=left), needle, ft.Container(expand=right)],
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
                    # 轨道 + 固定居中的绿区
                    ft.Container(left=0, right=0, top=0, content=track),
                    # 指针：按音分自己在轨道上走
                    ft.Container(left=0, right=0, top=0, content=pointer),
                    # 刻度骑在基线上：上下各留半个主刻度，中心 = 基线
                    ft.Container(left=0, right=0, top=(_GAUGE_H - _TICK_TALL) / 2, content=mark_row),
                ],
            ),
            labels,
        ],
    )
