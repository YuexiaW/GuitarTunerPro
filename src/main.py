import asyncio
import math
import os
import tempfile
import time

import flet as ft
import flet_audio_recorder as far
import numpy as np

from tuner_engine import AcfDetector, HAS_AUDIOFLUX

if HAS_AUDIOFLUX:
    import audioflux as af
else:  # 安卓/iOS：audioflux 无二进制，走纯 numpy 自相关
    af = None

# --- 配置参数 ---
SAMPLE_RATE = 16000  # 16kHz 足以覆盖吉他最高弦 E4 (329Hz) 及其泛音，且计算延迟更低
CHANNELS = 1
BYTES_PER_SAMPLE = 2
UPDATE_INTERVAL = 0.1  # UI 刷新节流：每 100ms 更新一次界面，防止卡顿
FRAME_SIZE = 4096  # audioflux PitchYIN 至少需要 4096 个采样才出结果(2048 返回空数组)
FRAME_BYTES = FRAME_SIZE * BYTES_PER_SAMPLE
POLL_INTERVAL = 0.05  # 采集轮询间隔
SIG_GATE = 0.005  # 噪声门限(原始信号 rms)：低于此值不做检测，避免底噪误报音符

# 录音临时文件：flet_audio_recorder 写 WAV，我们从文件尾增量读取 PCM16
CAPTURE_FILE = os.path.join(tempfile.gettempdir(), "guitar_tuner_capture.wav")

# 吉他标准调音音符与对应基频 (Hz)
GUITAR_STRINGS = {
    "E2": 82.41,
    "A2": 110.00,
    "D3": 146.83,
    "G3": 196.00,
    "B3": 246.94,
    "E4": 329.63
}


def _wav_data_offset(header: bytes):
    """从 WAV 头部定位 data 块起始偏移（数据区为 PCM16）"""
    if len(header) < 12 or header[:4] != b"RIFF":
        return None
    pos = 12
    while pos + 8 <= len(header):
        chunk_id = header[pos:pos + 4]
        chunk_size = int.from_bytes(header[pos + 4:pos + 8], "little")
        if chunk_id == b"data":
            return pos + 8
        pos += 8 + chunk_size + (chunk_size & 1)
    return None


def _lowpass(x, taps: int = 25, passes: int = 2):
    """吉他频段前置低通(~320Hz)：两级滑动平均 FIR。

    PitchYIN 对"弱基频 + 高频噪声"的信号会整段返回 0.0(判为无声)，
    滤掉几百 Hz 以上的噪声后同一段信号就能稳定测出基频；
    顺带压掉强二次谐波，避免把 220Hz 当成 110Hz。
    """
    kernel = np.ones(taps, dtype=np.float64) / taps
    y = x.astype(np.float64)
    for _ in range(passes):
        y = np.convolve(y, kernel, mode="same")
    return y


