from __future__ import annotations

import re

from .university_registry import resolve_university

NQU_OICA_HOME_URL = "https://oica.nqu.edu.tw/"
NQU_INTL_EXCHANGE_LIST_URL = "https://oica.nqu.edu.tw/p/412-1003-1150.php?Lang=zh-tw"
NQU_INTL_STAGE2_POST_URL = "https://oica.nqu.edu.tw/p/406-1003-21011,r902.php?Lang=zh-tw"
NQU_INTL_STAGE1_ADMIT_URL = "https://oica.nqu.edu.tw/p/406-1003-28138,r1150.php?Lang=zh-tw"
NQU_MAINLAND_2027_SPRING_URL = "https://oica.nqu.edu.tw/p/406-1003-31469,r902.php?Lang=zh-tw"
NQU_MAINLAND_2027_ADMIT_URL = "https://oica.nqu.edu.tw/p/406-1003-32428,r902.php?Lang=zh-tw"
NQU_INTL_PARTNERS_URL = "https://oica.nqu.edu.tw/p/404-1003-8171.php?Lang=zh-tw"
NQU_MAINLAND_PARTNERS_URL = "https://oica.nqu.edu.tw/p/404-1003-8510.php?Lang=zh-tw"
NQU_INTL_REGULATIONS_URL = "https://oica.nqu.edu.tw/p/405-1003-7397,c1153.php?Lang=zh-tw"
NQU_INTL_FORMS_URL = "https://oica.nqu.edu.tw/p/412-1003-995.php?Lang=zh-tw"
NQU_XUEHAI_POST_URL = "https://oica.nqu.edu.tw/p/406-1003-29910,r928.php?Lang=zh-tw"
NQU_EXP_MAINLAND_URL = "https://oica.nqu.edu.tw/p/412-1003-1182.php?Lang=zh-tw"
NQU_EXP_INTL_URL = "https://oica.nqu.edu.tw/p/412-1003-1207.php?Lang=zh-tw"
NQU_OUTGOING_GUIDELINES_PDF_URL = "https://oica.nqu.edu.tw/var/file/3/1003/img/735526301.pdf"
NQU_CREDIT_TRANSFER_PDF_URL = "https://teach.nqu.edu.tw/var/file/1/1001/img/419783707.pdf"

NQU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 500.0),
}


def is_nqu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == "nqu":
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立金門大學",
        "金門大學",
        "金大",
        "國立金門技術學院",
        "金門技術學院",
        "nqu",
        "national quemoy university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nqu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立金門大學學生國際交流甄選要點》、《115 學年度第一／二階段國際交換學生簡章》及《2027 春季班赴國內及大陸地區交換學生甄選簡章》規定："
                "（1）國際交換學生計畫：出國前須在校修業滿 4 學期（2 學年）以上之在學學生（即出國時為大三以上，特定姊妹校如日本新潟大學限人文社會學院研究生申請、日本琉球大學限管理學院學生申請），赴國外研修期間應保有本校學籍且不得辦理休學；"
                "（2）赴中國大陸地區交換計畫：本校日間部學生在校修業滿 1 學年（大二以上及碩、博士班；博、碩士生得優先錄取，各姊妹校至多限 1 名博碩士生優先錄取且須附指導教授同意函；廈門大學與福州大學不接受大一及大四學生申請）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in (
            "休學",
            "已畢業",
            "退學",
            "學分班",
            "選修生",
            "進修",
            "在職",
            "大一",
            "一年級",
            "專一",
            "專二",
            "專三",
        )
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立金門大學學生國際交流甄選要點》及大陸地區交換甄選簡章規定，"
                "國際交換出國前須在校修業滿 4 學期（2 學年）以上，赴大陸地區交換須為日間部修業滿 1 學年（大二以上）在學學生（大一新生、進修部／在職專班、休學生、已畢業生及非正式學籍生不得申請）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩、博士班研究生申請赴大陸交換可享每校至多 1 名優先錄取資格並須檢附指導教授同意函；國際交換如日本新潟大學僅限人文社會學院研究生申請）"
        if is_grad
        else (
            "（提醒：學士班學生申請國際交換須於出國前修滿 4 學期［大三以上］，申請赴大陸交換須為日間部修滿 1 學年［大二以上］且廈門大學、福州大學不接受大四生申請）"
        )
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立金門大學國際暨兩岸事務處出國及赴大陸交換學生在學學制規定{grad_note}。"
        ),
    )


