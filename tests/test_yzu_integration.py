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
from exchange_info.university_registry import YZU, require_university
from exchange_info.yzu_eligibility import (
    is_yzu,
    yzu_academic_check,
    yzu_degree_check,
    yzu_language_check,
)
from exchange_info.yzu_student_view import (
    build_yzu_student_dashboard,
    fetch_yzu_partner_universities,
    yzu_exchange_info,
    yzu_processed_pages,
)

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "yzu"


@pytest.mark.parametrize(
    "alias",
    [
        "yzu",
        "YZU",
        "元智",
        "元智大學",
        "私立元智大學",
        "Yuan Ze University",
    ],
)
def test_yzu_aliases(alias: str) -> None:
    assert require_university(alias) == YZU
    assert is_yzu(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@yzu.edu.tw", True),
        ("s1110001@saturn.yzu.edu.tw", True),
        ("s1110001@mail.yzu.edu.tw", True),
        ("student@cycu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_yzu_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == YZU) is allowed


def test_yzu_degree_and_academic_checks() -> None:
    assert yzu_degree_check("學士班", "大二")[0] == "pass"
    assert yzu_degree_check("碩士班", "碩一")[0] == "pass"
    assert yzu_degree_check("博士班", "博一")[0] == "pass"
    assert yzu_degree_check("學士班", "大一")[0] == "fail"
    assert yzu_degree_check("在職專班", "碩一")[0] == "fail"
    assert yzu_degree_check("EMBA碩士在職專班", None)[0] == "fail"
    assert yzu_degree_check(None, None)[0] == "needs_confirmation"

    assert yzu_academic_check("學士班", 80.0, 3.5, 25.0)[0] == "pass"
    assert yzu_academic_check("學士班", 58.0, 1.9, 50.0)[0] == "fail"
    assert yzu_academic_check("碩士班", 68.0, 2.5, 30.0)[0] == "fail"
    assert yzu_academic_check("碩士班", 75.0, 3.2, 30.0)[0] == "pass"
    assert yzu_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_yzu_language_checks() -> None:
    assert yzu_language_check(None, None, partner_country="中國大陸")[0] == "pass"
    assert yzu_language_check("toefl", 79.0, partner_country="美國")[0] == "pass"
    assert yzu_language_check("toefl", 40.0, partner_country="美國")[0] == "fail"
    assert yzu_language_check("ielts", 6.0, partner_country="英國")[0] == "pass"
    assert yzu_language_check("toeic", 650.0, partner_country="德國")[0] == "pass"
    assert yzu_language_check("toeic", 500.0, partner_country="德國")[0] == "fail"
    assert yzu_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"
    assert yzu_language_check("jlpt", 3.0, partner_country="日本")[0] == "pass"
    assert yzu_language_check("jlpt", 4.0, partner_country="日本")[0] == "fail"
    assert yzu_language_check("topik", 3.0, partner_country="韓國")[0] == "pass"


def test_yzu_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_yzu_partner_universities()
    assert len(partners) == 90
    assert sum(1 for p in partners if p.availability_status == "open") == 80
    assert sum(1 for p in partners if p.availability_status == "reference_only") == 10
    assert sum(1 for p in partners if p.application_window_status == "open") == 7
    assert sum(1 for p in partners if p.application_window_status == "closed") == 83
    assert all(p.location and p.location.geocode_status == "verified" for p in partners)
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_yzu_student_dashboard()
    assert dashboard.school_name == YZU.school_name
    assert len(dashboard.partner_universities) == 90
    assert len(dashboard.application_periods) == 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(yzu_exchange_info().scholarship_info) >= 3
    assert len(yzu_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == YZU.school_name
    ]
    assert len(workflows) == 90
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "verified" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
        if d.home_university == YZU.school_name
    ]
    assert len(destinations) == 90
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert est is not None, f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("yzu")
    assert len(templates) == 6
    assert all("yzu.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads((BUNDLE / "import_provenance.json").read_text(encoding="utf-8"))
    assert len(provenance["sources"]) >= 8
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_yzu_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_yzu_partner_universities()
    sample = next(p for p in partners if p.availability_status == "open")
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=YZU.school_name,
            partner_university=sample.school_name,
            academic_year="115",
            application_round="115-2",
        ),
    )
    assert wf is not None
    assert len(wf.steps) == 5

    dest = next(
        d
        for d in destinations
        if d.school_name == sample.school_name and d.home_university == YZU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=YZU.school_name,
            academic_year="115",
            application_round="115-2",
            degree_level="學士班",
            current_year="大二",
            college="管理學院",
            academic_score=85.0,
            academic_gpa=3.8,
            class_rank_percent=15.0,
            language_test="toefl",
            language_score=88,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=YZU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=YZU.school_name,
    )
    assert completeness.available_count >= 8

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    yzu_entry = next(u for u in r_unis.json() if u["id"] == "yzu")
    assert yzu_entry["partner_count"] == 90
    assert len(yzu_entry["colleges"]) == 6

    r_cov = client.get("/coverage?school=yzu")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 90
    assert cov["workflow_school_count"] == 90
    assert cov["destination_profile_count"] == 90
    assert cov["image_count"] == 90
    assert cov["official_website_count"] == 90
    assert cov["experience_school_count"] >= 39
