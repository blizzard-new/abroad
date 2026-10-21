from pathlib import Path

from exchange_info.application_documents import all_application_templates
from exchange_info.verified_window_deadlines import build_verified_window_deadline_catalog
from exchange_info.wzu_eligibility import wzu_academic_check, wzu_degree_check
from exchange_info.wzu_source_review import load_snapshot
from exchange_info.wzu_student_view import build_wzu_student_dashboard


def test_program_specific_percentage_cannot_be_replaced_by_gpa():
    assert wzu_academic_check("學士班", None, 4.0, 1)[0] == "needs_confirmation"
    assert wzu_academic_check("學士班", 69.9, 4.0, 1, program_type="一般組")[0] == "fail"
    assert wzu_academic_check("學士班", 69.9, program_type="語言學習組")[0] == "pass"
    assert wzu_academic_check("學士班", 64.9, 4.0, 1, program_type="語言學習組")[0] == "fail"
    assert wzu_academic_check("學士班", 70, program_type="一般組")[0] == "pass"


def test_application_year_and_outbound_year_are_distinct():
    assert wzu_degree_check("學士班", "大一")[0] == "needs_confirmation"
    assert wzu_degree_check("四技", "一年級上學期")[0] == "fail"
    assert wzu_degree_check("五專", "三下", program_type="一般組（日語組）")[0] == "fail"
    assert wzu_degree_check("二技", "三年級")[0] == "needs_confirmation"
    assert wzu_degree_check("碩士班", "碩一")[0] == "needs_confirmation"
    assert wzu_degree_check("在職碩士", "碩二")[0] == "fail"


def test_closed_application_is_not_reopened_by_interview_window():
    d = build_wzu_student_dashboard()
    historical = [p for p in d.application_periods if p.academic_year == "115"]
    assert len(historical) == 4
    assert all((p.deadline_at.hour, p.deadline_at.minute) == (23, 59) for p in historical)
    future = next(p for p in d.application_periods if p.academic_year == "116")
    assert future.deadline_at is None and future.opens_at is None
    assert not future.reminder_eligible
    card = next(c for c in build_verified_window_deadline_catalog().items if c.school_id == "wzu")
    assert card.window_status == "closed_current_round"
    assert not card.subtasks and card.primary_deadline_at is None
    assert card.online_deadline.exact_deadline_at.isoformat() == "2026-10-13T23:59:00+08:00"
    assert card.study_plan_limit.max_pages is None  # Five pages is the whole CV, not one essay.
    assert card.study_plan_limit.min_chars is None


def test_cv_limit_and_later_signatures_are_not_initial_paper_requirements():
    t = {t.id: t for t in all_application_templates("wzu")}
    assert not t["exchange-application-data"].signatures
    assert not t["exchange-application-data"].stamps
    assert "合計A4五頁" in t["study-plan"].description
    assert "返國兩週" in t["return-report"].description
    assert "初審使用當期Google表單" in t["exchange-application-data"].conditional_note


def test_source_snapshot_preserves_rounds_and_unmatched_programs():
    s = load_snapshot(Path(__file__).resolve().parents[1])
    assert len(s["table_matches"]) == 128 and s["whole_records_verified"] == 0
    assert {t["file"][:6] for t in s["tables"]} == {"529353", "529354", "530751", "530752"}
    assert any("暫停交流" in u["name"] for u in s["unmatched_table_names"])
    assert any("聖地牙哥" in u["name"] for u in s["unmatched_table_names"])
