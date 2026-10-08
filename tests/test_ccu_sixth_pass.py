"""Keep incoming scopes, term deadlines, actual form contents and years separate."""

import hashlib
import importlib.util
import io
import json
import zipfile

import requests

from exchange_info.ccu_overseas import reviewed_rows
from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.models import DestinationProfile, UniversityApplicationWorkflow
from exchange_info.storage import read_jsonl


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


def source(sid):
    return json.loads((BUNDLE / "overseas_sources" / f"{sid}.json").read_text())


def test_hcmute_optional_certificates_do_not_remove_home_or_host_language_rules():
    p = at(68)
    f = p.partner_exchange_details
    assert f["eligibility"].status == "verified_current"
    assert "No limitation" in f["eligibility"].value
    assert "GPA3.0且平均70" in f["eligibility"].value
    assert "B2" in f["language"].value and "optional" in f["language"].value
    assert f["documents"].status == "verified_current"
    assert "mandatory五项" in f["documents"].value
    assert "optional兩项" in f["documents"].value
    assert source("p68-r6-factsheet2027")["text_pages"][0].count("Optional") == 1
    assert f["nomination_deadline"].status == "missing"
    assert f["academic_calendar"].status == "missing"
    assert f["arrival"].status == "missing"
    assert f["application_forms"].status == "needs_confirmation"


def test_hcmute_term_deadlines_conflict_on_all_projections_without_reminders():
    p = at(68)
    f = p.partner_exchange_details["application_deadline"]
    assert f.status == "conflict"
    for date in ["2027-01-25", "2027-01-04", "2027-04-12"]:
        assert date in f.value
    assert "2027/01/25" in p.reference_data["partner_application_deadline"]
    assert p.partner_application_deadline == f.value
    assert p.student_summary_zh.application_deadline == f.value
    assert p.field_evidence["partner_application_deadline"].status == "conflict"
    flows = read_jsonl(
        BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow
    )
    flow = next(x for x in flows if x.school_name == p.school_name)
    assert "2027-04-12" in flow.steps[4].timing
    assert flow.steps[4].deadline_at is None
    assert not flow.steps[4].deadline_reminder_eligible
    assert {page for e in f.evidence for page in e.source_pages} == {2, 68}
    raw = source("p68-r6-ccu-list")
    assert raw["acquisition_mode"] == "reread_existing_bundled_official_pdf"
    assert raw["bundled_file"] == "2027-spring-partners.pdf"


def test_hcmute_fee_units_and_suggested_insurance_do_not_become_guarantees():
    f = at(68).partner_exchange_details
    assert "USD1195/學年" in f["costs"].value
    assert "每人153" in f["costs"].value and "整房306" in f["costs"].value
    assert "suggest" in f["insurance"].value
    assert f["housing_deadline"].status == "missing"
    assert "administrativefee" in f["host_tuition"].value
    assert "非協議" in f["host_tuition"].value
    assert "ETCs" in f["course_restrictions"].value
    assert "ApplicationDeadlines" in f["exchange_duration"].value


def test_chiba_unyear_rules_keep_orientation_difference_and_invited_packet():
    f = at(33).partner_exchange_details
    assert "N2" in f["language"].value and "expected" in f["language"].value
    assert f["language"].status == "needs_confirmation"
    assert f["academic_calendar"].status == "conflict"
    assert f["arrival"].status == "conflict"
    assert "JPY38000" in f["costs"].value
    assert f["application_forms"].status == "needs_confirmation"
    assert "2027" in f["application_forms"].value
    assert "交換身分" in f["insurance"].value
    assert f["visa"].status == "missing"


def test_dntu_news_and_chinese_culture_ccu_do_not_fill_incoming_fields_or_quota():
    p = at(71)
    assert p.quota is None and p.quota_status == "not_published"
    assert p.availability_status == "needs_confirmation"
    assert all(f.status == "missing" for f in p.partner_exchange_details.values())
    assert "CHINESE CULTURE UNIVERSITY (CCU)" in source(
        "p71-r6-international"
    )["text_pages"][0]
    assert source("p71-r6-pas")["content_applicability"] == "reference_only"
    ledger = json.loads((BUNDLE / "semantic-review-ledger.json").read_text())
    d = next(x for x in ledger if x["ccu_page"] == 71)
    assert "非國立中正" in d["fields"]["program_scope"]["note"]