def main(page: ft.Page):
    page.title = "🎸 吉他调音器"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 30
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- UI 组件 ---
    note_text = ft.Text("?", size=90, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400)
    freq_text = ft.Text("-- Hz", size=24, color=ft.Colors.GREY_600)
    status = ft.Text("点击「开始」以请求麦克风权限", size=16, color=ft.Colors.BLUE)

    # 音分指示器指针
    pointer = ft.Container(
        width=24,
        height=24,
        bgcolor=ft.Colors.GREEN,
        border_radius=12,
        border=ft.Border.all(2, ft.Colors.WHITE),
        animate_offset=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
    )

    meter_bg = ft.Container(
        width=320,
        height=12,
        bgcolor=ft.Colors.GREY_300,
        border_radius=6,
        content=ft.Stack(
            controls=[
                ft.Container(width=2, height=20, bgcolor=ft.Colors.GREY_600, left=159, top=-4, border_radius=1),
                pointer
            ],
            alignment=ft.Alignment.CENTER
        )
    )

    cents_text = ft.Text("0.0 cents", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700)

    # --- 音高检测器初始化（安卓/iOS 无 audioflux，自动用纯 numpy 自相关） ---
    pitch_detector = af.PitchYIN(samplate=SAMPLE_RATE) if HAS_AUDIOFLUX else AcfDetector(SAMPLE_RATE)

    # --- 状态变量 ---
    buffer = bytearray()
    last_update_time = 0.0
    is_running = False

    def show_snackbar(message: str):
        page.show_dialog(ft.SnackBar(content=ft.Text(message), duration=ft.Duration(seconds=3)))

    def get_nearest_note(freq: float):
        best_note, target_freq, min_diff = "?", 0, float('inf')
        for note, ref_freq in GUITAR_STRINGS.items():
            diff = abs(freq - ref_freq)
            if diff < min_diff:
                min_diff = diff
                best_note = note
                target_freq = ref_freq
        cents = 1200 * math.log2(freq / target_freq)
        return best_note, target_freq, cents

    def process_audio(pcm_bytes: bytes):
        """对一段 PCM16 数据做音高检测并更新 UI（on_stream 在桌面端不推送，改由轮询回调驱动）"""
        nonlocal last_update_time

        # 转换并归一化；检测器分两条路：audioflux PitchYIN / 纯 numpy 自相关
        audio_data = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        if HAS_AUDIOFLUX:
            # 噪声门限：安静房间的底噪会让 PitchYIN 偶尔吐出 200~330Hz 的杂散值
            rms = float(np.sqrt(np.mean(audio_data ** 2)))
            if rms < SIG_GATE:
                if os.environ.get("TUNER_DEBUG"):
                    print(f"[dbg] rms={rms:.4f} 低于门限，跳过", flush=True)
                return

            # 前置低通：PitchYIN 对含高频噪声的弱基频信号会返回 0.0(判为无声)
            filtered = _lowpass(audio_data)
            fre_arr, _, _ = pitch_detector.pitch(np.ascontiguousarray(filtered.astype(np.float32)))
            # 过滤有效频率 (吉他基频范围约 80-330Hz，放宽至 60-500Hz 容纳泛音)
            valid_freqs = [float(f) for f in fre_arr if 60.0 < float(f) < 500.0]
            rms = float(np.sqrt(np.mean(audio_data ** 2)))
        else:
            # 回退路径：门限与低通在 AcfDetector 内部完成
            rms = float(np.sqrt(np.mean(audio_data ** 2)))
            freq, conf = pitch_detector.detect(audio_data)
            valid_freqs = [freq] if freq > 0 and conf >= 0.4 else []

        if os.environ.get("TUNER_DEBUG"):
            print(f"[dbg] rms={rms:.4f} freqs={valid_freqs[:5]}", flush=True)

        if valid_freqs:
            current_freq = float(np.median(valid_freqs))
            note, target, cents = get_nearest_note(current_freq)
            display_cents = max(-50.0, min(50.0, cents))

            # 更新 UI 数据
            note_text.value = note
            freq_text.value = f"{current_freq:.1f} Hz"
            cents_text.value = f"{cents:+.1f} cents"

            if abs(cents) <= 5.0:
                note_text.color = ft.Colors.GREEN
                pointer.bgcolor = ft.Colors.GREEN
                status.value = "✅ 音准完美！"
                status.color = ft.Colors.GREEN
            else:
                note_text.color = ft.Colors.AMBER
                pointer.bgcolor = ft.Colors.RED
                status.value = "⬆️ 偏高" if cents > 5.0 else "⬇️ 偏低"
                status.color = ft.Colors.RED

            # 指针以自身尺寸为单位偏移：320 宽量表上 ±50 cent 走 ±132px
            pointer.offset = ft.Offset(display_cents / 50.0 * 5.5, 0)

            # UI 节流刷新 (防止高频调用 page.update 导致卡顿)
            current_time = time.time()
            if current_time - last_update_time > UPDATE_INTERVAL:
                page.update()
                last_update_time = current_time

    async def capture_loop():
        """轮询录音文件增量：flet_audio_recorder 在 Windows 桌面端不触发 on_stream，
        改为记录到 WAV 文件、我们从文件尾增量读取 PCM16 数据"""
        nonlocal is_running
        data_offset = None
        consumed = 0
        while is_running:
            try:
                size = os.path.getsize(CAPTURE_FILE)
            except OSError:
                size = 0

            if data_offset is None:
                if size >= 44:
                    try:
                        with open(CAPTURE_FILE, "rb") as f:
                            head = f.read(512)
                        data_offset = _wav_data_offset(head) or 44
                    except OSError:
                        data_offset = None
            elif size > data_offset + consumed:
                try:
                    with open(CAPTURE_FILE, "rb") as f:
                        f.seek(data_offset + consumed)
                        raw = f.read(min(size - data_offset - consumed, 256 * 1024))
                except OSError:
                    raw = b""
                consumed += len(raw)
                if raw:
                    buffer.extend(raw)
                    while len(buffer) >= FRAME_BYTES:
                        frame = bytes(buffer[:FRAME_BYTES])
                        del buffer[:FRAME_BYTES]
                        process_audio(frame)

            await asyncio.sleep(POLL_INTERVAL)

    async def handle_recording_start(e: ft.ControlEvent):
        nonlocal is_running
        if is_running:
            return
        if not await recorder.has_permission():
            show_snackbar("需要麦克风权限才能调音。")
            return

        buffer.clear()
        try:
            os.remove(CAPTURE_FILE)
        except OSError:
            pass

        status.value = "🎤 正在监听音频..."
        status.color = ft.Colors.BLUE
        page.update()

        try:
            ok = await recorder.start_recording(
                output_path=CAPTURE_FILE,
                configuration=far.AudioRecorderConfiguration(
                    encoder=far.AudioEncoder.WAV,
                    sample_rate=SAMPLE_RATE,
                    channels=CHANNELS,
                ),
            )
        except Exception as ex:
            ok = False
            print(f"录音启动失败: {ex}", flush=True)

        if not ok:
            status.value = "❌ 无法打开麦克风！"
            status.color = ft.Colors.RED
            page.update()
            return

        is_running = True
        page.run_task(capture_loop)

    async def handle_recording_stop(e: ft.ControlEvent):
        nonlocal is_running
        is_running = False
        try:
            await recorder.stop_recording()
        except Exception:
            pass
        try:
            os.remove(CAPTURE_FILE)
        except OSError:
            pass
        status.value = "⏸️ 已停止监听"
        status.color = ft.Colors.GREY_600

        # 重置 UI
        note_text.value = "?"
        note_text.color = ft.Colors.GREY_400
        freq_text.value = "-- Hz"
        cents_text.value = "0.0 cents"
        pointer.offset = ft.Offset(0, 0)
        page.update()

    # --- 实例化 Recorder (Service，无需 page.add) ---
    recorder = far.AudioRecorder()

    # --- 布局组装 ---
    page.add(
        ft.SafeArea(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("🎸 实时吉他调音器", size=28, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                    note_text,
                    freq_text,
                    ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                    meter_bg,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    cents_text,
                    ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                    status,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Row([
                        ft.Button("开始调音", icon=ft.Icons.MIC, on_click=handle_recording_start,
                                  style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE)),
                        ft.Button("停止", icon=ft.Icons.STOP, on_click=handle_recording_stop,
                                  style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.RED)),
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ],
            ),
        )
    )

    if os.environ.get("TUNER_AUTOSTART"):
        async def _auto():
            await asyncio.sleep(2.0)
            print("[dbg] autostart", flush=True)
            await handle_recording_start(None)
        page.run_task(_auto)


if __name__ == "__main__":
    ft.run(main)