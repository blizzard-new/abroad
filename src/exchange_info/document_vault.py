from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Mapping, Protocol
from urllib.parse import quote
from zipfile import BadZipFile, ZipFile

import requests
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import supabase_http
from .supabase_keys import supabase_key_headers
from .models import (
    VaultAuditAction,
    VaultAuditRecord,
    VaultCleanupResult,
    VaultConsentPurpose,
    VaultConsentRecord,
    VaultDocumentCategory,
    VaultDocumentList,
    VaultDocumentRecord,
    VaultDocumentSummary,
    VaultDocumentVersionRecord,
    VaultDownloadGrant,
    VaultVersionSummary,
    utc_now,
)
from .settings import DEFAULT_DATA_DIR
from .storage import (
    data_paths,
    ensure_data_dirs,
    load_vault_audits,
    load_vault_consents,
    load_vault_documents,
    load_vault_versions,
    save_vault_audits,
    save_vault_consents,
    save_vault_documents,
    save_vault_versions,
)


MAX_VAULT_FILE_BYTES = 20 * 1024 * 1024
DEFAULT_DOWNLOAD_TTL_SECONDS = 300
VAULT_TERMS_VERSION = "2026-07-28"
DEFAULT_VAULT_BUCKET = "exchange-private-vault"
ALLOWED_MEDIA_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


class VaultError(RuntimeError):
    pass


class VaultConfigurationError(VaultError):
    pass


class VaultValidationError(VaultError):
    pass


class VaultConsentError(VaultError):
    pass


class VaultNotFoundError(VaultError):
    pass


class VaultAuthorizationError(VaultError):
    pass


class VaultExpiredError(VaultError):
    pass


class VaultIntegrityError(VaultError):
    pass


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class DocumentVaultRepository(Protocol):
    backend_name: str

    def list_documents(self, account_id: str) -> list[VaultDocumentRecord]: ...

    def list_all_documents(self) -> list[VaultDocumentRecord]: ...

    def find_document(
        self, account_id: str, document_id: str
    ) -> VaultDocumentRecord | None: ...

    def save_document(self, document: VaultDocumentRecord) -> VaultDocumentRecord: ...

    def list_versions(
        self, account_id: str, document_id: str | None = None
    ) -> list[VaultDocumentVersionRecord]: ...

    def find_version(
        self, account_id: str, version_id: str
    ) -> VaultDocumentVersionRecord | None: ...

    def save_version(
        self, version: VaultDocumentVersionRecord
    ) -> VaultDocumentVersionRecord: ...

    def list_consents(
        self, account_id: str, document_id: str | None = None
    ) -> list[VaultConsentRecord]: ...

    def save_consent(self, consent: VaultConsentRecord) -> VaultConsentRecord: ...

    def delete_version(self, account_id: str, version_id: str) -> None: ...

    def delete_document(self, account_id: str, document_id: str) -> None: ...

    def append_audit(self, audit: VaultAuditRecord) -> VaultAuditRecord: ...

    def upload_object(self, object_key: str, ciphertext: bytes) -> None: ...

    def read_object(self, object_key: str) -> bytes: ...

    def delete_objects(self, object_keys: list[str]) -> None: ...

    def list_object_keys(self) -> set[str]: ...


