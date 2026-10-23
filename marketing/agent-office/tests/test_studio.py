"""The allocation from the README: Claude Code writes, Codex draws and reviews, Antigravity researches and checks
posts before they go out. Runs a whole day against the fake command lines."""

import os
from datetime import date

import pytest

from fake_cli import install
from office.config import Settings
from office.office import Office
from office.pipeline import run_day

STUDIO = (
    "research=antigravity,strategist=claude-code,threads=claude-code,designer=claude-code,video=claude-code,"
    "community=claude-code,reviewer=codex,publisher=antigravity,analyst=antigravity"
)


@pytest.fixture
def studio(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": STUDIO, "OFFICE_BRAIN_FALLBACK": "offline",
           "OFFICE_IMAGES": "codex", "OFFICE_RENDER_MEDIA": "0"}
    return Office(Settings.from_env(env=env))


def test_each_desk_uses_its_own_tool(studio):
    run_day(studio, date(2026, 10, 23))
    used = {(e["agent"], e["data"]["brain"]) for e in studio.store.events(limit=500) if e["kind"] == "brain"}
    assert ("strategist", "antigravity") in used  # research
    assert ("strategist", "claude-code") in used  # planning
    assert ("threads", "claude-code") in used
    assert ("reviewer", "codex") in used
    drafts = studio.store.drafts(day="2026-10-23")
    assert drafts and {d["status"] for d in drafts} == {"pending_approval"}
    plan = studio.store.latest_run()["plan"]
    assert plan["items"][0]["topic"] == "語言檢定怎麼選"
    # The fake planner only filled the first slot; the rest still get a topic.
    assert all(item["topic"] for item in plan["items"])


def test_the_publisher_can_hold_a_post_and_the_boss_can_overrule(studio, monkeypatch):
    run_day(studio, date(2026, 10, 23))
    post = next(d for d in studio.store.drafts() if d["channel"] == "threads")
    monkeypatch.setenv("FAKE_PREFLIGHT", "hold")
    studio.approve(post["id"], publish_now=True)
    studio.staff["publisher"].publish_due()
    held = studio.store.draft(post["id"])
    assert held["status"] == "needs_changes"
    assert any("官方公告剛改了日期" in issue for issue in held["review"]["issues"])
    # Approving again after reading the reason sends it without asking the checker a second time.
    studio.approve(post["id"], publish_now=True)
    studio.staff["publisher"].publish_due()
    assert studio.store.draft(post["id"])["status"] == "published"
