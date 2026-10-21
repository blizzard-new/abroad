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
from exchange_info.ntub_eligibility import (
    is_ntub,
    ntub_academic_check,
    ntub_degree_check,
    ntub_language_check,
)
from exchange_info.ntub_student_view import (
    build_ntub_student_dashboard,
    fetch_ntub_partner_universities,
    ntub_exchange_info,
    ntub_processed_pages,
)
from exchange_info.models import ApplicationRuleContext, PersonalApplicationPlanRequest
from exchange_info.school_completeness import build_school_completeness
from exchange_info.university_registry import NTUB, require_university
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ntub"


@pytest.mark.parametrize(
    "alias",
    [
        "ntub",
        "NTUB",
        "北商",
        "北商大",
        "臺北商大",
        "台北商大",
        "國立臺北商業大學",
        "國立台北商業大學",
        "National Taipei University of Business",
    ],
)
def test_ntub_aliases(alias: str) -> None:
    assert require_university(alias) == NTUB
    assert is_ntub(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@ntub.edu.tw", True),
        ("s112456@mail.ntub.edu.tw", True),
        ("s112456@gm.ntub.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_ntub_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == NTUB) is allowed


def test_ntub_degree_and_academic_checks() -> None:
    assert ntub_degree_check("四技", "大一")[0] == "fail"
    assert ntub_degree_check("四技", "大二")[0] == "pass"
    assert ntub_degree_check("二技", "二技一上")[0] == "fail"
    assert ntub_degree_check("二技", "二技一下")[0] == "pass"
    assert ntub_degree_check("五專", "專三")[0] == "fail"
    assert ntub_degree_check("五專", "專四")[0] == "pass"
    assert ntub_degree_check("碩士班", "碩一上")[0] == "fail"
    assert ntub_degree_check("碩士班", "碩一下")[0] == "pass"
    assert ntub_degree_check("碩士班", "碩二")[0] == "pass"
    assert ntub_degree_check("學分班", "一")[0] == "fail"
    assert ntub_degree_check("四技", "休學")[0] == "fail"
    assert ntub_degree_check(None, None)[0] == "needs_confirmation"

    assert ntub_academic_check("四技", 82.0, 3.6, 15.0)[0] == "pass"
    assert ntub_academic_check("四技", 76.0, 3.1, 18.0)[0] == "pass"
    assert ntub_academic_check("四技", 75.0, 2.8, 80.0)[0] == "fail"
    assert ntub_academic_check("四技", None, None, 15.0)[0] == "pass"
    assert ntub_academic_check("四技", None, 3.5, None)[0] == "pass"
    assert ntub_academic_check("四技", None, 2.5, None)[0] == "fail"
    assert ntub_academic_check("四技", None, None, None)[0] == "needs_confirmation"


def test_ntub_language_checks() -> None:
    assert ntub_language_check(None, None, partner_country="中國大陸")[0] == "pass"
    assert (
        ntub_language_check(None, None, partner_country="德國")[0]
        == "needs_confirmation"
    )
    assert ntub_language_check("toefl", 85.0, partner_country="德國")[0] == "pass"
    assert ntub_language_check("toefl", 65.0, partner_country="德國")[0] == "pass"
    assert ntub_language_check("toefl", 55.0, partner_country="德國")[0] == "fail"
    assert ntub_language_check("ielts", 6.5, partner_country="英國")[0] == "pass"
    assert ntub_language_check("ielts", 5.5, partner_country="捷克")[0] == "pass"
    assert ntub_language_check("ielts", 4.5, partner_country="英國")[0] == "fail"
    assert ntub_language_check("toeic", 800.0, partner_country="中國大陸")[0] == "pass"
    assert ntub_language_check("toeic", 800.0, partner_country="德國")[0] == "fail"
    assert ntub_language_check("jlpt", 1.0, partner_country="日本")[0] == "pass"
    assert ntub_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"
    assert ntub_language_check("jlpt", 3.0, partner_country="日本")[0] == "fail"
    assert ntub_language_check("jlpt", 4.0, partner_country="日本")[0] == "fail"
    assert ntub_language_check("jlpt", 5.0, partner_country="日本")[0] == "fail"
    assert ntub_language_check("topik", 3.0, partner_country="韓國")[0] == "pass"
    assert ntub_language_check("topik", 2.0, partner_country="韓國")[0] == "fail"
    assert ntub_language_check("topik", 1.0, partner_country="韓國")[0] == "fail"
    assert ntub_language_check("duolingo", 105.0, partner_country="美國")[0] == "needs_confirmation"


def test_ntub_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_ntub_partner_universities()
    assert len(partners) == 93
    assert sum(1 for p in partners if p.availability_status == "open") == 51
    assert sum(1 for p in partners if p.availability_status == "reference_only") == 42
    assert sum(1 for p in partners if p.application_window_status == "open") == 51
    assert sum(1 for p in partners if p.application_window_status == "closed") == 42
    assert all(
        p.location and p.location.geocode_status == "verified" for p in partners
    )
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_ntub_student_dashboard()
    assert dashboard.school_name == NTUB.school_name
    assert len(dashboard.partner_universities) == 93
    assert len(dashboard.application_periods) >= 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(ntub_exchange_info().scholarship_info) >= 3
    assert len(ntub_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NTUB.school_name
    ]
    assert len(workflows) == 93
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "verified" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == NTUB.school_name
    ]
    assert len(destinations) == 93
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert (
            est is not None
        ), f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("ntub")
    assert len(templates) == 6
    assert all("ntub.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads(
        (BUNDLE / "import_provenance.json").read_text(encoding="utf-8")
    )
    assert len(provenance["sources"]) >= 10
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_ntub_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_ntub_partner_universities()
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
            home_university=NTUB.school_name,
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
        and d.home_university == NTUB.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=NTUB.school_name,
            academic_year=sample.academic_year or "115",
            application_round=sample.application_round,
            degree_level="四技",
            current_year="大三",
            college="財經學院",
            academic_score=84.0,
            academic_gpa=3.7,
            class_rank_percent=12.0,
            language_test="toefl",
            language_score=85,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=NTUB.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=NTUB.school_name,
    )
    assert completeness.available_count >= 8

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    ntub_entry = next(u for u in r_unis.json() if u["id"] == "ntub")
    assert ntub_entry["partner_count"] == 93
    assert len(ntub_entry["colleges"]) == 4

    r_cov = client.get("/coverage?school=ntub")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 93
    assert cov["image_count"] == 93
    assert cov["official_website_count"] == 93
    assert cov["workflow_school_count"] == 93
    assert cov["destination_profile_count"] == 93
    assert cov["experience_school_count"] >= 42
    assert cov["experience_source_count"] >= 295
