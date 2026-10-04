from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Protocol
from uuid import uuid4

import requests
from pydantic import BaseModel, Field, ValidationError

from .supabase_keys import supabase_key_headers
from .models import (
    ApplicationWorkflowIssueReport,
    ApplicationWorkflowIssueReportReview,
    ApplicationWorkflowIssueReportStatus,
    utc_now,
)
from .settings import DEFAULT_DATA_DIR
from .storage import read_jsonl, storage_path_lock, write_jsonl


ISSUE_REPORT_RATE_LIMIT = 10
ISSUE_REPORT_RATE_WINDOW = timedelta(hours=1)
DEIDENTIFIED_PENDING_RETENTION = timedelta(days=90)
TERMINAL_REVIEW_REPLAY_RETENTION = timedelta(hours=24)


class WorkflowIssueReportRepositoryError(RuntimeError):
    pass


class WorkflowIssueReportMutationStatus(str, Enum):
    COMMITTED = "committed"
    REPORT_MISSING = "report_missing"
    STATUS_CONFLICT = "status_conflict"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    RATE_LIMITED = "rate_limited"
    ACCOUNT_MISSING = "account_missing"
    STUDENT_VERIFICATION_REQUIRED = "student_verification_required"
    INVALID_REQUEST = "invalid_request"


class WorkflowIssueReportReviewRecord(BaseModel):
    review: ApplicationWorkflowIssueReportReview
    reviewer_account_id: str | None
    mutation_id: str = Field(min_length=16, max_length=128)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class WorkflowIssueReportRecord(BaseModel):
    report: ApplicationWorkflowIssueReport
    reporter_account_id: str | None
    mutation_id: str = Field(min_length=16, max_length=128)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    reporter_deleted_at: datetime | None = None
    retained_until: datetime | None = None
    review_record: WorkflowIssueReportReviewRecord | None = None

    @property
    def public_report(self) -> ApplicationWorkflowIssueReport:
        review = self.review_record.review if self.review_record else None
        return self.report.model_copy(update={"review": review})


