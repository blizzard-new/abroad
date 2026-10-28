"""A patrol's findings go to a second colleague first; only what she confirms reaches the boss, with an edit list."""

import json
import os
import sys

import pytest

from fake_cli import install
from office import proposals
from office.brand import School, platform_record
from office.config import Settings
from office.llm import WriterError
from office.models import FieldEdit, SchoolCheck, Verdict
from office.office import Office
from office.proposals import Proposal
from office.telegram import TelegramBridge

CGU = School("cgu", "長庚大學", "https://www.cgu.edu.tw/oia-ch", "長庚大學交換資料", "full", 12)


@pytest.fixture
def staffed(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_RENDER_MEDIA": "0", "OFFICE_BRAIN_FALLBACK": "offline",
           "OFFICE_BRAINS": "chief=antigravity,reviewer=codex,*=claude-code"}
    office = Office(Settings.from_env(env=env))
    office.hire("Dora", "校園情報研究員", "巡查各大學官網")
    office.hire("小公主", "驗證員", "驗證 Dora 的巡查結果")
    office.split_schools(["Dora"])
    return office


def calls():
    path = os.environ["FAKE_LOG"]
    return [json.loads(line) for line in open(path, encoding="utf-8")] if os.path.exists(path) else []


def asks_for(title):
    return [c for c in calls() if "--json-schema" in c["args"] and json.loads(c["args"][c["args"].index("--json-schema") + 1])["title"] == title]


def drafts(office):
    return [d for d in office.store.drafts(limit=100) if d["format"] == "data_update"]


def patrol(office):
    return office.colleague("Dora").check_schools()


# ---- Leo names the verifier ----
def test_leo_makes_a_colleague_the_verifier_and_can_take_it_away(staffed, monkeypatch):
    chief = staffed.staff["chief"]
    monkeypatch.setenv("FAKE_CHIEF", json.dumps({"reply": "好", "actions": [{"type": "set_verifier", "name": "小公主"}]}))
    answer = chief.handle("請小公主負責驗證 Dora 的巡查結果")["text"]
    assert "小公主現在是驗證員" in answer and "Dora" in answer
    assert staffed.verifier().persona.name == "小公主" and "驗證員：小公主" in chief.state_text()
    assert Office(staffed.settings).verifier().persona.name == "小公主"  # it survives a restart

    monkeypatch.setenv("FAKE_CHIEF", json.dumps({"reply": "好", "actions": [{"type": "set_verifier", "name": ""}]}))
    assert "取消驗證員" in chief.handle("不用驗證員了")["text"] and staffed.verifier() is None and "驗證員：目前沒有" in chief.state_text()

    monkeypatch.setenv("FAKE_CHIEF", json.dumps({"reply": "好", "actions": [{"type": "set_verifier", "name": "Kiki"}]}))
    assert "原本的同事" in chief.handle("讓 Kiki 驗證")["text"]  # only a new colleague can take the job

    staffed.set_verifier("小公主")
    staffed.dismiss("小公主")
    assert staffed.verifier() is None  # nobody is left holding a job they no longer have


# ---- the patrol, the verification and the inbox ----
def test_a_finding_the_verifier_confirms_becomes_a_proposal_with_an_edit_list(staffed):
    staffed.set_verifier("小公主")
    report = patrol(staffed)
    assert "📮 資料更新提案已送進審核匣" in report
    (found,) = drafts(staffed)
    payload = found["payload"]
    assert found["status"] == "pending_approval" and payload["verified_by"] == "小公主" and "第二梯次" in payload["verdict_reason"]
    assert payload["edits"][0]["target"].endswith("cgu → online_deadline.value_text") and payload["source_url"] == "https://www.cgu.edu.tw/oia-ch/news/1"
    assert not found["review"]["issues"] and not found["review"]["notes"]

    (call,) = asks_for("VerificationReport")  # one batch: the verifier re-reads the page and compares it with the platform record
    assert "WebSearch,WebFetch" in call["args"] and "不要只相信對方的說法" in call["stdin"]  # she may browse; nothing else
    assert "國際處公告 116 學年度第二梯次甄選" in call["stdin"] and "school_id=cgu" in call["stdin"] and "verified_window_deadlines.py" in call["stdin"]

    proposal = Proposal.from_payload(payload)
    body = proposal.pr_body()
    assert "### 二次驗證" in body and "**小公主** 重新打開官網核對" in body and "**修改 1**" in body and "online_deadline.value_text" in body
    record = json.loads(proposal.content())
    assert record["schema"] == "uniway-office-proposal/2" and record["verification"]["verified_by"] == "小公主" and record["edits"][0]["proposed"].startswith("第二梯次")


