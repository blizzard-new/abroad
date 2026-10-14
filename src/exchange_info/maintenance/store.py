"""Maintenance repository, private blob storage, review workflow, and atomic release/rollback engine (Spec Sections 4, 9, 11, 12)."""

from __future__ import annotations

import copy
import hashlib
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    ChangeOrigin,
    CycleSpec,
    DataFreshnessStatus,
    EvidenceRecord,
    FieldAssertion,
    OfferingLifecycleStatus,
    PublishedFieldEnvelope,
    QuotaUnit,
    QuotaValue,
    ReviewStatus,
    RiskLevel,
    ScopeEntry,
    SourceHealthStatus,
    ValueState,
    canonical_json_hash,
    utc_now,
)
from .queue_worker import BudgetAndDiskGuard, PersistentJobQueue
from .reconciler import ChangeItemRecord, ChangeSetRecord, aggregate_quotas_safely


class OptimisticLockConflictError(ValueError):
    """Raised when candidate_version, evidence_set_hash, or base_release_id is stale (HTTP 409)."""


class AccessDeniedError(PermissionError):
    """Raised when a user/role lacks permission or attempts privilege escalation / path traversal (HTTP 403)."""


class InstitutionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    country_code: str
    canonical_name: str
    english_name: str | None = None
    institution_type: Literal["home", "host", "both"]
    official_url: str | None = None
    aliases: list[str] = Field(default_factory=list)
    colleges: list[str] = Field(default_factory=list)
    current_revision_id: str | None = None


class SourceRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    owner_institution_id: str
    source_type: Literal[
        "official_announcement",
        "official_quota_list",
        "official_partner_detail",
        "official_fact_sheet",
        "authorized_experience_feed",
        "manual_admin",
    ]
    authority_scope: list[str] = Field(default_factory=list)
    approved_domains: list[str] = Field(default_factory=list)
    entry_url: str
    terms_url: str | None = None
    reuse_basis: Literal[
        "official_public_fact",
        "explicit_consent",
        "link_and_short_excerpt_only",
        "internal_verification_only",
    ] = "official_public_fact"
    enabled: bool = True
    policy_version: str = "v1"
    risk_class: RiskLevel = RiskLevel.HIGH
    retention_days: int = 90


class SourceResourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str
    normalized_url: str
    original_url: str
    resource_kind: Literal["html_list", "html_detail", "pdf_attachment", "doc_attachment", "api_json", "rss_feed"] = "html_detail"
    expected_scope: dict[str, Any] = Field(default_factory=dict)
    etag: str | None = None
    last_modified: str | None = None
    health_status: SourceHealthStatus = SourceHealthStatus.HEALTHY
    last_checked_at: datetime | None = None
    last_successfully_checked_at: datetime | None = None
    last_meaningful_change_at: datetime | None = None
    next_due_at: datetime | None = None
    latest_snapshot_id: str | None = None


class ContentBlobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    raw_sha256: str
    normalized_content_hash: str
    storage_key: str
    mime: str
    byte_count: int
    retention_class: Literal["standard_90d", "published_evidence", "ephemeral_metadata_only"] = "standard_90d"
    authorized_source_ids: set[str] = Field(default_factory=set)
    created_at: datetime = Field(default_factory=utc_now)


class SnapshotRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    resource_id: str
    source_id: str
    blob_id: str
    fetched_at: datetime = Field(default_factory=utc_now)
    source_published_at: datetime | None = None
    source_modified_at: datetime | None = None
    content_language: str = "zh-TW"
    input_context_hash: str


class OfferingRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    home_id: str
    host_id: str
    program_id: str
    cycle_id: str
    scope_key: str
    campus_scope: ScopeEntry
    academic_unit_scope: ScopeEntry
    degree_level_scope: ScopeEntry
    lifecycle_status: OfferingLifecycleStatus = OfferingLifecycleStatus.UNKNOWN
    fields: dict[str, PublishedFieldEnvelope] = Field(default_factory=dict)
    current_revision_id: str | None = None


class EntityRevisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    entity_type: Literal["institution", "offering", "experience"]
    entity_id: str
    payload_schema_version: str = "v1"
    payload: dict[str, Any]
    provenance_map: dict[str, Any] = Field(default_factory=dict)
    revision_hash: str
    created_at: datetime = Field(default_factory=utc_now)


class ReleaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    previous_release_id: str | None = None
    reason: str
    published_by: str
    published_at: datetime = Field(default_factory=utc_now)
    status: Literal["published", "rolled_back_source"] = "published"
    idempotency_key: str
    members: dict[str, str] = Field(default_factory=dict)  # f"{entity_type}:{entity_id}" -> revision_id


class AuditEventRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"aud_{uuid4().hex[:16]}")
    actor_id: str
    action: str
    target_type: str
    target_id: str
    from_id: str | None = None
    to_id: str | None = None
    reason: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ExperiencePublicRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    home_id: str | None = None
    host_id: str
    author_display_mode: Literal["anonymous", "nickname", "real_name"] = "anonymous"
    author_display_name: str = "匿名交換生"
    student_role: Literal["exchange_student", "local_degree_student", "international_degree_student", "other"] = "exchange_student"
    experience_period: str
    experience_year: int
    topics: list[str] = Field(default_factory=list)
    summary_zh: str
    personal_cost_note: str | None = None
    source_url: str | None = None
    is_ai_summary: bool = False
    is_translated: bool = False
    review_status: Literal["pending", "approved", "rejected", "suppressed"] = "pending"
    consent_version: str = "v1"
    submitter_account_id: str
    fetched_or_updated_at: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)


class PrivateConsentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    experience_id: str
    submitter_account_id: str
    contact_email_hmac: str | None = None
    public_scope: str = "uniway_public"
    allow_summary: bool = True
    allow_translation: bool = True
    consent_text_version: str = "v1"
    consented_at: datetime = Field(default_factory=utc_now)
    withdrawn_at: datetime | None = None


class PrivateBlobVault:
    """Private content-addressed file store with path traversal guard and source-scoped ACL (Spec 10.3, 11.4, T02, T35)."""

    def __init__(self, root_dir: Path, guard: BudgetAndDiskGuard) -> None:
        self.root_dir = root_dir.resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.guard = guard
        self._lock = threading.RLock()
        self._blobs_by_sha: dict[str, ContentBlobRecord] = {}
        self._blobs_by_id: dict[str, ContentBlobRecord] = {}

    def put_blob(
        self,
        *,
        raw_bytes: bytes,
        normalized_content_hash: str,
        mime: str,
        source_id: str,
        retention_class: Literal["standard_90d", "published_evidence", "ephemeral_metadata_only"] = "standard_90d",
    ) -> tuple[ContentBlobRecord, bool]:
        """Store blob deduplicated by raw_sha256; write durably to disk before returning reference (Spec 3.5, 7.2, T02)."""
        self.guard.check_disk_watermark(len(raw_bytes))
        raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        with self._lock:
            existing = self._blobs_by_sha.get(raw_sha256)
            if existing is not None:
                existing.authorized_source_ids.add(source_id)
                if retention_class == "published_evidence":
                    existing.retention_class = "published_evidence"
                return existing.model_copy(deep=True), True

            storage_key = f"{raw_sha256[:2]}/{raw_sha256}.bin"
            target_path = self._safe_resolve_key(storage_key)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = target_path.with_suffix(".tmp")
            with open(temp_path, "wb") as fh:
                fh.write(raw_bytes)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(temp_path, target_path)

            record = ContentBlobRecord(
                id=f"blob_{raw_sha256[:16]}",
                raw_sha256=raw_sha256,
                normalized_content_hash=normalized_content_hash,
                storage_key=storage_key,
                mime=mime,
                byte_count=len(raw_bytes),
                retention_class=retention_class,
                authorized_source_ids={source_id},
            )
            self._blobs_by_sha[raw_sha256] = record
            self._blobs_by_id[record.id] = record
            return record.model_copy(deep=True), False

    def _safe_resolve_key(self, storage_key: str) -> Path:
        """Prevent path traversal and symlink escapes out of private storage root (Spec 11.4 / T35)."""
        if not storage_key or ".." in storage_key or storage_key.startswith(("/", "\\")) or ":" in storage_key:
            raise AccessDeniedError("Invalid storage key: path traversal blocked")
        candidate = (self.root_dir / storage_key).resolve()
        try:
            candidate.relative_to(self.root_dir)
        except ValueError as exc:
            raise AccessDeniedError("Path traversal outside private blob root blocked") from exc
        if candidate.exists() and candidate.is_symlink():
            raise AccessDeniedError("Symlink access inside private blob root is forbidden")
        return candidate

    def read_blob_authorized(
        self,
        blob_id: str,
        *,
        requesting_source_id: str,
        allowed_admin_source_ids: set[str] | None = None,
    ) -> bytes:
        """Read private blob verifying source-level authorization; deduplicated hash never widens read access (Spec 11.4 / T35)."""
        with self._lock:
            record = self._blobs_by_id.get(blob_id)
            if record is None:
                raise KeyError(f"Blob {blob_id} not found")
            if requesting_source_id not in record.authorized_source_ids:
                raise AccessDeniedError(
                    f"Source {requesting_source_id} is not authorized to read blob {blob_id} despite content deduplication"
                )
            if allowed_admin_source_ids is not None and requesting_source_id not in allowed_admin_source_ids:
                raise AccessDeniedError("Admin scope does not cover this source")
            path = self._safe_resolve_key(record.storage_key)
            return path.read_bytes()

    def cleanup_expired_blobs(
        self,
        *,
        referenced_blob_ids: set[str],
        now_dt: datetime | None = None,
        max_age_days: int = 90,
    ) -> dict[str, list[str]]:
        """Purge expired unreferenced blobs while strictly protecting any blob referenced by published/historical evidence (Spec 3.5, 10.3, T32)."""
        now_val = now_dt or utc_now()
        cutoff = now_val - timedelta(days=max_age_days)
        deleted: list[str] = []
        protected: list[str] = []

        with self._lock:
            for blob_id, record in list(self._blobs_by_id.items()):
                if blob_id in referenced_blob_ids or record.retention_class == "published_evidence":
                    protected.append(blob_id)
                    continue
                if record.created_at < cutoff:
                    path = self._safe_resolve_key(record.storage_key)
                    path.unlink(missing_ok=True)
                    del self._blobs_by_id[blob_id]
                    self._blobs_by_sha.pop(record.raw_sha256, None)
                    deleted.append(blob_id)
        return {"deleted_blob_ids": deleted, "protected_blob_ids": protected}


