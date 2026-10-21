from pathlib import Path
import json

from exchange_info.application_documents import all_application_templates
from exchange_info.ntut_eligibility import ntut_academic_check, ntut_language_check
from exchange_info.ntut_student_view import build_ntut_student_dashboard
from exchange_info.verified_window_deadlines import (
    build_verified_window_deadline_catalog,
)

ROOT = Path(__file__).parents[1]


def test_exchange_has_no_home_academic_floor_but_dual_degree_is_separate():
    status, detail = ntut_academic_check("學士班", 60, 1.5, 90)
    assert status == "pass"
    assert "獎學金" in detail and "接待校" in detail
    assert ntut_academic_check("學士班", 99, 4.3, 1, program_type="雙聯學位")[0] == "needs_confirmation"
    assert ntut_language_check("jlpt", 5, partner_country="日本")[0] == "needs_confirmation"
    assert ntut_language_check(None, None, partner_country="中國大陸")[0] == "needs_confirmation"


def test_recurring_calendar_does_not_create_a_current_deadline():
    card = next(c for c in build_verified_window_deadline_catalog().items if c.school_id == "ntut")
    assert card.primary_deadline_at is None and card.primary_deadline_date is None
    assert not card.subtasks and not card.ics_download_url
    assert card.paper_deadline.submission_mode == "signed_scan_upload"
    assert card.study_plan_limit.max_pages == 1
    assert "不收紙本" in card.paper_deadline.value_text


def test_tku_whole_application_limit_is_not_a_plan_limit():
    card = next(c for c in build_verified_window_deadline_catalog().items if c.school_id == "tku")
    assert card.study_plan_limit.max_pages is None
    assert "全部文件合計不超過16頁" in card.study_plan_limit.value_text
    assert card.paper_deadline.exact_deadline_at is None
    assert card.online_deadline.exact_deadline_at.day == 30


def test_current_mother_list_explicit_closures_are_not_open():
    d = build_ntut_student_dashboard()
    assert d.maximum_preferences == 10
    assert d.academic_score_minimum is None and d.language_score_minimums == {}
    assert not any(p.availability_status == "open" for p in d.partner_universities)
    closed = [p for p in d.partner_universities if p.availability_status == "not_open"]
    assert len(closed) == 2
    assert all(p.country == "瓜地馬拉" for p in closed)
    assert all(p.reference_data for p in d.partner_universities)
    assert all(p.field_evidence["language_requirement"].status == "needs_confirmation" for p in d.partner_universities)


def test_preparation_tools_do_not_restore_obsolete_paper_or_score_rules():
    templates = all_application_templates("ntut")
    text = json.dumps([t.model_dump(mode="json") for t in templates], ensure_ascii=False)
    assert "不收紙本" in text
    assert "www.cc.ntut.edu.tw" not in text
    assert "前 30%" not in text and "前 50%" not in text
    assert "上限 5 項" not in text
    assert "2000字" in text and "3000字" in text


def test_default_country_costs_do_not_become_verified_school_budgets():
    from exchange_info.models import DestinationProfile
    from exchange_info.cost_estimates import extract_monthly_estimates, primary_estimate
    path = ROOT / "src/exchange_info/official_data/ntut/destination_profiles.jsonl"
    for line in path.read_text("utf8").splitlines():
        raw = json.loads(line)
        assert raw["reference_data"]["cost_summary"]
        dest = DestinationProfile.model_validate(raw)
        assert primary_estimate(extract_monthly_estimates(dest)) is None
