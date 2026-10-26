"""The chief can hire a colleague with a chosen AI, give them work, and let them go."""

import json
import os
import time

import pytest

from fake_cli import install
from office.config import Settings
from office.office import Office


@pytest.fixture
def office(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_RENDER_MEDIA": "0", "OFFICE_BRAIN_FALLBACK": "offline",
           "OFFICE_BRAINS": "chief=antigravity,reviewer=codex,*=claude-code"}
    return Office(Settings.from_env(env=env))


def chief_does(monkeypatch, *actions, reply="好"):
    monkeypatch.setenv("FAKE_CHIEF", json.dumps({"reply": reply, "actions": list(actions)}, ensure_ascii=False))


def calls():
    path = os.environ["FAKE_LOG"]
    return [json.loads(line) for line in open(path, encoding="utf-8")] if os.path.exists(path) else []


def wait_for(predicate, seconds=10.0):
    end = time.time() + seconds
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def test_hire_a_researcher_on_sonnet_and_give_her_work(office, monkeypatch):
    chief_does(monkeypatch, {"type": "hire", "name": "小美", "title": "Dcard 研究員", "instructions": "研究 Dcard 和 PTT 上學生在討論什麼",
                             "brain": "claude-code", "model": "sonnet", "effort": "high"})
    answer = office.staff["chief"].handle("新增一位同事叫小美，研究 Dcard，用 Sonnet high")
    assert "小美（Dcard 研究員）加入了，用 Claude Code｜模型 sonnet｜思考強度 high" in answer["text"]
    hire = office.colleague("小美")
    assert hire.id in office.roles() and office.snapshot()["agents"][-2]["name"] == "小美"  # the chief stays last
    assert any(e["kind"] == "staff" for e in office.store.events())

    chief_does(monkeypatch, {"type": "assign", "name": "小美", "task_kind": "report", "instructions": "查這週大家在問什麼"})
    office.staff["chief"].handle("請小美查這週大家在問什麼")
    assert wait_for(lambda: any("小美回報" in m["text"] for m in office.store.chat()))
    report = next(m["text"] for m in office.store.chat() if "小美回報" in m["text"])
    assert "托福有效期兩年" in report and "https://www.dcard.tw/f/exchange" in report
    call = next(c for c in reversed(calls()) if "--json-schema" in c["args"] and json.loads(c["args"][c["args"].index("--json-schema") + 1])["title"] == "Report")
    assert call["tool"] == "claude" and call["args"][call["args"].index("--model") + 1] == "sonnet"
    assert call["args"][call["args"].index("--effort") + 1] == "high"


def test_a_new_colleague_writes_threads_that_wait_for_the_boss(office, monkeypatch):
    office.hire("阿寫", "Threads 寫手", "寫語言檢定相關的 Threads")
    chief_does(monkeypatch, {"type": "assign", "name": "阿寫", "task_kind": "threads", "instructions": "托福和雅思怎麼選"})
    office.staff["chief"].handle("請阿寫寫一則 Threads 講托福和雅思怎麼選")
    assert wait_for(lambda: any(d["payload"].get("author") == "阿寫" for d in office.store.drafts()))
    draft = next(d for d in office.store.drafts() if d["payload"].get("author") == "阿寫")
    assert draft["channel"] == "threads" and draft["status"] in {"pending_approval", "needs_changes"}
    assert any(c["tool"] == "codex" for c in calls())  # Kiki reviewed it


def test_hires_survive_a_restart_and_can_leave(office, tmp_path):
    office.hire("小美", "研究員", "研究學生討論", brain="codex", effort="xhigh")
    again = Office(office.settings)
    assert again.colleague("小美").persona.title == "研究員"
    assert again.describe_brain(again.colleague("小美").id) == "Codex｜模型 預設｜思考強度 xhigh"
    assert again.dismiss("小美") == "小美"
    assert not Office(office.settings).hires()


