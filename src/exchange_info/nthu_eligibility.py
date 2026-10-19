from __future__ import annotations

import re

from .university_registry import NTHU, resolve_university

NTHU_OUTBOUND_URL = "https://oga.site.nthu.edu.tw/p/412-1524-18680.php?Lang=zh-tw"
NTHU_OVERSEAS_PARTNERS_URL = "https://oga.site.nthu.edu.tw/p/404-1524-9358.php"
NTHU_MAINLAND_PARTNERS_URL = "https://oga.site.nthu.edu.tw/p/404-1524-9359.php?Lang=zh-tw"
NTHU_VM_PORTAL_URL = "https://oga-exchange.vm.nthu.edu.tw/outexchange/index/index/puid/11521"
NTHU_VM_OVERVIEW_URL = "https://oga-exchange.vm.nthu.edu.tw/outexchange/overview/index/puid/11521"
NTHU_2027_2028_GUIDELINES_ZH_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/2027F2028Sapplicationguideline-CH.pdf"
NTHU_SELECTION_REGULATIONS_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4534/525909033.pdf"
NTHU_SCHOLARSHIP_REGULATIONS_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4534/666778079.pdf"
NTHU_DISADVANTAGED_SCHOLARSHIP_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4534/517637953.pdf"
NTHU_LANGUAGE_STANDARDS_ZH_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4534/153594726.pdf"
NTHU_MAINLAND_GUIDELINES_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4542/510394575.pdf"
NTHU_UST_116_NOTICE_URL = "https://oga.site.nthu.edu.tw/p/406-1524-300405,r3318.php?Lang=zh-tw"
NTHU_POPULARITY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1G1mETD3Zt49jr0nJTK-2-3gOP8U5nJmg/edit?usp=sharing"
NTHU_EXPERIENCE_OVERSEAS_URL = "https://oga.site.nthu.edu.tw/p/412-1524-18684.php?Lang=zh-tw"

NTHU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT（新制對應 4.0）", 79.0),
    "ielts": ("IELTS Academic", 6.0),
}


def is_nthu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTHU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立清華大學",
        "清華大學",
        "清大",
        "nthu",
        "tsing hua university",
        "national tsing hua university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nthu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；《國立清華大學學生出國交換甄選辦法》及出國交換生甄選簡章規定：申請人須為本校大學部二年級（含）以上、碩士班一年級（含）以上或博士班一年級（含）以上之正式學籍在學學生（不含在職專班及在職生；申請時與出國交換期間學籍學位須一致）。",
        )
    if "在職" in degree or "專班" in degree:
        return (
            "fail",
            f"已填報 {degree}；依《國立清華大學學生出國交換甄選辦法》及出國交換生甄選簡章規定，出國交換計畫限一般正式學籍在學學生申請，不含在職專班及在職生。",
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"一年級", "大一", "1"}:
        return (
            "fail",
            f"已填報 {degree}（{year}）；依《國立清華大學出國交換生甄選簡章》規定，校級海外交換申請人須為大學部二年級（含）以上或碩博士班一年級（含）以上在學學生（惟赴大陸及港澳地區學期交換計畫開放大一、碩一、博一或轉學生提具前一學期成績證明申請）。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立清華大學出國交換生學制與年級資格（大學部二年級以上、碩博班一年級以上正式學籍在學學生；注意申請時與出國交換期間之學籍學位必須一致）。",
    )


