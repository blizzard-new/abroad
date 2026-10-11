"""Document clauses, current course exclusions, and public access boundaries."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents, verified_form_urls
from exchange_info.ccu_overseas import reviewed_rows
from exchange_info.ccu_profile import reviewed_profiles
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def read(name):
    return json.loads((BUNDLE / name).read_text())


def at(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def test_corrected_clauses_point_to_actual_requirement_pages():
    report = read("nineteenth-document-evidence-corrections.json")
    assert report["correction_count"] == len(report["corrections"]) == 19
    documents = reviewed_documents()
    for correction in report["corrections"]:
        item = documents[correction["ccu_page"]]["requirements"][correction["requirement_index"]]
        evidence = item["evidence"][0]
        source = read("overseas_sources/" + evidence["source_id"] + ".json")
        actual = " ".join(" ".join(source["text_pages"][p - 1].split()) for p in evidence["source_pages"])
        excerpt = " ".join(evidence["excerpt"].split())
        assert excerpt in actual
        assert correction["required_clause"] in excerpt
        assert evidence["source_pages"] == correction["after"]["source_pages"]
    assert all(r["evidence"][0]["source_pages"] == [15] for r in documents[34]["requirements"])


def test_nagoya_language_and_jasso_conditions_are_not_universal():
    requirements = reviewed_documents()[34]["requirements"]
    language = requirements[4]
    assert language["conditional"]
    assert "exempt" in language["evidence"][0]["excerpt"].casefold()
    financial = requirements[9]
    assert financial["conditional"] and "未獲JASSO提名仍計畫" in financial["requirement"]["name"]
    assert "even if they are not nominated" in financial["evidence"][0]["excerpt"]
    assert "500,000" in financial["evidence"][0]["excerpt"]


def test_sungshin_and_tianjin_do_not_invent_english_conditions():
    docs = reviewed_documents()
    enrolment = docs[49]["requirements"][3]
    assert "未明定語言" in enrolment["requirement"]["name"]
    photo = docs[49]["requirements"][7]
    assert "線上上傳" in photo["requirement"]["name"]
    assert "online" in photo["evidence"][0]["excerpt"].casefold()
    cv = next(r for r in docs[24]["requirements"] if "履歷" in r["requirement"]["name"])
    assert "未明定語言" in cv["requirement"]["name"]


def test_presidency_inbound_form_projects_real_signers_and_pending_year(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-center/catalog", params={"school": HOME, "target_school": at(80).school_name})
    assert response.status_code == 200, response.text
    items = [r for r in response.json()["items"] if r.get("stage")]
    assert len(items) == 6 and all(r["applicability_status"] == "needs_confirmation" for r in items)
    application = items[0]
    assert application["official_form_verified"] and application["download_available"]
    assert "6818985ddb4fe1746442333.pdf" in application["official_form_url"]
    assert "6818987ff360e1746442367.pdf" not in str(items)
    assert len(application["signatures"]) == 2
    assert not at(80).quota and at(80).quota_status == "not_published"


def test_dorm_documents_and_jis_card_keep_later_stages():
    docs = reviewed_documents()
    tb = docs[43]["requirements"][-1]
    intent = docs[107]["requirements"][-1]
    for item in (tb, intent):
        assert item["stage"] == "post_offer" and item["conditional"]
        assert item["applicability_status"] == "needs_confirmation"
    assert len(intent["requirement"]["signatures"]) == 2
    assert intent["requirement"]["official_form_url"] in verified_form_urls()
    assert docs[109]["requirements"][1]["stage"] == "post_offer"


def test_tbu_current_course_exclusion_does_not_publish_course_capacity_as_quota():
    field = reviewed_rows()[108]["fields"]["course_restrictions"]
    assert field["status"] == "verified_current"
    assert "AE8SV" in field["value"] and "不開" in field["value"]
    assert "1PE3E" in field["value"] and "Master" in field["value"]
    assert "15" in field["value"] and "課程" in field["value"]
    assert at(108).quota != "15"
    assert reviewed_profiles()[108]["fields"]["colleges"]["status"] == "missing"
    manual = read("overseas_sources/p108-r19-manual-preview.json")
    assert manual["content_applicability"] == "reference_only"
    assert "2025/2026" in manual["text_pages"][7]
    assert not any(r["requirement"].get("official_form_url") == manual["source_url"]
                   for r in reviewed_documents()[108]["requirements"])
    assert reviewed_rows()[108]["fields"]["documents"]["status"] == "conflict"


def test_hufs_old_graduate_limit_conflicts_without_overwriting_current_source():
    field = reviewed_rows()[47]["fields"]["course_restrictions"]
    assert field["status"] == "conflict"
    assert "12" in field["value"] and "20" in field["value"]
    source = read("overseas_sources/p47-r19-course-registration.json")
    assert source["content_applicability"] == "reference_only"
    assert "Fall2026" in source["content_academic_year"]


def test_password_prompt_is_an_access_limit_without_login(tmp_path):
    spec = importlib.util.spec_from_file_location("ccu_fetch_r19", Path(__file__).resolve().parents[1] / "scripts/fetch_ccu_overseas_sources.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    body = b'<html><form class="post-password-form"><input type="password"></form></html>'
    calls = []
    url = "https://example.edu/exchange/form"
    response = SimpleNamespace(content=body, text=body.decode(), url=url, status_code=200,
                               headers={"Content-Type": "text/html"}, raise_for_status=lambda: None)

    def get(*args, **kwargs):
        calls.append((args, kwargs))
        return response

    result = module.fetch_public_source({"source_id": "fixture", "ccu_page": 35, "url": url,
                                         "authority": "partner_official_public_page"}, tmp_path,
                                        session=SimpleNamespace(get=get))
    assert len(calls) == 1 and result["access_result"] == "password_protected"
    assert "No password, login or bypass" in result["review_note"]
    actual = read("overseas_sources/p35-r19-339169bb82.json")
    assert actual["access_result"] == "password_protected"
    gaps = read("remaining-gaps.json")
    source = next(s for r in gaps["schools"] for s in r["checked_sources"] if s["source_id"] == actual["source_id"])
    assert source["review_state"] == "access_limited_not_policy_content"


def test_bnu_and_bordeaux_housing_body_years_remain_reference():
    for sid, year in [("p10-r19-977d3343c8", "2019"), ("p85-r19-cd9ffae29e", "2022")]:
        source = read("overseas_sources/" + sid + ".json")
        assert source["content_applicability"] == "reference_only"
        assert year in source["content_academic_year"]
        assert not any(r["requirement"].get("official_form_url") == source["source_url"]
                       for row in reviewed_documents().values() for r in row["requirements"])


def test_reviewed_same_content_aliases_have_actual_acquisition_proof():
    report = read("public-link-queue.json")
    assert report["review_input_sha256"] == hashlib.sha256((BUNDLE / "public-link-reviews.json").read_bytes()).hexdigest()
    reviews = read("nineteenth-source-review.json")
    assert reviews["acquisition_count"] == len(reviews["source_reviews"]) == 99
    assert reviews["new_source_count"] == 77
    for candidate in report["candidates"]:
        if candidate["disposition"] == "same_content_reviewed":
            review = candidate["content_review"]
            source = read("overseas_sources/" + review["source_id"] + ".json")
            assert review["sha256"] == source["sha256"]
            assert review["text_sha256"] == source["text_sha256"]
            assert candidate["source_availability"] != "unrequested"
