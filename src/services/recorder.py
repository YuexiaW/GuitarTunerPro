"""services/recorder.py —— 麦克风采集：把数据变成一帧帧 PCM16 交给上层

两条路径（实测结论，别互换）：
  - 安卓/iOS：on_stream 流式推送 PCM16 分片，不写文件（沙箱临时目录不保证可写，
    写了会导致 start_recording 直接返回 False → 界面报「无法打开麦克风」）
  - 桌面（Windows 实测）：on_stream 一个分片都不推，必须走「写 WAV 文件 + 增量轮询读取」；
    挂了 on_stream 还会强制流式模式，与文件模式冲突，所以桌面不挂
"""

import asyncio
import os

import flet as ft
import flet_audio_recorder as far

from core.constants import (
    CAPTURE_FILE, CHANNELS, FRAME_BYTES, POLL_INTERVAL, SAMPLE_RATE,
)
from models.state import TunerState

# start() 的返回码
OK = ""
PERMISSION_DENIED = "permission"


class RecorderService:
    """开始/停止采集，凑满一帧就回调 on_frame(PCM16 bytes)"""

    def __init__(self, page: ft.Page, state: TunerState, on_frame, on_status,
                 *, is_mobile: bool):
        self.page = page
        self.state = state
        self.on_frame = on_frame            # on_frame(frame: bytes)
        self.on_status = on_status          # on_status(text, level)：level ∈ dim/accent/bad/warn
        self.is_mobile = is_mobile
        self.recorder = (
            far.AudioRecorder(on_stream=self.handle_stream)
            if is_mobile
            else far.AudioRecorder()
        )

    # ---------- 对外 ----------
    async def start(self) -> str:
        """开始采集：返回 "" 成功 / PERMISSION_DENIED 缺权限 / 其他为失败原因文本"""
        if self.state.running:
            return OK
        if not await self.recorder.has_permission():
            return PERMISSION_DENIED

        self.state.reset_capture()
        try:
            os.remove(CAPTURE_FILE)
        except OSError:
            pass

        err_detail = ""
        try:
            if self.is_mobile:
                # 流式：必须用 PCM16BITS，且不能传 output_path
                ok = await self.recorder.start_recording(
                    configuration=far.AudioRecorderConfiguration(
                        encoder=far.AudioEncoder.PCM16BITS,
                        sample_rate=SAMPLE_RATE,
                        channels=CHANNELS,
                    ),
                )
            else:
                ok = await self.recorder.start_recording(
                    output_path=CAPTURE_FILE,
                    configuration=far.AudioRecorderConfiguration(
                        encoder=far.AudioEncoder.WAV,
                        sample_rate=SAMPLE_RATE,
                        channels=CHANNELS,
                    ),
                )
        except Exception as ex:
            ok = False
            err_detail = f"{type(ex).__name__}: {ex}"
            print(f"录音启动失败: {err_detail}", flush=True)

        if not ok:
            # 安卓上看不到 stdout，把原因交给上层显示到界面上，方便定位
            return err_detail or await self.diagnostics()

        self.state.running = True
        if self.is_mobile:
            self.page.run_task(self._stream_watchdog)
        else:
            self.page.run_task(self._capture_loop)
        return OK

    async def stop(self):
        self.state.running = False
        try:
            await self.recorder.stop_recording()
        except Exception:
            pass
        try:
            os.remove(CAPTURE_FILE)
        except OSError:
            pass

    # ---------- 移动端流式 ----------
    def handle_stream(self, e):
        """插件推 PCM16 分片，攒够一帧就送检测"""
        chunk = getattr(e, "chunk", None)
        if chunk is None:      # 兜底：事件字段在不同平台/版本上形态可能不同
            chunk = getattr(e, "data", None)
        if not isinstance(chunk, (bytes, bytearray)):
            return
        self.state.stream_bytes += len(chunk)
        self.state.buffer.extend(chunk)
        self._drain_frames()

    async def _stream_watchdog(self):
        """启动后 3 秒仍无任何分片 → 说明该平台 on_stream 不推送"""
        await asyncio.sleep(3)
        if self.state.running and self.state.stream_bytes == 0:
            self.on_status("⚠️ 已开始录音但没收到音频流（on_stream 未推送），需要换采集方式",
                           "warn")

    # ---------- 桌面端轮询 ----------
    async def _capture_loop(self):
        """从 WAV 文件尾增量读取 PCM16（flet_audio_recorder 桌面端不触发 on_stream）"""
        data_offset = None
        consumed = 0
        while self.state.running:
            try:
                size = os.path.getsize(CAPTURE_FILE)
            except OSError:
                size = 0

            if data_offset is None:
                if size >= 44:
                    try:
                        with open(CAPTURE_FILE, "rb") as f:
                            head = f.read(512)
                        data_offset = wav_data_offset(head) or 44
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
                    self.state.buffer.extend(raw)
                    self._drain_frames()

            await asyncio.sleep(POLL_INTERVAL)

    # ---------- 内部 ----------
    def _drain_frames(self):
        """缓冲里凑满一帧就回调一次（检测是整帧计算，半帧会算不准）"""
        buf = self.state.buffer
        while len(buf) >= FRAME_BYTES:
            frame = bytes(buf[:FRAME_BYTES])
            del buf[:FRAME_BYTES]
            self.on_frame(frame)

    async def diagnostics(self) -> str:
        """启动失败时把原因组成一句话（安卓上看不到 print 输出）"""
        parts = [f"平台={self.page.platform}"]
        for name, enc in (("PCM16", far.AudioEncoder.PCM16BITS),
                          ("WAV", far.AudioEncoder.WAV)):
            try:
                supported = await self.recorder.is_supported_encoder(enc)
                parts.append(f"{name}={'支持' if supported else '不支持'}")
            except Exception as ex:
                parts.append(f"{name}探测失败({type(ex).__name__})")
        parts.append(f"目录可写={os.access(os.path.dirname(CAPTURE_FILE), os.W_OK)}")
        return "，".join(parts)


def wav_data_offset(header: bytes) -> int | None:
    """从 WAV 头定位 data 块起始偏移（数据区为 PCM16）"""
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
