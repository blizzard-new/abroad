"""Persistent job queue, lease fencing tokens, idempotent effects, and outage/budget/disk guards (Spec Sections 3.5, 6, 10)."""

from __future__ import annotations

import hashlib
import shutil
import threading
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .contracts import canonical_json_hash, utc_now

ALLOWED_WORKER_JOB_TYPES = frozenset(
    {"discover", "fetch", "extract", "validate", "reconcile", "recheck_health", "reprocess"}
)


class JobStatus(str, Enum):
    QUEUED = "queued"
    LEASED = "leased"
    SUCCEEDED = "succeeded"
    RETRY_WAIT = "retry_wait"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class StaleLeaseError(RuntimeError):
    """Raised when a worker attempts to heartbeat or commit with an expired lease or superseded fencing token (T10)."""


class DiskWatermarkError(RuntimeError):
    """Raised when free disk space drops below the safety watermark (Spec 3.5 / T32)."""


class BudgetExhaustedError(RuntimeError):
    """Raised when paid OCR/model budget is exhausted or unconfigured (Spec 10.2 / T24)."""


class JobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"job_{uuid4().hex[:16]}")
    job_type: Literal["discover", "fetch", "extract", "validate", "reconcile", "recheck_health", "reprocess"]
    resource_id: str | None = None
    snapshot_id: str | None = None
    entity_scope: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    dedupe_key: str
    status: JobStatus = JobStatus.QUEUED
    priority: int = 100
    scheduled_at: datetime = Field(default_factory=utc_now)
    attempts: int = 0
    max_attempts: int = 5
    lease_until: datetime | None = None
    lease_token: int = 0
    worker_id: str | None = None
    error_class: str | None = None
    error_detail: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class JobEffectReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    effect_key: str
    job_id: str
    lease_token: int
    result_id: str
    result_payload: dict[str, Any] = Field(default_factory=dict)
    committed_at: datetime = Field(default_factory=utc_now)


def build_fetch_dedupe_key(resource_id: str, window_bucket: str, policy_version: str = "v1") -> str:
    raw = f"fetch|{resource_id}|{window_bucket}|{policy_version}"
    return "dk_fetch_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def build_extract_dedupe_key(
    blob_sha256: str,
    parser_name: str,
    parser_version: str,
    schema_version: str,
    input_context_hash: str,
) -> str:
    raw = f"extract|{blob_sha256}|{parser_name}|{parser_version}|{schema_version}|{input_context_hash}"
    return "dk_extract_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def build_candidate_dedupe_key(
    entity_scope: str,
    field_path: str,
    typed_value: Any,
    value_state: str,
    unit: str | None,
    effective_scope: dict[str, Any],
    evidence_set_hash: str,
) -> str:
    raw = canonical_json_hash(
        {
            "entity_scope": entity_scope,
            "field_path": field_path,
            "typed_value": typed_value,
            "value_state": value_state,
            "unit": unit,
            "effective_scope": effective_scope,
            "evidence_set_hash": evidence_set_hash,
        }
    )
    return "dk_cand_" + raw[:24]


