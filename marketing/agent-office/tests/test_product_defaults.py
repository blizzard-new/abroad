"""The settings the boss wants (posts every second day, no Claude, Codex on gpt-6.1-sol at high, Antigravity on
Gemini 4 Argon) are the office's own defaults, so updating the code and restarting is enough: an existing .env that never heard of
them, or that still names Claude, must end up in the same place."""

import json
import os
from datetime import date, datetime, timedelta, timezone

import pytest

from fake_cli import install
from office import brains
from office.config import Settings, _load_dotenv
from office.llm import make_writer
from office.brand import BrandFacts, Briefing
from office.models import PlanItem
from office.office import Office
from office.scheduler import tick

pytestmark = pytest.mark.product_defaults

# The .env the office was set up with before: Claude Code on six desks, Claude in the fallbacks, nothing about models.
OLD_ENV = {
    "OFFICE_BRAINS": "chief=antigravity,research=antigravity,strategist=claude-code,threads=claude-code,designer=claude-code,"
                     "visual=claude-code,video=claude-code,community=claude-code,reviewer=codex,publisher=antigravity,analyst=antigravity",
    "OFFICE_BRAIN_FALLBACK": "claude-code,api,offline",
    "OFFICE_IMAGES": "codex",
    "OFFICE_DRY_RUN": "0",
}
FACTS = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")
BRIEFING = Briefing(day=date(2026, 11, 17), facts=FACTS)
ITEM = PlanItem(channel="threads", format="text", pillar="value", angle="pain", topic="語言檢定", brief="language-test")


def settings(tmp_path, **env) -> Settings:
    return Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_RENDER_MEDIA": "0", **env})


def test_an_empty_env_gets_the_wanted_settings(tmp_path):
    s = settings(tmp_path)
    assert s.post_every_days == 2
    assert s.brains_allowed == ("codex", "antigravity")
    assert (s.codex_model, s.codex_effort, s.antigravity_model) == ("gpt-6.1-sol", "high", "Gemini 4 Argon (High)")


def test_the_old_env_file_ends_up_with_no_claude_and_the_new_split(tmp_path):
    s = settings(tmp_path, **OLD_ENV)
    for role in brains.ROLES:
        assert "claude-code" not in brains.chain(s, role) and "api" not in brains.chain(s, role), role
    first = {role: brains.chain(s, role)[0] for role in brains.ROLES}
    assert first["strategist"] == first["community"] == first["chief"] == first["research"] == "antigravity"
    assert first["threads"] == first["designer"] == first["visual"] == first["video"] == first["reviewer"] == "codex"
    # a desk does not fall straight to the templates just because .env still named Claude: the other tool backs it up
    assert brains.chain(s, "threads") == ["codex", "antigravity", "offline"]
    assert brains.chain(s, "strategist") == ["antigravity", "codex", "offline"]
    assert brains.chain(s, "reviewer") == ["codex", "antigravity", "offline"]


def test_a_real_env_file_is_read_the_same_way(tmp_path):
    path = tmp_path / ".env"
    path.write_text("\n".join(f"{k}={v}" for k, v in OLD_ENV.items()) + "\nOFFICE_HOME=" + str(tmp_path / "var") + "\n", encoding="utf-8")
    s = Settings.from_env(env=_load_dotenv(path))
    assert brains.chain(s, "video")[:2] == ["codex", "antigravity"] and s.post_every_days == 2


def test_a_colleague_nobody_assigned_gets_antigravity_first(tmp_path):
    writer = make_writer(settings(tmp_path, **OLD_ENV))
    assert [b.key if b else "offline" for b in writer.chain("dora")] == ["antigravity", "codex", "offline"]


def test_a_desk_set_to_the_offline_layout_stays_on_it(tmp_path):
    s = settings(tmp_path, **{**OLD_ENV, "OFFICE_BRAINS": OLD_ENV["OFFICE_BRAINS"] + ",visual=offline"})
    assert brains.chain(s, "visual")[0] == "offline"


def test_an_env_line_still_wins_and_an_empty_limit_switches_it_off(tmp_path):
    s = settings(tmp_path, OFFICE_POST_EVERY_DAYS="1", OFFICE_CODEX_EFFORT="medium", OFFICE_CODEX_MODEL="gpt-6.1-luna",
                 OFFICE_ANTIGRAVITY_MODEL="Gemini 4 Argon (Low)")
    assert (s.post_every_days, s.codex_effort, s.codex_model, s.antigravity_model) == (1, "medium", "gpt-6.1-luna", "Gemini 4 Argon (Low)")
    open_ = settings(tmp_path, **{**OLD_ENV, "OFFICE_BRAINS_ALLOWED": ""})
    assert open_.brains_allowed == () and brains.chain(open_, "threads") == ["claude-code", "api", "offline"]


def test_blank_model_lines_do_not_blank_the_defaults(tmp_path):
    s = settings(tmp_path, OFFICE_CODEX_MODEL="", OFFICE_CODEX_EFFORT="", OFFICE_ANTIGRAVITY_MODEL="")
    assert (s.codex_model, s.codex_effort, s.antigravity_model) == ("gpt-6.1-sol", "high", "Gemini 4 Argon (High)")


# ---- the whole way, from the old .env ----
@pytest.fixture
def cli(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-present-but-must-not-be-used")

    def calls():
        path = tmp_path / "calls.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    return calls


def test_the_old_env_writes_a_threads_post_with_codex_on_the_new_model_and_never_calls_claude(tmp_path, cli):
    writer = make_writer(settings(tmp_path, **OLD_ENV))
    assert writer.threads(ITEM, BRIEFING).topic_tag == "交換學生"
    (call,) = cli()
    assert call["tool"] == "codex" and call["args"][call["args"].index("-m") + 1] == "gpt-6.1-sol"
    assert 'model_reasoning_effort="high"' in call["args"]


def test_when_codex_is_down_antigravity_answers_on_its_model_and_claude_is_still_never_called(tmp_path, cli, monkeypatch):
    monkeypatch.setenv("FAKE_FAIL", "codex")
    writer = make_writer(settings(tmp_path, **OLD_ENV))
    assert writer.threads(ITEM, BRIEFING).topic_tag == "交換學生"
    calls = cli()
    assert [c["tool"] for c in calls] == ["codex", "agy"]
    assert calls[1]["args"][-2:] == ["--model", "Gemini 4 Argon (High)"]


def test_with_no_env_at_all_the_office_posts_every_second_day(tmp_path):
    office = Office(settings(tmp_path, OFFICE_BRAINS="offline"))
    day = date(2030, 1, 7)
    morning = lambda d: datetime(d.year, d.month, d.day, 1, 0, tzinfo=timezone.utc)  # noqa: E731 - 09:00 in Taipei
    assert tick(office, morning(day), background=False).get("run") == day.isoformat()
    assert "run" not in tick(office, morning(day + timedelta(days=1)), background=False)
    assert tick(office, morning(day + timedelta(days=2)), background=False).get("run") == (day + timedelta(days=2)).isoformat()


def test_the_chief_still_cannot_bring_claude_back_under_the_defaults(tmp_path):
    office = Office(settings(tmp_path, OFFICE_BRAINS="offline"))
    with pytest.raises(ValueError, match="只允許用 Codex、Antigravity"):
        office.tune("threads", brain="claude-code")
