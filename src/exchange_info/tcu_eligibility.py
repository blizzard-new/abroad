from __future__ import annotations

import re

from .university_registry import resolve_university

TCU_OGA_HOME_URL = "https://oga.tcu.edu.tw/"
TCU_EXCHANGE_HUB_URL = "https://oga.tcu.edu.tw/international-exchange/"
TCU_OUTBOUND_OVERVIEW_URL = (
    "https://oga.tcu.edu.tw/outbound-exchange-student-program/"
)
TCU_OUTBOUND_PARTNERS_URL = (
    "https://oia.tcu.edu.tw/outbound-exchange-student-program/"
)
TCU_DUAL_DEGREE_URL = "https://oga.tcu.edu.tw/dual-double-degree-program/"
TCU_DUAL_DEGREE_DETAIL_URL = "https://oia.tcu.edu.tw/a-double-degree/"
TCU_MAINLAND_EXCHANGE_URL = "https://oia.tcu.edu.tw/%e5%a4%a7%e9%99%b8%e5%9c%b0%e5%8d%80%e5%ad%b8%e7%94%9f%e6%a9%9f%e6%8f%9b%e7%a0%94%e7%bf%92%e7%94%b3%e8%ab%8b%e8%a8%8a%e6%81%af/"
TCU_SISTER_SCHOOLS_URL = "https://oga.tcu.edu.tw/sister-schools-3/"
TCU_REGULATIONS_URL = "https://oga.tcu.edu.tw/regulation-and-policies/"
TCU_SCHOLARSHIPS_URL = "https://oga.tcu.edu.tw/scholarship/"
TCU_FUNDING_PROJECTS_URL = (
    "https://oia.tcu.edu.tw/international-funding-projects/"
)
TCU_OVERSEAS_SUBSIDY_URL = (
    "https://oia.tcu.edu.tw/overseas-exchange-and-subsidy/"
)
TCU_MOE_XUEHAI_URL = (
    "https://oia.tcu.edu.tw/moe-scholarshipstudy-abroad-and-internship/"
)
TCU_OTHER_GRANTS_URL = (
    "https://oia.tcu.edu.tw/other-financial-assistance-grant/"
)
TCU_EXPERIENCES_URL = "https://oia.tcu.edu.tw/insightful-experience/"
TCU_STUDENT_STORIES_URL = "https://oia.tcu.edu.tw/student-stories/"
TCU_CREDIT_TRANSFER_URL = "https://academic.tcu.edu.tw/?page_id=3478"
TCU_LAW_INDEX_URL = "https://law.tcu.edu.tw/TCU/ScLawQryOut.php"

TCU_DUAL_DEGREE_REGULATION_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2025/11/慈濟大學與境外學校辦理雙聯學制實施辦法-1070508備查版.pdf"
TCU_ACADEMIC_COOP_REGULATION_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2025/11/慈濟大學與國內外學校機構簽訂學術合作協議書辦法.pdf"
TCU_ENGLISH_REF_TABLE_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2026/02/慈濟大學英語主要檢測參考對照表20260210.pdf"
TCU_CEFR_B1_TABLE_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2026/04/慈濟大學CEFR-B1-含-級以上或同等語言能力對照表.pdf"

TCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toefl_itp": ("TOEFL ITP/PBT", 460.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 85.0),
}


def is_tcu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == "tcu":
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "慈濟大學",
        "慈大",
        "慈濟",
        "慈濟醫學院",
        "慈濟技術學院",
        "慈濟科技大學",
        "tcu",
        "tzu chi university",
        "tzu chi university, taiwan",
        "tzu-chi university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def tcu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《慈濟大學國際交換學生甄選辦法》及出國交換生甄選簡章規定：（1）限本校在學全職學位生（大學部二年級（含）以上、碩士班、博士班在學學生；大一新生於大一下學期起得申請大二赴外交換；不含在職專班、延畢生及休學生）；（2）跨國雙聯與三聯學位須符合《慈濟大學與境外學校辦理雙聯學制實施辦法》規定之修業期限（學士班如英國密德薩斯大學 3+1 累計至少 32 個月、碩士班如德墨臺 TRIM 三聯碩士與美國安德魯斯大學 1+1 MBA 至少 12 個月、博士班如泰國瑪希敦與納黎萱博士雙聯至少 24 個月）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in (
            "在職專班",
            "碩專",
            "emba",
            "EMBA",
            "學分班",
            "選修生",
            "休學",
            "延畢",
            "延畢生",
            "延修",
            "應屆畢業",
            "當學期畢業",
        )
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《慈濟大學國際交換學生甄選辦法》、《慈濟大學學生海外交流補助辦法》與教育部學海系列計畫規定，在職專班、延畢（延修）生、休學生及當學期應屆畢業生不得申請出國交換與相關獎助學金。"
            ),
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"大一上", "一年級上學期"}:
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；依慈濟大學全球事務處出國交換學生甄選簡章規定，出國交換時須為大學部二年級（含）以上在學學生，大一新生須於大一下學期始得提出大二赴外交換申請。建議於大一上學期維持全班排名前 50%（GPA 2.5+）並累積服務學習訓練時數與外語檢定，於大一下學期報名甄選。"
            ),
        )
    grad_note = (
        "（提醒：碩博士班研究生可申請學期交換、德墨臺「跨洲際全球研究三聯碩士（TRIM）」、美國安德魯斯大學「1+1 MBA 雙碩士」或泰國瑪希敦大學／納黎萱大學「醫學科學研究所博士雙聯學位」，出國期間須維持慈大在學註冊）"
        if is_grad
        else "（提醒：學士班學生除可申請美、加、德、瑞、日、韓、馬、泰、陸學期交換外，公衛系、生科系、分遺系、外語系及國管學程學生另可申請英國倫敦密德薩斯大學 3+1 雙學士學位；堪薩斯州立大學交換限醫學院與國際學院、泰國法政大學限傳播學系、日本尚絅大學限女生、大陸南京大學限臺港澳籍學生）"
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合慈濟大學全球事務處（OGA）《國際交換學生甄選辦法》、《與境外學校辦理雙聯學制實施辦法》及教育部學海系列計畫之在學身分規定{grad_note}。"
        ),
    )


