"""A page load sent a thousand source texts through the translator again on every load; now each is asked and worked out once."""
from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info import public_translation
from exchange_info.api import create_app
from exchange_info.public_translation import (
    _valid_translation,
    needs_translation,
    standardize_terms,
    translate_display_phrases,
)

MODULE = Path("src/exchange_info/static/public-content-zh.js").resolve()
NTPU = "國立臺北大學"


def _node(script: str) -> None:
    result = subprocess.run(["node", "-e", script, str(MODULE)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr


def test_texts_the_server_cannot_translate_are_not_asked_about_again_in_the_same_visit() -> None:
    _node(r"""
const assert = require('node:assert/strict');
const zh = require(process.argv[1]);
let asked = [];
global.fetch = async (url, options) => {
  const body = JSON.parse(options.body); asked.push(...body.entries.map(row => row.text));
  return {ok: true, json: async () => ({generation_enabled: false, entries: body.entries.map(({text}) => (
    text.startsWith('Translated') ? {text, zh: '已翻譯', status: 'machine'} : {text, zh: '', status: 'pending'}))})};
};
(async () => {
  const data = () => ({summary_points: [], points: ['Translated one', 'Untranslated one', 'Untranslated two']});
  const first = await zh.localize('/destination-profiles', data());
  assert.deepEqual(first.points, ['已翻譯', 'Untranslated one', 'Untranslated two']);
  assert.equal(asked.length, 3);
  const second = await zh.localize('/destination-profiles', data());
  assert.deepEqual(second.points, ['已翻譯', 'Untranslated one', 'Untranslated two'], 'the page shows the same thing');
  assert.equal(asked.length, 3, 'nothing was sent the second time, neither the translated nor the pending texts');
  const third = await zh.localize('/destination-profiles', {points: ['Translated one', 'Brand new text']});
  assert.deepEqual(third.points, ['已翻譯', 'Brand new text']);
  assert.deepEqual(asked.slice(3), ['Brand new text'], 'only the text never seen before is sent');
})().catch(error => { console.error(error); process.exit(1); });
""")


def test_while_the_server_can_still_generate_translations_pending_texts_are_asked_again() -> None:
    _node(r"""
const assert = require('node:assert/strict');
const zh = require(process.argv[1]);
let rounds = 0;
global.fetch = async (url, options) => {
  const body = JSON.parse(options.body); if (!body.generate) rounds += 1;
  return {ok: true, json: async () => ({generation_enabled: true, entries: body.entries.map(({text}) => ({text, zh: '', status: 'pending'}))})};
};
(async () => {
  await zh.localize('/destination-profiles', {points: ['Needs a translation']});
  const before = rounds;
  await zh.localize('/destination-profiles', {points: ['Needs a translation']});
  assert.equal(rounds, before + 1, 'a generator may have produced it since');
})().catch(error => { console.error(error); process.exit(1); });
""")


def test_the_per_text_work_is_remembered_and_gives_the_same_answers() -> None:
    texts = [
        "The university offers many courses in English for exchange students.",
        "Housing is not guaranteed. Apply early.",
        "TOEIC 785 or IELTS 6.5 is required.",
        "宿舍費用每月約 NT$10,000。",
        "Die Bewerbung ist bis zum 15. Mai einzureichen.",
    ]
    for function in (needs_translation, standardize_terms, translate_display_phrases):
        function.cache_clear()
        expected = [function.__wrapped__(text) for text in texts]
        assert [function(text) for text in texts] == expected
        misses = function.cache_info().misses
        assert [function(text) for text in texts] == expected
        assert function.cache_info().misses == misses and function.cache_info().hits >= len(texts), function.__name__


def test_a_translation_that_is_not_text_is_rejected_without_error() -> None:
    for value in (None, ["中文"], {"zh": "中文"}, 7):
        assert _valid_translation("Housing", value) is False
    assert _valid_translation("Housing", "住宿") is True
    assert public_translation._valid_text_translation.cache_info().currsize >= 1


def test_the_compact_list_keeps_what_the_list_views_read_and_drops_the_guide_bodies() -> None:
    client = TestClient(create_app())
    full = client.get("/destination-profiles", params={"home_school": NTPU})
    compact = client.get("/destination-profiles", params={"home_school": NTPU, "compact": "true"})
    assert full.status_code == compact.status_code == 200
    assert len(compact.content) < len(full.content) * 0.5, "less than half the download"
    kept = ("school_name", "country", "city", "cost_summary", "housing_summary", "transport_summary",
            "campus_life_summary", "coverage_status", "coverage_note", "last_checked", "home_university")
    assert len(full.json()) == len(compact.json()) > 50
    for whole, slim in zip(full.json(), compact.json()):
        assert {key: whole[key] for key in kept} == {key: slim[key] for key in kept}
        assert [(s["title"], s["source_url"]) for s in whole["sources"]] == [(s["title"], s["source_url"]) for s in slim["sources"]]
        assert all(not s.get("summary") for s in slim["sources"])
        for heavy in ("student_guide_sections", "first_72_hours", "packing_from_taiwan", "buy_after_arrival"):
            assert slim[heavy] == []


def test_a_schools_full_profile_still_carries_its_guide() -> None:
    client = TestClient(create_app())
    profiles = client.get("/destination-profiles", params={"home_school": NTPU}).json()
    rich = next(row for row in profiles if row["student_guide_sections"] or row["first_72_hours"])
    single = client.get("/destination-profile", params={"school": rich["school_name"], "home_school": NTPU})
    assert single.status_code == 200
    assert single.json()["student_guide_sections"] == rich["student_guide_sections"]
    assert single.json()["first_72_hours"] == rich["first_72_hours"]


def test_the_default_list_is_unchanged() -> None:
    client = TestClient(create_app())
    plain = client.get("/destination-profiles", params={"home_school": NTPU}).json()
    assert any(row["student_guide_sections"] for row in plain)
    assert any(source.get("summary") for row in plain for source in row["sources"])