def test_hiring_rules(office):
    with pytest.raises(ValueError, match="已經有同事叫 Kiki"):
        office.hire("Kiki", "審稿", "x")
    with pytest.raises(ValueError, match="不能在 Codex 上跑"):
        office.hire("小美", "研究員", "x", brain="codex", model="sonnet")
    assert not office.hires() and "小美" not in [a.persona.name for a in office.staff.values()]
    with pytest.raises(ValueError, match="原本的同事"):
        office.dismiss("Kiki")
    for i in range(6):
        office.hire(f"同事{i}", "助理", "x")
    with pytest.raises(ValueError, match="最多"):
        office.hire("第七位", "助理", "x")


def test_a_failing_tool_falls_back_to_another_ai_and_says_why_when_none_works(office, monkeypatch):
    office.hire("Dora", "校園情報研究員", "巡查各大學官網", brain="antigravity", model="Gemini 4 Argon", effort="high")
    hire = office.colleague("Dora")
    assert [b.key if b else "offline" for b in office.writer.chain(hire.id)][-1] == "offline"
    monkeypatch.setenv("FAKE_FAIL", "agy")
    assert "托福有效期兩年" in hire.report("查這週大家在問什麼")  # Claude Code picked it up
    monkeypatch.setenv("PATH", "/nonexistent")
    answer = hire.report("查這週大家在問什麼")
    assert "沒辦法完成" in answer and "Antigravity" in answer and "沒有連上任何 AI" not in answer


def test_schools_are_shared_out_and_checked_every_morning(office, monkeypatch):
    from office.brand import load_schools
    from office.scheduler import tick

    office.hire("Dora", "校園情報研究員", "巡查各大學官網")
    office.hire("dora2", "校園情報研究員", "巡查各大學官網")
    chief_does(monkeypatch, {"type": "watch_schools", "names": ["Dora", "dora2"]})
    answer = office.staff["chief"].handle("把大學平分給 Dora 和 dora2，每天巡查")
    schools = load_schools(office.settings)
    first, second = office.colleague("Dora").record["schools"], office.colleague("dora2").record["schools"]
    assert first + second == [s.id for s in schools] and abs(len(first) - len(second)) <= 1
    assert f"Dora 負責 {len(first)} 所" in answer["text"] and schools[0].name in answer["text"]
    assert "巡查" in office.staff["chief"].state_text()

    morning = office.at(office.today(), office.settings.daily_at)
    with monkeypatch.context() as m:
        m.setattr(office.store, "run_for_day", lambda day: {"id": 1})  # the day's posts are already made
        tick(office, morning.astimezone(__import__("datetime").timezone.utc), background=False)
    assert wait_for(lambda: sum("今天巡查了" in msg["text"] for msg in office.store.chat()) == 2, seconds=20)
    report = next(msg["text"] for msg in office.store.chat() if msg["text"].startswith("Dora今天巡查了"))
    assert "🆕 新公告｜長庚大學" in report and "✅ 沒有變化：國立臺北大學" in report
    batches = [c for c in calls() if "--json-schema" in c["args"] and "SchoolReport" in c["args"][c["args"].index("--json-schema") + 1]]
    assert len(batches) >= 2 and "官網：" in batches[0]["stdin"]


def test_a_daily_assignment_is_remembered(office, monkeypatch):
    office.hire("小美", "研究員", "研究 Dcard")
    chief_does(monkeypatch, {"type": "assign", "name": "小美", "task_kind": "report", "instructions": "看 Dcard 交換版熱門話題", "every_day": True})
    answer = office.staff["chief"].handle("請小美每天看 Dcard 交換版")
    assert "從明天起每天" in answer["text"]
    assert office.colleague("小美").record["daily"] == "看 Dcard 交換版熱門話題"


def test_a_school_round_can_start_right_away(office, monkeypatch):
    office.hire("Dora", "校園情報研究員", "巡查各大學官網")
    chief_does(monkeypatch, {"type": "assign", "name": "Dora", "task_kind": "schools"})
    assert "還沒分到學校" in office.staff["chief"].handle("請 Dora 現在先巡查一次")["text"]
    office.split_schools(["Dora"])
    answer = office.staff["chief"].handle("請 Dora 現在先巡查一次")
    assert "現在開始巡查 33 所" in answer["text"]
    assert wait_for(lambda: any(m["text"].startswith("Dora今天巡查了") for m in office.store.chat()), seconds=20)
