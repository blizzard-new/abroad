from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.document_vault import (
    DocumentVaultService,
    LocalDocumentVaultRepository,
    SupabaseDocumentVaultRepository,
    VaultAuthorizationError,
    VaultConfigurationError,
    VaultConsentError,
    VaultExpiredError,
    VaultIntegrityError,
    create_document_vault_service,
)
from exchange_info.models import (
    AccountSessionRecord,
    ProductAccessTier,
    UserAccount,
    VaultConsentPurpose,
    VaultDocumentCategory,
)
from exchange_info.repositories import JsonlAccountRepository
from exchange_info.storage import load_vault_audits, load_vault_documents, load_vault_versions


PDF_ONE = b"%PDF-1.4\nprivate application content\n%%EOF"
PDF_TWO = b"%PDF-1.4\nupdated private application content\n%%EOF"
BASE_TIME = datetime(2026, 7, 28, 5, 0, tzinfo=timezone.utc)


def _service(tmp_path: Path, *, ttl: int = 30) -> DocumentVaultService:
    return DocumentVaultService(
        LocalDocumentVaultRepository(tmp_path),
        b"v" * 32,
        download_ttl_seconds=ttl,
    )


def _store(
    service: DocumentVaultService,
    account_id: str = "account-a",
    *,
    content: bytes = PDF_ONE,
    document_id: str | None = None,
    now: datetime = BASE_TIME,
    retention_days: int = 30,
):
    return service.store_version(
        account_id,
        document_id=document_id,
        file_name="交換申請表.pdf",
        content=content,
        media_type="application/pdf",
        label="校內交換申請表",
        category=VaultDocumentCategory.APPLICATION_FORM,
        purpose=VaultConsentPurpose.APPLICATION_PREPARATION,
        retention_days=retention_days,
        consent=True,
        now=now,
    )


def test_encryption_round_trip_hides_content_and_names_at_rest(tmp_path) -> None:
    service = _service(tmp_path)
    document = _store(service)
    version = document.versions[0]
    grant = service.create_download_grant("account-a", version.id, now=BASE_TIME)

    content, file_name, media_type = service.download(
        "account-a", grant.token, now=BASE_TIME + timedelta(seconds=1)
    )

    assert content == PDF_ONE
    assert file_name == "交換申請表.pdf"
    assert media_type == "application/pdf"
    repository = service.repository
    assert isinstance(repository, LocalDocumentVaultRepository)
    ciphertext = repository.read_object(
        repository.find_version("account-a", version.id).object_key
    )
    assert PDF_ONE not in ciphertext
    persisted = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (tmp_path / "private_vault").glob("*.jsonl")
    )
    assert "交換申請表.pdf" not in persisted
    assert "校內交換申請表" not in persisted


def test_every_file_and_version_requires_fresh_explicit_consent(tmp_path) -> None:
    service = _service(tmp_path)
    with pytest.raises(VaultConsentError, match="明確同意"):
        service.store_version(
            "account-a",
            file_name="application.pdf",
            content=PDF_ONE,
            media_type="application/pdf",
            label="交換申請表",
            category=VaultDocumentCategory.APPLICATION_FORM,
            purpose=VaultConsentPurpose.APPLICATION_PREPARATION,
            retention_days=30,
            consent=False,
        )

    first = _store(service)
    with pytest.raises(VaultConsentError, match="明確同意"):
        service.store_version(
            "account-a",
            document_id=first.id,
            file_name="application-v2.pdf",
            content=PDF_TWO,
            media_type="application/pdf",
            label=first.label,
            category=first.category,
            purpose=VaultConsentPurpose.CROSS_DEVICE_ACCESS,
            retention_days=30,
            consent=False,
        )
    assert len(service.list_documents("account-a", now=BASE_TIME).items[0].versions) == 1


def test_versions_use_distinct_encrypted_objects_and_keep_history(tmp_path) -> None:
    service = _service(tmp_path)
    first = _store(service)
    second = _store(
        service,
        content=PDF_TWO,
        document_id=first.id,
        now=BASE_TIME + timedelta(minutes=1),
    )

    records = service.repository.list_versions("account-a", first.id)
    assert {row.version_number for row in records} == {1, 2}
    assert len({row.object_key for row in records}) == 2
    assert len({row.wrapped_data_key for row in records}) == 2
    assert [row.version_number for row in second.versions] == [2, 1]


def test_download_grants_are_short_lived_and_account_scoped(tmp_path) -> None:
    service = _service(tmp_path, ttl=30)
    document = _store(service)
    grant = service.create_download_grant(
        "account-a", document.versions[0].id, now=BASE_TIME
    )

    assert grant.download_url == "/account/vault/download"
    assert "?" not in grant.download_url
    assert grant.token not in grant.download_url
    with pytest.raises(VaultAuthorizationError, match="不屬於"):
        service.download("account-b", grant.token, now=BASE_TIME + timedelta(seconds=1))
    with pytest.raises(VaultExpiredError, match="已過期"):
        service.download("account-a", grant.token, now=BASE_TIME + timedelta(seconds=30))


