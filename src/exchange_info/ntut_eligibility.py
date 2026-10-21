from __future__ import annotations

import re

from .university_registry import NTUT, resolve_university

NTUT_OUTBOUND_URL = "https://oia.ntut.edu.tw/p/412-1032-9312.php?Lang=zh-tw"
NTUT_GUIDELINES_PDF_URL = (
    "https://oia.ntut.edu.tw/p/412-1032-9409-1.php"
)
NTUT_APPLY_PORTAL_URL = (
    "https://oia.ntut.edu.tw/p/412-1032-9238.php?Lang=zh-tw"
)
NTUT_PARTNERS_URL = "https://oia.ntut.edu.tw/p/412-1032-9243.php?Lang=zh-tw"
NTUT_MATCHING_PDF_URL = (
    "https://oia.ntut.edu.tw/var/file/32/1032/img/201490897.pdf"
)
NTUT_MAINLAND_PARTNERS_URL = (
    "https://oia.ntut.edu.tw/p/412-1032-10190.php?Lang=zh-tw"
)
NTUT_DUAL_DEGREE_URL = "https://oia.ntut.edu.tw/p/412-1032-10643.php?Lang=zh-tw"
NTUT_EXPERIENCE_URL = "https://oia.ntut.edu.tw/p/412-1032-14379.php?Lang=zh-tw"
NTUT_MAINLAND_EXPERIENCE_URL = (
    "https://oia.ntut.edu.tw/p/412-1032-10191.php?Lang=zh-tw"
)
NTUT_SCHOLARSHIP_URL = "https://oia.ntut.edu.tw/p/412-1032-9313.php?Lang=zh-tw"
NTUT_SCHOLARSHIP_REGULATIONS_PDF_URL = (
    "https://oia.ntut.edu.tw/var/file/32/1032/img/869917322.pdf"
)

# No common exchange language score is established by the reviewed source.
NTUT_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}

def is_ntut(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTUT.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺北科技大學",
        "國立台北科技大學",
        "臺北科技大學",
        "台北科技大學",
        "臺北科大",
        "台北科大",
        "北科大",
        "北科",
        "ntut",
        "taipei tech",
        "national taipei university of technology",
    }



def ntut_degree_check(degree_level: str | None, current_year: str | None = None,
                      *, partner_country: str | None = None, program_type: str | None = None) -> tuple[str, str]:
    from .ntut_source_review import DEGREE
    if "雙聯" in (program_type or ""):
        return "needs_confirmation", "雙聯或同列交換／雙聯方案須選定計畫後核對學制。"
    degree = degree_level or ""
    year = current_year or ""
    if not degree or not year or "五專" in degree or "在職" in degree:
        return "needs_confirmation", DEGREE
    if partner_country in {"中國大陸", "大陸地區"}:
        return "needs_confirmation", "赴陸六校須大二以上或研究生，且有北科一學年成績；年級本身不足以確認完整北科修業紀錄。"
    if year in {"一年級", "大一", "碩一", "博一", "1"} or "一上" in year or "一下" in year:
        return "needs_confirmation", "新生及直升研究所須已在北科完成一學期；目前年級未能確認完成的學期。"
    if any(t in degree for t in ("學士", "大學", "碩", "博", "研究")) and (any(t in year for t in ("二", "三", "四", "五", "2", "3", "4", "5", "延畢"))):
        return "pass", "填報年級符合一般校級交換修業階段；仍須已在北科完成一學期，轉學生另確認，且出國期間維持在學。接待校及個別計畫另核。"
    return "needs_confirmation", DEGREE


def ntut_academic_check(degree_level: str | None, academic_score: float | None,
                        academic_gpa: float | None = None, class_rank_percent: float | None = None,
                        *, program_type: str | None = None) -> tuple[str, str]:
    from .ntut_source_review import ACADEMIC
    if "雙聯" in (program_type or ""):
        return "needs_confirmation", "雙聯學位成績須依個別計畫核對，不能套校級交換或學海獎助門檻。"
    return "pass", ACADEMIC + "此結果僅指母校一般交換成績項，不代表符合接待校或獎學金。"


def ntut_language_check(language_test: str | None, language_score: float | None,
                       *, partner_country: str | None = None) -> tuple[str, str]:
    from .ntut_source_review import LANGUAGE
    return "needs_confirmation", LANGUAGE
