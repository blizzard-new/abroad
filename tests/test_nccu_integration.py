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
from exchange_info.university_registry import NCCU, require_university
from exchange_info.nccu_eligibility import (
    is_nccu,
    nccu_academic_check,
    nccu_degree_check,
    nccu_language_check,
)
from exchange_info.nccu_student_view import (
    build_nccu_student_dashboard,
    fetch_nccu_partner_universities,
    nccu_exchange_info,
    nccu_processed_pages,
)

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "nccu"


@pytest.mark.parametrize(
    "alias",
    [
        "nccu",
        "NCCU",
        "政大",
        "政治大學",
        "國立政治大學",
        "Chengchi University",
        "National Chengchi University",
    ],
)
def test_nccu_aliases(alias: str) -> None:
    assert require_university(alias) == NCCU
    assert is_nccu(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@nccu.edu.tw", True),
        ("112301001@g.nccu.edu.tw", True),
        ("112301001@mail2.nccu.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_nccu_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == NCCU) is allowed


def test_nccu_degree_and_academic_checks() -> None:
    assert nccu_degree_check("學士班", "大一")[0] == "needs_confirmation"
    assert nccu_degree_check("學士班", "大二")[0] == "pass"
    assert nccu_degree_check("學士班", "大三")[0] == "pass"
    assert nccu_degree_check("碩士班", "碩一")[0] == "needs_confirmation"
    assert nccu_degree_check("碩士班", "碩二")[0] == "pass"
    assert nccu_degree_check("博士班", "博二")[0] == "pass"
    assert nccu_degree_check("在職專班", "碩二")[0] == "fail"
    assert nccu_degree_check("學士班", "延畢")[0] == "pass"
    assert nccu_degree_check(None, None)[0] == "needs_confirmation"

    assert nccu_academic_check("學士班", 82.0, 3.6, 20.0)[0] == "pass"
    assert nccu_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_nccu_language_checks() -> None:
    assert nccu_language_check(None, None, partner_country="中國大陸")[0] == "pass"
    assert nccu_language_check("toefl", 79.0, partner_country="美國")[0] == "pass"
    assert nccu_language_check("toefl", 65.0, partner_country="美國")[0] == "fail"
    assert nccu_language_check("ielts", 6.0, partner_country="英國")[0] == "pass"
    assert nccu_language_check("ielts", 5.5, partner_country="英國")[0] == "fail"
    assert nccu_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"
    assert nccu_language_check("jlpt", 5.0, partner_country="日本")[0] == "pass"
    assert nccu_language_check("jlpt", 6.0, partner_country="日本")[0] == "fail"
    assert nccu_language_check("topik", 3.0, partner_country="韓國")[0] == "pass"


def test_nccu_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_nccu_partner_universities()
    assert len(partners) == 266
    assert sum(1 for p in partners if p.availability_status == "open") == 222
    assert sum(1 for p in partners if p.availability_status == "agreement_only") == 44
    assert sum(1 for p in partners if p.application_window_status == "open") == 222
    assert sum(1 for p in partners if p.application_window_status == "closed") == 44
    assert all(p.location and p.location.geocode_status == "verified" for p in partners)
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_nccu_student_dashboard()
    assert dashboard.school_name == NCCU.school_name
    assert len(dashboard.partner_universities) == 266
    assert len(dashboard.application_periods) == 3
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(nccu_exchange_info().scholarship_info) >= 5
    assert len(nccu_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NCCU.school_name
    ]
    assert len(workflows) == 266
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "verified" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
        if d.home_university == NCCU.school_name
    ]
    assert len(destinations) == 266
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert est is not None, f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("nccu")
    assert len(templates) == 6
    assert all("nccu.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads((BUNDLE / "import_provenance.json").read_text(encoding="utf-8"))
    assert len(provenance["sources"]) >= 12
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_nccu_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_nccu_partner_universities()
    sample = next(p for p in partners if p.availability_status == "open")
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=NCCU.school_name,
            partner_university=sample.school_name,
            academic_year="116",
            application_round=sample.application_round,
        ),
    )
    assert wf is not None
    assert len(wf.steps) == 5

    dest = next(
        d
        for d in destinations
        if d.school_name == sample.school_name and d.home_university == NCCU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=NCCU.school_name,
            academic_year="116",
            application_round=sample.application_round,
            degree_level="學士班",
            current_year="大二",
            college="商學院",
            academic_score=85.0,
            academic_gpa=3.8,
            class_rank_percent=15.0,
            language_test="toefl",
            language_score=92,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=NCCU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=NCCU.school_name,
    )
    assert completeness.available_count >= 8

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    nccu_entry = next(u for u in r_unis.json() if u["id"] == "nccu")
    assert nccu_entry["partner_count"] == 266
    assert len(nccu_entry["colleges"]) == 13

    r_cov = client.get("/coverage?school=nccu")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 266
    assert cov["workflow_school_count"] == 266
    assert cov["destination_profile_count"] == 266
    assert cov["image_count"] == 266
    assert cov["official_website_count"] == 266
    assert cov["experience_school_count"] >= 192
