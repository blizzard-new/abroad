from __future__ import annotations

import hashlib
import json
from pathlib import Path
from exchange_info import storage
from exchange_info.access_control import school_from_email
from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates
from exchange_info.application_rules import (
    build_personal_application_plan,
    select_application_workflow,
)
from exchange_info.cost_estimates import extract_monthly_estimates, primary_estimate
from exchange_info.cmu_eligibility import (
    cmu_academic_check,
    cmu_degree_check,
    cmu_language_check,
    is_cmu,
)
from exchange_info.cmu_student_view import (
    build_cmu_student_dashboard,
    cmu_exchange_info,
    cmu_processed_pages,
    fetch_cmu_partner_universities,
)
from exchange_info.models import ApplicationRuleContext, PersonalApplicationPlanRequest
from exchange_info.school_completeness import build_school_completeness
from exchange_info.university_registry import CMU, require_university
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "cmu"


@pytest.mark.parametrize(
    "alias",
    [
        "cmu",
        "CMU",
        "中國醫",
        "中醫大",
        "中國醫大",
        "中國醫藥大學",
        "China Medical University",
    ],
)
def test_cmu_aliases(alias: str) -> None:
    assert require_university(alias) == CMU
    assert is_cmu(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@cmu.edu.tw", True),
        ("s123456@mail.cmu.edu.tw", True),
        ("s123456@u.cmu.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_cmu_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == CMU) is allowed


def test_cmu_degree_and_academic_checks() -> None:
    assert cmu_degree_check("學士班", "大一上")[0] == "fail"
    assert cmu_degree_check("學士班", "大一下")[0] == "fail"
    assert cmu_degree_check("學士班", "大二")[0] == "pass"
    assert cmu_degree_check("學士班", "大五")[0] == "pass"
    assert cmu_degree_check("碩士班", "碩一")[0] == "pass"
    assert cmu_degree_check("博士班", "博一")[0] == "pass"
    assert cmu_degree_check("在職專班", "碩二")[0] == "fail"
    assert cmu_degree_check("學分班", "一")[0] == "fail"
    assert cmu_degree_check("學士班", "休學")[0] == "fail"
    assert cmu_degree_check(None, None)[0] == "needs_confirmation"

    assert cmu_academic_check("學士班", 82.0, 3.6, 15.0)[0] == "pass"
    assert cmu_academic_check("學士班", 80.0, 3.0, 20.0)[0] == "pass"
    assert cmu_academic_check("學士班", 76.0, 2.8, 25.0)[0] == "pass"
    assert cmu_academic_check("學士班", 76.0, 2.8, 35.0)[0] == "needs_confirmation"
    assert cmu_academic_check("學士班", 65.0, None, None)[0] == "needs_confirmation"
    assert cmu_academic_check("學士班", 55.0, None, None)[0] == "fail"
    assert cmu_academic_check("碩士班", 82.0, 3.6, None)[0] == "pass"
    assert cmu_academic_check("碩士班", 65.0, None, None)[0] == "fail"
    assert cmu_academic_check("學士班", None, 3.2, 25.0)[0] == "pass"
    assert cmu_academic_check("學士班", None, 2.6, None)[0] == "needs_confirmation"
    assert cmu_academic_check("學士班", None, 1.5, None)[0] == "fail"
    assert cmu_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_cmu_language_checks() -> None:
    assert cmu_language_check(None, None, partner_country="中國大陸")[0] == "pass"
    assert cmu_language_check(None, None, partner_country="澳門")[0] == "pass"
    assert (
        cmu_language_check(None, None, partner_country="香港")[0]
        == "needs_confirmation"
    )
    assert (
        cmu_language_check(None, None, partner_country="美國")[0]
        == "needs_confirmation"
    )
    assert cmu_language_check("toefl", 92.0, partner_country="美國")[0] == "pass"
    assert cmu_language_check("toefl", 80.0, partner_country="美國")[0] == "pass"
    assert cmu_language_check("toefl", 72.0, partner_country="德國")[0] == "pass"
    assert cmu_language_check("toefl", 60.0, partner_country="日本")[0] == "pass"
    assert cmu_language_check("toefl", 50.0, partner_country="美國")[0] == "fail"
    assert cmu_language_check("ielts", 6.5, partner_country="美國")[0] == "pass"
    assert cmu_language_check("ielts", 6.0, partner_country="英國")[0] == "pass"
    assert cmu_language_check("ielts", 5.5, partner_country="日本")[0] == "pass"
    assert cmu_language_check("ielts", 4.0, partner_country="日本")[0] == "pass"
    assert cmu_language_check("ielts", 3.5, partner_country="英國")[0] == "fail"
    assert cmu_language_check("toeic", 800.0, partner_country="美國")[0] == "pass"
    assert cmu_language_check("toeic", 600.0, partner_country="日本")[0] == "pass"
    assert cmu_language_check("toeic", 500.0, partner_country="美國")[0] == "fail"
    assert cmu_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"
    assert cmu_language_check("jlpt", 3.0, partner_country="日本")[0] == "pass"
    assert cmu_language_check("jlpt", 5.0, partner_country="日本")[0] == "fail"
    assert cmu_language_check("topik", 3.0, partner_country="韓國")[0] == "pass"
    assert cmu_language_check("topik", 1.0, partner_country="韓國")[0] == "fail"
    assert cmu_language_check("gept", 2.0, partner_country="美國")[0] == "pass"
    assert cmu_language_check("bestep", 2.0, partner_country="美國")[0] == "pass"
    assert cmu_language_check("duolingo", 105.0, partner_country="美國")[0] == "needs_confirmation"


def test_cmu_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_cmu_partner_universities()
    assert len(partners) == 174
    assert sum(1 for p in partners if p.availability_status == "open") == 38
    assert sum(1 for p in partners if p.availability_status == "reference_only") == 136
    assert sum(1 for p in partners if p.application_window_status == "open") == 38
    assert sum(1 for p in partners if p.application_window_status == "closed") == 136
    assert all(
        p.location and p.location.geocode_status == "verified" for p in partners
    )
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_cmu_student_dashboard()
    assert dashboard.school_name == CMU.school_name
    assert len(dashboard.partner_universities) == 174
    assert len(dashboard.application_periods) >= 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(cmu_exchange_info().scholarship_info) >= 3
    assert len(cmu_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == CMU.school_name
    ]
    assert len(workflows) == 174
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "verified" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == CMU.school_name
    ]
    assert len(destinations) == 174
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert (
            est is not None
        ), f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("cmu")
    assert len(templates) == 6
    assert all("cmu.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads(
        (BUNDLE / "import_provenance.json").read_text(encoding="utf-8")
    )
    assert len(provenance["sources"]) >= 7
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_cmu_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_cmu_partner_universities()
    sample = next(p for p in partners if p.availability_status == "open" and p.country == "日本")
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(
        tmp_path, include_bundled_baseline=True
    )
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=CMU.school_name,
            partner_university=sample.school_name,
            academic_year=sample.academic_year or "115",
            application_round=sample.application_round,
        ),
    )
    assert wf is not None
    assert len(wf.steps) == 5

    dest = next(
        d
        for d in destinations
        if d.school_name == sample.school_name
        and d.home_university == CMU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=CMU.school_name,
            academic_year=sample.academic_year or "115",
            application_round=sample.application_round,
            degree_level="學士班",
            current_year="大三",
            college="醫學院",
            academic_score=84.0,
            academic_gpa=3.7,
            class_rank_percent=15.0,
            language_test="toeic",
            language_score=850,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=CMU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=CMU.school_name,
    )
    assert completeness.available_count >= 8

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    cmu_entry = next(u for u in r_unis.json() if u["id"] == "cmu")
    assert cmu_entry["partner_count"] == 174
    assert len(cmu_entry["colleges"]) == 9

    r_cov = client.get("/coverage?school=cmu")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 174
    assert cov["image_count"] == 174
    assert cov["official_website_count"] == 174
    assert cov["workflow_school_count"] == 174
    assert cov["destination_profile_count"] == 174
    assert cov["experience_school_count"] >= 18
    assert cov["experience_source_count"] >= 18
