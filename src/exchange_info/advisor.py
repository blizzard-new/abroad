from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

from .ai_gateway import structured_response
from .fit_signals import course_interest_fit, school_budget_fit, teaching_language_fit
from .ntu_eligibility import is_ntu, ntu_academic_check
from .qualification_scopes import (
    college_scope_needs_confirmation as _college_scope_needs_confirmation,
    degree_scope_needs_confirmation as _degree_scope_needs_confirmation,
    college_scope_matches as _scope_matches,
    degree_scope_matches as _degree_matches,
)


from .models import (
    ApplicationPeriodDateStatus,
    AdvisorAnswer,
    AdvisorCitation,
    AdvisorPlan,
    AdvisorProfile,
    AdvisorSchoolMatch,
    AdvisorTask,
    DestinationProfile,
    PartnerUniversity,
    ProcessedPage,
    RagSearchHit,
    StudentDashboard,
    UniversityApplicationWorkflow,
)


LANGUAGE_LABELS = {
    "toeic": "TOEIC",
    "ielts": "IELTS",
    "toefl": "TOEFL iBT",
    "toefl_new": "TOEFL iBT（新制6分制）",
    "duolingo": "Duolingo",
    "other": "其他語言證明",
}
CGU_LANGUAGE_MINIMUMS = {
    "toeic": 700.0,
    "ielts": 5.5,
    "toefl": 72.0,
    "duolingo": 105.0,
}


@dataclass(frozen=True)
class Evidence:
    title: str
    source_url: str
    section: str
    text: str
    published_at: str | None = None
    last_checked: datetime | None = None
    retrieval_score: float = 0.0


def build_advisor_plan(
    profile: AdvisorProfile,
    dashboard: StudentDashboard,
    pages: list[ProcessedPage],
    workflows: list[UniversityApplicationWorkflow],
    destinations: list[DestinationProfile],
    retrieved_chunks: list[RagSearchHit] | None = None,
) -> AdvisorPlan:
    workflow_map = {_school_key(item.school_name): item for item in workflows}
    destination_map = {_school_key(item.school_name): item for item in destinations}
    open_partners = [
        partner
        for partner in dashboard.partner_universities
        if partner.availability_status == "open"
    ]
    matches = [
        _score_partner(
            partner,
            profile,
            dashboard,
            workflow_map.get(_school_key(partner.school_name)),
            destination_map.get(_school_key(partner.school_name)),
        )
        for partner in open_partners
    ]
    eligibility_order = {"matches_known": 0, "needs_confirmation": 1, "does_not_match": 2}
    matches.sort(key=lambda item: (
        eligibility_order[item.eligibility_status], -item.match_score, item.school_name.casefold()
    ))
    # A country the student chose is a request to see that country, not a hint: listing other countries above it
    # (as a small score bonus did) answers "mainland China" with German schools. Eligibility still orders the list.
    # Every school stays in `matches`, so the chosen target school can be compared whatever its country.
    country = (profile.preferred_country or "").strip()
    in_country = [item for item in matches if country and _normal(item.country) == _normal(country)]
    country_note = ""
    candidates = matches
    if country and in_country:
        candidates = in_country
        country_note = f"已依你選的「{country}」，只列出該地區的 {len(in_country)} 所開放合作校；改選「不限國家」可看全部。"
    elif country:
        country_note = f"目前沒有「{country}」的開放合作校，先列出其他地區。"
    # Keep a small set of mismatches visible without letting them displace candidates.
    recommendations = [item for item in candidates if item.eligibility_status != "does_not_match"][:20]
    recommendations += [item for item in candidates if item.eligibility_status == "does_not_match"][:5]
    qualification = _qualification_summary(profile, dashboard)
    tasks = _build_tasks(profile, dashboard, recommendations)
    answer = None
    if profile.question and profile.question.strip():
        answer = answer_question(
            profile.question,
            dashboard,
            pages,
            workflows,
            destinations,
            retrieved_chunks=retrieved_chunks,
        )

    ready_count = sum(
        item.eligibility_status == "matches_known"
        for item in recommendations
    )
    missing = _missing_profile_fields(profile)
    if missing:
        summary = f"先補上{'、'.join(missing[:3])}，推薦排序會更準確；目前已依公開資料整理 {len(candidates)} 所合作校。"
    elif ready_count:
        summary = f"目前有 {ready_count} 所優先候選；先處理高優先任務，再逐校核對最新公告。"
    else:
        summary = "目前條件仍有缺口，先完成下方任務，再重新產生選校方案。"
    if country_note:
        summary = f"{country_note}{summary}"
    mode = "ai_enhanced" if answer and answer.ai_enhanced else "source_grounded"
    return AdvisorPlan(
        school_name=dashboard.school_name,
        mode=mode,
        summary=summary,
        qualification=qualification,
        recommendations=recommendations,
        target_match=next((item for item in matches if item.school_name == profile.target_school), None),
        tasks=tasks,
        answer=answer,
    )


