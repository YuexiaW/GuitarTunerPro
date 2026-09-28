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
    """用户偏好（可观察：页面上改了立刻重渲染）"""

    a4: float = A4_STANDARD          # 参考音，440 为标准音高
    nickname: str = DEFAULT_NICKNAME  # 「我的」页昵称
    avatar: str = DEFAULT_AVATAR     # 头像（先是一枚 emoji，换图片是后续的事）

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

    def save(self):
        try:
            path = self.path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"a4": self.a4, "nickname": self.nickname, "avatar": self.avatar},
                           ensure_ascii=False, indent=2),
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

    def is_standard_a4(self) -> bool:
        return abs(self.a4 - A4_STANDARD) < 0.01


settings_state = SettingsState()
