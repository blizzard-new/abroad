from __future__ import annotations

import re

from .university_registry import CYCU, resolve_university

CYCU_OUTBOUND_URL = "https://oia.cycu.edu.tw/?page_id=2956&lang=zh"
CYCU_APPLY_PORTAL_URL = "https://oia.cycu.edu.tw/?page_id=2968&lang=zh"
CYCU_QUOTALIST_URL = "https://oia.cycu.edu.tw/?page_id=10128&lang=zh"
CYCU_MAINLAND_URL = "https://oia.cycu.edu.tw/?p=6340&lang=zh"
CYCU_REGULATION_URL = "https://oia.cycu.edu.tw/wp-content/uploads/sites/2/2025/09/%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E9%81%B8%E9%80%81%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95.pdf"

CYCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS Academic", 5.5),
    "toeic": ("TOEIC", 600.0),
}


def is_cycu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == CYCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "中原大學",
        "中原",
        "cycu",
        "chung yuan christian university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def cycu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；中原大學規定申請人須為本校在學學生（不含休學生及在職專班學生），且申請時須於本校修業滿二學期以上（轉學生須於本校就讀滿一學年以上；五專轉學生須於本校就讀滿一學期以上）。",
        )
    if any(token in degree for token in ("在職", "進修", "推廣")):
        return (
            "fail",
            f"已填報 {degree}。中原大學《選送學生出國研習實施辦法》規定申請對象不含在職專班及休學學生。",
        )
    if any(token in year for token in ("大一", "碩一上", "博一上", "一年級")):
        return (
            "fail",
            f"已填報 {degree}（{year}）。中原大學規定申請時須於本校修業滿二學期以上（一年級新生尚不得報名；轉學生須於本校就讀滿一學年以上）。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合中原大學正式學籍在學學生申請範圍（請確認申請時已於本校修業滿二學期以上，且出國期間維持在學註冊繳費）。",
    )


def cycu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if academic_score is None and academic_gpa is None and class_rank_percent is None:
        return (
            "needs_confirmation",
            "尚未填寫歷年學業成績（GPA / 平均分數）或系所排名；中原大學規定歷年學業總平均須達 GPA 3.0 以上或班級排名前 30%（建築學系為歷年排名前 50% 且建築設計一～六均及格），並須符合各姊妹校個別 GPA 規定。",
        )

    details: list[str] = []
    gpa_ok = False
    score_ok = False
    rank_ok = False

    if academic_score is not None:
        details.append(f"歷年平均 {academic_score:g} 分")
        if academic_score >= 75.0:
            score_ok = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= 3.0:
            gpa_ok = True
    if class_rank_percent is not None:
        details.append(f"班級排名前 {class_rank_percent:g}%")
        if class_rank_percent <= 30.0:
            rank_ok = True

    summary = "、".join(details)
    passed = gpa_ok or score_ok or rank_ok
    if not passed:
        return (
            "fail",
            f"已填報 {summary}，未達中原大學校內門檻（歷年 GPA 3.0 / 平均 75 分以上或班級排名前 30%；建築學系為前 50%）。請確認歷年成績單與目標姊妹校個別 GPA 規定。",
        )
    return (
        "pass",
        f"已填報 {summary}；符合中原大學歷年 GPA 3.0（平均 75 分）以上或班級排名前 30% 之學業門檻，請同時核對《中原大學出國交換研修申請學校一覽表》各校個別 GPA 要求。",
    )


def cycu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請中原大學赴大陸地區（含北京清華、南開、武漢、西安交大、哈工大等 28 校）交換生計畫免附外語檢定證明；惟須符合歷年成績及格及目標學校學科規定。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。中原大學規定申請國際及香港姊妹校須檢附兩年內有效之外語能力檢定證明（英語組常見門檻為 TOEFL iBT 61–80、IELTS 5.5–6.5 或 TOEIC 600–785；日韓語組依各校規定 JLPT N1–N3 或 TOPIK 2–4 級）。",
        )
    if test in CYCU_ENGLISH_MINIMUMS:
        label, minimum = CYCU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        warning = (
            "重要提醒：歐美及香港姊妹校多數要求 TOEFL iBT 79–90 或 IELTS Academic 6.0–6.5（部分不採認 TOEIC 或校園考成績），請務必對照《出國交換研修申請學校一覽表》與各校 Fact Sheet 規定。"
        )
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}中原大學英語組常見基準門檻 {minimum:g}。{warning}",
        )
    if test == "jlpt":
        passed = 1.0 <= language_score <= 4.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}中原大學日本姊妹校常見門檻範圍（N1–N4；同志社、立命館、早稻田、中央大學等重點校多要求 N2 或 N1，請對照一覽表各校規定）。",
        )
    if test == "topik":
        passed = 2.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}中原大學韓國姊妹校常見門檻範圍（TOPIK 2–6 級或修畢韓語課程，請對照一覽表各校規定）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請核對中原大學《出國交換研修申請學校一覽表》與目標學校 Fact Sheet 之語言檢定級數要求。",
    )
