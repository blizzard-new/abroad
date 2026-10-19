from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
from collections.abc import Mapping
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Protocol

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import supabase_http
from .supabase_keys import supabase_key_headers
from .models import (
    ApplicationFormDraft,
    ApplicationFormDraftList,
    ApplicationFormDraftRecord,
    ApplicationFormDraftSave,
    utc_now,
)
from .school_identity import school_identity_key
from .settings import DEFAULT_DATA_DIR
from .storage import load_application_form_drafts, save_application_form_drafts


FORM_DRAFT_TABLE = "exchange_application_form_drafts"


class FormDraftError(RuntimeError):
    pass


class FormDraftConfigurationError(FormDraftError):
    pass


class FormDraftIntegrityError(FormDraftError):
    pass


class FormDraftNotFoundError(FormDraftError):
    pass


class FormDraftConflictError(FormDraftError):
    def __init__(self, current: ApplicationFormDraft | None) -> None:
        super().__init__("這份表單草稿已在另一個裝置更新。")
        self.current = current


class _RevisionConflict(FormDraftError):
    """The database rejected an atomic compare-and-set."""


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class FormDraftRepository(Protocol):
    backend_name: str

    def list_records(
        self, account_id: str, home_school_key: str | None = None
    ) -> list[ApplicationFormDraftRecord]: ...

    def find_record(
        self, account_id: str, home_school_key: str, template_id: str
    ) -> ApplicationFormDraftRecord | None: ...

    def save_record(
        self, record: ApplicationFormDraftRecord
    ) -> ApplicationFormDraftRecord: ...

    def delete_record(
        self,
        account_id: str,
        home_school_key: str,
        template_id: str,
        *,
        revision: int | None = None,
    ) -> None: ...

    def purge_account(self, account_id: str) -> None: ...


class LocalFormDraftRepository:
    backend_name = "local-encrypted"

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR) -> None:
        self.data_dir = Path(data_dir)

    def list_records(
        self, account_id: str, home_school_key: str | None = None
    ) -> list[ApplicationFormDraftRecord]:
        return [
            row
            for row in load_application_form_drafts(self.data_dir)
            if row.account_id == account_id
            and (home_school_key is None or row.home_school_key == home_school_key)
        ]

    def find_record(
        self, account_id: str, home_school_key: str, template_id: str
    ) -> ApplicationFormDraftRecord | None:
        return next(
            (
                row
                for row in self.list_records(account_id, home_school_key)
                if row.template_id == template_id
            ),
            None,
        )

    def save_record(
        self, record: ApplicationFormDraftRecord
    ) -> ApplicationFormDraftRecord:
        rows = [
            row
            for row in load_application_form_drafts(self.data_dir)
            if not (
                row.account_id == record.account_id
                and row.home_school_key == record.home_school_key
                and row.template_id == record.template_id
            )
        ]
        save_application_form_drafts([*rows, record], self.data_dir)
        return record

    def delete_record(
        self,
        account_id: str,
        home_school_key: str,
        template_id: str,
        *,
        revision: int | None = None,
    ) -> None:
        rows = [
            row
            for row in load_application_form_drafts(self.data_dir)
            if not (
                row.account_id == account_id
                and row.home_school_key == home_school_key
                and row.template_id == template_id
                and (revision is None or row.revision == revision)
            )
        ]
        save_application_form_drafts(rows, self.data_dir)

    def purge_account(self, account_id: str) -> None:
        rows = [
            row
            for row in load_application_form_drafts(self.data_dir)
            if row.account_id != account_id
        ]
        save_application_form_drafts(rows, self.data_dir)


