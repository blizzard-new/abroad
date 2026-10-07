from __future__ import annotations

import os
import threading
from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import Any, Protocol

import requests
from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import supabase_http
from .supabase_keys import supabase_key_headers
from .models import utc_now


class TransientAuthStateKind(str, Enum):
    OAUTH_LOGIN = "oauth_login"
    STUDENT_VERIFICATION_OAUTH = "student_verification_oauth"
    STUDENT_VERIFICATION_SESSION = "student_verification_session"


class TransientAuthState(BaseModel):
    model_config = ConfigDict(frozen=True)

    state_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    kind: TransientAuthStateKind
    provider_id: str | None = None
    account_id: str | None = None
    session_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime

    @field_validator("expires_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("transient auth expiry must include a timezone")
        return value


class TransientAuthStoreError(RuntimeError):
    pass


class TransientAuthStoreConfigurationError(TransientAuthStoreError):
    pass


class TransientAuthRateLimitError(TransientAuthStoreError):
    pass


class TransientAuthCapacityError(TransientAuthStoreError):
    pass


class TransientAuthStore(Protocol):
    backend_name: str

    def save_state(self, record: TransientAuthState) -> TransientAuthState: ...

    def start_oauth_state(
        self,
        record: TransientAuthState,
        *,
        client_fingerprint: str,
        window_start: datetime,
        start_limit: int,
        max_active: int,
        replace_session: bool = False,
    ) -> TransientAuthState: ...

    def get_state(
        self,
        state_hash: str,
        kind: TransientAuthStateKind,
    ) -> TransientAuthState | None: ...

    def consume_state(
        self,
        state_hash: str,
        kind: TransientAuthStateKind,
        *,
        expected_account_id: str | None = None,
        expected_session_id: str | None = None,
        expected_provider_id: str | None = None,
    ) -> TransientAuthState | None: ...

    def delete_account_states(self, account_id: str) -> int: ...


def _matches_expected(
    record: TransientAuthState,
    *,
    expected_account_id: str | None,
    expected_session_id: str | None,
    expected_provider_id: str | None,
) -> bool:
    return (
        (expected_account_id is None or record.account_id == expected_account_id)
        and (expected_session_id is None or record.session_id == expected_session_id)
        and (expected_provider_id is None or record.provider_id == expected_provider_id)
    )


class LocalTransientAuthStore:
    backend_name = "memory"

    def __init__(self) -> None:
        self._states: dict[str, TransientAuthState] = {}
        self._rate_events: dict[tuple[TransientAuthStateKind, str], list[datetime]] = {}
        self._lock = threading.RLock()

    def _purge(self, now: datetime) -> None:
        for state_hash in [
            key for key, row in self._states.items() if row.expires_at <= now
        ]:
            self._states.pop(state_hash, None)

    def save_state(self, record: TransientAuthState) -> TransientAuthState:
        now = utc_now()
        with self._lock:
            self._purge(now)
            if record.expires_at <= now:
                raise TransientAuthStoreError("不能保存已過期的 transient auth state。")
            if record.state_hash in self._states:
                raise TransientAuthStoreError("transient auth state 發生雜湊碰撞。")
            self._states[record.state_hash] = record.model_copy(deep=True)
        return record

    def start_oauth_state(
        self,
        record: TransientAuthState,
        *,
        client_fingerprint: str,
        window_start: datetime,
        start_limit: int,
        max_active: int,
        replace_session: bool = False,
    ) -> TransientAuthState:
        if record.kind not in {
            TransientAuthStateKind.OAUTH_LOGIN,
            TransientAuthStateKind.STUDENT_VERIFICATION_OAUTH,
        }:
            raise TransientAuthStoreError("只有 OAuth state 可以使用啟動限流。")
        if start_limit < 1 or max_active < 1:
            raise TransientAuthStoreError("OAuth state 限流與容量必須大於零。")
        if replace_session and (
            not record.session_id or not record.provider_id
        ):
            raise TransientAuthStoreError("替換 OAuth state 必須綁定 provider 與 session。")

        now = utc_now()
        rate_key = (record.kind, client_fingerprint)
        with self._lock:
            self._purge(now)
            recent_events = [
                event
                for event in self._rate_events.get(rate_key, [])
                if event > window_start
            ]
            if len(recent_events) >= start_limit:
                self._rate_events[rate_key] = recent_events
                raise TransientAuthRateLimitError("OAuth 重新導向嘗試過於頻繁。")

            replacement_keys = [
                key
                for key, existing in self._states.items()
                if replace_session
                and existing.kind == record.kind
                and existing.provider_id == record.provider_id
                and existing.session_id == record.session_id
            ]
            active_count = sum(
                1
                for key, existing in self._states.items()
                if existing.kind == record.kind and key not in replacement_keys
            )
            if active_count >= max_active:
                raise TransientAuthCapacityError("OAuth state 暫存容量已滿。")
            if record.state_hash in self._states and record.state_hash not in replacement_keys:
                raise TransientAuthStoreError("transient auth state 發生雜湊碰撞。")

            for key in replacement_keys:
                self._states.pop(key, None)
            self._rate_events[rate_key] = [*recent_events, now]
            self._states[record.state_hash] = record.model_copy(deep=True)
        return record

    def get_state(
        self,
        state_hash: str,
        kind: TransientAuthStateKind,
    ) -> TransientAuthState | None:
        now = utc_now()
        with self._lock:
            self._purge(now)
            record = self._states.get(state_hash)
            if record is None or record.kind != kind:
                return None
            return record.model_copy(deep=True)

    def consume_state(
        self,
        state_hash: str,
        kind: TransientAuthStateKind,
        *,
        expected_account_id: str | None = None,
        expected_session_id: str | None = None,
        expected_provider_id: str | None = None,
    ) -> TransientAuthState | None:
        now = utc_now()
        with self._lock:
            self._purge(now)
            record = self._states.get(state_hash)
            if record is None or record.kind != kind:
                return None
            if not _matches_expected(
                record,
                expected_account_id=expected_account_id,
                expected_session_id=expected_session_id,
                expected_provider_id=expected_provider_id,
            ):
                return None
            self._states.pop(state_hash, None)
            return record.model_copy(deep=True)

    def delete_account_states(self, account_id: str) -> int:
        now = utc_now()
        with self._lock:
            self._purge(now)
            keys = [
                key
                for key, record in self._states.items()
                if record.account_id == account_id
            ]
            for key in keys:
                self._states.pop(key, None)
            return len(keys)


class SupabaseTransientAuthStore:
    backend_name = "supabase"

    def __init__(
        self,
        url: str,
        secret_key: str,
        *,
        request_func=supabase_http.request,
    ) -> None:
        if not url.strip().casefold().startswith("https://"):
            raise TransientAuthStoreConfigurationError(
                "Supabase URL 必須使用 HTTPS。"
            )
        if not secret_key.strip():
            raise TransientAuthStoreConfigurationError(
                "Supabase transient auth store 缺少 server secret。"
            )
        self.url = url.rstrip("/")
        self.secret_key = secret_key
        self.request_func = request_func

    @property
    def headers(self) -> dict[str, str]:
        return {
            **supabase_key_headers(self.secret_key),
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs):
        response = self.request_func(
            method,
            f"{self.url}/rest/v1/{path}",
            headers={**self.headers, **kwargs.pop("headers", {})},
            timeout=20,
            **kwargs,
        )
        response.raise_for_status()
        return response

    @staticmethod
    def _record_from_payload(payload: object) -> TransientAuthState | None:
        if payload is None:
            return None
        if isinstance(payload, list):
            payload = payload[0] if payload else None
        if not isinstance(payload, dict):
            raise TransientAuthStoreError(
                "Supabase transient auth store 回傳非預期格式。"
            )
        return TransientAuthState.model_validate(payload)

    @staticmethod
    def _record_rpc_body(record: TransientAuthState) -> dict[str, object]:
        return {
            "p_state_hash": record.state_hash,
            "p_kind": record.kind.value,
            "p_provider_id": record.provider_id,
            "p_account_id": record.account_id,
            "p_session_id": record.session_id,
            "p_payload": record.payload,
            "p_expires_at": record.expires_at.isoformat(),
        }

    def save_state(self, record: TransientAuthState) -> TransientAuthState:
        response = self._request(
            "POST",
            "rpc/exchange_save_transient_auth_state",
            json=self._record_rpc_body(record),
        )
        saved = self._record_from_payload(response.json())
        if saved is None:
            raise TransientAuthStoreError("Supabase 未保存 transient auth state。")
        return saved

    def start_oauth_state(
        self,
        record: TransientAuthState,
        *,
        client_fingerprint: str,
        window_start: datetime,
        start_limit: int,
        max_active: int,
        replace_session: bool = False,
    ) -> TransientAuthState:
        response = self._request(
            "POST",
            "rpc/exchange_start_transient_auth_state",
            json={
                **self._record_rpc_body(record),
                "p_client_fingerprint": client_fingerprint,
                "p_window_start": window_start.isoformat(),
                "p_start_limit": start_limit,
                "p_max_active": max_active,
                "p_replace_session": replace_session,
            },
        )
        payload = response.json()
        if isinstance(payload, list):
            payload = payload[0] if payload else None
        if not isinstance(payload, dict):
            raise TransientAuthStoreError(
                "Supabase OAuth state 啟動回傳非預期格式。"
            )
        status = payload.get("status")
        if status == "rate_limited":
            raise TransientAuthRateLimitError("OAuth 重新導向嘗試過於頻繁。")
        if status == "capacity_reached":
            raise TransientAuthCapacityError("OAuth state 暫存容量已滿。")
        if status != "created":
            raise TransientAuthStoreError("Supabase 未建立 OAuth state。")
        return record

    def get_state(
        self,
        state_hash: str,
        kind: TransientAuthStateKind,
    ) -> TransientAuthState | None:
        response = self._request(
            "GET",
            "exchange_transient_auth_states",
            params={
                "select": "state_hash,kind,provider_id,account_id,session_id,payload,expires_at",
                "state_hash": f"eq.{state_hash}",
                "kind": f"eq.{kind.value}",
                "expires_at": f"gt.{utc_now().isoformat()}",
                "limit": "1",
            },
        )
        return self._record_from_payload(response.json())

    def consume_state(
        self,
        state_hash: str,
        kind: TransientAuthStateKind,
        *,
        expected_account_id: str | None = None,
        expected_session_id: str | None = None,
        expected_provider_id: str | None = None,
    ) -> TransientAuthState | None:
        response = self._request(
            "POST",
            "rpc/exchange_consume_transient_auth_state",
            json={
                "p_state_hash": state_hash,
                "p_kind": kind.value,
                "p_expected_account_id": expected_account_id,
                "p_expected_session_id": expected_session_id,
                "p_expected_provider_id": expected_provider_id,
            },
        )
        return self._record_from_payload(response.json())

    def delete_account_states(self, account_id: str) -> int:
        response = self._request(
            "DELETE",
            "exchange_transient_auth_states",
            params={"account_id": f"eq.{account_id}", "select": "state_hash"},
            headers={"Prefer": "return=representation"},
        )
        payload = response.json()
        if not isinstance(payload, list):
            raise TransientAuthStoreError(
                "Supabase transient auth 刪除回傳非預期格式。"
            )
        return len(payload)


def create_transient_auth_store(
    environ: Mapping[str, str] | None = None,
) -> TransientAuthStore:
    environment = os.environ if environ is None else environ
    runtime = environment.get("EXCHANGE_ENVIRONMENT", "development").strip().casefold()
    mode = environment.get("EXCHANGE_TRANSIENT_AUTH_BACKEND", "auto").strip().casefold()
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

    if mode not in {"auto", "memory", "supabase"}:
        raise TransientAuthStoreConfigurationError(
            "EXCHANGE_TRANSIENT_AUTH_BACKEND 必須是 auto、memory 或 supabase。"
        )
    if runtime in {"production", "prod"} and mode == "memory":
        raise TransientAuthStoreConfigurationError(
            "正式環境的 OAuth 與學生驗證 state 必須使用 Supabase。"
        )
    if bool(url) != bool(secret_key):
        raise TransientAuthStoreConfigurationError(
            "Supabase URL 與 secret key 必須同時設定。"
        )
    if mode == "supabase" or (mode == "auto" and url and secret_key):
        if not url or not secret_key:
            raise TransientAuthStoreConfigurationError(
                "Supabase transient auth store 尚未完成伺服器端設定。"
            )
        return SupabaseTransientAuthStore(url, secret_key)
    if runtime in {"production", "prod"}:
        raise TransientAuthStoreConfigurationError(
            "正式環境的 OAuth 與學生驗證 state 必須使用 Supabase。"
        )
    return LocalTransientAuthStore()