def answer_question(
    question: str,
    dashboard: StudentDashboard,
    pages: list[ProcessedPage],
    workflows: list[UniversityApplicationWorkflow],
    destinations: list[DestinationProfile],
    retrieved_chunks: list[RagSearchHit] | None = None,
) -> AdvisorAnswer:
    question_intent = _question_intent(question)
    evidence_rows = _collect_evidence(
        dashboard,
        pages,
        workflows,
        destinations,
        retrieved_chunks=retrieved_chunks,
    )
    ranked = _rank_evidence(question, evidence_rows)
    if not ranked:
        return AdvisorAnswer(
            question=question,
            answer="目前整理的公開資料不足以可靠回答這個問題。請改用學校名稱、文件名稱、補助、資格或截止日期等關鍵字再問一次。",
            evidence_status="not_found",
        )

    selected = [row for _, row in ranked[:5]]
    points = _evidence_points(selected, limit=6)
    citations = [
        AdvisorCitation(
            title=row.title,
            source_url=row.source_url,
            section=row.section,
            published_at=row.published_at,
            last_checked=row.last_checked,
        )
        for row in _unique_evidence(selected)
        if row.source_url
    ]
    fallback = "依目前已整理的官方資料，先確認以下重點：" if points else "目前只有相關來源，尚無足夠內容可下結論。"
    if question_intent == "initial_documents" and not any(
        _has_complete_document_list(row) for row in selected
    ):
        return AdvisorAnswer(
            question=question,
            answer="目前已查核的公開頁面只確認須填寫申請表並繳送紙本文件，尚未列出完整的校內甄選文件清單。",
            key_points=[
                "系統不會用簽證、錄取後或返國文件代替校內申請清單。",
                "請從下方官方來源確認當期表單與紙本文件要求。",
            ],
            sources=citations,
            evidence_status="limited",
            ai_enhanced=False,
        )
    ai_payload = structured_response(
        schema_name="grounded_study_abroad_answer",
        schema={
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "key_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 6,
                },
            },
            "required": ["answer", "key_points"],
            "additionalProperties": False,
        },
        instructions=(
            "你是台灣大學生交換申請顧問。只能使用提供的來源摘錄回答，使用繁體中文，每個列點不超過 60 個中文字。"
            "不得推測錄取率、不得補寫來源沒有的資格或日期；資料不足時要明確說明。"
        ),
        input_text=_question_prompt(question, selected),
    )
    ai_points = ai_payload.get("key_points") if isinstance(ai_payload, dict) else None
    if not isinstance(ai_points, list):
        ai_points = []
    cleaned_ai_points = [
        _compact_text(str(item), 160) for item in ai_points if str(item).strip()
    ][:6]
    answer_text = (
        _compact_text(str(ai_payload.get("answer", "")), 800)
        if isinstance(ai_payload, dict)
        else ""
    )
    top_score = ranked[0][0]
    return AdvisorAnswer(
        question=question,
        answer=answer_text or fallback,
        key_points=cleaned_ai_points or points,
        sources=citations,
        evidence_status="grounded" if top_score >= 8 else "limited",
        ai_enhanced=bool(answer_text),
    )


