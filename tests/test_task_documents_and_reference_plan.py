from __future__ import annotations

from datetime import date

import pytest

from exchange_info import storage
from exchange_info.application_plan_scheduling import schedule_application_plan
from exchange_info.application_rules import build_personal_application_plan
from exchange_info.models import (
    ApplicationDocumentRequirement,
    ApplicationPlanScheduleRequest,
    ApplicationStep,
    PersonalApplicationPlanRequest,
)
from exchange_info.plan_defaults import phase_rank, stage_gate_reason, suggest_effort_hours
from exchange_info.task_documents import audit_task_document_links, document_link_for_step


def step(title: str, *documents: str, phase: str = "校內申請") -> ApplicationStep:
    return ApplicationStep(
        order=1, phase=phase, title=title, responsible_party="學生", summary="說明",
        document_requirements=[ApplicationDocumentRequirement(name=name) for name in documents],
    )


def test_document_names_decide_the_tool_before_stage_defaults():
    link = document_link_for_step(step("完成申請", "簽名申請表", "交換研修計畫書", "家長同意資料（獲推薦後）"))
    assert link.template_ids == ["exchange-application-data", "study-plan", "guardian-consent"]
    assert link.basis == "document_name"
    assert link.unmapped_requirement_names == []


def test_uploads_without_a_tool_stay_listed_but_are_not_linked():
    link = document_link_for_step(step("依提名信完成合作校申請", "英文成績單", "護照影本", phase="合作校申請"))
    assert link.template_ids == []
    assert link.requirement_names == ["英文成績單", "護照影本"]
    assert link.unmapped_requirement_names == ["英文成績單", "護照影本"]


def test_steps_without_documents_or_a_matching_stage_have_no_link():
    assert document_link_for_step(step("等待校內甄選結果", phase="甄選與提名")) is None


def test_stage_only_match_is_last_resort_and_labelled():
    link = document_link_for_step(step("整理資料", phase="校內準備"))
    assert link.template_ids == ["exchange-application-data"]
    assert link.basis == "stage"


def test_every_bundled_step_is_either_linked_listed_or_documentless():
    workflows = storage.load_bundled_application_workflows()
    # CGU 77 (115) + 77 (116); NTPU 203 (115) + 206 (116); NTU 288 (116-1).
    assert len(workflows) == 1120
    ncu = [w for w in workflows if w.home_university == "國立中央大學"]
    assert len(ncu) == 214 and all(w.review_status == "pending_review" for w in ncu)
    ccu = [w for w in workflows if w.home_university == "國立中正大學"]
    assert len(ccu) == 55 and all(w.review_status == "legacy" for w in ccu)
    overall = audit_task_document_links(workflows)
    assert overall["steps"] == sum(len(row.steps) for row in workflows)
    # Keep the established schools' reviewed linkage contract separate from the
    # new CCU legacy and NCU pending host reference steps (including later health/arrival files).
    workflows = [w for w in workflows if w.home_university not in {"國立中央大學", "國立中正大學"}]
    assert len(workflows) == 851
    audit = audit_task_document_links(workflows)
    assert audit["steps"] == sum(len(row.steps) for row in workflows)
    assert audit["tool_linked"] + audit["requirements_only"] + audit["no_documents"] == audit["steps"]
    # Partner-side applications and visa/insurance paperwork use the partner's or a
    # government's own forms, so they stay list-only; every step on the home
    # school's own path must reach a preparation tool.
    allowed = ("依提名信", "辦理學生簽證")
    for row in audit["requirements_only_patterns"]:
        assert row["step_title"].startswith(allowed), row
    assert audit["tool_linked"] >= 1400


def test_partner_application_data_does_not_open_the_home_application_tool():
    link = document_link_for_step(
        step("依提名信完成合作校申請", "申請資料", "英文歷年成績單", "Learning Agreement／修課協議", phase="合作校申請")
    )
    assert "exchange-application-data" not in link.template_ids
    assert link.template_ids == ["course-preapproval"]
    link = document_link_for_step(step("接受錄取並完成選課", "出國選課行前申請資料", phase="錄取與行前"))
    assert "exchange-application-data" not in link.template_ids


