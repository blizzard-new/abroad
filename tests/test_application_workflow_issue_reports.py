from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from exchange_info.api import create_app
from exchange_info.models import (
    AccountSessionRecord,
    ApplicationWorkflowIssueCategory,
    ApplicationWorkflowIssueReport,
    ApplicationWorkflowIssueReportCreate,
    ApplicationWorkflowIssueReportReview,
    ApplicationWorkflowIssueReportStatus,
    StudentVerificationMethod,
    UserAccount,
    utc_now,
)
from exchange_info.workflow_issue_reports import (
    JsonlWorkflowIssueReportRepository,
    SupabaseWorkflowIssueReportRepository,
    WorkflowIssueReportRepositoryError,
    WorkflowIssueReportReviewMutation,
    WorkflowIssueReportSubmitMutation,
    create_workflow_issue_report_repository,
)


LINCOLN = "林肯大學 Lincoln University"


def _session(
    app,
    *,
    email: str,
    verified_student: bool,
    display_name: str = "流程回報測試學生",
) -> tuple[UserAccount, dict[str, str]]:
    account = UserAccount(
        email=email,
        email_verified=True,
        display_name=display_name,
        student_status_verified=verified_student,
        verified_university="長庚大學" if verified_student else None,
        student_verification_method=(
            StudentVerificationMethod.STUDENT_CARD if verified_student else None
        ),
        student_verified_at=utc_now() if verified_student else None,
    )
    token = f"issue-report-token-{account.id}"
    app.state.account_repository.save_account(account)
    app.state.account_repository.save_session(
        AccountSessionRecord(
            account_id=account.id,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            expires_at=utc_now() + timedelta(hours=1),
        )
    )
    return account, {"Authorization": f"Bearer {token}"}


def _workflow(client: TestClient) -> dict:
    response = client.get(
        "/application-workflow",
        params={"school": LINCOLN, "home_school": "長庚大學"},
    )
    assert response.status_code == 200
    workflow = response.json()
    assert workflow["workflow_id"]
    assert workflow["steps"][0]["rule_id"]
    return workflow


def _payload(workflow: dict, **updates) -> dict:
    payload = {
        "home_school": workflow["home_university"],
        "school_name": workflow["school_name"],
        "workflow_id": workflow["workflow_id"],
        "workflow_version": workflow["version"],
        "workflow_snapshot": workflow["issue_report_snapshot"],
        "step_rule_id": workflow["steps"][0]["rule_id"],
        "category": "deadline",
        "description": "官方公告顯示這一步的截止日期與目前頁面不同，請協助重新核對。",
        "official_source_url": "https://www.lincoln.ac.nz/study/apply/official-deadline/",
    }
    payload.update(updates)
    return payload


@pytest.mark.parametrize(
    "source_url",
    [
        "http://official.example.edu/rules",
        "https://student:secret@official.example.edu/rules",
        "https://localhost/rules",
        "https://127.0.0.1/rules",
        "https://224.0.0.1/rules",
        "https://240.0.0.1/rules",
        "https://192.0.2.1/rules",
        "https://198.51.100.1/rules",
        "https://203.0.113.1/rules",
    ],
)
def test_issue_report_model_rejects_unsafe_official_source_urls(source_url: str) -> None:
    with pytest.raises(ValidationError, match="官方來源"):
        ApplicationWorkflowIssueReportCreate(
            home_school="長庚大學",
            school_name=LINCOLN,
            workflow_id="workflow-12345678",
            workflow_version=1,
            workflow_snapshot="0" * 64,
            category=ApplicationWorkflowIssueCategory.DEADLINE,
            description="官方公告顯示截止日期不同，請協助重新核對目前整理內容。",
            official_source_url=source_url,
        )


