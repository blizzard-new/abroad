from pathlib import Path

from exchange_info.application_documents import all_application_templates
from exchange_info.pccu_eligibility import pccu_academic_check, pccu_degree_check, pccu_language_check
from exchange_info.pccu_source_review import load_snapshot
from exchange_info.pccu_student_view import build_pccu_student_dashboard
from exchange_info.verified_window_deadlines import build_verified_window_deadline_catalog


def test_award_and_unrelated_host_thresholds_cannot_approve_exchange():
    for score, gpa, rank in [(99, 4.3, 1), (62, 2.0, 65), (None, 4.0, 10)]:
        assert pccu_academic_check("學士班", score, gpa, rank)[0] == "needs_confirmation"
    for test, score, country in [(None, None, "中國大陸"), ("toefl", 61, "美國"),
        ("jlpt", 5, "日本"), ("topik", 1, "韓國")]:
        assert pccu_language_check(test, score, partner_country=country)[0] == "needs_confirmation"


def test_first_year_and_graduate_conditions_are_route_specific():
    assert pccu_degree_check("學士班", "大一", partner_country="中國大陸")[0] == "needs_confirmation"
    assert pccu_degree_check("學士班", "大一", program_type="國合組")[0] == "fail"
    status, detail = pccu_degree_check("碩士班", "碩二", program_type="韓國語文學系")
    assert status == "needs_confirmation" and "20學分" in detail
    status, detail = pccu_degree_check("碩士班", "碩二", program_type="日本語文學系")
    assert status == "needs_confirmation" and "出發前" in detail and "滿一年" in detail


def test_current_mainland_deadline_does_not_open_all_25_schools():
    d = build_pccu_student_dashboard()
    opened = [p for p in d.partner_universities if p.availability_status == "open"]
    assert {p.school_name.split()[0] for p in opened} == {"北京大學", "吉林大學", "蘭州大學"}
    assert all("115-1" in p.availability_note and "115-2" in p.availability_note for p in opened)
    assert d.maximum_preferences is None and not d.language_score_minimums
    kr = next(p for p in d.application_periods if "韓文系" in p.title)
    assert kr.status == "closed" and kr.deadline_at.hour == 8 and not kr.reminder_eligible
    jp = next(p for p in d.application_periods if "日文系" in p.title)
    assert jp.deadline_at is None and jp.status == "closed"
    card = next(c for c in build_verified_window_deadline_catalog().items if c.school_id == "pccu")
    assert card.primary_deadline_at.isoformat() == "2026-11-03T17:00:00+08:00"
    assert not any("japanese" in task.id or task.due_date == "2026-11-27" for task in card.subtasks)
    assert "僅限該階段名單" in card.online_deadline.value_text
    assert card.study_plan_limit.min_chars is None


def test_documents_preserve_distinct_lengths_and_submission_routes():
    t = {t.id: t for t in all_application_templates("pccu")}
    plan = t["study-plan"].description
    assert "300字以內" in plan and "至少200字" in plan and "合計至少500字" in plan
    assert "中文或韓文" in plan
    assert "大恩館" in t["exchange-application-data"].description
    assert not t["exchange-application-data"].signatures
    assert not t["exchange-application-data"].official_download_url


def test_source_snapshot_retains_missing_rows_and_distinct_quota_units():
    s = load_snapshot(Path(__file__).resolve().parents[1])
    assert s["whole_records_verified"] == 0
    assert len(s["oima_quota_reference"]) == 47
    assert len([r for r in s["korean_name_matches"] if r["school_name"] is None]) == 16
    assert len([r for r in s["mainland_rows"] if r["stage"] == "mainland-second" and r["matched_school_name"] is None]) == 15
    q = {r["school_name"]: r["quota_reference"] for r in s["oima_quota_reference"]}
    assert any("學期" in value for value in q.values())
    assert any("自費不限" in value for value in q.values())
