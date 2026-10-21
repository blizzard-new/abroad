"""A signed-in request used to cost three round trips to the database before any work began; now they are kept briefly."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

import exchange_info.repositories as repositories
from exchange_info.models import AccountSessionRecord, utc_now
from exchange_info.repositories import SupabaseAccountRepository, create_account_repository

TOKEN_HASH = "a" * 64


class _Response:
    def __init__(self, payload: Any) -> None:
        self._payload = payload
        self.content = b"x"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._payload


class _Database:
    """Answers the three lookups of a signed-in request and records every call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.display_name = "一號"

    def request(self, method: str, url: str, **kwargs: Any) -> _Response:
        table = url.rsplit("/", 1)[-1]
        self.calls.append((method, table))
        now = utc_now().isoformat()
        if table == "exchange_authenticate_account" and method == "POST":
            return _Response({
                "status": "valid",
                "session": {
                    "id": "s1", "account_id": "acc-1", "token_hash": TOKEN_HASH,
                    "expires_at": (utc_now() + timedelta(days=1)).isoformat(), "created_at": now,
                },
                "account": {
                    "id": "acc-1", "email": "a@example.com", "created_at": now, "updated_at": now,
                    "community_suspended_until": None,
                    "profile": {"display_name": self.display_name, "email_verified": True},
                    "workspaces": [],
                },
            })
        if table == "exchange_account_sessions" and method == "GET":
            return _Response([{"id": "s1", "account_id": "acc-1", "token_hash": TOKEN_HASH,
                               "expires_at": (utc_now() + timedelta(days=1)).isoformat(), "created_at": now}])
        if table == "exchange_accounts" and method == "GET":
            return _Response([{"id": "acc-1", "email": "a@example.com", "created_at": now, "updated_at": now,
                               "community_suspended_until": None,
                               "profile": {"display_name": self.display_name, "email_verified": True}}])
        if table == "exchange_account_workspaces":
            return _Response([])
        return _Response([])

    def reads(self) -> int:
        return sum(1 for method, _ in self.calls if method == "GET")


def _repository(database: _Database, seconds: float) -> SupabaseAccountRepository:
    return SupabaseAccountRepository("https://example.supabase.co", "sb_secret_test",
                                     request_session=database, read_cache_seconds=seconds)


def _sign_in_lookup(repository: SupabaseAccountRepository):
    session = repository.find_session_by_token_hash(TOKEN_HASH)
    return session, repository.find_account_by_id(session.account_id)


def test_the_three_lookups_of_a_signed_in_request_happen_once_within_the_window() -> None:
    database = _Database()
    repository = _repository(database, 30)
    _sign_in_lookup(repository)
    assert database.reads() == 3
    for _ in range(5):
        session, account = _sign_in_lookup(repository)
    assert database.reads() == 3, "the next five requests were answered without asking the database"
    assert session.account_id == "acc-1" and account.display_name == "一號"


def test_it_is_off_unless_asked_for() -> None:
    database = _Database()
    repository = _repository(database, 0)
    _sign_in_lookup(repository)
    _sign_in_lookup(repository)
    assert database.reads() == 6


def test_any_write_through_the_repository_drops_what_was_kept() -> None:
    database = _Database()
    repository = _repository(database, 30)
    _sign_in_lookup(repository)
    repository.save_session(AccountSessionRecord(account_id="acc-1", token_hash="b" * 64, expires_at=utc_now() + timedelta(days=1)))
    database.display_name = "改過名字"
    _, account = _sign_in_lookup(repository)
    assert account.display_name == "改過名字", "a write made through this process is visible on the next request"

    repository.delete_session_by_token_hash(TOKEN_HASH)
    reads_before = database.reads()
    _sign_in_lookup(repository)
    assert database.reads() == reads_before + 3


def test_the_window_ends() -> None:
    database = _Database()
    repository = _repository(database, 30)
    clock = [1000.0]
    original = repositories.time.monotonic
    repositories.time.monotonic = lambda: clock[0]
    try:
        _sign_in_lookup(repository)
        clock[0] += 29
        _sign_in_lookup(repository)
        assert database.reads() == 3
        clock[0] += 2
        _sign_in_lookup(repository)
        assert database.reads() == 6
    finally:
        repositories.time.monotonic = original


def test_each_caller_gets_its_own_copy_and_a_missing_account_is_not_invented() -> None:
    database = _Database()
    repository = _repository(database, 30)
    _, first = _sign_in_lookup(repository)
    first.display_name = "被呼叫端改掉"
    first.target_countries.append("日本")
    _, second = _sign_in_lookup(repository)
    assert second.display_name == "一號" and second.target_countries == []

    class Empty(_Database):
        def request(self, method, url, **kwargs):
            self.calls.append((method, url.rsplit("/", 1)[-1]))
            return _Response([])

    empty = Empty()
    missing = _repository(empty, 30)
    assert missing.find_session_by_token_hash(TOKEN_HASH) is None
    assert missing.find_session_by_token_hash(TOKEN_HASH) is None


def test_the_production_factory_turns_it_on_and_the_setting_can_turn_it_off() -> None:
    env = {"EXCHANGE_SUPABASE_URL": "https://example.supabase.co", "EXCHANGE_SUPABASE_SECRET_KEY": "sb_secret_test",
           "EXCHANGE_ACCOUNT_REPOSITORY": "supabase"}
    assert create_account_repository(Path("."), env)._read_cache_seconds == 20
    assert create_account_repository(Path("."), {**env, "EXCHANGE_ACCOUNT_READ_CACHE_SECONDS": "0"})._read_cache_seconds == 0


def test_uncached_workers_see_another_workers_account_update_and_session_revocation(tmp_path, monkeypatch):
    import hashlib
    from fastapi.testclient import TestClient
    from exchange_info.api import create_app

    token = "isolated-capacity-test-session"
    monkeypatch.setitem(globals(), "TOKEN_HASH", hashlib.sha256(token.encode()).hexdigest())
    class SharedDatabase(_Database):
        revoked = False

        def request(self, method, url, **kwargs):
            table = url.rsplit("/", 1)[-1]
            if table == "exchange_authenticate_account" and self.revoked:
                return _Response({"status": "invalid"})
            if table == "exchange_account_sessions":
                if method == "DELETE":
                    assert kwargs["params"] == {"token_hash": f"eq.{TOKEN_HASH}"}
                    self.revoked = True
                    return _Response([])
                if method == "GET" and self.revoked:
                    return _Response([])
            return super().request(method, url, **kwargs)

    database = SharedDatabase()
    first, second = _repository(database, 0), _repository(database, 0)
    first_client = TestClient(create_app(tmp_path / "first", account_repository=first))
    second_client = TestClient(create_app(tmp_path / "second", account_repository=second))
    headers = {"Authorization": f"Bearer {token}"}
    _sign_in_lookup(first)
    _sign_in_lookup(second)
    assert second_client.get("/auth/me", headers=headers).status_code == 200
    database.display_name = "另一個程序剛剛更新"
    assert second_client.get("/auth/me", headers=headers).json()["display_name"] == database.display_name
    assert first_client.post("/auth/logout", headers=headers).status_code == 204
    assert second_client.get("/auth/me", headers=headers).status_code == 401
    assert second.find_session_by_token_hash(TOKEN_HASH) is None
