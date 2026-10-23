"""The chief turns chat into a fixed set of actions and can never approve or publish."""

import json
import os
import time
from datetime import date

import pytest

from fake_cli import install
from office.config import Settings
from office.models import ChiefAction
from office.office import Office
from office.pipeline import run_day


@pytest.fixture
def office(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "chief=antigravity,*=offline",
           "OFFICE_BRAIN_FALLBACK": "offline", "OFFICE_RENDER_MEDIA": "0"}
    office = Office(Settings.from_env(env=env))
    run_day(office, office.today())
    return office


def chief_says(monkeypatch, reply="好的", **action):
    monkeypatch.setenv("FAKE_CHIEF", json.dumps({"reply": reply, "actions": [action] if action else []}, ensure_ascii=False))


def wait_for(predicate, seconds=10.0):
    end = time.time() + seconds
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def test_the_day_ends_with_a_report_from_the_chief(office):
    last = office.store.chat()[-1]
    assert last["sender"] == "chief" and "等你看" in last["text"]


def test_questions_get_answers_without_actions(office, monkeypatch):
    chief_says(monkeypatch, reply="今天有 4 則等你審。")
    answer = office.staff["chief"].handle("今天進度如何？")
    assert answer["text"] == "今天有 4 則等你審。"
    prompt = json.loads(open(os.environ["FAKE_LOG"], encoding="utf-8").read().splitlines()[-1])["args"][-1]
    assert "老闆剛剛說：今天進度如何？" in prompt and "#1｜Threads" in prompt


def test_redo_sends_the_draft_back_through_its_author_and_the_reviewer(office, monkeypatch):
    post = next(d for d in office.store.drafts() if d["channel"] == "threads")
    chief_says(monkeypatch, reply="交給阿脆", type="redo", draft_id=post["id"], instructions="開頭再口語一點")
    answer = office.staff["chief"].handle(f"#{post['id']} 開頭再口語一點")
    assert "阿脆" in answer["text"]
    assert wait_for(lambda: any("改好了" in m["text"] for m in office.store.chat()))
    events = office.store.events(limit=500)
    assert any(e["agent"] == "chief" and e["kind"] == "handoff" and e["data"]["to"] == "threads" for e in events)
    assert office.store.draft(post["id"])["status"] == "pending_approval"


def test_reschedule_reject_and_notes(office, monkeypatch):
    first, second = [d for d in office.store.drafts() if d["channel"] == "threads"]
    chief = office.staff["chief"]
    assert "改到" in chief.execute(ChiefAction(type="reschedule", draft_id=first["id"], time="20:45"))
    local = office.store.draft(first["id"])["scheduled_at"]
    assert office.at(office.today(), __import__("datetime").time(20, 45)).astimezone(__import__("datetime").timezone.utc).isoformat(timespec="seconds") == local
    assert "退回" in chief.execute(ChiefAction(type="reject", draft_id=second["id"], instructions="太像廣告"))
    assert office.store.draft(second["id"])["status"] == "rejected"
    assert "記下來" in chief.execute(ChiefAction(type="note_for_tomorrow", instructions="多做獎學金"))
    briefing = office.staff["strategist"].briefing(date(2026, 10, 24))
    assert "老闆交代：多做獎學金" in briefing.insights
    assert json.loads(office.store.get("boss_notes")) == []  # used once


def test_the_chief_cannot_touch_published_posts_or_unknown_drafts(office):
    chief = office.staff["chief"]
    post = next(d for d in office.store.drafts() if d["channel"] == "threads")
    office.approve(post["id"], publish_now=True)
    office.staff["publisher"].publish_due()
    assert "不能再改" in chief.execute(ChiefAction(type="redo", draft_id=post["id"], instructions="改"))
    assert "找不到" in chief.execute(ChiefAction(type="reject", draft_id=999))
    assert "HH:MM" in chief.execute(ChiefAction(type="reschedule", draft_id=post["id"] + 1, time="明天"))


def test_without_any_ai_the_chief_still_understands_start_and_progress(tmp_path):
    office = Office(Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0"}))
    assert "還沒有草稿" in office.staff["chief"].handle("進度？")["text"]
    assert "開工" in office.staff["chief"].handle("開工")["text"]
    assert wait_for(lambda: office.store.drafts())


def test_chat_endpoint(office):
    from fastapi.testclient import TestClient

    from office.server import create_app

    client = TestClient(create_app(office.settings, clock=False, office=office))
    assert client.post("/api/chat", json={"text": "  "}).status_code == 422
    assert client.post("/api/chat", json={"text": "進度"}).json() == {"accepted": True}
    assert wait_for(lambda: office.store.chat()[-1]["sender"] == "chief" and office.store.chat()[-2]["text"] == "進度")
    assert client.get("/api/state").json()["chat"]