class SupabaseFormDraftRepository:
    backend_name = "supabase-encrypted"
    atomic_revisions = True

    def __init__(self, url: str, secret_key: str) -> None:
        self.url = url.rstrip("/")
        self.secret_key = secret_key

    def _request(
        self,
        method: str,
        *,
        params: dict[str, str] | None = None,
        json_body: Any = None,
        prefer: str | None = None,
    ) -> list[dict[str, Any]]:
        headers = {
            **supabase_key_headers(self.secret_key),
        }
        if prefer:
            headers["Prefer"] = prefer
        response = supabase_http.request(
            method,
            f"{self.url}/rest/v1/{FORM_DRAFT_TABLE}",
            params=params,
            json=json_body,
            headers=headers,
            timeout=20,
        )
        if response.status_code == 409 and response.json().get("code") == "23505":
            raise _RevisionConflict()
        if response.status_code >= 400:
            raise FormDraftError(
                f"加密表單草稿資料庫操作失敗（HTTP {response.status_code}）。"
            )
        if not response.content:
            return []
        payload = response.json()
        return payload if isinstance(payload, list) else [payload]

    def list_records(
        self, account_id: str, home_school_key: str | None = None
    ) -> list[ApplicationFormDraftRecord]:
        params = {
            "account_id": f"eq.{account_id}",
            "select": "*",
            "order": "updated_at.desc",
        }
        if home_school_key is not None:
            params["home_school_key"] = f"eq.{home_school_key}"
        return [
            ApplicationFormDraftRecord.model_validate(row)
            for row in self._request("GET", params=params)
        ]

    def find_record(
        self, account_id: str, home_school_key: str, template_id: str
    ) -> ApplicationFormDraftRecord | None:
        rows = self._request(
            "GET",
            params={
                "account_id": f"eq.{account_id}",
                "home_school_key": f"eq.{home_school_key}",
                "template_id": f"eq.{template_id}",
                "select": "*",
                "limit": "1",
            },
        )
        return ApplicationFormDraftRecord.model_validate(rows[0]) if rows else None

    def save_record(
        self, record: ApplicationFormDraftRecord
    ) -> ApplicationFormDraftRecord:
        # Unique insertion protects revision zero; UPDATE ... WHERE revision = n
        # protects subsequent edits across workers and server instances.
        params = None if record.revision == 1 else {
            "account_id": f"eq.{record.account_id}",
            "home_school_key": f"eq.{record.home_school_key}",
            "template_id": f"eq.{record.template_id}",
            "revision": f"eq.{record.revision - 1}",
        }
        rows = self._request(
            "POST" if record.revision == 1 else "PATCH",
            params=params,
            json_body=record.model_dump(mode="json"),
            prefer="return=representation",
        )
        if not rows:
            raise _RevisionConflict()
        return ApplicationFormDraftRecord.model_validate(rows[0])

    def delete_record(
        self,
        account_id: str,
        home_school_key: str,
        template_id: str,
        *,
        revision: int | None = None,
    ) -> None:
        params = {
            "account_id": f"eq.{account_id}",
            "home_school_key": f"eq.{home_school_key}",
            "template_id": f"eq.{template_id}",
        }
        if revision is not None:
            params["revision"] = f"eq.{revision}"
        rows = self._request(
            "DELETE",
            params=params,
            prefer="return=representation",
        )
        if revision is not None and not rows:
            raise _RevisionConflict()

    def purge_account(self, account_id: str) -> None:
        self._request("DELETE", params={"account_id": f"eq.{account_id}"})


