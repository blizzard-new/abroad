"""voice.md: the voice notes the boss writes, read by every desk before it writes."""

import json
import os
from pathlib import Path

import pytest

from fake_cli import install
from office import checkup
from office.brains import ClaudeCodeBrain, CodexBrain
from office.brand import VOICE_GUIDE, VOICE_NOTES_LIMIT, VOICE_TEMPLATE, read_voice, voice_guide, write_voice_template
from office.cli import main
from office.config import Settings
from office.models import Review, ThreadsDraft


def settings(tmp_path, **env):
    return Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), **env})


def test_without_a_voice_file_the_writers_read_the_built_in_guide(tmp_path):
    assert voice_guide(settings(tmp_path)) == VOICE_GUIDE and voice_guide(None) == VOICE_GUIDE


def test_the_template_explains_itself_but_adds_nothing_until_the_boss_writes(tmp_path):
    s = settings(tmp_path)
    assert write_voice_template(s.voice_path) is True
    assert s.voice_path.read_text(encoding="utf-8") == VOICE_TEMPLATE
    assert read_voice(s.voice_path).text == "" and voice_guide(s) == VOICE_GUIDE


def test_a_voice_file_is_never_overwritten(tmp_path):
    s = settings(tmp_path)
    s.voice_path.write_text("口吻：像學長姐", encoding="utf-8")
    assert write_voice_template(s.voice_path) is False
    assert s.voice_path.read_text(encoding="utf-8") == "口吻：像學長姐"


def test_what_the_boss_writes_is_added_after_the_guide_and_the_comment_box_is_left_out(tmp_path):
    s = settings(tmp_path)
    write_voice_template(s.voice_path)
    s.voice_path.write_text(VOICE_TEMPLATE + "口吻：像學長姐在聊天，偶爾自嘲。\n範例：交換前我也慌過 🥲\n", encoding="utf-8")
    guide = voice_guide(s)
    assert guide.startswith(VOICE_GUIDE) and "口吻：像學長姐在聊天" in guide and "範例：交換前我也慌過" in guide
    assert "每位同事" not in guide and "<!--" not in guide  # the instructions in the comment box are not read to the AI
    assert "不能因此放寬" in guide  # the facts and the banned phrases still win


def test_a_byte_order_mark_from_notepad_is_fine(tmp_path):
    s = settings(tmp_path)
    s.voice_path.write_bytes("﻿口吻：直接一點".encode("utf-8"))
    assert read_voice(s.voice_path).text == "口吻：直接一點"


def test_notes_over_the_limit_are_cut_and_the_boss_is_told_how_much(tmp_path):
    s = settings(tmp_path)
    s.voice_path.write_text("字" * (VOICE_NOTES_LIMIT + 500), encoding="utf-8")
    notes = read_voice(s.voice_path)
    assert len(notes.text) == VOICE_NOTES_LIMIT and notes.cut == 500
    assert "500 字會被略過" in checkup.voice_rows(s)[0].detail


def test_a_file_saved_in_the_wrong_encoding_is_reported_not_guessed_at(tmp_path):
    s = settings(tmp_path)
    s.voice_path.write_bytes("口吻：像學長姐".encode("big5"))
    assert "UTF-8" in read_voice(s.voice_path).problem
    assert voice_guide(s) == VOICE_GUIDE
    row = checkup.voice_rows(s)[0]
    assert row.ok is False and "UTF-8" in row.detail


def test_check_says_where_the_voice_file_stands(tmp_path):
    s = settings(tmp_path)
    row = checkup.voice_rows(s)[0]
    assert row.ok is None and "uv run office voice" in row.detail
    s.voice_path.write_text("口吻：像學長姐", encoding="utf-8")
    row = checkup.voice_rows(s)[0]
    assert row.ok is True and "7 字" in row.detail
    assert ("語氣", [row]) == next((t, r) for t, r in checkup.run(s) if t == "語氣")


def test_the_voice_command_starts_the_file_and_reports_on_it(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OFFICE_HOME", str(tmp_path / "var"))
    assert main(["voice"]) == 0
    first = capsys.readouterr().out
    assert "剛建立好" in first and "目前是空的" in first and (tmp_path / "var" / "voice.md").is_file()
    (tmp_path / "var" / "voice.md").write_text(VOICE_TEMPLATE + "口吻：像學長姐", encoding="utf-8")
    assert main(["voice"]) == 0
    second = capsys.readouterr().out
    assert "剛建立好" not in second and "目前 7 字" in second


# ---- every kind of AI tool gets the notes ----
@pytest.fixture
def fake(tmp_path, monkeypatch):
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return lambda: [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def test_claude_code_and_codex_read_the_notes_before_every_task(tmp_path, fake):
    s = settings(tmp_path)
    s.voice_path.write_text("口吻：像學長姐在聊天", encoding="utf-8")
    ClaudeCodeBrain(s).ask(ThreadsDraft, "寫一則", "簡報")
    CodexBrain(s).ask(Review, "審稿", "簡報")
    claude, codex = fake()
    assert "口吻：像學長姐在聊天" in claude["args"][claude["args"].index("--system-prompt") + 1]
    assert "口吻：像學長姐在聊天" in codex["stdin"] and "不要用 AI 常見的口頭禪" in codex["stdin"]

    s.voice_path.write_text("口吻：改成很正式", encoding="utf-8")  # an edit counts on the very next task, no restart
    ClaudeCodeBrain(s).ask(ThreadsDraft, "寫一則", "簡報")
    assert "口吻：改成很正式" in fake()[-1]["args"][fake()[-1]["args"].index("--system-prompt") + 1]


def test_the_reviewer_is_told_to_watch_the_tone_too(tmp_path, fake):
    from datetime import date

    from office.brand import BrandFacts, Briefing
    from office.llm import ModelWriter
    from office.models import PlanItem

    s = settings(tmp_path)
    facts = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")
    item = PlanItem(channel="threads", format="text", pillar="value", angle="pain", topic="語言檢定", brief="language-test")
    draft = ThreadsDraft(text="先查門檻", topic_tag="交換學生", first_reply="app.uniway-tw.com")
    ModelWriter({"reviewer": [ClaudeCodeBrain(s)]}, settings=s).review("Threads 貼文", draft, item, [], Briefing(day=date(2026, 10, 23), facts=facts))
    assert "像不像真人寫的" in fake()[0]["stdin"]
