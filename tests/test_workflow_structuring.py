from datetime import datetime, timezone

from exchange_info.models import (
    ApplicationApplicabilityStatus,
    ApplicationCopyType,
    ApplicationDeadlineStatus,
    ApplicationSubmissionDetails,
    ApplicationSourceAuthority,
    ApplicationStep,
    ApplicationSubmissionMethod,
    ApplicationSupportStatus,
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowSource,
    UniversityApplicationWorkflow,
)
from exchange_info.workflow_structuring import (
    structure_application_workflow,
    workflow_structure_issues,
)


def _legacy_workflow() -> UniversityApplicationWorkflow:
    checked_at = datetime(2026, 7, 28, tzinfo=timezone.utc)
    return UniversityApplicationWorkflow(
        home_university="國立臺北大學",
        school_name="交換合作校",
        steps=[
            ApplicationStep(
                order=1,
                phase="校內申請",
                title="完成線上申請與文件上傳",
                responsible_party="學生 → 國立臺北大學國際事務處",
                timing="115 學年度秋季與春季梯次",
                summary="在校內系統上傳簽名申請表與護照影本。",
                required_documents=["簽名申請表", "護照影本", "成績單 2 份"],
                action_url="https://example.edu/application",
                source_urls=["https://example.edu/notice"],
            ),
            ApplicationStep(
                order=2,
                phase="合作校申請",
                title="依提名信完成合作校申請",
                responsible_party="學生 → 合作校",
                summary="合作校未公開完整送件方式。",
                required_documents=["合作校指定文件"],
                source_urls=["https://partner.example.edu/incoming"],
                needs_confirmation=True,
            ),
        ],
        sources=[
            ApplicationWorkflowSource(
                title="國立臺北大學 115 學年度交換公告",
                source_url="https://example.edu/notice",
                role="home_university",
                checked_at=checked_at,
            ),
            ApplicationWorkflowSource(
                title="Partner incoming exchange",
                source_url="https://partner.example.edu/incoming",
                role="partner_university",
                checked_at=checked_at,
            ),
        ],
        last_checked=checked_at,
        coverage_status="official_verified",
    )


def test_legacy_workflow_is_structured_without_guessing_unknown_values() -> None:
    workflow = structure_application_workflow(_legacy_workflow())
    online, partner = workflow.steps

    assert workflow.workflow_id
    assert workflow.academic_year == "115"
    assert online.rule_id
    assert online.scope.home_universities == ["國立臺北大學"]
    assert online.scope.partner_universities == ["交換合作校"]
    assert online.scope.academic_years == ["115"]
    assert online.scope.application_rounds == ["秋季／全學年梯次", "春季梯次"]
    assert online.submission.method == ApplicationSubmissionMethod.ONLINE
    assert online.submission.portal_url == "https://example.edu/application"
    assert online.document_requirements[0].signatures == ["本人"]
    assert online.document_requirements[1].copy_type == ApplicationCopyType.COPY
    assert online.document_requirements[2].copies == 2
    assert all(item.source_urls for item in online.document_requirements)
    assert workflow.sources[0].effective_academic_year is None
    assert workflow.applicability_status == ApplicationApplicabilityStatus.NEEDS_CONFIRMATION
    assert "來源適用學年度" in workflow.applicability_note
    assert workflow.effective_application_rounds == [
        "秋季／全學年梯次",
        "春季梯次",
    ]
    assert online.deadline_status == ApplicationDeadlineStatus.REFERENCE_ONLY
    assert online.deadline_reminder_eligible is False
    assert online.support_status == ApplicationSupportStatus.NEEDS_CONFIRMATION

    assert partner.submission.method == ApplicationSubmissionMethod.UNKNOWN
    assert partner.submission.address is None
    assert partner.submission.office is None
    assert partner.submission.send_by_at is None
    assert partner.submission.arrival_deadline_at is None
    assert partner.submission.deadline_note is None
    assert partner.document_requirements[0].copies is None
    assert partner.document_requirements[0].copy_type == ApplicationCopyType.UNSPECIFIED
    assert partner.document_requirements[0].needs_confirmation is True
    assert partner.support_status == ApplicationSupportStatus.NEEDS_CONFIRMATION
    assert "合作校提名通知" in (partner.confirmation_contact or "")


def test_explicit_applicability_review_hold_survives_complete_source_metadata() -> None:
    workflow = _legacy_workflow()
    workflow = workflow.model_copy(update={
        "academic_year": "115",
        "application_round": "第一梯次",
        "sources": [
            source.model_copy(update={"effective_academic_year": "115"})
            for source in workflow.sources
        ],
        "applicability_status": ApplicationApplicabilityStatus.NEEDS_CONFIRMATION,
        "applicability_note": "來源只提供預告，正式簡章與適用對象仍待確認。",
    })
    for _ in range(2):
        workflow = structure_application_workflow(workflow)
        assert workflow.applicability_status == ApplicationApplicabilityStatus.NEEDS_CONFIRMATION
        assert workflow.applicability_note == "來源只提供預告，正式簡章與適用對象仍待確認。"


