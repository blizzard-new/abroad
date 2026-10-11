"""Actual faculty conflicts, exchange fee scope and public-marker provenance."""
import json

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_language import assess_ccu_language
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def read(name):
    return json.loads((BUNDLE / name).read_text())


def at(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def test_fges_parent_wrong_year_does_not_silently_replace_faculty_deadline():
    partner = at(88)
    original = next(json.loads(line) for line in (BUNDLE / "partners.jsonl").read_text().splitlines()
                    if json.loads(line)["source_pages"][0] == 88)
    assert partner.quota == original["quota"] and partner.eligibility == original["eligibility"]
    assert partner.language_requirement == original["language_requirement"]
    assert partner.application_window_status == "closed" and partner.availability_status == "open"
    fields = partner.partner_exchange_details
    assert fields["nomination_deadline"].status == fields["application_deadline"].status == "conflict"
    assert "2026-11-15" in partner.partner_application_deadline and "2025" in partner.partner_application_deadline
    assert partner.student_summary_zh.application_deadline == partner.partner_application_deadline
    assert partner.field_evidence["partner_application_deadline"].status == "conflict"
    assert partner.reference_data["partner_application_deadline"] == original["partner_application_deadline"]
    assert any(e.source_pages == [9] and "2025" in e.excerpt for e in fields["application_deadline"].evidence)
    assert any("2026" in e.academic_year and "Spring 2027" in e.excerpt for e in fields["application_deadline"].evidence)


def test_fges_specific_table_rows_language_and_calendar_remain_distinct():
    partner = at(88)
    fields = partner.partner_exchange_details
    assert fields["language"].status == "conflict"
    assert "advised" in fields["language"].value and "minimum" in fields["language"].value
    assert "不能把FLSH心理學" in fields["language"].value
    assert partner.language_review_note == fields["language"].value
    assert all(c.requirement_level == "conflict" and c.scope_choice_required
               and c.evidence.status == "conflict" for c in partner.language_conditions)
    assert fields["language"].value in partner.student_summary_zh.eligibility_points
    assessed = assess_ccu_language(partner, "other", "大學部")
    assert assessed.threshold is None and assessed.note == fields["language"].value
    assert fields["academic_calendar"].status == "conflict"
    assert "不是FD" in fields["academic_calendar"].value and "M1" in fields["academic_calendar"].value
    assert fields["academic_calendar"].value in partner.student_summary_zh.study_period
    assert any(e.source_pages == [8] and "mid-June" in e.excerpt for e in fields["academic_calendar"].evidence)
    assert fields["course_restrictions"].status == "needs_confirmation"
    assert "25–26" in fields["course_restrictions"].value


def test_fges_recommended_housing_and_monthly_service_fee_are_not_guarantees():
    fields = at(88).partner_exchange_details
    assert fields["housing_deadline"].status == "verified_current"
    assert "recommended" in fields["housing_deadline"].value and "2026-11-15" in fields["housing_deadline"].value
    assert "不保證住宿" in fields["housing"].value and "1個月" in fields["housing"].value
    assert "105/月" in fields["costs"].value
    assert fields["application_forms"].status == "needs_confirmation"
    assert "帳號" in fields["application_forms"].value


def test_qut_2027_exchange_costs_scholarship_and_calendar_keep_their_scope():
    partner = at(120)
    assert partner.availability_status == "not_open"
    assert partner.quota is None and partner.eligibility is None and partner.language_requirement is None
    fields = json.loads(partner.reference_data["ccu_completion"])["reference_host_fields"]
    assert fields["host_tuition"]["status"] == "verified_current"
    assert "9900" in fields["host_tuition"]["value"] and "13200" in fields["host_tuition"]["value"]
    assert "免QUT tuition" in fields["host_tuition"]["value"] and "排除exchange" in fields["host_tuition"]["value"]
    assert fields["costs"]["status"] == "conflict" and "4095" in fields["costs"]["value"]
    assert fields["language"]["status"] == "needs_confirmation" and "未自行換算" in fields["language"]["value"]
    assert fields["academic_calendar"]["status"] == "verified_current"
    assert "2027-02-15" in fields["academic_calendar"]["value"] and "06-19" in fields["academic_calendar"]["value"]
    assert fields["nomination_deadline"]["status"] == "missing"
    assert fields["application_deadline"]["status"] == "needs_confirmation"


def test_personal_form_access_has_an_explicit_official_instruction():
    rows = {r["ccu_page"]: r for r in read("completion-followup-gap-research.json")["schools"]}
    for page in [88, 120]:
        forms = next(f for f in rows[page]["pending_host_policy_reviews"] if f["field"] == "application_forms")
        assert forms["classification"] == "personal_access_required" and forms["personal_access_required"] is True
        assert forms["official_not_announced"] is False
        assert any("account" in e["excerpt"] or "accepted nomination" in e["excerpt"] for e in forms["evidence"])
    baseline = read("completion-followup-gap-baseline.json")
    assert baseline["initial_counts"]["host_missing_fields"] == 702
    assert read("completion-followup-gap-research.json")["current_counts"]["host_missing_fields"] == 649


def test_fges_campus_is_the_faculty_marker_and_other_school_data_is_preserved(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/student-dashboard", params={"school": HOME})
    assert response.status_code == 200
    partner = next(r for r in response.json()["partner_universities"] if r["source_pages"][0] == 88)
    assert partner["location"]["latitude"] == 50.63312 and partner["location"]["longitude"] == 3.0439062
    assert partner["partner_exchange_details"]["application_deadline"]["status"] == "conflict"
    assert partner["partner_application_deadline"] == partner["student_summary_zh"]["application_deadline"]
    point = next(r for r in read("campus-assets.json")["schools"] if r["ccu_page"] == 88)["coordinates"]
    assert "building31" in point["evidence"][1]["excerpt"] and "map viewport" in point["value"]["note"]
    assert len(response.json()["partner_universities"]) == 104
    assert client.get("/coverage", params={"school": HOME}).json()["image_count"] == 100
