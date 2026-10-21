from __future__ import annotations

import re

from .university_registry import NTOU, resolve_university

NTOU_OIA_HUB_URL = "https://oia.ntou.edu.tw/"
NTOU_OUTBOUND_OVERVIEW_URL = "https://oia.ntou.edu.tw/p/412-1022-6958.php?Lang=zh-tw"
NTOU_EXCHANGE_PLAN_URL = "https://oia.ntou.edu.tw/p/412-1022-10817.php?Lang=zh-tw"
NTOU_DUAL_DEGREE_URL = "https://oia.ntou.edu.tw/p/412-1022-8671.php?Lang=zh-tw"
NTOU_DUAL_DEGREE_XLSX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/973/663723575.xlsx"
NTOU_XUEHAI_OVERVIEW_URL = "https://oia.ntou.edu.tw/p/412-1022-10818.php?Lang=zh-tw"
NTOU_XUEHAI_FEIYANG_URL = "https://oia.ntou.edu.tw/p/412-1022-10819.php?Lang=zh-tw"
NTOU_XUEHAI_XIZHU_URL = "https://oia.ntou.edu.tw/p/412-1022-10820.php?Lang=zh-tw"
NTOU_XUEHAI_ZHUMENG_URL = "https://oia.ntou.edu.tw/p/412-1022-10821.php?Lang=zh-tw"
NTOU_BROCHURE_2027_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/779655790.pdf"
NTOU_GUIDELINES_LANG_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/854516693.pdf"
NTOU_ENFORCEMENT_RULES_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/777268759.pdf"
NTOU_XUEHAI_RULES_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/830669231.pdf"
NTOU_MOE_XUEHAI_115_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/380374043.pdf"
NTOU_APP_CHECKLIST_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/892749589.pdf"
NTOU_AUTOBIO_EX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/764741202.pdf"
NTOU_STUDY_PLAN_EX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/288285085.pdf"
NTOU_BUDGET_EX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/814897101.pdf"
NTOU_PRE_DEPARTURE_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/705516691.pdf"
NTOU_REIMBURSEMENT_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/765889941.pdf"
NTOU_SOP_EXCHANGE_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/972/484468333.pdf"
NTOU_SOP_DUAL_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/972/757675578.pdf"
NTOU_MAINLAND_115_2_URL = "https://oia.ntou.edu.tw/p/406-1022-70577,r11.php?Lang=zh-tw"
NTOU_SISTER_SCHOOLS_URL = "https://oia.ntou.edu.tw/p/412-1022-6904.php?Lang=zh-tw"
NTOU_EXP_SHARING_URL = "https://oia.ntou.edu.tw/p/404-1022-86719.php?Lang=zh-tw"

NTOU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_ntou(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NTOU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立臺灣海洋大學",
      "國立台灣海洋大學",
      "臺灣海洋大學",
      "台灣海洋大學",
      "海洋大學",
      "海大",
      "ntou",
      "national taiwan ocean university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def ntou_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    from .ntou_source_review import DEGREE
    degree, year = degree_level or "", current_year or ""
    if any(s in degree for s in ("休學", "學分班")):
        return "fail", "申請及赴外研修期間均須為正式註冊在學生。"
    if not _is_graduate(degree) and year == "大一上":
        return "fail", "通則第4點排除大一上新生。"
    return "needs_confirmation", DEGREE + "需確認本學期是否畢業、研修期間學籍及各項同意。"


def ntou_academic_check(
    degree_level: str | None, academic_score: float | None,
    academic_gpa: float | None = None, class_rank_percent: float | None = None,
) -> tuple[str, str]:
    from .ntou_source_review import ACADEMIC
    return "needs_confirmation", ACADEMIC + "目前未取得前一學期成績期間及接待校適用要求，不能自動判定。"


def ntou_language_check(
    language_test: str | None, language_score: float | None, *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    from .ntou_source_review import LANGUAGE
    return "needs_confirmation", LANGUAGE
