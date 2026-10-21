from __future__ import annotations

import copy
import json
import re
from pathlib import Path
import shutil
from datetime import datetime

from exchange_info.application_rules import build_personal_application_plan
from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PersonalApplicationPlanRequest, UniversityApplicationWorkflow
from exchange_info.ncku_partner_table_review import ARCHIVE_KEY, MANIFEST, METADATA_MANIFEST, apply_ncku_partner_table_review, load_manifest
from exchange_info.ncku_student_view import fetch_ncku_partner_universities
from exchange_info.ntust_source_review import write_atomic

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path("src/exchange_info/official_data/ncku")


def rows(root, filename):
    return [json.loads(s) for s in (root / BUNDLE / filename).read_text("utf8").splitlines()]


def test_all_reviewed_rows_preserve_source_and_scope():
    manifest = load_manifest(ROOT)
    partners = {p.school_name: p for p in fetch_ncku_partner_universities(reference_time=datetime.fromisoformat("2026-10-21T12:00:00+08:00"))}
    assert len(manifest["source_rows"]) == 97
    for source in manifest["source_rows"]:
        assert re.sub(r'[\s*]', '', source["reviewed_requirement_text"]) == re.sub(r'[\s*]', '', source["requirements_raw"])
        partner = partners[source["school_name"]]
        evidence = partner.field_evidence["mother_table_requirements"]
        assert evidence.excerpt == source["requirements_raw"]
        assert evidence.source_pages == [source["page"]]
        assert partner.field_evidence["quota"].excerpt == source["quota_raw"]
        assert partner.availability_status == "needs_confirmation"
        assert partner.application_window_status == "upcoming"
    kit = next(p for p in partners.values() if p.school_name.startswith("九州工業大學 "))
    assert "大學部在校生:申請者須具備日語 JLPT N2" in kit.language_requirement
    assert "研究所在校生:申請者須具備英語CEFR B2" in kit.language_requirement
    ucl = next(p for p in partners.values() if p.school_name.startswith("倫敦大學學院 "))
    assert "大三上" in ucl.degree_levels and "高於 3.3" in ucl.eligibility
    assert "109" in ucl.language_requirement and "27" in ucl.language_requirement
    assert "僅可申請 European and International Social and Political Studies" in ucl.eligibility
    waseda = next(p for p in partners.values() if p.school_name.startswith("早稻田大學 "))
    assert "確認符合資格後提出申請" in waseda.language_requirement
    assert "不接受跨領域申請" in waseda.eligibility
    vilnius = next(p for p in partners.values() if p.school_name.startswith("維爾紐斯大學 "))
    assert vilnius.field_evidence["degree_levels"].status == "conflict"
    assert vilnius.field_evidence["language_requirement"].status == "conflict"
    assert "TOEIC 讀寫785" in vilnius.language_requirement
    akita = next(p for p in partners.values() if p.school_name.startswith("秋田大學 "))
    assert akita.field_evidence["degree_levels"].status == "conflict"


def test_mother_qualification_does_not_resolve_host_eligibility():
    partner = next(p for p in fetch_ncku_partner_universities() if p.school_name.startswith("早稻田大學 "))
    workflow = UniversityApplicationWorkflow.model_validate(next(
        r for r in rows(ROOT, "application_workflows.jsonl") if r["school_name"] == partner.school_name))
    assert workflow.review_status == "pending_review"
    host = next(s for s in workflow.steps if s.phase == "合作校申請")
    assert host.needs_confirmation and host.support_status == "needs_confirmation"
    assert "115-2" not in host.scope.application_rounds
    request = PersonalApplicationPlanRequest(home_school="國立成功大學", academic_year="116",
        application_round=partner.application_round, degree_level="博士班", current_year="博二",
        academic_score=95, language_test="toeic", language_score=990,
        preferences=[{"rank":1,"school_name":partner.school_name}])
    plan = build_personal_application_plan(request, [partner], [workflow], academic_score_minimum=None)
    assert plan.choices[0].status == "needs_confirmation"


def test_replay_restores_reviewed_variants_and_preserves_unrelated_data(tmp_path):
    manifest = load_manifest(ROOT)
    (tmp_path / Path(MANIFEST).parent).mkdir(parents=True)
    shutil.copy2(ROOT / MANIFEST, tmp_path / MANIFEST)
    shutil.copy2(ROOT / METADATA_MANIFEST, tmp_path / METADATA_MANIFEST)
    (tmp_path / BUNDLE).mkdir(parents=True)
    for filename in ("catalog-completeness.json", "verification_status.json"):
        shutil.copy2(ROOT / BUNDLE / filename, tmp_path / BUNDLE / filename)
    reviewed_names = {r["school_name"] for r in manifest["source_rows"]}
    unrelated = {}
    file_rows = {}
    for filename in {s["file"] for s in manifest["rows"]}:
        path = tmp_path / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / filename, path)
        data = rows(ROOT, path.name)
        unrelated[path.name] = [r for r in data if r["school_name"] not in reviewed_names]
        file_rows[filename] = data
    for scope in manifest["rows"]:
        target = next(r for r in file_rows[scope["file"]] if r["school_name"] == scope["school_name"])
        target.get("reference_data", {}).pop(ARCHIVE_KEY, None)
        for patch in scope["patches"]:
            parent, key = pointer_parent(target, patch["pointer"])
            if patch["expected_missing"]:
                parent.pop(key)
            else:
                parent[key] = copy.deepcopy(patch["expected_values"][0])
    for filename, data in file_rows.items():
        write_atomic(tmp_path / filename, data, True)
    assert apply_ncku_partner_table_review(tmp_path) == manifest["patch_count"]
    expected = {filename: (tmp_path / filename).read_bytes() for filename in file_rows}
    assert apply_ncku_partner_table_review(tmp_path) == 0
    assert all((tmp_path / f).read_bytes() == data for f, data in expected.items())
    for filename, original in unrelated.items():
        assert [r for r in rows(tmp_path, filename) if r["school_name"] not in reviewed_names] == original
    data = rows(tmp_path, "partners.jsonl")
    target = next(r for r in data if r["school_name"] in reviewed_names)
    target["language_requirement"] = "Independent later host review"
    write_atomic(tmp_path / BUNDLE / "partners.jsonl", data, True)
    assert apply_ncku_partner_table_review(tmp_path) == 0
    assert next(r for r in rows(tmp_path,"partners.jsonl") if r["school_name"] == target["school_name"])["language_requirement"] == "Independent later host review"
