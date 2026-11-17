"""OFFICE_BRAINS_ALLOWED=codex,antigravity: no desk ever reaches Claude, whatever asks for it, and the two tools run on the
models and thinking level set in .env."""

import json
import os
from datetime import date

import pytest

from fake_cli import install
from office import brains
from office.brains import AntigravityBrain, CodexBrain
from office.brand import BrandFacts, Briefing
from office.config import Settings
from office.llm import make_writer
from office.models import PlanItem, Review, ThreadsDraft
from office.office import Office

FACTS = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")
BRIEFING = Briefing(day=date(2026, 11, 17), facts=FACTS)
ITEM = PlanItem(channel="threads", format="text", pillar="value", angle="pain", topic="語言檢定", brief="language-test")
NO_CLAUDE = {
    "OFFICE_BRAINS": "chief=antigravity,research=antigravity,threads=codex,reviewer=codex,*=antigravity",
    "OFFICE_BRAIN_FALLBACK": "codex,antigravity,offline",
    "OFFICE_BRAINS_ALLOWED": "codex,antigravity",
    "OFFICE_CODEX_MODEL": "gpt-6.1-sol",
    "OFFICE_CODEX_EFFORT": "high",
    "OFFICE_ANTIGRAVITY_MODEL": "Gemini 4 Argon (High)",
}


