from pathlib import Path

from exchange_info.application_documents import all_application_templates
from exchange_info.nkust_eligibility import nkust_academic_check, nkust_degree_check, nkust_language_check
from exchange_info.nkust_source_review import load_snapshot
from exchange_info.nkust_student_view import build_nkust_student_dashboard
from exchange_info.verified_window_deadlines import build_verified_window_deadline_catalog


def test_conduct_grade_and_cefr_conversion_are_not_common_pass_thresholds():
    for score, gpa, rank in [(75, None, None), (99, 4.0, 1), (55, 2.0, 50), (None, 3.0, 20)]:
        assert nkust_academic_check("學士班", score, gpa, rank)[0] == "needs_confirmation"
    for test, score, country in [("toefl", 42, "美國"), ("ielts", 4, "英國"), ("jlpt", 5, "日本"), (None, None, "中國大陸")]:
        assert nkust_language_check(test, score, partner_country=country)[0] == "needs_confirmation"


def test_degree_requirements_do_not_extrapolate_115_selection_to_116():
    assert nkust_degree_check("學士班", "大一", program_type="校級交換", academic_year="115")[0] == "fail"
    assert nkust_degree_check("學士班", "大一", program_type="校級交換", academic_year="116")[0] == "needs_confirmation"
    assert nkust_degree_check("學士班", "大一", program_type="院系級交換", academic_year="115")[0] == "needs_confirmation"
    assert nkust_degree_check("在職碩士班", "碩二")[0] == "needs_confirmation"
    assert nkust_degree_check("五專", "專三")[0] == "fail"


def test_general_exchange_does_not_require_disadvantaged_program_essay():
    templates = {t.id: t for t in all_application_templates("nkust")}
    assert "只有符合學海惜珠" in templates["study-plan"].description
    assert "1000–1500字" in templates["study-plan"].description
    data = templates["exchange-application-data"]
    assert "一般交換無須附研修計畫" in data.description
    assert "掃描PDF上傳" in data.description and not data.stamps


def test_historical_tables_do_not_reopen_closed_selection():
    d = build_nkust_student_dashboard()
    assert not any(p.availability_status == "open" for p in d.partner_universities)
    assert sum(p.availability_status == "reference_only" for p in d.partner_universities) == 97
    old = next(p for p in d.application_periods if p.academic_year == "115")
    assert old.deadline_at.isoformat() == "2025-12-10T16:00:00+08:00" and old.status == "closed"
    new = next(p for p in d.application_periods if p.academic_year == "116")
    assert new.deadline_at is None and not new.reminder_eligible
    card = next(c for c in build_verified_window_deadline_catalog().items if c.school_id == "nkust")
    assert card.primary_deadline_at is None and not card.subtasks
    assert card.study_plan_limit.min_chars is None


def test_distinct_paid_programs_and_source_conflicts_are_preserved():
    s = load_snapshot(Path(__file__).resolve().parents[1])
    name = next(k for k in s["table_matches"] if "Kansas City" in k)
    rows = [r for r in s["table_matches"][name] if r["gid"] == "142150725"]
    assert len(rows) == 2
    assert {r["cells"][5] for r in rows} == {"2", "不限"}
    assert any("免繳" in r["cells"][7] for r in rows) and any("自費" in r["cells"][7] for r in rows)
    assert any("112/07/01" in c and "111/07/01" in c for c in s["source_conflicts"])
    assert s["whole_records_verified"] == 0
