"""First-party, anonymous product analytics: what visitors do on the site, stored in our own database.

Design rules (see docs/analytics.md):

* No third-party scripts, no cookies. A random visitor id lives in the browser's localStorage and is
  never linked to an account; the server never stores IP addresses, e-mail addresses, names or the
  text typed into forms.
* Events are an allowlist. Unknown names, oversized batches and non-scalar properties are dropped, so a
  noisy or hostile client cannot grow the table or smuggle personal data into it.
* Search terms are kept only when they look like a school, country or topic, never when they look like
  a person (e-mail, phone, student number, link).
* Automated traffic is kept but flagged (``is_bot``) and left out of every report by default.
* Analytics must never break the site: every failure here is logged and swallowed.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Protocol

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("exchange_info.analytics")

VISITOR_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
SERVER_ACTOR = "server"

# Everything the browser tracker may send. Anything else is dropped.
CLIENT_EVENT_NAMES = frozenset({
    "session_start", "page_view", "engagement", "click", "rage_click", "outbound_click", "file_download",
    "school_open", "favorite_toggle", "search", "filter_change", "view_switch",
    "auth_dialog_open", "auth_start", "auth_success", "auth_cancel", "logout",
    "school_pick", "school_choose", "home_school_change",
    "advisor_submit", "document_action", "calendar_action", "planning_action",
    "community_composer_open", "community_topic", "board_follow", "theme_toggle",
    "web_vitals", "js_error", "unhandled_rejection", "api_error", "optout",
})
# Written only by the server, from actions it has verified itself; the public endpoint ignores them.
SERVER_EVENT_NAMES = frozenset({
    "account_created", "account_login", "school_choice", "post_created", "comment_created",
})

MAX_BATCH_EVENTS = 40
MAX_BODY_BYTES = 64 * 1024
MAX_EVENT_AGE_MS = 24 * 60 * 60 * 1000
MAX_PROPS = 16

_CONTROL = re.compile(r"[\x00-\x1f\x7f]+")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_LONG_NUMBER = re.compile(r"\d{8,}")
_PROP_KEY = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_URL = re.compile(r"https?://|www\.", re.IGNORECASE)
_PHONE = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d)")
_STUDENT_NUMBER = re.compile(r"^[A-Za-z]{1,2}\d{6,10}$")

BOT_PATTERN = re.compile(
    r"bot|crawl|spider|slurp|facebookexternalhit|embedly|preview|headless|phantom|python-requests|"
    r"python-urllib|curl/|wget/|httpclient|okhttp|go-http|libwww|lighthouse|pingdom|uptime|monitor|"
    r"scrapy|axios|node-fetch|java/",
    re.IGNORECASE,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- models


class AnalyticsEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    occurred_at: datetime
    visitor_id: str
    session_id: str
    name: str
    route: str = ""
    home_school: str = ""
    props: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    device_class: str = ""
    browser: str = ""
    os: str = ""
    country: str = ""
    language: str = ""
    timezone: str = ""
    viewport: str = ""
    display_mode: str = ""
    connection: str = ""
    referrer_host: str = ""
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    utm_term: str = ""
    utm_content: str = ""
    new_visitor: bool = False
    signed_in: bool = False
    school_basis: str = ""
    is_bot: bool = False

    @property
    def is_server(self) -> bool:
        return self.visitor_id == SERVER_ACTOR


class ApiMetricRow(BaseModel):
    """One hour of one endpoint's traffic; latency buckets are cumulative-free counts."""

    bucket_hour: datetime
    route: str
    method: str
    status_class: str
    request_count: int = 0
    total_ms: int = 0
    max_ms: int = 0
    le_100: int = 0
    le_300: int = 0
    le_1000: int = 0
    le_3000: int = 0
    gt_3000: int = 0

    @property
    def key(self) -> tuple[datetime, str, str, str]:
        return (self.bucket_hour, self.route, self.method, self.status_class)


class ClientEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    n: str = Field(min_length=2, max_length=40)
    r: str = Field(default="", max_length=120)
    a: int = Field(default=0, ge=0)
    p: dict[str, Any] = Field(default_factory=dict)


