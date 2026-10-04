from exchange_info.application_rules import (
    build_personal_application_plan,
    compose_application_workflow,
)
from exchange_info.models import (
    ApplicationPlanEligibilityStatus,
    ApplicationPlanPreference,
    ApplicationRuleContext,
    ApplicationRuleScope,
    ApplicationStep,
    ApplicationSupportStatus,
    ApplicationWorkflowReviewStatus,
    PartnerUniversity,
    PersonalApplicationPlanRequest,
    UniversityApplicationWorkflow,
)


def _step(
    *,
    order: int,
    title: str,
    rule_id: str | None = None,
    overrides_rule_id: str | None = None,
    departments: list[str] | None = None,
    academic_years: list[str] | None = None,
    application_rounds: list[str] | None = None,
) -> ApplicationStep:
    return ApplicationStep(
        rule_id=rule_id,
        overrides_rule_id=overrides_rule_id,
        order=order,
        phase="校內申請",
        title=title,
        responsible_party="學生",
        summary=title,
        scope=ApplicationRuleScope(
            departments=departments or [],
            academic_years=academic_years or [],
            application_rounds=application_rounds or [],
        ),
    )


def _workflow() -> UniversityApplicationWorkflow:
    return UniversityApplicationWorkflow(
        home_university="國立臺北大學",
        school_name="交換合作校",
        steps=[
            _step(order=1, title="校級預設送件", rule_id="submit"),
            _step(
                order=1,
                title="資工系紙本送件",
                overrides_rule_id="submit",
                departments=["資訊工程學系"],
            ),
            _step(
                order=1,
                title="法律系紙本送件",
                overrides_rule_id="submit",
                departments=["法律學系"],
            ),
            _step(
                order=2,
                title="資工系額外系主任簽章",
                departments=["資訊工程學系"],
            ),
            _step(
                order=3,
                title="116 第一梯次補件",
                rule_id="round-extra",
                academic_years=["116"],
                application_rounds=["第一梯次"],
            ),
        ],
    )


def test_unpersonalized_request_preserves_published_workflow() -> None:
    workflow = _workflow()

    result = compose_application_workflow(
        workflow,
        ApplicationRuleContext(
            home_university=workflow.home_university,
            partner_university=workflow.school_name,
        ),
    )

    assert result is workflow
    assert len(result.steps) == 5
    assert result.applied_context is None


def test_department_override_replaces_school_default_and_adds_exception() -> None:
    result = compose_application_workflow(
        _workflow(),
        ApplicationRuleContext(
            department="資訊工程學系",
            academic_year="116",
            application_round="第一梯次",
        ),
    )

    assert [step.title for step in result.steps] == [
        "資工系紙本送件",
        "資工系額外系主任簽章",
        "116 第一梯次補件",
    ]
    assert result.applied_context is not None
    assert result.applied_context.home_university == "國立臺北大學"
    assert result.academic_year is None
    assert result.application_round is None
    assert result.applied_context.academic_year == "116"
    assert result.applied_context.application_round == "第一梯次"


def test_unknown_department_gets_school_default_without_other_department_rules() -> None:
    result = compose_application_workflow(
        _workflow(),
        ApplicationRuleContext(department="社會學系"),
    )

    assert [step.title for step in result.steps] == [
        "校級預設送件",
        "116 第一梯次補件",
    ]


def test_mismatched_year_and_round_exclude_scoped_rule() -> None:
    result = compose_application_workflow(
        _workflow(),
        ApplicationRuleContext(
            department="資訊工程學系",
            academic_year="117",
            application_round="第二梯次",
        ),
    )

    assert all(step.rule_id != "round-extra" for step in result.steps)


def _partner(
    school_name: str = "交換合作校",
    *,
    availability_status: str = "open",
) -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        availability_status=availability_status,
        availability_note=(
            "本期沒有公告名額。"
            if availability_status == "agreement_only"
            else "中央當期名單未列，須先向管理學院或國際處確認。"
            if availability_status == "departmental_reference"
            else None
        ),
        country="紐西蘭",
        school_name=school_name,
        colleges="工學院、資訊工程學系",
        degree_levels="大學部",
        eligibility="IELTS 總分 6.0",
        source_url="https://example.edu/partners",
    )


