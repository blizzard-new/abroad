from datetime import date, datetime, timezone

import pytest

from exchange_info.application_plan_scheduling import schedule_application_plan
from exchange_info.models import ApplicationPlanScheduleRequest, PreparationWorkItem, PlanningAvailability
from exchange_info.workload_planning import build_workload_schedule
from test_multi_application_plan import make_plan


def request_for(plan, settings=None, **kwargs):
    return ApplicationPlanScheduleRequest(plan={"home_school":plan.home_school,
        "preferences":[{"rank":row.rank,"school_name":row.school_name} for row in plan.choices]},
        task_settings=settings or {}, availability={"weekly_hours":6,"weekdays":[1,3,5],"horizon_days":14}, **kwargs)


def test_common_and_branches_share_capacity_without_inventing_a_deadline():
    plan=make_plan()
    shared=next(row for row in plan.tasks if row.task_scope == "home")
    settings={row.id:{"effort_hours":2,"depends_on":[] if row.id == shared.id else [shared.id]} for row in plan.tasks}
    original=plan.model_dump()
    result=schedule_application_plan(plan,request_for(plan,settings),as_of=date(2026,10,5)).schedule
    assert [row.event_id for row in result.work_sessions][0] == shared.id
    assert len(result.work_sessions) == 3
    assert sum(row.hours for row in result.work_sessions) == 6
    assert len({row.date for row in result.work_sessions}) == 3
    assert all(row.deadline_date is None and row.deadline_kind == "unspecified" for row in result.items)
    assert all(row.code == "missing_deadline" and not row.blocking for row in result.issues)
    assert plan.model_dump() == original


def test_personal_goal_cannot_move_official_date_and_completed_is_not_recreated():
    plan=make_plan()
    shared=plan.tasks[0]
    shared.official_deadline_at=datetime(2026,10,9,tzinfo=timezone.utc)
    settings={row.id:{"effort_hours":2,"personal_due_date":"2026-10-30"} for row in plan.tasks}
    settings[plan.tasks[1].id]["status"]="ready"
    result=schedule_application_plan(plan,request_for(plan,settings),as_of=date(2026,10,5)).schedule
    item=next(row for row in result.items if row.event_id == shared.id)
    assert item.deadline_date == date(2026,10,9) and item.deadline_kind == "official"
    assert not any(row.event_id == plan.tasks[1].id for row in result.work_sessions)
    settings[shared.id]["personal_due_date"]="2026-10-6"  # Invalid personal dates fail validation.
    with pytest.raises(ValueError):
        request_for(plan,settings)


def test_stale_source_settings_are_not_scheduled_and_manual_tasks_share_capacity():
    plan=make_plan()
    settings={row.id:{"effort_hours":2} for row in plan.tasks}
    settings["application-task-old-version"]={"effort_hours":100}
    request=request_for(plan,settings,personal_events=[{"id":"personal","title":"個人工作","date":"2026-10-05","effort_hours":2}])
    result=schedule_application_plan(plan,request,as_of=date(2026,10,5)).schedule
    assert result.work_sessions[0].event_id == "personal"
    assert "application-task-old-version" not in {row.event_id for row in result.items}
    assert sum(row.hours for row in result.work_sessions if row.date == date(2026,10,5)) == 2
    request.personal_events[0].id=plan.tasks[0].id
    with pytest.raises(ValueError,match="保留"):
        schedule_application_plan(plan,request,as_of=date(2026,10,5))


def test_source_dependencies_remain_blocked_if_parent_was_removed_or_waiting():
    plan=make_plan()
    plan.tasks[1].dependency_ids=[plan.tasks[0].id]
    settings={row.id:{"effort_hours":2} for row in plan.tasks}
    settings[plan.tasks[0].id]["waiting_reason"]="等系辦回覆"
    result=schedule_application_plan(plan,request_for(plan,settings),as_of=date(2026,10,5)).schedule
    assert any(row.event_id == plan.tasks[1].id and row.code == "blocked_dependency" for row in result.issues)
    plan.tasks[1].dependency_ids=["removed-task"]
    result=schedule_application_plan(plan,request_for(plan,settings),as_of=date(2026,10,5)).schedule
    assert any(row.event_id == plan.tasks[1].id and row.code == "missing_dependency" for row in result.issues)


