from __future__ import annotations

import re

from .university_registry import FCU, resolve_university

FCU_OUTBOUND_URL = "https://oia.fcu.edu.tw/sap/introduction/"
FCU_APPLY_PORTAL_URL = "https://oiasap.fcu.edu.tw/"
FCU_QUOTALIST_URL = "https://oiasap.fcu.edu.tw/"
FCU_COLLABORATION_URL = "https://oia.fcu.edu.tw/collaboration/"
FCU_SCHOLARSHIP_URL = "https://oia.fcu.edu.tw/sap/scholarship/"
FCU_DUALDEGREE_URL = "https://oia.fcu.edu.tw/sap/dualdegree/"

FCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS Academic", 5.5),
    "toeic": ("TOEIC", 550.0),
}


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
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；逢甲大學規定申請人於提出申請及出國研修期間應為本校註冊在學學生（原則上不得為延修生；復學或入學未滿 1 學期者不得申請，但研究生不在此限）。",
        )
    if any(token in degree for token in ("在職", "EMBA")):
        return (
            "fail",
            f"已填報 {degree}。逢甲大學出國交換及教育部學海系列獎助規定申請對象不含在職專班及休學學生。",
        )
    if any(token in year for token in ("延修", "延畢")):
        return (
            "fail",
            f"已填報 {degree}（{year}）。逢甲大學簡章規定申請人原則上不得為延修生（惟將出國研修列為畢業條件之特定系所／學位學程學生不在此限）。",
        )
    if not _is_graduate(degree) and any(token in year for token in ("大一上", "新生", "未滿一學期")):
        return (
            "fail",
            f"已填報 {degree}（{year}）。逢甲大學規定學士班入學或復學未滿 1 學期者不得申請（研究生不在此限）。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合逢甲大學正式學籍在學學生申請範圍（錄取後須繳交保證金：獲獎助或赴學費互免校 NT$10,000、自費研修 NT$5,000；出國期間每學期修課下限為大一至大三 12 學分、大四 9 學分、研究生 3 學分）。",
    )


def fcu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            "尚未填寫歷年學業成績（GPA / 平均分數）或系排名；逢甲大學《選送學生出國研修簡章》規定在校歷年總平均 GPA 須達 3.0（含）以上（百分制換算約 75 分以上），且申請全學年互免交換者歷年系排名須達前 50%。",
        )

    details: list[str] = []
    score_ok = False
    gpa_ok = False
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
        details.append(f"系／班排名前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            rank_ok = True

    summary = "、".join(details)
    if academic_gpa is not None:
        passed = gpa_ok
    elif academic_score is not None:
        passed = score_ok
    else:
        passed = rank_ok

    if not passed:
        return (
            "fail",
            f"已填報 {summary}，未達逢甲大學出國研修簡章規定之「在校歷年總平均 GPA 3.0（含）以上（或百分制約 75 分以上）」基本門檻。",
        )
    return (
        "pass",
        f"已填報 {summary}；符合逢甲大學「在校歷年總平均 GPA 3.0（含）以上」基本門檻（若申請全學年互免交換須同時符合系排名前 50%；系排名前 30% 並可納入逢甲出國研修獎助學金及教育部學海飛颺評比），請同時核對各合作校個別 GPA 規定。",
    )


def fcu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請逢甲大學赴大陸地區（含同濟、復旦、南京、天津、廈門、武漢、哈爾濱工業、大連理工、吉林、蘭州等校）交換生計畫免附外語檢定證明；惟國際與大陸地區僅能擇一申請，且建議選填與本身科系相近之專業。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。逢甲大學規定申請國際地區須檢附符合目標學校規定之有效外語檢定成績單（常見門檻為 TOEFL iBT 61–80、IELTS 5.5–6.5、TOEIC 550–785 或 Duolingo 95–110；日韓語組為 JLPT N1–N3 或 TOPIK 2–4 級），且考試日期須符合當期簡章有效期限規定。",
        )
    if test in FCU_ENGLISH_MINIMUMS:
        label, minimum = FCU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        warning = "重要提醒：逢甲《出國研修學校查詢系統（oiasap.fcu.edu.tw）》所列外語標準符合其中一項即可，惟歐美澳名校與雙聯學制多要求 TOEFL iBT 79–90 或 IELTS 6.0–6.5，請務必對照目標學校個別門檻。"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}逢甲大學國際地區常見英語基準門檻 {minimum:g}。{warning}",
        )
    if test == "jlpt":
        passed = 1.0 <= language_score <= 3.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}逢甲大學日本姊妹校常見門檻範圍（N1–N3；立命館、近畿、名城、山口、新潟、信州等校依學程要求 JLPT N1–N3 或英語檢定）。",
        )
    if test == "topik":
        passed = 2.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}逢甲大學韓國姊妹校常見門檻範圍（TOPIK 2–6 級；成均館、漢陽、中央、建國、東國等校英語授課學程亦可憑 TOEFL/IELTS/TOEIC 申請）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請核對逢甲大學《出國研修學校查詢系統（oiasap.fcu.edu.tw）》之目標學校語言檢定要求。",
    )
