"""Protect actual unread responses, obsolete forms, and visually verified policies."""

import hashlib
import json

from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


def source(sid):
    return json.loads((BUNDLE / "overseas_sources" / (sid + ".json")).read_text())


def test_uestc_image_policies_preserve_tuition_ambiguity_and_home_quota():
    p = at(27)
    fields = p.partner_exchange_details
    assert fields["exchange_duration"].status == "verified_current"
    assert "一學期為限" in fields["exchange_duration"].value
    assert (
        "保留" in fields["exchange_duration"].value
        and "打工" in fields["exchange_duration"].value
    )
    assert "開學一週內" in fields["insurance"].value
    assert fields["host_tuition"].status == "needs_confirmation"
    assert "費用由本校負擔" in fields["host_tuition"].value
    assert "不能改寫為普遍免學費" in fields["host_tuition"].value
    assert "不能指定宿舍" in fields["housing"].value
    assert fields["academic_calendar"].status == "missing"
    src = source("p27-r4-full-pdf")
    assert (
        hashlib.sha256((BUNDLE / src["bundled_file"]).read_bytes()).hexdigest()
        == src["sha256"]
    )
    assert src["sha256"] == source("p27-mirror")["sha256"]
    assert fields["application_deadline"].status == "conflict"
    assert "2026/11/30" in fields["application_deadline"].value


def test_ccnu_old_download_and_captcha_are_not_current_required_forms():
    fields = at(29).partner_exchange_details
    assert fields["application_forms"].status == "needs_confirmation"
    assert "驗證碼" in fields["application_forms"].value
    assert (
        "除簽名外" in fields["documents"].value
        and "學校公章" in fields["documents"].value
    )
    assert "不能擅加2016" in fields["documents"].value
    assert fields["language"].status == "missing"
    old = source("p29-r4-legacy-factsheet-web")
    assert old["content_applicability"] == "reference_only"
    assert "2016-2017学年" in old["text_pages"][0]
    blocked = source("p29-r4-legacy-attachment-blocked-web")
    assert blocked["access_result"] == "captcha_required"
    assert "http_status" not in blocked and "bundled_file" not in blocked
    assert (
        hashlib.sha256(blocked["web_extraction_response"].encode()).hexdigest()
        == blocked["sha256"]
    )


def test_anubis_http_200_and_empty_202_are_not_read_policy_successes():
    s = source("p111-r4-courses")
    assert s["http_status"] == 200 and s["access_result"] == "challenge_page"
    fields = at(111).partner_exchange_details
    assert fields["course_restrictions"].status == "missing"
    check = next(
        x
        for x in fields["course_restrictions"].source_checks
        if x.source_url == s["source_url"]
    )
    assert "未取得政策正文" in check.result and "HTTP 200" in check.result
    empty = source("p27-r4-hmt")
    assert empty["http_status"] == 202 and empty["access_result"] == "empty_response"
    assert not " ".join(empty["text_pages"]).strip()


def test_current_partner_portal_is_distinct_from_staff_and_freemover_routes():
    src = source("p111-r4-partner-form")
    assert "Partner universities (Students) 2026/2027" in src["text_pages"][0]
    assert "Taiwan" in src["text_pages"][0]
    form = at(111).partner_exchange_details["application_forms"]
    assert form.status == "needs_confirmation" and "完整欄位" in form.value
    assert at(111).partner_exchange_details["application_deadline"].status == "conflict"
    assert "2027" in at(111).partner_exchange_details["application_deadline"].value


def test_czech_current_government_and_partner_insurance_conflict_keep_scopes():
    field = at(111).partner_exchange_details["insurance"]
    assert (
        field.status == "conflict"
        and field.research_category == "unresolved_source_conflict"
    )
    assert "EUR60000" in field.value and "EUR400000" in field.value
    assert "Schengen" not in field.value or "分開" in field.value
    assert "2026-10-08" in field.value and "豁免" in field.value
    assert len(field.evidence) == 3
    assert (
        source("p111-r4-mfa-medical")["authority"] == "government_official_public_page"
    )


def test_full_read_ledger_does_not_turn_missing_values_into_nonpublication():
    ledger = json.loads((BUNDLE / "semantic-review-ledger.json").read_text())
    assert {24, 27, 29, 74, 111, 119} <= {x["ccu_page"] for x in ledger}
    for row in ledger:
        assert len(row["fields"]) == 17 and not row["complete_research_claimed"]
        for review in row["fields"].values():
            assert review["checked_source_ids"] and review["readable_source_ids"]
    fields = at(74).partner_exchange_details
    assert fields["housing"].status == "needs_confirmation"
    assert fields["documents"].status == "missing" and fields["documents"].value is None
    assert "已全文" in fields["documents"].research_note
    twinning = source("p74-r4-exchange-programs")
    assert (
        "UMass" in twinning["text_pages"][0]
        and "incoming" in twinning["content_review_note"]
    )
    assert at(119).partner_exchange_details["arrival"].status == "conflict"
    assert "2026" in at(119).partner_exchange_details["arrival"].value


def test_current_fact_rejects_captcha_as_policy_evidence(tmp_path, monkeypatch):
    import pytest

    import exchange_info.ccu_overseas as module

    rows = json.loads((BUNDLE / "overseas-reviewed-fields.json").read_text())
    field = next(r for r in rows if r["ccu_page"] == 29)["fields"]["application_forms"]
    evidence = next(e for e in field["evidence"] if "blocked-web" in e["source_id"])
    for row in rows:
        for f in row["fields"].values():
            f.update(value=None, status="missing", evidence=[])
    evidence["status"] = "verified_current"
    rows[0]["fields"]["application_forms"].update(
        value="Captcha", status="verified_current", evidence=[evidence]
    )
    (tmp_path / "overseas-reviewed-fields.json").write_text(json.dumps(rows))
    (tmp_path / "overseas_sources").mkdir()
    (tmp_path / "overseas_sources" / (evidence["source_id"] + ".json")).write_text(
        json.dumps(source(evidence["source_id"]))
    )
    monkeypatch.setattr(module, "BUNDLE", tmp_path)
    module.reviewed_rows.cache_clear()
    try:
        with pytest.raises(ValueError, match="Unread CCU access response"):
            module.reviewed_rows()
    finally:
        module.reviewed_rows.cache_clear()
