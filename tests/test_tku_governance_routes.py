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