def _score_partner(
    partner: PartnerUniversity,
    profile: AdvisorProfile,
    dashboard: StudentDashboard,
    workflow: UniversityApplicationWorkflow | None,
    destination: DestinationProfile | None,
) -> AdvisorSchoolMatch:
    score = 10
    reasons: list[str] = []
    gaps: list[str] = []
    blocked = False
    blocking_reasons: list[str] = []
    confirmation_items: list[str] = []

    if profile.college:
        if _college_scope_needs_confirmation(partner.colleges):
            confirmation_items.append("合作校學院範圍尚待確認")
            gaps.append(confirmation_items[-1])
        elif _scope_matches(partner.colleges, profile.college):
            score += 20
            reasons.append("符合學院範圍")
        else:
            gaps.append("公開學院範圍可能不符")
            blocking_reasons.append(f"公開學院範圍：{partner.colleges}；你的學院：{profile.college}")
            blocked = True
    else:
        gaps.append("尚未填所屬學院")
        confirmation_items.append(gaps[-1])

    if profile.degree_level:
        if _degree_scope_needs_confirmation(partner.degree_levels):
            confirmation_items.append("合作校學制範圍尚待確認")
            gaps.append(confirmation_items[-1])
        elif _degree_matches(partner.degree_levels, profile.degree_level):
            score += 15
            reasons.append("符合目前學制")
        else:
            gaps.append("公開學制範圍可能不符")
            blocking_reasons.append(f"公開學制範圍：{partner.degree_levels}；你的學制：{profile.degree_level}")
            blocked = True
    else:
        gaps.append("尚未填目前學制")
        confirmation_items.append(gaps[-1])

    academic_minimum = dashboard.academic_score_minimum
    if is_ntu(dashboard.school_name):
        status, detail = ntu_academic_check(profile.degree_level, profile.academic_gpa, profile.class_rank_percent)
        if status == "pass":
            score += 15
            reasons.append(detail)
        else:
            gaps.append(detail)
            if status == "fail":
                blocking_reasons.append(detail)
                blocked = True
            else:
                confirmation_items.append(detail)
    elif profile.academic_score is None:
        gaps.append("尚未填學業平均")
        confirmation_items.append(gaps[-1])
    elif academic_minimum is None:
        gaps.append("本校學業平均門檻尚待確認")
        confirmation_items.append(gaps[-1])
    elif profile.academic_score >= academic_minimum:
        score += 15
        reasons.append(f"達{dashboard.school_name}公開基本成績門檻")
    else:
        gaps.append(f"學業平均未達{dashboard.school_name}公開基本門檻 {academic_minimum:g} 分")
        blocking_reasons.append(gaps[-1])
        blocked = True

    threshold = _partner_language_threshold(partner, profile.language_test)
    if not profile.language_test or profile.language_test == "other":
        gaps.append("語言證明需逐校確認")
        confirmation_items.append(gaps[-1])
    elif profile.language_score is None:
        gaps.append("尚未填語言成績")
        confirmation_items.append(gaps[-1])
    elif threshold is None:
        score += 7
        gaps.append("合作校語言門檻需核對官方來源")
        confirmation_items.append(gaps[-1])
    elif profile.language_score >= threshold:
        score += 20
        reasons.append(f"{LANGUAGE_LABELS[profile.language_test]} 達公開門檻 {threshold:g}")
    else:
        gaps.append(f"{LANGUAGE_LABELS[profile.language_test]} 未達公開門檻 {threshold:g}")
        blocking_reasons.append(gaps[-1])
        blocked = True

    home_language_minimum = dashboard.language_score_minimums.get(profile.language_test or "")
    if home_language_minimum is None:
        confirmation_items.append("本校語言資格需核對官方來源")
    elif profile.language_score is not None and profile.language_score < home_language_minimum:
        blocking_reasons.append(f"{LANGUAGE_LABELS[profile.language_test]} 未達本校公開門檻 {home_language_minimum:g}")
        gaps.append(blocking_reasons[-1])
        blocked = True

    # College matching cannot establish department-specific eligibility.
    confirmation_items.append("科系、年度與梯次仍須核對當期規定")

    if profile.preferred_country:
        if _normal(profile.preferred_country) == _normal(partner.country):
            score += 15
            reasons.append(f"位於優先國家 {partner.country}")
        else:
            score = max(0, score - 4)

    if workflow and workflow.steps:
        score += 7
        reasons.append("申請流程已有來源整理")
    else:
        gaps.append("合作校申請流程尚待完整查核")
    if destination and destination.coverage_status != "not_collected":
        score += 5
        reasons.append("生活費與住宿已有來源")
    budget = school_budget_fit(destination, profile.monthly_budget)
    if budget is not None:
        if budget.status == "within":
            score += 8
            reasons.append(
                f"來源記載的每月生活費約 NT${budget.low_twd:,}–{budget.high_twd:,}（概估），在你的預算內"
            )
        elif budget.status == "partly_within":
            gaps.append(f"來源記載的每月生活費上限約 NT${budget.high_twd:,}，可能高於你的預算")
        elif budget.status == "over":
            score = max(0, score - 10)
            gaps.append(f"來源記載的每月生活費約 NT${budget.low_twd:,}–{budget.high_twd:,}（概估），高於你的預算")
        else:
            gaps.append(f"無法比對預算：{budget.reason}")
    language = teaching_language_fit(partner, profile.preferred_teaching_language)
    if language is not None and profile.preferred_teaching_language:
        if language.status == "listed":
            score += 6
            reasons.append("語組或語言要求與你偏好的授課語言相符")
        elif language.status == "not_listed":
            score = max(0, score - 6)
            gaps.append("公開資料的語組／語言要求不是你偏好的授課語言")
    course = course_interest_fit(partner, destination, profile.course_interests)
    if course is not None:
        if course.status == "mentioned":
            reasons.append(f"公開資料提到你想修的領域：{'、'.join(course.matched_terms)}")
        else:
            gaps.append("沒有逐校課程目錄可比對你想修的領域")
    if profile.needs_scholarship:
        gaps.append("補助須另依身分與計畫審查")

    score = max(0, min(100, score))
    if blocked:
        fit_label = "目前條件不符"
        eligibility_status = "does_not_match"
    elif len(confirmation_items) > 1:
        fit_label = "資格待確認"
        eligibility_status = "needs_confirmation"
    elif score >= 78:
        fit_label = "條件高度相符"
        eligibility_status = "matches_known"
    elif score >= 52:
        fit_label = "值得進一步確認"
        eligibility_status = "matches_known"
    else:
        fit_label = "公開資料不足"
        eligibility_status = "needs_confirmation"
    source_urls = _unique_strings([partner.source_url, partner.website])
    return AdvisorSchoolMatch(
        school_name=partner.school_name,
        country=partner.country,
        match_score=score,
        fit_label=fit_label,
        eligibility_status=eligibility_status,
        blocking_reasons=blocking_reasons,
        confirmation_items=confirmation_items,
        reasons=reasons[:4],
        gaps=gaps[:4],
        source_urls=source_urls,
        image_url=partner.image_url,
        budget_fit=budget,
        teaching_language=language,
        course_interest=course,
    )


