"""Settings for the marketing office, read from environment variables (and an optional .env file)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if value[:1] in {'"', "'"}:
            value = value[1:].split(value[0], 1)[0]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        values[key.strip()] = value
    return values


def _time(value: str) -> time:
    hours, _, minutes = value.strip().partition(":")
    return time(int(hours), int(minutes or 0))


def _flag(value: str | None, default: bool | None) -> bool | None:
    """Only an explicit yes or no changes a flag; anything unreadable keeps the (safe) default."""
    text = (value or "").strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _count(value: str | None, default: int) -> int:
    """A small non-negative whole number; anything else keeps the default."""
    try:
        return max(0, int((value or "").strip()))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    home: Path
    repo_root: Path
    timezone: ZoneInfo = ZoneInfo("Asia/Taipei")
    site_url: str = "https://app.uniway-tw.com"
    brand_name: str = "UniWay"

    # "manual": every draft waits for you in the inbox. "auto": drafts that pass review are scheduled straight away.
    approval: str = "manual"
    # While true nothing leaves the machine: the publisher writes what it would send to var/outbox/.
    dry_run: bool = True
    # Which AI each desk thinks with: "role=brain,…", or one brain for every role. Brains: claude-code, codex,
    # antigravity, api (Claude API), offline (templates) and auto (Claude API with credentials, otherwise offline).
    brains: str = "auto"
    # Tried in order when a desk's own brain is missing, logged out or fails.
    brain_fallback: tuple[str, ...] = ("api", "offline")
    # Cover illustrations for carousels and stories: "codex" (its built-in image generation) or "none".
    images: str = "none"
    model: str = "claude-opus-5-5"
    claude_code_command: str = "claude"
    claude_code_model: str = ""
    codex_command: str = "codex"
    codex_model: str = ""
    antigravity_command: str = "agy -p"
    brain_timeout: int = 600

    daily_at: time = time(7, 30)
    threads_slots: tuple[time, ...] = (time(12, 30), time(21, 0))
    threads_albums: int = 1  # how many of the day's Threads posts (the latest ones) are multi-image posts; 0 for none
    instagram_slot: time = time(19, 30)
    youtube_slot: time = time(18, 0)
    analytics_at: time = time(23, 30)
    long_video_weekday: int = 6  # Sunday
    video_fps: int = 30
    render_media: bool = True
    threads_images: bool = True

    threads_user_id: str = ""
    threads_token: str = ""
    threads_app_secret: str = ""
    instagram_user_id: str = ""
    instagram_token: str = ""
    instagram_app_secret: str = ""
    instagram_graph_host: str = "graph.instagram.com"
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_refresh_token: str = ""
    youtube_privacy: str = "public"

    media_host: str = "none"  # none | static | supabase
    public_base_url: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_bucket: str = "marketing-media"

    # GitHub: the draft pull requests Pat opens from the data updates you approve. The token lives in .env or in
    # `office auth github`; no AI desk ever sees it, and nothing here can merge.
    github_repo: str = "blizzard-new/abroad"
    github_base: str = "main"
    github_token: str = ""
    # None: pull requests are only recorded in var/outbox/ while OFFICE_DRY_RUN is on; True or False decides it alone.
    github_dry_run: bool | None = None

    # When set, the office page and API need ?token=… once (a cookie remembers it). /media stays public.
    access_token: str = ""

    # Your phone line: a Telegram bot you create with @BotFather, paired with `office auth telegram`.
    telegram_bot_token: str = ""
    # Where your phone opens the office (for example over Tailscale); notifications link to it when set.
    office_url: str = ""

    @property
    def github_simulated(self) -> bool:
        return self.dry_run if self.github_dry_run is None else self.github_dry_run

    @property
    def db_path(self) -> Path:
        return self.home / "office.sqlite3"

    @property
    def voice_path(self) -> Path:
        return self.home / "voice.md"

    @property
    def media_dir(self) -> Path:
        return self.home / "media"

    @property
    def outbox_dir(self) -> Path:
        return self.home / "outbox"

    @property
    def brand_assets_dir(self) -> Path:
        return self.repo_root / "marketing" / "promo-video" / "assets"

    @property
    def fonts_dir(self) -> Path:
        return self.repo_root / "src" / "exchange_info" / "static" / "assets" / "fonts"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None, **overrides) -> "Settings":
        if env is None:
            env = {**_load_dotenv(PROJECT_DIR / ".env"), **os.environ}
        get = env.get
        repo_root = Path(get("OFFICE_REPO_ROOT") or REPO_ROOT)
        values = dict(
            home=Path(get("OFFICE_HOME") or PROJECT_DIR / "var"),
            repo_root=repo_root,
            timezone=ZoneInfo(get("OFFICE_TIMEZONE") or "Asia/Taipei"),
            site_url=(get("OFFICE_SITE_URL") or "https://app.uniway-tw.com").rstrip("/"),
            approval=(get("OFFICE_APPROVAL") or "manual").lower(),
            dry_run=_flag(get("OFFICE_DRY_RUN"), True),
            brains=(get("OFFICE_BRAINS") or "auto").lower(),
            brain_fallback=tuple(b.strip().lower() for b in (get("OFFICE_BRAIN_FALLBACK") or "api,offline").split(",") if b.strip()),
            images=(get("OFFICE_IMAGES") or "none").lower(),
            model=get("OFFICE_MODEL") or "claude-opus-5-5",
            claude_code_command=get("OFFICE_CLAUDE_CODE_COMMAND") or "claude",
            claude_code_model=get("OFFICE_CLAUDE_CODE_MODEL") or "",
            codex_command=get("OFFICE_CODEX_COMMAND") or "codex",
            codex_model=get("OFFICE_CODEX_MODEL") or "",
            antigravity_command=get("OFFICE_ANTIGRAVITY_COMMAND") or "agy -p",
            brain_timeout=int(get("OFFICE_BRAIN_TIMEOUT") or 600),
            daily_at=_time(get("OFFICE_DAILY_AT") or "07:30"),
            threads_slots=tuple(_time(t) for t in (get("OFFICE_THREADS_SLOTS") or "12:30,21:00").split(",") if t.strip()),
            threads_albums=_count(get("OFFICE_THREADS_ALBUMS"), 1),
            instagram_slot=_time(get("OFFICE_INSTAGRAM_SLOT") or "19:30"),
            youtube_slot=_time(get("OFFICE_YOUTUBE_SLOT") or "18:00"),
            analytics_at=_time(get("OFFICE_ANALYTICS_AT") or "23:30"),
            long_video_weekday=int(get("OFFICE_LONG_VIDEO_WEEKDAY") or 6),
            video_fps=int(get("OFFICE_VIDEO_FPS") or 30),
            render_media=_flag(get("OFFICE_RENDER_MEDIA"), True),
            threads_images=_flag(get("OFFICE_THREADS_IMAGES"), True),
            threads_user_id=get("THREADS_USER_ID") or "",
            threads_token=get("THREADS_ACCESS_TOKEN") or "",
            threads_app_secret=get("THREADS_APP_SECRET") or "",
            instagram_user_id=get("INSTAGRAM_USER_ID") or "",
            instagram_token=get("INSTAGRAM_ACCESS_TOKEN") or "",
            instagram_app_secret=get("INSTAGRAM_APP_SECRET") or "",
            instagram_graph_host=get("INSTAGRAM_GRAPH_HOST") or "graph.instagram.com",
            youtube_client_id=get("YOUTUBE_CLIENT_ID") or "",
            youtube_client_secret=get("YOUTUBE_CLIENT_SECRET") or "",
            youtube_refresh_token=get("YOUTUBE_REFRESH_TOKEN") or "",
            youtube_privacy=get("YOUTUBE_PRIVACY") or "public",
            github_repo=get("OFFICE_GITHUB_REPO") or "blizzard-new/abroad",
            github_base=get("OFFICE_GITHUB_BASE") or "main",
            github_token=get("OFFICE_GITHUB_TOKEN") or "",
            github_dry_run=_flag(get("OFFICE_GITHUB_DRY_RUN"), None),
            media_host=(get("OFFICE_MEDIA_HOST") or "none").lower(),
            public_base_url=(get("OFFICE_PUBLIC_BASE_URL") or "").rstrip("/"),
            supabase_url=(get("SUPABASE_URL") or "").rstrip("/"),
            supabase_service_key=get("SUPABASE_SERVICE_ROLE_KEY") or "",
            supabase_bucket=get("SUPABASE_MARKETING_BUCKET") or "marketing-media",
            access_token=get("OFFICE_ACCESS_TOKEN") or "",
            telegram_bot_token=get("TELEGRAM_BOT_TOKEN") or "",
            office_url=(get("OFFICE_URL") or "").rstrip("/"),
        )
        values.update(overrides)
        settings = cls(**values)
        for path in (settings.home, settings.media_dir, settings.outbox_dir):
            path.mkdir(parents=True, exist_ok=True)
        return settings
