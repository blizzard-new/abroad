from __future__ import annotations

import json
from pathlib import Path

from exchange_info.nycu_eligibility import nycu_academic_check, nycu_degree_check, nycu_language_check
from exchange_info.nycu_source_review import load_snapshot
from exchange_info.verified_window_deadlines import get_verified_school_window_card

ROOT = Path(__file__).parents[1]
FOLDER = ROOT / "src/exchange_info/official_data/nycu"


def rows(name):
    return [json.loads(s) for s in (FOLDER / name).read_text("utf8").splitlines()]


def test_review_total_is_not_an_academic_or_cumulative_gpa_cutoff():
    assert nycu_academic_check("學士班", 58, 1.5, 90)[0] == "needs_confirmation"
    assert nycu_academic_check("碩士班", 95, 4.3, 1)[0] == "needs_confirmation"
    assert nycu_degree_check("學士班", None)[0] == "needs_confirmation"
    assert nycu_degree_check("系統工程與科技學位學程", "大二")[0] == "needs_confirmation"
    assert nycu_language_check("toeic", 990, partner_country="美國")[0] == "needs_confirmation"
    assert nycu_language_check("jlpt", 5, partner_country="日本")[0] == "needs_confirmation"


def test_only_current_ust_deadline_can_create_a_reminder():
    periods = json.loads((FOLDER / "student_dashboard.json").read_text("utf8"))["application_periods"]
    active = [p for p in periods if p["reminder_eligible"]]
    assert len(active) == 1
    assert active[0]["deadline_at"] == "2026-12-31T16:00:00+08:00"
    assert active[0]["opens_at"] is None
    assert "ex-out@nycu.edu.tw" in active[0]["deadline_note"]
    assert all(p["deadline_at"] is None for p in periods if not p["reminder_eligible"])
    card = get_verified_school_window_card("nycu")
    assert card.primary_deadline_date == "2026-12-31"
    assert card.study_plan_limit.max_pages is None


def test_old_ust_hosts_do_not_inherit_the_116_ust_deadline():
    partners = rows("partners.jsonl")
    active = {p["school_name"] for p in partners if p["availability_status"] == "open"}
    assert active == {
        "南洋理工大學 Nanyang Technological University",
        "香港城市大學 City University of Hong Kong",
        "香港中文大學 The Chinese University of Hong Kong",
        "伯恩大學 University of Bern",
    }
    for w in rows("application_workflows.jsonl"):
        reminders = [s for s in w["steps"] if s["deadline_reminder_eligible"]]
        if w["school_name"] in active:
            assert len(reminders) == 1
            assert reminders[0]["submission"]["email"] == "ex-out@nycu.edu.tw"
        else:
            assert not reminders


def test_official_table_keeps_faculty_rows_and_has_no_color_inference():
    snapshot = load_snapshot(ROOT)
    assert len(snapshot["table_matches"]) == 182
    assert len(set(snapshot["table_matches"].values())) == 182
    peking = next(g for g in snapshot["table_groups"] if "Peking University" in g["name"])
    quotas = [r["cells"][3] for r in peking["rows"] if r["cells"][3]]
    assert quotas == ["3/sem.", "1 student"]
    assert snapshot["whole_record_verified"] is False
    assert snapshot["table_limitations"]
    assert "University of California, Santa Cruz" in snapshot["ust_hosts"]
    assert not any("Santa Cruz" in p["school_name"] for p in rows("partners.jsonl"))


def test_common_documents_match_chinese_115_forms_and_three_signatures():
    docs = json.loads((FOLDER / "documents.json").read_text("utf8"))["required_documents"]
    text = "\n".join(docs)
    assert "中文歷年等第成績單" in text
    assert "申請人、導師／指導教授、系主任／所長三處簽章" in text
    assert "中文非母語者可用英文" in text
    assert "一封教授英文推薦函" in text
    assert all(w["applicability_status"] == "needs_confirmation" for w in rows("application_workflows.jsonl"))
