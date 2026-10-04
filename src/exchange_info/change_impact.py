"""Map a published rule change onto the student's own preparation tasks.

Task IDs carry the instruction signature, so a changed step becomes a new task
and the student's earlier progress stays attached to the old one. This module
only reports that relationship; it never edits progress, hours or deadlines.
"""
from __future__ import annotations

from .application_rules import compose_application_workflow
from .application_task_identity import preparation_identity
from .models import (
    AccountApplicationWorkspace,
    AffectedTaskImpact,
    ApplicationRuleContext,
    ApplicationStep,
    ApplicationWorkflowComparison,
    UniversityApplicationWorkflow,
)
from .notifications import matching_workspaces
from .task_documents import document_link_for_step

_DEADLINE_FIELDS = {"deadline_at", "deadline_status", "deadline_source_url", "timing", "submission"}
_DOCUMENT_FIELDS = {"document_requirements", "official_form_urls", "signature_requirements"}


def _context(workspace: AccountApplicationWorkspace, workflow: UniversityApplicationWorkflow) -> ApplicationRuleContext:
    saved = workspace.application_context
    return ApplicationRuleContext(
        home_university=workspace.home_school,
        partner_university=workflow.school_name,
        college=saved.college,
        department=saved.department,
        academic_year=saved.academic_year,
        application_round=saved.application_round or saved.semester,
    )


def _index(
    workflow: UniversityApplicationWorkflow | None, context: ApplicationRuleContext
) -> dict[str, tuple[str, ApplicationStep]]:
    from .content_governance import _step_identity

    if workflow is None:
        return {}
    composed = compose_application_workflow(workflow, context)
    return {
        _step_identity(step): (preparation_identity(composed, step, number)[0], step)
        for number, step in enumerate(composed.steps, start=1)
    }


def _status(workspace: AccountApplicationWorkspace, task_id: str | None, school: str) -> str | None:
    if task_id is None:
        return None
    saved = workspace.preparation_tasks.get(task_id)
    if saved is not None:
        return saved.status
    done = workspace.application_progress.get(school, {}).get(task_id)
    return "ready" if done else None


def affected_task_impacts(
    account,
    comparison: ApplicationWorkflowComparison,
    candidate: UniversityApplicationWorkflow,
    visible_keys: set[str],
) -> list[AffectedTaskImpact]:
    """Return one row per changed step that appears in the student's plan."""

    if not comparison.has_base or comparison.base_workflow is None:
        return []
    rows: list[AffectedTaskImpact] = []
    seen: set[str] = set()
    for workspace in matching_workspaces(account, candidate, None):
        context = _context(workspace, candidate)
        before_index = _index(comparison.base_workflow, context)
        after_index = _index(candidate, context)
        for change in comparison.step_changes:
            if change.step_key not in visible_keys or change.step_key in seen:
                continue
            before = before_index.get(change.step_key)
            after = after_index.get(change.step_key)
            if before is None and after is None:
                continue  # Scoped out of this student's department, year or round.
            seen.add(change.step_key)
            fields = {row.field for row in change.changes}
            previous_id = before[0] if before else None
            current_id = after[0] if after else None
            status = _status(workspace, previous_id, candidate.school_name) or _status(
                workspace, previous_id, workspace.home_school
            )
            settings = workspace.preparation_tasks.get(previous_id or "")
            has_settings = bool(
                settings and (
                    settings.effort_hours is not None or settings.remaining_hours is not None
                    or settings.waiting_reason or settings.document_id or settings.depends_on
                )
            )
            link = document_link_for_step(after[1]) if after else None
            title = change.title
            if change.change_type == "removed":
                action = "retired_task"
                guidance = (
                    f"官方新版已移除「{title}」。你原本的紀錄會保留，但不再列入準備清單；"
                    "請向承辦單位確認這項工作是否真的不用做。"
                )
            elif change.change_type == "added":
                action = "new_task"
                guidance = f"官方新版新增「{title}」，已列入你的準備清單；請先確認文件、期限與負責單位。"
            elif status == "ready":
                action = "recheck_completed"
                guidance = (
                    f"你把舊版「{title}」標為已完成，但官方內容已改變。新版是一項新的工作，"
                    "尚未標示完成；請對照變更後再決定是否重新完成。舊版的完成紀錄不會被刪除。"
                )
            else:
                action = "review_progress"
                guidance = (
                    f"官方更新了「{title}」。你在舊版記錄的工時、等待原因與文件連結仍保留在舊版，"
                    "新版需要重新設定；系統不會自動搬移。"
                    if has_settings or status
                    else f"官方更新了「{title}」，新版已列入你的準備清單，請重新核對。"
                )
            rows.append(
                AffectedTaskImpact(
                    step_key=change.step_key,
                    step_title=title,
                    change_type=change.change_type,
                    changed_fields=[row.label for row in change.changes],
                    deadline_changed=bool(fields & _DEADLINE_FIELDS),
                    documents_changed=bool(fields & _DOCUMENT_FIELDS),
                    previous_task_id=previous_id,
                    current_task_id=current_id,
                    previous_status=status,
                    has_personal_settings=has_settings,
                    action=action,
                    guidance=guidance,
                    document_template_ids=list(link.template_ids) if link else [],
                )
            )
    order = {"recheck_completed": 0, "review_progress": 1, "new_task": 2, "retired_task": 3}
    rows.sort(key=lambda row: (order[row.action], not row.deadline_changed, row.step_title))
    return rows