class MaintenanceStore:
    """In-memory / local transactional store implementing full Spec Sections 4, 8, 9, 11, 12, 13."""

    def __init__(self, storage_dir: Path) -> None:
        self._lock = threading.RLock()
        self.storage_dir = storage_dir.resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.guard = BudgetAndDiskGuard(storage_root=self.storage_dir)
        self.blob_vault = PrivateBlobVault(self.storage_dir / "private_blobs", self.guard)
        self.queue = PersistentJobQueue()

        self.institutions: dict[str, InstitutionRecord] = {}
        self.cycles: dict[str, CycleSpec] = {}
        self.sources: dict[str, SourceRegistration] = {}
        self.resources: dict[str, SourceResourceRecord] = {}
        self.snapshots: dict[str, SnapshotRecord] = {}
        self.evidence: dict[str, EvidenceRecord] = {}
        self.assertions: dict[str, FieldAssertion] = {}
        self.offerings: dict[str, OfferingRecord] = {}
        self.change_sets: dict[str, ChangeSetRecord] = {}
        self.review_decisions: dict[str, dict[str, Any]] = {}
        self.entity_revisions: dict[str, EntityRevisionRecord] = {}
        self.releases: dict[str, ReleaseRecord] = {}
        self.releases_by_idempotency: dict[str, str] = {}
        self.current_release_id: str | None = None
        self.publication_lock_version: int = 0
        self.suppressions: dict[tuple[str, str], dict[str, Any]] = {}
        self.audit_events: list[AuditEventRecord] = []
        self.experiences: dict[str, ExperiencePublicRecord] = {}
        self.consents: dict[str, PrivateConsentRecord] = {}
        self.reports: list[dict[str, Any]] = []
        self.parser_runs_count: int = 0
        self.paid_ocr_model_calls_count: int = 0

    def register_institution(self, inst: InstitutionRecord, *, actor_id: str = "system_bootstrap") -> InstitutionRecord:
        with self._lock:
            payload = inst.model_dump(mode="json", exclude={"current_revision_id"})
            rev_hash = canonical_json_hash(payload)
            rev_id = f"rev_inst_{inst.id}_{rev_hash[:12]}"
            rev = EntityRevisionRecord(
                id=rev_id,
                entity_type="institution",
                entity_id=inst.id,
                payload=payload,
                revision_hash=rev_hash,
            )
            self.entity_revisions[rev_id] = rev
            inst.current_revision_id = rev_id
            self.institutions[inst.id] = inst.model_copy(deep=True)
            return inst.model_copy(deep=True)

    def update_institution_name(self, inst_id: str, new_canonical_name: str, *, actor_id: str) -> EntityRevisionRecord:
        """Create a new institution revision without mutating past revisions (Spec 4.1 / T28)."""
        with self._lock:
            inst = self.institutions.get(inst_id)
            if inst is None:
                raise KeyError(f"Institution {inst_id} not found")
            inst.canonical_name = new_canonical_name
            payload = inst.model_dump(mode="json", exclude={"current_revision_id"})
            rev_hash = canonical_json_hash(payload)
            rev_id = f"rev_inst_{inst.id}_{rev_hash[:12]}"
            rev = EntityRevisionRecord(
                id=rev_id,
                entity_type="institution",
                entity_id=inst.id,
                payload=payload,
                revision_hash=rev_hash,
            )
            self.entity_revisions[rev_id] = rev
            inst.current_revision_id = rev_id
            self.audit_events.append(
                AuditEventRecord(
                    actor_id=actor_id,
                    action="institution_revision_created",
                    target_type="institution",
                    target_id=inst_id,
                    to_id=rev_id,
                    reason="canonical_name_update",
                )
            )
            return rev.model_copy(deep=True)

    def register_offering(self, offering: OfferingRecord) -> OfferingRecord:
        with self._lock:
            payload = offering.model_dump(mode="json", exclude={"current_revision_id"})
            rev_hash = canonical_json_hash(payload)
            rev_id = f"rev_off_{offering.id}_{rev_hash[:12]}"
            rev = EntityRevisionRecord(
                id=rev_id,
                entity_type="offering",
                entity_id=offering.id,
                payload=payload,
                revision_hash=rev_hash,
            )
            self.entity_revisions[rev_id] = rev
            offering.current_revision_id = rev_id
            self.offerings[offering.id] = offering.model_copy(deep=True)
            return offering.model_copy(deep=True)

    def create_initial_release(self, *, actor_id: str, reason: str = "initial_baseline_release") -> ReleaseRecord:
        with self._lock:
            members: dict[str, str] = {}
            for inst_id, inst in sorted(self.institutions.items()):
                if inst.current_revision_id:
                    members[f"institution:{inst_id}"] = inst.current_revision_id
            for off_id, off in sorted(self.offerings.items()):
                if off.current_revision_id:
                    members[f"offering:{off_id}"] = off.current_revision_id

            rel_id = f"rel_{uuid4().hex[:12]}"
            rel = ReleaseRecord(
                id=rel_id,
                previous_release_id=self.current_release_id,
                reason=reason,
                published_by=actor_id,
                idempotency_key=f"init_{rel_id}",
                members=members,
            )
            self.releases[rel_id] = rel
            self.current_release_id = rel_id
            self.publication_lock_version += 1
            return rel.model_copy(deep=True)

    def stage_change_set(self, change_set: ChangeSetRecord) -> ChangeSetRecord:
        """Stage or update a candidate ChangeSet. If evidence changes for an existing pending ChangeSet, bump candidate_version and invalidate prior approvals (Spec 9.3 / T14)."""
        with self._lock:
            for existing in self.change_sets.values():
                if existing.entity_scope == change_set.entity_scope and existing.status in {
                    ReviewStatus.PENDING,
                    ReviewStatus.APPROVED,
                    ReviewStatus.PARTIALLY_APPROVED,
                    ReviewStatus.CONFLICTING,
                }:
                    if existing.evidence_set_hash == change_set.evidence_set_hash:
                        # Deduplicate identical candidate (Spec 6.3 / T09)
                        return existing.model_copy(deep=True)
                    # New evidence arrived while candidate was in review/approved -> increment candidate_version and invalidate old approvals (T14)!
                    existing.candidate_version += 1
                    existing.evidence_set_hash = change_set.evidence_set_hash
                    existing.items = copy.deepcopy(change_set.items)
                    for item in existing.items:
                        item.approval_status = "pending"
                    existing.status = change_set.status
                    existing.risk = change_set.risk
                    existing.updated_at = utc_now()
                    return existing.model_copy(deep=True)

            self.change_sets[change_set.id] = change_set.model_copy(deep=True)
            return change_set.model_copy(deep=True)

    def review_change_set(
        self,
        *,
        change_set_id: str,
        reviewer_id: str,
        candidate_version: int,
        evidence_set_hash: str,
        base_release_id: str | None,
        decision: Literal["approve", "reject", "defer", "recheck", "flag_source"],
        selected_fields: list[str],
        reason: str,
        idempotency_key: str,
    ) -> tuple[ChangeSetRecord, ChangeSetRecord | None]:
        """Review selected fields of a ChangeSet. Supports partial approval without silently accepting unselected fields (Spec 9.2, 9.3, T14)."""
        if not reason or len(reason.strip()) < 3:
            raise ValueError("Review decision requires an explicit reason")

        with self._lock:
            if idempotency_key in self.review_decisions:
                prev = self.review_decisions[idempotency_key]
                cs = self.change_sets[prev["change_set_id"]]
                rem = self.change_sets.get(prev["remaining_change_set_id"]) if prev.get("remaining_change_set_id") else None
                return cs.model_copy(deep=True), (rem.model_copy(deep=True) if rem else None)

            cs = self.change_sets.get(change_set_id)
            if cs is None:
                raise KeyError(f"ChangeSet {change_set_id} not found")

            if (
                cs.candidate_version != candidate_version
                or cs.evidence_set_hash != evidence_set_hash
                or cs.base_release_id != base_release_id
                or self.current_release_id != base_release_id
            ):
                raise OptimisticLockConflictError(
                    "409 Conflict: Candidate version, evidence set hash, or base release has changed since review started."
                )

            selected_set = set(selected_fields)
            available_fields = {item.field_path for item in cs.items}
            if not selected_set or not selected_set.issubset(available_fields):
                raise ValueError(f"selected_fields {selected_fields} must be a non-empty subset of {sorted(available_fields)}")

            if decision == "approve":
                for item in cs.items:
                    if item.field_path in selected_set:
                        if item.after_state in {ValueState.CONFLICTING, ValueState.UNVERIFIED} and item.risk == RiskLevel.HIGH:
                            raise ValueError(f"High-risk field '{item.field_path}' has conflicting or unverified evidence and cannot be approved for publication.")
                        item.approval_status = "approved"

                approved_items = [item for item in cs.items if item.approval_status == "approved"]
                unapproved_items = [item for item in cs.items if item.approval_status != "approved"]

                remaining_cs: ChangeSetRecord | None = None
                if unapproved_items:
                    # Spec 9.2: Partial approval keeps unapproved fields at old value/provenance and rebuilds a remaining candidate
                    cs.items = approved_items
                    cs.status = ReviewStatus.APPROVED
                    rem_hash = canonical_json_hash([i.model_dump(mode="json") for i in unapproved_items])
                    remaining_cs = ChangeSetRecord(
                        entity_scope=cs.entity_scope,
                        home_id=cs.home_id,
                        host_id=cs.host_id,
                        program_id=cs.program_id,
                        cycle_id=cs.cycle_id,
                        base_release_id=cs.base_release_id,
                        candidate_version=1,
                        evidence_set_hash=rem_hash,
                        risk=RiskLevel.HIGH if any(i.risk == RiskLevel.HIGH for i in unapproved_items) else RiskLevel.MEDIUM,
                        change_origin=cs.change_origin,
                        status=ReviewStatus.PENDING,
                        items=unapproved_items,
                    )
                    self.change_sets[remaining_cs.id] = remaining_cs
                else:
                    cs.status = ReviewStatus.APPROVED
            elif decision == "reject":
                for item in cs.items:
                    if item.field_path in selected_set:
                        item.approval_status = "rejected"
                if all(item.approval_status == "rejected" for item in cs.items):
                    cs.status = ReviewStatus.REJECTED
                remaining_cs = None
            else:
                for item in cs.items:
                    if item.field_path in selected_set:
                        item.approval_status = "deferred"
                cs.status = ReviewStatus.DEFERRED
                remaining_cs = None

            cs.updated_at = utc_now()
            self.review_decisions[idempotency_key] = {
                "change_set_id": cs.id,
                "remaining_change_set_id": remaining_cs.id if remaining_cs else None,
                "reviewer_id": reviewer_id,
                "decision": decision,
                "selected_fields": list(selected_fields),
                "reason": reason,
                "decided_at": utc_now().isoformat(),
            }
            self.audit_events.append(
                AuditEventRecord(
                    actor_id=reviewer_id,
                    action=f"review_{decision}",
                    target_type="change_set",
                    target_id=cs.id,
                    reason=reason,
                    metadata={"selected_fields": list(selected_fields), "candidate_version": candidate_version},
                )
            )
            return cs.model_copy(deep=True), (remaining_cs.model_copy(deep=True) if remaining_cs else None)

    def publish_approved_changes(
        self,
        *,
        change_set_ids: list[str],
        base_release_id: str | None,
        publisher_id: str,
        reason: str,
        idempotency_key: str,
        fail_mid_transaction: bool = False,
    ) -> ReleaseRecord:
        """Atomically publish approved ChangeSets in a single locked transaction (Spec Section 9.3, T15, T16)."""
        with self._lock:
            # Idempotent replay if same idempotency_key already succeeded (Spec 9.3 item 5 / T15)
            if idempotency_key in self.releases_by_idempotency:
                rel_id = self.releases_by_idempotency[idempotency_key]
                return self.releases[rel_id].model_copy(deep=True)

            if self.current_release_id != base_release_id:
                raise OptimisticLockConflictError(
                    f"409 Conflict: Publication head has moved from {base_release_id} to {self.current_release_id}."
                )

            if not change_set_ids:
                raise ValueError("change_set_ids cannot be empty")

            # Snapshot state before transaction so mid-transaction failure rolls back 100% cleanly (T16)
            offerings_backup = copy.deepcopy(self.offerings)
            revisions_backup = copy.deepcopy(self.entity_revisions)
            change_sets_backup = copy.deepcopy(self.change_sets)
            head_backup = self.current_release_id
            lock_ver_backup = self.publication_lock_version

            try:
                base_members = (
                    copy.deepcopy(self.releases[base_release_id].members)
                    if base_release_id and base_release_id in self.releases
                    else {}
                )

                for cs_id in change_set_ids:
                    cs = self.change_sets.get(cs_id)
                    if cs is None:
                        raise KeyError(f"ChangeSet {cs_id} not found")
                    if cs.status != ReviewStatus.APPROVED:
                        raise OptimisticLockConflictError(f"ChangeSet {cs_id} is in status '{cs.status.value}', not approved")
                    if cs.base_release_id != base_release_id:
                        raise OptimisticLockConflictError(f"ChangeSet {cs_id} base_release_id mismatch")

                    offering = self.offerings.get(cs.entity_scope)
                    if offering is None:
                        raise KeyError(f"Offering {cs.entity_scope} not found")

                    for item in cs.items:
                        if item.approval_status != "approved":
                            continue
                        # Check that none of the supporting assertions/evidence have been suppressed
                        for ev in item.evidence_excerpts:
                            if ("evidence", ev.get("assertion_id", "")) in self.suppressions:
                                raise OptimisticLockConflictError("Supporting evidence has been suppressed/withdrawn")

                        offering.fields[item.field_path] = PublishedFieldEnvelope(
                            value=item.after_value,
                            value_state=item.after_state,
                            unit=item.unit,
                            effective_scope=item.effective_scope,
                            evidence_refs=item.evidence_excerpts,
                            last_verified_at=utc_now(),
                            freshness_status=DataFreshnessStatus.CURRENT,
                        )

                    if fail_mid_transaction:
                        raise RuntimeError("Simulated mid-transaction failure before switching publication_head")

                    payload = offering.model_dump(mode="json", exclude={"current_revision_id"})
                    rev_hash = canonical_json_hash(payload)
                    new_rev_id = f"rev_off_{offering.id}_{rev_hash[:12]}"
                    new_rev = EntityRevisionRecord(
                        id=new_rev_id,
                        entity_type="offering",
                        entity_id=offering.id,
                        payload=payload,
                        revision_hash=rev_hash,
                    )
                    self.entity_revisions[new_rev_id] = new_rev
                    offering.current_revision_id = new_rev_id
                    base_members[f"offering:{offering.id}"] = new_rev_id
                    cs.status = ReviewStatus.PUBLISHED
                    cs.updated_at = utc_now()

                # Also pin current institution revisions in the release manifest
                for inst_id, inst in sorted(self.institutions.items()):
                    key = f"institution:{inst_id}"
                    if key not in base_members and inst.current_revision_id:
                        base_members[key] = inst.current_revision_id

                new_release_id = f"rel_{uuid4().hex[:12]}"
                new_release = ReleaseRecord(
                    id=new_release_id,
                    previous_release_id=base_release_id,
                    reason=reason,
                    published_by=publisher_id,
                    idempotency_key=idempotency_key,
                    members=base_members,
                )
                self.releases[new_release_id] = new_release
                self.releases_by_idempotency[idempotency_key] = new_release_id
                self.current_release_id = new_release_id
                self.publication_lock_version += 1

                self.audit_events.append(
                    AuditEventRecord(
                        actor_id=publisher_id,
                        action="publish_release",
                        target_type="release",
                        target_id=new_release_id,
                        from_id=base_release_id,
                        to_id=new_release_id,
                        reason=reason,
                        metadata={"change_set_ids": list(change_set_ids)},
                    )
                )
                return new_release.model_copy(deep=True)
            except BaseException:
                # Full atomic rollback (T16)
                self.offerings = offerings_backup
                self.entity_revisions = revisions_backup
                self.change_sets = change_sets_backup
                self.current_release_id = head_backup
                self.publication_lock_version = lock_ver_backup
                raise

    def rollback_release_entities(
        self,
        *,
        current_release_id: str,
        target_release_id: str,
        entity_keys: list[str] | None,
        actor_id: str,
        reason: str,
        idempotency_key: str,
    ) -> ReleaseRecord:
        """Create a new release pointing selected entities (or all) to an older release's revisions without deleting history (Spec 9.4 / T18)."""
        if not reason or len(reason.strip()) < 3:
            raise ValueError("Rollback requires an explicit reason")

        with self._lock:
            if idempotency_key in self.releases_by_idempotency:
                return self.releases[self.releases_by_idempotency[idempotency_key]].model_copy(deep=True)

            if self.current_release_id != current_release_id:
                raise OptimisticLockConflictError("409 Conflict: current_release_id does not match publication_head")

            cur_rel = self.releases.get(current_release_id)
            tgt_rel = self.releases.get(target_release_id)
            if cur_rel is None or tgt_rel is None:
                raise KeyError("Specified current or target release does not exist")

            new_members = copy.deepcopy(cur_rel.members)
            keys_to_restore = entity_keys if entity_keys else list(tgt_rel.members.keys())

            for e_key in keys_to_restore:
                if e_key not in tgt_rel.members:
                    raise KeyError(f"Entity {e_key} was not present in target release {target_release_id}")
                target_rev_id = tgt_rel.members[e_key]
                if ("revision", target_rev_id) in self.suppressions or ("entity", e_key) in self.suppressions:
                    raise ValueError(f"Cannot restore {e_key} to revision {target_rev_id}: content is in active suppression list")
                new_members[e_key] = target_rev_id

                # Sync active working state for offerings if rolled back
                if e_key.startswith("offering:"):
                    off_id = e_key.split(":", 1)[1]
                    rev_obj = self.entity_revisions[target_rev_id]
                    restored_off = OfferingRecord.model_validate({**rev_obj.payload, "current_revision_id": target_rev_id})
                    self.offerings[off_id] = restored_off

            new_release_id = f"rel_rb_{uuid4().hex[:10]}"
            new_release = ReleaseRecord(
                id=new_release_id,
                previous_release_id=current_release_id,
                reason=reason,
                published_by=actor_id,
                idempotency_key=idempotency_key,
                members=new_members,
            )
            self.releases[new_release_id] = new_release
            self.releases_by_idempotency[idempotency_key] = new_release_id
            self.current_release_id = new_release_id
            self.publication_lock_version += 1

            self.audit_events.append(
                AuditEventRecord(
                    actor_id=actor_id,
                    action="rollback_release",
                    target_type="release",
                    target_id=new_release_id,
                    from_id=current_release_id,
                    to_id=target_release_id,
                    reason=reason,
                    metadata={"restored_entity_keys": list(keys_to_restore)},
                )
            )
            return new_release.model_copy(deep=True)

    def suppress_content(
        self,
        *,
        target_type: Literal["entity", "revision", "evidence", "experience", "source"],
        target_id: str,
        actor_id: str,
        reason: str,
    ) -> None:
        """Suppress withdrawn/PII/copyright content across all public releases, caches, and summaries while keeping content-free audit (Spec 9.4, 12.4, T25)."""
        with self._lock:
            self.suppressions[(target_type, target_id)] = {
                "target_type": target_type,
                "target_id": target_id,
                "reason": reason,
                "suppressed_by": actor_id,
                "suppressed_at": utc_now().isoformat(),
            }
            if target_type == "experience" and target_id in self.experiences:
                exp = self.experiences[target_id]
                exp.review_status = "suppressed"
                exp.summary_zh = "[已依作者或來源要求撤回]"
            self.audit_events.append(
                AuditEventRecord(
                    actor_id=actor_id,
                    action="suppress_content",
                    target_type=target_type,
                    target_id=target_id,
                    reason=reason,
                )
            )

    def get_public_offering_projection(self, offering_id: str, *, release_id: str | None = None) -> dict[str, Any]:
        """Read-only public projection pinned to a specific release_id, resolving fixed institution revisions and applying suppressions (Spec 9.3, T17, T25, T28)."""
        with self._lock:
            rel_id = release_id or self.current_release_id
            if not rel_id or rel_id not in self.releases:
                raise KeyError(f"Release {rel_id} not found")
            if ("entity", f"offering:{offering_id}") in self.suppressions:
                raise KeyError(f"Offering {offering_id} has been suppressed/withdrawn")

            rel = self.releases[rel_id]
            off_rev_id = rel.members.get(f"offering:{offering_id}")
            if not off_rev_id or ("revision", off_rev_id) in self.suppressions:
                raise KeyError(f"Offering {offering_id} is not available in release {rel_id}")

            off_rev = self.entity_revisions[off_rev_id]
            off_payload = copy.deepcopy(off_rev.payload)

            # Resolve home and host institution names from the exact institution revision pinned in `rel` (T28: no live join drift!)
            home_id = off_payload["home_id"]
            host_id = off_payload["host_id"]
            home_rev_id = rel.members.get(f"institution:{home_id}")
            host_rev_id = rel.members.get(f"institution:{host_id}")
            home_payload = self.entity_revisions[home_rev_id].payload if home_rev_id else {}
            host_payload = self.entity_revisions[host_rev_id].payload if host_rev_id else {}

            return {
                "release_id": rel_id,
                "offering_id": offering_id,
                "revision_id": off_rev_id,
                "home_institution": {
                    "id": home_id,
                    "canonical_name": home_payload.get("canonical_name"),
                    "revision_id": home_rev_id,
                },
                "host_institution": {
                    "id": host_id,
                    "canonical_name": host_payload.get("canonical_name"),
                    "country_code": host_payload.get("country_code"),
                    "revision_id": host_rev_id,
                },
                "program_id": off_payload["program_id"],
                "cycle_id": off_payload["cycle_id"],
                "scope_key": off_payload["scope_key"],
                "lifecycle_status": off_payload["lifecycle_status"],
                "fields": off_payload.get("fields", {}),
            }

    def list_public_offerings(
        self,
        *,
        home_id: str | None = None,
        cycle_id: str | None = None,
        release_id: str | None = None,
    ) -> dict[str, Any]:
        """List public offerings pinned to the same release_id with safe quota aggregation (Spec 9.3, 13.3, T06, T07, T17)."""
        with self._lock:
            rel_id = release_id or self.current_release_id
            if not rel_id or rel_id not in self.releases:
                raise KeyError(f"Release {rel_id} not found")
            rel = self.releases[rel_id]

            items: list[dict[str, Any]] = []
            quotas_for_summary: list[QuotaValue] = []

            for member_key in sorted(rel.members.keys()):
                if not member_key.startswith("offering:"):
                    continue
                off_id = member_key.split(":", 1)[1]
                if ("entity", member_key) in self.suppressions:
                    continue
                proj = self.get_public_offering_projection(off_id, release_id=rel_id)
                if home_id and proj["home_institution"]["id"] != home_id:
                    continue
                if cycle_id and proj["cycle_id"] != cycle_id:
                    continue
                items.append(proj)

                q_env = proj["fields"].get("quota")
                if q_env and isinstance(q_env.get("value"), dict):
                    try:
                        quotas_for_summary.append(QuotaValue.model_validate(q_env["value"]))
                    except Exception:
                        pass

            return {
                "release_id": rel_id,
                "total_count": len(items),
                "quota_summary": aggregate_quotas_safely(quotas_for_summary),
                "items": items,
            }

    def submit_student_experience(
        self,
        *,
        submitter_account_id: str,
        raw_payload: dict[str, Any],
        contact_email: str | None = None,
    ) -> ExperiencePublicRecord:
        """Accept student experience submission while blocking privilege escalation and isolating private consent/contact (Spec 11.3, 12, T19, T20, T26)."""
        forbidden_keys = {"approved", "review_status", "reviewer_id", "owner", "published", "is_admin", "role"}
        attempted_escalation = forbidden_keys.intersection(raw_payload.keys())
        if attempted_escalation:
            raise AccessDeniedError(
                f"Privilege escalation blocked: submitter cannot set protected fields {sorted(attempted_escalation)}"
            )

        if not raw_payload.get("consent_agreed"):
            raise ValueError("Explicit consent is required for experience submissions")

        exp_year = int(raw_payload["experience_year"])
        exp_id = f"exp_{uuid4().hex[:14]}"
        record = ExperiencePublicRecord(
            id=exp_id,
            home_id=raw_payload.get("home_id"),
            host_id=raw_payload["host_id"],
            author_display_mode=raw_payload.get("author_display_mode", "anonymous"),
            author_display_name=raw_payload.get("author_display_name", "匿名交換生"),
            student_role=raw_payload.get("student_role", "exchange_student"),
            experience_period=raw_payload["experience_period"],
            experience_year=exp_year,  # T26: Always retain actual experience year (e.g., 2023), never overwrite with current year!
            topics=list(raw_payload.get("topics", [])),
            summary_zh=str(raw_payload["summary_zh"]).strip(),
            personal_cost_note=raw_payload.get("personal_cost_note"),
            source_url=raw_payload.get("source_url"),
            review_status="pending",
            submitter_account_id=submitter_account_id,
        )
        email_hmac = (
            hashlib.sha256(contact_email.strip().lower().encode("utf-8")).hexdigest()
            if contact_email and contact_email.strip()
            else None
        )
        consent = PrivateConsentRecord(
            id=f"cns_{uuid4().hex[:14]}",
            experience_id=exp_id,
            submitter_account_id=submitter_account_id,
            contact_email_hmac=email_hmac,
        )
        with self._lock:
            self.experiences[exp_id] = record
            self.consents[consent.id] = consent
            return record.model_copy(deep=True)

    # ------------------------------------------------------------------
    # Backup & Restore with Manifest + Blob SHA-256 Verification (Spec 14.3, T33)
    # ------------------------------------------------------------------
    def export_backup_bundle(self, bundle_dir: str | Path) -> dict[str, Any]:
        """Export DB metadata snapshot + private blob files + cryptographic manifest (Spec 14.3, T33)."""
        import json
        import shutil

        out_dir = Path(bundle_dir).resolve()
        blobs_out = out_dir / "blobs"
        blobs_out.mkdir(parents=True, exist_ok=True)

        with self._lock:
            blob_entries: list[dict[str, Any]] = []
            for blob_id, blob in sorted(self.blob_vault._blobs_by_id.items()):
                src_file = (self.blob_vault.root_dir / blob.storage_key).resolve()
                rel_path = Path(blob.storage_key)
                dst_file = (blobs_out / rel_path).resolve()
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                actual_sha = hashlib.sha256(dst_file.read_bytes()).hexdigest()
                if actual_sha != blob.raw_sha256:
                    raise ValueError(f"Source blob integrity error before backup for {blob_id}")
                blob_entries.append(
                    {
                        "blob_id": blob.id,
                        "storage_key": blob.storage_key,
                        "raw_sha256": blob.raw_sha256,
                        "normalized_content_hash": blob.normalized_content_hash,
                        "byte_count": blob.byte_count,
                        "mime": blob.mime,
                        "authorized_source_ids": sorted(blob.authorized_source_ids),
                        "retention_class": blob.retention_class,
                    }
                )

            db_snapshot = {
                "current_release_id": self.current_release_id,
                "institutions": {k: v.model_dump(mode="json") for k, v in self.institutions.items()},
                "offerings": {k: v.model_dump(mode="json") for k, v in self.offerings.items()},
                "evidence": {k: v.model_dump(mode="json") for k, v in self.evidence.items()},
                "releases": {k: v.model_dump(mode="json") for k, v in self.releases.items()},
            }
            db_bytes = json.dumps(db_snapshot, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
            db_file = out_dir / "db_snapshot.json"
            db_file.write_bytes(db_bytes)
            db_sha256 = hashlib.sha256(db_bytes).hexdigest()

            manifest = {
                "backup_format_version": "1.1",
                "created_at": utc_now().isoformat(),
                "rpo_target_hours": 24,
                "rto_target_hours": 4,
                "db_snapshot_file": "db_snapshot.json",
                "db_snapshot_sha256": db_sha256,
                "blob_count": len(blob_entries),
                "evidence_count": len(self.evidence),
                "blobs": blob_entries,
            }
            manifest_bytes = json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
            (out_dir / "manifest.json").write_bytes(manifest_bytes)
            return manifest

    @staticmethod
    def verify_and_restore_backup_bundle(
        bundle_dir: str | Path,
        restore_vault_dir: str | Path,
    ) -> dict[str, Any]:
        """Restore DB + Storage files into an isolated directory and verify every evidence blob SHA-256 against the manifest (T33)."""
        import json
        import shutil

        in_dir = Path(bundle_dir).resolve()
        manifest_path = in_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError("Backup manifest.json is missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        db_path = in_dir / manifest["db_snapshot_file"]
        if not db_path.exists():
            raise FileNotFoundError("Backup db_snapshot.json is missing")
        actual_db_sha = hashlib.sha256(db_path.read_bytes()).hexdigest()
        if actual_db_sha != manifest["db_snapshot_sha256"]:
            raise ValueError("DB snapshot SHA-256 mismatch against manifest")

        db_data = json.loads(db_path.read_text(encoding="utf-8"))
        restored_store = MaintenanceStore(restore_vault_dir)

        blobs_in = in_dir / "blobs"
        verified_blobs = 0
        blob_id_to_sha: dict[str, str] = {}
        for b_meta in manifest["blobs"]:
            rel_key = b_meta["storage_key"]
            src_blob_file = (blobs_in / rel_key).resolve()
            if not src_blob_file.exists():
                raise FileNotFoundError(f"Missing blob file in backup bundle: {rel_key}")
            raw_bytes = src_blob_file.read_bytes()
            computed_sha = hashlib.sha256(raw_bytes).hexdigest()
            if computed_sha != b_meta["raw_sha256"]:
                raise ValueError(
                    f"Blob SHA-256 mismatch for {b_meta['blob_id']}: expected {b_meta['raw_sha256']}, got {computed_sha}"
                )
            dst_blob_file = (restored_store.blob_vault.root_dir / rel_key).resolve()
            dst_blob_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_blob_file, dst_blob_file)
            blob_rec = ContentBlobRecord(
                id=b_meta["blob_id"],
                raw_sha256=b_meta["raw_sha256"],
                normalized_content_hash=b_meta["normalized_content_hash"],
                storage_key=b_meta["storage_key"],
                byte_count=b_meta["byte_count"],
                mime=b_meta["mime"],
                authorized_source_ids=set(b_meta.get("authorized_source_ids", [])),
                retention_class=b_meta["retention_class"],
            )
            restored_store.blob_vault._blobs_by_id[blob_rec.id] = blob_rec
            restored_store.blob_vault._blobs_by_sha[blob_rec.raw_sha256] = blob_rec
            blob_id_to_sha[blob_rec.id] = computed_sha
            verified_blobs += 1

        verified_evidence_links = 0
        for ev_id, ev_dict in db_data.get("evidence", {}).items():
            ev_rec = EvidenceRecord.model_validate(ev_dict)
            restored_store.evidence[ev_id] = ev_rec
            if ev_rec.snapshot_id not in blob_id_to_sha:
                raise ValueError(f"Evidence {ev_id} references missing snapshot blob {ev_rec.snapshot_id} after restore")
            blob_obj = restored_store.blob_vault._blobs_by_id[ev_rec.snapshot_id]
            any_src = next(iter(blob_obj.authorized_source_ids))
            opened_bytes = restored_store.blob_vault.read_blob_authorized(
                ev_rec.snapshot_id,
                requesting_source_id=any_src,
            )
            if hashlib.sha256(opened_bytes).hexdigest() != blob_id_to_sha[ev_rec.snapshot_id]:
                raise ValueError(f"Restored evidence {ev_id} snapshot blob SHA-256 mismatch")
            verified_evidence_links += 1

        return {
            "manifest_verified": True,
            "db_sha256_verified": True,
            "verified_blobs": verified_blobs,
            "verified_evidence_links": verified_evidence_links,
            "restored_store": restored_store,
        }

