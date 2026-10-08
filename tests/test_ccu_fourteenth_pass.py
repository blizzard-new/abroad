"""Latest SeoulTech body, separate home requirements and uncertain public routes."""

import json

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents
from exchange_info.ccu_profile import reviewed_profiles
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


def test_seoultech_new_body_supersedes_old_housing_and_dates_without_guessing():
    partner = at(48)
    fields = partner.partner_exchange_details
    assert "不保證" in fields["housing"].value
    assert "1329120" in fields["costs"].value and "529200" in fields["costs"].value
    assert "2027-06-21" in fields["academic_calendar"].value
    assert fields["course_restrictions"].status == "conflict"
    assert "最少3" in fields["course_restrictions"].value
    assert (
        fields["eligibility"].status
        == fields["host_tuition"].status
        == "verified_current"
    )
    assert fields["housing_deadline"].value is None
    assert fields["application_forms"].status == "needs_confirmation"
    assert "未含空白Form1" in fields["application_forms"].value
    assert "大學部" in partner.degree_levels and "研究所" in partner.degree_levels
    assert partner.field_evidence["degree_levels"].status == "verified_current"
    new = json.loads(
        (BUNDLE / "overseas_sources/p48-r14-factsheet2027.json").read_text()
    )
    old = json.loads((BUNDLE / "overseas_sources/p48-mirror.json").read_text())
    assert "2027 Spring" in new["text_pages"][0] and len(new["text_pages"]) == 8
    assert "guarantees" in " ".join(old["text_pages"])
    assert "does not guarantee" in new["text_pages"][5]


def test_actual_catalogue_keeps_first_second_dorm_and_home_recommendation_separate(
    tmp_path,
):
    client = TestClient(create_app(tmp_path))
    name = at(48).school_name
    flow_response = client.get(
        "/application-workflow", params={"home_school": HOME, "school": name}
    )
    assert flow_response.status_code == 200
    flow = flow_response.json()
    assert flow["review_status"] == "legacy" and len(flow["steps"]) == 8
    after = next(s for s in flow["steps"] if s["phase"] == "合作校第二次文件送件")
    assert len(after["document_requirements"]) == 3
    assert "不猜錄取前後" in after["timing"]
    assert "Recommendation Letter" in " ".join(flow["steps"][3]["details"])
    registry = reviewed_documents()[48]
    assert (
        len(registry["requirements"]) == 12
        and registry["list_completeness"] == "partial_not_exhaustive"
    )
    assert not any("推薦" in r["requirement"]["name"] for r in registry["requirements"])
    catalog_response = client.get(
        "/application-center/catalog", params={"school": "CCU", "target_school": name}
    )
    assert catalog_response.status_code == 200
    host = [r for r in catalog_response.json()["items"] if r["stage"]]
    assert len(host) == 12
    first = [r for r in host if r["stage"] == "student_application"]
    second = [r for r in host if r["stage"] == "second_submission"]
    dorm = [r for r in host if r["conditional"]]
    assert len(first) == 7 and len(second) == 3 and len(dorm) == 2
    assert all(r["phase"] == "合作校第二次文件送件" for r in second)
    assert all("僅宿舍申請者" in r["condition"] for r in dorm)
    assert all(r["needs_confirmation"] for r in host)
    study = next(r for r in first if "Study Plan" in r["name"])
    assert not study["official_form_verified"] and not study["download_available"]
    bank = next(r for r in second if "銀行" in r["name"])
    assert not bank["conditional"] and bank["copy_type"] == "unspecified"


def test_public_routes_fill_missing_but_preserve_year_campus_and_nationality_scope():
    profiles = reviewed_profiles()
    for page in [26, 108, 109]:
        field = profiles[page]["fields"]["transport"]
        assert field["value"] and field["status"] == "needs_confirmation"
        assert field["evidence"] and field["evidence"][0]["checked_at"].startswith(
            "2026-10-08"
        )
    assert "臺灣HMT適用未核" in profiles[26]["fields"]["transport"]["value"]
    assert "教育學院" in profiles[109]["fields"]["transport"]["value"]
    old = profiles[27]["fields"]["transport"]
    assert old["status"] == "reference_only" and "2025" in old["value"]
    guide = json.loads((BUNDLE / "overseas_sources/p27-r14-guide2025.json").read_text())
    assert "2025 Guidebook" in guide["text_pages"][0]
    empty = json.loads((BUNDLE / "overseas_sources/p27-r14-transport.json").read_text())
    assert empty["http_status"] == 202 and empty["access_result"] == "empty_response"
    bad = json.loads((BUNDLE / "overseas_sources/p48-r14-directions.json").read_text())
    assert bad["http_status"] == 404 and bad["status"] == "fetch_failed"
