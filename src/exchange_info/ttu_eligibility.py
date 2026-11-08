"""Tatung University (大同大學, TTU) outbound exchange & dual-degree eligibility checks.

Official rule sources:
- 大同大學交換學生計畫實施辦法 (113.10.22 行政會議修正通過, rid=1049):
  https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1049
- 大同大學與境外大學校院辦理雙聯學制實施辦法 (115.01.19 教務會議修正通過, rid=1043):
  https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1043
- 大同大學校友捐助國際交流專案獎助學金實施辦法 (115.03.12 行政會議通過, rid=1124):
  https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1124
- 大同大學鼓勵學生出國交換研修助學金實施辦法 (113.10.22 修正, rid=1045):
  https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1045
- 大同大學學生暑期赴境外學校交流助學金實施辦法 (113.10.22 修正, rid=1047):
  https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1047
- 大同大學學生暑期赴境外語言學習助學金實施辦法 (115.05.28 行政會議通過, rid=1129):
  https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1129
- 大同大學國際暨兩岸事務處 2026 秋季／2027 春季姊妹校交換計畫與雙聯學位申請第一波&第二波公告:
  https://oia.ttu.edu.tw/p/406-1076-44122,r11.php?Lang=zh-tw
  https://oia.ttu.edu.tw/p/406-1076-41452,r11.php?Lang=zh-tw
"""

from __future__ import annotations

import re

from .university_registry import TTU, resolve_university

TTU_OIA_HOME_URL = "https://oia.ttu.edu.tw/"
TTU_SISTER_SCHOOLS_URL = "https://ao.ttu.edu.tw/p/412-1073-2438.php"
TTU_2027_SPRING_EXCHANGE_URL = "https://oia.ttu.edu.tw/p/406-1076-44122,r11.php?Lang=zh-tw"
TTU_2026_FALL_EXCHANGE_URL = "https://oia.ttu.edu.tw/p/406-1076-41452,r11.php?Lang=zh-tw"
TTU_XUEHAI_URL = "https://oia.ttu.edu.tw/p/406-1076-41325,r11.php?Lang=zh-tw"
TTU_EXCHANGE_REGULATION_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1049"
TTU_DUAL_DEGREE_REGULATION_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1043"

TTU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 5.5),
    "toefl_itp": ("TOEFL ITP/PBT", 500.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 95.0),
}


def is_ttu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == TTU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "ttu",
        "大同",
        "大同大學",
        "tatung",
        "tatung university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究", "master", "phd", "doctoral"))


def ttu_degree_check(
    degree_level: str | None, current_year: str | int | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = str(current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《大同大學交換學生計畫實施辦法》第 3 條及《大同大學與境外大學校院辦理雙聯學制實施辦法》：申請對象為在本校大學部或研究所至少就讀一年以上之在學學生（大學部二年級以上、碩博士班；不含在職專班、休學或已畢業學生；陸生、僑生及外籍生不得交換至其原居住國，且領取臺灣獎學金之外籍生不得申請）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學", "已畢業")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依大同大學國際暨兩岸事務處甄選公告及教育部學海系列簡章規定，在職專班、學分班、休學或已畢業學生不在校級出國交換與學海獎學金選送範圍內。"
            ),
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"1", "大一", "一年級", "一年級上學期"}:
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；依《大同大學交換學生計畫實施辦法》第 3 條規定，申請交換學生須在本校大學部或研究所至少就讀一年以上；大一新生可先申請《大同大學學生暑期赴境外語言學習助學金》（最高補助新臺幣 5 萬元）或暑期赴境外學校交流助學金，於升大二起申請學期交換或跨國雙聯學位。"
            ),
        )
    grad_note = (
        "（提醒：碩士班學生可申請美國愛荷華州立大學 ISU、韋恩州立大學 WSU、拉瑪大學 Lamar、英國密德薩斯大學 MDXU、布魯內爾大學 BUL、德國斯圖加特應用科技大學 HFT Stuttgart［事經／資經／資工 1+1 雙碩士］、法國 ESIEE-Amiens、澳洲紐卡索大學 1+1 雙碩士及日歐亞學期交換；注意日本大阪學院大學與武藏野大學僅開放學士班交換）"
        if is_grad
        else "（提醒：大學部學生可申請日韓歐美亞學期交換，以及英國密德薩斯大學 MDXU 3+1 雙學士［事經／資經／工設／媒設］、3+1.5 學碩雙聯［應外系］、英國布魯內爾大學 BUL 4+1 學碩雙聯及美國愛荷華州立大學 ISU 3.5+1.5 學碩雙聯［限大四生申請四下赴美］）"
    )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合大同大學出國交換與跨國雙聯學位之在學身分規定{grad_note}。",
    )