def test_when_the_verifier_says_no_nothing_is_proposed_and_the_report_says_why(staffed, monkeypatch):
    staffed.set_verifier("小公主")
    monkeypatch.setenv("FAKE_VERDICT", "not_exchange")
    report = patrol(staffed)
    assert drafts(staffed) == [] and "📮" not in report
    assert "🔎 小公主 驗證 長庚大學：不屬於校級交換，沒有送審（這是雙聯學位說明會，不是校級交換公告）" in report
    assert "🆕 新公告｜長庚大學" in report  # what Dora found stays in her report


def test_if_the_verifier_cannot_answer_the_finding_still_reaches_the_boss_marked_unverified(staffed, monkeypatch):
    staffed.set_verifier("小公主")

    def down(*args, **kwargs):
        raise WriterError("Claude Code 沒有登入")

    monkeypatch.setattr(staffed.writer, "verify_findings", down)
    patrol(staffed)
    (found,) = drafts(staffed)
    assert found["status"] == "needs_changes" and "二次驗證沒有完成：Claude Code 沒有登入" in found["review"]["issues"][0]
    assert found["payload"]["verified_by"] == "" and found["payload"]["edits"] == []


def test_nobody_verifies_their_own_patrol(staffed):
    staffed.set_verifier("Dora")
    report = patrol(staffed)
    assert "Dora自己就是驗證員" in report and asks_for("VerificationReport") == []
    (found,) = drafts(staffed)
    assert found["status"] == "pending_approval" and found["review"]["notes"] == ["沒有指定驗證員，只有巡查同事的說法，沒有二次驗證"]


def test_without_a_verifier_the_proposal_says_it_was_not_verified(staffed):
    patrol(staffed)
    (found,) = drafts(staffed)
    assert found["review"]["notes"] and "沒有二次驗證" in Proposal.from_payload(found["payload"]).pr_body()
    assert asks_for("VerificationReport") == []


def test_the_inbox_and_the_phone_show_the_verification_and_the_edit_list(staffed):
    staffed.set_verifier("小公主")
    patrol(staffed)
    (found,) = drafts(staffed)
    text = TelegramBridge(staffed, spawn=lambda *_: None).draft_message(found)["text"]
    assert "🔎 小公主 驗證：需要更新平台" in text and "1. verified_window_deadlines.py → cgu" in text and "改成：第二梯次甄選" in text


# ---- what the platform says today, read without running anything ----
def test_the_platform_record_is_read_from_the_source_without_importing_the_web_app(settings):
    sys.modules.pop("exchange_info.models", None)
    text = platform_record(settings, "cgu")
    assert "school_id=cgu" in text and "online_deadline" in text and "https://www.cgu.edu.tw" in text and "查核日" in text
    assert "exchange_info.models" not in sys.modules  # `ast` only: the repository's code is never executed in the office
    assert "沒有 nope 的已核實" in platform_record(settings, "nope")


def test_a_missing_platform_file_is_said_plainly(tmp_path):
    other = Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_REPO_ROOT": str(tmp_path)})
    assert "讀不到" in platform_record(other, "cgu")


# ---- text from the verifier is as untrusted as the patrol's ----
def test_the_edit_list_is_cleaned_like_everything_else_from_a_web_page():
    hostile = Verdict(school="長庚大學", verdict="confirmed_update", reason="確認 @maintainer", source_url="https://www.cgu.edu.tw/oia-ch/news/1",
                      edits=[FieldEdit(target="x → cgu → y", current="舊‮", proposed="見 [這裡](http://evil.test) <img src=x>", basis="@octocat 說的")])
    check = SchoolCheck(school="長庚大學", status="new_notice", detail="國際處公告第二梯次甄選", source_url="https://www.cgu.edu.tw/oia-ch")
    proposal = Proposal.from_check(check, CGU, author="Dora", day="2026-10-28", verdict=hostile, verified_by="小公主")
    body = proposal.pr_body()
    assert "@octocat" not in body and "@maintainer" not in body and "<img" not in body and "](http://evil.test)" not in body
    assert "‮" not in proposal.edits[0]["current"]
    plain = Proposal.from_check(check, CGU, author="Dora", day="2026-10-28")
    assert plain.path != proposal.path  # different edits are a different proposal
    many = Verdict(school="長庚大學", verdict="confirmed_update", reason="r", source_url="", edits=[FieldEdit(target=f"t{i}", current="c", proposed="p", basis="b") for i in range(20)])
    assert len(Proposal.from_check(check, CGU, author="Dora", day="2026-10-28", verdict=many, verified_by="小公主").edits) == proposals.MAX_EDITS
