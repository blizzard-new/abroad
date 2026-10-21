from __future__ import annotations

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
from exchange_info.fju_eligibility import (
    fju_academic_check,
    fju_degree_check,
    fju_internal_language_points,
    fju_language_check,
    is_fju,
)
from exchange_info.fju_student_view import (
    build_fju_student_dashboard,
    fetch_fju_partner_universities,
    fju_exchange_info,
    fju_processed_pages,
)
from exchange_info.models import ApplicationRuleContext, PersonalApplicationPlanRequest
from exchange_info.school_completeness import build_school_completeness
from exchange_info.university_registry import FJU, require_university

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "fju"


@pytest.mark.parametrize(
    "alias",
    [
        "fju",
        "FJU",
        "輔大",
        "輔仁",
        "輔仁大學",
        "天主教輔仁大學",
        "Fu Jen Catholic University",
    ],
)
def test_fju_aliases(alias: str) -> None:
    assert require_university(alias) == FJU
    assert is_fju(alias)


@pytest.mark.parametrize(
    "email,allowed",
    [
        ("student@fju.edu.tw", True),
        ("412345678@mail.fju.edu.tw", True),
        ("student@gapp.fju.edu.tw", True),
        ("student@m365.fju.edu.tw", True),
        ("student@ntu.edu.tw", False),
        ("student@gmail.com", False),
    ],
)
def test_fju_email_domains(email: str, allowed: bool) -> None:
    assert (school_from_email(email) == FJU) is allowed


def test_fju_degree_and_academic_checks() -> None:
    assert fju_degree_check("大學部", "大二")[0] == "pass"
    assert fju_degree_check("大學部", "大四")[0] == "needs_confirmation"
    assert fju_degree_check("碩士班", "碩一")[0] == "pass"
    assert fju_degree_check("博士班", "博一")[0] == "pass"
    assert fju_degree_check(None, None)[0] == "needs_confirmation"

    # 116-1 notice requires undergraduate average 70; rank is not an alternative.
    assert fju_academic_check("大學部", 75.0, 3.2, None)[0] == "pass"
    assert fju_academic_check("大學部", 68.0, 2.8, 45.0)[0] == "fail"
    assert fju_academic_check("大學部", 65.0, 2.5, 60.0)[0] == "fail"
    assert fju_academic_check("大學部", None, None, None)[0] == "needs_confirmation"


def test_fju_language_checks_and_internal_points() -> None:
    assert fju_language_check(None, None, partner_country="中國大陸")[0] == "pass"
    assert fju_language_check("toefl", 85.0, partner_country="美國")[0] == "pass"
    assert fju_language_check("toefl", 70.0, partner_country="美國")[0] == "fail"
    assert fju_language_check("ielts", 6.5, partner_country="英國")[0] == "pass"
    assert fju_language_check("toeic", 785.0, partner_country="日本")[0] == "pass"

    assert fju_internal_language_points("toefl", 95.0) is None
    assert fju_internal_language_points("ielts", 6.5) == 60.0
    assert fju_internal_language_points("toeic", 785.0) is None


