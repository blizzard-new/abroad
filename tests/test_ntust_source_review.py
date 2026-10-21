from datetime import datetime

from exchange_info.ntust_eligibility import ntust_academic_check, ntust_language_check
from exchange_info.ntust_student_view import build_ntust_student_dashboard
from exchange_info.verified_window_deadlines import get_verified_school_window_card


def test_mainland_uses_its_own_average_and_requires_language():
    assert ntust_academic_check("學士班", 74, 4.0, 1, partner_country="中國大陸")[0] == "fail"
    assert ntust_academic_check("碩士班", 79, 4.0, 1, partner_country="中國大陸")[0] == "fail"
    assert ntust_academic_check("碩士班", 80, None, None, partner_country="中國大陸")[0] == "pass"
    assert ntust_academic_check("學士班", None, 4.0, 1, partner_country="中國大陸")[0] == "needs_confirmation"
    assert ntust_language_check(None, None, partner_country="中國大陸")[0] == "needs_confirmation"
    assert ntust_language_check("toeic", 549, partner_country="中國大陸")[0] == "fail"
    assert ntust_language_check("toeic", 550, partner_country="中國大陸")[0] == "pass"


def test_rank_needs_the_required_semester_and_allows_department_exception():
    assert ntust_academic_check("學士班", 100, 4.3, None, partner_country="德國")[0] == "needs_confirmation"
    assert ntust_academic_check("學士班", 90, 4.0, 75, partner_country="德國")[0] == "needs_confirmation"
    assert ntust_language_check("topik", 2, partner_country="韓國")[0] == "fail"
    assert ntust_language_check("toefl", 4, partner_country="美國")[0] == "needs_confirmation"
    assert ntust_language_check("toefl", 57, partner_country="美國")[0] == "pass"


def test_upcoming_round_and_paperless_advisory_limits():
    card = get_verified_school_window_card("ntust")
    assert card.primary_deadline_at == datetime.fromisoformat("2026-12-07T15:00:00+08:00")
    assert card.window_status == "upcoming"
    assert card.paper_deadline.submission_mode == "paperless"
    assert card.paper_deadline.exact_deadline_at is None
    assert card.study_plan_limit.max_pages is None
    dashboard = build_ntust_student_dashboard(reference_time=datetime.fromisoformat("2026-10-21T12:00:00+08:00"))
    current, mainland = dashboard.application_periods
    assert current.status == "upcoming"
    assert mainland.deadline_at == datetime.fromisoformat("2026-07-03T17:00:00+08:00")
    assert mainland.status == "closed"
    assert not mainland.reminder_eligible
