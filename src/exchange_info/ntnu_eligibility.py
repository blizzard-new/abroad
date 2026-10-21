from __future__ import annotations

import re

from .university_registry import NTNU, resolve_university

NTNU_OUTBOUND_URL = "https://bds.oia.ntnu.edu.tw/bds/web/OUT"
NTNU_APPLY_PORTAL_URL = "https://bds.oia.ntnu.edu.tw/bds/OE"
NTNU_QUOTALIST_URL = "https://bds.oia.ntnu.edu.tw/bds/web/OUT-QUOTALIST"
NTNU_GUIDELINE_1161_URL = "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf"
NTNU_REGULATION_URL = "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_%E5%9C%8B%E7%AB%8B%E8%87%BA%E7%81%A3%E5%B8%AB%E7%AF%84%E5%A4%A7%E5%AD%B8%E8%B5%B4%E5%A4%96%E4%BA%A4%E6%8F%9B%E7%94%9F%E7%94%84%E9%81%B8%E4%BD%9C%E6%A5%AD%E8%A6%81%E9%BB%9E20190903.pdf"

# Official rules defer language thresholds to each host and programme.
NTNU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


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
    return (
        "needs_confirmation",
        "臺師大當期簡章未列全校統一60分或GPA2.0門檻；學業及相關表現占甄選30%（含EMI修課5%），申請資格須逐一核對所選合作校學程要求，不能用一般及格分數判定通過或不符。",
    )


def ntnu_language_check(
    language_test: str | None,
    language_score: float | None,
    *, partner_country: str | None = None, program_type: str | None = None,
) -> tuple[str, str]:
    if program_type and "中文組" in program_type:
        return "pass", "簡章文件清單對中文組免附語言能力證明；僅確認校內文件要求，合作校課程條件仍須核對。"
    return (
        "needs_confirmation",
        "臺師大依所選合作校及語組審核語言條件，沒有此簡章支持的統一TOEFL61、IELTS5.5或TOEIC門檻；須核對個別學程及有效期限，不得只憑目的地國家推定免附語檢。",
    )
