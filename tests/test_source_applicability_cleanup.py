from datetime import datetime, timezone

from exchange_info.workflow_structuring import (
    clear_derived_source_applicability,
)
from exchange_info.models import (
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowSource,
    UniversityApplicationWorkflow,
)


def _workflow(
    *,
    review_status: ApplicationWorkflowReviewStatus = (
        ApplicationWorkflowReviewStatus.LEGACY
    ),
) -> UniversityApplicationWorkflow:
    return UniversityApplicationWorkflow(
        governance_key=(
            "stable-reviewed-workflow"
            if review_status == ApplicationWorkflowReviewStatus.PUBLISHED
            else None
        ),
        home_university="國立臺北大學",
        school_name="測試合作校",
        academic_year="115",
        review_status=review_status,
        published_at=(
            datetime(2026, 8, 12, tzinfo=timezone.utc)
            if review_status == ApplicationWorkflowReviewStatus.PUBLISHED
            else None
        ),
        sources=[
            ApplicationWorkflowSource(
                title="一般合作校首頁",
                source_url="https://partner.example.edu/",
                role="partner_university",
                effective_academic_year="115",
                application_round="秋季梯次",
            )
        ],
    )


def test_cleanup_clears_pre_review_source_applicability() -> None:
    cleaned, count = clear_derived_source_applicability(_workflow())

    assert count == 1
    assert cleaned.academic_year == "115"
    assert cleaned.sources[0].effective_academic_year is None
    assert cleaned.sources[0].application_round is None
    assert cleaned.applicability_status.value == "needs_confirmation"


def test_cleanup_preserves_formally_published_source_applicability() -> None:
    workflow = _workflow(review_status=ApplicationWorkflowReviewStatus.PUBLISHED)

    cleaned, count = clear_derived_source_applicability(workflow)

    assert count == 0
    assert cleaned == workflow
