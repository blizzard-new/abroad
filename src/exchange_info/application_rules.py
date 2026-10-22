from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable

from .application_task_identity import preparation_identity
from .plan_defaults import suggest_effort_hours
from .school_identity import same_school_program
from .fju_eligibility import FJU_LANG_SCORE_URL, fju_academic_check, fju_degree_check, fju_language_check, is_fju
from .scu_eligibility import is_scu, scu_academic_check, scu_degree_check, scu_language_check
from .ntnu_eligibility import is_ntnu, ntnu_academic_check, ntnu_degree_check, ntnu_language_check
from .cycu_eligibility import cycu_academic_check, cycu_degree_check, cycu_language_check, is_cycu
from .ntust_eligibility import is_ntust, ntust_academic_check, ntust_degree_check, ntust_language_check
from .yzu_eligibility import is_yzu, yzu_academic_check, yzu_degree_check, yzu_language_check
from .fcu_eligibility import fcu_academic_check, fcu_degree_check, fcu_language_check, is_fcu
from .nsysu_eligibility import is_nsysu, nsysu_academic_check, nsysu_degree_check, nsysu_language_check
from .nchu_eligibility import is_nchu, nchu_academic_check, nchu_degree_check, nchu_language_check
from .ntut_eligibility import is_ntut, ntut_academic_check, ntut_degree_check, ntut_language_check
from .nccu_eligibility import is_nccu, nccu_academic_check, nccu_degree_check, nccu_language_check
from .ncku_eligibility import is_ncku, ncku_academic_check, ncku_degree_check, ncku_language_check
from .nycu_eligibility import is_nycu, nycu_academic_check, nycu_degree_check, nycu_language_check
from .nthu_eligibility import is_nthu, nthu_academic_check, nthu_degree_check, nthu_language_check
from .pccu_eligibility import is_pccu, pccu_academic_check, pccu_degree_check, pccu_language_check
from .wzu_eligibility import is_wzu, wzu_academic_check, wzu_degree_check, wzu_language_check
from .nkust_eligibility import is_nkust, nkust_academic_check, nkust_degree_check, nkust_language_check
from .yuntech_eligibility import is_yuntech, yuntech_academic_check, yuntech_degree_check, yuntech_language_check
from .ntou_eligibility import is_ntou, ntou_academic_check, ntou_degree_check, ntou_language_check
from .ncue_eligibility import is_ncue, ncue_academic_check, ncue_degree_check, ncue_language_check
from .nknu_eligibility import is_nknu, nknu_academic_check, nknu_degree_check, nknu_language_check
from .tmu_eligibility import is_tmu, tmu_academic_check, tmu_degree_check, tmu_language_check
from .csmu_eligibility import csmu_academic_check, csmu_degree_check, csmu_language_check, is_csmu
from .cmu_eligibility import cmu_academic_check, cmu_degree_check, cmu_language_check, is_cmu
from .kmu_eligibility import is_kmu, kmu_academic_check, kmu_degree_check, kmu_language_check
from .ncu_eligibility import is_ncu, ncu_academic_check, ncu_language_check
from .ncu_document_conditions import document_applicability
from .ntu_eligibility import is_ntu, ntu_academic_check, ntu_language_check, ntu_published_quota
from .task_documents import document_link_for_step
from .qualification_scopes import (
    coupled_academic_scope_matches,
    college_scope_matches as _partner_scope_matches,
    partner_degree_scope_matches,
    partner_scope_needs_confirmation,
    resolved_degree_level,
)

from .models import (
    ApplicationPlanChecklistItem,
    ApplicationPlanEligibilityCheck,
    ApplicationPlanEligibilityStatus,
    ApplicationRuleContext,
    ApplicationRuleScope,
    ApplicationStep,
    ApplicationSupportStatus,
    ApplicationWorkflowReviewStatus,
    PartnerUniversity,
    PersonalApplicationPlanChoice,
    PersonalApplicationPlanRequest,
    PersonalApplicationPlanResult,
    UniversityApplicationWorkflow,
    UnifiedApplicationTask,
)


def compose_application_workflow(
    workflow: UniversityApplicationWorkflow,
    context: ApplicationRuleContext,
) -> UniversityApplicationWorkflow:
    """Apply scoped rules without mutating the stored published workflow.

    Unscoped legacy steps remain visible. College and department rules are only
    exposed when that part of the student's profile is known, preventing an
    exception for one department from leaking into another student's plan.
    """

    effective_context = context.model_copy(
        update={
            "home_university": context.home_university or workflow.home_university,
            "partner_university": context.partner_university or workflow.school_name,
        }
    )
    if not _personalization_requested(effective_context):
        return workflow

    applicable: list[tuple[int, ApplicationStep]] = [
        (index, step)
        for index, step in enumerate(workflow.steps)
        if scope_matches(step.scope, effective_context)
    ]
    selected_by_target: dict[str, tuple[tuple[int, int, int], int, ApplicationStep]] = {}
    unkeyed: list[tuple[int, ApplicationStep]] = []

    for index, step in applicable:
        target = step.overrides_rule_id or step.rule_id
        if not target:
            unkeyed.append((index, step))
            continue
        rank = (
            scope_specificity(step.scope, effective_context),
            1 if step.overrides_rule_id else 0,
            index,
        )
        current = selected_by_target.get(target)
        if current is None or rank > current[0]:
            selected_by_target[target] = (rank, index, step)

    selected: list[tuple[int, ApplicationStep]] = [
        (index, step) for _, index, step in selected_by_target.values()
    ]
    selected.extend(unkeyed)
    selected.sort(key=lambda item: (item[1].order, item[0]))

    return workflow.model_copy(
        update={
            "applied_context": effective_context,
            "steps": [step for _, step in selected],
        }
    )


