"""琴头（纯控件拼的，没有美术资源）：圆角琴头体 + 六根弦 + 左右各三个旋钮

高度跟旁边那一列弦钮（`string_buttons.COLUMN_HEIGHT`）一致，
所以左右旋钮与弦钮是同心的一排排，看着像「弦绕在旋钮上」。
"""

import flet as ft

from app.theme import ACCENT

BODY_WIDTH = 104          # 琴头体宽
BODY_RADIUS = 18          # 下缘圆角（上缘做成半圆，像琴头顶端）
PEG_SIZE = 14             # 旋钮直径
PEG_OVERHANG = 7          # 旋钮探出琴头体外多少（看着像拧上去的）
STRING_W = 1.5            # 琴弦线宽
STRING_ROWS = 6           # 六根弦


def headstock(p: dict, *, height: float, row_pitch: float, first_center: float,
              rows: int = 3) -> ft.Stack:
    """琴头

    height       琴头体高度（= 旁边一列弦钮的总高）
    row_pitch    相邻两颗钮的中心距
    first_center 第一颗钮中心到顶边的距离（= 弦钮半径）
    """
    body = ft.Container(
        width=BODY_WIDTH,
        height=height,
        border_radius=ft.BorderRadius.only(
            top_left=BODY_WIDTH / 2, top_right=BODY_WIDTH / 2,
            bottom_left=BODY_RADIUS, bottom_right=BODY_RADIUS,
        ),
        bgcolor=p["surface"],
        border=ft.Border.all(1, p["surface_border"]),
        alignment=ft.Alignment(0, 0),
        content=ft.Row(
            spacing=0,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            controls=[
                ft.Container(width=STRING_W, height=height - 46,
                             bgcolor=ft.Colors.with_opacity(0.38, ACCENT),
                             border_radius=ft.BorderRadius.all(1))
                for _ in range(STRING_ROWS)
            ],
        ),
    )

    controls: list[ft.Control] = [ft.Container(left=PEG_OVERHANG, top=0, content=body)]
    for i in range(rows):
        # 与旁边那列弦钮同心：第 i 颗钮中心 = i × 中心距 + 首颗钮中心
        top = i * row_pitch + first_center - PEG_SIZE / 2
        for on_left in (True, False):
            controls.append(ft.Container(
                width=PEG_SIZE, height=PEG_SIZE,
                border_radius=ft.BorderRadius.all(PEG_SIZE / 2),
                bgcolor=p["surface"] if p["is_dark"] else p["surface_border"],
                border=ft.Border.all(1, ft.Colors.with_opacity(0.30, ACCENT)),
                top=top,
                **({"left": 0} if on_left else {"right": 0}),
            ))

    return ft.Stack(width=BODY_WIDTH + PEG_OVERHANG * 2, height=height, controls=controls)
