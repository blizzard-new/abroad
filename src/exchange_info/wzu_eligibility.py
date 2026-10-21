from __future__ import annotations

import math
import re

from .university_registry import WZU, resolve_university

WZU_OICC_HUB_URL = "https://c015.wzu.edu.tw/"
WZU_IED_HUB_URL = "https://d020.wzu.edu.tw/"
WZU_OUTBOUND_GUIDE_URL = "https://d020.wzu.edu.tw/article/492285"
WZU_R1_ANNOUNCEMENT_URL = "https://d020.wzu.edu.tw/article/529354"
WZU_R2_ANNOUNCEMENT_URL = "https://d020.wzu.edu.tw/article/530752"
WZU_R1_115_1_ANNOUNCEMENT_URL = "https://d020.wzu.edu.tw/article/524735"
WZU_PARTNER_INFO_URL = "https://d020.wzu.edu.tw/category/154399"
WZU_EXP_ALBUM_URL = "https://d020.wzu.edu.tw/album/list/152198"
WZU_UMAP_URL = "https://d020.wzu.edu.tw/article/517638"
WZU_ACUCA_URL = "https://d020.wzu.edu.tw/article/517642"
WZU_SCHOLARSHIP_HUB_URL = "https://d020.wzu.edu.tw/category/152197"
WZU_REGULATIONS_URL = "https://d020.wzu.edu.tw/category/152182"
WZU_SOSA_URL = "https://d020.wzu.edu.tw/category/152202"

WZU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_wzu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == WZU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "文藻外語大學",
      "文藻外語學院",
      "文藻外大",
      "文藻",
      "wzu",
      "wenzao",
      "wenzao ursuline university of languages",
  }


def wzu_degree_check(degree_level: str | None, current_year: str | None = None,
                     *, program_type: str | None = None) -> tuple[str, str]:
    from .wzu_source_review import DEGREE
    degree, year = (degree_level or "").strip(), (current_year or "").strip()
    if "在職" in degree or "休學" in degree:
        return "fail", "115-2不含在職專班，申請及出訪均須在學。" + DEGREE
    if not degree or not year:
        return "needs_confirmation", "尚缺學制、年級及學期資料。" + DEGREE
    if "轉" in degree or any(x in degree for x in ("碩", "博", "研究")):
        return "needs_confirmation", "須確認已在文藻就讀滿一學期；研究生的二招修課學分例外須向承辦確認。" + DEGREE
    if "二技" in degree:
        if year in {"四年級", "四上", "四下", "4"}:
            return "pass", "申報年級達二技共同最低年級；另查在學及學分條件。" + DEGREE
        return "needs_confirmation", "二技三年級須區分本校五專直升身分與上／下學期。" + DEGREE
    if "五專" in degree or year.startswith("專"):
        if year in {"專一", "專二", "一年級", "二年級", "1", "2", "三上"}:
            return "fail", "尚未達五專三下申請門檻。" + DEGREE
        if year in {"專三", "三年級", "3", "三下"}:
            if "日語" in (program_type or ""):
                return "fail", "日語組不收五專三年級（含）以下。" + DEGREE
            return "needs_confirmation", "五專須確認已三下；日語組另有較高年級限制。" + DEGREE
        if year in {"專四", "專五", "四年級", "五年級", "4", "5"}:
            return "pass", "申報年級達五專門檻；另查在學及學分條件。" + DEGREE
        return "needs_confirmation", DEGREE
    if any(x in degree for x in ("學士", "大學", "四技")):
        if year in {"大一", "一年級", "1", "一下", "一年級下學期"}:
            return "needs_confirmation", "四技一下即可申請，不能把所有大一學生判為不合格；須確認學期及出訪年級。" + DEGREE
        if year in {"一上", "一年級上學期"}:
            return "fail", "尚未達四技一下申請門檻。" + DEGREE
        if year in {"大二", "大三", "大四", "二年級", "三年級", "四年級", "2", "3", "4", "延畢"}:
            return "pass", "申報年級達四技最低年級；另查在學、修課學分及出訪身分。" + DEGREE
    return "needs_confirmation", DEGREE


def wzu_academic_check(degree_level: str | None, academic_score: float | None,
                       academic_gpa: float | None = None, class_rank_percent: float | None = None,
                       *, program_type: str | None = None) -> tuple[str, str]:
    from .wzu_source_review import ACADEMIC
    if academic_score is None or not math.isfinite(academic_score):
        return "needs_confirmation", "須提供歷年百分制總平均，GPA或排名不能替代。" + ACADEMIC
    score = math.floor(academic_score)
    kind = program_type or ""
    minimum = 65 if "語言學習組" in kind else 70 if "一般組" in kind else None
    if minimum is None:
        status = "pass" if score >= 70 else "fail" if score < 65 else "needs_confirmation"
    else:
        status = "pass" if score >= minimum else "fail"
    return status, f"歷年平均{academic_score:g}分，認列{score}分；僅判斷所選組別學業門檻，操行及接待校條件另查。" + ACADEMIC


def wzu_language_check(language_test: str | None, language_score: float | None,
                       *, partner_country: str | None = None) -> tuple[str, str]:
    from .wzu_source_review import LANGUAGE
    return "needs_confirmation", LANGUAGE + "本項待核對接待校要求及正式證明，沒有語檢不代表初審報名不合格。"
