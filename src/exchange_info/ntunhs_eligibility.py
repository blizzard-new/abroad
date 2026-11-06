"""National Taipei University of Nursing and Health Sciences (國立臺北護理健康大學, NTUNHS) outbound exchange & dual-degree eligibility checks.

Official rule sources:
- 國立臺北護理健康大學學生出國期間有關學業及學籍處理要點:
  https://reg-acad.ntunhs.edu.tw/var/file/39/1039/img/39/412506617.pdf
- 國立臺北護理健康大學學生抵免學分處理辦法:
  https://teaching-acad.ntunhs.edu.tw/var/file/40/1040/img/1423/B12-R013-20260624.pdf
- 國立臺北護理健康大學學則:
  https://reg-acad.ntunhs.edu.tw/var/file/39/1039/img/39/252256746.pdf
- 國立臺北護理健康大學研究發展處國際暨兩岸教育中心「雙聯學制／海外長短期交換／教育部學海系列獎學金」專區:
  https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3252.php?Lang=zh-tw
  https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3251.php?Lang=zh-tw
  https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3253.php?Lang=zh-tw
  https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3250.php?Lang=zh-tw
"""

from __future__ import annotations

import re

from .university_registry import NTUNHS, resolve_university

NTUNHS_ICSED_HOME_URL = "https://icsed-rnd.ntunhs.edu.tw/"
NTUNHS_DUAL_DEGREE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3252.php?Lang=zh-tw"
NTUNHS_EXCHANGE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3251.php?Lang=zh-tw"
NTUNHS_XUEHAI_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3253.php?Lang=zh-tw"
NTUNHS_SISTER_SCHOOLS_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3250.php?Lang=zh-tw"
NTUNHS_OUTBOUND_STATUS_RULES_PDF = "https://reg-acad.ntunhs.edu.tw/var/file/39/1039/img/39/412506617.pdf"
NTUNHS_CREDIT_TRANSFER_RULES_PDF = "https://teaching-acad.ntunhs.edu.tw/var/file/40/1040/img/1423/B12-R013-20260624.pdf"

NTUNHS_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 5.5),
    "toefl_itp": ("TOEFL ITP/PBT", 500.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 95.0),
}


def is_ntunhs(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTUNHS.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "ntunhs",
        "國北護",
        "北護",
        "北護大",
        "臺北護理健康大學",
        "台北護理健康大學",
        "國立臺北護理健康大學",
        "國立台北護理健康大學",
        "national taipei university of nursing and health sciences",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究", "master", "phd", "doctoral"))


def ntunhs_degree_check(
    degree_level: str | None, current_year: str | int | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = str(current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立臺北護理健康大學學生出國期間有關學業及學籍處理要點》及國際暨兩岸教育中心交換與雙聯簡章：申請對象為具本校日間部正式學籍之四技（2～4年級）、二技、學士後護理系、碩士班及博士班在學學生（不含在職專班、休學或已畢業學生；出國交換期間須維持北護在學學籍並經系所同意）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學", "已畢業")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依國立臺北護理健康大學國際暨兩岸教育中心甄選簡章及教育部學海系列規定，在職專班、學分班、休學或已畢業學生不在校級出國交換與學海獎學金選送範圍內。"
            ),
        )
    is_grad = _is_graduate(degree)
    is_two_year_tech = "二技" in degree or "學士後" in degree
    if (
        not is_grad
        and not is_two_year_tech
        and year in {"1", "大一", "四技一", "一年級", "一年級上學期"}
    ):
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；依國立臺北護理健康大學學期交換與教育部學海系列甄選規定，四技（大學部）申請人須於本校修業滿一學期或一學年以上並具歷年成績單，四技一年級新生可先參與校內國際學伴（International Buddy）及暑期短期海外研習，於升二年級起申請學期交換或雙聯學位。"
            ),
        )
    grad_note = (
        "（提醒：碩博士班學生可申請美國奧本大學 Auburn University 護理碩博雙聯、澳洲昆士蘭大學 UQ 護理／聽力學／社工碩士雙聯、日本名古屋市立大學與捷克奧斯特拉瓦大學等學期交換，出國前須經指導教授與系所主任同意）"
        if is_grad
        else "（提醒：四技／二技／學士後護理系學生出國交換或修讀澳洲 UQ、QUT、Deakin、WAI 及英國 UWE 雙聯學位前，務必與系所確認專業必修課與臨床實習排程，並維持北護在學註冊學籍）"
    )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立臺北護理健康大學出國交換、跨國雙聯學位與海外實習之在學身分規定{grad_note}。",
    )


