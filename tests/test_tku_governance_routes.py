"""Real admin adapters; only isolated JSONL stores and synthetic identities."""
import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.content_governance import LocalContentGovernanceStore
from exchange_info.models import UserAccount
from exchange_info.repositories import JsonlAccountRepository
from test_notification_changes import session


@pytest.fixture
def governance_client(tmp_path, monkeypatch):
    repository = JsonlAccountRepository(tmp_path / "accounts")
    admin = UserAccount(email="synthetic-admin@example.com", display_name="Synthetic admin")
    outsider = UserAccount(email="synthetic-outsider@example.com", display_name="Synthetic outsider")
    admin_headers = session(repository, admin, "synthetic-governance-admin")
    outsider_headers = session(repository, outsider, "synthetic-governance-outsider")
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", admin.email)
    store = LocalContentGovernanceStore(tmp_path / "content")
    client = TestClient(create_app(tmp_path / "app", account_repository=repository, content_governance_store=store))
    return client, admin_headers, outsider_headers, store


READ_ROUTES = [
    "/admin/content-review", "/admin/session", "/admin/application-workflow-review-backlog",
    "/admin/application-workflow-source-replacement-candidates", "/admin/application-workflow-publications",
    "/admin/application-workflow-release-readiness", "/admin/web-release-readiness",
    "/admin/destination-profile-review-queue", "/admin/destination-profile-publications",
    "/admin/application-workflow-review-batches.csv",
]


@pytest.mark.parametrize("path", READ_ROUTES)
def test_governance_reads_require_actual_admin_and_are_private(governance_client, path):
    client, admin, outsider, _ = governance_client
    assert client.get(path).status_code == 401
    assert client.get(path, headers=outsider).status_code == 403
    response = client.get(path, headers=admin)
    assert response.status_code == 200
    assert "no-store" in response.headers["cache-control"]
    assert "password_hash" not in response.text and "token_hash" not in response.text


def test_readiness_and_exports_do_not_stage_approve_or_publish(governance_client):
    client, admin, _, store = governance_client
    before = (store.list_revisions(), store.load_published_workflows())
    assert client.get("/admin/web-release-readiness", headers=admin).status_code == 200
    assert client.get("/admin/application-workflow-review-batches.csv", headers=admin).status_code == 200
    assert client.get("/admin/application-workflow-source-replacement-candidates", headers=admin).json() == []
    assert (store.list_revisions(), store.load_published_workflows()) == before


def test_stale_workflow_exports_fail_closed_without_mutation(governance_client):
    client, admin, _, store = governance_client
    for path in ("/admin/application-workflow-review-backlog", "/admin/application-workflow-review-batches.csv",
                 "/admin/application-workflow-source-replacement-review-queue.csv"):
        response = client.get(path, headers=admin, params={"expected_snapshot": "0" * 64})
        assert response.status_code == 409
    assert store.list_revisions() == [] and store.load_published_workflows() == []


def test_issue_report_status_filter_excludes_terminal_reports(tmp_path, monkeypatch):
    from test_application_workflow_issue_reports import _session, _workflow, _payload

    app = create_app(tmp_path)
    client = TestClient(app)
    _, student = _session(app, email="filter-student@example.com", has_school=True)
    account, admin = _session(app, email="filter-admin@example.com", has_school=False)
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", account.email)
    created = client.post("/application-workflow-issue-reports", json=_payload(_workflow(client)),
        headers={**student, "X-Content-Report-Mutation-ID": "synthetic-filter-report-create"})
    assert created.status_code == 202
    report_id = created.json()["id"]
    endpoint = "/admin/application-workflow-issue-reports"
    assert [row["id"] for row in client.get(endpoint, headers=admin, params={"status": "pending"}).json()] == [report_id]
    reviewed = client.patch(f"{endpoint}/{report_id}", json={"status": "resolved", "note": "隔離測試核對，實際公開規定保持原狀。"},
        headers={**admin, "X-Content-Report-Mutation-ID": "synthetic-filter-report-review"})
    assert reviewed.status_code == 200
    assert client.get(endpoint, headers=admin, params={"status": "pending"}).json() == []
    assert client.get(endpoint, headers=admin, params={"status": "dismissed"}).json() == []
    assert client.get(endpoint, headers=admin, params={"status": "resolved"}).json()[0]["id"] == report_id
    assert len(client.get(endpoint, headers=admin).json()) == 1
    assert client.get(endpoint, headers=admin, params={"status": "invalid"}).status_code == 422


WRITE_REQUESTS = [
    ("post", "/admin/application-workflow-review-backlog/synthetic-missing/stage", None),
    ("post", "/admin/application-workflow-review-batches/synthetic-missing/stage",
        {"expected_snapshot":"0"*64,"batch_size":1}),
    ("patch", "/admin/application-workflow-revisions/synthetic-missing/applicability",
        {"expected_content_hash":"0"*64,"academic_year":"117","note":"Synthetic scoped applicability edit"}),
    ("post", "/admin/application-workflow-revisions/synthetic-missing/approve",
        {"expected_content_hash":"0"*64,"reviewed_source_urls":["https://synthetic.edu/exchange"],
            "reviewed_rule_keys":["synthetic-rule"],"note":"Synthetic full independent attestation"}),
    ("post", "/admin/application-workflow-revisions/synthetic-missing/publish", {"note":"Synthetic explicit publication"}),
    ("post", "/admin/application-workflow-revisions/synthetic-missing/reject", {"note":"Synthetic request for correction"}),
    ("post", "/admin/application-workflow-rollbacks", {"workflow_key":"synthetic-missing",
        "expected_current_revision_id":"synthetic-current","expected_current_version":2,
        "expected_current_content_hash":"0"*64,"restore_revision_id":"synthetic-older","note":"Synthetic scoped restoration"}),
    ("post", "/admin/destination-profile-reviews", {"home_university":"Synthetic home","school_name":"Synthetic host",
        "expected_snapshot":"0"*64,"expected_profile_content_hash":"0"*64,"decision":"approve",
        "reviewed_source_urls":["https://synthetic.edu/exchange"],"reviewed_section_keys":["synthetic-section"],
        "note":"Synthetic full independent destination attestation"}),
    ("post", "/admin/destination-profile-promotions", {"home_university":"Synthetic home","school_name":"Synthetic host",
        "expected_snapshot":"0"*64,"expected_profile_content_hash":"0"*64,"note":"Synthetic explicit audited promotion"}),
    ("post", "/admin/destination-profile-rollbacks", {"home_university":"Synthetic home","school_name":"Synthetic host",
        "expected_active_promotion_event_id":"synthetic-active","expected_latest_publication_event_id":"synthetic-active",
        "expected_public_profile_content_hash":"0"*64,"note":"Synthetic explicit audited restoration"}),
]


@pytest.mark.parametrize("method,path,payload", WRITE_REQUESTS)
def test_every_governance_write_requires_actual_admin_before_mutation(governance_client, method, path, payload):
    client, admin, outsider, store = governance_client
    before = store.command_snapshot()
    assert getattr(client, method)(path, json=payload).status_code == 401
    assert getattr(client, method)(path, json=payload, headers=outsider).status_code == 403
    # The actual admin reaches lookup/snapshot guards with a valid request;
    # a schema422 would conceal an untested authorization boundary.
    authorized = getattr(client, method)(path, json=payload, headers=admin)
    assert authorized.status_code in {404,409}, authorized.text
    assert store.command_snapshot() == before
