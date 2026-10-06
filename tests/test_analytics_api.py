"""Analytics over HTTP: the public collector, the admin-only reports, and the events the server writes itself."""
from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from exchange_info.legal_pages import TERMS_VERSION
from exchange_info.analytics import RateLimiter
from exchange_info.analytics_repository import JsonlAnalyticsRepository
from exchange_info.api import create_app
from exchange_info.models import AccountSessionRecord, UserAccount, utc_now
from exchange_info.storage import ensure_data_dirs, save_account_sessions, save_user_accounts

CHROME = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/126.0 Safari/537.36")


def payload(events=None, **context):
    base = {"visitor_id": "visitor-abcdef", "session_id": "session-abcdef", "school": "長庚大學", "new_visitor": True}
    return {"v": 1, "context": {**base, **context}, "events": events if events is not None else [
        {"n": "page_view", "r": "partners"}, {"n": "school_open", "p": {"school": "明治大學"}}]}


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
    client = TestClient(create_app(tmp_path), headers={"user-agent": CHROME})
    client.admin = {"Authorization": "Bearer admin-id"}
    client.student = {"Authorization": "Bearer student-id"}
    client.data_dir = tmp_path
    return client


def stored(client, hours=1):
    now = datetime.now(timezone.utc)
    return client.app.state.analytics.repository.fetch_events(now - timedelta(hours=hours), now + timedelta(hours=1), 1000)[0]


# ----------------------------------------------------------------------------- collector


def test_collector_stores_valid_events_and_quietly_drops_the_rest(site):
    body = payload([{"n": "page_view", "r": "partners"}, {"n": "account_created"}, {"n": "bogus"}])
    response = site.post("/analytics/events", json=body)
    assert response.status_code == 202 and response.json() == {"accepted": 1, "dropped": 2}
    assert response.headers["cache-control"] == "no-store"
    (event,) = stored(site)
    assert (event.name, event.route, event.home_school, event.browser, event.device_class) == (
        "page_view", "partners", "長庚大學", "Chrome", "desktop")
    assert event.is_bot is False and event.new_visitor is True


def test_collector_accepts_a_beacon_without_a_json_content_type(site):
    raw = json.dumps(payload([{"n": "page_view"}])).encode()
    assert site.post("/analytics/events", content=raw, headers={"content-type": "text/plain"}).status_code == 202
    assert len(stored(site)) == 1


def test_collector_never_stores_an_ip_address_or_account(site):
    site.post("/analytics/events", json=payload([{"n": "page_view"}]), headers=site.admin)
    text = (site.data_dir / "analytics").glob("events-*.jsonl").__next__().read_text(encoding="utf-8")
    assert "testclient" not in text and "127.0.0.1" not in text and "admin-id" not in text


def test_collector_rejects_malformed_and_oversized_requests(site):
    assert site.post("/analytics/events", content=b"not json").status_code == 422
    assert site.post("/analytics/events", json={"v": 1, "events": []}).status_code == 422
    assert site.post("/analytics/events", json=payload([{"n": "page_view"}] * 41)).status_code == 422
    assert site.post("/analytics/events", json=payload(visitor_id="no")).status_code == 422
    huge = payload([{"n": "page_view", "p": {"note": "x" * 70_000}}])
    assert site.post("/analytics/events", json=huge).status_code == 413
    assert stored(site) == []


def test_collector_rate_limits_a_noisy_client(site):
    site.app.state.analytics.rate_limiter = RateLimiter(max_batches=2)
    assert [site.post("/analytics/events", json=payload()).status_code for _ in range(3)] == [202, 202, 429]


def test_analytics_can_be_switched_off(tmp_path, monkeypatch):
    monkeypatch.setenv("EXCHANGE_ANALYTICS", "off")
    monkeypatch.setenv("EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS", "admin-id")
    save_user_accounts([UserAccount(id="admin-id", display_name="管理員")], tmp_path)
    save_account_sessions([AccountSessionRecord(
        account_id="admin-id", token_hash=hashlib.sha256(b"admin-id").hexdigest(),
        expires_at=utc_now() + timedelta(days=1))], tmp_path)
    client = TestClient(create_app(tmp_path))
    assert client.post("/analytics/events", json=payload()).json() == {"accepted": 0, "dropped": 0}
    assert not (tmp_path / "analytics").exists()
    assert client.get("/admin/analytics/report", headers={"Authorization": "Bearer admin-id"}).status_code == 503


# ----------------------------------------------------------------------------- admin reports


def test_report_is_admin_only_and_never_cached(site):
    assert site.get("/admin/analytics/report").status_code == 401
    assert site.get("/admin/analytics/report", headers=site.student).status_code == 403
    assert site.get("/admin/analytics/export.csv", headers=site.student).status_code == 403
    assert site.post("/admin/analytics/purge", params={"older_than_days": 90}, headers=site.student).status_code == 403
    response = site.get("/admin/analytics/report", headers=site.admin)
    assert response.status_code == 200 and "no-store" in response.headers["cache-control"]


