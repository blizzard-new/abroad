"""The office's hands for the OpenBot assistants (`office tool ...`): same rules, same inbox, nothing posted until it is switched on."""

import json

import pytest

from office import brand, cli, proposals, tools
from office.config import Settings
from office.store import Store


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("OFFICE_HOME", str(tmp_path / "var"))
    monkeypatch.setenv("OFFICE_RENDER_MEDIA", "0")
    monkeypatch.setenv("OFFICE_DRY_RUN", "0")  # the old office was live: the tools must still start out simulating
    monkeypatch.setenv("OFFICE_POST_EVERY_DAYS", "2")
    monkeypatch.setenv("OFFICE_BRAINS", "offline")
    return tmp_path


def run(*argv):
    return tools.execute([str(a) for a in argv])


def write(path, data) -> str:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


GOOD = {
    "channel": "threads", "format": "text", "publish_at": "2030-01-08 12:30", "title": "預算",
    "payload": {
        "text": "交換申請前，你有算過一學期要花多少錢嗎？\n\n先把住宿、機票、保險列出來，再看補助。\n\n你最想先查哪一項？",
        "topic_tag": "交換學生", "first_reply": "整理好的合作校和預算在 app.uniway-tw.com，各校規定請以官方公告為準。",
    },
}


def good(**changes):
    return {**GOOD, **changes}


# ---- nothing goes out by accident ----
def test_the_tools_simulate_until_they_are_switched_on(home):
    assert run("status")["simulating"] is True and run("status")["tools_live"] is False
    assert run("live", "on")["simulating"] is False  # .env says live, and the tools were switched on: this is the real thing
    assert run("status")["tools_live"] is True
    assert run("live", "off")["simulating"] is True
    assert run("live", "status")["tools_live"] is False


def test_an_env_that_is_still_simulating_wins_over_the_switch(home, monkeypatch):
    monkeypatch.setenv("OFFICE_DRY_RUN", "1")
    answer = run("live", "on")
    assert answer["tools_live"] is True and answer["simulating"] is True and "OFFICE_DRY_RUN" in answer["message"]


def test_comments_dms_metrics_and_tokens_do_nothing_while_simulating(home):
    assert run("comments-due")["posts"] == []
    assert run("auto-dm")["sent"] == 0
    assert run("refresh-tokens")["refreshed"] == []
    assert run("metrics")["collected"] == 0


# ---- the posting day ----
def test_every_second_day_is_a_posting_day_and_the_day_between_is_not(home):
    first = run("begin-day", "--date", "2030-01-07")
    assert first["started"] and first["posting_day"]
    threads = [s for s in first["slots"] if s["channel"] == "threads"]
    assert [s["publish_at"] for s in threads] == ["2030-01-07 12:30", "2030-01-07 21:00"]
    instagram = next(s for s in first["slots"] if s["channel"] == "instagram")
    assert instagram["publish_at"] == "2030-01-07 19:30" and instagram["youtube_short_at"] == "2030-01-07 18:00"

    again = run("begin-day", "--date", "2030-01-07")
    assert not again["started"] and "開過工" in again["message"]
    between = run("begin-day", "--date", "2030-01-08")
    assert not between["started"] and between["posting_day"] is False and between["next_posting_day"] == "2030-01-09"
    assert run("begin-day", "--date", "2030-01-09")["started"]


def test_the_weekly_long_video_has_its_slot_on_sunday(home):
    sunday = run("begin-day", "--date", "2030-01-13")  # a Sunday
    long = next(s for s in sunday["slots"] if s["channel"] == "youtube")
    assert long["format"] == "long" and long["publish_at"] == "2030-01-13 19:00"


def test_a_failed_day_does_not_count(home):
    day = run("begin-day", "--date", "2030-01-07")
    assert run("end-day", day["run_id"], "--status", "failed", "--error", "企劃失敗")["status"] == "failed"
    assert run("begin-day", "--date", "2030-01-08")["started"]


# ---- what the assistants write is checked by the office's own rules ----
def test_check_flags_what_the_rules_flag(home, tmp_path):
    bad = good(payload={"text": "保證錄取！詳情看 https://example.com", "topic_tag": "交換學生", "first_reply": "沒有連結"})
    answer = run("check", write(tmp_path / "bad.json", bad))
    assert answer["ok"] is False
    joined = "\n".join(answer["issues"])
    assert "保證錄取" in joined and "網址" in joined and "app.uniway-tw.com" in joined
    assert run("check", write(tmp_path / "good.json", good()))["ok"] is True


