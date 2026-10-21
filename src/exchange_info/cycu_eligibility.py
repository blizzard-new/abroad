from __future__ import annotations

import re

from .university_registry import CYCU, resolve_university

CYCU_OUTBOUND_URL = "https://oia.cycu.edu.tw/?p=6336"
CYCU_APPLY_PORTAL_URL = "https://oia.cycu.edu.tw/?page_id=2968&lang=zh"
CYCU_QUOTALIST_URL = "https://oia.cycu.edu.tw/?page_id=10128&lang=zh"
CYCU_MAINLAND_URL = "https://oia.cycu.edu.tw/?p=6340&lang=zh"
CYCU_REGULATION_URL = "https://oia.cycu.edu.tw/wp-content/uploads/sites/2/2025/09/%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E9%81%B8%E9%80%81%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95.pdf"

CYCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_cycu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == CYCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "中原大學",
        "中原",
        "cycu",
        "chung yuan christian university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def cycu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree, year = (degree_level or "").strip(), (current_year or "").strip()
    if not degree or not year:
        return "needs_confirmation", "須確認在學身分、實際就讀學期、轉學及提前畢業狀態，僅有學制不足以判定。"
    if any(x in degree for x in ("在職", "進修", "推廣")):
        return "needs_confirmation", "本輪已讀當期公告未列在職或進修學生一律不得申請，須核對學制及所屬計畫。"
    if any(x in year for x in ("大一", "大學一年級", "學士班一年級")):
        return "fail", "當期公告排除大一新生，轉學生亦須在本校就讀滿一年。"
    if _is_graduate(degree) and any(x in year for x in ("碩一", "博一", "一年級")):
        return "needs_confirmation", "一般介紹要求就讀兩學期，但當期公告的排除名單未明列研究所新生；須確認目前學制適用性。"
    return "pass", "符合已填學制與年級的一般範圍；仍須確認轉學就讀滿一年、未申請當學期提前畢業及交換期間維持學籍。"


def cycu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    if academic_gpa is not None and academic_gpa >= 3.0:
        return "pass", "已填GPA達3.0，符合當期公告的一般成績要求；建築系另須系排名前50%及建築設計一至六全數修畢及格，接待校條件另核。"
    if class_rank_percent is not None and not 0 < class_rank_percent <= 100:
        return "needs_confirmation", "請提供成績單上有效的歷年系排名百分比。"
    if class_rank_percent is not None and class_rank_percent <= 30:
        return "needs_confirmation", "一般介紹／文件頁列GPA3.0或系排前30%，但當期國際二梯與大陸公告均將GPA3.0列為必備；僅靠排名是否可申請須向中原確認。"
    if academic_gpa is not None and class_rank_percent is not None:
        return "fail", "已填GPA未達3.0且系排名不在前30%；百分制平均75分不能代替任一官方條件，特殊系所另核。"
    return "needs_confirmation", "須提供GPA及／或歷年系排名；不得把平均75分換成GPA3.0。當期GPA必備與一般頁面排名替代的差異仍待校方確認。"


def cycu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return "pass", "母校大陸組申請文件清單未列外語檢定；這僅是母校文件要求，不代表接待校或特定課程免除語言條件。"
    return "needs_confirmation", "母校要求依所申請姊妹校提交有效正式語檢，沒有可共用的TOEFL61／IELTS5.5／TOEIC600門檻；須按方案核對學制、授課語言、單項成績與效期。"
