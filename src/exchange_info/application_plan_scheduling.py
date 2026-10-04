"""Project current sourced tasks and personal settings into a single capacity pool."""
from __future__ import annotations

from datetime import date

from .models import (
    ApplicationPlanScheduleRequest, ApplicationPlanScheduleResult,
    ApplicationPreparationTaskState, PersonalApplicationPlanResult, PreparationWorkItem,
)
from .plan_defaults import phase_rank, stage_gate_reason
from .workload_planning import build_workload_schedule


def schedule_application_plan(
    plan: PersonalApplicationPlanResult, request: ApplicationPlanScheduleRequest, *, as_of: date
) -> ApplicationPlanScheduleResult:
    # The caller must build plan from the current catalogue, never from a client snapshot.
    tasks = []
    excluded = {choice.school_name for choice in plan.choices if choice.status.value in {"ineligible", "unavailable"}}
    unfinished: list[tuple[set[str], int]] = []
    for task in plan.tasks:
        rank = phase_rank(task.phase)
        status = request.task_settings.get(task.id, ApplicationPreparationTaskState()).status
        if rank is not None and status != "ready":
            unfinished.append((set(task.school_names), rank))
    for task in plan.tasks:
        settings = request.task_settings.get(task.id, ApplicationPreparationTaskState())
        official = task.official_deadline_at.date() if task.official_deadline_at else None
        personal = settings.personal_due_date
        deadline = min(official, personal) if official and personal else official or personal
        kind = "official" if official and deadline == official else "personal" if personal else "unspecified"
        waiting = settings.waiting_reason
        if all(school in excluded for school in task.school_names):
            waiting = "目前志願不符合條件或未開放，請先核對資格／可申請狀態。"
        if (
            not waiting and deadline is None and settings.status != "ready"
            and settings.depends_on is None and settings.available_from is None
            and not task.dependency_ids
        ):
            # Undated work in a later stage waits for the earlier stages to be
            # marked done. Dated work keeps its own deadline-driven schedule.
            schools = set(task.school_names)
            waiting = stage_gate_reason(
                phase_rank(task.phase),
                (rank for names, rank in unfinished if names & schools),
            )
        effort, remaining = settings.effort_hours, settings.remaining_hours
        suggested = effort is None and remaining is None and task.suggested_effort_hours is not None
        if suggested:
            effort = task.suggested_effort_hours
        tasks.append(PreparationWorkItem(
            id=task.id, title=task.title[:120], date=deadline.isoformat() if deadline else None,
            deadline_kind=kind, origin="official" if kind == "official" else "personal",
            school_name=plan.home_school if task.task_scope == "home" else task.school_names[0],
            source_url=task.deadline_source_url, status=settings.status,
            effort_hours=effort, remaining_hours=remaining,
            depends_on=task.dependency_ids if settings.depends_on is None else settings.depends_on,
            available_from=settings.available_from, waiting_reason=waiting, document_id=settings.document_id,
            process_order=task.order, effort_is_suggested=suggested,
        ))
    # Personal calendar tasks share the same weekly capacity. Reserved source IDs
    # cannot shadow or resurrect a task from an obsolete published version.
    if any(row.id.startswith("application-task-") for row in request.personal_events):
        raise ValueError("日曆個人任務不可使用申請流程保留的識別碼。")
    tasks.extend(request.personal_events)
    return ApplicationPlanScheduleResult(plan=plan, schedule=build_workload_schedule(
        tasks, availability=request.availability, as_of=as_of))