class WorkflowIssueReportSubmitMutation(BaseModel):
    mutation_id: str = Field(
        min_length=16,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    account_id: str = Field(min_length=8, max_length=128)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    report: ApplicationWorkflowIssueReport


class WorkflowIssueReportReviewMutation(BaseModel):
    mutation_id: str = Field(
        min_length=16,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    reviewer_account_id: str = Field(min_length=8, max_length=128)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    review: ApplicationWorkflowIssueReportReview


class WorkflowIssueReportMutationResult(BaseModel):
    status: WorkflowIssueReportMutationStatus
    report: ApplicationWorkflowIssueReport | None = None
    idempotent: bool = False
    retry_after_seconds: int | None = Field(default=None, ge=1)


class WorkflowIssueReportRepository(Protocol):
    backend_name: str

    def submit_report(
        self,
        request: WorkflowIssueReportSubmitMutation,
    ) -> WorkflowIssueReportMutationResult: ...

    def list_reports(
        self,
        status: ApplicationWorkflowIssueReportStatus | None = None,
    ) -> list[ApplicationWorkflowIssueReport]: ...

    def list_records(self) -> list[WorkflowIssueReportRecord]: ...

    def list_reviews(self) -> list[ApplicationWorkflowIssueReportReview]: ...

    def list_reports_for_account(
        self,
        account_id: str,
    ) -> list[ApplicationWorkflowIssueReport]: ...

    def review_report(
        self,
        request: WorkflowIssueReportReviewMutation,
    ) -> WorkflowIssueReportMutationResult: ...

    def deidentify_reporter(self, account_id: str) -> None: ...


class JsonlWorkflowIssueReportRepository:
    backend_name = "local-jsonl"

    def __init__(
        self,
        data_dir: Path = DEFAULT_DATA_DIR,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.path = Path(data_dir) / "processed" / "application_workflow_issue_reports.jsonl"
        self._clock = clock

    def _load_locked(self, *, now: datetime | None = None) -> list[WorkflowIssueReportRecord]:
        current = now or self._clock()
        records = read_jsonl(self.path, WorkflowIssueReportRecord)
        retained = [
            row
            for row in records
            if row.retained_until is None or row.retained_until > current
        ]
        if len(retained) != len(records):
            write_jsonl(self.path, retained)
        return retained

    def _save_locked(self, records: list[WorkflowIssueReportRecord]) -> None:
        write_jsonl(self.path, records)

    def submit_report(
        self,
        request: WorkflowIssueReportSubmitMutation,
    ) -> WorkflowIssueReportMutationResult:
        current = self._clock()
        with storage_path_lock(self.path):
            records = self._load_locked(now=current)
            existing = next(
                (
                    row
                    for row in records
                    if row.reporter_account_id == request.account_id
                    and row.mutation_id == request.mutation_id
                ),
                None,
            )
            if existing is not None:
                if existing.request_fingerprint != request.request_fingerprint:
                    return WorkflowIssueReportMutationResult(
                        status=WorkflowIssueReportMutationStatus.IDEMPOTENCY_CONFLICT
                    )
                return WorkflowIssueReportMutationResult(
                    status=WorkflowIssueReportMutationStatus.COMMITTED,
                    report=existing.public_report,
                    idempotent=True,
                )
            window_start = current - ISSUE_REPORT_RATE_WINDOW
            recent_count = sum(
                1
                for row in records
                if row.reporter_account_id == request.account_id
                and row.report.created_at >= window_start
            )
            if recent_count >= ISSUE_REPORT_RATE_LIMIT:
                return WorkflowIssueReportMutationResult(
                    status=WorkflowIssueReportMutationStatus.RATE_LIMITED,
                    retry_after_seconds=int(ISSUE_REPORT_RATE_WINDOW.total_seconds()),
                )
            safe_report = request.report.model_copy(
                update={
                    "status": ApplicationWorkflowIssueReportStatus.PENDING,
                    "created_at": current,
                    "updated_at": current,
                    "review": None,
                }
            )
            record = WorkflowIssueReportRecord(
                report=safe_report,
                reporter_account_id=request.account_id,
                mutation_id=request.mutation_id,
                request_fingerprint=request.request_fingerprint,
            )
            records.append(record)
            self._save_locked(records)
            return WorkflowIssueReportMutationResult(
                status=WorkflowIssueReportMutationStatus.COMMITTED,
                report=record.public_report,
            )

    def list_records(self) -> list[WorkflowIssueReportRecord]:
        with storage_path_lock(self.path):
            records = self._load_locked()
        return sorted(records, key=lambda row: row.report.created_at, reverse=True)

    def list_reports(
        self,
        status: ApplicationWorkflowIssueReportStatus | None = None,
    ) -> list[ApplicationWorkflowIssueReport]:
        reports = [row.public_report for row in self.list_records()]
        if status is not None:
            reports = [row for row in reports if row.status == status]
        return reports

    def list_reviews(self) -> list[ApplicationWorkflowIssueReportReview]:
        return [
            row.review_record.review
            for row in self.list_records()
            if row.review_record is not None
        ]

    def list_reports_for_account(
        self,
        account_id: str,
    ) -> list[ApplicationWorkflowIssueReport]:
        return [
            row.public_report
            for row in self.list_records()
            if row.reporter_account_id == account_id
        ]

    def review_report(
        self,
        request: WorkflowIssueReportReviewMutation,
    ) -> WorkflowIssueReportMutationResult:
        current = self._clock()
        with storage_path_lock(self.path):
            records = self._load_locked(now=current)
            for record in records:
                review_record = record.review_record
                if (
                    review_record is not None
                    and review_record.reviewer_account_id == request.reviewer_account_id
                    and review_record.mutation_id == request.mutation_id
                ):
                    if review_record.request_fingerprint != request.request_fingerprint:
                        return WorkflowIssueReportMutationResult(
                            status=WorkflowIssueReportMutationStatus.IDEMPOTENCY_CONFLICT
                        )
                    return WorkflowIssueReportMutationResult(
                        status=WorkflowIssueReportMutationStatus.COMMITTED,
                        report=record.public_report,
                        idempotent=True,
                    )
            target = next(
                (row for row in records if row.report.id == request.review.report_id),
                None,
            )
            if target is None:
                return WorkflowIssueReportMutationResult(
                    status=WorkflowIssueReportMutationStatus.REPORT_MISSING
                )
            if target.report.status != ApplicationWorkflowIssueReportStatus.PENDING:
                return WorkflowIssueReportMutationResult(
                    status=WorkflowIssueReportMutationStatus.STATUS_CONFLICT
                )
            safe_review = request.review.model_copy(
                update={"id": uuid4().hex, "reviewed_at": current}
            )
            target.review_record = WorkflowIssueReportReviewRecord(
                review=safe_review,
                reviewer_account_id=request.reviewer_account_id,
                mutation_id=request.mutation_id,
                request_fingerprint=request.request_fingerprint,
            )
            target.report = target.report.model_copy(
                update={
                    "status": request.review.status,
                    "updated_at": current,
                    "review": safe_review,
                }
            )
            if target.reporter_deleted_at is not None:
                replay_expiry = current + TERMINAL_REVIEW_REPLAY_RETENTION
                target.retained_until = min(
                    target.retained_until or replay_expiry,
                    replay_expiry,
                )
            self._save_locked(records)
            return WorkflowIssueReportMutationResult(
                status=WorkflowIssueReportMutationStatus.COMMITTED,
                report=target.public_report,
            )

    def deidentify_reporter(self, account_id: str) -> None:
        current = self._clock()
        with storage_path_lock(self.path):
            records = self._load_locked(now=current)
            retained: list[WorkflowIssueReportRecord] = []
            for record in records:
                review_record = record.review_record
                if (
                    review_record is not None
                    and review_record.reviewer_account_id == account_id
                ):
                    review_record = review_record.model_copy(
                        update={
                            "review": review_record.review.model_copy(
                                update={"reviewer_display_name": "已刪除管理員"}
                            ),
                            "reviewer_account_id": None,
                            "mutation_id": f"deleted-{uuid4().hex}",
                            "request_fingerprint": hashlib.sha256(
                                uuid4().bytes
                            ).hexdigest(),
                        }
                    )
                    record = record.model_copy(
                        update={
                            "report": record.report.model_copy(
                                update={"review": review_record.review}
                            ),
                            "review_record": review_record,
                        }
                    )
                if record.reporter_account_id == account_id:
                    if record.report.status != ApplicationWorkflowIssueReportStatus.PENDING:
                        continue
                    retained.append(
                        record.model_copy(
                            update={
                                "reporter_account_id": None,
                                "reporter_deleted_at": current,
                                "retained_until": current
                                + DEIDENTIFIED_PENDING_RETENTION,
                                "mutation_id": f"deleted-{uuid4().hex}",
                                "request_fingerprint": hashlib.sha256(
                                    uuid4().bytes
                                ).hexdigest(),
                                "review_record": review_record,
                            }
                        )
                    )
                    continue
                retained.append(record)
            self._save_locked(retained)


class SupabaseWorkflowIssueReportRepository:
    backend_name = "supabase"

    def __init__(
        self,
        url: str,
        service_role_key: str,
        *,
        request_func=requests.request,
    ) -> None:
        if not url.strip().casefold().startswith("https://"):
            raise WorkflowIssueReportRepositoryError("Supabase URL 必須使用 HTTPS。")
        self.url = url.rstrip("/")
        self.service_role_key = service_role_key
        self.request_func = request_func

    @property
    def headers(self) -> dict[str, str]:
        return {
            **supabase_key_headers(self.service_role_key),
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs):
        try:
            response = self.request_func(
                method,
                f"{self.url}{path}",
                headers={**self.headers, **kwargs.pop("headers", {})},
                timeout=20,
                **kwargs,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise WorkflowIssueReportRepositoryError(
                "Supabase 申請規定回報請求失敗。"
            ) from exc

    @staticmethod
    def _json(response):
        try:
            return response.json()
        except (TypeError, ValueError) as exc:
            raise WorkflowIssueReportRepositoryError(
                "Supabase 申請規定回報回應格式無效。"
            ) from exc

    @classmethod
    def _mutation_payload(
        cls,
        response,
        *,
        require_review: bool = False,
    ) -> tuple[dict, WorkflowIssueReportMutationStatus]:
        payload = cls._json(response)
        if not isinstance(payload, dict) or not isinstance(payload.get("status"), str):
            raise WorkflowIssueReportRepositoryError(
                "Supabase 申請規定回報回應格式無效。"
            )
        try:
            status = WorkflowIssueReportMutationStatus(payload["status"])
        except ValueError as exc:
            raise WorkflowIssueReportRepositoryError(
                "Supabase 申請規定回報回應格式無效。"
            ) from exc
        if status == WorkflowIssueReportMutationStatus.COMMITTED:
            if not isinstance(payload.get("report"), dict):
                raise WorkflowIssueReportRepositoryError(
                    "Supabase 申請規定回報回應格式無效。"
                )
            if require_review and not isinstance(payload.get("review"), dict):
                raise WorkflowIssueReportRepositoryError(
                    "Supabase 申請規定回報回應格式無效。"
                )
        return payload, status

    @staticmethod
    def _review_from_row(row: dict | None) -> WorkflowIssueReportReviewRecord | None:
        if isinstance(row, list):
            if len(row) > 1:
                raise WorkflowIssueReportRepositoryError(
                    "同一申請規定回報存在多筆終態審核。"
                )
            row = row[0] if row else None
        if not row:
            return None
        review = ApplicationWorkflowIssueReportReview.model_validate(
            {
                "id": row["id"],
                "report_id": row["report_id"],
                "status": row["status"],
                "note": row["note"],
                "reviewer_display_name": row["reviewer_display_name"],
                "reviewed_at": row["reviewed_at"],
            }
        )
        return WorkflowIssueReportReviewRecord(
            review=review,
            reviewer_account_id=row.get("reviewer_account_id"),
            mutation_id=row["mutation_id"],
            request_fingerprint=row["request_fingerprint"],
        )

    @classmethod
    def _record_from_row(
        cls,
        row: dict,
        review_row: dict | None = None,
    ) -> WorkflowIssueReportRecord:
        try:
            review_record = cls._review_from_row(review_row or row.get("review"))
            report = ApplicationWorkflowIssueReport.model_validate(
                {
                    "id": row["id"],
                    "workflow_key": row["workflow_key"],
                    "workflow_id": row["workflow_id"],
                    "workflow_version": row["workflow_version"],
                    "workflow_snapshot": row["workflow_snapshot"],
                    "home_school": row["home_school"],
                    "school_name": row["school_name"],
                    "step_rule_id": row.get("step_rule_id"),
                    "step_title": row.get("step_title"),
                    "college": row.get("college"),
                    "department": row.get("department"),
                    "academic_year": row.get("academic_year"),
                    "application_round": row.get("application_round"),
                    "category": row["category"],
                    "description": row["description"],
                    "official_source_url": row["official_source_url"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "review": review_record.review if review_record else None,
                }
            )
            return WorkflowIssueReportRecord(
                report=report,
                reporter_account_id=row.get("reporter_account_id"),
                mutation_id=row["mutation_id"],
                request_fingerprint=row["request_fingerprint"],
                reporter_deleted_at=row.get("reporter_deleted_at"),
                retained_until=row.get("retained_until"),
                review_record=review_record,
            )
        except WorkflowIssueReportRepositoryError:
            raise
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise WorkflowIssueReportRepositoryError(
                "Supabase 申請規定回報回應格式無效。"
            ) from exc

    def submit_report(
        self,
        request: WorkflowIssueReportSubmitMutation,
    ) -> WorkflowIssueReportMutationResult:
        response, status = self._mutation_payload(self._request(
            "POST",
            "/rest/v1/rpc/exchange_submit_application_workflow_issue_report",
            json={
                "p_account_id": request.account_id,
                "p_mutation_id": request.mutation_id,
                "p_request_fingerprint": request.request_fingerprint,
                "p_report": request.report.model_dump(
                    mode="json",
                    exclude={"id", "status", "created_at", "updated_at", "review"},
                ),
                "p_rate_limit": ISSUE_REPORT_RATE_LIMIT,
                "p_rate_window_seconds": int(ISSUE_REPORT_RATE_WINDOW.total_seconds()),
            },
        ))
        record = self._record_from_row(response["report"]) if response.get("report") else None
        return WorkflowIssueReportMutationResult(
            status=status,
            report=record.public_report if record else None,
            idempotent=bool(response.get("idempotent")),
            retry_after_seconds=response.get("retry_after_seconds"),
        )

    def _list_records(
        self,
        *,
        status: ApplicationWorkflowIssueReportStatus | None = None,
        reporter_account_id: str | None = None,
    ) -> list[WorkflowIssueReportRecord]:
        self._request(
            "POST",
            "/rest/v1/rpc/exchange_purge_expired_application_workflow_issue_reports",
            json={},
        )
        base_params: dict[str, object] = {
            "select": "*,review:application_workflow_issue_report_reviews(*)",
            "order": "created_at.desc",
        }
        if status is not None:
            base_params["status"] = f"eq.{status.value}"
        if reporter_account_id is not None:
            base_params["reporter_account_id"] = f"eq.{reporter_account_id}"
        rows: list[dict] = []
        page_size = 500
        while True:
            page = self._json(
                self._request(
                    "GET",
                    "/rest/v1/application_workflow_issue_reports",
                    params={
                        **base_params,
                        "limit": page_size,
                        "offset": len(rows),
                    },
                )
            )
            if not isinstance(page, list):
                raise WorkflowIssueReportRepositoryError(
                    "Supabase 申請規定回報列表格式無效。"
                )
            rows.extend(page)
            if len(page) < page_size:
                break
        return [self._record_from_row(row) for row in rows]

    def list_records(self) -> list[WorkflowIssueReportRecord]:
        return self._list_records()

    def list_reports(
        self,
        status: ApplicationWorkflowIssueReportStatus | None = None,
    ) -> list[ApplicationWorkflowIssueReport]:
        return [row.public_report for row in self._list_records(status=status)]

    def list_reviews(self) -> list[ApplicationWorkflowIssueReportReview]:
        return [
            row.review_record.review
            for row in self.list_records()
            if row.review_record is not None
        ]

    def list_reports_for_account(
        self,
        account_id: str,
    ) -> list[ApplicationWorkflowIssueReport]:
        return [
            row.public_report
            for row in self._list_records(reporter_account_id=account_id)
        ]

    def review_report(
        self,
        request: WorkflowIssueReportReviewMutation,
    ) -> WorkflowIssueReportMutationResult:
        response, status = self._mutation_payload(self._request(
            "POST",
            "/rest/v1/rpc/exchange_review_application_workflow_issue_report",
            json={
                "p_reviewer_account_id": request.reviewer_account_id,
                "p_mutation_id": request.mutation_id,
                "p_request_fingerprint": request.request_fingerprint,
                "p_review": {
                    "report_id": request.review.report_id,
                    "status": request.review.status.value,
                    "note": request.review.note,
                },
            },
        ), require_review=True)
        record = (
            self._record_from_row(response["report"], response.get("review"))
            if response.get("report")
            else None
        )
        return WorkflowIssueReportMutationResult(
            status=status,
            report=record.public_report if record else None,
            idempotent=bool(response.get("idempotent")),
        )

    def deidentify_reporter(self, account_id: str) -> None:
        # Production account deletion is protected by the database trigger in
        # the same transaction as the account row deletion.  Calling this
        # method separately would create a cross-request partial state.
        return None


def create_workflow_issue_report_repository(
    data_dir: Path = DEFAULT_DATA_DIR,
    environ: Mapping[str, str] | None = None,
) -> WorkflowIssueReportRepository:
    values = os.environ if environ is None else environ
    environment = values.get("EXCHANGE_ENVIRONMENT", "development").strip().casefold()
    backend = values.get("EXCHANGE_WORKFLOW_ISSUE_REPORT_BACKEND", "auto").strip().casefold()
    url = (values.get("EXCHANGE_SUPABASE_URL") or values.get("SUPABASE_URL") or "").strip()
    key = (
        values.get("EXCHANGE_SUPABASE_SECRET_KEY")
        or values.get("SUPABASE_SECRET_KEY")
        or values.get("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()
    if backend not in {"auto", "jsonl", "supabase"}:
        raise WorkflowIssueReportRepositoryError(
            "EXCHANGE_WORKFLOW_ISSUE_REPORT_BACKEND 只能是 auto、jsonl 或 supabase。"
        )
    if bool(url) != bool(key):
        raise WorkflowIssueReportRepositoryError(
            "Supabase 申請規定回報持久層必須同時設定 URL 與 server secret。"
        )
    if backend == "supabase" or (backend == "auto" and url and key):
        if not url or not key:
            raise WorkflowIssueReportRepositoryError(
                "Supabase 申請規定回報持久層必須同時設定 URL 與 server secret。"
            )
        return SupabaseWorkflowIssueReportRepository(url, key)
    if environment in {"production", "prod"}:
        raise WorkflowIssueReportRepositoryError(
            "正式環境禁止使用 JSONL 申請規定回報持久層。"
        )
    return JsonlWorkflowIssueReportRepository(data_dir)


def canonical_issue_report_fingerprint(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
