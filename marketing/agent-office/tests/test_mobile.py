"""The phone app's side of the office: signing in with a header, the lockout, the notification feed, the phone page."""

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from office import notices
from office.config import Settings
from office.mobile import FailureLimit, feed
from office.office import Office
from office.pipeline import run_day
from office.server import create_app

TOKEN = "a-long-random-pass-phrase"


def make(tmp_path, **env):
    settings = Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0", **env})
    office = Office(settings)
    return TestClient(create_app(settings, clock=False, office=office)), office


@pytest.fixture
def day(tmp_path):
    client, office = make(tmp_path)
    run_day(office, date(2026, 10, 23))
    return client, office


# ---- signing in ----
def test_the_app_signs_in_with_a_bearer_header_and_the_cookie_takes_over(tmp_path):
    client, _ = make(tmp_path, OFFICE_ACCESS_TOKEN=TOKEN)
    assert client.get("/api/state").status_code == 401
    ok = client.get("/api/mobile/feed", headers={"Authorization": f"Bearer {TOKEN}"})
    assert ok.status_code == 200 and "office_token" in ok.cookies
    assert client.get("/m").status_code == 200  # the page the WebView shows, now with the cookie
    assert client.get("/api/state", headers={"Authorization": "Bearer not-it"}).status_code == 401


def test_a_wrong_token_with_chinese_characters_is_refused_without_crashing(tmp_path):
    client, _ = make(tmp_path, OFFICE_ACCESS_TOKEN=TOKEN)
    assert client.get("/api/state", params={"token": "錯的"}).status_code == 401


