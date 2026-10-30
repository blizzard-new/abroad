from __future__ import annotations

import re

from .university_registry import USC, resolve_university

USC_OIA_HOME_URL = "https://uscoia.usc.edu.tw/"
USC_PORTAL_URL = "https://oia-exchange.vercel.app/"
USC_EXCHANGE_OVERVIEW_URL = "https://uscoia.usc.edu.tw/p/412-1049-1331.php?Lang=zh-tw"
USC_EXCHANGE_SCHOOLS_URL = "https://uscoia.usc.edu.tw/p/412-1049-1415.php?Lang=zh-tw"
USC_DUAL_DEGREE_SCHOOLS_URL = "https://uscoia.usc.edu.tw/p/412-1049-1416.php?Lang=zh-tw"
USC_SCHOLARSHIPS_URL = "https://uscoia.usc.edu.tw/p/412-1049-2216.php?Lang=zh-tw"
USC_REGULATIONS_URL = "https://uscoia.usc.edu.tw/p/412-1049-468.php?Lang=zh-tw"
USC_FORMS_URL = "https://uscoia.usc.edu.tw/p/412-1049-1879.php?Lang=zh-tw"
USC_FAQ_URL = "https://uscoia.usc.edu.tw/p/412-1049-1877.php?Lang=zh-tw"
USC_CREDIT_TRANSFER_URL = "https://uscoia.usc.edu.tw/p/412-1049-1880.php?Lang=zh-tw"
USC_EXPERIENCES_URL = "https://uscoia.usc.edu.tw/p/412-1049-1894.php?Lang=zh-tw"
USC_OIA_ADVISORS_URL = "https://uscoia.usc.edu.tw/p/412-1049-467.php?Lang=zh-tw"

USC_115_2_BROCHURE_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/753042862.pdf"
USC_115_1_BROCHURE_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/536932215.pdf"
USC_DUAL_DEGREE_RULES_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/816434517.pdf"
USC_STUDY_ABROAD_SCHOLARSHIP_RULES_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/598520263.pdf"
USC_STUDY_ABROAD_GUIDELINES_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/552408866.pdf"
USC_XUEHAI_FEIYANG_RULES_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/539881728.pdf"
USC_XUEHAI_XIZHU_RULES_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/161763858.pdf"
USC_LANG_TABLE_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/957/821831637.pdf"
USC_GRADE_CREDIT_TABLE_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/411457463.pdf"
USC_REPORT_TEMPLATE_PDF_URL = "https://uscoia.usc.edu.tw/var/file/49/1049/img/959/220219236.pdf"

USC_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 460.0),
}


def is_usc(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == USC.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "實踐大學",
        "實踐",
        "usc",
        "shih chien university",
        "shih chien",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def usc_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《實踐大學辦理本校學生赴境外大專校院進修作業要點》及《赴境外姊妹校交換暨雙聯學制計畫簡章》規定：（1）單學期交換計畫與單學期訪問計畫（Study Abroad）申請人須為於實踐大學修業滿一學期以上之在籍學生（不限學制，大一下即可申請大二出國；延修生須經系所主任及國際交流輔導教師同意，且兩封推薦信須由系主任、院長或導師撰寫）；（2）雙聯學制學士班須修業滿五學期以上（2+2 雙學士須滿三學期以上；1+1 雙碩士須滿一學期以上）；（3）休學中或已畢業者不得申請，且申請教育部學海飛颺／惜珠獎學金者不含國內及境外在職專班生。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("休學", "已畢業", "退學", "學分班", "選修生")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依實踐大學國際事務處《出國交換 FAQ》與《辦理本校學生赴境外大專校院進修作業要點》，本校交換暨雙聯計畫僅限具有正式學籍且在校之學生申請，已畢業或休學中不得申請。"
            ),
        )
    if year in {"大一上", "一年級上學期", "碩一上", "碩士班一年級上學期"}:
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；依《115-2 實踐大學赴境外姊妹校交換暨雙聯學制計畫簡章》參、一，申請人須於本校修業滿一學期以上（最快申請赴姊妹校交換時間為大一下學期申請、大二出國；1+1 雙碩士須修業滿一學期以上）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩士班學生可申請出國交換或 1+1 雙碩士計畫［如法國雷恩商學院、美國加州大學河濱分校 UCR、澳洲國際飯店管理學院 ICHM、西班牙桑特波爾廚藝學院 EUHT StPOL、瑞士 HTMi］，轉換回實踐後每學期最低應修 6 學分；在職專班學生可申請交換但不得申請教育部學海飛颺／惜珠獎學金）"
        if is_grad
        else "（提醒：每位學生至多可填 5 個志願並須繳交申請費 NT$ 2,000；大學部轉換回實踐後每學期不得少於 9 學分；雙聯學制 2+2 須修業滿三學期、3+1／3+1.5／3+1+1／3+2 須修業滿五學期；延修生申請須經系主任及國際交流輔導教師同意）"
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《實踐大學辦理本校學生赴境外大專校院進修作業要點》與《交換暨雙聯學制計畫簡章》在學學籍及修業學期規定{grad_note}。"
        ),
    )


