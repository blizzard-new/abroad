"""National Ilan University (國立宜蘭大學, NIU) outbound exchange & dual-degree eligibility checks.

Official rule sources:
- 國立宜蘭大學學生赴境外研修甄選作業要點 (110.11.02 行政會議通過):
  https://oia.niu.edu.tw/var/file/14/1014/img/462/88737351.pdf
- 國立宜蘭大學與境外大學辦理雙聯學制實施辦法 (113.03.21 教務會議修正通過):
  https://oia.niu.edu.tw/var/file/14/1014/img/414/692375089.pdf
- 國立宜蘭大學學生赴境外研修獎補助要點 (110.12.07 校務基金管理委員會通過):
  https://oia.niu.edu.tw/var/file/14/1014/img/462/196586951.pdf
- 國立宜蘭大學學海系列方案甄選及補助要點 (115.03.10 校務基金管理委員會通過):
  https://oia.niu.edu.tw/var/file/14/1014/img/414/896982223.pdf
- 國立宜蘭大學學生赴境外研習暨交換申請資訊簡章與密西根大學迪爾伯恩分校雙聯學位專頁:
  https://oia.niu.edu.tw/p/404-1014-9618.php
  https://oia.niu.edu.tw/p/404-1014-9619.php
"""

from __future__ import annotations

import re

from .university_registry import NIU, resolve_university

NIU_OIA_HOME_URL = "https://oia.niu.edu.tw/"
NIU_OUTBOUND_EXCHANGE_URL = "https://oia.niu.edu.tw/p/404-1014-9618.php"
NIU_UMD_DUAL_DEGREE_URL = "https://oia.niu.edu.tw/p/404-1014-9619.php"
NIU_SCHOLARSHIPS_URL = "https://oia.niu.edu.tw/p/404-1014-9622.php"
NIU_SISTER_SCHOOLS_URL = "https://oia.niu.edu.tw/p/404-1014-9163.php"
NIU_EXPERIENCES_URL = "https://oia.niu.edu.tw/p/404-1014-68131.php"

NIU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 55.0),
    "ielts": ("IELTS", 5.0),
    "toefl_itp": ("TOEFL ITP/PBT", 500.0),
    "toeic": ("TOEIC", 500.0),
    "duolingo": ("Duolingo English Test", 95.0),
}


def is_niu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NIU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "niu",
        "國立宜蘭大學",
        "宜蘭大學",
        "宜大",
        "national ilan university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究", "master", "phd", "doctoral"))


def niu_degree_check(
    degree_level: str | None, current_year: str | int | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = str(current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立宜蘭大學學生赴境外研修甄選作業要點》第 4 點及《學生赴境外研習暨交換申請資訊》：申請人須為具本校學籍之日間學制大學部或研究所在學學生（不含在職專班、進修學士班及休學生；非中華民國籍學生可參加甄選，但不得交換至原屬國家境內之學校）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("在職專班", "碩專", "進修", "emba", "EMBA", "學分班", "選修生", "休學")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立宜蘭大學學生赴境外研修甄選作業要點》第 4 點及《學海系列方案甄選及補助要點》第 3 點規定，僅限具本校學籍之日間學制在學學生申請，在職專班、進修學士班或休學期間不在校級交換與教育部學海系列獎補助範圍內。"
            ),
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"4", "大四", "大四上", "大四下", "四年級", "四年級上學期", "四年級下學期", "應屆畢業"}:
        return (
            "pass",
            (
                f"已填報 {degree}（{year}）；依《國立宜蘭大學學生境外學習手冊》規定，應屆畢業生可提出申請，惟至境外交換期間仍須保有本校日間學籍（注意：美國庫茨敦大學、日本三重大學、越南胡志明市國際大學及北京交通大學、北京林業大學、華中科技大學、南京農業大學、河南大學、廈門大學、華東師範大學等校限制申請時須非應屆畢業班學生；法國 IMT Atlantique 限大三修業滿五學期）。"
            ),
        )
    grad_note = (
        "（提醒：碩士班學生於本校修滿一學期或 24 學分後，亦可申請美國密西根大學迪爾伯恩分校 UM-Dearborn 1+1 雙碩士、印尼阿瑪加雅大學建研所 1+1 雙碩士、大陸福州大學經管學院 1+1 雙碩士或法國 IMT Atlantique 交換）"
        if is_grad
        else "（提醒：部分姊妹校如美國庫茨敦大學、日本三重大學、越南國際大學及大陸北京交大、北京林大、華中科大、南京農大、河南大學、廈門大學、華東師大規定申請時須在本校修業滿一學年；美國密西根大學迪爾伯恩分校 3+2 學碩雙聯限大三升大四申請，加拿大英屬哥倫比亞大學 UBC 森資系 2+2 雙聯限大二升大三申請，瑞士 SHMS 酒店管理大學 3+1／2+1+1／3+2 雙聯限休健系學生申請）"
    )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立宜蘭大學日間學制在學學生赴境外交換與雙聯學位申請資格{grad_note}。",
    )


