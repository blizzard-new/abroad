from pathlib import Path

from exchange_info.application_documents import all_application_templates
from exchange_info.yuntech_eligibility import yuntech_academic_check, yuntech_language_check
from exchange_info.yuntech_source_review import load_snapshot
from exchange_info.yuntech_student_view import build_yuntech_student_dashboard
from exchange_info.verified_window_deadlines import build_verified_window_deadline_catalog


def test_gpa_conversion_and_score_rubric_do_not_establish_admission():
    for score, gpa, rank in [(None, 2.75, None), (75, None, None), (60, None, 50), (60, 2.0, 70)]:
        status, detail = yuntech_academic_check("學士班", score, gpa, rank)
        assert status == "needs_confirmation" and "操行" in detail
    for test, score, country in [("toefl", 61, "美國"), ("ielts", 5, "英國"), ("toeic", 550, "越南"),
                                 ("jlpt", 3, "日本"), (None, None, "中國大陸")]:
        assert yuntech_language_check(test, score, partner_country=country)[0] == "needs_confirmation"


def test_closed_rosters_and_separate_semester_year_quotas():
    s = load_snapshot(Path(__file__).resolve().parents[1])
    d = build_yuntech_student_dashboard()
    assert len(s["table_matches"]) == 108 and len(s["unmatched_source_rows"]) == 44
    assert not any(p.availability_status == "open" for p in d.partner_universities)
    assert sum(p.availability_status == "needs_confirmation" for p in d.partner_universities) == 4
    p = next(p for p in d.partner_universities if "拉曼大學" in p.school_name)
    assert "一學期3、一學年2" in p.quota and "不相加" in p.quota
    p = next(p for p in d.partner_universities if "釜山大學 " in p.school_name)
    assert "管理學院" in p.colleges and "不能寫不限學院" in p.colleges
    mainland = next(p for p in d.application_periods if "赴陸" in p.title)
    assert mainland.deadline_at.isoformat() == "2026-10-01T12:00:00+08:00"
    card = next(c for c in build_verified_window_deadline_catalog().items if c.school_id == "yuntech")
    assert card.primary_deadline_at is None and not card.subtasks


def test_document_language_and_award_only_course_and_report_rules():
    templates = {t.id: t for t in all_application_templates("yuntech")}
    assert "英文或接待國語言" in templates["study-plan"].description
    assert "固定字數或頁數上限" in templates["study-plan"].description
    assert "或參與至少一位校內教授研究計畫" in templates["course-preapproval"].description
    assert "王秋雄受獎生" in templates["return-report"].description
    assert "至少5頁" in templates["return-report"].description
    assert "一個月" in templates["return-report"].description
    assert "推薦函積分以3分" in templates["exchange-application-data"].conditional_note


def test_conflicting_documents_are_preserved_for_followup():
    s = load_snapshot(Path(__file__).resolve().parents[1])
    assert any("赴陸免外語" in c and "語言能力證明" in c for c in s["source_conflicts"])
    assert any("114/06/13" in c and "114學年度" in c for c in s["source_conflicts"])
    assert s["whole_records_verified"] == 0
