from __future__ import annotations

import re

from .university_registry import NYCU, resolve_university

NYCU_OUTBOUND_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0006&id=286"
NYCU_PORTAL_URL = "https://oia-sys.nycu.edu.tw/outgoing"
NYCU_QUOTA_SHEET_URL = "https://docs.google.com/spreadsheets/d/1MjFpOfI77e4-yQWc3dHuukoR9MJB6ZndldtSFfXiyj4/edit?gid=1079257447"
NYCU_CONTRACTS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1XGeMX1F-niYApCrtge7n5f_YfsLZ1uZrp3ckdp-35UQ/edit?usp=sharing"
NYCU_DUAL_DEGREE_SHEET_URL = "https://docs.google.com/spreadsheets/d/10zt_cwrlv7HvZ6evw5NkIhS1tHhMjaxaUSB896nJBJ0/edit?usp=sharing"
NYCU_115_2_GUIDELINES_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1501852894511501312&type=s"
NYCU_115_1_GUIDELINES_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1442785684455690240&type=s"
NYCU_REGULATIONS_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1501852894452781056&type=s"
NYCU_SCHOLARSHIP_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0007&id=300"
NYCU_EXPERIENCE_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0008&id=307"
NYCU_UST_NOTICE_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1552119722735046656&type=s"

# No school-wide numeric score may substitute for the chosen program.
NYCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_nycu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NYCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立陽明交通大學",
        "陽明交通大學",
        "陽明交大",
        "國立交通大學",
        "國立陽明大學",
        "nycu",
        "nctu",
        "ym",
        "yang ming chiao tung university",
        "national yang ming chiao tung university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nycu_degree_check(degree_level: str | None, current_year: str | None = None) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if "系統工程與科技" in degree:
        return "needs_confirmation", "此學程由國防部專案辦理，不適用校級一般交換辦法。"
    if not degree or "在職" in degree:
        return "needs_confirmation", "須確認正式學籍、所選計畫與接待校學制；不能用獎學金排除規則推定交換資格。"
    if not _is_graduate(degree):
        if year in {"大一", "一年級", "1"}:
            return "fail", "115-2校級簽核表明列大一新生不得申請；台聯大116計畫亦限大二以上，各計畫依當期文件。"
        if year not in {"大二", "大三", "大四", "大五", "大六", "二年級", "三年級", "四年級", "五年級", "六年級", "2", "3", "4", "5", "6", "延畢"}:
            return "needs_confirmation", "尚不能確認年級符合所選計畫；不得因學制有填便視為大二以上。"
    return "pass", "所填學制年級未觸及115-2校級簽核表的大一排除；正式學籍及各接待校院系／年級仍須逐項確認。此項不代表台聯大各方案或獎學金資格。"


def nycu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    return (
        "needs_confirmation",
        "校級交換60分是含成績、語言、自傳等項目的書面審查總分，不能用平均70、GPA2.7或排名50%代換，也不能因平均低於60就判定書審不及格。接待校另訂條件。116台聯大要求前一學年平均GPA3.0或B，現有欄位未確認計算期間，不能以累計GPA自動通過。",
    )


def nycu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country == "中國大陸":
        return "pass", "112年修訂校級辦法僅對國外及港澳規定共同語檢文件；此項只代表校內一般規則，接待校／個別計畫語言資格仍待確認。"
    return (
        "needs_confirmation",
        "校級赴國外／港澳須語檢證明，沒有共同TOEFL79、IELTS6或TOEIC785通過門檻；TOEIC須含口說與寫作，第三外語須為志願校接受。新版TOEFL計分亦須確認。116台聯大依各方案及兩年效期要求，香港中文大學暑期不需英檢；不能套學期方案或只憑國家／分數判定通過。",
    )