def test_revoked_per_file_consent_invalidates_existing_and_new_download_grants(
    tmp_path,
) -> None:
    service = _service(tmp_path, ttl=30)
    document = _store(service)
    version = service.repository.find_version("account-a", document.versions[0].id)
    assert version is not None
    grant = service.create_download_grant("account-a", version.id, now=BASE_TIME)
    consent = next(
        row
        for row in service.repository.list_consents("account-a", document.id)
        if row.id == version.consent_id
    )
    service.repository.save_consent(
        consent.model_copy(update={"revoked_at": BASE_TIME + timedelta(seconds=1)})
    )

    with pytest.raises(VaultAuthorizationError, match="逐檔保存同意"):
        service.download(
            "account-a",
            grant.token,
            now=BASE_TIME + timedelta(seconds=2),
        )
    with pytest.raises(VaultAuthorizationError, match="逐檔保存同意"):
        service.create_download_grant(
            "account-a",
            version.id,
            now=BASE_TIME + timedelta(seconds=2),
        )


def test_ciphertext_tampering_fails_closed(tmp_path) -> None:
    service = _service(tmp_path)
    document = _store(service)
    version = service.repository.find_version("account-a", document.versions[0].id)
    assert version is not None
    repository = service.repository
    assert isinstance(repository, LocalDocumentVaultRepository)
    path = repository._object_path(version.object_key)
    ciphertext = bytearray(path.read_bytes())
    ciphertext[-1] ^= 1
    path.write_bytes(ciphertext)
    grant = service.create_download_grant("account-a", version.id, now=BASE_TIME)

    with pytest.raises(VaultIntegrityError, match="密文雜湊"):
        service.download("account-a", grant.token, now=BASE_TIME + timedelta(seconds=1))


def test_permanent_version_and_document_deletion_remove_objects(tmp_path) -> None:
    service = _service(tmp_path)
    first = _store(service)
    second = _store(service, content=PDF_TWO, document_id=first.id)
    version_two = next(row for row in second.versions if row.version_number == 2)
    record_two = service.repository.find_version("account-a", version_two.id)
    assert record_two is not None

    updated = service.delete_version(
        "account-a",
        first.id,
        version_two.id,
        now=BASE_TIME,
    )
    assert updated is not None
    assert [row.version_number for row in updated.versions] == [1]
    with pytest.raises(Exception):
        service.repository.read_object(record_two.object_key)

    remaining = service.repository.list_versions("account-a", first.id)[0]
    service.delete_document("account-a", first.id)
    assert service.list_documents("account-a").items == []
    with pytest.raises(Exception):
        service.repository.read_object(remaining.object_key)


def test_cleanup_removes_all_expired_versions_and_orphan_objects(tmp_path) -> None:
    service = _service(tmp_path)
    document = _store(service, retention_days=1)
    _store(
        service,
        content=PDF_TWO,
        document_id=document.id,
        now=BASE_TIME + timedelta(minutes=1),
        retention_days=1,
    )
    service.repository.upload_object("vault/orphan.bin", b"orphan-ciphertext")

    result = service.cleanup(now=BASE_TIME + timedelta(days=2))

    assert result.expired_version_count == 2
    assert result.removed_document_count == 1
    assert result.orphan_object_count == 1
    assert service.repository.list_object_keys() == set()
    assert service.repository.list_documents("account-a") == []


def test_vault_audit_log_contains_no_account_names_or_document_content(tmp_path) -> None:
    service = _service(tmp_path)
    document = _store(service, account_id="secret-account-id")
    grant = service.create_download_grant(
        "secret-account-id", document.versions[0].id, now=BASE_TIME
    )
    service.download(
        "secret-account-id", grant.token, now=BASE_TIME + timedelta(seconds=1)
    )
    audits = load_vault_audits(tmp_path)

    assert audits
    for audit in audits:
        payload = audit.model_dump(mode="json")
        assert set(payload) == {
            "id",
            "subject_fingerprint",
            "document_id",
            "version_id",
            "action",
            "created_at",
        }
        serialized = json.dumps(payload, ensure_ascii=False)
        assert "secret-account-id" not in serialized
        assert "交換申請表" not in serialized
        assert "private application content" not in serialized


def test_factory_requires_private_supabase_configuration_in_production(tmp_path) -> None:
    with pytest.raises(VaultConfigurationError, match="必須使用 Supabase"):
        create_document_vault_service(
            tmp_path,
            {"EXCHANGE_ENVIRONMENT": "production", "EXCHANGE_VAULT_BACKEND": "auto"},
        )
    with pytest.raises(VaultConfigurationError, match="同時設定"):
        create_document_vault_service(
            tmp_path,
            {"EXCHANGE_SUPABASE_URL": "https://project.supabase.co"},
        )