def test_paper_send_by_without_arrival_deadline_is_never_reminder_eligible() -> None:
    checked_at = datetime(2026, 7, 28, tzinfo=timezone.utc)
    workflow = UniversityApplicationWorkflow(
        home_university="長庚大學",
        school_name="交換合作校",
        academic_year="116",
        application_round="第一梯次",
        steps=[
            ApplicationStep(
                order=1,
                phase="校內申請",
                title="寄送紙本",
                responsible_party="學生",
                summary="依公告寄送。",
                submission=ApplicationSubmissionDetails(
                    method=ApplicationSubmissionMethod.PAPER,
                    send_by_at=checked_at,
                ),
                source_urls=["https://example.edu/notice"],
                checked_at=checked_at,
            )
        ],
        sources=[
            ApplicationWorkflowSource(
                title="116 學年度第一梯次公告",
                source_url="https://example.edu/notice",
                role="home_university",
                effective_academic_year="116",
                application_round="第一梯次",
                checked_at=checked_at,
            )
        ],
        last_checked=checked_at,
        coverage_status="official_verified",
    )

    step = structure_application_workflow(workflow).steps[0]

    assert step.deadline_status == ApplicationDeadlineStatus.NEEDS_CONFIRMATION
    assert step.deadline_reminder_eligible is False
    assert step.support_status == ApplicationSupportStatus.NEEDS_CONFIRMATION


def test_exact_deadline_requires_published_workflow_before_reminder() -> None:
    checked_at = datetime(2026, 7, 28, tzinfo=timezone.utc)
    legacy = UniversityApplicationWorkflow(
        home_university="長庚大學",
        school_name="交換合作校",
        academic_year="116",
        application_round="第一梯次",
        steps=[
            ApplicationStep(
                order=1,
                phase="校內申請",
                title="完成線上申請",
                responsible_party="學生",
                summary="依當期公告送出。",
                deadline_at=checked_at,
                submission=ApplicationSubmissionDetails(
                    method=ApplicationSubmissionMethod.ONLINE,
                ),
                source_urls=["https://example.edu/notice"],
                checked_at=checked_at,
            )
        ],
        sources=[
            ApplicationWorkflowSource(
                title="116 學年度第一梯次公告",
                source_url="https://example.edu/notice",
                role="home_university",
                effective_academic_year="116",
                application_round="第一梯次",
                checked_at=checked_at,
            )
        ],
        last_checked=checked_at,
        coverage_status="official_verified",
    )

    legacy_structured = structure_application_workflow(legacy)
    published_structured = structure_application_workflow(
        legacy.model_copy(
            update={
                "review_status": ApplicationWorkflowReviewStatus.PUBLISHED,
                "published_at": checked_at,
            }
        )
    )

    assert legacy_structured.steps[0].deadline_status == (
        ApplicationDeadlineStatus.VERIFIED_EXACT
    )
    assert legacy_structured.steps[0].deadline_reminder_eligible is False
    assert workflow_structure_issues(legacy_structured) == []
    assert published_structured.steps[0].deadline_reminder_eligible is True
    assert workflow_structure_issues(published_structured) == []


def test_published_workflow_without_published_at_fails_structure_audit() -> None:
    workflow = _legacy_workflow().model_copy(
        update={"review_status": ApplicationWorkflowReviewStatus.PUBLISHED}
    )

    assert "workflow:published_at_missing" in workflow_structure_issues(
        structure_application_workflow(workflow)
    )


def test_source_authority_follows_official_priority_order() -> None:
    workflow = _legacy_workflow().model_copy(
        update={
            "sources": [
                ApplicationWorkflowSource(
                    title="校內甄選公告",
                    source_url="https://example.edu/notice",
                    role="home_university",
                ),
                ApplicationWorkflowSource(
                    title="學分抵免表",
                    source_url="https://example.edu/academic-en/credit",
                    role="home_university",
                ),
                ApplicationWorkflowSource(
                    title="Incoming exchange",
                    source_url="https://partner.example.edu/incoming",
                    role="partner_university",
                ),
            ]
        }
    )

    sources = structure_application_workflow(workflow).sources

    assert [(source.authority, source.priority) for source in sources] == [
        (ApplicationSourceAuthority.HOME_OFFICIAL_NOTICE, 1),
        (ApplicationSourceAuthority.HOME_ACADEMIC_UNIT, 2),
        (ApplicationSourceAuthority.PARTNER_OFFICIAL, 4),
    ]


def test_workflow_structuring_is_idempotent_and_passes_audit() -> None:
    first = structure_application_workflow(_legacy_workflow())
    second = structure_application_workflow(first)

    assert second.model_dump(mode="json") == first.model_dump(mode="json")
    assert workflow_structure_issues(second) == []