def _qualification_summary(
    profile: AdvisorProfile,
    dashboard: StudentDashboard,
) -> list[str]:
    rows: list[str] = []
    academic_minimum = dashboard.academic_score_minimum
    if is_ntu(dashboard.school_name):
        rows.append(ntu_academic_check(profile.degree_level, profile.academic_gpa, profile.class_rank_percent)[1])
    elif profile.academic_score is None:
        rows.append("學業平均尚未填寫")
    elif academic_minimum is None:
        rows.append("本校學業平均門檻待確認")
    elif profile.academic_score >= academic_minimum:
        rows.append(f"學業平均達{dashboard.school_name}公開基本門檻 {academic_minimum:g} 分")
    else:
        rows.append(f"學業平均未達{dashboard.school_name}公開基本門檻 {academic_minimum:g} 分")

    test = profile.language_test
    if not test or test == "other" or profile.language_score is None:
        rows.append("語言成績尚未完成比對")
    else:
        minimum = dashboard.language_score_minimums.get(test)
        label = LANGUAGE_LABELS[test]
        if minimum is None:
            rows.append(f"{label} 需由國際處個別認定")
        elif profile.language_score >= minimum:
            rows.append(f"{label} 達目前公開基本門檻 {minimum:g}")
        else:
            rows.append(f"{label} 未達目前公開基本門檻 {minimum:g}")
    if profile.college and profile.degree_level:
        rows.append(f"已設定 {profile.college}、{profile.degree_level} 的申請範圍")
    else:
        rows.append("補齊學院與學制後可排除不適用學校")
    if profile.department and profile.current_year:
        rows.append(f"已記錄 {profile.department}、{profile.current_year}，課程仍需逐校比對")
    return rows