def usc_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 75.0
    gpa_min = 3.0
    rank_max = 50.0
    xuehai_rank_max = 30.0
    details: list[str] = []
    passes_usc = False

    if academic_score is not None:
        details.append(f"歷年學業總平均 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_usc = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_usc = True
    if class_rank_percent is not None:
        details.append(f"班級排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max and academic_score is None and academic_gpa is None:
            passes_usc = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績、GPA 或班排名百分比；依《115-2 實踐大學赴境外姊妹校交換暨雙聯學制計畫簡章》參、二及《資料考核表》規定：（1）在校歷年學業成績總平均須達 75 分以上（約 GPA 3.0+），且歷年操行成績平均須達 75 分以上、無大過／小過／警告紀錄；（2）校內初選《資料考核表》學業成績配分：基準 20 分，總平均 75–77 加 1 分、78–80 加 2 分、81–83 加 3 分、84–86 加 4 分、87 分以上加 5 分（最高 25 分）；（3）申請教育部《學海飛颺》或《學海惜珠》獎學金者，前一學期學業成績須達全班前 30%、操行成績達 80 分以上。"
            ),
        )

    if passes_usc:
        bonus = 1
        if academic_score is not None:
            if academic_score >= 87:
                bonus = 5
            elif academic_score >= 84:
                bonus = 4
            elif academic_score >= 81:
                bonus = 3
            elif academic_score >= 78:
                bonus = 2
        xuehai_ok = (
            (class_rank_percent is not None and class_rank_percent <= xuehai_rank_max)
            or (academic_score is not None and academic_score >= 82.0)
            or (academic_gpa is not None and academic_gpa >= 3.5)
        )
        tier_note = (
            f"符合實踐大學交換暨雙聯學制歷年總平均 75 分門檻（於校內初選《資料考核表》學業成績項目可獲 20+{bonus}={20+bonus} 分），且符合教育部《學海飛颺／惜珠》獎學金（前一學期全班前 30%）及實踐 1-8 優秀學生交換獎學金申請標準"
            if xuehai_ok
            else f"符合實踐大學交換暨雙聯學制歷年總平均 75 分門檻（於校內初選《資料考核表》學業成績項目可獲 20+{bonus}={20+bonus} 分）；若欲申請教育部《學海飛颺／惜珠》獎學金，請確認前一學期學業成績達全班前 30% 且操行達 80 分以上"
        )
        return (
            "pass",
            f"已填報 {summary}；符合實踐大學赴境外姊妹校交換暨雙聯學制甄選學業標準（{tier_note}）。",
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達《實踐大學赴境外姊妹校交換暨雙聯學制計畫簡章》規定之歷年學業成績總平均 75 分以上（或相當於 GPA 3.0 以上）門檻。"
        ),
    )


