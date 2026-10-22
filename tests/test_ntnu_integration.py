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
from exchange_info.ntnu_eligibility import (
    is_ntnu,
    ntnu_academic_check,
    ntnu_degree_check,
    ntnu_language_check,
)
from exchange_info.ntnu_student_view import (
    build_ntnu_student_dashboard,
    fetch_ntnu_partner_universities,
    ntnu_exchange_info,
    ntnu_processed_pages,
)
from exchange_info.school_completeness import build_school_completeness
from exchange_info.university_registry import NTNU, require_university

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ntnu"


@pytest.mark.parametrize(
    "alias",
    [
        "ntnu",
        "NTNU",
        "師大",
        "臺師大",
        "台師大",
        "臺灣師範大學",
        "台灣師範大學",
        "國立臺灣師範大學",
        "國立台灣師範大學",
        "National Taiwan Normal University",
    ],
)
def test_ntnu_aliases(alias: str) -> None:
    assert require_university(alias) == NTNU
    assert is_ntnu(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@ntnu.edu.tw", True),
        ("41123456@gapps.ntnu.edu.tw", True),
        ("41123456@std.ntnu.edu.tw", True),
        ("student@scu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_ntnu_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == NTNU) is allowed


def test_ntnu_degree_and_academic_checks() -> None:
    assert ntnu_degree_check("學士班", "大二")[0] == "pass"
    assert ntnu_degree_check("碩士班", "碩二")[0] == "pass"
    assert ntnu_degree_check("博士班", "博二")[0] == "pass"
    assert ntnu_degree_check("學士班", "大一上")[0] == "fail"
    assert ntnu_degree_check("在職專班", "碩一")[0] == "fail"
    assert ntnu_degree_check("進修推廣學院", None)[0] == "fail"
    assert ntnu_degree_check(None, None)[0] == "needs_confirmation"

    assert ntnu_academic_check("學士班", 82.0, 3.6, 15.0)[0] == "needs_confirmation"
    assert ntnu_academic_check("學士班", 55.0, 1.8, 90.0)[0] == "needs_confirmation"
    assert ntnu_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_ntnu_language_checks() -> None:
    assert ntnu_language_check(None, None, partner_country="中國大陸")[0] == "needs_confirmation"
    assert ntnu_language_check("toefl", 80.0, partner_country="美國")[0] == "needs_confirmation"
    assert ntnu_language_check("toefl", 50.0, partner_country="美國")[0] == "needs_confirmation"
    assert ntnu_language_check("ielts", 6.0, partner_country="英國")[0] == "needs_confirmation"
    assert ntnu_language_check("toeic", 785.0, partner_country="韓國")[0] == "needs_confirmation"
    assert ntnu_language_check("jlpt", 2.0, partner_country="日本")[0] == "needs_confirmation"
    assert ntnu_language_check("topik", 3.0, partner_country="韓國")[0] == "needs_confirmation"


def test_ntnu_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_ntnu_partner_universities()
    assert len(partners) == 236
    # A listed partner must not imply a confirmed current exchange quota.
    waseda = next(p for p in partners if "Waseda University" in p.school_name)
    assert waseda.quota_status == "not_published"
    assert waseda.availability_status == "needs_confirmation"
    assert "原合併數值來自 115-2／115-1" in waseda.language_requirement
    assert all(p.application_window_status in {"upcoming", "needs_confirmation", "open", "closed"} for p in partners)
    assert any(p.application_window_status == "needs_confirmation" for p in partners)
    assert all(p.location and p.location.geocode_status == "verified" for p in partners)
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_ntnu_student_dashboard()
    assert dashboard.school_name == NTNU.school_name
    assert dashboard.maximum_preferences == 10
    assert len(dashboard.partner_universities) == 236
    assert len(dashboard.application_periods) == 3
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(ntnu_exchange_info().scholarship_info) == 5
    assert len(ntnu_processed_pages()) == 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NTNU.school_name
    ]
    assert len(workflows) == 236
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "needs_confirmation" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
        if d.home_university == NTNU.school_name
    ]
    assert len(destinations) == 236
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert est is not None, f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("ntnu")
    assert len(templates) == 6
    assert all("ntnu.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads((BUNDLE / "import_provenance.json").read_text(encoding="utf-8"))
    assert len(provenance["sources"]) == 13
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_ntnu_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_ntnu_partner_universities()
    sample = next(p for p in partners if (p.degree_levels or "").startswith("【跨期資料待核對】"))
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=NTNU.school_name,
            partner_university=sample.school_name,
            academic_year="116",
            application_round="116-1",
        ),
    )
    assert wf is not None
    assert len(wf.steps) == 5

    dest = next(
        d
        for d in destinations
        if d.school_name == sample.school_name and d.home_university == NTNU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=NTNU.school_name,
            academic_year="116",
            application_round="116-1",
            degree_level="學士班",
            current_year="大二",
            college="文學院",
            academic_score=85.0,
            academic_gpa=3.8,
            class_rank_percent=12.0,
            language_test="toefl",
            language_score=90,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=NTNU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "needs_confirmation"
    assert checks["home_language_score"].status == "needs_confirmation"
    assert checks["degree_level"].status == "pass"
    assert checks["partner_degree_level"].status == "needs_confirmation"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=NTNU.school_name,
    )
    assert completeness.available_count >= 8

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    ntnu_entry = next(u for u in r_unis.json() if u["id"] == "ntnu")
    assert ntnu_entry["partner_count"] == 236
    assert len(ntnu_entry["colleges"]) == 10

    r_cov = client.get("/coverage?school=ntnu")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 236
    assert cov["workflow_school_count"] == 236
    assert cov["destination_profile_count"] == 236
    assert cov["image_count"] == 236
    assert cov["official_website_count"] == 236
    assert cov["experience_school_count"] >= 174
