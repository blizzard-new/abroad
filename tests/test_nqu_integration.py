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
from exchange_info.nqu_eligibility import (
    is_nqu,
    nqu_academic_check,
    nqu_degree_check,
    nqu_language_check,
)
from exchange_info.nqu_student_view import (
    build_nqu_student_dashboard,
    fetch_nqu_partner_universities,
    nqu_exchange_info,
    nqu_processed_pages,
)
from exchange_info.university_registry import NQU, require_university
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "nqu"


@pytest.mark.parametrize(
    "alias",
    [
        "nqu",
        "NQU",
        "金大",
        "金門大學",
        "國立金門大學",
        "國立金門技術學院",
        "National Quemoy University",
    ],
)
def test_nqu_aliases(alias: str) -> None:
    assert require_university(alias) == NQU
    assert is_nqu(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@nqu.edu.tw", True),
        ("s11123456@email.nqu.edu.tw", True),
        ("s11123456@student.nqu.edu.tw", True),
        ("s11123456@mail.nqu.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_nqu_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == NQU) is allowed


def test_nqu_degree_and_academic_checks() -> None:
    assert nqu_degree_check("學士班", "大一")[0] == "fail"
    assert nqu_degree_check("學士班", "大二")[0] == "pass"
    assert nqu_degree_check("學士班", "大三")[0] == "pass"
    assert nqu_degree_check("學士班", "大四")[0] == "pass"
    assert nqu_degree_check("碩士班", "碩一")[0] == "pass"
    assert nqu_degree_check("碩士班", "碩二")[0] == "pass"
    assert nqu_degree_check("博士班", "博二")[0] == "pass"
    assert nqu_degree_check("進修學士班", "大二")[0] == "fail"
    assert nqu_degree_check("在職專班", "碩一")[0] == "fail"
    assert nqu_degree_check("學分班", "選修生")[0] == "fail"
    assert nqu_degree_check("學士班", "休學")[0] == "fail"
    assert nqu_degree_check("學士班", "已畢業")[0] == "fail"
    assert nqu_degree_check(None, None)[0] == "needs_confirmation"

    assert nqu_academic_check("學士班", 82.0, 3.5, 18.0)[0] == "pass"
    assert nqu_academic_check("學士班", 73.0, 2.6, 52.0)[0] == "pass"
    assert nqu_academic_check("學士班", 66.0, 1.8, 75.0)[0] == "fail"
    assert nqu_academic_check("學士班", None, None, 45.0)[0] == "pass"
    assert nqu_academic_check("學士班", None, None, 75.0)[0] == "fail"
    assert nqu_academic_check("學士班", None, 3.2, None)[0] == "pass"
    assert nqu_academic_check("學士班", None, 1.8, None)[0] == "fail"
    assert nqu_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_nqu_language_checks() -> None:
    assert nqu_language_check(None, None, partner_country="中國大陸")[0] == "pass"
    assert nqu_language_check(None, None, partner_country="澳門")[0] == "pass"
    assert (
        nqu_language_check(None, None, partner_country="美國")[0]
        == "needs_confirmation"
    )
    assert nqu_language_check("toefl", 82.0, partner_country="美國")[0] == "pass"
    assert nqu_language_check("toefl", 65.0, partner_country="泰國")[0] == "pass"
    assert nqu_language_check("toefl", 45.0, partner_country="德國")[0] == "fail"
    assert nqu_language_check("ielts", 6.5, partner_country="馬來西亞")[0] == "pass"
    assert nqu_language_check("ielts", 5.5, partner_country="土耳其")[0] == "pass"
    assert nqu_language_check("ielts", 4.0, partner_country="德國")[0] == "fail"
    assert nqu_language_check("toeic", 785.0, partner_country="德國")[0] == "pass"
    assert nqu_language_check("toeic", 600.0, partner_country="越南")[0] == "pass"
    assert nqu_language_check("toeic", 450.0, partner_country="德國")[0] == "fail"
    assert nqu_language_check("jlpt", 1.0, partner_country="日本")[0] == "pass"
    assert nqu_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"
    assert nqu_language_check("jlpt", 3.0, partner_country="日本")[0] == "pass"
    assert nqu_language_check("jlpt", 4.0, partner_country="日本")[0] == "fail"
    assert nqu_language_check("topik", 4.0, partner_country="韓國")[0] == "pass"
    assert nqu_language_check("topik", 2.0, partner_country="韓國")[0] == "pass"
    assert nqu_language_check("topik", 1.0, partner_country="韓國")[0] == "fail"
    assert nqu_language_check("duolingo", 95.0, partner_country="美國")[0] == "pass"


def test_nqu_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_nqu_partner_universities()
    assert len(partners) == 64
    assert sum(1 for p in partners if p.availability_status == "open") == 48
    assert sum(1 for p in partners if p.availability_status == "reference_only") == 16
    assert all(
        p.location and p.location.geocode_status == "verified" for p in partners
    )
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_nqu_student_dashboard()
    assert dashboard.school_name == NQU.school_name
    assert len(dashboard.partner_universities) == 64
    assert dashboard.maximum_preferences == 5
    assert dashboard.academic_score_minimum == 70.0
    assert len(dashboard.application_periods) >= 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(nqu_exchange_info().scholarship_info) >= 1
    assert len(nqu_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NQU.school_name
    ]
    assert len(workflows) == 64
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "verified" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == NQU.school_name
    ]
    assert len(destinations) == 64
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert (
            est is not None
        ), f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("nqu")
    assert len(templates) == 6
    assert all("nqu.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads(
        (BUNDLE / "import_provenance.json").read_text(encoding="utf-8")
    )
    assert len(provenance["sources"]) >= 40
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_nqu_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_nqu_partner_universities()
    sample = next(
        p for p in partners if p.availability_status == "open" and p.country == "馬來西亞"
    )
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(
        tmp_path, include_bundled_baseline=True
    )
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=NQU.school_name,
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
        and d.home_university == NQU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=NQU.school_name,
            academic_year=sample.academic_year or "115",
            application_round=sample.application_round,
            degree_level="學士班",
            current_year="大三",
            college="管理學院",
            academic_score=84.0,
            academic_gpa=3.6,
            class_rank_percent=18.0,
            language_test="toeic",
            language_score=785,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=NQU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=NQU.school_name,
    )
    assert completeness.available_count >= 8

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    nqu_entry = next(u for u in r_unis.json() if u["id"] == "nqu")
    assert nqu_entry["partner_count"] == 64
    assert len(nqu_entry["colleges"]) == 4

    r_cov = client.get("/coverage?school=nqu")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 64
    assert cov["image_count"] == 64
    assert cov["official_website_count"] == 64
    assert cov["workflow_school_count"] == 64
    assert cov["destination_profile_count"] == 64
    assert cov["experience_school_count"] >= 30
    assert cov["experience_source_count"] >= 310
