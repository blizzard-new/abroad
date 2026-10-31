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
from exchange_info.models import ApplicationRuleContext, PersonalApplicationPlanRequest
from exchange_info.school_completeness import build_school_completeness
from exchange_info.ncyu_eligibility import (
    is_ncyu,
    ncyu_academic_check,
    ncyu_degree_check,
    ncyu_language_check,
)
from exchange_info.ncyu_student_view import (
    build_ncyu_student_dashboard,
    fetch_ncyu_partner_universities,
    ncyu_exchange_info,
    ncyu_processed_pages,
)
from exchange_info.university_registry import NCYU, require_university
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ncyu"


@pytest.mark.parametrize(
    "alias",
    [
        "ncyu",
        "NCYU",
        "嘉大",
        "嘉義大學",
        "國立嘉義大學",
        "National Chiayi University",
    ],
)
def test_ncyu_aliases(alias: str) -> None:
    assert require_university(alias) == NCYU
    assert is_ncyu(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@ncyu.edu.tw", True),
        ("s1123456@mail.ncyu.edu.tw", True),
        ("s1123456@g.ncyu.edu.tw", True),
        ("student@ccu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_ncyu_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == NCYU) is allowed


def test_ncyu_degree_and_academic_checks() -> None:
    assert ncyu_degree_check("學士班", "大一上")[0] == "fail"
    assert ncyu_degree_check("學士班", "大一下")[0] == "fail"
    assert ncyu_degree_check("學士班", "大二")[0] == "pass"
    assert ncyu_degree_check("學士班", "大三")[0] == "pass"
    assert ncyu_degree_check("碩士班", "碩一")[0] == "pass"
    assert ncyu_degree_check("碩士班", "碩二")[0] == "pass"
    assert ncyu_degree_check("博士班", "博一")[0] == "pass"
    assert ncyu_degree_check("在職專班", "碩一")[0] == "pass"
    assert ncyu_degree_check("學分班", "選修生")[0] == "fail"
    assert ncyu_degree_check("學士班", "休學")[0] == "fail"
    assert ncyu_degree_check("學士班", "已畢業")[0] == "fail"
    assert ncyu_degree_check(None, None)[0] == "needs_confirmation"

    assert ncyu_academic_check("學士班", 82.0, 3.6, 15.0)[0] == "pass"
    assert ncyu_academic_check("學士班", 76.0, 3.1, 45.0)[0] == "pass"
    assert ncyu_academic_check("學士班", 65.0, 2.1, 75.0)[0] == "fail"
    assert ncyu_academic_check("學士班", None, None, 20.0)[0] == "pass"
    assert ncyu_academic_check("學士班", None, None, 48.0)[0] == "fail"
    assert ncyu_academic_check("學士班", None, 3.2, None)[0] == "pass"
    assert ncyu_academic_check("學士班", None, 2.1, None)[0] == "fail"
    assert ncyu_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_ncyu_language_checks() -> None:
    assert ncyu_language_check(None, None, partner_country="中國大陸")[0] == "pass"
    assert (
        ncyu_language_check(None, None, partner_country="美國")[0]
        == "needs_confirmation"
    )
    assert ncyu_language_check("toefl", 85.0, partner_country="美國")[0] == "pass"
    assert ncyu_language_check("toefl", 75.0, partner_country="德國")[0] == "pass"
    assert ncyu_language_check("toefl", 50.0, partner_country="泰國")[0] == "pass"
    assert ncyu_language_check("toefl", 40.0, partner_country="德國")[0] == "fail"
    assert ncyu_language_check("ielts", 6.5, partner_country="英國")[0] == "pass"
    assert ncyu_language_check("ielts", 5.5, partner_country="波蘭")[0] == "pass"
    assert ncyu_language_check("ielts", 5.0, partner_country="印尼")[0] == "pass"
    assert ncyu_language_check("ielts", 4.5, partner_country="英國")[0] == "fail"
    assert ncyu_language_check("toeic", 785.0, partner_country="德國")[0] == "pass"
    assert ncyu_language_check("toeic", 600.0, partner_country="泰國")[0] == "pass"
    assert ncyu_language_check("toeic", 500.0, partner_country="德國")[0] == "fail"
    assert ncyu_language_check("jlpt", 1.0, partner_country="日本")[0] == "pass"
    assert ncyu_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"
    assert ncyu_language_check("jlpt", 3.0, partner_country="日本")[0] == "pass"
    assert ncyu_language_check("jlpt", 4.0, partner_country="日本")[0] == "fail"
    assert ncyu_language_check("jlpt", 5.0, partner_country="日本")[0] == "fail"
    assert ncyu_language_check("topik", 5.0, partner_country="韓國")[0] == "pass"
    assert ncyu_language_check("topik", 4.0, partner_country="韓國")[0] == "pass"
    assert ncyu_language_check("topik", 3.0, partner_country="韓國")[0] == "pass"
    assert ncyu_language_check("topik", 2.0, partner_country="韓國")[0] == "fail"
    assert ncyu_language_check("dele", 2.0, partner_country="西班牙")[0] == "pass"
    assert ncyu_language_check("delf", 2.0, partner_country="法國")[0] == "pass"
    assert ncyu_language_check("goethe", 2.0, partner_country="德國")[0] == "pass"


def test_ncyu_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_ncyu_partner_universities()
    assert len(partners) == 140
    assert sum(1 for p in partners if p.availability_status == "open") == 48
    assert sum(1 for p in partners if p.availability_status == "reference_only") == 92
    assert all(
        p.location and p.location.geocode_status == "verified" for p in partners
    )
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_ncyu_student_dashboard()
    assert dashboard.school_name == NCYU.school_name
    assert len(dashboard.partner_universities) == 140
    assert len(dashboard.application_periods) >= 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(ncyu_exchange_info().scholarship_info) >= 1
    assert len(ncyu_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NCYU.school_name
    ]
    assert len(workflows) == 140
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "verified" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == NCYU.school_name
    ]
    assert len(destinations) == 140
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert (
            est is not None
        ), f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("ncyu")
    assert len(templates) == 6
    assert all("ncyu.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads(
        (BUNDLE / "import_provenance.json").read_text(encoding="utf-8")
    )
    assert len(provenance["sources"]) >= 25
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_ncyu_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_ncyu_partner_universities()
    sample = next(
        p for p in partners if p.availability_status == "open" and p.country == "日本"
    )
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(
        tmp_path, include_bundled_baseline=True
    )
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=NCYU.school_name,
            partner_university=sample.school_name,
            academic_year=sample.academic_year or "115-1",
            application_round=sample.application_round,
        ),
    )
    assert wf is not None
    assert len(wf.steps) == 5

    dest = next(
        d
        for d in destinations
        if d.school_name == sample.school_name
        and d.home_university == NCYU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=NCYU.school_name,
            academic_year=sample.academic_year or "115-1",
            application_round=sample.application_round,
            degree_level="學士班",
            current_year="大三",
            college="農學院",
            academic_score=85.0,
            academic_gpa=3.7,
            class_rank_percent=12.0,
            language_test="toefl",
            language_score=96,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=NCYU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=NCYU.school_name,
    )
    assert completeness.available_count >= 8

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    ncyu_entry = next(u for u in r_unis.json() if u["id"] == "ncyu")
    assert ncyu_entry["partner_count"] == 140
    assert len(ncyu_entry["colleges"]) == 7

    r_cov = client.get("/coverage?school=ncyu")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 140
    assert cov["image_count"] == 140
    assert cov["official_website_count"] == 140
    assert cov["workflow_school_count"] == 140
    assert cov["destination_profile_count"] == 140
    assert cov["experience_school_count"] >= 20
    assert cov["experience_source_count"] >= 95
