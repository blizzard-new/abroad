from __future__ import annotations

import re

from .university_registry import NTUST, resolve_university

NTUST_OUTBOUND_URL = "https://www.oia.ntust.edu.tw/p/412-1060-8921.php?Lang=zh-tw"
NTUST_APPLY_PORTAL_URL = "https://www.oia.ntust.edu.tw/p/412-1060-8926.php?Lang=zh-tw"
NTUST_QUOTALIST_URL = "https://www.oia.ntust.edu.tw/p/405-1060-62105,c9035.php?Lang=zh-tw"
NTUST_MAINLAND_URL = "https://www.oia.ntust.edu.tw/p/405-1060-101241,c9111.php?Lang=zh-tw"
NTUST_REGULATION_URL = "https://www.oia.ntust.edu.tw/var/file/60/1060/img/2289/948853506.pdf"

NTUST_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 57.0),
    "ielts": ("IELTS Academic", 4.0),
    "toeic": ("TOEIC", 550.0),
}


def is_ntust(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTUST.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺灣科技大學",
        "國立台灣科技大學",
        "臺灣科技大學",
        "台灣科技大學",
        "臺科大",
        "台科大",
        "ntust",
        "taiwan tech",
        "national taiwan university of science and technology",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ntust_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；臺科大規定申請人須為本校大學部二年級以上（須有完整一學年成績）或碩、博士班一年級以上在學學生，不含各類在職專班。",
        )
    if any(token in degree for token in ("在職", "進修", "推廣", "EMBA")):
        return (
            "fail",
            f"已填報 {degree}。臺科大《選送優秀學生出國研習甄選簡章》規定申請資格限一般生，不含在職專班學生。",
        )
    if any(token in year for token in ("大一", "大學一年級", "學士班一年級")):
        return (
            "fail",
            f"已填報 {degree}（{year}）。臺科大規定大學部學生須為二年級以上且具完整一學年成績始得報名（碩、博士班為一年級以上）。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合臺科大大學部二年級以上或碩、博士班一年級以上一般生申請範圍（同一學制以出國交換一次為原則，不得同時申請雙聯學位）。",
    )


def ntust_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if academic_score is None and academic_gpa is None and class_rank_percent is None:
        return (
            "needs_confirmation",
            "尚未填寫歷年學業成績（GPA / 平均分數）或系所排名；臺科大規定海外交換申請人歷年名次須在全班前 70% 以內（大陸地區交換為大學部歷年總平均 75 分以上、研究所 80 分以上），且在校學業成績占校內書審總分 20%。",
        )

    details: list[str] = []
    passed = True
    if class_rank_percent is not None:
        details.append(f"歷年排名前 {class_rank_percent:g}%")
        if class_rank_percent > 70.0:
            passed = False
    if academic_score is not None:
        details.append(f"歷年平均 {academic_score:g} 分")
        if academic_score < 65.0:
            passed = False
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa < 2.3:
            passed = False

    summary = "、".join(details)
    if not passed:
        return (
            "fail",
            f"已填報 {summary}，未達臺科大歷年名次全班前 70% 之基本門檻（大陸地區交換須大學部平均 75 分、研究所 80 分以上）。",
        )
    return (
        "pass",
        f"已填報 {summary}；符合臺科大歷年名次前 70% 門檻（校內書面審查學業成績占 20%，申請大陸地區交換者須確認大學部平均 75 分、研究所 80 分以上），請同時核對各姊妹校個別 GPA 規定。",
    )


def ntust_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請臺科大赴大陸地區 44 所姊妹校交換生計畫免附外語檢定證明；惟大學部歷年學業總平均須達 75 分以上、研究所須達 80 分以上。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。臺科大海外交換生甄選語言能力占總成績 60%，校內基本門檻為 TOEIC 550 / TOEFL iBT 57 / IELTS 4.0 / 全民英檢中級複試 / JLPT N2 / CEFR B1（申請校內獎學金門檻為 TOEIC 750 / TOEFL iBT 79 / IELTS 6.0 / JLPT N2）。",
        )
    if test in NTUST_ENGLISH_MINIMUMS:
        label, minimum = NTUST_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        scholarship_threshold = {"toefl": 79.0, "ielts": 6.0, "toeic": 750.0}.get(test, minimum)
        sch_note = (
            f"（亦達臺科大校內獎學金語言門檻 {label} {scholarship_threshold:g}）"
            if language_score >= scholarship_threshold
            else f"（惟尚未達臺科大校內出國交換獎學金語言門檻 {label} {scholarship_threshold:g}）"
        )
        warning = (
            "重要提醒：臺科大校內書審語言能力占 60%，且多數歐美及亞洲重點姊妹校要求 TOEFL iBT 79–90 或 IELTS 6.0–6.5（部分不採認 TOEIC），請務必對照《申請條件一覽表》各校規定。"
        )
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}臺科大校內基本報名門檻 {minimum:g}{sch_note}。{warning}",
        )
    if test == "jlpt":
        passed = 1.0 <= language_score <= 2.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}臺科大日語組校內及獎學金基準門檻（JLPT N2 以上；部分日本姊妹校英語授課學程得改以英語檢定申請，請對照一覽表各校規定）。",
        )
    if test == "topik":
        passed = 2.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}臺科大韓語組姊妹校常見門檻範圍（校內韓文基準為 TOPIK 3 級 / CEFR B1，部分韓國姊妹校接受英語檢定申請）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請核對臺科大《國外姊妹校申請條件一覽表》與簡章附表語言能力積分標準（第二外語達 CEFR B1 以上另可加總分 1 分）。",
    )
