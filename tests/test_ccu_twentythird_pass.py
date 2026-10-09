"""Keep public forms, their legal versions and later requirements separate."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info import ccu_overseas, ccu_profile
from exchange_info.api import create_app
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def read(name):
    return json.loads((BUNDLE / name).read_text())


def partner(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def test_arc_documents_are_later_conditional_and_not_initial_exchange_forms(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-workflow", params={"home_school": HOME, "school": partner(45).school_name})
    assert response.status_code == 200
    steps = response.json()["steps"]
    initial = next(s for s in steps if s["phase"] == "合作校申請")
    assert not any("ARC" in r["name"] for r in initial["document_requirements"])
    life = next(s for s in steps if s["phase"] == "合作校行前與生活")
    arc = [r for r in life["document_requirements"] if "ARC" in r["name"]]
    assert len(arc) == 7 and all(r["conditional"] for r in arc)
    assert all(r["stage"] == "post_offer" for r in arc)
    assert all(r["applicability_status"] == "needs_confirmation" for r in arc)
    form = next(r for r in arc if "統合" in r["name"])
    assert form["official_form_url"] == "https://www.hikorea.go.kr/board/BoardApplicationListR.pt?page=1"
    assert not form["official_form_verified"]  # a form index is not a direct PDF
    assert not form["stamps"] and "擇一" in form["signatures"][0]
    assert "非全體配偶／父母必簽" in form["condition"]
    assert "六個月" in next(r for r in arc if "35×45" in r["name"])["condition"]


def test_latest_public_form_and_undated_school_mirror_are_different_versions():
    current = read("overseas_sources/p45-r23-government-integrated-form.json")
    mirror = read("overseas_sources/p45-r23-84928111ff.json")
    assert current["sha256"] != mirror["sha256"]
    assert "2022. 4. 12." in current["text_pages"][0]
    assert "2022. 4. 12." not in mirror["text_pages"][0]
    assert current["content_applicability"] == mirror["content_applicability"] == "needs_confirmation"
    assert current["public_download_method"] == "POST"
    assert current["public_file_view_url"].startswith("https://www.hikorea.go.kr/board/")
    assert hashlib.sha256((BUNDLE / current["bundled_file"]).read_bytes()).hexdigest() == current["sha256"]


def test_old_dorm_guide_and_past_jype_samples_cannot_be_current_checklists():
    dorm = read("overseas_sources/p45-r23-46f871a492.json")
    sample = read("overseas_sources/p35-r23-ae2833c5b0.json")
    assert len(dorm["text_pages"]) == 10 and "2021-2nd semester" in dorm["text_pages"][0]
    assert "These are the samples from JYPE students in the past." in " ".join(sample["text_pages"][0].split())
    assert dorm["content_applicability"] == sample["content_applicability"] == "reference_only"
    field = ccu_overseas.reviewed_rows()[45]["fields"]["housing"]
    assert field["status"] == "conflict"
    assert next(e for e in field["evidence"] if e["source_id"] == dorm["source_id"])["status"] == "reference_only"


def test_registration_fee_is_not_tuition_and_current_visa_is_not_arc_template():
    fields = ccu_overseas.reviewed_rows()[45]["fields"]
    assert fields["visa"]["status"] == "needs_confirmation"
    assert any(e["status"] == "verified_current" for e in fields["visa"]["evidence"])
    assert fields["costs"]["status"] == "conflict"
    assert "30,000" in fields["costs"]["value"] and "35,000" in fields["costs"]["value"]
    assert "不是交換申請平台收費" in fields["costs"]["value"]
    assert fields["host_tuition"]["status"] == "needs_confirmation"
    assert "Visiting" in fields["host_tuition"]["value"]
    source = read("overseas_sources/p45-r23-follow-11e35a3763.json")
    assert "2025" in source["text_pages"][0] and "35,000 won" in source["text_pages"][0]


def test_current_tuition_and_semp_scope_reach_partner_api(tmp_path):
    client = TestClient(create_app(tmp_path))
    result = client.get("/student-dashboard", params={"school": HOME})
    assert result.status_code == 200
    rows = {p["school_name"]: p for p in result.json()["partner_universities"]}
    current = rows[partner(106).school_name]["partner_exchange_details"]["host_tuition"]
    assert current["status"] == "verified_current"
    assert current["evidence"][0]["source_pages"] == [3]
    assert "No tuition" in current["evidence"][0]["excerpt"]
    zhaw = rows[partner(103).school_name]["partner_exchange_details"]["host_tuition"]
    assert zhaw["status"] == "needs_confirmation" and "SEMP/Erasmus+" in zhaw["value"]
    assert "CCU" in zhaw["value"] and "是否" in zhaw["value"]


def test_student_library_fee_exceptions_do_not_apply_to_all_users():
    profiles = ccu_profile.reviewed_profiles()
    assert "PrivateBorrower" in profiles[89]["fields"]["campus_life"]["value"]
    assert "externaluser" in profiles[100]["fields"]["campus_life"]["value"]
    fields = ccu_overseas.reviewed_rows()
    assert "每月必繳" in fields[89]["fields"]["costs"]["value"]
    assert "FHNW成員" in fields[104]["fields"]["costs"]["value"]
    assert "指定館" in fields[104]["fields"]["costs"]["value"]


@pytest.mark.parametrize("module,name,function", [
    (ccu_overseas, "overseas-reviewed-fields.json", ccu_overseas.reviewed_rows),
    (ccu_profile, "profile-reviewed-fields.json", ccu_profile.reviewed_profiles),
])
def test_a_current_field_cannot_be_supported_only_by_noncurrent_evidence(tmp_path, monkeypatch, module, name, function):
    rows = read(name)
    field = next(f for r in rows for f in r["fields"].values() if f["status"] == "verified_current")
    for evidence in field["evidence"]:
        evidence["status"] = "needs_confirmation"
    (tmp_path / name).write_text(json.dumps(rows, ensure_ascii=False))
    monkeypatch.setattr(module, "BUNDLE", tmp_path)
    function.cache_clear()
    try:
        with pytest.raises(ValueError, match="[Cc]urrent"):
            function()
    finally:
        function.cache_clear()


def collector():
    spec = importlib.util.spec_from_file_location("ccu_public_collector", Path(__file__).resolve().parents[1] / "scripts/fetch_ccu_overseas_sources.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicFileClient:
    def __init__(self, body):
        self.body, self.calls = body, []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return type("Response", (), {"raise_for_status": lambda self: None})()

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return type("Response", (), {"url": url, "status_code": 200, "headers": {"Content-Type": "text/html"}, "content": self.body, "raise_for_status": lambda self: None})()


def file_request():
    return {"source_id": "public-form", "ccu_page": 45, "url": "https://www.hikorea.go.kr/fileNewExistsChkAjax.pt", "authority": "government_official_public_document", "public_download_method": "POST", "public_download_parameters": {"spec": "pt", "dir": "info", "apndFileNm": "down-1-1-2.pdf", "oriFileNm": "통합신청서(신고서).pdf"}}


def test_public_file_button_post_extracts_pdf_even_with_html_content_type(tmp_path):
    source = read("overseas_sources/p45-r23-government-integrated-form.json")
    body = (BUNDLE / source["bundled_file"]).read_bytes()
    client = PublicFileClient(body)
    result = collector().fetch_public_source(file_request(), tmp_path, client)
    assert result["status"] == "pdf" and len(result["text_pages"]) == 1
    assert result["sha256"] == source["sha256"]
    assert [r[0] for r in client.calls] == ["GET", "POST"]
    assert client.calls[1][2]["data"] == file_request()["public_download_parameters"]
    assert "verify" not in client.calls[1][2]


@pytest.mark.parametrize("change", ["another_host", "personal_data", "another_method"])
def test_public_download_support_does_not_allow_general_post_or_application_data(tmp_path, change):
    request = file_request()
    if change == "another_host":
        request["url"] = "https://example.invalid/application"
    elif change == "personal_data":
        request["public_download_parameters"]["student_name"] = "unused"
    else:
        request["public_download_method"] = "PUT"
    client = PublicFileClient(b"")
    result = collector().fetch_public_source(request, tmp_path, client)
    assert result["status"] == "fetch_failed" and "Unsupported" in result["error"]
    assert not client.calls


def test_source_review_freezes_prior_files_and_does_not_claim_unread_targets():
    report = read("twentythird-source-review.json")
    assert report["acquisition_count"] == len(report["source_reviews"]) == 21
    assert report["new_source_count"] == 13 and len(report["same_body_rechecks"]) == 2
    assert len(report["prior_snapshot_hashes"]) == 943
    for sid, digest in report["prior_snapshot_hashes"].items():
        assert hashlib.sha256((BUNDLE / "overseas_sources" / (sid + ".json")).read_bytes()).hexdigest() == digest
    scope = read("twentythird-link-scope-screening.json")["reviews"]
    assert len(scope) == 6 and all(r["source_content_read"] is False for r in scope)
    assert all(r["review_extent"] == "link_scope_screening_only" for r in scope)
    assert not report["body_policy_newest_verified"]