def nqu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 70.0
    gpa_min = 2.0
    rank_max = 60.0
    details: list[str] = []
    passes_nqu = False

    if academic_score is not None:
        details.append(f"歷年學業平均成績 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_nqu = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_nqu = True
    if class_rank_percent is not None:
        details.append(f"班（系）排名前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_nqu = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績、GPA 或班（系）排名百分比；依國立金門大學交換甄選簡章規定："
                "（1）國際交換學生計畫：操行成績平均達 80 分（含）以上，且須符合各接待姊妹校 GPA 門檻（泰國農業大學与皇太后大學 GPA 2.00/4.00、阿卜杜拉居爾大學 GPA 2.20/4.00、土耳其 TED 大學與東南密蘇里州立大學及胡志明市理工大學／外語資訊大學 GPA 2.50/4.00、馬來亞大學／夏威夷大學馬諾阿分校／印度尼西亞大學／加查馬達大學／詹伯大學 GPA 3.00/4.00），校內書面審查占 60%（GPA 20%＋語測 20%＋自傳與讀書計畫 10%＋績優證明 5%＋推薦信 5%）＋面試 40%；"
                "（2）赴中國大陸地區交換計畫：學士班歷年學業總成績平均需達 70 分以上，且歷年班、系排名百分比在 60% 以內（兩項條件皆需符合），校內書面審查占 60%（班系排名百分比 30%＋操行成績 10%＋自傳與學習計畫 10%＋推薦信及績優證明 10%）＋實體面試 40%。"
            ),
        )

    if not passes_nqu or (
        academic_score is not None and academic_score < score_min
    ):
        return (
            "fail",
            (
                f"已填報 {summary}；未達國立金門大學出國／赴大陸交換學生計畫基本學業門檻"
                f"（赴大陸交換學士班須同時符合歷年學業總平均 {score_min:g} 分以上且班／系排名前 {rank_max:g}%；國際交換操行成績須達 80 分以上且達姊妹校 GPA {gpa_min:g}–3.00 門檻）。"
            ),
        )

    is_top_tier = (
        (academic_gpa is not None and academic_gpa >= 3.0)
        or (academic_score is not None and academic_score >= 80.0)
    ) and (class_rank_percent is None or class_rank_percent <= 30.0)

    if is_top_tier:
        tier_note = (
            "同時符合金大國際交換高門檻姊妹校（馬來亞大學、夏威夷大學馬諾阿分校、印度尼西亞大學 UI、加查馬達大學 UGM、詹伯大學 GPA 3.00/4.00）、"
            "大陸 985／雙一流名校（廈門大學、四川大學、中國政法大學、中國海洋大學、蘭州大學）及教育部《學海飛颺／學海惜珠》獎學金申請標準"
        )
    elif class_rank_percent is not None and class_rank_percent > 60.0:
        tier_note = (
            "符合部分國際交換姊妹校基本 GPA 門檻，惟班（系）排名超過 60%，未達赴大陸地區交換學士班『平均 70 分以上且班系排名前 60%』雙重門檻"
        )
    else:
        tier_note = (
            "符合赴大陸地區交換（平均 70 分以上且班系排名前 60%）及多數國際交換姊妹校（GPA 2.00–2.50）門檻；建議強化語言檢定（占國際交換審查 20%）與面試表現（占 40%）以提升序位"
        )

    return (
        "pass",
        f"已填報 {summary}；符合國立金門大學交換學生學業審核基準（{tier_note}）。",
    )


