"""Storage for analytics events: JSONL files for development, Supabase (PostgREST) in production."""
from __future__ import annotations

import os
import threading
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping

import requests

from .supabase_keys import supabase_key_headers
from .analytics import AnalyticsEvent, ApiMetricRow

DEFAULT_DATA_DIR = Path("data")
PAGE_SIZE = 1000          # PostgREST returns at most 1000 rows per request on Supabase
INSERT_CHUNK = 200
MAX_FETCH_ROWS = 200_000  # a report reads at most this many events and says so when it stops there


class AnalyticsRepositoryError(RuntimeError):
    pass


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


# --------------------------------------------------------------------------- JSONL


class JsonlAnalyticsRepository:
    """Month-partitioned files under ``<data>/analytics``; one writer process at a time."""

    backend_name = "jsonl"

    def __init__(self, data_dir: Path) -> None:
        self.directory = Path(data_dir) / "analytics"  # created on the first write
        self._lock = threading.RLock()

    @property
    def metrics_path(self) -> Path:
        return self.directory / "api-hourly.jsonl"

    @staticmethod
    def _month(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y%m")

    def _event_files(self) -> list[Path]:
        return sorted(self.directory.glob("events-*.jsonl"))

    def record_events(self, events: list[AnalyticsEvent]) -> int:
        grouped: dict[str, list[str]] = defaultdict(list)
        for event in events:
            grouped[self._month(event.occurred_at)].append(event.model_dump_json())
        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            for month, lines in grouped.items():
                with (self.directory / f"events-{month}.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write("\n".join(lines) + "\n")
        return len(events)

    def fetch_events(self, start: datetime, end: datetime, limit: int) -> tuple[list[AnalyticsEvent], bool]:
        first, last = self._month(start), self._month(end)
        found: list[AnalyticsEvent] = []
        with self._lock:
            for path in self._event_files():
                month = path.stem.removeprefix("events-")
                if not first <= month <= last:
                    continue
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    event = AnalyticsEvent.model_validate_json(line)
                    if start <= event.occurred_at < end:
                        found.append(event)
        found.sort(key=lambda event: (event.occurred_at, event.id))
        return found[:limit], len(found) > limit

    def _read_metrics(self) -> dict[tuple, ApiMetricRow]:
        rows: dict[tuple, ApiMetricRow] = {}
        if self.metrics_path.exists():
            for line in self.metrics_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = ApiMetricRow.model_validate_json(line)
                    rows[row.key] = row
        return rows

    def _write_metrics(self, rows: Mapping[tuple, ApiMetricRow]) -> None:
        temporary = self.metrics_path.with_suffix(".tmp")
        temporary.write_text("".join(row.model_dump_json() + "\n" for row in rows.values()),
                             encoding="utf-8", newline="\n")
        os.replace(temporary, self.metrics_path)

    def record_api_metrics(self, rows: list[ApiMetricRow]) -> None:
        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            merged = self._read_metrics()
            for row in rows:
                current = merged.get(row.key)
                if current is None:
                    merged[row.key] = row.model_copy()
                    continue
                for field in ("request_count", "total_ms", "le_100", "le_300", "le_1000", "le_3000", "gt_3000"):
                    setattr(current, field, getattr(current, field) + getattr(row, field))
                current.max_ms = max(current.max_ms, row.max_ms)
            self._write_metrics(merged)

    def fetch_api_metrics(self, start: datetime, end: datetime) -> list[ApiMetricRow]:
        with self._lock:
            return [row for row in self._read_metrics().values() if start <= row.bucket_hour < end]

    def purge(self, before: datetime) -> dict[str, int]:
        removed_events = 0
        with self._lock:
            for path in self._event_files():
                kept: list[str] = []
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    if AnalyticsEvent.model_validate_json(line).occurred_at < before:
                        removed_events += 1
                    else:
                        kept.append(line)
                if kept:
                    path.write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")
                else:
                    path.unlink()
            metrics = self._read_metrics()
            kept_metrics = {key: row for key, row in metrics.items() if row.bucket_hour >= before}
            if len(kept_metrics) != len(metrics):
                self._write_metrics(kept_metrics)
        return {"events": removed_events, "api_hourly": len(metrics) - len(kept_metrics)}


# --------------------------------------------------------------------------- Supabase


class SupabaseAnalyticsRepository:
    backend_name = "supabase"
    EVENTS = "exchange_analytics_events"
    API_HOURLY = "exchange_analytics_api_hourly"

    def __init__(self, url: str, service_role_key: str, *,
                 request_func: Callable[..., requests.Response] = requests.request) -> None:
        if not url.strip().casefold().startswith("https://"):
            raise AnalyticsRepositoryError("Supabase URL 必須使用 HTTPS。")
        self.url = url.rstrip("/")
        self.service_role_key = service_role_key
        self.request_func = request_func

    def _request(self, method: str, path: str, **kwargs):
        headers = {
            **supabase_key_headers(self.service_role_key),
            "Content-Type": "application/json",
            **kwargs.pop("headers", {}),
        }
        try:
            response = self.request_func(method, f"{self.url}{path}", headers=headers, timeout=20, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise AnalyticsRepositoryError("Supabase 使用統計請求失敗。") from exc

    @staticmethod
    def _rows(response) -> list[dict]:
        try:
            rows = response.json()
        except (TypeError, ValueError) as exc:
            raise AnalyticsRepositoryError("Supabase 使用統計回應格式無效。") from exc
        if not isinstance(rows, list):
            raise AnalyticsRepositoryError("Supabase 使用統計回應格式無效。")
        return rows

    def record_events(self, events: list[AnalyticsEvent]) -> int:
        for index in range(0, len(events), INSERT_CHUNK):
            chunk = events[index:index + INSERT_CHUNK]
            self._request(
                "POST", f"/rest/v1/{self.EVENTS}?on_conflict=id",
                json=[event.model_dump(mode="json") for event in chunk],
                headers={"Prefer": "return=minimal,resolution=ignore-duplicates"},
            )
        return len(events)

    def _paged(self, table: str, params: list[tuple[str, str]], limit: int) -> tuple[list[dict], bool]:
        """Read up to ``limit`` rows (one extra tells whether more exist) in PostgREST-sized pages."""
        rows: list[dict] = []
        while len(rows) <= limit:
            want = min(PAGE_SIZE, limit + 1 - len(rows))
            page = self._rows(self._request(
                "GET", f"/rest/v1/{table}",
                params=[*params, ("limit", str(want)), ("offset", str(len(rows)))],
            ))
            rows.extend(page)
            if len(page) < want:
                break
        return rows[:limit], len(rows) > limit

    def fetch_events(self, start: datetime, end: datetime, limit: int) -> tuple[list[AnalyticsEvent], bool]:
        rows, truncated = self._paged(
            self.EVENTS,
            [("select", "*"), ("occurred_at", f"gte.{_iso(start)}"), ("occurred_at", f"lt.{_iso(end)}"),
             ("order", "occurred_at.asc,id.asc")],
            limit,
        )
        return [AnalyticsEvent.model_validate(row) for row in rows], truncated

    def record_api_metrics(self, rows: list[ApiMetricRow]) -> None:
        self._request(
            "POST", "/rest/v1/rpc/exchange_analytics_add_api_hourly",
            json={"p_rows": [row.model_dump(mode="json") for row in rows]},
        )

    def fetch_api_metrics(self, start: datetime, end: datetime) -> list[ApiMetricRow]:
        rows, _ = self._paged(
            self.API_HOURLY,
            [("select", "*"), ("bucket_hour", f"gte.{_iso(start)}"), ("bucket_hour", f"lt.{_iso(end)}"),
             ("order", "bucket_hour.asc")],
            MAX_FETCH_ROWS,
        )
        return [ApiMetricRow.model_validate(row) for row in rows]

    def purge(self, before: datetime) -> dict[str, int]:
        response = self._request("POST", "/rest/v1/rpc/exchange_analytics_purge", json={"p_before": _iso(before)})
        payload = response.json()
        return {key: int(value) for key, value in payload.items()} if isinstance(payload, dict) else {}


# --------------------------------------------------------------------------- factory


def create_analytics_repository(
    data_dir: Path = DEFAULT_DATA_DIR,
    environ: Mapping[str, str] | None = None,
):
    values = os.environ if environ is None else environ
    environment = values.get("EXCHANGE_ENVIRONMENT", "development").strip().casefold()
    backend = values.get("EXCHANGE_ANALYTICS_BACKEND", "auto").strip().casefold()
    url = (values.get("EXCHANGE_SUPABASE_URL") or values.get("SUPABASE_URL") or "").strip()
    key = (
        values.get("EXCHANGE_SUPABASE_SECRET_KEY")
        or values.get("SUPABASE_SECRET_KEY")
        or values.get("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()
    if backend not in {"auto", "jsonl", "supabase"}:
        raise AnalyticsRepositoryError("EXCHANGE_ANALYTICS_BACKEND 只能是 auto、jsonl 或 supabase。")
    if backend == "supabase" or (backend == "auto" and url and key):
        if not url or not key:
            raise AnalyticsRepositoryError("Supabase 使用統計持久層必須同時設定 URL 與 server secret。")
        return SupabaseAnalyticsRepository(url, key)
    if environment in {"production", "prod"}:
        raise AnalyticsRepositoryError("正式環境禁止使用 JSONL 使用統計持久層。")
    return JsonlAnalyticsRepository(data_dir)
