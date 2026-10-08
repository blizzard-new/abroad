"""Real paired scopes, year-labelled pending documents and clean library sources."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from test_ccu_semantics import client_for

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents, verified_form_urls
from exchange_info.ccu_profile import reviewed_profiles
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.content_governance import workflow_content_hash
from exchange_info.qualification_scopes import coupled_academic_scope_matches
from exchange_info.storage import load_bundled_application_workflows


def at(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


@pytest.mark.parametrize("college,degree,allowed", [
    ("教育學院", "大學部", True), ("教育學院", "碩士班", True),
    ("教育學院", "博士班", True), ("法學院", "碩士班", True),
    ("法學院", "大學部", False), ("法學院", "博士班", False),
    ("管理學院", "碩士班", False),
])
def test_nagoya_pairs_in_both_real_apis(tmp_path, college, degree, allowed):
    partner = at(34)
    assert len(partner.program_options) == 2
    assert coupled_academic_scope_matches(partner, college, degree) is allowed
    client = client_for(tmp_path)
    common = {"college": college, "degree_level": degree, "academic_gpa": 3.5, "academic_score": 85}
    response = client.post("/advisor/plan", json=dict(
        school_name=HOME, target_school=partner.school_name, **common
    ))
    assert response.status_code == 200, response.text
    target = response.json()["target_match"]
    assert ("符合目前學制" in target["reasons"]) is allowed
    if not allowed:
        assert any("配對不符" in reason for reason in target["blocking_reasons"])
    response = client.post("/application-plan/evaluate", json=dict(
        home_school=HOME, preferences=[{"rank": 1, "school_name": partner.school_name}], **common
    ))
    assert response.status_code == 200, response.text
    checks = {r["code"]: r for r in response.json()["choices"][0]["checks"]}
    assert checks["degree_level"]["status"] == ("pass" if allowed else "fail")
    assert "配對" in checks["degree_level"]["detail"]
    changed = partner.model_copy(deep=True)
    changed.field_evidence["colleges"].status = "needs_confirmation"
    assert coupled_academic_scope_matches(changed, college, degree) is None


def test_pending_documents_render_without_promoting_completeness(tmp_path):
    docs = reviewed_documents()
    assert len(docs) == 26 and sum(len(r["requirements"]) for r in docs.values()) == 197
    client = TestClient(create_app(tmp_path))
    for page, count in [(98, 5), (102, 10), (23, 4)]:
        response = client.get("/application-center/catalog", params={
            "school": HOME, "target_school": at(page).school_name
        })
        assert response.status_code == 200, response.text
        catalog = response.json()
        items = [r for r in catalog["items"] if r.get("stage")]
        assert len(items) == count and catalog["workflow_review_status"] == "legacy"
        assert all(r["applicability_year"] and r["applicability_note"] for r in items)
        assert all(r["needs_confirmation"] for r in items)
        assert docs[page]["list_completeness"] == "partial_not_exhaustive"
        if page == 98:
            assert len([r for r in items if r["official_form_verified"]]) == 2
            assert all(r["download_available"] for r in items if r["official_form_verified"])
            assert all(r["applicability_status"] == "needs_confirmation" for r in items if r["official_form_verified"])
            assert len([r for r in items if r["applicability_status"] == "verified_current"]) == 2
            room = next(r for r in items if "Accommodation" in r["name"])
            assert not room["conditional"] and "不保證" in room["name"]
        if page == 102:
            la = next(r for r in items if "Learning Agreement" in r["name"])
            assert la["official_form_url"].endswith("Learning-Agreement-Incoming.pdf")
            assert not la["official_form_verified"] and not la["download_available"]
            assert la["official_form_url"] not in verified_form_urls()
        if page == 23:
            assert all(r["conditional"] and r["stage"] == "conditional_program" for r in items)
            assert not any(r["official_form_url"] for r in items)


def test_hcmute_mother_compiles_nomination_bundle(tmp_path):
    row = reviewed_documents()[68]
    assert len(row["requirements"]) == 7
    assert sum(r["conditional"] for r in row["requirements"]) == 2
    assert all(r["stage"] == "nomination" for r in row["requirements"])
    client = TestClient(create_app(tmp_path))
    flow = client.get("/application-workflow", params={
        "home_school": HOME, "school": at(68).school_name
    }).json()
    assert "母校彙整" in flow["steps"][4]["title"]
    assert len([r for r in flow["steps"][3]["document_requirements"] if r["stage"] == "nomination"]) == 7
    assert not flow["steps"][4]["document_requirements"]


def test_dntu_library_training_hours_and_cs1_scope_are_separate(tmp_path):
    profiles = reviewed_profiles()
    life = profiles[71]["fields"]["campus_life"]
    assert life["status"] == "needs_confirmation" and "訓練" in life["value"]
    assert all("library" in e["source_id"] for e in life["evidence"])
    assert profiles[71]["fields"]["city"]["status"] == "needs_confirmation"
    hours = json.loads((BUNDLE / "seventeenth-library-hours-conflict.json").read_text())
    assert hours["status"] == "conflict" and not hours["mapped_as_definite_hours"]
    assert "19/01/2026" in hours["evidence"][2]["excerpt"]
    assert "08 giờ 00" in hours["evidence"][1]["excerpt"]
    transport = profiles[68]["fields"]["transport"]
    assert "僅CS1" in transport["value"] and "不推成接機" in transport["value"]
    client = TestClient(create_app(tmp_path))
    guide = client.get("/destination-profile", params={
        "home_school": HOME, "school": at(71).school_name
    }).json()
    assert "訓練" in guide["campus_life_summary"]
    assert "07:30" not in guide["campus_life_summary"]


def test_metadata_is_hash_bound_and_existing_school_data_remains_default():
    workflows = load_bundled_application_workflows()
    ccu = next(r for r in workflows if r.home_university == HOME and r.school_name == at(98).school_name)
    changed = ccu.model_copy(deep=True)
    changed.steps[4].document_requirements[0].applicability_note += " changed"
    assert workflow_content_hash(changed) != workflow_content_hash(ccu)
    assert all(r.applicability_status is None for w in workflows if w.home_university != HOME
               for step in w.steps for r in step.document_requirements)


def test_per_school_gap_inventory_distinguishes_mapping_from_exhaustion():
    report = json.loads((BUNDLE / "remaining-gaps.json").read_text())
    assert report["school_count"] == 55 and report["source_count"] == 697
    for name, expected in report["input_sha256"].items():
        assert hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest() == expected
    for sid, expected in report["input_source_json_sha256"].items():
        assert hashlib.sha256((BUNDLE / "overseas_sources" / (sid + ".json")).read_bytes()).hexdigest() == expected
    assert all(not r["public_sources_exhausted"] for r in report["schools"])
    assert all(r["checked_sources"] for r in report["schools"])
    nagoya = next(r for r in report["schools"] if r["ccu_page"] == 34)
    assert "college_scope" not in nagoya["gaps"] and "degree_scope" not in nagoya["gaps"]
    assert len(nagoya["academic_scope_options"]) == 2
    mapped = {e["source_id"] for name in ["profile-reviewed-fields.json", "overseas-reviewed-fields.json"]
              for row in json.loads((BUNDLE / name).read_text())
              for field in row["fields"].values() for e in field["evidence"]}
    mapped |= {e["source_id"] for row in json.loads((BUNDLE / "partner-document-requirements.json").read_text())
               for item in row["requirements"] for e in item["evidence"]}
    for row in report["schools"]:
        for source in row["checked_sources"]:
            actual = json.loads((BUNDLE / "overseas_sources" / (source["source_id"] + ".json")).read_text())
            limited = actual.get("access_result") in {"empty_response", "challenge_page", "captcha_required", "unrelated_content_anomaly"}
            assert (source["review_state"] == "mapped_field_evidence_not_whole_document_completion") is (source["source_id"] in mapped and not limited)
            if source["review_state"] == "content_not_obtained":
                assert not any(actual.get("text_pages", []))
            if limited:
                assert source["review_state"] == "access_limited_not_policy_content"
            if actual.get("access_result") == "public_legacy_content":
                assert source["review_state"] != "access_limited_not_policy_content"


def test_discovered_general_sources_keep_program_and_year_limits():
    old = json.loads((BUNDLE / "overseas_sources/p23-r17-discovery-1.json").read_text())
    assert old["content_applicability"] == "reference_only"
    assert "2018-2019" in old["text_pages"][0]
    tbu = json.loads((BUNDLE / "overseas_sources/p108-r17-discovery-2.json").read_text())
    assert tbu["content_applicability"] == "needs_confirmation"
    assert "freemovers" in tbu["text_pages"][0]
    assert reviewed_profiles()[108]["fields"]["colleges"]["status"] == "missing"
    profile = reviewed_profiles()[109]["fields"]
    for key, sid in [("transport", "p109-r17-discovery-3"), ("campus_life", "p109-r17-discovery-4")]:
        assert profile[key]["status"] == "needs_confirmation"
        assert profile[key]["evidence"][0]["source_id"] == sid
        source = json.loads((BUNDLE / "overseas_sources" / (sid + ".json")).read_text())
        assert len(source["text_pages"]) == 1
        assert hashlib.sha256((BUNDLE / source["bundled_file"]).read_bytes()).hexdigest() == source["sha256"]
    hcmut = next(w for w in load_bundled_application_workflows() if
                 w.home_university == HOME and w.school_name == at(67).school_name)
    passport = next(r for s in hcmut.steps for r in s.document_requirements if r.name == "護照copy")
    assert passport.applicability_note is None and passport.stamps == []


def test_fetcher_flags_literal_anomalous_footer_before_html_cleanup(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "ccu_fetch_r17", Path(__file__).resolve().parents[1] / "scripts/fetch_ccu_overseas_sources.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    body = b"<html><main>Official-looking service</main><footer>phpshells.net</footer></html>"
    url = "https://example.edu/service"
    response = SimpleNamespace(content=body, text=body.decode(), url=url,
                               status_code=200, headers={"Content-Type": "text/html"},
                               raise_for_status=lambda: None)
    session = SimpleNamespace(get=lambda *args, **kwargs: response)
    result = module.fetch_public_source({"source_id": "fixture", "ccu_page": 71,
                                        "url": url, "authority": "partner_official_public_page"},
                                       tmp_path, session=session)
    assert result["access_result"] == "unrelated_content_anomaly"
    assert result["sha256"] == hashlib.sha256(body).hexdigest()
    assert "phpshells.net" not in result["text_pages"][0]
    assert "do not map" in result["review_note"]
