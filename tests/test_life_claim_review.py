"""Bounded correction regressions; these tests do not verify external facts."""
import json
from pathlib import Path
import pytest

from exchange_info import life_context as life
from exchange_info.generated_content_review import ROUND21_MANIFEST, ROUND22_MANIFEST, load_manifest, review_generated_content
from exchange_info.life_claim_review import withdrawn_life_claim
from exchange_info.models import DestinationProfile, PartnerUniversity

ROOT = Path(__file__).resolve().parents[1]


def old_life_row(school="fcu"):
    path = ROOT / "src/exchange_info/official_data" / school / "student_life.jsonl"
    row = json.loads(path.read_text("utf8").splitlines()[0])
    archived = row["reference_data"]
    row.update(archived.get("generated_life_before_review", archived))
    return row


@pytest.mark.parametrize("round_id,expected", [(21, 2359), (22, 425)])
def test_inspected_life_bundles_keep_originals_outside_evidence(round_id, expected):
    manifest = load_manifest(ROOT, round_id=round_id)
    count = 0
    for school in manifest["schools"]:
        path = ROOT / "src/exchange_info/official_data" / school / "student_life.jsonl"
        for row in map(json.loads, path.read_text("utf8").splitlines()):
            snapshot = life.LifeResearchSnapshot.model_validate(row)
            assert snapshot.status == "partial" and not snapshot.evidence
            old = row["reference_data"]["generated_life_before_review"]
            assert len(old["evidence"]) == 5
            assert all(withdrawn_life_claim(row["school_name"], row["country"], e) for e in old["evidence"])
            count += 1
    assert count == expected


@pytest.mark.parametrize("school", ["fcu", "fju", "scu"])
def test_stale_cache_does_not_restore_generated_claims_or_drop_new_sources(tmp_path, school):
    row = old_life_row(school)
    snapshot = life.LifeResearchSnapshot.model_validate(row)
    original = snapshot.evidence[0]
    # Same wording with a different supporting source is outside the old index.
    fresh = original.model_copy(update={"sources": [life.LifeSource(
        title="Independent source to review", url="https://host.example.edu/incoming/housing")],
        "scope": "New independent source; not verified by this test"})
    snapshot = snapshot.model_copy(update={"evidence": [*snapshot.evidence, fresh]})
    partner = PartnerUniversity(school_name=row["school_name"], country=row["country"],
        program_type="交換學生", source_url="https://home.example.edu/exchange")
    path = life._cache_path(partner, tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(snapshot.model_dump_json(), encoding="utf8")
    before = path.read_bytes()
    result = life.read_research(partner, tmp_path)
    assert result.evidence == [fresh]
    assert result.status == "partial"
    assert any("範本" in note for note in result.notes)
    assert path.read_bytes() == before


def test_prior_reviewed_bundles_are_also_filtered_from_cached_snapshots():
    for school in ("nkust", "yuntech", "wzu", "pccu", "ntou"):
        snapshot = life.LifeResearchSnapshot.model_validate(old_life_row(school))
        assert snapshot.evidence
        result = life.reviewed_life_snapshot(snapshot)
        assert not result.evidence and result.status == "partial"


@pytest.mark.parametrize("school", ["fcu", "fju", "scu"])
def test_profile_flag_does_not_repromote_inspected_generated_values(school):
    path = ROOT / "src/exchange_info/official_data" / school / "destination_profiles.jsonl"
    raw = json.loads(path.read_text("utf8").splitlines()[0])
    # Later source reviews may legitimately replace a template. This regression
    # exercises the inspected original values, not the new source-backed text.
    archive = raw.get("reference_data", {}).get("source_review_round25", {})
    for field in ("housing_summary", "cost_summary", "transport_summary", "campus_life_summary"):
        if "/" + field in archive:
            raw[field] = archive["/" + field]["value"]
    profile = DestinationProfile.model_validate(raw)
    # A stronger-looking label cannot turn the same generated values into evidence.
    profile = profile.model_copy(update={"coverage_status": "official_verified"})
    assert profile.sources
    assert not life._profile_evidence(profile)
    changed = profile.model_copy(update={"housing_summary": "另行整理的新住宿原文內容，舊指紋不得覆寫。"})
    rows = life._profile_evidence(changed)
    assert len(rows) == 1 and rows[0].text == changed.housing_summary


@pytest.mark.parametrize("school,round_id,source", [("fcu", 21, ROUND21_MANIFEST),
    ("fju", 22, ROUND22_MANIFEST), ("scu", 22, ROUND22_MANIFEST)])
def test_life_replay_is_bounded_and_preserves_independently_edited_rows(tmp_path, school, round_id, source):
    manifest = tmp_path / source
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes((ROOT / source).read_bytes())
    original = old_life_row(school)
    modified = json.loads(json.dumps(original))
    modified["evidence"][0]["text"] = "新的逐校住宿整理；不可套用舊範本修正。"
    folder = tmp_path / "src/exchange_info/official_data" / school
    folder.mkdir(parents=True)
    path = folder / "student_life.jsonl"
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [original, modified]) + "\n", "utf8")
    stories = folder / "student_experiences.jsonl"
    stories.write_bytes(b"UNRELATED STORIES MUST NOT BE READ OR REWRITTEN\n")
    assert review_generated_content(tmp_path, school, round_id=round_id) == {
        "stories_changed": 0, "life_changed": 1, "digests_changed": 0}
    rows = list(map(json.loads, path.read_text("utf8").splitlines()))
    assert not rows[0]["evidence"] and rows[1] == modified
    before = path.read_bytes()
    assert not any(review_generated_content(tmp_path, school, round_id=round_id).values())
    assert before == path.read_bytes()
    assert stories.read_bytes() == b"UNRELATED STORIES MUST NOT BE READ OR REWRITTEN\n"