def test_completed_legacy_bad_date_does_not_block_its_unfinished_child():
    rows=[PreparationWorkItem(id="done",title="完成",date="2026-99-99",status="ready"),
          PreparationWorkItem(id="next",title="下一項",effort_hours=1,depends_on=["done"])]
    result=build_workload_schedule(rows,availability=PlanningAvailability(weekdays=[1]),as_of=date(2026,10,5))
    assert [row.event_id for row in result.work_sessions] == ["next"]
    assert next(row for row in result.issues if row.code == "invalid_date").blocking is False


def test_ineligible_branch_cannot_be_scheduled_as_available_work():
    plan=make_plan()
    from exchange_info.models import ApplicationPlanEligibilityStatus
    plan.choices[0].status=ApplicationPlanEligibilityStatus.INELIGIBLE
    result=schedule_application_plan(plan,request_for(plan,{row.id:{"effort_hours":1} for row in plan.tasks}),as_of=date(2026,10,5)).schedule
    branch=next(row for row in plan.tasks if row.task_scope == "partner" and row.school_names == [plan.choices[0].school_name])
    assert not any(row.event_id == branch.id for row in result.work_sessions)
    assert any(row.event_id == branch.id and row.code == "waiting" for row in result.issues)


def test_source_projection_requires_published_confirmed_timezone_and_explicit_dependencies():
    from exchange_info.application_rules import _workflow_checklist
    from exchange_info.models import ApplicationRuleContext, ApplicationStep, UniversityApplicationWorkflow
    first=ApplicationStep(rule_id="parent",order=1,phase="校內",title="先準備",summary="準備",responsible_party="學生")
    second=ApplicationStep(rule_id="child",depends_on_rule_ids=["parent","missing"],order=2,phase="送件",title="送件",
        summary="送件",responsible_party="學生",support_status="verified",deadline_status="verified_exact",
        deadline_at=datetime(2026,10,9,tzinfo=timezone.utc),deadline_checked_at=datetime(2026,10,1,tzinfo=timezone.utc),
        deadline_source_url="https://home.edu/deadline")
    workflow=UniversityApplicationWorkflow(home_university="測試大學",school_name="合作校",steps=[first,second],review_status="published",
        academic_year="116",application_round="第一梯次",
        applied_context=ApplicationRuleContext(academic_year="116",application_round="第一梯次"),
        applicability_status="verified",published_at=datetime(2026,10,1,tzinfo=timezone.utc))
    rows=_workflow_checklist(1,workflow,"國際處")
    assert rows[1].dependency_ids == [rows[0].id,"unresolved-rule:missing"]
    assert rows[1].official_deadline_at == second.deadline_at
    for updates in ({"deadline_checked_at":None},{"needs_confirmation":True},{"deadline_at":datetime(2026,10,9)}):
        workflow.steps[1]=second.model_copy(update=updates)
        assert _workflow_checklist(1,workflow,"國際處")[1].official_deadline_at is None
    workflow.steps[1]=second
    workflow.review_status="draft"
    assert _workflow_checklist(1,workflow,"國際處")[1].official_deadline_at is None
    assert "depends_on_rule_ids" not in first.model_dump()  # No hash drift for existing publications.
    assert second.model_dump()['depends_on_rule_ids'] == ['parent','missing']


def test_common_rule_survives_storage_structure_and_reload(tmp_path):
    from exchange_info.models import ApplicationRuleScope, ApplicationStep, UniversityApplicationWorkflow
    from exchange_info.storage import replace_application_workflow, load_application_workflows
    from exchange_info.workflow_structuring import workflow_structure_issues
    step=ApplicationStep(rule_id="home-common",order=1,phase="校內申請",title="校內準備",summary="準備",
        responsible_party="學生",scope=ApplicationRuleScope(home_universities=["測試大學"]))
    for name in ("合作校甲","合作校乙"):
        replace_application_workflow(UniversityApplicationWorkflow(home_university="測試大學",school_name=name,steps=[step]),tmp_path)
    rows=load_application_workflows(tmp_path)
    assert len(rows) == 2
    assert all(row.steps[0].scope.partner_universities == [] for row in rows)
    assert all("home-common:missing_partner_scope" not in workflow_structure_issues(row) for row in rows)