def niu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    is_grad = _is_graduate(degree_level)
    details: list[str] = []
    passes_exchange = False
    passes_subsidy_and_xuehai = False

    if class_rank_percent is not None:
        details.append(f"班排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= 40.0:
            passes_exchange = True
            passes_subsidy_and_xuehai = True
        elif not is_grad and class_rank_percent <= 60.0:
            passes_exchange = True
    if academic_score is not None:
        details.append(f"學業平均 {academic_score:g} 分")
        if academic_score >= 80.0:
            passes_exchange = True
            passes_subsidy_and_xuehai = True
        elif academic_score >= 75.0:
            passes_exchange = True
        elif not is_grad and academic_score >= 70.0 and class_rank_percent is None:
            passes_exchange = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= 3.0:
            passes_exchange = True
            passes_subsidy_and_xuehai = True
        elif not is_grad and academic_gpa >= 2.5 and class_rank_percent is None and academic_score is None:
            passes_exchange = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫前一學期班排名百分比、學業平均成績或 GPA；依《國立宜蘭大學學生赴境外研修甄選作業要點》第 4 點、《學生赴境外研修獎補助要點》第 2 點及《學海系列方案甄選及補助要點》第 3 點：（1）一般交換學生甄選：大學部前一學期學業成績須為全班前 60%，研究生學業成績平均須達 75 分以上，且前一學期操行成績達 75 分以上無重大違紀事件；（2）教育部《學海飛颺／學海惜珠》與《校內學生赴境外研修獎補助》：大學部前一學期學業成績須為全班前 40%，研究生學業平均成績須達 80 分以上；（3）美國密西根大學迪爾伯恩分校（UM-Dearborn 3+2／1+1 雙聯學位）要求在校平均 GPA 3.0/4.0 以上（商學院 MBA 達 GPA 3.2 免 GMAT），韓國國民大學交換要求 GPA 3.0/4.5 以上，日本金城學院大學要求 GPA 2.15 以上。"
            ),
        )

    if passes_exchange:
        tier_notes: list[str] = []
        if passes_subsidy_and_xuehai:
            tier_notes.append(
                "同時達到教育部《學海飛颺／學海惜珠》（5 萬～45 萬元）、《國立宜蘭大學學生赴境外研修獎補助》（最高 3 萬元＋重點學校獎助 5 千元＋語文獎助 4 千元）之大學部全班前 40%／研究生 80 分以上門檻，以及美國密西根大學迪爾伯恩分校（UM-Dearborn 3+2／1+1 雙聯 GPA 3.0）與韓國國民大學交換門檻"
            )
        else:
            tier_notes.append(
                "符合國立宜蘭大學一般出國交換甄選基本門檻（大學部前一學期全班前 60%／研究生平均 75 分以上，另須前一學期操行 75 分以上）；惟申請教育部《學海飛颺／學海惜珠》或《校內學生赴境外研修獎補助》須達大學部全班前 40%／研究生平均 80 分以上，申請美國 UM-Dearborn 雙聯須達 GPA 3.0 以上"
            )
        return (
            "pass",
            f"已填報 {summary}；符合國立宜蘭大學出國交換甄選學業標準（{'；'.join(tier_notes)}）。",
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達《國立宜蘭大學學生赴境外研修甄選作業要點》第 4 點規定之基本學業門檻（大學部前一學期學業成績須為全班前 60%，研究生學業成績平均須達 75 分以上；申請教育部學海系列及校內境外研修獎補助須達大學部前 40%／研究生 80 分以上）。"
        ),
    )


