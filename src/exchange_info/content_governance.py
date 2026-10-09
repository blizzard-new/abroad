from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Protocol

import requests

from . import supabase_http
from .supabase_keys import supabase_key_headers
from .models import (
    ApplicationApplicabilityStatus,
    ApplicationDeadlineStatus,
    ApplicationRuleScope,
    ApplicationSupportStatus,
    ApplicationWorkflowComparison,
    ApplicationWorkflowApplicabilityUpdateRequest,
    ApplicationWorkflowPublicationAction,
    ApplicationWorkflowPublicationHistory,
    ApplicationWorkflowPublicationRevisionSummary,
    ApplicationWorkflowPublicationState,
    ApplicationWorkflowRefreshResult,
    ApplicationWorkflowReviewBacklog,
    ApplicationWorkflowReviewBacklogItem,
    ApplicationWorkflowReviewGapCode,
    ApplicationWorkflowReviewApproval,
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowRevision,
    ApplicationWorkflowRevisionEdit,
    ApplicationWorkflowRollbackRequest,
    ApplicationWorkflowSource,
    ApplicationWorkflowSourceEvidenceGapGroup,
    ApplicationWorkflowSourceEvidenceReviewRow,
    ApplicationWorkflowSourceMetadataResearchCandidate,
    ApplicationWorkflowSourceChange,
    ApplicationWorkflowStepChange,
    ApplicationWorkflowValueChange,
    UniversityApplicationWorkflow,
    utc_now,
)
from .settings import DEFAULT_DATA_DIR
from .source_url_policy import canonical_source_url_identity
from .review_source_metadata_candidates import (
    source_metadata_research_candidate_for_url,
)
from .storage import (
    cached_workflow_catalog,
    load_bundled_application_workflows,
    load_application_workflow_revisions,
    load_application_workflows,
    merge_application_workflows,
    replace_application_workflow,
    save_application_workflow_revisions,
    workflow_catalog_token,
)
from .workflow_structuring import structure_application_workflow
from .workflow_identity import workflow_storage_key
from .governance_commands import atomic_workflow_command, local_store_command_lock


class ContentGovernanceStore(Protocol):
    backend_name: str

    def load_published_workflows(self) -> list[UniversityApplicationWorkflow]: ...

    def list_revisions(self) -> list[ApplicationWorkflowRevision]: ...

    def save_revision(
        self, revision: ApplicationWorkflowRevision
    ) -> ApplicationWorkflowRevision: ...

    def publish_workflow(
        self,
        workflow: UniversityApplicationWorkflow,
        revision_id: str,
        *,
        workflow_key: str | None = None,
    ) -> UniversityApplicationWorkflow: ...


_WORKFLOW_COMPARISON_FIELDS = (
    ("home_university", "本校"),
    ("school_name", "合作校"),
    ("partner_website", "合作校官網"),
    ("country", "國家／地區"),
    ("program_type", "計畫類型"),
    ("academic_year", "適用學年度"),
    ("application_round", "申請梯次"),
    ("effective_application_rounds", "有效梯次"),
    ("applicability_status", "適用範圍狀態"),
    ("applicability_note", "適用範圍說明"),
    ("coverage_status", "資料涵蓋狀態"),
    ("coverage_note", "資料涵蓋說明"),
    ("disclaimer", "學生端提醒"),
)

_STEP_COMPARISON_FIELDS = (
    ("order", "步驟順序"),
    ("phase", "階段"),
    ("title", "標題"),
    ("responsible_party", "負責角色"),
    ("responsible_unit", "承辦單位"),
    ("timing", "時程文字"),
    ("deadline_at", "精確期限"),
    ("deadline_status", "期限狀態"),
    ("deadline_source_url", "期限來源"),
    ("deadline_reminder_eligible", "可建立期限提醒"),
    ("summary", "步驟摘要"),
    ("details", "詳細說明"),
    ("document_requirements", "文件要求"),
    ("signature_requirements", "簽名／核章要求"),
    ("official_form_urls", "官方表單"),
    ("scope", "適用校系／年度／梯次"),
    ("submission", "送件方式與地點"),
    ("action_url", "操作連結"),
    ("source_urls", "步驟來源"),
    ("support_status", "支援狀態"),
    ("confirmation_contact", "待確認聯絡單位"),
    ("needs_confirmation", "仍需確認"),
)

_SOURCE_COMPARISON_FIELDS = (
    ("title", "來源名稱"),
    ("role", "來源角色"),
    ("authority", "來源權威層級"),
    ("priority", "來源優先序"),
    ("effective_academic_year", "來源適用學年度"),
    ("application_round", "來源適用梯次"),
    ("content_hash", "來源內容版本"),
)

_SOURCE_EVIDENCE_REVIEW_SCHEMA_VERSION = 1

_COMPARISON_VALUE_LABELS = {
    "verified": "已核對",
    "needs_confirmation": "仍需人工確認",
    "unverified": "尚未核對",
    "legacy_unclassified": "舊資料未分類",
    "not_applicable": "不適用",
    "verified_exact": "官方精確期限",
    "reference_only": "僅供參考",
    "online": "線上送件",
    "paper": "紙本送件",
    "email": "Email 送件",
    "in_person": "親送",
    "mixed": "混合送件",
    "unknown": "待確認",
    "original": "正本",
    "copy": "影本",
    "original_and_copy": "正本與影本",
    "digital": "電子檔",
    "unspecified": "未註明",
    "official_verified": "官方資料已核對",
    "official_partial": "官方資料部分核對",
    "not_collected": "尚未收集",
}


class LocalContentGovernanceStore:
    backend_name = "local-jsonl"

    def __init__(
        self,
        data_dir: Path = DEFAULT_DATA_DIR,
        *,
        include_bundled_baseline: bool = False,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.include_bundled_baseline = include_bundled_baseline

    def catalog_token(self) -> tuple:
        return workflow_catalog_token(self.data_dir)

    def command_snapshot(self):
        from .governance_commands import local_workflow_snapshot
        return local_workflow_snapshot(self)

    def commit_command(self, expected, changed, published, *, operation, actor):
        from .governance_commands import local_commit_workflow_command
        return local_commit_workflow_command(self, expected, changed, published, operation=operation, actor=actor)

    @local_store_command_lock
    def load_published_workflows(self) -> list[UniversityApplicationWorkflow]:
        def build() -> list[UniversityApplicationWorkflow]:
            local = load_application_workflows(self.data_dir)
            if not self.include_bundled_baseline:
                return local
            return merge_application_workflows(
                load_bundled_application_workflows(),
                local,
            )

        return cached_workflow_catalog(("published", self.catalog_token(), self.include_bundled_baseline), build)

    @local_store_command_lock
    def list_revisions(self) -> list[ApplicationWorkflowRevision]:
        return load_application_workflow_revisions(self.data_dir)

    @local_store_command_lock
    def save_revision(
        self, revision: ApplicationWorkflowRevision
    ) -> ApplicationWorkflowRevision:
        revisions = {
            row.id: row for row in load_application_workflow_revisions(self.data_dir)
        }
        revisions[revision.id] = revision
        save_application_workflow_revisions(
            sorted(revisions.values(), key=lambda row: row.detected_at),
            self.data_dir,
        )
        return revision

    @local_store_command_lock
    def publish_workflow(
        self,
        workflow: UniversityApplicationWorkflow,
        revision_id: str,
        *,
        workflow_key: str | None = None,
    ) -> UniversityApplicationWorkflow:
        replace_application_workflow(workflow, self.data_dir)
        return workflow


class SupabaseContentGovernanceStore:
    backend_name = "supabase"

    def __init__(
        self,
        url: str,
        service_role_key: str,
        *,
        fallback: LocalContentGovernanceStore | None = None,
        request_func=supabase_http.request,
    ) -> None:
        if not url.strip().casefold().startswith("https://"):
            raise ValueError("Supabase URL 必須使用 HTTPS。")
        self.url = url.rstrip("/")
        self.service_role_key = service_role_key
        self.fallback = fallback
        self.request_func = request_func
        self._published_lock = threading.Lock()
        self._published: tuple[float, tuple, list[UniversityApplicationWorkflow]] | None = None

    @property
    def headers(self) -> dict[str, str]:
        return {
            **supabase_key_headers(self.service_role_key),
            "Content-Type": "application/json",
        }

    # Every catalogue request asked Supabase (Sydney) for the published workflows and merged them again. What is published
    # only changes through this store, so the merged result is kept for a short while and dropped as soon as this store
    # saves or publishes anything (or the local files behind the fallback change).
    PUBLISHED_CACHE_SECONDS = 20.0

    def _forget_published(self) -> None:
        with self._published_lock:
            self._published = None

    def command_snapshot(self):
        from .governance_commands import supabase_workflow_snapshot
        return supabase_workflow_snapshot(self)

    def commit_command(self, expected, changed, published, *, operation, actor):
        from .governance_commands import supabase_commit_workflow_command
        return supabase_commit_workflow_command(self, expected, changed, published, operation=operation, actor=actor)

    def load_published_workflows(self) -> list[UniversityApplicationWorkflow]:
        token = self.fallback.catalog_token() if hasattr(self.fallback, "catalog_token") else None
        with self._published_lock:
            cached = self._published
        if (
            cached is not None
            and token is not None
            and cached[1] == token
            and time.monotonic() - cached[0] < self.PUBLISHED_CACHE_SECONDS
        ):
            return list(cached[2])
        response = self._request(
            "GET",
            "/rest/v1/application_workflows",
            params={
                "select": "published_payload",
                "published_payload": "not.is.null",
            },
        )
        remote = [
            UniversityApplicationWorkflow.model_validate(row["published_payload"])
            for row in response.json()
        ]
        if self.fallback is None:
            return remote
        merged = {
            workflow_storage_key(row): row
            for row in self.fallback.load_published_workflows()
        }
        merged.update({workflow_storage_key(row): row for row in remote})
        rows = list(merged.values())
        if token is not None:
            with self._published_lock:
                self._published = (time.monotonic(), token, rows)
        return list(rows)

    def list_revisions(self) -> list[ApplicationWorkflowRevision]:
        response = self._request(
            "GET",
            "/rest/v1/application_workflow_revisions",
            params={"select": "*", "order": "detected_at.asc"},
        )
        return [self._revision_from_row(row) for row in response.json()]

    def save_revision(
        self, revision: ApplicationWorkflowRevision
    ) -> ApplicationWorkflowRevision:
        workflow = revision.workflow
        row = self._revision_row(revision)
        self._forget_published()
        self._request(
            "POST",
            "/rest/v1/rpc/exchange_commit_application_workflow_revision",
            json={
                "p_revision_id": row["id"],
                "p_workflow_key": row["workflow_key"],
                "p_version": row["version"],
                "p_base_version": row["base_version"],
                "p_status": row["status"],
                "p_content_hash": row["content_hash"],
                "p_change_summary": row["change_summary"],
                "p_workflow_payload": row["workflow_payload"],
                "p_detected_by": row["detected_by"],
                "p_detected_at": row["detected_at"],
                "p_required_review_count": row["required_review_count"],
                "p_review_approvals": row["review_approvals"],
                "p_edit_history": row["edit_history"],
                "p_reviewed_by": row["reviewed_by"],
                "p_reviewed_at": row["reviewed_at"],
                "p_review_note": row["review_note"],
                "p_publication_action": row["publication_action"],
                "p_rolled_back_from_revision_id": row["rolled_back_from_revision_id"],
                "p_restored_revision_id": row["restored_revision_id"],
                "p_home_university": workflow.home_university,
                "p_partner_university": workflow.school_name,
                "p_program_type": workflow.program_type,
                "p_academic_year": workflow.academic_year,
                "p_application_round": workflow.application_round,
                "p_updated_at": utc_now().isoformat(),
            },
        )
        return revision

    def publish_workflow(
        self,
        workflow: UniversityApplicationWorkflow,
        revision_id: str,
        *,
        workflow_key: str | None = None,
    ) -> UniversityApplicationWorkflow:
        self._forget_published()
        self._request(
            "POST",
            "/rest/v1/rpc/exchange_commit_application_workflow_publication",
            json={
                "p_workflow_key": workflow_key or workflow_storage_key(workflow),
                "p_home_university": workflow.home_university,
                "p_partner_university": workflow.school_name,
                "p_program_type": workflow.program_type,
                "p_academic_year": workflow.academic_year,
                "p_application_round": workflow.application_round,
                "p_published_version": workflow.version,
                "p_published_payload": workflow.model_dump(mode="json"),
                "p_published_at": (
                    workflow.published_at.isoformat() if workflow.published_at else None
                ),
                "p_current_revision_id": revision_id,
                "p_updated_at": utc_now().isoformat(),
            },
        )
        return workflow

    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs,
    ):
        merged_headers = {**self.headers, **(headers or {})}
        try:
            response = self.request_func(
                method,
                f"{self.url}{path}",
                headers=merged_headers,
                timeout=20,
                **kwargs,
            )
            response.raise_for_status()
            return response
        finally:
            if method.upper() != "GET":
                # Also after the write: a reader that cached the old rows while it was in flight must not keep them.
                self._forget_published()

    @staticmethod
    def _revision_row(revision: ApplicationWorkflowRevision) -> dict:
        return {
            "id": revision.id,
            "workflow_key": revision.workflow_key,
            "version": revision.version,
            "base_version": revision.base_version,
            "status": revision.status.value,
            "content_hash": revision.content_hash,
            "change_summary": revision.change_summary,
            "workflow_payload": revision.workflow.model_dump(mode="json"),
            "detected_by": revision.detected_by,
            "detected_at": revision.detected_at.isoformat(),
            "required_review_count": revision.required_review_count,
            "review_approvals": [
                approval.model_dump(mode="json")
                for approval in revision.review_approvals
            ],
            "edit_history": [
                edit.model_dump(mode="json") for edit in revision.edit_history
            ],
            "reviewed_by": revision.reviewed_by,
            "reviewed_at": (
                revision.reviewed_at.isoformat() if revision.reviewed_at else None
            ),
            "review_note": revision.review_note,
            "publication_action": revision.publication_action.value,
            "rolled_back_from_revision_id": (
                revision.rolled_back_from_revision_id
            ),
            "restored_revision_id": revision.restored_revision_id,
        }

    @staticmethod
    def _revision_from_row(row: dict) -> ApplicationWorkflowRevision:
        return ApplicationWorkflowRevision.model_validate(
            {
                "id": row["id"],
                "workflow_key": row["workflow_key"],
                "version": row["version"],
                "base_version": row.get("base_version"),
                "status": row["status"],
                "content_hash": row["content_hash"],
                "change_summary": row.get("change_summary") or [],
                "workflow": row["workflow_payload"],
                "detected_by": row.get("detected_by") or "automated_refresh",
                "detected_at": row["detected_at"],
                "required_review_count": row.get("required_review_count") or 2,
                "review_approvals": row.get("review_approvals") or [],
                "edit_history": row.get("edit_history") or [],
                "reviewed_by": row.get("reviewed_by"),
                "reviewed_at": row.get("reviewed_at"),
                "review_note": row.get("review_note"),
                "publication_action": row.get("publication_action") or "standard",
                "rolled_back_from_revision_id": row.get(
                    "rolled_back_from_revision_id"
                ),
                "restored_revision_id": row.get("restored_revision_id"),
            }
        )


