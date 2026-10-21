import json
from pathlib import Path

from exchange_info.generated_content_review import MANIFEST, digest, review_generated_content
from exchange_info.models import StudentExperienceSource
from exchange_info.experience_collector import build_experience_digest
from exchange_info.life_context import LifeResearchSnapshot

ROOT = Path(__file__).resolve().parents[1]


def test_only_the_inspected_generated_claims_are_withdrawn(tmp_path):
    manifest = tmp_path / MANIFEST
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes((ROOT / MANIFEST).read_bytes())
    real = ROOT / "src/exchange_info/official_data/pccu"
    row = json.loads((real / "student_experiences.jsonl").read_text("utf8").splitlines()[0])
    original = row["reference_data"]["generated_claims_before_review"]
    row.update(original)
    independently_changed = json.loads(json.dumps(row))
    independently_changed["summary"] = "重新查核原文後的獨立修改；不可被舊範本修正覆寫。"
    independently_changed["theme_summaries"] = {"housing": "新來源的宿舍資訊另有證據。"}
    folder = tmp_path / "src/exchange_info/official_data/pccu"
    folder.mkdir(parents=True)
    stories = folder / "student_experiences.jsonl"
    stories.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [row, independently_changed]) + "\n", "utf8")
    (folder / "student_life.jsonl").write_text("", "utf8")
    counts = review_generated_content(tmp_path, "pccu")
    assert counts["stories_changed"] == 1
    result = [json.loads(line) for line in stories.read_text("utf8").splitlines()]
    assert result[0]["content_status"] == "metadata_only"
    assert not result[0]["theme_summaries"]
    assert digest(result[0]["reference_data"]["generated_claims_before_review"]) == digest(original)
    assert result[1] == independently_changed
    before = stories.read_bytes()
    assert review_generated_content(tmp_path, "pccu")["stories_changed"] == 0
    assert stories.read_bytes() == before


def test_four_bundles_preserve_candidates_without_generated_testimony():
    story_count = life_count = 0
    for school in ("nkust", "yuntech", "wzu", "pccu"):
        folder = ROOT / "src/exchange_info/official_data" / school
        for line in (folder / "student_experiences.jsonl").read_text("utf8").splitlines():
            raw = json.loads(line)
            source = StudentExperienceSource.model_validate(raw)
            assert source.content_status == "metadata_only" and source.source_url
            assert not source.theme_summaries and not source.theme_summaries_zh
            digest_result = build_experience_digest(source.school_name, source.country, [source])
            assert not digest_result.highlights and not digest_result.common_strengths
            assert raw["reference_data"]["generated_claims_before_review"]
            story_count += 1
        for line in (folder / "student_life.jsonl").read_text("utf8").splitlines():
            raw = json.loads(line)
            entry = LifeResearchSnapshot.model_validate(raw)
            assert entry.status == "partial" and not entry.evidence
            assert raw["reference_data"]["generated_life_before_review"]["evidence"]
            life_count += 1
    assert story_count == 129 and life_count == 501