def _build_tasks(
    profile: AdvisorProfile,
    dashboard: StudentDashboard,
    recommendations: list[AdvisorSchoolMatch],
) -> list[AdvisorTask]:
    tasks: list[AdvisorTask] = []
    missing = _missing_profile_fields(profile)
    if missing:
        tasks.append(
            _task(
                title="補齊個人申請條件",
                detail=f"還缺：{'、'.join(missing)}",
                category="profile",
                priority="high",
            )
        )
    academic_minimum = dashboard.academic_score_minimum
    if academic_minimum is not None and profile.academic_score is not None and profile.academic_score < academic_minimum:
        tasks.append(
            _task(
                title="先向國際處確認成績資格",
                detail=f"目前學業平均低於公開基本門檻 {academic_minimum:g} 分，送件前需確認是否有例外或其他計畫。",
                category="eligibility",
                priority="high",
                source_url=_first_source(dashboard.eligibility),
            )
        )
    test = profile.language_test
    minimum = dashboard.language_score_minimums.get(test or "")
    if minimum and (profile.language_score is None or profile.language_score < minimum):
        label = LANGUAGE_LABELS.get(test or "", "語言證明")
        tasks.append(
            _task(
                title=f"完成 {label} 門檻",
                detail=f"目前公開基本門檻為 {minimum:g}；合作校可能另有更高要求。",
                category="language",
                priority="high",
                source_url=_first_source(dashboard.language_requirements),
            )
        )

    candidate_names = {item.school_name for item in recommendations[:5]}
    deadline_rows = _dashboard_deadlines(dashboard)
    for title, deadline, source_url, detail in deadline_rows[:6]:
        remaining = (deadline - date.today()).days
        priority = "high" if remaining <= 30 else "medium" if remaining <= 90 else "low"
        tasks.append(
            _task(
                title=title,
                detail=detail,
                category="deadline",
                priority=priority,
                due_date=deadline.isoformat(),
                days_remaining=remaining,
                source_url=source_url,
            )
        )

    for item in dashboard.required_documents[:3]:
        tasks.append(
            _task(
                title=f"準備：{item.title}",
                detail=_compact_text("；".join(item.details), 160) or "打開申請文件頁確認欄位、份數與簽章。",
                category="documents",
                priority="medium",
                source_url=item.source.source_url if item.source else None,
            )
        )
    if profile.needs_scholarship:
        tasks.append(
            _task(
                title="確認可申請補助",
                detail="比對補助身分、不得重複領取限制與核銷文件。",
                category="scholarship",
                priority="medium",
                source_url=_first_source(dashboard.scholarship_info),
            )
        )
    return _unique_tasks(tasks)[:12]


