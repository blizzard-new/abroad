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
from exchange_info.university_registry import NTOU, require_university
from exchange_info.ntou_eligibility import (
    is_ntou,
    ntou_academic_check,
    ntou_degree_check,
    ntou_language_check,
)
from exchange_info.ntou_student_view import (
    build_ntou_student_dashboard,
    fetch_ntou_partner_universities,
    ntou_exchange_info,
    ntou_processed_pages,
)
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ntou"


@pytest.mark.parametrize(
    "alias",
    [
        "ntou",
        "NTOU",
        "海大",
        "海洋大學",
        "台灣海洋大學",
        "臺灣海洋大學",
        "國立台灣海洋大學",
        "國立臺灣海洋大學",
        "National Taiwan Ocean University",
    ],
)
def test_ntou_aliases(alias: str) -> None:
    assert require_university(alias) == NTOU
    assert is_ntou(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@ntou.edu.tw", True),
        ("01257001@mail.ntou.edu.tw", True),
        ("01257001@email.ntou.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_ntou_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == NTOU) is allowed


def test_ntou_degree_and_academic_checks() -> None:
    assert ntou_degree_check("學士班", "大一上")[0] == "fail"
    assert ntou_degree_check("學士班", "大一下")[0] == "pass"
    assert ntou_degree_check("學士班", "大二")[0] == "pass"
    assert ntou_degree_check("學士班", "大三")[0] == "pass"
    assert ntou_degree_check("碩士班", "碩一")[0] == "pass"
    assert ntou_degree_check("博士班", "博一")[0] == "pass"
    assert ntou_degree_check("在職專班", "碩二")[0] == "needs_confirmation"
    assert ntou_degree_check("學士班", "延畢")[0] == "needs_confirmation"
    assert ntou_degree_check(None, None)[0] == "needs_confirmation"

    assert ntou_academic_check("學士班", 80.0, 3.5, 20.0)[0] == "pass"
    assert ntou_academic_check("學士班", 60.0, None, None)[0] == "pass"
    assert ntou_academic_check("學士班", 58.0, None, None)[0] == "fail"
    assert ntou_academic_check("碩士班", 75.0, 3.4, None)[0] == "pass"
    assert ntou_academic_check("碩士班", 65.0, None, None)[0] == "fail"
    assert ntou_academic_check("學士班", None, 3.2, None)[0] == "pass"
    assert ntou_academic_check("學士班", None, 2.2, None)[0] == "needs_confirmation"
    assert ntou_academic_check("學士班", None, 1.8, None)[0] == "fail"
    assert ntou_academic_check("學士班", None, None, None)[0] == "needs_confirmation"


def test_ntou_language_checks() -> None:
    assert ntou_language_check(None, None, partner_country="中國大陸")[0] == "pass"
    assert (
        ntou_language_check(None, None, partner_country="美國")[0]
        == "needs_confirmation"
    )
    assert ntou_language_check("toefl", 79.0, partner_country="美國")[0] == "pass"
    assert ntou_language_check("toefl", 60.0, partner_country="德國")[0] == "pass"
    assert ntou_language_check("toefl", 50.0, partner_country="美國")[0] == "fail"
    assert ntou_language_check("ielts", 6.0, partner_country="英國")[0] == "pass"
    assert ntou_language_check("ielts", 5.0, partner_country="日本")[0] == "pass"
    assert ntou_language_check("ielts", 4.5, partner_country="英國")[0] == "fail"
    assert ntou_language_check("toeic", 785.0, partner_country="美國")[0] == "pass"
    assert ntou_language_check("toeic", 600.0, partner_country="法國")[0] == "pass"
    assert ntou_language_check("toeic", 550.0, partner_country="美國")[0] == "fail"
    assert ntou_language_check("jlpt", 2.0, partner_country="日本")[0] == "pass"
    assert ntou_language_check("jlpt", 3.0, partner_country="日本")[0] == "pass"
    assert ntou_language_check("jlpt", 4.0, partner_country="日本")[0] == "fail"
    assert ntou_language_check("jlpt", 6.0, partner_country="日本")[0] == "fail"
    assert ntou_language_check("topik", 3.0, partner_country="韓國")[0] == "pass"
    assert ntou_language_check("topik", 2.0, partner_country="韓國")[0] == "fail"


def test_ntou_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_ntou_partner_universities()
    assert len(partners) == 123
    assert sum(1 for p in partners if p.availability_status == "open") == 46
    assert (
        sum(1 for p in partners if p.availability_status == "reference_only")
        == 77
    )
    assert sum(1 for p in partners if p.application_window_status == "closed") == 123
    assert all(
        p.location and p.location.geocode_status == "verified" for p in partners
    )
    assert all(p.image_status == "verified" and p.image_url for p in partners)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_ntou_student_dashboard()
    assert dashboard.school_name == NTOU.school_name
    assert len(dashboard.partner_universities) == 123
    assert len(dashboard.application_periods) >= 2
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(ntou_exchange_info().scholarship_info) >= 4
    assert len(ntou_processed_pages()) >= 5

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NTOU.school_name
    ]
    assert len(workflows) == 123
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status == "verified" for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == NTOU.school_name
    ]
    assert len(destinations) == 123
    for dest in destinations:
        est = primary_estimate(extract_monthly_estimates(dest))
        assert (
            est is not None
        ), f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"

    templates = all_application_templates("ntou")
    assert len(templates) == 6
    assert all("ntou.edu.tw" in (t.source_url or "") for t in templates)

    provenance = json.loads(
        (BUNDLE / "import_provenance.json").read_text(encoding="utf-8")
    )
    assert len(provenance["sources"]) >= 20
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_ntou_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_ntou_partner_universities()
    sample = next(p for p in partners if p.availability_status == "open" and p.country == "日本")
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(
        tmp_path, include_bundled_baseline=True
    )
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=NTOU.school_name,
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
        and d.home_university == NTOU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=NTOU.school_name,
            academic_year="115",
            application_round=sample.application_round,
            degree_level="學士班",
            current_year="大二",
            college="海運暨管理學院",
            academic_score=82.0,
            academic_gpa=3.6,
            class_rank_percent=18.0,
            language_test="toeic",
            language_score=800,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=NTOU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=NTOU.school_name,
    )
    assert completeness.available_count >= 8

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    ntou_entry = next(u for u in r_unis.json() if u["id"] == "ntou")
    assert ntou_entry["partner_count"] == 123
    assert len(ntou_entry["colleges"]) == 8

    r_cov = client.get("/coverage?school=ntou")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 123
    assert cov["workflow_school_count"] == 123
    assert cov["destination_profile_count"] == 123
    assert cov["image_count"] == 123
    assert cov["official_website_count"] == 123
    assert cov["experience_school_count"] >= 30