@pytest.fixture
def cli(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-present-but-must-not-be-used")  # a Claude API key is right there

    def calls():
        path = tmp_path / "calls.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    return calls


def settings(tmp_path, **env):
    return Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_RENDER_MEDIA": "0", **env})


# ---- the chains ----
def test_claude_is_left_out_of_every_chain_even_when_the_settings_name_it(tmp_path):
    s = settings(tmp_path, **{**NO_CLAUDE, "OFFICE_BRAINS": "threads=claude-code,reviewer=api,*=auto", "OFFICE_BRAIN_FALLBACK": "claude-code,api,codex,offline"})
    for role in brains.ROLES:
        chain = brains.chain(s, role)
        assert "claude-code" not in chain and "api" not in chain, (role, chain)
    assert brains.chain(s, "threads") == ["codex", "offline"]


def test_a_desk_with_only_claude_to_use_ends_on_the_offline_templates(tmp_path):
    s = settings(tmp_path, **{**NO_CLAUDE, "OFFICE_BRAINS": "*=claude-code", "OFFICE_BRAIN_FALLBACK": "claude-code,api"})
    assert brains.chain(s, "threads") == ["offline"]


def test_without_the_list_nothing_changes(tmp_path):
    s = settings(tmp_path, OFFICE_BRAINS="threads=claude-code,*=antigravity", OFFICE_BRAIN_FALLBACK="claude-code,api,offline")
    assert s.brains_allowed == ()
    assert brains.chain(s, "threads") == ["claude-code", "api", "offline"]


# ---- the models and the thinking level ----
def test_codex_runs_on_the_env_model_at_the_env_effort_whatever_the_desk_asks(tmp_path, cli):
    CodexBrain(settings(tmp_path, **NO_CLAUDE)).ask(Review, "審稿", "簡報", effort="low")
    args = cli()[0]["args"]
    assert args[args.index("-m") + 1] == "gpt-6.1-sol"
    assert 'model_reasoning_effort="high"' in args and 'model_reasoning_effort="low"' not in args


def test_a_desk_the_chief_tuned_explicitly_keeps_its_own_effort_and_model(tmp_path, cli):
    CodexBrain(settings(tmp_path, **NO_CLAUDE)).ask(Review, "審稿", "簡報", effort="medium", model="gpt-6.1-luna", explicit_effort=True)
    args = cli()[0]["args"]
    assert args[args.index("-m") + 1] == "gpt-6.1-luna" and 'model_reasoning_effort="medium"' in args


def test_codex_effort_is_left_to_each_desk_when_the_setting_is_empty(tmp_path, cli):
    CodexBrain(settings(tmp_path, **{**NO_CLAUDE, "OFFICE_CODEX_EFFORT": ""})).ask(Review, "審稿", "簡報", effort="low")
    assert 'model_reasoning_effort="low"' in cli()[0]["args"]


def test_antigravity_gets_the_model_name_exactly_as_written(tmp_path, cli):
    AntigravityBrain(settings(tmp_path, **NO_CLAUDE)).ask(ThreadsDraft, "寫一則", "簡報")
    args = cli()[0]["args"]
    assert args[0] == "-p" and args[-2:] == ["--model", "Gemini 4 Argon (High)"]


def test_antigravity_without_a_model_setting_adds_no_flag(tmp_path, cli):
    AntigravityBrain(settings(tmp_path, **{**NO_CLAUDE, "OFFICE_ANTIGRAVITY_MODEL": ""})).ask(ThreadsDraft, "寫一則", "簡報")
    assert "--model" not in cli()[0]["args"]


def test_the_env_file_reads_the_quoted_model_name():
    from office.config import _load_dotenv
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / ".env"
        path.write_text('OFFICE_ANTIGRAVITY_MODEL="Gemini 4 Argon (High)"   # comment\nOFFICE_CODEX_EFFORT=high # x\n', encoding="utf-8")
        values = _load_dotenv(path)
    assert values["OFFICE_ANTIGRAVITY_MODEL"] == "Gemini 4 Argon (High)" and values["OFFICE_CODEX_EFFORT"] == "high"


# ---- real calls never reach Claude ----
def test_when_codex_is_down_the_work_goes_to_antigravity_not_to_claude(tmp_path, cli, monkeypatch):
    monkeypatch.setenv("FAKE_FAIL", "codex")
    writer = make_writer(settings(tmp_path, **{**NO_CLAUDE, "OFFICE_BRAIN_FALLBACK": "claude-code,api,codex,antigravity,offline"}))
    assert writer.threads(ITEM, BRIEFING).topic_tag == "交換學生"
    tools = [call["tool"] for call in cli()]
    assert tools == ["codex", "agy"]  # Codex failed, Antigravity answered, and no `claude` call at all


def test_when_both_are_missing_the_offline_templates_answer_and_claude_is_never_called(tmp_path, cli):
    bin_dir = tmp_path / "bin"
    (bin_dir / "codex").unlink()
    (bin_dir / "agy").unlink()  # only the fake `claude` is left on the PATH
    writer = make_writer(settings(tmp_path, **{**NO_CLAUDE, "OFFICE_BRAIN_FALLBACK": "claude-code,api,codex,antigravity,offline"}))
    assert writer.threads(ITEM, BRIEFING).topic_tag  # the offline template
    assert cli() == []


# ---- the chief and saved choices cannot bring Claude back ----
@pytest.fixture
def office(tmp_path, cli):
    return Office(settings(tmp_path, **NO_CLAUDE))


def test_the_chief_cannot_switch_a_desk_to_claude_or_pick_a_claude_model(office):
    with pytest.raises(ValueError, match="只允許用 Codex、Antigravity"):
        office.tune("threads", brain="claude-code")
    with pytest.raises(ValueError, match="不用 Claude 的模型"):
        office.tune("threads", model="sonnet")
    with pytest.raises(ValueError, match="不用 Claude 的模型"):
        office.tune("reviewer", brain="antigravity", model="claude-opus-5-5")  # Claude on Antigravity is still Claude
    assert office.tuning("threads") == {} and office.tuning("reviewer") == {}
    assert office.tune("threads", brain="antigravity", model="Gemini 4 Argon (High)")["brain"] == "antigravity"


def test_an_old_saved_claude_choice_is_ignored(office):
    office.store.set("tuning:threads", json.dumps({"brain": "claude-code", "model": "opus", "effort": "high"}))
    assert office.tuning("threads") == {"effort": "high"}
    assert [b.key if b else "offline" for b in office.writer.chain("threads")] == ["codex", "antigravity", "offline"]
    assert office.describe_brain("threads").startswith("Codex｜模型 gpt-6.1-sol｜思考強度 high")


def test_a_saved_claude_model_on_an_allowed_tool_is_ignored_too(office):
    office.store.set("tuning:research", json.dumps({"model": "opus"}))  # Antigravity can host Claude models
    assert office.tuning("research") == {}


def test_leo_is_told_what_is_allowed_and_each_desk_shows_its_model(office):
    text = office.staff["chief"].state_text()
    assert "只允許用 Codex、Antigravity" in text
    assert "Antigravity｜模型 Gemini 4 Argon (High)" in text and "Codex｜模型 gpt-6.1-sol｜思考強度 high" in text


def test_the_check_up_lists_the_model_and_effort_of_each_tool(tmp_path, cli):
    from office import checkup

    rows = {row.name: row for row in checkup.brain_rows(settings(tmp_path, **NO_CLAUDE))}
    assert "模型 gpt-6.1-sol、思考強度 high" in rows["Codex"].detail
    assert "模型 Gemini 4 Argon (High)" in rows["Antigravity"].detail
    assert "Claude Code" not in rows and "Claude API" not in rows
