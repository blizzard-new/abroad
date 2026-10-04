import hashlib
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates
from exchange_info.form_drafts import (
    FormDraftIntegrityError,
    FormDraftService,
    LocalFormDraftRepository,
)
from exchange_info.models import (
    AccountSessionRecord,
    ApplicationFormDraftSave,
    UserAccount,
    utc_now,
)
from exchange_info.storage import (
    load_application_form_drafts,
    save_account_sessions,
    save_application_form_drafts,
    save_user_accounts,
)


def _client(tmp_path: Path):
    account = UserAccount(display_name="表單草稿測試學生")
    token = "application-form-draft-test-token"
    save_user_accounts([account], tmp_path)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            )
        ],
        tmp_path,
    )
    return (
        TestClient(create_app(tmp_path)),
        {"Authorization": f"Bearer {token}"},
        account,
    )


def _version(template_id: str) -> str:
    return next(
        row.version
        for row in all_application_templates("長庚大學")
        if row.id == template_id
    )


def _draft_payload(template_id: str, revision: int = 0):
    return {
        "home_school": "長庚大學",
        "template_version": _version(template_id),
        "revision": revision,
        "profile": {
            "student_name_zh": "一般草稿秘密姓名",
            "email": "draft-secret@example.com",
        },
        "answers": {
            "planned_start_date": "2026-09-01",
            "planned_end_date": "2027-01-20",
            "overseas_institution": "Lincoln University",
        },
        "attachments": {},
    }


def test_form_draft_requires_login_and_encrypts_general_fields_at_rest(tmp_path) -> None:
    client, headers, _ = _client(tmp_path)
    payload = _draft_payload("guardian-consent")

    assert client.get("/account/application-drafts").status_code == 401
    assert client.put(
        "/account/application-drafts/guardian-consent", json=payload
    ).status_code == 401

    saved = client.put(
        "/account/application-drafts/guardian-consent",
        headers=headers,
        json=payload,
    )
    assert saved.status_code == 200
    assert saved.headers["cache-control"] == "private, no-store, max-age=0"
    assert saved.json()["revision"] == 1
    assert saved.json()["profile"]["student_name_zh"] == "一般草稿秘密姓名"

    restored = client.get(
        "/account/application-drafts",
        params={"home_school": "長庚大學"},
        headers=headers,
    )
    assert restored.status_code == 200
    assert restored.json()["items"][0]["answers"]["overseas_institution"] == "Lincoln University"

    persisted = b"\n".join(
        path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    )
    assert "一般草稿秘密姓名".encode() not in persisted
    assert b"draft-secret@example.com" not in persisted
    records = load_application_form_drafts(tmp_path)
    assert len(records) == 1
    assert records[0].ciphertext
    assert records[0].nonce


