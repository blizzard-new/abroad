from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .content_governance import workflow_review_source_urls
from .models import (
    ApplicationWorkflowReviewBacklog,
    ApplicationWorkflowRevision,
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowSourceReplacementCandidate,
    ApplicationWorkflowSourceReplacementCandidateDefinition,
    ApplicationWorkflowSourceReplacementReviewRow,
    UniversityApplicationWorkflow,
)
from .workflow_identity import workflow_storage_key


SOURCE_REPLACEMENT_CANDIDATES_PATH = (
    Path(__file__).resolve().parent
    / "official_data"
    / "review"
    / "source_replacement_candidates.json"
)


class _SourceReplacementCandidateManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2]
    review_status: Literal["human_review_required"]
    publication_effect: Literal["none"]
    approvals_created: Literal[False]
    public_student_data_changed: Literal[False]
    expected_candidate_count: int = Field(ge=1)
    expected_verified_https_candidate_count: int = Field(ge=0)
    expected_transport_blocked_candidate_count: int = Field(ge=0)
    items: list[ApplicationWorkflowSourceReplacementCandidateDefinition] = Field(
        min_length=1
    )

    @model_validator(mode="after")
    def validate_manifest(self) -> "_SourceReplacementCandidateManifest":
        if len(self.items) != self.expected_candidate_count:
            raise ValueError("來源替換候選數量與 manifest 宣告不一致。")
        if (
            sum(item.transport_status == "verified_https" for item in self.items)
            != self.expected_verified_https_candidate_count
        ):
            raise ValueError("已驗證 HTTPS 候選數量與 manifest 宣告不一致。")
        if (
            sum(not item.can_prefill for item in self.items)
            != self.expected_transport_blocked_candidate_count
        ):
            raise ValueError("傳輸阻擋候選數量與 manifest 宣告不一致。")
        identities = [
            (item.workflow_id, item.current_url.casefold()) for item in self.items
        ]
        if len(identities) != len(set(identities)):
            raise ValueError("同一流程的同一原網址不可重複建立替換候選。")
        return self


@lru_cache(maxsize=1)
def load_source_replacement_candidate_definitions() -> tuple[
    ApplicationWorkflowSourceReplacementCandidateDefinition, ...
]:
    manifest = _SourceReplacementCandidateManifest.model_validate_json(
        SOURCE_REPLACEMENT_CANDIDATES_PATH.read_text(encoding="utf-8")
    )
    return tuple(manifest.items)


def list_source_replacement_candidates(
    revisions: list[ApplicationWorkflowRevision],
) -> list[ApplicationWorkflowSourceReplacementCandidate]:
    """Return only candidates that still match an unsaved pending revision source."""

    definitions_by_workflow: dict[
        str, list[ApplicationWorkflowSourceReplacementCandidateDefinition]
    ] = {}
    for definition in load_source_replacement_candidate_definitions():
        definitions_by_workflow.setdefault(definition.workflow_id, []).append(
            definition
        )

    results: list[ApplicationWorkflowSourceReplacementCandidate] = []
    for revision in revisions:
        if revision.status != ApplicationWorkflowReviewStatus.PENDING_REVIEW:
            continue
        definitions = definitions_by_workflow.get(revision.workflow.workflow_id, [])
        if not definitions:
            continue
        review_sources = {
            source_url.casefold(): source_url
            for source_url in workflow_review_source_urls(revision.workflow)
        }
        for definition in definitions:
            current_key = definition.current_url.casefold()
            if current_key not in review_sources:
                continue
            results.append(
                ApplicationWorkflowSourceReplacementCandidate(
                    **definition.model_dump(),
                    revision_id=revision.id,
                    workflow_key=revision.workflow_key,
                )
            )
    return sorted(
        results,
        key=lambda row: (
            row.revision_id.casefold(),
            row.current_url.casefold(),
            row.candidate_url.casefold(),
        ),
    )