def ntunhs_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 70.0
    gpa_min = 2.0
    details: list[str] = []
    passes_general = False
    passes_priority = False

    if academic_score is not None:
        details.append(f"學業平均 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_general = True
        if academic_score >= 80.0:
            passes_priority = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_general = True
        if academic_gpa >= 3.0:
            passes_priority = True
    if class_rank_percent is not None:
        details.append(f"班排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            passes_general = True
        if class_rank_percent <= 30.0:
            passes_priority = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績、GPA 或班排名百分比；依國立臺北護理健康大學國際暨兩岸教育中心甄選簡章：（1）學期交換與短期海外研習：在校歷年平均須達 GPA 2.0（百分制約 70 分）以上，操行成績 80 分以上且無懲戒紀錄；（2）教育部《學海飛颺／學海惜珠》獎學金與英美澳跨國雙聯學位（澳洲昆士蘭大學 UQ、昆士蘭科技大學 QUT、迪肯大學 Deakin、英國西英格蘭大學 UWE、美國奧本大學 Auburn）：以班排名百分比前 50%（雙聯建議 GPA 2.75–3.0 / 75–80 分以上）優先推薦。"
            ),
        )

    if passes_general:
        tier_note = (
            "同時達到歐美紐澳跨國雙聯學位（澳洲 UQ、QUT、Deakin、英國 UWE、美國 Auburn、紐西蘭 Massey）及教育部《學海飛颺／學海惜珠》獎學金優先推薦門檻（班排前 50%／GPA 3.0／80 分以上）"
            if passes_priority
            else "符合國立臺北護理健康大學一般學期交換（捷克奧斯特拉瓦大學、日本名古屋市立大學、縣立廣島大學、韓國大邱保健大學、立陶宛 KVK、澳洲 WAI／TAFE）基本學業門檻（GPA 2.0／70 分以上）；若申請教育部學海飛颺獎學金或雙聯學位，以班排前 50% 及操行 80 分以上優先"
        )
        return (
            "pass",
            f"已填報 {summary}；符合國立臺北護理健康大學出國交換甄選學業標準（{tier_note}）。",
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達國立臺北護理健康大學出國交換與雙聯學位基本學業門檻（在校平均成績須達 70 分 / GPA 2.0 以上或班排前 50%，且操行成績達 80 分以上無懲戒紀錄）。"
        ),
    )