def tcu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 75.0
    gpa_min = 2.5
    rank_max = 50.0
    details: list[str] = []
    passes_general = False
    passes_high_tier = False

    if academic_score is not None:
        details.append(f"學業平均 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_general = True
        if academic_score >= 80.0:
            passes_high_tier = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_general = True
        if academic_gpa >= 3.0:
            passes_high_tier = True
    if class_rank_percent is not None:
        details.append(f"全班排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_general = True
        if class_rank_percent <= 30.0:
            passes_high_tier = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業成績、GPA 或全班排名百分比；依慈濟大學全球事務處《出國交換學生甄選簡章》及《國際交換學生甄選辦法》規定：（1）歷年學業成績排名須達全班前百分之五十（50%）（約折合學業平均 75 分或 GPA 2.5 以上），且在校期間操行成績優良；（2）美國加州州立大學海峽群島分校（CSUCI）明訂歷年 GPA 須達 2.5 以上；（3）申請跨國雙聯與三聯學位（德墨臺 TRIM 三聯碩士、英國密德薩斯大學 3+1、美國安德魯斯大學 1+1 MBA、泰國瑪希敦／納黎萱博士雙聯）及教育部《學海飛颺／惜珠》建議維持 GPA 2.7–3.2（或全班前 30%）以上。"
            ),
        )

    if passes_general:
        tier_notes: list[str] = [
            "符合慈濟大學《國際交換學生甄選辦法》（歷年學業成績排名達全班前 50%，約 GPA 2.5 / 平均 75 分以上）及美國加州州立大學海峽群島分校（GPA 2.5+）之基本學業門檻"
        ]
        if passes_high_tier:
            tier_notes.append(
                "且達跨國雙聯／三聯學位（TRIM 三聯碩士、英國密德薩斯大學 3+1、美國安德魯斯大學 1+1 MBA、泰國博士雙聯）及教育部《學海飛颺／學海惜珠》之競爭性高階學業基準"
            )
        else:
            tier_notes.append(
                "若欲申請跨國雙聯／三聯學位或競爭日本佛教大學、天理大學、尚絅大學及大陸蘭州大學「學雜費住宿費雙全免」名額，建議同步強化讀書計畫與服務學習訓練時數（占校內海外交流補助學習成效評分 40%）"
            )
        return (
            "pass",
            f"已填報 {summary}；{'；'.join(tier_notes)}。",
        )

    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；未達慈濟大學出國交換學生甄選簡章規定之「歷年學業成績排名達全班前 50%（約平均 75 分或 GPA 2.5 以上）」門檻，建議同時填報全班排名百分比或向全球事務處交流組（分機 1014、11018）確認是否符合特定短期交流或海外實習計畫資格。"
        ),
    )


