from __future__ import annotations

import hashlib
import json
from urllib.parse import quote

from .content_governance import (
    ContentGovernanceStore,
    application_workflow_publication_integrity_issues,
    list_workflow_review_backlog,
    stage_existing_workflow_for_review,
    workflow_content_hash,
    workflow_review_rule_labels,
    workflow_review_rule_keys,
    workflow_review_rule_source_urls,
    workflow_review_source_metadata,
    workflow_review_source_urls,
    workflow_storage_key,
)
from .destination_profile_review import (
    DestinationProfileReviewStore,
    build_destination_profile_review_queue,
    destination_profile_publication_integrity_issues,
)
from .models import (
    ApplicationApplicabilityStatus,
    ApplicationDeadlineStatus,
    ApplicationSupportStatus,
    ApplicationWorkflowReleaseGateCheck,
    ApplicationWorkflowReleaseReadinessReport,
    ApplicationWorkflowReviewBatchRow,
    ApplicationWorkflowReviewBatchRuleRow,
    ApplicationWorkflowReviewBatchStageItem,
    ApplicationWorkflowReviewBatchStageResult,
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowRevision,
    DestinationProfile,
    DestinationProfilePromotionEvent,
    DestinationProfileReviewEvent,
    DestinationProfileRollbackEvent,
    UniversityApplicationWorkflow,
    WebReleaseReadinessReport,
)
from .workflow_structuring import structure_application_workflow
from .source_url_policy import canonical_source_url_identity
from .governance_commands import atomic_workflow_command


_CONFIRMATION_STATUSES = {
    ApplicationSupportStatus.NEEDS_CONFIRMATION,
    ApplicationSupportStatus.UNVERIFIED,
    ApplicationSupportStatus.LEGACY_UNCLASSIFIED,
}
_REVIEW_BATCH_SCHEMA_VERSION = 3


def _published_revision_has_complete_evidence(
    workflow: UniversityApplicationWorkflow,
    revisions: list[ApplicationWorkflowRevision],
) -> bool:
    workflow_key = workflow_storage_key(workflow)
    published_content_hash = workflow_content_hash(workflow)
    expected_source_keys = {
        canonical_source_url_identity(source_url)
        for source_url in workflow_review_source_urls(workflow)
    }
    expected_rule_keys = set(workflow_review_rule_keys(workflow))
    for revision in revisions:
        if (
            revision.workflow_key != workflow_key
            or revision.version != workflow.version
            or revision.status != ApplicationWorkflowReviewStatus.PUBLISHED
            or workflow_content_hash(
                structure_application_workflow(revision.workflow)
            )
            != published_content_hash
            or revision.reviewed_at is None
            or not (revision.reviewed_by or "").strip()
        ):
            continue
        reviewer_ids = {
            approval.reviewer_id.strip().casefold()
            for approval in revision.review_approvals
            if approval.reviewer_id.strip()
        }
        if (
            len(revision.review_approvals) < revision.required_review_count
            or len(reviewer_ids) < revision.required_review_count
        ):
            continue
        if all(
            approval.reviewed_content_hash == revision.content_hash
            and {
                canonical_source_url_identity(source_url)
                for source_url in approval.reviewed_source_urls
            }
            == expected_source_keys
            and set(approval.reviewed_rule_keys) == expected_rule_keys
            for approval in revision.review_approvals
        ):
            return True
    return False


