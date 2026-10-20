from __future__ import annotations

import base64
import hashlib
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import PRODUCTION_PERSISTENCE_BACKENDS, create_app
from exchange_info.document_vault import create_document_vault_service
from exchange_info.email_verification import create_email_verification_service
from exchange_info.form_drafts import create_form_draft_service
from exchange_info.models import (
    AccountApplicationWorkspace,
    AccountSessionRecord,
    ApplicationCenterContext,
    UserAccount,
    utc_now,
)
from exchange_info.repositories import (
    AccountDeletionMutationRequest,
    AccountDeletionMutationStatus,
    AccountRepositoryError,
    JsonlAccountRepository,
    SupabaseAccountRepository,
    WorkspaceMutationKind,
    WorkspaceMutationRequest,
    WorkspaceMutationStatus,
    create_account_repository,
)
from exchange_info.transient_auth import LocalTransientAuthStore


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload
        self.content = b"[]" if not payload else b"[{...}]"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class _FakeSession:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self.responses:
            raise AssertionError(f"Unexpected repository request: {method} {url}")
        return _FakeResponse(self.responses.pop(0))


def _workspace() -> AccountApplicationWorkspace:
    return AccountApplicationWorkspace(
        home_school="長庚大學",
        favorite_schools=["林肯大學 Lincoln University"],
        application_context=ApplicationCenterContext(school_name="長庚大學"),
    )


def test_jsonl_repository_remains_an_explicit_local_fallback(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    account = UserAccount(display_name="本機測試", application_workspaces=[_workspace()])
    session = AccountSessionRecord(
        account_id=account.id,
        token_hash="token-hash",
        expires_at=utc_now() + timedelta(days=1),
    )

    repository.save_account(account)
    repository.save_session(session)

    assert repository.find_account_by_id(account.id) == account
    assert repository.find_account_by_email("missing@example.com") is None
    assert repository.find_session_by_token_hash("token-hash") == session
    assert repository.authenticate_by_token_hash("token-hash") == (account, session)
    assert repository.purge_expired_sessions(utc_now()) == 0

    repository.delete_account(account.id)
    assert repository.find_account_by_id(account.id) is None
    assert repository.find_session_by_token_hash("token-hash") is None


def test_supabase_authentication_is_one_consistent_rpc_snapshot() -> None:
    workspace = _workspace().model_copy(update={"revision": 7})
    account = UserAccount(display_name="容量測試")
    session = AccountSessionRecord(
        account_id=account.id,
        token_hash="a" * 64,
        expires_at=utc_now() + timedelta(days=1),
    )
    fake = _FakeSession([
        {
            "status": "valid",
            "session": session.model_dump(mode="json"),
            "account": {
                "id": account.id,
                "email": account.email,
                "profile": account.model_dump(
                    mode="json",
                    exclude={"application_workspaces", "community_suspended_until"},
                ),
                "community_suspended_until": None,
                "created_at": account.created_at.isoformat(),
                "updated_at": account.updated_at.isoformat(),
                "workspaces": [{
                    "workspace": workspace.model_dump(mode="json"),
                    "revision": workspace.revision,
                }],
            },
        }
    ])
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "sb_secret_test-only",
        request_session=fake,
    )

    authenticated = repository.authenticate_by_token_hash("a" * 64)

    assert authenticated is not None
    restored, restored_session = authenticated
    assert restored_session == session
    assert restored.application_workspaces == [workspace]
    assert len(fake.calls) == 1
    assert fake.calls[0]["method"] == "POST"
    assert fake.calls[0]["url"].endswith("/rpc/exchange_authenticate_account")
    assert fake.calls[0]["json"] == {"p_token_hash": "a" * 64}


def test_repository_factory_fails_closed_in_production_without_supabase(tmp_path) -> None:
    with pytest.raises(AccountRepositoryError, match="正式環境禁止使用 JSONL"):
        create_account_repository(
            tmp_path,
            {
                "EXCHANGE_ENVIRONMENT": "production",
                "EXCHANGE_ACCOUNT_REPOSITORY": "auto",
            },
        )

    with pytest.raises(AccountRepositoryError, match="正式環境禁止使用 JSONL"):
        create_account_repository(
            tmp_path,
            {
                "EXCHANGE_ENVIRONMENT": "production",
                "EXCHANGE_ACCOUNT_REPOSITORY": "jsonl",
                "EXCHANGE_SUPABASE_URL": "https://project.supabase.co",
                "EXCHANGE_SUPABASE_SECRET_KEY": "server-secret",
            },
        )

    legacy = create_account_repository(
        tmp_path,
        {
            "EXCHANGE_ACCOUNT_REPOSITORY": "supabase",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "legacy-server-key",
        },
    )
    assert legacy.backend_name == "supabase"

    with pytest.raises(AccountRepositoryError, match="必須同時設定"):
        create_account_repository(
            tmp_path,
            {
                "EXCHANGE_SUPABASE_URL": "https://project.supabase.co",
            },
        )


