from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

from .ai_gateway import structured_response
from .models import (
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
    matches = [
        _score_partner(
            partner,
            profile,
            dashboard,
            workflow_map.get(_school_key(partner.school_name)),
            destination_map.get(_school_key(partner.school_name)),
        )
        for partner in dashboard.partner_universities
    ]
    matches.sort(
        key=lambda item: (-item.match_score, item.school_name.casefold())
    )
    recommendations = matches[:20]
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
        item.fit_label in {"條件高度相符", "值得進一步確認"}
        for item in recommendations
    )
    missing = _missing_profile_fields(profile)
    if missing:
        summary = f"先補上{'、'.join(missing[:3])}，推薦排序會更準確；目前已依公開資料整理 {len(matches)} 所合作校。"
    elif ready_count:
        summary = f"目前有 {ready_count} 所優先候選；先處理高優先任務，再逐校核對最新公告。"
    else:
        summary = "目前條件仍有缺口，先完成下方任務，再重新產生選校方案。"
    mode = "ai_enhanced" if answer and answer.ai_enhanced else "source_grounded"
    return AdvisorPlan(
        school_name=dashboard.school_name,
        mode=mode,
        summary=summary,
        qualification=qualification,
        recommendations=recommendations,
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

    if profile.college:
        if _scope_matches(partner.colleges, profile.college):
            score += 20
            reasons.append("符合學院範圍")
        else:
            gaps.append("公開學院範圍可能不符")
            blocked = True
    else:
        gaps.append("尚未填所屬學院")

    if profile.degree_level:
        if _degree_matches(partner.degree_levels, profile.degree_level):
            score += 15
            reasons.append("符合目前學制")
        else:
            gaps.append("公開學制範圍可能不符")
            blocked = True
    else:
        gaps.append("尚未填目前學制")

    academic_minimum = dashboard.academic_score_minimum or 70
    if profile.academic_score is None:
        gaps.append("尚未填學業平均")
    elif profile.academic_score >= academic_minimum:
        score += 15
        reasons.append(f"達{dashboard.school_name}公開基本成績門檻")
    else:
        gaps.append(f"學業平均未達{dashboard.school_name}公開基本門檻 {academic_minimum:g} 分")
        blocked = True

    threshold = _partner_language_threshold(partner, profile.language_test)
    if not profile.language_test or profile.language_test == "other":
        gaps.append("語言證明需逐校確認")
    elif profile.language_score is None:
        gaps.append("尚未填語言成績")
    elif threshold is None:
        score += 7
        gaps.append("合作校語言門檻需核對官方來源")
    elif profile.language_score >= threshold:
        score += 20
        reasons.append(f"{LANGUAGE_LABELS[profile.language_test]} 達公開門檻 {threshold:g}")
    else:
        gaps.append(f"{LANGUAGE_LABELS[profile.language_test]} 未達公開門檻 {threshold:g}")
        blocked = True

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
    elif profile.monthly_budget:
        gaps.append("生活成本資料不足，暫時無法比對預算")
    if profile.needs_scholarship:
        gaps.append("補助須另依身分與計畫審查")

    score = max(0, min(100, score))
    if blocked:
        fit_label = "需先補齊條件"
    elif score >= 78:
        fit_label = "條件高度相符"
    elif score >= 52:
        fit_label = "值得進一步確認"
    else:
        fit_label = "公開資料不足"
    source_urls = _unique_strings([partner.source_url, partner.website])
    return AdvisorSchoolMatch(
        school_name=partner.school_name,
        country=partner.country,
        match_score=score,
        fit_label=fit_label,
        reasons=reasons[:4],
        gaps=gaps[:4],
        source_urls=source_urls,
        image_url=partner.image_url,
    )


def _qualification_summary(
    profile: AdvisorProfile,
    dashboard: StudentDashboard,
) -> list[str]:
    rows: list[str] = []
    academic_minimum = dashboard.academic_score_minimum or 70
    if profile.academic_score is None:
        rows.append("學業平均尚未填寫")
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
    academic_minimum = dashboard.academic_score_minimum or 70
    if profile.academic_score is not None and profile.academic_score < academic_minimum:
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
    deadline_rows = _dashboard_deadlines(dashboard, candidate_names)
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
    candidate_names: set[str],
) -> list[tuple[str, date, str | None, str]]:
    rows: list[tuple[str, date, str | None, str]] = []
    for period in dashboard.application_periods:
        for detail in period.details:
            dates = _dates_from_text(detail)
            for deadline in dates[-1:]:
                rows.append(
                    (
                        period.title,
                        deadline,
                        period.source.source_url if period.source else None,
                        _compact_text(detail, 180),
                    )
                )
    for partner in dashboard.partner_universities:
        if partner.school_name not in candidate_names:
            continue
        for deadline in _dates_from_text(partner.application_deadline or ""):
            rows.append(
                (
                    f"核對 {partner.school_name} 截止日",
                    deadline,
                    partner.source_url,
                    _compact_text(partner.application_deadline or "合作校公開期限", 180),
                )
            )
    return sorted(rows, key=lambda item: item[1])


def _dates_from_text(text: str) -> list[date]:
    value = str(text or "")
    explicit_year = re.search(r"(20\d{2})\s*年?", value)
    pairs = [
        (int(match.group(1)), int(match.group(2)))
        for match in re.finditer(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日", value)
    ]
    pairs.extend(
        (int(match.group(1)), int(match.group(2)))
        for match in re.finditer(r"(?<!\d)(\d{1,2})\s*[/.-]\s*(\d{1,2})(?!\d)", value)
    )
    today = date.today()
    dates: list[date] = []
    for month, day_value in pairs:
        year = int(explicit_year.group(1)) if explicit_year else today.year
        try:
            candidate = date(year, month, day_value)
            if not explicit_year and candidate < today:
                candidate = date(year + 1, month, day_value)
        except ValueError:
            continue
        if candidate >= today:
            dates.append(candidate)
    return sorted(set(dates))


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
    match = re.search(patterns[language_test], text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _scope_matches(scope: str | None, target: str) -> bool:
    if not scope:
        return True
    normalized = _normal(scope)
    if any(term in normalized for term in ["不限", "全校", "all", "各學院"]):
        return True
    target_value = _normal(target)
    aliases = {
        "醫學院": ["醫學", "medicine", "medical"],
        "工學院": ["工學", "工程", "engineering"],
        "管理學院": ["管理", "商學", "business", "management"],
        "資訊工程學系": ["資訊", "電腦", "computer", "informatics"],
    }
    candidates = [target_value, *aliases.get(target, [])]
    return any(candidate and _normal(candidate) in normalized for candidate in candidates)


def _degree_matches(scope: str | None, target: str) -> bool:
    if not scope:
        return True
    normalized = _normal(scope)
    aliases = {
        "大學部": ["大學部", "學士", "undergraduate", "bachelor"],
        "碩士班": ["碩士", "研究所", "master", "graduate"],
        "博士班": ["博士", "研究所", "doctoral", "phd", "graduate"],
    }
    values = aliases.get(target, [target])
    return any(_normal(value) in normalized for value in values)


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
    return [label for value, label in fields if value is None or value == ""]


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
