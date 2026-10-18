from __future__ import annotations

import re

from .university_registry import NCKU, resolve_university

NCKU_OUTBOUND_URL = "https://oia.ncku.edu.tw/p/404-1032-227700.php?Lang=zh-tw"
NCKU_116_1_ANNOUNCEMENT_URL = "https://oia.ncku.edu.tw/p/406-1032-301175,r3414.php?Lang=zh-tw"
NCKU_GUIDELINES_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf"
NCKU_PARTNERS_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/535260712.pdf"
NCKU_PORTAL_URL = "https://exchange.oia.ncku.edu.tw/index.php?outgoing_auth"
NCKU_REGULATION_URL = "https://oia.ncku.edu.tw/p/404-1032-227702.php?Lang=zh-tw"
NCKU_SCHOLARSHIP_URL = "https://oia.ncku.edu.tw/p/404-1032-228571.php?Lang=zh-tw"
NCKU_EXPERIENCE_URL = "https://oia.ncku.edu.tw/p/405-1032-252564,c29777.php?Lang=zh-tw"

NCKU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 72.0),
    "ielts": ("IELTS Academic", 5.5),
    "toeic": ("TOEIC Listening & Reading", 785.0),
}


def is_ncku(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NCKU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立成功大學",
        "成功大學",
        "成大",
        "ncku",
        "cheng kung university",
        "national cheng kung university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ncku_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；《國立成功大學校級薦外交換學生計畫甄選簡章》規定：申請資格限本校大學部二年級以上、碩士班一年級以上、博士班一年級以上在學學生（轉學生須為二年級以上且於成大就讀滿一學期並有成績單；交換期間須為成大在學學生，不得休學或畢業）。",
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"一年級", "大一", "1"}:
        return (
            "fail",
            f"已填報 {degree}（{year}）；依《國立成功大學校級薦外交換學生計畫甄選簡章》規定，大學部學生須為二年級以上方得申請校級薦外交換（碩士班、博士班則自一年級起即可申請）。",
        )
    if "在職" in degree or "專班" in degree:
        return (
            "needs_confirmation",
            f"已填報 {degree}；成大在職專班在學學生雖可依校級甄選簡章報名薦外交換，惟依《國立成功大學學生跨國雙向研修獎助學金補助辦法》規定，在職專班學生不具該項獎助學金申請資格，且須確認目標姊妹校是否接受在職專班學制。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立成功大學校級薦外交換計畫學制與年級資格（大學部二年級以上、碩博班一年級以上；出國交換期間須於成大註冊並維持在學身分，同一學制以出國交換一次為原則）。",
    )


def ncku_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    is_grad = _is_graduate(degree_level)
    details: list[str] = []
    score_ok = False
    gpa_ok = False
    rank_ok = False

    if academic_score is not None:
        details.append(f"平均成績 {academic_score:g} 分")
        if academic_score >= 77.0:
            score_ok = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= 3.1:
            gpa_ok = True
    if class_rank_percent is not None:
        details.append(f"班/系排名前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            rank_ok = True

    summary = "、".join(details)
    if is_grad:
        return (
            "pass",
            f"{f'已填報 {summary}；' if summary else ''}依《國立成功大學校級薦外交換學生計畫甄選簡章》規定，研究所（碩士班、博士班）學生無校內學業成績最低門檻限制（須取得指導教授或系所主管簽章同意，且甄選總分中「在校成績」占 50%，並須符合目標交換學校之 GPA 要求）。",
        )

    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            "尚未填寫學業平均成績或班/系排名百分比；成大校級薦外交換甄選簡章規定：大學部學生前一學期課業成績平均須達 77 分（含）以上，或全班／全系排名前 50%（研究所學生則無校內成績門檻，惟須取得指導教授同意）。",
        )

    if score_ok or rank_ok or gpa_ok:
        return (
            "pass",
            f"已填報 {summary}；符合國立成功大學大學部校級薦外交換「前一學期課業成績平均 77 分以上或全班／全系排名前 50%」門檻（甄選評分比重：在校成績 50%、研究/讀書計畫 25%、自傳及其餘表現 25%）。",
        )

    return (
        "fail",
        f"已填報 {summary}；未達國立成功大學大學部校級薦外交換「前一學期課業成績平均 77 分（含）以上或全班／全系排名前 50%」之基本申請門檻。",
    )


def ncku_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。成大校級薦外交換甄選規定：申請者須檢附報名截止日前 2 年內有效之外語能力證明，英語能力須達 CEFR B2 以上（TOEFL iBT 72［新制 4.0］、IELTS Academic 5.5 或 TOEIC 785 以上；申請大陸地區學校者亦須檢附符合成大標準之英語能力證明），或具備交換學校要求之日語（JLPT）、韓語（TOPIK）、德語、法語等外語檢定門檻。",
        )
    if test in NCKU_ENGLISH_MINIMUMS:
        label, minimum = NCKU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立成功大學校級薦外交換英語基本門檻 {minimum:g}（CEFR B2：TOEFL iBT 72［新制 4.0］／IELTS Academic 5.5／TOEIC 785）。提醒：各締約學校可能有更高總分、單科小分或不採計 TOEIC 之規定，請務必逐校核對《簽約學校一覽表》。",
        )
    if test == "jlpt":
        if partner_country and partner_country != "日本":
            return (
                "needs_confirmation",
                f"已填寫 JLPT N{int(language_score)}；申請非日本地區姊妹校（含大陸地區）須檢附符合成大 CEFR B2 標準之英語能力證明或該校指定語種檢定。",
            )
        passed = 1.0 <= language_score <= 5.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}國立成功大學赴日本交換日語檢定條件（日本姊妹校依校別要求 JLPT N1、N2 或 N3，或英語 TOEFL/IELTS/TOEIC 達標，請依簽約學校一覽表為準）。",
        )
    if test == "topik":
        if partner_country and partner_country != "韓國":
            return (
                "needs_confirmation",
                f"已填寫 TOPIK {int(language_score)} 級；申請非韓國地區姊妹校須檢附符合成大 CEFR B2 標準之英語能力證明或該校指定語種檢定。",
            )
        passed = 1.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}國立成功大學赴韓國交換韓語檢定條件（韓國姊妹校多接受英語檢定或 TOPIK 2–4 級，請對照簽約學校一覽表）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請對照國立成功大學《116學年度第1學期校級薦外交換學生計畫簽約學校一覽表》（{NCKU_PARTNERS_PDF_URL}）各校指定外語檢定標準。",
    )