class BudgetAndDiskGuard:
    """Enforces disk low-watermark and paid OCR/model budget hard caps before expensive operations (Spec 3.5, 10.2)."""

    def __init__(
        self,
        *,
        storage_root: Path,
        min_free_bytes: int = 5 * 1024 * 1024 * 1024,  # 5 GiB safety default
        external_ai_opted_in: bool = False,
        monthly_budget_twd: float = 0.0,
        rate_table_verified_at: str | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self.storage_root = storage_root
        self.min_free_bytes = min_free_bytes
        self.external_ai_opted_in = external_ai_opted_in
        self.monthly_budget_twd = monthly_budget_twd
        self.rate_table_verified_at = rate_table_verified_at
        self.settled_spend_twd: float = 0.0
        self.reserved_inflight_twd: float = 0.0
        self.simulated_free_bytes: int | None = None
        self.alerts: list[str] = []

    def check_disk_watermark(self, required_bytes: int = 0) -> int:
        if self.simulated_free_bytes is not None:
            free_bytes = self.simulated_free_bytes
        else:
            self.storage_root.mkdir(parents=True, exist_ok=True)
            free_bytes = shutil.disk_usage(self.storage_root).free
        if free_bytes - required_bytes < self.min_free_bytes:
            raise DiskWatermarkError(
                f"Free disk space ({free_bytes} bytes) below safety watermark ({self.min_free_bytes} bytes); new downloads/extractions paused."
            )
        return free_bytes

    def reserve_paid_work(self, estimated_cost_twd: float) -> str:
        """Reserve budget for concurrent paid OCR/LLM work; fail closed if disabled or >= 100% cap (Spec 10.2 / T24, T34)."""
        with self._lock:
            if not self.external_ai_opted_in or self.monthly_budget_twd <= 0 or not self.rate_table_verified_at:
                raise BudgetExhaustedError(
                    "External paid OCR/LLM is disabled by default or missing verified budget/rate configuration."
                )
            projected = self.settled_spend_twd + self.reserved_inflight_twd + estimated_cost_twd
            if projected > self.monthly_budget_twd:
                if "budget_100_percent_paused" not in self.alerts:
                    self.alerts.append("budget_100_percent_paused")
                raise BudgetExhaustedError(
                    f"Paid work blocked: projected spend {projected:.2f} TWD exceeds hard cap {self.monthly_budget_twd:.2f} TWD."
                )
            self.reserved_inflight_twd += estimated_cost_twd
            ratio = (self.settled_spend_twd + self.reserved_inflight_twd) / self.monthly_budget_twd
            if ratio >= 0.8 and "budget_80_percent_warning" not in self.alerts:
                self.alerts.append("budget_80_percent_warning")
            return f"res_{uuid4().hex[:12]}"

    def settle_paid_work(self, reserved_cost_twd: float, actual_cost_twd: float) -> None:
        with self._lock:
            self.reserved_inflight_twd = max(0.0, self.reserved_inflight_twd - reserved_cost_twd)
            self.settled_spend_twd += max(0.0, actual_cost_twd)


class PersistentJobQueue:
    """Transactional job queue with lease fencing tokens, deduplication, and outage recovery (Spec Section 6)."""

    def __init__(self, *, clock: Any = None) -> None:
        self._lock = threading.RLock()
        self._clock = clock or utc_now
        self._jobs: dict[str, JobRecord] = {}
        self._effects: dict[str, JobEffectReceipt] = {}
        self._domain_last_request_at: dict[str, datetime] = {}

    def now(self) -> datetime:
        return self._clock()

    def enqueue(
        self,
        *,
        job_type: str,
        dedupe_key: str,
        resource_id: str | None = None,
        snapshot_id: str | None = None,
        entity_scope: str | None = None,
        payload: dict[str, Any] | None = None,
        priority: int = 100,
        scheduled_at: datetime | None = None,
        boost_if_exists: bool = False,
    ) -> JobRecord:
        if job_type not in ALLOWED_WORKER_JOB_TYPES:
            raise ValueError(f"Job type '{job_type}' is forbidden in worker queue (publish must go through protected admin flow)")

        with self._lock:
            now_dt = self.now()
            # Coalesce pending/queued jobs with the same dedupe_key (Spec 6.3)
            for existing in self._jobs.values():
                if existing.dedupe_key == dedupe_key and existing.status in {JobStatus.QUEUED, JobStatus.RETRY_WAIT}:
                    if boost_if_exists and priority > existing.priority:
                        existing.priority = priority
                        existing.scheduled_at = min(existing.scheduled_at, scheduled_at or now_dt)
                        existing.updated_at = now_dt
                    return existing.model_copy(deep=True)

            job = JobRecord(
                job_type=job_type,  # type: ignore[arg-type]
                resource_id=resource_id,
                snapshot_id=snapshot_id,
                entity_scope=entity_scope,
                payload=dict(payload or {}),
                dedupe_key=dedupe_key,
                status=JobStatus.QUEUED,
                priority=priority,
                scheduled_at=scheduled_at or now_dt,
                created_at=now_dt,
                updated_at=now_dt,
            )
            self._jobs[job.id] = job
            return job.model_copy(deep=True)

    def claim_next(self, *, worker_id: str, lease_seconds: int = 120) -> JobRecord | None:
        if not worker_id or not worker_id.strip():
            raise ValueError("worker_id is required")
        with self._lock:
            now_dt = self.now()
            self._reclaim_expired_unlocked(now_dt)

            candidates = [
                job
                for job in self._jobs.values()
                if job.status == JobStatus.QUEUED and job.scheduled_at <= now_dt
            ]
            if not candidates:
                return None

            candidates.sort(key=lambda j: (-j.priority, j.scheduled_at, j.id))
            chosen = candidates[0]
            chosen.status = JobStatus.LEASED
            chosen.worker_id = worker_id
            chosen.lease_token += 1
            chosen.lease_until = now_dt + timedelta(seconds=lease_seconds)
            chosen.attempts += 1
            chosen.updated_at = now_dt
            return chosen.model_copy(deep=True)

    def _verify_active_lease_unlocked(self, job_id: str, worker_id: str, lease_token: int, now_dt: datetime) -> JobRecord:
        job = self._jobs.get(job_id)
        if (
            job is None
            or job.status != JobStatus.LEASED
            or job.worker_id != worker_id
            or job.lease_token != lease_token
            or job.lease_until is None
            or job.lease_until <= now_dt
        ):
            raise StaleLeaseError(
                f"Rejected write for job {job_id}: lease expired or fencing token {lease_token} superseded"
            )
        return job

    def heartbeat(self, *, job_id: str, worker_id: str, lease_token: int, lease_seconds: int = 120) -> JobRecord:
        with self._lock:
            now_dt = self.now()
            job = self._verify_active_lease_unlocked(job_id, worker_id, lease_token, now_dt)
            job.lease_until = now_dt + timedelta(seconds=lease_seconds)
            job.updated_at = now_dt
            return job.model_copy(deep=True)

    def complete_with_effect(
        self,
        *,
        job_id: str,
        worker_id: str,
        lease_token: int,
        effect_key: str,
        result_id: str,
        result_payload: dict[str, Any] | None = None,
    ) -> tuple[JobEffectReceipt, bool]:
        """Atomically record side-effect and complete job, or return prior receipt if effect_key already committed (Spec 6.2, 6.4, T09, T10)."""
        with self._lock:
            now_dt = self.now()
            # If the DB transaction previously committed this exact effect_key but the response was lost,
            # return the original receipt without duplicating work (Spec 6.4).
            existing_receipt = self._effects.get(effect_key)
            if existing_receipt is not None:
                return existing_receipt.model_copy(deep=True), True

            # Even if no new worker has claimed the job yet, an expired worker MUST NOT write visible results (Spec 6.2 / T10)!
            job = self._verify_active_lease_unlocked(job_id, worker_id, lease_token, now_dt)

            receipt = JobEffectReceipt(
                effect_key=effect_key,
                job_id=job.id,
                lease_token=lease_token,
                result_id=result_id,
                result_payload=dict(result_payload or {}),
                committed_at=now_dt,
            )
            self._effects[effect_key] = receipt
            job.status = JobStatus.SUCCEEDED
            job.lease_until = None
            job.updated_at = now_dt
            return receipt.model_copy(deep=True), False

    def fail_or_retry(
        self,
        *,
        job_id: str,
        worker_id: str,
        lease_token: int,
        error_class: str,
        error_detail: str,
        should_retry: bool,
        backoff_seconds: int = 60,
    ) -> JobRecord:
        with self._lock:
            now_dt = self.now()
            job = self._verify_active_lease_unlocked(job_id, worker_id, lease_token, now_dt)
            job.error_class = error_class
            job.error_detail = error_detail
            job.lease_until = None
            job.worker_id = None
            job.updated_at = now_dt
            if should_retry and job.attempts < job.max_attempts:
                job.status = JobStatus.RETRY_WAIT
                job.scheduled_at = now_dt + timedelta(seconds=max(1, backoff_seconds))
                # Transition retry_wait back to queued when due
            else:
                job.status = JobStatus.DEAD_LETTER
            return job.model_copy(deep=True)

    def _reclaim_expired_unlocked(self, now_dt: datetime) -> int:
        reclaimed = 0
        for job in self._jobs.values():
            if job.status == JobStatus.LEASED and job.lease_until is not None and job.lease_until <= now_dt:
                if job.attempts >= job.max_attempts:
                    job.status = JobStatus.DEAD_LETTER
                    job.error_class = job.error_class or "lease_expired_max_attempts"
                else:
                    job.status = JobStatus.QUEUED
                job.worker_id = None
                job.lease_until = None
                job.updated_at = now_dt
                reclaimed += 1
            elif job.status == JobStatus.RETRY_WAIT and job.scheduled_at <= now_dt:
                job.status = JobStatus.QUEUED
                job.updated_at = now_dt
        return reclaimed

    def recover_after_outage(self, *, overdue_resource_ids: list[str], window_bucket: str, min_spacing_seconds: int = 2) -> dict[str, int]:
        """Recover from power loss/reboot: clean expired leases, coalesce duplicate overdue fetches, and space out schedules (Spec 3.5, 6.4, T31)."""
        with self._lock:
            now_dt = self.now()
            reclaimed = self._reclaim_expired_unlocked(now_dt)

            seen_resources: set[str] = set()
            coalesced_count = 0
            enqueued_count = 0
            offset_sec = 0

            # Deduplicate any already-queued fetch jobs for the same resource
            queued_by_resource: dict[str, list[JobRecord]] = {}
            for job in self._jobs.values():
                if job.job_type == "fetch" and job.resource_id and job.status in {JobStatus.QUEUED, JobStatus.RETRY_WAIT}:
                    queued_by_resource.setdefault(job.resource_id, []).append(job)

            for res_id, jobs in queued_by_resource.items():
                jobs.sort(key=lambda j: (-j.priority, j.created_at))
                seen_resources.add(res_id)
                primary = jobs[0]
                primary.scheduled_at = now_dt + timedelta(seconds=offset_sec)
                offset_sec += min_spacing_seconds
                for duplicate in jobs[1:]:
                    duplicate.status = JobStatus.CANCELLED
                    duplicate.error_class = "coalesced_after_outage"
                    coalesced_count += 1

            for res_id in overdue_resource_ids:
                if res_id in seen_resources:
                    coalesced_count += 1
                    continue
                seen_resources.add(res_id)
                dk = build_fetch_dedupe_key(res_id, window_bucket)
                self.enqueue(
                    job_type="fetch",
                    dedupe_key=dk,
                    resource_id=res_id,
                    scheduled_at=now_dt + timedelta(seconds=offset_sec),
                )
                offset_sec += min_spacing_seconds
                enqueued_count += 1

            return {
                "reclaimed_leases": reclaimed,
                "coalesced_duplicates": coalesced_count,
                "enqueued_overdue": enqueued_count,
            }

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.model_copy(deep=True) if job else None

    def list_jobs(self, *, status: JobStatus | None = None) -> list[JobRecord]:
        with self._lock:
            rows = [j.model_copy(deep=True) for j in self._jobs.values() if status is None or j.status == status]
            rows.sort(key=lambda j: (j.created_at, j.id))
            return rows
