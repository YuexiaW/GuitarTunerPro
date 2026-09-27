"""最小录音验证程序：只做"录到文件"这件事，用来看麦克风采集是否正常。

运行：
    uv run flet run recorder_test.py          # 手动点按钮
    TUNER_AUTOREC=6 uv run flet run recorder_test.py   # 启动后自动录 6 秒再停（自检用）

录音文件落在项目下的 recordings/ 目录，保存后可直接用播放器打开试听。
"""

import asyncio
import os
import time

import flet as ft
import flet_audio_recorder as far

# --- 参数 ---
SAMPLE_RATE = 16000          # 16kHz 单声道足够调音用；想听音质可改 44100
CHANNELS = 1
POLL_INTERVAL = 0.2          # 实时显示文件大小的轮询间隔
REC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "recordings")
REC_DIR = os.path.abspath(REC_DIR)


def main(page: ft.Page):
    page.title = "🎙️ 录音自检"
    page.padding = 30
    page.window.width = 520
    page.window.height = 560
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    os.makedirs(REC_DIR, exist_ok=True)

    title = ft.Text("🎙️ 录音自检", size=26, weight=ft.FontWeight.BOLD)
    hint = ft.Text("点「开始录音」随便说句话/弹几下，再点「停止保存」", size=13,
                   color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
    state_text = ft.Text("待机中", size=20, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700)
    live_text = ft.Text("--", size=15, color=ft.Colors.BLUE)
    result_text = ft.Text("", size=13, color=ft.Colors.GREY_800, selectable=True,
                          text_align=ft.TextAlign.CENTER)

    recorder = far.AudioRecorder()

    state = {"running": False, "path": None, "started": 0.0}

    level_bar = ft.Container(width=2, height=14, bgcolor=ft.Colors.GREY_400, border_radius=3,
                            animate=ft.Animation(90, ft.AnimationCurve.EASE_OUT))
    level_meter = ft.Container(
        width=380, height=14, bgcolor=ft.Colors.GREY_300, border_radius=3,
        content=ft.Row([level_bar], alignment=ft.MainAxisAlignment.START),
    )
    level_text = ft.Text("电平 峰值 -- dBFS", size=12, color=ft.Colors.GREY_600)

    def refresh_level(bar_w: float, peak_dbfs: float, rms_dbfs: float):
        level_bar.width = max(2.0, bar_w)
        level_bar.bgcolor = (ft.Colors.GREEN if peak_dbfs > -20
                             else ft.Colors.ORANGE if peak_dbfs > -40
                             else ft.Colors.GREY_400)
        level_text.value = f"电平 峰值 {peak_dbfs:.1f} dBFS　有效值 {rms_dbfs:.1f} dBFS"

    def show_snack(message: str):
        page.show_dialog(ft.SnackBar(content=ft.Text(message), duration=ft.Duration(seconds=4)))

    async def live_loop():
        """边录边读新写入的 PCM：显示文件增长 + 实时电平（确认麦克风真的在采声音）"""
        import numpy as np

        offset = None
        consumed = 0
        peak_hold = 0.0
        while state["running"]:
            path = state["path"]
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0

            # 定位 WAV data 块（跳过 44 字节头）
            if offset is None and size >= 44:
                try:
                    with open(path, "rb") as f:
                        head = f.read(512)
                    if head[:4] == b"RIFF":
                        idx = head.find(b"data")
                        offset = idx + 8 if idx >= 0 else 44
                except OSError:
                    offset = None
            elif offset is not None and size > offset + consumed:
                try:
                    with open(path, "rb") as f:
                        f.seek(offset + consumed)
                        raw = f.read(size - offset - consumed)
                except OSError:
                    raw = b""
                consumed += len(raw)
                if raw:
                    samples = np.frombuffer(raw[:len(raw) // 2 * 2], dtype=np.int16).astype(np.float32)
                    if samples.size:
                        peak = float(np.abs(samples).max()) / 32768.0
                        rms = float(np.sqrt(np.mean(samples ** 2))) / 32768.0
                        peak_hold = max(peak, peak_hold * 0.9)
                        bar_w = min(1.0, peak_hold / 0.5) * 376
                        refresh_level(bar_w, 20 * (np.log10(peak_hold) if peak_hold > 1e-6 else -6),
                                      20 * (np.log10(rms) if rms > 1e-6 else -6))
                        print(f"[rec] rms={rms:.5f} peak={peak:.5f} size={size}", flush=True)

            elapsed = time.time() - state["started"]
            live_text.value = f"已录 {elapsed:4.1f} s　文件 {size / 1024:7.1f} KB"
            page.update()
            await asyncio.sleep(POLL_INTERVAL)

    async def start_recording(e=None):
        if state["running"]:
            return

        granted = await recorder.has_permission()
        if not granted:
            state_text.value = "❌ 没有麦克风权限"
            state_text.color = ft.Colors.RED
            page.update()
            show_snack("系统未授予麦克风权限，请在 Windows 设置里允许桌面应用使用麦克风")
            return

        path = os.path.join(REC_DIR, time.strftime("rec_%Y%m%d_%H%M%S.wav"))
        state["path"] = path
        state["started"] = time.time()
        result_text.value = ""

        try:
            ok = await recorder.start_recording(
                output_path=path,
                configuration=far.AudioRecorderConfiguration(
                    encoder=far.AudioEncoder.WAV,
                    sample_rate=SAMPLE_RATE,
                    channels=CHANNELS,
                ),
            )
        except Exception as ex:
            ok = False
            print(f"[rec] start_recording 异常: {ex}", flush=True)

        if not ok:
            state_text.value = "❌ 启动录音失败"
            state_text.color = ft.Colors.RED
            page.update()
            show_snack("启动录音失败（麦克风可能被其它程序占用）")
            return

        state["running"] = True
        state_text.value = "🔴 录音中…"
        state_text.color = ft.Colors.RED
        page.update()
        page.run_task(live_loop)
        print(f"[rec] 开始录音 -> {path}", flush=True)

    async def stop_recording(e=None):
        if not state["running"]:
            return
        state["running"] = False
        try:
            await recorder.stop_recording()
        except Exception as ex:
            print(f"[rec] stop_recording 异常: {ex}", flush=True)

        path = state["path"]
        await asyncio.sleep(0.3)          # 等客户端把最后一块刷盘
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        elapsed = time.time() - state["started"]

        state_text.value = "⏹️ 已停止"
        state_text.color = ft.Colors.GREEN if size > 1024 else ft.Colors.RED
        live_text.value = f"时长 {elapsed:.1f} s　文件 {size / 1024:.1f} KB"
        if size > 1024:
            result_text.value = f"已保存：{path}\n（点「打开文件夹」试听）"
        else:
            result_text.value = "文件几乎没有内容，说明麦克风没采到声音。"
        page.update()
        print(f"[rec] 停止录音 size={size} elapsed={elapsed:.1f}", flush=True)

    def open_folder(e=None):
        if os.path.isdir(REC_DIR):
            os.startfile(REC_DIR)

    page.add(
        ft.SafeArea(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    title,
                    hint,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Container(
                        content=ft.Column([state_text, live_text, level_meter, level_text], spacing=10,
                                          horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20,
                        border_radius=12,
                        bgcolor=ft.Colors.GREY_100,
                        width=420,
                    ),
                    ft.Row(
                        [
                            ft.Button("开始录音", icon=ft.Icons.MIC, on_click=start_recording,
                                      style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.RED)),
                            ft.Button("停止保存", icon=ft.Icons.STOP, on_click=stop_recording,
                                      style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_GREY)),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Button("打开文件夹", icon=ft.Icons.FOLDER_OPEN, on_click=open_folder),
                    result_text,
                ],
            )
        )
    )

    # 自检模式：启动后自动录 N 秒再停（窗口保留，方便继续手动测）
    auto_sec = os.environ.get("TUNER_AUTOREC")
    if auto_sec:
        async def auto_flow():
            await asyncio.sleep(1.5)
            await start_recording()
            await asyncio.sleep(float(auto_sec))
            await stop_recording()
        page.run_task(auto_flow)


if __name__ == "__main__":
    ft.run(main)