def test_effort_suggestion_scales_with_documents_and_is_capped():
    light = suggest_effort_hours(step("確認資格"), None)
    heavy = suggest_effort_hours(
        step("完成申請", "交換研修計畫書", "有效語言證明", "簽名申請表", "正式成績單"), None
    )
    assert 1 <= light < heavy <= 30
    assert heavy * 2 == int(heavy * 2)


def test_stage_gate_only_holds_back_later_stages():
    assert phase_rank("校內申請") == 1 and phase_rank("不存在") is None
    assert stage_gate_reason(3, [1, 3]) is not None
    assert stage_gate_reason(3, [3, 4]) is None
    assert stage_gate_reason(1, [0]) is None
    assert stage_gate_reason(None, [0]) is None


def ntpu_plan(year: str, round_: str | None = "第一梯次"):
    workflows = [row for row in storage.load_bundled_application_workflows() if row.home_university == "國立臺北大學"]
    partners = {row.school_name for row in workflows}
    partner = sorted(partners)[0]
    request = PersonalApplicationPlanRequest(
        home_school="國立臺北大學", college="法律學院", academic_year=year, application_round=round_,
        preferences=[{"rank": 1, "school_name": partner}],
    )
    from exchange_info.models import PartnerUniversity
    return build_personal_application_plan(
        request,
        [PartnerUniversity(school_name=partner, program_type="交換", colleges="全校", degree_levels="大學部",
                           source_url="https://example.edu/p")],
        workflows, academic_score_minimum=70,
    ), workflows


def test_unpublished_year_gets_an_estimated_checklist_without_official_deadlines():
    years = {row.academic_year for row in storage.load_bundled_application_workflows() if row.home_university == "國立臺北大學"}
    assert years == {"115", "116"}
    plan, _ = ntpu_plan("117")
    choice = plan.choices[0]
    # The newest published period stands in for a year nobody has published yet.
    assert choice.reference_academic_year == "116"
    assert plan.tasks, "an unpublished year must still produce preparation work"
    assert all(task.task_origin == "reference_year" for task in plan.tasks)
    assert all(task.official_deadline_at is None and task.deadline_source_url is None for task in plan.tasks)
    assert all(task.title.startswith("預估：") and task.needs_confirmation for task in plan.tasks)
    assert all(task.id.startswith("application-task-ref-") for task in plan.tasks)
    assert all(task.suggested_effort_hours for task in plan.tasks)
    workflow_check = next(check for check in choice.checks if check.code == "workflow")
    assert workflow_check.status == "needs_confirmation" and "沒有官方期限" in workflow_check.detail


def test_published_year_keeps_official_tasks_and_no_reference():
    plan, _ = ntpu_plan("116", None)
    assert plan.choices[0].reference_academic_year is None
    assert all(task.task_origin == "official" for task in plan.tasks)


def test_estimated_tasks_are_scheduled_in_stage_order_with_later_stages_waiting():
    plan, _ = ntpu_plan("117")
    request = ApplicationPlanScheduleRequest(
        plan={"home_school": plan.home_school, "preferences": [{"rank": 1, "school_name": plan.choices[0].school_name}]},
        availability={"weekly_hours": 10, "weekdays": [1, 3, 5], "horizon_days": 60},
    )
    schedule = schedule_application_plan(plan, request, as_of=date(2026, 10, 5)).schedule
    by_id = {task.id: task for task in plan.tasks}
    scheduled = [by_id[session.event_id] for session in schedule.work_sessions]
    assert scheduled, "nothing could be scheduled from an estimated plan"
    assert {task.phase for task in scheduled} <= {"校內準備", "校內申請", "甄選與分發"}
    assert [task.order for task in scheduled] == sorted(task.order for task in scheduled)
    waiting = {issue.event_id for issue in schedule.issues if issue.code == "waiting"}
    assert waiting and all(phase_rank(by_id[key].phase) >= 3 for key in waiting)
    assert any(issue.code == "suggested_effort" and not issue.blocking for issue in schedule.issues)
    assert not any(issue.code == "missing_effort" for issue in schedule.issues)
    assert all(item.deadline_date is None for item in schedule.items)


