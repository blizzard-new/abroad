from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import date
from typing import Iterable

from .models import (
    AccountCalendarEvent,
    CalendarConflictGroup,
    CalendarConflictKind,
    CalendarConflictReport,
)
from .school_identity import school_identity_key


CALENDAR_CONFLICT_WINDOW_DAYS = 3


def _valid_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _conflict_id(
    start_date: str,
    end_date: str,
    events: list[AccountCalendarEvent],
) -> str:
    identity = "|".join(
        [
            start_date,
            end_date,
            *(sorted(event.id for event in events)),
        ]
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"calendar-conflict-{digest}"


def _school_names(events: Iterable[AccountCalendarEvent]) -> list[str]:
    display_by_key: dict[str, str] = {}
    for event in events:
        school_name = str(event.school_name or "").strip()
        if not school_name:
            continue
        display_by_key.setdefault(school_identity_key(school_name), school_name)
    return sorted(display_by_key.values(), key=str.casefold)


def build_calendar_conflict_report(
    events: Iterable[AccountCalendarEvent],
) -> CalendarConflictReport:
    """Find deterministic cross-plan deadline pressure without guessing dates."""

    deduplicated = {event.id: event for event in events}
    eligible = [
        event
        for event in deduplicated.values()
        if str(event.school_name or "").strip() and _valid_date(event.date)
    ]
    eligible.sort(key=lambda event: (event.date, event.title.casefold(), event.id))
    events_by_date: dict[str, list[AccountCalendarEvent]] = defaultdict(list)
    for event in eligible:
        events_by_date[event.date].append(event)

    dates = sorted(events_by_date)
    groups: list[CalendarConflictGroup] = []
    for index, start_date in enumerate(dates):
        start_value = _valid_date(start_date)
        if start_value is None:  # already filtered; keeps the boundary explicit
            continue
        for end_date in dates[index:]:
            end_value = _valid_date(end_date)
            if end_value is None:
                continue
            day_gap = (end_value - start_value).days
            if day_gap > CALENDAR_CONFLICT_WINDOW_DAYS:
                break
            grouped_events = list(events_by_date[start_date])
            if end_date != start_date:
                grouped_events.extend(events_by_date[end_date])
            school_names = _school_names(grouped_events)
            if len(school_names) < 2:
                continue
            kind = (
                CalendarConflictKind.SAME_DAY
                if day_gap == 0
                else CalendarConflictKind.TIGHT_WINDOW
            )
            resolution_hint = (
                "同一天有不同申請計畫的任務；請先確認不可延後的送件、紙本送達與交通安排。"
                if kind == CalendarConflictKind.SAME_DAY
                else (
                    f"不同申請計畫的任務相距 {day_gap} 天；"
                    "請把共用文件與簽核完成日提前，並分開確認每所學校的正式期限。"
                )
            )
            groups.append(
                CalendarConflictGroup(
                    id=_conflict_id(start_date, end_date, grouped_events),
                    kind=kind,
                    start_date=start_date,
                    end_date=end_date,
                    day_gap=day_gap,
                    school_names=school_names,
                    events=grouped_events,
                    resolution_hint=resolution_hint,
                )
            )

    groups.sort(
        key=lambda group: (
            group.start_date,
            group.day_gap,
            group.end_date,
            group.id,
        )
    )
    conflicting_event_ids = {
        event.id for group in groups for event in group.events
    }
    return CalendarConflictReport(
        analyzed_event_count=len(eligible),
        plan_count=len(_school_names(eligible)),
        conflict_count=len(groups),
        conflicting_event_count=len(conflicting_event_ids),
        same_day_conflict_count=sum(
            group.kind == CalendarConflictKind.SAME_DAY for group in groups
        ),
        tight_window_conflict_count=sum(
            group.kind == CalendarConflictKind.TIGHT_WINDOW for group in groups
        ),
        groups=groups,
    )
