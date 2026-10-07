"""HTTP surface of the user feedback: a public, write-only form endpoint and an admin-only inbox."""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from .analytics import RateLimited
from .feedback import (
    MAX_LIST,
    FeedbackRejected,
    FeedbackRepositoryError,
    FeedbackService,
    FeedbackSubmission,
    csv_cell,
)
from .request_origin import client_address

LOGGER = logging.getLogger(__name__)
TAIPEI = ZoneInfo("Asia/Taipei")
MAX_BODY_BYTES = 8 * 1024


class StatusChange(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    status: Literal["new", "read", "done"]
    note: str = Field(default="", max_length=1000)


def register_feedback_routes(
    app: FastAPI,
    service: FeedbackService,
    authenticated_admin: Callable[[Request], Any],
    optional_account: Callable[[Request], Any],
    *,
    static_dir: Path,
) -> None:
    def authorize(request: Request, response: Response) -> None:
        authenticated_admin(request)
        response.headers["Cache-Control"] = "private, no-store, max-age=0"

    @app.post("/feedback", status_code=201, include_in_schema=False)
    async def submit(request: Request, response: Response, payload: FeedbackSubmission) -> dict[str, bool]:
        """Public and write-only: the answer says nothing about what is stored or who can read it."""
        response.headers["Cache-Control"] = "no-store"
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="內容太長。")
        signed_in = optional_account(request) is not None
        try:
            await run_in_threadpool(
                lambda: service.submit(payload, client_key=client_address(request), signed_in=signed_in)
            )
        except RateLimited as exc:
            raise HTTPException(status_code=429, detail="送出太頻繁，請稍後再試。", headers={"Retry-After": "600"}) from exc
        except FeedbackRejected as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except FeedbackRepositoryError as exc:
            LOGGER.error("feedback could not be stored: %s", exc)
            raise HTTPException(status_code=503, detail="暫時無法儲存，請稍後再試。") from exc
        return {"ok": True}  # also for a bot: it learns nothing

    @app.get("/admin/feedback", include_in_schema=False)
    def inbox_page() -> FileResponse:
        # The page holds no data; every row comes from the admin-only list endpoint below.
        return FileResponse(static_dir / "feedback-admin.html", headers={"Cache-Control": "no-store"})

    @app.get("/admin/feedback/list", include_in_schema=False)
    async def inbox(
        request: Request, response: Response,
        status: Literal["new", "read", "done"] | None = Query(None),
        kind: Literal["suggestion", "bug", "praise", "other"] | None = Query(None),
    ) -> dict[str, Any]:
        authorize(request, response)
        try:
            everything = await run_in_threadpool(lambda: service.repository.list(limit=MAX_LIST))
        except FeedbackRepositoryError as exc:
            LOGGER.error("feedback could not be read: %s", exc)
            raise HTTPException(status_code=503, detail="暫時無法讀取用戶評價。") from exc
        counts = {"new": 0, "read": 0, "done": 0}
        for row in everything:
            counts[row.status] += 1
        items = [row for row in everything if (not status or row.status == status) and (not kind or row.kind == kind)]
        ratings = [row.rating for row in everything if row.rating]
        return {
            "items": [row.model_dump(mode="json") for row in items],
            "counts": counts,
            "total": len(everything),
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "rating_count": len(ratings),
            "truncated": len(everything) >= MAX_LIST,
        }

    @app.post("/admin/feedback/{feedback_id}/status", include_in_schema=False)
    async def change_status(feedback_id: str, change: StatusChange, request: Request, response: Response) -> dict[str, Any]:
        authorize(request, response)
        if not (8 <= len(feedback_id) <= 64 and feedback_id.isalnum()):
            raise HTTPException(status_code=404, detail="找不到這則評價。")
        try:
            record = await run_in_threadpool(
                lambda: service.repository.update(feedback_id, status=change.status, note=change.note)
            )
        except FeedbackRepositoryError as exc:
            LOGGER.error("feedback could not be updated: %s", exc)
            raise HTTPException(status_code=503, detail="暫時無法更新。") from exc
        if record is None:
            raise HTTPException(status_code=404, detail="找不到這則評價。")
        return record.model_dump(mode="json")

    @app.get("/admin/feedback/export.csv", include_in_schema=False)
    async def export_csv(request: Request, response: Response) -> Response:
        authorize(request, response)
        rows = await run_in_threadpool(lambda: service.repository.list(limit=MAX_LIST))
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["time_taipei", "kind", "rating", "message", "contact", "page", "school", "signed_in", "status", "note"])
        for row in rows:
            created: datetime = row.created_at.astimezone(TAIPEI)
            writer.writerow([csv_cell(value) for value in (
                created.strftime("%Y-%m-%d %H:%M:%S"), row.kind, row.rating or "", row.message, row.contact,
                row.route, row.home_school, "yes" if row.signed_in else "no", row.status, row.admin_note)])
        return Response(
            content="﻿" + buffer.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Cache-Control": "private, no-store, max-age=0",
                "Content-Disposition": 'attachment; filename="uniway-feedback.csv"',
            },
        )
