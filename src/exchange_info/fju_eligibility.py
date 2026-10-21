from __future__ import annotations

import math
import re

from .university_registry import FJU, resolve_university

FJU_PROCESS_URL = "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39"
FJU_LANG_SCORE_URL = "https://iscoie.fju.edu.tw/DownloadNewsFileServlet?file=1344"
FJU_REGULATION_URL = "https://iscoie.fju.edu.tw/teachingServices.jsp?file=910"

FJU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 79.0),
    "toefl_new": ("TOEFL iBT（新制6分制）", 4.0),
    "ielts": ("IELTS", 6.5),
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


def fju_internal_language_score_range(test: str, score: float) -> tuple[float, float] | None:
    """116-1 briefing p.17; ranges do not imply an unpublished interpolation rule."""
    if not math.isfinite(score):
        return None
    key = test.strip().lower()
    if key in {"ielts", "toefl_new"}:
        scores = {"ielts": (5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5),
                  "toefl_new": (3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0)}[key]
        if score in scores:
            points = float(40 + scores.index(score) * 10)
            return points, points
        return None
    bands = {
        "toefl": ((46, 59, 40, 49), (60, 78, 50, 59), (79, 93, 60, 69),
                  (94, 101, 70, 79), (102, 109, 80, 89), (110, 114, 90, 99), (115, 120, 100, 100)),
        "toeic": ((550, 665, 40, 49), (670, 780, 50, 59), (785, 865, 60, 69),
                  (870, 940, 70, 79), (945, 990, 80, 89)),
    }
    for low, high, points_low, points_high in bands.get(key, ()):
        if low <= score <= high and score == int(score):
            return float(points_low), float(points_high)
    return None


def fju_internal_language_points(test: str, score: float) -> float | None:
    """Return an exact point value only when p.17 actually specifies one."""
    interval = fju_internal_language_score_range(test, score)
    return interval[0] if interval and interval[0] == interval[1] else None


def fju_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；116-1簡報要求校內申請時大學部大二以上或碩、博士班一年級以上。",
        )
    if not _is_graduate(degree) and year in {"大一", "一年級", "1"}:
        return "fail", "116-1簡報要求校內申請時已為大二以上；目前大一不符合這項年級條件。"
    if not _is_graduate(degree) and year in {"大四", "四年級", "4", "大五", "五年級", "5", "應屆畢業生"}:
        return (
            "needs_confirmation",
            f"已填報 {degree}（{year}）。應屆畢業生限交換期間尚有雙主修、輔系或學分學程學分未修畢，並須確認接待校接受年級及在學資格。",
        )
    if not year or not (_is_graduate(degree) or degree in {"大學部", "學士班", "學士", "進修學士班"}):
        return "needs_confirmation", "目前學制或年級不足以確認116-1申請條件；須核對申請時年級、學籍及接待校要求。"
    if not _is_graduate(degree) and year not in {"大二", "二年級", "2", "大三", "三年級", "3"}:
        return "needs_confirmation", "尚未確認申請時年級及延畢適用情形，請向母校承辦核對。"
    if _is_graduate(degree) and not re.fullmatch(r"(?:碩|博|研)?(?:[一二三四五六七八九十]|[1-9][0-9]*)(?:年級)?", year):
        return "needs_confirmation", "目前研究所年級無法確認；須核對申請時為碩、博士班一年級以上及在學資格。"
    return (
        "pass",
        f"已填報學制為 {degree}（{year}），符合申請時學制年級範圍；115-2及交換期間學籍、轉學生在校已讀滿一學期、其他資格仍須分別確認。",
    )


def fju_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if _is_graduate(degree_level):
        return (
            "needs_confirmation",
            "116-1公告的70分學業門檻明列適用學士班；研究生須另向國際學生中心確認，並符合接待校規定。",
        )
    if academic_score is None:
        return (
            "needs_confirmation",
            "尚未填寫歷年學業成績總平均；輔大116-1公告要求學士班歷年平均70分以上，未列班排名替代條件。",
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
            "尚未填寫語言檢定成績。輔大116-1英語授課校申請門檻為 TOEFL iBT 79、IELTS 6.5 或 TOEIC 750 擇一；其他授課語言及接待校較高門檻須分別核對。",
        )
    if test == "toefl" and 1 <= language_score <= 6:
        return "needs_confirmation", "請確認TOEFL iBT成績量尺：116-1母校門檻為舊制79或新制4.0；目前未指定量尺，不能直接判為通過或不通過。"
    if test in FJU_ENGLISH_MINIMUMS:
        maximum = {"toefl": 120, "toefl_new": 6, "ielts": 9, "toeic": 990}[test]
        if not math.isfinite(language_score) or not 0 <= language_score <= maximum:
            return "needs_confirmation", "填寫的語言成績超出所選量尺或無法辨識；請核對正式成績單後重新填寫。"
        label, minimum = FJU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        interval = fju_internal_language_score_range(test, language_score)
        pts_note = ""
        if interval:
            low, high = interval
            pts_note = (f"（116-1簡報第17頁校內評分為 {low:g} 分）" if low == high else
                        f"（116-1簡報第17頁校內評分範圍 {low:g}–{high:g} 分；表內未載區間內換算方法，不能推定精確分數）")
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
        f"已填寫 {language_test} {language_score:g}；請核對輔大116-1簡報第13、17–19頁及目標姊妹校語檢標準。",
    )
