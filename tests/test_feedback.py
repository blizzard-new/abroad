"""User feedback: anyone can leave a message, only an administrator reads it, and nothing identifies the sender."""
from __future__ import annotations

import hashlib
from datetime import timedelta

import pytest
import requests
from fastapi.testclient import TestClient

from exchange_info.analytics import RateLimiter
from exchange_info.api import PRODUCTION_PERSISTENCE_BACKENDS, create_app
from exchange_info.feedback import (
    FeedbackRecord,
    FeedbackRepositoryError,
    FeedbackService,
    FeedbackSubmission,
    JsonlFeedbackRepository,
    SupabaseFeedbackRepository,
    create_feedback_repository,
    csv_cell,
)
from exchange_info.models import AccountSessionRecord, UserAccount, utc_now
from exchange_info.storage import save_account_sessions, save_user_accounts

MESSAGE = {"kind": "suggestion", "rating": 4, "message": "希望學校搜尋可以直接比較學費。", "contact": "", "route": "partners", "home_school": "長庚大學"}


@pytest.fixture
def site(tmp_path, monkeypatch):
    monkeypatch.setenv("EXCHANGE_ACCOUNT_REPOSITORY", "jsonl")
    monkeypatch.setenv("EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS", "admin-id")
    accounts = [
        UserAccount(id="admin-id", display_name="管理員", email_verified=True),
        UserAccount(id="student-id", display_name="一般同學", email_verified=True),
    ]
    save_user_accounts(accounts, tmp_path)
    save_account_sessions([AccountSessionRecord(
        account_id=a.id, token_hash=hashlib.sha256(a.id.encode()).hexdigest(),
        expires_at=utc_now() + timedelta(days=1)) for a in accounts], tmp_path)
    client = TestClient(create_app(tmp_path))
    client.admin = {"Authorization": "Bearer admin-id"}
    client.student = {"Authorization": "Bearer student-id"}
    client.data_dir = tmp_path
    return client


def inbox(client, **params):
    response = client.get("/admin/feedback/list", params=params, headers=client.admin)
    assert response.status_code == 200, response.text
    return response.json()


# ----------------------------------------------------------------------------- the form


def test_anyone_can_leave_a_message_and_the_answer_reveals_nothing(site):
    response = site.post("/feedback", json=MESSAGE)
    assert response.status_code == 201 and response.json() == {"ok": True}
    assert response.headers["cache-control"] == "no-store"
    row = inbox(site)["items"][0]
    assert row["message"] == MESSAGE["message"] and row["rating"] == 4 and row["kind"] == "suggestion"
    assert row["route"] == "partners" and row["home_school"] == "長庚大學"
    assert row["status"] == "new" and row["signed_in"] is False


def test_nothing_that_identifies_the_sender_is_stored(site):
    site.post("/feedback", json=MESSAGE, headers=site.student)
    stored = site.app.state.feedback_service.repository.list()[0]
    assert set(stored.model_dump()) == {"id", "created_at", "kind", "rating", "message", "contact", "route", "home_school",
                                         "signed_in", "status", "admin_note", "handled_at"}
    assert stored.signed_in is True, "only whether they were signed in"
    assert "student-id" not in stored.model_dump_json() and "testclient" not in stored.model_dump_json()


@pytest.mark.parametrize("change", [
    {"message": "好"},                      # too short
    {"message": "字" * 2001},               # too long
    {"kind": "complaint"},                  # not one of the kinds
    {"rating": 6}, {"rating": 0},
    {"contact": "x" * 121},
    {"unexpected": "field"},
])
def test_a_message_that_does_not_fit_the_form_is_refused(site, change):
    assert site.post("/feedback", json={**MESSAGE, **change}).status_code == 422
    assert inbox(site)["total"] == 0


def test_spaces_and_control_characters_are_cleaned_but_words_are_kept_as_typed(site):
    body = {**MESSAGE, "message": "  第一行\x00\x07\r\n\r\n\r\n\r\n第二行 <b>粗體</b>  "}
    assert site.post("/feedback", json=body).status_code == 201
    row = inbox(site)["items"][0]
    assert row["message"] == "第一行\n\n第二行 <b>粗體</b>", "plain text; the page shows it as text, never as markup"


def test_a_bot_that_fills_the_hidden_field_is_thanked_and_ignored(site):
    assert site.post("/feedback", json={**MESSAGE, "website": "http://spam.example"}).status_code == 201
    assert inbox(site)["total"] == 0


def test_a_pile_of_links_is_refused(site):
    spam = "看這裡 http://a.example http://b.example http://c.example"
    assert site.post("/feedback", json={**MESSAGE, "message": spam}).status_code == 422
    assert site.post("/feedback", json={**MESSAGE, "message": "參考 https://example.org/a 這篇"}).status_code == 201


