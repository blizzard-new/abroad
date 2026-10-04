from datetime import datetime, timezone

from exchange_info.application_rules import build_personal_application_plan
from exchange_info.application_task_identity import NTPU_GUIDELINE
from exchange_info.models import (
    ApplicationRuleScope, ApplicationStep, ApplicationWorkflowSource,
    PartnerUniversity, PersonalApplicationPlanRequest, UniversityApplicationWorkflow,
)


def make_plan(*, order=("合作校甲", "合作校乙"), modified=False, home_scope=True):
    partners = [PartnerUniversity(school_name=name, program_type="交換", colleges="工學院",
                degree_levels="大學部", eligibility="IELTS 6.0", source_url="https://home.edu/partners")
                for name in order]
    workflows = []
    for name in order:
        shared = ApplicationStep(rule_id="home-submit", order=1, phase="校內申請", title="校內送件",
            responsible_party="學生", responsible_unit="國際處", summary="核對表格並送件",
            scope=ApplicationRuleScope(home_universities=["測試大學"], partner_universities=[] if home_scope else [name]),
            source_urls=["https://home.edu/notice"], support_status="verified")
        if modified and name == "合作校乙":
            shared.summary = "送件前另須系主任簽章"
        branch = shared.model_copy(deep=True, update={"rule_id":"host-submit", "title":"合作校送件",
            "scope":ApplicationRuleScope(partner_universities=[name]), "phase":"合作校申請"})
        workflows.append(UniversityApplicationWorkflow(home_university="測試大學", school_name=name,
            academic_year="116", application_round="第一梯次", steps=[shared,branch]))
    request = PersonalApplicationPlanRequest(home_school="測試大學",college="工學院", academic_year="116",
        application_round="第一梯次", preferences=[{"rank":i+1,"school_name":name} for i,name in enumerate(order)])
    before = [row.model_dump(mode="json") for row in workflows]
    plan = build_personal_application_plan(request, partners, workflows, academic_score_minimum=75)
    assert before == [row.model_dump(mode="json") for row in workflows]
    return plan


def test_shared_home_work_once_and_host_branches_remain_distinct():
    plan = make_plan()
    shared = [task for task in plan.tasks if task.task_scope == "home"]
    assert len(shared) == 1
    assert shared[0].school_names == ["合作校甲","合作校乙"]
    assert len(plan.tasks) == 3
    assert plan.choices[0].checklist[0].id == plan.choices[1].checklist[0].id
    assert plan.choices[0].checklist[1].id != plan.choices[1].checklist[1].id


def test_reordering_and_removing_preferences_does_not_change_task_identity():
    first = make_plan()
    reordered = make_plan(order=("合作校乙","合作校甲"))
    assert {task.id for task in first.tasks} == {task.id for task in reordered.tasks}
    remaining = make_plan(order=("合作校乙",))
    assert {task.id for task in remaining.tasks}.issubset({task.id for task in first.tasks})


def test_identical_title_does_not_merge_partner_scoped_or_conflicting_rules():
    assert len(make_plan(home_scope=False).tasks) == 4
    changed = make_plan(modified=True)
    assert len(changed.tasks) == 4
    assert changed.choices[0].checklist[0].source_signature != changed.choices[1].checklist[0].source_signature


def test_changed_deadline_gets_new_identity_but_checked_timestamp_does_not():
    from exchange_info.application_task_identity import preparation_identity
    step = ApplicationStep(rule_id="submit", order=1, phase="申請", title="送件", summary="送件",
                           responsible_party="學生", deadline_at=datetime(2027,1,1,tzinfo=timezone.utc))
    workflow = UniversityApplicationWorkflow(home_university="測試大學",school_name="合作校甲",steps=[step])
    original = preparation_identity(workflow,step,1)
    assert original == preparation_identity(workflow,step.model_copy(update={"checked_at":datetime.now(timezone.utc)}),1)
    assert original[0] != preparation_identity(workflow,step.model_copy(update={"deadline_at":datetime(2027,1,2,tzinfo=timezone.utc)}),1)[0]


def test_ntpu_legacy_shared_rule_is_source_and_year_bound():
    from exchange_info.application_task_identity import preparation_identity
    step = ApplicationStep(rule_id="per-school-id",order=2,phase="校內申請",
        title="完成臺北大學線上申請與報名表",summary="核對資料",responsible_party="學生",
        scope=ApplicationRuleScope(home_universities=["國立臺北大學"],partner_universities=["合作校甲"]),
        source_urls=[NTPU_GUIDELINE])
    workflow = UniversityApplicationWorkflow(home_university="國立臺北大學",school_name="合作校甲",academic_year="115",
        sources=[ApplicationWorkflowSource(title="簡章",source_url=NTPU_GUIDELINE,role="home_university")],steps=[step])
    assert preparation_identity(workflow,step,1)[1] == "home"
    assert preparation_identity(workflow.model_copy(update={"academic_year":"116"}),step,1)[1] == "partner"
    assert preparation_identity(workflow,step.model_copy(update={"source_urls":[NTPU_GUIDELINE,"https://host.edu/extra"]}),1)[1] == "partner"
    assert preparation_identity(workflow,step.model_copy(update={"title":"合作校送件"}),1)[1] == "partner"
