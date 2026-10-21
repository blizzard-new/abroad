from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil

from exchange_info.application_rules import build_personal_application_plan
from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PersonalApplicationPlanRequest, UniversityApplicationWorkflow
from exchange_info.ntut_ips_review import ARCHIVE_KEY, DISPLAY_MANIFEST, MANIFEST, METADATA_MANIFEST, apply_ntut_ips_review, load_manifest
from exchange_info.ntut_source_review import SNAPSHOT, review_bundle
from exchange_info.ntut_student_view import fetch_ntut_partner_universities, ntut_school_location
from exchange_info.ntust_source_review import write_atomic

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path("src/exchange_info/official_data/ntut")
NAME = "早稻田大學 Waseda University"


def _rows(root, filename):
    return [json.loads(line) for line in (root / BUNDLE / filename).read_text("utf8").splitlines()]


def _waseda(root, filename):
    return next(row for row in _rows(root, filename) if row["school_name"] == NAME)


def test_degree_route_keeps_conflicts_and_does_not_award_exchange_eligibility():
    partner = next(p for p in fetch_ntut_partner_universities() if p.school_name == NAME)
    raw = _waseda(ROOT, "partners.jsonl")
    workflow = UniversityApplicationWorkflow.model_validate(_waseda(ROOT, "application_workflows.jsonl"))
    visible = json.dumps({k: v for k, v in raw.items() if k != "reference_data"}, ensure_ascii=False)
    assert "ITP 520" not in visible and "總平均達 70" not in visible
    assert "1+1.5" in partner.study_period and "總表仍寫 1+1" in partner.study_period
    assert "日本以外及 IP 不收" in partner.language_requirement
    assert "2026/11/16–11/27" in partner.application_deadline and "矛盾" in partner.application_deadline
    assert "917,500" in partner.tuition_info
    assert all("12月1日至12月10日" not in s.title and "70 分" not in s.title for s in workflow.steps)
    assert all(not s.deadline_reminder_eligible for s in workflow.steps)
    assert "2028" not in json.dumps(workflow.effective_application_rounds, ensure_ascii=False)
    request = PersonalApplicationPlanRequest(
        home_school="國立臺北科技大學", academic_year="116", application_round=workflow.application_round,
        degree_level="學士班", current_year="大三", college="電資學院", academic_score=95,
        language_test="toeic", language_score=990, preferences=[{"rank": 1, "school_name": NAME}],
    )
    plan = build_personal_application_plan(request, [partner], [workflow], academic_score_minimum=None)
    assert plan.choices[0].status == "needs_confirmation"
    assert partner.location.city == "北九州市（福岡縣）"
    assert partner.location.latitude is None
    destination = _waseda(ROOT, "destination_profiles.jsonl")
    assert "Tokyo" not in destination["transport_summary"]
    assert "待查核" in destination["housing_summary"]
    assert "4–8 週" not in json.dumps(destination["student_guide_sections"], ensure_ascii=False)
    # A global university pin must not silently put this degree program in Tokyo.
    unrelated_campus = object()
    assert ntut_school_location(partner, unrelated_campus) is partner.location


def test_value_guarded_replay_preserves_other_rows_and_independent_edits(tmp_path):
    manifest = load_manifest(ROOT)
    (tmp_path / Path(MANIFEST).parent).mkdir(parents=True)
    shutil.copy2(ROOT / MANIFEST, tmp_path / MANIFEST)
    shutil.copy2(ROOT / METADATA_MANIFEST, tmp_path / METADATA_MANIFEST)
    shutil.copy2(ROOT / DISPLAY_MANIFEST, tmp_path / DISPLAY_MANIFEST)
    before_other = {}
    for scope in manifest["rows"]:
        path = tmp_path / scope["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / scope["file"], path)
        rows = _rows(ROOT, path.name)
        before_other[path.name] = [r for r in rows if r["school_name"] != NAME]
        target = next(r for r in rows if r["school_name"] == NAME)
        target.get("reference_data", {}).pop(ARCHIVE_KEY, None)
        for patch in scope["patches"]:
            parent, key = pointer_parent(target, patch["pointer"])
            if patch["expected_missing"]:
                parent.pop(key)
            else:
                parent[key] = copy.deepcopy(patch["expected_values"][0])
        write_atomic(path, rows, True)
    assert apply_ntut_ips_review(tmp_path) == manifest["patch_count"]
    first = {s["file"]: (tmp_path / s["file"]).read_bytes() for s in manifest["rows"]}
    assert apply_ntut_ips_review(tmp_path) == 0
    assert all((tmp_path / file).read_bytes() == data for file, data in first.items())
    for filename, other in before_other.items():
        assert [r for r in _rows(tmp_path, filename) if r["school_name"] != NAME] == other
    rows = _rows(tmp_path, "partners.jsonl")
    target = next(r for r in rows if r["school_name"] == NAME)
    target["tuition_info"] = "Independent later fee agreement review"
    write_atomic(tmp_path / BUNDLE / "partners.jsonl", rows, True)
    assert apply_ntut_ips_review(tmp_path) == 0
    assert _waseda(tmp_path, "partners.jsonl")["tuition_info"] == target["tuition_info"]


def test_mother_rule_refresh_retains_more_specific_degree_review(tmp_path):
    from exchange_info.vilnius_akita_review import MANIFEST as HOST_MANIFEST, COST_MANIFEST
    for relative in (MANIFEST, METADATA_MANIFEST, DISPLAY_MANIFEST, SNAPSHOT, HOST_MANIFEST, COST_MANIFEST):
        (tmp_path / Path(relative).parent).mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, tmp_path / relative)
    (tmp_path / BUNDLE).mkdir(parents=True)
    filenames = ["student_dashboard.json", "home_rules.json", "exchange_info.json", "pages.jsonl",
                 "partners.jsonl", "application_workflows.jsonl", "destination_profiles.jsonl",
                 "catalog-completeness.json", "verification_status.json", "import_provenance.json",
                 "documents.json", "scholarships.json"]
    for filename in filenames:
        shutil.copy2(ROOT / BUNDLE / filename, tmp_path / BUNDLE / filename)
    expected = {name: _waseda(tmp_path, name) for name in
                ("partners.jsonl", "application_workflows.jsonl", "destination_profiles.jsonl")}
    host_expected = {name: [r for r in _rows(tmp_path, name) if 'source_review_round45' in r.get('reference_data', {})]
                     for name in expected}
    review_bundle(tmp_path)
    assert {name: _waseda(tmp_path, name) for name in expected} == expected
    assert {name: [r for r in _rows(tmp_path, name) if 'source_review_round45' in r.get('reference_data', {})]
            for name in expected} == host_expected
