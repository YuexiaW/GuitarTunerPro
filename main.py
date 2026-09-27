import tkinter as tk
from tkinter import font as tkfont
import numpy as np
import pyaudio
import threading
import math
import time
from collections import deque


class GuitarTuner:
    """吉他调音器核心引擎"""

    STANDARD_TUNING = {
        'E2': 82.41, 'A2': 110.00, 'D3': 146.83,
        'G3': 196.00, 'B3': 246.94, 'E4': 329.63,
    }

    STRING_NAMES = ['E2', 'A2', 'D3', 'G3', 'B3', 'E4']
    STRING_LABELS = ['6弦 E2', '5弦 A2', '4弦 D3', '3弦 G3', '2弦 B3', '1弦 E4']
    ALL_NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self):
        self.sample_rate = 44100
        self.buffer_size = 8192
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        self.current_freq = 0.0
        self.current_note = ""
        self.current_cents = 0.0
        self.confidence = 0.0
        self.freq_history = deque(maxlen=5)
        self.selected_string = None

    def start_stream(self):
        try:
            self.stream = self.audio.open(
                format=pyaudio.paFloat32, channels=1,
                rate=self.sample_rate, input=True,
                frames_per_buffer=self.buffer_size
            )
            self.is_running = True
            return True
        except Exception as e:
            print(f"无法打开音频输入: {e}")
            return False

    def stop_stream(self):
        self.is_running = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        self.stream = None

    def cleanup(self):
        self.stop_stream()
        self.audio.terminate()

    def find_nearest_string(self, freq):
        if freq <= 0:
            return None, 0
        min_cents = float('inf')
        nearest = None
        for name, target in self.STANDARD_TUNING.items():
            cents = 1200 * math.log2(freq / target)
            if abs(cents) < abs(min_cents):
                min_cents = cents
                nearest = name
        return nearest, min_cents

    def autocorrelation_pitch(self, signal):
        windowed = signal * np.hanning(len(signal))
        if np.max(np.abs(windowed)) < 0.01:
            return 0, 0

        corr = np.correlate(windowed, windowed, mode='full')
        corr = corr[len(corr) // 2:]
        if corr[0] != 0:
            corr = corr / corr[0]

        min_period = int(self.sample_rate / 400)
        max_period = int(self.sample_rate / 60)

        zero_crossings = np.where(np.diff(np.sign(corr[:max_period])))[0]
        if len(zero_crossings) == 0:
            return 0, 0

        start = max(zero_crossings[0], min_period)
        search_end = min(max_period, len(corr))
        if start >= search_end:
            return 0, 0

        peak_index = start + np.argmax(corr[start:search_end])
        confidence = corr[peak_index]

        if confidence < 0.3:
            return 0, 0

        # 抛物线插值
        if 0 < peak_index < len(corr) - 1:
            a, b, g = corr[peak_index - 1], corr[peak_index], corr[peak_index + 1]
            denom = 2 * b - a - g
            peak_refined = peak_index + (0.5 * (a - g) / denom if denom != 0 else 0)
        else:
            peak_refined = peak_index

        return self.sample_rate / peak_refined, confidence

    def process_audio(self):
        if not self.stream:
            return
        try:
            data = self.stream.read(self.buffer_size, exception_on_overflow=False)
            signal = np.frombuffer(data, dtype=np.float32)
            rms = np.sqrt(np.mean(signal ** 2))

            if rms < 0.01:
                self.current_freq = 0
                self.current_note = ""
                self.current_cents = 0
                self.confidence = 0
                return

            freq, conf = self.autocorrelation_pitch(signal)
            if freq > 0 and conf > 0.3:
                self.freq_history.append(freq)
                median_freq = np.median(list(self.freq_history)) if len(self.freq_history) >= 3 else freq
                self.current_freq = median_freq
                self.confidence = conf

                if self.selected_string is not None:
                    target = self.STANDARD_TUNING[self.STRING_NAMES[self.selected_string]]
                    self.current_cents = 1200 * math.log2(median_freq / target)
                    self.current_note = self.STRING_NAMES[self.selected_string]
                else:
                    nearest, cents = self.find_nearest_string(median_freq)
                    if nearest:
                        self.current_note = nearest
                        self.current_cents = cents
        except:
            pass


class TunerApp:
    """调音器 GUI（使用滚动布局确保完整显示）"""

    COLORS = {
        'bg': '#1a1a2e', 'panel': '#16213e', 'accent': '#0f3460',
        'green': '#00e676', 'yellow': '#ffea00', 'red': '#ff1744',
        'text': '#e0e0e0', 'text_dim': '#888888', 'meter_bg': '#0a0a1a',
        'string_active': '#00e5ff', 'string_normal': '#455a64',
        'btn_bg': '#1e3a5f', 'btn_active': '#2962ff',
    }

    def __init__(self):
        self.tuner = GuitarTuner()
        self.root = tk.Tk()
        self.root.title("🎸 吉他调音器 Guitar Tuner")
        self.root.configure(bg=self.COLORS['bg'])
        self.root.resizable(True, True)

        # ---------- 获取屏幕大小，自适应窗口 ----------
        screen_h = self.root.winfo_screenheight()
        win_w = 680
        win_h = min(screen_h - 80, 900)  # 不超过屏幕
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.minsize(600, 600)

        # ---------- 可滚动容器 ----------
        self._build_scrollable()
        self._setup_fonts()
        self._build_ui()

        self.is_tuning = False
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ─────── 可滚动框架 ───────
    def _build_scrollable(self):
        """创建可滚动容器，防止小屏幕截断"""
        outer = tk.Frame(self.root, bg=self.COLORS['bg'])
        outer.pack(fill='both', expand=True)

        self.canvas_scroll = tk.Canvas(outer, bg=self.COLORS['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient='vertical', command=self.canvas_scroll.yview)
        self.scroll_frame = tk.Frame(self.canvas_scroll, bg=self.COLORS['bg'])

        self.scroll_frame.bind("<Configure>",
                               lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all")))
        self.canvas_scroll.create_window((0, 0), window=self.scroll_frame, anchor='nw')
        self.canvas_scroll.configure(yscrollcommand=scrollbar.set)

        self.canvas_scroll.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 鼠标滚轮
        self.canvas_scroll.bind_all("<MouseWheel>",
                                    lambda e: self.canvas_scroll.yview_scroll(-e.delta // 120, "units"))

    def _setup_fonts(self):
        self.ft_title = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.ft_huge = tkfont.Font(family="Helvetica", size=56, weight="bold")
        self.ft_large = tkfont.Font(family="Helvetica", size=16, weight="bold")
        self.ft_med = tkfont.Font(family="Helvetica", size=14)
        self.ft_small = tkfont.Font(family="Helvetica", size=11)
        self.ft_tiny = tkfont.Font(family="Helvetica", size=9)
        self.ft_freq = tkfont.Font(family="Courier", size=14, weight="bold")

    # ─────── 构建 UI ───────
    def _build_ui(self):
        C = self.COLORS
        parent = self.scroll_frame
        pad_x = 20

        # ===== 标题 =====
        tk.Label(parent, text="🎸 吉他调音器  Guitar Tuner",
                 font=self.ft_title, fg=C['text'], bg=C['bg']).pack(pady=(12, 4))

        # ===== 音符显示 =====
        nf = tk.Frame(parent, bg=C['panel'], highlightbackground=C['accent'], highlightthickness=2)
        nf.pack(fill='x', padx=pad_x, pady=8)

        self.lbl_note = tk.Label(nf, text="--", font=self.ft_huge, fg=C['text'], bg=C['panel'])
        self.lbl_note.pack(pady=(10, 0))

        self.lbl_freq = tk.Label(nf, text="0.00 Hz", font=self.ft_freq, fg=C['text_dim'], bg=C['panel'])
        self.lbl_freq.pack()

        self.lbl_status = tk.Label(nf, text="等待信号…", font=self.ft_med, fg=C['text_dim'], bg=C['panel'])
        self.lbl_status.pack(pady=(0, 10))

        # ===== 调音表 =====
        self.meter = tk.Canvas(parent, width=640, height=110, bg=C['meter_bg'],
                               highlightbackground=C['accent'], highlightthickness=2)
        self.meter.pack(padx=pad_x, pady=6)
        self._draw_meter(0)

        # ===== 音分偏差 =====
        self.lbl_cents = tk.Label(parent, text="0 cents", font=self.ft_med, fg=C['text_dim'], bg=C['bg'])
        self.lbl_cents.pack(pady=2)

        # ===== 偏差条 =====
        self.bar = tk.Canvas(parent, width=640, height=32, bg=C['meter_bg'],
                             highlightbackground=C['accent'], highlightthickness=1)
        self.bar.pack(padx=pad_x, pady=4)
        self._draw_bar(0)

        # ===== 琴弦选择 =====
        sf = tk.LabelFrame(parent, text=" 选择琴弦（点击选择/再点取消，不选=自动检测） ",
                           font=self.ft_small, fg=C['text'], bg=C['panel'],
                           highlightbackground=C['accent'], highlightthickness=1)
        sf.pack(fill='x', padx=pad_x, pady=8)

        grid = tk.Frame(sf, bg=C['panel'])
        grid.pack(pady=10, padx=10)

        self.str_btns = []
        for i in range(6):
            b = tk.Button(grid, text=self.tuner.STRING_LABELS[i], font=self.ft_small,
                          width=10, height=1, bg=C['btn_bg'], fg=C['text'],
                          activebackground=C['btn_active'], activeforeground='white',
                          relief='raised', bd=2, command=lambda idx=i: self._sel_string(idx))
            b.grid(row=i // 3, column=i % 3, padx=6, pady=4)
            self.str_btns.append(b)

        self.lbl_mode = tk.Label(sf, text="🔄 自动检测模式", font=self.ft_small,
                                 fg=C['string_active'], bg=C['panel'])
        self.lbl_mode.pack(pady=(0, 8))

        # ===== 琴弦可视化 =====
        self.strings_cv = tk.Canvas(parent, width=640, height=90, bg=C['meter_bg'], highlightthickness=0)
        self.strings_cv.pack(padx=pad_x, pady=6)
        self._draw_strings()

        # ===== 开始/停止按钮 =====
        self.btn_start = tk.Button(
            parent, text="🎤  开始调音", font=self.ft_large,
            width=20, height=2, bg=C['green'], fg='#1a1a2e',
            activebackground='#00c853', relief='raised', bd=3,
            command=self._toggle
        )
        self.btn_start.pack(pady=12)

        # ===== 底部说明 =====
        tk.Label(parent,
                 text="标准调音 ▸ E2(82.4) A2(110) D3(146.8) G3(196) B3(246.9) E4(329.6) Hz",
                 font=self.ft_tiny, fg=C['text_dim'], bg=C['bg']).pack(pady=(0, 15))

    # ─────── 绘图：扇形调音表 ───────
    def _draw_meter(self, cents):
        cv = self.meter
        cv.delete("all")
        w, h = 640, 110
        cx, cy = w // 2, h + 30
        R = 130
        C = self.COLORS

        # 刻度
        for i in range(-50, 51, 5):
            ang = math.radians(90 + (i / 50) * 60)
            r1, r2 = R - 12, R
            x1, y1 = cx + r1 * math.cos(ang), cy - r1 * math.sin(ang)
            x2, y2 = cx + r2 * math.cos(ang), cy - r2 * math.sin(ang)
            if i == 0:
                col, wd = C['green'], 3
            elif abs(i) <= 10:
                col, wd = C['yellow'], 2
            else:
                col, wd = (C['red'] if abs(i) >= 40 else C['text_dim']), 1
            cv.create_line(x1, y1, x2, y2, fill=col, width=wd)

        # 数字
        for v in (-50, -25, 0, 25, 50):
            ang = math.radians(90 + (v / 50) * 60)
            x = cx + (R + 16) * math.cos(ang)
            y = cy - (R + 16) * math.sin(ang)
            cv.create_text(x, y, text=str(v), font=self.ft_tiny, fill=C['text_dim'])

        # 指针
        cl = max(-50, min(50, cents))
        ang = math.radians(90 + (cl / 50) * 60)
        px = cx + (R - 25) * math.cos(ang)
        py = cy - (R - 25) * math.sin(ang)
        pc = C['green'] if abs(cents) <= 5 else (C['yellow'] if abs(cents) <= 15 else C['red'])
        cv.create_line(cx, cy, px, py, fill=pc, width=3)
        cv.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=pc, outline='')

        cv.create_text(25, 20, text="♭ 低", font=self.ft_small, fill=C['text_dim'])
        cv.create_text(w - 25, 20, text="♯ 高", font=self.ft_small, fill=C['text_dim'])

    # ─────── 绘图：水平偏差条 ───────
    def _draw_bar(self, cents):
        cv = self.bar
        cv.delete("all")
        w, h = 640, 32
        cx = w // 2
        C = self.COLORS

        # 背景条
        cv.create_rectangle(20, 10, w - 20, h - 10, fill='#111122', outline=C['accent'])
        # 中心线
        cv.create_line(cx, 6, cx, h - 6, fill=C['green'], width=2)

        # 指示块
        cl = max(-50, min(50, cents))
        bx = cx + cl / 50 * (cx - 30)
        pc = C['green'] if abs(cents) <= 5 else (C['yellow'] if abs(cents) <= 15 else C['red'])
        cv.create_rectangle(bx - 6, 8, bx + 6, h - 8, fill=pc, outline='')

    # ─────── 绘图：琴弦 ───────
    def _draw_strings(self, active=None, tuned=False):
        cv = self.strings_cv
        cv.delete("all")
        w, C = 640, self.COLORS

        cv.create_rectangle(18, 3, 23, 87, fill='#795548', outline='#5d4037')
        cv.create_rectangle(w - 23, 3, w - 18, 87, fill='#795548', outline='#5d4037')

        for i in range(6):
            y = 12 + i * 13
            thick = max(1, 3 - i * 0.35)

            if active and self.tuner.STRING_NAMES[i] == active:
                col = C['green'] if tuned else C['yellow']
                pts = []
                for x in range(23, w - 23, 3):
                    a = 3 * math.sin(time.time() * 12 + x * 0.06)
                    pts += [x, y + a]
                if len(pts) >= 4:
                    cv.create_line(pts, fill=col, width=thick + 1, smooth=True)
            else:
                cv.create_line(23, y, w - 23, y, fill=C['string_normal'], width=thick)

            cv.create_text(w - 8, y, text=f"{6 - i}", font=self.ft_tiny, fill=C['text_dim'])

    # ─────── 琴弦选择 ───────
    def _sel_string(self, idx):
        C = self.COLORS
        if self.tuner.selected_string == idx:
            self.tuner.selected_string = None
            self.lbl_mode.config(text="🔄 自动检测模式", fg=C['string_active'])
        else:
            self.tuner.selected_string = idx
            name = self.tuner.STRING_LABELS[idx]
            hz = self.tuner.STANDARD_TUNING[self.tuner.STRING_NAMES[idx]]
            self.lbl_mode.config(text=f"🎯 {name}  ({hz} Hz)", fg=C['yellow'])

        for i, b in enumerate(self.str_btns):
            if i == self.tuner.selected_string:
                b.config(bg=C['btn_active'], relief='sunken')
            else:
                b.config(bg=C['btn_bg'], relief='raised')

    # ─────── 开始 / 停止 ───────
    def _toggle(self):
        if self.is_tuning:
            self._stop()
        else:
            self._start()

    def _start(self):
        if self.tuner.start_stream():
            self.is_tuning = True
            self.btn_start.config(text="⏹  停止调音", bg=self.COLORS['red'],
                                  activebackground='#d50000')
            threading.Thread(target=self._loop, daemon=True).start()
        else:
            self.lbl_status.config(text="❌ 无法打开麦克风!", fg=self.COLORS['red'])

    def _stop(self):
        self.is_tuning = False
        self.tuner.stop_stream()
        C = self.COLORS
        self.btn_start.config(text="🎤  开始调音", bg=C['green'], activebackground='#00c853')
        self.lbl_note.config(text="--", fg=C['text'])
        self.lbl_freq.config(text="0.00 Hz")
        self.lbl_status.config(text="等待信号…", fg=C['text_dim'])
        self.lbl_cents.config(text="0 cents", fg=C['text_dim'])
        self._draw_meter(0)
        self._draw_bar(0)
        self._draw_strings()

    def _loop(self):
        while self.is_tuning:
            self.tuner.process_audio()
            try:
                self.root.after(0, self._refresh)
            except:
                break
            time.sleep(0.05)

    def _refresh(self):
        if not self.is_tuning:
            return
        C = self.COLORS
        freq = self.tuner.current_freq
        note = self.tuner.current_note
        cents = self.tuner.current_cents

        if freq > 0 and note:
            self.lbl_note.config(text=note)
            self.lbl_freq.config(text=f"{freq:.1f} Hz")

            ac = abs(cents)
            if ac <= 5:
                col, st, tuned = C['green'], "✅ 准了！Perfect!", True
            elif ac <= 15:
                d = "↑ 偏高" if cents > 0 else "↓ 偏低"
                col, st, tuned = C['yellow'], f"⚠️ 接近 {d}", False
            else:
                d = "↑ 偏高，请松弦" if cents > 0 else "↓ 偏低，请紧弦"
                col, st, tuned = C['red'], f"❌ {d}", False

            self.lbl_note.config(fg=col)
            self.lbl_status.config(text=st, fg=col)
            self.lbl_cents.config(text=f"{cents:+.1f} cents", fg=col)
            self._draw_meter(cents)
            self._draw_bar(cents)
            self._draw_strings(active=note, tuned=tuned)
        else:
            self.lbl_note.config(text="--", fg=C['text'])
            self.lbl_freq.config(text="-- Hz")
            self.lbl_status.config(text="🎵 请弹一根弦…", fg=C['text_dim'])
            self.lbl_cents.config(text="-- cents", fg=C['text_dim'])
            self._draw_meter(0)
            self._draw_bar(0)
            self._draw_strings()

    def on_close(self):
        self.is_tuning = False
        self.tuner.cleanup()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("=" * 50)
    print("       🎸 吉他调音器 Guitar Tuner")
    print("=" * 50)
    print()
    print("  使用说明:")
    print("    1. 点击 [开始调音]")
    print("    2. 对着麦克风弹响一根弦")
    print("    3. 绿色=准了  黄色=接近  红色=需调整")
    print("    4. 可点击琴弦按钮锁定目标弦")
    print()
    app = TunerApp()
    app.run()