def test_only_verified_students_can_submit_without_mutating_formal_content(
    tmp_path: Path,
) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    workflow = _workflow(client)
    payload = _payload(workflow)
    revisions_before = app.state.content_governance_store.list_revisions()
    published_before = [
        row.model_dump(mode="json")
        for row in app.state.content_governance_store.load_published_workflows()
    ]

    guest = client.post(
        "/application-workflow-issue-reports",
        headers={"X-Content-Report-Mutation-ID": "guest-report-mutation-0001"},
        json=payload,
    )
    _, unverified_headers = _session(
        app,
        email="unverified-report@example.com",
        verified_student=False,
    )
    unverified = client.post(
        "/application-workflow-issue-reports",
        headers={
            **unverified_headers,
            "X-Content-Report-Mutation-ID": "unverified-report-mutation-0001",
        },
        json=payload,
    )
    _, verified_headers = _session(
        app,
        email="verified-report@example.com",
        verified_student=True,
    )
    accepted = client.post(
        "/application-workflow-issue-reports",
        headers={
            **verified_headers,
            "X-Content-Report-Mutation-ID": "verified-report-mutation-0001",
        },
        json=payload,
    )

    assert guest.status_code == 401
    assert unverified.status_code == 403
    assert accepted.status_code == 202
    assert accepted.headers["X-Idempotent-Replay"] == "false"
    report = accepted.json()
    assert report["status"] == ApplicationWorkflowIssueReportStatus.PENDING.value
    assert report["workflow_key"]
    assert report["workflow_id"] == workflow["workflow_id"]
    assert report["workflow_version"] == workflow["version"]
    assert report["workflow_snapshot"] == workflow["issue_report_snapshot"]
    assert report["step_rule_id"] == workflow["steps"][0]["rule_id"]
    assert report["step_title"] == workflow["steps"][0]["title"]
    assert "reporter_account_id" not in report
    assert "mutation_id" not in report
    assert app.state.content_governance_store.list_revisions() == revisions_before
    assert [
        row.model_dump(mode="json")
        for row in app.state.content_governance_store.load_published_workflows()
    ] == published_before


def test_submit_is_idempotent_and_rejects_target_or_payload_tampering(
    tmp_path: Path,
) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    workflow = _workflow(client)
    _, headers = _session(
        app,
        email="idempotent-report@example.com",
        verified_student=True,
    )
    mutation_headers = {
        **headers,
        "X-Content-Report-Mutation-ID": "workflow-report-idempotency-0001",
    }

    created = client.post(
        "/application-workflow-issue-reports",
        headers=mutation_headers,
        json=_payload(workflow),
    )
    replayed = client.post(
        "/application-workflow-issue-reports",
        headers=mutation_headers,
        json=_payload(workflow),
    )
    conflict = client.post(
        "/application-workflow-issue-reports",
        headers=mutation_headers,
        json=_payload(workflow, description="同一操作識別碼改成另一份說明，必須拒絕。"),
    )
    wrong_version = client.post(
        "/application-workflow-issue-reports",
        headers={
            **headers,
            "X-Content-Report-Mutation-ID": "workflow-report-version-0001",
        },
        json=_payload(workflow, workflow_version=workflow["version"] + 1),
    )
    wrong_step = client.post(
        "/application-workflow-issue-reports",
        headers={
            **headers,
            "X-Content-Report-Mutation-ID": "workflow-report-step-0001",
        },
        json=_payload(workflow, step_rule_id="not-a-real-rule"),
    )

    assert created.status_code == 202
    assert replayed.status_code == 202
    assert replayed.headers["X-Idempotent-Replay"] == "true"
    assert replayed.json()["id"] == created.json()["id"]
    assert conflict.status_code == 409
    assert wrong_version.status_code == 409
    assert wrong_step.status_code == 422
    assert len(app.state.workflow_issue_report_repository.list_reports()) == 1


def test_report_rejects_contact_details_and_rate_limits_new_submissions(
    tmp_path: Path,
) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    workflow = _workflow(client)
    _, headers = _session(
        app,
        email="rate-limit-report@example.com",
        verified_student=True,
    )

    sensitive = client.post(
        "/application-workflow-issue-reports",
        headers={
            **headers,
            "X-Content-Report-Mutation-ID": "workflow-report-sensitive-0001",
        },
        json=_payload(
            workflow,
            description="請聯絡我 student@example.com，我發現官方公告日期不同。",
        ),
    )
    responses = [
        client.post(
            "/application-workflow-issue-reports",
            headers={
                **headers,
                "X-Content-Report-Mutation-ID": f"workflow-report-rate-{index:04d}",
            },
            json=_payload(
                workflow,
                description=f"官方公告第 {index} 處與頁面不同，請協助人工核對內容。",
            ),
        )
        for index in range(1, 12)
    ]

    assert sensitive.status_code == 422
    assert [response.status_code for response in responses[:10]] == [202] * 10
    assert responses[10].status_code == 429
    assert responses[10].headers["Retry-After"] == "3600"


