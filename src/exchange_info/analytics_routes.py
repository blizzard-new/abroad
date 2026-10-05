"""HTTP surface of the analytics system: a public, write-only collector and admin-only reports."""
from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from .analytics import (
    MAX_BODY_BYTES,
    AnalyticsService,
    ClientBatch,
    RateLimited,
)
from .analytics_report import TAIPEI, build_report, events_to_csv_rows
from .analytics_repository import MAX_FETCH_ROWS
from .request_origin import client_address

MAX_RANGE_DAYS = 400
EXPORT_LIMIT = 100_000


def resolve_window(days: int, start: date | None, end: date | None,
                   now: datetime | None = None) -> tuple[datetime, datetime]:
    """The report window as UTC instants covering whole Taipei days, ``end`` inclusive."""
    today = (now or datetime.now(timezone.utc)).astimezone(TAIPEI).date()
    last_day = end or today
    first_day = start or last_day - timedelta(days=days - 1)
    if first_day > last_day:
        raise HTTPException(status_code=422, detail="起始日不可晚於結束日。")
    if (last_day - first_day).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(status_code=422, detail=f"一次最多查詢 {MAX_RANGE_DAYS} 天。")
    start_at = datetime.combine(first_day, time.min, TAIPEI).astimezone(timezone.utc)
    end_at = datetime.combine(last_day + timedelta(days=1), time.min, TAIPEI).astimezone(timezone.utc)
    return start_at, end_at


def register_analytics_routes(
    app: FastAPI,
    service: AnalyticsService,
    authenticated_admin: Callable[[Request], Any],
    *,
    static_dir: Path,
    school_countries: Callable[[], Mapping[str, str]] | None = None,
) -> None:
    def authorize(request: Request, response: Response) -> None:
        authenticated_admin(request)
        response.headers["Cache-Control"] = "private, no-store, max-age=0"

    @app.post("/analytics/events", status_code=202, include_in_schema=False)
    async def collect(request: Request, response: Response) -> dict[str, int]:
        """Write-only and deliberately quiet: the browser tracker ignores every answer."""
        response.headers["Cache-Control"] = "no-store"
        if not service.enabled:
            return {"accepted": 0, "dropped": 0}
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="資料過大。")
        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="資料過大。")
        try:
            batch = ClientBatch.model_validate(json.loads(body))
        except (ValueError, ValidationError) as exc:
            raise HTTPException(status_code=422, detail="格式不正確。") from exc
        client = client_address(request)
        try:
            result = await run_in_threadpool(
                service.ingest, batch,
                user_agent=request.headers.get("user-agent", ""),
                headers=dict(request.headers), client_key=client,
            )
        except RateLimited as exc:
            raise HTTPException(status_code=429, detail="請稍後再試。", headers={"Retry-After": "60"}) from exc
        return result.model_dump()

    @app.get("/admin/analytics", include_in_schema=False)
    def dashboard() -> FileResponse:
        # The page holds no data; every number comes from the admin-only report endpoint below.
        return FileResponse(static_dir / "analytics-dashboard.html", headers={"Cache-Control": "no-store"})

    def load(start_at: datetime, end_at: datetime, limit: int):
        return service.repository.fetch_events(start_at, end_at, limit)  # type: ignore[union-attr]

    @app.get("/admin/analytics/report", include_in_schema=False)
    async def report(
        request: Request, response: Response,
        days: int = Query(30, ge=1, le=MAX_RANGE_DAYS),
        start: date | None = Query(None), end: date | None = Query(None),
        include_bots: bool = Query(False), school: str | None = Query(None, max_length=60),
    ) -> dict[str, Any]:
        authorize(request, response)
        if not service.enabled:
            raise HTTPException(status_code=503, detail="使用統計目前已關閉（EXCHANGE_ANALYTICS=off）。")
        start_at, end_at = resolve_window(days, start, end)
        span = end_at - start_at

        def compute() -> dict[str, Any]:
            service.flush_api_metrics()
            events, truncated = load(start_at - span, end_at, MAX_FETCH_ROWS)
            current = [e for e in events if e.occurred_at >= start_at]
            previous = [e for e in events if e.occurred_at < start_at]
            rows = service.repository.fetch_api_metrics(start_at, end_at)  # type: ignore[union-attr]
            countries: Mapping[str, str] = {}
            if school_countries is not None:
                try:
                    countries = school_countries()
                except Exception:  # the catalogue lookup only adds a country column
                    countries = {}
            return build_report(
                current, rows, start=start_at, end=end_at, previous_events=previous,
                include_bots=include_bots, home_school=school or None,
                school_countries=countries, truncated=truncated,
            )

        return await run_in_threadpool(compute)

    @app.get("/admin/analytics/export.csv", include_in_schema=False)
    async def export_csv(
        request: Request, response: Response,
        days: int = Query(30, ge=1, le=MAX_RANGE_DAYS),
        start: date | None = Query(None), end: date | None = Query(None),
        include_bots: bool = Query(False),
    ) -> Response:
        authorize(request, response)
        if not service.enabled:
            raise HTTPException(status_code=503, detail="使用統計目前已關閉（EXCHANGE_ANALYTICS=off）。")
        start_at, end_at = resolve_window(days, start, end)
        events, truncated = await run_in_threadpool(load, start_at, end_at, EXPORT_LIMIT)
        rows = events_to_csv_rows(e for e in events if include_bots or not e.is_bot)
        buffer = io.StringIO()
        csv.writer(buffer).writerows(rows)
        return Response(
            content="﻿" + buffer.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Cache-Control": "private, no-store, max-age=0",
                "Content-Disposition": 'attachment; filename="uniway-analytics-events.csv"',
                "X-Export-Truncated": "true" if truncated else "false",
            },
        )

    @app.post("/admin/analytics/purge", include_in_schema=False)
    async def purge(request: Request, response: Response,
                    older_than_days: int = Query(..., ge=30, le=3650)) -> dict[str, Any]:
        authorize(request, response)
        before = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        removed = await run_in_threadpool(service.purge_before, before)
        return {"before": before.isoformat(), "removed": removed}
