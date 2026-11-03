"""Kainan University (開南大學, KNU) outbound exchange & dual-degree eligibility checks.

Official rule sources:
- 開南大學與境外大學校院辦理跨國雙學位制實施辦法:
  https://knuoica.knu.edu.tw/var/file/4/1004/img/307/582461487.pdf
- 開南大學選派優秀學生赴國外研修獎助學金執行要點:
  https://knuoica.knu.edu.tw/var/file/4/1004/img/307/368304457.pdf
- 開南大學國際及兩岸事務處「出國交換留學／雙聯學位／大陸交換」各梯次甄選簡章與表單專區:
  https://knuoica.knu.edu.tw/p/406-1004-59525,r30.php?Lang=zh-tw
  https://knuoica.knu.edu.tw/p/406-1004-59716,r30.php?Lang=zh-tw
  https://knuoica.knu.edu.tw/p/406-1004-59719,r30.php?Lang=zh-tw
  https://knuoica.knu.edu.tw/p/406-1004-59718,r30.php?Lang=zh-tw
"""

from __future__ import annotations

import re

from .university_registry import KNU, resolve_university

KNU_OICA_HOME_URL = "https://knuoica.knu.edu.tw/"
KNU_DUAL_DEGREE_URL = "https://knuoica.knu.edu.tw/p/406-1004-59525,r30.php?Lang=zh-tw"
KNU_JAPAN_EXCHANGE_URL = "https://knuoica.knu.edu.tw/p/406-1004-59716,r30.php?Lang=zh-tw"
KNU_OVERSEAS_EXCHANGE_URL = "https://knuoica.knu.edu.tw/p/406-1004-59719,r30.php?Lang=zh-tw"
KNU_MAINLAND_EXCHANGE_URL = "https://knuoica.knu.edu.tw/p/406-1004-59718,r30.php?Lang=zh-tw"
KNU_SCHOLARSHIP_URL = "https://knuoica.knu.edu.tw/p/406-1004-59515,r30.php?Lang=zh-tw"
KNU_PARTNER_LIST_URL = "https://www.knu.edu.tw/p/404-1000-46730.php?Lang=zh-tw"

KNU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 4.5),
    "toefl_itp": ("TOEFL ITP/PBT", 500.0),
    "toeic": ("TOEIC", 500.0),
    "duolingo": ("Duolingo English Test", 90.0),
}


def is_knu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == KNU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "knu",
        "開南大學",
        "開南",
        "kainan university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究", "master", "phd", "doctoral"))


def knu_degree_check(
    degree_level: str | None, current_year: str | int | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = str(current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依開南大學《與境外大學校院辦理跨國雙學位制實施辦法》、《選派優秀學生赴國外研修獎助學金執行要點》及出國交換留學甄選簡章：申請對象為開南大學日間部及進修學士班大學部 1～3 年級、碩士班 1 年級在學學生（轉學生須於開南就讀滿一學年以上；不含碩士在職專班及應屆畢業生；修讀 2+2 雙聯學位須於本校修滿 4 學期及 64 學分）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依開南大學出國交換留學與跨國雙聯學位甄選簡章規定，碩士在職專班、休學或不具正式一般生學籍者不在校級交換與教育部學海系列獎助學金申請範圍內。"
            ),
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"4", "大四", "大四上", "大四下", "四年級", "四年級上學期", "四年級下學期", "應屆畢業"}:
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；開南大學一般出國交換申請對象為大學部 1～3 年級及碩士班 1 年級在學學生（應屆畢業生原則上不得申請，惟申請美國密蘇里科技大學 3+1.5 學碩雙聯、義大利佛羅倫斯美國大學 AUF 3+1 雙聯或辦理延畢交換者依雙聯簡章辦理）。"
            ),
        )
    if is_grad and year in {"2", "3", "4", "碩二", "碩三", "碩四", "二年級", "三年級"}:
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；開南大學研究所出國交換申請對象以碩士班 1 年級在學學生為原則，碩二以上學生須確認出國期間仍保有本校在學學籍並經指導教授及系所同意。"
            ),
        )
    grad_note = (
        "（提醒：碩士班學生申請須檢附專題研究計畫，並可申請密蘇里科技大學 M.S. in Economics and Innovation 等合作計畫）"
        if is_grad
        else "（提醒：大學部 1～3 年級可申請日本 42 校、歐美亞太及大陸 12 校學期／學年交換；轉學生須於開南就讀滿一學年；申請日本國立富山大學 2+2、札幌國際大學 2+2、美國威斯康辛河瀑分校 2+2 或義大利 AUF 2+2 雙聯學位者，出國前須於開南修滿 4 學期及 64 學分）"
    )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合開南大學出國交換留學與跨國雙聯學位之在學學籍與年級規定{grad_note}。",
    )