def test_admin_queue_and_terminal_review_are_protected_and_append_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    workflow = _workflow(client)
    _, student_headers = _session(
        app,
        email="student-report-queue@example.com",
        verified_student=True,
    )
    admin, admin_headers = _session(
        app,
        email="content-admin-report@example.com",
        verified_student=False,
        display_name="內容管理員",
    )
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", admin.email or "")

    created = client.post(
        "/application-workflow-issue-reports",
        headers={
            **student_headers,
            "X-Content-Report-Mutation-ID": "workflow-report-review-target-0001",
        },
        json=_payload(workflow),
    )
    assert created.status_code == 202
    report_id = created.json()["id"]

    assert client.get("/admin/application-workflow-issue-reports").status_code == 401
    assert (
        client.get(
            "/admin/application-workflow-issue-reports",
            headers=student_headers,
        ).status_code
        == 403
    )
    queue = client.get(
        "/admin/application-workflow-issue-reports",
        headers=admin_headers,
    )
    assert queue.status_code == 200
    assert queue.headers["Cache-Control"] == "no-store"
    assert [row["id"] for row in queue.json()] == [report_id]
    assert "reporter_account_id" not in queue.json()[0]

    review_headers = {
        **admin_headers,
        "X-Content-Report-Mutation-ID": "workflow-report-review-0001",
    }
    reviewed = client.patch(
        f"/admin/application-workflow-issue-reports/{report_id}",
        headers=review_headers,
        json={
            "status": "resolved",
            "note": "已核對學生提供的官方來源；後續另走正式 revision 與雙審流程。",
        },
    )
    replayed = client.patch(
        f"/admin/application-workflow-issue-reports/{report_id}",
        headers=review_headers,
        json={
            "status": "resolved",
            "note": "已核對學生提供的官方來源；後續另走正式 revision 與雙審流程。",
        },
    )
    conflicting = client.patch(
        f"/admin/application-workflow-issue-reports/{report_id}",
        headers={
            **admin_headers,
            "X-Content-Report-Mutation-ID": "workflow-report-review-0002",
        },
        json={"status": "dismissed", "note": "不能覆寫已完成的審查結果。"},
    )

    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "resolved"
    assert reviewed.json()["review"]["reviewer_display_name"] == "內容管理員"
    assert replayed.status_code == 200
    assert replayed.headers["X-Idempotent-Replay"] == "true"
    assert conflicting.status_code == 409
    assert len(app.state.workflow_issue_report_repository.list_reviews()) == 1
    assert app.state.content_governance_store.list_revisions() == []


def test_local_account_deletion_deidentifies_reporter_without_deleting_report(
    tmp_path: Path,
) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    workflow = _workflow(client)
    account, headers = _session(
        app,
        email="delete-report-owner@example.com",
        verified_student=True,
    )
    created = client.post(
        "/application-workflow-issue-reports",
        headers={
            **headers,
            "X-Content-Report-Mutation-ID": "workflow-report-delete-owner-0001",
        },
        json=_payload(workflow),
    )
    assert created.status_code == 202

    deleted = client.delete("/auth/me", headers=headers)

    assert deleted.status_code == 204
    records = app.state.workflow_issue_report_repository.list_records()
    assert len(records) == 1
    assert records[0].reporter_account_id is None
    assert records[0].reporter_deleted_at is not None
    assert account.id not in (tmp_path / "processed" / "application_workflow_issue_reports.jsonl").read_text(encoding="utf-8")