def ntunhs_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸", "中國", "大陸地區"} and (
        not test or language_score is None
    ):
        return (
            "pass",
            (
                "申請赴大陸地區姊妹校（中南大學、廣州醫科大學、濱州醫學院、廈門醫學院、宜春學院、山東協和學院等）交流研修以中文授課為主，免附外語能力檢定證明。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依國立臺北護理健康大學雙聯學制與交換簡章各校門檻：（1）雙聯學位：澳洲昆士蘭大學（UQ 護理學士／碩士、聽力學碩士、社工碩士）要求 IELTS 7.0（各單科不低於 7.0）或 TOEFL iBT 100；美國奧本大學（Auburn 護理碩博）、澳洲昆士蘭科技大學（QUT 資管 2+2）、迪肯大學（Deakin 健管 MBA 3.5+1.5）、英國西英格蘭大學（UWE 護理雙聯）要求 IELTS 6.5（UWE 資管 3+1 與澳洲墨爾本威廉安格利斯學院 WAI 要求 IELTS 6.0）；（2）學期交換：紐西蘭梅西大學（Massey）要求 IELTS 6.0–6.5；捷克奧斯特拉瓦大學（University of Ostrava）與立陶宛克萊佩達市立大學（KVK）要求英語 CEFR B1–B2（TOEIC 550–785 / IELTS 5.5–6.0 / TOEFL iBT 61–79）；日本名古屋市立大學要求 JLPT N1 或英語 CEFR B2，日本縣立廣島大學、山形縣立保健醫療大學、沖繩縣立看護大學、佐久大學要求具備基礎至中級日語（JLPT N2–N3）或英語溝通能力；韓國大邱保健大學與春海保健大學要求基礎韓語（TOPIK 2–3 級）或英語溝通能力。"
            ),
        )
    if test in NTUNHS_ENGLISH_MINIMUMS:
        label, minimum = NTUNHS_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達國北護歐洲（捷克奧斯特拉瓦大學、立陶宛 KVK）與亞太英語授課交換基本門檻（TOEIC 550 / IELTS 5.5 / TOEFL iBT 61 / ITP 500）"
        if (test == "ielts" and language_score >= 7.0) or (
            test == "toefl" and language_score >= 100
        ):
            tier_note = "達澳洲昆士蘭大學（UQ 護理、聽力學、社工雙聯 IELTS 7.0 / TOEFL iBT 100）及全校所有英美紐澳歐雙聯與交換計畫最高英語門檻"
        elif (
            (test == "ielts" and language_score >= 6.5)
            or (test == "toefl" and language_score >= 79)
            or (test == "toeic" and language_score >= 785)
            or (test == "duolingo" and language_score >= 110)
        ):
            tier_note = "符合美國奧本大學（Auburn）、英國西英格蘭大學（UWE）、澳洲昆士蘭科技大學（QUT）、迪肯大學（Deakin）、紐西蘭梅西大學（Massey）及歐洲 CEFR B2 交換門檻（惟澳洲昆士蘭大學 UQ 護理／聽力／社工雙聯要求 IELTS 7.0 各科 7.0）"
        elif (test == "ielts" and language_score >= 6.0) or (
            test == "toefl" and language_score >= 70
        ):
            tier_note = "符合英國西英格蘭大學資管系 3+1 雙聯（IELTS 6.0）、澳洲墨爾本威廉安格利斯學院 WAI（IELTS 6.0）、紐西蘭梅西大學 Study Abroad 及捷克奧斯特拉瓦大學、立陶宛 KVK 交換門檻"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺北護理健康大學出國交換與雙聯學位英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。",
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level == 1:
            tier_note = "JLPT N1 符合日本名古屋市立大學（Nagoya City University）、縣立廣島大學、山形縣立保健醫療大學、沖繩縣立看護大學、東京都立大學、佐久大學等全部日本合作校最高日語門檻"
        elif level in (2, 3):
            tier_note = f"JLPT N{level} 符合日本縣立廣島大學、山形縣立保健醫療大學、沖繩縣立看護大學、佐久大學等交換及短期研修日語門檻（名古屋市立大學日語組要求 N1，或改以英語 CEFR B2 申請）"
        else:
            tier_note = "國立臺北護理健康大學日本學期交換姊妹校建議具備 JLPT N3～N1（名古屋市立大學要求 N1 或英語 B2）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立臺北護理健康大學日本姊妹校交換日語檢定基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = level >= 2
        tier_note = (
            f"TOPIK {level} 級符合韓國大邱保健大學（Daegu Health College）、首爾女子護理大學、春海保健大學及高麗大學交換與研修韓語門檻"
            if passed
            else "申請韓國姊妹校韓語授課課程建議具備 TOPIK 2 級以上（或以英語檢定成績申請英語授課計畫）"
        )
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立臺北護理健康大學韓國姊妹校交換韓語基準（{tier_note}）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立臺北護理健康大學國際暨兩岸教育中心簡章確認目標姊妹校語言門檻。",
    )