def _dashboard_deadlines(
    dashboard: StudentDashboard,
) -> list[tuple[str, date, str | None, str]]:
    rows: list[tuple[str, date, str | None, str]] = []
    for period in dashboard.application_periods:
        if (
            not period.reminder_eligible
            or period.date_status != ApplicationPeriodDateStatus.VERIFIED_EXACT
            or period.deadline_at is None
        ):
            continue
        deadline = period.deadline_at.date()
        if deadline < date.today():
            continue
        rows.append(
            (
                period.title,
                deadline,
                period.source.source_url if period.source else None,
                _compact_text(period.deadline_note or period.status_note, 180),
            )
        )
    return sorted(rows, key=lambda item: item[1])


def _task(
    *,
    title: str,
    detail: str,
    category: str,
    priority: str,
    due_date: str | None = None,
    days_remaining: int | None = None,
    source_url: str | None = None,
) -> AdvisorTask:
    identity = f"{category}|{title}|{due_date or ''}"
    return AdvisorTask(
        id=hashlib.sha256(identity.encode("utf-8")).hexdigest()[:14],
        title=title,
        detail=detail,
        category=category,
        priority=priority,
        due_date=due_date,
        days_remaining=days_remaining,
        source_url=source_url,
    )


def _collect_evidence(
    dashboard: StudentDashboard,
    pages: list[ProcessedPage],
    workflows: list[UniversityApplicationWorkflow],
    destinations: list[DestinationProfile],
    retrieved_chunks: list[RagSearchHit] | None = None,
) -> list[Evidence]:
    rows: list[Evidence] = []
    page_metadata = {page.source_url: page for page in pages}
    for hit in retrieved_chunks or []:
        chunk = hit.chunk
        rows.append(
            Evidence(
                title=chunk.source_title,
                source_url=chunk.source_url,
                section=chunk.section,
                text=chunk.text,
                published_at=chunk.published_at,
                last_checked=chunk.last_checked,
                retrieval_score=hit.score,
            )
        )
    groups = [
        ("申請時程", dashboard.application_periods),
        ("計畫類型", dashboard.program_overview),
        ("申請資格", dashboard.eligibility),
        ("語言門檻", dashboard.language_requirements),
        ("必要文件", dashboard.required_documents),
        ("補助資訊", dashboard.scholarship_info),
    ]
    for section, items in groups:
        for item in items:
            if item.source:
                source_page = page_metadata.get(item.source.source_url)
                rows.append(
                    Evidence(
                        title=item.title,
                        source_url=item.source.source_url,
                        section=section,
                        text="；".join(item.details),
                        published_at=source_page.published_at if source_page else None,
                        last_checked=(source_page.crawled_at if source_page else dashboard.last_checked),
                    )
                )
    for rule in [*dashboard.document_explanations, *dashboard.rule_explanations]:
        source_url = rule.document_url or rule.source.source_url
        source_page = page_metadata.get(source_url) or page_metadata.get(rule.source.source_url)
        rows.append(
            Evidence(
                title=rule.title,
                source_url=source_url,
                section="官方文件摘要",
                text="；".join([rule.summary, *rule.key_points, *rule.applies_to]),
                published_at=source_page.published_at if source_page else None,
                last_checked=(source_page.crawled_at if source_page else dashboard.last_checked),
            )
        )
    for partner in dashboard.partner_universities:
        source_page = page_metadata.get(partner.source_url)
        summary = partner.student_summary_zh
        text = "；".join(
            value
            for value in [
                partner.country,
                partner.program_type,
                partner.colleges,
                partner.degree_levels,
                summary.study_period,
                summary.application_deadline,
                *summary.eligibility_points,
                *summary.application_steps,
                *summary.tuition_points,
            ]
            if value
        )
        rows.append(
            Evidence(
                title=partner.school_name,
                source_url=partner.source_url,
                section="合作校條件",
                text=text,
                published_at=source_page.published_at if source_page else None,
                last_checked=(source_page.crawled_at if source_page else dashboard.last_checked),
            )
        )
    for workflow in workflows:
        text = "；".join(
            part
            for step in workflow.steps
            for part in [step.title, step.summary, *step.details, *step.required_documents]
            if part
        )
        source = next(iter(workflow.sources), None)
        source_url = source.source_url if source else ""
        if text and source_url:
            rows.append(
                Evidence(
                    title=workflow.school_name,
                    source_url=source_url,
                    section="申請流程",
                    text=text,
                    last_checked=workflow.last_checked or (source.checked_at if source else None),
                )
            )
    for profile in destinations:
        text = "；".join(
            value
            for value in [
                profile.country,
                profile.city,
                profile.cost_summary,
                profile.housing_summary,
                profile.transport_summary,
                profile.campus_life_summary,
            ]
            if value
        )
        source = next((item.source_url for item in profile.sources), "")
        if text and source:
            rows.append(
                Evidence(
                    title=profile.school_name,
                    source_url=source,
                    section="生活情報",
                    text=text,
                    last_checked=profile.last_checked,
                )
            )
    for page in pages:
        text = "；".join(value for value in [page.summary, _compact_text(page.text, 900)] if value)
        if text:
            rows.append(
                Evidence(
                    title=page.title,
                    source_url=page.source_url,
                    section=page.category.value,
                    text=text,
                    published_at=page.published_at,
                    last_checked=page.crawled_at,
                )
            )
    return _unique_evidence(rows)


