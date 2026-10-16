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
from exchange_info.cost_estimates import extract_monthly_estimates, primary_estimate
from exchange_info.models import ApplicationRuleContext, PersonalApplicationPlanRequest
from exchange_info.school_completeness import build_school_completeness
from exchange_info.scu_eligibility import (
    is_scu,
    scu_academic_check,
    scu_degree_check,
    scu_language_check,
    scu_undergraduate_weighted_academic_score,
)
from exchange_info.scu_student_view import (
    build_scu_student_dashboard,
    fetch_scu_partner_universities,
    scu_exchange_info,
    scu_processed_pages,
)
from exchange_info.university_registry import SCU, require_university

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "scu"


@pytest.mark.parametrize(
    "alias",
    [
        "scu",
        "SCU",
        "東吳",
        "東吳大學",
        "Soochow University",
        "Soochow University (Taiwan)",
    ],
)
def test_scu_aliases(alias: str) -> None:
    assert require_university(alias) == SCU
    assert is_scu(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@scu.edu.tw", True),
        ("11234567@gm.scu.edu.tw", True),
        ("alumni@alumni.scu.edu.tw", True),
        ("student@mail.scu.edu.tw", True),
        ("student@fju.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_scu_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == SCU) is allowed


def test_scu_degree_and_academic_checks() -> None:
    assert scu_degree_check("大學部", "大二")[0] == "pass"
    assert scu_degree_check("大學部", "延修第二年")[0] == "fail"
    assert scu_degree_check("碩士班", "碩一")[0] == "pass"
    assert scu_degree_check("博士班", "博一")[0] == "pass"
    assert scu_degree_check("進修學士班", "大二")[0] == "needs_confirmation"
    assert scu_degree_check("在職專班", None)[0] == "needs_confirmation"
    assert scu_degree_check(None, None)[0] == "needs_confirmation"

    # Undergraduate: class rank top 85% or average score >= 65
    assert scu_academic_check("大學部", 80.0, 3.5, 30.0)[0] == "pass"
    assert scu_academic_check("大學部", 62.0, 2.0, 90.0)[0] == "fail"
    assert scu_academic_check("大學部", 75.0, 3.2, None)[0] == "pass"
    assert scu_academic_check("大學部", None, None, None)[0] == "needs_confirmation"

    # Graduate: average >= 80
    assert scu_academic_check("碩士班", 84.0, 3.8, None)[0] == "pass"
    assert scu_academic_check("碩士班", 76.0, 3.1, None)[0] == "fail"

    # Undergraduate weighted score: gpa * 0.45 + (1 - pct/100)*100 * 0.55
    assert scu_undergraduate_weighted_academic_score(80.0, 20.0) == 80.0


def test_scu_language_checks() -> None:
    assert scu_language_check(None, None, partner_country="中國大陸")[0] == "pass"
    assert scu_language_check("toefl", 80.0, partner_country="美國")[0] == "pass"
    assert scu_language_check("toefl", 55.0, partner_country="美國")[0] == "fail"
    assert scu_language_check("ielts", 6.0, partner_country="英國")[0] == "pass"
    assert scu_language_check("toeic", 785.0, partner_country="韓國")[0] == "pass"
    assert scu_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"


def test_scu_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_scu_partner_universities()
    assert len(partners) == 191
    assert sum(1 for p in partners if p.country == "中國大陸") == 62
    assert sum(1 for p in partners if p.country != "中國大陸") == 129
    assert sum(1 for p in partners if "自費研修" in p.program_type) == 3
    assert all(p.quota_status == "published" for p in partners)
    assert all(p.availability_status == "open" for p in partners)
    assert all(p.application_window_status == "open" for p in partners)
    assert all(p.location and p.location.geocode_status == "verified" for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_scu_student_dashboard()
    assert dashboard.school_name == SCU.school_name
    assert len(dashboard.partner_universities) == 191
    assert len(dashboard.application_periods) == 3
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(scu_exchange_info().scholarship_info) == 5
    assert len(scu_processed_pages()) >= 3

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == SCU.school_name
    ]
    assert len(workflows) == 191
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "verified" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
        if d.home_university == SCU.school_name
    ]
    assert len(destinations) == 191
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert est is not None, f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("scu")
    assert len(templates) == 6
    assert all("scu.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads((BUNDLE / "import_provenance.json").read_text(encoding="utf-8"))
    assert len(provenance["sources"]) == 16
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_scu_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_scu_partner_universities()
    sample = partners[0]
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=SCU.school_name,
            partner_university=sample.school_name,
            academic_year="116",
            application_round="第1學期（秋季班）",
        ),
    )
    assert wf is not None
    assert len(wf.steps) == 5

    dest = next(
        d
        for d in destinations
        if d.school_name == sample.school_name and d.home_university == SCU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=SCU.school_name,
            academic_year="116",
            application_round="第1學期（秋季班）",
            degree_level="大學部",
            current_year="大二",
            college="外國語文學院",
            academic_score=84.0,
            academic_gpa=3.7,
            class_rank_percent=18.0,
            language_test="toefl",
            language_score=88,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=SCU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=SCU.school_name,
    )
    assert completeness.available_count >= 8

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    scu_entry = next(u for u in r_unis.json() if u["id"] == "scu")
    assert scu_entry["partner_count"] == 191
    assert len(scu_entry["colleges"]) == 6

    r_cov = client.get("/coverage?school=scu")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 191
    assert cov["workflow_school_count"] == 191
    assert cov["destination_profile_count"] == 191
    assert cov["image_count"] == 191
    assert cov["official_website_count"] == 191