def test_presidency_opened_inbound_template_and_2025_sheet_keep_actual_scope():
    f = at(80).partner_exchange_details
    assert "incoming" in f["eligibility"].value
    assert "outgoing最低CGPA6.0" in f["eligibility"].value
    assert f["application_deadline"].status == "missing"
    assert f["course_restrictions"].status == "reference_only"
    assert f["host_tuition"].status == "reference_only"
    assert f["application_forms"].status == "needs_confirmation"
    assert "母校系主任與國際處" in f["application_forms"].value
    assert source("p80-r6-predeparture")["content_applicability"] == "reference_only"
    assert "Last update: January 2025" in source("p80-r6-factsheet")["text_pages"][-1]
    for sid in ["p80-r6-incoming-form", "p80-r6-factsheet"]:
        s = source(sid)
        assert hashlib.sha256((BUNDLE / s["bundled_file"]).read_bytes()).hexdigest() == s["sha256"]
        assert (BUNDLE / s["bundled_file"]).read_bytes().startswith(b"%PDF-")
    assert at(80).quota is None


def test_presidency_calendar_general_and_mba_specific_dates_are_both_preserved():
    f = at(80).partner_exchange_details
    assert f["academic_calendar"].status == "conflict"
    assert "2027-01-18" in f["academic_calendar"].value
    assert "01-27" in f["academic_calendar"].value
    assert "MBA" in f["academic_calendar"].value
    assert f["exchange_duration"].status == "verified_current"
    assert "SummerTerm" in f["exchange_duration"].value


def test_jena_current_guest_deadline_evidence_is_not_degree_admission_text():
    f = at(99).partner_exchange_details
    assert f["nomination_deadline"].status == "verified_current"
    assert "2026-11-15" in f["nomination_deadline"].value
    assert f["application_deadline"].status == "verified_current"
    assert f["application_deadline"].evidence[0].source_pages == [15]
    assert "after nomination by home university" in f["application_deadline"].evidence[0].excerpt
    assert f["eligibility"].status == "conflict"
    assert "第4Bachelor" in f["eligibility"].value
    assert f["academic_calendar"].status == "conflict"
    assert f["arrival"].status == "conflict"
    assert "probably" in f["academic_calendar"].value
    assert f["exchange_duration"].status == "verified_current"
    assert "考試依faculty" in f["exchange_duration"].value


def test_jena_forms_and_costs_keep_research_and_winter_scopes():
    f = at(99).partner_exchange_details
    assert f["application_forms"].status == "needs_confirmation"
    assert "登入" in f["application_forms"].value
    assert "研究" in f["documents"].value
    assert f["housing_deadline"].status == "verified_current"
    assert "2027-01-15" in f["housing_deadline"].value
    assert f["costs"].status == "needs_confirmation"
    assert "333.05" in f["costs"].value and "Summer2027" in f["costs"].value
    assert f["visa"].status == "needs_confirmation"
    assert "臺灣護照例外" in f["visa"].value
    assert "travel/emergency" in f["insurance"].value
    s = source("p99-r6-nomination-list")
    assert s["status"] == "xlsx"
    assert hashlib.sha256((BUNDLE / s["bundled_file"]).read_bytes()).hexdigest() == s["sha256"]
    assert "FORMULA (not evaluated)" in s["text_pages"][0]


def test_uwb_formal_calendar_and_dorm_documents_keep_faculty_and_fee_components():
    f = at(109).partner_exchange_details
    assert f["academic_calendar"].status == "verified_current"
    assert "05-19至06-30及08-16至31" in f["academic_calendar"].value
    assert "Health" in f["academic_calendar"].value
    assert f["academic_calendar"].evidence[0].source_pages == [2]
    assert f["housing_deadline"].status == "needs_confirmation"
    assert "12/10" in f["housing_deadline"].value
    assert "每月15" in f["housing_deadline"].value
    assert "2500security+3500blocking" in f["costs"].value
    assert f["costs"].status == "needs_confirmation"
    assert f["application_forms"].status == "needs_confirmation"
    assert "contract" in f["application_forms"].value
    assert f["insurance"].status == "missing"
    assert source("p109-r6-public-prices-index")["http_status"] == 404
    assert source("p109-r6-display-prices-index")["http_status"] == 200


def test_sixth_ledger_and_counts_preserve_partial_review_and_actual_acquisition_mode():
    ledger = json.loads((BUNDLE / "semantic-review-ledger.json").read_text())
    assert {33, 68, 71, 80, 99, 109}.issubset(x["ccu_page"] for x in ledger)
    assert len(ledger) >= 18 and all(not x["complete_research_claimed"] for x in ledger)
    j = next(x for x in ledger if x["ccu_page"] == 99)
    assert "p99-r6-application-compass" in j["fields"]["language"]["partially_reviewed_source_ids"]
    c = json.loads((BUNDLE / "sixth-pass-changes.json").read_text())
    assert c["new_source_count"] == 66
    assert c["new_network_acquisition_records"] == 65
    assert len(c["changes"]) == 65
    assert sum(x["previous_status"] == "missing" for x in c["changes"]) == 57
    assert len(reviewed_rows()) == 55


