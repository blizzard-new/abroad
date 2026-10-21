from __future__ import annotations

import re

from .university_registry import YUNTECH, resolve_university

YUNTECH_OIA_HUB_URL = "https://tdx.yuntech.edu.tw/"
YUNTECH_OE_PORTAL_URL = "https://admissions-oia.yuntech.edu.tw/oe/index/index/puid/115-2/lang/zh_TW"
YUNTECH_OE_INTRO_115_2_URL = 'https://admissions-oia.yuntech.edu.tw/oe/index/intro.school/puid/115-2'
YUNTECH_OUTBOUND_NON_MAINLAND_URL = 'https://tdx.yuntech.edu.tw/index.php/2020-02-26-09-23-21/item/1144-2021-12-09-06-40-33'
YUNTECH_MAINLAND_2027S_URL = 'https://tdx.yuntech.edu.tw/index.php/newsclass/2020-03-05-07-13-34/item/1432-2026-114-2'
YUNTECH_APPLY_2027S_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1413-2027"
YUNTECH_ROSTER_2027S_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1472-2027"
YUNTECH_EXCHANGE_GUIDELINES_URL = 'https://tdx.yuntech.edu.tw/index.php/2020-02-26-09-23-21/item/download/2710_976089c1dacc28aecc1f4d7a4caf699c'
YUNTECH_SCORING_RUBRIC_URL = 'https://tdx.yuntech.edu.tw/index.php/2020-02-26-09-23-21/item/download/2711_51d8afaa5fcc22bf6ef55a9ed56db372'
YUNTECH_SLIDES_2027S_URL = "https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Non_mainland_China_area/2027%E6%98%A5%E5%AD%A3(115-2)%E8%B5%B4%E9%9D%9E%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E7%B0%A1%E5%A0%B1.pdf"
YUNTECH_GRANT_PAGE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E7%8D%8E%E5%8A%A9%E5%AD%B8%E9%87%91/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81%E6%88%96%E9%80%B2%E4%BF%AE%E8%A3%9C%E5%8A%A9/115%E5%B9%B4%E5%BA%A6"
YUNTECH_SUBSIDY_RULES_URL = 'https://tdx.yuntech.edu.tw/index.php/2020-02-26-09-23-21/item/download/3204_a8f4eca3ef03d9b08d78596d65c23b71'
YUNTECH_WANG_PAGE_URL = 'https://tdx.yuntech.edu.tw/index.php/2020-02-26-09-23-21/item/300-2021-07-28-07-27-14'
YUNTECH_WANG_RULES_URL = 'https://tdx.yuntech.edu.tw/index.php/2020-02-26-09-23-21/item/download/2123_8e3e890c9bc3db3084498d98540b43b9'
YUNTECH_XUEHAI_PAGE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1400-115"
YUNTECH_XUEHAI_RULES_URL = "https://tdx.yuntech.edu.tw/images/Scholarship/%E5%AD%B8%E6%B5%B7%E7%B3%BB%E5%88%97/%E5%9C%8B%E7%AB%8B%E9%9B%B2%E6%9E%97%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E3%80%8C%E5%AD%B8%E6%B5%B7%E9%A3%9B%E9%A2%BA%E3%80%8D%E8%88%87%E3%80%8C%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E3%80%8D%E5%B0%88%E6%A1%88%E6%8E%A8%E8%96%A6%E4%BD%9C%E6%A5%AD%E8%A6%81%E9%BB%9E1130422%E4%BF%AE%E8%A8%82%E9%80%9A%E9%81%8E.pdf"
YUNTECH_DUAL_DEGREE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D"
YUNTECH_PATHWAY_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E9%8A%9C%E6%8E%A5%E5%AD%B8%E4%BD%8D"
YUNTECH_EXP_115_URL = "https://tdx.yuntech.edu.tw/index.php/expsharing/item/1401-115"

YUNTECH_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_yuntech(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == YUNTECH.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立雲林科技大學",
      "雲林科技大學",
      "雲科大",
      "yuntech",
      "nyust",
      "national yunlin university of science and technology",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def yuntech_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    from .yuntech_source_review import DEGREE
    degree, year = degree_level or "", current_year or ""
    if any(s in degree for s in ("學分班", "休學")):
        return "fail", "須為正式在學生並於交換期間完成註冊。"
    if not _is_graduate(degree) and year == "大一上":
        return "fail", "校級交換大學部須入學一學期以上。"
    if not degree or "延畢" in year or (not _is_graduate(degree) and year not in {"大一下", "大二", "大三", "大四"} and "在職" not in degree):
        return "needs_confirmation", DEGREE
    return "pass", "僅就已填學制／年級符合通則；仍須確認在學、核准與接待校條件。" + DEGREE


def yuntech_academic_check(
    degree_level: str | None, academic_score: float | None,
    academic_gpa: float | None = None, class_rank_percent: float | None = None,
) -> tuple[str, str]:
    from .yuntech_source_review import ACADEMIC
    numeric = ((academic_score is not None and academic_score >= 75) or
               (class_rank_percent is not None and 0 < class_rank_percent <= 50))
    return "needs_confirmation", ("已填學業或班排達通則數值，仍缺操行與適用證據。" if numeric else
        "需確認百分制成績或班排、操行及優秀表現特例；GPA不能自行換算。") + ACADEMIC


def yuntech_language_check(
    language_test: str | None, language_score: float | None, *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    from .yuntech_source_review import LANGUAGE
    return "needs_confirmation", LANGUAGE
