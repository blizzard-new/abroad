import json
import os
from datetime import date
from pathlib import Path

import pytest

from fake_cli import install
from office import brains
from office.brains import AntigravityBrain, BrainError, ClaudeCodeBrain, CodexBrain, parse_json_text, strict_schema
from office.brand import BrandFacts, Briefing
from office.config import Settings
from office.llm import ModelWriter, WriterError
from office.models import PlanItem, Review, ThreadsDraft

FACTS = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")
BRIEFING = Briefing(day=date(2026, 10, 23), facts=FACTS)
ITEM = PlanItem(channel="threads", format="text", pillar="value", angle="pain", topic="語言檢定", brief="language-test")


@pytest.fixture
def fake(tmp_path, monkeypatch):
    bin_dir = install(tmp_path / "bin")
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-reach-claude-code")

    def calls():
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []

    return calls


def settings(tmp_path, **env):
    return Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), **env})


def test_brain_assignment_per_desk(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "no-config"))
    s = settings(tmp_path, OFFICE_BRAINS="threads=claude-code,reviewer=codex,*=antigravity", OFFICE_BRAIN_FALLBACK="claude-code,api,offline")
    assert brains.chain(s, "threads") == ["claude-code", "api", "offline"]
    assert brains.chain(s, "reviewer") == ["codex", "claude-code", "api", "offline"]
    assert brains.chain(s, "research")[0] == "antigravity"
    assert brains.resolve("auto", "threads") == "offline"  # no Claude API credentials here
    with pytest.raises(ValueError):
        brains.resolve("threads=gpt", "threads")


def test_strict_schema_requires_every_field_and_drops_defaults():
    schema = strict_schema(Review)
    assert schema["required"] == ["approved", "issues", "notes"]
    assert schema["additionalProperties"] is False
    assert "default" not in json.dumps(schema)


def test_json_is_found_in_chatty_output():
    assert parse_json_text('好的 {"a": "含 } 的字", "b": [1]} 謝謝') == {"a": "含 } 的字", "b": [1]}
    with pytest.raises(BrainError):
        parse_json_text("沒有 JSON")


def test_claude_code_runs_headless_on_the_subscription(tmp_path, fake):
    result = ClaudeCodeBrain(settings(tmp_path)).ask(ThreadsDraft, "寫一則", "簡報")
    assert result.topic_tag == "交換學生"
    call = fake()[0]
    assert call["args"][:3] == ["-p", "--output-format", "json"]
    assert "--json-schema" in call["args"] and "--system-prompt" in call["args"]
    assert "寫一則" in call["stdin"]
    assert call["api_key"] is None  # the API key is kept away so Claude Code uses your plan
    assert Path(call["cwd"]).name.startswith("office-claude-")


def test_codex_answers_through_an_output_schema_file(tmp_path, fake):
    result = CodexBrain(settings(tmp_path, OFFICE_CODEX_MODEL="gpt-test")).ask(Review, "審稿", "簡報", effort="high")
    assert result.approved is True
    args = fake()[0]["args"]
    assert args[:2] == ["exec", "-"]
    assert ["--sandbox", "read-only"] == args[args.index("--sandbox") : args.index("--sandbox") + 2]
    assert 'model_reasoning_effort="high"' in args and "gpt-test" in args


def test_codex_draws_a_cover(tmp_path, fake):
    art = CodexBrain(settings(tmp_path)).image("行李箱", tmp_path / "out" / "art.png")
    assert art.read_bytes().startswith(b"\x89PNG")
    assert "$imagegen" in fake()[0]["stdin"]


def test_antigravity_output_is_read_leniently(tmp_path, fake):
    result = AntigravityBrain(settings(tmp_path)).ask(ThreadsDraft, "寫一則", "簡報")
    assert result.first_reply.endswith("app.uniway-tw.com")
    assert fake()[0]["args"][0] == "-p"


def test_a_stalled_cli_times_out(tmp_path, fake, monkeypatch):
    monkeypatch.setenv("FAKE_STALL", "agy")
    with pytest.raises(BrainError, match="沒有回應"):
        AntigravityBrain(settings(tmp_path, OFFICE_BRAIN_TIMEOUT="1")).ask(ThreadsDraft, "x", "y")


def test_writer_falls_back_down_the_chain(tmp_path, fake, monkeypatch):
    monkeypatch.setenv("FAKE_FAIL", "codex")
    s = settings(tmp_path)
    seen = []
    writer = ModelWriter(
        {"threads": [CodexBrain(s), ClaudeCodeBrain(s)], "reviewer": [None]},
        on_brain=lambda role, key, failures: seen.append((role, key, list(failures))),
    )
    assert writer.threads(ITEM, BRIEFING).topic_tag == "交換學生"
    assert seen[-1][1] == "claude-code" and "Codex" in seen[-1][2][0]
    # A chain that ends in the offline templates always produces something.
    assert writer.review("Threads", ThreadsDraft(text="t", topic_tag="x", first_reply="y"), ITEM, [], BRIEFING).approved


def test_research_never_runs_on_a_brain_that_cannot_browse(tmp_path, fake):
    s = settings(tmp_path)
    writer = ModelWriter({"research": [CodexBrain(s)]})
    assert not writer.uses_model("research", need_web=True)
    with pytest.raises(WriterError, match="不能上網"):
        writer.research(BRIEFING)