def create_content_governance_store(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> ContentGovernanceStore:
    # The product runtime always needs the tracked official baseline, even when
    # account/session data lives in an isolated preview or deployment directory.
    # Direct LocalContentGovernanceStore callers remain isolated by default.
    local = LocalContentGovernanceStore(data_dir, include_bundled_baseline=True)
    url = (
        os.environ.get("EXCHANGE_SUPABASE_URL")
        or os.environ.get("SUPABASE_URL")
        or ""
    ).strip()
    key = (
        os.environ.get("EXCHANGE_SUPABASE_SECRET_KEY")
        or os.environ.get("SUPABASE_SECRET_KEY")
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()
    if url and key:
        return SupabaseContentGovernanceStore(url, key, fallback=local)
    return local


def _source_evidence_review_snapshot_fingerprint(
    source_url: str,
    workflow_snapshots: dict[str, dict[str, object]],
    research_candidate: ApplicationWorkflowSourceMetadataResearchCandidate | None,
) -> str:
    """Bind one source-evidence export to its exact rows and research candidate."""

    canonical = json.dumps(
        {
            "source_evidence_review_schema_version": (
                _SOURCE_EVIDENCE_REVIEW_SCHEMA_VERSION
            ),
            "source_url": canonical_source_url_identity(source_url),
            "workflows": [
                {
                    "workflow_key": workflow_key,
                    **workflow_snapshots[workflow_key],
                }
                for workflow_key in sorted(workflow_snapshots)
            ],
            "research_candidate": (
                research_candidate.model_dump(mode="json")
                if research_candidate is not None
                else None
            ),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def list_workflow_review_backlog(
    store: ContentGovernanceStore,
) -> ApplicationWorkflowReviewBacklog:
    """List published legacy workflows that have not passed the dual-review gate."""
    revisions = store.list_revisions()
    pending_by_key: dict[str, ApplicationWorkflowRevision] = {}
    for revision in sorted(revisions, key=lambda row: row.detected_at, reverse=True):
        if (
            revision.status == ApplicationWorkflowReviewStatus.PENDING_REVIEW
            and revision.workflow_key not in pending_by_key
        ):
            pending_by_key[revision.workflow_key] = revision

    items: list[ApplicationWorkflowReviewBacklogItem] = []
    source_metadata_gap_groups_by_url: dict[str, dict[str, object]] = {}
    confirmation_statuses = {
        ApplicationSupportStatus.NEEDS_CONFIRMATION,
        ApplicationSupportStatus.UNVERIFIED,
        ApplicationSupportStatus.LEGACY_UNCLASSIFIED,
    }
    for workflow in store.load_published_workflows():
        if (
            workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
            and workflow.published_at is not None
        ):
            continue
        key = workflow_storage_key(workflow)
        pending = pending_by_key.get(key)
        if pending is not None:
            if workflow_storage_key(pending.workflow) != key:
                raise RuntimeError(
                    "待審版本的穩定流程身分與公開版不一致，不能產生審查待辦。"
                )
            workflow = pending.workflow
        academic_year_ready = bool((workflow.academic_year or "").strip())
        effective_application_rounds = list(
            dict.fromkeys(
                value.strip()
                for value in [
                    workflow.application_round,
                    *workflow.effective_application_rounds,
                ]
                if value and value.strip()
            )
        )
        effective_round_ready = bool(effective_application_rounds)
        verified_exact_deadline_count = sum(
            step.deadline_status == ApplicationDeadlineStatus.VERIFIED_EXACT
            and step.deadline_at is not None
            and bool((step.deadline_source_url or "").strip())
            and step.deadline_checked_at is not None
            for step in workflow.steps
        )
        reference_deadline_count = sum(
            step.deadline_status == ApplicationDeadlineStatus.REFERENCE_ONLY
            for step in workflow.steps
        )
        source_metadata = workflow_review_source_metadata(workflow)
        source_metadata_missing_count = sum(
            source is None
            or not source.title.strip()
            or source.authority is None
            for source in source_metadata.values()
        )
        source_year_missing_count = sum(
            source is None
            or not bool((source.effective_academic_year or "").strip())
            or bool((workflow.academic_year or "").strip())
            and source.effective_academic_year.strip() != workflow.academic_year.strip()
            for source in source_metadata.values()
        )
        review_timestamp_missing_count = (
            int(workflow.last_checked is None)
            + sum(
                source is None or source.checked_at is None
                for source in source_metadata.values()
            )
            + sum(step.checked_at is None for step in workflow.steps)
        )
        review_source_urls = workflow_review_source_urls(workflow)
        rule_source_urls = workflow_review_rule_source_urls(workflow)
        for source_url, source in source_metadata.items():
            if (
                source is not None
                and source.title.strip()
                and source.authority is not None
            ):
                continue
            source_key = canonical_source_url_identity(source_url)
            group = source_metadata_gap_groups_by_url.setdefault(
                source_key,
                {
                    "source_url": source_url,
                    "workflow_keys": set(),
                    "workflow_snapshots": {},
                    "home_universities": set(),
                    "school_names": set(),
                    "critical_rule_reference_count": 0,
                },
            )
            workflow_keys = group["workflow_keys"]
            workflow_snapshots = group["workflow_snapshots"]
            home_universities = group["home_universities"]
            school_names = group["school_names"]
            assert isinstance(workflow_keys, set)
            assert isinstance(workflow_snapshots, dict)
            assert isinstance(home_universities, set)
            assert isinstance(school_names, set)
            workflow_keys.add(key)
            workflow_snapshots[key] = {
                "content_hash": workflow_content_hash(workflow),
                "workflow_version": workflow.version,
                "has_pending_revision": pending is not None,
                "pending_revision_id": pending.id if pending is not None else None,
                "current_source_checked_at": (
                    source.checked_at.isoformat()
                    if source is not None and source.checked_at is not None
                    else None
                ),
            }
            home_universities.add(workflow.home_university)
            school_names.add(workflow.school_name)
            group["critical_rule_reference_count"] = int(
                group["critical_rule_reference_count"]
            ) + sum(
                source_key
                in {
                    canonical_source_url_identity(url)
                    for url in source_urls
                }
                for source_urls in rule_source_urls.values()
            )
        critical_rule_source_gap_count = sum(
            not source_urls for source_urls in rule_source_urls.values()
        )
        insecure_source_count = sum(
            not source_url.casefold().startswith("https://")
            for source_url in review_source_urls
        )
        needs_confirmation_count = sum(
            step.needs_confirmation or step.support_status in confirmation_statuses
            for step in workflow.steps
        )
        review_gap_codes: list[ApplicationWorkflowReviewGapCode] = []
        if not academic_year_ready:
            review_gap_codes.append(
                ApplicationWorkflowReviewGapCode.MISSING_ACADEMIC_YEAR
            )
        if not effective_round_ready:
            review_gap_codes.append(
                ApplicationWorkflowReviewGapCode.MISSING_EFFECTIVE_ROUND
            )
        if verified_exact_deadline_count == 0:
            review_gap_codes.append(
                ApplicationWorkflowReviewGapCode.NO_VERIFIED_EXACT_DEADLINE
            )
        if source_year_missing_count:
            review_gap_codes.append(
                ApplicationWorkflowReviewGapCode.SOURCE_YEAR_MISSING
            )
        if source_metadata_missing_count:
            review_gap_codes.append(
                ApplicationWorkflowReviewGapCode.SOURCE_METADATA_MISSING
            )
        if review_timestamp_missing_count:
            review_gap_codes.append(
                ApplicationWorkflowReviewGapCode.REVIEW_TIMESTAMP_MISSING
            )
        if critical_rule_source_gap_count:
            review_gap_codes.append(
                ApplicationWorkflowReviewGapCode.CRITICAL_RULE_SOURCE_MISSING
            )
        if insecure_source_count:
            review_gap_codes.append(
                ApplicationWorkflowReviewGapCode.INSECURE_OFFICIAL_SOURCE
            )
        if needs_confirmation_count:
            review_gap_codes.append(
                ApplicationWorkflowReviewGapCode.NEEDS_CONFIRMATION
            )
        items.append(
            ApplicationWorkflowReviewBacklogItem(
                workflow_key=key,
                home_university=workflow.home_university,
                school_name=workflow.school_name,
                country=workflow.country,
                program_type=workflow.program_type,
                academic_year=workflow.academic_year,
                application_round=workflow.application_round,
                effective_application_rounds=effective_application_rounds,
                version=workflow.version,
                review_status=workflow.review_status,
                step_count=len(workflow.steps),
                source_count=len(review_source_urls),
                critical_rule_count=len(workflow_review_rule_keys(workflow)),
                critical_rule_source_gap_count=critical_rule_source_gap_count,
                insecure_source_count=insecure_source_count,
                needs_confirmation_count=needs_confirmation_count,
                academic_year_ready=academic_year_ready,
                effective_round_ready=effective_round_ready,
                verified_exact_deadline_count=verified_exact_deadline_count,
                reference_deadline_count=reference_deadline_count,
                source_year_missing_count=source_year_missing_count,
                source_metadata_missing_count=source_metadata_missing_count,
                review_timestamp_missing_count=review_timestamp_missing_count,
                review_gap_codes=review_gap_codes,
                review_gap_count=len(review_gap_codes),
                has_pending_revision=pending is not None,
                pending_revision_id=pending.id if pending is not None else None,
                review_approval_count=(
                    len(pending.review_approvals) if pending is not None else 0
                ),
                required_review_count=(
                    pending.required_review_count if pending is not None else 2
                ),
                review_ready_to_publish=(
                    pending is not None
                    and len(pending.review_approvals)
                    >= pending.required_review_count
                ),
            )
        )
    items.sort(
        key=lambda row: (
            row.home_university.casefold(),
            row.school_name.casefold(),
            (row.program_type or "").casefold(),
            row.academic_year or "",
            row.application_round or "",
        )
    )
    staged_count = sum(row.has_pending_revision for row in items)
    source_metadata_gap_groups = []
    for source_key, group in source_metadata_gap_groups_by_url.items():
        source_url = source_key
        workflow_snapshots = group["workflow_snapshots"]
        assert isinstance(workflow_snapshots, dict)
        research_candidate = source_metadata_research_candidate_for_url(source_url)
        source_metadata_gap_groups.append(
            ApplicationWorkflowSourceEvidenceGapGroup(
                source_url=source_url,
                source_evidence_snapshot_fingerprint=(
                    _source_evidence_review_snapshot_fingerprint(
                        source_url,
                        workflow_snapshots,
                        research_candidate,
                    )
                ),
                workflow_count=len(group["workflow_keys"]),
                critical_rule_reference_count=int(
                    group["critical_rule_reference_count"]
                ),
                home_universities=sorted(
                    group["home_universities"], key=str.casefold
                ),
                school_names=sorted(group["school_names"], key=str.casefold),
                workflow_keys=sorted(group["workflow_keys"]),
                research_candidate=research_candidate,
            )
        )
    source_metadata_gap_groups.sort(
        key=lambda group: (
            -group.workflow_count,
            group.source_url.casefold(),
            group.source_url,
        )
    )
    return ApplicationWorkflowReviewBacklog(
        items=items,
        total_count=len(items),
        unstaged_count=len(items) - staged_count,
        staged_count=staged_count,
        review_unstarted_count=sum(
            row.has_pending_revision and row.review_approval_count == 0
            for row in items
        ),
        review_partially_approved_count=sum(
            row.has_pending_revision
            and 0 < row.review_approval_count < row.required_review_count
            for row in items
        ),
        review_ready_count=sum(row.review_ready_to_publish for row in items),
        critical_rule_count=sum(row.critical_rule_count for row in items),
        workflows_with_critical_rule_source_gaps=sum(
            row.critical_rule_source_gap_count > 0 for row in items
        ),
        workflows_with_insecure_sources=sum(
            row.insecure_source_count > 0 for row in items
        ),
        missing_academic_year_count=sum(
            not row.academic_year_ready for row in items
        ),
        missing_effective_round_count=sum(
            not row.effective_round_ready for row in items
        ),
        no_verified_exact_deadline_count=sum(
            row.verified_exact_deadline_count == 0 for row in items
        ),
        workflows_with_source_year_gaps=sum(
            row.source_year_missing_count > 0 for row in items
        ),
        workflows_with_source_metadata_gaps=sum(
            row.source_metadata_missing_count > 0 for row in items
        ),
        source_metadata_gap_reference_count=sum(
            row.source_metadata_missing_count for row in items
        ),
        distinct_source_metadata_gap_url_count=len(source_metadata_gap_groups),
        source_metadata_gap_groups=source_metadata_gap_groups,
        workflows_with_review_timestamp_gaps=sum(
            row.review_timestamp_missing_count > 0 for row in items
        ),
        needs_confirmation_workflow_count=sum(
            row.needs_confirmation_count > 0 for row in items
        ),
        home_universities=sorted(
            {row.home_university for row in items},
            key=str.casefold,
        ),
    )


@atomic_workflow_command
def stage_existing_workflow_for_review(
    store: ContentGovernanceStore,
    workflow_key: str,
    *,
    detected_by: str,
) -> ApplicationWorkflowRevision:
    """Copy an existing public workflow into review without changing public data."""
    current = next(
        (
            workflow
            for workflow in store.load_published_workflows()
            if workflow_storage_key(workflow) == workflow_key
        ),
        None,
    )
    if current is None:
        raise LookupError("找不到指定的既有申請流程。")
    if (
        current.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
        and current.published_at is not None
    ):
        raise ValueError("這個流程已通過雙人審核並正式發布。")

    revisions = [
        row for row in store.list_revisions() if row.workflow_key == workflow_key
    ]
    existing_pending = next(
        (
            row
            for row in sorted(
                revisions,
                key=lambda revision: revision.detected_at,
                reverse=True,
            )
            if row.status == ApplicationWorkflowReviewStatus.PENDING_REVIEW
        ),
        None,
    )
    if existing_pending is not None:
        return existing_pending

    current_hash = workflow_content_hash(current)
    baseline = next(
        (
            row
            for row in revisions
            if row.version == current.version
            and row.content_hash == current_hash
            and row.status
            in {
                ApplicationWorkflowReviewStatus.PUBLISHED,
                ApplicationWorkflowReviewStatus.SUPERSEDED,
            }
        ),
        None,
    )
    if baseline is None:
        if any(row.version == current.version for row in revisions):
            raise ValueError("既有流程版本與審核紀錄衝突，請先由管理者排除。")
        baseline = ApplicationWorkflowRevision(
            workflow_key=workflow_key,
            version=current.version,
            base_version=None,
            # A historical unreviewed reference is a comparison baseline,
            # never evidence of an independently reviewed publication.
            status=ApplicationWorkflowReviewStatus.SUPERSEDED,
            content_hash=current_hash,
            change_summary=["匯入既有公開流程作為雙人審核基準。"],
            workflow=current,
            detected_by="legacy_import",
            reviewed_by="legacy_import",
            reviewed_at=current.published_at or current.last_checked or utc_now(),
            review_note="系統導入雙人內容審核前已存在的學生可見流程。",
        )
        store.save_revision(baseline)
        revisions.append(baseline)

    version = max(
        [row.version for row in revisions] + [current.version]
    ) + 1
    staged_workflow = current.model_copy(
        update={
            "governance_key": workflow_key,
            "version": version,
            "review_status": ApplicationWorkflowReviewStatus.PENDING_REVIEW,
            "published_at": None,
            "supersedes_version": current.version,
            "applied_context": None,
        }
    )
    revision = ApplicationWorkflowRevision(
        workflow_key=workflow_key,
        version=version,
        base_version=current.version,
        content_hash=current_hash,
        change_summary=["將既有流程納入雙人逐條查核；學生可見內容尚未變更。"],
        workflow=staged_workflow,
        detected_by=detected_by,
    )
    return store.save_revision(revision)


@atomic_workflow_command
def stage_workflow_refresh(
    store: ContentGovernanceStore,
    candidate: UniversityApplicationWorkflow,
    *,
    detected_by: str = "automated_refresh",
) -> ApplicationWorkflowRefreshResult:
    candidate = structure_application_workflow(candidate)
    key = workflow_storage_key(candidate)
    current = next(
        (
            row
            for row in store.load_published_workflows()
            if workflow_storage_key(row) == key
        ),
        None,
    )
    content_hash = workflow_content_hash(candidate)
    if current and workflow_content_hash(current) == content_hash:
        return ApplicationWorkflowRefreshResult(
            change_detected=False,
            current_version=current.version,
            workflow=current,
        )

    revisions = [row for row in store.list_revisions() if row.workflow_key == key]
    if current is not None and not any(
        row.content_hash == workflow_content_hash(current)
        and row.status
        in {
            ApplicationWorkflowReviewStatus.PUBLISHED,
            ApplicationWorkflowReviewStatus.SUPERSEDED,
        }
        for row in revisions
    ):
        baseline = ApplicationWorkflowRevision(
            workflow_key=key,
            version=current.version,
            base_version=None,
            status=ApplicationWorkflowReviewStatus.SUPERSEDED,
            content_hash=workflow_content_hash(current),
            change_summary=["匯入既有已發布流程作為版本基線。"],
            workflow=current,
            detected_by="legacy_import",
            reviewed_by="legacy_import",
            reviewed_at=current.published_at or current.last_checked or utc_now(),
            review_note="系統導入內容治理前已存在的公開流程。",
        )
        store.save_revision(baseline)
        revisions.append(baseline)
    existing_pending = next(
        (
            row
            for row in revisions
            if row.status == ApplicationWorkflowReviewStatus.PENDING_REVIEW
            and row.content_hash == content_hash
        ),
        None,
    )
    if existing_pending is not None:
        return ApplicationWorkflowRefreshResult(
            change_detected=True,
            current_version=current.version if current else None,
            revision=existing_pending,
            workflow=existing_pending.workflow,
        )
    highest_version = max(
        [row.version for row in revisions]
        + ([current.version] if current is not None else [0])
    )
    version = highest_version + 1
    staged_workflow = candidate.model_copy(
        update={
            "governance_key": key,
            "version": version,
            "review_status": ApplicationWorkflowReviewStatus.PENDING_REVIEW,
            "published_at": None,
            "supersedes_version": current.version if current else None,
            "applied_context": None,
        }
    )
    revision = ApplicationWorkflowRevision(
        workflow_key=key,
        version=version,
        base_version=current.version if current else None,
        content_hash=content_hash,
        change_summary=summarize_workflow_changes(current, candidate),
        workflow=staged_workflow,
        detected_by=detected_by,
    )
    store.save_revision(revision)
    return ApplicationWorkflowRefreshResult(
        change_detected=True,
        current_version=current.version if current else None,
        revision=revision,
        workflow=staged_workflow,
    )


@atomic_workflow_command
def update_pending_workflow_applicability(
    store: ContentGovernanceStore,
    revision_id: str,
    payload: ApplicationWorkflowApplicabilityUpdateRequest,
    *,
    edited_by: str,
) -> ApplicationWorkflowRevision:
    """Edit applicability evidence on a pending revision without changing public data."""

    revisions = store.list_revisions()
    revision = _revision_for_review(revisions, revision_id)
    if revision.content_hash != payload.expected_content_hash:
        raise ValueError("待審版本已由其他管理者修改，請重新載入後再儲存。")

    normalized_editor = edited_by.strip()
    if not normalized_editor:
        raise ValueError("編輯者識別不可為空白。")

    source_updates = {
        canonical_source_url_identity(row.source_url): row
        for row in payload.source_updates
    }
    available_sources = {
        canonical_source_url_identity(row.source_url): row
        for row in revision.workflow.sources
    }
    review_source_keys = {
        canonical_source_url_identity(source_url)
        for source_url in workflow_review_source_urls(revision.workflow)
    }
    unknown_sources = [
        row.source_url
        for row in payload.source_updates
        if canonical_source_url_identity(row.source_url) not in review_source_keys
    ]
    if unknown_sources:
        raise ValueError("修正內容包含不屬於此版本的官方來源。")
    new_source_updates = [
        row
        for row in payload.source_updates
        if canonical_source_url_identity(row.source_url) not in available_sources
    ]
    metadata_source_updates = [
        row
        for row in payload.source_updates
        if canonical_source_url_identity(row.source_url) not in available_sources
        or not available_sources[
            canonical_source_url_identity(row.source_url)
        ].title.strip()
        or available_sources[canonical_source_url_identity(row.source_url)].authority
        is None
    ]
    if any(
        not row.title or row.role is None or row.authority is None
        for row in metadata_source_updates
    ):
        raise ValueError("尚未建立證據資料的來源必須填寫來源名稱、角色與權威層級。")
    if any(
        row.replacement_source_url
        and canonical_source_url_identity(row.replacement_source_url)
        != canonical_source_url_identity(row.source_url)
        for row in new_source_updates
    ):
        raise ValueError("新增來源證據資料與安全網址替換必須分開處理。")

    replacement_urls = {
        source_key: source_update.replacement_source_url
        for source_key, source_update in source_updates.items()
        if source_update.replacement_source_url
        and canonical_source_url_identity(source_update.replacement_source_url)
        != source_key
    }
    resulting_source_groups: dict[str, list[ApplicationWorkflowSource]] = {}
    for source in revision.workflow.sources:
        target_url = (
            replacement_urls.get(
                canonical_source_url_identity(source.source_url)
            )
            or source.source_url
        ).strip()
        resulting_source_groups.setdefault(
            canonical_source_url_identity(target_url), []
        ).append(source)
    for target_key, grouped_sources in resulting_source_groups.items():
        if len(grouped_sources) < 2:
            continue
        # Existing evidence can cite one URL for different official roles.
        # An applicability edit does not merge those records or replace a URL.
        if not any(canonical_source_url_identity(source.source_url) in replacement_urls
                   for source in grouped_sources):
            continue
        grouped_updates = [
            source_updates.get(
                canonical_source_url_identity(source.source_url)
            )
            for source in grouped_sources
        ]
        if any(
            source_update is None
            or not source_update.replacement_source_url
            or canonical_source_url_identity(
                source_update.replacement_source_url
            )
            != target_key
            for source_update in grouped_updates
        ):
            raise ValueError("替代網址會與未合併的官方來源重複。")
        source_signatures = {
            (
                source.title.strip(),
                source.role,
                source.authority,
                source.priority,
                source.content_hash,
            )
            for source in grouped_sources
        }
        update_signatures = {
            (
                source_update.effective_academic_year,
                source_update.application_round,
            )
            for source_update in grouped_updates
            if source_update is not None
        }
        if len(source_signatures) != 1 or len(update_signatures) != 1:
            raise ValueError("要合併的官方來源中繼資料不一致，請分開處理。")

    def replace_source_url(source_url: str | None) -> str | None:
        normalized = (source_url or "").strip()
        if not normalized:
            return source_url
        return (
            replacement_urls.get(canonical_source_url_identity(normalized))
            or normalized
        )

    def replace_source_urls(source_urls: list[str]) -> list[str]:
        updated: list[str] = []
        seen: set[str] = set()
        for source_url in source_urls:
            replacement = replace_source_url(source_url)
            if replacement is None:
                continue
            key = canonical_source_url_identity(replacement)
            if key in seen:
                continue
            seen.add(key)
            updated.append(replacement)
        return updated

    now = utc_now()
    updated_sources = []
    updated_source_keys: set[str] = set()
    for source in revision.workflow.sources:
        source_update = source_updates.get(
            canonical_source_url_identity(source.source_url)
        )
        if source_update is None:
            updated_source_keys.add(
                canonical_source_url_identity(source.source_url)
            )
            updated_sources.append(source)
            continue
        updated_source = source.model_copy(
            update={
                "source_url": replace_source_url(source.source_url),
                "title": source_update.title or source.title,
                "role": source_update.role or source.role,
                "authority": source_update.authority or source.authority,
                "effective_academic_year": source_update.effective_academic_year,
                "application_round": source_update.application_round,
                "checked_at": now,
            }
        )
        updated_source_key = canonical_source_url_identity(
            updated_source.source_url
        )
        if (updated_source_key in updated_source_keys
            and canonical_source_url_identity(source.source_url) in replacement_urls):
            continue
        updated_source_keys.add(updated_source_key)
        updated_sources.append(updated_source)
    for source_update in new_source_updates:
        source_key = canonical_source_url_identity(source_update.source_url)
        if source_key in updated_source_keys:
            continue
        updated_source_keys.add(source_key)
        updated_sources.append(
            ApplicationWorkflowSource(
                title=source_update.title or source_update.source_url,
                source_url=source_update.source_url,
                role=source_update.role,
                authority=source_update.authority,
                effective_academic_year=source_update.effective_academic_year,
                application_round=source_update.application_round,
                checked_at=now,
            )
        )

    updated_steps = []
    for step in revision.workflow.steps:
        scope = step.scope.model_copy(
            update={
                "academic_years": step.scope.academic_years
                or [payload.academic_year],
                "application_rounds": step.scope.application_rounds
                or ([payload.application_round] if payload.application_round else []),
            }
        )
        updated_documents = [
            document.model_copy(
                update={
                    "source_urls": replace_source_urls(document.source_urls),
                    "official_form_url": replace_source_url(
                        document.official_form_url
                    ),
                }
            )
            for document in step.document_requirements
        ]
        updated_submission = step.submission.model_copy(
            update={
                "portal_url": replace_source_url(step.submission.portal_url),
            }
        )
        updated_steps.append(
            step.model_copy(
                update={
                    "scope": scope,
                    "source_urls": replace_source_urls(step.source_urls),
                    "deadline_source_url": replace_source_url(
                        step.deadline_source_url
                    ),
                    "official_form_urls": replace_source_urls(
                        step.official_form_urls
                    ),
                    "document_requirements": updated_documents,
                    "submission": updated_submission,
                    "action_url": replace_source_url(step.action_url),
                }
            )
        )

    application_round = (
        payload.application_round
        if payload.application_round is not None
        else revision.workflow.application_round
    )
    effective_rounds = list(revision.workflow.effective_application_rounds)
    if application_round and application_round not in effective_rounds:
        effective_rounds.insert(0, application_round)
    updated_sources_by_key = {
        canonical_source_url_identity(source.source_url): source
        for source in updated_sources
    }
    updated_review_source_keys = {
        canonical_source_url_identity(
            replace_source_url(source_url) or source_url
        )
        for source_url in workflow_review_source_urls(revision.workflow)
    }
    missing_source_metadata_count = sum(
        source_key not in updated_sources_by_key
        for source_key in updated_review_source_keys
    )
    missing_source_year_count = sum(
        source_key in updated_sources_by_key
        and updated_sources_by_key[source_key].effective_academic_year
        != payload.academic_year
        for source_key in updated_review_source_keys
    )
    missing: list[str] = []
    if not effective_rounds:
        missing.append("申請梯次")
    if not updated_sources:
        missing.append("官方來源")
    if missing_source_metadata_count:
        missing.append(f"來源證據資料（{missing_source_metadata_count} 筆）")
    if missing_source_year_count:
        missing.append(f"來源適用學年度（{missing_source_year_count} 筆）")
    applicability_status = (
        ApplicationApplicabilityStatus.NEEDS_CONFIRMATION
        if missing
        else ApplicationApplicabilityStatus.VERIFIED
    )
    applicability_note = (
        f"{'、'.join(missing)}尚未完成官方確認；不能把學生選擇的年度或梯次套用到這份流程。"
        if missing
        else (
            f"官方來源適用 {payload.academic_year} 學年度，梯次為"
            f"{'、'.join(effective_rounds)}；仍應在送件前核對當期公告。"
        )
    )
    updated_workflow = revision.workflow.model_copy(
        update={
            "academic_year": payload.academic_year,
            "application_round": application_round,
            "effective_application_rounds": effective_rounds,
            "applicability_status": applicability_status,
            "applicability_note": applicability_note,
            "partner_website": replace_source_url(
                revision.workflow.partner_website
            ),
            "steps": updated_steps,
            "sources": updated_sources,
            "last_checked": now,
        }
    )
    # Persist and review the exact normalized payload that publication stores.
    # In particular, newly registered sources receive their deterministic
    # priority before the content hash and human approvals are recorded.
    updated_workflow = structure_application_workflow(updated_workflow).model_copy(
        update={
            "applicability_status": applicability_status,
            "applicability_note": applicability_note,
        }
    )
    updated_hash = workflow_content_hash(updated_workflow)
    if updated_hash == revision.content_hash:
        raise ValueError("沒有可儲存的適用年度、梯次或來源變更。")

    baseline = base_workflow_for_revision(revisions, revision)
    edit = ApplicationWorkflowRevisionEdit(
        edited_by=normalized_editor,
        note=payload.note,
        previous_content_hash=revision.content_hash,
        content_hash=updated_hash,
        invalidated_review_approvals=revision.review_approvals,
    )
    change_summary = summarize_workflow_changes(baseline, updated_workflow)
    change_summary.append(
        f"{normalized_editor} 已更新候選適用範圍；修正說明：{payload.note}"
    )
    updated_revision = revision.model_copy(
        update={
            "content_hash": updated_hash,
            "change_summary": change_summary,
            "workflow": updated_workflow,
            "review_approvals": [],
            "edit_history": [*revision.edit_history, edit],
        }
    )
    return store.save_revision(updated_revision)


def workflow_review_source_urls(
    workflow: UniversityApplicationWorkflow,
) -> list[str]:
    """Return the exact, de-duplicated source set each reviewer must attest."""

    urls: list[str] = []
    seen: set[str] = set()

    def add(source_url: str | None) -> None:
        normalized = (source_url or "").strip()
        key = canonical_source_url_identity(normalized)
        if not normalized or key in seen:
            return
        seen.add(key)
        urls.append(normalized)

    for source in workflow.sources:
        add(source.source_url)
    for step in workflow.steps:
        for source_url in step.source_urls:
            add(source_url)
        add(step.deadline_source_url)
        for source_url in step.official_form_urls:
            add(source_url)
        for document in step.document_requirements:
            for source_url in document.source_urls:
                add(source_url)
            add(document.official_form_url)
    return urls


def workflow_review_source_metadata(
    workflow: UniversityApplicationWorkflow,
) -> dict[str, ApplicationWorkflowSource | None]:
    """Map every review URL to the evidence metadata stored for that URL."""

    metadata_by_url = {
        canonical_source_url_identity(source.source_url): source
        for source in workflow.sources
    }
    return {
        source_url: metadata_by_url.get(
            canonical_source_url_identity(source_url)
        )
        for source_url in workflow_review_source_urls(workflow)
    }


def workflow_review_metadata_issues(
    workflow: UniversityApplicationWorkflow,
    *,
    require_review_timestamps: bool = True,
) -> list[str]:
    """Return fail-closed applicability and review-timestamp gaps."""

    issues: list[str] = []
    academic_year = (workflow.academic_year or "").strip()
    effective_rounds = {
        value.strip()
        for value in [
            workflow.application_round,
            *workflow.effective_application_rounds,
        ]
        if value and value.strip()
    }
    if not academic_year:
        issues.append("流程適用學年度尚未完成官方確認")
    if not effective_rounds:
        issues.append("流程有效梯次尚未完成官方確認")
    if workflow.applicability_status != ApplicationApplicabilityStatus.VERIFIED:
        issues.append("流程適用狀態仍為待確認")

    source_metadata = workflow_review_source_metadata(workflow)
    missing_source_metadata_count = sum(
        source is None
        or not source.title.strip()
        or source.authority is None
        for source in source_metadata.values()
    )
    if missing_source_metadata_count:
        issues.append(
            f"{missing_source_metadata_count} 個官方來源尚未建立來源證據資料"
        )
    source_year_gap_count = sum(
        source is not None
        and (
            not (source.effective_academic_year or "").strip()
            or bool(academic_year)
            and source.effective_academic_year.strip() != academic_year
        )
        for source in source_metadata.values()
    )
    if source_year_gap_count:
        issues.append(
            f"{source_year_gap_count} 個官方來源的適用學年度缺漏或與流程不一致"
        )
    if require_review_timestamps:
        source_check_gap_count = sum(
            source is not None and source.checked_at is None
            for source in source_metadata.values()
        )
        if source_check_gap_count:
            issues.append(f"{source_check_gap_count} 個官方來源缺少最後查核日期")
        if workflow.last_checked is None:
            issues.append("流程缺少最後查核日期")
        step_check_gap_count = sum(step.checked_at is None for step in workflow.steps)
        if step_check_gap_count:
            issues.append(f"{step_check_gap_count} 個流程步驟缺少最後查核日期")
    return issues


def workflow_review_rule_source_urls(
    workflow: UniversityApplicationWorkflow,
) -> dict[str, list[str]]:
    """Map every critical rule to the official evidence shown to reviewers."""

    def unique_urls(values: list[str | None]) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = (value or "").strip()
            key = canonical_source_url_identity(normalized)
            if not normalized or key in seen:
                continue
            seen.add(key)
            urls.append(normalized)
        return urls

    rule_sources = {
        "workflow:applicability": unique_urls(
            [source.source_url for source in workflow.sources]
        )
    }
    for step_index, step in enumerate(workflow.steps):
        rule_sources[f"step:{step_index}"] = unique_urls(
            [*step.source_urls, step.deadline_source_url, *step.official_form_urls]
        )
        for document_index, document in enumerate(step.document_requirements):
            rule_sources[f"document:{step_index}:{document_index}"] = unique_urls(
                [*document.source_urls, document.official_form_url]
            )
    return rule_sources


def workflow_review_rule_labels(
    workflow: UniversityApplicationWorkflow,
) -> dict[str, str]:
    """Return stable, human-readable labels for every review rule key."""

    labels = {"workflow:applicability": "流程適用學年度、梯次與適用狀態"}
    for step_index, step in enumerate(workflow.steps):
        labels[f"step:{step_index}"] = (
            f"第 {step.order} 步｜{step.phase}｜{step.title}"
        )
        for document_index, document in enumerate(step.document_requirements):
            labels[f"document:{step_index}:{document_index}"] = (
                f"第 {step.order} 步文件｜{document.name}"
            )
    return labels


def workflow_source_reference_contexts(
    workflow: UniversityApplicationWorkflow,
    source_url: str,
) -> list[str]:
    """Explain each exact field where a source URL is used in one workflow."""

    source_key = canonical_source_url_identity(source_url)
    contexts: list[str] = []

    def add(label: str, candidate_url: str | None) -> None:
        if canonical_source_url_identity(candidate_url or "") != source_key:
            return
        if label not in contexts:
            contexts.append(label)

    for source in workflow.sources:
        add("流程適用範圍來源清單", source.source_url)
    for step in workflow.steps:
        step_label = f"第 {step.order} 步「{step.title}」"
        for candidate_url in step.source_urls:
            add(f"{step_label}的內容與要求", candidate_url)
        add(f"{step_label}的期限", step.deadline_source_url)
        for candidate_url in step.official_form_urls:
            add(f"{step_label}的官方表單", candidate_url)
        for document in step.document_requirements:
            document_label = f"{step_label}的文件「{document.name}」"
            for candidate_url in document.source_urls:
                add(f"{document_label}規定", candidate_url)
            add(f"{document_label}官方表單", document.official_form_url)
    return contexts


def list_source_evidence_gap_review_rows(
    store: ContentGovernanceStore,
    source_url: str,
) -> list[ApplicationWorkflowSourceEvidenceReviewRow]:
    """Build a read-only review checklist for one exact missing-evidence URL."""

    normalized_source_url = source_url.strip()
    if not normalized_source_url:
        return []
    source_key = canonical_source_url_identity(normalized_source_url)
    backlog = list_workflow_review_backlog(store)
    source_gap_group = next(
        (
            group
            for group in backlog.source_metadata_gap_groups
            if canonical_source_url_identity(group.source_url) == source_key
        ),
        None,
    )
    if source_gap_group is None:
        return []
    source_evidence_snapshot_fingerprint = (
        source_gap_group.source_evidence_snapshot_fingerprint
    )
    backlog_by_key = {item.workflow_key: item for item in backlog.items}
    revisions_by_id = {revision.id: revision for revision in store.list_revisions()}
    rows: list[ApplicationWorkflowSourceEvidenceReviewRow] = []
    for workflow in store.load_published_workflows():
        workflow_key = workflow_storage_key(workflow)
        backlog_item = backlog_by_key.get(workflow_key)
        if backlog_item is None:
            continue
        if backlog_item.pending_revision_id is not None:
            pending = revisions_by_id.get(backlog_item.pending_revision_id)
            if pending is None:
                raise RuntimeError(
                    "待審版本已在產生來源證據清單期間變更，請重新整理。"
                )
            if workflow_storage_key(pending.workflow) != workflow_key:
                raise RuntimeError(
                    "待審版本的穩定流程身分與公開版不一致，不能產生來源證據清單。"
                )
            workflow = pending.workflow
        source_metadata = workflow_review_source_metadata(workflow)
        matched_source_url = next(
            (
                candidate_url
                for candidate_url in source_metadata
                if canonical_source_url_identity(candidate_url) == source_key
            ),
            None,
        )
        if matched_source_url is None:
            continue
        source = source_metadata[matched_source_url]
        if (
            source is not None
            and source.title.strip()
            and source.authority is not None
        ):
            continue
        rule_sources = workflow_review_rule_source_urls(workflow)
        referenced_rule_keys = [
            rule_key
            for rule_key, rule_source_urls in rule_sources.items()
            if source_key
            in {
                canonical_source_url_identity(url)
                for url in rule_source_urls
            }
        ]
        rule_labels = workflow_review_rule_labels(workflow)
        application_rounds = list(
            dict.fromkeys(
                value.strip()
                for value in [
                    workflow.application_round,
                    *workflow.effective_application_rounds,
                ]
                if value and value.strip()
            )
        )
        rows.append(
            ApplicationWorkflowSourceEvidenceReviewRow(
                source_url=matched_source_url,
                source_evidence_snapshot_fingerprint=(
                    source_evidence_snapshot_fingerprint
                ),
                home_university=workflow.home_university,
                school_name=workflow.school_name,
                workflow_key=workflow_key,
                workflow_version=workflow.version,
                academic_year=workflow.academic_year,
                application_rounds=application_rounds,
                referenced_rule_keys=referenced_rule_keys,
                referenced_rule_labels=[
                    rule_labels[rule_key] for rule_key in referenced_rule_keys
                ],
                reference_contexts=workflow_source_reference_contexts(
                    workflow, matched_source_url
                ),
                has_pending_revision=backlog_item.has_pending_revision,
                pending_revision_id=backlog_item.pending_revision_id,
                current_source_title=source.title if source is not None else None,
                current_source_role=source.role if source is not None else None,
                current_source_authority=(
                    source.authority if source is not None else None
                ),
                current_effective_academic_year=(
                    source.effective_academic_year if source is not None else None
                ),
                current_application_round=(
                    source.application_round if source is not None else None
                ),
                current_checked_at=(
                    source.checked_at if source is not None else None
                ),
                research_candidate=source_gap_group.research_candidate,
            )
        )
    rows = sorted(
        rows,
        key=lambda row: (
            row.home_university.casefold(),
            row.school_name.casefold(),
            row.workflow_key,
        ),
    )
    if sorted({row.workflow_key for row in rows}) != sorted(
        source_gap_group.workflow_keys
    ):
        raise RuntimeError(
            "待查核內容在產生來源證據清單時已變更，請重新下載。"
        )
    backlog_after = list_workflow_review_backlog(store)
    source_gap_group_after = next(
        (
            group
            for group in backlog_after.source_metadata_gap_groups
            if canonical_source_url_identity(group.source_url) == source_key
        ),
        None,
    )
    if (
        source_gap_group_after is None
        or source_gap_group_after.source_evidence_snapshot_fingerprint
        != source_evidence_snapshot_fingerprint
    ):
        raise RuntimeError(
            "待查核內容在產生來源證據清單時已變更，請重新下載。"
        )
    return rows


def workflow_review_rule_keys(
    workflow: UniversityApplicationWorkflow,
) -> list[str]:
    """Return every critical workflow, step, and document rule to attest."""

    keys = ["workflow:applicability"]
    for step_index, step in enumerate(workflow.steps):
        keys.append(f"step:{step_index}")
        for document_index, _document in enumerate(step.document_requirements):
            keys.append(f"document:{step_index}:{document_index}")
    return keys


@atomic_workflow_command
def approve_workflow_revision(
    store: ContentGovernanceStore,
    revision_id: str,
    *,
    reviewer_id: str,
    note: str,
    expected_content_hash: str,
    reviewed_source_urls: list[str],
    reviewed_rule_keys: list[str],
) -> ApplicationWorkflowRevision:
    revision = _revision_for_review(store.list_revisions(), revision_id)
    normalized_reviewer = reviewer_id.strip()
    if not normalized_reviewer:
        raise ValueError("審查者識別不可為空白。")
    if revision.content_hash != expected_content_hash:
        raise ValueError("待審版本已變更，請重新載入來源與版本對照後再核准。")
    expected_source_urls = workflow_review_source_urls(revision.workflow)
    if not expected_source_urls:
        raise ValueError("候選版本沒有可逐頁查核的官方來源，不能核准。")
    missing_rule_source_keys = [
        key
        for key, source_urls in workflow_review_rule_source_urls(
            revision.workflow
        ).items()
        if not source_urls
    ]
    if missing_rule_source_keys:
        raise ValueError(
            f"還有 {len(missing_rule_source_keys)} 個關鍵規定沒有對應官方來源，不能核准。"
        )
    invalid_source_urls = [
        url for url in expected_source_urls if not url.casefold().startswith("https://")
    ]
    if invalid_source_urls:
        raise ValueError("候選版本含有非 HTTPS 官方來源，請先修正後再核准。")
    metadata_issues = workflow_review_metadata_issues(
        revision.workflow,
        require_review_timestamps=False,
    )
    if metadata_issues:
        raise ValueError(
            "候選版本的適用範圍與查核證據尚未完整："
            + "；".join(metadata_issues)
            + "，不能核准。"
        )
    reviewed_by_key = {
        canonical_source_url_identity(url): url.strip()
        for url in reviewed_source_urls
    }
    expected_by_key = {
        canonical_source_url_identity(url): url
        for url in expected_source_urls
    }
    if set(reviewed_by_key) - set(expected_by_key):
        raise ValueError("核准清單包含不屬於這個候選版本的官方來源。")
    missing_source_urls = set(expected_by_key) - set(reviewed_by_key)
    if missing_source_urls:
        raise ValueError(
            f"還有 {len(missing_source_urls)} 個官方來源未逐頁確認，不能核准。"
        )
    expected_rule_keys = workflow_review_rule_keys(revision.workflow)
    reviewed_rule_key_set = {key.strip() for key in reviewed_rule_keys}
    unknown_rule_keys = reviewed_rule_key_set - set(expected_rule_keys)
    if unknown_rule_keys:
        raise ValueError("核准清單包含不屬於這個候選版本的關鍵規定。")
    missing_rule_keys = set(expected_rule_keys) - reviewed_rule_key_set
    if missing_rule_keys:
        raise ValueError(
            f"還有 {len(missing_rule_keys)} 個關鍵規定未逐項確認，不能核准。"
        )
    if any(
        row.reviewer_id.casefold() == normalized_reviewer.casefold()
        for row in revision.review_approvals
    ):
        raise ValueError("同一位審查者不能重複核准同一版本。")
    if len(revision.review_approvals) >= revision.required_review_count:
        raise ValueError("這個版本已取得所需核准，請執行正式發布。")
    reviewed_at = utc_now()
    approval = ApplicationWorkflowReviewApproval(
        reviewer_id=normalized_reviewer,
        note=note,
        reviewed_at=reviewed_at,
        reviewed_content_hash=revision.content_hash,
        reviewed_source_urls=expected_source_urls,
        reviewed_rule_keys=expected_rule_keys,
    )
    reviewed_workflow = revision.workflow.model_copy(
        update={
            "last_checked": reviewed_at,
            "sources": [
                source.model_copy(update={"checked_at": reviewed_at})
                for source in revision.workflow.sources
            ],
            "steps": [
                step.model_copy(update={"checked_at": reviewed_at})
                for step in revision.workflow.steps
            ],
        }
    )
    approved = revision.model_copy(
        update={
            "workflow": reviewed_workflow,
            "review_approvals": [*revision.review_approvals, approval],
        }
    )
    return store.save_revision(approved)


@atomic_workflow_command
def publish_workflow_revision(
    store: ContentGovernanceStore,
    revision_id: str,
    *,
    reviewer_id: str,
    note: str | None = None,
) -> UniversityApplicationWorkflow:
    revisions = store.list_revisions()
    previous = next((row for row in revisions if row.id == revision_id), None)
    if previous is not None and previous.status == ApplicationWorkflowReviewStatus.PUBLISHED:
        public = next((row for row in store.load_published_workflows()
            if workflow_storage_key(row) == previous.workflow_key), None)
        if (not _revision_has_complete_publication_evidence(previous)
            or application_workflow_publication_integrity_issues(previous.workflow_key, revisions, public)
            or previous.review_note != note
            or (previous.reviewed_by or "").casefold() != reviewer_id.strip().casefold()
            or reviewer_id.strip().casefold() not in {row.reviewer_id.casefold() for row in previous.review_approvals}):
            raise ValueError("目前發布版本與重試請求或完整雙審證據不一致，請重新載入。")
        return previous.workflow
    revision = _revision_for_review(revisions, revision_id)
    approval_count = len(revision.review_approvals)
    if approval_count < revision.required_review_count:
        remaining = revision.required_review_count - approval_count
        raise ValueError(
            f"尚需 {remaining} 位不同內容管理者獨立核准，才能正式發布。"
        )
    expected_source_keys = {
        canonical_source_url_identity(url)
        for url in workflow_review_source_urls(revision.workflow)
    }
    expected_rule_keys = set(workflow_review_rule_keys(revision.workflow))
    if not expected_source_keys:
        raise ValueError("候選版本沒有可逐頁查核的官方來源，不能正式發布。")
    missing_rule_source_keys = [
        key
        for key, source_urls in workflow_review_rule_source_urls(
            revision.workflow
        ).items()
        if not source_urls
    ]
    if missing_rule_source_keys:
        raise ValueError(
            f"還有 {len(missing_rule_source_keys)} 個關鍵規定沒有對應官方來源，不能正式發布。"
        )
    if any(not key.startswith("https://") for key in expected_source_keys):
        raise ValueError("候選版本含有非 HTTPS 官方來源，請先修正後再正式發布。")
    metadata_issues = workflow_review_metadata_issues(revision.workflow)
    if metadata_issues:
        raise ValueError(
            "候選版本的適用範圍與查核證據尚未完整："
            + "；".join(metadata_issues)
            + "，不能正式發布。"
        )
    incomplete_approvals = [
        approval
        for approval in revision.review_approvals
        if approval.reviewed_content_hash != revision.content_hash
        or {
            canonical_source_url_identity(url)
            for url in approval.reviewed_source_urls
        }
        != expected_source_keys
        or set(approval.reviewed_rule_keys) != expected_rule_keys
    ]
    if incomplete_approvals:
        raise ValueError("核准紀錄未完整綁定目前版本、全部官方來源與關鍵規定，請兩位管理者重新核准。")
    if not any(
        approval.reviewer_id.casefold() == reviewer_id.strip().casefold()
        for approval in revision.review_approvals
    ):
        raise ValueError("只有已完成獨立核准的審查者可以執行正式發布。")
    now = utc_now()
    published = revision.workflow.model_copy(
        update={
            "governance_key": revision.workflow_key,
            "version": revision.version,
            "review_status": ApplicationWorkflowReviewStatus.PUBLISHED,
            "published_at": now,
            "applied_context": None,
        }
    )
    for existing in revisions:
        if (
            existing.workflow_key == revision.workflow_key
            and existing.status == ApplicationWorkflowReviewStatus.PUBLISHED
        ):
            store.save_revision(
                existing.model_copy(
                    update={"status": ApplicationWorkflowReviewStatus.SUPERSEDED}
                )
            )
    reviewed = revision.model_copy(
        update={
            "status": ApplicationWorkflowReviewStatus.PUBLISHED,
            "workflow": published,
            "reviewed_by": reviewer_id,
            "reviewed_at": now,
            "review_note": note,
        }
    )
    store.save_revision(reviewed)
    store.publish_workflow(
        published,
        revision.id,
        workflow_key=revision.workflow_key,
    )
    return published


def _revision_has_complete_publication_evidence(
    revision: ApplicationWorkflowRevision,
) -> bool:
    if (
        revision.workflow.review_status
        != ApplicationWorkflowReviewStatus.PUBLISHED
        or revision.workflow.published_at is None
        or revision.reviewed_at is None
        or not (revision.reviewed_by or "").strip()
    ):
        return False
    expected_sources = {
        canonical_source_url_identity(url)
        for url in workflow_review_source_urls(revision.workflow)
    }
    expected_rules = set(workflow_review_rule_keys(revision.workflow))
    if not expected_sources or any(
        not url.startswith("https://") for url in expected_sources
    ):
        return False
    if any(
        not sources
        for sources in workflow_review_rule_source_urls(
            revision.workflow
        ).values()
    ):
        return False
    reviewer_ids = {
        approval.reviewer_id.casefold()
        for approval in revision.review_approvals
    }
    if (
        len(revision.review_approvals) < revision.required_review_count
        or len(reviewer_ids) < revision.required_review_count
    ):
        return False
    return all(
        approval.reviewed_content_hash == revision.content_hash
        and {
            canonical_source_url_identity(url)
            for url in approval.reviewed_source_urls
        }
        == expected_sources
        and set(approval.reviewed_rule_keys) == expected_rules
        for approval in revision.review_approvals
    )


def _publication_revision_summary(
    revision: ApplicationWorkflowRevision,
    *,
    is_current: bool,
) -> ApplicationWorkflowPublicationRevisionSummary:
    published_at = revision.workflow.published_at or revision.reviewed_at
    if published_at is None:
        raise ValueError("申請流程發布版本缺少可追溯的發布時間。")
    return ApplicationWorkflowPublicationRevisionSummary(
        revision_id=revision.id,
        version=revision.version,
        content_hash=revision.content_hash,
        status=revision.status,
        publication_action=revision.publication_action,
        published_at=published_at,
        published_by=(revision.reviewed_by or revision.detected_by),
        note=revision.review_note,
        rolled_back_from_revision_id=revision.rolled_back_from_revision_id,
        restored_revision_id=revision.restored_revision_id,
        source_count=len(revision.workflow.sources),
        step_count=len(revision.workflow.steps),
        is_current=is_current,
    )


def application_workflow_publication_integrity_issues(
    workflow_key: str,
    revisions: list[ApplicationWorkflowRevision],
    public_workflow: UniversityApplicationWorkflow | None,
) -> list[str]:
    """Return fail-closed integrity issues for one workflow's publication chain."""

    workflow_revisions = [
        revision
        for revision in revisions
        if revision.workflow_key == workflow_key
    ]
    current_rows = [
        revision
        for revision in workflow_revisions
        if revision.status == ApplicationWorkflowReviewStatus.PUBLISHED
    ]
    rollback_rows = [
        revision
        for revision in workflow_revisions
        if revision.publication_action
        == ApplicationWorkflowPublicationAction.ROLLBACK
    ]
    public_is_published = (
        public_workflow is not None
        and public_workflow.review_status
        == ApplicationWorkflowReviewStatus.PUBLISHED
        and public_workflow.published_at is not None
    )
    issues: list[str] = []

    if len(current_rows) > 1:
        issues.append("同一流程存在多個目前發布版本")
    elif not current_rows:
        if public_is_published or rollback_rows:
            issues.append("公開資料或復原歷程找不到唯一的目前發布版本")
    else:
        current = current_rows[0]
        if not public_is_published:
            issues.append("目前發布版本找不到對應的學生公開資料")
        elif public_workflow is not None and (
            public_workflow.version != current.version
            or workflow_content_hash(public_workflow)
            != workflow_content_hash(
                structure_application_workflow(current.workflow)
            )
        ):
            issues.append("目前發布版本與學生公開資料的版號或內容指紋不一致")

    publication_rows = [
        revision
        for revision in workflow_revisions
        if revision.status
        in {
            ApplicationWorkflowReviewStatus.PUBLISHED,
            ApplicationWorkflowReviewStatus.SUPERSEDED,
        }
        and revision.workflow.review_status
        == ApplicationWorkflowReviewStatus.PUBLISHED
        and revision.workflow.published_at is not None
    ]
    for revision in publication_rows:
        if (
            workflow_content_hash(revision.workflow)
            != revision.content_hash
        ):
            issues.append(f"發布版本 {revision.id} 的內容指紋與快照不一致")

    by_id = {revision.id: revision for revision in workflow_revisions}
    seen_rollback_pairs: set[tuple[str, str]] = set()
    for revision in rollback_rows:
        rollback_pair = (
            revision.rolled_back_from_revision_id or "",
            revision.restored_revision_id or "",
        )
        if rollback_pair in seen_rollback_pairs:
            issues.append(
                f"復原版本 {revision.id} 重複記錄相同撤回與恢復事件"
            )
        seen_rollback_pairs.add(rollback_pair)
        rolled_back_from = by_id.get(
            revision.rolled_back_from_revision_id or ""
        )
        restored = by_id.get(revision.restored_revision_id or "")
        if (
            revision.status
            not in {
                ApplicationWorkflowReviewStatus.PUBLISHED,
                ApplicationWorkflowReviewStatus.SUPERSEDED,
            }
            or revision.workflow.review_status
            != ApplicationWorkflowReviewStatus.PUBLISHED
            or revision.workflow.published_at is None
        ):
            issues.append(f"復原版本 {revision.id} 不是可追溯的發布版本")
            continue
        if rolled_back_from is None or restored is None:
            issues.append(f"復原版本 {revision.id} 參照不存在的歷史版本")
            continue
        if (
            revision.base_version != rolled_back_from.version
            or revision.workflow.supersedes_version
            != rolled_back_from.version
            or revision.version <= rolled_back_from.version
            or revision.version <= restored.version
        ):
            issues.append(f"復原版本 {revision.id} 的版本鏈不一致")
        if (
            revision.content_hash != restored.content_hash
            or revision.required_review_count != restored.required_review_count
            or revision.review_approvals != restored.review_approvals
            or not _revision_has_complete_publication_evidence(restored)
        ):
            issues.append(f"復原版本 {revision.id} 未精確保留恢復目標的雙審快照")

    return list(dict.fromkeys(issues))


def build_application_workflow_publication_history(
    store: ContentGovernanceStore,
    *,
    home_university: str | None = None,
) -> ApplicationWorkflowPublicationHistory:
    revisions = store.list_revisions()
    public_by_key = {
        workflow_storage_key(workflow): workflow
        for workflow in store.load_published_workflows()
    }
    grouped: dict[str, list[ApplicationWorkflowRevision]] = {}
    for revision in revisions:
        grouped.setdefault(revision.workflow_key, []).append(revision)
    items: list[ApplicationWorkflowPublicationState] = []
    for workflow_key, workflow_revisions in grouped.items():
        current_rows = [
            revision
            for revision in workflow_revisions
            if revision.status == ApplicationWorkflowReviewStatus.PUBLISHED
        ]
        if not current_rows:
            continue
        if len(current_rows) != 1:
            raise ValueError("同一申請流程存在多個目前發布版本，已停止提供復原操作。")
        current = current_rows[0]
        if (
            home_university is not None
            and current.workflow.home_university != home_university
        ):
            continue
        if not _revision_has_complete_publication_evidence(current):
            raise ValueError("目前申請流程發布版本缺少完整雙審證據。")
        public_workflow = public_by_key.get(workflow_key)
        integrity_issues = application_workflow_publication_integrity_issues(
            workflow_key,
            workflow_revisions,
            public_workflow,
        )
        if integrity_issues:
            raise ValueError(
                "申請流程發布與復原稽核鏈不完整："
                f"{integrity_issues[0]}。"
            )
        publication_revisions = [
            revision
            for revision in workflow_revisions
            if revision.status
            in {
                ApplicationWorkflowReviewStatus.PUBLISHED,
                ApplicationWorkflowReviewStatus.SUPERSEDED,
            }
            and revision.workflow.review_status
            == ApplicationWorkflowReviewStatus.PUBLISHED
            and revision.workflow.published_at is not None
        ]
        pending = max(
            (
                revision
                for revision in workflow_revisions
                if revision.status
                == ApplicationWorkflowReviewStatus.PENDING_REVIEW
            ),
            key=lambda revision: (revision.detected_at, revision.id),
            default=None,
        )
        targets = [
            revision
            for revision in publication_revisions
            if revision.id != current.id
            and revision.status == ApplicationWorkflowReviewStatus.SUPERSEDED
            and revision.content_hash != current.content_hash
            and _revision_has_complete_publication_evidence(revision)
        ]
        targets.sort(key=lambda revision: (revision.version, revision.id), reverse=True)
        if pending is not None:
            block_reason = "這筆流程仍有待審版本；請先發布或退回後再復原。"
        elif not targets:
            block_reason = "目前沒有內容不同且曾通過完整雙審的舊發布版本。"
        else:
            block_reason = None
        history = sorted(
            publication_revisions,
            key=lambda revision: (revision.version, revision.id),
            reverse=True,
        )
        items.append(
            ApplicationWorkflowPublicationState(
                workflow_key=workflow_key,
                home_university=current.workflow.home_university,
                school_name=current.workflow.school_name,
                program_type=current.workflow.program_type,
                current_revision_id=current.id,
                current_version=current.version,
                current_content_hash=current.content_hash,
                current_published_at=current.workflow.published_at,
                current_publication_action=current.publication_action,
                pending_revision_id=pending.id if pending else None,
                can_rollback=bool(targets) and pending is None,
                rollback_block_reason=block_reason,
                rollback_targets=[
                    _publication_revision_summary(target, is_current=False)
                    for target in targets
                ],
                publication_history=[
                    _publication_revision_summary(
                        revision,
                        is_current=revision.id == current.id,
                    )
                    for revision in history
                ],
            )
        )
    return ApplicationWorkflowPublicationHistory(
        home_university=home_university,
        workflow_count=len(items),
        rollback_ready_count=sum(item.can_rollback for item in items),
        publication_revision_count=sum(
            len(item.publication_history) for item in items
        ),
        rollback_revision_count=sum(
            summary.publication_action
            == ApplicationWorkflowPublicationAction.ROLLBACK
            for item in items
            for summary in item.publication_history
        ),
        items=sorted(
            items,
            key=lambda item: (
                item.home_university.casefold(),
                item.school_name.casefold(),
                item.workflow_key,
            ),
        ),
    )


@atomic_workflow_command
def rollback_published_workflow(
    store: ContentGovernanceStore,
    request: ApplicationWorkflowRollbackRequest,
    *,
    rolled_back_by: str,
) -> ApplicationWorkflowRevision:
    revisions = store.list_revisions()
    matching_retry = next(
        (
            revision
            for revision in revisions
            if revision.workflow_key == request.workflow_key
            and revision.publication_action
            == ApplicationWorkflowPublicationAction.ROLLBACK
            and revision.rolled_back_from_revision_id
            == request.expected_current_revision_id
            and revision.restored_revision_id == request.restore_revision_id
        ),
        None,
    )
    if matching_retry is not None:
        rolled_back_from = next(
            (
                revision
                for revision in revisions
                if revision.id == request.expected_current_revision_id
            ),
            None,
        )
        if (
            rolled_back_from is None
            or rolled_back_from.version != request.expected_current_version
            or rolled_back_from.content_hash
            != request.expected_current_content_hash
        ):
            raise ValueError("申請流程復原請求與既有稽核事件不一致。")
        current_rows = [row for row in revisions if row.workflow_key == request.workflow_key
                        and row.status == ApplicationWorkflowReviewStatus.PUBLISHED]
        if len(current_rows) != 1 or current_rows[0].id != matching_retry.id:
            raise ValueError("此復原後已有其他公開版本；舊請求不能撤回後續發布。")
        for revision in revisions:
            if (
                revision.workflow_key == request.workflow_key
                and revision.status == ApplicationWorkflowReviewStatus.PUBLISHED
                and revision.id != matching_retry.id
            ):
                store.save_revision(
                    revision.model_copy(
                        update={
                            "status": ApplicationWorkflowReviewStatus.SUPERSEDED
                        }
                    )
                )
        if matching_retry.status != ApplicationWorkflowReviewStatus.PUBLISHED:
            matching_retry = matching_retry.model_copy(
                update={"status": ApplicationWorkflowReviewStatus.PUBLISHED}
            )
            store.save_revision(matching_retry)
        store.publish_workflow(
            matching_retry.workflow,
            matching_retry.id,
            workflow_key=matching_retry.workflow_key,
        )
        return matching_retry

    history = build_application_workflow_publication_history(store)
    state = next(
        (
            item
            for item in history.items
            if item.workflow_key == request.workflow_key
        ),
        None,
    )
    if state is None:
        raise LookupError("找不到具有完整雙審證據的目前申請流程發布版本。")
    if (
        state.current_revision_id != request.expected_current_revision_id
        or state.current_version != request.expected_current_version
        or state.current_content_hash != request.expected_current_content_hash
    ):
        raise ValueError("申請流程公開版本已變更；請重新載入後再復原。")
    if not state.can_rollback:
        raise ValueError(
            state.rollback_block_reason or "目前沒有可安全復原的申請流程版本。"
        )
    target_summary = next(
        (
            target
            for target in state.rollback_targets
            if target.revision_id == request.restore_revision_id
        ),
        None,
    )
    if target_summary is None:
        raise ValueError("指定版本不是目前可安全恢復的舊發布版本。")
    by_id = {revision.id: revision for revision in revisions}
    current = by_id[state.current_revision_id]
    target = by_id[target_summary.revision_id]
    now = utc_now()
    next_version = max(
        revision.version
        for revision in revisions
        if revision.workflow_key == request.workflow_key
    ) + 1
    restored_workflow = target.workflow.model_copy(
        update={
            "governance_key": request.workflow_key,
            "version": next_version,
            "review_status": ApplicationWorkflowReviewStatus.PUBLISHED,
            "published_at": now,
            "supersedes_version": current.version,
            "applied_context": None,
        }
    )
    restored_hash = workflow_content_hash(restored_workflow)
    if restored_hash != target.content_hash:
        raise ValueError("舊發布版本內容已無法精確重建，已停止復原。")
    rollback_revision = ApplicationWorkflowRevision(
        workflow_key=request.workflow_key,
        version=next_version,
        base_version=current.version,
        status=ApplicationWorkflowReviewStatus.PUBLISHED,
        content_hash=restored_hash,
        change_summary=[
            f"緊急復原：撤回版本 {current.version}，恢復曾完成雙審的版本 {target.version}。",
            "復原建立新版本並保留全部歷史；後續修改仍須重新雙審。",
        ],
        workflow=restored_workflow,
        detected_by=rolled_back_by,
        detected_at=now,
        required_review_count=target.required_review_count,
        review_approvals=target.review_approvals,
        edit_history=[],
        reviewed_by=rolled_back_by,
        reviewed_at=now,
        review_note=request.note,
        publication_action=ApplicationWorkflowPublicationAction.ROLLBACK,
        rolled_back_from_revision_id=current.id,
        restored_revision_id=target.id,
    )
    store.save_revision(rollback_revision)
    store.save_revision(
        current.model_copy(
            update={"status": ApplicationWorkflowReviewStatus.SUPERSEDED}
        )
    )
    store.publish_workflow(
        restored_workflow,
        rollback_revision.id,
        workflow_key=request.workflow_key,
    )
    return rollback_revision


@atomic_workflow_command
def reject_workflow_revision(
    store: ContentGovernanceStore,
    revision_id: str,
    *,
    reviewer_id: str,
    note: str | None = None,
) -> ApplicationWorkflowRevision:
    revision = _revision_for_review(store.list_revisions(), revision_id)
    rejected = revision.model_copy(
        update={
            "status": ApplicationWorkflowReviewStatus.REJECTED,
            "reviewed_by": reviewer_id,
            "reviewed_at": utc_now(),
            "review_note": note,
        }
    )
    return store.save_revision(rejected)


def workflow_content_hash(workflow: UniversityApplicationWorkflow) -> str:
    payload = workflow.model_dump(mode="json")
    for field in (
        "workflow_id",
        "governance_key",
        "issue_report_snapshot",
        "version",
        "review_status",
        "published_at",
        "supersedes_version",
        "applied_context",
        "last_checked",
    ):
        payload.pop(field, None)
    for step in payload.get("steps", []):
        step.pop("checked_at", None)
    for source in payload.get("sources", []):
        source.pop("checked_at", None)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def summarize_workflow_changes(
    current: UniversityApplicationWorkflow | None,
    candidate: UniversityApplicationWorkflow,
) -> list[str]:
    if current is None:
        return ["建立第一版申請流程，發布前需確認所有官方來源與適用梯次。"]

    summary: list[str] = []
    current_steps = {_step_identity(step): step for step in current.steps}
    candidate_steps = {_step_identity(step): step for step in candidate.steps}
    added = candidate_steps.keys() - current_steps.keys()
    removed = current_steps.keys() - candidate_steps.keys()
    changed = {
        key
        for key in current_steps.keys() & candidate_steps.keys()
        if _step_payload(current_steps[key]) != _step_payload(candidate_steps[key])
    }
    if added:
        summary.append(
            f"新增 {len(added)} 個步驟：{_step_titles(added, candidate_steps)}"
        )
    if removed:
        summary.append(
            f"移除 {len(removed)} 個步驟：{_step_titles(removed, current_steps)}"
        )
    if changed:
        summary.append(
            f"調整 {len(changed)} 個步驟：{_step_titles(changed, candidate_steps)}"
        )

    current_sources = {row.source_url for row in current.sources}
    candidate_sources = {row.source_url for row in candidate.sources}
    if candidate_sources - current_sources:
        summary.append(f"新增 {len(candidate_sources - current_sources)} 個官方來源。")
    if current_sources - candidate_sources:
        summary.append(f"移除 {len(current_sources - candidate_sources)} 個來源，需人工確認。")
    if not summary:
        summary.append("流程中繼資料或來源內容雜湊有變動，需人工確認。")
    return summary


def base_workflow_for_revision(
    revisions: list[ApplicationWorkflowRevision],
    revision: ApplicationWorkflowRevision,
) -> UniversityApplicationWorkflow | None:
    """Return the exact version that a reviewed revision superseded."""
    if revision.base_version is None:
        return None
    base = next(
        (
            row
            for row in revisions
            if row.workflow_key == revision.workflow_key
            and row.version == revision.base_version
            and row.status
            in {
                ApplicationWorkflowReviewStatus.PUBLISHED,
                ApplicationWorkflowReviewStatus.SUPERSEDED,
            }
        ),
        None,
    )
    return base.workflow if base is not None else None


def compare_workflow_revision(
    revisions: list[ApplicationWorkflowRevision],
    revision: ApplicationWorkflowRevision,
) -> ApplicationWorkflowComparison:
    """Build a review-safe, human-readable comparison against the exact base."""
    base = base_workflow_for_revision(revisions, revision)
    if base is None:
        return ApplicationWorkflowComparison(
            revision=revision,
            base_workflow=None,
            has_base=False,
            unchanged_step_count=0,
        )

    candidate = revision.workflow
    workflow_changes = _comparison_changes(
        base,
        candidate,
        _WORKFLOW_COMPARISON_FIELDS,
    )
    base_steps = {_step_identity(step): step for step in base.steps}
    candidate_steps = {_step_identity(step): step for step in candidate.steps}
    step_changes: list[ApplicationWorkflowStepChange] = []
    unchanged_step_count = 0
    for key in sorted(
        base_steps.keys() | candidate_steps.keys(),
        key=lambda value: _comparison_step_sort_key(
            value, base_steps, candidate_steps
        ),
    ):
        before = base_steps.get(key)
        after = candidate_steps.get(key)
        if before is not None and after is not None:
            if _step_payload(before) == _step_payload(after):
                unchanged_step_count += 1
                continue
            change_type = "changed"
        elif before is None:
            change_type = "added"
        else:
            change_type = "removed"
        changes = _comparison_changes(before, after, _STEP_COMPARISON_FIELDS)
        before_title = before.title if before is not None else None
        after_title = after.title if after is not None else None
        step_changes.append(
            ApplicationWorkflowStepChange(
                step_key=key,
                change_type=change_type,
                title=after_title or before_title or key,
                before_title=before_title,
                after_title=after_title,
                changes=changes,
            )
        )

    base_sources = {row.source_url: row for row in base.sources}
    candidate_sources = {row.source_url: row for row in candidate.sources}
    source_changes: list[ApplicationWorkflowSourceChange] = []
    for source_url in sorted(base_sources.keys() | candidate_sources.keys()):
        before = base_sources.get(source_url)
        after = candidate_sources.get(source_url)
        changes = _comparison_changes(before, after, _SOURCE_COMPARISON_FIELDS)
        if before is not None and after is not None and not changes:
            continue
        if before is None:
            change_type = "added"
        elif after is None:
            change_type = "removed"
        else:
            change_type = "changed"
        source_changes.append(
            ApplicationWorkflowSourceChange(
                source_url=source_url,
                change_type=change_type,
                title=(after.title if after is not None else before.title),
                changes=changes,
            )
        )

    return ApplicationWorkflowComparison(
        revision=revision,
        base_workflow=base,
        has_base=True,
        workflow_changes=workflow_changes,
        step_changes=step_changes,
        source_changes=source_changes,
        unchanged_step_count=unchanged_step_count,
    )


def affected_workflow_scopes(
    current: UniversityApplicationWorkflow,
    candidate: UniversityApplicationWorkflow,
) -> list[ApplicationRuleScope] | None:
    """Return changed rule scopes; ``None`` means the whole workflow changed."""
    current_steps = {_step_identity(step): step for step in current.steps}
    candidate_steps = {_step_identity(step): step for step in candidate.steps}
    changed_keys = (
        current_steps.keys() ^ candidate_steps.keys()
    ) | {
        key
        for key in current_steps.keys() & candidate_steps.keys()
        if _step_payload(current_steps[key]) != _step_payload(candidate_steps[key])
    }
    if not changed_keys:
        # Source or workflow metadata changes affect every plan for this workflow.
        return None

    scopes: list[ApplicationRuleScope] = []
    seen: set[str] = set()
    for key in sorted(changed_keys):
        for step in (current_steps.get(key), candidate_steps.get(key)):
            if step is None:
                continue
            scope = step.scope
            if not any(
                (
                    scope.home_universities,
                    scope.partner_universities,
                    scope.colleges,
                    scope.departments,
                    scope.academic_years,
                    scope.application_rounds,
                )
            ):
                return None
            fingerprint = json.dumps(
                scope.model_dump(mode="json"),
                ensure_ascii=False,
                sort_keys=True,
            )
            if fingerprint not in seen:
                seen.add(fingerprint)
                scopes.append(scope)
    return scopes or None


def _revision_for_review(
    revisions: list[ApplicationWorkflowRevision],
    revision_id: str,
) -> ApplicationWorkflowRevision:
    revision = next((row for row in revisions if row.id == revision_id), None)
    if revision is None:
        raise LookupError("找不到指定的申請流程版本。")
    if revision.status != ApplicationWorkflowReviewStatus.PENDING_REVIEW:
        raise ValueError("只有待審版本可以發布或退回。")
    return revision


def _step_identity(step) -> str:
    return step.rule_id or step.overrides_rule_id or f"{step.order}:{step.phase}:{step.title}"


def _step_payload(step) -> dict:
    payload = step.model_dump(mode="json")
    payload.pop("checked_at", None)
    return payload


def _step_titles(values, steps: dict) -> str:
    titles = [steps[value].title for value in values if value in steps]
    return "、".join(sorted(titles)[:5])


def _comparison_changes(
    before,
    after,
    fields: tuple[tuple[str, str], ...],
) -> list[ApplicationWorkflowValueChange]:
    before_payload = before.model_dump(mode="json") if before is not None else {}
    after_payload = after.model_dump(mode="json") if after is not None else {}
    changes: list[ApplicationWorkflowValueChange] = []
    for field, label in fields:
        before_value = before_payload.get(field)
        after_value = after_payload.get(field)
        if before_value == after_value:
            continue
        before_text = _format_comparison_value(field, before_value)
        after_text = _format_comparison_value(field, after_value)
        if before_text is None and after_text is not None:
            change_type = "added"
        elif before_text is not None and after_text is None:
            change_type = "removed"
        else:
            change_type = "changed"
        changes.append(
            ApplicationWorkflowValueChange(
                field=field,
                label=label,
                change_type=change_type,
                before=before_text,
                after=after_text,
            )
        )
    return changes


def _format_comparison_value(field: str, value) -> str | None:
    if value is None or value == "" or value == [] or value == {}:
        return None
    if isinstance(value, bool):
        return "是" if value else "否"
    if field == "document_requirements" and isinstance(value, list):
        return "\n".join(_format_document_requirement(row) for row in value)
    if field == "scope" and isinstance(value, dict):
        labels = {
            "home_universities": "本校",
            "partner_universities": "合作校",
            "colleges": "學院",
            "departments": "學系",
            "academic_years": "學年度",
            "application_rounds": "梯次",
        }
        parts = [
            f"{labels[key]}：{'、'.join(items)}"
            for key, items in value.items()
            if items and key in labels
        ]
        return "\n".join(parts) or "全部學生"
    if field == "submission" and isinstance(value, dict):
        labels = {
            "method": "方式",
            "office": "收件單位",
            "address": "地址",
            "receiving_hours": "收件時間",
            "email": "Email",
            "portal_url": "線上系統",
            "send_by_at": "最晚寄出",
            "arrival_deadline_at": "必須送達",
            "deadline_note": "期限說明",
        }
        parts = []
        for key, label in labels.items():
            item = value.get(key)
            if item is None or item == "":
                continue
            parts.append(f"{label}：{_format_scalar(item)}")
        return "\n".join(parts) or None
    if isinstance(value, list):
        return "\n".join(_format_scalar(item) for item in value) or None
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return _format_scalar(value)


def _format_document_requirement(row) -> str:
    if not isinstance(row, dict):
        return _format_scalar(row)
    parts = [str(row.get("name") or "未命名文件")]
    if row.get("copies"):
        parts.append(f"{row['copies']} 份")
    copy_type = row.get("copy_type")
    if copy_type and copy_type != "unspecified":
        parts.append(_COMPARISON_VALUE_LABELS.get(copy_type, str(copy_type)))
    if row.get("signatures"):
        parts.append(f"簽名：{'、'.join(row['signatures'])}")
    if row.get("stamps"):
        parts.append(f"核章：{'、'.join(row['stamps'])}")
    if row.get("official_form_url"):
        parts.append(f"表單：{row['official_form_url']}")
    if row.get("needs_confirmation"):
        parts.append("仍需確認")
    return "｜".join(parts)


def _format_scalar(value) -> str:
    text = str(value)
    if text in _COMPARISON_VALUE_LABELS:
        return _COMPARISON_VALUE_LABELS[text]
    if text == "True":
        return "是"
    if text == "False":
        return "否"
    return text


def _comparison_step_sort_key(
    key: str,
    base_steps: dict,
    candidate_steps: dict,
) -> tuple[int, str, str]:
    step = candidate_steps.get(key) or base_steps.get(key)
    return (step.order, step.title, key)


def _normal(value: str | None) -> str:
    return " ".join(str(value or "").strip().casefold().split())
