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

import httpx
from pydantic import BaseModel

from . import accounts, brains
from .accounts import Row
from .config import PROJECT_DIR, Settings
from .store import Store

FFMPEG_HINT = "Windows：winget install --id Gyan.FFmpeg -e；Mac：brew install ffmpeg（裝完重開終端機）"


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
    ffmpeg = shutil.which("ffmpeg")
    return [Row(True, "ffmpeg", ffmpeg) if ffmpeg else Row(False, "ffmpeg", f"找不到。{FFMPEG_HINT}"), _chromium()]


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
        try:
            brain.ask(Ping, "連線測試：照格式回覆 ok=true，不要做任何其他事。", "", effort="low")
        except brains.BrainError as error:
            rows.append(Row(False, label, f"有安裝但沒有正常回覆，可能還沒登入：{str(error)[:160]}（{duty}）"))
            continue
        rows.append(Row(True, label, f"測試回覆正常，{time.monotonic() - started:.0f} 秒（{duty}）"))
    return rows


def run(settings: Settings, *, ping: bool = False, http: httpx.Client | None = None) -> list[tuple[str, list[Row]]]:
    store = Store(settings.db_path)
    return [
        ("模式", mode_rows(settings)),
        ("圖片影片", tool_rows(settings)),
        ("每張桌子的 AI", brain_rows(settings, ping)),
        ("社群帳號（只讀取帳號資料，不會發文）", accounts.check(settings, store, http)),
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