def knu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 75.0
    gpa_min = 2.75
    details: list[str] = []
    passes_general = False
    passes_dual_and_xuehai = False
    passes_auf = False

    if academic_score is not None:
        details.append(f"學業平均 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_general = True
            passes_auf = True
        elif academic_score >= 70.0:
            passes_auf = True
        if academic_score >= 80.0:
            passes_dual_and_xuehai = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_general = True
            passes_auf = True
        elif academic_gpa >= 2.5:
            passes_auf = True
        if academic_gpa >= 3.0:
            passes_dual_and_xuehai = True
    if class_rank_percent is not None:
        details.append(f"班排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= 30.0:
            passes_general = True
            passes_dual_and_xuehai = True
            passes_auf = True
        elif class_rank_percent <= 50.0 and academic_score is None and academic_gpa is None:
            passes_general = True
            passes_auf = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績、GPA 或班排名百分比；依開南大學出國交換簡章與《與境外大學校院辦理跨國雙學位制實施辦法》：（1）一般海外、日本及大陸交換：歷年每學期學業平均成績須達 75 分（GPA 2.75）以上；（2）跨國雙聯學位（日本國立富山大學 2+2、札幌國際大學 2+2、美國威斯康辛大學河瀑分校 2+2）與教育部《學海飛颺／學海惜珠》及《開南大學選派優秀學生赴國外研修獎助學金》：歷年學業平均成績須達 80 分（GPA 3.0）以上且操行成績平均達 82 分以上；（3）義大利佛羅倫斯美國大學（AUF 2+2／3+1 雙聯）學業門檻為 GPA 2.5（約 70 分）以上。"
            ),
        )

    if passes_general:
        tier_notes: list[str] = []
        if passes_dual_and_xuehai:
            tier_notes.append(
                "同時達到日本國立富山大學 2+2（免繳日方學費）、札幌國際大學 2+2、美國威斯康辛河瀑分校 2+2 雙聯學位，以及教育部《學海飛颺／學海惜珠》與《開南大學選派優秀學生赴國外研修獎助學金》（歷年平均 80 分 / GPA 3.0 以上，另須操行 82 分以上）最高學業門檻"
            )
        else:
            tier_notes.append(
                "符合開南大學一般海外、日本、大陸交換（歷年平均 75 分 / GPA 2.75 以上）及義大利佛羅倫斯美國大學 AUF 雙聯學位（GPA 2.5）門檻；惟申請富山大學、札幌國際大學、威斯康辛河瀑分校雙聯學位或教育部學海系列獎學金須達歷年平均 80 分（GPA 3.0）以上"
            )
        return (
            "pass",
            f"已填報 {summary}；符合開南大學出國交換甄選學業標準（{'；'.join(tier_notes)}）。",
        )

    if passes_auf:
        return (
            "fail" if (academic_score is not None and academic_score < 75.0) else "needs_confirmation",
            (
                f"已填報 {summary}；雖達義大利佛羅倫斯美國大學 AUF 雙聯學位（GPA 2.5）門檻，但未達開南大學一般海外、日本與大陸交換基本門檻（歷年每學期學業平均 75 分 / GPA 2.75 以上），亦未達富山大學等雙聯及學海獎學金門檻（80 分 / GPA 3.0 以上）。"
            ),
        )

    return (
        "fail" if (academic_score is not None and academic_score < 75.0) else "needs_confirmation",
        (
            f"已填報 {summary}；依開南大學出國交換留學甄選簡章規定，申請人歷年每學期學業平均成績須達 75 分（GPA 2.75）以上，雙聯學位與教育部學海系列獎學金須達 80 分（GPA 3.0）以上且操行成績達 82 分以上。"
        ),
    )