class _FakeResponse:
    def __init__(self, payload: Any = None, content: bytes = b"{}") -> None:
        self.payload = {} if payload is None else payload
        self.content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self.payload


def test_supabase_repository_verifies_private_bucket_and_uses_server_secret() -> None:
    calls: list[dict[str, Any]] = []

    def request(method: str, url: str, **kwargs: Any) -> _FakeResponse:
        calls.append({"method": method, "url": url, **kwargs})
        if method == "GET" and "/storage/v1/bucket/" in url:
            return _FakeResponse({"public": False})
        return _FakeResponse()

    repository = SupabaseDocumentVaultRepository(
        "https://project.supabase.co",
        "sb_secret_server-only",
        request_func=request,
    )
    repository.upload_object("vault/encrypted.bin", b"ciphertext-only")

    assert len(calls) == 2
    upload = calls[1]
    assert upload["url"].endswith("/storage/v1/object/exchange-private-vault/vault/encrypted.bin")
    assert upload["headers"]["apikey"] == "sb_secret_server-only"
    assert "Authorization" not in upload["headers"], "an sb_secret key is not a JWT, so it goes in apikey only"
    assert upload["headers"]["x-upsert"] == "false"
    assert upload["data"] == b"ciphertext-only"


def test_supabase_repository_recursively_lists_nested_objects_with_cursor() -> None:
    calls: list[dict[str, Any]] = []

    def request(method: str, url: str, **kwargs: Any) -> _FakeResponse:
        calls.append({"method": method, "url": url, **kwargs})
        if method == "GET":
            return _FakeResponse({"public": False})
        cursor = kwargs["json"].get("cursor")
        if cursor is None:
            return _FakeResponse(
                {
                    "hasNext": True,
                    "nextCursor": "runtime-next-page",
                    "folders": [],
                    "objects": [
                        {"id": "one", "name": "vault/account-a/nested/one.cipher"}
                    ],
                }
            )
        return _FakeResponse(
            {
                "hasNext": False,
                "folders": [],
                "objects": [
                    {"id": "two", "name": "vault/account-b/deeper/two.cipher"},
                    {"id": "outside", "name": "public/not-a-vault-object.txt"},
                ],
            }
        )

    repository = SupabaseDocumentVaultRepository(
        "https://project.supabase.co",
        "sb_secret_server-only",
        request_func=request,
    )

    assert repository.list_object_keys() == {
        "vault/account-a/nested/one.cipher",
        "vault/account-b/deeper/two.cipher",
    }
    list_calls = [call for call in calls if "/object/list-v2/" in call["url"]]
    assert len(list_calls) == 2
    assert list_calls[0]["json"] == {
        "prefix": "vault/",
        "limit": 1000,
        "with_delimiter": False,
    }
    assert list_calls[1]["json"]["cursor"] == "runtime-next-page"


