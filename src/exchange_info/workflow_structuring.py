from __future__ import annotations

import hashlib
import re
from datetime import datetime

from .models import (
    ApplicationApplicabilityStatus,
    ApplicationCopyType,
    ApplicationDeadlineStatus,
    ApplicationDocumentRequirement,
    ApplicationSourceAuthority,
    ApplicationSourceRole,
    ApplicationStep,
    ApplicationSubmissionDetails,
    ApplicationSubmissionMethod,
    ApplicationSupportStatus,
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowSource,
    UniversityApplicationWorkflow,
)

ACADEMIC_YEAR_PATTERN = re.compile(r"(?<!\d)(\d{3})\s*學年度")
COPY_COUNT_PATTERN = re.compile(r"(?<!\d)(\d{1,2})\s*份")


def _explicit_home_rule(step: ApplicationStep, workflow: UniversityApplicationWorkflow) -> bool:
    return bool(step.rule_id and workflow.home_university in step.scope.home_universities
                and not step.scope.partner_universities)


def structure_application_workflow(
    workflow: UniversityApplicationWorkflow,
) -> UniversityApplicationWorkflow:
    """Upgrade collected legacy workflow text without inventing missing rules."""

    academic_year = workflow.academic_year or _infer_academic_year(workflow)
    sources = [_structure_source(source) for source in workflow.sources]
    steps = [
        _structure_step(
            step,
            workflow=workflow,
            academic_year=academic_year,
            publication_eligible=_publication_eligible(workflow),
        )
        for step in workflow.steps
    ]
    effective_application_rounds = _effective_application_rounds(
        workflow,
        steps,
    )
    applicability_status, applicability_note = _applicability_metadata(
        workflow,
        sources=sources,
        effective_application_rounds=effective_application_rounds,
        academic_year=academic_year,
    )
    return workflow.model_copy(
        update={
            "workflow_id": workflow.workflow_id or _workflow_id(workflow, academic_year),
            "academic_year": academic_year,
            "effective_application_rounds": effective_application_rounds,
            "applicability_status": applicability_status,
            "applicability_note": applicability_note,
            "steps": steps,
            "sources": sources,
        }
    )


def clear_derived_source_applicability(
    workflow: UniversityApplicationWorkflow,
) -> tuple[UniversityApplicationWorkflow, int]:
    """Clear source applicability that predates the formal dual-review trail.

    Legacy bundle rows previously copied the workflow academic year into every
    source. A source URL, title, or general page is not evidence that the page
    applies to that year. Formally published rows are preserved; legacy rows
    must be re-confirmed source by source through the review workbench.
    """

    if (
        workflow.review_status != ApplicationWorkflowReviewStatus.LEGACY
        or workflow.published_at is not None
        or workflow.governance_key
    ):
        return workflow, 0
    cleared = sum(
        bool(source.effective_academic_year or source.application_round)
        for source in workflow.sources
    )
    if not cleared:
        return workflow, 0
    sources = [
        source.model_copy(
            update={
                "effective_academic_year": None,
                "application_round": None,
            }
        )
        for source in workflow.sources
    ]
    return (
        structure_application_workflow(
            workflow.model_copy(update={"sources": sources})
        ),
        cleared,
    )


def workflow_structure_issues(
    workflow: UniversityApplicationWorkflow,
) -> list[str]:
    issues: list[str] = []
    publication_eligible = _publication_eligible(workflow)
    if (
        workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
        and workflow.published_at is None
    ):
        issues.append("workflow:published_at_missing")
    if (
        workflow.review_status != ApplicationWorkflowReviewStatus.PUBLISHED
        and workflow.published_at is not None
    ):
        issues.append("workflow:published_at_without_published_status")
    for source_index, source in enumerate(workflow.sources, start=1):
        if source.authority is None or source.priority is None:
            issues.append(f"source[{source_index}]:missing_authority_priority")
    for step in workflow.steps:
        label = step.rule_id or f"step-{step.order}"
        if not step.rule_id:
            issues.append(f"{label}:missing_rule_id")
        if not step.scope.home_universities:
            issues.append(f"{label}:missing_home_scope")
        if not step.scope.partner_universities and not _explicit_home_rule(step, workflow):
            issues.append(f"{label}:missing_partner_scope")
        if len(step.document_requirements) != len(step.required_documents):
            issues.append(f"{label}:document_mapping_incomplete")
        if step.required_documents and any(
            not item.source_urls for item in step.document_requirements
        ):
            issues.append(f"{label}:document_source_missing")
        if step.support_status == ApplicationSupportStatus.LEGACY_UNCLASSIFIED:
            issues.append(f"{label}:support_status_unclassified")
        if (
            step.support_status == ApplicationSupportStatus.NEEDS_CONFIRMATION
            and not step.confirmation_contact
        ):
            issues.append(f"{label}:confirmation_contact_missing")
        if step.source_urls and step.checked_at is None:
            issues.append(f"{label}:checked_at_missing")
        if step.deadline_status == ApplicationDeadlineStatus.VERIFIED_EXACT:
            if publication_eligible and not step.deadline_reminder_eligible:
                issues.append(f"{label}:verified_deadline_not_reminder_eligible")
            if not publication_eligible and step.deadline_reminder_eligible:
                issues.append(f"{label}:unpublished_deadline_reminder_eligible")
            if not step.deadline_source_url:
                issues.append(f"{label}:verified_deadline_source_missing")
            if step.deadline_checked_at is None:
                issues.append(f"{label}:verified_deadline_checked_at_missing")
        elif step.deadline_reminder_eligible:
            issues.append(f"{label}:unverified_deadline_reminder_eligible")
    return issues


