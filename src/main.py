"""吉他调音器 — 入口

只负责启动。分层：
  app.py        页面组装 + 事件接线（唯一的「总线」）
  theme.py      暗/浅两套调色板 + 毛玻璃配方 + 主题登记表
  state.py      运行期共享状态（TunerState / NavState）
  audio.py      采集服务（桌面 WAV 轮询 / 安卓 on_stream 流式）
  pitch.py      调弦表 + 音分换算 + 一帧 PCM16 → 基频
  components/   参数驱动的叶子控件（顶栏 / 导航条 / 偏差条 / 弦胶囊 / 按钮胶囊）
  pages/        调音页 + 占位页
"""

import flet as ft

from app.app import main

if __name__ == "__main__":
    ft.run(main)