def test_account_export_includes_only_public_issue_report_fields(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    workflow = _workflow(client)
    _, headers = _session(
        app,
        email="export-report-owner@example.com",
        verified_student=True,
    )
    created = client.post(
        "/application-workflow-issue-reports",
        headers={
            **headers,
            "X-Content-Report-Mutation-ID": "workflow-report-export-owner-0001",
        },
        json=_payload(workflow),
    )
    assert created.status_code == 202

    exported = client.get("/auth/me/export", headers=headers)

    assert exported.status_code == 200
    reports = exported.json()["application_workflow_issue_reports"]
    assert [row["id"] for row in reports] == [created.json()["id"]]
    assert "reporter_account_id" not in reports[0]
    assert "mutation_id" not in reports[0]
    assert "request_fingerprint" not in reports[0]


def test_local_account_deletion_removes_closed_report(tmp_path: Path, monkeypatch) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    workflow = _workflow(client)
    _, student_headers = _session(
        app,
        email="closed-report-owner@example.com",
        verified_student=True,
    )
    admin, admin_headers = _session(
        app,
        email="closed-report-admin@example.com",
        verified_student=False,
    )
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", admin.email or "")
    created = client.post(
        "/application-workflow-issue-reports",
        headers={
            **student_headers,
            "X-Content-Report-Mutation-ID": "workflow-report-closed-owner-0001",
        },
        json=_payload(workflow),
    )
    reviewed = client.patch(
        f"/admin/application-workflow-issue-reports/{created.json()['id']}",
        headers={
            **admin_headers,
            "X-Content-Report-Mutation-ID": "workflow-report-closed-review-0001",
        },
        json={
            "status": "resolved",
            "note": "已核對官方來源，正式內容仍須另走 revision 與雙人審查。",
        },
    )
    assert reviewed.status_code == 200

    deleted = client.delete("/auth/me", headers=student_headers)

    assert deleted.status_code == 204
    assert app.state.workflow_issue_report_repository.list_records() == []


def test_review_of_deidentified_pending_report_is_replayable_during_cleanup_grace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    workflow = _workflow(client)
    _, student_headers = _session(
        app,
        email="deleted-pending-report-owner@example.com",
        verified_student=True,
    )
    admin, admin_headers = _session(
        app,
        email="deleted-pending-report-admin@example.com",
        verified_student=False,
        display_name="回報核對管理員",
    )
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", admin.email or "")
    created = client.post(
        "/application-workflow-issue-reports",
        headers={
            **student_headers,
            "X-Content-Report-Mutation-ID": "deleted-pending-report-submit-0001",
        },
        json=_payload(workflow),
    )
    assert created.status_code == 202
    assert client.delete("/auth/me", headers=student_headers).status_code == 204

    review_headers = {
        **admin_headers,
        "X-Content-Report-Mutation-ID": "deleted-pending-report-review-0001",
    }
    review_body = {
        "status": "resolved",
        "note": "已核對官方來源；去識別回報只短暫保留以支援結果不明時安全重送。",
    }
    reviewed = client.patch(
        f"/admin/application-workflow-issue-reports/{created.json()['id']}",
        headers=review_headers,
        json=review_body,
    )
    replayed = client.patch(
        f"/admin/application-workflow-issue-reports/{created.json()['id']}",
        headers=review_headers,
        json=review_body,
    )

    assert reviewed.status_code == 200
    assert replayed.status_code == 200
    assert replayed.headers["X-Idempotent-Replay"] == "true"
    assert replayed.json() == reviewed.json()
    record = app.state.workflow_issue_report_repository.list_records()[0]
    assert record.reporter_account_id is None
    assert record.report.status == ApplicationWorkflowIssueReportStatus.RESOLVED
    assert record.retained_until is not None
    assert timedelta(hours=23, minutes=59) <= (
        record.retained_until - record.report.updated_at
    ) <= timedelta(hours=24)


def test_reviewer_account_deletion_removes_reviewer_identity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    workflow = _workflow(client)
    _, student_headers = _session(
        app,
        email="reviewer-delete-student@example.com",
        verified_student=True,
    )
    admin, admin_headers = _session(
        app,
        email="reviewer-delete-admin@example.com",
        verified_student=False,
        display_name="應被去識別的管理員",
    )
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", admin.email or "")
    created = client.post(
        "/application-workflow-issue-reports",
        headers={
            **student_headers,
            "X-Content-Report-Mutation-ID": "workflow-report-reviewer-delete-target",
        },
        json=_payload(workflow),
    )
    review_mutation_id = "workflow-report-reviewer-delete-review"
    reviewed = client.patch(
        f"/admin/application-workflow-issue-reports/{created.json()['id']}",
        headers={
            **admin_headers,
            "X-Content-Report-Mutation-ID": review_mutation_id,
        },
        json={
            "status": "dismissed",
            "note": "官方來源與目前內容一致，因此結束此回報且不修改正式資料。",
        },
    )
    assert reviewed.status_code == 200

    deleted = client.delete("/auth/me", headers=admin_headers)

    assert deleted.status_code == 204
    record = app.state.workflow_issue_report_repository.list_records()[0]
    assert record.review_record is not None
    assert record.review_record.reviewer_account_id is None
    assert record.review_record.review.reviewer_display_name == "已刪除管理員"
    raw = (tmp_path / "processed" / "application_workflow_issue_reports.jsonl").read_text(
        encoding="utf-8"
    )
    assert admin.id not in raw
    assert "應被去識別的管理員" not in raw
    assert review_mutation_id not in raw


def test_local_repository_owns_status_timestamps_and_physically_purges_expiry(
    tmp_path: Path,
) -> None:
    current = [datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)]
    repository = JsonlWorkflowIssueReportRepository(
        tmp_path,
        clock=lambda: current[0],
    )
    malicious_review = ApplicationWorkflowIssueReportReview(
        report_id="malicious-report-id",
        status=ApplicationWorkflowIssueReportStatus.RESOLVED,
        note="這筆內部測試刻意帶入不應被 repository 接受的終態審查。",
        reviewer_display_name="偽造審查者",
    )
    report = ApplicationWorkflowIssueReport(
        id="malicious-report-id",
        workflow_key="workflow-key",
        workflow_id="workflow-12345678",
        workflow_version=1,
        workflow_snapshot="a" * 64,
        home_school="長庚大學",
        school_name=LINCOLN,
        category=ApplicationWorkflowIssueCategory.DEADLINE,
        description="官方公告顯示截止日期不同，請協助重新核對目前整理內容。",
        official_source_url="https://example.edu/official-deadline",
        status=ApplicationWorkflowIssueReportStatus.RESOLVED,
        created_at=current[0] - timedelta(days=30),
        updated_at=current[0] - timedelta(days=30),
        review=malicious_review,
    )
    result = repository.submit_report(
        WorkflowIssueReportSubmitMutation(
            mutation_id="repository-owned-fields-0001",
            account_id="account-12345678",
            request_fingerprint="b" * 64,
            report=report,
        )
    )

    assert result.report is not None
    assert result.report.status == ApplicationWorkflowIssueReportStatus.PENDING
    assert result.report.created_at == current[0]
    assert result.report.updated_at == current[0]
    assert result.report.review is None

    repository.deidentify_reporter("account-12345678")
    retained = repository.list_records()[0]
    assert retained.retained_until == current[0] + timedelta(days=90)
    current[0] += timedelta(days=91)

    assert repository.list_records() == []
    assert repository.path.read_text(encoding="utf-8") == ""