def test_too_many_messages_in_a_short_time_are_slowed_down(site):
    for index in range(3):
        assert site.post("/feedback", json={**MESSAGE, "message": f"第 {index} 則建議，內容夠長"}).status_code == 201
    slow = site.post("/feedback", json={**MESSAGE, "message": "第四則建議，內容夠長"})
    assert slow.status_code == 429 and slow.headers["retry-after"] == "600"
    assert inbox(site)["total"] == 3


def test_the_service_limits_each_visitor_separately_and_per_day():
    class Memory:
        backend_name = "memory"

        def __init__(self):
            self.rows = []

        def add(self, record):
            self.rows.append(record)
            return record

    repository = Memory()
    service = FeedbackService(repository, per_window=RateLimiter(max_batches=2, max_events=2, window_seconds=600.0),
                              per_day=RateLimiter(max_batches=3, max_events=3, window_seconds=86_400.0))
    payload = FeedbackSubmission(message="這是一則建議的內容")
    for key in ("a", "a", "b", "b"):
        assert service.submit(payload, client_key=key, signed_in=False, now=100.0)
    with pytest.raises(Exception):
        service.submit(payload, client_key="a", signed_in=False, now=101.0)
    assert service.submit(payload, client_key="a", signed_in=False, now=100.0 + 700) is not None, "the ten minutes passed"
    with pytest.raises(Exception):
        service.submit(payload, client_key="a", signed_in=False, now=100.0 + 1400), "but three in a day is the limit"
    assert len(repository.rows) == 5


# ----------------------------------------------------------------------------- the inbox


def test_only_an_administrator_can_read_or_change_anything(site):
    site.post("/feedback", json=MESSAGE)
    feedback_id = inbox(site)["items"][0]["id"]
    for method, url, kwargs in (
        ("get", "/admin/feedback/list", {}),
        ("get", "/admin/feedback/export.csv", {}),
        ("post", f"/admin/feedback/{feedback_id}/status", {"json": {"status": "done"}}),
    ):
        assert getattr(site, method)(url, **kwargs).status_code == 401, (url, "signed out")
        assert getattr(site, method)(url, headers=site.student, **kwargs).status_code == 403, (url, "an ordinary student")
    assert site.get("/admin/feedback/list", headers=site.admin).status_code == 200


def test_the_inbox_page_holds_no_data_and_is_not_cached(site):
    page = site.get("/admin/feedback")
    assert page.status_code == 200 and page.headers["cache-control"] == "no-store"
    assert "noindex" in page.text and "MESSAGE" not in page.text


def test_the_inbox_lists_newest_first_with_counts_filters_and_an_average(site):
    site.app.state.feedback_service.per_window = RateLimiter(max_batches=99, max_events=99)
    site.app.state.feedback_service.per_day = RateLimiter(max_batches=99, max_events=99)
    for kind, rating, text in (("bug", 2, "按鈕按不下去的問題"), ("praise", 5, "整理得很清楚，謝謝"), ("suggestion", None, "希望加入宿舍資訊頁面")):
        assert site.post("/feedback", json={**MESSAGE, "kind": kind, "rating": rating, "message": text}).status_code == 201
    everything = inbox(site)
    assert [row["message"] for row in everything["items"]] == ["希望加入宿舍資訊頁面", "整理得很清楚，謝謝", "按鈕按不下去的問題"]
    assert everything["counts"] == {"new": 3, "read": 0, "done": 0} and everything["total"] == 3
    assert everything["average_rating"] == 3.5 and everything["rating_count"] == 2
    assert [row["kind"] for row in inbox(site, kind="bug")["items"]] == ["bug"]
    assert inbox(site, status="done")["items"] == []
    assert site.get("/admin/feedback/list", params={"status": "weird"}, headers=site.admin).status_code == 422


def test_an_administrator_marks_messages_read_or_done_with_a_note(site):
    site.post("/feedback", json=MESSAGE)
    feedback_id = inbox(site)["items"][0]["id"]
    done = site.post(f"/admin/feedback/{feedback_id}/status", json={"status": "done", "note": "已排進下一版"}, headers=site.admin)
    assert done.status_code == 200 and done.json()["status"] == "done" and done.json()["admin_note"] == "已排進下一版"
    assert done.json()["handled_at"]
    assert inbox(site)["counts"] == {"new": 0, "read": 0, "done": 1}
    reopened = site.post(f"/admin/feedback/{feedback_id}/status", json={"status": "new"}, headers=site.admin)
    assert reopened.json()["handled_at"] is None
    assert site.post(f"/admin/feedback/{feedback_id}/status", json={"status": "gone"}, headers=site.admin).status_code == 422
    assert site.post("/admin/feedback/doesnotexist1/status", json={"status": "read"}, headers=site.admin).status_code == 404
    assert site.post("/admin/feedback/..%2f..%2fx/status", json={"status": "read"}, headers=site.admin).status_code in {404, 405}


