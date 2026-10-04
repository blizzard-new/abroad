from datetime import date

import pytest
from pydantic import ValidationError

from exchange_info.calendar_task_scheduling import build_calendar_task_schedule
from exchange_info.models import AccountCalendarEvent, PlanningAvailability


def task(key, *, deadline="2026-10-09", hours=2, **kwargs):
    return AccountCalendarEvent(id=key, title=key, date=deadline, effort_hours=hours, **kwargs)


def plan(events, *, today=date(2026, 10, 5), weekly_hours=6, weekdays=(1, 3, 5), horizon_days=30):
    return build_calendar_task_schedule(events, as_of=today, availability=PlanningAvailability(
        weekly_hours=weekly_hours, weekdays=list(weekdays), horizon_days=horizon_days))


def test_capacity_and_dependencies_are_respected_across_schools():
    events = [task("school-a", depends_on=["common"]), task("school-b", depends_on=["common"]), task("common")]
    original = [row.model_dump() for row in events]
    result = plan(events)
    assert [(row.event_id, row.date, row.hours) for row in result.work_sessions] == [
        ("common", date(2026, 10, 5), 2), ("school-a", date(2026, 10, 7), 2), ("school-b", date(2026, 10, 9), 2)]
    assert result.issues == []
    assert result.mode == "workload"
    assert [row.model_dump() for row in events] == original


def test_replan_uses_remaining_effort_keeps_completed_and_never_moves_deadlines():
    result = plan([task("finished", status="ready"), task("partial", hours=8, remaining_hours=1, status="preparing"),
                   task("next", depends_on=["finished", "partial"])])
    assert not any(row.event_id == "finished" for row in result.work_sessions)
    assert sum(row.hours for row in result.work_sessions if row.event_id == "partial") == 1
    assert all(row.date >= date(2026, 10, 5) for row in result.work_sessions)
    assert all(row.deadline_date == date(2026, 10, 9) for row in result.items)
    monday = [row for row in result.work_sessions if row.date == date(2026, 10, 5)]
    assert [row.event_id for row in monday] == ["partial", "next"]
    assert monday[0].sequence < monday[1].sequence


def test_missing_effort_is_not_guessed_from_lead_days_and_blocks_dependents():
    result = plan([task("estimate", hours=None, preparation_days=14), task("child", depends_on=["estimate"]), task("independent")])
    assert {(row.event_id, row.code) for row in result.issues} >= {("estimate", "missing_effort"), ("child", "blocked_dependency")}
    assert [row.event_id for row in result.work_sessions] == ["independent"]
    assert next(row for row in result.items if row.event_id == "estimate").suggested_start_date is None


def test_cycles_missing_references_and_waiting_do_not_block_independent_work():
    result = plan([task("a", depends_on=["b"]), task("b", depends_on=["a"]), task("c", depends_on=["a"]),
                   task("missing", depends_on=["nonexistent"]), task("wait", waiting_reason="校方確認"), task("ok")])
    codes = {(row.event_id, row.code) for row in result.issues}
    assert {("a", "dependency_cycle"), ("b", "dependency_cycle"), ("c", "blocked_dependency"),
            ("missing", "missing_dependency"), ("wait", "waiting")} <= codes
    assert [row.event_id for row in result.work_sessions] == ["ok"]


def test_shortfall_is_visible_and_no_work_is_scheduled_after_deadline():
    result = plan([task("urgent", deadline="2026-10-06", hours=8)])
    assert sum(row.hours for row in result.work_sessions) == 2
    assert result.items[0].unscheduled_hours == 6
    assert result.items[0].urgency == "blocked"
    assert result.issues[0].code == "capacity"
    assert all(row.date <= date(2026, 10, 6) for row in result.work_sessions)


def test_late_and_invalid_dates_are_reported_without_fabrication():
    result = plan([task("late", deadline="2026-09-30"), task("bad", deadline="2026-99-99")])
    assert result.work_sessions == []
    assert {(row.event_id, row.code) for row in result.issues} == {("late", "deadline_passed"), ("bad", "invalid_date")}
    assert result.items[0].deadline_date == date(2026, 9, 30)


def test_release_date_and_preview_horizon_are_respected():
    result = plan([task("release", available_from=date(2026, 10, 7)), task("distant", deadline="2027-10-01", hours=80)], horizon_days=7)
    assert next(row for row in result.work_sessions if row.event_id == "release").date == date(2026, 10, 7)
    assert all(row.date <= date(2026, 10, 11) for row in result.work_sessions)
    assert any(row.event_id == "distant" and row.code == "outside_horizon" for row in result.issues)


def test_shared_capacity_and_predecessor_deadline_priority():
    result = plan([task("parent", deadline="2026-10-30"), task("child", deadline="2026-10-05", depends_on=["parent"]),
                   task("later", deadline="2026-10-09")], weekly_hours=12)
    assert [(row.event_id, row.sequence) for row in result.work_sessions if row.date == date(2026, 10, 5)] == [("parent", 1), ("child", 2)]
    totals = {}
    for row in result.work_sessions:
        totals[row.date] = totals.get(row.date, 0) + row.hours
    assert all(total <= 4 for total in totals.values())


def test_zero_remaining_requires_student_confirmation_and_model_rejects_invalid_weekdays():
    result = plan([task("zero", remaining_hours=0)])
    assert result.issues[0].code == "confirm_completion"
    assert result.items[0].status == "todo"
    with pytest.raises(ValidationError):
        PlanningAvailability(weekdays=[0])
    assert PlanningAvailability(weekdays=[1, 1, 3]).weekdays == [1, 3]
