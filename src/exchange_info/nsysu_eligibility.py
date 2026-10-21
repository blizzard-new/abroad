from __future__ import annotations

import re

from .university_registry import NSYSU, resolve_university

NSYSU_OUTBOUND_URL = "https://oia.nsysu.edu.tw/p/412-1308-20539.php?Lang=zh-tw"
NSYSU_GUIDELINES_URL = "https://oia.nsysu.edu.tw/p/412-1308-22647.php?Lang=zh-tw"
NSYSU_APPLY_PORTAL_URL = "https://partners.oia.nsysu.edu.tw/exchange/login/user/"
NSYSU_FACTSHEET_URL = "https://oia.nsysu.edu.tw/p/412-1308-20623.php?Lang=zh-tw"
NSYSU_EXPERIENCE_URL = "https://oia.nsysu.edu.tw/p/412-1308-20732.php?Lang=zh-tw"
NSYSU_SCHOLARSHIP_URL = "https://oia.nsysu.edu.tw/p/412-1308-20733.php?Lang=zh-tw"
NSYSU_REGULATIONS_PDF_URL = "https://oia.nsysu.edu.tw/static/file/308/1308/img/4144/874755230.pdf"

NSYSU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 60.0),
    "ielts": ("IELTS Academic", 5.0),
    "toeic": ("TOEIC", 600.0),
    "duolingo": ("Duolingo", 80.0),
}


def is_nsysu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NSYSU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立中山大學",
        "中山大學",
        "中山",
        "nsysu",
        "national sun yat-sen university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nsysu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；《國立中山大學學生出國交換甄選要點》第 4 點規定申請對象為本校大學部一至四年級及碩士班一至二年級之在校學生（不包含延畢生及在職生身分入學者）。",
        )
    if any(token in degree for token in ("在職", "EMBA")):
        return (
            "fail",
            f"已填報 {degree}。《國立中山大學學生出國交換甄選要點》第 4 點規定申請對象不包含以在職生身分入學者。",
        )
    if "博" in degree:
        return (
            "fail",
            f"已填報 {degree}。《國立中山大學學生出國交換甄選要點》第 4 點規定校級出國交換申請對象為大學部一至四年級及碩士班一至二年級在校學生（博士班出國研修補助請洽研究發展處）。",
        )
    if any(token in year for token in ("延修", "延畢", "碩三", "碩四")):
        return (
            "fail",
            f"已填報 {degree}（{year}）。《國立中山大學學生出國交換甄選要點》第 4 點規定申請對象為大學部一至四年級及碩士班一至二年級在校學生，不包含延畢生。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立中山大學大學部一至四年級及碩士班一至二年級在校學生申請範圍（出國期間每學期至少須修習並通過 2 門課程，其中至少 1 門為專業課程；通過非中港澳出國交換甄選錄取者自動獲得「西灣領航計畫」每月 NT$10,000–15,000 獎助資格）。",
    )


def nsysu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if class_rank_percent is None or not 0 < class_rank_percent <= 100:
        return "needs_confirmation", "甄選要點採正式成績單的歷年班排名評分；須提供班排名，不能以平均70、GPA 2.5或排名前75%作共通錄取門檻。"
    return "pass", f"已填報歷年班排名前{class_rank_percent:g}%，可供校內學業項目評分；未設排名前75%的共通門檻。總分須達60且須通過分發，合作校學業資格仍須另核。"


def nsysu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請國立中山大學赴中國大陸地區（含北京大學、復旦、上海交大、南京、浙江、同濟、武漢、廈門、中山、南開等 16 校）出國交換計畫免繳交任何語言檢定證明（惟外國籍／僑生申請廈門大學等部分學校須具 HSK 5 級 210 分以上）。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。《國立中山大學學生出國交換甄選要點》第 4 點規定：申請「其他國家與地區」須達 TOEFL iBT 60、IELTS 5.0、TOEIC 600、Cambridge PET 154、Duolingo 80 或 BESTEP 培力英檢聽讀 170 以上；申請「日本地區」須具 JLPT N5（含）以上或上述任一英檢達標證明，且須同時符合各志願學校要求。",
        )
    if test in NSYSU_ENGLISH_MINIMUMS:
        label, minimum = NSYSU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        warning = "重要提醒：通過校內最低英語門檻（TOEFL iBT 60 / IELTS 5.0 / TOEIC 600）後，仍須符合各交換校個別語言標準（歐美及管院姊妹校多要求 TOEFL iBT 72–90 或 IELTS 5.5–6.5）。"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立中山大學出國交換甄選英語最低門檻 {minimum:g}。{warning}",
        )
    if test == "jlpt":
        if partner_country != "日本":
            return (
                "needs_confirmation",
                f"已填寫 JLPT N{int(language_score)}；申請非日本地區交換計畫須提供有效英語檢定證明（TOEFL iBT 60 / IELTS 5.0 / TOEIC 600 / Duolingo 80 / BESTEP 170 以上）。",
            )
        passed = 1.0 <= language_score <= 5.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}國立中山大學赴日本交換甄選校內最低日檢門檻（N5 含以上；惟東京大學、早稻田、東北、立命館、法政、同志社、九州、北海道、大阪等校日語授課組多要求 JLPT N1 或 N2，請務必對照目標學校規定）。",
        )
    if test == "topik":
        return "needs_confirmation", "TOPIK不能替代『其他國家與地區』甄選要求的英語證明；仍須檢附要點列明的任一英檢，並另核合作校韓語條件。"

    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請核對國立中山大學出國交換甄選簡章（Duolingo 最低 80、Cambridge PET 最低 154、BESTEP 聽讀最低 170）及各交換校個別語言檢定門檻。",
    )