def test_marking_earlier_stages_done_opens_the_next_stage():
    plan, _ = ntpu_plan("117")
    settings = {task.id: {"status": "ready"} for task in plan.tasks if phase_rank(task.phase) <= 2}
    request = ApplicationPlanScheduleRequest(
        plan={"home_school": plan.home_school, "preferences": [{"rank": 1, "school_name": plan.choices[0].school_name}]},
        availability={"weekly_hours": 10, "weekdays": [1, 3, 5], "horizon_days": 60}, task_settings=settings,
    )
    schedule = schedule_application_plan(plan, request, as_of=date(2026, 10, 5)).schedule
    by_id = {task.id: task for task in plan.tasks}
    phases = {by_id[session.event_id].phase for session in schedule.work_sessions}
    assert phases and min(phase_rank(phase) for phase in phases) >= 3
    assert not any(issue.code == "waiting" and phase_rank(by_id[issue.event_id].phase) == 3 for issue in schedule.issues)


def test_student_effort_overrides_the_suggestion_and_explicit_dependencies_skip_the_gate():
    plan, _ = ntpu_plan("117")
    first = plan.tasks[0]
    settings = {first.id: {"effort_hours": 4}}
    late = next(task for task in plan.tasks if phase_rank(task.phase) == 5)
    settings[late.id] = {"depends_on": []}
    request = ApplicationPlanScheduleRequest(
        plan={"home_school": plan.home_school, "preferences": [{"rank": 1, "school_name": plan.choices[0].school_name}]},
        availability={"weekly_hours": 10, "weekdays": [1, 3, 5], "horizon_days": 60}, task_settings=settings,
    )
    schedule = schedule_application_plan(plan, request, as_of=date(2026, 10, 5)).schedule
    item = next(row for row in schedule.items if row.event_id == first.id)
    assert item.effort_hours == 4
    assert not any(issue.event_id == first.id and issue.code == "suggested_effort" for issue in schedule.issues)
    assert not any(issue.event_id == late.id and issue.code == "waiting" for issue in schedule.issues)


def test_every_bundled_workflow_yields_a_schedulable_estimated_plan_for_an_unpublished_year():
    from exchange_info.models import PartnerUniversity

    workflows = storage.load_bundled_application_workflows()
    assert len(workflows) == 1120
    empty, unplannable = [], []
    for workflow in workflows:
        if len(workflow.school_name) > 200:
            # The plan API caps a school name at 200 characters. These two partner
            # names carry pasted requirement text and need a data fix, not a plan.
            unplannable.append(workflow.school_name[:20])
            continue
        partner = PartnerUniversity(
            program_type="交換", school_name=workflow.school_name, colleges="全校", degree_levels="大學部",
            source_url="https://example.edu/p",
        )
        request = PersonalApplicationPlanRequest(
            home_school=workflow.home_university, college="工學院", degree_level="大學部", academic_score=90,
            academic_year="120", application_round="第一梯次",
            preferences=[{"rank": 1, "school_name": workflow.school_name}],
        )
        plan = build_personal_application_plan(
            request, [partner], [row for row in workflows if row.home_university == workflow.home_university],
            academic_score_minimum=60,
        )
        if workflow.home_university == "國立中央大學":
            # No NCU workflow is published. Unknown years cannot borrow a
            # pending reference as an approved plan or scheduled deadline.
            assert workflow.review_status == "pending_review"
            assert not plan.tasks and not plan.choices[0].checklist
            continue
        scheduled = schedule_application_plan(
            plan,
            ApplicationPlanScheduleRequest(
                plan={"home_school": workflow.home_university,
                      "preferences": [{"rank": 1, "school_name": workflow.school_name}]},
                availability={"weekly_hours": 10, "weekdays": [1, 3, 5], "horizon_days": 90},
            ),
            as_of=date(2026, 10, 5),
        ).schedule
        if not plan.tasks or not scheduled.work_sessions:
            empty.append(workflow.school_name)
        assert all(task.official_deadline_at is None for task in plan.tasks)
    assert empty == []
    assert len(unplannable) <= 4  # two long names, in both NTPU rounds
