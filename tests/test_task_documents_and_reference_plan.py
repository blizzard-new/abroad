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
    import json
    from collections import Counter, defaultdict
    from exchange_info.university_registry import SUPPORTED_UNIVERSITIES

    # Keep every official source row and its review state through the runtime import.
    # This also catches a missing university bundle as the registry expands.
    source_rows = Counter()
    for school in SUPPORTED_UNIVERSITIES:
        path = storage.PACKAGE_DIR / "official_data" / school.id / "application_workflows.jsonl"
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    row = json.loads(line)
                    source_rows[school.school_name, row["school_name"], row.get("review_status", "legacy")] += 1

    workflows = storage.load_bundled_application_workflows()
    assert Counter((w.home_university, w.school_name, w.review_status) for w in workflows) == source_rows
    periods = defaultdict(list)
    for workflow in workflows:
        periods[workflow.home_university, workflow.academic_year].append(workflow)
    assert {home for home, _ in periods} == {school.school_name for school in SUPPORTED_UNIVERSITIES}

    # These releases established the contract for the home application tools.
    # Partner nomination, visa and insurance steps can list external forms alone.
    reviewed_periods = {
        ("國立臺北大學", "115"), ("國立臺北大學", "116"),
        ("長庚大學", "115"), ("長庚大學", "116"),
        ("國立臺灣大學", "116"), ("淡江大學", "2027-2028"),
    }
    assert reviewed_periods <= periods.keys()
    assert {("國立中央大學", "116"), ("國立中正大學", "115")} <= periods.keys()
    reviewed_linked = 0
    for period, rows in periods.items():
        audit = audit_task_document_links(rows)
        assert audit["steps"] == sum(len(row.steps) for row in rows) > 0, period
        assert audit["tool_linked"] + audit["requirements_only"] + audit["no_documents"] == audit["steps"], period
        patterns = audit["requirements_only_patterns"]
        assert sum(pattern["step_count"] for pattern in patterns) == audit["requirements_only"], period
        for pattern in patterns:
            assert pattern["required_documents"], (period, pattern)
            if period in reviewed_periods:
                if period[0] == "淡江大學":
                    assert pattern["step_title"] == "獲母校推薦後完成外校申請", pattern
                else:
                    assert pattern["step_title"].startswith(("依提名信", "辦理學生簽證")), pattern
        if period in reviewed_periods:
            reviewed_linked += audit["tool_linked"]
    assert reviewed_linked >= 1400


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
    from collections import defaultdict
    from exchange_info.models import PartnerUniversity

    # A request is for a school pair. Supply all its source periods together.
    periods_by_pair = defaultdict(list)
    for workflow in storage.load_bundled_application_workflows():
        periods_by_pair[workflow.home_university, workflow.school_name].append(workflow)
    assert periods_by_pair
    for (home, name), periods in periods_by_pair.items():
        if len(name) > 200:
            # Only these archived 115 import rows contain appended course notes
            # beyond the API limit. New or current over-length names must fail.
            assert home == "國立臺北大學" and {row.academic_year for row in periods} == {"115"}
            assert name.startswith(("拉斯帕爾瑪斯大學 (", "法國計算機及創新技術學院EPITECH (")), name
            continue
        source_years = {row.academic_year for row in periods}
        target_year = "2031-2032" if home == "淡江大學" else "120"
        assert target_year not in source_years, (home, name)
        partner = PartnerUniversity(
            program_type="交換", school_name=name, colleges="全校", degree_levels="大學部",
            source_url=periods[0].sources[0].source_url,
        )
        request = PersonalApplicationPlanRequest(
            home_school=home, college="工學院", degree_level="大學部", academic_score=90,
            academic_year=target_year, application_round="第一梯次",
            preferences=[{"rank": 1, "school_name": name}],
        )
        plan = build_personal_application_plan(request, [partner], periods, academic_score_minimum=60)
        scheduled = schedule_application_plan(
            plan, ApplicationPlanScheduleRequest(
                plan=request, availability={"weekly_hours": 10, "weekdays": [1, 3, 5], "horizon_days": 90},
            ), as_of=date(2026, 10, 5),
        ).schedule
        choice = plan.choices[0]
        check = next(item for item in choice.checks if item.code == "workflow")
        assert check.status == "needs_confirmation", (home, name)
        if home == "國立中央大學" and not any(row.review_status == "published" for row in periods):
            assert choice.reference_academic_year is None and not choice.checklist, name
            assert not plan.tasks and not scheduled.items and not scheduled.work_sessions, name
            continue
        assert choice.reference_academic_year in source_years and choice.checklist, (home, name)
        assert plan.tasks and scheduled.work_sessions, (home, name)
        for task in plan.tasks:
            assert task.task_origin == "reference_year" and task.needs_confirmation, (home, name)
            assert task.official_deadline_at is None and task.deadline_source_url is None, (home, name)
        assert all(item.deadline_date is None and item.deadline_kind == "unspecified" for item in scheduled.items), (home, name)


def test_enumerated_source_details_and_track_specific_requirements_survive_catalogue_import():
    from exchange_info.nycu_source_review import DOCS, UST_DOCS
    from exchange_info.task_documents import document_requirements_for_step

    source = "https://example.edu/exchange/requirements"
    legacy = step("備齊申請文件").model_copy(update={
        "source_urls": [source], "details": ["必備表單 1：簽名申請表", "選課安排另見公告"],
    })
    assert document_link_for_step(legacy).requirement_names == ["簽名申請表"]
    assert document_requirements_for_step(legacy)[0].source_urls == [source]
    ust = legacy.model_copy(update={"rule_id": "nycu-116-home-2-001", "details": UST_DOCS})
    requirements = document_requirements_for_step(ust)
    assert any(item.name == "台聯大簽名申請表" for item in requirements)
    assert next(item for item in requirements if "TOEFL" in item.name).conditional
    unscoped = ust.model_copy(update={"details": DOCS})
    assert document_requirements_for_step(unscoped) == []