def test_too_many_wrong_tokens_lock_the_address_out_even_for_the_right_one(tmp_path):
    client, _ = make(tmp_path, OFFICE_ACCESS_TOKEN=TOKEN)
    now = [1000.0]
    client.app.state.failure_limit.clock = lambda: now[0]
    for _ in range(3):  # a visit with no token at all is not a guess
        assert client.get("/api/state").status_code == 401
    for guess in range(8):
        assert client.get("/api/state", headers={"Authorization": f"Bearer guess-{guess}"}).status_code == 401
    locked = client.get("/api/state", headers={"Authorization": f"Bearer {TOKEN}"})
    assert locked.status_code == 429 and int(locked.headers["Retry-After"]) > 800
    now[0] += 901
    assert client.get("/api/state", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200


def test_the_limit_forgets_old_failures_and_a_success_clears_the_count():
    clock = [0.0]
    limit = FailureLimit(limit=3, window=60, lock=120, clock=lambda: clock[0])
    limit.failed("a"), limit.failed("a")
    clock[0] += 61
    limit.failed("a")  # the first two are outside the window now
    assert limit.wait("a") == 0
    limit.succeeded("a")
    limit.failed("a"), limit.failed("a")
    assert limit.wait("a") == 0
    limit.failed("a")
    assert 0 < limit.wait("a") <= 121
    assert limit.wait("b") == 0


# ---- the page ----
def test_the_phone_page_is_served_with_its_script_and_styles(tmp_path):
    client, _ = make(tmp_path)
    page = client.get("/m")
    assert page.status_code == 200 and "總管 Leo" in page.text and page.headers["cache-control"] == "no-cache"
    assert client.get("/static/m.js").headers["content-type"].startswith("text/javascript")
    assert client.get("/static/m.css").headers["content-type"].startswith("text/css")


# ---- the feed ----
def test_the_feed_lists_what_waits_for_the_boss_with_headlines_the_app_can_show(day):
    client, office = day
    data = client.get("/api/mobile/feed").json()
    waiting = [d for d in data["drafts"] if d["status"] == "pending_approval"]
    assert data["waiting"] == len(waiting) >= 2
    assert all(d["title"].startswith("📝 等你核准 #") and d["text"] for d in waiting)
    first = waiting[0]
    assert office.store.draft(first["id"])["title"] in first["text"]

    office.approve(first["id"])  # approved on the web: it stops waiting, so the phone takes its notification down
    after = client.get("/api/mobile/feed").json()
    assert first["id"] not in [d["id"] for d in after["drafts"]] and after["waiting"] == data["waiting"] - 1


def test_the_feed_reports_what_just_went_out_and_what_failed_but_not_old_news(day):
    client, office = day
    ids = [d["id"] for d in office.store.drafts(limit=10)]
    old = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat(timespec="seconds")
    office.store.update_draft(ids[0], status="published", remote_url="https://www.threads.com/@uniway.tw/post/x")
    office.store.update_draft(ids[1], status="failed", error="Threads 權杖過期")
    office.store.update_draft(ids[2], status="failed", error="很久以前的")
    office.store._exec("UPDATE drafts SET updated_at = ? WHERE id = ?", (old, ids[2]))
    by_id = {d["id"]: d for d in client.get("/api/mobile/feed").json()["drafts"]}
    assert by_id[ids[0]]["title"].startswith("🚀 已發出") and "threads.com" in by_id[ids[0]]["text"]
    assert by_id[ids[1]]["title"].startswith("❌ 發佈失敗") and "權杖過期" in by_id[ids[1]]["text"]
    assert ids[2] not in by_id


def test_leos_new_messages_come_once_and_a_fresh_install_does_not_replay_history(tmp_path):
    client, office = make(tmp_path)
    office.chat("boss", "開工")
    first = office.chat("chief", "開工了，今天排 4 則。")
    fresh = client.get("/api/mobile/feed").json()  # no chat_after: just where the conversation is now
    assert fresh["chat"] == [] and fresh["chat_last"] == first["id"]

    office.chat("boss", "進度如何？")
    reply = office.chat("chief", "3 則等你審。" + "很長" * 300)
    news = client.get(f"/api/mobile/feed?chat_after={first['id']}").json()
    assert [m["id"] for m in news["chat"]] == [reply["id"]]  # the boss's own words are not notified
    assert len(news["chat"][0]["text"]) <= 400 and news["chat_last"] == reply["id"]
    assert client.get(f"/api/mobile/feed?chat_after={reply['id']}").json()["chat"] == []


def test_the_feed_works_with_nothing_in_the_office_yet(tmp_path):
    _, office = make(tmp_path)
    assert feed(office) == {**feed(office), "waiting": 0, "chat_last": 0, "chat": [], "drafts": []}


# ---- the words a notification uses ----
def test_notification_wording_matches_what_telegram_says(day):
    _, office = day
    draft = next(d for d in office.store.drafts(limit=10) if d["status"] == "pending_approval")
    note = notices.notification(draft)
    assert note["title"] == f"📝 等你核准 {notices.label(draft)}" and notices.preview_text(draft) in note["text"]
    assert notices.notification({**draft, "status": "approved"}) is None
    proposal = {**draft, "format": "data_update", "channel": "github", "status": "published", "payload": {}, "remote_url": "https://github.com/x/pull/1"}
    assert notices.notification(proposal)["title"].startswith("📮 draft PR 開好了")


# ---- the checks and helpers around it ----
def test_check_warns_about_a_missing_short_or_unusable_access_token(tmp_path):
    from office import checkup

    def row(**env):
        (found,) = checkup.app_rows(Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), **env}))
        return found

    assert row().ok is None and "uv run office token" in row().detail
    short = row(OFFICE_ACCESS_TOKEN="pass-1234567")
    assert short.ok is None and "12 個字" in short.detail
    assert row(OFFICE_ACCESS_TOKEN="含中文的通行碼" * 4).ok is False
    assert row(OFFICE_ACCESS_TOKEN=TOKEN).ok is True


def test_office_token_makes_a_long_random_password(capsys):
    from office.cli import main

    assert main(["token"]) == 0
    first = capsys.readouterr().out
    assert main(["token"]) == 0
    second = capsys.readouterr().out
    line = next(l for l in first.splitlines() if l.strip().startswith("OFFICE_ACCESS_TOKEN="))
    token = line.split("=", 1)[1]
    assert len(token) >= 30 and token.isascii() and token not in second


def test_phone_addresses_are_labelled_and_loopback_is_never_offered():
    from office.netinfo import classify

    assert classify("100.101.1.2") == "Tailscale" and classify("192.168.0.5") == "區網" and classify("10.1.2.3") == "區網"
    assert classify("127.0.0.1") == "" and classify("8.8.8.8") == "" and classify("::1") == "" and classify("not an ip") == ""
