"""Check source semantics, real attachments, and stage/campus boundaries."""

import hashlib
import importlib.util
import json
from pathlib import Path

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


def flow(page):
    return next(
        f
        for f in read_jsonl(
            BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow
        )
        if f.school_name == at(page).school_name
    )


def test_colabs_request_submission_is_distinct_from_result_batch_and_tao():
    p = at(35)
    f = p.partner_exchange_details["application_deadline"]
    assert f.status == "conflict"
    for phrase in [
        "提交窗口2026-07-01至10-15 15:00 JST",
        "不是已核必須10/15取得同意",
        "EarlyNovember",
        "舊Q5",
        "TAO Oct1–Nov15",
    ]:
        assert phrase in f.value
    assert (
        p.partner_application_deadline
        == p.student_summary_zh.application_deadline
        == f.value
    )
    assert p.field_evidence["partner_application_deadline"].status == "conflict"
    assert "EarlyNovember" in flow(35).steps[4].timing
    assert flow(35).steps[4].deadline_at is None
    assert not flow(35).steps[4].deadline_reminder_eligible
    assert source("p35-r8-colabs-procedures")["content_applicability"] == "conflict"
    assert p.partner_exchange_details["nomination_deadline"].status == "missing"


def test_ryukoku_historical_grey_list_does_not_create_current_jlpt_requirement():
    p = at(32)
    home = p.field_evidence["partner_documents"]
    assert home.status == "reference_only"
    assert home.academic_year is None and home.application_round is None
    assert home.excerpt is None and home.reference_excerpt
    assert p.application_info is None
    assert p.partner_exchange_details["documents"].status == "verified_current"
    assert "ifavailable" in p.partner_exchange_details["documents"].value
    assert "不是本輪必有" in p.partner_exchange_details["documents"].value
    assert "不能當本期JLPT必附" in p.partner_exchange_details["language"].value


def test_kmutt_calendar_conflict_reaches_generic_and_guide_projections():
    p = at(61)
    f = p.partner_exchange_details["academic_calendar"]
    assert f.status == "conflict"
    assert "2027-01-13至05-28" in f.value and "01-11至05-15" in f.value
    assert "registrationday" in f.value and "SIT研究所" in f.value
    assert p.semester_dates == f.value
    assert "2027/01/11" in p.reference_data["semester_dates"]
    assert p.field_evidence["semester_dates"].status == "conflict"
    assert "Jan13–May28" in p.partner_exchange_details["exchange_duration"].value
    assert len(source("p61-r8-calendar2026")["text_pages"]) == 13
    assert (
        "Announced on April 7, 2026" in source("p61-r8-calendar2026")["text_pages"][10]
    )


def test_kmutt_incoming_forms_and_alternative_english_do_not_use_outgoing_form():
    f = at(61).partner_exchange_details
    assert f["application_forms"].status == "needs_confirmation"
    assert "OutgoingExchangeApplicationForm" in f["application_forms"].value
    assert source("p61-r8-learning-agreement")["access_result"] == "empty_response"
    assert "TOEIC550" in f["language"].value and "35–45" in f["language"].value
    assert f["nomination_deadline"].status == "needs_confirmation"
    assert "30August" in f["nomination_deadline"].value
    assert "most改all" in f["host_tuition"].value
    assert "SoA+D" in f["documents"].value


def test_veltech_fact_sheet_is_not_application_form_and_costs_and_dates_conflict():
    f = at(77).partner_exchange_details
    assert f["application_forms"].status == "needs_confirmation"
    assert (
        "FACTSHEET" in f["application_forms"].value
        and "href=#" in f["application_forms"].value
    )
    assert f["application_deadline"].status == f["costs"].status == "conflict"
    assert (
        "Nov1" in f["application_deadline"].value
        and "Oct1" in f["application_deadline"].value
    )
    for phrase in ["INR12000", "INR15000", "EUR150", "EUR250"]:
        assert phrase in f["costs"].value
    assert "any one department" in source("p77-r8-faq")["text_pages"][0]
    assert "不設分數最低" in f["language"].value
    assert "7workingdays" in f["arrival"].value
    assert flow(77).steps[4].deadline_at is None


def test_asbu_main_and_cyprus_and_graduate_calendars_are_kept_separate():
    f = at(105).partner_exchange_details
    assert f["academic_calendar"].status == "verified_current"
    for phrase in [
        "本科授課2027-02-08至06-04",
        "06-05至19",
        "研究所",
        "06-07至18",
        "Cyprus",
    ]:
        assert phrase in f["academic_calendar"].value
    assert (
        f["nomination_deadline"].status
        == f["application_deadline"].status
        == "conflict"
    )
    assert (
        "2026-11-15" in f["application_deadline"].value
        and "Nov30" in f["application_deadline"].value
    )
    assert "Spring Period" in source("p105-r8-flyer")["text_pages"][2]
    assert "NORTH CYPRUS CAMPUS" in source("p105-r8-calendar-cyprus")["text_pages"][0]
    assert (
        "不能" in f["application_deadline"].value
        or "不選" in f["application_deadline"].value
    )
    assert flow(105).steps[4].deadline_at is None


def test_asbu_recommended_language_conditional_medical_and_old_permit_cost():
    p = at(105)
    f = p.partner_exchange_details
    assert f["language"].status == f["documents"].status == "needs_confirmation"
    assert "強烈建議B1" in f["language"].value and "不收IELTS" in f["language"].value
    assert "僅ifdisability" in f["documents"].value
    assert "810TRY供參考" in f["costs"].value
    assert "2014circular" in f["insurance"].value and "台灣不在" in f["insurance"].value
    assert all(c.scope_choice_required for c in p.language_conditions)
    assert "does not provide accommodation" in source("p105-r8-flyer")["text_pages"][10]


