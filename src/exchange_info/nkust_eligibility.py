from __future__ import annotations

import re

from .university_registry import NKUST, resolve_university

NKUST_OIA_HUB_URL = "https://oia.nkust.edu.tw/"
NKUST_EXCHANGE_PAGE_URL = "https://oia.nkust.edu.tw/unit-4-374-21.html"
NKUST_SCHOLARSHIP_PAGE_URL = "https://oia.nkust.edu.tw/unit-4-377-45.html"
NKUST_SHORT_TERM_PAGE_URL = "https://oia.nkust.edu.tw/unit-4-352-39.html"
NKUST_GS_PORTAL_URL = "https://sites.google.com/nkust.edu.tw/exchange-student/"
NKUST_115_GUIDELINES_URL = "https://oia.nkust.edu.tw/images/upload/files/115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E7%94%9F%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A02025_12_02(1).pdf"
NKUST_115_PREF_FORM_URL = "https://oia.nkust.edu.tw/images/upload/files/115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E7%A0%94%E4%BF%AE%E5%BF%97%E9%A1%98%E8%A1%A8(2).docx"
NKUST_115_UNI_SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZdfUgev-p_N35eh2mD-vF7rH7iH8zJ3O/edit?gid=142150725#gid=142150725"
NKUST_COLLEGE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZdfUgev-p_N35eh2mD-vF7rH7iH8zJ3O/edit?gid=1014746314#gid=1014746314"
NKUST_REGULATIONS_URL = "https://oia.nkust.edu.tw/images/upload/files/%E5%9C%8B%EF%A7%97%E9%AB%98%E9%9B%84%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E5%A4%A7%E5%AD%B8%E6%A0%A1%E9%99%A2%E4%BA%A4%E6%8F%9B%E7%A0%94%E4%BF%AE%E4%BD%9C%E6%A5%AD%E8%A6%81%E9%BB%9E.pdf"
NKUST_SCHOLARSHIP_REG_URL = "https://oia.nkust.edu.tw/images/upload/files/%E5%9C%8B%E7%AB%8B%E9%AB%98%E9%9B%84%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E7%8D%8E%E5%8A%A9%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E5%A4%A7%E5%AD%B8%E6%A0%A1%E9%99%A2%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E(4).pdf"
NKUST_FLEC_CEF_URL = "https://flec.nkust.edu.tw/var/file/46/1046/img/581/277450219.pdf"
NKUST_116_INFO_SESSION_URL = "https://oia.nkust.edu.tw/news_det-980.html"

NKUST_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_nkust(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NKUST.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立高雄科技大學",
      "高雄科技大學",
      "高科大",
      "nkust",
      "national kaohsiung university of science and technology",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def nkust_degree_check(
    degree_level: str | None, current_year: str | None = None, *,
    program_type: str | None = None, academic_year: str | None = None,
) -> tuple[str, str]:
    from .nkust_source_review import DEGREE
    degree, year = degree_level or "", current_year or ""
    if "休學" in degree or "學分班" in degree:
        return "fail", "交換申請及研修期間須有正式在學學籍；非在學身分不符合。"
    if "專" in degree and year in {"專一", "專二", "專三", "五專一", "五專二", "五專三"}:
        return "fail", "通則要求五專四年級以上。"
    if academic_year == "115" and "校級" in (program_type or "") and not _is_graduate(degree) and year in {"大一", "一年級", "1"}:
        return "fail", "115校級簡章要求大學部二年級以上；其他年度及院系級須另確認。"
    return "needs_confirmation", DEGREE + "目前年級資訊不足以證明已具本學制一學期成績及當期甄選資格。"


def nkust_academic_check(
    degree_level: str | None, academic_score: float | None,
    academic_gpa: float | None = None, class_rank_percent: float | None = None,
) -> tuple[str, str]:
    from .nkust_source_review import ACADEMIC
    return "needs_confirmation", ACADEMIC + "需確認本學制成績、操行與個別接待校標準。"


def nkust_language_check(
    language_test: str | None, language_score: float | None, *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    from .nkust_source_review import LANGUAGE
    return "needs_confirmation", LANGUAGE
