"""models.settings —— 持久化偏好（参考音 A4、昵称、头像）

和 models.state 的分工：state 是「运行时状态」（音符/是否在采集/主题名），
这里只存「用户选过、下次还要记住」的东西，落一个 JSON 文件。

存放目录依次尝试：Flet 运行时注入的 FLET_APP_STORAGE_DATA（`flet run` 与打包后的
安卓/iOS 都指向应用私有目录）→ %APPDATA%/GuitarTuner（桌面）→ 家目录 .guitar_tuner。
不用 Flet 的 StoragePaths/SharedPreferences：它们都是**异步服务**（要 await），
而这里是同步初始化，env 变量那条路在两端都够用。

读写在 try 里，任何一步失败都只是「这次不持久化」，不影响调音本身（只读环境照样能用）。
"""

import json
import os
from datetime import date
from pathlib import Path

import flet as ft

from core.constants import A4_STANDARD, DEFAULT_AVATAR, DEFAULT_NICKNAME, NICKNAME_MAX, SETTINGS_FILE


def _settings_dir() -> Path:
    data_dir = os.environ.get("FLET_APP_STORAGE_DATA")
    if data_dir:
        return Path(data_dir)
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "GuitarTuner"
    return Path.home() / ".guitar_tuner"


@ft.observable
class SettingsState:
    """用户偏好 + 使用计数（可观察：页面上改了立刻重渲染）"""

    a4: float = A4_STANDARD           # 参考音，440 为标准音高
    nickname: str = DEFAULT_NICKNAME  # 「我的」页昵称
    avatar: str = DEFAULT_AVATAR      # 头像（先是一枚 emoji，换图片是后续的事）

    # 使用计数：都是真实累加，用来填「我的」页数据行（不写死假数据）
    sessions: int = 0                 # 点「开始调音」的次数
    in_tune_hits: int = 0             # 调准次数（每次从「不准」跨进绿区记一次）
    first_run: str = ""               # 首次使用日期 YYYY-MM-DD

    def path(self) -> Path:
        """配置文件路径（第一次用到时才定下来，之后不再变）"""
        cached = getattr(self, "_path", None)
        if cached is None:
            cached = _settings_dir() / SETTINGS_FILE
            self._path = cached       # 下划线字段：不触发通知
        return cached

    def load(self):
        """读磁盘；文件不存在 / 内容坏了 / 读不了，都保持默认值"""
        try:
            data = json.loads(self.path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        a4 = data.get("a4")
        if isinstance(a4, (int, float)) and 400 <= a4 <= 480:
            self.a4 = float(a4)
        nickname = data.get("nickname")
        if isinstance(nickname, str) and nickname.strip():
            self.nickname = nickname.strip()[:NICKNAME_MAX]
        avatar = data.get("avatar")
        if isinstance(avatar, str) and avatar:
            self.avatar = avatar
        for key in ("sessions", "in_tune_hits"):
            value = data.get(key)
            if isinstance(value, (int, float)) and value >= 0:
                setattr(self, key, int(value))
        first_run = data.get("first_run")
        if isinstance(first_run, str) and first_run:
            self.first_run = first_run

    def save(self):
        try:
            path = self.path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "a4": self.a4,
                        "nickname": self.nickname,
                        "avatar": self.avatar,
                        "sessions": self.sessions,
                        "in_tune_hits": self.in_tune_hits,
                        "first_run": self.first_run,
                    },
                    ensure_ascii=False, indent=2,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass

    def set_a4(self, value: float):
        """换参考音：改状态（页面自动重渲染）+ 立即落盘"""
        self.a4 = float(value)
        self.save()

    def set_nickname(self, text: str):
        """改昵称：空 / 全空白就退回默认，避免页面上出现空标题"""
        name = (text or "").strip()[:NICKNAME_MAX]
        self.nickname = name or DEFAULT_NICKNAME
        self.save()

    def set_avatar(self, emoji: str):
        self.avatar = emoji or DEFAULT_AVATAR
        self.save()

    # --- 使用计数 ---
    def add_session(self):
        """点一次「开始调音」：计数 +1，顺手记下首次使用日期"""
        self.sessions = int(self.sessions) + 1
        if not self.first_run:
            self.first_run = date.today().isoformat()
        self.save()

    def add_in_tune_hit(self):
        """调准一次（从「不准」跨进绿区）：计数 +1"""
        self.in_tune_hits = int(self.in_tune_hits) + 1
        self.save()

    def days_used(self) -> int:
        """使用天数：首次使用那天算第 1 天（没有记录时按 1 天显示）"""
        try:
            first = date.fromisoformat(self.first_run)
        except (TypeError, ValueError):
            return 1
        return max(1, (date.today() - first).days + 1)

    def is_standard_a4(self) -> bool:
        return abs(self.a4 - A4_STANDARD) < 0.01


settings_state = SettingsState()