class ClientContext(BaseModel):
    model_config = ConfigDict(extra="ignore")

    visitor_id: str = Field(pattern=VISITOR_ID_PATTERN.pattern)
    session_id: str = Field(pattern=VISITOR_ID_PATTERN.pattern)
    new_visitor: bool = False
    language: str = Field(default="", max_length=24)
    timezone: str = Field(default="", max_length=64)
    viewport: str = Field(default="", max_length=16)
    display_mode: str = Field(default="", max_length=16)
    connection: str = Field(default="", max_length=16)
    referrer_host: str = Field(default="", max_length=120)
    utm: dict[str, Any] = Field(default_factory=dict)
    automated: bool = False
    school: str = Field(default="", max_length=60)
    signed_in: bool = False
    school_basis: str = Field(default="", max_length=24)


class ClientBatch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    v: int = 1
    context: ClientContext
    events: list[ClientEvent] = Field(default_factory=list, max_length=MAX_BATCH_EVENTS)


class IngestResult(BaseModel):
    accepted: int = 0
    dropped: int = 0


class RateLimited(Exception):
    pass


class AnalyticsRepository(Protocol):
    backend_name: str

    def record_events(self, events: list[AnalyticsEvent]) -> int: ...

    def fetch_events(
        self, start: datetime, end: datetime, limit: int
    ) -> tuple[list[AnalyticsEvent], bool]: ...

    def record_api_metrics(self, rows: list[ApiMetricRow]) -> None: ...

    def fetch_api_metrics(self, start: datetime, end: datetime) -> list[ApiMetricRow]: ...

    def purge(self, before: datetime) -> dict[str, int]: ...


# --------------------------------------------------------------------------- sanitising


