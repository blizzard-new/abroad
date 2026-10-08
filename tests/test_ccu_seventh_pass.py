"""Keep current public templates, program stages and home/host discrepancies scoped."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import requests

from exchange_info.ccu_overseas import reviewed_rows
from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.models import UniversityApplicationWorkflow
from exchange_info.storage import read_jsonl


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


def source(sid):
    return json.loads((BUNDLE / "overseas_sources" / f"{sid}.json").read_text())


def test_ryukoku_current_round_and_deadline_conflict_reach_all_projections():
    p = at(32)
    f = p.partner_exchange_details
    assert f["application_forms"].status == "verified_current"
    assert f["application_forms"].evidence[0].source_url.endswith("s_exchange_02.html")
    assert "Spring2027" in f["application_forms"].value
    assert f["application_deadline"].status == "conflict"
    assert "2026-11-09 23:59 JST" in f["application_deadline"].value
    assert "2026-11-15" in f["application_deadline"].value
    assert (
        p.partner_application_deadline
        == p.student_summary_zh.application_deadline
        == f["application_deadline"].value
    )
    assert "2026/11/15" in p.reference_data["partner_application_deadline"]
    assert p.field_evidence["partner_application_deadline"].status == "conflict"
    flow = next(
        x
        for x in read_jsonl(
            BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow
        )
        if x.school_name == p.school_name
    )
    assert "11-09" in flow.steps[4].timing and "11-15" in flow.steps[4].timing
    assert (
        flow.steps[4].deadline_at is None
        and not flow.steps[4].deadline_reminder_eligible
    )


def test_ryukoku_language_optional_certificate_and_internal_housing_conflicts():
    p = at(32)
    f = p.partner_exchange_details
    assert f["language"].status == f["documents"].status == "needs_confirmation"
    assert (
        "recommended" in p.language_review_note and "PBL500" in p.language_review_note
    )
    assert "ifavailable" in f["documents"].value
    assert p.field_evidence["partner_documents"].status == "needs_confirmation"
    assert (
        f["housing"].status
        == f["costs"].status
        == f["housing_deadline"].status
        == "conflict"
    )
    assert "1960" in f["costs"].value and "1980" in f["costs"].value
    assert (
        "前月5日" in f["housing_deadline"].value
        and "前月7日" in f["housing_deadline"].value
    )
    assert "再自行扣一次" in f["costs"].value
    assert all(c.scope_choice_required for c in p.language_conditions)
    assert source("p32-r7-jclp")["content_applicability"] == "reference_only"


def test_current_ryukoku_health_and_recommendation_forms_have_actual_requirements():
    h = source("p32-r7-health-form")
    r = source("p32-r7-recommendation-form")
    assert "another Pulmonary" in h["text_pages"][0]
    assert "Signature of Physician" in h["text_pages"][0]
    assert "this form is required" in r["text_pages"][0]
    assert len(r["text_pages"]) == 2
    for s in [h, r]:
        body = (BUNDLE / s["bundled_file"]).read_bytes()
        assert (
            body.startswith(b"%PDF-")
            and hashlib.sha256(body).hexdigest() == s["sha256"]
        )


def test_colabs_prior_consent_is_not_a_nomination_deadline_or_tao_acceptance():
    f = at(35).partner_exchange_details
    assert f["nomination_deadline"].status == "missing"
    assert f["nomination_deadline"].value is None
    assert f["application_deadline"].status == "verified_current"
    for text in [
        "2026-10-15 15:00 JST",
        "Oct1–Nov15",
        "由division",
        "不可申请前直接聯繫教授",
        "不等入學",
    ]:
        assert text in f["application_deadline"].value
    assert "PDF" in f["documents"].value
    assert f["eligibility"].status == "needs_confirmation"
    assert "masterdegree-seeking" in f["eligibility"].value
    assert "博士" in f["eligibility"].value
    assert source("p35-r7-deep-calendar")["content_applicability"] == "reference_only"
    assert "certificates" not in f["nomination_deadline"].reason


def test_tohoku_english_medium_alternative_and_program_specific_current_calendar():
    p = at(35)
    f = p.partner_exchange_details
    assert (
        "CERTIFICATE" in p.language_review_note
        and "Duolingo/EFSET/ITP" in p.language_review_note
    )
    assert f["language"].status == "needs_confirmation"
    assert f["academic_calendar"].status == "verified_current"
    assert (
        "08-04至06" in f["academic_calendar"].value
        and "IPLA" in f["academic_calendar"].value
    )
    assert "JYPE春欄2026" in f["academic_calendar"].value
    assert "750schoolhours" in f["course_restrictions"].value
    assert "ECTS等量不自轉TU" in f["course_restrictions"].value


def test_hokkaido_program_deadlines_degrees_and_scores_do_not_cross_scopes():
    p = at(37)
    f = p.partner_exchange_details
    assert p.quota == "共 5名"
    assert "50是全部partners" in f["program_scope"].value
    assert (
        "2026-09-25" in f["nomination_deadline"].value
        and "不把9/25套HUSTEP" in f["nomination_deadline"].value
    )
    assert (
        "2026-10-23" in f["application_deadline"].value
        and "2026-11-13" in f["application_deadline"].value
    )
    assert (
        "January2028onward" in p.language_review_note
        and "不套Spring2027" in p.language_review_note
    )
    assert (
        "JASSO" in f["eligibility"].value
        and "不當一般錄取條件" in f["eligibility"].value
    )
    assert f["course_restrictions"].status == "conflict"
    assert (
        "10.5" in f["course_restrictions"].value
        and "10hours" in f["course_restrictions"].value
    )
    assert "SRS純研究不修課無credits" in f["course_restrictions"].value
    assert f["application_forms"].status == "needs_confirmation"
    assert "2026Spring課表tentative" in f["application_forms"].value


def test_hokkaido_actual_form_signatures_and_fee_years_are_kept():
    f = at(37).partner_exchange_details
    assert f["documents"].status == "verified_current"
    assert "非語言教師" in f["documents"].value
    assert "Official Stamp" in source("p37-r7-enrollment-form")["text_pages"][0]
    assert "Signature" in source("p37-r7-consent-form")["text_pages"][0]
    assert f["housing_deadline"].status == "needs_confirmation"
    assert "midJanuary/midJuly" in f["housing_deadline"].value
    assert f["costs"].status == "conflict"
    for text in ["2300+tax", "4000", "2026.6.1", "50000"]:
        assert text in f["costs"].value
    assert "2026.6.1-" in source("p37-r7-dorm-fees-xlsx")["text_pages"][1]
    assert source("p37-r7-hustep")["final_url"] != source("p37-r7-hustep")["source_url"]


def test_legacy_xls_actual_current_study_plan_is_read_without_running_formulas(
    tmp_path,
):
    pytest.importorskip("xlrd")
    spec = importlib.util.spec_from_file_location(
        "ccu_xls_fetch",
        Path(__file__).resolve().parents[1] / "scripts/fetch_ccu_overseas_sources.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    s = source("p37-r7-studyplan-form")
    body = (BUNDLE / s["bundled_file"]).read_bytes()
    assert body.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")

    class Session:
        def get(self, url, **kwargs):
            response = requests.Response()
            response.status_code = 200
            response.url = url
            response._content = body
            response.headers["Content-Type"] = "application/vnd.ms-excel"
            return response

    result = module.fetch_public_source(
        {
            "source_id": "actual-hu-plan",
            "ccu_page": 37,
            "url": s["source_url"],
            "authority": "partner_official_public_document",
        },
        tmp_path,
        session=Session(),
    )
    assert result["status"] == "xls"
    assert result["sha256"] == s["sha256"]
    assert result["text_pages"] == s["text_pages"]
    assert "Spring Semester, 2027" in result["text_pages"][0]
    assert "cached formula results" in result["spreadsheet_extraction_note"]
    assert (tmp_path / "actual-hu-plan.xls").read_bytes() == body
    assert not (tmp_path / "actual-hu-plan.doc").exists()


def test_tokiwa_other_round_and_donga_outgoing_or_degree_pages_do_not_fill_spring():
    f = at(39).partner_exchange_details
    assert f["academic_calendar"].status == "needs_confirmation"
    assert "2027-04-02" in f["academic_calendar"].value
    assert f["course_restrictions"].status == "reference_only"
    assert f["application_forms"].status == "needs_confirmation"
    assert source("p39-r7-parttime-enpdf")["text_pages"][0].lstrip().startswith("1")
    assert "PART-TIME" in source("p39-r7-parttime-enpdf")["text_pages"][0]
    d = at(42).partner_exchange_details
    assert d["language"].status == "missing" and d["eligibility"].status == "missing"
    for sid in [
        "p42-r7-exchange",
        "p42-r7-exchange-ii",
        "p42-r7-academic",
        "p42-r7-application",
    ]:
        assert source(sid)["content_applicability"] == "reference_only"
    assert d["insurance"].status == d["costs"].status == "conflict"
    assert "30%off" in d["insurance"].value and "71920" in d["insurance"].value
    assert "最新" in d["visa"].value


def test_kyungsung_spring_brochure_mixed_fall_housing_is_not_a_current_invoice():
    f = at(54).partner_exchange_details
    assert f["housing"].status == f["costs"].status == "conflict"
    assert "Sept1–Dec21" in f["housing"].value
    assert "Feb24–Mar1" in f["arrival"].value and "Feb25±2–3days" in f["arrival"].value
    assert f["language"].status == "missing"
    assert f["application_forms"].status == "needs_confirmation"
    assert source("p54-r7-application")["content_applicability"] == "reference_only"
    assert (
        source("p54-r7-mirror-reread")["acquisition_mode"]
        == "reread_existing_bundled_official_pdf"
    )


def test_seventh_acquisition_and_review_do_not_claim_all_public_research_complete():
    ledger = json.loads((BUNDLE / "semantic-review-ledger.json").read_text())
    assert {32, 35, 37, 39, 42, 54}.issubset(x["ccu_page"] for x in ledger)
    assert len(ledger) >= 24 and all(not x["complete_research_claimed"] for x in ledger)
    r = next(x for x in ledger if x["ccu_page"] == 32)
    assert (
        "p32-r7-spot-instructions"
        in r["fields"]["documents"]["partially_reviewed_source_ids"]
    )
    c = json.loads((BUNDLE / "seventh-pass-changes.json").read_text())
    assert c["new_source_count"] == 72 and c["new_network_acquisition_records"] == 65
    assert len(c["reread_existing_bundled_sources"]) == 7
    assert len(c["changes"]) == 60
    assert sum(x["previous_status"] == "missing" for x in c["changes"]) == 29
    assert len(reviewed_rows()) == 55