def test_strasbourg_current_deadlines_and_blank_learning_agreement():
    f = at(87).partner_exchange_details
    assert (
        f["nomination_deadline"].status
        == f["application_deadline"].status
        == "verified_current"
    )
    assert "2026-06-03至10-01" in f["application_deadline"].value
    assert f["application_forms"].status == "needs_confirmation"
    assert "202_-202_" in f["application_forms"].value
    assert "50%課同一department" in f["course_restrictions"].value
    s = source("p87-r8-learning-contract-pdf")
    assert len(s["text_pages"]) == 3
    assert s["source_url"].startswith("https://seafile.unistra.fr/d/")
    assert (BUNDLE / s["bundled_file"]).read_bytes().startswith(b"%PDF-")
    assert "Institutional coordinator" in s["text_pages"][0]


def test_strasbourg_housing_individual_deadline_and_apl_exceptions_are_not_guarantees():
    f = at(87).partner_exchange_details
    assert "individual非exchange" in f["housing_deadline"].value
    assert "externalpartner" in f["housing"].value
    assert "EUR201–600" in f["costs"].value
    assert "職業培訓contract" in f["costs"].value
    assert "一般實習" not in f["costs"].value
    assert "mutuelle" in f["insurance"].value
    assert "百分百報销" in f["insurance"].value
    assert source("p87-r8-housing-guide")["text_pages"][1].startswith(
        "Édition mai 2026"
    )


def test_xiamen_real_docx_and_captcha_keep_home_extra_documents():
    f = at(23).partner_exchange_details
    assert "2026-03-03" in f["program_scope"].value
    assert f["application_deadline"].status == "needs_confirmation"
    assert "仍交六項" in f["documents"].value and "≥800字" in f["documents"].value
    s = source("p23-r8-health-form")
    assert s["status"] == "docx"
    assert (BUNDLE / s["bundled_file"]).read_bytes().startswith(b"PK")
    assert source("p23-r8-physical-exam-record")["access_result"] == "captcha_required"
    assert "400–600RMB/sem" in f["housing"].value
    assert "25–26XLS" in f["course_restrictions"].value


def test_chongqing_errors_and_reference_brochure_are_not_current_forms():
    f = at(16).partner_exchange_details
    assert f["program_scope"].status == "needs_confirmation"
    assert "HTTP412" in f["program_scope"].value
    assert f["costs"].status == "reference_only"
    assert "800–1200/學年" in f["costs"].value
    assert "未取得表本體" in f["application_forms"].value
    assert "本科至少10學分" in f["course_restrictions"].value
    assert "研究生至少2門" in f["course_restrictions"].value
    assert source("p16-r8-calendar-index")["status"] == "fetch_failed"


def test_public_strasbourg_view_download_is_scoped_and_does_not_execute_scripts(
    tmp_path,
):
    spec = importlib.util.spec_from_file_location(
        "ccu_public_view_fetch",
        Path(__file__).resolve().parents[1] / "scripts/fetch_ccu_overseas_sources.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    s = source("p87-r8-learning-contract-pdf")
    body = (BUNDLE / s["bundled_file"]).read_bytes()
    public_view = s["source_url"]
    raw = "https://seafile.unistra.fr/seafhttp/files/public-token/blank.pdf"
    calls = []

    class Session:
        def get(self, url, **kwargs):
            calls.append(url)
            response = requests.Response()
            response.status_code = 200
            response.url = url
            response._content = (
                ("<script>rawPath: '" + raw + "'</script>").encode()
                if len(calls) == 1
                else body
            )
            return response

    result = module.fetch_public_source(
        {
            "source_id": "public-template",
            "ccu_page": 87,
            "url": public_view,
            "authority": "partner_official_public_document",
        },
        tmp_path,
        session=Session(),
    )
    assert calls == [public_view, raw]
    assert result["status"] == "pdf"
    assert result["sha256"] == hashlib.sha256(body).hexdigest()
    assert result["public_file_view_url"] == public_view
    assert result["text_pages"] == s["text_pages"]

    class UnexpectedSession:
        def get(self, url, **kwargs):
            response = requests.Response()
            response.status_code = 200
            response.url = url
            response._content = (
                b"<script>rawPath: 'https://unrelated.example/private.pdf'</script>"
            )
            return response

    result = module.fetch_public_source(
        {
            "source_id": "wrong-host",
            "ccu_page": 87,
            "url": public_view,
            "authority": "partner_official_public_document",
        },
        tmp_path,
        session=UnexpectedSession(),
    )
    assert result["status"] == "fetch_failed"
    assert "Unexpected public Strasbourg" in result["error"]


def test_eighth_counts_and_ledger_distinguish_acquisition_and_full_research():
    c = json.loads((BUNDLE / "eighth-pass-changes.json").read_text())
    assert c["new_source_count"] == 47
    assert c["new_network_acquisition_records"] == 40
    assert c["new_binary_attachment_count"] == 10
    assert len(c["changes"]) == 82
    assert sum(x["previous_status"] == "missing" for x in c["changes"]) == 46
    assert len(reviewed_rows()) == 55
    ledger = json.loads((BUNDLE / "semantic-review-ledger.json").read_text())
    assert all(not x["complete_research_claimed"] for x in ledger)