def workflow_structure_summary(
    workflows: list[UniversityApplicationWorkflow],
) -> dict[str, int]:
    structured = [structure_application_workflow(row) for row in workflows]
    steps = [step for workflow in structured for step in workflow.steps]
    sources = [source for workflow in structured for source in workflow.sources]
    documents = [
        requirement for step in steps for requirement in step.document_requirements
    ]
    return {
        "workflow_count": len(structured),
        "structured_workflow_count": sum(
            not workflow_structure_issues(row) for row in structured
        ),
        "step_count": len(steps),
        "structured_step_count": sum(
            bool(step.rule_id)
            and bool(step.scope.home_universities)
            and (bool(step.scope.partner_universities) or _explicit_home_rule(step, workflow))
            and step.support_status
            != ApplicationSupportStatus.LEGACY_UNCLASSIFIED
            for workflow in structured for step in workflow.steps
        ),
        "known_submission_method_count": sum(
            step.submission.method != ApplicationSubmissionMethod.UNKNOWN
            for step in steps
        ),
        "steps_needing_confirmation": sum(
            step.support_status == ApplicationSupportStatus.NEEDS_CONFIRMATION
            for step in steps
        ),
        "document_count": len(documents),
        "documents_needing_confirmation": sum(
            requirement.needs_confirmation for requirement in documents
        ),
        "source_count": len(sources),
        "prioritized_source_count": sum(
            source.authority is not None and source.priority is not None
            for source in sources
        ),
        "published_workflow_count": sum(
            row.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
            for row in structured
        ),
        "legacy_workflow_count": sum(
            row.review_status == ApplicationWorkflowReviewStatus.LEGACY
            for row in structured
        ),
        "published_at_workflow_count": sum(
            row.published_at is not None for row in structured
        ),
        "applicability_verified_workflow_count": sum(
            row.applicability_status == ApplicationApplicabilityStatus.VERIFIED
            for row in structured
        ),
        "verified_exact_deadline_count": sum(
            step.deadline_status == ApplicationDeadlineStatus.VERIFIED_EXACT
            for step in steps
        ),
        "reference_only_deadline_count": sum(
            step.deadline_status == ApplicationDeadlineStatus.REFERENCE_ONLY
            for step in steps
        ),
        "deadlines_needing_confirmation_count": sum(
            step.deadline_status == ApplicationDeadlineStatus.NEEDS_CONFIRMATION
            for step in steps
        ),
        "deadline_not_applicable_count": sum(
            step.deadline_status == ApplicationDeadlineStatus.NOT_APPLICABLE
            for step in steps
        ),
        "reminder_eligible_deadline_count": sum(
            step.deadline_reminder_eligible for step in steps
        ),
        "structure_issue_count": sum(
            len(workflow_structure_issues(row)) for row in structured
        ),
    }


def _structure_source(
    source: ApplicationWorkflowSource,
) -> ApplicationWorkflowSource:
    authority = source.authority
    priority = source.priority
    if authority is None or priority is None:
        if source.role == ApplicationSourceRole.PARTNER_UNIVERSITY:
            authority = authority or ApplicationSourceAuthority.PARTNER_OFFICIAL
            priority = priority or 4
        elif _is_home_academic_unit_source(source):
            authority = authority or ApplicationSourceAuthority.HOME_ACADEMIC_UNIT
            priority = priority or 2
        else:
            authority = authority or ApplicationSourceAuthority.HOME_OFFICIAL_NOTICE
            priority = priority or 1
    return source.model_copy(
        update={
            "authority": authority,
            "priority": priority,
        }
    )


