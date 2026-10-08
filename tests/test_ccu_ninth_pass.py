"""Meaningful runtime checks for geography, source-bound documents and scopes."""

import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents
from exchange_info.ccu_profile import reviewed_profiles, school_location
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.qualification_scopes import (
    college_scope_matches,
    degree_scope_needs_confirmation,
)
from exchange_info.university_locations import UniversityLocation


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


def test_profile_review_covers_source_backed_geography_and_distinct_life():
    rows = reviewed_profiles()
    assert len(rows) == 55
    assert len(reviewed_documents()) == 23
    for page, row in rows.items():
        partner = at(page)
        if row["fields"]["city"]["value"]:
            assert partner.location.city == row["fields"]["city"]["value"]
            assert (
                partner.location.latitude is None and partner.location.longitude is None
            )
            assert partner.location.geocode_status == "pending"
        life = row["fields"]["campus_life"]
        transport = row["fields"]["transport"]
        if life["value"] and transport["value"]:
            assert life["value"] != transport["value"]
    assert at(33).location.city == "市川"
    assert at(85).location.city == "Pessac"
    assert at(103).location.city == "Winterthur"
    assert at(111).location.city == "Karviná"
    assert at(71).location is None
    anomaly = json.loads(
        (BUNDLE / "overseas_sources/p71-profile-root.json").read_text()
    )
    assert anomaly["access_result"] == "unrelated_content_anomaly"


def test_explicit_operator_location_review_is_not_overridden():
    partner = at(33)
    missing = UniversityLocation(
        school_name=partner.school_name, country=partner.country
    )
    assert school_location(partner, missing).city == "市川"
    blocked = missing.model_copy(update={"geocode_status": "needs_review"})
    assert school_location(partner, blocked) is blocked
    operator = missing.model_copy(
        update={
            "city": "operator reviewed city",
            "source_url": "https://example.edu/official",
        }
    )
    assert school_location(partner, operator) is operator


def test_structured_academic_scopes_stay_conservative():
    assert college_scope_matches(at(105).colleges, "社會科學院")
    assert not college_scope_matches(at(105).colleges, "工學院")
    assert degree_scope_needs_confirmation(at(37).degree_levels)
    assert degree_scope_needs_confirmation(at(35).degree_levels)
    assert at(74).degree_levels is None


def test_hufs_actual_new_2027_body_resolves_old_calendar_without_editing_old_pdf():
    p = at(47)
    f = p.partner_exchange_details
    assert f["academic_calendar"].status == "verified_current"
    assert (
        "2027-03-02" in f["academic_calendar"].value
        and "06-21" in f["academic_calendar"].value
    )
    old = json.loads((BUNDLE / "overseas_sources/p47-mirror.json").read_text())
    assert "June 21, 2026" in " ".join(" ".join(t.split()) for t in old["text_pages"])
    assert "至少2.5" in f["eligibility"].value
    assert "B2簽章" in f["language"].value
    assert f["arrival"].status == "explicit_not_announced"


def test_runtime_preserves_city_and_separates_reference_life_status(tmp_path):
    client = TestClient(create_app(tmp_path))
    dashboard = client.get("/student-dashboard", params={"school": HOME}).json()
    partners = dashboard["partner_universities"]
    for page, city in [
        (33, "市川"),
        (85, "Pessac"),
        (103, "Winterthur"),
        (111, "Karviná"),
    ]:
        data = next(p for p in partners if p["school_name"] == at(page).school_name)
        assert data["location"]["city"] == city
        assert data["location"]["latitude"] is None
    p = at(83)
    guide = client.get(
        "/destination-profile", params={"home_school": HOME, "school": p.school_name}
    ).json()
    assert guide["city"] == p.location.city
    assert guide["transport_summary"] != guide["campus_life_summary"]
    assert {"transport", "campus_life"} <= {
        s["key"] for s in guide["student_guide_sections"]
    }
    p = at(42)
    result = client.get(
        "/school-data-completeness",
        params={"home_school": HOME, "school": p.school_name},
    ).json()
    items = {r["key"]: r for r in result["items"]}
    assert items["transport"]["status"] == "needs_confirmation"
    assert items["documents"]["status"] == "partial"
    unresolved = client.get(
        "/school-data-completeness",
        params={"home_school": HOME, "school": at(103).school_name},
    ).json()
    unresolved_items = {r["key"]: r for r in unresolved["items"]}
    assert unresolved_items["housing"]["status"] == "needs_confirmation"
    assert unresolved_items["cost"]["status"] == "needs_confirmation"
    missing = client.get(
        "/destination-profile",
        params={"home_school": HOME, "school": at(71).school_name},
    ).json()
    assert (
        missing["city"] is None
        and missing["transport_summary"] is None
        and missing["campus_life_summary"] is None
    )


