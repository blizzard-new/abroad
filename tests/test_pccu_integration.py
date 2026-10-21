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
from exchange_info.pccu_eligibility import (
    is_pccu,
    pccu_academic_check,
    pccu_degree_check,
    pccu_language_check,
)
from exchange_info.pccu_student_view import (
    build_pccu_student_dashboard,
    fetch_pccu_partner_universities,
    pccu_exchange_info,
    pccu_processed_pages,
)
from exchange_info.school_completeness import build_school_completeness
from exchange_info.university_registry import PCCU, require_university
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "pccu"


@pytest.mark.parametrize(
    "alias",
    [
        "pccu",
        "PCCU",
        "文化",
        "文大",
        "文化大學",
        "中國文化大學",
        "Chinese Culture University",
    ],
)
def test_pccu_aliases(alias: str) -> None:
    assert require_university(alias) == PCCU
    assert is_pccu(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@pccu.edu.tw", True),
        ("s111001@ulive.pccu.edu.tw", True),
        ("staff@dep.pccu.edu.tw", True),
        ("s111001@g.pccu.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_pccu_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == PCCU) is allowed


def test_pccu_degree_and_academic_checks() -> None:
    assert pccu_degree_check("學士班", "大一")[0] == "needs_confirmation"
    assert pccu_degree_check("學士班", "大二")[0] == "needs_confirmation"
    assert pccu_degree_check("學士班", "大三")[0] == "needs_confirmation"
    assert pccu_degree_check("碩士班", "碩一")[0] == "needs_confirmation"
    assert pccu_degree_check("博士班", "博二")[0] == "needs_confirmation"
    assert pccu_degree_check("在職專班", "碩二")[0] == "needs_confirmation"
    assert pccu_degree_check("學士班", "延畢")[0] == "needs_confirmation"
    assert pccu_degree_check(None, None)[0] == "needs_confirmation"

    assert pccu_academic_check("學士班", 75.0, 3.2, 25.0)[0] == "needs_confirmation"
    assert pccu_academic_check("學士班", 68.0, None, None)[0] == "needs_confirmation"
    assert pccu_academic_check("學士班", 62.0, 2.0, 65.0)[0] == "needs_confirmation"
    assert pccu_academic_check("碩士班", 82.0, 3.4, None)[0] == "needs_confirmation"
    assert pccu_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_pccu_language_checks() -> None:
    assert pccu_language_check(None, None, partner_country="中國大陸")[0] == "needs_confirmation"
    assert (
        pccu_language_check(None, None, partner_country="美國")[0]
        == "needs_confirmation"
    )
    assert pccu_language_check("toefl", 79.0, partner_country="美國")[0] == "needs_confirmation"
    assert pccu_language_check("toefl", 55.0, partner_country="美國")[0] == "needs_confirmation"
    assert pccu_language_check("ielts", 6.0, partner_country="英國")[0] == "needs_confirmation"
    assert pccu_language_check("ielts", 4.5, partner_country="英國")[0] == "needs_confirmation"
    assert pccu_language_check("toeic", 650.0, partner_country="美國")[0] == "needs_confirmation"
    assert pccu_language_check("toeic", 550.0, partner_country="美國")[0] == "needs_confirmation"
    assert pccu_language_check("jlpt", 2.0, partner_country="日本")[0] == "needs_confirmation"
    assert pccu_language_check("jlpt", 6.0, partner_country="日本")[0] == "needs_confirmation"
    assert pccu_language_check("topik", 3.0, partner_country="韓國")[0] == "needs_confirmation"


def test_pccu_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_pccu_partner_universities()
    assert len(partners) == 135
    assert sum(1 for p in partners if p.availability_status == "open") == 3
    assert (
        sum(1 for p in partners if p.availability_status == "reference_only")
        == 84
    )
    assert sum(1 for p in partners if p.application_window_status == "open") == 3
    assert sum(1 for p in partners if p.application_window_status == "closed") == 53
    assert all(
        p.location and p.location.geocode_status == "verified" for p in partners
    )
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_pccu_student_dashboard()
    assert dashboard.school_name == PCCU.school_name
    assert len(dashboard.partner_universities) == 135
    assert len(dashboard.application_periods) >= 3
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(pccu_exchange_info().scholarship_info) >= 4
    assert len(pccu_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == PCCU.school_name
    ]
    assert len(workflows) == 135
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "needs_confirmation" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == PCCU.school_name
    ]
    assert len(destinations) == 135
    for dest in destinations:
        assert "逐校生活費待查" in dest.cost_summary
        assert dest.coverage_status == "official_partial"

    templates = all_application_templates("pccu")
    assert len(templates) == 6
    assert all("pccu.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads(
        (BUNDLE / "import_provenance.json").read_text(encoding="utf-8")
    )
    assert len(provenance["sources"]) >= 25
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_pccu_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_pccu_partner_universities()
    sample = next(p for p in partners if p.availability_status == "open" and p.country == "中國大陸")
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(
        tmp_path, include_bundled_baseline=True
    )
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=PCCU.school_name,
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
        and d.home_university == PCCU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=PCCU.school_name,
            academic_year="115",
            application_round=sample.application_round,
            degree_level="學士班",
            current_year="大二",
            college="商學院",
            academic_score=80.0,
            academic_gpa=3.5,
            class_rank_percent=20.0,
            language_test="toefl",
            language_score=85,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=PCCU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "needs_confirmation"
    assert checks["home_language_score"].status == "needs_confirmation"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=PCCU.school_name,
    )
    assert completeness.available_count >= 1
    assert wf.applicability_status == "needs_confirmation"

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    pccu_entry = next(u for u in r_unis.json() if u["id"] == "pccu")
    assert pccu_entry["partner_count"] == 135
    assert len(pccu_entry["colleges"]) == 12

    r_cov = client.get("/coverage?school=pccu")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 135
    assert cov["workflow_school_count"] == 135
    assert cov["destination_profile_count"] == 135
    assert cov["image_count"] == 135
    assert cov["official_website_count"] == 135
    assert cov["experience_school_count"] >= 9
