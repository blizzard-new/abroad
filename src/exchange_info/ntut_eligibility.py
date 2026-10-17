from __future__ import annotations

import re

from .university_registry import NTUT, resolve_university

NTUT_OUTBOUND_URL = "https://oia.ntut.edu.tw/p/412-1032-9312.php?Lang=zh-tw"
NTUT_GUIDELINES_PDF_URL = (
    "https://oia.ntut.edu.tw/var/file/32/1032/img/2933/169590471.pdf"
)
NTUT_APPLY_PORTAL_URL = (
    "https://oia.ntut.edu.tw/p/412-1032-9238.php?Lang=zh-tw"
)
NTUT_PARTNERS_URL = "https://oia.ntut.edu.tw/p/412-1032-9243.php?Lang=zh-tw"
NTUT_MATCHING_PDF_URL = (
    "https://oia.ntut.edu.tw/var/file/32/1032/img/2933/201490897.pdf"
)
NTUT_MAINLAND_PARTNERS_URL = (
    "https://oia.ntut.edu.tw/p/412-1032-10190.php?Lang=zh-tw"
)
NTUT_DUAL_DEGREE_URL = "https://oia.ntut.edu.tw/p/412-1032-10643.php?Lang=zh-tw"
NTUT_EXPERIENCE_URL = "https://oia.ntut.edu.tw/p/412-1032-14379.php?Lang=zh-tw"
NTUT_MAINLAND_EXPERIENCE_URL = (
    "https://oia.ntut.edu.tw/p/412-1032-10191.php?Lang=zh-tw"
)
NTUT_SCHOLARSHIP_URL = "https://oia.ntut.edu.tw/p/412-1032-9313.php?Lang=zh-tw"
NTUT_SCHOLARSHIP_REGULATIONS_PDF_URL = (
    "https://oia.ntut.edu.tw/var/file/32/1032/img/2933/869917322.pdf"
)

NTUT_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 68.0),
    "ielts": ("IELTS Academic", 5.5),
    "toeic": ("TOEIC Listening & Reading", 700.0),
}


def is_ntut(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTUT.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺北科技大學",
        "國立台北科技大學",
        "臺北科技大學",
        "台北科技大學",
        "臺北科大",
        "台北科大",
        "北科大",
        "北科",
        "ntut",
        "taipei tech",
        "national taipei university of technology",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ntut_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；《國立臺北科技大學赴外研修計畫甄選簡章》規定：本校在學學生（含本國籍學生、國際生、僑生、陸生）皆可申請，惟至少需在北科修業「完成」一學期（最快大一下或碩一下申請；申請大陸地區交換須為大二以上大學生及研究生且具一學年成績）。",
        )
    if "五專" in degree:
        if any(token in year for token in ("一", "二", "三", "1", "2", "3")):
            return (
                "needs_confirmation",
                f"已填報 {degree}（{year}）。北科大國際事務處 Q&A 提醒：由於多數海外姊妹校僅收大學部一年級以上學生，為免被交換校退件，建議五專部學生於「專四或專五（對應學制為大一、大二）」時再提出申請。",
            )
        return (
            "pass",
            f"已填報 {degree}{f'（{year}）' if year else ''}；五專部專四、專五學生可對應大學部一、二年級學制提出赴外交換申請（請同時確認目標姊妹校 Fact Sheet 學制要求）。",
        )
    if year in {"一年級", "大一", "碩一", "博一", "1"}:
        return (
            "needs_confirmation",
            f"已填報 {degree}（{year}）。依北科大國際處出國交換 Q&A 規定，大一及碩一新生（含直升研究所）至少需要在北科修業「完成」一學期取得成績單後始可提出申請（最快申請時間為一下／碩一下；大陸地區研修則限大二以上及研究生）。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立臺北科技大學在學學生赴外研修申請資格（出國研修期間須維持北科大在學學生身分，不得辦理畢業或休學手續；原則以交換一學期為主，每學期至少修習 1 門專業課程）。",
    )


