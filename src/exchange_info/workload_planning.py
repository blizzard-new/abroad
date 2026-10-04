"""Deterministic, preview-only planning from student effort and availability.

Official deadlines and task status are immutable inputs. Dependencies are
explicit task IDs; text order is never treated as evidence of a dependency.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable

from .models import (
    AccountCalendarEvent,
    CalendarTaskScheduleItem,
    CalendarTaskScheduleReport,
    CalendarTaskUrgency,
    PlanningAvailability,
    PlanningScheduleIssue,
    PlanningWorkSession,
)


def build_workload_schedule(
    events: Iterable[AccountCalendarEvent], *, availability: PlanningAvailability, as_of: date
) -> CalendarTaskScheduleReport:
    tasks = {event.id: event for event in events if not event.generated_from_event_id}
    deadlines: dict[str, date] = {}
    issues: list[PlanningScheduleIssue] = []
    blocked: set[str] = set()
    end = as_of + timedelta(days=availability.horizon_days - 1)

    def issue(key: str, code: str, detail: str, *, blocking: bool = True) -> None:
        if not any(row.event_id == key and row.code == code for row in issues):
            issues.append(PlanningScheduleIssue(event_id=key, code=code, detail=detail, blocking=blocking))
        if blocking:
            blocked.add(key)

    dependencies = {key: list(dict.fromkeys(task.depends_on)) for key, task in tasks.items()}
    for key, task in tasks.items():
        try:
            if task.date is not None:
                deadlines[key] = date.fromisoformat(task.date)
            elif task.status != "ready":
                issue(key, "missing_deadline", "未設定完成期限；僅依預覽期間安排個人準備，不代表官方申請期限。", blocking=False)
        except ValueError:
            issue(key, "invalid_date", "日期無法解析，請核對原任務日期；未改寫期限。", blocking=task.status != "ready")
        if task.status == "ready":
            continue
        missing = [dep for dep in dependencies[key] if dep not in tasks]
        if missing:
            issue(key, "missing_dependency", "找不到前置任務：" + "、".join(missing))
        if task.waiting_reason:
            issue(key, "waiting", "正在等待：" + task.waiting_reason)
        if task.effort_hours is None and task.remaining_hours is None:
            issue(key, "missing_effort", "先填預估工作時數；準備天數不等於工作時數。")
        elif getattr(task, "effort_is_suggested", False):
            issue(
                key, "suggested_effort",
                f"先以系統建議的約 {task.effort_hours:g} 小時安排（依文件數量與類型的通用估計，不是校方規定）；"
                "可在「安排工時與文件」改成你的實際工時。",
                blocking=False,
            )
        if task.remaining_hours == 0:
            issue(key, "confirm_completion", "剩餘工時為 0，請確認是否已完成；系統未自動更改完成狀態。")
        if key in deadlines and deadlines[key] < as_of:
            issue(key, "deadline_passed", "期限已過，請向校方確認處理方式；不把官方期限往後移。")

    # Detect genuine cycle members, including self-dependencies. Completed tasks
    # already satisfy dependencies and need no new work or prerequisite checks.
    visited: set[str] = set()
    active: list[str] = []
    order: list[str] = []

    def visit(key: str) -> None:
        if key in active:
            for member in active[active.index(key):]:
                issue(member, "dependency_cycle", "前置任務形成循環，請修改依賴後重新預覽。")
            return
        if key in visited:
            return
        active.append(key)
        if tasks[key].status != "ready":
            for dep in dependencies[key]:
                if dep in tasks:
                    visit(dep)
        active.pop()
        visited.add(key)
        order.append(key)

    for key in sorted(tasks):
        visit(key)
    for key in order:
        if tasks[key].status != "ready" and key not in blocked and any(dep in blocked for dep in dependencies[key]):
            issue(key, "blocked_dependency", "前置任務尚不能安排，請先處理它的缺口或等待事項。")

    effective_due = {key: deadlines.get(key, end + timedelta(days=1)) for key in tasks}
    for key in reversed(order):
        if key not in effective_due or key in blocked or tasks[key].status == "ready":
            continue
        for dep in dependencies[key]:
            if dep in effective_due and tasks[dep].status != "ready":
                effective_due[dep] = min(effective_due[dep], effective_due[key])

    order_hint = {
        key: process_order for key, task in tasks.items()
        if (process_order := getattr(task, "process_order", None)) is not None
    }
    remaining = {
        key: float(task.remaining_hours if task.remaining_hours is not None else task.effort_hours or 0)
        for key, task in tasks.items()
    }
    finished = {key for key, task in tasks.items() if task.status == "ready"}
    sessions: list[PlanningWorkSession] = []
    daily_hours = availability.weekly_hours / len(availability.weekdays)
    current = as_of
    while current <= end:
        if current.isoweekday() not in availability.weekdays:
            current += timedelta(days=1)
            continue
        capacity = daily_hours
        sequence = 0
        while capacity > 0.000001:
            eligible = [
                key for key, task in tasks.items()
                if key not in blocked and key not in finished
                and (key not in deadlines or deadlines[key] >= current)
                and (task.available_from is None or task.available_from <= current)
                and all(dep in finished for dep in dependencies[key])
                and remaining[key] > 0.000001
            ]
            if not eligible:
                break
            key = min(eligible, key=lambda value: (
                effective_due[value], deadlines.get(value, end + timedelta(days=1)),
                order_hint.get(value, 1_000_000), value))
            hours = min(capacity, remaining[key])
            sequence += 1
            sessions.append(PlanningWorkSession(event_id=key, date=current, hours=hours, sequence=sequence))
            remaining[key] = max(0, remaining[key] - hours)
            capacity = max(0, capacity - hours)
            if remaining[key] <= 0.000001:
                finished.add(key)
        current += timedelta(days=1)

    by_task: dict[str, list[PlanningWorkSession]] = defaultdict(list)
    for session in sessions:
        by_task[session.event_id].append(session)
    for key, task in tasks.items():
        if key in blocked or key in finished:
            continue
        if any(dep not in finished for dep in dependencies[key]):
            issue(key, "blocked_dependency", "前置任務未能在可用時間內完成，這項任務尚不能開始。")
        elif key not in deadlines or deadlines[key] > end:
            issue(key, "outside_horizon", f"預覽期間內仍有 {remaining[key]:g} 小時未安排，可增加預覽天數後重算。")
        else:
            issue(key, "capacity", f"期限前可用時間不足，仍有 {remaining[key]:g} 小時未安排；請調整工作量或可投入時間。")

    items: list[CalendarTaskScheduleItem] = []
    for key, task in tasks.items():
        if key not in deadlines and task.date is not None:
            continue  # Invalid dates are reported as issues, never substituted.
        deadline = deadlines.get(key)
        rows = by_task[key]
        start = rows[0].date if rows else None
        finish = rows[-1].date if rows else None
        task_issues = [row.detail for row in issues if row.event_id == key]
        if task.status == "ready":
            urgency = CalendarTaskUrgency.COMPLETED
            reason = "這項任務已完成，重排不會重新建立工作。"
        elif deadline and deadline < as_of:
            urgency = CalendarTaskUrgency.OVERDUE
            reason = "期限已過，需先確認官方處理方式。"
        elif key in blocked:
            urgency = CalendarTaskUrgency.BLOCKED
            reason = "；".join(task_issues)
        elif deadline and (deadline - as_of).days <= 3:
            urgency = CalendarTaskUrgency.DUE_SOON
            reason = "期限將近，已依工作時數與前置任務安排。"
        elif start == as_of:
            urgency = CalendarTaskUrgency.START_NOW
            reason = "今天有可執行的準備工作。"
        else:
            urgency = CalendarTaskUrgency.SCHEDULED
            reason = "已依可準備星期、每週時數及前置任務安排；這是個人工作計畫。"
        items.append(CalendarTaskScheduleItem(
            event_id=key, title=task.title, school_name=task.school_name,
            deadline_date=deadline, suggested_start_date=start,
            deadline_kind=getattr(task, "deadline_kind", task.origin),
            preparation_days=max(1, task.preparation_days), status=task.status,
            urgency=urgency, days_until_start=(start - as_of).days if start else 0,
            days_until_deadline=(deadline - as_of).days if deadline else None,
            recommended_reminder_days=[] if task.status == "ready" else [0], reason=reason,
            effort_hours=task.effort_hours, remaining_hours=task.remaining_hours,
            scheduled_hours=sum(row.hours for row in rows),
            unscheduled_hours=0 if task.status == "ready" else remaining[key],
            suggested_finish_date=finish, dependency_ids=dependencies[key], document_id=task.document_id,
        ))
    items.sort(key=lambda item: (item.status == "ready", item.deadline_date or date.max, item.event_id))
    return CalendarTaskScheduleReport(
        as_of=as_of, mode="workload", availability=availability,
        analyzed_event_count=len(items), incomplete_count=sum(row.status != "ready" for row in items),
        scheduled_count=sum(row.urgency == CalendarTaskUrgency.SCHEDULED for row in items),
        start_now_count=sum(row.urgency == CalendarTaskUrgency.START_NOW for row in items),
        due_soon_count=sum(row.urgency == CalendarTaskUrgency.DUE_SOON for row in items),
        overdue_count=sum(row.urgency == CalendarTaskUrgency.OVERDUE for row in items),
        completed_count=sum(row.urgency == CalendarTaskUrgency.COMPLETED for row in items),
        blocked_count=sum(row.urgency == CalendarTaskUrgency.BLOCKED for row in items),
        items=items, work_sessions=sessions, issues=issues,
    )
