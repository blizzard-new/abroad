from __future__ import annotations

import re

from .university_registry import FCU, resolve_university

FCU_OUTBOUND_URL = "https://oia.fcu.edu.tw/sap/introduction/"
FCU_APPLY_PORTAL_URL = "https://oiasap.fcu.edu.tw/"
FCU_QUOTALIST_URL = "https://oiasap.fcu.edu.tw/"
FCU_COLLABORATION_URL = "https://oia.fcu.edu.tw/collaboration/"
FCU_SCHOLARSHIP_URL = "https://oia.fcu.edu.tw/sap/scholarship/"
FCU_DUALDEGREE_URL = "https://oia.fcu.edu.tw/sap/dualdegree/"

# Language thresholds are specific to the host program, not a shared floor.
FCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_fcu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == FCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "逢甲大學",
        "私立逢甲大學",
        "逢甲",
        "fcu",
        "feng chia university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def fcu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return "needs_confirmation", "須確認學制、在學狀態及是否已完成一學期；研究生不受入學一學期限制。"
    if any(token in degree for token in ("在職", "EMBA")):
        return "needs_confirmation", "115-1交換簡章未列在職專班一律不得申請；不可將獎助資格限制代替交換資格，須確認所屬計畫及系所條件。"
    if any(token in year for token in ("延修", "延畢")):
        return "needs_confirmation", "原則不得為延修生，但將出國研修列為畢業條件之特定系所／學程有例外，須確認適用條件。"
    if not _is_graduate(degree):
        if any(token in year for token in ("大一上", "新生", "未滿一學期")):
            return "fail", "學士班入學或復學未滿一學期不得申請；研究生不受此限制。"
        if not year or year in {"大一", "一年級"}:
            return "needs_confirmation", "須確認入學或復學已完成一學期；僅有學制或一年級資料不足以判定。"
    return "pass", "符合已填報學制／年級範圍；申請及出國研修期間仍須註冊在學，並符合系所及接待校條件。"


def fcu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if academic_gpa is None:
        return "needs_confirmation", "115-1簡章要求在校歷年總平均GPA 3.0以上。百分制分數及排名不能直接代替GPA，請提供成績單所列GPA；全學年互免交換另有排名前50%及適用條件。"
    if academic_gpa < 3.0:
        return "fail", f"已填報GPA {academic_gpa:g}，未達115-1簡章的歷年GPA 3.0門檻；平均分數或排名不能替代此門檻。"
    return "pass", f"已填報GPA {academic_gpa:g}，符合115-1簡章的歷年GPA 3.0門檻；全學年互免須另確認排名前50%與適用資格，各接待校要求另核。"


def fcu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    return "needs_confirmation", "115-1簡章要求符合所申請學校的有效外語檢定；沒有全校共同的TOEFL 61、IELTS 5.5或TOEIC 550門檻。須依合作方案核對考試種類、成績及效期，不能僅由國家或常見分數判定通過。"