def _rank_evidence(question: str, rows: list[Evidence]) -> list[tuple[int, Evidence]]:
    terms = _query_terms(question)
    intent = _question_intent(question)
    ranked: list[tuple[int, Evidence]] = []
    for row in rows:
        if intent == "initial_documents" and _exclude_from_initial_documents(row):
            continue
        title = _normal(row.title)
        section = _normal(row.section)
        body = _normal(row.text)
        score = sum(
            (8 if term in title else 0)
            + (4 if term in section else 0)
            + (1 if term in body else 0)
            for term in terms
        )
        score = max(score, round(row.retrieval_score * 12))
        if score:
            ranked.append((score, row))
    return sorted(ranked, key=lambda item: (-item[0], len(item[1].text)))


def _question_intent(question: str) -> str:
    value = _normal(question)
    if any(term in value for term in ("文件", "資料", "申請表")) and any(
        term in value for term in ("申請", "甄選", "準備", "繳交")
    ):
        if not any(
            term in value
            for term in ("簽證", "錄取後", "出國前", "返國", "核銷", "補助請款")
        ):
            return "initial_documents"
    return "general"


def _exclude_from_initial_documents(row: Evidence) -> bool:
    value = _normal(f"{row.title} {row.section} {row.text}")
    incoming_markers = (
        "在台就學",
        "在臺就學",
        "入境台灣",
        "入境臺灣",
        "外僑居留",
        "居留簽證",
        "停留簽證",
        "原屬學校",
        "離開長庚大學",
        "長庚大學核發的入學",
    )
    later_stage_markers = (
        "國外學校審查通過",
        "取得入學許可",
        "錄取後",
        "出國前一個月",
        "出國日前",
        "出國前後需處理",
        "交換期結束",
        "抵達國外後",
        "返國後",
    )
    if any(marker in value for marker in (*incoming_markers, *later_stage_markers)):
        return True
    if "交換" in value:
        return False
    return any(
        program in value
        for program in ("境外短期學分", "出國實習", "學海築夢", "雙聯學位")
    )


def _has_complete_document_list(row: Evidence) -> bool:
    if _exclude_from_initial_documents(row):
        return False
    value = _normal(row.text)
    document_terms = (
        "申請表",
        "成績單",
        "讀書計畫",
        "推薦信",
        "語言證明",
        "在學證明",
        "履歷",
    )
    return sum(term in value for term in document_terms) >= 3


