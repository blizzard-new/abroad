from __future__ import annotations

import re

from .university_registry import NCHU, resolve_university

NCHU_OUTBOUND_URL = "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info"
NCHU_GUIDELINES_PDF_URL = "https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf"
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
    is_grad = _is_graduate(degree_level)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        if is_grad:
            return (
                "needs_confirmation",
                "尚未填寫歷年學業成績或名次；中興大學碩、博士班學生須通過系所推薦並檢附歷年成績單（碩一、博一新生尚無本校成績者，應繳交原畢業學校歷年成績單；在校成績占國外組甄選總成績 30%、大陸組 50%）。",
            )
        return (
            "needs_confirmation",
            "尚未填寫歷年學業總平均分數或 GPA；中興大學出國交換甄選規定學士班學生歷年在校總平均分數須達 60 分（含）以上（在校成績占國外組總成績 30%、大陸組 50%；申請學海飛颺或興大海外研修獎學金者須歷年名次前 50% 或平均 80 分以上）。",
        )

    details: list[str] = []
    score_ok = False
    gpa_ok = False
    rank_ok = False

    if academic_score is not None:
        details.append(f"歷年總平均 {academic_score:g} 分")
        if academic_score >= 60.0:
            score_ok = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= 2.0:
            gpa_ok = True
    if class_rank_percent is not None:
        details.append(f"歷年名次前 {class_rank_percent:g}%")
        if class_rank_percent <= 100.0:
            rank_ok = True

    summary = "、".join(details)
    if academic_score is not None:
        passed = score_ok
    elif academic_gpa is not None:
        passed = gpa_ok
    else:
        passed = rank_ok

    if not passed:
        return (
            "fail",
            f"已填報 {summary}，未達國立中興大學出國交換甄選學士班歷年在校總平均分數 60 分（或 GPA 2.0）之最低門檻。",
        )

    scholarship_hint = ""
    if (academic_score is not None and academic_score >= 80.0) or (
        class_rank_percent is not None and class_rank_percent <= 50.0
    ):
        scholarship_hint = "（同時符合教育部學海飛颺及中興大學選送學生赴海外研修獎學金之學業門檻：歷年名次前 50% 或平均 80 分以上）"
    return (
        "pass",
        f"已填報 {summary}；符合國立中興大學出國交換甄選學業門檻（歷年總平均 60 分以上；校內評分比重：國外姊妹校組在校成績占 30%、大陸地區姊妹校組占 50%）。{scholarship_hint}請同時對照各姊妹校個別 GPA 規定（部分歐美日名校要求 GPA 3.0 / 4.0 以上）。",
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
