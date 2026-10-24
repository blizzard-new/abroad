"""The chief can see and change which AI, model and thinking effort each desk uses."""

import json
import os
from datetime import date

import pytest

from fake_cli import install
from office.brand import BrandFacts, Briefing
from office.config import Settings
from office.models import PlanItem, ThreadsDraft
from office.office import Office

FACTS = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")
BRIEFING = Briefing(day=date(2026, 10, 24), facts=FACTS)
ITEM = PlanItem(channel="threads", format="text", pillar="value", angle="pain", topic="語言檢定", brief="language-test")


@pytest.fixture
def office(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_RENDER_MEDIA": "0", "OFFICE_BRAIN_FALLBACK": "offline",
           "OFFICE_BRAINS": "chief=antigravity,reviewer=codex,*=claude-code"}
    return Office(Settings.from_env(env=env))


def calls():
    path = os.environ["FAKE_LOG"]
    return [json.loads(line) for line in open(path, encoding="utf-8")] if os.path.exists(path) else []


def test_the_chief_moves_the_reviewer_from_codex_to_sonnet_at_high_effort(office, monkeypatch):
    action = {"type": "set_brain", "role": "reviewer", "brain": "claude-code", "model": "sonnet", "effort": "high"}
    monkeypatch.setenv("FAKE_CHIEF", json.dumps({"reply": "Kiki 改用 Sonnet", "actions": [action]}))
    answer = office.staff["chief"].handle("Kiki 改用 sonnet，強度 high")
    assert "審稿改用 Claude Code｜模型 sonnet｜思考強度 high" in answer["text"]
    assert office.writer.primary("reviewer") == "claude-code"
    assert office.snapshot()["settings"]["tuning"]["reviewer"] == "Claude Code｜模型 sonnet｜思考強度 high"

    draft = ThreadsDraft(text="語言檢定還沒考的看這裡", topic_tag="交換學生", first_reply="app.uniway-tw.com")
    office.writer.review("Threads", draft, ITEM, [], BRIEFING)
    review = calls()[-1]
    assert review["tool"] == "claude"
    assert review["args"][review["args"].index("--model") + 1] == "sonnet"
    assert review["args"][review["args"].index("--effort") + 1] == "high"
    assert not any(call["tool"] == "codex" for call in calls())

    # The chief sees every desk's current AI when it answers.
    office.staff["chief"].handle("大家現在用什麼模型？")
    prompt = calls()[-1]["args"][1]
    assert "role=reviewer（Kiki・審稿）：Claude Code｜模型 sonnet｜思考強度 high" in prompt


def test_untuned_desks_keep_their_defaults(office):
    office.writer.threads(ITEM, BRIEFING)
    call = calls()[-1]
    assert call["tool"] == "claude" and "--effort" not in call["args"] and "--model" not in call["args"]


def test_effort_alone_tunes_the_desks_own_tool(office):
    office.tune("reviewer", effort="xhigh")
    draft = ThreadsDraft(text="x", topic_tag="交換學生", first_reply="app.uniway-tw.com")
    office.writer.review("Threads", draft, ITEM, [], BRIEFING)
    call = calls()[-1]
    assert call["tool"] == "codex" and 'model_reasoning_effort="xhigh"' in call["args"]


def test_models_must_run_on_a_tool_that_has_them(office):
    with pytest.raises(ValueError, match="不能在 Codex 上跑"):
        office.tune("reviewer", model="claude-sonnet-5-5")
    with pytest.raises(ValueError, match="不能在 Claude Code 上跑"):
        office.tune("threads", model="gpt-5.5")
    with pytest.raises(ValueError):
        office.tune("threads", model="sonnet; rm -rf /\n")
    with pytest.raises(ValueError):
        office.tune("nobody", brain="codex")
    assert office.tuning("reviewer") == {}


def test_default_puts_a_desk_back(office):
    office.tune("reviewer", brain="claude-code", model="opus", effort="max")
    office.tune("reviewer", brain="default", model="default", effort="default")
    assert office.tuning("reviewer") == {} and office.writer.primary("reviewer") == "codex"


def test_the_chief_still_cannot_approve(office, monkeypatch):
    monkeypatch.setenv("FAKE_CHIEF", json.dumps({"reply": "好", "actions": [{"type": "approve", "draft_id": 1}]}))
    answer = office.staff["chief"].handle("全部核准")
    assert "approve" not in json.dumps(answer.get("data", {}))


def test_the_chief_knows_whether_posting_is_real_and_where_that_is_set(office):
    state = office.staff["chief"].state_text()
    assert "模擬發佈（OFFICE_DRY_RUN=1）" in state and "OFFICE_DRY_RUN 改成 0" in state
    assert "Threads 未連上" in state and "網頁和審核匣上沒有開關" in state
