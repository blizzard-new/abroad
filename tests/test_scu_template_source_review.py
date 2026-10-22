"""Source-free constants cannot imply verified host faculties or calendar dates."""
import json
from pathlib import Path
import shutil

from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PartnerUniversity
from exchange_info.scu_template_source_review import MANIFEST, apply_scu_template_source_review, load_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_withdrawal_preserves_specific_corrections_and_independent_new_evidence(tmp_path):
    manifest = load_manifest(ROOT)
    (tmp_path / MANIFEST).parent.mkdir(parents=True)
    shutil.copy2(ROOT / MANIFEST, tmp_path / MANIFEST)
    path = tmp_path / "src/exchange_info/official_data/scu/partners.jsonl"
    path.parent.mkdir(parents=True)
    rows = [json.loads(line) for line in (ROOT / path.relative_to(tmp_path)).read_text("utf8").splitlines()]
    names = {row["school_name"]: row for row in rows}
    for scope in manifest["rows"]:
        for patch in scope["patches"]:
            parent, key = pointer_parent(names[scope["school_name"]], patch["pointer"])
            parent[key] = patch["expected_values"][0]
    chosen = next(row for row in rows if "Chuo University" in row["school_name"])
    chosen["housing_info"] = "Independently checked host residence information"
    before = {row["school_name"]: {key: row.get(key) for key in
              ("quota", "language_requirement", "application_deadline", "gpa_requirement", "degree_levels", "availability_status")}
              for row in rows}
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), "utf8")
    assert apply_scu_template_source_review(tmp_path) == 1135
    after = [json.loads(line) for line in path.read_text("utf8").splitlines()]
    for row in after:
        PartnerUniversity.model_validate(row)
        assert all(row.get(key) == value for key, value in before[row["school_name"]].items())
        assert row["colleges"] != "全校各學院（部分院系或專業限制依協議校規定）"
        assert "尚未核實" in row["semester_dates"] or "尚待核實" in row["semester_dates"]
        if "Chuo University" in row["school_name"]:
            assert row["housing_info"] == "Independently checked host residence information"
        else:
            assert "尚未逐校核實" in row["housing_info"]
        if "Kurume" in row["school_name"]:
            assert "日語別科" in row["colleges"]
    saved = path.read_bytes()
    assert apply_scu_template_source_review(tmp_path) == 0
    assert saved == path.read_bytes()
