"""Admin adapters for the existing review, snapshot and publication services.

Reading or exporting a queue never approves it. Every mutation uses the same
admin identity and store as the original workflow review commands.
"""
from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse

from . import content_governance as workflows
from . import destination_profile_review as destinations
from . import models as m
from . import release_readiness as readiness
from .review_source_candidates import (
    enrich_source_replacement_candidate_counts,
    list_source_replacement_candidate_review_rows,
    list_source_replacement_candidates,
)
from .storage import load_destination_profiles
from .governance_commands import local_governance_lock


PRIVATE_HEADERS = {"Cache-Control": "private, no-store, max-age=0"}
SNAPSHOT = Query(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
OPTIONAL_SNAPSHOT = Query(None, min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


def _csv_response(rows, columns, filename):
    """A read-only BOM CSV; neutralize spreadsheet formulas in every cell."""
    def cell(value):
        if isinstance(value, (list, tuple)):
            value = " || ".join(str(item) for item in value)
        elif isinstance(value, bool):
            value = "是" if value else "否"
        value = "" if value is None else str(value)
        return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value

    output = StringIO(newline="")
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow([label for label, _ in columns])
    for row in rows:
        values = row.model_dump(mode="json") if hasattr(row, "model_dump") else row
        writer.writerow([cell(key(values) if callable(key) else values.get(key)) for _, key in columns])
    return Response(output.getvalue(), media_type="text/csv", headers={
        **PRIVATE_HEADERS, "Content-Disposition": f'attachment; filename="{filename}"',
    })


def register_content_governance_routes(app: FastAPI, authenticated_admin, *,
                                       data_dir: Path, static_dir: Path) -> None:
    store = app.state.content_governance_store
    destination_store = app.state.destination_profile_review_store
    lock = app.state.content_review_lock

    def authorize(request, response):
        account, _ = authenticated_admin(request)
        response.headers.update(PRIVATE_HEADERS)
        return account

    def check_snapshot(expected, actual):
        if expected is not None and expected != actual:
            raise HTTPException(409, "這份審查清單的資料快照已過期；請重新載入目前版本。")

    def execute(command, *args, **kwargs):
        try:
            return command(*args, **kwargs)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except (ValueError, RuntimeError) as error:
            raise HTTPException(409, str(error)) from error

    def profiles():
        return load_destination_profiles(data_dir, include_bundled_baseline=True)

    def destination_queue(home, account):
        return execute(destinations.build_destination_profile_review_queue,
            profiles(), home_university=home, review_events=destination_store.list_events(),
            promotion_events=destination_store.list_promotion_events(),
            rollback_events=destination_store.list_rollback_events(), current_reviewer_id=account.id)

    def batch_rows(batch_size, expected):
        rows = execute(readiness.build_application_workflow_review_batch_rows, store, batch_size=batch_size)
        actual = rows[0].review_content_fingerprint if rows else readiness.build_application_workflow_review_content_fingerprint(store)
        check_snapshot(expected, actual)
        return rows

    @app.get("/admin/content-review", include_in_schema=False)
    def workbench(request: Request, response: Response):
        authorize(request, response)
        return FileResponse(static_dir / "content-review.html", headers=PRIVATE_HEADERS)

    @app.get("/admin/session", response_model=m.AccountProfile)
    def session(request: Request, response: Response):
        account = authorize(request, response)
        # The response model removes password hashes and all server-only fields.
        return account.model_dump()

    @app.get("/admin/application-workflow-review-backlog", response_model=m.ApplicationWorkflowReviewBacklog)
    def backlog(request: Request, response: Response, expected_snapshot: str | None = OPTIONAL_SNAPSHOT):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            check_snapshot(expected_snapshot, readiness.build_application_workflow_review_content_fingerprint(store))
            return enrich_source_replacement_candidate_counts(
                workflows.list_workflow_review_backlog(store), store.load_published_workflows(), store.list_revisions())

    @app.post("/admin/application-workflow-review-backlog/{workflow_key}/stage", response_model=m.ApplicationWorkflowRevision)
    def stage_one(workflow_key: str, request: Request, response: Response):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(workflows.stage_existing_workflow_for_review, store, workflow_key, detected_by=account.id)

    @app.patch("/admin/application-workflow-revisions/{revision_id}/applicability", response_model=m.ApplicationWorkflowRevision)
    def applicability(revision_id: str, payload: m.ApplicationWorkflowApplicabilityUpdateRequest,
                      request: Request, response: Response):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(workflows.update_pending_workflow_applicability, store, revision_id, payload, edited_by=account.id)

    @app.get("/admin/application-workflow-source-replacement-candidates", response_model=list[m.ApplicationWorkflowSourceReplacementCandidate])
    def source_candidates(request: Request, response: Response):
        authorize(request, response)
        return list_source_replacement_candidates(store.list_revisions())

    @app.get("/admin/application-workflow-source-replacement-review-queue.csv", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
    def source_candidates_csv(request: Request, response: Response, expected_snapshot: str | None = OPTIONAL_SNAPSHOT):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            actual = readiness.build_application_workflow_review_content_fingerprint(store)
            check_snapshot(expected_snapshot, actual)
            rows = list_source_replacement_candidate_review_rows(store.load_published_workflows(), store.list_revisions(), review_content_fingerprint=actual)
            backlog_keys = {row.workflow_key for row in workflows.list_workflow_review_backlog(store).items}
            rows = [row for row in rows if row.workflow_key in backlog_keys]
            return _csv_response(rows, SOURCE_REPLACEMENT_COLUMNS, f"source-replacement-review-{actual[:12]}.csv")

    @app.get("/admin/application-workflow-review-backlog/source-evidence.csv", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
    def source_evidence_csv(request: Request, response: Response, source_url: str = Query(min_length=8, max_length=2000), expected_snapshot: str = SNAPSHOT):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            rows = workflows.list_source_evidence_gap_review_rows(store, source_url)
            if not rows:
                raise HTTPException(404, "找不到這個來源證據缺口。")
            check_snapshot(expected_snapshot, rows[0].source_evidence_snapshot_fingerprint)
            return _csv_response(rows, SOURCE_EVIDENCE_COLUMNS, f"source-evidence-review-{expected_snapshot[:12]}.csv")

    @app.get("/admin/application-workflow-review-batches.csv", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
    def workflow_batches_csv(request: Request, response: Response, batch_size: int = Query(10, ge=1, le=50), expected_snapshot: str | None = OPTIONAL_SNAPSHOT):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            rows = batch_rows(batch_size, expected_snapshot)
            return _csv_response(rows, WORKFLOW_BATCH_COLUMNS, "workflow-dual-review-batches.csv")

    @app.get("/admin/application-workflow-review-batches/{batch_id}", response_model=list[m.ApplicationWorkflowReviewBatchRow])
    def workflow_batch(batch_id: str, request: Request, response: Response, batch_size: int = Query(10, ge=1, le=50), expected_snapshot: str = SNAPSHOT):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            selected = [row for row in batch_rows(batch_size, expected_snapshot) if row.batch_id == batch_id]
            if not selected:
                raise HTTPException(404, "找不到目前快照中的這個審查批次。")
            return selected

    @app.get("/admin/application-workflow-review-batches/{batch_id}/rules.csv", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
    def workflow_batch_rules(batch_id: str, request: Request, response: Response, expected_snapshot: str = SNAPSHOT, batch_size: int = Query(10, ge=1, le=50)):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            rows = execute(readiness.build_application_workflow_review_batch_rule_rows, store, batch_id=batch_id, batch_size=batch_size, expected_snapshot=expected_snapshot)
            if not rows:
                raise HTTPException(404, "找不到目前快照中的這個審查批次。")
            return _csv_response(rows, WORKFLOW_RULE_COLUMNS, f"workflow-review-rules-{batch_id}.csv")

    @app.post("/admin/application-workflow-review-batches/{batch_id}/stage", response_model=m.ApplicationWorkflowReviewBatchStageResult)
    def stage_batch(batch_id: str, payload: m.ApplicationWorkflowReviewBatchStageRequest, request: Request, response: Response):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(readiness.stage_application_workflow_review_batch, store, batch_id, batch_size=payload.batch_size, expected_snapshot=payload.expected_snapshot, detected_by=account.id)

    @app.get("/admin/application-workflow-publications", response_model=m.ApplicationWorkflowPublicationHistory)
    def workflow_history(request: Request, response: Response, home_university: str | None = Query(None, max_length=200)):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(workflows.build_application_workflow_publication_history, store, home_university=home_university)

    @app.post("/admin/application-workflow-rollbacks", response_model=m.ApplicationWorkflowRevision)
    def workflow_rollback(payload: m.ApplicationWorkflowRollbackRequest, request: Request, response: Response):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            result = execute(workflows.rollback_published_workflow, store, payload, rolled_back_by=account.id)
            app.state.notification_service.refresh_content_updates()
            return result

    @app.get("/admin/web-release-readiness", response_model=m.WebReleaseReadinessReport)
    def release_readiness(request: Request, response: Response):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(readiness.build_web_release_readiness, store, profiles(), destination_store)

    @app.get("/admin/application-workflow-release-readiness", response_model=m.ApplicationWorkflowReleaseReadinessReport)
    def workflow_readiness(request: Request, response: Response):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(readiness.build_application_workflow_release_readiness, store)

    @app.get("/admin/destination-profile-review-queue", response_model=m.DestinationProfileReviewQueue)
    def destination_review_queue(request: Request, response: Response, home_university: str | None = Query(None, max_length=200)):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return destination_queue(home_university, account)

    @app.get("/admin/destination-profile-review-queue.csv", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
    def destination_review_csv(request: Request, response: Response, home_university: str = Query(min_length=1, max_length=200), expected_snapshot: str = SNAPSHOT):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            queue = destination_queue(home_university, account)
            check_snapshot(expected_snapshot, queue.snapshot_fingerprint)
            return _csv_response(queue.items, DESTINATION_COLUMNS, f"destination-profile-review-{expected_snapshot[:12]}.csv")

    def destination_batches(home, account, size, expected):
        queue = destination_queue(home, account)
        check_snapshot(expected, destinations.destination_profile_review_content_fingerprint(queue))
        return queue, execute(destinations.build_destination_profile_review_batch_rows, queue, batch_size=size)

    @app.get("/admin/destination-profile-review-batches.csv", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
    def destination_batches_csv(request: Request, response: Response, home_university: str = Query(min_length=1, max_length=200), expected_snapshot: str | None = OPTIONAL_SNAPSHOT, batch_size: int = Query(10, ge=1, le=50)):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            queue, rows = destination_batches(home_university, account, batch_size, expected_snapshot)
            fingerprint = destinations.destination_profile_review_content_fingerprint(queue)
            return _csv_response(rows, DESTINATION_BATCH_COLUMNS, f"destination-dual-review-{fingerprint[:12]}.csv")

    @app.get("/admin/destination-profile-review-batches/{batch_id}", response_model=list[m.DestinationProfileReviewBatchRow])
    def destination_batch(batch_id: str, request: Request, response: Response, home_university: str = Query(min_length=1, max_length=200), expected_snapshot: str = SNAPSHOT, batch_size: int = Query(10, ge=1, le=50)):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            _, rows = destination_batches(home_university, account, batch_size, expected_snapshot)
            selected = [row for row in rows if row.batch_id == batch_id]
            if not selected:
                raise HTTPException(404, "找不到目前快照中的生活情報批次。")
            return selected

    @app.get("/admin/destination-profile-review-batches/{batch_id}/checklist.csv", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
    def destination_checklist(batch_id: str, request: Request, response: Response, home_university: str = Query(min_length=1, max_length=200), expected_snapshot: str = SNAPSHOT, batch_size: int = Query(10, ge=1, le=50)):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            queue, rows = destination_batches(home_university, account, batch_size, expected_snapshot)
            if not any(row.batch_id == batch_id for row in rows):
                raise HTTPException(404, "找不到目前快照中的生活情報批次。")
            checklist = destinations.build_destination_profile_review_batch_checklist_rows(queue, batch_id=batch_id, batch_size=batch_size)
            return _csv_response(checklist, DESTINATION_CHECKLIST_COLUMNS, f"destination-review-checklist-{batch_id}.csv")

    @app.post("/admin/destination-profile-reviews", response_model=m.DestinationProfileReviewEvent)
    def destination_review(payload: m.DestinationProfileReviewSubmitRequest, request: Request, response: Response):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(destinations.record_destination_profile_review, destination_store, profiles(), payload, reviewer_id=account.id, reviewer_display_name=account.display_name)

    @app.post("/admin/destination-profile-promotions", response_model=m.DestinationProfilePromotionEvent)
    def destination_promotion(payload: m.DestinationProfilePromotionRequest, request: Request, response: Response):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(destinations.promote_destination_profile, destination_store, profiles(), payload, promoted_by_id=account.id, promoted_by_display_name=account.display_name)

    @app.get("/admin/destination-profile-publications", response_model=m.DestinationProfilePublicationHistory)
    def destination_history(request: Request, response: Response, home_university: str | None = Query(None, max_length=200)):
        authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(destinations.build_destination_profile_publication_history, profiles(), destination_store.list_promotion_events(), destination_store.list_rollback_events(), home_university=home_university)

    @app.post("/admin/destination-profile-rollbacks", response_model=m.DestinationProfileRollbackEvent)
    def destination_rollback(payload: m.DestinationProfileRollbackRequest, request: Request, response: Response):
        account = authorize(request, response)
        with lock, local_governance_lock(data_dir):
            return execute(destinations.rollback_destination_profile, destination_store, profiles(), payload, rolled_back_by_id=account.id, rolled_back_by_display_name=account.display_name)


# Exports are checklists, never importable approvals or publication commands.
DISCLAIMER = lambda row: "唯讀分工清單，不能匯入或取代工作台逐頁核對、雙人審查與正式發布。"
COMMON_COLUMNS = [("母校", "home_university"), ("合作校", "school_name"), ("國家", "country")]
WORKFLOW_BATCH_COLUMNS = COMMON_COLUMNS + [
    ("workflow_key", "workflow_key"), ("審查批次", "batch_id"), ("批次工作台路徑", "batch_workbench_path"),
    ("工作台路徑", "workbench_path"), ("規定檢查表路徑", "batch_rule_checklist_path"),
    ("審查內容指紋", "review_content_fingerprint"), ("快照指紋", "snapshot_fingerprint"),
    ("批次筆數", "batch_workflow_count"), ("批次內順序", "batch_position"), ("重要聲明", DISCLAIMER),
]
WORKFLOW_RULE_COLUMNS = COMMON_COLUMNS + [
    ("workflow_key", "workflow_key"), ("審查批次", "batch_id"), ("規定識別", "rule_key"),
    ("規定名稱", "rule_label"), ("規定內容", "rule_detail"), ("官方來源網址", "source_urls"),
    ("來源適用學年度", "source_academic_years"), ("來源查核時間", "source_checked_at"),
    ("審查內容指紋", "review_content_fingerprint"), ("審查者 A", lambda r: ""),
    ("審查者 B", lambda r: ""), ("審查者 A 已核對", lambda r: ""),
    ("審查者 B 已核對", lambda r: ""), ("重要聲明", DISCLAIMER),
]
SOURCE_REPLACEMENT_COLUMNS = COMMON_COLUMNS + [
    ("workflow_key", "workflow_key"), ("原網址", "current_url"), ("候選網址", "candidate_url"),
    ("審查內容指紋", "review_content_fingerprint"), ("工作台路徑", "workbench_path"),
    ("自動研究證據", "automated_evidence"), ("人工檢查事項", "required_human_checks"),
    ("可自動填入", "can_prefill"), ("重要聲明", DISCLAIMER),
    ("可填入待審欄位", "can_prefill"),
    ("傳輸安全狀態", lambda r: {"verified_https": "已確認 HTTPS", "downgrades_to_http": "會轉回 HTTP", "unverified": "尚未核實"}[r["transport_status"]]),
    ("審查者 A", lambda r: ""), ("審查者 B", lambda r: ""),
    ("自動核准", "approvals_created"), ("學生資料已變更", "public_student_data_changed"),
]
SOURCE_EVIDENCE_COLUMNS = COMMON_COLUMNS + [
    ("workflow_key", "workflow_key"), ("來源證據快照指紋", "source_evidence_snapshot_fingerprint"),
    ("官方來源網址", "source_url"), ("關鍵規定數", "critical_rule_reference_count"),
    ("研究狀態", lambda r: "已核對原始來源" if (r.get("research_candidate") or {}).get("research_status") == "verified_exact_source" else "來源待確認"),
    ("候選正式標題", lambda r: (r.get("research_candidate") or {}).get("proposed_title")),
    ("可自動填入", lambda r: False),
    ("自動研究證據", lambda r: (r.get("research_candidate") or {}).get("automated_evidence")),
    ("人工檢查事項", lambda r: (r.get("research_candidate") or {}).get("required_human_checks")),
    ("重要聲明", DISCLAIMER),
]
DESTINATION_COLUMNS = COMMON_COLUMNS + [
    ("城市／校區", "city"), ("目前查核狀態", "coverage_status"), ("審查缺口代碼", "review_gap_codes"),
    ("官方來源網址", "source_urls"), ("官方來源名稱", "source_titles"), ("檔案內容雜湊", "profile_content_hash"),
    ("快照指紋", "snapshot_fingerprint"), ("審查者 A", lambda r: ""), ("審查者 B", lambda r: ""),
    ("重要聲明", DISCLAIMER),
]
DESTINATION_BATCH_COLUMNS = DESTINATION_COLUMNS + [
    ("審查批次", "batch_id"), ("批次工作台路徑", "batch_workbench_path"),
    ("批次檢查表路徑", "batch_checklist_path"), ("審查內容指紋", "review_content_fingerprint"),
    ("生活情報內容指紋", "profile_content_hash"), ("官方來源數", "source_count"),
]
DESTINATION_CHECKLIST_COLUMNS = COMMON_COLUMNS + [
    ("審查批次", "batch_id"), ("項目類型", "item_type"), ("項目識別", "item_key"),
    ("項目名稱", "item_label"), ("候選內容", "candidate_content"), ("官方來源網址", "source_urls"),
    ("檔案內容雜湊", "profile_content_hash"), ("審查內容指紋", "review_content_fingerprint"),
    ("生活情報內容指紋", "profile_content_hash"),
    ("查核項目類型", lambda r: "官方來源" if r["item_type"] == "official_source" else "內容區塊"),
    ("審查者 A", lambda r: ""), ("審查者 B", lambda r: ""),
    ("審查者 A 已核對", lambda r: ""), ("審查者 B 已核對", lambda r: ""), ("重要聲明", DISCLAIMER),
]