def ttu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    is_grad = _is_graduate(degree_level)
    score_min = 75.0
    brunel_score_min = 70.0
    gpa_min = 3.0
    details: list[str] = []
    passes_standard = False
    passes_brunel = False
    passes_scholarship = False

    if academic_score is not None:
        details.append(f"學業平均 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_standard = True
        if academic_score >= brunel_score_min:
            passes_brunel = True
        if (is_grad and academic_score >= 80.0) or (not is_grad and academic_score >= 78.0):
            passes_scholarship = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_standard = True
            passes_brunel = True
        if academic_gpa >= 3.3:
            passes_scholarship = True
    if class_rank_percent is not None:
        details.append(f"班排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            passes_standard = True
            passes_brunel = True
            passes_scholarship = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績、GPA 或班排名百分比；依《大同大學交換學生計畫實施辦法》第 3 條及國際暨兩岸事務處公告：（1）學期交換與跨國雙聯學位：在校歷年總平均成績須達 GPA 3.0（百分制約 75 分）以上（英國布魯內爾大學 BUL 1+1／4+1 雙聯為歷年總平均 70 分以上；美國愛荷華州立大學 ISU 雙聯 GPA 達 3.5 以上可免 GRE）；（2）教育部《學海飛颺／學海惜珠》及《大同大學校友捐助國際交流專案獎助學金》：學士班前一學期全班排名前 50%、碩博士生前一學期平均 80 分以上。"
            ),
        )

    if passes_standard:
        tier_note = (
            "同時符合教育部《學海飛颺／學海惜珠》與《大同大學校友捐助國際交流專案獎助學金》學業門檻（學士班班排前 50%／碩博士班 80 分以上）"
            if passes_scholarship
            else "符合大同大學校級交換與跨國雙聯學位標準學業門檻（GPA 3.0／75 分以上）；若申請學海飛颺或校友捐助國際交流獎助學金，學士班須前一學期全班排名前 50%、碩博士生須前一學期平均 80 分以上"
        )
        return (
            "pass",
            f"已填報 {summary}；符合大同大學出國交換與雙聯學位甄選學業標準（{tier_note}）。",
        )

    if passes_brunel:
        return (
            "pass",
            (
                f"已填報 {summary}；符合英國布魯內爾大學（Brunel University London）1+1／4+1 雙聯學位學業門檻（歷年總平均 70 分以上），惟一般校級交換與其他雙聯計畫原則上要求英文歷年成績單達 GPA 3.0（約 75 分）以上。"
            ),
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達大同大學出國交換與雙聯學位基本學業門檻（一般交換與雙聯須達 GPA 3.0／約 75 分以上，英國布魯內爾大學雙聯須達 70 分以上）。"
        ),
    )