def test_create_app_rejects_injected_local_backends_in_production(
    tmp_path,
    monkeypatch,
) -> None:
    local_environment = {"EXCHANGE_ENVIRONMENT": "development"}
    accounts = JsonlAccountRepository(tmp_path / "accounts")
    vault = create_document_vault_service(
        tmp_path / "vault",
        environ=local_environment,
    )
    drafts = create_form_draft_service(
        tmp_path / "drafts",
        vault.master_key,
        environ=local_environment,
    )
    email = create_email_verification_service(
        accounts,
        tmp_path / "email",
        environ=local_environment,
    )
    monkeypatch.setenv("EXCHANGE_ENVIRONMENT", "production")
    monkeypatch.delenv("EXCHANGE_SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("EXCHANGE_SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    with pytest.raises(RuntimeError, match="正式環境禁止使用本機持久層"):
        create_app(
            tmp_path / "app",
            account_repository=accounts,
            document_vault_service=vault,
            form_draft_service=drafts,
            email_verification_service=email,
            transient_auth_store=LocalTransientAuthStore(),
        )


def test_create_app_accepts_complete_supabase_production_configuration(
    tmp_path,
    monkeypatch,
) -> None:
    master_key = base64.urlsafe_b64encode(b"v" * 32).decode("ascii")
    email_secret = base64.urlsafe_b64encode(b"e" * 32).decode("ascii")
    monkeypatch.setenv("EXCHANGE_ENVIRONMENT", "production")
    monkeypatch.setenv("EXCHANGE_SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("EXCHANGE_SUPABASE_SECRET_KEY", "server-secret")
    monkeypatch.setenv("EXCHANGE_ACCOUNT_REPOSITORY", "supabase")
    monkeypatch.setenv("EXCHANGE_VAULT_BACKEND", "supabase")
    monkeypatch.setenv("EXCHANGE_FORM_DRAFT_BACKEND", "supabase")
    monkeypatch.setenv("EXCHANGE_VAULT_MASTER_KEY", master_key)
    monkeypatch.setenv("EXCHANGE_EMAIL_VERIFICATION_SECRET", email_secret)
    monkeypatch.setenv("EXCHANGE_EMAIL_VERIFICATION_BACKEND", "disabled")

    app = create_app(tmp_path)

    assert app.state.persistence_backends == PRODUCTION_PERSISTENCE_BACKENDS


def test_supabase_repository_keeps_secret_server_side_and_uses_atomic_workspace_rpc() -> None:
    workspace = _workspace()
    committed_workspace = workspace.model_copy(update={"revision": 1})
    account = UserAccount(display_name="雲端測試")
    fake = _FakeSession(
        [
            [
                {
                    "id": account.id,
                    "email": account.email,
                    "profile": account.model_dump(
                        mode="json",
                        exclude={"application_workspaces"},
                    ),
                    "created_at": account.created_at.isoformat(),
                    "updated_at": account.updated_at.isoformat(),
                }
            ],
            {
                "status": "committed",
                "workspace": committed_workspace.model_dump(mode="json"),
            },
        ]
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "sb_secret_test-only",
        request_session=fake,
    )

    repository.create_account(account)
    result = repository.commit_workspace(
        WorkspaceMutationRequest(
            account_id=account.id,
            expected_revision=0,
            workspace=workspace,
            mutation_kind=WorkspaceMutationKind.WORKSPACE_REPLACE,
        )
    )

    assert result.status == WorkspaceMutationStatus.COMMITTED
    assert result.workspace == committed_workspace
    assert len(fake.calls) == 2
    account_call, workspace_call = fake.calls
    assert account_call["url"].endswith("/rest/v1/exchange_accounts")
    assert account_call["headers"]["apikey"] == "sb_secret_test-only"
    assert "Authorization" not in account_call["headers"], "an sb_secret key is not a JWT, so it goes in apikey only"
    assert "application_workspaces" not in account_call["json"]["profile"]
    assert "community_suspended_until" not in account_call["json"]["profile"]
    assert workspace_call["method"] == "POST"
    assert workspace_call["url"].endswith(
        "/rest/v1/rpc/exchange_commit_account_workspace"
    )
    assert workspace_call["json"] == {
        "p_account_id": account.id,
        "p_home_school_key": "長庚大學",
        "p_expected_revision": 0,
        "p_candidate_workspace": workspace.model_dump(mode="json"),
        "p_mutation_kind": "workspace_replace",
        "p_progress_key": None,
        "p_progress": None,
    }
    assert not any(
        call["url"].endswith("/rest/v1/exchange_account_workspaces")
        for call in fake.calls
    )


def test_supabase_account_deletion_uses_rpc_and_acknowledges_storage_cleanup() -> None:
    request = AccountDeletionMutationRequest(
        mutation_id="account-delete-mutation-0001",
        account_id="account-1",
        session_id="session-1",
        session_token_hash="a" * 64,
        email_fingerprint="b" * 64,
    )
    fake = _FakeSession(
        [
            {
                "status": "committed",
                "idempotent": False,
                "storage_object_keys": ["vault/account-1/file.bin"],
                "counts": {"identity": 1, "public_content": 2},
            },
            {"status": "committed"},
        ]
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "sb_secret_test-only",
        request_session=fake,
    )

    result = repository.commit_account_deletion(request)
    completion = repository.complete_account_deletion_storage(
        request.mutation_id,
        request.session_token_hash,
    )

    assert result.status == AccountDeletionMutationStatus.COMMITTED
    assert result.storage_object_keys == ["vault/account-1/file.bin"]
    assert result.counts == {"identity": 1, "public_content": 2}
    assert completion == AccountDeletionMutationStatus.COMMITTED
    deletion_call, completion_call = fake.calls
    assert deletion_call["url"].endswith(
        "/rest/v1/rpc/exchange_commit_account_deletion"
    )
    assert deletion_call["json"]["p_account_id"] == "account-1"
    assert deletion_call["json"]["p_session_id"] == "session-1"
    assert deletion_call["json"]["p_session_token_hash"] == "a" * 64
    assert deletion_call["json"]["p_email_fingerprint"] == "b" * 64
    assert len(deletion_call["json"]["p_request_fingerprint"]) == 64
    assert completion_call["url"].endswith(
        "/rest/v1/rpc/exchange_complete_account_deletion_storage"
    )
    assert completion_call["json"] == {
        "p_mutation_id": request.mutation_id,
        "p_session_token_hash": request.session_token_hash,
    }


def test_supabase_direct_account_delete_is_disabled() -> None:
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "sb_secret_test-only",
        request_session=_FakeSession([]),
    )

    with pytest.raises(AccountRepositoryError, match="原子操作"):
        repository.delete_account("account-1")


def test_supabase_account_deletion_storage_jobs_use_service_rpcs() -> None:
    fake = _FakeSession(
        [
            {
                "status": "committed",
                "jobs": [
                    {
                        "mutation_id": "account-delete-mutation-0002",
                        "storage_object_keys": ["vault/account-2/file.bin"],
                    }
                ],
            },
            {"status": "committed"},
            {"status": "committed", "receipts": 3},
        ]
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "sb_secret_test-only",
        request_session=fake,
    )

    jobs = repository.list_pending_account_deletion_storage(limit=25)
    completed = repository.complete_pending_account_deletion_storage(
        jobs[0].mutation_id
    )
    purged = repository.purge_account_deletion_receipts()

    assert jobs[0].storage_object_keys == ["vault/account-2/file.bin"]
    assert completed == AccountDeletionMutationStatus.COMMITTED
    assert purged == 3
    assert fake.calls[0]["url"].endswith(
        "/rest/v1/rpc/exchange_list_pending_account_deletion_storage"
    )
    assert fake.calls[0]["json"] == {"p_limit": 25}
    assert fake.calls[1]["url"].endswith(
        "/rest/v1/rpc/exchange_complete_pending_account_deletion_storage"
    )
    assert fake.calls[2]["url"].endswith(
        "/rest/v1/rpc/exchange_purge_account_deletion_receipts"
    )


def test_supabase_repository_hydrates_workspace_rows() -> None:
    workspace = _workspace()
    account = UserAccount(display_name="跨裝置測試")
    profile = account.model_dump(mode="json", exclude={"application_workspaces"})
    fake = _FakeSession(
        [
            [{"id": account.id, "email": None, "profile": profile}],
            [
                {
                    "home_school_key": "長庚大學",
                    "workspace": workspace.model_dump(mode="json"),
                }
            ],
        ]
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "sb_secret_test-only",
        request_session=fake,
    )

    restored = repository.find_account_by_id(account.id)

    assert restored is not None
    assert restored.application_workspaces == [workspace]
    assert fake.calls[0]["params"]["id"] == f"eq.{account.id}"
    assert fake.calls[1]["params"]["account_id"] == f"eq.{account.id}"


def test_api_can_use_injected_repository_without_reading_account_jsonl(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path / "repository-data")
    account = UserAccount(display_name="Repository API")
    token = "repository-api-token"
    repository.save_account(account)
    repository.save_session(
        AccountSessionRecord(
            account_id=account.id,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            expires_at=utc_now() + timedelta(days=1),
        )
    )
    app = create_app(tmp_path / "unrelated-app-data", account_repository=repository)

    response = TestClient(app).get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == account.id
    assert app.state.account_repository.backend_name == "jsonl"


def test_accounts_migration_denies_direct_client_roles() -> None:
    migration = (
        Path(__file__).parents[1]
        / "supabase"
        / "migrations"
        / "20260728120722_accounts_workspaces.sql"
    ).read_text(encoding="utf-8")
    normalized = " ".join(migration.casefold().split())

    for table in (
        "exchange_accounts",
        "exchange_account_workspaces",
        "exchange_account_sessions",
    ):
        assert f"alter table public.{table} enable row level security" in normalized
        assert f"revoke all on table public.{table} from anon, authenticated" in normalized
        assert (
            f"grant select, insert, update, delete on table public.{table} to service_role"
            in normalized
        )
    assert " to authenticated" not in normalized
