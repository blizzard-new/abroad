import json
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.openapi_contract import OPENAPI_CONTRACT_VERSION


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_SNAPSHOT = REPOSITORY_ROOT / "docs" / "api" / "openapi.json"


def test_frozen_openapi_contract_matches_live_schema(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    live_schema = client.get("/openapi.json").json()
    snapshot = json.loads(OPENAPI_SNAPSHOT.read_text(encoding="utf-8"))

    assert snapshot == live_schema
    assert snapshot["x-contract-version"] == OPENAPI_CONTRACT_VERSION
    assert snapshot["x-product-boundaries"] == {
        "account_routes_require_bearer_session": True,
        "ai_features": "paused",
        "personal_document_storage_requires_separate_consent": True,
        "platform_submits_applications": False,
        "public_read_without_login": True,
        "university_board_reads_require_verified_email": True,
        "university_board_writes_require_verified_email": True,
        "university_board_access_requires_matching_school": False,
        "workflow_issue_report_review_cannot_publish": True,
        "workflow_issue_reports_require_verified_student": True,
    }
    assert snapshot["x-common-error-status"] == {
        "authentication_required": 401,
        "permission_denied": 403,
        "rate_limited": 429,
        "resource_not_found": 404,
        "validation_failed": 422,
    }


def test_next_phase_keeps_public_discovery_routes_available(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    schema = client.get("/openapi.json")

    assert schema.status_code == 200
    paths = schema.json()["paths"]
    assert "get" in paths["/universities"]
    assert "get" in paths["/search"]
    assert "get" in paths["/application-workflow"]


def test_private_community_writes_expose_retry_mutation_header(tmp_path) -> None:
    paths = TestClient(create_app(tmp_path)).get("/openapi.json").json()["paths"]
    writes = (
        ("/community/conversations", "post"),
        ("/community/conversations/{conversation_id}/accept", "post"),
        ("/community/conversations/{conversation_id}/messages", "post"),
        ("/community/blocks", "post"),
        ("/community/reports", "post"),
        ("/admin/community/reports/{report_id}", "patch"),
    )

    for path, method in writes:
        parameters = paths[path][method]["parameters"]
        mutation_header = next(
            row for row in parameters if row["name"] == "X-Community-Mutation-ID"
        )
        assert mutation_header["in"] == "header"
        assert mutation_header["required"] is False
        value_schema = mutation_header["schema"]["anyOf"][0]
        assert value_schema["minLength"] == 16
        assert value_schema["maxLength"] == 128


def test_workflow_issue_report_contract_exposes_retry_and_admin_review_paths(tmp_path) -> None:
    schema = TestClient(create_app(tmp_path)).get("/openapi.json").json()
    paths = schema["paths"]

    assert "post" in paths["/application-workflow-issue-reports"]
    assert "get" in paths["/admin/application-workflow-issue-reports"]
    assert "patch" in paths[
        "/admin/application-workflow-issue-reports/{report_id}"
    ]
    for path, method in (
        ("/application-workflow-issue-reports", "post"),
        ("/admin/application-workflow-issue-reports/{report_id}", "patch"),
    ):
        mutation_header = next(
            row
            for row in paths[path][method]["parameters"]
            if row["name"] == "X-Content-Report-Mutation-ID"
        )
        assert mutation_header["in"] == "header"
        assert mutation_header["required"] is True
        assert mutation_header["schema"]["minLength"] == 16
        assert mutation_header["schema"]["maxLength"] == 128

    workflow_schema = schema["components"]["schemas"]["UniversityApplicationWorkflow"]
    assert "issue_report_snapshot" in workflow_schema["properties"]


def test_account_deletion_exposes_dedicated_retry_mutation_header(tmp_path) -> None:
    operation = TestClient(create_app(tmp_path)).get("/openapi.json").json()[
        "paths"
    ]["/auth/me"]["delete"]
    mutation_header = next(
        row
        for row in operation["parameters"]
        if row["name"] == "X-Account-Deletion-Mutation-ID"
    )

    assert mutation_header["in"] == "header"
    assert mutation_header["required"] is False
    value_schema = mutation_header["schema"]["anyOf"][0]
    assert value_schema["minLength"] == 16
    assert value_schema["maxLength"] == 128


def test_api_contract_page_does_not_depend_on_csp_blocked_assets(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert docs.headers["content-type"].startswith("text/html")
    assert 'href="/openapi.json"' in docs.text
    assert "cdn.jsdelivr.net" not in docs.text
    assert "<script" not in docs.text.casefold()
    assert "style=" not in docs.text.casefold()

    redoc = client.get("/redoc", follow_redirects=False)
    assert redoc.status_code == 307
    assert redoc.headers["location"] == "/docs"

    favicon = client.get("/favicon.ico")
    assert favicon.status_code == 200
    assert favicon.headers["content-type"].startswith("image/x-icon")
    assert favicon.content[:4] == b"\x00\x00\x01\x00", "a real .ico file, which cannot carry script"


def test_calendar_conflict_contract_preserves_application_plan_identity(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    openapi = client.get("/openapi.json").json()
    schemas = openapi["components"]["schemas"]

    assert "post" in openapi["paths"]["/calendar/conflicts/analyze"]
    assert "school_name" in schemas["AccountCalendarEvent"]["properties"]
    assert {
        "analyzed_event_count",
        "plan_count",
        "conflict_count",
        "conflicting_event_count",
        "same_day_conflict_count",
        "tight_window_conflict_count",
        "groups",
    } <= schemas["CalendarConflictReport"]["properties"].keys()
    assert {
        "kind",
        "start_date",
        "end_date",
        "day_gap",
        "school_names",
        "events",
        "resolution_hint",
    } <= schemas["CalendarConflictGroup"]["properties"].keys()


def test_calendar_task_schedule_contract_is_explicit_and_non_ai(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    openapi = client.get("/openapi.json").json()
    schemas = openapi["components"]["schemas"]

    assert "post" in openapi["paths"]["/calendar/tasks/schedule"]
    assert {
        "preparation_days",
        "status",
        "generated_from_event_id",
    } <= schemas["AccountCalendarEvent"]["properties"].keys()
    assert {
        "as_of",
        "analyzed_event_count",
        "incomplete_count",
        "scheduled_count",
        "start_now_count",
        "due_soon_count",
        "overdue_count",
        "completed_count",
        "items",
    } <= schemas["CalendarTaskScheduleReport"]["properties"].keys()
    assert {
        "suggested_start_date",
        "preparation_days",
        "status",
        "urgency",
        "recommended_reminder_days",
        "reason",
    } <= schemas["CalendarTaskScheduleItem"]["properties"].keys()


def test_external_calendar_contract_documents_subscription_boundary(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    paths = client.get("/openapi.json").json()["paths"]

    assert "403" in paths["/calendar-sync"]["get"]["responses"]
    assert "403" in paths["/calendar-sync/enable"]["post"]["responses"]
    assert "403" in paths["/calendar-sync/events"]["put"]["responses"]
    assert "403" not in paths["/calendar-sync"]["delete"]["responses"]


def test_application_document_contract_keeps_official_forms_public_and_gates_generation(
    tmp_path,
) -> None:
    client = TestClient(create_app(tmp_path))
    paths = client.get("/openapi.json").json()["paths"]

    assert "get" in paths["/application-center/templates"]
    assert "get" in paths["/application-center/catalog"]
    assert "401" not in paths["/application-center/templates"]["get"]["responses"]
    assert "403" not in paths["/application-center/catalog"]["get"]["responses"]
    assert "401" in paths["/application-center/manifest"]["post"]["responses"]
    assert "403" in paths["/application-center/manifest"]["post"]["responses"]
    assert "401" in paths["/application-center/pdf"]["post"]["responses"]
    assert "403" in paths["/application-center/pdf"]["post"]["responses"]


def test_document_completeness_contract_is_subscription_gated_and_ai_stays_paused(
    tmp_path,
) -> None:
    client = TestClient(create_app(tmp_path))
    paths = client.get("/openapi.json").json()["paths"]

    for path in ("/document-check", "/ai/review-document"):
        operation = paths[path]["post"]
        responses = operation["responses"]
        assert "401" in responses
        assert "403" in responses
        assert "422" in responses
        assert "503" in responses
        body_reference = operation["requestBody"]["content"][
            "multipart/form-data"
        ]["schema"]["$ref"]
        body_schema = client.get("/openapi.json").json()["components"]["schemas"][
            body_reference.rsplit("/", 1)[-1]
        ]
        assert "consent" in body_schema["required"]
        assert body_schema["properties"]["consent"]["type"] == "boolean"


def test_ai_compatibility_contract_is_explicitly_paused(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    paths = client.get("/openapi.json").json()["paths"]

    for path in ("/ai/chat", "/ai/rewrite-document"):
        operation = paths[path]["post"]
        assert operation["deprecated"] is True
        assert "503" in operation["responses"]

    assert "post" in paths["/advisor/ask"]


def test_application_workflow_contract_exposes_structured_rule_fields(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    schema = client.get("/openapi.json").json()
    step_properties = schema["components"]["schemas"]["ApplicationStep"]["properties"]
    submission_properties = schema["components"]["schemas"][
        "ApplicationSubmissionDetails"
    ]["properties"]
    workflow_properties = schema["components"]["schemas"][
        "UniversityApplicationWorkflow"
    ]["properties"]

    assert {
        "scope",
        "submission",
        "document_requirements",
        "responsible_unit",
        "deadline_at",
        "deadline_status",
        "deadline_source_url",
        "deadline_checked_at",
        "deadline_reminder_eligible",
        "official_form_urls",
        "checked_at",
        "support_status",
        "confirmation_contact",
    } <= step_properties.keys()
    assert {
        "academic_year",
        "application_round",
        "effective_application_rounds",
        "applicability_status",
        "applicability_note",
        "version",
        "review_status",
        "published_at",
    } <= workflow_properties.keys()
    assert {
        "send_by_at",
        "arrival_deadline_at",
        "deadline_note",
    } <= submission_properties.keys()


def test_content_review_contract_exposes_nonpublishing_source_candidates(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    openapi = client.get("/openapi.json").json()
    candidate_path = (
        "/admin/application-workflow-source-replacement-candidates"
    )
    candidate_export_path = (
        "/admin/application-workflow-source-replacement-review-queue.csv"
    )
    source_evidence_export_path = (
        "/admin/application-workflow-review-backlog/source-evidence.csv"
    )
    candidate = openapi["components"]["schemas"][
        "ApplicationWorkflowSourceReplacementCandidate"
    ]["properties"]
    backlog = openapi["components"]["schemas"][
        "ApplicationWorkflowReviewBacklog"
    ]["properties"]
    backlog_item = openapi["components"]["schemas"][
        "ApplicationWorkflowReviewBacklogItem"
    ]["properties"]
    source_evidence_group = openapi["components"]["schemas"][
        "ApplicationWorkflowSourceEvidenceGapGroup"
    ]

    assert "get" in openapi["paths"][candidate_path]
    assert "get" in openapi["paths"][candidate_export_path]
    assert "get" in openapi["paths"][source_evidence_export_path]
    export_parameters = openapi["paths"][candidate_export_path]["get"][
        "parameters"
    ]
    assert any(row["name"] == "expected_snapshot" for row in export_parameters)
    source_evidence_parameters = openapi["paths"][source_evidence_export_path][
        "get"
    ]["parameters"]
    expected_snapshot = next(
        row
        for row in source_evidence_parameters
        if row["name"] == "expected_snapshot"
    )
    assert expected_snapshot["in"] == "query"
    assert expected_snapshot["required"] is True
    assert expected_snapshot["schema"]["pattern"] == "^[0-9a-f]{64}$"
    assert expected_snapshot["schema"]["minLength"] == 64
    assert expected_snapshot["schema"]["maxLength"] == 64
    source_evidence_success_content = openapi["paths"][
        source_evidence_export_path
    ]["get"]["responses"]["200"]["content"]
    assert set(source_evidence_success_content) == {"text/csv"}
    assert "source_evidence_snapshot_fingerprint" in source_evidence_group[
        "required"
    ]
    assert {
        "revision_id",
        "workflow_key",
        "workflow_id",
        "current_url",
        "candidate_url",
        "candidate_status",
        "automated_evidence",
        "required_human_checks",
        "research_leads",
        "review_status",
        "publication_effect",
        "approvals_created",
        "public_student_data_changed",
    } <= candidate.keys()
    assert {
        "workflows_with_source_replacement_candidates",
        "source_replacement_candidate_count",
    } <= backlog.keys()
    assert {
        "source_replacement_candidate_count",
        "strong_source_replacement_candidate_count",
        "conditional_source_replacement_candidate_count",
    } <= backlog_item.keys()


def test_workflow_batch_stage_contract_is_snapshot_bound_and_nonpublishing(
    tmp_path,
) -> None:
    client = TestClient(create_app(tmp_path))
    openapi = client.get("/openapi.json").json()
    path = "/admin/application-workflow-review-batches/{batch_id}/stage"
    schemas = openapi["components"]["schemas"]

    assert "post" in openapi["paths"][path]
    request = schemas["ApplicationWorkflowReviewBatchStageRequest"]["properties"]
    result = schemas["ApplicationWorkflowReviewBatchStageResult"]["properties"]
    item = schemas["ApplicationWorkflowReviewBatchStageItem"]["properties"]
    assert {"expected_snapshot", "batch_size"} <= request.keys()
    assert {
        "batch_id",
        "review_content_fingerprint",
        "workflow_count",
        "created_count",
        "existing_count",
        "items",
        "approvals_created",
        "workflows_published",
        "public_student_data_changed",
    } <= result.keys()
    assert {"workflow_key", "revision_id", "created"} <= item.keys()


def test_destination_profile_review_contract_requires_explicit_audited_promotion(
    tmp_path,
) -> None:
    client = TestClient(create_app(tmp_path))
    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]
    schemas = openapi["components"]["schemas"]

    assert "get" in paths["/admin/destination-profile-review-queue"]
    assert "get" in paths["/admin/destination-profile-review-queue.csv"]
    assert "get" in paths["/admin/destination-profile-review-batches.csv"]
    assert "get" in paths["/admin/destination-profile-review-batches/{batch_id}"]
    assert "get" in paths[
        "/admin/destination-profile-review-batches/{batch_id}/checklist.csv"
    ]
    assert "post" in paths["/admin/destination-profile-reviews"]
    assert "post" in paths["/admin/destination-profile-promotions"]
    assert "get" in paths["/admin/destination-profile-publications"]
    assert "post" in paths["/admin/destination-profile-rollbacks"]
    queue = schemas["DestinationProfileReviewQueue"]["properties"]
    row = schemas["DestinationProfileReviewRow"]["properties"]
    event = schemas["DestinationProfileReviewEvent"]["properties"]
    request = schemas["DestinationProfileReviewSubmitRequest"]["properties"]
    promotion = schemas["DestinationProfilePromotionEvent"]["properties"]
    promotion_request = schemas["DestinationProfilePromotionRequest"]["properties"]
    rollback = schemas["DestinationProfileRollbackEvent"]["properties"]
    rollback_request = schemas["DestinationProfileRollbackRequest"]["properties"]
    publication = schemas["DestinationProfilePublicationState"]["properties"]
    publication_history = schemas["DestinationProfilePublicationHistory"]["properties"]
    batch_row = schemas["DestinationProfileReviewBatchRow"]["properties"]
    assert {
        "review_started_profile_count",
        "ready_for_promotion_count",
        "change_requested_profile_count",
        "current_review_event_count",
        "review_sections",
    } <= queue.keys()
    assert {
        "profile_content_hash",
        "profile",
        "review_history",
        "current_reviews",
        "review_approval_count",
        "review_change_request_count",
        "review_progress",
        "current_reviewer_decision",
        "ready_for_promotion",
    } <= row.keys()
    assert {
        "queue_snapshot_fingerprint",
        "review_content_fingerprint",
        "batch_id",
        "batch_number",
        "batch_profile_count",
        "batch_position",
        "priority_order",
        "profile_content_hash",
        "review_approval_count",
        "review_progress",
        "batch_workbench_path",
        "batch_checklist_path",
    } <= batch_row.keys()
    assert {
        "reviewer_id",
        "reviewer_display_name",
        "decision",
        "reviewed_source_urls",
        "reviewed_section_keys",
        "supersedes_event_id",
    } <= event.keys()
    assert {
        "expected_snapshot",
        "expected_profile_content_hash",
        "decision",
        "note",
        "reviewed_source_urls",
        "reviewed_section_keys",
    } <= request.keys()
    assert {
        "source_profile_content_hash",
        "promoted_profile_content_hash",
        "review_event_ids",
        "reviewer_ids",
        "promoted_by_id",
        "promoted_at",
        "promoted_profile",
    } <= promotion.keys()
    assert {
        "expected_snapshot",
        "expected_profile_content_hash",
        "note",
    } <= promotion_request.keys()
    assert {
        "rolled_back_from_event_id",
        "rolled_back_promotion_event_id",
        "restored_promotion_event_id",
        "previous_profile_content_hash",
        "restored_profile_content_hash",
        "rolled_back_by_id",
        "rolled_back_at",
        "restored_profile",
    } <= rollback.keys()
    assert {
        "expected_active_promotion_event_id",
        "expected_latest_publication_event_id",
        "expected_public_profile_content_hash",
        "note",
    } <= rollback_request.keys()
    assert {
        "current_candidate_content_hash",
        "current_public_profile_content_hash",
        "current_public_profile",
        "active_promotion_event_id",
        "latest_event_id",
        "latest_event_type",
        "candidate_changed_since_publication",
        "can_rollback",
        "promotion_history",
        "rollback_history",
    } <= publication.keys()
    assert {
        "profile_with_history_count",
        "active_promotion_count",
        "promotion_event_count",
        "rollback_event_count",
        "items",
    } <= publication_history.keys()


def test_application_workflow_publication_contract_exposes_safe_rollback(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]
    schemas = openapi["components"]["schemas"]

    assert "get" in paths["/admin/application-workflow-publications"]
    assert "post" in paths["/admin/application-workflow-rollbacks"]
    assert "get" in paths["/admin/web-release-readiness"]
    revision = schemas["ApplicationWorkflowRevision"]["properties"]
    request = schemas["ApplicationWorkflowRollbackRequest"]["properties"]
    summary = schemas["ApplicationWorkflowPublicationRevisionSummary"]["properties"]
    state = schemas["ApplicationWorkflowPublicationState"]["properties"]
    history = schemas["ApplicationWorkflowPublicationHistory"]["properties"]
    readiness = schemas["ApplicationWorkflowReleaseReadinessReport"]["properties"]
    web_readiness = schemas["WebReleaseReadinessReport"]["properties"]
    assert {
        "publication_action",
        "rolled_back_from_revision_id",
        "restored_revision_id",
    } <= revision.keys()
    assert {
        "workflow_key",
        "expected_current_revision_id",
        "expected_current_version",
        "expected_current_content_hash",
        "restore_revision_id",
        "note",
    } <= request.keys()
    assert {
        "revision_id",
        "version",
        "content_hash",
        "publication_action",
        "published_at",
        "published_by",
        "rolled_back_from_revision_id",
        "restored_revision_id",
        "is_current",
    } <= summary.keys()
    assert {
        "workflow_key",
        "current_revision_id",
        "current_version",
        "current_content_hash",
        "current_publication_action",
        "pending_revision_id",
        "can_rollback",
        "rollback_block_reason",
        "rollback_targets",
        "publication_history",
    } <= state.keys()
    assert {
        "workflow_count",
        "rollback_ready_count",
        "publication_revision_count",
        "rollback_revision_count",
        "items",
    } <= history.keys()
    assert "publication_history_integrity_gap_count" in readiness
    assert {
        "application_workflow_snapshot_fingerprint",
        "application_workflow_blocking_check_count",
        "destination_profile_snapshot_fingerprint",
        "destination_profile_blocking_check_count",
        "total_destination_profile_count",
        "verified_destination_profile_count",
        "pending_destination_profile_review_count",
        "pending_destination_profile_source_count",
        "destination_profile_review_event_count",
        "destination_profile_promotion_event_count",
        "destination_profile_rollback_event_count",
        "destination_profile_publication_integrity_gap_count",
    } <= web_readiness.keys()


def test_application_document_review_contract_tracks_the_reviewed_version(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    document_selection = schemas["ApplicationDocumentSelection"]["properties"]
    account_selection = schemas["AccountApplicationSelection"]["properties"]
    document_template = schemas["ApplicationDocumentTemplate"]["properties"]
    manifest_item = schemas["ApplicationPacketManifestItem"]["properties"]

    assert {
        "reviewed_version",
        "reviewed_content_sha256",
        "reviewed_at",
    } <= document_selection.keys()
    assert {
        "reviewed_version",
        "reviewed_content_sha256",
        "reviewed_at",
    } <= account_selection.keys()
    assert {
        "paper_size",
        "print_sides",
        "print_note",
        "attachment_field_order",
    } <= document_template.keys()
    assert {
        "template_version",
        "review_content_sha256",
        "reviewed",
        "preview_fields",
        "paper_size",
        "print_sides",
        "print_note",
        "attachment_order",
        "attachments",
        "invalid_attachment_fields",
        "source_url",
    } <= manifest_item.keys()
    attachment = schemas["ApplicationPacketAttachmentItem"]["properties"]
    assert {
        "order",
        "field_id",
        "field_label",
        "file_name",
        "media_type",
        "page_count",
        "placement",
    } <= attachment.keys()
    assert "validation_error" in schemas["ApplicationFieldPreviewItem"]["properties"]


def test_submission_progress_contract_tracks_manual_status_and_proof_metadata(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    openapi = client.get("/openapi.json").json()
    schemas = openapi["components"]["schemas"]

    workspace = schemas["AccountApplicationWorkspace"]["properties"]
    progress = schemas["AccountSubmissionProgress"]["properties"]
    proof = schemas["SubmissionProofMetadata"]["properties"]
    transition = schemas["SubmissionProgressTransitionRequest"]["properties"]

    assert "post" in openapi["paths"]["/account/submission-progress"]
    assert "submission_progress" in workspace
    assert {
        "method",
        "status",
        "responsible_unit",
        "send_by_at",
        "arrival_deadline_at",
        "proof_metadata",
        "recorded_by",
        "platform_submitted",
        "completed_at",
    } <= progress.keys()
    assert {
        "kind",
        "reference",
        "file_name",
        "content_type",
        "source",
        "original_file_stored",
        "recorded_at",
    } <= proof.keys()
    assert {"home_school", "progress_key", "action", "method", "proof_metadata"} <= transition.keys()


def test_notification_contract_exposes_center_read_delete_and_admin_run_routes(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]
    schemas = openapi["components"]["schemas"]

    assert "get" in paths["/account/notifications"]
    assert "delete" in paths["/account/notifications"]
    assert "patch" in paths["/account/notifications/{notification_id}/read"]
    assert "delete" in paths["/account/notifications/{notification_id}"]
    assert "patch" in paths["/account/notifications/read-all"]
    assert "post" in paths["/admin/notifications/run-due"]
    assert {
        "dedupe_key",
        "channels",
        "deadline_at",
        "reminder_days",
        "read_at",
        "deleted_at",
    } <= schemas["AccountNotification"]["properties"].keys()
    assert {
        "created_count",
        "queued_email_count",
        "sent_count",
        "retry_count",
        "failed_count",
    } <= schemas["NotificationRunResult"]["properties"].keys()
