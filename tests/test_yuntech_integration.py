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
from exchange_info.university_registry import YUNTECH, require_university
from exchange_info.yuntech_eligibility import (
    is_yuntech,
    yuntech_academic_check,
    yuntech_degree_check,
    yuntech_language_check,
)
from exchange_info.yuntech_student_view import (
    build_yuntech_student_dashboard,
    fetch_yuntech_partner_universities,
    yuntech_exchange_info,
    yuntech_processed_pages,
)
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "yuntech"


@pytest.mark.parametrize(
    "alias",
    [
        "yuntech",
        "YunTech",
        "YUNTECH",
        "nyust",
        "NYUST",
        "雲科大",
        "雲林科技大學",
        "國立雲林科技大學",
        "National Yunlin University of Science and Technology",
    ],
)
def test_yuntech_aliases(alias: str) -> None:
    assert require_university(alias) == YUNTECH
    assert is_yuntech(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@yuntech.edu.tw", True),
        ("B11200001@gemail.yuntech.edu.tw", True),
        ("M11300001@live.yuntech.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_yuntech_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == YUNTECH) is allowed


def test_yuntech_degree_and_academic_checks() -> None:
    assert yuntech_degree_check("學士班", "大一上")[0] == "fail"
    assert yuntech_degree_check("學士班", "大一下")[0] == "pass"
    assert yuntech_degree_check("學士班", "大二")[0] == "pass"
    assert yuntech_degree_check("學士班", "大三")[0] == "pass"
    assert yuntech_degree_check("碩士班", "碩一")[0] == "pass"
    assert yuntech_degree_check("博士班", "博一")[0] == "pass"
    assert yuntech_degree_check("在職專班", "碩二")[0] == "pass"
    assert yuntech_degree_check("學士班", "延畢")[0] == "needs_confirmation"
    assert yuntech_degree_check(None, None)[0] == "needs_confirmation"

    assert yuntech_academic_check("學士班", 80.0, 3.5, 20.0)[0] == "needs_confirmation"
    assert yuntech_academic_check("學士班", 75.0, None, None)[0] == "needs_confirmation"
    assert yuntech_academic_check("學士班", 72.0, None, 45.0)[0] == "needs_confirmation"
    assert yuntech_academic_check("學士班", None, None, 50.0)[0] == "needs_confirmation"
    assert yuntech_academic_check("學士班", 72.0, None, None)[0] == "needs_confirmation"
    assert yuntech_academic_check("學士班", 65.0, None, 65.0)[0] == "needs_confirmation"
    assert yuntech_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_yuntech_language_checks() -> None:
    assert yuntech_language_check(None, None, partner_country="中國大陸")[0] == "needs_confirmation"
    assert (
        yuntech_language_check(None, None, partner_country="越南")[0]
        == "needs_confirmation"
    )
    assert (
        yuntech_language_check(None, None, partner_country="美國")[0]
        == "needs_confirmation"
    )
    assert yuntech_language_check("toefl", 79.0, partner_country="美國")[0] == "needs_confirmation"
    assert yuntech_language_check("toefl", 35.0, partner_country="美國")[0] == "needs_confirmation"
    assert yuntech_language_check("ielts", 6.0, partner_country="英國")[0] == "needs_confirmation"
    assert yuntech_language_check("ielts", 3.5, partner_country="英國")[0] == "needs_confirmation"
    assert yuntech_language_check("toeic", 785.0, partner_country="美國")[0] == "needs_confirmation"
    assert yuntech_language_check("toeic", 650.0, partner_country="德國")[0] == "needs_confirmation"
    assert (
        yuntech_language_check("toeic", 580.0, partner_country="美國")[0]
        == "needs_confirmation"
    )
    assert yuntech_language_check("toeic", 580.0, partner_country="印尼")[0] == "needs_confirmation"
    assert yuntech_language_check("toeic", 450.0, partner_country="美國")[0] == "needs_confirmation"
    assert yuntech_language_check("jlpt", 2.0, partner_country="日本")[0] == "needs_confirmation"
    assert yuntech_language_check("jlpt", 6.0, partner_country="日本")[0] == "needs_confirmation"
    assert yuntech_language_check("topik", 3.0, partner_country="韓國")[0] == "needs_confirmation"


def test_yuntech_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_yuntech_partner_universities()
    assert len(partners) == 112
    assert sum(1 for p in partners if p.availability_status == "open") == 0
    assert (
        sum(1 for p in partners if p.availability_status == "reference_only")
        == 108
    )
    assert sum(1 for p in partners if p.application_window_status == "closed") == 108
    assert all(
        p.location and p.location.geocode_status == "verified" for p in partners
    )
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_yuntech_student_dashboard()
    assert dashboard.school_name == YUNTECH.school_name
    assert len(dashboard.partner_universities) == 112
    assert len(dashboard.application_periods) >= 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(yuntech_exchange_info().scholarship_info) >= 4
    assert len(yuntech_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == YUNTECH.school_name
    ]
    assert len(workflows) == 112
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "needs_confirmation" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == YUNTECH.school_name
    ]
    assert len(destinations) == 112
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert est is None, f"Unverified default cost remained for {dest.school_name}"

    templates = all_application_templates("yuntech")
    assert len(templates) == 6
    assert all("yuntech.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads(
        (BUNDLE / "import_provenance.json").read_text(encoding="utf-8")
    )
    assert len(provenance["sources"]) >= 25
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_yuntech_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_yuntech_partner_universities()
    sample = next(p for p in partners if p.availability_status == "reference_only" and p.country == "德國")
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(
        tmp_path, include_bundled_baseline=True
    )
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=YUNTECH.school_name,
            partner_university=sample.school_name,
            academic_year="115",
            application_round=sample.application_round,
        ),
    )
    assert wf is not None
    assert len(wf.steps) == 5

    dest = next(
        d
        for d in destinations
        if d.school_name == sample.school_name
        and d.home_university == YUNTECH.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=YUNTECH.school_name,
            academic_year="115",
            application_round=sample.application_round,
            degree_level="學士班",
            current_year="大二",
            college="工程學院",
            academic_score=82.0,
            academic_gpa=3.6,
            class_rank_percent=18.0,
            language_test="toeic",
            language_score=800,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=YUNTECH.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "needs_confirmation"
    assert checks["home_language_score"].status == "needs_confirmation"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=YUNTECH.school_name,
    )
    assert "每月生活費" in completeness.priority_gaps
    assert "申請流程" in completeness.priority_gaps

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    yuntech_entry = next(u for u in r_unis.json() if u["id"] == "yuntech")
    assert yuntech_entry["partner_count"] == 112
    assert len(yuntech_entry["colleges"]) == 5

    r_cov = client.get("/coverage?school=yuntech")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 112
    assert cov["workflow_school_count"] == 112
    assert cov["destination_profile_count"] == 112
    assert cov["image_count"] == 112
    assert cov["official_website_count"] == 112
    assert cov["experience_school_count"] >= 29