def tcu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        if (partner_country or "").strip() in {
            "中國大陸",
            "中國",
            "大陸",
            "大陸地區",
            "香港",
            "澳門",
        }:
            return (
                "pass",
                "申請大陸地區姊妹校交換（蘭州大學［學雜費住宿費全免］、南京大學、蘇州大學等）以中文授課為主，免附外語檢定成績（惟可檢附英語或其他專業證明作為校內甄選加分佐證）。",
            )
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依《慈濟大學英語主要檢測參考對照表》、《慈濟大學 CEFR B1（含）級以上或同等語言能力對照表》及出國交換簡章：（1）校內 CEFR B1 基本門檻為 TOEIC 550、TOEFL iBT 42、TOEFL ITP 460、IELTS 4.0、全民英檢 GEPT 中級複試通過；（2）歐美與泰國英語交換門檻：美國加州州立大學海峽群島分校（CSUCI）要求 TOEFL iBT 61 / IELTS 6.0 / DAAD B / Eiken Pre-1、美國堪薩斯州立大學要求 TOEFL iBT 79 / IELTS 6.5（免修英語課）、泰國清邁大學要求 TOEFL iBT 61 / PBT 500 / CBT 173 / IELTS 5.0 / TOEIC 600、瑞典哈爾姆斯塔德大學要求 IELTS 6.5 / TOEFL iBT 90；（3）雙聯與三聯學位門檻：德墨臺 TRIM 三聯碩士與美國安德魯斯大學 1+1 MBA 要求 TOEFL iBT 79–80 / IELTS 6.5、英國倫敦密德薩斯大學 3+1 要求 IELTS 6.0（單科 5.5）/ TOEFL iBT 72；（4）日韓姊妹校（佛教大學、天理大學、尚絅大學、愛知學院大學、釜山外大、東西大學、東國大學）要求 JLPT N2–N4 或 TOPIK 2–3 級；大陸姊妹校（蘭州大學、南京大學、蘇州大學）以中文授課為主。"
            ),
        )
    if test in TCU_ENGLISH_MINIMUMS:
        label, minimum = TCU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達《慈濟大學 CEFR B1（含）級以上語言能力對照表》基礎英語門檻（符合馬來西亞拉曼大學 UTAR、韓國姊妹校英語組及校內海外交流補助基本外語基準）"
        if (
            (test == "toefl" and language_score >= 79)
            or (test == "ielts" and language_score >= 6.5)
            or (test == "toefl_itp" and language_score >= 550)
            or (test == "toeic" and language_score >= 800)
            or (test == "duolingo" and language_score >= 110)
        ):
            tier_note = "達高階英語門檻（TOEFL iBT 79+ / IELTS 6.5+），符合美國堪薩斯州立大學（免修英語加強課直接選修專業課）、德墨臺「跨洲際全球研究三聯碩士（TRIM）」、美國安德魯斯大學「1+1 MBA 雙碩士」、英國倫敦密德薩斯大學「3+1 雙學士」、泰國瑪希敦／納黎萱博士雙聯及全數歐美亞交換姊妹校標準（註：瑞典哈爾姆斯塔德大學若以 iBT 申請要求 90 分或 IELTS 6.5）"
        elif (
            (test == "toefl" and language_score >= 61)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toefl_itp" and language_score >= 500)
            or (test == "toeic" and language_score >= 600)
        ):
            tier_note = "達中堅英語門檻（TOEFL iBT 61+ / ITP 500+ / IELTS 6.0+ / TOEIC 600+），符合美國加州州立大學海峽群島分校（CSUCI，iBT 61 / IELTS 6.0）、泰國清邁大學（iBT 61 / PBT 500 / IELTS 5.0 / TOEIC 600）、泰國法政大學（傳播系英語授課）、泰國納黎萱大學、德國杜伊斯堡-埃森大學與西薩克森應用科學大學，以及英國倫敦密德薩斯大學 3+1 雙學士（IELTS 6.0 單科不低於 5.5 / iBT 72）門檻"
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}慈濟大學出國交換暨雙聯學位英語檢定基準（校內 CEFR B1 最低採計門檻：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 4
        if level in (1, 2):
            tier_note = f"JLPT N{level} 符合慈濟大學全部日本交換姊妹校門檻（含京都佛教大學［日本語文學，學雜費住宿費全免］、奈良天理大學［國際學部，學雜費住宿費全免］、熊本尚絅大學［現代文化學部，學雜費住宿費全免］、名古屋愛知學院大學［日本研究中心］）及教育部學海飛颺日語標準"
        elif level == 3:
            tier_note = "JLPT N3 符合日本天理大學、尚絅大學、愛知學院大學交換門檻並達《慈濟大學 CEFR B1 語言能力對照表》日語基準（若欲申請京都佛教大學日本語文學專業課程，建議達 JLPT N2 以上）"
        elif level == 4:
            tier_note = "JLPT N4 符合日本愛知學院大學（Center for Japanese Studies）及天理大學基礎日語研修門檻（若欲申請佛教大學或尚絅大學專業學部課程，建議提升至 JLPT N3–N2）"
        else:
            tier_note = f"目前為 JLPT N{level}，建議提升至 JLPT N4–N2 以符合日本佛教大學、天理大學、尚絅大學及愛知學院大學之日語交換門檻"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}慈濟大學日本姊妹校交換日語檢定基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 2 <= level <= 6
        if level >= 3:
            tier_note = f"TOPIK {level} 級符合韓國首爾東國大學（Dongguk University）、釜山外國語大學（BUFS）、東西大學（Dongseo University）等全部韓國姊妹校韓語授課組門檻，並達《慈濟大學 CEFR B1 語言能力對照表》韓語基準"
        elif level == 2:
            tier_note = "TOPIK 2 級符合韓國釜山外國語大學、東西大學等姊妹校基本韓語門檻（首爾東國大學韓語專業課程建議 TOPIK 3 級以上，或改以英語檢定申請英語授課課程）"
        else:
            tier_note = f"目前為 TOPIK {level} 級，未達韓國姊妹校韓語授課組一般門檻（TOPIK 2–3 級以上，惟可改以 TOEFL/IELTS/TOEIC 申請英語授課課程）"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}慈濟大學韓國姊妹校交換韓語檢定基準（{tier_note}）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}），請對照《慈濟大學 CEFR B1（含）級以上或同等語言能力對照表》與目標姊妹校簡章確認是否符合要求。",
    )
