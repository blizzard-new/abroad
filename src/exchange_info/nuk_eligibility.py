from __future__ import annotations

import re

from .university_registry import NUK, resolve_university

NUK_OIA_HOME_URL = "https://dia.nuk.edu.tw/"
NUK_PORTAL_URL = "https://diasis.nuk.edu.tw/"
NUK_EXCHANGE_PROGRAM_URL = "https://dia.nuk.edu.tw/p/412-1034-4130.php?Lang=zh-tw"
NUK_EXCHANGE_APPLY_WORK_URL = "https://dia.nuk.edu.tw/p/406-1034-94206,r1423.php?Lang=zh-tw"
NUK_EXCHANGE_GUIDELINES_PAGE_URL = "https://dia.nuk.edu.tw/p/404-1034-41950.php?Lang=zh-tw"
NUK_EXCHANGE_ELIGIBILITY_URL = "https://dia.nuk.edu.tw/p/404-1034-41951.php?Lang=zh-tw"
NUK_EXCHANGE_PROCESS_URL = "https://dia.nuk.edu.tw/p/404-1034-41952.php?Lang=zh-tw"
NUK_EXCHANGE_SCHEDULE_URL = "https://dia.nuk.edu.tw/p/404-1034-41953.php?Lang=zh-tw"
NUK_EXCHANGE_QUOTAS_URL = "https://dia.nuk.edu.tw/p/404-1034-41956.php?Lang=zh-tw"
NUK_EXCHANGE_ADMITTED_URL = "https://dia.nuk.edu.tw/p/404-1034-45737.php?Lang=zh-tw"
NUK_EXCHANGE_NOTICE_URL = "https://dia.nuk.edu.tw/p/412-1034-4131.php?Lang=zh-tw"
NUK_DUAL_DEGREE_URL = "https://dia.nuk.edu.tw/p/412-1034-4132.php?Lang=zh-tw"
NUK_SCHOLARSHIPS_URL = "https://dia.nuk.edu.tw/p/412-1034-4135.php?Lang=zh-tw"
NUK_EXPERIENCES_URL = "https://dia.nuk.edu.tw/p/412-1034-4136.php?Lang=zh-tw"
NUK_REGS_FORMS_URL = "https://dia.nuk.edu.tw/p/403-1034-1417.php?Lang=zh-tw"
NUK_SISTERS_STATS_URL = "https://dia.nuk.edu.tw/p/412-1034-4120.php?Lang=zh-tw"
NUK_OUTBOUND_STATS_URL = "https://dia.nuk.edu.tw/p/404-1034-42697.php?Lang=zh-tw"

NUK_2027_SPRING_BRIEFING_PDF_URL = "https://dia.nuk.edu.tw/var/file/34/1034/img/563/324829248.pdf"
NUK_2026_SPRING_BRIEFING_PDF_URL = "https://dia.nuk.edu.tw/var/file/34/1034/img/563/750298945.pdf"
NUK_2027_SPRING_QUOTAS_PDF_URL = "https://dia.nuk.edu.tw/var/file/34/1034/img/563/150622.pdf"
NUK_2026_FALL_QUOTAS_PDF_URL = "https://dia.nuk.edu.tw/var/file/34/1034/img/563/150102.pdf"
NUK_LANG_STD_PDF_URL = "https://dia.nuk.edu.tw/var/file/34/1034/img/563/449281794.pdf"
NUK_SELECTION_GUIDELINES_PDF_URL = "https://dia.nuk.edu.tw/var/file/34/1034/img/563/176919109.pdf"
NUK_XUEHAI_LANG_STD_PDF_URL = "https://dia.nuk.edu.tw/var/file/34/1034/img/563/643195488.pdf"

NUK_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 64.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 590.0),
    "toefl_itp": ("TOEFL ITP", 510.0),
}