def select_application_workflow(
    workflows: Iterable[UniversityApplicationWorkflow],
    context: ApplicationRuleContext,
) -> UniversityApplicationWorkflow | None:
    """Select the most specific workflow version, then apply scoped overrides."""

    partner_key = _normalize(context.partner_university or "")
    candidates = [
        workflow
        for workflow in workflows
        if (
            _normalize(workflow.school_name) == partner_key
            # NCU catalogue names carry distinct faculty / self-funded tracks.
            # The institution matcher tolerates trailing Chinese notes, which
            # would otherwise merge those tracks and reuse the wrong workflow.
            or (not is_ncu(context.home_university)
                and same_school_program(workflow.school_name, context.partner_university or ""))
        )
        and _matches_optional_filter(
            [workflow.academic_year] if workflow.academic_year else [],
            context.academic_year,
        )
        and _matches_optional_filter(
            list(dict.fromkeys([*workflow.effective_application_rounds, *([workflow.application_round] if workflow.application_round else [])])),
            context.application_round,
        )
    ]
    if not candidates:
        return None
    selected = max(
        candidates,
        key=lambda workflow: (
            int(
                bool(context.home_university)
                and bool(workflow.home_university)
                and _normalize(workflow.home_university or "")
                == _normalize(context.home_university or "")
            ),
            int(
                bool(context.academic_year)
                and bool(workflow.academic_year)
                and _normalize(workflow.academic_year or "")
                == _normalize(context.academic_year or "")
            ),
            int(
                bool(context.application_round)
                and bool(workflow.application_round)
                and _normalize(workflow.application_round or "")
                == _normalize(context.application_round or "")
            ),
            # With no year chosen, the newest academic year wins.
            _year_number(workflow.academic_year),
            workflow.version,
            (
                workflow.published_at.timestamp()
                if workflow.published_at
                else workflow.last_checked.timestamp()
                if workflow.last_checked
                else 0
            ),
        ),
    )
    return compose_application_workflow(selected, context)


def build_personal_application_plan(
    request: PersonalApplicationPlanRequest,
    partners: Iterable[PartnerUniversity],
    workflows: Iterable[UniversityApplicationWorkflow],
    *,
    academic_score_minimum: float | None,
    academic_source_url: str | None = None,
) -> PersonalApplicationPlanResult:
    """Create a deterministic plan from structured rules without AI inference."""

    partner_by_name = {_normalize(partner.school_name): partner for partner in partners}
    from .university_registry import resolve_university
    home = resolve_university(request.home_school)
    if home and home.id == "ccu" and len(request.preferences) > 3:
        raise ValueError("中正大學2027春季校級交換最多3個志願（簡章第1頁及申請表第1頁）。")
    if home and home.id == "cgu" and len(request.preferences) > 2:
        raise ValueError("長庚大學校級交換最多2個志願。")
    workflow_rows = list(workflows)
    contact_unit = f"{request.home_school}國際事務處／所屬系所"
    choices: list[PersonalApplicationPlanChoice] = []
    for preference in sorted(request.preferences, key=lambda item: item.rank):
        partner = partner_by_name.get(_normalize(preference.school_name))
        if partner is None:
            raise ValueError(f"{preference.school_name} 不在 {request.home_school} 目前支援的合作校名單中。")
        context = ApplicationRuleContext(
            home_university=request.home_school,
            partner_university=partner.school_name,
            college=request.college,
            department=request.department,
            academic_year=request.academic_year,
            application_round=request.application_round,
        )
        workflow = select_application_workflow(workflow_rows, context)
        # A period the school has not published yet still gets an estimated
        # checklist, built from the most recent published period.
        reference = (
            select_reference_workflow(workflow_rows, context)
            if workflow is None and (request.academic_year or request.application_round)
            else None
        )
        checks = _eligibility_checks(
            request,
            partner,
            workflow,
            academic_score_minimum=academic_score_minimum,
            academic_source_url=academic_source_url,
            contact_unit=contact_unit,
            reference=reference,
        )
        status = _choice_status(partner, checks)
        if status == ApplicationPlanEligibilityStatus.UNAVAILABLE:
            checklist = []
        elif workflow is not None:
            checklist = _workflow_checklist(preference.rank, workflow, contact_unit, preference.document_preparation_state)
        elif reference is not None:
            checklist = _reference_checklist(reference, context, contact_unit)
        else:
            checklist = []
        shown = workflow or reference
        source_urls = _unique_urls(
            [
                partner.source_url,
                academic_source_url,
                *(
                    [source.source_url for source in shown.sources]
                    if shown
                    else []
                ),
                *(
                    [url for step in shown.steps for url in step.source_urls]
                    if shown
                    else []
                ),
            ]
        )
        summary = {
            ApplicationPlanEligibilityStatus.ELIGIBLE: "目前已知條件皆通過，可依清單繼續準備。",
            ApplicationPlanEligibilityStatus.NEEDS_CONFIRMATION: f"仍有條件未能由公開資料確認，請先聯絡{contact_unit}。",
            ApplicationPlanEligibilityStatus.INELIGIBLE: "至少一項已知條件不符；如認為有例外，請向校方確認。",
            ApplicationPlanEligibilityStatus.UNAVAILABLE: partner.availability_note or "目前未列入當期開放名單。",
        }[status]
        choices.append(
            PersonalApplicationPlanChoice(
                rank=preference.rank,
                school_name=partner.school_name,
                country=partner.country,
                status=status,
                summary=summary,
                checks=checks,
                checklist=checklist,
                workflow_coverage_status=(
                    workflow.coverage_status if workflow else "not_collected"
                ),
                workflow_review_status=(workflow.review_status if workflow else None),
                reference_academic_year=(reference.academic_year if reference else None),
                source_urls=source_urls,
            )
        )
    tasks: dict[str, UnifiedApplicationTask] = {}
    for choice in choices:
        for item in choice.checklist:
            if item.id not in tasks:
                tasks[item.id] = UnifiedApplicationTask(
                    **item.model_dump(), school_names=[choice.school_name],
                )
            elif choice.school_name not in tasks[item.id].school_names:
                tasks[item.id].school_names.append(choice.school_name)
    return PersonalApplicationPlanResult(
        home_school=request.home_school,
        choices=choices,
        contact_unit=contact_unit,
        tasks=list(tasks.values()),
    )


def scope_matches(
    scope: ApplicationRuleScope,
    context: ApplicationRuleContext,
) -> bool:
    if not _matches_known_value(scope.home_universities, context.home_university):
        return False
    if not _matches_partner(scope.partner_universities, context.partner_university):
        return False
    if not _matches_required_identity(scope.colleges, context.college):
        return False
    if not _matches_required_identity(scope.departments, context.department):
        return False
    if not _matches_optional_filter(scope.academic_years, context.academic_year):
        return False
    if not _matches_optional_filter(
        scope.application_rounds, context.application_round
    ):
        return False
    return True


def scope_specificity(
    scope: ApplicationRuleScope,
    context: ApplicationRuleContext,
) -> int:
    score = 0
    if scope.departments and context.department:
        score += 32
    if scope.colleges and context.college:
        score += 16
    if scope.application_rounds and context.application_round:
        score += 8
    if scope.academic_years and context.academic_year:
        score += 4
    if scope.home_universities and context.home_university:
        score += 2
    if scope.partner_universities and context.partner_university:
        score += 1
    return score


