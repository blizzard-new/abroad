"""Source-bound regression checks; not whole-school verification."""
import json
from pathlib import Path

from exchange_info import life_context as life
from exchange_info.models import DestinationProfile
from exchange_info.usp_source_review import MANIFEST, apply_usp_source_review, load_manifest, pointer_parent

ROOT = Path(__file__).resolve().parents[1]
BAD = "international.umontreal.ca"


def rows(path):
    return list(map(json.loads, path.read_text("utf8").splitlines()))


def test_all_scoped_usp_field_corrections_and_archives_are_present():
    for scope in load_manifest(ROOT)["rows"]:
        row = next(r for r in rows(ROOT / scope["file"]) if r["school_name"] == scope["school_name"])
        archive = row["reference_data"]["source_review_round23"]
        if isinstance(archive, str):
            archive = json.loads(archive)
        for patch in scope["patches"]:
            parent, key = pointer_parent(row, patch["pointer"])
            assert parent[key] == patch["value"]
            assert archive[patch["pointer"]] in patch["expected_values"]
        active = {k: v for k, v in row.items() if k != "reference_data"}
        assert BAD not in json.dumps(active)


def test_nthu_housing_uses_its_host_source_and_keeps_other_profiles_unchanged():
    path = ROOT / "src/exchange_info/official_data/nthu/destination_profiles.jsonl"
    row = next(r for r in rows(path) if r["school_name"].startswith("聖保羅大學"))
    profile = DestinationProfile.model_validate(row)
    evidence = life._profile_evidence(profile)
    assert len(evidence) == 1
    assert evidence[0].theme == "housing" and "不提供交換生校內住宿" in evidence[0].text
    assert [s.url for s in evidence[0].sources] == [
        "https://internationaloffice.usp.br/en/index.php/admissions/studentexchange/"]


def test_cached_old_usp_navigation_and_medical_claims_do_not_return():
    scope = next(s for s in load_manifest(ROOT)["rows"] if s["home_id"] == "ntu")
    old = scope["patches"][0]["expected_values"][0]
    fresh = {**old[0], "text": "獨立新資料；此測試不代表已核實。"}
    snapshot = life.LifeResearchSnapshot(school_name="聖保羅大學", country="巴西",
        status="ready", evidence=[*old, fresh])
    result = life.reviewed_life_snapshot(snapshot)
    assert len(result.evidence) == 1 and result.evidence[0].text == fresh["text"]
    assert result.status == "partial"


def test_partial_rebuild_preserves_independent_evidence_and_is_idempotent(tmp_path):
    manifest = load_manifest(ROOT)
    scope = next(s for s in manifest["rows"] if s["home_id"] == "ntu")
    path = tmp_path / scope["file"]
    path.parent.mkdir(parents=True)
    source = tmp_path / MANIFEST
    source.parent.mkdir(parents=True)
    source.write_bytes((ROOT / MANIFEST).read_bytes())
    old = scope["patches"][0]["expected_values"][0]
    fresh = {**old[0], "text": "獨立新資料；重新建置不得刪除。"}
    # Initial extraction has already filtered old navigation; completion can
    # reintroduce just these three historical additions.
    row = {"school_name": "聖保羅大學", "country": "巴西", "status": "partial",
        "evidence": [*old[-3:], fresh], "notes": ["independent note"], "checked_at": None}
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", "utf8")
    assert apply_usp_source_review(tmp_path, "ntu") == 1
    result = rows(path)[0]
    assert result["evidence"][0] == fresh
    assert len(result["evidence"]) == 9 and result["notes"] == ["independent note"]
    before = path.read_bytes()
    assert apply_usp_source_review(tmp_path, "ntu") == 0
    assert path.read_bytes() == before
