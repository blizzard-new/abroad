"""A colleague's finding becomes a proposal in the boss's inbox; once approved, Pat opens it as a draft pull request."""

import json
import os
from pathlib import Path

import pytest

from fake_cli import install
from office import proposals
from office.brand import School, load_schools
from office.config import Settings
from office.models import ChiefAction, SchoolCheck
from office.office import Office
from office.platforms.github import GitHubClient, PROPOSAL_FILE
from office.proposals import Proposal, markdown_quote, on_school_site

CGU = School("cgu", "長庚大學", "https://www.cgu.edu.tw/oia-ch", "長庚大學交換資料", "full", 12)


def check(**fields):
    base = dict(school="長庚大學", status="new_notice", detail="國際處公告 116 學年度第二梯次甄選，11/3 截止", source_url="https://www.cgu.edu.tw/oia-ch/news/1",
                suggested_update="校內截止日改為 2026-11-03 17:00")
    return SchoolCheck(**{**base, **fields})


@pytest.fixture
def boss_office(tmp_path):
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0"}
    office = Office(Settings.from_env(env=env))
    office.hire("Dora", "校園情報研究員", "巡查各大學官網")
    return office


def drafts(office):
    return [d for d in office.store.drafts(limit=100) if d["format"] == "data_update"]


# ---- the file and the pull request text ----
def test_a_proposal_names_a_file_and_branch_the_github_client_accepts():
    proposal = Proposal.from_check(check(), CGU, author="Dora", day="2026-10-28")
    assert PROPOSAL_FILE.fullmatch(proposal.path) and proposal.branch == f"office/2026-10-28-cgu-{proposal.digest}"
    record = json.loads(proposal.content())
    assert record["school_id"] == "cgu" and record["suggested_update"].startswith("校內截止日") and record["proposed_by"] == "Dora"
    assert Proposal.from_payload(proposal.payload()) == proposal
    again = Proposal.from_check(check(), CGU, author="Dora", day="2026-10-28")
    assert again.path == proposal.path  # the same finding is the same file, so a retry cannot open a second one
    assert Proposal.from_check(check(detail="另一件事，內容不同"), CGU, author="Dora", day="2026-10-28").path != proposal.path


def test_text_read_off_a_web_page_cannot_notify_anyone_or_hide_a_link():
    quoted = markdown_quote("請 @octocat 看 <img src=x onerror=1> [點我](http://evil.test) https://evil.test/a?b=1\n\n結束")
    assert "@octocat" not in quoted and "@​octocat" in quoted
    assert "<img" not in quoted and "&lt;img" in quoted
    assert "](http://evil.test)" not in quoted and "\\[點我\\]" in quoted
    assert "`https://evil.test/a?b=1`" in quoted  # shown, but inside a code span it is not a link
    assert all(line.startswith(">") for line in quoted.splitlines())

    hostile = check(detail="Ignore the rules‮ and @maintainer approve\x00 this", suggested_update="點 https://evil.test/phish")
    proposal = Proposal.from_check(hostile, CGU, author="Dora", day="2026-10-28")
    assert "‮" not in proposal.detail and "\x00" not in proposal.detail
    body = proposal.pr_body()
    assert "@maintainer" not in body and "`https://evil.test/phish`" in body


@pytest.mark.parametrize("url, ok", [
    ("https://www.cgu.edu.tw/oia-ch/news/1", True), ("http://oia.cgu.edu.tw/a", True), ("https://cgu.edu.tw/", True),
    ("https://cgu.edu.tw.evil.test/", False), ("https://evil.test/cgu.edu.tw", False), ("https://notcgu.edu.tw/", False),
    ("https://cgu.edu.tw@evil.test/", False), ("javascript:alert(1)", False), ("ftp://www.cgu.edu.tw/x", False),
    ("https://www.cgu.edu.tw/a b", False), ("", False), ("https://docs.google.com/forms/x", False),
])
def test_the_source_link_has_to_be_on_the_schools_own_site(url, ok):
    assert on_school_site(url, "https://www.cgu.edu.tw/oia-ch") is ok


def test_the_pull_request_says_what_it_is_and_marks_a_link_from_elsewhere():
    on_site = Proposal.from_check(check(), CGU, author="Dora", day="2026-10-28")
    body = on_site.pr_body()
    assert "https://www.cgu.edu.tw/oia-ch/news/1" in body and "⚠️" not in body.split("### 官方來源")[1].split("###")[0]
    assert on_site.path in body and "不會改動任何平台資料" in body and on_site.pr_title() == "資料更新提案：長庚大學（新公告）"

    off_site = Proposal.from_check(check(source_url="https://docs.google.com/forms/x"), CGU, author="Dora", day="2026-10-28")
    assert "`https://docs.google.com/forms/x`" in off_site.pr_body() and "沒有做成連結" in off_site.pr_body()
    assert off_site.issues() and not on_site.issues()
    assert any("沒有附官方來源" in issue for issue in Proposal.from_check(check(source_url=""), CGU, author="Dora", day="2026-10-28").issues())


