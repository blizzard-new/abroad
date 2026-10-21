"""Audit invariants and regressions supported by the dated official-source ledger."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_university_data", ROOT / "scripts/audit_university_data.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_zero_quota_and_false_are_not_missing():
    assert not audit.is_empty(0)
    assert not audit.is_empty(False)
    assert audit.is_empty(None)
    assert audit.is_empty("")


def test_source_identity_preserves_case_sensitive_paths_and_queries():
    assert audit.url_identity("HTTPS://EXAMPLE.EDU/A?FileId=AbC#page=2") == "https://example.edu/A?FileId=AbC"
    assert audit.url_identity("https://example.edu/A?FileId=AbC") != audit.url_identity("https://example.edu/a?FileId=abc")
    assert audit.url_identity("https://user:password@example.edu/") is None


def test_existing_verified_marker_is_never_a_new_fact_verification(tmp_path):
    census = audit.Census(tmp_path)
    record = census.add("ntu", "partner", "p1", {"school_name": "示例大學", "quota": "0", "review_status": "verified"}, "example")
    assert record["review_status"] == "pending_review"
    assert record["data"]["review_status"] == "verified"
    assert not any(gap["field"] == "quota" for gap in census.gaps)
    with pytest.raises(ValueError, match="duplicate"):
        census.add("ntu", "partner", "p1", {}, "example")


def test_cgu_exchange_preferences_follow_official_list_instead_of_model_default():
    from exchange_info.student_view import build_student_dashboard
    dashboard = build_student_dashboard([], fetch_partner_sheets=False, fetch_regulation_rules=False)
    assert dashboard.maximum_preferences == 2


def test_ntu_official_preference_limit_and_fee_are_consistent_across_payloads():
    from exchange_info.ntu_student_view import build_ntu_student_dashboard
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    dashboard = build_ntu_student_dashboard(partner_universities=[])
    raw = json.loads((ROOT / "src/exchange_info/official_data/ntu/student_dashboard.json").read_text("utf-8"))
    assert dashboard.maximum_preferences == raw["maximum_preferences"] == 30
    card = get_verified_school_window_card("ntu")
    assert "1,250" in card.online_deadline.value_text
    assert "1,000" not in card.online_deadline.value_text
    assert "免繳" in card.online_deadline.value_text


def test_ncu_distinguishes_student_department_and_return_report_requirements():
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    card = get_verified_school_window_card("ncu")
    assert card.paper_deadline.exact_deadline_at.isoformat() == "2026-12-11T17:00:00+08:00"
    assert "2026/12/18" in card.paper_deadline.value_text
    assert "2026/12/16" not in card.paper_deadline.value_text
    assert "未列讀書計畫或自傳" in card.study_plan_limit.value_text
    assert "返校心得" in card.study_plan_limit.value_text
    assert card.study_plan_limit.min_chars is None
    assert card.study_plan_limit.max_pages is None


def test_cgu_one_page_guidance_is_not_a_fabricated_hard_limit():
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    rule = get_verified_school_window_card("cgu").study_plan_limit
    assert "1 頁即可" in rule.value_text
    assert rule.max_pages is None


@pytest.mark.parametrize("home", ["nkust", "yuntech", "ntou"])
def test_forecasts_without_current_cycle_evidence_cannot_create_deadline_reminders(home):
    import importlib
    module = importlib.import_module(f"exchange_info.{home}_student_view")
    dashboard = getattr(module, f"build_{home}_student_dashboard")(partner_universities=[])
    pending = [p for p in dashboard.application_periods if p.date_status.value == "needs_confirmation"]
    assert pending
    for period in pending:
        assert period.status.value == "needs_confirmation"
        assert period.opens_at is None and period.deadline_at is None
        assert period.reminder_eligible is False
    assert not any(p.reminder_eligible for p in dashboard.application_periods)
    raw_rules = json.loads((ROOT / f"src/exchange_info/official_data/{home}/home_rules.json").read_text("utf-8"))
    pending_raw = [p for p in raw_rules["application_periods"] if p["date_status"] == "needs_confirmation"]
    assert pending_raw and all(p["deadline_at"] is None for p in pending_raw)


@pytest.mark.parametrize("home", ["nkust", "yuntech", "ntou"])
def test_missing_deadline_evidence_is_renderable_but_never_generates_calendar_events(home):
    from fastapi.testclient import TestClient
    from exchange_info.api import create_app
    from exchange_info.cross_school_partners import _build_home_agreement
    from exchange_info.university_registry import require_university
    client = TestClient(create_app())
    response = client.get("/verified-window-deadlines", params={"school": home})
    assert response.status_code == 200
    card = response.json()["items"][0]
    assert card["online_deadline"]["verification_status"] == "needs_confirmation"
    assert card["primary_deadline_at"] is None
    assert card["subtasks"] == []
    assert card["google_calendar_url"] is None
    calendar = client.get("/calendar/school-window.ics", params={"school": home})
    assert calendar.status_code == 200
    assert "BEGIN:VEVENT" not in calendar.text
    agreement = _build_home_agreement(require_university(home), None)
    assert "未核實" in agreement.internal_online_deadline or "待核實" in agreement.internal_online_deadline


def test_cross_school_display_accepts_single_character_quota_and_language_values():
    from exchange_info.cross_school_partners import _build_home_agreement
    from exchange_info.models import PartnerUniversity
    from exchange_info.university_registry import require_university
    partner = PartnerUniversity(
        country="日本", school_name="示例大學", quota="2", language_requirement="無",
        program_type="交換", source_url="https://example.edu/exchange",
    )
    agreement = _build_home_agreement(require_university("ntu"), [partner])
    assert agreement.quota_summary == "2"
    assert agreement.language_requirement_summary == "無"


def test_yuntech_current_notice_is_not_applied_to_other_cycles_or_mainland():
    from exchange_info.yuntech_student_view import build_yuntech_student_dashboard, fetch_yuntech_partner_universities
    from exchange_info.models import UniversityApplicationWorkflow
    dashboard = build_yuntech_student_dashboard(partner_universities=[])
    period = next(p for p in dashboard.application_periods if "非大陸" in p.application_round)
    assert period.opens_at.isoformat() == "2026-07-27T08:00:00+08:00"
    assert period.deadline_at.isoformat() == "2026-09-24T12:00:00+08:00"
    assert "非大陸" in period.application_round
    partners = fetch_yuntech_partner_universities()
    for partner in partners:
        if partner.country != "中國大陸":
            assert partner.program_type != "大陸地區校級交換學生計畫"
        else:
            assert "10/01 12:00" in partner.application_deadline
            assert "10/16" not in partner.application_deadline
    path = ROOT / "src/exchange_info/official_data/yuntech/application_workflows.jsonl"
    for line in path.read_text("utf-8").splitlines():
        workflow = UniversityApplicationWorkflow.model_validate_json(line)
        assert workflow.applicability_status.value == "needs_confirmation"
        assert not {"116-1", "116-2"}.intersection(workflow.effective_application_rounds)
        for step in workflow.steps:
            if step.deadline_at:
                assert step.deadline_at.isoformat() not in {
                    "2026-09-25T16:00:00+08:00", "2026-10-22T12:00:00+08:00",
                }


def test_unreviewed_country_defaults_never_become_school_budget_or_experience(monkeypatch):
    from exchange_info import cross_school_partners as cross
    monkeypatch.setattr(cross, "_match_bundled_digests_for_entity", lambda entity: [])
    entity = cross.AggregatedPartnerEntity(
        country_slug="japan", country_name_zh="日本", institution_slug="example-university",
        school_name_zh="示例大學", school_name_en="Example University",
    )
    living, housing, courses, experiences = cross._synthesize_cross_school_intelligence(entity, [])
    assert "尚未核實" in living[0].summary_zh
    assert cross.COUNTRY_DEFAULT_CURRENCY_HINT["日本"] not in living[0].summary_zh
    assert "非生活費金額證據" in living[0].source_title
    assert experiences == []


def test_current_fju_and_scu_requirements_do_not_accept_unsupported_alternatives():
    from exchange_info.fju_eligibility import fju_academic_check, fju_language_check
    from exchange_info.scu_eligibility import scu_academic_check, scu_language_check
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    assert fju_language_check("ielts", 6.0, partner_country="英國")[0] == "fail"
    assert fju_language_check("ielts", 6.5, partner_country="英國")[0] == "pass"
    assert fju_academic_check("大學部", 68.0, class_rank_percent=10)[0] == "fail"
    assert fju_academic_check("碩士班", 95.0)[0] == "needs_confirmation"
    assert scu_academic_check("大學部", 95.0)[0] == "needs_confirmation"
    assert scu_academic_check("大學部", 60.0, class_rank_percent=80)[0] == "pass"
    assert scu_language_check("ielts", 8.5, partner_country="英國")[0] == "needs_confirmation"
    assert get_verified_school_window_card("scu").study_plan_limit.max_chars is None


def test_nthu_nchu_official_grading_rules_do_not_invent_conversions():
    from exchange_info.nthu_eligibility import nthu_academic_check
    from exchange_info.nchu_eligibility import nchu_academic_check

    # NTHU accepts GPA 3.20 or rank 50%, never a fixed percentage shortcut.
    assert nthu_academic_check("學士班", 95, None, None)[0] == "needs_confirmation"
    assert nthu_academic_check("學士班", 95, 2.5, 80)[0] == "fail"
    assert nthu_academic_check("學士班", 60, 3.2, 80)[0] == "pass"
    assert nthu_academic_check("學士班", 60, 2.5, 50)[0] == "pass"
    # NCHU's undergraduate mean cannot be substituted by class rank or GPA.
    assert nchu_academic_check("學士班", None, 4.3, 1)[0] == "needs_confirmation"
    assert nchu_academic_check("學士班", 59, 4.3, 1)[0] == "fail"
    assert nchu_academic_check("學士班", 60, None, None)[0] == "pass"
    assert nchu_academic_check("碩士班", 59, None, None)[0] == "needs_confirmation"


def test_nthu_nchu_documents_and_deadlines_match_reviewed_sources():
    from exchange_info.verified_window_deadlines import build_verified_window_deadline_catalog

    cards = {c.school_id: c for c in build_verified_window_deadline_catalog().items}
    nthu, nchu = cards["nthu"], cards["nchu"]
    assert nthu.paper_deadline.submission_mode == "paper_required"
    assert nthu.paper_deadline.exact_deadline_at.isoformat() == "2026-10-08T16:00:00+08:00"
    assert "可用中文" in nthu.study_plan_limit.value_text
    assert nchu.paper_deadline.exact_deadline_at is None
    assert nchu.study_plan_limit.max_pages == 3
    assert "1,000" not in nchu.study_plan_limit.value_text


def test_fju_directory_quota_and_ranking_cannot_become_eligibility_or_duration():
    builder_spec = importlib.util.spec_from_file_location("fju_builder_audit", ROOT / "scripts/build_fju_catalog.py")
    builder = importlib.util.module_from_spec(builder_spec)
    builder_spec.loader.exec_module(builder)
    metadata = builder.parse_listing_metadata(["美國", "天普大學Temple University", "2", "QS #721-730"], 0)
    assert metadata["contract_quota"] == "2"
    assert metadata["grade_limit"] == metadata["semester_limit"] == ""
    assert metadata["directory_notes"] == "QS #721-730"
    mainland = builder.parse_listing_metadata(["香港", "範例學校", "5", "O", "", "O", "#100"], 1)
    assert mainland["grade_limit"] == mainland["semester_limit"] == ""
    with pytest.raises(ValueError):
        builder.parse_listing_metadata(["美洲"], 0)
    rows = [json.loads(line) for line in (ROOT / "src/exchange_info/official_data/fju/partners.jsonl").read_text("utf8").splitlines()]
    temple = next(r for r in rows if "Temple University" in r["school_name"])
    assert "待確認" in temple["degree_levels"]
    assert "QS" not in temple["study_period"]
    assert "可申請對象：2" not in temple["eligibility"]


def test_reviewed_rank_only_rules_do_not_publish_invented_percentage_thresholds():
    from exchange_info.university_registry import NTHU, SCU
    assert NTHU.academic_score_minimum is None
    assert SCU.academic_score_minimum is None


def test_ntpu_submission_destination_and_interview_dates_follow_current_notice():
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    card = get_verified_school_window_card("ntpu")
    assert "Google 表單" in card.paper_deadline.value_text
    assert "系所核章" not in card.paper_deadline.value_text
    assert "11/23" in card.online_deadline.value_text
    assert "11/27" in card.online_deadline.value_text
    assert "11/11" not in card.online_deadline.value_text


def test_ncku_does_not_invent_application_fee_or_hide_signature_conflict():
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    card = get_verified_school_window_card("ncku")
    assert "繳交報名費" not in card.online_deadline.value_text
    assert "09:00" not in card.window_badge
    assert card.paper_deadline.verification_status == "needs_confirmation"
    assert "歧義" in card.paper_deadline.value_text
    assert card.study_plan_limit.max_pages is None


def test_ccu_approximate_document_length_is_not_a_hard_limit_or_future_deadline():
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    card = get_verified_school_window_card("ccu")
    assert card.study_plan_limit.max_pages is None
    assert card.study_plan_limit.verification_status == "verified_reference"
    assert all(task.due_date <= "2026-09-21" for task in card.subtasks)


def test_identical_translated_visual_records_are_not_false_ambiguities():
    from exchange_info.school_identity import VisualRecordIndex
    common = {"status": "verified", "local_path": "/same.jpg", "content_hash": "same", "source": "same"}
    records = {
        ("香港理工大學", "香港"): {"school_name": "香港理工大學", **common},
        ("the hong kong polytechnic university", "香港"): {
            "school_name": "香港理工大學 The Hong Kong Polytechnic University", **common,
        },
    }
    query = ("香港理工大學 Hong Kong Polytechnic University", "香港")
    assert VisualRecordIndex(records).get(query)["local_path"] == "/same.jpg"
    assert VisualRecordIndex(records).get((query[0], "中國大陸")) is None
    records[("香港理工大學", "香港")]["status"] = "needs_confirmation"
    assert VisualRecordIndex(records).get(query) is None


def test_nccu_academic_result_respects_program_and_evidence_type():
    from exchange_info.nccu_eligibility import nccu_academic_check, nccu_language_check
    assert nccu_academic_check("學士班", 95, 4.3, None, partner_country="美國")[0] == "needs_confirmation"
    assert nccu_academic_check("學士班", 60, None, 100, partner_country="美國")[0] == "pass"
    assert nccu_academic_check("碩士班", None, 4.3, 1, partner_country="美國")[0] == "needs_confirmation"
    assert nccu_academic_check("碩士班", 69, 4.3, 1, partner_country="美國")[0] == "fail"
    assert nccu_academic_check("碩士班", 69, 4.3, 1, partner_country="中國大陸")[0] == "needs_confirmation"
    assert nccu_language_check("toeic", 990, partner_country="美國")[0] == "fail"
    assert nccu_language_check("jlpt", 5, partner_country="日本")[0] == "fail"


def test_ntnu_language_exemption_requires_program_evidence_not_country_guess():
    from exchange_info.ntnu_eligibility import ntnu_language_check
    assert ntnu_language_check(None, None, partner_country="中國大陸")[0] == "needs_confirmation"
    assert ntnu_language_check(None, None, partner_country="中國大陸", program_type="校級中文組交換")[0] == "pass"
    assert ntnu_language_check("toefl", 120, partner_country="美國")[0] == "needs_confirmation"


def test_scoped_milestones_and_conflicting_word_minimum_are_not_conflated():
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    nccu, ntnu = (get_verified_school_window_card(home) for home in ("nccu", "ntnu"))
    task = next(task for task in nccu.subtasks if task.id == "nccu-subtask-deadline")
    assert "語檢上傳" in task.title and "限已報名者" in task.title
    assert "09/24" in nccu.online_deadline.value_text
    assert nccu.study_plan_limit.max_chars is None
    assert nccu.study_plan_limit.max_pages is None
    assert ntnu.paper_deadline.exact_deadline_at.isoformat() == "2026-11-15T23:59:59+08:00"
    assert ntnu.study_plan_limit.verification_status == "needs_confirmation"
    assert ntnu.study_plan_limit.min_chars is None


def test_client_rank_only_policy_does_not_treat_null_gpa_as_zero():
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        pytest.skip("Node runtime unavailable")
    source = (ROOT / "src/exchange_info/static/app.js").read_text("utf8")
    start = source.index("function homeAcademicPass(")
    end = source.index("\nfunction renderAcademicFields(", start)
    script = """
