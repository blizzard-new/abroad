"""Regression coverage for inspected story templates, not external school facts."""
import json
from collections import Counter
from pathlib import Path

from exchange_info.experience_collector import build_experience_digest
from exchange_info.experience_digests import source_kind
from exchange_info.generated_content_review import (
    ROUND20_MANIFEST, load_manifest, review_generated_content,
)
from exchange_info.models import StudentExperienceSource

ROOT = Path(__file__).resolve().parents[1]


def test_round20_story_bundles_have_no_generated_theme_claims():
    manifest = load_manifest(ROOT, round_id=20)
    roles = Counter()
    for school in manifest["schools"]:
        folder = ROOT / "src/exchange_info/official_data" / school
        for raw in map(json.loads, (folder / "student_experiences.jsonl").read_text("utf8").splitlines()):
            source = StudentExperienceSource.model_validate(raw)
            assert source.content_status == "metadata_only"
            assert not source.themes and not source.theme_summaries and not source.theme_summaries_zh
            assert raw["reference_data"]["generated_claims_before_review"]
            roles[source.perspective] += 1
            if source.perspective == "official_program_record":
                digest = build_experience_digest(source.school_name, source.country, [source])
                assert digest.total_sources == 0
            elif source.perspective == "official_directory":
                assert source_kind(source) == "source_index"
    assert roles == {"official_directory": 1697, "official_program_record": 302, "official_student_story": 2}


def test_official_short_excerpts_survive_without_inferred_topics():
    folder = ROOT / "src/exchange_info/official_data/fcu"
    rows = [row for row in map(json.loads, (folder / "student_experiences.jsonl").read_text("utf8").splitlines())
        if row["perspective"] == "official_student_story"]
    assert {row["author_name"] for row in rows} == {"國貿系 池濬竹", "建築系 林子瑜"}
    for row in rows:
        source = StudentExperienceSource.model_validate(row)
        assert "非完整報告" in source.summary
        assert "未提供修課、宿舍或費用細節" in source.summary
        assert source_kind(source) == "personal_story"
        assert row["reference_data"]["excerpt_review"]["source_sha256"] == "ac8e5e2fc2a6bbbd570d22e305c87345d01b198c1d2cb2af9edcfccf7eeef636"
        assert not build_experience_digest(source.school_name, source.country, [source]).highlights


def test_round20_replay_preserves_independent_edits_and_unreviewed_life(tmp_path):
    path = tmp_path / ROUND20_MANIFEST
    path.parent.mkdir(parents=True)
    path.write_bytes((ROOT / ROUND20_MANIFEST).read_bytes())
    real = ROOT / "src/exchange_info/official_data/fcu/student_experiences.jsonl"
    row = next(row for row in map(json.loads, real.read_text("utf8").splitlines())
        if row["perspective"] == "official_student_story")
    row.update(row["reference_data"]["generated_claims_before_review"])
    edited = json.loads(json.dumps(row))
    edited["summary"] = "另外讀過原文後的獨立修正，不套舊指紋。"
    folder = tmp_path / "src/exchange_info/official_data/fcu"
    folder.mkdir(parents=True)
    stories = folder / "student_experiences.jsonl"
    stories.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [row, edited]) + "\n", "utf8")
    life = folder / "student_life.jsonl"
    life.write_bytes(b"UNREVIEWED LIFE CONTENT MUST STAY IDENTICAL\n")
    before_life = life.read_bytes()
    assert review_generated_content(tmp_path, "fcu", round_id=20) == {
        "stories_changed": 1, "life_changed": 0, "digests_changed": 0,
    }
    result = list(map(json.loads, stories.read_text("utf8").splitlines()))
    assert result[0]["content_status"] == "metadata_only"
    assert result[0]["author_name"] in {"國貿系 池濬竹", "建築系 林子瑜"}
    assert result[1] == edited
    assert life.read_bytes() == before_life
    before_stories = stories.read_bytes()
    assert not any(review_generated_content(tmp_path, "fcu", round_id=20).values())
    assert stories.read_bytes() == before_stories