def _personalization_requested(context: ApplicationRuleContext) -> bool:
    return any(
        value and value.strip()
        for value in (
            context.college,
            context.department,
            context.academic_year,
            context.application_round,
        )
    )


def _year_number(value: str | None) -> int:
    match = re.search(r"\d+", value or "")
    return int(match.group()) if match else 0


def _matches_partner(values: list[str], actual: str | None) -> bool:
    """Like a known-value match, but a school's spelling may differ between years."""

    if not values:
        return True
    if not actual:
        return False
    return any(
        _normalize(actual) == _normalize(value) or same_school_program(actual, value)
        for value in values
    )


def _matches_known_value(values: list[str], actual: str | None) -> bool:
    if not values:
        return True
    if not actual:
        return False
    return _normalize(actual) in {_normalize(value) for value in values}


def _matches_required_identity(values: list[str], actual: str | None) -> bool:
    if not values:
        return True
    if not actual:
        return False
    return _normalize(actual) in {_normalize(value) for value in values}


def _matches_optional_filter(values: list[str], actual: str | None) -> bool:
    if not values or not actual:
        return True
    return _normalize(actual) in {_normalize(value) for value in values}


def _eligibility_checks(
    request: PersonalApplicationPlanRequest,
    partner: PartnerUniversity,
    workflow: UniversityApplicationWorkflow | None,
    *,
    academic_score_minimum: float | None,
    academic_source_url: str | None,
    contact_unit: str,
    reference: UniversityApplicationWorkflow | None = None,
) -> list[ApplicationPlanEligibilityCheck]:
    checks: list[ApplicationPlanEligibilityCheck] = []
    partner_source = partner.source_url
    from .university_registry import resolve_university
    home = resolve_university(request.home_school)
    ncku_current_rules = False
    ncku_cycle_note = "已核實的成大母校簡章僅適用116-1；本筆合作方案或所選年度／梯次尚未具備相符證據，不能沿用該期資格門檻。"
    if is_ncku(request.home_school):
        from .ncku_guidelines_review import GUIDE_URL, ncku_1161_rules_apply
        ncku_current_rules = ncku_1161_rules_apply(partner, request.academic_year, request.application_round)
        academic_source_url = GUIDE_URL
        if not ncku_current_rules:
            checks.append(_check("source_cycle", "needs_confirmation", "成大規則適用年度與梯次",
                                 ncku_cycle_note, source_url=GUIDE_URL, contact_unit=contact_unit))
    if home and home.id == "ccu":
        from .ccu_sources import GUIDELINES_URL
        gpa = request.academic_gpa
        checks.append(_check("academic_gpa", "needs_confirmation" if gpa is None else "pass" if gpa >= 3 else "fail",
            "中正歷年GPA門檻", "尚未提供GPA；歷年GPA至少3.0且平均至少70分，兩項均須符合。" if gpa is None else f"歷年GPA {gpa:g}，門檻3.0（簡章第1頁）。",
            source_url=GUIDELINES_URL, contact_unit=contact_unit if gpa is None or gpa < 3 else None))
        checks.append(_check("home_year", "needs_confirmation", "中正在校年級與修業期間",
            "須在中正就讀滿兩學期，大二至大四上／碩博士二年級以上；大四專案須承辦確認（簡章第1頁、申請表第1頁）。",
            source_url=GUIDELINES_URL, contact_unit=contact_unit))
        if partner.application_window_status == "closed":
            checks.append(_check("home_deadline", "needs_confirmation", "校內申請期限",
                "2027春季校內收件已截止；僅已有申請／提名者可依通知繼續，不代表仍接受新申請。",
                source_url=partner.field_evidence["application_deadline"].source_url, contact_unit=contact_unit))
        if request.academic_year and request.academic_year != partner.academic_year or request.application_round and not request.application_round.startswith(partner.application_round or "2027春季"):
            checks.append(_check("source_cycle", "needs_confirmation", "資料適用年度與梯次",
                "已核實資料僅適用115學年度第二學期／2027春季，所選新版尚未核實。",source_url=partner_source,contact_unit=contact_unit))
    if partner.application_window_status == "upcoming":
        checks.append(_check("home_deadline", "needs_confirmation", "校內申請尚未開始",
            partner.availability_note or "已公告申請日期，但尚未開始受理；請依母校公告日期辦理。",
            source_url=partner_source, contact_unit=contact_unit))
    elif home and home.id == "ntnu" and partner.application_window_status != "open":
        checks.append(_check("home_deadline", "needs_confirmation", "校內申請時窗",
            "校級收件已截止；須確認已有申請或提名資格。" if partner.application_window_status == "closed"
            else "校級系統開放時間或院系所辦理期限尚待確認，不能視為目前可送件。",
            source_url=partner_source, contact_unit=contact_unit))
    if partner.availability_status != "open":
        checks.append(
            _check(
                "availability",
                "needs_confirmation" if partner.availability_status == "needs_confirmation" or is_fju(request.home_school) or ((is_ntu(request.home_school) or is_ncu(request.home_school)) and partner.quota is None) or (is_ntu(request.home_school) and ntu_published_quota(partner)) else "fail",
                "當期名額",
                partner.availability_note
                or ("輔大 116-1 名額表預計於 2026 年 11 月底公告；目前顯示姊妹校專頁與 115-2／115-1 甄選名額供規劃參考。" if is_fju(request.home_school) else "這筆資料目前未列入當期公開開放名單。"),
                source_url=partner_source,
                contact_unit=contact_unit,
            )
        )
    else:
        checks.append(
            _check(
                "availability",
                "pass",
                "當期名額",
                "當期名額已列；校內收件已截止。" if partner.application_window_status == "closed" else "當期名額已列；校內申請尚未開始。" if partner.application_window_status == "upcoming" else "目前列在公開可申請名單中。",
                source_url=partner_source,
            )
        )

    if is_ntu(request.home_school) or is_ncu(request.home_school) or is_fju(request.home_school):
        checks.append(_check("college", "needs_confirmation", "學院／學系範圍",
                             "合作校本期學院與系所範圍尚未全面確認；詳情頁的既有條件僅供參考。",
                             source_url=partner_source, contact_unit=contact_unit))
    elif not request.college and not request.department:
        checks.append(
            _check(
                "college",
                "needs_confirmation",
                "學院／學系範圍",
                "尚未提供學院或學系，無法套用合作校範圍。",
                source_url=partner_source,
                contact_unit=contact_unit,
            )
        )
    elif partner_scope_needs_confirmation(partner, "colleges"):
        checks.append(
            _check(
                "college",
                "needs_confirmation",
                "學院／學系範圍",
                f"公開資料沒有明確學院範圍，請向{contact_unit}確認。",
                source_url=partner_source,
                contact_unit=contact_unit,
            )
        )
    else:
        college_matches = any(
            value and _partner_scope_matches(partner.colleges, value)
            for value in (request.college, request.department)
        )
        checks.append(
            _check(
                "college",
                "pass" if college_matches else "fail",
                "學院／學系範圍",
                (
                    f"你的 {request.department or request.college} 符合公開範圍：{partner.colleges}。"
                    if college_matches
                    else f"你的 {request.department or request.college} 不在公開範圍：{partner.colleges}。"
                ),
                source_url=partner_source,
                contact_unit=None if college_matches else contact_unit,
            )
        )

    if is_ncu(request.home_school):
        checks.append(_check("degree_level", "needs_confirmation", "學制與學籍",
                             "中央校內在职專班可申請；大學部需有至少一學年在學成績，碩一可附大學歷年成績。須以甄選身分出國且保有學籍。外校當期學制與track另查。",
                             source_url=academic_source_url, contact_unit=contact_unit))
    elif is_ntu(request.home_school):
        checks.append(_check("degree_level", "needs_confirmation", "學制與學籍",
                             "校內須為在學學士二年級以上或研究生；合作校本期可提名學制、在學狀態與年級仍須確認。",
                             source_url=partner_source, contact_unit=contact_unit))
    elif is_fju(request.home_school):
        deg_status, deg_detail = fju_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與學籍",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_scu(request.home_school):
        deg_status, deg_detail = scu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與學籍",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_ntnu(request.home_school):
        deg_status, deg_detail = ntnu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學學期資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
        # Passing the home enrollment rule does not establish host eligibility.
        host_degree = resolved_degree_level(request.degree_level, request.current_year)
        host_match = (None if not host_degree or partner_scope_needs_confirmation(partner, "degree_levels")
                      else partner_degree_scope_matches(partner, request.college or request.department, host_degree))
        host_status = "needs_confirmation" if host_match is None else "pass" if host_match else "fail"
        host_detail = ("合作校本期學制範圍尚待確認；母校學籍資格通過不代表符合接待校條件。"
                       if host_match is None else f"你的學制{'符合' if host_match else '不在'}合作校公開範圍：{partner.degree_levels}。")
        checks.append(_check("partner_degree_level", host_status, "合作校學制",
                             host_detail, source_url=partner_source,
                             contact_unit=None if host_status == "pass" else contact_unit))
    elif is_cycu(request.home_school):
        deg_status, deg_detail = cycu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學學期資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_ntust(request.home_school):
        deg_status, deg_detail = ntust_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_yzu(request.home_school):
        deg_status, deg_detail = yzu_degree_check(request.degree_level, request.current_year, partner_country=partner.country, program_type=partner.program_type)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_fcu(request.home_school):
        deg_status, deg_detail = fcu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_nsysu(request.home_school):
        deg_status, deg_detail = nsysu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_nchu(request.home_school):
        deg_status, deg_detail = nchu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_ntut(request.home_school):
        deg_status, deg_detail = ntut_degree_check(request.degree_level, request.current_year, partner_country=partner.country, program_type=partner.program_type)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_nccu(request.home_school):
        deg_status, deg_detail = nccu_degree_check(request.degree_level, request.current_year, partner_country=partner.country)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_ncku(request.home_school):
        deg_status, deg_detail = (ncku_degree_check(request.degree_level, request.current_year)
                                  if ncku_current_rules else ("needs_confirmation", ncku_cycle_note))
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
        host_degree = resolved_degree_level(request.degree_level, request.current_year)
        host_match = (None if not ncku_current_rules or not host_degree or partner_scope_needs_confirmation(partner, "degree_levels")
                      else partner_degree_scope_matches(partner, request.college or request.department, host_degree))
        host_status = "needs_confirmation" if host_match is None else "pass" if host_match else "fail"
        checks.append(_check("partner_degree_level", host_status, "成大表列合作校學制範圍",
                             "合作校學制範圍有缺漏或衝突，須另行確認。" if host_match is None
                             else f"你的學制{'符合' if host_match else '不在'}成大本期合作校表列範圍：{partner.degree_levels}；接待校當期完整條件仍須核對。",
                             source_url=partner_source, contact_unit=None if host_status == "pass" else contact_unit))
    elif is_nycu(request.home_school):
        deg_status, deg_detail = nycu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_nthu(request.home_school):
        deg_status, deg_detail = nthu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_pccu(request.home_school):
        deg_status, deg_detail = pccu_degree_check(request.degree_level, request.current_year, program_type=partner.program_type, partner_country=partner.country)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_wzu(request.home_school):
        deg_status, deg_detail = wzu_degree_check(request.degree_level, request.current_year, program_type=partner.program_type)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_nkust(request.home_school):
        deg_status, deg_detail = nkust_degree_check(request.degree_level, request.current_year, program_type=partner.program_type, academic_year=request.academic_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_yuntech(request.home_school):
        deg_status, deg_detail = yuntech_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_ntou(request.home_school):
        deg_status, deg_detail = ntou_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_ncue(request.home_school):
        deg_status, deg_detail = ncue_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_nknu(request.home_school):
        deg_status, deg_detail = nknu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_tmu(request.home_school):
        deg_status, deg_detail = tmu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_csmu(request.home_school):
        deg_status, deg_detail = csmu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_cmu(request.home_school):
        deg_status, deg_detail = cmu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif is_kmu(request.home_school):
        deg_status, deg_detail = kmu_degree_check(request.degree_level, request.current_year)
        checks.append(_check("degree_level", deg_status, "學制與在學年級資格",
                             deg_detail,
                             source_url=academic_source_url, contact_unit=None if deg_status == "pass" else contact_unit))
    elif not request.degree_level:
        checks.append(
            _check(
                "degree_level",
                "needs_confirmation",
                "學制",
                "尚未提供目前學制。",
                source_url=partner_source,
                contact_unit=contact_unit,
            )
        )
    elif partner_scope_needs_confirmation(partner, "degree_levels"):
        checks.append(
            _check(
                "degree_level",
                "needs_confirmation",
                "學制",
                f"公開資料沒有明確學制範圍，請向{contact_unit}確認。",
                source_url=partner_source,
                contact_unit=contact_unit,
            )
        )
    else:
        degree = resolved_degree_level(request.degree_level, request.current_year)
        degree_matches = partner_degree_scope_matches(partner, request.college or request.department, degree)
        coupled_match = coupled_academic_scope_matches(
            partner, request.college or request.department, degree
        )
        degree_detail = (
            f"你的學制符合公開範圍：{partner.degree_levels}。"
            if degree_matches else f"你的學制不在公開範圍：{partner.degree_levels}。"
        )
        if coupled_match is not None:
            degree_detail = f"你的學院／學制配對{'符合' if coupled_match else '不符'}公開範圍：{request.college or request.department}／{degree}；{partner.degree_levels}。"
        if degree_matches is None:
            degree_detail = f"研究所尚未區分碩博士，不能判定符合學院／學制範圍：{partner.degree_levels}；請設定碩士班或博士班。"
        checks.append(
            _check(
                "degree_level",
                "needs_confirmation" if degree_matches is None else "pass" if degree_matches else "fail",
                "學制",
                degree_detail,
                source_url=partner_source,
                contact_unit=None if degree_matches else contact_unit,
            )
        )

    if is_ncu(request.home_school):
        status, detail = ncu_academic_check(request.degree_level, request.academic_score, request.current_year)
        checks.append(_check("academic_score", status, "校內成績門檻", detail, source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit))
    elif is_ntu(request.home_school):
        status, detail = ntu_academic_check(request.degree_level, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "校內成績門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_fju(request.home_school):
        status, detail = fju_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "校內成績門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_scu(request.home_school):
        status, detail = scu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "校內成績門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_ntnu(request.home_school):
        status, detail = ntnu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "校內學業與 EMI 修課表現", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_cycu(request.home_school):
        status, detail = cycu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "校內 GPA 或班排門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_ntust(request.home_school):
        status, detail = ntust_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent, partner_country=partner.country)
        checks.append(_check(
            "academic_score", status, "校內學業名次與平均門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_yzu(request.home_school):
        status, detail = yzu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent, program_type=partner.program_type)
        checks.append(_check(
            "academic_score", status, "申請管道與學業條件", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_fcu(request.home_school):
        status, detail = fcu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "校內 GPA 3.0 與系排門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_nsysu(request.home_school):
        status, detail = nsysu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "校內歷年班排名與書審門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_nchu(request.home_school):
        status, detail = nchu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "校內歷年總平均 60 分與書審門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_ntut(request.home_school):
        status, detail = ntut_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent, program_type=partner.program_type)
        checks.append(_check(
            "academic_score", status, "北科校級交換與獎助成績條件", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_nccu(request.home_school):
        status, detail = nccu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent, partner_country=partner.country)
        checks.append(_check(
            "academic_score", status, "政大班排換算／研究所 70 分與甄選門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_ncku(request.home_school):
        status, detail = (ncku_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
                          if ncku_current_rules else ("needs_confirmation", ncku_cycle_note))
        checks.append(_check(
            "academic_score", status, "成大前一學期平均77分或班／系排名前50%（研究所無最低分數門檻）", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_nycu(request.home_school):
        status, detail = nycu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "陽明交大書審總分 60 分門檻與獎學金 GPA／排名基準", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_nthu(request.home_school):
        status, detail = nthu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "清大前一學年 GPA 3.20 或系排前 50% 門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_pccu(request.home_school):
        status, detail = pccu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent, program_type=partner.program_type, partner_country=partner.country)
        checks.append(_check(
            "academic_score", status, "文大各管道與接待校學業條件", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_wzu(request.home_school):
        status, detail = wzu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent, program_type=partner.program_type)
        checks.append(_check(
            "academic_score", status, "文藻歷年學業總平均整數 70 分（語言學習組 65 分）與操行 80 分門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_nkust(request.home_school):
        status, detail = nkust_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "高科大學業條件與接待校要求（操行及獎助另列）", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_yuntech(request.home_school):
        status, detail = yuntech_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "雲科大歷年平均 75 分或班排前 50% 及操行 80 分門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_ntou(request.home_school):
        status, detail = ntou_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "海大前一學期及格與接待校學業要求", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_ncue(request.home_school):
        status, detail = ncue_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "彰師大操行80分、學海飛颺平均80分（或班排前30%）與姊妹校門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_nknu(request.home_school):
        status, detail = nknu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "高師大學士班平均70分（GPA 2.44）且班排前50%／碩博80分（GPA 3.38）與操行80分門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_tmu(request.home_school):
        status, detail = tmu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "北醫大學海飛颺／惜珠系排前40%或班排前30%（研究所免排）、雙聯GPA 3.0（75分）與操行80分門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_csmu(request.home_school):
        status, detail = csmu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "中山醫學海飛颺／惜珠系排前40%或班排前30%（研究所免排）、雙聯GPA 2.75–3.2（75分）與操行80分門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_cmu(request.home_school):
        status, detail = cmu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "中國醫藥大學歷年平均80分（GPA 3.0／A-）或班排前20%（學海飛颺前50%）與操行80分門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif is_kmu(request.home_school):
        status, detail = kmu_academic_check(request.degree_level, request.academic_score, request.academic_gpa, request.class_rank_percent)
        checks.append(_check(
            "academic_score", status, "高雄醫學大學歷年平均70分（GPA 2.44）或班排前50%（學海飛颺GPA 3.0或前50%）與操行80分門檻", detail,
            source_url=academic_source_url, contact_unit=None if status == "pass" else contact_unit,
        ))
    elif academic_score_minimum is None:
        checks.append(
            _check(
                "academic_score",
                "needs_confirmation",
                "校內成績門檻",
                f"目前沒有可計算的校內成績門檻，請向{contact_unit}確認。",
                source_url=academic_source_url,
                contact_unit=contact_unit,
            )
        )
    elif request.academic_score is None:
        checks.append(
            _check(
                "academic_score",
                "needs_confirmation",
                "校內成績門檻",
                f"尚未提供學業平均；公開基本門檻為 {academic_score_minimum:g} 分。",
                source_url=academic_source_url,
                contact_unit=contact_unit,
            )
        )
    else:
        academic_pass = request.academic_score >= academic_score_minimum
        checks.append(
            _check(
                "academic_score",
                "pass" if academic_pass else "fail",
                "校內成績門檻",
                f"學業平均 {request.academic_score:g} 分，{'達到' if academic_pass else '未達'}公開基本門檻 {academic_score_minimum:g} 分。",
                source_url=academic_source_url,
                contact_unit=None if academic_pass else contact_unit,
            )
        )

    language_threshold = _partner_language_threshold(partner, request.language_test, request.degree_level)
    if is_ntu(request.home_school):
        # NTU's partner requirements in this bundle are not cycle-confirmed.
        language_threshold = None
        home_status, home_detail = ntu_language_check(request.language_test, request.language_score)
        checks.append(_check("home_language_score", home_status, "校內語組門檻", home_detail, source_url=academic_source_url, contact_unit=contact_unit))
    if is_ncu(request.home_school):
        language_threshold = None
        home_status, home_detail = ncu_language_check(request.language_test, request.language_score)
        checks.append(_check("home_language_score", home_status, "校內正式語檢", home_detail, source_url=academic_source_url, contact_unit=contact_unit))
    if is_fju(request.home_school):
        home_status, home_detail = fju_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "輔大語組門檻與換分", home_detail, source_url=FJU_LANG_SCORE_URL, contact_unit=None if home_status == "pass" else contact_unit))
    if is_scu(request.home_school):
        home_status, home_detail = scu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "東吳語檢資格與採認", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_ntnu(request.home_school):
        home_status, home_detail = ntnu_language_check(request.language_test, request.language_score, partner_country=partner.country, program_type=partner.program_type)
        checks.append(_check("home_language_score", home_status, "臺師大四語組資格與採認", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_cycu(request.home_school):
        home_status, home_detail = cycu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "中原外語檢定與兩岸組資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_ntust(request.home_school):
        home_status, home_detail = ntust_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "臺科大語檢門檻與獎學金標準", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_yzu(request.home_school):
        home_status, home_detail = yzu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "元智兩年內有效語檢與兩岸組資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_fcu(request.home_school):
        home_status, home_detail = fcu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "逢甲有效外語檢定與方案適用範圍", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_nsysu(request.home_school):
        home_status, home_detail = nsysu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "中山大學三線語檢門檻與中國免語檢資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_nchu(request.home_school):
        home_status, home_detail = nchu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "中興大學 CEFR B2 語檢門檻與大陸免語檢資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_ntut(request.home_school):
        home_status, home_detail = ntut_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "臺北科大接待校語檢條件待核對", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_nccu(request.home_school):
        home_status, home_detail = nccu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "政大八大語組語檢門檻與大陸免語檢資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_ncku(request.home_school):
        home_status, home_detail = (ncku_language_check(request.language_test, request.language_score, partner_country=partner.country)
                                    if ncku_current_rules else ("needs_confirmation", ncku_cycle_note))
        checks.append(_check("home_language_score", home_status, "成大116-1校內語檢門檻（中國交換也須語言證明）", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_nycu(request.home_school):
        home_status, home_detail = nycu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "陽明交大外語檢定必繳規定（TOEIC 須含聽讀說寫）與大陸免語檢資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_nthu(request.home_school):
        home_status, home_detail = nthu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "清大海外交換 TOEFL iBT 79 / IELTS 6.5 門檻與大陸免語檢資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_pccu(request.home_school):
        home_status, home_detail = pccu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "文大各管道與接待校語言條件", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_wzu(request.home_school):
        home_status, home_detail = wzu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "文藻初審語檢加分與接待校語言條件", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_nkust(request.home_school):
        home_status, home_detail = nkust_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "高科大語檢證明與接待校條件", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_yuntech(request.home_school):
        home_status, home_detail = yuntech_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "雲科大英語授課 TOEIC 650 基準（東南亞及大陸除外）與 40 分制語檢評分", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_ntou(request.home_school):
        home_status, home_detail = ntou_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "海大附表一外語能力最低門檻（TOEFL 60／IELTS 5.0／TOEIC 600／JLPT N3／TOPIK 3）與大陸免語檢資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_ncue(request.home_school):
        home_status, home_detail = ncue_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "彰師大國外交換 CEFR B1 外語門檻（TOEIC 550／TOEFL 61／IELTS 5.0／JLPT N3／TOPIK 2）與大陸免語檢資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_nknu(request.home_school):
        home_status, home_detail = nknu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "高師大兩年內有效語檢、校內獎助 CEFR B1／B2 標準與大陸免語檢資格", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_tmu(request.home_school):
        home_status, home_detail = tmu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "北醫大學海飛颺／惜珠（TOEFL 79／75、IELTS 5.5／5.0、JLPT N2）與校內獎學金 CEFR B2 標準", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_csmu(request.home_school):
        home_status, home_detail = csmu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "中山醫雙聯（TOEFL 79–80、IELTS 6.5、Duolingo 105）、日韓語檢（JLPT N2–N3／TOPIK 2–3）與學海標準", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_cmu(request.home_school):
        home_status, home_detail = cmu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "中國醫藥大學外語基準（TOEFL 57／IELTS 4.0／TOEIC 550）、雙聯（IELTS 6.5／TOEFL 79+）與日韓語檢（JLPT N2–N3／TOPIK 2–3）標準", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    if is_kmu(request.home_school):
        home_status, home_detail = kmu_language_check(request.language_test, request.language_score, partner_country=partner.country)
        checks.append(_check("home_language_score", home_status, "高雄醫學大學英語組基準（TOEFL 69／IELTS 6.0／TOEIC 650／全民英檢中高級初試）與日語組基準（JLPT N4+）標準", home_detail, source_url=academic_source_url, contact_unit=None if home_status == "pass" else contact_unit))
    language_label = {
        "toeic": "TOEIC",
        "ielts": "IELTS",
        "toefl": "TOEFL iBT",
        "toefl_new": "TOEFL iBT（新制6分制）",
        "duolingo": "Duolingo",
        "other": "其他語言證明",
    }.get(request.language_test or "", "語言證明")
    if not request.language_test or request.language_test == "other":
        checks.append(
            _check(
                "language_score",
                "needs_confirmation",
                "語言門檻",
                f"尚未選擇可自動比對的語言測驗，請向{contact_unit}確認可接受的證明。",
                source_url=partner_source,
                contact_unit=contact_unit,
            )
        )
    elif request.language_score is None:
        checks.append(
            _check(
                "language_score",
                "needs_confirmation",
                "語言門檻",
                f"尚未提供 {language_label} 成績。",
                source_url=partner_source,
                contact_unit=contact_unit,
            )
        )
    elif language_threshold is None:
        checks.append(
            _check(
                "language_score",
                "needs_confirmation",
                "語言門檻",
                (partner.language_review_note or f"公開資料無法可靠解析 {language_label} 最低分，請向{contact_unit}確認。"),
                source_url=partner_source,
                contact_unit=contact_unit,
            )
        )
    else:
        language_pass = request.language_score >= language_threshold
        checks.append(
            _check(
                "language_score",
                "pass" if language_pass else "fail",
                "語言門檻",
                f"{language_label} {request.language_score:g}，{'達到' if language_pass else '未達'}公開門檻 {language_threshold:g}。",
                source_url=partner_source,
                contact_unit=None if language_pass else contact_unit,
            )
        )

    checks.extend(
        _workflow_context_checks(
            request,
            workflow,
            contact_unit=contact_unit,
            reference=reference,
        )
    )
    return checks


def _workflow_context_checks(
    request: PersonalApplicationPlanRequest,
    workflow: UniversityApplicationWorkflow | None,
    *,
    contact_unit: str,
    reference: UniversityApplicationWorkflow | None = None,
) -> list[ApplicationPlanEligibilityCheck]:
    source_url = workflow.sources[0].source_url if workflow and workflow.sources else None
    matching_round = None
    if workflow and request.application_round:
        matching_round = next((value for value in [*workflow.effective_application_rounds, workflow.application_round or ""]
            if _normalize(value) == _normalize(request.application_round)), None)
    checks: list[ApplicationPlanEligibilityCheck] = []
    for code, title, requested, actual in (
        ("academic_year", "學年度", request.academic_year, workflow.academic_year if workflow else None),
        ("application_round", "申請梯次", request.application_round, matching_round),
    ):
        if not requested:
            checks.append(
                _check(
                    code,
                    "needs_confirmation",
                    title,
                    f"尚未選擇{title}，不能確認這份流程是否適用。",
                    source_url=source_url,
                    contact_unit=contact_unit,
                )
            )
        elif actual and _normalize(actual) == _normalize(requested):
            checks.append(
                _check(
                    code,
                    "pass",
                    title,
                    f"已套用 {actual} 的結構化流程。",
                    source_url=source_url,
                )
            )
        else:
            checks.append(
                _check(
                    code,
                    "needs_confirmation",
                    title,
                    f"目前流程未明確標示 {requested}；請向{contact_unit}確認適用版本。",
                    source_url=source_url,
                    contact_unit=contact_unit,
                )
            )
    workflow_published = bool(
        workflow
        and workflow.steps
        and workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
    )
    if workflow_published:
        workflow_detail = f"已找到 {len(workflow.steps)} 個已發布的結構化步驟；其中標示待確認的項目仍須聯絡指定單位。"
    elif workflow and workflow.steps:
        workflow_detail = f"已找到 {len(workflow.steps)} 個結構化步驟，但整體流程尚未標示為已發布；只可直接採用其中標示已查核的項目，其餘請向{contact_unit}確認。"
    elif reference is not None:
        reference_label = (
            f"{reference.academic_year} 學年度" if reference.academic_year else "先前"
        )
        workflow_detail = (
            f"你選的年度與梯次尚無已發布的結構化流程；清單以{reference_label}"
            f"已查核流程推估，只代表可能要準備的項目，沒有官方期限，實際文件與日期請待{contact_unit}公告後確認。"
        )
    else:
        workflow_detail = f"尚無可用的結構化申請步驟，請向{contact_unit}索取當期流程。"
    checks.append(
        _check(
            "workflow",
            "pass" if workflow_published else "needs_confirmation",
            "申請步驟",
            workflow_detail,
            source_url=source_url,
            contact_unit=None if workflow_published else contact_unit,
        )
    )
    return checks


def _workflow_checklist(
    preference_rank: int,
    workflow: UniversityApplicationWorkflow | None,
    contact_unit: str,
    document_preparation_state=None,
) -> list[ApplicationPlanChecklistItem]:
    if workflow is None:
        return []
    context = workflow.applied_context
    period_matches = bool(
        context and context.academic_year and workflow.academic_year
        and _normalize(context.academic_year) == _normalize(workflow.academic_year)
        and context.application_round
        and any(_normalize(value) == _normalize(context.application_round)
            for value in [*workflow.effective_application_rounds, workflow.application_round or ""] if value)
    )
    workflow_sources = [source.source_url for source in workflow.sources]
    checklist: list[ApplicationPlanChecklistItem] = []
    rule_tasks: dict[str, list[str]] = {}
    for index, step in enumerate(workflow.steps, start=1):
        if step.rule_id:
            rule_tasks.setdefault(step.rule_id, []).append(preparation_identity(workflow, step, index)[0])
    for index, step in enumerate(workflow.steps, start=1):
        task_id, task_scope, signature = preparation_identity(workflow, step, index)
        link = document_link_for_step(step)
        applicability = [result for requirement in step.document_requirements
                         if (result := document_applicability(workflow.home_university, workflow.school_name, requirement, document_preparation_state))]
        inactive = {result.requirement_name for result in applicability
                    if result.status != "applicable"}
        if link and inactive:
            link = link.model_copy(update={
                "requirement_names": [name for name in link.requirement_names if name not in inactive],
                "unmapped_requirement_names": [name for name in link.unmapped_requirement_names if name not in inactive],
            })
        confirmed = (
            step.support_status
            in {ApplicationSupportStatus.VERIFIED, ApplicationSupportStatus.NOT_APPLICABLE}
            and not step.needs_confirmation
        )
        confirmation_contact = (
            step.confirmation_contact
            or step.responsible_unit
            or contact_unit
        )
        source_urls = _unique_urls(
            [
                *step.source_urls,
                *step.official_form_urls,
                *(url for requirement in step.document_requirements for url in requirement.source_urls),
                *workflow_sources,
            ]
        )
        checklist.append(
            ApplicationPlanChecklistItem(
                id=task_id,
                order=step.order,
                phase=step.phase,
                title=step.title if confirmed else f"確認：{step.title}",
                detail=(
                    step.summary
                    if confirmed
                    else f"{step.summary} 尚有未確認欄位，請先向{confirmation_contact}核對後再執行。"
                ),
                responsible_unit=(
                    step.responsible_unit or step.responsible_party or contact_unit
                ),
                support_status=step.support_status,
                needs_confirmation=not confirmed,
                document_applicability=applicability,
                confirmation_contact=(None if confirmed else confirmation_contact),
                source_urls=source_urls,
                task_scope=task_scope,
                source_signature=signature,
                official_deadline_at=(step.deadline_at if confirmed
                    and workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
                    and workflow.published_at and workflow.published_at.tzinfo
                    and period_matches and workflow.applicability_status.value == "verified"
                    and step.deadline_status.value == "verified_exact"
                    and step.deadline_checked_at and step.deadline_checked_at.tzinfo and step.deadline_source_url
                    and step.deadline_at and step.deadline_at.tzinfo else None),
                deadline_source_url=step.deadline_source_url,
                dependency_ids=[rule_tasks[rule][0] if len(rule_tasks.get(rule, [])) == 1
                    else f"unresolved-rule:{rule}" for rule in step.depends_on_rule_ids],
                document_link=link,
                suggested_effort_hours=suggest_effort_hours(step, link),
            )
        )
    return checklist


def select_reference_workflow(
    workflows: Iterable[UniversityApplicationWorkflow],
    context: ApplicationRuleContext,
) -> UniversityApplicationWorkflow | None:
    """Pick the newest published period of the same school pair as a stand-in.

    Only the structure is reused. The result never supplies deadlines, and the
    student's year and round are not matched against it.
    """

    partner_key = _normalize(context.partner_university or "")
    home_key = _normalize(context.home_university or "")
    candidates = [
        workflow
        for workflow in workflows
        if (
            _normalize(workflow.school_name) == partner_key
            or (not is_ncu(context.home_university)
                and same_school_program(workflow.school_name, context.partner_university or ""))
        )
        and (not home_key or _normalize(workflow.home_university) == home_key)
        and workflow.steps
        and (not is_ncu(context.home_university)
             or workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED)
    ]
    if not candidates:
        return None

    def recency(workflow: UniversityApplicationWorkflow) -> tuple[int, int, float]:
        match = re.search(r"\d+", workflow.academic_year or "")
        stamp = workflow.published_at or workflow.last_checked
        return (
            int(match.group()) if match else 0,
            workflow.version,
            stamp.timestamp() if stamp else 0.0,
        )

    selected = max(candidates, key=recency)
    return compose_application_workflow(
        selected,
        context.model_copy(update={"academic_year": None, "application_round": None}),
    )


def _reference_checklist(
    reference: UniversityApplicationWorkflow,
    context: ApplicationRuleContext,
    contact_unit: str,
) -> list[ApplicationPlanChecklistItem]:
    year = f"{reference.academic_year} 學年度" if reference.academic_year else "先前"
    target = " ".join(
        value for value in (
            f"{context.academic_year} 學年度" if context.academic_year else "",
            context.application_round or "",
        ) if value
    ) or "目前選擇的期間"
    sources = [source.source_url for source in reference.sources]
    checklist: list[ApplicationPlanChecklistItem] = []
    for index, step in enumerate(reference.steps, start=1):
        base_id, task_scope, signature = preparation_identity(reference, step, index)
        # The ID follows the student's target period, not the reference one, so
        # progress is never shared with a task from a real published workflow.
        digest = hashlib.sha256(
            "|".join(
                (base_id, context.academic_year or "", context.application_round or "")
            ).encode("utf-8")
        ).hexdigest()
        link = document_link_for_step(step)
        contact = step.confirmation_contact or step.responsible_unit or contact_unit
        checklist.append(
            ApplicationPlanChecklistItem(
                id=f"application-task-ref-{digest[:28]}",
                order=step.order,
                phase=step.phase,
                title=f"預估：{step.title}",
                detail=(
                    f"{target} 的官方流程尚未發布，這項依 {year}流程推估；沒有官方期限。"
                    f"請待{contact}公告後確認文件、期限與送件方式。"
                ),
                responsible_unit=step.responsible_unit or step.responsible_party or contact_unit,
                support_status=ApplicationSupportStatus.NEEDS_CONFIRMATION,
                needs_confirmation=True,
                confirmation_contact=contact,
                source_urls=_unique_urls(
                    [*step.source_urls, *step.official_form_urls, *sources]
                ),
                task_scope=task_scope,
                source_signature=signature,
                document_link=link,
                task_origin="reference_year",
                reference_academic_year=reference.academic_year,
                suggested_effort_hours=suggest_effort_hours(step, link),
            )
        )
    return checklist


def _choice_status(
    partner: PartnerUniversity,
    checks: list[ApplicationPlanEligibilityCheck],
) -> ApplicationPlanEligibilityStatus:
    if partner.availability_status != "open" and any(check.code == "availability" and check.status == "fail" for check in checks):
        return ApplicationPlanEligibilityStatus.UNAVAILABLE
    if any(check.status == "fail" for check in checks):
        return ApplicationPlanEligibilityStatus.INELIGIBLE
    if any(check.status == "needs_confirmation" for check in checks):
        return ApplicationPlanEligibilityStatus.NEEDS_CONFIRMATION
    return ApplicationPlanEligibilityStatus.ELIGIBLE


def _check(
    code: str,
    status: str,
    title: str,
    detail: str,
    *,
    source_url: str | None,
    contact_unit: str | None = None,
) -> ApplicationPlanEligibilityCheck:
    return ApplicationPlanEligibilityCheck(
        code=code,
        status=status,
        title=title,
        detail=detail,
        source_url=source_url,
        contact_unit=contact_unit,
    )


def _partner_language_threshold(
    partner: PartnerUniversity,
    language_test: str | None,
    degree_level: str | None = None,
) -> float | None:
    from .ccu_language import assess_ccu_language, is_ccu_partner

    evidence = partner.field_evidence.get("language_requirement")
    if evidence is not None and evidence.status != "verified_current":
        # A score in a historical or unresolved quotation is not a current
        # eligibility threshold, even if a regex can parse a number from it.
        return None
    if is_ccu_partner(partner):
        return assess_ccu_language(partner, language_test, degree_level).threshold
    if not language_test or language_test == "other":
        return None
    text = " ".join(
        value
        for value in [
            partner.eligibility,
            partner.application_info,
            *partner.student_summary_zh.eligibility_points,
        ]
        if value
    )
    patterns = {
        "toeic": r"(?:TOEIC|多益)\s*(?:達|至少|總分|成績)?\s*(\d{3})",
        "ielts": r"IELTS\s*(?:總分|overall|達|至少)?\s*(\d(?:\.\d)?)",
        "toefl": r"TOEFL(?:\s*iBT)?\s*(?:總分|達|至少)?\s*(\d{2,3})",
        "duolingo": r"Duolingo\s*(?:達|至少)?\s*(\d{2,3})",
    }
    # Never convert a partner's old TOEFL score into the six-point scale.
    if language_test not in patterns:
        return None
    match = re.search(patterns[language_test], text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _unique_urls(values: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().casefold().split())