def _query_terms(question: str) -> set[str]:
    value = _normal(question)
    terms = set(re.findall(r"[a-z0-9][a-z0-9._+-]{1,}|[\u4e00-\u9fff]{2,}", value))
    for chunk in list(terms):
        if re.fullmatch(r"[\u4e00-\u9fff]+", chunk):
            for size in (2, 3, 4):
                terms.update(chunk[index : index + size] for index in range(max(0, len(chunk) - size + 1)))
    expansions = {
        "文件": {"申請表", "同意書", "計畫書", "成績單", "推薦信"},
        "資格": {"成績", "學制", "學院", "門檻"},
        "英文": {"語言", "toeic", "ielts", "toefl", "duolingo"},
        "補助": {"獎學金", "學海", "領航者", "經費"},
        "截止": {"期限", "申請期間", "日期"},
        "住宿": {"宿舍", "租屋", "housing"},
        "費用": {"生活費", "預算", "學費", "cost"},
        "流程": {"申請步驟", "提名", "送件"},
    }
    for trigger, additions in expansions.items():
        if trigger in value:
            terms.update(additions)
    return {term for term in terms if len(term) >= 2}


def _evidence_points(rows: list[Evidence], *, limit: int) -> list[str]:
    points: list[str] = []
    for row in rows:
        for part in re.split(r"[；。\n]+", row.text):
            compact = _compact_text(part, 180)
            if len(compact) < 8 or compact in points:
                continue
            points.append(compact)
            if len(points) >= limit:
                return points
    return points


def _question_prompt(question: str, rows: list[Evidence]) -> str:
    evidence = "\n\n".join(
        f"[{index}] {row.title}｜{row.section}\n來源：{row.source_url}\n摘錄：{_compact_text(row.text, 1800)}"
        for index, row in enumerate(rows, start=1)
    )
    return f"學生問題：{question}\n\n可使用的已查核來源：\n{evidence}"[:14_000]


def _partner_language_threshold(
    partner: PartnerUniversity,
    language_test: str | None,
) -> float | None:
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
    if language_test not in patterns:
        return None
    match = re.search(patterns[language_test], text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _missing_profile_fields(profile: AdvisorProfile) -> list[str]:
    fields = [
        (profile.college, "學院"),
        (profile.department, "科系／領域"),
        (profile.current_year, "年級"),
        (profile.degree_level, "學制"),
        (profile.academic_score, "學業平均"),
        (profile.language_test, "語言測驗"),
        (profile.language_score, "語言成績"),
        (profile.target_term, "預計學期"),
    ]
    missing = [label for value, label in fields if value is None or value == ""]
    if is_ntu(profile.school_name):
        missing = [label for label in missing if label != "學業平均"]
        if ntu_academic_check(profile.degree_level, profile.academic_gpa, profile.class_rank_percent)[0] == "needs_confirmation":
            missing.append("學年GPA或班排名")
    return missing


def _first_source(items: Iterable) -> str | None:
    for item in items:
        if getattr(item, "source", None):
            return item.source.source_url
    return None


def _unique_tasks(tasks: list[AdvisorTask]) -> list[AdvisorTask]:
    seen: set[str] = set()
    output: list[AdvisorTask] = []
    for task in tasks:
        if task.id in seen:
            continue
        seen.add(task.id)
        output.append(task)
    return sorted(
        output,
        key=lambda task: (
            {"high": 0, "medium": 1, "low": 2}[task.priority],
            task.due_date or "9999-12-31",
        ),
    )


def _unique_evidence(rows: list[Evidence]) -> list[Evidence]:
    seen: set[tuple[str, str, str]] = set()
    output: list[Evidence] = []
    for row in rows:
        key = (row.title, row.source_url, row.section)
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def _unique_strings(values: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def _school_key(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", _normal(value))


def _normal(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _compact_text(value: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", str(value or "")).strip()
    return compact if len(compact) <= limit else f"{compact[: limit - 1].rstrip()}…"