def knu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸", "中國", "大陸地區"} and (not test or language_score is None):
        return (
            "pass",
            (
                "申請赴大陸地區 12 所姊妹校（南京大學、北京交通大學、大連理工大學、廣州美術學院、西北政法大學、福州大學等）交換以中文授課為主，免附英／日／韓外語能力檢定證明（外籍生非母語為中文者須具 TOCFL 華語文能力測驗證明）。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依開南大學國際及兩岸事務處出國交換與雙聯學位簡章各組門檻：（1）英語組：海外歐美亞太交換與義大利佛羅倫斯美國大學 AUF 雙聯要求 TOEIC 500 / IELTS 4.5 / TOEFL iBT 61 / TOEFL ITP 500 以上；日本全英語授課交換（金澤工業大學、東京國際大學、關西國際大學、日本經濟大學等）要求 TOEIC 600 / IELTS 5.0 / TOEFL iBT 61 以上；美國威斯康辛大學河瀑分校 2+2 雙聯要求 TOEFL iBT 61 / IELTS 5.5 / Duolingo 95；美國密蘇里科技大學 3+1.5 學碩雙聯要求 TOEFL iBT 80 / IELTS 6.5 / Duolingo 115；日本公立秋田國際教養大學（AIU）要求 TOEIC 785 / TOEFL iBT 71 / IELTS 6.0；（2）日語組：島根大學、德島大學、愛媛大學、弘前大學、山口大學、名櫻大學、神戶國際大學、星城大學要求 JLPT N3 以上；奈良女子大學、東京海洋大學、山形大學、香川大學、琉球大學、北九州市立大學、尾道市立大學、公立小松大學、長野大學、青山學院大學、法政大學、明治學院大學、亞細亞大學及札幌國際大學雙聯要求 JLPT N2 以上；國立御茶水女子大學及國立富山大學（交換與 2+2 免日方學費雙聯）要求 JLPT N1；（3）韓語組：韓國中央大學、漢陽大學 ERICA、仁荷大學、明知大學、德成女子大學、韓南大學、釜山外國語大學、蔚山大學要求 TOPIK 3 級（或英語組 TOEIC 500 / IELTS 4.0～4.5）。"
            ),
        )
    if test in KNU_ENGLISH_MINIMUMS:
        label, minimum = KNU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達開南大學海外歐美亞太英語組及義大利 AUF 雙聯基礎門檻（TOEIC 500 / IELTS 4.5 / TOEFL iBT 61 / ITP 500）"
        if (
            (test == "toefl" and language_score >= 80)
            or (test == "ielts" and language_score >= 6.5)
            or (test == "toeic" and language_score >= 800)
            or (test == "duolingo" and language_score >= 115)
        ):
            tier_note = "達美國密蘇里科技大學 3+1.5 學碩雙聯（iBT 80 / IELTS 6.5）、日本秋田國際教養大學 AIU（iBT 71 / IELTS 6.0 / TOEIC 785）、歐洲維也納應用科大／華沙經濟大學／盧布爾雅那大學／維爾紐斯大學及全部英語授課姊妹校最高門檻"
        elif (
            (test == "toefl" and language_score >= 61)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toefl_itp" and language_score >= 500)
            or (test == "toeic" and language_score >= 600)
            or (test == "duolingo" and language_score >= 95)
        ):
            tier_note = "符合日本全英語授課姊妹校（TOEIC 600 / IELTS 5.0 / iBT 61）、美國威斯康辛大學河瀑分校 2+2 雙聯（iBT 61 / IELTS 5.5）、歐洲與韓國英語授課交換門檻（惟日本秋田國際教養大學 AIU 需 TOEIC 785 / iBT 71 / IELTS 6.0，美國密蘇里科技大學碩士雙聯需 iBT 80 / IELTS 6.5）"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}開南大學出國交換與雙聯學位英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。",
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level == 1:
            tier_note = "JLPT N1 符合日本國立御茶水女子大學、國立富山大學（交換及 2+2 免日方學費雙學士雙聯）及全部 42 所日本國公私立姊妹校最高日語門檻"
        elif level == 2:
            tier_note = "JLPT N2 符合日本奈良女子大學、東京海洋大學、山形大學、香川大學、琉球大學、北九州市立大學、尾道市立大學、公立小松大學、長野大學、青山學院大學、法政大學、明治學院大學、亞細亞大學及札幌國際大學 2+2 雙聯等絕大多數日本姊妹校門檻（惟御茶水女子大學及富山大學要求 N1）"
        elif level == 3:
            tier_note = "JLPT N3 符合日本國立島根大學、德島大學、愛媛大學、弘前大學、山口大學、公立名櫻大學、神戶國際大學及星城大學交換門檻（奈良女大、東京海洋、山形、香川、琉球、青山學院、法政、明治學院及札幌國際雙聯要求 N2，御茶水女大及富山大學要求 N1）"
        else:
            tier_note = "開南大學日本交換姊妹校最低要求為 JLPT N3（島根、德島、愛媛、弘前、山口、名櫻、神戶國際、星城）、N2 或 N1（御茶水女大、富山大學）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}開南大學日本姊妹校交換與雙聯學位日語檢定基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = level >= 3
        if level >= 3:
            tier_note = f"TOPIK {level} 級符合韓國中央大學、漢陽大學 ERICA、仁荷大學、明知大學、德成女子大學、韓南大學、釜山外國語大學、蔚山大學等韓語授課交換門檻"
        else:
            tier_note = "開南大學韓國姊妹校韓語授課組要求 TOPIK 3 級以上（若修讀英語授課學程則可改以 TOEIC 500 / IELTS 4.0～4.5 申請）"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}開南大學韓國姊妹校交換韓語基準（{tier_note}）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照開南大學國際及兩岸事務處出國交換與雙聯學位簡章（英語組 TOEIC 500～600 / IELTS 4.5～5.5 / TOEFL iBT 61、日語組 JLPT N3～N1、韓語組 TOPIK 3 級）確認目標姊妹校語言門檻。",
    )