def _structure_step(
    step: ApplicationStep,
    *,
    workflow: UniversityApplicationWorkflow,
    academic_year: str | None,
    publication_eligible: bool,
) -> ApplicationStep:
    method = step.submission.method
    # This CCU step combines housing, visa and arrival notices from several
    # host offices. A notice sent by email does not establish how a later form
    # must be submitted. Keep the collector's unknown method until explicit
    # delivery instructions are available; preserve any verified method.
    ccu_host_life = (
        workflow.home_university == "國立中正大學"
        and step.phase == "合作校行前與生活"
    )
    if method == ApplicationSubmissionMethod.UNKNOWN and not ccu_host_life:
        method = _infer_submission_method(step)
    submission = step.submission.model_copy(
        update={
            "method": method,
            "portal_url": (
                step.submission.portal_url
                or (
                    step.action_url
                    if method
                    in {
                        ApplicationSubmissionMethod.ONLINE,
                        ApplicationSubmissionMethod.MIXED,
                    }
                    else None
                )
            ),
        }
    )
    scope = step.scope.model_copy(
        update={
            "home_universities": (
                step.scope.home_universities or [workflow.home_university]
            ),
            "partner_universities": (
                step.scope.partner_universities if _explicit_home_rule(step, workflow)
                else step.scope.partner_universities or [workflow.school_name]
            ),
            "academic_years": (
                step.scope.academic_years
                or ([academic_year] if academic_year else [])
            ),
            "application_rounds": (
                step.scope.application_rounds or _infer_application_rounds(step)
            ),
        }
    )
    requirements = [
        _structure_document_requirement(
            requirement,
            step=step,
            submission=submission,
        )
        for requirement in step.document_requirements
    ]
    checked_at = step.checked_at or workflow.last_checked
    (
        deadline_status,
        deadline_source_url,
        deadline_checked_at,
        deadline_reminder_eligible,
    ) = _deadline_metadata(
        step,
        submission=submission,
        checked_at=checked_at,
        publication_eligible=publication_eligible,
    )
    effective_needs_confirmation = step.needs_confirmation or any(
        requirement.needs_confirmation for requirement in requirements
    ) or deadline_status in {
        ApplicationDeadlineStatus.REFERENCE_ONLY,
        ApplicationDeadlineStatus.NEEDS_CONFIRMATION,
    }
    support_status = step.support_status
    if (
        support_status == ApplicationSupportStatus.LEGACY_UNCLASSIFIED
        or effective_needs_confirmation
    ):
        if effective_needs_confirmation:
            support_status = ApplicationSupportStatus.NEEDS_CONFIRMATION
        elif step.source_urls and workflow.coverage_status != "not_found":
            support_status = ApplicationSupportStatus.VERIFIED
        else:
            support_status = ApplicationSupportStatus.UNVERIFIED
    signatures = list(step.signature_requirements)
    for requirement in requirements:
        for signer in requirement.signatures:
            if signer not in signatures:
                signatures.append(signer)
    return step.model_copy(
        update={
            "rule_id": step.rule_id or _rule_id(workflow, step),
            "responsible_unit": (
                step.responsible_unit or _responsible_unit(step.responsible_party)
            ),
            "document_requirements": requirements,
            "signature_requirements": signatures,
            "scope": scope,
            "submission": submission,
            "checked_at": checked_at,
            "deadline_status": deadline_status,
            "deadline_source_url": deadline_source_url,
            "deadline_checked_at": deadline_checked_at,
            "deadline_reminder_eligible": deadline_reminder_eligible,
            "support_status": support_status,
            "confirmation_contact": (
                step.confirmation_contact
                or _confirmation_contact(
                    step,
                    workflow.home_university,
                    needs_confirmation=effective_needs_confirmation,
                )
            ),
        }
    )