def ttu_language_check(
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
                "申請赴大陸地區姊妹校（哈爾濱工業大學、大連理工大學、江南大學、中國傳媒大學、中國石油大學、華中農業大學、廣西大學、寧波大學、福建師範大學、濟南大學等）交換以中文授課為主，免附外語檢定證明（惟請注意華僑大學、常熟理工學院、東北電力大學之學分無法於大同大學辦理抵免）。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依大同大學交換與雙聯公告及學海簡章門檻：（1）教育部學海飛颺／惜珠與校友捐助獎學金最低語檢門檻：英語系國家 TOEIC 650 以上、非英語系歐盟國家（德／法／西／荷／奧／芬）TOEIC 600 以上、非英語系亞洲國家（韓／泰／越／印／菲）TOEIC 550 以上、日本 JLPT N4 或 TOEIC 550 以上；（2）歐美澳雙聯學位：德國斯圖加特應用科技大學（資工雙聯 TOEFL iBT 85、經營雙聯 TOEFL iBT 80 / IELTS 6.0）、澳洲紐卡索大學（TOEFL iBT 80 / IELTS 6.5 單科 6.0）、美國愛荷華州立大學與韋恩州立大學（TOEFL iBT 79 / IELTS 6.5）、英國布魯內爾大學（TOEFL iBT 77 / IELTS 6.0）、美國拉瑪大學（TOEFL iBT 71 / IELTS 6.5）、英國密德薩斯大學（3+1 雙學士 IELTS 6.0、1+1／3+1.5 碩士雙聯 IELTS 6.5）；（3）日本交換：千葉大學、京都工藝纖維大學、大阪工業大學、熊本大學、廣島經濟大學要求 JLPT N2 或英語 CEFR B2（TOEIC 750–780 / TOEFL iBT 61–72 / IELTS 5.5–6.0），武藏野大學語言留學要求 JLPT N5–N2、學科留學要求 JLPT N1 或英語 B2。"
            ),
        )
    if test in TTU_ENGLISH_MINIMUMS:
        label, minimum = TTU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達大同大學亞洲地區交換與德國德根道夫應用科技學院（DIT TOEIC 550 / CEFR B1）及學海亞洲地區獎學金基本門檻（TOEIC 550 / IELTS 5.5 / TOEFL iBT 61 / ITP 500）"
        if (
            (test == "toefl" and language_score >= 85)
            or (test == "ielts" and language_score >= 6.5)
            or (test == "toeic" and language_score >= 850)
        ):
            tier_note = "達德國斯圖加特應用科技大學資工雙聯（TOEFL iBT 85）、澳洲紐卡索大學、美國愛荷華州立大學（ISU）、韋恩州立大學（WSU）、拉瑪大學（Lamar）、英國密德薩斯大學（MDXU 1+1／3+1.5）等全校最高雙聯與歐美交換門檻"
        elif (
            (test == "toefl" and language_score >= 79)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 780)
        ):
            tier_note = "符合德國斯圖加特應用科技大學（HFT Stuttgart 經營雙聯與交換 iBT 80 / IELTS 6.0）、德國紐倫堡歐姆應科大（iBT 80）、德國 DHBW Heidenheim、荷蘭方提斯應科大（Fontys）、奧地利上奧地利應科大、法國貢比涅技術大學（UTC）、英國布魯內爾大學（BUL）、密德薩斯大學（3+1 雙學士）及泰國朱拉隆功大學交換門檻"
        elif (
            (test == "toefl" and language_score >= 61)
            or (test == "toeic" and language_score >= 650)
        ):
            tier_note = "符合教育部學海飛颺英語系／歐盟國家獎學金門檻（TOEIC 650 / 600）、美國內華達大學拉斯維加斯分校（UNLV）、芬蘭 XAMK 應科大、日本熊本大學與武藏野大學英語授課交換門檻"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}大同大學出國交換與雙聯學位英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。",
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 5
        if level == 1:
            tier_note = "JLPT N1 符合日本武藏野大學學科留學、千葉大學、京都工藝纖維大學、大阪工業大學、熊本大學、廣島經濟大學、東京都市大學、大阪學院大學等全部日本合作校最高日語門檻"
        elif level == 2:
            tier_note = "JLPT N2 符合日本千葉大學、京都工藝纖維大學（KIT）、大阪工業大學（OIT）、熊本大學、廣島經濟大學專業課程及武藏野大學語言留學日語門檻"
        elif level in (3, 4, 5):
            tier_note = f"JLPT N{level} 符合日本武藏野大學語言留學（N5–N2）、大阪學院大學及教育部學海飛颺日本地區獎學金門檻（N4 以上）；若申請千葉大學、京都工藝纖維大學、大阪工業大學或熊本大學日語學程則須達 N2（或改以英語 CEFR B2 成績申請）"
        else:
            tier_note = "大同大學日本交換姊妹校建議具備 JLPT N5～N1（專業修課多要求 N2 以上）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}大同大學日本姊妹校交換日語檢定基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = level >= 2
        tier_note = (
            f"TOPIK {level} 級符合韓國中央大學（Chung-Ang University）、亞洲大學（Ajou University）、梨花女子大學等韓國姊妹校交換參考門檻"
            if passed
            else "申請韓國姊妹校建議具備 TOPIK 2 級以上或英語 TOEIC 550–650 以上"
        )
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}大同大學韓國姊妹校交換韓語基準（{tier_note}）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照大同大學國際暨兩岸事務處最新交換與雙聯公告確認目標姊妹校語言門檻（須為申請截止日前三年內之檢定成績）。",
    )