def nthu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    details: list[str] = []
    score_ok = False
    gpa_ok = False
    rank_ok = False
    ust_ok = False

    if academic_score is not None:
        details.append(f"平均成績 {academic_score:g} 分")
        if academic_score >= 78.0:
            score_ok = True
        elif academic_score >= 75.0:
            ust_ok = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= 3.20:
            gpa_ok = True
        elif academic_gpa >= 3.00:
            ust_ok = True
    if class_rank_percent is not None:
        details.append(f"班/系排名前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            rank_ok = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            "尚未填寫學業平均成績、GPA 或班/系排名百分比；《國立清華大學出國交換生甄選簡章》規定：校級海外交換須達申請前兩學期平均 GPA 3.20（約合百分制 78 分）以上或班排名前 50% 以上（陸港澳交換須達 GPA 3.20 或班排前 30%；台灣聯大 UST 交換須達 GPA 3.0 以上；申請 A/B 類出國交換獎學金、清寒獎學金及劉維全校友獎學金須達前一學年平均 GPA 3.40 以上或全班／系前 20% 以上）。",
        )

    if gpa_ok or score_ok or rank_ok:
        sch_eligible = (
            (academic_gpa is not None and academic_gpa >= 3.40)
            or (academic_score is not None and academic_score >= 82.0)
            or (class_rank_percent is not None and class_rank_percent <= 20.0)
        )
        sch_note = (
            "同時符合清大出國交換生獎學金（A/B 類）、清寒學生出國交流獎學金及劉維全校友獎學金學業門檻（前一學年 GPA 3.40 或班／系排前 20%）"
            if sch_eligible
            else "若欲申請清大出國交換生獎學金（A/B 類）、清寒獎學金或劉維全校友獎學金，須達前一學年平均 GPA 3.40 以上或全班／系排名前 20% 以上（教育部學海惜珠為 GPA 3.20 以上）"
        )
        return (
            "pass",
            f"已填報 {summary}；符合國立清華大學校級海外交換學業成績基本門檻（前兩學期 GPA 3.20 或班排名前 50% 以上；請同步核對目標姊妹校是否訂有更高 GPA 門檻，且{sch_note}）。",
        )

    if ust_ok:
        return (
            "needs_confirmation",
            f"已填報 {summary}；符合「台灣聯合大學系統（UST）學生出國交換計畫」門檻（前一學年平均 GPA 3.0 以上），惟若申請清大校級海外交換，須達前兩學期 GPA 3.20 以上或班級排名前 50% 以上（陸港澳交換為 GPA 3.20 或班排前 30%）。",
        )

    return (
        "fail",
        f"已填報 {summary}；未達國立清華大學校級海外出國交換最低成績標準（前兩學期平均 GPA 3.20［約 78 分］以上或班級排名前 50% 以上）及台灣聯大交換門檻（GPA 3.0 以上）。",
    )


def nthu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country == "中國大陸" and (not test or language_score is None):
        return (
            "pass",
            "申請赴大陸地區交換者，一般中文授課課程免附外語檢定證明（惟若申請寧波諾丁漢大學等全英語授課校區或修讀英文授課課程，仍須符合接待校英語門檻）。",
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。依《國立清華大學出國交換生外語能力標準表》（2026.08.28 修訂），申請校級海外交換須於申請截止日前檢附 2 年內有效之外語成績單：英語組 TOEFL iBT 79（新制 4.0）或 IELTS Academic 6.0；日語組 JLPT N2；德／法／西語組 B1（或 TestDaF TDN 3／FLPT 筆試 150 且口試 S-2）；韓語組 TOPIK 4 級（不接受 MyBest Scores、TOEIC、GEPT、GRE、Duolingo）。",
        )
    if test == "toeic":
        return (
            "fail",
            f"已填報 TOEIC {language_score:g}；注意：《國立清華大學出國交換生甄選簡章》及《外語能力標準表》明訂校級海外交換「不接受多益（TOEIC）、全民英檢（GEPT）、GRE、Duolingo 及 TOEFL MyBest Scores」，英語組僅採計 TOEFL iBT（最低 79 分／新制 4.0）或 IELTS Academic（最低 6.0）！",
        )
    if test in NTHU_ENGLISH_MINIMUMS:
        label, minimum = NTHU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立清華大學校級海外交換英語組最低門檻（{minimum:g}；注意不採計 TOEFL iBT MyBest Scores 拼分成績，且若目標姊妹校訂有更高總分或單科門檻，須從其規定）。",
        )
    if test == "jlpt":
        passed = 1.0 <= language_score <= 2.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}國立清華大學出國交換日語組校內最低門檻（須達 JLPT N2［含］以上；部分日本姊妹校英語授課計畫另可憑 TOEFL iBT 79 或 IELTS 6.0 申請）。",
        )
    if test == "topik":
        passed = 4.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}國立清華大學出國交換韓語組校內最低門檻（須達 TOPIK 4 級［含］以上；韓國姊妹校英語授課組另可憑 TOEFL iBT 79 或 IELTS 6.0 申請）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請對照《國立清華大學出國交換生外語能力標準表》（{NTHU_LANGUAGE_STANDARDS_ZH_URL}：法語 DELF/TCF B1、德語 Goethe B1/TestDaF TDN 3、西語 DELE B1 或 FLPT 筆試 150 口試 S-2）及各姊妹校最新門檻。",
    )