def _deadline_metadata(
    step: ApplicationStep,
    *,
    submission: ApplicationSubmissionDetails,
    checked_at: datetime | None,
    publication_eligible: bool,
) -> tuple[ApplicationDeadlineStatus, str | None, datetime | None, bool]:
    source_url = step.deadline_source_url or next(
        (
            value
            for value in step.source_urls
            if str(value).strip().casefold().startswith("https://")
        ),
        None,
    )
    deadline_checked_at = step.deadline_checked_at or checked_at
    paper_flow = submission.method in {
        ApplicationSubmissionMethod.PAPER,
        ApplicationSubmissionMethod.MIXED,
    }
    any_exact_deadline = bool(
        step.deadline_at
        or submission.send_by_at
        or submission.arrival_deadline_at
    )
    required_exact_deadline = (
        submission.arrival_deadline_at
        if paper_flow
        else step.deadline_at or submission.arrival_deadline_at
    )
    can_verify = bool(
        required_exact_deadline
        and source_url
        and deadline_checked_at
        and submission.method != ApplicationSubmissionMethod.UNKNOWN
    )
    if can_verify:
        status = ApplicationDeadlineStatus.VERIFIED_EXACT
    elif any_exact_deadline:
        status = ApplicationDeadlineStatus.NEEDS_CONFIRMATION
    elif (step.timing or "").strip() or (submission.deadline_note or "").strip():
        status = ApplicationDeadlineStatus.REFERENCE_ONLY
    else:
        status = ApplicationDeadlineStatus.NOT_APPLICABLE
    return (
        status,
        source_url,
        deadline_checked_at,
        status == ApplicationDeadlineStatus.VERIFIED_EXACT and publication_eligible,
    )


def _publication_eligible(workflow: UniversityApplicationWorkflow) -> bool:
    return bool(
        workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
        and workflow.published_at is not None
    )


def _effective_application_rounds(
    workflow: UniversityApplicationWorkflow,
    steps: list[ApplicationStep],
) -> list[str]:
    values = [
        *workflow.effective_application_rounds,
        *([workflow.application_round] if workflow.application_round else []),
        *(
            value
            for step in steps
            for value in step.scope.application_rounds
        ),
    ]
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))


def _applicability_metadata(
    workflow: UniversityApplicationWorkflow,
    *,
    sources: list[ApplicationWorkflowSource],
    effective_application_rounds: list[str],
    academic_year: str | None,
) -> tuple[ApplicationApplicabilityStatus, str]:
    missing: list[str] = []
    if not academic_year:
        missing.append("適用學年度")
    if not effective_application_rounds:
        missing.append("申請梯次")
    if workflow.last_checked is None:
        missing.append("流程最後查核日期")
    if not sources:
        missing.append("官方來源")
    elif academic_year and any(
        source.effective_academic_year != academic_year
        for source in sources
    ):
        missing.append("來源適用學年度")
    if missing:
        return (
            ApplicationApplicabilityStatus.NEEDS_CONFIRMATION,
            f"{'、'.join(missing)}尚未完成官方確認；不能把學生選擇的年度或梯次套用到這份流程。",
        )
    return (
        ApplicationApplicabilityStatus.VERIFIED,
        (
            f"官方來源適用 {academic_year} 學年度，梯次為"
            f"{'、'.join(effective_application_rounds)}；仍應在送件前核對當期公告。"
        ),
    )


def _structure_document_requirement(
    requirement: ApplicationDocumentRequirement,
    *,
    step: ApplicationStep,
    submission: ApplicationSubmissionDetails,
) -> ApplicationDocumentRequirement:
    # Individually reviewed receiving documents already supply their metadata.
    # A name such as "non-OECD: original" must not impose originals on everyone.
    if requirement.stage is not None:
        return requirement.model_copy(
            update={
                "source_urls": requirement.source_urls or list(step.source_urls),
                "needs_confirmation": (
                    requirement.needs_confirmation or step.needs_confirmation
                ),
            }
        )
    copies = requirement.copies
    if copies is None and (match := COPY_COUNT_PATTERN.search(requirement.name)):
        copies = int(match.group(1))
    copy_type = requirement.copy_type
    if copy_type == ApplicationCopyType.UNSPECIFIED:
        copy_type = _infer_copy_type(requirement.name, submission.method)
    signatures = requirement.signatures or _explicit_signatures(requirement.name)
    needs_confirmation = requirement.needs_confirmation or step.needs_confirmation
    if submission.method in {
        ApplicationSubmissionMethod.UNKNOWN,
        ApplicationSubmissionMethod.PAPER,
        ApplicationSubmissionMethod.IN_PERSON,
        ApplicationSubmissionMethod.MIXED,
    } and (copies is None or copy_type == ApplicationCopyType.UNSPECIFIED):
        needs_confirmation = True
    return requirement.model_copy(
        update={
            "copies": copies,
            "copy_type": copy_type,
            "signatures": signatures,
            "source_urls": requirement.source_urls or list(step.source_urls),
            "needs_confirmation": needs_confirmation,
        }
    )


