from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from exchange_info import storage
from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates
from exchange_info.access_control import school_from_email
from exchange_info.application_rules import build_personal_application_plan
from exchange_info.advisor import build_advisor_plan
from exchange_info.models import AdvisorProfile, AccountSelectionProfile, PersonalApplicationPlanRequest
from exchange_info.ntu_eligibility import ntu_academic_check
from exchange_info.ntu_student_view import build_ntu_student_dashboard, fetch_ntu_partner_universities
from exchange_info.university_registry import NTU, require_university
from exchange_info.school_identity import same_school, school_identity_key
from pydantic import ValidationError


@pytest.mark.parametrize("alias", ["臺大", "台大", "台灣大學", "國立臺灣大學", "NTU", "National Taiwan University"])
def test_ntu_aliases_resolve_to_the_third_school(alias):
    assert require_university(alias) == NTU


def test_shared_exchange_visiting_note_does_not_merge_different_schools():
    note = "（E交換學生計畫、V訪問學生計畫）"
    assert same_school("奧瑞岡大學" + note, "奧瑞岡大學")
    assert not same_school("奧瑞岡大學" + note, "夏威夷大學希羅分校" + note)
    assert school_identity_key("臺灣大學 National Taiwan University") == "national taiwan university"


def test_ntu_email_domain_and_subdomains_are_recognized():
    assert school_from_email("student@ntu.edu.tw") == NTU
    assert school_from_email("student@g.ntu.edu.tw") == NTU
    assert school_from_email("student@ntu.edu.tw.example.com") is None


@pytest.mark.parametrize("degree,gpa,rank,status", [
    ("大學部", 2.44, 70, "pass"),
    ("大學部", 2, 50, "pass"),
    ("大學部", 2.43, 50.01, "fail"),
    ("大學部", 2.43, None, "needs_confirmation"),
    ("大學部", None, 60, "needs_confirmation"),
    ("大學部", None, None, "needs_confirmation"),
    ("研究所", None, None, "pass"),
    ("碩士班", 1, 90, "pass"),
    ("博士班", None, None, "pass"),
    ("在職碩士班", 4, 1, "fail"),
    (None, 4, 1, "needs_confirmation"),
])
def test_ntu_gpa_or_rank_and_graduate_exception(degree, gpa, rank, status):
    assert ntu_academic_check(degree, gpa, rank)[0] == status


def test_bundle_does_not_promote_contract_or_historical_quotas(tmp_path):
    partners = fetch_ntu_partner_universities()
    assert len(partners) == 288
    assert len({partner.source_url for partner in partners}) == 288
    assert len({school_identity_key(partner.school_name) for partner in partners}) == 288
    assert sum(partner.quota is None for partner in partners) == 282
    assert sum(partner.quota == "0 名" for partner in partners) == 6
    assert all(partner.availability_status != "open" for partner in partners)
    assert all(not partner.study_period or "名" not in partner.study_period for partner in partners)
    workflows = [row for row in storage.load_bundled_application_workflows() if row.home_university == NTU.school_name]
    destinations = [row for row in storage.load_destination_profiles(tmp_path, include_bundled_baseline=True) if row.home_university == NTU.school_name]
    assert len(workflows) == len(destinations) == 288
    assert all(row.applicability_status == "needs_confirmation" and row.published_at is None for row in workflows)
    assert all(not step.deadline_reminder_eligible for row in workflows for step in row.steps)
    assert storage.load_application_workflows(tmp_path) == []


def test_ntu_dashboard_uses_announced_taipei_times_without_percent_grade_gate():
    upcoming = build_ntu_student_dashboard(reference_time=datetime.fromisoformat("2026-10-08T12:00:00+08:00"))
    open_dashboard = build_ntu_student_dashboard(reference_time=datetime.fromisoformat("2026-11-03T10:00:00+08:00"))
    closed = build_ntu_student_dashboard(reference_time=datetime.fromisoformat("2026-11-09T16:01:00+08:00"))
    assert upcoming.academic_score_minimum is None
    assert "或" in upcoming.academic_score_rule
    assert upcoming.language_score_minimums == {"ielts": 6, "toefl": 79, "toefl_new": 4}
    assert upcoming.application_periods[0].status == "upcoming"
    assert open_dashboard.application_periods[0].status == "open"
    assert closed.application_periods[0].status == "closed"
    assert upcoming.application_periods[2].opens_at == datetime.fromisoformat("2026-12-02T16:00:00+08:00")
    assert len(upcoming.required_documents[0].details) == 11
    assert len([item for item in upcoming.program_overview if "院級" in item.title]) == 4


def test_ntu_catalog_api_works_offline_and_keeps_pending_visible(monkeypatch, tmp_path):
    def network_not_allowed():
        raise AssertionError("NTU must not fetch CGU or NTPU at runtime")
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", network_not_allowed)
    monkeypatch.setattr("exchange_info.api.fetch_ntpu_partner_universities", network_not_allowed)
    client = TestClient(create_app(tmp_path))
    assert [row["id"] for row in client.get("/universities").json()] == ["cgu", "ntpu", "ntu", "ncu"]
    dashboard = client.get("/student-dashboard", params={"school": "台大"})
    assert dashboard.status_code == 200
    assert dashboard.json()["school_name"] == NTU.school_name
    assert len(dashboard.json()["partner_universities"]) == 288
    coverage = client.get("/coverage", params={"school": "NTU"}).json()
    assert coverage["total_partner_schools"] == 288
    assert coverage["workflow_school_count"] == coverage["destination_profile_count"] == 288
    assert all(row["workflow_status"] == "official_partial" for row in coverage["partners"])
    partner = dashboard.json()["partner_universities"][0]
    detail = client.get("/destination-profile", params={"school": partner["school_name"], "home_school": "NTU"})
    assert detail.status_code == 200 and detail.json()["home_university"] == NTU.school_name
    for row in dashboard.json()["partner_universities"]:
        if "E交換學生計畫" in row["school_name"]:
            destination = client.get("/destination-profile", params={"school": row["school_name"], "home_school": "NTU"}).json()
            assert destination["school_name"] == row["school_name"]
            assert destination["sources"][0]["source_url"] == row["source_url"]
    documents = client.get("/documents", params={"school": "NTU"}).json()
    assert documents and all("ntu.edu.tw" in row["source_url"] for row in documents)
    assert len(client.get("/deadlines", params={"school": "NTU"}).json()) >= 6
    assert client.get("/search", params={"school": "NTU", "q": "2.44"}).json()


