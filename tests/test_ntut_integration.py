from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from exchange_info import storage
from exchange_info.access_control import school_from_email
from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates
from exchange_info.application_rules import (
    build_personal_application_plan,
    select_application_workflow,
)
from exchange_info.cost_estimates import budget_fit, extract_monthly_estimates, primary_estimate
from exchange_info.models import ApplicationRuleContext, PersonalApplicationPlanRequest
from exchange_info.school_completeness import build_school_completeness
from exchange_info.university_registry import NTUT, require_university
from exchange_info.ntut_eligibility import (
    is_ntut,
    ntut_academic_check,
    ntut_degree_check,
    ntut_language_check,
)
from exchange_info.ntut_student_view import (
    build_ntut_student_dashboard,
    fetch_ntut_partner_universities,
    ntut_exchange_info,
    ntut_processed_pages,
)

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ntut"


@pytest.mark.parametrize(
    "alias",
    [
        "ntut",
        "NTUT",
        "北科大",
        "臺北科大",
        "台北科大",
        "臺北科技大學",
        "國立臺北科技大學",
        "Taipei Tech",
        "National Taipei University of Technology",
    ],
)
def test_ntut_aliases(alias: str) -> None:
    assert require_university(alias) == NTUT
    assert is_ntut(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@ntut.edu.tw", True),
        ("t1110001@tmail.ntut.edu.tw", True),
        ("t1110001@mail.ntut.edu.tw", True),
        ("t1110001@ntut.org.tw", True),
        ("student@ntust.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_ntut_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == NTUT) is allowed


def test_ntut_degree_and_academic_checks() -> None:
    assert ntut_degree_check("學士班", "大一")[0] == "needs_confirmation"
    assert ntut_degree_check("學士班", "大二")[0] == "pass"
    assert ntut_degree_check("學士班", "大三")[0] == "pass"
    assert ntut_degree_check("五專部", "專四")[0] == "needs_confirmation"
    assert ntut_degree_check("五專部", "專二")[0] == "needs_confirmation"
    assert ntut_degree_check("碩士班", "碩一")[0] == "needs_confirmation"
    assert ntut_degree_check("碩士班", "碩二")[0] == "pass"
    assert ntut_degree_check("博士班", "博二")[0] == "pass"
    assert ntut_degree_check("學士班", "延畢")[0] == "pass"
    assert ntut_degree_check(None, None)[0] == "needs_confirmation"

    assert ntut_academic_check("學士班", 80.0, 3.5, 25.0)[0] == "pass"
    assert ntut_academic_check("學士班", 70.0, None, None)[0] == "pass"
    assert ntut_academic_check("學士班", 68.0, 2.5, 60.0)[0] == "pass"
    assert ntut_academic_check("碩士班", 82.0, 3.6, 20.0)[0] == "pass"
    assert ntut_academic_check("學士班", None, None, None)[0] == "pass"


def test_ntut_language_checks() -> None:
    assert ntut_language_check(None, None, partner_country="中國大陸")[0] == "needs_confirmation"
    assert ntut_language_check("toefl", 79.0, partner_country="美國")[0] == "needs_confirmation"
    assert ntut_language_check("toefl", 60.0, partner_country="美國")[0] == "needs_confirmation"
    assert ntut_language_check("ielts", 5.5, partner_country="英國")[0] == "needs_confirmation"
    assert ntut_language_check("ielts", 5.0, partner_country="英國")[0] == "needs_confirmation"
    assert ntut_language_check("toeic", 700.0, partner_country="德國")[0] == "needs_confirmation"
    assert ntut_language_check("toeic", 650.0, partner_country="德國")[0] == "needs_confirmation"
    assert ntut_language_check("jlpt", 2.0, partner_country="日本")[0] == "needs_confirmation"
    assert ntut_language_check("jlpt", 3.0, partner_country="日本")[0] == "needs_confirmation"
    assert ntut_language_check("jlpt", 6.0, partner_country="日本")[0] == "needs_confirmation"
    assert ntut_language_check("topik", 3.0, partner_country="韓國")[0] == "needs_confirmation"


def test_ntut_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_ntut_partner_universities()
    assert len(partners) == 206
    assert sum(1 for p in partners if p.availability_status == "open") == 0
    assert sum(1 for p in partners if p.availability_status == "needs_confirmation") == 204
    assert sum(1 for p in partners if p.application_window_status == "open") == 0
    assert sum(1 for p in partners if p.application_window_status == "closed") == 2
    waseda = next(p for p in partners if "早稻田" in p.school_name)
    assert waseda.location.city == "北九州市（福岡縣）"
    assert waseda.location.geocode_status == "needs_review"
    assert all(p.location and p.location.geocode_status == "verified" for p in partners if p is not waseda)
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_ntut_student_dashboard()
    assert dashboard.school_name == NTUT.school_name
    assert len(dashboard.partner_universities) == 206
    assert len(dashboard.application_periods) == 3
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(ntut_exchange_info().scholarship_info) >= 2
    assert len(ntut_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NTUT.school_name
    ]
    assert len(workflows) == 206
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "needs_confirmation" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
        if d.home_university == NTUT.school_name
    ]
    assert len(destinations) == 206
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        if dest.school_name == '秋田大學 Akita University':
            assert est is not None and est.low == 80000
            assert est.applicability_status == 'reference_only'
            assert est.source_urls == (dest.cost_evidence.source_url,)
            assert budget_fit([est],1000000)['status'] == 'unknown'
        else:
            assert est is None, f"Unverified country estimate for {dest.school_name}"

    templates = all_application_templates("ntut")
    assert len(templates) == 6
    assert all("ntut.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads((BUNDLE / "import_provenance.json").read_text(encoding="utf-8"))
    assert len(provenance["sources"]) >= 8
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_ntut_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_ntut_partner_universities()
    sample = next(p for p in partners if "Michigan-Dearborn" in p.school_name)
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=NTUT.school_name,
            partner_university=sample.school_name,
            academic_year="116",
            application_round="116學年度第1、2學期（2027秋季班／2028春季班）赴外研修計畫甄選",
        ),
    )
    assert wf is not None
    assert len(wf.steps) == 5

    dest = next(
        d
        for d in destinations
        if d.school_name == sample.school_name and d.home_university == NTUT.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=NTUT.school_name,
            academic_year="116",
            application_round="116學年度第1、2學期（2027秋季班／2028春季班）赴外研修計畫甄選",
            degree_level="學士班",
            current_year="大二",
            college="電資學院",
            academic_score=85.0,
            academic_gpa=3.8,
            class_rank_percent=15.0,
            language_test="toefl",
            language_score=88,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=NTUT.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "needs_confirmation"
    assert checks["home_language_score"].status == "needs_confirmation"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=NTUT.school_name,
    )
    assert completeness.priority_gaps

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    ntut_entry = next(u for u in r_unis.json() if u["id"] == "ntut")
    assert ntut_entry["partner_count"] == 206
    assert len(ntut_entry["colleges"]) == 7

    r_cov = client.get("/coverage?school=ntut")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 206
    assert cov["workflow_school_count"] == 206
    assert cov["destination_profile_count"] == 206
    assert cov["image_count"] == 206
    assert cov["official_website_count"] == 206
    assert cov["experience_school_count"] >= 107
