"""Behavior needed before increasing the self-hosted web worker count."""
import hashlib
from types import SimpleNamespace

from fastapi.testclient import TestClient

import exchange_info.api as api
import exchange_info.analytics as analytics
from exchange_info.analytics import AnalyticsService
from exchange_info.repositories import JsonlAccountRepository


def test_logout_deletes_only_its_token_without_reading_or_replacing_other_sessions(tmp_path, monkeypatch):
    repository = JsonlAccountRepository(tmp_path)
    client = TestClient(api.create_app(tmp_path, account_repository=repository))
    deleted = []

    def forbidden(*args, **kwargs):
        raise AssertionError("logout must not read or replace all sessions")

    monkeypatch.setattr(api, "load_account_sessions", forbidden)
    monkeypatch.setattr(api, "save_account_sessions", forbidden)
    repository.delete_session_by_token_hash = deleted.append
    response = client.post("/auth/logout", headers={"Authorization": "Bearer one-session"})
    assert response.status_code == 204
    assert deleted == [hashlib.sha256(b"one-session").hexdigest()]
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_status_shares_expensive_metadata_but_keeps_runtime_state_live(tmp_path, monkeypatch):
    client = TestClient(api.create_app(tmp_path))
    now = [10.0]
    runtime = ["paused"]
    scans = []
    indexes = []
    monkeypatch.setattr(api, "time", SimpleNamespace(monotonic=lambda: now[0]))
    monkeypatch.setattr(api, "ai_runtime_state", lambda: runtime[0])
    monkeypatch.setattr(api, "ai_enabled", lambda: False)

    def sources(*args):
        scans.append(1)
        return [None] * len(scans)

    def index(*args):
        indexes.append(1)
        return SimpleNamespace(model_dump=lambda **kwargs: {"source_count": len(indexes)})

    monkeypatch.setattr(api, "load_structured_sources", sources)
    monkeypatch.setattr(api, "rag_index_status", index)
    first = client.get("/ai/status").json()
    runtime[0] = "offline"
    second = client.get("/advisor/status").json()
    assert first["runtime_state"] == "paused"
    assert second["runtime_state"] == "offline"
    assert second["rag_index"] == first["rag_index"]
    assert len(scans) == len(indexes) == 1
    now[0] += 6
    third = client.get("/ai/status").json()
    assert third["structured_source_count"] == 2
    assert len(scans) == len(indexes) == 2


def test_request_burst_schedules_only_one_metrics_flush_and_can_schedule_again(monkeypatch):
    pending = []
    saved = []
    repository = SimpleNamespace(record_api_metrics=lambda rows: saved.extend(rows))
    service = AnalyticsService(repository, flush_seconds=1)
    service._last_flush = float("-inf")

    class DelayedThread:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            pending.append(self.target)

    monkeypatch.setattr(analytics.threading, "Thread", DelayedThread)
    for _ in range(1000):
        service.record_request("/ai/status", "GET", 200, 2)
    assert len(pending) == 1
    pending.pop()()
    assert sum(row.request_count for row in saved) == 1000
    service._last_flush = float("-inf")
    service.record_request("/ai/status", "GET", 200, 2)
    assert len(pending) == 1
    pending.pop()()
    assert sum(row.request_count for row in saved) == 1001