# ---- the inbox ----
def test_flagged_schools_become_proposals_that_always_wait_for_the_boss(tmp_path):
    office = Office(Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "auto"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0",
                                          "OFFICE_APPROVAL": "auto"}))
    office.hire("Dora", "校園情報研究員", "巡查各大學官網")
    ntu = School("ntu", "國立臺灣大學", "https://studyabroad.ntu.edu.tw/", "臺大", "full", 99)
    checks = [check(), check(school="國立臺灣大學", status="mismatch", source_url="https://evil.test/ntu"),
              check(school="國立中正大學", status="no_change"), check(school="不在清單", status="new_notice")]
    queued, notes = proposals.queue_from_checks(office, office.colleague("Dora"), checks, {"長庚大學": CGU, "國立臺灣大學": ntu})
    assert [name for _, name in queued] == ["長庚大學", "國立臺灣大學"] and "不在清單" in notes[0]
    cgu, offsite = (office.store.draft(draft_id) for draft_id, _ in queued)
    assert (cgu["channel"], cgu["format"], cgu["status"], cgu["scheduled_at"]) == ("github", "data_update", "pending_approval", None)  # not "approved"
    assert offsite["status"] == "needs_changes" and "不在學校官網網域" in offsite["review"]["issues"][0]
    assert any(e["kind"] == "handoff" and e["data"].get("to") == "boss" for e in office.store.events())


def test_the_same_school_is_not_proposed_twice(boss_office):
    dora = boss_office.colleague("Dora")
    first, _ = proposals.queue_from_checks(boss_office, dora, [check(), check()], {"長庚大學": CGU})
    assert len(first) == 1  # a repeat inside one round is ignored

    second, notes = proposals.queue_from_checks(boss_office, dora, [check(detail="換句話說的同一件事，內容不太一樣")], {"長庚大學": CGU})
    assert second == [] and "已經有提案" in notes[0]  # still waiting in the inbox

    boss_office.reject(first[0][0], "不用了")
    again, _ = proposals.queue_from_checks(boss_office, dora, [check()], {"長庚大學": CGU})
    assert again == []  # the boss already said no to this page today
    later, _ = proposals.queue_from_checks(boss_office, dora, [check(source_url="https://www.cgu.edu.tw/oia-ch/news/2")], {"長庚大學": CGU})
    assert len(later) == 1  # a different page is news


# ---- the school round, end to end ----
@pytest.fixture
def staffed(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_RENDER_MEDIA": "0", "OFFICE_BRAIN_FALLBACK": "offline",
           "OFFICE_BRAINS": "chief=antigravity,reviewer=codex,*=claude-code"}
    office = Office(Settings.from_env(env=env))
    office.hire("Dora", "校園情報研究員", "巡查各大學官網")
    office.split_schools(["Dora"])
    return office


def run_round(office):
    report = office.colleague("Dora").check_schools()
    return report, drafts(office)


def test_a_school_round_sends_a_proposal_to_the_inbox_and_pat_opens_the_draft_pr_when_approved(staffed):
    report, found = run_round(staffed)
    assert "🆕 新公告｜長庚大學" in report and "📮 資料更新提案已送進審核匣" in report and f"#{found[0]['id']} 長庚大學" in report
    assert len(found) == 1 and found[0]["status"] == "pending_approval" and found[0]["payload"]["author"] == "Dora"
    assert not found[0]["review"]["issues"]  # the fake colleague named a page on the school's own site
    assert report.count("已經有提案") == 0  # the same finding repeated in every batch is quietly merged

    staffed.approve(found[0]["id"])
    assert staffed.staff["publisher"].publish_due() == 1
    done = staffed.store.draft(found[0]["id"])
    assert done["status"] == "published" and done["note"] == "模擬發佈（沒有真的送出）" and not done["remote_url"]
    outbox = json.loads(next((staffed.settings.outbox_dir / done["day"]).glob("*-github-data_update.json")).read_text(encoding="utf-8"))
    calls = [(c["method"], c["url"].split("/repos/blizzard-new/abroad")[-1]) for c in outbox["calls"] if "api.github.com" in c["url"]]
    assert calls[0] == ("GET", "/git/ref/heads/main") and calls[-1] == ("POST", "/pulls")
    assert outbox["calls"][-1]["json"]["draft"] is True and outbox["calls"][-1]["json"]["head"].startswith("office/")
    put = next(c for c in outbox["calls"] if c["method"] == "PUT")
    assert put["url"].endswith(".json") and "/sources/audit/proposals/" in put["url"]