def test_a_draft_file_with_the_wrong_shape_is_explained(home, tmp_path):
    with pytest.raises(tools.ToolError, match="payload 欄位不對"):
        run("check", write(tmp_path / "x.json", {"channel": "threads", "format": "text", "payload": {"text": "只有主文"}}))
    with pytest.raises(tools.ToolError, match="不支援"):
        run("check", write(tmp_path / "y.json", {"channel": "line", "format": "text", "payload": {}}))
    with pytest.raises(tools.ToolError, match="找不到檔案"):
        run("check", str(tmp_path / "missing.json"))


def test_tools_print_an_error_instead_of_a_traceback(home, tmp_path, capsys):
    assert tools.main(["check", str(tmp_path / "missing.json")]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


# ---- queue, approve, publish ----
def test_a_post_goes_to_the_inbox_then_out_only_after_the_boss_approves(home, tmp_path, capsys):
    file = write(tmp_path / "t.json", good())
    queued = run("queue", file)
    assert queued["ok"] and queued["status"] == "pending_approval" and queued["simulating"] is True
    draft_id = queued["draft_id"]
    with pytest.raises(tools.ToolError, match="已經在審核匣"):
        run("queue", file)  # a routine that fires twice must not post twice

    assert run("publish-due")["count"] == 0  # not approved: nothing goes out
    assert run("approve", draft_id, "--now")["status"] == "approved"
    sent = run("publish-due")
    assert sent["count"] == 1 and sent["published"][0]["status"] == "published" and sent["published"][0]["simulated"] is True
    assert list((tmp_path / "var" / "outbox").rglob("*.json")), "the simulated call is recorded, not sent"
    assert run("show", draft_id)["status"] == "published"


def test_the_review_can_hold_a_draft_and_the_fixed_version_replaces_it(home, tmp_path):
    file = write(tmp_path / "t.json", good())
    review = write(tmp_path / "review.json", {"approved": False, "issues": ["第二段太像新聞稿"], "notes": []})
    held = run("queue", file, "--review", review)
    assert held["status"] == "needs_changes" and held["issues"] == ["第二段太像新聞稿"]

    fixed = run("queue", file, "--review", write(tmp_path / "ok.json", {"approved": True, "issues": [], "notes": ["口吻OK"]}))
    assert fixed["status"] == "pending_approval"
    assert run("show", held["draft_id"])["status"] == "rejected"  # the sent-back version is gone from the inbox


def test_a_review_that_says_no_without_a_reason_still_blocks(home, tmp_path):
    answer = run("queue", write(tmp_path / "t.json", good()), "--review", write(tmp_path / "r.json", {"approved": False}))
    assert answer["status"] == "needs_changes" and "審稿沒有通過" in answer["issues"][0]


def test_rule_problems_hold_a_draft_even_when_the_review_passed_it(home, tmp_path):
    bad = good(title="壞", payload={**GOOD["payload"], "text": "保證錄取，不用擔心"})
    answer = run("queue", write(tmp_path / "t.json", bad), "--review", write(tmp_path / "r.json", {"approved": True, "issues": []}))
    assert answer["status"] == "needs_changes" and any("保證錄取" in i for i in answer["issues"])


def test_the_final_check_can_hold_an_approved_post_and_the_boss_can_override(home, tmp_path):
    draft_id = run("queue", write(tmp_path / "t.json", good()))["draft_id"]
    run("approve", draft_id, "--now")
    held = run("hold", draft_id, "--reason", "引用的公告已經撤下")
    assert held["status"] == "needs_changes" and "發文前檢查擋下" in held["issues"][0]
    assert run("publish-due")["count"] == 0
    run("approve", draft_id, "--now")  # the boss has seen why and approves again
    assert run("publish-due")["count"] == 1


def test_the_boss_can_reject_and_edit(home, tmp_path):
    draft_id = run("queue", write(tmp_path / "t.json", good()))["draft_id"]
    run("edit", draft_id, "--set", "text=改過的主文")
    assert run("show", draft_id)["payload"]["text"] == "改過的主文"
    assert run("reject", draft_id, "--note", "不要這題")["status"] == "rejected"
    with pytest.raises(tools.ToolError, match="沒有編號"):
        run("approve", 999)


def test_a_published_post_cannot_be_held_or_edited(home, tmp_path):
    draft_id = run("queue", write(tmp_path / "t.json", good()))["draft_id"]
    run("approve", draft_id, "--now")
    run("publish-due")
    with pytest.raises(tools.ToolError):
        run("hold", draft_id, "--reason", "太晚了")
    with pytest.raises(tools.ToolError, match="已經發佈"):
        run("edit", draft_id, "--set", "text=x")


# ---- replies ----
def published_post(tmp_path) -> int:
    store = Store(Settings.from_env().db_path)
    return store.add_draft(
        run_id=None, day="2030-01-08", channel="threads", format="text", pillar="value", title="預算", payload={"text": "主文"},
        status="published", scheduled_at=None,
    ) and store.drafts()[0]["id"]


def test_a_reply_always_waits_for_the_boss_and_is_not_queued_twice(home, tmp_path):
    post_id = published_post(tmp_path)
    reply = {"post_id": post_id, "comment_id": "c1", "comment_text": "住宿怎麼找？", "username": "amy", "text": "可以先看學校的宿舍申請時間，各校規定請以官方公告為準。"}
    answer = run("reply", write(tmp_path / "r.json", reply))
    assert answer["ok"]
    draft = run("show", answer["draft_id"])
    assert draft["format"] == "reply" and draft["status"] == "pending_approval" and draft["payload"]["reply_to_id"] == "c1"
    with pytest.raises(tools.ToolError, match="已經有回覆草稿"):
        run("reply", write(tmp_path / "r2.json", reply))
    with pytest.raises(tools.ToolError, match="不是已經發出去"):
        run("reply", write(tmp_path / "r3.json", {**reply, "post_id": 999}))


# ---- briefing and notes ----
def test_the_briefing_carries_the_numbers_the_notes_and_the_insights(home):
    run("note", "這週多講住宿")
    run("insights", "--note", "清單型貼文表現最好", "--note", "story 角度偏弱")
    briefing = run("briefing", "--date", "2030-01-08")
    assert briefing["facts"]["university_count"] > 0
    assert "老闆交代：這週多講住宿" in briefing["insights"]
    assert "清單型貼文表現最好" in briefing["text"] and str(briefing["facts"]["university_count"]) in briefing["text"]
    assert "老闆交代" not in "".join(run("briefing")["insights"])  # a note is passed on once
    assert run("insights")["insights"] == ["清單型貼文表現最好", "story 角度偏弱"]


# ---- auto private messages ----
def test_dm_rules_can_be_added_listed_and_removed(home):
    added = run("dm-rule-add", "--keywords", "雅思,IELTS", "--message", "雅思閱讀教材在這裡 👉 app.uniway-tw.com", "--offer", "領雅思閱讀教材")
    assert added["ok"] and added["rule"]["keywords"]
    listed = run("dm-rules")["rules"]
    assert len(listed) == 1 and "雅思" in listed[0]["text"]
    with pytest.raises(tools.ToolError):
        run("dm-rule-add", "--keywords", "想", "--message", "x")  # too common a word, and no real message
    assert run("dm-rule-remove", added["rule"]["id"])["ok"]
    assert run("dm-rules")["rules"] == []
    with pytest.raises(tools.ToolError, match="沒有編號"):
        run("dm-rule-remove", 99)


# ---- school patrol ----
def test_a_patrol_finding_becomes_a_proposal_the_boss_must_approve(home, tmp_path):
    settings = Settings.from_env()
    school = brand.load_schools(settings)[0]
    finding = {
        "author": "巡查員", "verifier": "",
        "checks": [{"school": school.name, "status": "new_notice", "detail": "國際處公告今年的交換甄選時間改了", "source_url": school.official_url,
                    "suggested_update": "校內截止日改為 2030-03-01"}],
    }
    answer = run("proposal", write(tmp_path / "p.json", finding))
    assert [q["school"] for q in answer["queued"]] == [school.name]
    draft = run("show", answer["queued"][0]["draft_id"])
    assert draft["format"] == proposals.FORMAT and draft["status"] in {"pending_approval", "needs_changes"}
    again = run("proposal", write(tmp_path / "p2.json", finding))
    assert again["queued"] == [] and again["notes"]  # already waiting in the inbox: not proposed twice
    assert run("schools", "--query", school.id)["count"] >= 1
    assert school.id in run("school-record", school.id)["record"] or "平台" in run("school-record", school.id)["record"]


def test_schools_can_be_split_between_assistants(home):
    total = run("schools")["count"]
    parts = [run("schools", "--part", f"{n}/3")["count"] for n in (1, 2, 3)]
    assert sum(parts) == total and all(parts)
    with pytest.raises(tools.ToolError, match="--part"):
        run("schools", "--part", "abc")


# ---- the command line ----
def test_office_tool_is_a_command_of_the_office(home, capsys):
    assert cli.main(["tool", "status"]) == 0
    assert "today" in json.loads(capsys.readouterr().out)
    assert cli.main(["tool", "queue", "missing.json"]) == 1
