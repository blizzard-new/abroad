from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable
from zoneinfo import ZoneInfo

from .models import (
    AccountCalendarEvent,
    CalendarTaskScheduleItem,
    CalendarTaskScheduleReport,
    CalendarTaskUrgency,
    PlanningAvailability,
)


TAIPEI_TIMEZONE = ZoneInfo("Asia/Taipei")


def _valid_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _recommended_reminder_days(preparation_days: int) -> list[int]:
    checkpoints = [
        preparation_days,
        max(1, preparation_days // 2),
        7,
        3,
        1,
        0,
    ]
    return sorted(
        {day for day in checkpoints if 0 <= day <= preparation_days},
        reverse=True,
    )


def build_calendar_task_schedule(
    events: Iterable[AccountCalendarEvent],
    *,
    as_of: date | None = None,
    availability: PlanningAvailability | None = None,
) -> CalendarTaskScheduleReport:
    """Arrange user-estimated preparation windows without inferring durations."""

    current = as_of or datetime.now(TAIPEI_TIMEZONE).date()
    if availability is not None:
        from .workload_planning import build_workload_schedule

        return build_workload_schedule(events, availability=availability, as_of=current)
    deduplicated = {event.id: event for event in events}
    items: list[CalendarTaskScheduleItem] = []
    for event in deduplicated.values():
        deadline = _valid_date(event.date)
        if (
            deadline is None
            or event.preparation_days < 1
            or event.generated_from_event_id
        ):
            continue
        suggested_start = deadline - timedelta(days=event.preparation_days)
        days_until_start = (suggested_start - current).days
        days_until_deadline = (deadline - current).days
        if event.status == "ready":
            urgency = CalendarTaskUrgency.COMPLETED
            reason = "這項任務已完成，系統不再安排開始提醒。"
            reminders: list[int] = []
        elif days_until_deadline < 0:
            urgency = CalendarTaskUrgency.OVERDUE
            reason = "期限已過但任務仍未完成；請先核對官方狀態，再更新任務。"
            reminders = [0]
        elif days_until_deadline <= 3:
            urgency = CalendarTaskUrgency.DUE_SOON
            reason = f"距離期限只剩 {days_until_deadline} 天，請優先處理並確認送件方式。"
            reminders = [day for day in [3, 1, 0] if day <= days_until_deadline]
        elif days_until_start <= 0:
            urgency = CalendarTaskUrgency.START_NOW
            reason = (
                f"依你設定的 {event.preparation_days} 天準備時間，現在應開始處理。"
            )
            reminders = [day for day in _recommended_reminder_days(event.preparation_days) if day <= days_until_deadline]
        else:
            urgency = CalendarTaskUrgency.SCHEDULED
            reason = (
                f"依你設定的 {event.preparation_days} 天準備時間，"
                f"建議於 {suggested_start.isoformat()} 開始。"
            )
            reminders = _recommended_reminder_days(event.preparation_days)
        items.append(
            CalendarTaskScheduleItem(
                event_id=event.id,
                title=event.title,
                school_name=event.school_name,
                deadline_date=deadline,
                suggested_start_date=suggested_start,
                preparation_days=event.preparation_days,
                status=event.status,
                urgency=urgency,
                days_until_start=days_until_start,
                days_until_deadline=days_until_deadline,
                recommended_reminder_days=reminders,
                reason=reason,
            )
        )

    urgency_order = {
        CalendarTaskUrgency.OVERDUE: 0,
        CalendarTaskUrgency.DUE_SOON: 1,
        CalendarTaskUrgency.START_NOW: 2,
        CalendarTaskUrgency.SCHEDULED: 3,
        CalendarTaskUrgency.COMPLETED: 4,
    }
    items.sort(
        key=lambda item: (
            urgency_order[item.urgency],
            item.deadline_date,
            item.title.casefold(),
            item.event_id,
        )
    )
    return CalendarTaskScheduleReport(
        as_of=current,
        analyzed_event_count=len(items),
        incomplete_count=sum(item.status != "ready" for item in items),
        scheduled_count=sum(item.urgency == CalendarTaskUrgency.SCHEDULED for item in items),
        start_now_count=sum(item.urgency == CalendarTaskUrgency.START_NOW for item in items),
        due_soon_count=sum(item.urgency == CalendarTaskUrgency.DUE_SOON for item in items),
        overdue_count=sum(item.urgency == CalendarTaskUrgency.OVERDUE for item in items),
        completed_count=sum(item.urgency == CalendarTaskUrgency.COMPLETED for item in items),
        items=items,
    )