def clean_text(value: object, limit: int) -> str:
    text = _CONTROL.sub(" ", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def scrub_personal_text(text: str) -> str:
    """Mask the two things that most often leak into free text: e-mail addresses and long numbers."""
    return _LONG_NUMBER.sub("[number]", _EMAIL.sub("[email]", text))


def sanitize_search_term(value: object) -> str:
    """The term itself, or ``""`` when it looks like something personal rather than a topic."""
    text = clean_text(value, 80).lower()
    if len(text) < 2 or len(text) > 60:
        return ""
    if "@" in text or _URL.search(text) or _STUDENT_NUMBER.match(text.replace(" ", "")):
        return ""
    if _PHONE.search(text) and sum(ch.isdigit() for ch in text) >= 7:
        return ""
    return text


def normalize_route(value: object) -> str:
    text = clean_text(value, 80).lstrip("#/")
    text = re.split(r"[=?&]", text, maxsplit=1)[0]
    return text.strip("/ ") or ""


def clean_props(props: Mapping[str, Any]) -> dict[str, str | int | float | bool | None]:
    """Scalars only, at most MAX_PROPS of them, every string trimmed and scrubbed."""
    cleaned: dict[str, str | int | float | bool | None] = {}
    for key, value in props.items():
        if len(cleaned) >= MAX_PROPS:
            break
        if not isinstance(key, str) or not _PROP_KEY.match(key):
            continue
        if value is None or isinstance(value, bool):
            cleaned[key] = value
        elif isinstance(value, int):
            cleaned[key] = max(-10**12, min(10**12, value))
        elif isinstance(value, float):
            if math.isfinite(value):
                cleaned[key] = round(value, 3)
        elif isinstance(value, str):
            cleaned[key] = scrub_personal_text(clean_text(value, 160))
    return cleaned


MAX_PROPS_BYTES = 3000  # the database rejects a row whose props exceed 4 KB, which would drop its whole batch


def fit_props(props: dict[str, Any]) -> dict[str, Any]:
    """Drop the longest values until the serialised properties fit the database's row limit."""
    fitted = dict(props)
    while len(json.dumps(fitted, ensure_ascii=False).encode("utf-8")) > MAX_PROPS_BYTES and fitted:
        longest = max(fitted, key=lambda key: len(str(fitted[key])))
        del fitted[longest]
    return fitted


def _finish_props(name: str, props: dict[str, Any]) -> dict[str, Any]:
    if name in {"js_error", "unhandled_rejection"} and isinstance(props.get("message"), str):
        props["message"] = re.sub(r"https?://\S+", "[url]", props["message"])[:200]
    for key in ("path", "href"):
        if isinstance(props.get(key), str):
            props[key] = re.split(r"[?#]", props[key], maxsplit=1)[0][:100]
    return props


def parse_user_agent(user_agent: str) -> tuple[str, str, str, bool]:
    """(device_class, browser, os, is_bot) from a User-Agent; coarse on purpose."""
    ua = user_agent or ""
    is_bot = bool(BOT_PATTERN.search(ua)) or not ua
    lowered = ua.lower()
    if "ipad" in lowered or "tablet" in lowered or ("android" in lowered and "mobile" not in lowered):
        device = "tablet"
    elif "mobi" in lowered or "iphone" in lowered or "ipod" in lowered:
        device = "mobile"
    else:
        device = "desktop"
    if "Line/" in ua:
        browser = "Line (in-app)"
    elif "Instagram" in ua:
        browser = "Instagram (in-app)"
    elif "FBAN" in ua or "FBAV" in ua:
        browser = "Facebook (in-app)"
    elif "Edg/" in ua or "EdgA/" in ua or "EdgiOS/" in ua:
        browser = "Edge"
    elif "OPR/" in ua or "Opera" in ua:
        browser = "Opera"
    elif "SamsungBrowser" in ua:
        browser = "Samsung Internet"
    elif "Firefox/" in ua or "FxiOS/" in ua:
        browser = "Firefox"
    elif "CriOS/" in ua or "Chrome/" in ua:
        browser = "Chrome"
    elif "Safari/" in ua:
        browser = "Safari"
    else:
        browser = "Other"
    if "Windows" in ua:
        os_name = "Windows"
    elif "iPhone" in ua or "iPad" in ua or "iPod" in ua:
        os_name = "iOS"
    elif "Android" in ua:
        os_name = "Android"
    elif "Mac OS X" in ua or "Macintosh" in ua:
        os_name = "macOS"
    elif "CrOS" in ua:
        os_name = "ChromeOS"
    elif "Linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Other"
    return device, browser, os_name, is_bot


COUNTRY_HEADERS = ("cf-ipcountry", "cloudfront-viewer-country", "x-vercel-ip-country", "x-country-code")


def country_from_headers(headers: Mapping[str, str]) -> str:
    """A coarse country code when a CDN supplies one; the IP address itself is never read."""
    lowered = {key.lower(): value for key, value in headers.items()}
    for name in COUNTRY_HEADERS:
        value = (lowered.get(name) or "").strip().upper()
        if re.fullmatch(r"[A-Z]{2}", value) and value not in {"XX", "T1"}:
            return value
    return ""


def primary_language(*candidates: str) -> str:
    for candidate in candidates:
        tag = re.split(r"[,;]", candidate or "", maxsplit=1)[0].strip()
        if re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", tag):
            return tag[:24]
    return ""


def normalize_batch(
    batch: ClientBatch,
    *,
    user_agent: str,
    headers: Mapping[str, str],
    now: datetime | None = None,
) -> tuple[list[AnalyticsEvent], int]:
    """Turn a validated client batch into storable events; returns (events, dropped_count)."""
    now = now or utc_now()
    ctx = batch.context
    device, browser, os_name, ua_bot = parse_user_agent(user_agent)
    country = country_from_headers(headers)
    language = primary_language(ctx.language, headers.get("accept-language", ""))
    utm = {key: clean_text(ctx.utm.get(key, ""), 80).lower() for key in
           ("source", "medium", "campaign", "term", "content")}
    shared: dict[str, Any] = dict(
        visitor_id=ctx.visitor_id,
        session_id=ctx.session_id,
        device_class=device,
        browser=browser,
        os=os_name,
        country=country,
        language=language,
        timezone=clean_text(ctx.timezone, 64),
        viewport=clean_text(ctx.viewport, 16),
        display_mode=clean_text(ctx.display_mode, 16),
        connection=clean_text(ctx.connection, 16),
        referrer_host=clean_text(ctx.referrer_host, 120).lower(),
        utm_source=utm["source"],
        utm_medium=utm["medium"],
        utm_campaign=utm["campaign"],
        utm_term=utm["term"],
        utm_content=utm["content"],
        new_visitor=ctx.new_visitor,
        signed_in=ctx.signed_in,
        school_basis=clean_text(ctx.school_basis, 24),
        home_school=clean_text(ctx.school, 60),
        is_bot=ua_bot or ctx.automated,
    )
    events: list[AnalyticsEvent] = []
    dropped = 0
    for item in batch.events:
        if item.n not in CLIENT_EVENT_NAMES:
            dropped += 1
            continue
        age_ms = min(item.a, MAX_EVENT_AGE_MS)
        props = clean_props({k: v for k, v in item.p.items() if not (item.n == "search" and k == "q")})
        if item.n == "search":
            raw_term = item.p.get("q", "")
            term = sanitize_search_term(raw_term)
            props["q_len"] = len(clean_text(raw_term, 200))
            if term:
                props["q"] = term
            else:
                props["q_redacted"] = True
        props = fit_props(_finish_props(item.n, props))
        events.append(AnalyticsEvent(
            occurred_at=now - timedelta(milliseconds=age_ms),
            name=item.n,
            route=normalize_route(item.r),
            props=props,
            **shared,
        ))
    return events, dropped


# --------------------------------------------------------------------------- rate limiting


class RateLimiter:
    """Sliding window per client key; in memory, so nothing about a client is ever persisted."""

    def __init__(self, max_batches: int = 60, max_events: int = 600, window_seconds: float = 60.0,
                 max_keys: int = 5000) -> None:
        self.max_batches = max_batches
        self.max_events = max_events
        self.window = window_seconds
        self.max_keys = max_keys
        self._hits: dict[str, deque[tuple[float, int]]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, events: int, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            if len(self._hits) > self.max_keys:
                self._hits = {k: v for k, v in self._hits.items() if v and now - v[-1][0] < self.window}
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0][0] >= self.window:
                hits.popleft()
            if len(hits) >= self.max_batches or sum(count for _, count in hits) + events > self.max_events:
                return False
            hits.append((now, events))
            return True


# --------------------------------------------------------------------------- API metrics

LATENCY_BUCKETS = (("le_100", 100), ("le_300", 300), ("le_1000", 1000), ("le_3000", 3000))


def latency_bucket(duration_ms: float) -> str:
    for name, bound in LATENCY_BUCKETS:
        if duration_ms < bound:
            return name
    return "gt_3000"


def status_class(status: int) -> str:
    return f"{status // 100}xx" if 100 <= status < 600 else "other"


class ApiMetricsAggregator:
    """Counts requests per (hour, endpoint, method, status class) in memory until flushed."""

    def __init__(self) -> None:
        self._rows: dict[tuple[datetime, str, str, str], ApiMetricRow] = {}
        self._lock = threading.Lock()

    def record(self, route: str, method: str, status: int, duration_ms: float,
               now: datetime | None = None) -> None:
        now = now or utc_now()
        hour = now.replace(minute=0, second=0, microsecond=0)
        key = (hour, route[:120], method.upper()[:10], status_class(status))
        with self._lock:
            row = self._rows.get(key)
            if row is None:
                row = self._rows[key] = ApiMetricRow(
                    bucket_hour=hour, route=key[1], method=key[2], status_class=key[3])
            duration = max(0, int(duration_ms))
            row.request_count += 1
            row.total_ms += duration
            row.max_ms = max(row.max_ms, duration)
            setattr(row, latency_bucket(duration), getattr(row, latency_bucket(duration)) + 1)

    def drain(self) -> list[ApiMetricRow]:
        with self._lock:
            rows = list(self._rows.values())
            self._rows = {}
        return rows

    def restore(self, rows: list[ApiMetricRow]) -> None:
        """Put rows back after a failed flush so a database blip does not lose them."""
        with self._lock:
            for row in rows:
                existing = self._rows.get(row.key)
                if existing is None:
                    self._rows[row.key] = row
                    continue
                for field in ("request_count", "total_ms", "le_100", "le_300", "le_1000", "le_3000", "gt_3000"):
                    setattr(existing, field, getattr(existing, field) + getattr(row, field))
                existing.max_ms = max(existing.max_ms, row.max_ms)


# --------------------------------------------------------------------------- service


class AnalyticsService:
    def __init__(
        self,
        repository: AnalyticsRepository | None,
        *,
        enabled: bool = True,
        retention_days: int = 400,
        flush_seconds: float = 60.0,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.repository = repository
        self.enabled = bool(enabled and repository is not None)
        self.retention_days = max(30, retention_days)
        self.flush_seconds = flush_seconds
        self.rate_limiter = rate_limiter or RateLimiter()
        self.metrics = ApiMetricsAggregator()
        self._last_flush = time.monotonic()
        self._last_purge = float("-inf")  # the first collection after a restart also trims old rows
        self._flush_lock = threading.Lock()
        self._flush_pending = threading.Lock()

    @classmethod
    def from_environment(cls, repository: AnalyticsRepository | None,
                         environ: Mapping[str, str] | None = None) -> "AnalyticsService":
        values = os.environ if environ is None else environ
        enabled = values.get("EXCHANGE_ANALYTICS", "on").strip().lower() not in {"off", "0", "false", "no"}
        return cls(
            repository,
            enabled=enabled,
            retention_days=int(values.get("EXCHANGE_ANALYTICS_RETENTION_DAYS", "400") or 400),
            flush_seconds=float(values.get("EXCHANGE_ANALYTICS_FLUSH_SECONDS", "60") or 60),
        )

    @property
    def backend_name(self) -> str:
        return getattr(self.repository, "backend_name", "disabled") if self.enabled else "disabled"

    # -- ingestion

    def ingest(self, batch: ClientBatch, *, user_agent: str, headers: Mapping[str, str],
               client_key: str) -> IngestResult:
        if not self.enabled or not batch.events:
            return IngestResult()
        if not self.rate_limiter.allow(client_key, len(batch.events)):
            raise RateLimited()
        events, dropped = normalize_batch(batch, user_agent=user_agent, headers=headers)
        accepted = 0
        if events:
            try:
                accepted = self.repository.record_events(events)  # type: ignore[union-attr]
            except Exception:  # analytics must never take the site down
                logger.exception("analytics: could not store %d events", len(events))
                dropped += len(events)
        self.maybe_purge()
        return IngestResult(accepted=accepted, dropped=dropped)

    def emit(self, name: str, *, route: str = "", props: Mapping[str, Any] | None = None,
             home_school: str = "", signed_in: bool = True, school_basis: str = "") -> None:
        """Record something the server itself verified (a new account, a post). Never raises."""
        if not self.enabled or name not in SERVER_EVENT_NAMES:
            return
        try:
            self.repository.record_events([AnalyticsEvent(  # type: ignore[union-attr]
                occurred_at=utc_now(), visitor_id=SERVER_ACTOR, session_id=SERVER_ACTOR, name=name,
                route=normalize_route(route), home_school=clean_text(home_school, 60),
                props=fit_props(clean_props(props or {})), signed_in=signed_in,
                school_basis=clean_text(school_basis, 24), is_bot=False)])
        except Exception:
            logger.exception("analytics: could not store server event %s", name)

    # -- API metrics

    def record_request(self, route: str, method: str, status: int, duration_ms: float) -> None:
        if not self.enabled:
            return
        self.metrics.record(route, method, status, duration_ms)
        if (self.flush_seconds > 0 and time.monotonic() - self._last_flush >= self.flush_seconds
                and self._flush_pending.acquire(blocking=False)):
            try:
                threading.Thread(target=self._flush_in_background, daemon=True).start()
            except RuntimeError:
                self._flush_pending.release()
                logger.exception("analytics: could not start metrics flush")

    def _flush_in_background(self) -> None:
        try:
            self.flush_api_metrics()
        finally:
            self._flush_pending.release()

    def flush_api_metrics(self) -> int:
        if not self.enabled:
            return 0
        with self._flush_lock:
            self._last_flush = time.monotonic()
            rows = self.metrics.drain()
            if not rows:
                return 0
            try:
                self.repository.record_api_metrics(rows)  # type: ignore[union-attr]
            except Exception:
                logger.exception("analytics: could not store API metrics")
                self.metrics.restore(rows)
                return 0
            return sum(row.request_count for row in rows)

    # -- housekeeping

    def purge_before(self, before: datetime) -> dict[str, int]:
        if not self.enabled:
            return {}
        return self.repository.purge(before)  # type: ignore[union-attr]

    def maybe_purge(self) -> None:
        """Drop data past the retention window, at most once a day per process."""
        now = time.monotonic()
        if not self.enabled or now - self._last_purge < 24 * 3600:
            return
        self._last_purge = now
        try:
            self.purge_before(utc_now() - timedelta(days=self.retention_days))
        except Exception:
            logger.exception("analytics: retention purge failed")


# --------------------------------------------------------------------------- request metrics middleware

UNMEASURED_PATHS = frozenset({"/analytics/events", "/health"})


class ApiMetricsMiddleware:
    """Counts requests per endpoint and status; a plain ASGI middleware so it adds no buffering of bodies.

    (A BaseHTTPMiddleware would stream every static file through an extra in-memory pipe, which measurably
    slowed page loads.)
    """

    def __init__(self, app, service: "AnalyticsService") -> None:
        self.app = app
        self.service = service

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if (scope["type"] != "http" or not self.service.enabled or path.startswith("/static")
                or path in UNMEASURED_PATHS):
            await self.app(scope, receive, send)
            return
        started = time.perf_counter()
        status = 500

        async def send_and_note_status(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_and_note_status)
        finally:
            route = scope.get("route")
            self.service.record_request(
                getattr(route, "path", None) or "(unmatched)", scope.get("method", "GET"), status,
                (time.perf_counter() - started) * 1000,
            )
