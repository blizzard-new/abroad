from __future__ import annotations

import re

from .university_registry import NTNU, resolve_university

NTNU_OUTBOUND_URL = "https://bds.oia.ntnu.edu.tw/bds/web/OUT"
NTNU_APPLY_PORTAL_URL = "https://bds.oia.ntnu.edu.tw/bds/OE"
NTNU_QUOTALIST_URL = "https://bds.oia.ntnu.edu.tw/bds/web/OUT-QUOTALIST"
NTNU_GUIDELINE_1161_URL = "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf"
NTNU_REGULATION_URL = "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_%E5%9C%8B%E7%AB%8B%E8%87%BA%E7%81%A3%E5%B8%AB%E7%AF%84%E5%A4%A7%E5%AD%B8%E8%B5%B4%E5%A4%96%E4%BA%A4%E6%8F%9B%E7%94%9F%E7%94%84%E9%81%B8%E4%BD%9C%E6%A5%AD%E8%A6%81%E9%BB%9E20190903.pdf"

NTNU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS Academic", 5.5),
    "toeic": ("TOEIC", 750.0),
}


def is_ntnu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTNU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺灣師範大學",
        "國立台灣師範大學",
        "臺灣師範大學",
        "台灣師範大學",
        "臺師大",
        "台師大",
        "師大",
        "ntnu",
        "national taiwan normal university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ntnu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；臺師大規定須為本校正式學籍全職學士班、碩士班或博士班在學學生，且於本校就讀滿一學期以上（不含進修推廣學院、碩士在職專班及受領臺灣獎學金之國際學生）。",
        )
    if any(token in degree for token in ("在職", "進修", "推廣")):
        return (
            "fail",
            f"已填報 {degree}。臺師大赴外交換生甄選限本校全職學士班、碩士班及博士班在學學生申請，不含進修推廣學院及碩士在職專班。",
        )
    if any(token in year for token in ("大一上", "碩一上", "博一上", "一年級上")):
        return (
            "fail",
            f"已填報 {degree}（{year}）。臺師大規定申請人須於本校就讀滿一學期以上，一年級第一學期新生尚不得報名（最早於一年級下學期始得申請）。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合臺師大全職學士、碩士、博士班申請範圍（請確認於本校已就讀滿一學期以上，且同一學制內赴外交換以 2 次、每次原則 1 學期、合計至多 2 學期為限）。",
    )


def ntnu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if academic_score is None and academic_gpa is None and class_rank_percent is None:
        return (
            "needs_confirmation",
            "尚未填寫歷年學業成績（GPA / 平均分數）或系所排名；臺師大校級甄選「在校學業及相關表現」占總成績 30%（含全英語授課 EMI 課程修習表現 5%：修滿 5 門以上得滿分 5%），且各姊妹校另有個別 GPA 門檻（常見 GPA 2.5–3.5 / 4.3）。",
        )

    details: list[str] = []
    passed = True
    if academic_score is not None:
        details.append(f"歷年平均 {academic_score:g} 分")
        if academic_score < 60.0:
            passed = False
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa < 2.0:
            passed = False
    if class_rank_percent is not None:
        details.append(f"系所排名前 {class_rank_percent:g}%")

    summary = "、".join(details)
    if not passed:
        return (
            "fail",
            f"已填報 {summary}，未達基本及格門檻。請確認歷年成績單與目標姊妹校個別 GPA 規定。",
        )
    return (
        "pass",
        f"已填報 {summary}；臺師大校級書面審查「在校學業及相關表現」占 30%（其中修習 EMI 全英語授課課程占 5%，修滿 5 門以上得滿分 5%），請同時核對《116-1 赴外交換學校一覽表》各校個別 GPA 門檻。",
    )


def ntnu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return (
            "pass",
            "申請臺師大「中文組」赴大陸及港澳地區部分中文授課姊妹校免附外語能力檢定證明（若申請港澳英語授課組別則須符合英歐語組檢定門檻）。",
        )
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。臺師大校級甄選分「英歐語組、日語組、韓語組、中文組」四組（限擇一組別報名、至多填 10 個志願），語言能力占總成績 30%，且不採計 TOEFL MyBest Scores 拼分成績。",
        )
    if test in NTNU_ENGLISH_MINIMUMS:
        label, minimum = NTNU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        warning = (
            "重要提醒：臺師大不採計 TOEFL iBT MyBest Scores 拼分成績，且歐美多數姊妹校要求 TOEFL iBT 79–100 或 IELTS Academic 6.0–7.0（部分不採認 TOEIC 或 GEPT），請務必對照《赴外交換學校一覽表》各校規定。"
        )
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}臺師大英歐語組基準門檻 {minimum:g}。{warning}",
        )
    if test == "jlpt":
        passed = 1.0 <= language_score <= 3.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}臺師大日語組姊妹校常見門檻範圍（N1–N3；多數日本國立及重點私大要求 N1 或 N2，請對照一覽表各校規定）。",
        )
    if test == "topik":
        passed = 2.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}臺師大韓語組姊妹校常見門檻範圍（TOPIK 2–6 級，請對照一覽表各校規定）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請核對臺師大《116-1 赴外交換學校一覽表》所屬語組（英歐語組／日語組／韓語組／中文組）與目標學校之單科及級數要求。",
    )
