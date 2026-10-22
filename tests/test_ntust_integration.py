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
from exchange_info.ntust_eligibility import (
    is_ntust,
    ntust_academic_check,
    ntust_degree_check,
    ntust_language_check,
)
from exchange_info.ntust_student_view import (
    build_ntust_student_dashboard,
    fetch_ntust_partner_universities,
    ntust_exchange_info,
    ntust_processed_pages,
)
from exchange_info.school_completeness import build_school_completeness
from exchange_info.university_registry import NTUST, require_university

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ntust"


@pytest.mark.parametrize(
    "alias",
    [
        "ntust",
        "NTUST",
        "臺科大",
        "台科大",
        "臺灣科技大學",
        "台灣科技大學",
        "國立臺灣科技大學",
        "國立台灣科技大學",
        "Taiwan Tech",
        "National Taiwan University of Science and Technology",
    ],
)
def test_ntust_aliases(alias: str) -> None:
    assert require_university(alias) == NTUST
    assert is_ntust(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@ntust.edu.tw", True),
        ("b11101001@mail.ntust.edu.tw", True),
        ("b11101001@gapps.ntust.edu.tw", True),
        ("student@cycu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_ntust_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == NTUST) is allowed


def test_ntust_degree_and_academic_checks() -> None:
    assert ntust_degree_check("學士班", "大二")[0] == "pass"
    assert ntust_degree_check("碩士班", "碩一")[0] == "needs_confirmation"
    assert ntust_degree_check("博士班", "博一")[0] == "needs_confirmation"
    assert ntust_degree_check("學士班", "大一")[0] == "needs_confirmation"
    assert ntust_degree_check("在職專班", "碩一")[0] == "fail"
    assert ntust_degree_check("EMBA碩士在職專班", None)[0] == "fail"
    assert ntust_degree_check(None, None)[0] == "needs_confirmation"

    assert ntust_academic_check("學士班", 80.0, 3.5, 25.0)[0] == "needs_confirmation"
    assert ntust_academic_check("學士班", 75.0, 3.0, 75.0)[0] == "needs_confirmation"
    assert ntust_academic_check("學士班", 58.0, 1.9, 50.0)[0] == "needs_confirmation"
    assert ntust_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_ntust_language_checks() -> None:
    assert ntust_language_check(None, None, partner_country="中國大陸")[0] == "needs_confirmation"
    assert ntust_language_check("toefl", 79.0, partner_country="美國")[0] == "pass"
    assert ntust_language_check("toefl", 50.0, partner_country="美國")[0] == "fail"
    assert ntust_language_check("ielts", 6.0, partner_country="英國")[0] == "pass"
    assert ntust_language_check("toeic", 750.0, partner_country="德國")[0] == "pass"
    assert ntust_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"
    assert ntust_language_check("jlpt", 3.0, partner_country="日本")[0] == "fail"
    assert ntust_language_check("topik", 3.0, partner_country="韓國")[0] == "pass"


def test_ntust_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_ntust_partner_universities()
    assert len(partners) == 237
    assert sum(1 for p in partners if p.availability_status == "open") == 0
    assert sum(1 for p in partners if p.availability_status == "reference_only") == 237
    assert sum(1 for p in partners if p.application_window_status == "closed") == 237
    assert all(p.location and p.location.geocode_status == "verified" for p in partners)
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_ntust_student_dashboard()
    assert dashboard.school_name == NTUST.school_name
    assert len(dashboard.partner_universities) == 237
    assert len(dashboard.application_periods) == 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(ntust_exchange_info().scholarship_info) >= 4
    assert len(ntust_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NTUST.school_name
    ]
    assert len(workflows) == 237
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "needs_confirmation" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
        if d.home_university == NTUST.school_name
    ]
    assert len(destinations) == 237
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert est is not None, f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("ntust")
    assert len(templates) == 6
    assert all("ntust.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads((BUNDLE / "import_provenance.json").read_text(encoding="utf-8"))
    assert len(provenance["sources"]) >= 8
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_ntust_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_ntust_partner_universities()
    sample = next(p for p in partners if p.country == "香港")
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=NTUST.school_name,
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
        if d.school_name == sample.school_name and d.home_university == NTUST.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=NTUST.school_name,
            academic_year="115",
            application_round="115-2",
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
        academic_score_minimum=NTUST.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "needs_confirmation"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=NTUST.school_name,
    )
    assert any(item.status == "needs_confirmation" for item in completeness.items)

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    ntust_entry = next(u for u in r_unis.json() if u["id"] == "ntust")
    assert ntust_entry["partner_count"] == 237
    assert len(ntust_entry["colleges"]) == 7

    r_cov = client.get("/coverage?school=ntust")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 237
    assert cov["workflow_school_count"] == 237
    assert cov["destination_profile_count"] == 237
    assert cov["image_count"] == 237
    assert cov["official_website_count"] == 237
    assert cov["experience_school_count"] >= 126
