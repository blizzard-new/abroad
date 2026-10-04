"""Budget, teaching-language and course-interest signals for a school match.

Each signal reports what the public data actually says and otherwise returns
``unknown`` with the reason. None of them decides eligibility, affordability or
that a course will be offered.
"""
from __future__ import annotations

import re

from .cost_estimates import budget_fit, extract_monthly_estimates, fx_reference
from .models import (
    BudgetFit,
    CourseInterestFit,
    DestinationProfile,
    PartnerUniversity,
    TeachingLanguageFit,
)

_TRACKS = {"英語組": "english", "日語組": "japanese", "中文組": "chinese"}
_LABELS = {
    "english": "英語", "japanese": "日語", "chinese": "中文", "other": "其他語言",
    "french": "法語", "german": "德語", "spanish": "西班牙語",
}
_REQUIREMENT_SIGNALS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("english", re.compile(r"IELTS|TOEFL|TOEIC|多益|雅思|托福|Duolingo|英文|英語|English|CEFR\s*B[12]", re.I)),
    ("japanese", re.compile(r"JLPT|日本語|日語|日文能力|N[1-5]\b")),
    ("chinese", re.compile(r"HSK|華語|漢語|中文能力|Chinese proficiency", re.I)),
    ("french", re.compile(r"DELF|DALF|TCF|TEF|法語|法文|French", re.I)),
    ("german", re.compile(r"TestDaF|Goethe|DSH|德語|德文|German", re.I)),
    ("spanish", re.compile(r"DELE|西班牙語|西語|西班牙文|Spanish", re.I)),
)


def school_budget_fit(
    destination: DestinationProfile | None, monthly_budget_twd: float | None
) -> BudgetFit | None:
    """Compare the sourced monthly living cost with the student's budget."""

    if not monthly_budget_twd:
        return None
    if destination is None or not destination.cost_summary:
        return BudgetFit(status="unknown", reason="尚未取得這所學校的費用資料，無法比對預算。")
    result = budget_fit(extract_monthly_estimates(destination), monthly_budget_twd)
    fx_note = None
    if result.get("low_twd") is not None:
        reference = fx_reference()
        fx_note = (
            f"以 {str(reference.get('provider_updated_at', ''))[:16] or '近期'} 的參考匯率概估，"
            "不是銀行即時牌價；實際匯率與費用以校方及你的支付方式為準。"
        )
    return BudgetFit(**result, fx_note=fx_note)


def teaching_language_fit(
    partner: PartnerUniversity, preferred: str | None
) -> TeachingLanguageFit | None:
    track_text = " ".join([partner.program_type, *(row.program_type for row in partner.program_options)])
    tracks = [code for label, code in _TRACKS.items() if label in track_text]
    if tracks:
        names = "、".join(_LABELS[code] for code in tracks)
        if preferred is None:
            return TeachingLanguageFit(
                status="unknown", languages=_labels(tracks), basis="partner_track",
                detail=f"本校名額表把這所學校列在{names}組；未設定偏好授課語言。",
            )
        if preferred in tracks:
            return TeachingLanguageFit(
                status="listed", languages=_labels(tracks), basis="partner_track",
                detail=f"本校名額表把這所學校列在{names}組，與你的偏好相符；實際開課語言仍以合作校課程為準。",
            )
        return TeachingLanguageFit(
            status="not_listed", languages=_labels(tracks), basis="partner_track",
            detail=f"本校名額表把這所學校列在{names}組，不在你偏好的授課語言。",
        )
    text = " ".join(
        value for value in (partner.eligibility, partner.application_info, *partner.student_summary_zh.eligibility_points)
        if value
    )
    found = [code for code, pattern in _REQUIREMENT_SIGNALS if pattern.search(text)]
    if not found:
        return None
    names = "、".join(_LABELS[code] for code in found)
    if preferred is None:
        return TeachingLanguageFit(
            status="unknown", languages=_labels(found), basis="requirement_text",
            detail=f"公開資格說明提到{names}能力要求；這不等於授課語言，請向合作校確認。",
        )
    if preferred in found:
        return TeachingLanguageFit(
            status="listed", languages=_labels(found), basis="requirement_text",
            detail=f"公開資格說明提到{_LABELS[preferred]}能力要求；這不等於授課語言，請向合作校確認可修的英語／該語言課程。",
        )
    return TeachingLanguageFit(
        status="not_listed", languages=_labels(found), basis="requirement_text",
        detail=f"公開資格說明只提到{names}能力要求，沒有看到{_LABELS.get(preferred, '你偏好的語言')}；授課語言仍請向合作校確認。",
    )


def _labels(codes: list[str]) -> list[str]:
    return [_LABELS.get(code, code) for code in codes]


def course_interest_fit(
    partner: PartnerUniversity, destination: DestinationProfile | None, interests: str | None
) -> CourseInterestFit | None:
    terms = [
        term for term in dict.fromkeys(re.split(r"[,，、;；/\s]+", (interests or "").strip()))
        if len(term) >= 2
    ][:6]
    if not terms:
        return None
    pool = [
        partner.colleges, partner.eligibility, partner.application_info,
        *(row.colleges for row in partner.program_options),
        *(row.eligibility for row in partner.program_options),
        *partner.student_summary_zh.eligibility_points,
    ]
    if destination is not None:
        for section in destination.student_guide_sections:
            if section.key == "courses_and_workload":
                pool.extend([section.summary, *section.points])
    matched: list[str] = []
    evidence: list[str] = []
    for term in terms:
        for text in pool:
            if not text:
                continue
            position = text.casefold().find(term.casefold())
            if position >= 0:
                matched.append(term)
                evidence.append(text[max(0, position - 20): position + len(term) + 40].strip())
                break
    if matched:
        return CourseInterestFit(
            status="mentioned", matched_terms=matched, evidence=evidence[:3],
            detail="公開資料有提到你填的領域；這不代表該學期有開課、可跨系選修或能抵免，仍須查合作校課程目錄與系所核可。",
        )
    return CourseInterestFit(
        status="unknown",
        detail="公開資料沒有逐校課程目錄可比對你填的領域；請查合作校官網的課程目錄與交換生選課限制。",
    )
