"""`uv run office check`: is this computer ready to run the office, and is every desk connected to what it needs?

Sections: the safety modes, the programs that make images and videos, the AI each desk thinks with (optionally
asking each one a one-line test question) and the social accounts. Account checks only read who a token belongs to;
nothing is posted.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from types import SimpleNamespace

import httpx
from pydantic import BaseModel

from . import accounts, brains
from .accounts import Row
from .config import PROJECT_DIR, Settings
from .render.renderer import ffmpeg_exe
from .store import Store

FFMPEG_HINT = "自己裝一個（Windows：winget install --id Gyan.FFmpeg -e；Mac：brew install ffmpeg），或用 IMAGEIO_FFMPEG_EXE 指定"


PING_TIMEOUT = 180  # a tool stuck on a login or trust prompt should not hold the check for the full brain timeout


class Ping(BaseModel):
    ok: bool


def mode_rows(settings: Settings) -> list[Row]:
    rows = []
    if not (PROJECT_DIR / ".env").is_file():
        rows.append(Row(None, ".env", "還沒有，把 .env.example 複製成 .env 再改"))
    if settings.dry_run:
        rows.append(Row(None, "模擬發文", "OFFICE_DRY_RUN=1：只寫進 var/outbox/，不會真的發文；社群帳號都是 ○ 之後再改成 0"))
    else:
        rows.append(Row(True, "正式發文", "OFFICE_DRY_RUN=0：核准的貼文會真的發出去"))
    if settings.approval == "auto":
        rows.append(Row(None, "自動排程", "OFFICE_APPROVAL=auto：審稿通過就排程，不等你核准"))
    else:
        rows.append(Row(True, "人工審核", "每則貼文都等你在審核匣按核准"))
    return rows


def tool_rows(settings: Settings) -> list[Row]:
    if not settings.render_media:
        return [Row(None, "圖片影片", "OFFICE_RENDER_MEDIA=0：只寫文案，不需要 ffmpeg 和 Chromium")]
    try:
        ffmpeg = Row(True, "ffmpeg", ffmpeg_exe())
    except RuntimeError as error:  # imageio-ffmpeg has no build for this machine and none is on PATH
        ffmpeg = Row(False, "ffmpeg", f"找不到：{error}。{FFMPEG_HINT}")
    return [ffmpeg, _chromium()]


def _chromium() -> Row:
    custom = os.environ.get("CHROMIUM_PATH")
    if custom:
        return Row(Path(custom).is_file(), "Chromium", custom if Path(custom).is_file() else f"CHROMIUM_PATH 指到的檔案不存在：{custom}")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            path = playwright.chromium.executable_path
    except Exception as error:  # noqa: BLE001 - any failure here means the renderer cannot start either
        return Row(False, "Chromium", f"Playwright 啟動失敗：{str(error)[:160]}")
    if Path(path).is_file():
        return Row(True, "Chromium", path)
    return Row(False, "Chromium", "還沒下載：uv run playwright install chromium")


def brain_rows(settings: Settings, ping: bool = False) -> list[Row]:
    """One row per AI tool in use: where it is installed and which desks rely on it first."""
    from .office import STAFF, desk_of

    names = {agent.persona.id: agent.persona.name for agent in STAFF}
    chains = {role: brains.chain(settings, role) for role in brains.ROLES}
    keys = list(dict.fromkeys(key for chain in chains.values() for key in chain))
    rows = []
    for key in keys:
        label = brains.LABELS[key]
        desks = list(dict.fromkeys(names[desk_of(role)] for role, chain in chains.items() if chain[0] == key))
        duty = f"負責 {'、'.join(desks)}" if desks else "備援"
        brain = brains.build(key, settings)
        if brain is None:
            rows.append(Row(True, label, f"內建，永遠可用（{duty}）"))
            continue
        if not brain.available():
            if key == "api":
                hint = "沒有 ANTHROPIC_API_KEY"
            else:
                hint = f"找不到 {brain.command[0]}：安裝後先在終端機執行一次登入"
            rows.append(Row(False if desks else None, label, f"{hint}（{duty}）"))
            continue
        where = shutil.which(brain.command[0]) if brain.command else "API 金鑰"
        if not ping:
            rows.append(Row(True, label, f"{where}（{duty}）"))
            continue
        started = time.monotonic()
        brain.timeout = min(brain.timeout, PING_TIMEOUT)
        try:
            brain.ask(Ping, "連線測試：照格式回覆 ok=true，不要做任何其他事。", "", effort="low")
        except brains.BrainError as error:
            rows.append(Row(False, label, f"有安裝但沒有正常回覆，可能還沒登入：{str(error)[:160]}（{duty}）"))
            continue
        rows.append(Row(True, label, f"測試回覆正常，{time.monotonic() - started:.0f} 秒（{duty}）"))
    return rows


def phone_rows(settings: Settings, store: Store, http: httpx.Client | None = None) -> list[Row]:
    if not settings.telegram_bot_token:
        return [Row(None, "Telegram", "還沒設定：想用手機跟 Leo 說話、收通知，見 README「用手機跟 Leo 說話」")]
    from .telegram import TelegramBridge, TelegramError

    # Looking the bot up needs only the settings and the store, not a whole office.
    bridge = TelegramBridge(SimpleNamespace(settings=settings, store=store), http=http)
    try:
        name = bridge.bot_name()
    except TelegramError as error:
        return [Row(False, "Telegram", f"TELEGRAM_BOT_TOKEN 不對或連不上：{error}")]
    if not bridge.chat_id:
        return [Row(False, "Telegram", f"機器人 @{name} 還沒連到你的手機：uv run office auth telegram")]
    who = store.get("handle:telegram") or "你"
    return [Row(True, "Telegram", f"@{name} → {who} 的手機（跟 Leo 聊天、收通知、按核准）")]


def run(settings: Settings, *, ping: bool = False, http: httpx.Client | None = None) -> list[tuple[str, list[Row]]]:
    store = Store(settings.db_path)
    return [
        ("模式", mode_rows(settings)),
        ("圖片影片", tool_rows(settings)),
        ("每張桌子的 AI", brain_rows(settings, ping)),
        ("社群帳號（只讀取帳號資料，不會發文）", accounts.check(settings, store, http)),
        ("手機", phone_rows(settings, store, http)),
    ]


def render(sections: list[tuple[str, list[Row]]]) -> str:
    mark = {True: "○", False: "×", None: "△"}
    lines = []
    for title, rows in sections:
        lines.append(f"\n【{title}】")
        lines += [f"  {mark[row.ok]} {row.name}：{row.detail}" for row in rows]
    problems = sum(1 for _, rows in sections for row in rows if row.ok is False)
    lines.append("\n全部就緒。" if not problems else f"\n有 {problems} 項要處理（×），△ 是提醒。")
    return "\n".join(lines)
