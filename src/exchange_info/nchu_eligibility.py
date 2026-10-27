from __future__ import annotations

import re

from .university_registry import NCHU, resolve_university

NCHU_OUTBOUND_URL = "https://www.oia.nchu.edu.tw/index.php/zh/5-global-mobility-tw/5-1-exchange-student-program-tw/5-1-1-application-guildeline-tw"
NCHU_GUIDELINE_EN_URL = "https://oia.nchu.edu.tw/index.php/5-global-mobility-en/5-1-exchange-student-program-en/5-1-1-application-guildeline-en"
NCHU_GUIDELINES_PDF_URL = "https://www.oia.nchu.edu.tw/images/File/05_Global_Mobility/5-1-Exchange-Student-Programs/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf"
NCHU_APPLY_PORTAL_URL = "https://oiawp.nchu.edu.tw/out-going-program-online-application/"
NCHU_PARTNERS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1acE37cH-R7k88O9g-sT8wH-rX99rQT3a/edit?usp=sharing&ouid=108931068757503846261&rtpof=true&sd=true"
NCHU_MAINLAND_PARTNERS_URL = "https://www.oia.nchu.edu.tw/index.php/zh-tw/2-uncategorised/158-1-2-exchange-china"
NCHU_EXPERIENCE_URL = "https://iss.nchu.edu.tw/target/outbound/"
NCHU_SCHOLARSHIP_URL = "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/155-1-1-exchange-scholarship"
NCHU_REGULATIONS_PDF_URL = "https://www.oia.nchu.edu.tw/images/File/01_OIA_Regulations/R6_Regulations_for_nominating_NCHU_outbound_exchange_TW.pdf"

NCHU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 72.0),
    "ielts": ("IELTS Academic", 5.5),
    "toeic": ("TOEIC Listening & Reading", 785.0),
}


def is_nchu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NCHU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立中興大學",
        "中興大學",
        "中興",
        "興大",
        "nchu",
        "national chung hsing university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nchu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；《國立中興大學選送學生出國交換甄選辦法》規定申請對象為本校學位生（含進修部）：學士班一年級僅可申請春季班、學士班二年級（含）以上、碩士班一年級（含）以上、博士班一年級（含）以上，通過系所推薦者。",
        )
    if any(token in degree for token in ("在職", "EMBA")):
        return (
            "pass",
            f"已填報 {degree}；可依中興大學規定申請校級交換計畫（惟簡章規定在職專班學生不得申請教育部學海系列獎學金）。",
        )
    if "學士" in degree or "大學" in degree:
        if year in {"一年級", "大一", "1"}:
            return (
                "needs_confirmation",
                f"已填報 {degree}（{year}）。依中興大學交換學生甄選簡章規定，學士班一年級學生「僅可申請春季班（第2學期出國交換）」，學士班二年級（含）以上始可申請秋季班與春季班。",
            )
    if any(token in year for token in ("延修", "延畢")):
        return (
            "pass",
            f"已填報 {degree}（{year}）。中興大學允許延畢生申請並出國交換（惟出國交換不得作為申請延畢之理由，且部分大陸地區姊妹校不接受大四生或延畢生申請，請留意各校備註）。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立中興大學學士班、碩士班及博士班在學學位生申請範圍（同一學制內最多可交換 2 次、每次以 1 學期為限；交換期間每學期至少須選修相當於興大 6 學分／108 授課小時之課程）。",
    )


def nchu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if not degree_level or _is_graduate(degree_level):
        return "needs_confirmation", "中興本期簡章的 60 分門檻限學士班；碩博士班須檢附成績並通過系所推薦，尚須確認個別姊妹校資格。"
    if academic_score is None:
        return "needs_confirmation", "學士班須提供歷年在校總平均以核對 60 分門檻；GPA 或排名不能直接替代該項要求。"
    passed = academic_score >= 60.0
    return (
        "pass" if passed else "fail",
        f"歷年總平均 {academic_score:g} 分{'符合' if passed else '未達'}中興學士班 60 分門檻；仍須系所推薦及符合姊妹校要求。",
    )


def nchu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請國立中興大學赴大陸地區 43 所姊妹校（含北京大學、復旦、上海交大、南京、浙江、武漢、同濟、哈工大、中農大等）交換計畫免繳交語言能力證明。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。《國立中興大學交換學生申請簡章》規定：申請國外姊妹校須達 CEFR B2 英語標準（TOEFL iBT 72［新制 4 分／ITP 543］、IELTS 5.5 或 TOEIC 785 以上）；若申請非英語系國家且該校可接受其他語言檢定（如日檢 JLPT、韓檢 TOPIK、德檢、法檢、西檢），則可免交英語能力證明。",
        )
    if test in NCHU_ENGLISH_MINIMUMS:
        label, minimum = NCHU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        warning = "重要提醒：通過興大校內 CEFR B2 英語門檻（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785）後，仍須符合各志願學校要求之語言成績標準（且英檢須為申請截止日前 2 年內應試之成績）。"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立中興大學出國交換甄選 CEFR B2 英語門檻 {minimum:g}。{warning}",
        )
    if test == "jlpt":
        if partner_country and partner_country != "日本":
            return (
                "needs_confirmation",
                f"已填寫 JLPT N{int(language_score)}；申請非日本地區姊妹校須提供有效英語檢定證明（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785 以上）或該國對應語檢證明。",
            )
        passed = 1.0 <= language_score <= 5.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}國立中興大學赴日本姊妹校日語檢定申請條件（簡章規定非英語系國家學校若可接受日檢 JLPT N1–N5 則免交英檢證明；惟若志願序中任一所學校要求英檢，仍須同時繳交英檢證書）。",
        )
    if test == "topik":
        if partner_country and partner_country != "韓國":
            return (
                "needs_confirmation",
                f"已填寫 TOPIK {int(language_score)} 級；申請非韓國地區姊妹校須提供有效英語檢定證明（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785 以上）。",
            )
        passed = 1.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}國立中興大學赴韓國姊妹校韓語檢定申請條件（簡章規定若韓國姊妹校接受韓檢 TOPIK 則可免交英檢；惟若志願序中任一所學校要求英檢，仍須同時繳交英檢證書）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請核對國立中興大學出國交換甄選簡章（英語標準為 TOEFL iBT 72 / ITP 543 / IELTS 5.5 / TOEIC 785，或非英語系國家接受之日、韓、德、法、西語檢定）及各姊妹校個別語言門檻。",
    )
