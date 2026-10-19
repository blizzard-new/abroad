from __future__ import annotations

import re

from .university_registry import PCCU, resolve_university

PCCU_OIMA_HUB_URL = "https://oima.pccu.edu.tw/exchanges.htm"
PCCU_OUTBOUND_GUIDE_URL = "https://oima.pccu.edu.tw/exchanges-detail.htm"
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
PCCU_RU_EXCHANGE_URL = "https://crgarl.pccu.edu.tw/p/405-1113-110334,c11303.php?Lang=zh-tw"

PCCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 575.0),
}


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
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；《中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點》規定：學士班學生須於本校修業滿一學年以上（轉學生至少完成一學期學業），碩、博士班學生須於本校完成至少一學期學業（在職專班學生如欲申請須另附工作單位同意函）。",
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"一年級", "大一", "1"}:
        return (
            "fail",
            f"已填報 {degree}（{year}）；依《中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點》規定，學士班申請人須於本校完成一學年以上之學業（轉學生須於本校完成至少一學期學業）。",
        )
    if "在職" in degree or "專班" in degree:
        return (
            "needs_confirmation",
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點》第四點規定，在職生提出申請時除系（所）許可及家長同意具結書外，須另附「工作單位同意函」。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合中國文化大學出國交換學生學制與年級規定（學士班修業滿一學年以上、轉學生及碩博士班修業滿一學期以上正式學籍在學學生；交換期間須維持文大在學學籍並完成註冊繳費）。",
    )


def pccu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    is_grad = _is_graduate(degree_level)
    min_score = 80.0 if is_grad else 70.0
    details: list[str] = []
    score_ok = False
    gpa_ok = False
    disadvantaged_sch_ok = False

    if academic_score is not None:
        details.append(f"平均成績 {academic_score:g} 分")
        if academic_score >= min_score:
            score_ok = True
        elif academic_score >= 65.0:
            disadvantaged_sch_ok = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= (3.25 if is_grad else 2.5):
            gpa_ok = True
    if class_rank_percent is not None:
        details.append(f"班/系排名前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            score_ok = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            "尚未填寫學業平均成績、GPA 或班/系排名百分比；中國文化大學日本語文學系赴日交換及「學生國際移動力獎學金」規定：大學部前一學期平均須達 70 分以上、研究所須達 80 分以上（特殊才能或經濟不利生申請國際移動力獎學金須達 65 分以上；國際處海外姊妹校依各校規定須達 GPA 2.5–3.25 以上；教育部學海飛颺須達系排前 20%、學海惜珠須達系排前 30%）。",
        )

    if score_ok or gpa_ok:
        xuehai_note = (
            "同時符合教育部學海飛颺（系排前 20%）與文大國際移動力獎學金學業門檻"
            if (class_rank_percent is not None and class_rank_percent <= 20.0)
            else "符合文大國際移動力獎學金一般生學業門檻（大學部 70 分／研究所 80 分，每次補助 NT$20,000，每年 5/20 及 11/20 截止）；若欲申請教育部學海飛颺須達全系前 20%、學海惜珠須達全系前 30%"
        )
        return (
            "pass",
            f"已填報 {summary}；符合中國文化大學出國交換學業成績門檻（{xuehai_note}；請同步核對目標姊妹校是否訂有特定 GPA 門檻，如清邁大學研究所 GPA 3.25、艾爾朗加大學 GPA 3.2、威斯康辛麥迪遜／海德堡／東義／印尼多媒體大學 GPA 3.0）。",
        )

    if disadvantaged_sch_ok:
        return (
            "needs_confirmation",
            f"已填報 {summary}；達中國文化大學「國際移動力獎學金」特殊才能或經濟不利學生門檻（65 分以上，最高補助 NT$50,000）及部分免設特定 GPA 門檻之國際處／韓文系／大陸姊妹校申請條件，惟未達日本語文學系赴日交換或國際移動力獎學金一般生門檻（大學部 70 分／研究所 80 分）。",
        )

    return (
        "fail",
        f"已填報 {summary}；未達中國文化大學出國交換及國際移動力獎學金最低學業成績標準（一般生大學部平均 70 分／研究所 80 分或 GPA 2.5 以上，經濟不利生 65 分以上）。",
    )


def pccu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country == "中國大陸" and (not test or language_score is None):
        return (
            "pass",
            "申請赴大陸地區 25 所姊妹校交換者，一般中文授課課程免附外語檢定證明（若選修全英語授課課程須符合接待校英語要求）。",
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。依《中國文化大學國際處甄選交換學校一覽表（2026.04.29 更新）》及各語文學系簡章：英語授課姊妹校接受 TOEFL iBT（52–82 分）、IELTS（5.0–6.5）、TOEIC（575–750 分）或 Duolingo（80–115 分）；日文系 28 所日本姊妹校依各校規定要求 JLPT N1–N5；韓文系要求韓語面試（持 TOPIK 加分）；法文組要求 DELF B1–B2。",
        )
    if test in PCCU_ENGLISH_MINIMUMS:
        label, minimum = PCCU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}中國文化大學國際處海外交換英語授課姊妹校基本門檻（{minimum:g}；注意美加英澳部分學校要求 TOEFL iBT 78–82、IELTS 6.0–6.5 或 TOEIC 650–750，請對照各校名額表規定）。",
        )
    if test == "jlpt":
        passed = 1.0 <= language_score <= 5.0
        level = int(language_score)
        tier_note = (
            "符合早稻田、成城、明治、國士館研究所、高知研究所等 N1 要求及所有 N2–N5 日本姊妹校門檻"
            if level == 1
            else (
                "符合二松學舍、大阪經法、東京國際、多摩、長崎國際、敬愛、天理、東洋、名古屋學院、平成國際、琉球等 N2 姊妹校門檻（早稻田、成城一般課程須 N1）"
                if level == 2
                else (
                    "符合長崎大學 JLCP、別府大學、筑紫女學園大學、同志社女子大學、同志社大學（N3）及弘前、大阪國際（N4）、中部、創價、神田外語、信州（N5）門檻"
                    if level == 3
                    else "符合弘前大學、大阪國際大學（N4）或中部大學、創價大學別科、神田外語大學別科、信州大學（N5）門檻（多數日本學部課程須達 N2 以上）"
                )
            )
        )
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}中國文化大學赴日本交換留學日語檢定門檻（{tier_note}）。",
        )
    if test == "topik":
        passed = 1.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}中國文化大學韓國語文學系赴韓留學交換檢定採計標準（韓文系甄選含前學期韓文專業平均 30%、韓語面試 30%、書面審查 40%，持有 TOPIK 檢定證書於書審中優先加分）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請對照《中國文化大學國際處甄選交換學校一覽表》（{PCCU_OIMA_QUOTA_LIST_PDF_URL}：支援 Duolingo 80–115、PTE 43–58、德語 B1–B2、法語 DELF B1–B2、義語 B1、西語 A2–B2）及各語文學系最新門檻。",
    )
