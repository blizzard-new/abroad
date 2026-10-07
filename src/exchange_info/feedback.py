"""User feedback ("用戶評價"): anyone can leave a suggestion; only an administrator can read what was left.

Nothing that identifies the sender is stored by the server: no IP address, no account id, no e-mail address. ``contact`` is
only what the person chose to type, and ``home_school`` / ``route`` are the school and page they were looking at.
"""
from __future__ import annotations

import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal, Mapping

import requests
from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import supabase_http
from .analytics import RateLimited, RateLimiter
from .supabase_keys import supabase_key_headers

DEFAULT_DATA_DIR = Path("data")
Kind = Literal["suggestion", "bug", "praise", "other"]
Status = Literal["new", "read", "done"]
MAX_LIST = 500
MAX_LINKS = 2
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_BLANK_RUNS = re.compile(r"\n{3,}")


class FeedbackRepositoryError(RuntimeError):
    pass


def clean_text(value: str) -> str:
    """Plain text only: no control characters, no long runs of blank lines."""
    text = _CONTROL.sub("", value.replace("\r\n", "\n").replace("\r", "\n"))
    return _BLANK_RUNS.sub("\n\n", text).strip()


class FeedbackSubmission(BaseModel):
    """What the form sends."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    kind: Kind = "suggestion"
    rating: int | None = Field(default=None, ge=1, le=5)
    message: str = Field(min_length=5, max_length=2000)
    contact: str = Field(default="", max_length=120)
    route: str = Field(default="", max_length=120)
    home_school: str = Field(default="", max_length=60)
    website: str = Field(default="", max_length=200)  # a field people never see; bots fill it in

    @field_validator("message", "contact", "route", "home_school", mode="after")
    @classmethod
    def _plain(cls, value: str) -> str:
        return clean_text(value)


class FeedbackRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    kind: Kind = "suggestion"
    rating: int | None = Field(default=None, ge=1, le=5)
    message: str
    contact: str = ""
    route: str = ""
    home_school: str = ""
    signed_in: bool = False
    status: Status = "new"
    admin_note: str = Field(default="", max_length=1000)
    handled_at: datetime | None = None


# --------------------------------------------------------------------------- JSONL (development)


class JsonlFeedbackRepository:
    backend_name = "jsonl"

    def __init__(self, data_dir: Path) -> None:
        self.path = Path(data_dir) / "feedback" / "feedback.jsonl"
        self._lock = threading.RLock()

    def _read(self) -> list[FeedbackRecord]:
        if not self.path.exists():
            return []
        return [FeedbackRecord.model_validate_json(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _write(self, rows: list[FeedbackRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text("".join(row.model_dump_json() + "\n" for row in rows), encoding="utf-8", newline="\n")
        os.replace(temporary, self.path)

    def add(self, record: FeedbackRecord) -> FeedbackRecord:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(record.model_dump_json() + "\n")
        return record

    def list(self, *, status: str | None = None, kind: str | None = None, limit: int = MAX_LIST) -> list[FeedbackRecord]:
        with self._lock:
            rows = self._read()
        rows = [row for row in rows if (not status or row.status == status) and (not kind or row.kind == kind)]
        rows.sort(key=lambda row: row.created_at, reverse=True)
        return rows[:limit]

    def update(self, feedback_id: str, *, status: str, note: str) -> FeedbackRecord | None:
        with self._lock:
            rows = self._read()
            target = next((row for row in rows if row.id == feedback_id), None)
            if target is None:
                return None
            target.status = status  # type: ignore[assignment]
            target.admin_note = note
            target.handled_at = datetime.now(timezone.utc) if status != "new" else None
            self._write(rows)
            return target


# --------------------------------------------------------------------------- Supabase (production)


class SupabaseFeedbackRepository:
    backend_name = "supabase"
    TABLE = "exchange_user_feedback"

    def __init__(self, url: str, service_role_key: str, *,
                 request_func: Callable[..., requests.Response] = supabase_http.request) -> None:
        if not url.strip().casefold().startswith("https://"):
            raise FeedbackRepositoryError("Supabase URL 必須使用 HTTPS。")
        self.url = url.rstrip("/")
        self.service_role_key = service_role_key
        self.request_func = request_func

    def _request(self, method: str, params: list[tuple[str, str]] | None = None, **kwargs):
        headers = {
            **supabase_key_headers(self.service_role_key),
            "Content-Type": "application/json",
            **kwargs.pop("headers", {}),
        }
        try:
            response = self.request_func(method, f"{self.url}/rest/v1/{self.TABLE}", headers=headers,
                                         params=params, timeout=20, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise FeedbackRepositoryError("Supabase 用戶評價請求失敗。") from exc

    @staticmethod
    def _rows(response) -> list[dict]:
        try:
            rows = response.json()
        except (TypeError, ValueError) as exc:
            raise FeedbackRepositoryError("Supabase 用戶評價回應格式無效。") from exc
        if not isinstance(rows, list):
            raise FeedbackRepositoryError("Supabase 用戶評價回應格式無效。")
        return rows

    def add(self, record: FeedbackRecord) -> FeedbackRecord:
        self._request("POST", json=record.model_dump(mode="json"), headers={"Prefer": "return=minimal"})
        return record

    def list(self, *, status: str | None = None, kind: str | None = None, limit: int = MAX_LIST) -> list[FeedbackRecord]:
        params = [("select", "*"), ("order", "created_at.desc"), ("limit", str(limit))]
        if status:
            params.append(("status", f"eq.{status}"))
        if kind:
            params.append(("kind", f"eq.{kind}"))
        return [FeedbackRecord.model_validate(row) for row in self._rows(self._request("GET", params))]

    def update(self, feedback_id: str, *, status: str, note: str) -> FeedbackRecord | None:
        body = {"status": status, "admin_note": note,
                "handled_at": datetime.now(timezone.utc).isoformat() if status != "new" else None}
        rows = self._rows(self._request("PATCH", [("id", f"eq.{feedback_id}")], json=body,
                                        headers={"Prefer": "return=representation"}))
        return FeedbackRecord.model_validate(rows[0]) if rows else None


def create_feedback_repository(data_dir: Path = DEFAULT_DATA_DIR, environ: Mapping[str, str] | None = None):
    values = os.environ if environ is None else environ
    environment = values.get("EXCHANGE_ENVIRONMENT", "development").strip().casefold()
    backend = values.get("EXCHANGE_FEEDBACK_BACKEND", "auto").strip().casefold()
    url = (values.get("EXCHANGE_SUPABASE_URL") or values.get("SUPABASE_URL") or "").strip()
    key = (
        values.get("EXCHANGE_SUPABASE_SECRET_KEY")
        or values.get("SUPABASE_SECRET_KEY")
        or values.get("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()
    if backend not in {"auto", "jsonl", "supabase"}:
        raise FeedbackRepositoryError("EXCHANGE_FEEDBACK_BACKEND 只能是 auto、jsonl 或 supabase。")
    if backend == "supabase" or (backend == "auto" and url and key):
        if not url or not key:
            raise FeedbackRepositoryError("Supabase 用戶評價持久層必須同時設定 URL 與 server secret。")
        return SupabaseFeedbackRepository(url, key)
    if environment in {"production", "prod"}:
        raise FeedbackRepositoryError("正式環境禁止使用 JSONL 用戶評價持久層。")
    return JsonlFeedbackRepository(data_dir)


# --------------------------------------------------------------------------- the service


class FeedbackRejected(Exception):
    """The text itself is not acceptable (for example, a pile of links)."""


class FeedbackService:
    def __init__(self, repository, *, per_window: RateLimiter | None = None, per_day: RateLimiter | None = None) -> None:
        self.repository = repository
        # Three messages in ten minutes and ten in a day, per visitor address; kept in memory only.
        self.per_window = per_window or RateLimiter(max_batches=3, max_events=3, window_seconds=600.0)
        self.per_day = per_day or RateLimiter(max_batches=10, max_events=10, window_seconds=86_400.0)

    @property
    def backend_name(self) -> str:
        return getattr(self.repository, "backend_name", "jsonl")

    def submit(self, payload: FeedbackSubmission, *, client_key: str, signed_in: bool, now: float | None = None) -> FeedbackRecord | None:
        """Store one message. Returns None for a bot (the form's hidden field was filled), which is told nothing."""
        if payload.website:
            return None
        if len(re.findall(r"https?://", payload.message, flags=re.IGNORECASE)) > MAX_LINKS:
            raise FeedbackRejected("請不要在內容裡放太多連結。")
        if not self.per_window.allow(client_key, 1, now) or not self.per_day.allow(client_key, 1, now):
            raise RateLimited()
        record = FeedbackRecord(
            kind=payload.kind, rating=payload.rating, message=payload.message, contact=payload.contact,
            route=payload.route, home_school=payload.home_school, signed_in=signed_in,
        )
        return self.repository.add(record)


def csv_cell(value: object) -> str:
    """A cell a spreadsheet will not run as a formula."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in {"=", "+", "-", "@", "\t", "\r"} else text
