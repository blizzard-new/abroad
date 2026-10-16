from __future__ import annotations

import re

from .university_registry import SCU, resolve_university

SCU_APPLY_URL = "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply"
SCU_CHINA_APPLY_URL = "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply"
SCU_REVIEW_CRITERIA_URL = "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/requirements"
SCU_REGULATION_URL = "https://icae.scu.edu.tw/sites/default/files/2025-09/06_%E6%9D%B1%E5%90%B3%E5%A4%A7%E5%AD%B8%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E8%A8%88%E7%95%AB%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95_0.pdf"

SCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 60.0),
    "ielts": ("IELTS Academic", 5.5),
    "toeic": ("TOEIC", 650.0),
}


def is_scu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == SCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "東吳大學",
        "私立東吳大學",
        "東吳",
        "scu",
        "soochow university",
        "soochow university (taiwan)",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def scu_undergraduate_weighted_academic_score(
    academic_score: float, class_rank_percent: float
) -> float:
    """Return SCU's official undergraduate review academic score:
    歷年平均成績 × 45% + (1 - 累計班排名百分比) × 100 × 55%.
    """
    rank_ratio = max(0.0, min(1.0, class_rank_percent / 100.0))
    return round(academic_score * 0.45 + (1.0 - rank_ratio) * 100.0 * 0.55, 2)


def scu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；東吳規定申請及交換期間均應具正式在學學籍（不得為休學或大學部延修第二年；赴陸交換及澳門城市大學不開放進修學士班、碩士在職專班等非全日制學生）。",
        )
    if "延修第二年" in year or "延二" in year or "大六" in year:
        return (
            "fail",
            f"已填報 {degree}（{year}）。東吳規定交換期間不得為休學或大學部延修第二年。",
        )
    if "在職" in degree or "進修" in degree:
        return (
            "needs_confirmation",
            f"已填報 {degree}。提醒：赴大陸交換及澳門城市大學不開放非全日制學生（進修學士班、碩士在職專班）申請，僅可申請部分開放之海外協議校。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合東吳大學正式在學學籍範圍（操行成績須達 80 分以上且無校規懲處紀錄）。",
    )


def scu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if _is_graduate(degree_level):
        if academic_score is None:
            return (
                "needs_confirmation",
                "尚未填寫研究所歷年成績總平均；東吳規定碩博班學生入學後成績總平均須達 80 分（含）以上，且操行成績須達 80 分以上。",
            )
        passed = academic_score >= 80.0
        return (
            "pass" if passed else "fail",
            f"碩博班入學後歷年總平均 {academic_score:g} 分，{'符合' if passed else '未達'}東吳碩博班 80 分以上門檻（另須確認操行達 80 分以上）。",
        )

    if class_rank_percent is not None:
        passed = 0 < class_rank_percent <= 85.0
        weighted_note = ""
        if academic_score is not None:
            weighted = scu_undergraduate_weighted_academic_score(academic_score, class_rank_percent)
            weighted_note = f"（依東吳學業採計公式換算為 {weighted:g} 分）"
        return (
            "pass" if passed else "fail",
            f"大學部累計班排名為前 {class_rank_percent:g}%{weighted_note}，{'符合' if passed else '未達'}東吳大學部累計班排名前 85% 以內門檻（另須確認操行達 80 分以上及各協議校個別 GPA 規定）。",
        )

    if academic_score is None:
        return (
            "needs_confirmation",
            "尚未填寫累計班排名百分比或歷年平均成績；東吳大學部須達累計班排名前 85% 以內、碩博班須達總平均 80 分以上，且操行須達 80 分以上。",
        )

    passed = academic_score >= 65.0
    return (
        "pass" if passed else "needs_confirmation",
        f"歷年學業總平均 {academic_score:g} 分；東吳大學部主要以「累計班排名前 85% 以內」為審查門檻（公式：歷年平均×45%＋(1－累計班排名百分比)×100×55%），請一併確認累計班排名百分比與操行成績（80 分以上）。",
    )


def scu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請東吳校級赴大陸地區協議學校交換免附外語檢定證明。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。申請赴外（含港澳）交換須至少符合目標協議校於《116學年度校級赴外交換學校一覽表》所列任一語檢門檻（英歐語須為 2025/01/31 後核發、JLPT 須為 2024/01/31 後核發，不接受多益校園考）。",
        )
    if test in SCU_ENGLISH_MINIMUMS:
        label, minimum = SCU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        warning = (
            "重要提醒：東吳不接受多益校園考（Institutional TOEIC）成績，且歐美及多數協議校僅採認 TOEFL iBT 或 IELTS Academic，請務必對照目標學校一覽表規定。"
            if test == "toeic"
            else "各協議校若有更高分數或單科門檻（如 TOEFL iBT 79–100、IELTS Academic 6.0–7.0），須依一覽表各校規定辦理。"
        )
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}東吳赴外交換英語基準門檻 {minimum:g}。{warning}",
        )
    if test == "jlpt":
        passed = 1.0 <= language_score <= 4.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}東吳日語組協議校基準範圍（N1–N4，須為 2024/01/31 後核發；各校 N1/N2/N3 個別規定請對照一覽表）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請核對《116學年度校級赴外交換學校一覽表》目標學校之語檢級數要求及發證年限（JLPT 須為 2024/01/31 後核發）。",
    )