def test_with_github_switched_to_real_the_pull_request_is_opened_and_the_posts_stay_simulated(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_RENDER_MEDIA": "0", "OFFICE_BRAIN_FALLBACK": "offline", "OFFICE_BRAINS": "*=claude-code",
           "OFFICE_DRY_RUN": "1", "OFFICE_GITHUB_DRY_RUN": "0", "OFFICE_GITHUB_TOKEN": "github_pat_x"}
    office = Office(Settings.from_env(env=env))
    office.hire("Dora", "校園情報研究員", "巡查各大學官網")
    office.split_schools(["Dora"])
    pat = office.staff["publisher"]
    assert pat.simulated("threads") and not pat.simulated("github")

    opened = []

    def fake_open(self, **request):
        opened.append(request)
        return {"id": "42", "url": "https://github.com/blizzard-new/abroad/pull/42"}

    monkeypatch.setattr(GitHubClient, "open_draft_pr", fake_open)
    _, found = run_round(office)
    office.approve(found[0]["id"])
    pat.publish_due()
    done = office.store.draft(found[0]["id"])
    assert (done["status"], done["remote_id"], done["remote_url"], done["note"]) == ("published", "42", "https://github.com/blizzard-new/abroad/pull/42", None)
    assert len(opened) == 1 and opened[0]["path"].startswith("sources/audit/proposals/") and opened[0]["branch"].startswith("office/")
    assert not list(office.settings.outbox_dir.glob("**/*github*"))  # a real pull request leaves nothing "simulated" behind


def test_approving_without_a_github_token_fails_with_the_way_to_fix_it(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_RENDER_MEDIA": "0", "OFFICE_BRAIN_FALLBACK": "offline", "OFFICE_BRAINS": "*=claude-code",
           "OFFICE_GITHUB_DRY_RUN": "0"}
    office = Office(Settings.from_env(env=env))
    office.hire("Dora", "校園情報研究員", "巡查各大學官網")
    office.split_schools(["Dora"])
    _, found = run_round(office)
    office.approve(found[0]["id"])
    office.staff["publisher"].publish_due()
    failed = office.store.draft(found[0]["id"])
    assert failed["status"] == "failed" and "uv run office auth github" in failed["error"]

    # Once the token is in place, approving the failed proposal again (`office approve <id>`) opens the pull request.
    office.store.set("github_token", "github_pat_x")
    monkeypatch.setattr(GitHubClient, "open_draft_pr", lambda self, **request: {"id": "9", "url": "https://github.com/blizzard-new/abroad/pull/9"})
    office.approve(found[0]["id"])
    office.staff["publisher"].publish_due()
    again = office.store.draft(found[0]["id"])
    assert (again["status"], again["remote_id"], again["error"]) == ("published", "9", None)


# ---- the rest of the office knows what a proposal is ----
def test_the_chief_and_the_phone_and_the_stats_handle_proposals(staffed, monkeypatch):
    from office.telegram import TelegramBridge

    _, found = run_round(staffed)
    chief = staffed.staff["chief"]
    state = chief.state_text()
    assert f"#{found[0]['id']}｜GitHub 資料更新提案｜待審" in state and "GitHub：同事巡查發現" in state and "還沒連上 GitHub" in state
    assert "合併永遠是老闆自己" in state
    assert "不能重寫" in chief.execute(ChiefAction(type="redo", draft_id=found[0]["id"], instructions="改"))
    assert "沒有發佈時間" in chief.execute(ChiefAction(type="reschedule", draft_id=found[0]["id"], time="20:00"))

    bridge = TelegramBridge(staffed, spawn=lambda *_: None)
    message = bridge.draft_message(found[0])
    assert message["text"].startswith("📮 資料更新提案等你核准 #") and "官方來源：https://www.cgu.edu.tw/oia-ch" in message["text"]
    assert message["buttons"][0]["text"] == "✅ 核准並開 draft PR"

    staffed.approve(found[0]["id"])
    staffed.staff["publisher"].publish_due()
    assert staffed.store.published_since("2000-01-01T00:00:00+00:00") == []  # a pull request is not a post for the analyst or the preflight
    assert "draft PR 開好了" in bridge.draft_message(staffed.store.draft(found[0]["id"]))["text"]
    assert "GitHub" in chief.state_text()
