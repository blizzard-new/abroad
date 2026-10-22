from __future__ import annotations

import re

from .university_registry import YZU, resolve_university
from .yzu_source_review import ACADEMIC, DEGREE, LANGUAGE, GENERAL, MAINLAND, NOTICE, MANAGEMENT

YZU_OUTBOUND_URL = GENERAL
YZU_APPLY_PORTAL_URL = NOTICE
YZU_QUOTALIST_URL = NOTICE
YZU_CM_OIP_URL = MANAGEMENT
YZU_MAINLAND_URL = MAINLAND
YZU_REGULATION_URL = GENERAL
YZU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_yzu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == YZU.id:
        return True
    return re.sub(r"\s+", " ", (school_name or "")).strip().lower() in {
        "元智大學", "元智", "yzu", "yuan ze university",
    }


def yzu_degree_check(degree_level: str | None, current_year: str | None = None,
                     *, partner_country: str | None = None, program_type: str | None = None) -> tuple[str, str]:
    degree, year = (degree_level or "").strip(), (current_year or "").strip()
    if not degree or not year or any(s in degree for s in ("在職", "進修", "推廣", "EMBA")):
        return "needs_confirmation", "尚需確認學制、已修業期間與申請管道；" + DEGREE
    grad = any(s in degree for s in ("碩", "博", "研究"))
    if partner_country in {"中國大陸", "大陸地區"} and grad:
        return "needs_confirmation", "赴陸頁寫二年級以上學位生，與國際組研究生條件不同，不能自動套用。" + DEGREE
    if grad and year in {"碩一上", "博一上"}:
        return "fail", "校級簡報要求研究生就讀滿一學期；第一學期尚未完成者不符。"
    if grad and year in {"碩一", "博一", "一年級"}:
        return "needs_confirmation", "僅填一年級不足以判斷是否已完成至少一學期。" + DEGREE
    if not grad and year in {"大一", "一年級"}:
        return "fail", "校級當期簡報要求學士班二年級以上；其他管道須另核。"
    if "管理學院" in (program_type or ""):
        return "needs_confirmation", "管院須核對本院一般生與指定學制年級；" + DEGREE
    if not ((grad and re.search(r"[碩博][二三四五六]|[碩博]一下", year)) or
            (not grad and re.search(r"大[二三四五六]|[二三四五六]年級", year))):
        return "needs_confirmation", "年級與已修業期間尚待確認；" + DEGREE
    return "pass", "填報年級在校級基本範圍內，仍須持續在學並核對個別方案條件。" + DEGREE


def yzu_academic_check(degree_level: str | None, academic_score: float | None,
                       academic_gpa: float | None = None, class_rank_percent: float | None = None,
                       *, program_type: str | None = None) -> tuple[str, str]:
    program = program_type or ""
    if "管理學院" in program and "校級" not in program:
        if academic_gpa is not None and academic_gpa >= 3.0:
            return "pass", "填報GPA符合管院原則3.0的母校學業項目；接待校門檻與當期適用仍須核對。"
        return "needs_confirmation", "管院以歷年平均GPA3.0以上為原則，平均分數或班排不能替代；例外及當期資格由管院確認。"
    return "needs_confirmation", ACADEMIC + " 輸入成績不能單獨證明符合個別接待校及申請管道。"


def yzu_language_check(language_test: str | None, language_score: float | None,
                       *, partner_country: str | None = None) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return "pass", "母校赴陸志願表明列免附英檢，此判斷只涵蓋母校文件；接待校及授課語言要求仍須逐校確認。"
    return "needs_confirmation", LANGUAGE
