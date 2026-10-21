"""Only explicit admissions degrees may be shown for SCU partner rows."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PartnerUniversity
from exchange_info.scu_degree_source_review import MANIFEST, apply_scu_degree_source_review, degree_scope, load_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_unknown_degrees_do_not_default_to_all_levels():
    assert degree_scope("僅受理學士生申請。") == "大學部（僅學士生可申請）"
    assert degree_scope("僅受理碩士生申請。") == "碩士班（僅碩士生可申請）"
    assert "未分碩、博士" in degree_scope("學士、研究生。")
    with pytest.raises(ValueError, match="needs source review"):
        degree_scope("請洽各院系")
    with pytest.raises(ValueError, match="needs source review"):
        degree_scope("僅開放學士課程供研究生選修")


def test_builder_parses_all_126_source_degree_lines_without_expanding_graduate():
    spec = importlib.util.spec_from_file_location("scu_builder_under_test", ROOT / "scripts/build_scu_catalog.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    rows = builder.parse_intl_126_schools()
    reviewed = {row["school_name"]: row for row in load_manifest(ROOT)["source_rows"]}
    assert len(rows) == len(reviewed) == 126
    for row in rows:
        assert row["degree_levels"] == reviewed[row["full_name"]]["value"]
    counts = Counter(row["degree_levels"] for row in rows)
    assert counts["大學部（僅學士生可申請）"] == 8
    assert counts["碩士班（僅碩士生可申請）"] == 1
    assert sum("申請時" in row["degree_levels"] for row in rows) == 2


def test_scoped_replay_keeps_other_schools_and_previous_conflicts(tmp_path):
    manifest = load_manifest(ROOT)
    (tmp_path / MANIFEST).parent.mkdir(parents=True)
    shutil.copy2(ROOT / MANIFEST, tmp_path / MANIFEST)
    path = tmp_path / "src/exchange_info/official_data/scu/partners.jsonl"
    path.parent.mkdir(parents=True)
    rows = [json.loads(line) for line in (ROOT / path.relative_to(tmp_path)).read_text("utf8").splitlines()]
    by_name = {row["school_name"]: row for row in rows}
    for scope in manifest["rows"]:
        row = by_name[scope["school_name"]]
        for patch in scope["patches"]:
            parent, key = pointer_parent(row, patch["pointer"], create=True)
            if patch["expected_missing"]:
                parent.pop(key, None)
            else:
                parent[key] = patch["expected_values"][0]
    independent = next(row for row in rows if "Chuo University" in row["school_name"])
    independent["degree_levels"] = "New independent faculty confirmation"
    unchanged = {r["school_name"]: json.dumps(r, ensure_ascii=False) for r in rows
                 if r["school_name"] not in {s["school_name"] for s in manifest["rows"]}}
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf8")
    assert apply_scu_degree_source_review(tmp_path) == 500
    result = [json.loads(line) for line in path.read_text("utf8").splitlines()]
    for row in result:
        PartnerUniversity.model_validate(row)
        if row["school_name"] in unchanged:
            assert json.dumps(row, ensure_ascii=False) == unchanged[row["school_name"]]
        if "Chuo University" in row["school_name"]:
            assert row["degree_levels"] == "New independent faculty confirmation"
        if any(name in row["school_name"] for name in ("Takushoku", "Tunku Abdul")):
            assert row["availability_status"] == "needs_confirmation"
        if "Kurume" in row["school_name"]:
            assert "日語別科" in row["course_restrictions"]
    before = path.read_bytes()
    assert apply_scu_degree_source_review(tmp_path) == 0
    assert path.read_bytes() == before