def test_the_csv_export_opens_in_a_spreadsheet_without_running_anything(site):
    site.post("/feedback", json={**MESSAGE, "message": "=HYPERLINK(\"http://x\")，這是公式", "contact": "+886 900"})
    response = site.get("/admin/feedback/export.csv", headers=site.admin)
    assert response.status_code == 200 and response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    body = response.content.decode("utf-8")
    assert body.startswith("﻿") and body.splitlines()[0].startswith("﻿time_taipei,kind,rating,message")
    assert "'=HYPERLINK" in body and "'+886 900" in body
    assert csv_cell("@x") == "'@x" and csv_cell("普通") == "普通" and csv_cell(None) == ""


def test_the_routes_are_not_part_of_the_published_api(site):
    paths = site.get("/openapi.json").json()["paths"]
    assert not [path for path in paths if "feedback" in path]


# ----------------------------------------------------------------------------- storage


def test_the_development_file_keeps_messages_between_restarts(tmp_path):
    first = JsonlFeedbackRepository(tmp_path)
    record = first.add(FeedbackRecord(message="第一則留言內容", kind="bug"))
    first.add(FeedbackRecord(message="第二則留言內容"))
    again = JsonlFeedbackRepository(tmp_path)
    assert {row.message for row in again.list()} == {"第一則留言內容", "第二則留言內容"}
    assert [row.id for row in again.list(kind="bug")] == [record.id]
    assert again.update(record.id, status="read", note="看過了").status == "read"
    assert JsonlFeedbackRepository(tmp_path).list(status="read")[0].admin_note == "看過了"
    assert again.update("nope", status="done", note="") is None


class FakeResponse:
    def __init__(self, rows=None, fail=False):
        self.rows, self.fail = rows if rows is not None else [], fail

    def raise_for_status(self):
        if self.fail:
            raise requests.HTTPError("boom")

    def json(self):
        return self.rows


def test_the_production_store_talks_to_its_own_table_with_the_server_key_only():
    calls = []

    def fake(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return FakeResponse([{"id": "abcdef12", "created_at": "2026-10-08T01:00:00+00:00", "message": "測試留言內容",
                              "status": "new", "kind": "bug", "rating": None, "contact": "", "route": "", "home_school": "",
                              "signed_in": False, "admin_note": "", "handled_at": None}])

    repository = SupabaseFeedbackRepository("https://project.supabase.co", "server-secret", request_func=fake)
    repository.add(FeedbackRecord(id="abcdef12", message="測試留言內容", kind="bug"))
    method, url, kwargs = calls[-1]
    assert (method, url) == ("POST", "https://project.supabase.co/rest/v1/exchange_user_feedback")
    assert kwargs["json"]["message"] == "測試留言內容" and kwargs["headers"]["Prefer"] == "return=minimal"
    assert "server-secret" in str(kwargs["headers"]) and kwargs["timeout"] == 20
    rows = repository.list(status="new", kind="bug", limit=10)
    assert rows[0].id == "abcdef12"
    params = dict(calls[-1][2]["params"])
    assert params["status"] == "eq.new" and params["kind"] == "eq.bug" and params["order"] == "created_at.desc" and params["limit"] == "10"
    updated = repository.update("abcdef12", status="done", note="完成")
    assert updated.id == "abcdef12"
    method, url, kwargs = calls[-1]
    assert method == "PATCH" and dict(kwargs["params"]) == {"id": "eq.abcdef12"} and kwargs["json"]["status"] == "done"
    assert kwargs["headers"]["Prefer"] == "return=representation"


def test_a_failing_database_is_reported_without_leaking_details():
    repository = SupabaseFeedbackRepository("https://project.supabase.co", "server-secret",
                                            request_func=lambda *a, **k: FakeResponse(fail=True))
    with pytest.raises(FeedbackRepositoryError) as caught:
        repository.add(FeedbackRecord(message="測試留言內容"))
    assert "server-secret" not in str(caught.value)
    with pytest.raises(FeedbackRepositoryError):
        SupabaseFeedbackRepository("http://insecure.example", "key")


def test_production_needs_the_database_and_development_falls_back_to_a_file(tmp_path):
    assert isinstance(create_feedback_repository(tmp_path, {}), JsonlFeedbackRepository)
    cloud = {"EXCHANGE_SUPABASE_URL": "https://project.supabase.co", "EXCHANGE_SUPABASE_SECRET_KEY": "secret"}
    assert isinstance(create_feedback_repository(tmp_path, cloud), SupabaseFeedbackRepository)
    with pytest.raises(FeedbackRepositoryError):
        create_feedback_repository(tmp_path, {"EXCHANGE_ENVIRONMENT": "production"})
    with pytest.raises(FeedbackRepositoryError):
        create_feedback_repository(tmp_path, {"EXCHANGE_FEEDBACK_BACKEND": "supabase"})
    with pytest.raises(FeedbackRepositoryError):
        create_feedback_repository(tmp_path, {"EXCHANGE_FEEDBACK_BACKEND": "other"})
    assert PRODUCTION_PERSISTENCE_BACKENDS["feedback"] == "supabase"
