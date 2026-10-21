import json
from pathlib import Path

from exchange_info.yzu_eligibility import yzu_academic_check, yzu_degree_check, yzu_language_check
from exchange_info.yzu_source_review import load_tables, matching_rows, deadline_text
from exchange_info.verified_window_deadlines import get_verified_school_window_card

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/yzu"


def test_course_grading_does_not_become_admission_and_management_is_separate():
    for score, gpa, rank in [(99, 4.0, 1), (69, 2.5, 50), (None, None, None)]:
        assert yzu_academic_check("學士班", score, gpa, rank)[0] == "needs_confirmation"
    assert yzu_academic_check("學士班", 95, None, 1, program_type="管理學院 OIP 院級交換")[0] == "needs_confirmation"
    assert yzu_academic_check("學士班", None, 3.0, None, program_type="管理學院 OIP 院級交換")[0] == "pass"
    assert yzu_academic_check("學士班", None, 4.0, None, program_type="校級交換＋管理學院院級交換")[0] == "needs_confirmation"


def test_eligibility_preserves_missing_semester_and_proof_details():
    assert yzu_degree_check("碩士班", "碩一")[0] == "needs_confirmation"
    assert yzu_degree_check("碩士班", "碩一上")[0] == "fail"
    assert yzu_degree_check("碩士班", "碩二", partner_country="中國大陸")[0] == "needs_confirmation"
    assert yzu_degree_check("在職專班", "碩二")[0] == "needs_confirmation"
    assert yzu_language_check("toefl", 61, partner_country="美國")[0] == "needs_confirmation"
    assert yzu_language_check("jlpt", 2, partner_country="日本")[0] == "needs_confirmation"
    assert "只涵蓋母校文件" in yzu_language_check(None, None, partner_country="中國大陸")[1]


def test_individual_table_dates_and_conflicts_are_not_merged():
    tables = load_tables(ROOT)
    partners = [json.loads(s) for s in (BUNDLE / "partners.jsonl").read_text("utf8").splitlines()]
    assert sum(matching_rows(p, tables)[0] == "international" for p in partners) == 53
    wuhan = next(p for p in partners if p["school_name"].startswith("武漢大學 "))
    group, rows = matching_rows(wuhan, tables)
    assert len(rows) == 2
    assert "03.31" in deadline_text(group, rows)
    assert "10.20" in deadline_text(group, rows)
    nanjing = next(p for p in partners if p["school_name"].startswith("南京大學 "))
    assert "2026.10.16" in nanjing["application_deadline"]
    assert "17:00" not in nanjing["application_deadline"]
    royal = next(p for p in partners if p["school_name"].startswith("皇家山大學 "))
    assert matching_rows(royal, tables)[1][0]["cells"]["B"] == "9/11"


def test_blank_quota_and_nonwaived_tuition_are_not_defaulted():
    partners = [json.loads(s) for s in (BUNDLE / "partners.jsonl").read_text("utf8").splitlines()]
    ohio = next(p for p in partners if "The Ohio State University" in p["school_name"])
    assert "空白" in ohio["quota"]
    assert "不免學費" in ohio["tuition_info"]
    assert "2 名" in ohio["reference_data"]["quota"]
    prague = next(p for p in partners if p["school_name"].startswith("布拉格化工大學 "))
    assert "不加總" in prague["quota"]
    assert all(p["availability_status"] != "open" for p in partners)
    assert all(p["field_evidence"]["language_requirement"]["status"] != "verified_current" for p in partners)


def test_no_common_mainland_timestamp_or_plan_word_count():
    card = get_verified_school_window_card("yzu")
    assert card.primary_deadline_at is None
    assert card.primary_deadline_date is None
    assert card.study_plan_limit.min_chars is None
    assert card.ics_download_url is None
    dashboard = json.loads((BUNDLE / "student_dashboard.json").read_text("utf8"))
    overseas, mainland = dashboard["application_periods"]
    assert overseas["opens_at"] is None
    assert overseas["deadline_at"] == "2026-09-22T12:00:00+08:00"
    assert mainland["deadline_at"] is None
    assert not mainland["reminder_eligible"]
    assert "院長" in dashboard["required_documents"][2]["details"][0]
