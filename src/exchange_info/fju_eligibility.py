from __future__ import annotations

import re

from .university_registry import FJU, resolve_university

FJU_PROCESS_URL = "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39"
FJU_LANG_SCORE_URL = "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=44"
FJU_REGULATION_URL = "https://iscoie.fju.edu.tw/teachingServices.jsp?file=910"

FJU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 79.0),
    "ielts": ("IELTS", 6.0),
    "toeic": ("TOEIC", 750.0),
}


def is_fju(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == FJU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "天主教輔仁大學",
        "輔仁大學",
        "輔大",
        "fju",
        "fu jen catholic university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def fju_internal_language_points(test: str, score: float) -> float | None:
    """Return FJU's internal language evaluation score (40-100 scale) from labelID=44."""
    key = test.strip().lower()
    if key == "toefl":
        if score >= 93:
            return 100.0
        if score >= 88:
            return 90.0
        if score >= 83:
            return 80.0
        if score >= 79:
            return 70.0
        if score >= 74:
            return 60.0
        if score >= 68:
            return 50.0
        if score >= 61:
            return 40.0
        return None
    if key == "ielts":
        if score >= 7.0:
            return 100.0
        if score >= 6.5:
            return 90.0
        if score >= 6.0:
            return 70.0
        if score >= 5.5:
            return 50.0
        if score >= 5.0:
            return 40.0
        return None
    if key == "toeic":
        if score >= 900:
            return 100.0
        if score >= 855:
            return 90.0
        if score >= 820:
            return 80.0
        if score >= 785:
            return 70.0
        if score >= 750:
            return 60.0
        if score >= 700:
            return 50.0
        if score >= 650:
            return 40.0
        return None
    return None


def fju_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；輔大規定須為在學學士班（含進修部）出國時大二以上，或碩、博士班在學學生。",
        )
    if not _is_graduate(degree) and year in {"大四", "四年級", "4", "應屆畢業生"}:
        return (
            "needs_confirmation",
            f"已填報 {degree}（{year}）。應屆畢業生須符合延畢規定並核對各姊妹校是否接受大四生交換。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合輔大在學學士班（出國時須大二以上）或碩博士班之學制範圍。",
    )


def fju_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if class_rank_percent is not None and 0 < class_rank_percent <= 50.0:
        return (
            "pass",
            f"歷年系排名百分比前 {class_rank_percent:g}%，符合輔大校內歷年學業成績系排名前 50% 以內門檻（另須確認各姊妹校個別 GPA 門檻）。",
        )
    if academic_score is None:
        return (
            "needs_confirmation",
            "尚未填寫歷年學業成績總平均；輔大校級交換門檻為歷年學業總平均達 70 分以上或系排名前 50% 以內。",
        )
    passed = academic_score >= 70.0
    return (
        "pass" if passed else "fail",
        f"歷年學業成績總平均 {academic_score:g} 分，{'符合' if passed else '未達'}輔大校內總平均 70 分以上門檻（另須核對各姊妹校個別 GPA 規定）。",
    )


def fju_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區", "澳門"}:
        return (
            "pass",
            "申請大陸及澳門地區中文授課姊妹校（中語組）免附外語檢定；若選修全英語學程仍須依接待校規定提供英檢證明。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫語言檢定成績。輔大外語組英語門檻為 TOEFL iBT 79 或 IELTS 6.0（校內換分另含 TOEIC 750+）；日、韓、歐語組須符合各姊妹校語檢標準。",
        )
    if test in FJU_ENGLISH_MINIMUMS:
        label, minimum = FJU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        internal_pts = fju_internal_language_points(test, language_score)
        pts_note = f"（對應輔大校內外語能力換分表 {internal_pts:g} 分）" if internal_pts is not None else ""
        toeic_warning = (
            "提醒：多數歐美姊妹校僅接受 TOEFL iBT 或 IELTS Academic，除非該校明列接受 TOEIC，選填前務必逐校核對。"
            if test == "toeic"
            else "各姊妹校標準較高或有單科門檻者從其規定。"
        )
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}輔大外語組參考門檻 {minimum:g}{pts_note}。{toeic_warning}",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請核對輔大外語能力換分表（labelID=44）及目標姊妹校語檢標準。",
    )