class _WorkflowIssueFakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


class _WorkflowIssueFakeSession:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs) -> _WorkflowIssueFakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self.responses:
            raise AssertionError(f"unexpected request: {method} {url}")
        return _WorkflowIssueFakeResponse(self.responses.pop(0))


def test_workflow_issue_repository_factory_rejects_partial_supabase_configuration(
    tmp_path: Path,
) -> None:
    with pytest.raises(WorkflowIssueReportRepositoryError, match="必須同時設定"):
        create_workflow_issue_report_repository(
            tmp_path,
            {"EXCHANGE_SUPABASE_URL": "https://project.supabase.co"},
        )


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"status": "committed"},
        {"status": "not-a-real-status"},
    ],
)
def test_supabase_repository_rejects_malformed_mutation_responses(payload: object) -> None:
    session = _WorkflowIssueFakeSession([payload])
    repository = SupabaseWorkflowIssueReportRepository(
        "https://project.supabase.co",
        "server-secret",
        request_func=session.request,
    )
    report = ApplicationWorkflowIssueReport(
        id="client-report-id",
        workflow_key="長庚大學::林肯大學",
        workflow_id="workflow-12345678",
        workflow_version=1,
        workflow_snapshot="a" * 64,
        home_school="長庚大學",
        school_name=LINCOLN,
        category=ApplicationWorkflowIssueCategory.DEADLINE,
        description="官方公告顯示截止日期不同，請重新核對目前學生看到的內容。",
        official_source_url="https://example.edu/official-deadline",
    )

    with pytest.raises(WorkflowIssueReportRepositoryError, match="回應格式"):
        repository.submit_report(
            WorkflowIssueReportSubmitMutation(
                mutation_id="malformed-response-submit-0001",
                account_id="account-12345678",
                request_fingerprint="b" * 64,
                report=report,
            )
        )