def test_report_reflects_collected_events_and_filters(site):
    site.post("/analytics/events", json=payload([
        {"n": "page_view", "r": "home"}, {"n": "page_view", "r": "partners"},
        {"n": "school_open", "p": {"school": "明治大學"}},
        {"n": "search", "p": {"q": "日本", "results": 4}},
    ]))
    site.post("/analytics/events", json=payload([{"n": "page_view", "r": "home"}],
                                                visitor_id="visitor-other1", session_id="session-other1",
                                                school="國立臺北大學"))
    site.post("/analytics/events", json=payload([{"n": "page_view", "r": "home"}], automated=True,
                                                visitor_id="visitor-robot1", session_id="session-robot1"))
    report = site.get("/admin/analytics/report", params={"days": 7}, headers=site.admin).json()
    assert report["range"]["days"] == 7 and report["range"]["timezone"] == "Asia/Taipei"
    current = report["overview"]["current"]
    assert (current["visitors"], current["sessions"], current["pageviews"]) == (2, 2, 3)
    assert report["data_quality"]["bot_events_in_range"] == 1
    assert report["search"]["top_terms"][0]["term"] == "日本"
    assert report["schools"]["top"][0]["school"] == "明治大學"
    assert report["funnel"][0]["visitors"] == 2 and report["funnel"][1]["visitors"] == 1
    with_bots = site.get("/admin/analytics/report", params={"include_bots": "true"}, headers=site.admin).json()
    assert with_bots["overview"]["current"]["visitors"] == 3
    one_school = site.get("/admin/analytics/report", params={"school": "國立臺北大學"}, headers=site.admin).json()
    assert one_school["overview"]["current"]["visitors"] == 1


def test_report_validates_its_date_range(site):
    assert site.get("/admin/analytics/report", params={"start": "2026-10-05", "end": "2026-10-01"},
                    headers=site.admin).status_code == 422
    assert site.get("/admin/analytics/report", params={"start": "2024-01-01", "end": "2026-10-01"},
                    headers=site.admin).status_code == 422
    assert site.get("/admin/analytics/report", params={"days": 0}, headers=site.admin).status_code == 422
    ok = site.get("/admin/analytics/report", params={"start": "2026-09-01", "end": "2026-09-30"}, headers=site.admin)
    assert ok.status_code == 200 and ok.json()["range"]["days"] == 30


def test_request_counts_per_endpoint_appear_in_the_report(site):
    for _ in range(3):
        site.get("/universities")
    site.get("/definitely-not-a-route")
    site.get("/static/app.js")
    site.get("/health")
    site.post("/analytics/events", json=payload())
    rows = {row["route"]: row for row in site.get(
        "/admin/analytics/report", headers=site.admin).json()["api"]["routes"]}
    assert rows["/universities"]["requests"] == 3 and rows["/universities"]["error_5xx"] == 0
    assert rows["(unmatched)"]["error_4xx"] == 1
    assert not {"/health", "/analytics/events"} & set(rows) and not any(r.startswith("/static") for r in rows)


def test_csv_export_excludes_bots_by_default_and_neutralises_formulas(site):
    site.post("/analytics/events", json=payload([{"n": "click", "p": {"target": "=cmd", "label": "@x"}}]))
    site.post("/analytics/events", json=payload([{"n": "page_view"}], automated=True,
                                                visitor_id="visitor-robot1", session_id="session-robot1"))
    response = site.get("/admin/analytics/export.csv", headers=site.admin)
    assert response.status_code == 200 and response.headers["content-type"].startswith("text/csv")
    assert response.headers["x-export-truncated"] == "false" and "no-store" in response.headers["cache-control"]
    text = response.content.decode("utf-8-sig")
    lines = text.strip().splitlines()
    assert lines[0].startswith("time_taipei,name,route") and len(lines) == 2
    assert "visitor-robot1" not in text
    full = site.get("/admin/analytics/export.csv", params={"include_bots": "true"}, headers=site.admin)
    assert len(full.content.decode("utf-8-sig").strip().splitlines()) == 3


def test_old_data_is_trimmed_automatically_and_on_request_but_never_recent_data(site):
    repository = site.app.state.analytics.repository
    from exchange_info.analytics import AnalyticsEvent

    def row(days, visitor):
        return AnalyticsEvent(occurred_at=datetime.now(timezone.utc) - timedelta(days=days), visitor_id=visitor,
                              session_id=visitor, name="page_view")

    def everything():
        now = datetime.now(timezone.utc)
        return repository.fetch_events(now - timedelta(days=1000), now + timedelta(hours=1), 1000)[0]

    repository.record_events([row(500, "visitor-past-500"), row(100, "visitor-past-100")])
    site.post("/analytics/events", json=payload())      # the first collection after a start applies the 400-day limit
    assert {e.visitor_id for e in everything()} == {"visitor-past-100", "visitor-abcdef"}
    assert site.post("/admin/analytics/purge", params={"older_than_days": 5}, headers=site.admin).status_code == 422
    removed = site.post("/admin/analytics/purge", params={"older_than_days": 60}, headers=site.admin).json()["removed"]
    assert removed["events"] == 1
    assert {e.visitor_id for e in everything()} == {"visitor-abcdef"}