def test_pending_quota_plan_cannot_claim_current_eligibility_or_convert_percentage():
    partners = fetch_ntu_partner_universities()
    pending = next(row for row in partners if row.quota is None)
    zero = next(row for row in partners if row.quota == "0 名")
    request = PersonalApplicationPlanRequest(
        home_school=NTU.school_name, college="工學院", department="機械工程學系", degree_level="大學部", academic_score=90,
        academic_gpa=None, class_rank_percent=None, language_test="toefl_new", language_score=4,
        preferences=[{"rank": 1, "school_name": pending.school_name}, {"rank": 2, "school_name": zero.school_name}],
    )
    result = build_personal_application_plan(request, partners, [], academic_score_minimum=None)
    assert result.choices[0].status == "needs_confirmation"
    assert result.choices[1].status == "unavailable"
    checks = {check.code: check for check in result.choices[0].checks}
    assert checks["academic_score"].status == "needs_confirmation"
    assert checks["language_score"].status == "needs_confirmation"
    assert checks["home_language_score"].status == "pass"


def test_ntu_preparation_tools_do_not_claim_other_schools_official_forms():
    templates = all_application_templates("臺大")
    assert templates
    for template in templates:
        assert not template.official_layout and template.official_download_url is None
        assert "ntu.edu.tw" in template.source_url
        assert "cgu.edu.tw" not in template.model_dump_json()
        assert "長庚" not in template.model_dump_json()
    plan = next(template for template in templates if template.id == "study-plan")
    assert "500字" in plan.description and "A4兩面" in plan.description


@pytest.mark.parametrize("model", [AdvisorProfile, AccountSelectionProfile, PersonalApplicationPlanRequest])
def test_zero_class_rank_is_rejected(model):
    payload = {"class_rank_percent":0}
    if model is PersonalApplicationPlanRequest:
        payload.update(home_school=NTU.school_name, preferences=[{"rank":1,"school_name":"測試大學"}])
    with pytest.raises(ValidationError) as error:
        model.model_validate(payload)
    assert [item["loc"] for item in error.value.errors()] == [("class_rank_percent",)]
    model.model_validate({**payload, "class_rank_percent":1})
    assert ntu_academic_check("大學部", None, 0)[0] == "needs_confirmation"


@pytest.mark.parametrize("language_test,score,home_status", [("toefl_new",4.5,"pass"), ("toefl_new",3.5,"needs_confirmation"),
    ("toefl",78,"needs_confirmation"), ("ielts",5.5,"needs_confirmation"), ("toeic",990,"needs_confirmation")])
def test_ntu_advisor_includes_pending_quota_and_agrees_with_evaluation(language_test, score, home_status):
    dashboard = build_ntu_student_dashboard()
    pending = next(row for row in dashboard.partner_universities if row.quota is None)
    zero_names = {row.school_name for row in dashboard.partner_universities if row.quota == "0 名"}
    profile = AdvisorProfile(school_name=NTU.school_name, college="工學院", department="機械工程學系", degree_level="大學部",
                             academic_gpa=3.5, class_rank_percent=20, language_test=language_test, language_score=score,
                             target_school=pending.school_name)
    recommendation = build_advisor_plan(profile, dashboard, [], [], [])
    assert recommendation.recommendations
    assert recommendation.target_match is not None
    assert all(row.eligibility_status == "needs_confirmation" for row in recommendation.recommendations)
    assert not zero_names.intersection(row.school_name for row in recommendation.recommendations)
    assert any("本期甄選名額尚未公告" in note for note in recommendation.target_match.confirmation_items)
    request = PersonalApplicationPlanRequest(home_school=NTU.school_name, college=profile.college, department=profile.department,
        degree_level=profile.degree_level, academic_gpa=profile.academic_gpa, class_rank_percent=profile.class_rank_percent,
        language_test=language_test, language_score=score, preferences=[{"rank":1,"school_name":pending.school_name}])
    evaluation = build_personal_application_plan(request, dashboard.partner_universities, [], academic_score_minimum=None)
    assert evaluation.choices[0].status == "needs_confirmation"
    assert next(check for check in evaluation.choices[0].checks if check.code == "home_language_score").status == home_status


def test_ntu_catalog_rebuilds_from_tracked_source_snapshot(tmp_path):
    root = Path(__file__).parents[1]
    subprocess.run([sys.executable, "scripts/build_ntu_catalog.py", "--output-dir", str(tmp_path)], cwd=root, check=True, capture_output=True, timeout=30)
    bundled = root / "src/exchange_info/official_data/ntu"
    for source in bundled.iterdir():
        if source.is_file():
            assert (tmp_path / source.name).read_bytes() == source.read_bytes(), source.name
    provenance = json.loads((tmp_path / "import_provenance.json").read_text())
    assert provenance["original_home_flags"]["candidate_only"] is True
    assert provenance["content_verification_status"] == "partial_current_cycle"