@pytest.mark.parametrize(
    ("template_id", "field_name", "target"),
    [
        ("guardian-consent", "guardian_id_number", "profile"),
        ("credit-transfer", "transcript_attachment", "answers"),
    ],
)
def test_form_draft_rejects_sensitive_values_and_raw_files(
    tmp_path,
    template_id: str,
    field_name: str,
    target: str,
) -> None:
    client, headers, _ = _client(tmp_path)
    payload = {
        "home_school": "長庚大學",
        "template_version": _version(template_id),
        "revision": 0,
        "profile": {},
        "answers": {},
        "attachments": {},
    }
    payload[target][field_name] = (
        "A123456789" if target == "profile" else "data:application/pdf;base64,JVBERi0="
    )

    response = client.put(
        f"/account/application-drafts/{template_id}",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 422
    persisted = b"\n".join(
        path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    )
    assert b"A123456789" not in persisted
    assert b"data:application/pdf" not in persisted


def test_form_draft_revision_conflict_and_permanent_delete(tmp_path) -> None:
    client, headers, _ = _client(tmp_path)
    payload = _draft_payload("guardian-consent")
    first = client.put(
        "/account/application-drafts/guardian-consent", headers=headers, json=payload
    ).json()

    payload["answers"]["overseas_institution"] = "Other University"
    conflict = client.put(
        "/account/application-drafts/guardian-consent", headers=headers, json=payload
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "application_draft_revision_conflict"
    assert conflict.json()["detail"]["current_draft"]["revision"] == 1

    deleted = client.delete(
        "/account/application-drafts/guardian-consent",
        params={"home_school": "長庚大學", "revision": first["revision"]},
        headers=headers,
    )
    assert deleted.status_code == 204
    assert client.get(
        "/account/application-drafts", headers=headers
    ).json()["items"] == []


def test_account_deletion_permanently_purges_encrypted_form_drafts(tmp_path) -> None:
    client, headers, _ = _client(tmp_path)
    saved = client.put(
        "/account/application-drafts/guardian-consent",
        headers=headers,
        json=_draft_payload("guardian-consent"),
    )
    assert saved.status_code == 200
    assert len(load_application_form_drafts(tmp_path)) == 1

    deleted = client.delete("/auth/me", headers=headers)

    assert deleted.status_code == 204
    assert load_application_form_drafts(tmp_path) == []
    assert client.get("/account/application-drafts", headers=headers).status_code == 401


def test_sensitive_attachment_reference_requires_explicit_vault_consent_and_owner(
    tmp_path,
) -> None:
    client, headers, _ = _client(tmp_path)
    rejected = client.post(
        "/account/vault/documents",
        headers=headers,
        files={"file": ("transcript.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
        data={
            "label": "交換成績單",
            "category": "transcript",
            "purpose": "cross_device_access",
            "retention_days": "30",
            "consent": "false",
        },
    )
    assert rejected.status_code == 422

    stored = client.post(
        "/account/vault/documents",
        headers=headers,
        files={"file": ("transcript.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
        data={
            "label": "交換成績單",
            "category": "transcript",
            "purpose": "cross_device_access",
            "retention_days": "30",
            "consent": "true",
        },
    )
    assert stored.status_code == 201
    document = stored.json()
    version = document["versions"][0]
    payload = {
        "home_school": "長庚大學",
        "template_version": _version("credit-transfer"),
        "revision": 0,
        "profile": {"student_name_zh": "王同學"},
        "answers": {
            "completed_courses": "COMP101 | Example | 3 | A",
            "requested_mapping": "COMP101 → 選修學分",
        },
        "attachments": {
            "transcript_attachment": [
                {
                    "document_id": document["id"],
                    "version_id": version["id"],
                    "label": "client value is not trusted",
                    "file_name": "client.pdf",
                    "category": "other",
                    "purpose": "application_preparation",
                    "retention_days": 1,
                    "expires_at": version["expires_at"],
                }
            ]
        },
    }

    saved = client.put(
        "/account/application-drafts/credit-transfer",
        headers=headers,
        json=payload,
    )
    assert saved.status_code == 200
    reference = saved.json()["attachments"]["transcript_attachment"][0]
    assert reference["document_id"] == document["id"]
    assert reference["file_name"] == "transcript.pdf"
    assert reference["purpose"] == "cross_device_access"
    assert reference["retention_days"] == 30


def test_form_draft_integrity_failure_stops_plaintext_return(tmp_path) -> None:
    repository = LocalFormDraftRepository(tmp_path)
    service = FormDraftService(repository, b"d" * 32)
    service.save_draft(
        "account-1",
        "guardian-consent",
        ApplicationFormDraftSave(
            home_school="長庚大學",
            template_version="2026-07-16",
            profile={"student_name_zh": "王同學"},
        ),
    )
    record = load_application_form_drafts(tmp_path)[0]
    replacement = "A" if record.ciphertext[0] != "A" else "B"
    save_application_form_drafts(
        [record.model_copy(update={"ciphertext": replacement + record.ciphertext[1:]})],
        tmp_path,
    )

    with pytest.raises(FormDraftIntegrityError):
        service.list_drafts("account-1", "長庚大學")


def test_form_draft_migration_denies_direct_browser_roles() -> None:
    sql = (
        Path(__file__).resolve().parents[1]
        / "supabase"
        / "migrations"
        / "20260729100000_form_drafts.sql"
    ).read_text(encoding="utf-8").lower()
    normalized = " ".join(sql.split())

    assert "exchange_application_form_drafts" in sql
    assert "enable row level security" in normalized
    assert "revoke all on table public.exchange_application_form_drafts from anon, authenticated" in normalized
    assert "to service_role" in normalized
    assert "ciphertext" in sql
    assert "plaintext_sha256" in sql