def test_supabase_repository_rejects_a_public_bucket() -> None:
    def request(method: str, url: str, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse({"public": True})

    repository = SupabaseDocumentVaultRepository(
        "https://project.supabase.co",
        "sb_secret_server-only",
        request_func=request,
    )
    with pytest.raises(VaultConfigurationError, match="private"):
        repository.upload_object("vault/encrypted.bin", b"ciphertext-only")


def _api_client(tmp_path: Path, *, tier: ProductAccessTier = ProductAccessTier.FREE):
    account_repository = JsonlAccountRepository(tmp_path / "accounts")
    account = UserAccount(display_name="Vault Student", product_tier=tier)
    token = "vault-test-access-token"
    account_repository.save_account(account)
    account_repository.save_session(
        AccountSessionRecord(
            account_id=account.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=BASE_TIME + timedelta(days=365),
        )
    )
    service = _service(tmp_path / "vault")
    client = TestClient(
        create_app(
            tmp_path / "app",
            account_repository=account_repository,
            document_vault_service=service,
        )
    )
    return client, account_repository, account, service, {
        "Authorization": f"Bearer {token}"
    }


def test_vault_api_requires_login_consent_and_never_exposes_object_keys(tmp_path) -> None:
    client, _, _, _, headers = _api_client(tmp_path)
    assert client.get("/account/vault/documents").status_code == 401

    denied = client.post(
        "/account/vault/documents",
        headers=headers,
        data={
            "label": "校內交換申請表",
            "category": "application_form",
            "purpose": "application_preparation",
            "retention_days": "30",
            "consent": "false",
        },
        files={"file": ("application.pdf", PDF_ONE, "application/pdf")},
    )
    assert denied.status_code == 422

    created = client.post(
        "/account/vault/documents",
        headers=headers,
        data={
            "label": "校內交換申請表",
            "category": "application_form",
            "purpose": "application_preparation",
            "retention_days": "30",
            "consent": "true",
        },
        files={"file": ("application.pdf", PDF_ONE, "application/pdf")},
    )
    assert created.status_code == 201
    payload = created.json()
    assert "object_key" not in json.dumps(payload)
    assert "download_url" not in json.dumps(payload)


def test_vault_api_download_uses_header_token_and_enforces_owner(tmp_path) -> None:
    client, repository, account, _, headers = _api_client(tmp_path)
    created = client.post(
        "/account/vault/documents",
        headers=headers,
        data={
            "label": "校內交換申請表",
            "category": "application_form",
            "purpose": "application_preparation",
            "retention_days": "30",
            "consent": "true",
        },
        files={"file": ("application.pdf", PDF_ONE, "application/pdf")},
    ).json()
    version_id = created["versions"][0]["id"]
    grant = client.post(
        f"/account/vault/versions/{version_id}/download-grant", headers=headers
    )
    assert grant.status_code == 200
    assert "?" not in grant.json()["download_url"]
    assert client.post(grant.json()["download_url"], headers=headers).status_code == 403
    downloaded = client.post(
        grant.json()["download_url"],
        headers={**headers, "X-Vault-Download-Token": grant.json()["token"]},
    )
    assert downloaded.status_code == 200
    assert downloaded.content == PDF_ONE
    assert downloaded.headers["cache-control"] == "private, no-store, max-age=0"

    other = UserAccount(display_name="Other Student")
    other_token = "other-vault-token"
    repository.save_account(other)
    repository.save_session(
        AccountSessionRecord(
            account_id=other.id,
            token_hash=hashlib.sha256(other_token.encode()).hexdigest(),
            expires_at=BASE_TIME + timedelta(days=365),
        )
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.post(
        f"/account/vault/versions/{version_id}/download-grant",
        headers=other_headers,
    ).status_code == 404
    assert account.id != other.id


def test_account_deletion_purges_vault_before_account_record(tmp_path) -> None:
    client, repository, account, service, headers = _api_client(tmp_path)
    response = client.post(
        "/account/vault/documents",
        headers=headers,
        data={
            "label": "校內交換申請表",
            "category": "application_form",
            "purpose": "application_preparation",
            "retention_days": "30",
            "consent": "true",
        },
        files={"file": ("application.pdf", PDF_ONE, "application/pdf")},
    )
    assert response.status_code == 201
    assert service.repository.list_object_keys()

    deleted = client.delete("/auth/me", headers=headers)

    assert deleted.status_code == 204
    assert repository.find_account_by_id(account.id) is None
    assert service.repository.list_object_keys() == set()
    assert service.repository.list_documents(account.id) == []


def test_public_release_blocks_free_account_vault_access(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    client, _, _, _, headers = _api_client(tmp_path)

    response = client.get("/account/vault/documents", headers=headers)

    assert response.status_code == 403
    assert "進階功能" in response.json()["detail"]


def test_document_vault_migration_denies_direct_browser_roles() -> None:
    migration = (
        Path(__file__).parents[1]
        / "supabase"
        / "migrations"
        / "20260728130940_document_vault.sql"
    ).read_text(encoding="utf-8")
    normalized = " ".join(migration.casefold().split())

    for table in (
        "exchange_vault_documents",
        "exchange_vault_versions",
        "exchange_vault_consents",
        "exchange_vault_audit_log",
    ):
        assert f"alter table public.{table} enable row level security" in normalized
        assert f"revoke all on table public.{table} from anon, authenticated" in normalized
    assert " to authenticated" not in normalized
    assert "storage.objects" not in normalized
    assert "storage.buckets" not in normalized
    assert "grant select, insert, update, delete on table public.exchange_vault_documents to service_role" in normalized


def test_web_vault_requires_explicit_consent_and_keeps_generated_pdf_local() -> None:
    static_dir = Path(__file__).parents[1] / "src" / "exchange_info" / "static"
    html = (static_dir / "index.html").read_text(encoding="utf-8")
    script = (static_dir / "app.js").read_text(encoding="utf-8")

    assert 'id="private-vault"' in html
    assert 'name="consent" type="checkbox" required' in html
    assert "登入不代表同意上傳" in html
    assert "不包含公開分享、社群連結或 AI 訓練" in html
    assert "state.generatedVaultCandidate =" in script
    assert 'payload.append("consent", "true")' in script
    assert '"X-Vault-Download-Token": grant.token' in script
    assert "grant.token" not in script.split("const response = await fetch(grant.download_url", 1)[0].split("async function downloadPrivateVaultVersion", 1)[1]