def test_dashboard_page_is_served_without_data(site):
    page = site.get("/admin/analytics")
    assert page.status_code == 200 and "text/html" in page.headers["content-type"]
    assert "no-store" in page.headers["cache-control"]
    assert "/admin/analytics/report" in site.get("/static/analytics-dashboard.js").text


# ----------------------------------------------------------------------------- events the server writes itself


def names(client):
    return [(e.name, e.props) for e in stored(client) if e.is_server]


def test_choosing_a_school_is_recorded_without_the_account(site):
    site.patch("/auth/me", json={"home_university": "北大"}, headers=site.student)
    # A picked school stays for three days, so let the first pick age before choosing again.
    site.app.state.account_repository.patch_account_fields(
        "student-id", {"home_university_changed_at": utc_now() - timedelta(days=4)})
    site.patch("/auth/me", json={"home_university": "國立某某大學"}, headers=site.student)
    assert names(site) == [
        ("school_choice", {"school": "國立臺北大學", "supported": True}),
        ("school_choice", {"school": "other", "supported": False}),
    ]
    assert "student-id" not in json.dumps([e.model_dump(mode="json") for e in stored(site)])


def test_posts_and_comments_are_recorded_by_board_and_identity(site):
    identity = site.post("/auth/community-identity", headers=site.student).json()
    headers = {**site.student, "X-Anonymous-ID": identity["id"], "X-Anonymous-Token": identity["access_token"]}
    created = site.post("/community/posts", headers=headers,
                        json={"title": "交換申請測試問題", "body": "這是用來確認統計事件的測試文章。", "board_id": "cgu"})
    assert created.status_code == 201, created.text
    site.post(f"/community/posts/{created.json()['id']}/comments", headers=headers, json={"body": "測試回覆"})
    events = {name: props for name, props in names(site)}
    assert events["post_created"]["board"] == "cgu" and events["post_created"]["identity_mode"] == "anonymous"
    assert events["comment_created"]["board"] == "cgu"
    assert "測試文章" not in json.dumps([e.model_dump(mode="json") for e in stored(site)], ensure_ascii=False)


def test_google_sign_in_records_new_accounts_and_returning_logins(tmp_path, monkeypatch):
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "secret")

    class Json:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self.data

    def sign_in(browser):
        start = browser.get(f"/auth/oauth/google/start?terms={TERMS_VERSION}", follow_redirects=False)
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        user = {"sub": "sub-1", "name": "測試同學", "email": "b1128003@cgu.edu.tw", "email_verified": True}
        with (patch("exchange_info.api.requests.post", return_value=Json({"access_token": "t"})),
              patch("exchange_info.api.requests.get", return_value=Json(user))):
            assert browser.get("/auth/oauth/google/callback", params={"state": state, "code": "authorization-code"},
                               follow_redirects=False).status_code == 303

    first = TestClient(create_app(tmp_path))
    sign_in(first)
    sign_in(TestClient(create_app(tmp_path)))
    events = [e for e in stored(first) if e.is_server]
    assert [e.name for e in events] == ["account_created", "account_login"]
    assert events[0].school_basis == "school_email" and events[0].home_school == "長庚大學"
    assert events[0].props == {"provider": "google", "school_from_mail": True}
    assert "b1128003" not in json.dumps([e.model_dump(mode="json") for e in events])


# ----------------------------------------------------------------------------- production guard


def production_environment(monkeypatch):
    monkeypatch.setenv("EXCHANGE_ENVIRONMENT", "production")
    monkeypatch.setenv("EXCHANGE_SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("EXCHANGE_SUPABASE_SECRET_KEY", "server-secret")
    monkeypatch.setenv("EXCHANGE_ACCOUNT_REPOSITORY", "supabase")
    monkeypatch.setenv("EXCHANGE_VAULT_BACKEND", "supabase")
    monkeypatch.setenv("EXCHANGE_FORM_DRAFT_BACKEND", "supabase")
    monkeypatch.setenv("EXCHANGE_VAULT_MASTER_KEY", base64.urlsafe_b64encode(b"v" * 32).decode("ascii"))
    monkeypatch.setenv("EXCHANGE_EMAIL_VERIFICATION_SECRET", base64.urlsafe_b64encode(b"e" * 32).decode("ascii"))
    monkeypatch.setenv("EXCHANGE_EMAIL_VERIFICATION_BACKEND", "disabled")


def test_production_refuses_local_analytics_storage_unless_analytics_is_off(tmp_path, monkeypatch):
    production_environment(monkeypatch)
    app = create_app(tmp_path)
    assert app.state.analytics.backend_name == "supabase"
    with pytest.raises(RuntimeError, match="analytics"):
        create_app(tmp_path, analytics_repository=JsonlAnalyticsRepository(tmp_path))
    monkeypatch.setenv("EXCHANGE_ANALYTICS", "off")
    assert create_app(tmp_path).state.analytics.enabled is False