def _infer_submission_method(step: ApplicationStep) -> ApplicationSubmissionMethod:
    text = " ".join(
        [step.title, step.summary, *(step.details or [])]
    ).casefold()
    methods: set[ApplicationSubmissionMethod] = set()
    if any(
        signal in text
        for signal in ("線上申請", "文件上傳", "線上填寫", "官網提出申請")
    ):
        methods.add(ApplicationSubmissionMethod.ONLINE)
    if any(signal in text for signal in ("email", "e-mail", "電子郵件")):
        methods.add(ApplicationSubmissionMethod.EMAIL)
    if any(signal in text for signal in ("親送", "繳交至", "送至系辦", "送到系辦")):
        methods.add(ApplicationSubmissionMethod.IN_PERSON)
    if any(signal in text for signal in ("紙本", "列印")):
        methods.add(ApplicationSubmissionMethod.PAPER)
    if len(methods) > 1:
        return ApplicationSubmissionMethod.MIXED
    return next(iter(methods), ApplicationSubmissionMethod.UNKNOWN)


def _infer_copy_type(
    name: str,
    method: ApplicationSubmissionMethod,
) -> ApplicationCopyType:
    has_original = "正本" in name
    has_copy = "影本" in name or "副本" in name
    if has_original and has_copy:
        return ApplicationCopyType.ORIGINAL_AND_COPY
    if has_original:
        return ApplicationCopyType.ORIGINAL
    if has_copy:
        return ApplicationCopyType.COPY
    if method in {
        ApplicationSubmissionMethod.ONLINE,
        ApplicationSubmissionMethod.EMAIL,
    }:
        return ApplicationCopyType.DIGITAL
    return ApplicationCopyType.UNSPECIFIED


def _explicit_signatures(name: str) -> list[str]:
    if "簽名" not in name and "簽署" not in name and "簽章" not in name:
        return []
    signers: list[str] = []
    for signal, signer in (
        ("家長", "家長"),
        ("教授", "教授"),
        ("指導老師", "指導老師"),
        ("系主任", "系主任"),
        ("本人", "本人"),
    ):
        if signal in name:
            signers.append(signer)
    return signers or ["本人"]


def _infer_application_rounds(step: ApplicationStep) -> list[str]:
    text = " ".join((step.title, step.timing or "", step.summary))
    rounds: list[str] = []
    for signal, label in (
        ("第一梯次", "第一梯次"),
        ("第二梯次", "第二梯次"),
        ("秋季", "秋季／全學年梯次"),
        ("春季", "春季梯次"),
    ):
        if signal in text and label not in rounds:
            rounds.append(label)
    return rounds


def _infer_academic_year(workflow: UniversityApplicationWorkflow) -> str | None:
    values = [source.title for source in workflow.sources]
    values.extend(
        value
        for step in workflow.steps
        for value in (step.title, step.timing or "", step.summary)
    )
    for value in values:
        match = ACADEMIC_YEAR_PATTERN.search(value)
        if match:
            return match.group(1)
    return None


def _responsible_unit(responsible_party: str) -> str | None:
    value = responsible_party.strip()
    if not value or value == "學生":
        return None
    return value


def _confirmation_contact(
    step: ApplicationStep,
    home_university: str,
    *,
    needs_confirmation: bool,
) -> str | None:
    if not needs_confirmation:
        return None
    text = f"{step.phase} {step.responsible_party} {step.summary}"
    if "合作校" in text or "提名信" in text:
        return f"{home_university}國際事務處及合作校提名通知所列承辦人"
    return f"{home_university}國際事務處"


def _is_home_academic_unit_source(source: ApplicationWorkflowSource) -> bool:
    text = f"{source.title} {source.source_url}".casefold()
    return any(signal in text for signal in ("學分抵免", "academic-en", "系所公告"))


def _rule_id(
    workflow: UniversityApplicationWorkflow,
    step: ApplicationStep,
) -> str:
    identity = "|".join(
        (
            workflow.home_university,
            workflow.school_name,
            step.phase,
            step.title,
            str(step.order),
        )
    )
    return f"rule-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20]}"


def _workflow_id(
    workflow: UniversityApplicationWorkflow,
    academic_year: str | None,
) -> str:
    identity = "|".join(
        (
            workflow.home_university,
            workflow.school_name,
            workflow.program_type or "",
            academic_year or "",
            workflow.application_round or "",
        )
    )
    return f"workflow-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"
