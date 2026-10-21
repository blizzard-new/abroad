"""Prevent GPA scale conversion and semester inflation in SCU public data."""
import json
import shutil
from pathlib import Path

from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PartnerUniversity, UniversityApplicationWorkflow
from exchange_info.scu_table_source_review import MANIFEST, apply_scu_table_source_review, load_manifest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path("src/exchange_info/official_data/scu")


def fixture(root):
    manifest = load_manifest(ROOT)
    (root / MANIFEST).parent.mkdir(parents=True)
    shutil.copy2(ROOT / MANIFEST, root / MANIFEST)
    paths = {s["file"] for s in manifest["rows"]} | {str(BUNDLE / name) for name in ("catalog-completeness.json", "verification_status.json")}
    for name in paths:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    for filename in {s["file"] for s in manifest["rows"]}:
        path = root / filename
        rows = [json.loads(line) for line in path.read_text("utf8").splitlines()]
        for scope in [s for s in manifest["rows"] if s["file"] == filename]:
            row = next(r for r in rows if r["school_name"] == scope["school_name"])
            for patch in scope["patches"]:
                parent, key = pointer_parent(row, patch["pointer"], create=True)
                if patch["expected_missing"]:
                    parent.pop(key, None)
                else:
                    parent[key] = patch["expected_values"][0]
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf8")
    return manifest, paths


def test_original_scales_and_years_are_retained_without_removing_other_conditions(tmp_path):
    manifest, files = fixture(tmp_path)
    path = tmp_path / BUNDLE / "partners.jsonl"
    before = {r["school_name"]: r for r in map(json.loads, path.read_text("utf8").splitlines())}
    assert apply_scu_table_source_review(tmp_path) == 54
    rows = list(map(json.loads, path.read_text("utf8").splitlines()))
    def school(needle):
        return next(r for r in rows if needle in r["school_name"])
    for needle, scale in [("Niigata", "2.3 / 3.0"), ("Fukui", "2.3 / 3.0"), ("Hanyang", "60 / 100"), ("Handong", "2.5 / 4.5")]:
        assert scale in school(needle)["gpa_requirement"]
        assert "/ 4.0" not in school(needle)["gpa_requirement"]
        assert "85%" in school(needle)["gpa_requirement"]
    assert "未提供最低數值" in school("De La Salle")["gpa_requirement"]
    sogang = school("Sogang")
    assert "每學年1名" in sogang["quota"] and "每學年1名" in sogang["notes"]
    assert "每學年名額/Quota" not in sogang["language_requirement"]
    assert "校內門檻" in sogang["eligibility"] and "法律系課程不開放" in sogang["notes"]
    for needle, year in [("Takushoku", "2027春季"), ("Tunku Abdul", "2026秋季")]:
        row = school(needle)
        assert row["availability_status"] == "needs_confirmation"
        assert row["quota_status"] == "reference_only" and year in row["quota"]
        assert "116學年度第1學期／第2學期" not in row["notes"]
    changed = {s["school_name"] for s in manifest["rows"]}
    assert all(row == before[row["school_name"]] for row in rows if row["school_name"] not in changed)
    for row in rows:
        PartnerUniversity.model_validate(row)
    for line in (tmp_path / BUNDLE / "application_workflows.jsonl").read_text("utf8").splitlines():
        UniversityApplicationWorkflow.model_validate(json.loads(line))
    metadata = json.loads((tmp_path / BUNDLE / "verification_status.json").read_text("utf8"))
    assert metadata["status"] == "partial_review"
    assert metadata["counts"]["open_partners"] == 189
    assert metadata["counts"]["needs_confirmation_partners"] == 2
    assert metadata["counts"]["whole_partner_records_verified"] == 0
    saved = {name: (tmp_path / name).read_bytes() for name in files}
    assert apply_scu_table_source_review(tmp_path) == 0
    assert saved == {name: (tmp_path / name).read_bytes() for name in files}