def nqu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸", "澳門"} and (
        not test or language_score is None
    ):
        return (
            "pass",
            (
                "申請赴中國大陸地區締約姊妹校（廈門大學、四川大學、中國政法大學、北京交通大學、北京科技大學、東華大學、中國海洋大學、華中師範大學、蘭州大學、福州大學等）或澳門科技大學交換研修，"
                "依簡章規定以中文授課為主，免附外語能力檢定證明。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫有效之語言能力檢定成績。依《國立金門大學 115 學年度第一／二階段國際交換簡章》及《學海飛颺／學海惜珠甄選簡章》規定："
                "（1）國際交換書面審查中「語言測驗成績」占總成績 20%，且檢附之語言能力證明必須為證書日期起算 2 年內有效成績（逾期不予採計）；"
                "（2）英語授課姊妹校多要求 CEFR B1–B2（TOEIC 550–785／TOEFL iBT 61–80／IELTS 5.0–6.0），日本姊妹校（三重大學、琉球大學、新潟大學）要求 JLPT N2–N3，韓國姊妹校（建國大學、誠信女子大學、釜山外國語大學）要求 TOPIK 2–3 級或英語檢定；"
                "（3）申請赴中國大陸地區交換者免附外語檢定證明。"
            ),
        )
    if test in NQU_ENGLISH_MINIMUMS:
        label, minimum = NQU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = (
            "達金大國際交換多數東南亞與亞洲英語授課姊妹校基本門檻（CEFR B1：TOEFL iBT 61 / IELTS 5.0 / TOEIC 550）"
        )
        if (
            (test == "toefl" and language_score >= 80)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "toefl_itp" and language_score >= 550)
        ):
            tier_note = (
                "達高階英語標準（CEFR B2：TOEFL iBT 80+ / IELTS 6.0+ / TOEIC 785+），"
                "符合馬來亞大學（UM）、夏威夷大學馬諾阿分校（UH Manoa）、德國維爾茨堡-施韋因富特科技大學（THWS）、"
                "土耳其阿卜杜拉居爾大學（AGU）、土耳其教育協會大學（TEDU）、印度尼西亞大學（UI）、加查馬達大學（UGM）等全數英語授課姊妹校門檻"
            )
        elif (
            (test == "toefl" and language_score >= 65)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toeic" and language_score >= 600)
            or (test == "toefl_itp" and language_score >= 520)
        ):
            tier_note = (
                "達美國東南密蘇里州立大學（SEMO）、韓國誠信女子大學與建國大學英語學程、泰國農業大學（KU）、皇太后大學（MFU）、"
                "越南胡志明市理工大學（HCMUT）與外語資訊大學（HUFLIT）、印尼巴查查蘭大學等姊妹校英語交換門檻"
            )
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}國立金門大學國際暨兩岸事務處國際交換暨教育部學海計畫英語能力標準"
                f"（基本基準：{label} {minimum:g}，且證書須在 2 年有效期內；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level in (1, 2):
            tier_note = (
                f"達 JLPT N{level} 標準，完全符合日本三重大學、琉球大學、新潟大學、廣島大學等日本姊妹校專業課程交換門檻及教育部學海計畫日語標準"
            )
        elif level == 3:
            tier_note = (
                "達 JLPT N3 標準，符合日本新潟大學（人文社會學院研究生）及日本姊妹校日語研習學程基本基準（修讀三重大學或琉球大學一般學部專業課程建議達 N2 以上）"
            )
        else:
            tier_note = f"JLPT N{level} 未達金大日本姊妹校交換日語能力標準（須達 JLPT N3–N2 以上，且證書須在 2 年有效期內）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立金門大學日本姊妹校交換日語能力標準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 2 <= level <= 6
        if level >= 3:
            tier_note = (
                f"TOPIK {level} 級完全符合韓國建國大學、誠信女子大學、釜山外國語大學等韓國姊妹校韓語授課專業課程交換門檻"
            )
        elif level == 2:
            tier_note = "TOPIK 2 級符合韓國誠信女子大學、建國大學與釜山外國語大學基礎韓語交換門檻"
        else:
            tier_note = "韓國姊妹校要求 TOPIK 2–3 級以上，或改以英語檢定成績（TOEIC 600+／TOEFL iBT 65+／IELTS 5.5+）申請英語授課課程"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立金門大學韓國姊妹校韓語能力標準（{tier_note}）。",
        )
    if test in {"duolingo"}:
        passed = language_score >= 90.0
        return (
            "pass" if passed else "fail",
            f"Duolingo English Test {language_score:g} {'符合' if passed else '未達'}美國東南密蘇里州立大學（SEMO）與夏威夷大學馬諾阿分校等姊妹校英語替代檢定基準（建議達 95 分以上）。",
        )
    if test in {"dele", "delf", "goethe", "testdaf", "tcf", "cambridge", "linguaskill", "gept"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}國立金門大學國際暨兩岸事務處外語能力檢定標準（證書須為 2 年有效期內，德國維爾茨堡-施韋因富特科技大學建議達 CEFR B2）。",
        )
    return (
        "needs_confirmation",
        f"已填報 {language_test}（{language_score:g}），請對照國立金門大學當期《國際交換學生甄選簡章》確認是否符合志願校語言門檻（證書須為 2 年內有效）。",
    )
