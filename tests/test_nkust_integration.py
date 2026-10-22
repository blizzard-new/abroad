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
from exchange_info.nkust_eligibility import (
    is_nkust,
    nkust_academic_check,
    nkust_degree_check,
    nkust_language_check,
)
from exchange_info.nkust_student_view import (
    build_nkust_student_dashboard,
    fetch_nkust_partner_universities,
    nkust_exchange_info,
    nkust_processed_pages,
)
from exchange_info.school_completeness import build_school_completeness
from exchange_info.university_registry import NKUST, require_university
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "nkust"


@pytest.mark.parametrize(
    "alias",
    [
        "nkust",
        "NKUST",
        "高科大",
        "高雄科技大學",
        "國立高雄科技大學",
        "National Kaohsiung University of Science and Technology",
    ],
)
def test_nkust_aliases(alias: str) -> None:
    assert require_university(alias) == NKUST
    assert is_nkust(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@nkust.edu.tw", True),
        ("C111001@gm.nkust.edu.tw", True),
        ("C111001@std.nkust.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_nkust_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == NKUST) is allowed


def test_nkust_degree_and_academic_checks() -> None:
    assert nkust_degree_check("學士班", "大一")[0] == "needs_confirmation"
    assert nkust_degree_check("學士班", "大二")[0] == "needs_confirmation"
    assert nkust_degree_check("學士班", "大三")[0] == "needs_confirmation"
    assert nkust_degree_check("二技", "三年級")[0] == "needs_confirmation"
    assert nkust_degree_check("五專", "專二")[0] == "fail"
    assert nkust_degree_check("五專", "專四")[0] == "needs_confirmation"
    assert nkust_degree_check("碩士班", "碩一")[0] == "needs_confirmation"
    assert nkust_degree_check("博士班", "博一")[0] == "needs_confirmation"
    assert nkust_degree_check("在職專班", "碩二")[0] == "needs_confirmation"
    assert nkust_degree_check("學士班", "延畢")[0] == "needs_confirmation"
    assert nkust_degree_check(None, None)[0] == "needs_confirmation"

    assert nkust_academic_check("學士班", 80.0, 3.5, 20.0)[0] == "needs_confirmation"
    assert nkust_academic_check("學士班", 75.0, None, None)[0] == "needs_confirmation"
    assert nkust_academic_check("學士班", None, 3.1, None)[0] == "needs_confirmation"
    assert nkust_academic_check("學士班", None, None, 25.0)[0] == "needs_confirmation"
    assert nkust_academic_check("學士班", 68.0, None, None)[0] == "needs_confirmation"
    assert nkust_academic_check("學士班", 55.0, None, None)[0] == "needs_confirmation"
    assert nkust_academic_check("學士班", None, 1.5, None)[0] == "needs_confirmation"
    assert nkust_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_nkust_language_checks() -> None:
    assert nkust_language_check(None, None, partner_country="中國大陸")[0] == "needs_confirmation"
    assert (
        nkust_language_check(None, None, partner_country="美國")[0]
        == "needs_confirmation"
    )
    assert nkust_language_check("toefl", 79.0, partner_country="美國")[0] == "needs_confirmation"
    assert nkust_language_check("toefl", 35.0, partner_country="美國")[0] == "needs_confirmation"
    assert nkust_language_check("ielts", 6.0, partner_country="英國")[0] == "needs_confirmation"
    assert nkust_language_check("ielts", 3.5, partner_country="英國")[0] == "needs_confirmation"
    assert nkust_language_check("toeic", 785.0, partner_country="美國")[0] == "needs_confirmation"
    assert nkust_language_check("toeic", 600.0, partner_country="德國")[0] == "needs_confirmation"
    assert nkust_language_check("toeic", 500.0, partner_country="美國")[0] == "needs_confirmation"
    assert nkust_language_check("jlpt", 2.0, partner_country="日本")[0] == "needs_confirmation"
    assert nkust_language_check("jlpt", 6.0, partner_country="日本")[0] == "needs_confirmation"
    assert nkust_language_check("topik", 3.0, partner_country="韓國")[0] == "needs_confirmation"


def test_nkust_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_nkust_partner_universities()
    assert len(partners) == 107
    assert sum(1 for p in partners if p.availability_status == "open") == 0
    assert (
        sum(1 for p in partners if p.availability_status == "reference_only")
        == 97
    )
    assert all(p.application_window_status in {"closed", "needs_confirmation"} for p in partners)
    assert all(
        p.location and p.location.geocode_status == "verified" for p in partners
    )
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_nkust_student_dashboard()
    assert dashboard.school_name == NKUST.school_name
    assert len(dashboard.partner_universities) == 107
    assert len(dashboard.application_periods) >= 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(nkust_exchange_info().scholarship_info) >= 4
    assert len(nkust_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NKUST.school_name
    ]
    assert len(workflows) == 107
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "needs_confirmation" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == NKUST.school_name
    ]
    assert len(destinations) == 107
    for dest in destinations:
        assert "逐校生活費尚待查證" in dest.cost_summary
        assert dest.coverage_status == "official_partial"

    templates = all_application_templates("nkust")
    assert len(templates) == 6
    assert all("nkust.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads(
        (BUNDLE / "import_provenance.json").read_text(encoding="utf-8")
    )
    assert len(provenance["sources"]) >= 20
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_nkust_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_nkust_partner_universities()
    sample = next(p for p in partners if p.availability_status == "reference_only" and p.country == "德國")
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(
        tmp_path, include_bundled_baseline=True
    )
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=NKUST.school_name,
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
        and d.home_university == NKUST.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=NKUST.school_name,
            academic_year="115",
            application_round=sample.application_round,
            degree_level="學士班",
            current_year="大二",
            college="管理學院",
            academic_score=80.0,
            academic_gpa=3.5,
            class_rank_percent=20.0,
            language_test="toeic",
            language_score=800,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=NKUST.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "needs_confirmation"
    assert checks["home_language_score"].status == "needs_confirmation"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=NKUST.school_name,
    )
    assert completeness.available_count >= 1
    assert wf.applicability_status == "needs_confirmation"

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    nkust_entry = next(u for u in r_unis.json() if u["id"] == "nkust")
    assert nkust_entry["partner_count"] == 107
    assert len(nkust_entry["colleges"]) == 12

    r_cov = client.get("/coverage?school=nkust")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 107
    assert cov["workflow_school_count"] == 107
    assert cov["destination_profile_count"] == 107
    assert cov["image_count"] == 107
    assert cov["official_website_count"] == 107
    assert cov["experience_school_count"] >= 15