def test_supabase_repository_sends_only_fingerprinted_fields_and_reads_one_snapshot() -> None:
    created_at = datetime(2026, 8, 31, 1, 0, tzinfo=timezone.utc)
    report = ApplicationWorkflowIssueReport(
        id="client-must-not-control-this-id",
        workflow_key="長庚大學::林肯大學",
        workflow_id="workflow-12345678",
        workflow_version=2,
        workflow_snapshot="a" * 64,
        home_school="長庚大學",
        school_name=LINCOLN,
        step_rule_id="rule-deadline",
        step_title="繳交校內申請",
        college="管理學院",
        department="工商管理學系",
        academic_year="2026-2027",
        application_round="秋季班",
        category=ApplicationWorkflowIssueCategory.DEADLINE,
        description="官方公告顯示截止日期不同，請重新核對目前學生看到的內容。",
        official_source_url="https://example.edu/official-deadline",
        status=ApplicationWorkflowIssueReportStatus.RESOLVED,
        created_at=created_at - timedelta(days=3),
        updated_at=created_at - timedelta(days=2),
    )
    fingerprint = "b" * 64
    report_row = {
        **report.model_dump(
            mode="json",
            exclude={"review", "id", "status", "created_at", "updated_at"},
        ),
        "id": "server-report-id",
        "status": "pending",
        "reporter_account_id": "account-12345678",
        "mutation_id": "workflow-report-submit-0001",
        "request_fingerprint": fingerprint,
        "created_at": created_at.isoformat(),
        "updated_at": created_at.isoformat(),
        "reporter_deleted_at": None,
        "retained_until": None,
    }
    review_fingerprint = "c" * 64
    review_row = {
        "id": "server-review-id",
        "report_id": "server-report-id",
        "status": "resolved",
        "note": "已逐頁核對官方公告，回報成立；正式資料仍須另走雙人審查。",
        "reviewer_account_id": "admin-12345678",
        "reviewer_display_name": "內容管理員",
        "mutation_id": "workflow-report-review-0001",
        "request_fingerprint": review_fingerprint,
        "reviewed_at": (created_at + timedelta(hours=1)).isoformat(),
    }
    reviewed_report_row = {
        **report_row,
        "status": "resolved",
        "updated_at": (created_at + timedelta(hours=1)).isoformat(),
    }
    embedded_row = {**reviewed_report_row, "review": [review_row]}
    session = _WorkflowIssueFakeSession(
        [
            {"status": "committed", "report": report_row, "idempotent": False},
            {
                "status": "committed",
                "report": reviewed_report_row,
                "review": review_row,
                "idempotent": False,
            },
            {"status": "committed", "purged_count": 0},
            [embedded_row],
        ]
    )
    repository = SupabaseWorkflowIssueReportRepository(
        "https://project.supabase.co",
        "server-secret",
        request_func=session.request,
    )

    submitted = repository.submit_report(
        WorkflowIssueReportSubmitMutation(
            mutation_id="workflow-report-submit-0001",
            account_id="account-12345678",
            request_fingerprint=fingerprint,
            report=report,
        )
    )
    reviewed = repository.review_report(
        WorkflowIssueReportReviewMutation(
            mutation_id="workflow-report-review-0001",
            reviewer_account_id="admin-12345678",
            request_fingerprint=review_fingerprint,
            review=ApplicationWorkflowIssueReportReview(
                report_id="server-report-id",
                status=ApplicationWorkflowIssueReportStatus.RESOLVED,
                note=review_row["note"],
                reviewer_display_name="不應由 client 控制",
            ),
        )
    )
    rows = repository.list_reports(ApplicationWorkflowIssueReportStatus.RESOLVED)

    assert submitted.report is not None and submitted.report.id == "server-report-id"
    assert reviewed.report is not None and reviewed.report.review is not None
    assert rows[0].review is not None and rows[0].review.id == "server-review-id"
    submit_payload = session.calls[0]["json"]
    assert isinstance(submit_payload, dict)
    assert set(submit_payload["p_report"]) == {
        "workflow_key",
        "workflow_id",
        "workflow_version",
        "workflow_snapshot",
        "home_school",
        "school_name",
        "step_rule_id",
        "step_title",
        "college",
        "department",
        "academic_year",
        "application_round",
        "category",
        "description",
        "official_source_url",
    }
    review_payload = session.calls[1]["json"]
    assert isinstance(review_payload, dict)
    assert review_payload["p_review"] == {
        "report_id": "server-report-id",
        "status": "resolved",
        "note": review_row["note"],
    }
    get_call = session.calls[3]
    assert get_call["method"] == "GET"
    assert get_call["params"]["select"] == (
        "*,review:application_workflow_issue_report_reviews(*)"
    )
    assert get_call["params"]["status"] == "eq.resolved"