def is_nuk(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NUK.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立高雄大學",
        "高雄大學",
        "高大",
        "nuk",
        "national university of kaohsiung",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nuk_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立高雄大學交換學生甄選作業要點》規定：（1）申請及出國就讀時須為非當學期畢業且為大二（含）以上之本校日間學制（學士班、碩士班、博士班）在學學生（轉學生須於高大修滿 2 學期以上且具成績）；（2）不含在職專班、當學期應屆畢業生及休學中學生；（3）交換期限以一學期或一學年為限，最長一年，不得申請延長；（4）雙聯學制學生須於高大修業至少滿 2 學期（二校修業時間學士班合計至少滿 32 個月、碩士班合計至少滿 12 個月）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("休學", "已畢業", "退學", "在職", "學分班", "選修生")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立高雄大學交換學生甄選作業要點》，本校交換學生計畫僅限非當學期畢業之日間學制在學學生申請，不含在職專班、已畢業或休學中學生。"
            ),
        )
    if year in {"大一", "大一上", "大一下", "一年級", "學士班一年級"}:
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；依《國立高雄大學交換學生甄選作業要點》及國際事務處《申請資格》規定，申請及出國就讀時須為大二（含）以上之在學學生（轉學生須在本校有 2 學期［含］以上之成績）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：研究所學生校內徵選評分占比為「歷年總成績班級排名 35%、自傳暨研修計畫與有利審查資料 35%、指導教授推薦函 30%」，總分達 70 分［含］以上始獲考慮薦送資格；亦可申請 1+1 雙聯碩士計畫）"
        if is_grad
        else "（提醒：大學部學生校內徵選評分占比為「歷年總成績班級排名 65%、自傳暨研修計畫與有利審查資料 35%」，總分達 70 分［含］以上始獲考慮薦送資格；轉學生須於高大有 2 學期以上成績）"
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立高雄大學交換學生甄選作業要點》日間學制在學及修業年級規定{grad_note}。"
        ),
    )


def nuk_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 70.0
    gpa_min = 2.5
    rank_max = 50.0
    details: list[str] = []
    passes_nuk = False

    if academic_score is not None:
        details.append(f"歷年學業總平均／甄選預估總分 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_nuk = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_nuk = True
    if class_rank_percent is not None:
        details.append(f"班級排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max and academic_score is None and academic_gpa is None:
            passes_nuk = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績、GPA 或班排名百分比；依《國立高雄大學交換學生甄選作業要點》規定：（1）大學部學生：歷年總成績班級排名占 65%、自傳暨研修計畫及其他有利審查之資料（如國際生活／課輔學伴、夏日學校隊輔、SDG 志工大使）占 35%；（2）研究所學生：歷年總成績班級排名占 35%、自傳暨研修計畫占 35%、指導教授推薦函占 30%；（3）總分達 70 分（含）以上者始獲考慮薦送資格（未達 70 分者得補件由審查委員會酌予加分至多 10%）。"
            ),
        )

    if passes_nuk:
        xuehai_ok = (
            (class_rank_percent is not None and class_rank_percent <= 30.0)
            or (academic_score is not None and academic_score >= 80.0)
            or (academic_gpa is not None and academic_gpa >= 3.2)
        )
        tier_note = (
            "符合國立高雄大學校內徵選 70 分及格門檻與多數歐美日韓姊妹校 GPA 2.5–3.0 要求，且具備競爭教育部《學海飛颺／惜珠》出國研修獎學金之優勢班排表現"
            if xuehai_ok
            else "符合國立高雄大學校內徵選 70 分及格門檻；建議強化中英文自傳暨研修計畫與國際學伴／志工大使等有利審查資料（占 35%）以拉高甄選總分"
        )
        return (
            "pass",
            f"已填報 {summary}；符合國立高雄大學交換學生暨雙聯學制甄選學業標準（{tier_note}）。",
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達《國立高雄大學交換學生甄選作業要點》規定之校內審查總分 70 分（含）以上（或相當於 GPA 2.5 以上／班排前 50%）基準。"
        ),
    )