class FormDraftService:
    def __init__(self, repository: FormDraftRepository, master_key: bytes) -> None:
        if len(master_key) != 32:
            raise FormDraftConfigurationError("加密表單草稿 master key 必須是 32 bytes。")
        import threading

        self._lock = threading.RLock()
        self.repository = repository
        self.encryption_key = hmac.new(
            master_key,
            b"exchange-application-form-drafts-v1",
            hashlib.sha256,
        ).digest()

    @staticmethod
    def _aad(record: ApplicationFormDraftRecord) -> bytes:
        return (
            "application-form-draft:v1:"
            f"{record.account_id}:{record.home_school_key}:{record.template_id}:"
            f"{record.template_version}:{record.revision}"
        ).encode("utf-8")

    def _decode(self, record: ApplicationFormDraftRecord) -> ApplicationFormDraft:
        try:
            plaintext = AESGCM(self.encryption_key).decrypt(
                _unb64(record.nonce),
                _unb64(record.ciphertext),
                self._aad(record),
            )
        except (InvalidTag, ValueError, binascii.Error) as error:
            raise FormDraftIntegrityError("表單草稿解密或完整性驗證失敗。") from error
        if hashlib.sha256(plaintext).hexdigest() != record.plaintext_sha256:
            raise FormDraftIntegrityError("表單草稿原文雜湊不一致。")
        try:
            payload = json.loads(plaintext.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FormDraftIntegrityError("表單草稿內容格式無效。") from error
        return ApplicationFormDraft(
            home_school=record.home_school,
            template_id=record.template_id,
            template_version=record.template_version,
            revision=record.revision,
            profile=payload.get("profile") or {},
            answers=payload.get("answers") or {},
            attachments=payload.get("attachments") or {},
            updated_at=record.updated_at,
        )

    def list_drafts(self, account_id: str, home_school: str) -> ApplicationFormDraftList:
        school_key = school_identity_key(home_school)
        items = [
            self._decode(row)
            for row in self.repository.list_records(account_id, school_key)
        ]
        return ApplicationFormDraftList(
            items=sorted(items, key=lambda row: row.updated_at, reverse=True)
        )

    def save_draft(
        self,
        account_id: str,
        template_id: str,
        payload: ApplicationFormDraftSave,
    ) -> ApplicationFormDraft:
        with nullcontext() if getattr(self.repository, "atomic_revisions", False) else self._lock:
            school_key = school_identity_key(payload.home_school)
            current_record = self.repository.find_record(account_id, school_key, template_id)
            current_revision = current_record.revision if current_record else 0
            if payload.revision != current_revision:
                raise FormDraftConflictError(
                    self._decode(current_record) if current_record is not None else None
                )
            revision = current_revision + 1
            updated_at = utc_now()
            plaintext = json.dumps(
                {
                    "profile": payload.profile,
                    "answers": payload.answers,
                    "attachments": {
                        field_id: [item.model_dump(mode="json") for item in items]
                        for field_id, items in payload.attachments.items()
                    },
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            nonce = secrets.token_bytes(12)
            record = ApplicationFormDraftRecord(
                account_id=account_id,
                home_school_key=school_key,
                home_school=payload.home_school,
                template_id=template_id,
                template_version=payload.template_version,
                revision=revision,
                ciphertext="placeholder",
                nonce=_b64(nonce),
                plaintext_sha256=hashlib.sha256(plaintext).hexdigest(),
                updated_at=updated_at,
            )
            ciphertext = AESGCM(self.encryption_key).encrypt(nonce, plaintext, self._aad(record))
            try:
                saved = self.repository.save_record(
                    record.model_copy(update={"ciphertext": _b64(ciphertext)})
                )
            except _RevisionConflict as error:
                latest = self.repository.find_record(account_id, school_key, template_id)
                raise FormDraftConflictError(self._decode(latest) if latest else None) from error
            return self._decode(saved)

    def delete_draft(
        self,
        account_id: str,
        home_school: str,
        template_id: str,
        *,
        revision: int,
    ) -> None:
        with nullcontext() if getattr(self.repository, "atomic_revisions", False) else self._lock:
            school_key = school_identity_key(home_school)
            current = self.repository.find_record(account_id, school_key, template_id)
            if current is None:
                raise FormDraftNotFoundError("找不到這份表單草稿。")
            if current.revision != revision:
                raise FormDraftConflictError(self._decode(current))
            try:
                self.repository.delete_record(
                    account_id, school_key, template_id, revision=revision
                )
            except _RevisionConflict as error:
                latest = self.repository.find_record(account_id, school_key, template_id)
                raise FormDraftConflictError(self._decode(latest) if latest else None) from error

    def purge_account(self, account_id: str) -> None:
        self.repository.purge_account(account_id)


def create_form_draft_service(
    data_dir: Path,
    master_key: bytes,
    environ: Mapping[str, str] | None = None,
) -> FormDraftService:
    environment = os.environ if environ is None else environ
    mode = environment.get("EXCHANGE_FORM_DRAFT_BACKEND", "auto").strip().casefold()
    runtime = environment.get("EXCHANGE_ENVIRONMENT", "development").strip().casefold()
    url = (
        environment.get("EXCHANGE_SUPABASE_URL")
        or environment.get("SUPABASE_URL")
        or ""
    ).strip()
    secret_key = (
        environment.get("EXCHANGE_SUPABASE_SECRET_KEY")
        or environment.get("SUPABASE_SECRET_KEY")
        or environment.get("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()
    if mode not in {"auto", "local", "supabase"}:
        raise FormDraftConfigurationError(
            "EXCHANGE_FORM_DRAFT_BACKEND 必須是 auto、local 或 supabase。"
        )
    if bool(url) != bool(secret_key):
        raise FormDraftConfigurationError("Supabase URL 與 secret key 必須同時設定。")
    use_supabase = mode == "supabase" or (mode == "auto" and bool(url and secret_key))
    if use_supabase:
        if not url or not secret_key:
            raise FormDraftConfigurationError("Supabase 表單草稿尚未完成伺服器端設定。")
        repository: FormDraftRepository = SupabaseFormDraftRepository(url, secret_key)
    else:
        if runtime in {"production", "prod"}:
            raise FormDraftConfigurationError("正式環境的加密表單草稿必須使用 Supabase。")
        repository = LocalFormDraftRepository(data_dir)
    return FormDraftService(repository, master_key)
