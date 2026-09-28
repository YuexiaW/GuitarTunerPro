"""琴头（纯控件拼的，没有美术资源）：圆角琴头体 + 六根弦 + 左右各三个旋钮

**尺寸不写死**：只收一个 `height`（= 旁边那一列弦钮的总高），
琴头体宽、旋钮、弦线、留白全部按比例从这个高度算出来 —— 高度一变整体跟着缩放。
高度与弦钮列一致，所以左右旋钮与弦钮同心，看着像「弦绕在旋钮上」。
六根弦按真实弦径做粗细分档（6 弦最粗、1 弦最细），从左到右依次变细。
"""

import flet as ft

from app.theme import ACCENT

# 以下都是「相对高度」的比例（基准：高 154 → 宽 104 那一版）
BODY_RATIO = 104 / 154        # 琴头体宽 : 高
BODY_RADIUS_RATIO = 18 / 154  # 下缘圆角（上缘做成半圆，像琴头顶端）
PEG_RATIO = 14 / 154          # 旋钮直径
OVERHANG_RATIO = 7 / 154      # 旋钮探出琴头体外多少（看着像拧上去的）
INSET_RATIO = 46 / 154        # 弦线上下各留的空白
# 六根弦的线宽：6 弦（E2）最粗 → 1 弦（E4）最细，比例参考真实弦径
STRING_RATIOS = (2.8 / 154, 2.4 / 154, 2.0 / 154, 1.6 / 154, 1.2 / 154, 0.9 / 154)


def headstock(p: dict, *, height: float, row_pitch: float, first_center: float,
              rows: int = 3) -> ft.Stack:
    """琴头

    height       琴头体高度（= 旁边一列弦钮的总高），其余尺寸按比例推导
    row_pitch    相邻两颗钮的中心距
    first_center 第一颗钮中心到顶边的距离（= 弦钮半径）
    """
    body_w = height * BODY_RATIO
    peg = height * PEG_RATIO
    overhang = height * OVERHANG_RATIO
    body = ft.Container(
        width=body_w,
        height=height,
        border_radius=ft.BorderRadius.only(
            top_left=body_w / 2, top_right=body_w / 2,
            bottom_left=height * BODY_RADIUS_RATIO, bottom_right=height * BODY_RADIUS_RATIO,
        ),
        bgcolor=p["surface"],
        border=ft.Border.all(1, p["surface_border"]),
        alignment=ft.Alignment(0, 0),
        content=ft.Row(
            spacing=0,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            controls=[
                ft.Container(width=height * ratio,
                             height=height - height * INSET_RATIO * 2,
                             bgcolor=ft.Colors.with_opacity(0.38, ACCENT),
                             border_radius=ft.BorderRadius.all(height * ratio / 2))
                for ratio in STRING_RATIOS
            ],
        ),
    )

    controls: list[ft.Control] = [ft.Container(left=overhang, top=0, content=body)]
    for i in range(rows):
        # 与旁边那列弦钮同心：第 i 颗钮中心 = i × 中心距 + 首颗钮中心
        top = i * row_pitch + first_center - peg / 2
        for on_left in (True, False):
            controls.append(ft.Container(
                width=peg, height=peg,
                border_radius=ft.BorderRadius.all(peg / 2),
                bgcolor=p["surface"] if p["is_dark"] else p["surface_border"],
                border=ft.Border.all(1, ft.Colors.with_opacity(0.30, ACCENT)),
                top=top,
                **({"left": 0} if on_left else {"right": 0}),
            ))

    return ft.Stack(width=body_w + overhang * 2, height=height, controls=controls)