def enrich_source_replacement_candidate_counts(
    backlog: ApplicationWorkflowReviewBacklog,
    published_workflows: list[UniversityApplicationWorkflow],
    revisions: list[ApplicationWorkflowRevision],
) -> ApplicationWorkflowReviewBacklog:
    """Add review-candidate counts without staging or mutating any workflow."""

    definitions_by_workflow: dict[
        str, list[ApplicationWorkflowSourceReplacementCandidateDefinition]
    ] = {}
    for definition in load_source_replacement_candidate_definitions():
        definitions_by_workflow.setdefault(definition.workflow_id, []).append(
            definition
        )
    pending_by_key: dict[str, ApplicationWorkflowRevision] = {}
    for revision in sorted(
        revisions,
        key=lambda row: row.detected_at,
        reverse=True,
    ):
        if (
            revision.status == ApplicationWorkflowReviewStatus.PENDING_REVIEW
            and revision.workflow_key not in pending_by_key
        ):
            pending_by_key[revision.workflow_key] = revision

    counts_by_key: dict[str, tuple[int, int, int, int]] = {}
    for published in published_workflows:
        key = workflow_storage_key(published)
        pending = pending_by_key.get(key)
        workflow = pending.workflow if pending is not None else published
        current_sources = {
            source_url.casefold()
            for source_url in workflow_review_source_urls(workflow)
        }
        applicable = [
            definition
            for definition in definitions_by_workflow.get(workflow.workflow_id, [])
            if definition.current_url.casefold() in current_sources
        ]
        if not applicable:
            continue
        strong_count = sum(
            definition.candidate_status == "strong_candidate"
            for definition in applicable
        )
        conditional_count = len(applicable) - strong_count
        transport_blocked_count = sum(
            not definition.can_prefill for definition in applicable
        )
        counts_by_key[key] = (
            len(applicable),
            strong_count,
            conditional_count,
            transport_blocked_count,
        )

    enriched_items = []
    for item in backlog.items:
        (
            total_count,
            strong_count,
            conditional_count,
            transport_blocked_count,
        ) = counts_by_key.get(
            item.workflow_key,
            (0, 0, 0, 0),
        )
        enriched_items.append(
            item.model_copy(
                update={
                    "source_replacement_candidate_count": total_count,
                    "strong_source_replacement_candidate_count": strong_count,
                    "conditional_source_replacement_candidate_count": (
                        conditional_count
                    ),
                    "transport_blocked_source_replacement_candidate_count": (
                        transport_blocked_count
                    ),
                }
            )
        )
    return backlog.model_copy(
        update={
            "items": enriched_items,
            "workflows_with_source_replacement_candidates": sum(
                item.source_replacement_candidate_count > 0
                for item in enriched_items
            ),
            "source_replacement_candidate_count": sum(
                item.source_replacement_candidate_count for item in enriched_items
            ),
            "transport_blocked_source_replacement_candidate_count": sum(
                item.transport_blocked_source_replacement_candidate_count
                for item in enriched_items
            ),
        }
    )


def list_source_replacement_candidate_review_rows(
    published_workflows: list[UniversityApplicationWorkflow],
    revisions: list[ApplicationWorkflowRevision],
    *,
    review_content_fingerprint: str,
) -> list[ApplicationWorkflowSourceReplacementReviewRow]:
    """Build a read-only pre-staging queue without changing review state."""

    definitions_by_workflow: dict[
        str, list[ApplicationWorkflowSourceReplacementCandidateDefinition]
    ] = {}
    for definition in load_source_replacement_candidate_definitions():
        definitions_by_workflow.setdefault(definition.workflow_id, []).append(
            definition
        )
    pending_by_key: dict[str, ApplicationWorkflowRevision] = {}
    for revision in sorted(
        revisions,
        key=lambda row: row.detected_at,
        reverse=True,
    ):
        if (
            revision.status == ApplicationWorkflowReviewStatus.PENDING_REVIEW
            and revision.workflow_key not in pending_by_key
        ):
            pending_by_key[revision.workflow_key] = revision

    rows: list[ApplicationWorkflowSourceReplacementReviewRow] = []
    for published in published_workflows:
        workflow_key = workflow_storage_key(published)
        pending = pending_by_key.get(workflow_key)
        workflow = pending.workflow if pending is not None else published
        current_sources = {
            source_url.casefold()
            for source_url in workflow_review_source_urls(workflow)
        }
        application_rounds = list(workflow.effective_application_rounds)
        if not application_rounds and workflow.application_round:
            application_rounds = [workflow.application_round]
        for definition in definitions_by_workflow.get(
            workflow.workflow_id or "",
            [],
        ):
            if definition.current_url.casefold() not in current_sources:
                continue
            workbench_path = (
                "/admin/content-review?workflow_key="
                f"{quote(workflow_key, safe='')}"
                "&review_snapshot="
                f"{review_content_fingerprint}"
            )
            rows.append(
                ApplicationWorkflowSourceReplacementReviewRow(
                    **definition.model_dump(),
                    review_content_fingerprint=review_content_fingerprint,
                    workflow_key=workflow_key,
                    home_university=workflow.home_university,
                    school_name=workflow.school_name,
                    country=workflow.country,
                    program_type=workflow.program_type,
                    workflow_version=workflow.version,
                    academic_year=workflow.academic_year,
                    application_rounds=application_rounds,
                    has_pending_revision=pending is not None,
                    pending_revision_id=pending.id if pending is not None else None,
                    workbench_path=workbench_path,
                )
            )
    return sorted(
        rows,
        key=lambda row: (
            row.home_university.casefold(),
            row.school_name.casefold(),
            row.workflow_key.casefold(),
            row.current_url.casefold(),
        ),
    )