def ntut_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            "尚未填寫歷年學業總平均成績或班排名百分比；《國立臺北科技大學赴外研修計畫甄選簡章》規定申請者「歷年學業總平均須達 70 分以上」，並須檢附含班排名之中文歷年成績單。",
        )

    details: list[str] = []
    score_ok = False
    gpa_ok = False
    rank_ok = False

    if academic_score is not None:
        details.append(f"歷年總平均 {academic_score:g} 分")
        if academic_score >= 70.0:
            score_ok = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= 2.7:
            gpa_ok = True
    if class_rank_percent is not None:
        details.append(f"班排名前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
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
            f"已填報 {summary}，未達國立臺北科技大學赴外研修計畫甄選簡章規定之「歷年學業總平均 70 分以上（或相當於 GPA 2.7 / 班排前 50%）」基本門檻。",
        )

    return (
        "pass",
        f"已填報 {summary}；符合國立臺北科技大學赴外研修計畫學業門檻（歷年學業總平均 70 分以上）。校內甄選基本分為 70 分，在校成績、外語能力（含培力英檢 BESTEP／EMI 修課證明）及國際處服務時數皆可加分，並同步決定教育部「學海飛颺」獎學金補助排序。",
    )


def ntut_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請國立臺北科技大學赴大陸地區姊妹校（北京科技大學、天津大學、大連理工大學、西南交通大學、上海財經大學、華南理工大學等）交換計畫以中文授課為主，免檢附外語能力檢定證明。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。《國立臺北科技大學赴外研修計畫甄選簡章》規定外語能力須達到海外研修機構之要求標準（一般英語組姊妹校基準約為 TOEFL iBT 68 / ITP 520 / IELTS 5.5 / TOEIC 700 以上；日語組為 JLPT N2/N1；德、法、西語組為 CEFR B1/B2；另檢附培力英檢 BESTEP 或 EMI 修課通過證明可酌予加分）。",
        )
    if test in NTUT_ENGLISH_MINIMUMS:
        label, minimum = NTUT_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        warning = "提醒：除符合基本門檻外，務必逐一核對目標姊妹校於北科大「交換學校列表（9243.php）」及 Fact Sheet 所列之個別外語標準（例如荷蘭 University of Twente 自 2026 年起不採計 TOEIC，僅採計 IELTS 與 TOEFL iBT）。"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺北科技大學赴外研修一般英語檢定參考基準 {minimum:g}。{warning}",
        )
    if test == "jlpt":
        if partner_country and partner_country != "日本":
            return (
                "needs_confirmation",
                f"已填寫 JLPT N{int(language_score)}；申請非日本地區姊妹校須提供符合該校要求之英語檢定證明（如 TOEFL iBT / IELTS / TOEIC）或當地語言檢定。",
            )
        passed = 1.0 <= language_score <= 5.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}國立臺北科技大學赴日本姊妹校日語檢定申請條件（多數日本交換校要求 JLPT N2 或 N1，或英語授課學程 요구之 TOEIC/TOEFL 成績，請依各校 Fact Sheet 為準）。",
        )
    if test == "topik":
        if partner_country and partner_country != "韓國":
            return (
                "needs_confirmation",
                f"已填寫 TOPIK {int(language_score)} 級；申請非韓國地區姊妹校須提供符合該校要求之英語檢定證明。",
            )
        passed = 1.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}國立臺北科技大學赴韓國姊妹校韓語檢定申請條件（韓國姊妹校多數同時接受英語檢定 TOEIC/TOEFL/IELTS 或 TOPIK 成績）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請對照國立臺北科技大學交換學校列表（https://oia.ntut.edu.tw/p/412-1032-9243.php?Lang=zh-tw）各姊妹校 Fact Sheet 之語言能力要求標準。",
    )