def _plan_request(*preferences: ApplicationPlanPreference) -> PersonalApplicationPlanRequest:
    return PersonalApplicationPlanRequest(
        home_school="國立臺北大學",
        college="工學院",
        department="資訊工程學系",
        degree_level="大學部",
        academic_score=82,
        language_test="ielts",
        language_score=6.5,
        academic_year="116",
        application_round="第一梯次",
        preferences=list(preferences)
        or [ApplicationPlanPreference(rank=1, school_name="交換合作校")],
    )


def test_personal_plan_uses_scoped_verified_rules_for_checklist() -> None:
    workflow = _workflow().model_copy(
        update={
            "academic_year": "116",
            "application_round": "第一梯次",
            "review_status": ApplicationWorkflowReviewStatus.PUBLISHED,
            "steps": [
                step.model_copy(
                    update={"support_status": ApplicationSupportStatus.VERIFIED}
                )
                for step in _workflow().steps
            ],
        }
    )

    result = build_personal_application_plan(
        _plan_request(),
        [_partner()],
        [workflow],
        academic_score_minimum=70,
        academic_source_url="https://example.edu/eligibility",
    )

    choice = result.choices[0]
    assert choice.status == ApplicationPlanEligibilityStatus.ELIGIBLE
    assert [item.title for item in choice.checklist] == [
        "資工系紙本送件",
        "資工系額外系主任簽章",
        "116 第一梯次補件",
    ]
    assert all(not item.needs_confirmation for item in choice.checklist)
    assert choice.workflow_review_status == ApplicationWorkflowReviewStatus.PUBLISHED


def test_personal_plan_missing_values_become_confirmation_tasks() -> None:
    request = PersonalApplicationPlanRequest(
        home_school="國立臺北大學",
        academic_year="116",
        application_round="第一梯次",
        preferences=[ApplicationPlanPreference(rank=1, school_name="交換合作校")],
    )

    result = build_personal_application_plan(
        request,
        [_partner()],
        [_workflow()],
        academic_score_minimum=None,
    )

    choice = result.choices[0]
    assert choice.status == ApplicationPlanEligibilityStatus.NEEDS_CONFIRMATION
    assert {check.code for check in choice.checks if check.status == "needs_confirmation"} >= {
        "college",
        "degree_level",
        "academic_score",
        "language_score",
    }
    assert all(
        check.contact_unit == "國立臺北大學國際事務處／所屬系所"
        for check in choice.checks
        if check.status == "needs_confirmation"
    )


def test_personal_plan_keeps_preference_order_and_marks_closed_choice_unavailable() -> None:
    result = build_personal_application_plan(
        _plan_request(
            ApplicationPlanPreference(rank=2, school_name="第二志願"),
            ApplicationPlanPreference(rank=1, school_name="交換合作校"),
        ),
        [_partner(), _partner("第二志願", availability_status="agreement_only")],
        [_workflow()],
        academic_score_minimum=70,
    )

    assert [choice.school_name for choice in result.choices] == [
        "交換合作校",
        "第二志願",
    ]
    assert result.choices[1].status == ApplicationPlanEligibilityStatus.UNAVAILABLE
    assert result.choices[1].checklist == []


def test_personal_plan_blocks_departmental_reference_until_current_opening_is_confirmed() -> None:
    result = build_personal_application_plan(
        _plan_request(
            ApplicationPlanPreference(rank=1, school_name="院級參考校"),
        ),
        [_partner("院級參考校", availability_status="departmental_reference")],
        [_workflow()],
        academic_score_minimum=70,
    )

    choice = result.choices[0]
    assert choice.status == ApplicationPlanEligibilityStatus.UNAVAILABLE
    assert choice.checklist == []
    availability_check = next(check for check in choice.checks if check.code == "availability")
    assert availability_check.status == "fail"
    assert "中央當期名單未列" in availability_check.detail
    assert "中央當期名單未列" in choice.summary