def test_api_host_documents_have_individual_forms_conditions_and_later_stages(tmp_path):
    client = TestClient(create_app(tmp_path))
    for page in [32, 37, 43, 47, 48, 53, 68, 108, 114]:
        flow = client.get(
            "/application-workflow",
            params={"home_school": HOME, "school": at(page).school_name},
        ).json()
        assert flow["review_status"] != "published"
        host = flow["steps"][4]
        registry = reviewed_documents()[page]
        assert len(host["document_requirements"]) == len(registry["requirements"])
        assert len(host["document_requirements"]) > 1
        assert all(len(r["name"]) < 240 for r in host["document_requirements"])
        if page == 32:
            assert any(
                "if available" in r["name"] and "JLPT" in r["name"]
                for r in host["document_requirements"]
            )
            assert len(host["official_form_urls"]) >= 5
            assert any(
                "歷史灰字參考" in detail and "不作必備文件" in detail
                for detail in flow["steps"][3]["details"]
            )
        if page == 53:
            assert any(
                "12/20" in r["name"]
                and "1/15" in r["name"]
                and r["copy_type"] == "original"
                for r in host["document_requirements"]
            )
            assert any(
                "中正逐校第二階文件：當期已核實" in detail
                and "Certificate of Enrollment" in detail
                for detail in flow["steps"][3]["details"]
            )
        if page == 68:
            assert any("optional" in r["name"] for r in host["document_requirements"])
        if page == 108:
            assert any(
                "不得自行套中正" in r["name"] for r in host["document_requirements"]
            )


def test_tampered_document_source_is_rejected(tmp_path, monkeypatch):
    import exchange_info.ccu_documents as module

    rows = json.loads((BUNDLE / "partner-document-requirements.json").read_text())
    (tmp_path / "partner-document-requirements.json").write_text(json.dumps(rows))
    ev = rows[0]["requirements"][0]["evidence"][0]
    source = json.loads(
        (BUNDLE / "overseas_sources" / (ev["source_id"] + ".json")).read_text()
    )
    source["text_pages"][0] += " changed"
    source["sha256"] = hashlib.sha256(b"changed").hexdigest()
    (tmp_path / "overseas_sources").mkdir()
    (tmp_path / "overseas_sources" / (ev["source_id"] + ".json")).write_text(
        json.dumps(source)
    )
    monkeypatch.setattr(module, "BUNDLE", tmp_path)
    module.reviewed_documents.cache_clear()
    try:
        with pytest.raises(ValueError, match="Changed CCU document evidence"):
            module.reviewed_documents()
    finally:
        module.reviewed_documents.cache_clear()


def test_direct_life_link_uses_resolved_ccu_home_without_query(tmp_path, monkeypatch):
    from exchange_info import api

    monkeypatch.setattr(api, "fetch_partner_universities", list)
    monkeypatch.setattr(api, "fetch_ntpu_partner_universities", list)
    monkeypatch.setattr(api, "fetch_ntu_partner_universities", list)
    client = TestClient(create_app(tmp_path))
    response = client.get("/school-life-context", params={"school": at(33).school_name})
    assert response.status_code == 200
    assert "市川" in response.json()["location_note"]
    assert "尚無已核對的校區座標" in response.json()["location_note"]
    transport = next(
        c for c in response.json()["categories"] if c["theme"] == "transport"
    )
    assert any(
        "cuc.ac.jp/eng/about/accessmap.html" in s["url"]
        for e in transport["evidence"]
        for s in e["sources"]
    )
    assert all(
        "2027" in e["text"] and "適用年度或條件待確認" in e["scope"]
        for e in transport["evidence"]
    )