class LocalDocumentVaultRepository:
    backend_name = "local-encrypted"

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR) -> None:
        self.data_dir = Path(data_dir)
        ensure_data_dirs(self.data_dir)
        self.blob_root = data_paths(self.data_dir)["vault_blobs"].resolve()

    def list_documents(self, account_id: str) -> list[VaultDocumentRecord]:
        return [
            row for row in load_vault_documents(self.data_dir) if row.account_id == account_id
        ]

    def list_all_documents(self) -> list[VaultDocumentRecord]:
        return load_vault_documents(self.data_dir)

    def find_document(
        self, account_id: str, document_id: str
    ) -> VaultDocumentRecord | None:
        return next(
            (row for row in self.list_documents(account_id) if row.id == document_id),
            None,
        )

    def save_document(self, document: VaultDocumentRecord) -> VaultDocumentRecord:
        rows = [row for row in load_vault_documents(self.data_dir) if row.id != document.id]
        save_vault_documents([*rows, document], self.data_dir)
        return document

    def list_versions(
        self, account_id: str, document_id: str | None = None
    ) -> list[VaultDocumentVersionRecord]:
        return [
            row
            for row in load_vault_versions(self.data_dir)
            if row.account_id == account_id
            and (document_id is None or row.document_id == document_id)
        ]

    def find_version(
        self, account_id: str, version_id: str
    ) -> VaultDocumentVersionRecord | None:
        return next(
            (row for row in self.list_versions(account_id) if row.id == version_id),
            None,
        )

    def save_version(
        self, version: VaultDocumentVersionRecord
    ) -> VaultDocumentVersionRecord:
        rows = [row for row in load_vault_versions(self.data_dir) if row.id != version.id]
        save_vault_versions([*rows, version], self.data_dir)
        return version

    def list_consents(
        self, account_id: str, document_id: str | None = None
    ) -> list[VaultConsentRecord]:
        return [
            row
            for row in load_vault_consents(self.data_dir)
            if row.account_id == account_id
            and (document_id is None or row.document_id == document_id)
        ]

    def save_consent(self, consent: VaultConsentRecord) -> VaultConsentRecord:
        rows = [row for row in load_vault_consents(self.data_dir) if row.id != consent.id]
        save_vault_consents([*rows, consent], self.data_dir)
        return consent

    def delete_version(self, account_id: str, version_id: str) -> None:
        version = self.find_version(account_id, version_id)
        if version is None:
            return
        save_vault_versions(
            [row for row in load_vault_versions(self.data_dir) if row.id != version_id],
            self.data_dir,
        )
        save_vault_consents(
            [
                row
                for row in load_vault_consents(self.data_dir)
                if row.version_id != version_id
            ],
            self.data_dir,
        )

    def delete_document(self, account_id: str, document_id: str) -> None:
        save_vault_documents(
            [
                row
                for row in load_vault_documents(self.data_dir)
                if not (row.id == document_id and row.account_id == account_id)
            ],
            self.data_dir,
        )
        save_vault_versions(
            [
                row
                for row in load_vault_versions(self.data_dir)
                if not (row.document_id == document_id and row.account_id == account_id)
            ],
            self.data_dir,
        )
        save_vault_consents(
            [
                row
                for row in load_vault_consents(self.data_dir)
                if not (row.document_id == document_id and row.account_id == account_id)
            ],
            self.data_dir,
        )

    def append_audit(self, audit: VaultAuditRecord) -> VaultAuditRecord:
        save_vault_audits([*load_vault_audits(self.data_dir), audit], self.data_dir)
        return audit

    def _object_path(self, object_key: str) -> Path:
        normalized = PurePosixPath(object_key)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise VaultValidationError("文件儲存路徑無效。")
        path = (self.blob_root / Path(*normalized.parts)).resolve()
        if self.blob_root != path and self.blob_root not in path.parents:
            raise VaultValidationError("文件儲存路徑超出私人文件庫。")
        return path

    def upload_object(self, object_key: str, ciphertext: bytes) -> None:
        path = self._object_path(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise VaultValidationError("私人文件物件已存在。")
        temporary = path.with_suffix(f"{path.suffix}.tmp-{secrets.token_hex(6)}")
        temporary.write_bytes(ciphertext)
        temporary.replace(path)

    def read_object(self, object_key: str) -> bytes:
        path = self._object_path(object_key)
        if not path.is_file():
            raise VaultNotFoundError("找不到加密文件內容。")
        return path.read_bytes()

    def delete_objects(self, object_keys: list[str]) -> None:
        for object_key in object_keys:
            path = self._object_path(object_key)
            if path.is_file():
                path.unlink()
            parent = path.parent
            while parent != self.blob_root and parent.exists():
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent

    def list_object_keys(self) -> set[str]:
        if not self.blob_root.exists():
            return set()
        return {
            path.relative_to(self.blob_root).as_posix()
            for path in self.blob_root.rglob("*.bin")
            if path.is_file()
        }


class SupabaseDocumentVaultRepository:
    backend_name = "supabase-private-storage"

    def __init__(
        self,
        url: str,
        secret_key: str,
        *,
        bucket: str = DEFAULT_VAULT_BUCKET,
        request_func=supabase_http.request,
    ) -> None:
        if not url.strip().casefold().startswith("https://"):
            raise VaultConfigurationError("Supabase URL 必須使用 HTTPS。")
        if not secret_key.strip():
            raise VaultConfigurationError("Supabase secret key 不可為空。")
        self.url = url.rstrip("/")
        self.secret_key = secret_key.strip()
        self.bucket = bucket.strip() or DEFAULT_VAULT_BUCKET
        self.request_func = request_func
        self._bucket_verified = False

    @property
    def headers(self) -> dict[str, str]:
        return {
            **supabase_key_headers(self.secret_key),
        }

    def _request(self, method: str, path: str, **kwargs):
        response = self.request_func(
            method,
            f"{self.url}{path}",
            headers={**self.headers, **kwargs.pop("headers", {})},
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def _table(
        self,
        method: str,
        table: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict | None = None,
        prefer: str | None = None,
    ) -> list[dict]:
        headers = {"Content-Type": "application/json"}
        if prefer:
            headers["Prefer"] = prefer
        response = self._request(
            method,
            f"/rest/v1/{table}",
            params=params,
            json=json_body,
            headers=headers,
        )
        if not response.content:
            return []
        value = response.json()
        return value if isinstance(value, list) else [value]

    def list_documents(self, account_id: str) -> list[VaultDocumentRecord]:
        rows = self._table(
            "GET",
            "exchange_vault_documents",
            params={"select": "*", "account_id": f"eq.{account_id}", "order": "updated_at.desc"},
        )
        return [VaultDocumentRecord.model_validate(row) for row in rows]

    def list_all_documents(self) -> list[VaultDocumentRecord]:
        results: list[VaultDocumentRecord] = []
        offset = 0
        while True:
            rows = self._table(
                "GET",
                "exchange_vault_documents",
                params={"select": "*", "limit": "1000", "offset": str(offset)},
            )
            results.extend(VaultDocumentRecord.model_validate(row) for row in rows)
            if len(rows) < 1000:
                return results
            offset += len(rows)

    def find_document(
        self, account_id: str, document_id: str
    ) -> VaultDocumentRecord | None:
        rows = self._table(
            "GET",
            "exchange_vault_documents",
            params={
                "select": "*",
                "account_id": f"eq.{account_id}",
                "id": f"eq.{document_id}",
                "limit": "1",
            },
        )
        return VaultDocumentRecord.model_validate(rows[0]) if rows else None

    def save_document(self, document: VaultDocumentRecord) -> VaultDocumentRecord:
        rows = self._table(
            "POST",
            "exchange_vault_documents",
            params={"on_conflict": "id"},
            json_body=document.model_dump(mode="json"),
            prefer="resolution=merge-duplicates,return=representation",
        )
        return VaultDocumentRecord.model_validate(rows[0]) if rows else document

    def list_versions(
        self, account_id: str, document_id: str | None = None
    ) -> list[VaultDocumentVersionRecord]:
        params = {"select": "*", "account_id": f"eq.{account_id}", "order": "version_number.desc"}
        if document_id is not None:
            params["document_id"] = f"eq.{document_id}"
        rows = self._table("GET", "exchange_vault_versions", params=params)
        return [VaultDocumentVersionRecord.model_validate(row) for row in rows]

    def find_version(
        self, account_id: str, version_id: str
    ) -> VaultDocumentVersionRecord | None:
        rows = self._table(
            "GET",
            "exchange_vault_versions",
            params={
                "select": "*",
                "account_id": f"eq.{account_id}",
                "id": f"eq.{version_id}",
                "limit": "1",
            },
        )
        return VaultDocumentVersionRecord.model_validate(rows[0]) if rows else None

    def save_version(
        self, version: VaultDocumentVersionRecord
    ) -> VaultDocumentVersionRecord:
        rows = self._table(
            "POST",
            "exchange_vault_versions",
            params={"on_conflict": "id"},
            json_body=version.model_dump(mode="json"),
            prefer="resolution=merge-duplicates,return=representation",
        )
        return VaultDocumentVersionRecord.model_validate(rows[0]) if rows else version

    def list_consents(
        self, account_id: str, document_id: str | None = None
    ) -> list[VaultConsentRecord]:
        params = {"select": "*", "account_id": f"eq.{account_id}"}
        if document_id is not None:
            params["document_id"] = f"eq.{document_id}"
        rows = self._table("GET", "exchange_vault_consents", params=params)
        return [VaultConsentRecord.model_validate(row) for row in rows]

    def save_consent(self, consent: VaultConsentRecord) -> VaultConsentRecord:
        rows = self._table(
            "POST",
            "exchange_vault_consents",
            params={"on_conflict": "id"},
            json_body=consent.model_dump(mode="json"),
            prefer="resolution=merge-duplicates,return=representation",
        )
        return VaultConsentRecord.model_validate(rows[0]) if rows else consent

    def delete_version(self, account_id: str, version_id: str) -> None:
        self._table(
            "DELETE",
            "exchange_vault_versions",
            params={"account_id": f"eq.{account_id}", "id": f"eq.{version_id}"},
            prefer="return=minimal",
        )

    def delete_document(self, account_id: str, document_id: str) -> None:
        self._table(
            "DELETE",
            "exchange_vault_documents",
            params={"account_id": f"eq.{account_id}", "id": f"eq.{document_id}"},
            prefer="return=minimal",
        )

    def append_audit(self, audit: VaultAuditRecord) -> VaultAuditRecord:
        rows = self._table(
            "POST",
            "exchange_vault_audit_log",
            json_body=audit.model_dump(mode="json"),
            prefer="return=representation",
        )
        return VaultAuditRecord.model_validate(rows[0]) if rows else audit

    def _ensure_private_bucket(self) -> None:
        if self._bucket_verified:
            return
        response = self._request("GET", f"/storage/v1/bucket/{quote(self.bucket, safe='')}")
        payload = response.json()
        if payload.get("public") is not False:
            raise VaultConfigurationError("私人文件庫 bucket 必須設定為 private。")
        self._bucket_verified = True

    def upload_object(self, object_key: str, ciphertext: bytes) -> None:
        self._ensure_private_bucket()
        self._request(
            "POST",
            f"/storage/v1/object/{quote(self.bucket, safe='')}/{quote(object_key, safe='/')}",
            headers={
                "Content-Type": "application/octet-stream",
                "Cache-Control": "no-store",
                "x-upsert": "false",
            },
            data=ciphertext,
        )

    def read_object(self, object_key: str) -> bytes:
        self._ensure_private_bucket()
        response = self._request(
            "GET",
            f"/storage/v1/object/authenticated/{quote(self.bucket, safe='')}/{quote(object_key, safe='/')}",
            headers={"Cache-Control": "no-store"},
        )
        return response.content

    def delete_objects(self, object_keys: list[str]) -> None:
        if not object_keys:
            return
        self._ensure_private_bucket()
        self._request(
            "DELETE",
            f"/storage/v1/object/{quote(self.bucket, safe='')}",
            headers={"Content-Type": "application/json"},
            json={"prefixes": object_keys},
        )

    def list_object_keys(self) -> set[str]:
        self._ensure_private_bucket()
        results: set[str] = set()
        cursor: str | None = None
        seen_cursors: set[str] = set()
        while True:
            payload: dict[str, object] = {
                "prefix": "vault/",
                "limit": 1000,
                "with_delimiter": False,
            }
            if cursor is not None:
                payload["cursor"] = cursor
            response = self._request(
                "POST",
                f"/storage/v1/object/list-v2/{quote(self.bucket, safe='')}",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            page = response.json()
            if not isinstance(page, dict) or not isinstance(page.get("objects"), list):
                raise VaultConfigurationError("Supabase Storage 回傳無效的物件清單。")
            for row in page["objects"]:
                if not isinstance(row, dict):
                    raise VaultConfigurationError("Supabase Storage 回傳無效的物件資料。")
                object_key = row.get("name")
                if isinstance(object_key, str) and object_key.startswith("vault/"):
                    results.add(object_key)
            if page.get("hasNext") is not True:
                return results
            next_cursor = page.get("nextCursor")
            if (
                not isinstance(next_cursor, str)
                or not next_cursor
                or next_cursor in seen_cursors
            ):
                raise VaultConfigurationError("Supabase Storage 分頁游標無效。")
            seen_cursors.add(next_cursor)
            cursor = next_cursor


class DocumentVaultService:
    def __init__(
        self,
        repository: DocumentVaultRepository,
        master_key: bytes,
        *,
        download_ttl_seconds: int = DEFAULT_DOWNLOAD_TTL_SECONDS,
    ) -> None:
        if len(master_key) != 32:
            raise VaultConfigurationError("私人文件庫 master key 必須是 32 bytes。")
        if not 30 <= download_ttl_seconds <= 600:
            raise VaultConfigurationError("私人文件下載授權必須介於 30 到 600 秒。")
        self.repository = repository
        self.master_key = master_key
        self.download_ttl_seconds = download_ttl_seconds
        self._signing_key = hmac.new(
            master_key, b"exchange-vault-download-signing", hashlib.sha256
        ).digest()

    def _fingerprint(self, account_id: str) -> str:
        return hmac.new(
            self.master_key, f"account:{account_id}".encode(), hashlib.sha256
        ).hexdigest()[:32]

    def _audit(
        self,
        account_id: str,
        action: VaultAuditAction,
        *,
        document_id: str | None = None,
        version_id: str | None = None,
        now: datetime | None = None,
    ) -> None:
        self.repository.append_audit(
            VaultAuditRecord(
                subject_fingerprint=self._fingerprint(account_id),
                document_id=document_id,
                version_id=version_id,
                action=action,
                created_at=_aware_utc(now or utc_now()),
            )
        )

    def _encrypt_text(self, value: str, aad: bytes) -> tuple[str, str]:
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(self.master_key).encrypt(nonce, value.encode("utf-8"), aad)
        return _b64(ciphertext), _b64(nonce)

    def _decrypt_text(self, ciphertext: str, nonce: str, aad: bytes) -> str:
        try:
            value = AESGCM(self.master_key).decrypt(
                _unb64(nonce), _unb64(ciphertext), aad
            )
            return value.decode("utf-8")
        except (InvalidTag, UnicodeDecodeError, ValueError) as error:
            raise VaultIntegrityError("私人文件 metadata 完整性驗證失敗。") from error

    @staticmethod
    def _data_aad(version: VaultDocumentVersionRecord) -> bytes:
        return (
            f"vault:{version.account_id}:{version.document_id}:{version.id}:"
            f"{version.version_number}:{version.media_type}"
        ).encode("utf-8")

    def _encrypt_content(
        self,
        content: bytes,
        *,
        account_id: str,
        document_id: str,
        version_id: str,
        version_number: int,
        media_type: str,
    ) -> tuple[bytes, str, str, str]:
        data_key = secrets.token_bytes(32)
        content_nonce = secrets.token_bytes(12)
        aad = (
            f"vault:{account_id}:{document_id}:{version_id}:"
            f"{version_number}:{media_type}"
        ).encode("utf-8")
        ciphertext = AESGCM(data_key).encrypt(content_nonce, content, aad)
        wrap_nonce = secrets.token_bytes(12)
        wrapped_key = AESGCM(self.master_key).encrypt(
            wrap_nonce, data_key, b"vault-data-key:" + aad
        )
        return ciphertext, _b64(wrapped_key), _b64(wrap_nonce), _b64(content_nonce)

    def _decrypt_content(
        self, version: VaultDocumentVersionRecord, ciphertext: bytes
    ) -> bytes:
        if hashlib.sha256(ciphertext).hexdigest() != version.ciphertext_sha256:
            raise VaultIntegrityError("私人文件密文雜湊不一致。")
        aad = self._data_aad(version)
        try:
            data_key = AESGCM(self.master_key).decrypt(
                _unb64(version.wrap_nonce),
                _unb64(version.wrapped_data_key),
                b"vault-data-key:" + aad,
            )
            plaintext = AESGCM(data_key).decrypt(
                _unb64(version.content_nonce), ciphertext, aad
            )
        except (InvalidTag, ValueError) as error:
            raise VaultIntegrityError("私人文件解密或完整性驗證失敗。") from error
        if hashlib.sha256(plaintext).hexdigest() != version.plaintext_sha256:
            raise VaultIntegrityError("私人文件原文雜湊不一致。")
        return plaintext

    @staticmethod
    def _validate_file(
        file_name: str, content: bytes, media_type: str | None
    ) -> tuple[str, str]:
        name = Path(str(file_name or "").strip()).name
        if not name or len(name) > 255 or any(ord(char) < 32 for char in name):
            raise VaultValidationError("檔名無效或過長。")
        if not content:
            raise VaultValidationError("不能保存空白檔案。")
        if len(content) > MAX_VAULT_FILE_BYTES:
            raise VaultValidationError("私人文件單檔不可超過 20 MB。")
        suffix = Path(name).suffix.casefold()
        expected = ALLOWED_MEDIA_BY_SUFFIX.get(suffix)
        if expected is None:
            raise VaultValidationError("只接受 PDF、DOCX、TXT、JPG、PNG 或 WebP。")
        normalized_media = str(media_type or "").split(";", 1)[0].strip().casefold()
        if normalized_media in {"", "application/octet-stream"}:
            normalized_media = expected
        if normalized_media != expected:
            raise VaultValidationError("檔案副檔名與內容類型不一致。")
        valid = False
        if suffix == ".pdf":
            valid = content.startswith(b"%PDF-")
        elif suffix in {".jpg", ".jpeg"}:
            valid = content.startswith(b"\xff\xd8\xff")
        elif suffix == ".png":
            valid = content.startswith(b"\x89PNG\r\n\x1a\n")
        elif suffix == ".webp":
            valid = len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
        elif suffix == ".txt":
            try:
                content.decode("utf-8")
                valid = True
            except UnicodeDecodeError:
                valid = False
        elif suffix == ".docx":
            try:
                from io import BytesIO

                with ZipFile(BytesIO(content)) as archive:
                    infos = archive.infolist()
                    if (
                        len(infos) > 1000
                        or sum(max(0, info.file_size) for info in infos) > 50 * 1024 * 1024
                    ):
                        valid = False
                    else:
                        names = [info.filename for info in infos]
                        valid = "[Content_Types].xml" in names and any(
                            item.startswith("word/") for item in names
                        )
            except BadZipFile:
                valid = False
        if not valid:
            raise VaultValidationError("檔案內容與宣告格式不符。")
        return name, normalized_media

    def store_version(
        self,
        account_id: str,
        *,
        file_name: str,
        content: bytes,
        media_type: str | None,
        label: str,
        category: VaultDocumentCategory,
        purpose: VaultConsentPurpose,
        retention_days: int,
        consent: bool,
        document_id: str | None = None,
        now: datetime | None = None,
    ) -> VaultDocumentSummary:
        if not consent:
            raise VaultConsentError("必須針對這個檔案明確同意保存後才能上傳。")
        if not 1 <= int(retention_days) <= 365:
            raise VaultValidationError("保存期限必須介於 1 到 365 天。")
        clean_name, clean_media = self._validate_file(file_name, content, media_type)
        clean_label = " ".join(str(label or "").split())
        if not 2 <= len(clean_label) <= 100:
            raise VaultValidationError("文件名稱必須介於 2 到 100 個字。")
        current = _aware_utc(now or utc_now())
        existing = None
        if document_id:
            existing = self.repository.find_document(account_id, document_id)
            if existing is None:
                raise VaultNotFoundError("找不到這份私人文件。")
            versions = self.repository.list_versions(account_id, document_id)
            version_number = max((row.version_number for row in versions), default=0) + 1
            document = existing
        else:
            document_id = secrets.token_hex(16)
            label_ciphertext, label_nonce = self._encrypt_text(
                clean_label, f"vault-label:{account_id}:{document_id}".encode()
            )
            version_number = 1
            document = VaultDocumentRecord(
                id=document_id,
                account_id=account_id,
                label_ciphertext=label_ciphertext,
                label_nonce=label_nonce,
                category=category,
                created_at=current,
                updated_at=current,
            )
        version_id = secrets.token_hex(16)
        consent_id = secrets.token_hex(16)
        file_ciphertext, file_nonce = self._encrypt_text(
            clean_name,
            f"vault-filename:{account_id}:{document_id}:{version_id}".encode(),
        )
        ciphertext, wrapped_key, wrap_nonce, content_nonce = self._encrypt_content(
            content,
            account_id=account_id,
            document_id=document_id,
            version_id=version_id,
            version_number=version_number,
            media_type=clean_media,
        )
        fingerprint = self._fingerprint(account_id)
        object_key = f"vault/{fingerprint}-{document_id}-{version_id}.bin"
        expires_at = current + timedelta(days=int(retention_days))
        version = VaultDocumentVersionRecord(
            id=version_id,
            document_id=document_id,
            account_id=account_id,
            version_number=version_number,
            file_name_ciphertext=file_ciphertext,
            file_name_nonce=file_nonce,
            media_type=clean_media,
            plaintext_size=len(content),
            plaintext_sha256=hashlib.sha256(content).hexdigest(),
            ciphertext_size=len(ciphertext),
            ciphertext_sha256=hashlib.sha256(ciphertext).hexdigest(),
            object_key=object_key,
            wrapped_data_key=wrapped_key,
            wrap_nonce=wrap_nonce,
            content_nonce=content_nonce,
            consent_id=consent_id,
            retention_expires_at=expires_at,
            created_at=current,
        )
        consent_record = VaultConsentRecord(
            id=consent_id,
            account_id=account_id,
            document_id=document_id,
            version_id=version_id,
            purpose=purpose,
            retention_days=int(retention_days),
            terms_version=VAULT_TERMS_VERSION,
            granted_at=current,
            expires_at=expires_at,
        )
        self.repository.upload_object(object_key, ciphertext)
        try:
            if existing is None:
                self.repository.save_document(document)
            self.repository.save_version(version)
            self.repository.save_consent(consent_record)
            all_versions = [
                *self.repository.list_versions(account_id, document_id),
            ]
            document = document.model_copy(
                update={
                    "latest_version": max(row.version_number for row in all_versions),
                    "version_count": len(all_versions),
                    "updated_at": current,
                }
            )
            self.repository.save_document(document)
        except Exception:
            self.repository.delete_version(account_id, version_id)
            if existing is None:
                self.repository.delete_document(account_id, document_id)
            self.repository.delete_objects([object_key])
            raise
        self._audit(
            account_id,
            VaultAuditAction.VERSION_STORED,
            document_id=document_id,
            version_id=version_id,
            now=current,
        )
        return self.get_document(account_id, document_id, now=current)

    def _summary(
        self,
        document: VaultDocumentRecord,
        versions: list[VaultDocumentVersionRecord],
        consents: list[VaultConsentRecord],
    ) -> VaultDocumentSummary:
        consent_by_id = {row.id: row for row in consents}
        label = self._decrypt_text(
            document.label_ciphertext,
            document.label_nonce,
            f"vault-label:{document.account_id}:{document.id}".encode(),
        )
        summaries: list[VaultVersionSummary] = []
        for version in sorted(versions, key=lambda row: row.version_number, reverse=True):
            consent = consent_by_id.get(version.consent_id)
            if consent is None:
                raise VaultIntegrityError("私人文件版本缺少逐檔同意紀錄。")
            file_name = self._decrypt_text(
                version.file_name_ciphertext,
                version.file_name_nonce,
                (
                    f"vault-filename:{version.account_id}:{version.document_id}:"
                    f"{version.id}"
                ).encode(),
            )
            summaries.append(
                VaultVersionSummary(
                    id=version.id,
                    version_number=version.version_number,
                    file_name=file_name,
                    media_type=version.media_type,
                    size_bytes=version.plaintext_size,
                    sha256=version.plaintext_sha256,
                    purpose=consent.purpose,
                    retention_days=consent.retention_days,
                    consented_at=consent.granted_at,
                    expires_at=consent.expires_at,
                    created_at=version.created_at,
                )
            )
        return VaultDocumentSummary(
            id=document.id,
            label=label,
            category=document.category,
            latest_version=max((row.version_number for row in versions), default=1),
            versions=summaries,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def list_documents(
        self, account_id: str, *, now: datetime | None = None
    ) -> VaultDocumentList:
        current = _aware_utc(now or utc_now())
        documents = self.repository.list_documents(account_id)
        versions = [
            row
            for row in self.repository.list_versions(account_id)
            if row.retention_expires_at > current
        ]
        consents = [
            row
            for row in self.repository.list_consents(account_id)
            if row.expires_at > current and row.revoked_at is None
        ]
        by_document: dict[str, list[VaultDocumentVersionRecord]] = {}
        for version in versions:
            by_document.setdefault(version.document_id, []).append(version)
        items = [
            self._summary(
                document,
                by_document[document.id],
                [row for row in consents if row.document_id == document.id],
            )
            for document in documents
            if by_document.get(document.id)
        ]
        items.sort(key=lambda row: row.updated_at, reverse=True)
        return VaultDocumentList(
            items=items,
            total_bytes=sum(row.plaintext_size for row in versions),
        )

    def get_document(
        self,
        account_id: str,
        document_id: str,
        *,
        now: datetime | None = None,
    ) -> VaultDocumentSummary:
        document = self.repository.find_document(account_id, document_id)
        if document is None:
            raise VaultNotFoundError("找不到這份私人文件。")
        current = _aware_utc(now or utc_now())
        versions = [
            row
            for row in self.repository.list_versions(account_id, document_id)
            if row.retention_expires_at > current
        ]
        if not versions:
            raise VaultExpiredError("這份私人文件已超過保存期限。")
        return self._summary(
            document,
            versions,
            self.repository.list_consents(account_id, document_id),
        )

    def create_download_grant(
        self,
        account_id: str,
        version_id: str,
        *,
        now: datetime | None = None,
    ) -> VaultDownloadGrant:
        current = _aware_utc(now or utc_now())
        version = self.repository.find_version(account_id, version_id)
        if version is None:
            raise VaultNotFoundError("找不到這個私人文件版本。")
        if version.retention_expires_at <= current:
            raise VaultExpiredError("這個私人文件版本已超過保存期限。")
        self._require_active_consent(version, current)
        expires_at = current + timedelta(seconds=self.download_ttl_seconds)
        payload = {
            "v": version.id,
            "s": self._fingerprint(account_id),
            "exp": int(expires_at.timestamp()),
            "n": secrets.token_urlsafe(12),
        }
        encoded = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signature = _b64(hmac.new(self._signing_key, encoded.encode(), hashlib.sha256).digest())
        self._audit(
            account_id,
            VaultAuditAction.DOWNLOAD_GRANTED,
            document_id=version.document_id,
            version_id=version.id,
            now=current,
        )
        return VaultDownloadGrant(token=f"{encoded}.{signature}", expires_at=expires_at)

    def download(
        self,
        account_id: str,
        token: str,
        *,
        now: datetime | None = None,
    ) -> tuple[bytes, str, str]:
        current = _aware_utc(now or utc_now())
        try:
            encoded, signature = token.split(".", 1)
            expected = _b64(
                hmac.new(self._signing_key, encoded.encode(), hashlib.sha256).digest()
            )
            if not hmac.compare_digest(signature, expected):
                raise VaultAuthorizationError("私人文件下載授權無效。")
            payload = json.loads(_unb64(encoded))
        except VaultAuthorizationError:
            raise
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise VaultAuthorizationError("私人文件下載授權格式無效。") from error
        if payload.get("s") != self._fingerprint(account_id):
            raise VaultAuthorizationError("這個下載授權不屬於目前帳號。")
        if int(payload.get("exp", 0)) <= int(current.timestamp()):
            raise VaultExpiredError("私人文件下載授權已過期。")
        version = self.repository.find_version(account_id, str(payload.get("v", "")))
        if version is None:
            raise VaultNotFoundError("找不到這個私人文件版本。")
        if version.retention_expires_at <= current:
            raise VaultExpiredError("這個私人文件版本已超過保存期限。")
        # Re-check consent at download time. A grant issued before revocation must
        # not remain usable for the rest of its short TTL.
        self._require_active_consent(version, current)
        ciphertext = self.repository.read_object(version.object_key)
        plaintext = self._decrypt_content(version, ciphertext)
        file_name = self._decrypt_text(
            version.file_name_ciphertext,
            version.file_name_nonce,
            (
                f"vault-filename:{version.account_id}:{version.document_id}:"
                f"{version.id}"
            ).encode(),
        )
        self._audit(
            account_id,
            VaultAuditAction.DOWNLOADED,
            document_id=version.document_id,
            version_id=version.id,
            now=current,
        )
        return plaintext, file_name, version.media_type

    def _require_active_consent(
        self,
        version: VaultDocumentVersionRecord,
        current: datetime,
    ) -> VaultConsentRecord:
        consent = next(
            (
                row
                for row in self.repository.list_consents(
                    version.account_id,
                    version.document_id,
                )
                if row.id == version.consent_id
                and row.version_id == version.id
                and row.account_id == version.account_id
                and row.document_id == version.document_id
            ),
            None,
        )
        if (
            consent is None
            or consent.revoked_at is not None
            or _aware_utc(consent.expires_at) <= current
        ):
            raise VaultAuthorizationError(
                "這個私人文件版本已沒有有效的逐檔保存同意。"
            )
        return consent

    def delete_version(
        self,
        account_id: str,
        document_id: str,
        version_id: str,
        *,
        action: VaultAuditAction = VaultAuditAction.VERSION_DELETED,
        now: datetime | None = None,
    ) -> VaultDocumentSummary | None:
        document = self.repository.find_document(account_id, document_id)
        version = self.repository.find_version(account_id, version_id)
        if document is None or version is None or version.document_id != document_id:
            raise VaultNotFoundError("找不到這個私人文件版本。")
        versions = self.repository.list_versions(account_id, document_id)
        if len(versions) == 1:
            self.delete_document(account_id, document_id, action=action, now=now)
            return None
        self.repository.delete_objects([version.object_key])
        self.repository.delete_version(account_id, version_id)
        remaining = [row for row in versions if row.id != version_id]
        current = _aware_utc(now or utc_now())
        self.repository.save_document(
            document.model_copy(
                update={
                    "latest_version": max(row.version_number for row in remaining),
                    "version_count": len(remaining),
                    "updated_at": current,
                }
            )
        )
        self._audit(
            account_id,
            action,
            document_id=document_id,
            version_id=version_id,
            now=current,
        )
        return self.get_document(account_id, document_id, now=current)

    def delete_document(
        self,
        account_id: str,
        document_id: str,
        *,
        action: VaultAuditAction = VaultAuditAction.DOCUMENT_DELETED,
        now: datetime | None = None,
    ) -> None:
        document = self.repository.find_document(account_id, document_id)
        if document is None:
            raise VaultNotFoundError("找不到這份私人文件。")
        versions = self.repository.list_versions(account_id, document_id)
        self.repository.delete_objects([row.object_key for row in versions])
        self.repository.delete_document(account_id, document_id)
        self._audit(account_id, action, document_id=document_id, now=now)

    def purge_account(self, account_id: str, *, now: datetime | None = None) -> int:
        documents = self.repository.list_documents(account_id)
        for document in documents:
            self.delete_document(account_id, document.id, now=now)
        return len(documents)

    def cleanup(self, *, now: datetime | None = None) -> VaultCleanupResult:
        current = _aware_utc(now or utc_now())
        documents = self.repository.list_all_documents()
        expired: list[VaultDocumentVersionRecord] = []
        removed_documents: set[str] = set()
        for document in documents:
            versions = self.repository.list_versions(document.account_id, document.id)
            document_expired = [
                row for row in versions if row.retention_expires_at <= current
            ]
            expired.extend(document_expired)
            if not document_expired:
                continue
            if len(document_expired) == len(versions):
                self.delete_document(
                    document.account_id,
                    document.id,
                    action=VaultAuditAction.RETENTION_EXPIRED,
                    now=current,
                )
                removed_documents.add(document.id)
                continue
            for version in document_expired:
                self.delete_version(
                    version.account_id,
                    version.document_id,
                    version.id,
                    action=VaultAuditAction.RETENTION_EXPIRED,
                    now=current,
                )
        referenced = {
            row.object_key
            for document in self.repository.list_all_documents()
            for row in self.repository.list_versions(document.account_id, document.id)
        }
        orphaned = sorted(self.repository.list_object_keys() - referenced)
        if orphaned:
            self.repository.delete_objects(orphaned)
            self.repository.append_audit(
                VaultAuditRecord(
                    subject_fingerprint="0" * 32,
                    action=VaultAuditAction.ORPHAN_REMOVED,
                    created_at=current,
                )
            )
        return VaultCleanupResult(
            expired_version_count=len(expired),
            removed_document_count=len(removed_documents),
            orphan_object_count=len(orphaned),
            ran_at=current,
        )

def _decode_master_key(value: str) -> bytes:
    candidate = value.strip()
    if candidate.startswith("base64:"):
        candidate = candidate[7:]
    try:
        key = _unb64(candidate)
    except (ValueError, binascii.Error) as error:
        raise VaultConfigurationError("EXCHANGE_VAULT_MASTER_KEY 必須是 base64url。") from error
    if len(key) != 32:
        raise VaultConfigurationError("EXCHANGE_VAULT_MASTER_KEY 解碼後必須是 32 bytes。")
    return key


def _local_development_key(data_dir: Path) -> bytes:
    paths = ensure_data_dirs(data_dir)
    key_path = paths["vault_master_key"]
    if key_path.exists():
        return _decode_master_key(key_path.read_text(encoding="ascii"))
    key = secrets.token_bytes(32)
    key_path.write_text(_b64(key), encoding="ascii")
    try:
        key_path.chmod(0o600)
    except OSError:
        pass
    return key


def create_document_vault_service(
    data_dir: Path = DEFAULT_DATA_DIR,
    environ: Mapping[str, str] | None = None,
) -> DocumentVaultService:
    environment = os.environ if environ is None else environ
    mode = environment.get("EXCHANGE_VAULT_BACKEND", "auto").strip().casefold()
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
    key_value = environment.get("EXCHANGE_VAULT_MASTER_KEY", "").strip()
    if mode not in {"auto", "local", "supabase"}:
        raise VaultConfigurationError(
            "EXCHANGE_VAULT_BACKEND 必須是 auto、local 或 supabase。"
        )
    if bool(url) != bool(secret_key):
        raise VaultConfigurationError("Supabase URL 與 secret key 必須同時設定。")
    use_supabase = mode == "supabase" or (mode == "auto" and bool(url and secret_key))
    if runtime in {"production", "prod"} and not use_supabase:
        raise VaultConfigurationError("正式環境的私人文件庫必須使用 Supabase private Storage。")
    if use_supabase:
        if not url or not secret_key:
            raise VaultConfigurationError("Supabase 私人文件庫尚未完成伺服器端設定。")
        if not key_value:
            raise VaultConfigurationError("Supabase 私人文件庫必須設定 master key。")
        repository: DocumentVaultRepository = SupabaseDocumentVaultRepository(
            url,
            secret_key,
            bucket=environment.get("EXCHANGE_VAULT_BUCKET", DEFAULT_VAULT_BUCKET),
        )
        master_key = _decode_master_key(key_value)
    else:
        repository = LocalDocumentVaultRepository(data_dir)
        master_key = _decode_master_key(key_value) if key_value else _local_development_key(data_dir)
    try:
        ttl = int(
            environment.get(
                "EXCHANGE_VAULT_DOWNLOAD_TTL_SECONDS",
                str(DEFAULT_DOWNLOAD_TTL_SECONDS),
            )
        )
    except ValueError as error:
        raise VaultConfigurationError(
            "EXCHANGE_VAULT_DOWNLOAD_TTL_SECONDS 必須是整數。"
        ) from error
    return DocumentVaultService(
        repository,
        master_key,
        download_ttl_seconds=ttl,
    )