def test_fju_bundle_and_dashboard_completeness(tmp_path: Path) -> None:
    partners = fetch_fju_partner_universities()
    assert len(partners) == 237
    assert sum(1 for p in partners if p.country in {"中國大陸", "香港", "澳門"}) == 63
    assert sum(1 for p in partners if p.country not in {"中國大陸", "香港", "澳門"}) == 174
    assert all(p.quota_status == "reference_only" for p in partners)
    assert all(p.availability_status == "agreement_only" for p in partners)
    # Newly added reference routes retain explicit location gaps.
    assert {p.school_name for p in partners if not p.location} == {
        "(自費)東洋大學 Toyo University", "(自費)南山大學 Nanzan University",
        "(自費)同志社大學 Doshisha University",
    }
    assert all(p.location.geocode_status == "verified" for p in partners if p.location)
    assert all(p.student_summary_zh is not None for p in partners)

    dashboard = build_fju_student_dashboard()
    assert dashboard.school_name == FJU.school_name
    assert len(dashboard.partner_universities) == 237
    assert len(dashboard.application_periods) == 3
    assert len(dashboard.document_explanations) >= 1
    assert len(dashboard.rule_explanations) >= 1
    assert len(fju_exchange_info().scholarship_info) >= 3
    assert len(fju_processed_pages()) >= 3

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == FJU.school_name
    ]
    assert len(workflows) == 237
    assert all(w.review_status == "published" for w in workflows)
    assert all(w.applicability_status in {"verified", "needs_confirmation"} for w in workflows)

    destinations = [
        d
        for d in storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
        if d.home_university == FJU.school_name
    ]
    assert len(destinations) == 237
    unconfirmed_costs = set()
    for dest in destinations:
        if dest.cost_evidence and dest.cost_evidence.status in {"needs_confirmation", "reference_only"}:
            from exchange_info.cost_estimates import budget_fit
            assert budget_fit(extract_monthly_estimates(dest), 1000000)["status"] == "unknown"
            unconfirmed_costs.add(dest.school_name)
            continue
        est = primary_estimate(extract_monthly_estimates(dest))
        assert est is not None, f"Missing primary monthly cost estimate for {dest.school_name}"
        assert est.scope == "total_living"
    assert unconfirmed_costs == {
        "聖心女子大學 University of the Sacred Heart, Tokyo",
        "(語言密集課程)聖心女子大學 University of the Sacred Heart, Tokyo",
        "梅光學院大學 Baiko Gakuin University",
        "(自費)梅光學院大學 Baiko Gakuin University",
        "(自費)東洋大學 Toyo University",
        "(自費)南山大學 Nanzan University",
        "(自費)同志社大學 Doshisha University",
    }

    templates = all_application_templates("fju")
    assert len(templates) == 6
    assert all("fju.edu.tw" in (t.source_url or "") for t in templates)

    import hashlib
    import json

    provenance = json.loads((BUNDLE / "import_provenance.json").read_text(encoding="utf-8"))
    assert len(provenance["sources"]) == 18
    for src in provenance["sources"]:
        path = ROOT / src["file"]
        assert path.is_file(), f"Missing archived source: {src['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]


def test_fju_workflow_plan_and_api_endpoints(tmp_path: Path) -> None:
    partners = fetch_fju_partner_universities()
    sample = partners[0]
    workflows = storage.load_bundled_application_workflows()
    destinations = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    wf = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=FJU.school_name,
            partner_university=sample.school_name,
            academic_year="116",
            application_round="第1學期（秋季班）",
        ),
    )
    assert wf is not None
    assert len(wf.steps) == 5

    dest = next(
        d
        for d in destinations
        if d.school_name == sample.school_name and d.home_university == FJU.school_name
    )
    assert dest is not None

    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(
            home_school=FJU.school_name,
            academic_year="116",
            application_round="第1學期（秋季班）",
            degree_level="大學部",
            current_year="大二",
            college="管理學院",
            academic_score=82.5,
            academic_gpa=3.6,
            language_test="toefl",
            language_score=88,
            preferences=[{"rank": 1, "school_name": sample.school_name}],
        ),
        partners,
        workflows,
        academic_score_minimum=FJU.academic_score_minimum,
    )
    assert len(plan.choices) == 1
    checks = {c.code: c for c in plan.choices[0].checks}
    assert checks["academic_score"].status == "pass"
    assert checks["home_language_score"].status == "pass"

    completeness = build_school_completeness(
        sample,
        dest,
        wf,
        home_university=FJU.school_name,
    )
    eligibility_item = next(item for item in completeness.items if item.key == "eligibility")
    assert eligibility_item.status == "partial"
    assert "部分不明" in eligibility_item.note

    client = TestClient(create_app(tmp_path))
    r_unis = client.get("/universities")
    assert r_unis.status_code == 200
    fju_entry = next(u for u in r_unis.json() if u["id"] == "fju")
    assert fju_entry["partner_count"] == 237
    assert len(fju_entry["colleges"]) == 14

    r_cov = client.get("/coverage?school=fju")
    assert r_cov.status_code == 200
    cov = r_cov.json()
    assert cov["total_partner_schools"] == 237
    assert cov["workflow_school_count"] == 237
    assert cov["destination_profile_count"] == 237
    # Coverage reuses institutional imagery across program variants. This is a
    # display count, not evidence that the three new route campuses were reviewed.
    assert cov["image_count"] == 237
    assert cov["official_website_count"] >= 150