def test_parent_corrections_reach_language_calendar_and_destination_guides():
    amu = at(95)
    assert amu.field_evidence["language_requirement"].status == "needs_confirmation"
    assert {c.test for c in amu.language_conditions} == {"ielts", "toeic", "toefl", "other"}
    assert all(c.requirement_level == "needs_confirmation" for c in amu.language_conditions)
    assert all(c.scope_choice_required and c.additional_conditions for c in amu.language_conditions)
    letter = next(c for c in amu.language_conditions if c.test == "other")
    assert letter.minimum_score is None
    assert letter.evidence.source_pages == [10]
    assert "Rector／Dean／Coordinator" in amu.language_review_note
    assert "兩年內有效檢定" in amu.language_review_note
    assert "recommended" in amu.language_review_note
    assert amu.language_review_note in amu.student_summary_zh.eligibility_points
    language = amu.partner_exchange_details["language"]
    assert language.status == "needs_confirmation"
    assert {e["source_id"] for e in reviewed_rows()[95]["fields"]["language"]["evidence"]}.issuperset({"p95-mirror", "p95-r6-ccu-list", "p95-r6-ccu-guidelines"})
    nagoya = at(34)
    calendar = nagoya.partner_exchange_details["academic_calendar"]
    assert calendar.status == "conflict"
    assert nagoya.semester_dates == calendar.value
    assert calendar.value in nagoya.student_summary_zh.study_period
    assert nagoya.field_evidence["semester_dates"].status == "conflict"
    assert "2027/04/12" in nagoya.reference_data["semester_dates"]
    for date in ["2027-04-09", "2027-04-12", "08-06"]:
        assert date in calendar.value
    arrival = nagoya.partner_exchange_details["arrival"]
    assert arrival.status == "verified_current" and "04-01" in arrival.value
    assert nagoya.partner_exchange_details["exchange_duration"].status == "conflict"
    guides = read_jsonl(BUNDLE / "destination_profiles.jsonl", DestinationProfile)
    guide = next(x for x in guides if x.school_name == nagoya.school_name)
    section = next(x for x in guide.student_guide_sections if x.key == "academic_calendar")
    assert section.summary == calendar.value and "來源矛盾" in section.caution
    bordeaux = at(85).partner_exchange_details["housing"]
    assert "持學徒／職業化培訓合約" in bordeaux.value
    assert "可能符合" in bordeaux.value and "不能泛化為一般stage實習" in bordeaux.value
    assert "工作/實習" not in bordeaux.value
    government = next(e for e in bordeaux.evidence if "A18981" in e.source_url)
    assert "contrat d’apprentissage ou de professionnalisation" in government.excerpt
    guide = next(x for x in guides if x.school_name == at(85).school_name)
    assert bordeaux.value in guide.housing_summary
    flows = read_jsonl(BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow)
    flow = next(x for x in flows if x.school_name == amu.school_name)
    assert any(amu.language_review_note in x for x in flow.steps[4].details)


def test_xlsx_fetcher_does_not_confuse_word_or_evaluate_cell_formulas(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "ccu_xlsx", "scripts/fetch_ccu_overseas_sources.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    body = io.BytesIO()
    with zipfile.ZipFile(body, "w") as archive:
        archive.writestr("xl/workbook.xml", "<workbook/>")
        archive.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>bilateral partnership</t></si></sst>',
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1" t="s"><v>0</v></c><c r="A2" t="inlineStr"><is><t>CEFR</t></is></c><c r="H25"><f>DO_NOT_EVALUATE()</f><v>999</v></c></row></sheetData></worksheet>',
        )

    class Session:
        def get(self, url, **kwargs):
            response = requests.Response()
            response.url = url
            response.status_code = 200
            response._content = body.getvalue()
            response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            return response

    s = module.fetch_public_source(
        {"url": "https://official.example.edu/nomination.xlsx", "source_id": "nomination", "authority": "partner_official_public_page"},
        tmp_path,
        Session(),
    )
    assert s["status"] == "xlsx" and (tmp_path / "nomination.xlsx").exists()
    assert not (tmp_path / "nomination.docx").exists()
    assert "A1: bilateral partnership" in s["text_pages"][0]
    assert "A2: CEFR" in s["text_pages"][0]
    assert "FORMULA (not evaluated): DO_NOT_EVALUATE()" in s["text_pages"][0]
    assert "999" not in s["text_pages"][0]
    assert s["content_applicability"] == "needs_confirmation"
