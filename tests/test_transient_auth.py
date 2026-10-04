from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from exchange_info.models import utc_now
from exchange_info.transient_auth import (
    LocalTransientAuthStore,
    SupabaseTransientAuthStore,
    TransientAuthCapacityError,
    TransientAuthRateLimitError,
    TransientAuthState,
    TransientAuthStateKind,
    TransientAuthStoreConfigurationError,
    create_transient_auth_store,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPOSITORY_ROOT
    / "supabase"
    / "migrations"
    / "20260821190000_transient_auth_state.sql"
)


class _Response:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class _RequestRecorder:
    def __init__(self, *payloads: object) -> None:
        self.payloads = list(payloads)
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def __call__(self, method: str, url: str, **kwargs) -> _Response:
        self.calls.append((method, url, kwargs))
        return _Response(self.payloads.pop(0))


def _state(
    suffix: str,
    *,
    kind: TransientAuthStateKind = TransientAuthStateKind.OAUTH_LOGIN,
    provider_id: str = "google",
    account_id: str | None = None,
    session_id: str | None = None,
) -> TransientAuthState:
    return TransientAuthState(
        state_hash=(suffix * 64)[:64],
        kind=kind,
        provider_id=provider_id,
        account_id=account_id,
        session_id=session_id,
        payload={"marker": suffix},
        expires_at=utc_now() + timedelta(minutes=10),
    )


def test_local_store_consumes_once_without_wrong_identity_destroying_state() -> None:
    store = LocalTransientAuthStore()
    record = _state(
        "a",
        kind=TransientAuthStateKind.STUDENT_VERIFICATION_OAUTH,
        provider_id="cgu-microsoft",
        account_id="account-a",
        session_id="session-a",
    )
    store.start_oauth_state(
        record,
        client_fingerprint="client-a",
        window_start=utc_now() - timedelta(minutes=10),
        start_limit=20,
        max_active=100,
        replace_session=True,
    )

    assert store.consume_state(
        record.state_hash,
        record.kind,
        expected_account_id="wrong-account",
        expected_session_id="session-a",
        expected_provider_id="cgu-microsoft",
    ) is None
    assert store.get_state(record.state_hash, record.kind) == record

    consumed = store.consume_state(
        record.state_hash,
        record.kind,
        expected_account_id="account-a",
        expected_session_id="session-a",
        expected_provider_id="cgu-microsoft",
    )
    assert consumed == record
    assert store.consume_state(record.state_hash, record.kind) is None


def test_local_store_enforces_shared_rate_capacity_and_session_replacement() -> None:
    store = LocalTransientAuthStore()
    now = utc_now()
    first = _state("b")
    store.start_oauth_state(
        first,
        client_fingerprint="client-a",
        window_start=now - timedelta(minutes=10),
        start_limit=1,
        max_active=10,
    )
    with pytest.raises(TransientAuthRateLimitError):
        store.start_oauth_state(
            _state("c"),
            client_fingerprint="client-a",
            window_start=now - timedelta(minutes=10),
            start_limit=1,
            max_active=10,
        )

    with pytest.raises(TransientAuthCapacityError):
        store.start_oauth_state(
            _state("d"),
            client_fingerprint="client-b",
            window_start=now - timedelta(minutes=10),
            start_limit=20,
            max_active=1,
        )

    original = _state(
        "e",
        kind=TransientAuthStateKind.STUDENT_VERIFICATION_OAUTH,
        provider_id="cgu-microsoft",
        account_id="account-a",
        session_id="session-a",
    )
    replacement = original.model_copy(
        update={
            "state_hash": "f" * 64,
            "payload": {"marker": "replacement"},
        }
    )
    store = LocalTransientAuthStore()
    for record in (original, replacement):
        store.start_oauth_state(
            record,
            client_fingerprint=f"client-{record.state_hash[0]}",
            window_start=now - timedelta(minutes=10),
            start_limit=20,
            max_active=1,
            replace_session=True,
        )
    assert store.get_state(original.state_hash, original.kind) is None
    assert store.get_state(replacement.state_hash, replacement.kind) == replacement


