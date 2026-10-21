from __future__ import annotations

import re

from .university_registry import PCCU, resolve_university

PCCU_OIMA_HUB_URL = "https://oima.pccu.edu.tw/exchanges.htm"
PCCU_OUTBOUND_GUIDE_URL = "https://oima.pccu.edu.tw/study-abroad-detail5.htm"
PCCU_OUTBOUND_GUIDELINES_PDF_URL = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283508.pdf"
PCCU_OUTBOUND_FAQ_PDF_URL = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283509.pdf"
PCCU_OIMA_QUOTA_LIST_PDF_URL = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283510.pdf"
PCCU_SISTER_MASTER_LIST_PDF_URL = "https://oima.pccu.edu.tw/Upload/202609/exchange_2026090314332408.pdf"
PCCU_MOBILITY_SCHOLARSHIP_PDF_URL = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071522332308.pdf"
PCCU_SHORT_TERM_GRANT_PDF_URL = "https://oima.pccu.edu.tw/Upload/202608/exchange_2026082710142908.pdf"
PCCU_JP_ANNOUNCEMENT_URL = "https://japanese.pccu.edu.tw/p/406-1109-140489,r278.php?Lang=zh-tw"
PCCU_KR_SOP_URL = "https://kor.pccu.edu.tw/p/405-1112-72586,c1202.php?Lang=zh-tw"
PCCU_KR_EXP_HUB_URL = "https://kor.pccu.edu.tw/p/412-1112-10453.php?Lang=zh-tw"
PCCU_FR_EXCHANGE_URL = "https://french.pccu.edu.tw/p/412-1115-7823.php"
PCCU_RU_EXCHANGE_URL = "https://crgarl.pccu.edu.tw/p/16-1113-110334.php?Lang=zh-tw"

PCCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_pccu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == PCCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "中國文化大學",
        "文化大學",
        "文化",
        "文大",
        "pccu",
        "chinese culture university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def pccu_degree_check(
    degree_level: str | None, current_year: str | None = None, *,
    program_type: str | None = None, partner_country: str | None = None,
) -> tuple[str, str]:
    from .pccu_source_review import DEGREE, route
    degree = degree_level or ""
    year = current_year or ""
    kind = route(program_type, partner_country)
    if kind == "mainland":
        detail = "赴陸須在文大完成至少一學期，不能一律排除大一；仍須確認已完成學期及在學身分。"
    elif kind == "kr":
        detail = "韓文系研究生須在文大修滿20學分；需確認前一學期系上修課及學業成績。"
    elif kind == "jp":
        detail = "日文系碩士及轉學生須在出發前於文大就讀滿一年，不能套國合組滿一學期規定。"
    else:
        detail = DEGREE
    if program_type and kind == "oima" and not _is_graduate(degree) and "轉" not in degree and year in {"大一", "一年級", "1"}:
        return "fail", "國合組一般學士申請須在文大完成一年；轉學生另依完成一學期規定。"
    return "needs_confirmation", detail


def pccu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
    *, program_type: str | None = None, partner_country: str | None = None,
) -> tuple[str, str]:
    from .pccu_source_review import ACADEMIC
    # The request fields do not establish which semester a reported score covers.
    # Do not substitute an award threshold or an unrelated host's GPA requirement.
    return "needs_confirmation", ACADEMIC + "目前填報成績未確認適用學期、系上修課及個別目標校條件，不能自動判定通過或不符。"


def pccu_language_check(
    language_test: str | None, language_score: float | None, *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    from .pccu_source_review import LANGUAGE
    return "needs_confirmation", LANGUAGE