def _snapshot_fingerprint(
    workflows: list[UniversityApplicationWorkflow],
    revisions: list[ApplicationWorkflowRevision],
) -> str:
    payload = {
        "workflows": [
            {
                "workflow_key": workflow_storage_key(workflow),
                "version": workflow.version,
                "content_hash": workflow_content_hash(workflow),
                "review_status": workflow.review_status.value,
                "published_at": (
                    workflow.published_at.isoformat() if workflow.published_at else None
                ),
            }
            for workflow in workflows
        ],
        "revisions": [
            {
                "id": revision.id,
                "workflow_key": revision.workflow_key,
                "version": revision.version,
                "status": revision.status.value,
                "content_hash": revision.content_hash,
                "publication_action": revision.publication_action.value,
                "rolled_back_from_revision_id": (
                    revision.rolled_back_from_revision_id
                ),
                "restored_revision_id": revision.restored_revision_id,
                "base_version": revision.base_version,
                "required_review_count": revision.required_review_count,
                "review_note": revision.review_note,
                "published_workflow_hash": workflow_content_hash(
                    structure_application_workflow(revision.workflow)
                ),
                "reviewed_by": revision.reviewed_by,
                "reviewed_at": (
                    revision.reviewed_at.isoformat()
                    if revision.reviewed_at
                    else None
                ),
                "approvals": [
                    {
                        "reviewer_id": approval.reviewer_id,
                        "reviewed_at": approval.reviewed_at.isoformat(),
                        "reviewed_content_hash": approval.reviewed_content_hash,
                        "reviewed_source_urls": approval.reviewed_source_urls,
                        "reviewed_rule_keys": approval.reviewed_rule_keys,
                    }
                    for approval in revision.review_approvals
                ],
            }
            for revision in revisions
        ],
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _equal_zero_check(
    code: str,
    label: str,
    actual_count: int,
    detail: str,
) -> ApplicationWorkflowReleaseGateCheck:
    return ApplicationWorkflowReleaseGateCheck(
        code=code,
        label=label,
        passed=actual_count == 0,
        actual_count=actual_count,
        required_count=0,
        comparison="equal",
        detail=detail,
    )


def build_application_workflow_release_readiness(
    store: ContentGovernanceStore,
) -> ApplicationWorkflowReleaseReadinessReport:
    """Build a read-only, fail-closed release gate from the current catalog."""

    workflows = sorted(
        store.load_published_workflows(),
        key=lambda workflow: (
            workflow_storage_key(workflow),
            workflow.version,
        ),
    )
    revisions = sorted(
        store.list_revisions(),
        key=lambda revision: (
            revision.workflow_key,
            revision.version,
            revision.id,
        ),
    )
    published_workflows = [
        workflow
        for workflow in workflows
        if workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
        and workflow.published_at is not None
    ]
    pending_revisions = [
        revision
        for revision in revisions
        if revision.status == ApplicationWorkflowReviewStatus.PENDING_REVIEW
    ]

    critical_rule_count = 0
    critical_rule_source_gap_count = 0
    missing_academic_year_workflow_count = 0
    missing_effective_round_workflow_count = 0
    no_verified_exact_deadline_workflow_count = 0
    source_metadata_gap_count = 0
    source_year_gap_count = 0
    review_timestamp_gap_count = 0
    insecure_source_url_count = 0
    needs_confirmation_rule_count = 0

    for workflow in workflows:
        academic_year = (workflow.academic_year or "").strip()
        effective_rounds = {
            value.strip()
            for value in [
                workflow.application_round,
                *workflow.effective_application_rounds,
            ]
            if value and value.strip()
        }
        missing_academic_year_workflow_count += int(not academic_year)
        missing_effective_round_workflow_count += int(not effective_rounds)
        no_verified_exact_deadline_workflow_count += int(
            not any(
                step.deadline_status == ApplicationDeadlineStatus.VERIFIED_EXACT
                and step.deadline_at is not None
                and (step.deadline_source_url or "").casefold().startswith("https://")
                and step.deadline_checked_at is not None
                for step in workflow.steps
            )
        )

        source_metadata = workflow_review_source_metadata(workflow)
        source_metadata_gap_count += sum(
            source is None
            or not source.title.strip()
            or source.authority is None
            for source in source_metadata.values()
        )
        source_year_gap_count += sum(
            source is None
            or not (source.effective_academic_year or "").strip()
            or bool(academic_year)
            and source.effective_academic_year.strip() != academic_year
            for source in source_metadata.values()
        )
        review_timestamp_gap_count += (
            int(workflow.last_checked is None)
            + sum(
                source is None or source.checked_at is None
                for source in source_metadata.values()
            )
            + sum(step.checked_at is None for step in workflow.steps)
        )

        source_urls = workflow_review_source_urls(workflow)
        insecure_source_url_count += sum(
            not source_url.casefold().startswith("https://")
            for source_url in source_urls
        )
        rule_sources = workflow_review_rule_source_urls(workflow)
        critical_rule_count += len(rule_sources)
        critical_rule_source_gap_count += sum(
            not source_urls for source_urls in rule_sources.values()
        )
        needs_confirmation_rule_count += int(
            workflow.applicability_status != ApplicationApplicabilityStatus.VERIFIED
        )
        needs_confirmation_rule_count += sum(
            step.needs_confirmation or step.support_status in _CONFIRMATION_STATUSES
            for step in workflow.steps
        )
        needs_confirmation_rule_count += sum(
            document.needs_confirmation
            for step in workflow.steps
            for document in step.document_requirements
        )

    unpublished_workflow_count = len(workflows) - len(published_workflows)
    published_without_dual_review_evidence_count = sum(
        not _published_revision_has_complete_evidence(workflow, revisions)
        for workflow in published_workflows
    )
    public_by_key = {
        workflow_storage_key(workflow): workflow for workflow in workflows
    }
    publication_history_integrity_gap_count = sum(
        bool(
            application_workflow_publication_integrity_issues(
                workflow_key,
                revisions,
                public_by_key.get(workflow_key),
            )
        )
        for workflow_key in sorted(
            {
                revision.workflow_key for revision in revisions
            }
            | {
                workflow_storage_key(workflow)
                for workflow in published_workflows
            }
        )
    )
    checks = [
        ApplicationWorkflowReleaseGateCheck(
            code="catalog_present",
            label="流程目錄已載入",
            passed=len(workflows) >= 1,
            actual_count=len(workflows),
            required_count=1,
            comparison="at_least",
            detail="正式檢查必須至少載入一份申請流程，空目錄不能視為可發布。",
        ),
        _equal_zero_check(
            "all_workflows_published",
            "所有流程均已正式發布",
            unpublished_workflow_count,
            "legacy、draft、待審或缺 published_at 的流程都維持發布阻擋。",
        ),
        _equal_zero_check(
            "published_dual_review_evidence",
            "已發布流程具有完整雙審證據",
            published_without_dual_review_evidence_count,
            "每份 published 流程都必須有相同版本、內容雜湊、兩位不同審查者、完整來源與規定清單。",
        ),
        _equal_zero_check(
            "publication_history_integrity",
            "申請流程發布與復原稽核鏈完整",
            publication_history_integrity_gap_count,
            "目前公開版、發布快照、撤回版本、恢復目標與原雙審證據必須形成同一流程內可驗證且不可重複的稽核鏈。",
        ),
        _equal_zero_check(
            "no_pending_revisions",
            "沒有尚未處置的待審版本",
            len(pending_revisions),
            "仍在 pending_review 的候選內容必須先核准發布或明確退回。",
        ),
        _equal_zero_check(
            "academic_years_complete",
            "流程適用學年度完整",
            missing_academic_year_workflow_count,
            "流程學年度只能依真人核對的官方證據補正。",
        ),
        _equal_zero_check(
            "application_rounds_complete",
            "流程有效梯次完整",
            missing_effective_round_workflow_count,
            "至少要有一個已確認的申請梯次。",
        ),
        _equal_zero_check(
            "verified_exact_deadlines_complete",
            "每份流程具有可驗證精確期限",
            no_verified_exact_deadline_workflow_count,
            "精確期限必須同時有日期、HTTPS 官方來源與查核日期。",
        ),
        _equal_zero_check(
            "source_metadata_complete",
            "來源證據資料完整",
            source_metadata_gap_count,
            "每個規定引用的網址都必須有正式名稱、角色與權威層級。",
        ),
        _equal_zero_check(
            "source_years_complete",
            "來源適用學年度完整且一致",
            source_year_gap_count,
            "每個來源年度必須逐頁確認，不能由流程年度自動回填。",
        ),
        _equal_zero_check(
            "review_timestamps_complete",
            "流程、來源與步驟查核日期完整",
            review_timestamp_gap_count,
            "最後查核日期必須來自實際審查紀錄。",
        ),
        _equal_zero_check(
            "critical_rules_sourced",
            "所有關鍵規定都有直接官方來源",
            critical_rule_source_gap_count,
            "流程適用範圍、每個步驟與每份文件都必須直接連到官方來源。",
        ),
        _equal_zero_check(
            "https_sources_only",
            "所有官方來源均使用 HTTPS",
            insecure_source_url_count,
            "非 HTTPS 網址只能在真人核實替代頁後於 pending revision 修正。",
        ),
        _equal_zero_check(
            "no_needs_confirmation_rules",
            "沒有尚待確認的流程、步驟或文件",
            needs_confirmation_rule_count,
            "仍標示待確認的規定不能支持學生只依產品指示完成申請。",
        ),
    ]
    blocking_check_count = sum(not check.passed for check in checks)
    return ApplicationWorkflowReleaseReadinessReport(
        snapshot_fingerprint=_snapshot_fingerprint(workflows, revisions),
        release_ready=blocking_check_count == 0,
        blocking_check_count=blocking_check_count,
        total_workflow_count=len(workflows),
        published_workflow_count=len(published_workflows),
        unpublished_workflow_count=unpublished_workflow_count,
        published_without_dual_review_evidence_count=(
            published_without_dual_review_evidence_count
        ),
        publication_history_integrity_gap_count=(
            publication_history_integrity_gap_count
        ),
        pending_revision_count=len(pending_revisions),
        critical_rule_count=critical_rule_count,
        critical_rule_source_gap_count=critical_rule_source_gap_count,
        missing_academic_year_workflow_count=(
            missing_academic_year_workflow_count
        ),
        missing_effective_round_workflow_count=(
            missing_effective_round_workflow_count
        ),
        no_verified_exact_deadline_workflow_count=(
            no_verified_exact_deadline_workflow_count
        ),
        source_metadata_gap_count=source_metadata_gap_count,
        source_year_gap_count=source_year_gap_count,
        review_timestamp_gap_count=review_timestamp_gap_count,
        insecure_source_url_count=insecure_source_url_count,
        needs_confirmation_rule_count=needs_confirmation_rule_count,
        checks=checks,
    )


def _destination_profile_release_fingerprint(
    profiles: list[DestinationProfile],
    review_events: list[DestinationProfileReviewEvent],
    promotion_events: list[DestinationProfilePromotionEvent],
    rollback_events: list[DestinationProfileRollbackEvent],
) -> str:
    def sorted_payload(rows: list) -> list[dict]:
        return [
            row.model_dump(mode="json")
            for row in sorted(rows, key=lambda item: item.id)
        ]

    payload = {
        "profiles": [
            profile.model_dump(mode="json")
            for profile in sorted(
                profiles,
                key=lambda row: (
                    (row.home_university or "").casefold(),
                    row.school_name.casefold(),
                ),
            )
        ],
        "review_events": sorted_payload(review_events),
        "promotion_events": sorted_payload(promotion_events),
        "rollback_events": sorted_payload(rollback_events),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_web_release_readiness(
    store: ContentGovernanceStore,
    destination_profiles: list[DestinationProfile],
    destination_review_store: DestinationProfileReviewStore,
) -> WebReleaseReadinessReport:
    """Build the actual Web release gate across workflows and living information."""

    workflow_report = build_application_workflow_release_readiness(store)
    review_events = destination_review_store.list_events()
    promotion_events = destination_review_store.list_promotion_events()
    rollback_events = destination_review_store.list_rollback_events()
    destination_fingerprint = _destination_profile_release_fingerprint(
        destination_profiles,
        review_events,
        promotion_events,
        rollback_events,
    )
    integrity_issues = destination_profile_publication_integrity_issues(
        destination_profiles,
        review_events,
        promotion_events,
        rollback_events,
    )
    try:
        destination_queue = build_destination_profile_review_queue(
            destination_profiles,
            review_events=review_events,
            promotion_events=promotion_events,
            rollback_events=rollback_events,
        )
    except ValueError as exc:
        integrity_issues = list(dict.fromkeys([*integrity_issues, str(exc)]))
        total_profile_count = len(destination_profiles)
        verified_profile_count = sum(
            profile.coverage_status == "official_verified"
            for profile in destination_profiles
        )
        pending_review_count = total_profile_count - verified_profile_count
        pending_source_count = sum(
            len(profile.sources)
            for profile in destination_profiles
            if profile.coverage_status != "official_verified"
        )
        review_started_count = 0
        ready_for_promotion_count = 0
        change_requested_count = 0
    else:
        total_profile_count = destination_queue.total_profile_count
        verified_profile_count = destination_queue.verified_profile_count
        pending_review_count = destination_queue.pending_review_count
        pending_source_count = destination_queue.pending_source_count
        review_started_count = destination_queue.review_started_profile_count
        ready_for_promotion_count = destination_queue.ready_for_promotion_count
        change_requested_count = destination_queue.change_requested_profile_count

    destination_checks = [
        ApplicationWorkflowReleaseGateCheck(
            code="destination_catalog_present",
            label="生活情報目錄已載入",
            passed=total_profile_count >= 1,
            actual_count=total_profile_count,
            required_count=1,
            comparison="at_least",
            detail="Web 總發布檢查必須載入生活情報；空目錄不能被視為完成。",
        ),
        _equal_zero_check(
            "all_destination_profiles_verified",
            "所有生活情報均達完整查核或已完成雙審升級",
            pending_review_count,
            "既有 official_verified 基準可保留；official_partial、未收集、仍待雙審或尚未明確升級的生活情報都維持 Web 發布阻擋。",
        ),
        _equal_zero_check(
            "destination_publication_history_integrity",
            "生活情報審查、升級與復原稽核鏈完整",
            len(integrity_issues),
            "升級必須精確綁定兩位有效審查者；公開內容、事件順序、復原目標與內容指紋都必須可驗證且不可重複。",
        ),
    ]
    destination_blocking_count = sum(
        not check.passed for check in destination_checks
    )
    combined_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "application_workflows": workflow_report.snapshot_fingerprint,
                "destination_profiles": destination_fingerprint,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    checks = [*workflow_report.checks, *destination_checks]
    blocking_check_count = (
        workflow_report.blocking_check_count + destination_blocking_count
    )
    payload = workflow_report.model_dump()
    payload.update(
        {
            "snapshot_fingerprint": combined_fingerprint,
            "release_ready": blocking_check_count == 0,
            "blocking_check_count": blocking_check_count,
            "checks": checks,
            "application_workflow_snapshot_fingerprint": (
                workflow_report.snapshot_fingerprint
            ),
            "application_workflow_blocking_check_count": (
                workflow_report.blocking_check_count
            ),
            "destination_profile_snapshot_fingerprint": destination_fingerprint,
            "destination_profile_blocking_check_count": (
                destination_blocking_count
            ),
            "total_destination_profile_count": total_profile_count,
            "verified_destination_profile_count": verified_profile_count,
            "pending_destination_profile_review_count": pending_review_count,
            "pending_destination_profile_source_count": pending_source_count,
            "destination_profile_review_started_count": review_started_count,
            "destination_profile_ready_for_promotion_count": (
                ready_for_promotion_count
            ),
            "destination_profile_change_requested_count": (
                change_requested_count
            ),
            "destination_profile_review_event_count": len(review_events),
            "destination_profile_promotion_event_count": len(promotion_events),
            "destination_profile_rollback_event_count": len(rollback_events),
            "destination_profile_publication_integrity_gap_count": len(
                integrity_issues
            ),
        }
    )
    return WebReleaseReadinessReport.model_validate(payload)


def build_application_workflow_review_content_fingerprint(
    store: ContentGovernanceStore,
) -> str:
    """Hash substantive content and membership, excluding review progress evidence."""

    pending_by_key: dict[str, ApplicationWorkflowRevision] = {}
    for revision in sorted(
        store.list_revisions(),
        key=lambda row: row.detected_at,
        reverse=True,
    ):
        if (
            revision.status == ApplicationWorkflowReviewStatus.PENDING_REVIEW
            and revision.workflow_key not in pending_by_key
        ):
            pending_by_key[revision.workflow_key] = revision
    content_rows = []
    for workflow in store.load_published_workflows():
        if (
            workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
            and workflow.published_at is not None
        ):
            continue
        workflow_key = workflow_storage_key(workflow)
        effective = pending_by_key.get(workflow_key)
        content_rows.append(
            {
                "workflow_key": workflow_key,
                "content_hash": workflow_content_hash(
                    effective.workflow if effective is not None else workflow
                ),
            }
        )
    canonical = json.dumps(
        {
            "review_batch_schema_version": _REVIEW_BATCH_SCHEMA_VERSION,
            "workflows": sorted(
                content_rows,
                key=lambda row: row["workflow_key"],
            ),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_application_workflow_review_batch_rows(
    store: ContentGovernanceStore,
    *,
    batch_size: int = 10,
) -> list[ApplicationWorkflowReviewBatchRow]:
    """Split the live backlog into deterministic, risk-first human-review batches."""

    if not 1 <= batch_size <= 50:
        raise ValueError("每個審查批次必須包含 1 至 50 筆流程。")
    content_fingerprint_before = (
        build_application_workflow_review_content_fingerprint(store)
    )
    backlog = list_workflow_review_backlog(store)
    readiness = build_application_workflow_release_readiness(store)

    ordered = sorted(
        backlog.items,
        key=lambda row: (
            -row.insecure_source_count,
            -row.critical_rule_source_gap_count,
            -row.source_metadata_missing_count,
            -int(not row.academic_year_ready),
            -row.source_year_missing_count,
            -int(row.verified_exact_deadline_count == 0),
            -row.needs_confirmation_count,
            -row.critical_rule_count,
            row.home_university.casefold(),
            row.school_name.casefold(),
            row.workflow_key,
        ),
    )
    release_fingerprint = readiness.snapshot_fingerprint
    review_fingerprint = content_fingerprint_before
    rows: list[ApplicationWorkflowReviewBatchRow] = []
    for index, item in enumerate(ordered):
        batch_number = index // batch_size + 1
        batch_start = (batch_number - 1) * batch_size
        batch_workflow_count = min(batch_size, len(ordered) - batch_start)
        application_rounds = list(
            dict.fromkeys(
                value.strip()
                for value in [
                    item.application_round,
                    *item.effective_application_rounds,
                ]
                if value and value.strip()
            )
        )
        rows.append(
            ApplicationWorkflowReviewBatchRow(
                snapshot_fingerprint=release_fingerprint,
                review_content_fingerprint=review_fingerprint,
                batch_id=(
                    f"review-{review_fingerprint[:12]}-"
                    f"{batch_size:03d}-{batch_number:03d}"
                ),
                batch_number=batch_number,
                batch_workflow_count=batch_workflow_count,
                batch_position=index % batch_size + 1,
                priority_order=index + 1,
                workflow_key=item.workflow_key,
                home_university=item.home_university,
                school_name=item.school_name,
                country=item.country,
                program_type=item.program_type,
                academic_year=item.academic_year,
                application_rounds=application_rounds,
                review_gap_codes=item.review_gap_codes,
                review_gap_count=item.review_gap_count,
                critical_rule_count=item.critical_rule_count,
                source_count=item.source_count,
                source_metadata_missing_count=(
                    item.source_metadata_missing_count
                ),
                source_year_missing_count=item.source_year_missing_count,
                review_timestamp_missing_count=(
                    item.review_timestamp_missing_count
                ),
                critical_rule_source_gap_count=(
                    item.critical_rule_source_gap_count
                ),
                insecure_source_count=item.insecure_source_count,
                needs_confirmation_count=item.needs_confirmation_count,
                verified_exact_deadline_count=(
                    item.verified_exact_deadline_count
                ),
                has_pending_revision=item.has_pending_revision,
                pending_revision_id=item.pending_revision_id,
                review_approval_count=item.review_approval_count,
                required_review_count=item.required_review_count,
                review_ready_to_publish=item.review_ready_to_publish,
                workbench_path=(
                    "/admin/content-review?workflow_key="
                    + quote(item.workflow_key, safe="")
                    + "&review_snapshot="
                    + review_fingerprint
                ),
                batch_workbench_path=(
                    "/admin/content-review?review_batch="
                    f"review-{review_fingerprint[:12]}-"
                    f"{batch_size:03d}-{batch_number:03d}"
                    f"&batch_size={batch_size}"
                    "&review_snapshot="
                    + review_fingerprint
                ),
                batch_rule_checklist_path=(
                    "/admin/application-workflow-review-batches/"
                    f"review-{review_fingerprint[:12]}-"
                    f"{batch_size:03d}-{batch_number:03d}"
                    f"/rules.csv?batch_size={batch_size}"
                    "&expected_snapshot="
                    + review_fingerprint
                ),
            )
        )
    content_fingerprint_after = (
        build_application_workflow_review_content_fingerprint(store)
    )
    if content_fingerprint_before != content_fingerprint_after:
        raise RuntimeError("待查核內容在產生審查批次時已變更，請重新下載。")
    return rows


@atomic_workflow_command
def stage_application_workflow_review_batch(
    store: ContentGovernanceStore,
    batch_id: str,
    *,
    batch_size: int,
    expected_snapshot: str,
    detected_by: str,
) -> ApplicationWorkflowReviewBatchStageResult:
    """Idempotently stage one current review batch without publishing it."""

    rows = build_application_workflow_review_batch_rows(
        store,
        batch_size=batch_size,
    )
    current_fingerprint = (
        rows[0].review_content_fingerprint
        if rows
        else build_application_workflow_review_content_fingerprint(store)
    )
    if current_fingerprint != expected_snapshot:
        raise RuntimeError(
            "這份雙人審查分工清單的資料快照已過期；請重新下載目前版本。"
        )
    batch_rows = [row for row in rows if row.batch_id == batch_id]
    if not batch_rows:
        raise LookupError("找不到目前快照中的這個審查批次。")

    staged_items: list[ApplicationWorkflowReviewBatchStageItem] = []
    for row in batch_rows:
        revision = stage_existing_workflow_for_review(
            store,
            row.workflow_key,
            detected_by=detected_by,
        )
        staged_items.append(
            ApplicationWorkflowReviewBatchStageItem(
                workflow_key=row.workflow_key,
                revision_id=revision.id,
                created=not row.has_pending_revision,
            )
        )
    created_count = sum(item.created for item in staged_items)
    return ApplicationWorkflowReviewBatchStageResult(
        batch_id=batch_id,
        review_content_fingerprint=current_fingerprint,
        batch_size=batch_size,
        workflow_count=len(staged_items),
        created_count=created_count,
        existing_count=len(staged_items) - created_count,
        items=staged_items,
    )


def _workflow_review_rule_detail(
    workflow: UniversityApplicationWorkflow,
    rule_key: str,
) -> str:
    if rule_key == "workflow:applicability":
        rounds = list(
            dict.fromkeys(
                value.strip()
                for value in [
                    workflow.application_round,
                    *workflow.effective_application_rounds,
                ]
                if value and value.strip()
            )
        )
        return "；".join(
            [
                f"適用學年度：{workflow.academic_year or '待確認'}",
                f"有效梯次：{'、'.join(rounds) if rounds else '待確認'}",
                f"適用狀態：{workflow.applicability_status.value}",
                f"說明：{workflow.applicability_note}",
            ]
        )

    parts = rule_key.split(":")
    step_index = int(parts[1])
    step = workflow.steps[step_index]
    if parts[0] == "step":
        detail_parts = [
            step.summary,
            *step.details,
            f"負責單位：{step.responsible_unit or step.responsible_party}",
            f"時程：{step.timing or '待確認'}",
            f"期限狀態：{step.deadline_status.value}",
        ]
        if step.deadline_at is not None:
            detail_parts.append(f"精確期限：{step.deadline_at.isoformat()}")
        return "；".join(value for value in detail_parts if value)

    document = step.document_requirements[int(parts[2])]
    document_parts = [
        f"文件：{document.name}",
        f"份數：{document.copies if document.copies is not None else '待確認'}",
        f"正影本：{document.copy_type.value}",
    ]
    if document.signatures:
        document_parts.append(f"簽名：{'、'.join(document.signatures)}")
    if document.stamps:
        document_parts.append(f"蓋章：{'、'.join(document.stamps)}")
    return "；".join(document_parts)


def build_application_workflow_review_batch_rule_rows(
    store: ContentGovernanceStore,
    *,
    batch_id: str,
    batch_size: int = 10,
    expected_snapshot: str | None = None,
) -> list[ApplicationWorkflowReviewBatchRuleRow]:
    """Expand one snapshot-bound workflow batch into every rule reviewers attest."""

    batch_rows = build_application_workflow_review_batch_rows(
        store,
        batch_size=batch_size,
    )
    if not batch_rows:
        return []
    release_fingerprint = batch_rows[0].snapshot_fingerprint
    review_fingerprint = batch_rows[0].review_content_fingerprint
    if expected_snapshot and expected_snapshot != review_fingerprint:
        raise RuntimeError(
            "這份雙人審查分工清單的資料快照已過期；請重新下載目前版本。"
        )
    selected = [row for row in batch_rows if row.batch_id == batch_id]
    if not selected:
        return []

    workflows_by_key = {
        workflow_storage_key(workflow): workflow
        for workflow in store.load_published_workflows()
    }
    effective_pending_keys: set[str] = set()
    for revision in sorted(
        store.list_revisions(),
        key=lambda row: row.detected_at,
        reverse=True,
    ):
        if (
            revision.status == ApplicationWorkflowReviewStatus.PENDING_REVIEW
            and revision.workflow_key in workflows_by_key
            and revision.workflow_key not in effective_pending_keys
        ):
            if workflow_storage_key(revision.workflow) != revision.workflow_key:
                raise RuntimeError(
                    "待審版本的穩定流程身分與公開版不一致，不能產生逐規定查核表。"
                )
            workflows_by_key[revision.workflow_key] = revision.workflow
            effective_pending_keys.add(revision.workflow_key)
    output: list[ApplicationWorkflowReviewBatchRuleRow] = []
    for batch_row in selected:
        workflow = workflows_by_key.get(batch_row.workflow_key)
        if workflow is None:
            raise RuntimeError(
                "產生逐規定查核表期間流程資料已變更；請重新下載目前版本。"
            )
        rule_sources = workflow_review_rule_source_urls(workflow)
        rule_labels = workflow_review_rule_labels(workflow)
        source_metadata = workflow_review_source_metadata(workflow)
        for rule_key in workflow_review_rule_keys(workflow):
            source_urls = rule_sources[rule_key]
            sources = [source_metadata.get(source_url) for source_url in source_urls]
            source_metadata_missing_count = sum(
                source is None
                or not source.title.strip()
                or source.authority is None
                for source in sources
            )
            source_year_missing_count = sum(
                source is None
                or not (source.effective_academic_year or "").strip()
                or bool((workflow.academic_year or "").strip())
                and source.effective_academic_year.strip()
                != workflow.academic_year.strip()
                for source in sources
            )
            review_timestamp_missing_count = sum(
                source is None or source.checked_at is None for source in sources
            )
            insecure_source_count = sum(
                not source_url.casefold().startswith("https://")
                for source_url in source_urls
            )
            if rule_key == "workflow:applicability":
                needs_confirmation = (
                    not bool((workflow.academic_year or "").strip())
                    or not bool(
                        [
                            value
                            for value in [
                                workflow.application_round,
                                *workflow.effective_application_rounds,
                            ]
                            if value and value.strip()
                        ]
                    )
                    or workflow.applicability_status
                    != ApplicationApplicabilityStatus.VERIFIED
                )
                review_timestamp_missing_count += int(
                    workflow.last_checked is None
                )
            else:
                key_parts = rule_key.split(":")
                step = workflow.steps[int(key_parts[1])]
                if key_parts[0] == "step":
                    needs_confirmation = (
                        step.needs_confirmation
                        or step.support_status in _CONFIRMATION_STATUSES
                    )
                    review_timestamp_missing_count += int(step.checked_at is None)
                else:
                    document = step.document_requirements[int(key_parts[2])]
                    needs_confirmation = (
                        document.needs_confirmation
                        or step.needs_confirmation
                        or step.support_status in _CONFIRMATION_STATUSES
                    )
                    review_timestamp_missing_count += int(step.checked_at is None)
            blocked = (
                not source_urls
                or bool(source_metadata_missing_count)
                or bool(source_year_missing_count)
                or bool(review_timestamp_missing_count)
                or bool(insecure_source_count)
                or needs_confirmation
            )
            output.append(
                ApplicationWorkflowReviewBatchRuleRow(
                    snapshot_fingerprint=release_fingerprint,
                    review_content_fingerprint=review_fingerprint,
                    batch_id=batch_row.batch_id,
                    batch_number=batch_row.batch_number,
                    batch_position=batch_row.batch_position,
                    workflow_key=batch_row.workflow_key,
                    home_university=batch_row.home_university,
                    school_name=batch_row.school_name,
                    academic_year=batch_row.academic_year,
                    application_rounds=batch_row.application_rounds,
                    rule_key=rule_key,
                    rule_label=rule_labels[rule_key],
                    rule_detail=_workflow_review_rule_detail(workflow, rule_key),
                    source_urls=source_urls,
                    source_titles=[source.title if source is not None else "" for source in sources],
                    source_roles=[source.role.value if source is not None else "" for source in sources],
                    source_authorities=[
                        source.authority.value
                        if source is not None and source.authority is not None
                        else ""
                        for source in sources
                    ],
                    source_academic_years=[
                        source.effective_academic_year or ""
                        if source is not None
                        else ""
                        for source in sources
                    ],
                    source_checked_at=[
                        source.checked_at.isoformat()
                        if source is not None and source.checked_at is not None
                        else ""
                        for source in sources
                    ],
                    source_metadata_missing_count=source_metadata_missing_count,
                    source_year_missing_count=source_year_missing_count,
                    review_timestamp_missing_count=review_timestamp_missing_count,
                    insecure_source_count=insecure_source_count,
                    needs_confirmation=needs_confirmation,
                    blocked=blocked,
                    workbench_path=batch_row.workbench_path,
                )
            )

    content_fingerprint_after = (
        build_application_workflow_review_content_fingerprint(store)
    )
    if content_fingerprint_after != review_fingerprint:
        raise RuntimeError(
            "產生逐規定查核表期間資料快照已變更；請重新下載目前版本。"
        )
    return output