def niu_language_check(
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
                "申請赴大陸地區 15 所姊妹校（北京交通大學、北京林業大學、華中農業大學、華中科技大學、蘭州大學、南京農業大學、海南大學、河南大學、廈門大學經濟學院、華東師範大學、中國石油大學［華東］、福州大學經濟與管理學院雙聯等）交換或雙聯以中文授課為主，免附英／日／韓外語能力檢定證明。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依國立宜蘭大學國際事務處《學生赴境外研習暨交換申請資訊》與雙聯學位簡章各組門檻：（1）英語組：印尼日惹大學（UGM）、直葛潘查薩克蒂大學（UPT）、馬來西亞拉曼大學（UTAR）要求 TOEIC 500 / IELTS 5.0 / TOEFL ITP 500 以上；瑞士 SHMS 與 César Ritz 酒店管理大學雙聯要求 TOEFL iBT 55 / IELTS 5.5；波蘭瓦爾米亞-馬祖里大學、韓國啟明大學、泰國清邁大學／湄州大學／亞洲理工學院 AIT、菲律賓瑪布亞大學／德拉薩大學、印度 IIT Guwahati／SRM／KLU／清奈理工學院要求 TOEIC 600–605（印度姊妹校另要求在校英文成績 80 分以上）；波蘭克拉科夫工業大學要求 TOEIC 700；美國庫茨敦大學、法國大西洋高等礦業電信學院 IMT Atlantique、波蘭華沙生命科學大學 SGGW、韓國釜慶大學、印度 IIT Indore 要求 CEFR B2（TOEIC 785 / IELTS 5.5–6.0 / TOEFL iBT 70 / Duolingo 105）；馬來西亞馬來亞大學（UM）與越南胡志明市國際大學（VNU-HCM）要求 IELTS 6.0 / TOEFL iBT 80；美國密西根大學迪爾伯恩分校（UM-Dearborn 3+2／1+1 雙聯）要求大學部 TOEFL iBT 80 / IELTS 6.5、碩士班 TOEFL iBT 84 / IELTS 6.5；（2）日語組：日本金城學院大學（限大學部女生）要求 JLPT N5；西九州大學、國立島根大學要求 JLPT N3；福井縣立大學、關東學院大學、福岡工業大學、國立鹿兒島大學（或 IELTS 5.5）、杏林大學外國語學部要求 JLPT N2；杏林大學國際協力研究科（碩士）要求 JLPT N1；（3）韓語組：韓國國民大學、啟明大學要求 TOPIK 3 級（檀國大學、釜慶大學、國民大學亦可憑英語 TOEIC 600–785 申請）。"
            ),
        )
    if test in NIU_ENGLISH_MINIMUMS:
        label, minimum = NIU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達印尼日惹大學 UGM、直葛潘查薩克蒂大學與馬來西亞拉曼大學 UTAR 英語組基本門檻（TOEIC 500 / IELTS 5.0 / TOEFL ITP 500）"
        if (
            (test == "toefl" and language_score >= 84)
            or (test == "ielts" and language_score >= 6.5)
            or (test == "toeic" and language_score >= 850)
            or (test == "duolingo" and language_score >= 115)
        ):
            tier_note = "達美國密西根大學迪爾伯恩分校（UM-Dearborn 3+2 學碩／1+1 雙碩士，iBT 80–84 / IELTS 6.5）、加拿大英屬哥倫比亞大學（UBC 森資系 2+2 雙聯）、馬來亞大學（UM）、越南國際大學（VNU-HCM）及全部歐美亞太英語授課姊妹校最高門檻"
        elif (
            (test == "toefl" and language_score >= 70)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "duolingo" and language_score >= 105)
        ):
            tier_note = "達 CEFR B2 門檻（TOEIC 785 / IELTS 6.0 / TOEFL iBT 70），符合美國賓夕法尼亞庫茨敦大學、法國大西洋高等礦業電信學院 IMT Atlantique、波蘭華沙生命科學大學 SGGW、波蘭克拉科夫工業大學、韓國釜慶大學、國民大學及印度 IIT Indore 交換標準（惟美國 UM-Dearborn 雙聯需 iBT 80–84 / IELTS 6.5）"
        elif (
            (test == "toefl" and language_score >= 60)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toefl_itp" and language_score >= 500)
            or (test == "toeic" and language_score >= 600)
            or (test == "duolingo" and language_score >= 95)
        ):
            tier_note = "符合波蘭瓦爾米亞-馬祖里大學（UWM）、瑞士 SHMS／César Ritz 酒店管理大學雙聯（iBT 55 / IELTS 5.5）、日本鹿兒島大學英語組（IELTS 5.5）、韓國檀國大學／啟明大學、泰國清邁大學／湄州大學／亞洲理工學院 AIT、菲律賓瑪布亞大學／德拉薩大學及印度 IIT Guwahati／SRM／KLU 英語門檻（惟庫茨敦大學、華沙生命科學大學、IMT Atlantique 需 TOEIC 785 / IELTS 6.0）"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立宜蘭大學出國交換與雙聯學位英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。",
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 5
        if level == 1:
            tier_note = "JLPT N1 符合日本杏林大學國際協力研究科（碩士）及全部 16 所日本國公私立姊妹校最高日語門檻"
        elif level == 2:
            tier_note = "JLPT N2 符合日本福井縣立大學、關東學院大學、福岡工業大學、國立鹿兒島大學、國立三重大學、杏林大學外國語學部、西九州大學、國立島根大學及金城學院大學日語門檻（惟杏林大學國際協力研究科碩士班要求 N1）"
        elif level == 3:
            tier_note = "JLPT N3 符合日本西九州大學、國立島根大學、國立三重大學及金城學院大學（限大學部女生）交換門檻（惟福井縣立大學、關東學院大學、福岡工業大學、鹿兒島大學、杏林大學外國語學部要求 N2）"
        elif level in (4, 5):
            tier_note = "JLPT N4–N5 符合日本金城學院大學（限大學部女生，要求 JLPT N5 及 GPA 2.15 以上）及部分姊妹校基礎日語門檻（西九州大學與島根大學要求 N3，福井縣立大學、關東學院大學、福岡工業大學、鹿兒島大學要求 N2）"
        else:
            tier_note = "國立宜蘭大學日本交換姊妹校要求為 JLPT N5（金城學院大學）、N3（西九州、島根）、N2（福井縣立、關東學院、福岡工大、鹿兒島、杏林學部）或 N1（杏林大學院）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立宜蘭大學日本姊妹校交換日語檢定基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = level >= 3
        return (
            "pass" if passed else "fail",
            (
                f"TOPIK {level} 級{'符合' if passed else '未達'}國立宜蘭大學韓國姊妹校（國民大學、啟明大學、檀國大學、國立釜慶大學、國立順天大學）韓語檢定基準（須達 TOPIK 3 級以上，或改以英語 TOEIC 600–785 申請）。"
            ),
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立宜蘭大學國際事務處《學生赴境外研習暨交換申請資訊》各姊妹校外語門檻確認。",
    )
