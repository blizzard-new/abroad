"""Nana's review: a post is judged against what its own kind usually gets, not by the biggest raw number."""

import json
import os
from datetime import date

import pytest

from fake_cli import install
from office.agents.analyst import MIN_PEERS, audit_lines, rank, verdict
from office.brains import ClaudeCodeBrain
from office.brand import BrandFacts, Briefing
from office.cli import main
from office.llm import ModelWriter, briefing_text
from office.store import now_utc


def post(office, channel, format, title, **metrics):
    store = office.store
    draft_id = store.add_draft(run_id=None, day="2026-10-23", channel=channel, format=format, title=title, payload={}, status="approved")
    store.update_draft(draft_id, status="published", published_at=now_utc(), remote_id=f"r{draft_id}")
    store.add_metrics(draft_id, metrics)
    return draft_id


@pytest.fixture
def week(make_office):
    """Five Threads posts that usually get ~10 likes (one hit), and five Reels that usually get ~400 (one flop)."""
    office = make_office()
    ids = {}
    for title, likes in (("托福還是雅思", 10), ("住宿怎麼找", 12), ("簽證時間線", 11), ("預算表", 9), ("爆款：語言門檻", 40)):
        ids[title] = post(office, "threads", "text", title, likes=likes)
    for title, likes in (("宿舍導覽", 400), ("機票比價", 420), ("行前清單", 380), ("選課心得", 410), ("冷門話題", 100)):
        ids[title] = post(office, "instagram", "reel", title, likes=likes)
    return office, ids


def test_a_post_is_ranked_against_its_own_kind_not_by_raw_numbers(week):
    office, ids = week
    rows = {r["draft_id"]: r for r in office.staff["analyst"].standings()}
    hit, flop, ordinary_reel = rows[ids["爆款：語言門檻"]], rows[ids["冷門話題"]], rows[ids["宿舍導覽"]]
    assert hit["score"] == 40 and hit["usual"] == 10.5 and hit["multiple"] == 3.8
    assert flop["score"] == 100 and flop["multiple"] < 0.3  # 100 is more than the Threads hit's 40, and still a flop for a Reel
    assert 0.9 <= ordinary_reel["multiple"] <= 1.1
    order = [r["title"] for r in office.staff["analyst"].audit(7)]
    assert order[0] == "爆款：語言門檻" and order[-1] == "冷門話題"


def test_a_kind_with_too_few_posts_has_nothing_to_be_compared_with():
    posts = [{"id": i, "title": f"t{i}", "channel": "threads", "format": "text"} for i in range(1, MIN_PEERS + 1)]  # only MIN_PEERS - 1 peers each
    rows = rank(posts, {i: {"likes": i * 10} for i in range(1, MIN_PEERS + 1)})
    assert all(r["multiple"] is None and r["usual"] is None for r in rows)
    assert [r["score"] for r in rows] == [30, 20, 10]  # raw score decides until there is history
    assert "同類貼文還太少" in verdict(rows[0])


def test_a_usual_score_of_zero_cannot_divide(make_office):
    office = make_office()
    for number in range(5):
        post(office, "threads", "text", f"沒人理 {number}", likes=0)
    assert all(r["multiple"] is None for r in office.staff["analyst"].standings())


def test_the_posts_worth_remaking_beat_their_kind(week):
    office, ids = week
    winners = office.staff["analyst"].winners()
    assert [w["title"] for w in winners] == ["爆款：語言門檻"]  # the only Threads post above its usual; the rest are ordinary
    assert winners[0]["multiple"] == 3.8 and set(winners[0]) == {"draft_id", "title", "score", "multiple"}


def test_with_no_history_yet_any_post_with_interactions_is_still_a_candidate(make_office):
    office = make_office()
    post(office, "threads", "text", "第一則", likes=5)
    post(office, "threads", "text", "第二則", likes=9)
    post(office, "threads", "text", "沒人看", likes=0)
    assert [w["title"] for w in office.staff["analyst"].winners()] == ["第二則", "第一則"]


def test_the_chief_answers_what_worked_from_the_review(week):
    office, _ = week
    text = office.staff["chief"].state_text()
    assert "成效復盤" in text
    assert "爆款：語言門檻｜互動分數 40，是同類平常的 3.8 倍 ↑" in text
    assert "冷門話題" in text and "↓" in text  # the weakest are named too, so "what should we stop doing" has an answer


def test_an_office_with_no_numbers_says_so(make_office):
    assert "最近沒有發出去又有數據的貼文" in make_office().staff["chief"].state_text()


def test_the_audit_command_prints_the_ranking(week, monkeypatch, capsys):
    office, _ = week
    monkeypatch.setenv("OFFICE_HOME", str(office.settings.home))
    monkeypatch.setenv("OFFICE_BRAINS", "offline")
    assert main(["audit", "--days", "7"]) == 0
    out = capsys.readouterr().out
    assert " 1. Threads貼文｜爆款：語言門檻｜互動分數 40，是同類平常的 3.8 倍 ↑" in out
    assert "IGReels｜冷門話題" in out and "隔幾天再看比較準" in out


def test_the_audit_command_without_numbers(make_office, monkeypatch, capsys):
    monkeypatch.setenv("OFFICE_HOME", str(make_office().settings.home))
    monkeypatch.setenv("OFFICE_BRAINS", "offline")
    assert main(["audit"]) == 0
    assert "沒有發出去又有數據的貼文" in capsys.readouterr().out


def test_the_strategist_and_the_analyst_both_see_the_multiple(week, tmp_path, monkeypatch):
    office, _ = week
    facts = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")
    briefing = Briefing(day=date(2026, 10, 23), facts=facts, winners=office.staff["analyst"].winners())
    assert "爆款：語言門檻（互動分數 40.0，是同類貼文平常的 3.8 倍）" in briefing_text(briefing)

    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rows = [{"channel": "threads", "format": "text", "title": "爆款", "metrics": {"likes": 40}, "multiple": 3.8},
            {"channel": "threads", "format": "text", "title": "新的", "metrics": {"likes": 3}, "multiple": None}]
    ModelWriter({"analyst": [ClaudeCodeBrain(office.settings)]}, settings=office.settings).insights(rows, briefing)
    prompt = json.loads(log.read_text(encoding="utf-8").splitlines()[0])["stdin"]
    assert "爆款｜{\"likes\": 40}｜比同類貼文平常 3.8 倍" in prompt
    assert "新的｜{\"likes\": 3}\n" in prompt or prompt.rstrip().endswith("新的｜{\"likes\": 3}") or "新的｜{\"likes\": 3}｜比" not in prompt
    assert "不要只看絕對數字" in prompt


def test_audit_lines_name_the_platform_and_format():
    row = {"channel": "instagram", "format": "carousel", "title": "交換預算表", "score": 120.0, "multiple": 0.5}
    assert audit_lines([row]) == ["IG輪播｜交換預算表｜互動分數 120，只有同類平常的 0.5 倍 ↓"]