def nuk_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸"} and (
        not test or language_score is None
    ):
        return (
            "pass",
            (
                "申請赴中國大陸姊妹校交換（含廈門大學、華南理工大學、四川大學、重慶大學、東南大學、湖南大學、北京交通大學、大連理工大學、蘭州大學、西北工業大學、深圳大學等），依《國立高雄大學選送優秀學生出國研修之語文能力證明標準》規定免繳語言能力證明。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依《國立高雄大學選送優秀學生出國研修之語文能力證明標準》（須為 2 年內有效成績，申請大陸地區免繳；若尚未取得成績單可先繳報考證明並於補件期限前補繳）：（1）英文：TOEFL iBT 64 / TOEFL ITP 510 / IELTS 5.0 / TOEIC 590 / GEPT 中高級初試或中級複試以上（申請教育部學海飛颺／惜珠需 TOEFL iBT 68 / ITP 520 / IELTS 5.5 / TOEIC 700）；（2）日文：JLPT N3 以上（學海需 N2；熊本、近畿、千葉、滋賀、福岡等需 N2，岡山與宮城學院女子大學需 N1）；（3）韓文：TOPIK 3級以上（學海需 4級；首爾大學需 5級）；（4）法／德／西文：A1 以上（學海需 A2）；（5）越南文：VINATEST B 或 IVPT B1 以上。"
            ),
        )
    if test in NUK_ENGLISH_MINIMUMS:
        label, minimum = NUK_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達《國立高雄大學選送優秀學生出國研修之語文能力證明標準》校內英語門檻（TOEFL iBT 64 / ITP 510 / IELTS 5.0 / TOEIC 590）"
        if (
            (test == "toefl" and language_score >= 80)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "toefl_itp" and language_score >= 550)
        ):
            tier_note = "同時符合高大校內交換門檻、教育部《學海飛颺／惜珠》獎學金標準（iBT 68 / IELTS 5.5 / TOEIC 700）及歐美日韓雙聯與頂尖姊妹校（如首爾大學、密西根大學迪爾伯恩分校、羅浮堡大學、丹地大學、亞伯丁大學、華盛頓州立大學）進階英語門檻"
        elif (
            (test == "toefl" and language_score >= 68)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toeic" and language_score >= 700)
            or (test == "toefl_itp" and language_score >= 520)
        ):
            tier_note = "同時符合高大校內交換門檻及《國立高雄大學配合教育部獎助大學校院選送優秀學生出國研修語文能力標準》（TOEFL iBT 68 / ITP 520 / IELTS 5.5 / TOEIC 700），可同步申請教育部學海飛颺與學海惜珠獎學金"
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}國立高雄大學國際事務處出國研修英語能力證明標準（校內最低門檻：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level == 1:
            tier_note = "符合高大校內門檻（N3）、教育部學海飛颺／惜珠標準（N2）及日本全部 50 所姊妹校（含要求 N1 之岡山大學、宮城學院女子大學與要求 N2 之千葉大學、熊本大學、近畿大學、滋賀大學、福岡大學）最高日語門檻"
        elif level == 2:
            tier_note = "同時符合高大校內門檻（N3）、教育部學海飛颺／惜珠獎學金標準（N2）及熊本大學、近畿大學、神戶藝術工科大學、滋賀大學、福岡大學、關西國際大學、千葉大學等熱門日本姊妹校門檻"
        elif level == 3:
            tier_note = "符合《國立高雄大學選送優秀學生出國研修之語文能力證明標準》日文 JLPT N3 門檻（可申請琉球大學、創價大學、東亞大學、名櫻大學、鹿兒島大學、長崎大學、松山大學、愛媛大學、新潟大學、尚絅大學、公立函館未來大學等；若欲申請教育部學海獎學金則需達 JLPT N2）"
        else:
            tier_note = "國立高雄大學選送優秀學生出國研修之日文門檻為 JLPT N3（3級）以上合格"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立高雄大學日本姊妹校日語能力證明標準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 3 <= level <= 6
        if level >= 5:
            tier_note = "符合高大校內門檻（3級）、教育部學海獎學金標準（4級）及韓國國立首爾大學（要求 TOPIK 5級）、崇實大學（4級）、成均館大學、漢陽大學、中央大學、世宗大學、加圖立大學等全部 29 所韓國姊妹校最高韓語門檻"
        elif level == 4:
            tier_note = "同時符合高大校內門檻（3級）、教育部學海飛颺／惜珠獎學金標準（4級）及崇實大學、漢陽大學、中央大學、成均館大學、世宗大學、加圖立大學等絕大多數韓國姊妹校韓語門檻"
        elif level == 3:
            tier_note = "符合《國立高雄大學選送優秀學生出國研修之語文能力證明標準》韓文 TOPIK 3級門檻（若欲申請教育部學海獎學金或崇實大學需達 4級，首爾大學需達 5級）"
        else:
            tier_note = "國立高雄大學選送優秀學生出國研修之韓文門檻為 TOPIK 3級以上合格"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立高雄大學韓國姊妹校韓語能力證明標準（{tier_note}）。",
        )
    if test in {"dele", "delf", "goethe", "testdaf", "tcf", "vinatest", "ivpt"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}國立高雄大學國際事務處第二外語（法／德／西文 A1、越文 B1 以上）語文能力證明標準。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照《國立高雄大學選送優秀學生出國研修之語文能力證明標準》與各姊妹校最新交換名額表確認。",
    )
