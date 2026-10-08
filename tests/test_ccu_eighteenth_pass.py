"""Legacy graduate choices and source-explicit HCMUTE submission projection."""

import hashlib
import json
from collections import Counter

import pytest
from fastapi.testclient import TestClient
from test_ccu_semantics import client_for

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents
from exchange_info.ccu_overseas import reviewed_rows
from exchange_info.ccu_profile import reviewed_profiles
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.qualification_scopes import (
    degree_scope_matches,
    partner_degree_scope_matches,
    resolved_degree_level,
)


def at(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


@pytest.mark.parametrize("college,degree,year,status", [
    ("法學院", "研究所", "博士班", "fail"),
    ("法學院", "研究所", "碩士班", "pass"),
    ("法學院", "研究所", None, "needs_confirmation"),
    ("法學院", "博士班", "博士班", "fail"),
    ("法學院", "碩士班", "碩士班", "pass"),
    ("法學院", "大學部", "大三", "fail"),
    ("教育學院", "研究所", None, "pass"),
    ("教育學院", "研究所", "博士班", "pass"),
    ("教育學院", "大學部", "大三", "pass"),
])
def test_nagoya_graduate_subtype_in_both_apis(tmp_path, college, degree, year, status):
    partner = at(34)
    match = partner_degree_scope_matches(partner, college, resolved_degree_level(degree, year))
    assert match is {"pass": True, "fail": False, "needs_confirmation": None}[status]
    client = client_for(tmp_path)
    inputs = {"college": college, "degree_level": degree, "current_year": year,
              "academic_gpa": 3.5, "academic_score": 85}
    response = client.post("/advisor/plan", json=dict(
        school_name=HOME, target_school=partner.school_name, **inputs
    ))
    assert response.status_code == 200, response.text
    target = response.json()["target_match"]
    assert ("符合目前學制" in target["reasons"]) is (status == "pass")
    if status == "fail":
        assert any("配對不符" in s for s in target["blocking_reasons"])
    elif status == "needs_confirmation":
        assert not any("配對不符" in s for s in target["blocking_reasons"])
        assert any("尚未區分碩博士" in s for s in target["confirmation_items"])
    response = client.post("/application-plan/evaluate", json=dict(
        home_school=HOME, preferences=[{"rank": 1, "school_name": partner.school_name}], **inputs
    ))
    assert response.status_code == 200, response.text
    check = next(c for c in response.json()["choices"][0]["checks"] if c["code"] == "degree_level")
    assert check["status"] == status
    if year == "博士班" and status == "fail":
        assert "博士班" in check["detail"]


def test_unspecified_graduate_is_not_a_specific_degree_pass():
    assert degree_scope_matches("碩士班", "研究所") is None
    assert degree_scope_matches("博士班", "研究所") is None
    assert degree_scope_matches("碩士、博士", "研究所") is True
    assert degree_scope_matches("研究所", "研究所") is True
    assert degree_scope_matches("大學部", "研究所") is False


def test_hcmute_api_uses_explicit_mother_email_for_both_steps(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-workflow", params={"home_school": HOME, "school": at(68).school_name})
    assert response.status_code == 200, response.text
    nomination, followup = response.json()["steps"][3:5]
    for step in (nomination, followup):
        assert step["submission"]["method"] == "email"
        assert "母校" in step["responsible_party"]
        assert step["submission"]["email"] == "oia@hcmute.edu.vn"
        assert step["submission"]["portal_url"] is None
    docs = [r for r in nomination["document_requirements"] if r["stage"] == "nomination"]
    assert len(docs) == 7 and sum(r["conditional"] for r in docs) == 2
    assert not followup["document_requirements"]


def test_pilsen_routes_project_transfer_points_without_year_upgrade(tmp_path):
    field = reviewed_profiles()[109]["fields"]["transport"]
    assert field["status"] == "needs_confirmation"
    assert "B線至Florenc再轉巴士" in field["value"]
    assert "B線至Florenc轉C線到Hlavní Nádraží（中央車站），再搭火車" in field["value"]
    client = TestClient(create_app(tmp_path))
    response = client.get("/destination-profile", params={"home_school": HOME, "school": at(109).school_name})
    assert response.status_code == 200, response.text
    assert "B線至Florenc再轉巴士" in response.json()["transport_summary"]
    assert "2027路線／班次／票價" in response.json()["transport_summary"]


def test_dit_public_documents_and_wrong_program_templates_remain_pending(tmp_path):
    row = reviewed_documents()[101]
    assert len(row["requirements"]) == 6
    assert Counter(r["stage"] for r in row["requirements"]) == {"student_application": 5, "post_offer": 1}
    assert all(r["applicability_status"] == "needs_confirmation" for r in row["requirements"])
    assert not any(r["requirement"]["official_form_url"] for r in row["requirements"])
    client = TestClient(create_app(tmp_path))
    catalog = client.get("/application-center/catalog", params={"school": HOME, "target_school": at(101).school_name}).json()
    items = [r for r in catalog["items"] if r.get("stage")]
    assert len(items) == 6 and all(r["applicability_year"] for r in items)
    assert all(not r["official_form_verified"] for r in items)
    assert "EU/associated countries" in json.loads((BUNDLE / "overseas_sources/p114-r18-study-la.json").read_text())["content_academic_year"]
    assert "p114-r18-study-la" not in {e["source_id"] for r in reviewed_documents()[114]["requirements"] for e in r["evidence"]}
    assert reviewed_rows()[108]["fields"]["documents"]["status"] == "conflict"
    assert reviewed_profiles()[104]["fields"]["colleges"]["status"] == "needs_confirmation"
    assert reviewed_profiles()[104]["fields"]["degree_levels"]["status"] == "needs_confirmation"
    dorm = json.loads((BUNDLE / "overseas_sources/p35-r18-application-guide.json").read_text())
    assert dorm["content_applicability"] == "reference_only"
    assert "October, 2026" in dorm["text_pages"][0]
    assert "October 1, 2024" in dorm["text_pages"][2]


def test_link_queue_accounts_for_all_hrefs_and_keeps_checks_separate():
    report = json.loads((BUNDLE / "public-link-queue.json").read_text())
    gaps = json.loads((BUNDLE / "remaining-gaps.json").read_text())
    assert hashlib.sha256((BUNDLE / "remaining-gaps.json").read_bytes()).hexdigest() == report["input_sha256"]
    original = Counter((s["ccu_page"], l["url"], l["discovered_in_source"])
                       for s in gaps["schools"] for l in s["unrequested_discovered_links"])
    grouped = Counter((o["ccu_page"], o["url"], o["discovered_in_source"])
                      for c in report["candidates"] for o in c["occurrences"])
    assert original == grouped
    assert report["raw_href_count"] == sum(grouped.values())
    assert report["raw_href_count"] == report["unique_url_count"] + report["collapsed_href_count"]
    assert len({c["url"] for c in report["candidates"]}) == report["unique_url_count"]
    assert len(report["schools"]) == 55 and all(not r["public_sources_exhausted"] for r in report["schools"])
    for c in report["candidates"]:
        if c["source_content_read"]:
            review = c["content_review"]
            assert review and review["review_extent"] in {
                "necessary_policy_sections", "role_and_relevant_sections",
            }
            assert review["sha256"] and review["text_sha256"] and review["checked_at"]
            assert c["source_availability"] != "unrequested"
        else:
            assert c["source_content_read"] in (False, None)
        if c["disposition"] == "already_requested":
            assert c["source_availability"] != "unrequested" and c["source_content_read"] is None
        if "caslogin" in c["url"] or "?authTarget" in c["url"]:
            assert c["disposition"] == "excluded_auth_navigation"
        if "proton-exchange-membrane" in c["url"]:
            assert c["disposition"] == "excluded_research"
        for o in c["occurrences"]:
            source = json.loads((BUNDLE / "overseas_sources" / (o["discovered_in_source"] + ".json")).read_text())
            assert any(l["url"] == o["url"] for l in source["links"])
