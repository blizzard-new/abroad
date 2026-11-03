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
from exchange_info.tpcu_eligibility import (
    is_tpcu,
    tpcu_academic_check,
    tpcu_degree_check,
    tpcu_language_check,
)
from exchange_info.tpcu_student_view import (
    build_tpcu_student_dashboard,
    fetch_tpcu_partner_universities,
    tpcu_exchange_info,
    tpcu_processed_pages,
)
from exchange_info.university_registry import TPCU, require_university
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "tpcu"


@pytest.mark.parametrize(
    "alias",
    [
        "tpcu",
        "TPCU",
        "城市科大",
        "北城科大",
        "臺北城市科大",
        "台北城市科大",
        "臺北城市科技大學",
        "台北城市科技大學",
        "光武工專",
        "北台科大",
        "Taipei City University of Science and Technology",
    ],
)
def test_tpcu_aliases(alias: str) -> None:
    assert require_university(alias) == TPCU
    assert is_tpcu(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@tpcu.edu.tw", True),
        ("b1123456@mail.tpcu.edu.tw", True),
        ("b1123456@gm.tpcu.edu.tw", True),
        ("b1123456@smail.tpcu.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_tpcu_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == TPCU) is allowed


def test_tpcu_degree_and_academic_checks() -> None:
    assert tpcu_degree_check("學士班", "大一")[0] == "fail"
    assert tpcu_degree_check("學士班", "大一上")[0] == "fail"
    assert tpcu_degree_check("學士班", "大二")[0] == "pass"
    assert tpcu_degree_check("學士班", "大三")[0] == "pass"
    assert tpcu_degree_check("五專部", "專四")[0] == "pass"
    assert tpcu_degree_check("碩士班", "碩一")[0] == "pass"
    assert tpcu_degree_check("碩士班", "碩二")[0] == "pass"
    assert tpcu_degree_check("境外碩士專班", "碩一")[0] == "fail"
    assert tpcu_degree_check("在職專班", "碩一")[0] == "fail"
    assert tpcu_degree_check("學分班", "一")[0] == "fail"
    assert tpcu_degree_check("學士班", "休學")[0] == "fail"
    assert tpcu_degree_check(None, None)[0] == "needs_confirmation"

    assert tpcu_academic_check("學士班", 82.0, 3.5, 15.0)[0] == "pass"
    assert tpcu_academic_check("學士班", 60.0, 2.0, 60.0)[0] == "pass"
    assert tpcu_academic_check("學士班", 58.0, 1.8, 85.0)[0] == "fail"
    assert tpcu_academic_check("學士班", None, None, 25.0)[0] == "pass"
    assert tpcu_academic_check("學士班", None, 2.5, None)[0] == "pass"
    assert tpcu_academic_check("學士班", None, 1.5, None)[0] == "fail"
    assert tpcu_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_tpcu_language_checks() -> None:
    assert (
        tpcu_language_check(None, None, partner_country="日本")[0]
        == "needs_confirmation"
    )
    assert tpcu_language_check("toefl", 79.0, partner_country="美國")[0] == "pass"
    assert tpcu_language_check("toefl", 61.0, partner_country="紐西蘭")[0] == "pass"
    assert tpcu_language_check("toefl", 35.0, partner_country="英國")[0] == "fail"
    assert tpcu_language_check("ielts", 6.0, partner_country="英國")[0] == "pass"
    assert tpcu_language_check("ielts", 5.5, partner_country="紐西蘭")[0] == "pass"
    assert tpcu_language_check("ielts", 4.0, partner_country="英國")[0] == "fail"
    assert tpcu_language_check("toefl_itp", 500.0, partner_country="美國")[0] == "pass"
    assert tpcu_language_check("toefl_itp", 400.0, partner_country="美國")[0] == "fail"
    assert tpcu_language_check("toeic", 750.0, partner_country="美國")[0] == "pass"
    assert tpcu_language_check("toeic", 550.0, partner_country="日本")[0] == "pass"
    assert tpcu_language_check("toeic", 300.0, partner_country="美國")[0] == "fail"
    assert tpcu_language_check("jlpt", 1.0, partner_country="日本")[0] == "pass"
    assert tpcu_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"
    assert tpcu_language_check("jlpt", 3.0, partner_country="日本")[0] == "pass"
    assert tpcu_language_check("jlpt", 4.0, partner_country="日本")[0] == "pass"
    assert tpcu_language_check("jlpt", 6.0, partner_country="日本")[0] == "fail"
    assert tpcu_language_check("topik", 4.0, partner_country="南韓")[0] == "pass"
    assert tpcu_language_check("topik", 3.0, partner_country="南韓")[0] == "pass"
    assert tpcu_language_check("topik", 2.0, partner_country="南韓")[0] == "pass"
    assert tpcu_language_check("topik", 0.0, partner_country="南韓")[0] == "fail"
    assert (
        tpcu_language_check("duolingo", 110.0, partner_country="美國")[0]
        == "needs_confirmation"
    )


def test_tpcu_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_tpcu_partner_universities()
    assert len(partners) == 18
    assert sum(1 for p in partners if p.availability_status == "open") == 18
    assert sum(1 for p in partners if p.application_window_status == "open") == 18
    assert all(
        p.location and p.location.geocode_status == "verified" for p in partners
    )
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_tpcu_student_dashboard()
    assert dashboard.school_name == TPCU.school_name
    assert len(dashboard.partner_universities) == 18
    assert len(dashboard.application_periods) >= 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(tpcu_exchange_info().scholarship_info) >= 3
    assert len(tpcu_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == TPCU.school_name
    ]
    assert len(workflows) == 18
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "verified" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == TPCU.school_name
    ]
    assert len(destinations) == 18
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert (
            est is not None
        ), f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("tpcu")
    assert len(templates) == 6
    assert all("tpcu.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads(
        (BUNDLE / "import_provenance.json").read_text(encoding="utf-8")
    )
    assert len(provenance["sources"]) >= 25
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_tpcu_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_tpcu_partner_universities()
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
            home_university=TPCU.school_name,
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
        and d.home_university == TPCU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=TPCU.school_name,
            academic_year=sample.academic_year or "115",
            application_round=sample.application_round,
            degree_level="學士班",
            current_year="大三",
            college="商管學院",
            academic_score=84.0,
            academic_gpa=3.7,
            class_rank_percent=12.0,
            language_test="toefl",
            language_score=85,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=TPCU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=TPCU.school_name,
    )
    assert completeness.available_count >= 7

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    tpcu_entry = next(u for u in r_unis.json() if u["id"] == "tpcu")
    assert tpcu_entry["partner_count"] == 18
    assert len(tpcu_entry["colleges"]) == 3

    r_cov = client.get("/coverage?school=tpcu")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 18
    assert cov["image_count"] == 18
    assert cov["official_website_count"] == 18
    assert cov["workflow_school_count"] == 18
    assert cov["destination_profile_count"] == 18
    assert cov["experience_school_count"] == 18
    assert cov["experience_source_count"] >= 38
