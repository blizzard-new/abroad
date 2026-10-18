from __future__ import annotations

import re

from .university_registry import NCCU, resolve_university

NCCU_OUTBOUND_URL = "https://outbound.nccu.edu.tw/"
NCCU_GUIDELINES_PDF_URL = "https://outbound.nccu.edu.tw/get_file/68dddee81ad07"
NCCU_PARTNERS_URL = "https://outbound.nccu.edu.tw/student-outgoing-list"
NCCU_PARTNERS_XLSX_URL = "https://outbound.nccu.edu.tw/get_file/6909abcb86a87"
NCCU_MAINLAND_URL = "https://oic.nccu.edu.tw/Post/119"
NCCU_MAINLAND_PDF_URL = "https://oic.nccu.edu.tw/File/Download/20612"
NCCU_EXPERIENCE_URL = "https://oic.nccu.edu.tw/Experience"
NCCU_SCHOLARSHIP_URL = "https://outbound.nccu.edu.tw/student-outgoing-scholarship"
NCCU_REGULATION_PDF_URL = "https://oic.nccu.edu.tw/File/Download/712"

NCCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 75.0),
    "ielts": ("IELTS Academic", 6.0),
    "toeic": ("TOEIC Listening & Reading", 750.0),
}


def is_nccu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NCCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立政治大學",
        "政治大學",
        "政大",
        "nccu",
        "national chengchi university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nccu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；《國立政治大學選送學生出國進修與交流實施辦法》及校級交換甄選簡章規定：本校在學學生（不含在職專班生）於出國前至少須在政大就讀滿一學期（外國轉學生須滿一學年），且出國交換期間須完成政大註冊並維持在學身分。",
        )
    if "在職" in degree or "專班" in degree:
        return (
            "fail",
            f"已填報 {degree}；依《國立政治大學選送學生出國進修與交流實施辦法》第三條規定，申請資格限本校在學學生（不含在職專班生）。",
        )
    if year in {"一年級", "大一", "碩一", "博一", "1"}:
        return (
            "needs_confirmation",
            f"已填報 {degree}（{year}）。政大校級交換甄選開放大一、碩一及博一新生於入學第一學期提出申請（預定於大二／碩二／博二出國交換），但出國前至少須於政大修業滿一學期並取得前學期成績單（大一與碩一新生申請時倘尚無前學期政大成績，須依簡章規定檢附學測／分科測驗成績單或大學歷年成績單）。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立政治大學在學學生校級交換甄選申請資格（出國期間須維持政大註冊在學身分，不得辦理休學或畢業；於政大修讀同一學位期間，透過校級甄選赴國外或大陸交換各以一次為限）。",
    )


def nccu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    is_grad = _is_graduate(degree_level)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            "尚未填寫歷年學業總平均成績或班排名百分比；政大校級赴國外交換甄選規定：研究生前學期總平均成績須達 70 分以上（碩一、博一新生採計大學或碩士歷年成績），學士班則依前學期全班排名百分比換算在校成績（101 減去班排百分比，占甄選總分 20%）。",
        )

    details: list[str] = []
    score_ok = False
    gpa_ok = False
    rank_ok = False

    if academic_score is not None:
        details.append(f"歷年總平均 {academic_score:g} 分")
        if academic_score >= 70.0:
            score_ok = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= 2.7:
            gpa_ok = True
    if class_rank_percent is not None:
        details.append(f"班排名前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            rank_ok = True

    summary = "、".join(details)
    if is_grad:
        passed = score_ok if academic_score is not None else (gpa_ok or rank_ok)
        if not passed:
            return (
                "fail",
                f"已填報 {summary}（研究所學制），未達國立政治大學校級交換學生甄選簡章規定之「研究生前學期總平均成績 70 分以上」基本門檻。",
            )
    else:
        passed = score_ok or gpa_ok or rank_ok
        if not passed:
            return (
                "needs_confirmation",
                f"已填報 {summary}；政大學士班校級交換雖無硬性 70 分淘汰門檻（以 101 減去全班排名百分比占甄選總分 20%），惟多數海外姊妹校要求 GPA 2.75–3.0（約 70–75 分）以上，且大陸交換甄選總成績須達 75 分以上始予錄取。",
            )

    return (
        "pass",
        f"已填報 {summary}；符合國立政治大學校級交換學業成績條件（甄選總分計算：外語檢定成績占 50%、讀書計畫及自傳占 30%、在校成績占 20%；赴大陸交換則為口試 35%、在校成績 30%、書審 35%，總成績須達 75 分以上）。",
    )


def nccu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請國立政治大學赴大陸地區 26 所姊妹校（北京大學、清華大學、復旦大學、上海交通大學、南京大學等）交換計畫以中文授課為主，免檢附外語能力檢定證明。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。政大校級赴國外交換分為八大語組（英語、日語、德語、法語、西語、韓語、俄語、土語），報名時須繳交距離報名截止日兩年內有效之合格檢定證書正本（英語組多要求 TOEFL iBT 75–100 或 IELTS Academic 6.0–7.0，僅布拉格經濟大學、里昂第三大學及亞洲部分姊妹校接受 TOEIC；各校明確門檻請對照簡章附件一）。",
        )
    if test in NCCU_ENGLISH_MINIMUMS:
        label, minimum = NCCU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        if test == "toeic":
            warning = "重要提醒：政大校級英語組絕大多數歐美姊妹校僅採計 TOEFL iBT 或 IELTS Academic，僅少數特定姊妹校（如捷克布拉格經濟大學、法國里昂第三大學及部分亞洲英語組名額）接受 TOEIC，請務必逐校核對《115學年度第1學期出國交換生甄選學校一覽表》。"
        else:
            warning = "提醒：外語檢定成績占政大校級交換甄選總成績 50%，且不得跨語組選填志願；請務必確認目標姊妹校於簡章附件一所列之單項小分與總分門檻。"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立政治大學校級交換英語組常見基準 {minimum:g}。{warning}",
        )
    if test == "jlpt":
        if partner_country and partner_country != "日本":
            return (
                "needs_confirmation",
                f"已填寫 JLPT N{int(language_score)}；政大日語組僅限選填日本地區日語組姊妹校，若欲申請英語組姊妹校須檢附有效之 TOEFL iBT 或 IELTS 成績。",
            )
        passed = 1.0 <= language_score <= 5.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}國立政治大學日語組檢定申請條件（日本日語組 37 所姊妹校依校別要求 JLPT N1、N2 或 N3–N4，請依各校一覽表為準）。",
        )
    if test == "topik":
        if partner_country and partner_country != "韓國":
            return (
                "needs_confirmation",
                f"已填寫 TOPIK {int(language_score)} 級；政大韓語組僅限選填韓國地區韓語組姊妹校，申請其他語組須檢附對應語組檢定證明。",
            )
        passed = 1.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}國立政治大學韓語組檢定申請條件（韓語組 10 所姊妹校依校別要求 TOPIK 1–4 級，請對照簡章附件一）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請對照國立政治大學《校級出國交換生甄選學校一覽表》（https://outbound.nccu.edu.tw/student-outgoing-list）八大語組各校檢定標準。",
    )
