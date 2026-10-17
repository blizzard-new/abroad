from __future__ import annotations

import re

from .university_registry import YZU, resolve_university

YZU_OUTBOUND_URL = "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-51-28"
YZU_APPLY_PORTAL_URL = "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00"
YZU_QUOTALIST_URL = "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00"
YZU_CM_OIP_URL = "https://oip.cm.yzu.edu.tw/abrd_deg/list/es"
YZU_MAINLAND_URL = "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37"
YZU_REGULATION_URL = "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07"

YZU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS Academic", 5.5),
    "toeic": ("TOEIC", 650.0),
}


def is_yzu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == YZU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "元智大學",
        "元智",
        "yzu",
        "yuan ze university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def yzu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；元智大學規定申請人須為本校正式學籍在學之學士班二年級（含）以上學生，或於本校就讀滿一學期以上之碩博士班研究生（不含在職專班及休學學生）。",
        )
    if any(token in degree for token in ("在職", "進修", "推廣")):
        return (
            "fail",
            f"已填報 {degree}。元智大學出國交換甄選規定申請對象不含在職專班及休學學生。",
        )
    if any(token in year for token in ("大一", "碩一上", "博一上", "一年級")):
        return (
            "fail",
            f"已填報 {degree}（{year}）。元智大學規定學士班須為二年級（含）以上、研究生須於元智就讀滿一學期以上始得申請。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合元智大學正式學籍在學學生申請範圍（錄取確認時須繳交保證金 NT$5,000，且交換期間每學期至少須修習 4 門課或 12 ECTS）。",
    )


def yzu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    is_grad = _is_graduate(degree_level)
    min_score = 80.0 if is_grad else 70.0
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            "尚未填寫歷年學業成績（GPA / 平均分數）或系排名；元智大學全球事務處校級交換依「系排名成績 50%＋英文檢定成績 50%」評比分發，管理學院院級交換要求歷年成績在班級前 50% 為原則，且境外選課及格標準為大學部 70 分、研究生 80 分。",
        )

    details: list[str] = []
    score_ok = False
    gpa_ok = False
    rank_ok = False

    if academic_score is not None:
        details.append(f"歷年平均 {academic_score:g} 分")
        if academic_score >= min_score:
            score_ok = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= (3.0 if is_grad else 2.75):
            gpa_ok = True
    if class_rank_percent is not None:
        details.append(f"系／班排名前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            rank_ok = True

    summary = "、".join(details)
    if academic_score is not None or academic_gpa is not None:
        passed = score_ok or gpa_ok
    else:
        passed = rank_ok
    if not passed:
        return (
            "fail",
            f"已填報 {summary}，未達元智大學建議學業門檻（班排名前 50% 或 GPA 2.75 / 大學部平均 70 分、研究所 80 分以上）。請確認歷年成績單與目標姊妹校個別 GPA 規定。",
        )
    return (
        "pass",
        f"已填報 {summary}；符合元智大學交換甄選學業基準（校級交換採計系排名 50%＋英檢 50%，管院院級要求班排前 50% 為原則），請同時核對《赴外交換學校一覽表》各校個別 GPA 要求。",
    )


def yzu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請元智大學赴大陸地區（含同濟、南京、武漢、重慶、西南、蘇州、西安交大等校）交換生計畫免附外語檢定證明；惟須具中華民國國籍、持有效臺胞證且在校操行成績達 85 分以上。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。元智大學規定申請國際及香港姊妹校須檢附 2 年內有效之 TOEFL iBT、IELTS（Academic）或 TOEIC 官方成績單（常見門檻為 CEFR B2：TOEFL iBT 72–80、IELTS 5.5–6.5 或 TOEIC 650–785；日韓語組依各校規定 JLPT N1–N3 或 TOPIK 2–4 級）。",
        )
    if test in YZU_ENGLISH_MINIMUMS:
        label, minimum = YZU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        warning = "重要提醒：多數歐美姊妹校要求 CEFR B2（TOEFL iBT 72–80 或 IELTS 6.0），且部分名校（如俄亥俄州立大學、奧克拉荷馬大學、格羅寧根大學、南丹麥大學）不採認 TOEIC，請務必對照《赴外交換學校一覽表》規定。"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}元智大學英語組常見基準門檻 {minimum:g}。{warning}",
        )
    if test == "jlpt":
        passed = 1.0 <= language_score <= 3.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}元智大學日本姊妹校常見門檻範圍（N1–N3；神戶大學、法政大學、神奈川大學等日語授課學程多要求 N2 或 N1，英語授課學程則採計 TOEFL/IELTS/TOEIC）。",
        )
    if test == "topik":
        passed = 2.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}元智大學韓國姊妹校常見門檻範圍（TOPIK 2–6 級；英語授課學程則可憑 TOEFL/IELTS/TOEIC 申請）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請核對元智大學《赴外交換學校一覽表》與管理學院 OIP 公告之目標學校語言檢定要求。",
    )