def usc_language_check(
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
                "申請赴中國大陸 24 所姊妹校交換（含上海交通大學、同濟大學、東華大學、上海戲劇學院、北京外國語大學、中國傳媒大學、中央音樂學院、中國政法大學、北京服裝學院、中山大學、廣州美術學院、四川大學、重慶大學、西安交通大學、江南大學、蘭州大學等），依實踐大學國際事務處規定免繳外語能力檢定證明（若有語檢成績仍可於《資料考核表》加分）。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依《實踐大學學生赴境外交換資料考核表—語言成績轉換表》與姊妹校規定：（1）語檢須為兩年內有效，對照 CEFR 四級於考核表加分：CEFR B1（加1分：TOEIC 550 / IELTS 4.0 / TOEFL iBT 42 / JLPT N3 95分）、CEFR B2（加2分：TOEIC 750–785 / IELTS 5.5 / TOEFL iBT 72 / JLPT N2 90分）、CEFR C1（加3分：TOEIC 880–945 / IELTS 7.0 / TOEFL iBT 95）、CEFR C2（加4分：TOEIC 950 / IELTS 8.5 / JLPT N1 100分）；（2）歐美、大洋洲與亞洲英語授課學程多要求 TOEFL iBT 61–80、IELTS 5.5–6.5 或 TOEIC 600–785；（3）日本 16 校要求 JLPT N2–N3（英語授課組採認 TOEIC / TOEFL / IELTS）；（4）韓國 9 校要求 TOPIK 2–4 級或英語檢定；（5）中國大陸 24 校免附外語檢定。"
            ),
        )
    if test in USC_ENGLISH_MINIMUMS:
        label, minimum = USC_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達實踐《語言成績轉換表》CEFR B1（考核表 20+1=21 分），可申請採認 CEFR B1（TOEIC 550–600 / IELTS 5.0 / TOEFL iBT 61）之亞洲與部分歐洲姊妹校"
        if (
            (test == "toefl" and language_score >= 95)
            or (test == "ielts" and language_score >= 7.0)
            or (test == "toeic" and language_score >= 880)
            or (test == "toefl_itp" and language_score >= 627)
        ):
            tier_note = "達實踐《語言成績轉換表》CEFR C1–C2（考核表加 3–4 分，獲 23–24 分），符合實踐大學全部歐美、大洋洲、亞洲英語授課交換、訪問計畫（如倫敦藝術大學 UAL、UC Davis、RMIT）及全部 20 校跨國雙聯學制最高英語門檻"
        elif (
            (test == "toefl" and language_score >= 72)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toeic" and language_score >= 750)
            or (test == "toefl_itp" and language_score >= 543)
        ):
            tier_note = "達實踐《語言成績轉換表》CEFR B2（考核表 20+2=22 分），符合絕大多數歐美、澳洲、日韓英語授課交換及雙聯學制（TOEFL iBT 72–80 / IELTS 5.5–6.0 / TOEIC 750–785）門檻"
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}實踐大學國際事務處出國交換暨雙聯學制英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 4
        if level == 1:
            tier_note = "達實踐《語言成績轉換表》CEFR C2（考核表 20+4=24 分），符合千葉大學、文化學園大學、實踐女子大學、東京家政大學、明治學院大學、京都橘大學、大阪公立大學等全部 16 所日本交換與雙聯姊妹校最高日語門檻"
        elif level == 2:
            tier_note = "達實踐《語言成績轉換表》CEFR B2（考核表 20+2=22 分），符合千葉大學、文化學園大學、實踐女子大學、東京家政大學、杉野服飾大學、城西國際大學、京都橘大學、大阪公立大學、長崎外國語大學、武庫川女子大學等絕大多數日本姊妹校日語門檻"
        elif level == 3:
            tier_note = "達實踐《語言成績轉換表》CEFR B1（考核表 20+1=21 分），可申請採認 JLPT N3 之日本姊妹校（如實踐女子大學、東京家政大學、杉野服飾大學、青森大學、吉備國際大學、長崎外國語大學、東北文教大學等）"
        elif level == 4:
            tier_note = "可申請日本青森大學、吉備國際大學等採認基礎日語或搭配英語授課之日本姊妹校（建議提升至 JLPT N3–N2 以取得考核表語言加分）"
        else:
            tier_note = "實踐大學日本姊妹校日語授課一般要求 JLPT N2 或 N3 以上（或改以英語檢定申請英語授課學程）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}實踐大學日本姊妹校日語檢定基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 1 <= level <= 6
        if level >= 3:
            tier_note = "符合漢陽大學、漢陽大學 ERICA 校區、建國大學、國民大學、誠信女子大學、明知大學、韓國航空大學、國立全北大學、釜山外國語大學等全部 9 所韓國姊妹校韓語授課門檻"
        elif level >= 1:
            tier_note = "可申請接受基礎韓語（TOPIK 2 級）或搭配英語檢定（TOEFL iBT 71+ / IELTS 5.5+ / TOEIC 750+）之韓國姊妹校（如又松大學 SolBridge、明知大學、釜山外國語大學等）"
        else:
            tier_note = "實踐大學韓國姊妹校要求 TOPIK 2–4 級以上，或以英語檢定（CEFR B2）申請英語授課課程"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}實踐大學韓國姊妹校韓語檢定基準（{tier_note}）。",
        )
    if test in {"dele", "delf", "goethe", "testdaf"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}實踐大學國際事務處歐語區（西語／法語／德語）姊妹校語言檢定基準。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照《實踐大學學生赴境外交換資料考核表—語言成績轉換表（CEFR B1–C2）》與各姊妹校申請資訊專頁確認。",
    )