const assert = require("node:assert/strict");
const homeSelectionRules = () => ({
  academic_policy: "gpa_or_rank",
  undergraduate_gpa_minimum: null,
  undergraduate_rank_maximum: 50
});
""" + source[start:end] + """
assert.equal(homeAcademicPass({degree:"學士班",academicGpa:4.3,classRankPercent:90}), false);
assert.equal(homeAcademicPass({degree:"學士班",academicGpa:1.0,classRankPercent:50}), true);
"""
    subprocess.run([node, "-e", script], check=True, capture_output=True, text=True)


def test_fju_current_submission_does_not_mix_legacy_paper_instructions():
    from exchange_info.models import ApplicationStep

    spec = importlib.util.spec_from_file_location("fju_catalog_submission", ROOT / "scripts/build_fju_catalog.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    expected = builder.current_home_submission_step("example")
    rows = [
        json.loads(line) for line in
        (ROOT / "src/exchange_info/official_data/fju/application_workflows.jsonl").read_text("utf8").splitlines()
    ]
    assert len(rows) == 234
    for row in rows:
        step = row["steps"][1]
        ApplicationStep.model_validate(step)
        assert {**step, "rule_id": "example"} == expected
        assert step["submission"]["method"] == "mixed"
        assert len(step["document_requirements"]) == 4
        assert "20MB" in step["summary"]
        assert "Google" not in json.dumps(step, ensure_ascii=False)
        assert "A113" not in json.dumps(step, ensure_ascii=False)
        assert row["steps"][0]["deadline_at"] is None
        assert not row["steps"][0]["deadline_reminder_eligible"]


def test_scu_information_session_is_not_an_eligibility_deadline():
    directory = ROOT / "src/exchange_info/official_data/scu"
    rows = [json.loads(line) for line in (directory / "application_workflows.jsonl").read_text("utf8").splitlines()]
    assert len(rows) == 191
    for row in rows:
        first, submission = row["steps"][:2]
        assert first["deadline_at"] is None
        assert first["deadline_status"] == "not_applicable"
        assert not first["deadline_reminder_eligible"]
        assert submission["deadline_at"] == "2026-11-16T12:00:00+08:00"
    for name in ("student_dashboard.json", "home_rules.json"):
        periods = json.loads((directory / name).read_text("utf8"))["application_periods"]
        session = next(p for p in periods if p["source"]["category"] == "info_session")
        assert session["deadline_at"] == "2026-10-16T19:00:00+08:00"
        results = next(p for p in periods if p["application_round"] == "116學年度結果公告")
        assert results["opens_at"] is None and results["deadline_at"] is None
        assert not results["reminder_eligible"]


def test_ncku_day_only_opening_and_old_cycle_do_not_publish_invented_timestamps():
    directory = ROOT / "src/exchange_info/official_data/ncku"
    for name in ("student_dashboard.json", "home_rules.json"):
        current, future = json.loads((directory / name).read_text("utf8"))["application_periods"][:2]
        assert current["opens_at"] is None
        assert current["deadline_at"] == "2026-11-19T16:00:00+08:00"
        assert future["opens_at"] is None and future["deadline_at"] is None
        assert future["date_status"] == "needs_confirmation"
        assert not future["reminder_eligible"]


def test_fcu_gpa_floor_cannot_be_replaced_by_percentage_or_class_rank():
    from exchange_info.fcu_eligibility import fcu_academic_check, fcu_degree_check
    assert fcu_academic_check("學士班", 99, None, 1)[0] == "needs_confirmation"
    assert fcu_academic_check("學士班", 99, 2.9, 1)[0] == "fail"
    assert fcu_academic_check("學士班", None, 3.0, 90)[0] == "pass"
    assert fcu_degree_check("學士班", "延畢")[0] == "needs_confirmation"
    assert fcu_degree_check("學士班", "大一")[0] == "needs_confirmation"


def test_nsysu_rank_is_scored_without_an_invented_gpa_cutoff():
    from exchange_info.nsysu_eligibility import nsysu_academic_check, nsysu_language_check
    assert nsysu_academic_check("學士班", 99, 4.0, None)[0] == "needs_confirmation"
    assert nsysu_academic_check("學士班", 50, 1.0, 100)[0] == "pass"
    assert nsysu_language_check("jlpt", 1, partner_country=None)[0] == "needs_confirmation"
    assert nsysu_language_check("topik", 6, partner_country="韓國")[0] == "needs_confirmation"
    assert nsysu_language_check("duolingo", 80, partner_country="美國")[0] == "pass"


def test_fcu_and_nsysu_unconfirmed_rounds_do_not_create_deadline_events():
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    for slug in ("fcu", "nsysu"):
        card = get_verified_school_window_card(slug)
        assert card.primary_deadline_date is None
        assert card.primary_deadline_at is None
        assert not card.subtasks
        assert card.ics_download_url is None
        assert card.google_calendar_url is None
    fcu = get_verified_school_window_card("fcu")
    assert fcu.study_plan_limit.min_chars == 1000
    assert fcu.study_plan_limit.verification_status == "verified_reference"
    nsysu = get_verified_school_window_card("nsysu")
    assert nsysu.online_deadline.verification_status == "verified_reference"
    assert "01/12為預定簡章公告日" in nsysu.online_deadline.value_text
    assert nsysu.study_plan_limit.max_pages is None


def test_source_urls_stop_before_chinese_parenthetical_notes():
    assert audit.urls_in("https://example.edu/Form?ID=AbC（申請表）") == {"https://example.edu/Form?ID=AbC"}
