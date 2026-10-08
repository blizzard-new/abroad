"""Say, school by school, which parts of the public picture are still missing.

This never fills a gap. It reads what is already stored for a partner school and
labels each part available, partial, needs-confirmation or missing, with a short
Chinese note, so a student can see what to ask the school and a maintainer can
see where to research next.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from .cost_estimates import extract_monthly_estimates, primary_estimate
from .models import (
    ApplicationDeadlineStatus,
    ApplicationWorkflowReviewStatus,
    DestinationProfile,
    PartnerUniversity,
    SchoolCompletenessItem,
    SchoolDataCompleteness,
    UniversityApplicationWorkflow,
)
from .qualification_scopes import college_scope_needs_confirmation, degree_scope_needs_confirmation
from .ntu_eligibility import is_ntu

_UNPUBLISHED = re.compile(r"未公開|尚未|未取得|待補|未提供|未完成|無法.*核對|未公布|未列")
_CJK = re.compile(r"[一-鿿]")
_PRIORITY = ("eligibility", "deadline", "workflow", "documents", "cost")


def _item(
    key: str, label: str, status: str, note: str, urls: Iterable[str | None] = ()
) -> SchoolCompletenessItem:
    return SchoolCompletenessItem(
        key=key, label=label, status=status, note=note,
        source_urls=list(dict.fromkeys(url for url in urls if url))[:3],
    )


def _summary_item(key: str, label: str, text: str | None, urls: Iterable[str | None]) -> SchoolCompletenessItem:
    value = (text or "").strip()
    if not value:
        return _item(key, label, "missing", "目前沒有這項資料。", urls)
    if _UNPUBLISHED.search(value) and len(value) < 120:
        return _item(key, label, "missing", "尚未取得可核對的內容，需向學校確認。", urls)
    if _UNPUBLISHED.search(value):
        return _item(key, label, "partial", "已有部分內容，但來源也註明仍有未公開或待核對的部分。", urls)
    return _item(key, label, "available", "已有來源整理的內容。", urls)


def build_school_completeness(
    partner: PartnerUniversity,
    destination: DestinationProfile | None,
    workflow: UniversityApplicationWorkflow | None,
    *,
    home_university: str | None = None,
    include_eligibility: bool = True,
) -> SchoolDataCompleteness:
    from .ncu_eligibility import is_ncu
    if is_ncu(home_university or (destination.home_university if destination else "") or (workflow.home_university if workflow else "")):
        from .ncu_student_view import ncu_field_audit
        audit = ncu_field_audit(partner.school_name)
        if audit:
            rows = [SchoolCompletenessItem.model_validate({k:v for k,v in item.items() if k in {"key","label","status","note","source_urls"}}) for item in audit["fields"].values()]
            return SchoolDataCompleteness(school_name=partner.school_name, country=partner.country, home_university=home_university,
                items=rows, available_count=sum(r.status == "available" for r in rows), total_count=len(rows),
                score=round(sum({"available":1,"partial":.5,"needs_confirmation":.25,"missing":0}[r.status] for r in rows)/len(rows),3),
                priority_gaps=[r.label for r in rows if r.status != "available"],
                disclaimer="home與host逐欄分開；取得原文不代表116適用性已確認。尚未取得不表示官方未公告。")
    destination = destination or DestinationProfile(school_name=partner.school_name)
    urls = [source.source_url for source in destination.sources]
    items: list[SchoolCompletenessItem] = []

    ntu = is_ntu(home_university or destination.home_university or (workflow.home_university if workflow else ""))
    known = [
        bool(partner.colleges and not college_scope_needs_confirmation(partner.colleges)),
        bool(partner.degree_levels and not degree_scope_needs_confirmation(partner.degree_levels)),
        bool((partner.eligibility or "").strip() and not _UNPUBLISHED.fullmatch((partner.eligibility or "").strip())),
    ]
    if include_eligibility:
        items.append(_item(
            "eligibility", "申請資格與範圍",
            "available" if all(known) else "partial" if any(known) else "missing",
            "學院、學制與語言資格都有明確來源。" if all(known)
            else "資格、學院或學制範圍有部分不明，須向學校確認。" if any(known)
            else "公開資料沒有明確資格範圍。",
            [partner.source_url],
        ))
        if ntu:
            items[-1] = _item("eligibility", "申請資格與範圍", "needs_confirmation",
                              "已有官方參考條件，但合作校116-1名額、資格及學院／學制範圍尚未全面確認。", [partner.source_url])

    exact = [
        step for step in (workflow.steps if workflow else [])
        if step.deadline_at and step.deadline_status == ApplicationDeadlineStatus.VERIFIED_EXACT
    ]
    if exact:
        items.append(_item("deadline", "申請期限", "available", "已有附來源的精確期限。",
                           [exact[0].deadline_source_url, partner.source_url]))
    elif workflow and workflow.steps or partner.application_deadline:
        items.append(_item("deadline", "申請期限", "needs_confirmation",
                           "只有文字說明或年度梯次未確認，沒有可排進日曆的精確日期。",
                           [partner.source_url]))
    else:
        items.append(_item("deadline", "申請期限", "missing", "沒有期限資料。", [partner.source_url]))

    if workflow and workflow.steps:
        published = workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
        items.append(_item(
            "workflow", "申請流程",
            "available" if published and workflow.applicability_status.value == "verified" else "needs_confirmation",
            f"{len(workflow.steps)} 個步驟；"
            + ("已發布且適用年度已確認。" if published and workflow.applicability_status.value == "verified"
               else "尚未完成發布或適用年度／梯次確認。"),
            [source.source_url for source in workflow.sources],
        ))
    else:
        items.append(_item("workflow", "申請流程", "missing", "沒有結構化流程。", [partner.source_url]))

    requirements = [r for step in (workflow.steps if workflow else []) for r in step.document_requirements]
    if any(r.official_form_url for r in requirements):
        items.append(_item("documents", "文件與表格", "available", "有文件清單與官方表格連結。",
                           [r.official_form_url for r in requirements]))
    elif requirements:
        items.append(_item("documents", "文件與表格", "partial", "有文件名稱，但沒有官方表格連結或份數／簽章細節。"))
    else:
        items.append(_item("documents", "文件與表格", "missing", "沒有文件清單。"))

    estimates = extract_monthly_estimates(destination)
    estimate = primary_estimate(estimates)
    cost_text = (destination.cost_summary or "").strip()
    if estimate and not estimate.outdated:
        items.append(_item("cost", "每月生活費", "available", "來源明列每月生活費總額，可換算比對預算。", urls))
    elif estimate:
        items.append(_item("cost", "每月生活費", "needs_confirmation", "來源的金額是舊年度或歷史基準。", urls))
    elif cost_text and not _UNPUBLISHED.search(cost_text):
        items.append(_item("cost", "每月生活費", "partial", "有費用片段，但沒有可直接比對的每月總額。", urls))
    else:
        items.append(_item("cost", "每月生活費", "missing", "尚未取得可核對的每月生活費。", urls))

    items.append(_summary_item("housing", "住宿", destination.housing_summary, urls))
    items.append(_summary_item("transport", "交通", destination.transport_summary, urls))
    items.append(_summary_item("campus_life", "校園生活", destination.campus_life_summary, urls))
    if ntu:
        for index, item in enumerate(items):
            if item.key in {"cost", "housing", "transport", "campus_life"} and item.status == "available":
                items[index] = _item(item.key, item.label, "needs_confirmation",
                                     "已有官方參考內容；116-1適用性、當期金額及完整條件仍須確認。", item.source_urls)
    items.append(_item(
        "city", "城市", "available" if destination.city else "missing",
        "已標示所在城市。" if destination.city else "尚未標示城市。", urls,
    ))
    texts = [t for t in (destination.cost_summary, destination.housing_summary,
                         destination.transport_summary, destination.campus_life_summary) if t and t.strip()]
    if not texts:
        items.append(_item("chinese", "中文說明", "missing", "沒有可閱讀的生活說明。"))
    elif all(_CJK.search(t) for t in texts):
        items.append(_item("chinese", "中文說明", "available", "生活說明皆有中文。"))
    else:
        items.append(_item("chinese", "中文說明", "partial", "部分說明仍是外文原文。"))

    weight = {"available": 1.0, "partial": 0.5, "needs_confirmation": 0.25, "missing": 0.0}
    score = sum(weight[row.status] for row in items) / len(items)
    by_key = {row.key: row for row in items}
    gaps = [by_key[key] for key in _PRIORITY if key in by_key and by_key[key].status != "available"]
    return SchoolDataCompleteness(
        school_name=partner.school_name, country=partner.country,
        home_university=home_university or (workflow.home_university if workflow else None),
        items=items,
        available_count=sum(row.status == "available" for row in items),
        total_count=len(items),
        score=round(score, 3),
        priority_gaps=[row.label for row in gaps],
        disclaimer="這只說明本平台目前整理到哪裡；『沒有資料』不代表學校沒有公開，也不代表可以用推測補上。",
    )