def test_student_verification_session_is_ttl_bound_and_account_purgeable() -> None:
    store = LocalTransientAuthStore()
    record = _state(
        "1",
        kind=TransientAuthStateKind.STUDENT_VERIFICATION_SESSION,
        provider_id="student-card",
        account_id="account-a",
    )
    store.save_state(record)

    assert store.get_state(record.state_hash, record.kind) == record
    assert store.delete_account_states("account-a") == 1
    assert store.get_state(record.state_hash, record.kind) is None


def test_transient_auth_factory_forbids_memory_in_production() -> None:
    with pytest.raises(
        TransientAuthStoreConfigurationError,
        match="正式環境",
    ):
        create_transient_auth_store(
            {
                "EXCHANGE_ENVIRONMENT": "production",
                "EXCHANGE_TRANSIENT_AUTH_BACKEND": "memory",
            }
        )


def test_supabase_store_uses_atomic_start_and_consume_rpcs() -> None:
    record = _state(
        "9",
        kind=TransientAuthStateKind.STUDENT_VERIFICATION_OAUTH,
        provider_id="ntpu-entra",
        account_id="account-a",
        session_id="session-a",
    )
    request = _RequestRecorder(
        {"status": "created"},
        record.model_dump(mode="json"),
    )
    store = SupabaseTransientAuthStore(
        "https://project.supabase.co",
        "server-secret",
        request_func=request,
    )

    started = store.start_oauth_state(
        record,
        client_fingerprint="8" * 64,
        window_start=utc_now() - timedelta(minutes=10),
        start_limit=20,
        max_active=2048,
        replace_session=True,
    )
    consumed = store.consume_state(
        record.state_hash,
        record.kind,
        expected_account_id="account-a",
        expected_session_id="session-a",
        expected_provider_id="ntpu-entra",
    )

    assert started == record
    assert consumed == record
    assert request.calls[0][0:2] == (
        "POST",
        "https://project.supabase.co/rest/v1/rpc/exchange_start_transient_auth_state",
    )
    assert request.calls[0][2]["json"]["p_client_fingerprint"] == "8" * 64
    assert request.calls[0][2]["json"]["p_replace_session"] is True
    assert request.calls[1][0:2] == (
        "POST",
        "https://project.supabase.co/rest/v1/rpc/exchange_consume_transient_auth_state",
    )
    assert request.calls[1][2]["json"]["p_expected_account_id"] == "account-a"
    assert request.calls[1][2]["json"]["p_expected_session_id"] == "session-a"


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [
        ("rate_limited", TransientAuthRateLimitError),
        ("capacity_reached", TransientAuthCapacityError),
    ],
)
def test_supabase_store_maps_atomic_start_rejections(
    status: str,
    expected_error: type[Exception],
) -> None:
    request = _RequestRecorder({"status": status})
    store = SupabaseTransientAuthStore(
        "https://project.supabase.co",
        "server-secret",
        request_func=request,
    )

    with pytest.raises(expected_error):
        store.start_oauth_state(
            _state("7"),
            client_fingerprint="6" * 64,
            window_start=utc_now() - timedelta(minutes=10),
            start_limit=20,
            max_active=2048,
        )


def test_supabase_migration_keeps_transient_auth_private_and_atomic() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").casefold()

    assert "exchange_transient_auth_states" in sql
    assert "exchange_transient_auth_rate_events" in sql
    assert "exchange_start_transient_auth_state" in sql
    assert "exchange_consume_transient_auth_state" in sql
    assert "pg_advisory_xact_lock" in sql
    assert "enable row level security" in sql
    assert "revoke all" in sql
    assert "from anon, authenticated" in sql
    assert "grant execute" in sql
    assert "to service_role" in sql
