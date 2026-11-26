"""Core data aggregation, conversion formulas, schemas, and .ics generation for Wave 1 SEO tools & data pages.

All school, quota, language threshold, and deadline figures are strictly derived from UniWay's
existing verified/sourced repositories without fabricating unannounced values.
"""
from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from html import escape
from typing import Any, Literal
from urllib.parse import quote, urlencode, urlsplit
from zoneinfo import ZoneInfo

from . import api as _api_mod
from .cost_estimates import fx_reference
from .destination_tips import canonical_country
from .models import (
    ApplicationPeriodDateStatus,
    ApplicationPeriodItem,
    ApplicationPeriodStatus,
    CatalogueSourceStatus,
    PartnerUniversity,
)
from .school_identity import school_identity_key
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university
from .verified_window_deadlines import (
    CATALOG_LAST_CHECKED_AT,
    get_verified_school_window_card,
)

TAIPEI_TZ = ZoneInfo("Asia/Taipei")

MANDATORY_DISCLAIMER = "實際資格、名額與期限以各校最新官方公告為準。"

# Strictly enforced forbidden phrases from Shared/uniway/共同規則.md
FORBIDDEN_TERMS: tuple[str, ...] = (
    "保證錄取",
    "保證上",
    "一定上",
    "穩上",
    "100%錄取",
    "百分百錄取",
    "官方授權",
    "官方合作",
    "學校指定",
    "最便宜",
    "全台唯一",
    "讓我們",
    "總而言之",
    "綜上所述",
    "總的來說",
    "總結來說",
    "簡而言之",
    "一言以蔽之",
    "值得一提的是",
    "值得注意的是",
    "需要注意的是",
    "不可否認",
    "毋庸置疑",
    "毫無疑問",
    "眾所周知",
    "在當今社會",
    "在當今時代",
    "與此同時",
    "深入探討",
    "全面解析",
    "深度解析",
    "賦能",
    "希望這篇",
    "希望對你有幫助",
)


@dataclass(frozen=True)
class PageMetaSpec:
    path: str
    slug: str
    kind: Literal["tool_hub", "tool", "data_hub", "data"]
    short_title: str
    title: str
    h1: str
    description: str
    core_conclusion: str  # Must be 40-60 chars


WAVE1_SPECS: dict[str, PageMetaSpec] = {
    "/tools": PageMetaSpec(
        path="/tools",
        slug="tools",
        kind="tool_hub",
        short_title="交換免費工具總覽",
        title="交換學生免費實用工具箱｜ECTS學分、GPA、語言門檻、預算與時程試算｜UniWay",
        h1="UniWay 交換學生免費實用工具總覽",
        description="免登入線上換算歐洲 ECTS 學分、台灣大學 GPA 與德國巴伐利亞公式、IELTS/TOEFL/TOEIC/JLPT 語言門檻、交換預算匯率敏感度及申請倒推時程行事曆。",
        core_conclusion="免登入交換工具箱整合學分、GPA、語言門檻、預算與倒推時程五大試算功能，實際資格與期限以各校最新官方公告為準。",
    ),
    "/tools/ects-credit-converter": PageMetaSpec(
        path="/tools/ects-credit-converter",
        slug="ects-credit-converter",
        kind="tool",
        short_title="ECTS 學分換算器",
        title="歐洲 ECTS 學分換算器｜台灣、美國、日本學分對照與最低修課試算｜UniWay",
        h1="歐洲 ECTS ↔ 台灣／美國／日本學分換算器",
        description="即時換算歐洲 ECTS 與台灣學分、美國學期學分及日本単位，試算交換期間母校與姊妹校最低修課門檻及建議選課門數。",
        core_conclusion="歐洲全日制一學期標準為 30 ECTS，台灣與美國多以 2 ECTS 折算 1 學分，實際抵免以各校最新官方公告為準。",
    ),
    "/tools/gpa-converter": PageMetaSpec(
        path="/tools/gpa-converter",
        slug="gpa-converter",
        kind="tool",
        short_title="台灣大學 GPA 換算器",
        title="台灣大學 GPA 換算器｜百分制 ↔ 4.0 ↔ 4.3 與德國巴伐利亞公式試算｜UniWay",
        h1="台灣大學 GPA 換算器（百分制 ↔ 4.0 ↔ 4.3 ＋ 德國巴伐利亞公式）",
        description="支援台灣各大學百分制成績、4.3 制與 4.0 制 GPA 雙向對照、德國交換必備巴伐利亞公式計算，以及多科目學分加權精算。",
        core_conclusion="出國交換常需將台灣百分制或 4.3 制換算為 4.0 制與德國巴伐利亞公式分數，實際採計標準以各校最新官方公告為準。",
    ),
    "/tools/language-score-converter": PageMetaSpec(
        path="/tools/language-score-converter",
        slug="language-score-converter",
        kind="tool",
        short_title="語言檢定換算與選校查詢",
        title="語言檢定分數換算器｜IELTS・TOEFL・TOEIC・CEFR・JLPT 對照與合作校查詢｜UniWay",
        h1="語言檢定分數換算器（連動母校合作校門檻資料庫）",
        description="對照 IELTS、TOEFL iBT、TOEIC、CEFR 與日檢 JLPT 級距，選擇就讀母校即可即時統計資料庫中列載達標的海外合作校數量與清單。",
        core_conclusion="提供雅思、托福、多益、CEFR 與日檢分數對照，並連動母校資料庫篩選合作校門檻，實際申請資格以各校最新官方公告為準。",
    ),
    "/tools/exchange-budget-calculator": PageMetaSpec(
        path="/tools/exchange-budget-calculator",
        slug="exchange-budget-calculator",
        kind="tool",
        short_title="交換學生預算試算器",
        title="交換學生一學期預算試算器｜12 國費用模板與 ±10% 匯率波動情境｜UniWay",
        h1="交換學生預算試算器（多國模板＋±10% 匯率波動試算）",
        description="依交換國家與月數估算住宿、飲食、交通、機票簽證保險及獎學金折抵，內建正負 10% 匯率敏感度情境表並支援一鍵分享預算明細。",
        core_conclusion="交換學生預算應分列月生活費、機票簽證保險與正負 10% 匯率波動緩衝並扣除補助，實際收費標準以各校最新官方公告為準。",
    ),
    "/tools/timeline-generator": PageMetaSpec(
        path="/tools/timeline-generator",
        slug="timeline-generator",
        kind="tool",
        short_title="交換申請倒推時程產生器",
        title="交換學生申請倒推時程表產生器｜全台 71 校截止日連動與 .ics 行事曆下載｜UniWay",
        h1="交換申請倒推時程表產生器（支援下載 .ics 行事曆）",
        description="選擇台灣母校與預計出發學期，自動倒推語檢報考、推薦信邀約、讀書計畫定稿與校內送件節點，一鍵匯出標準 iCalendar 行事曆檔。",
        core_conclusion="選定母校與出發學期即可自動倒推語檢、推薦信、讀書計畫與校內送件節點並匯出行事曆，實際截止期限以各校最新官方公告為準。",
    ),
    "/data": PageMetaSpec(
        path="/data",
        slug="data",
        kind="data_hub",
        short_title="台灣交換公開數據總覽",
        title="台灣大學生出國交換公開數據中心｜全台 71 校合作規模與截止日統計｜UniWay",
        h1="UniWay 台灣交換學生公開數據總覽",
        description="由全台 71 所大專校院國際處公開資料自動彙整之年度交換數據庫，提供各校海外姊妹校規模、國家分布與校內申請截止日總表。",
        core_conclusion="公開數據頁自動彙整全台 71 所大學海外合作校規模、國家分布與校內截止日，實際資格、名額與期限以各校最新官方公告為準。",
    ),
    "/data/taiwan-exchange-overview": PageMetaSpec(
        path="/data/taiwan-exchange-overview",
        slug="taiwan-exchange-overview",
        kind="data",
        short_title="全台 71 校交換資源總覽表",
        title="全台 71 所大學交換資源總覽表｜各校海外姊妹校數、國家數與語檢門檻統計｜UniWay",
        h1="全台 71 所大學交換資源總覽表",
        description="直接由 UniWay 資料庫計算全台 71 所公私立大學之海外合作校頁面數、涵蓋國家地區數、語言門檻列載分布與國際處官方來源連結。",
        core_conclusion="由資料庫自動統計全台 71 所大學海外合作校數、涵蓋國家與語檢門檻分布，實際資格、名額與期限以各校最新官方公告為準。",
    ),
    "/data/deadlines": PageMetaSpec(
        path="/data/deadlines",
        slug="deadlines",
        kind="data",
        short_title="全台 71 校交換截止日總表",
        title="全台 71 校交換學生校內申請截止日行事曆總表｜依月份與學校查詢｜UniWay",
        h1="全台 71 校交換校內申請截止日行事曆總表",
        description="彙整全台 71 所大學出國交換校內甄選期限、受理狀態、核對日期與官方簡章連結，支援依申請月份、學校屬性與關鍵字快速篩選。",
        core_conclusion="彙整全台 71 所大學校級交換線上申請期限、送件狀態與國際處官方簡章連結，實際資格、名額與期限以各校最新官方公告為準。",
    ),
}

WAVE1_PATHS: tuple[str, ...] = tuple(WAVE1_SPECS.keys())

for _path, _spec in WAVE1_SPECS.items():
    if not (40 <= len(_spec.core_conclusion) <= 60):
        raise ValueError(f"{_path} core_conclusion length {len(_spec.core_conclusion)} must be 40..60")


def safe_https_or_http_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        parsed = urlsplit(url.strip())
    except ValueError:
        return None
    if parsed.scheme in {"https", "http"} and parsed.hostname and not parsed.username and not parsed.password:
        return url.strip()
    return None


def is_public_university(u: UniversityProfile) -> bool:
    return u.school_name.startswith(("國立", "臺北市立", "高雄市立"))


def partner_group_id(partner: PartnerUniversity) -> str:
    import hashlib
    identity = f"{partner.country or ''}|{school_identity_key(partner.school_name)}"
    return hashlib.sha256(identity.encode()).hexdigest()[:20]


def web_application_schema(origin: str, spec: PageMetaSpec) -> dict[str, Any]:
    url = origin + spec.path
    return {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "@id": url + "#webapp",
        "name": spec.h1,
        "url": url,
        "description": spec.description,
        "applicationCategory": "EducationalApplication",
        "operatingSystem": "All",
        "browserRequirements": "支援無 JavaScript 伺服器完整輸出；啟用瀏覽器腳本可即時互動試算",
        "inLanguage": "zh-Hant",
        "isAccessibleForFree": True,
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "TWD",
        },
        "publisher": {
            "@type": "Organization",
            "@id": origin + "/#organization",
            "name": "UniWay",
            "url": origin + "/",
        },
    }


def dataset_schema(
    origin: str,
    spec: PageMetaSpec,
    *,
    variables: Sequence[str],
    keywords: Sequence[str],
    date_modified: str = CATALOG_LAST_CHECKED_AT,
) -> dict[str, Any]:
    url = origin + spec.path
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "@id": url + "#dataset",
        "name": spec.h1,
        "description": f"{spec.description} {MANDATORY_DISCLAIMER}",
        "url": url,
        "inLanguage": "zh-Hant",
        "isAccessibleForFree": True,
        "license": origin + "/editorial-policy",
        "dateModified": date_modified,
        "keywords": list(keywords),
        "variableMeasured": list(variables),
        "creator": {
            "@type": "Organization",
            "@id": origin + "/#organization",
            "name": "UniWay",
            "url": origin + "/",
        },
        "publisher": {
            "@type": "Organization",
            "@id": origin + "/#organization",
            "name": "UniWay",
            "url": origin + "/",
        },
    }


def faq_page_schema(origin: str, path: str, faqs: Sequence[tuple[str, str]]) -> dict[str, Any]:
    url = origin + path
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": url + "#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a,
                },
            }
            for q, a in faqs
        ],
    }


def render_core_summary_and_citation_box(origin: str, spec: PageMetaSpec, *, checked_date: str | None = None) -> str:
    today_str = checked_date or datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    full_url = origin + spec.path
    citation_text = (
        f"UniWay（2026）。《{spec.h1}》。取自 {full_url}"
        f"（資料檢索日期：{today_str}；{MANDATORY_DISCLAIMER}）"
    )
    return f"""<section class="uw-summary-cite-card" aria-label="核心結論與引用格式">
  <div class="uw-core-conclusion">
    <span class="uw-badge-pill">本頁核心結論</span>
    <p data-core-conclusion>{escape(spec.core_conclusion)}</p>
  </div>
  <div class="uw-citation-box" data-citation-box>
    <div class="uw-citation-head">
      <strong>一鍵引用本頁資料（媒體／部落格／Dcard／報告適用）</strong>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-target="uw-citation-code">複製引用文字</button>
    </div>
    <code id="uw-citation-code" class="uw-citation-code">{escape(citation_text)}</code>
  </div>
</section>"""


def render_faq_section(faqs: Sequence[tuple[str, str]], heading: str = "常見問題（FAQ）") -> str:
    items_html = "".join(
        f'<details class="uw-faq-item"><summary>{escape(q)}</summary><div class="uw-faq-answer"><p>{escape(a)}</p></div></details>'
        for q, a in faqs
    )
    return f'<section class="uw-section" id="faq"><h2>{escape(heading)}</h2><div class="uw-faq-list">{items_html}</div></section>'


def render_compliance_strip(extra_note: str = "") -> str:
    note = f" {extra_note.strip()}" if extra_note.strip() else ""
    return (
        '<aside class="uw-compliance-banner" role="note">'
        f"<strong>資料合規提醒：</strong>{escape(MANDATORY_DISCLAIMER)}"
        "本頁由 UniWay 根據公開簡章與官方頁面整理，並非校方單位，不代辦申請、亦不承諾錄取結果；"
        f"未公告或尚未核實之欄位一律標示「待確認」或「依校方公告」。{escape(note)}"
        "</aside>"
    )


# ---------------------------------------------------------------------------
# 1. ECTS Credit Converter Logic
# ---------------------------------------------------------------------------

ECTS_SYSTEM_LABELS: dict[str, str] = {
    "ects": "歐洲學分（ECTS）",
    "tw": "台灣大學學分（學期制）",
    "us": "美國學期學分（US Semester Credits）",
    "jp": "日本大學學分（単位）",
}


def convert_credits(
    amount: float,
    source_system: str = "ects",
    ects_per_tw: float = 2.0,
    min_home_tw_credits: float = 6.0,
) -> dict[str, Any]:
    safe_amount = max(0.0, min(240.0, float(amount)))
    safe_ratio = max(1.0, min(4.0, float(ects_per_tw)))
    safe_min_tw = max(0.0, min(30.0, float(min_home_tw_credits)))

    if source_system == "tw":
        ects_val = safe_amount * safe_ratio
    elif source_system == "us":
        ects_val = safe_amount * 2.0
    elif source_system == "jp":
        ects_val = safe_amount * 2.0
    else:
        source_system = "ects"
        ects_val = safe_amount

    tw_credits = ects_val / safe_ratio
    us_semester_credits = ects_val / 2.0
    us_quarter_credits = us_semester_credits * 1.5
    jp_credits = ects_val / 2.0
    workload_hours_low = round(ects_val * 25)
    workload_hours_high = round(ects_val * 30)

    required_ects_for_home = safe_min_tw * safe_ratio
    courses_5_ects = math.ceil(required_ects_for_home / 5.0) if required_ects_for_home > 0 else 0
    courses_6_ects = math.ceil(required_ects_for_home / 6.0) if required_ects_for_home > 0 else 0
    meets_home_min = ects_val >= required_ects_for_home

    return {
        "input_amount": round(safe_amount, 2),
        "source_system": source_system,
        "source_label": ECTS_SYSTEM_LABELS.get(source_system, ECTS_SYSTEM_LABELS["ects"]),
        "ects_per_tw": round(safe_ratio, 2),
        "ects": round(ects_val, 2),
        "tw_credits": round(tw_credits, 2),
        "us_semester_credits": round(us_semester_credits, 2),
        "us_quarter_credits": round(us_quarter_credits, 2),
        "jp_credits": round(jp_credits, 2),
        "workload_hours_low": workload_hours_low,
        "workload_hours_high": workload_hours_high,
        "min_home_tw_credits": round(safe_min_tw, 1),
        "required_ects_for_home": round(required_ects_for_home, 1),
        "courses_5_ects": courses_5_ects,
        "courses_6_ects": courses_6_ects,
        "recommended_ects_with_buffer": round(required_ects_for_home + 5.0, 1),
        "meets_home_min": meets_home_min,
    }


# ---------------------------------------------------------------------------
# 2. GPA & Bavarian Formula Converter Logic
# ---------------------------------------------------------------------------

GPA_SCALE_TABLE: tuple[tuple[str, str, float, float, str], ...] = (
    ("A+", "90 – 100", 4.3, 4.0, "1.0 – 1.7"),
    ("A", "85 – 89", 4.0, 4.0, "1.8 – 2.1"),
    ("A-", "80 – 84", 3.7, 3.7, "2.2 – 2.5"),
    ("B+", "77 – 79", 3.3, 3.3, "2.5 – 2.7"),
    ("B", "73 – 76", 3.0, 3.0, "2.8 – 3.0"),
    ("B-", "70 – 72", 2.7, 2.7, "3.1 – 3.2"),
    ("C+", "67 – 69", 2.3, 2.3, "3.3 – 3.4"),
    ("C", "63 – 66", 2.0, 2.0, "3.5 – 3.7"),
    ("C-", "60 – 62", 1.7, 1.7, "3.8 – 4.0"),
    ("F / 不及格", "0 – 59", 0.0, 0.0, "5.0（不及格）"),
)


def score_to_gpa_43(score: float) -> float:
    if score >= 90:
        return 4.3
    if score >= 85:
        return 4.0
    if score >= 80:
        return 3.7
    if score >= 77:
        return 3.3
    if score >= 73:
        return 3.0
    if score >= 70:
        return 2.7
    if score >= 67:
        return 2.3
    if score >= 63:
        return 2.0
    if score >= 60:
        return 1.7
    return 0.0


def score_to_gpa_40_standard(score: float) -> float:
    if score >= 80:
        return 4.0
    if score >= 70:
        return 3.0
    if score >= 60:
        return 2.0
    return 0.0


def score_to_gpa_40_plusminus(score: float) -> float:
    return min(4.0, score_to_gpa_43(score))


def bavarian_formula(score: float, max_score: float = 100.0, min_pass_score: float = 60.0) -> float | None:
    """Modified Bavarian Formula: 1 + 3 * (Nmax - Nd) / (Nmax - Nmin), truncated to 1 decimal place."""
    if max_score <= min_pass_score or score < min_pass_score:
        return None
    clamped = min(max_score, score)
    raw = 1.0 + 3.0 * ((max_score - clamped) / (max_score - min_pass_score))
    # German universities and uni-assist truncate after 1 decimal place without rounding up
    truncated = math.floor((raw + 1e-9) * 10.0) / 10.0
    return max(1.0, min(4.0, truncated))


def convert_gpa_summary(
    value: float,
    scale: str = "percent",
    max_score: float = 100.0,
    min_pass: float = 60.0,
) -> dict[str, Any]:
    if scale == "gpa43":
        gpa43 = max(0.0, min(4.3, float(value)))
        # Approximate midpoint score on 4.3 table for cross-reference
        approx_pct = (
            92.0 if gpa43 >= 4.15 else
            87.0 if gpa43 >= 3.85 else
            82.0 if gpa43 >= 3.5 else
            78.0 if gpa43 >= 3.15 else
            75.0 if gpa43 >= 2.85 else
            71.0 if gpa43 >= 2.5 else
            68.0 if gpa43 >= 2.15 else
            65.0 if gpa43 >= 1.85 else
            61.0 if gpa43 >= 1.5 else 50.0
        )
        gpa40_pm = min(4.0, round(gpa43, 2))
        gpa40_std = score_to_gpa_40_standard(approx_pct)
        bav = bavarian_formula(gpa43, 4.3, 1.7)
    elif scale == "gpa40":
        gpa40_pm = max(0.0, min(4.0, float(value)))
        approx_pct = (
            88.0 if gpa40_pm >= 3.85 else
            82.0 if gpa40_pm >= 3.5 else
            78.0 if gpa40_pm >= 3.15 else
            75.0 if gpa40_pm >= 2.85 else
            71.0 if gpa40_pm >= 2.5 else
            68.0 if gpa40_pm >= 2.15 else
            65.0 if gpa40_pm >= 1.85 else
            61.0 if gpa40_pm >= 1.5 else 50.0
        )
        gpa43 = gpa40_pm
        gpa40_std = gpa40_pm
        bav = bavarian_formula(gpa40_pm, 4.0, 2.0)
    else:
        scale = "percent"
        approx_pct = max(0.0, min(100.0, float(value)))
        gpa43 = score_to_gpa_43(approx_pct)
        gpa40_pm = score_to_gpa_40_plusminus(approx_pct)
        gpa40_std = score_to_gpa_40_standard(approx_pct)
        bav = bavarian_formula(approx_pct, max_score=max_score, min_pass_score=min_pass)

    return {
        "scale": scale,
        "input_value": round(float(value), 2),
        "approx_percent": round(approx_pct, 1),
        "gpa_43": round(gpa43, 2),
        "gpa_40_plusminus": round(gpa40_pm, 2),
        "gpa_40_standard": round(gpa40_std, 2),
        "bavarian_grade": f"{bav:.1f}" if bav is not None else "不及格（低於最低及格門檻）",
        "bavarian_numeric": bav,
        "max_score": max_score,
        "min_pass": min_pass,
    }


# ---------------------------------------------------------------------------
# 3. Language Score Converter + Real Partner Database Matcher
# ---------------------------------------------------------------------------

# Concordance bands grounded in ETS / IELTS / CEFR published concordance ranges
ENGLISH_CONCORDANCE_BANDS: tuple[dict[str, Any], ...] = (
    {
        "cefr": "C2",
        "ielts_min": 8.5, "ielts_max": 9.0, "ielts_rep": 8.5,
        "toefl_min": 114, "toefl_max": 120, "toefl_rep": 116, "toefl_new": "6.0",
        "toeic_min": 975, "toeic_max": 990, "toeic_rep": 980,
        "jlpt_ref": "N1（日語高階獨立檢定）",
        "summary": "接近母語學術讀寫能力，符合絕大多數英語系頂尖院系與法學院高門檻",
    },
    {
        "cefr": "C1",
        "ielts_min": 7.0, "ielts_max": 8.0, "ielts_rep": 7.0,
        "toefl_min": 94, "toefl_max": 113, "toefl_rep": 96, "toefl_new": "5.0 – 5.5",
        "toeic_min": 945, "toeic_max": 974, "toeic_rep": 950,
        "jlpt_ref": "N1（日語高階獨立檢定）",
        "summary": "高階學術英語，常見於英美澳名校商管、傳播、法學與人文社科交換門檻",
    },
    {
        "cefr": "B2+",
        "ielts_min": 6.5, "ielts_max": 6.5, "ielts_rep": 6.5,
        "toefl_min": 79, "toefl_max": 93, "toefl_rep": 85, "toefl_new": "4.5",
        "toeic_min": 850, "toeic_max": 944, "toeic_rep": 880,
        "jlpt_ref": "N1 – N2（日語獨立檢定）",
        "summary": "歐美與亞洲英語授課交換最主流門檻區間（TOEFL 79–88／IELTS 6.5）",
    },
    {
        "cefr": "B2",
        "ielts_min": 5.5, "ielts_max": 6.0, "ielts_rep": 6.0,
        "toefl_min": 60, "toefl_max": 78, "toefl_rep": 72, "toefl_new": "4.0",
        "toeic_min": 785, "toeic_max": 849, "toeic_rep": 785,
        "jlpt_ref": "N2（日語一般學部交換主流門檻）",
        "summary": "歐陸 Erasmus 夥伴校與日韓英語授課學程常見基礎門檻（CEFR B2／IELTS 6.0）",
    },
    {
        "cefr": "B1",
        "ielts_min": 4.5, "ielts_max": 5.0, "ielts_rep": 5.0,
        "toefl_min": 42, "toefl_max": 59, "toefl_rep": 52, "toefl_new": "3.0 – 3.5",
        "toeic_min": 550, "toeic_max": 784, "toeic_rep": 650,
        "jlpt_ref": "N3（日語語學或部分姊妹校基礎門檻）",
        "summary": "部分亞洲姊妹校、校內初審基礎門檻或英語學習型交換方案常見區間",
    },
    {
        "cefr": "A2",
        "ielts_min": 4.0, "ielts_max": 4.0, "ielts_rep": 4.0,
        "toefl_min": 0, "toefl_max": 41, "toefl_rep": 35, "toefl_new": "2.0 – 2.5",
        "toeic_min": 225, "toeic_max": 549, "toeic_rep": 450,
        "jlpt_ref": "N4 – N5（基礎日語）",
        "summary": "基礎日常溝通程度，多數英語授課學分交換方案會要求達到 B1 或 B2 以上",
    },
)

JLPT_LEVEL_INFO: dict[str, dict[str, Any]] = {
    "N1": {"rank": 5, "cefr_ref": "約對應 CEFR C1（日語）", "desc": "日本綜合大學日語授課學部與研究科最常見門檻"},
    "N2": {"rank": 4, "cefr_ref": "約對應 CEFR B2 / B1+（日語）", "desc": "赴日交換多數一般學部與日語專修常見門檻"},
    "N3": {"rank": 3, "cefr_ref": "約對應 CEFR B1 / A2+（日語）", "desc": "部分日本私立大學、地方國立大學或語學別科接受"},
    "N4": {"rank": 2, "cefr_ref": "約對應 CEFR A2（日語）", "desc": "基礎日語檢定，少數語言研修或特定姊妹校採計"},
    "N5": {"rank": 1, "cefr_ref": "約對應 CEFR A1（日語）", "desc": "入門日語檢定，多數日語授課交換要求 N3–N1"},
}

CEFR_RANK: dict[str, int] = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "B2+": 4, "C1": 5, "C2": 6}


def convert_language_score(test: str, raw_score: str) -> dict[str, Any]:
    norm_test = (test or "ielts").strip().lower()
    raw = (raw_score or "").strip().upper()

    if norm_test == "jlpt":
        level = raw if raw in JLPT_LEVEL_INFO else "N2"
        info = JLPT_LEVEL_INFO[level]
        return {
            "test": "jlpt",
            "test_label": "JLPT 日本語能力試驗",
            "input_display": f"JLPT {level}",
            "is_japanese": True,
            "jlpt_level": level,
            "jlpt_rank": info["rank"],
            "cefr": info["cefr_ref"],
            "ielts_range": "不直接換算（英語與日語屬不同語種檢定）",
            "toefl_range": "不直接換算（英語與日語屬不同語種檢定）",
            "toefl_new": "—",
            "toeic_range": "不直接換算（英語與日語屬不同語種檢定）",
            "summary": info["desc"],
            "numeric_ielts": None,
            "numeric_toefl": None,
            "numeric_toeic": None,
            "cefr_code": "C1" if level == "N1" else "B2" if level == "N2" else "B1" if level == "N3" else "A2",
        }

    matched_band = ENGLISH_CONCORDANCE_BANDS[3]  # default B2
    numeric_val: float | None = None

    if norm_test == "cefr":
        code = raw if raw in {"A2", "B1", "B2", "B2+", "C1", "C2"} else "B2"
        matched_band = next((b for b in ENGLISH_CONCORDANCE_BANDS if b["cefr"] == code), ENGLISH_CONCORDANCE_BANDS[3])
        input_display = f"CEFR {code}"
        test_label = "CEFR 歐洲共同語言參考標準"
    else:
        try:
            numeric_val = float(raw)
        except ValueError:
            numeric_val = None

        if norm_test == "toefl":
            val = max(0.0, min(120.0, numeric_val if numeric_val is not None else 85.0))
            numeric_val = val
            matched_band = next(
                (b for b in ENGLISH_CONCORDANCE_BANDS if b["toefl_min"] <= val <= b["toefl_max"]),
                ENGLISH_CONCORDANCE_BANDS[-1],
            )
            input_display = f"TOEFL iBT {int(round(val))}"
            test_label = "TOEFL iBT 托福網路測驗"
        elif norm_test == "toeic":
            val = max(10.0, min(990.0, numeric_val if numeric_val is not None else 800.0))
            numeric_val = val
            matched_band = next(
                (b for b in ENGLISH_CONCORDANCE_BANDS if val >= b["toeic_min"]),
                ENGLISH_CONCORDANCE_BANDS[-1],
            )
            input_display = f"TOEIC L&R {int(round(val))}"
            test_label = "TOEIC 多益聽讀測驗"
        else:
            norm_test = "ielts"
            val = max(4.0, min(9.0, numeric_val if numeric_val is not None else 6.5))
            val = round(val * 2.0) / 2.0
            numeric_val = val
            matched_band = next(
                (b for b in ENGLISH_CONCORDANCE_BANDS if val >= b["ielts_min"]),
                ENGLISH_CONCORDANCE_BANDS[-1],
            )
            input_display = f"IELTS {val:.1f}"
            test_label = "IELTS 雅思學術組"

    ielts_eq = numeric_val if norm_test == "ielts" else float(matched_band["ielts_rep"])
    toefl_eq = numeric_val if norm_test == "toefl" else float(matched_band["toefl_rep"])
    toeic_eq = numeric_val if norm_test == "toeic" else float(matched_band["toeic_rep"])
    cefr_code = "B2" if matched_band["cefr"] == "B2+" else matched_band["cefr"]

    return {
        "test": norm_test,
        "test_label": test_label,
        "input_display": input_display,
        "is_japanese": False,
        "jlpt_level": None,
        "jlpt_rank": None,
        "cefr": f"CEFR {matched_band['cefr']}",
        "cefr_code": cefr_code,
        "ielts_range": (
            f"{matched_band['ielts_min']:.1f}"
            if matched_band["ielts_min"] == matched_band["ielts_max"]
            else f"{matched_band['ielts_min']:.1f} – {matched_band['ielts_max']:.1f}"
        ),
        "toefl_range": f"{matched_band['toefl_min']} – {matched_band['toefl_max']}",
        "toefl_new": matched_band["toefl_new"],
        "toeic_range": f"{matched_band['toeic_min']} – {matched_band['toeic_max']}",
        "summary": matched_band["summary"],
        "numeric_ielts": ielts_eq,
        "numeric_toefl": toefl_eq,
        "numeric_toeic": toeic_eq,
    }


_RE_IELTS = re.compile(r"(?:IELTS|雅思)(?:\s*(?:Academic|總分|overall|達|至少|以上|:|：))?\s*([4-8](?:\.[05])?|9(?:\.0)?)", re.IGNORECASE)
_RE_TOEFL_IBT = re.compile(
    r"(?:TOEFL\s*iBT|托福\s*iBT|TOEFL(?!\s*ITP)|托福(?!\s*ITP))(?:[^0-9\n;；。]{0,14}?)\b([4-9]\d|1[01]\d|120)\b",
    re.IGNORECASE,
)
_RE_TOEIC = re.compile(r"(?:TOEIC(?:\s*L&R)?|多益)(?:[^0-9\n;；。]{0,14}?)\b([3-8]\d\d|9[0-8]\d|990)\b", re.IGNORECASE)
_RE_CEFR = re.compile(r"(?:CEFR\s*[:：]?\s*(A1|A2|B1|B2|C1|C2)\b|\b(B1|B2|C1|C2)\s*(?:level|級|以上))", re.IGNORECASE)
_RE_JLPT = re.compile(r"(?:JLPT|日檢|日本語能力(?:試驗|測驗)?)\s*(N[1-5])\b|\b(N[1-5])\s*(?:以上|合格)", re.IGNORECASE)


def extract_partner_language_thresholds(rows: Sequence[PartnerUniversity]) -> dict[str, Any]:
    """Extract explicitly stated language thresholds from a partner's sourced records without guessing."""
    texts: list[str] = []
    ielts_vals: list[float] = []
    toefl_vals: list[float] = []
    toeic_vals: list[float] = []
    cefr_vals: list[str] = []
    jlpt_vals: list[str] = []

    for row in rows:
        for cond in row.language_conditions:
            if cond.requirement_level not in {"required", "recommended"} or cond.minimum_score is None:
                continue
            t_low = cond.test.lower()
            if "ielts" in t_low:
                ielts_vals.append(float(cond.minimum_score))
            elif "toefl" in t_low and "itp" not in (cond.test_variant or "").lower() and cond.minimum_score <= 120:
                toefl_vals.append(float(cond.minimum_score))
            elif "toeic" in t_low:
                toeic_vals.append(float(cond.minimum_score))

        for chunk in (
            row.language_requirement,
            row.eligibility,
            row.application_info,
            *row.student_summary_zh.eligibility_points,
        ):
            if chunk and chunk.strip():
                texts.append(chunk.strip())

    combined = " ； ".join(dict.fromkeys(texts))
    for m in _RE_IELTS.finditer(combined):
        val = float(m.group(1))
        if 4.0 <= val <= 9.0:
            ielts_vals.append(val)
    for m in _RE_TOEFL_IBT.finditer(combined):
        val = float(m.group(1))
        if 40 <= val <= 120:
            toefl_vals.append(val)
    for m in _RE_TOEIC.finditer(combined):
        val = float(m.group(1))
        if 300 <= val <= 990:
            toeic_vals.append(val)
    for m in _RE_CEFR.finditer(combined):
        code = (m.group(1) or m.group(2) or "").upper()
        if code in CEFR_RANK:
            cefr_vals.append(code)
    for m in _RE_JLPT.finditer(combined):
        lvl = (m.group(1) or m.group(2) or "").upper()
        if lvl in JLPT_LEVEL_INFO:
            jlpt_vals.append(lvl)

    snippet_src = next(
        (r.language_requirement.strip() for r in rows if r.language_requirement and r.language_requirement.strip()),
        "",
    ) or next((r.eligibility.strip() for r in rows if r.eligibility and r.eligibility.strip()), "")
    snippet = re.sub(r"\s+", " ", snippet_src).strip()
    if len(snippet) > 110:
        snippet = snippet[:109].rstrip() + "…"

    return {
        "ielts_min": min(ielts_vals) if ielts_vals else None,
        "toefl_min": min(toefl_vals) if toefl_vals else None,
        "toeic_min": min(toeic_vals) if toeic_vals else None,
        "cefr_min": min(cefr_vals, key=lambda c: CEFR_RANK[c]) if cefr_vals else None,
        "jlpt_min": min(jlpt_vals, key=lambda l: JLPT_LEVEL_INFO[l]["rank"]) if jlpt_vals else None,
        "has_any_parsed": bool(ielts_vals or toefl_vals or toeic_vals or cefr_vals or jlpt_vals),
        "snippet": snippet or "語言門檻未單獨列載，請依母校當期簡章與合作校規定確認",
    }


def match_partner_schools_for_home(
    home: UniversityProfile,
    partners: Sequence[PartnerUniversity],
    conversion: dict[str, Any],
    availability_labels: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    grouped: dict[str, list[PartnerUniversity]] = {}
    for p in partners:
        grouped.setdefault(partner_group_id(p), []).append(p)

    test = conversion["test"]
    direct_matches: list[dict[str, Any]] = []
    equiv_matches: list[dict[str, Any]] = []
    below_threshold_count = 0
    unconfirmed_or_other_count = 0

    user_cefr_rank = CEFR_RANK.get(conversion["cefr_code"], 0)

    for pid, rows in grouped.items():
        primary = rows[0]
        parsed = extract_partner_language_thresholds(rows)
        status_label = (
            availability_labels.get(primary.availability_status, primary.availability_status)
            if availability_labels
            else primary.availability_status
        )
        entry = {
            "school_name": primary.school_name,
            "country": canonical_country(primary.country) or primary.country or "國家待確認",
            "partner_url": f"/schools/{home.id}/partners/{pid}",
            "availability": status_label,
            "snippet": parsed["snippet"],
        }

        if conversion["is_japanese"]:
            req_jlpt = parsed["jlpt_min"]
            if req_jlpt is not None:
                if conversion["jlpt_rank"] >= JLPT_LEVEL_INFO[req_jlpt]["rank"]:
                    entry["matched_rule"] = f"列載日檢門檻 {req_jlpt}"
                    direct_matches.append(entry)
                else:
                    below_threshold_count += 1
            else:
                unconfirmed_or_other_count += 1
            continue

        # English test matching: strictly separate direct test listing vs equivalent English test / CEFR listing
        direct_req: float | str | None = None
        direct_pass: bool | None = None
        if test == "ielts" and parsed["ielts_min"] is not None:
            direct_req = f"IELTS {parsed['ielts_min']:g}"
            direct_pass = float(conversion["numeric_ielts"]) >= parsed["ielts_min"]
        elif test == "toefl" and parsed["toefl_min"] is not None:
            direct_req = f"TOEFL iBT {parsed['toefl_min']:g}"
            direct_pass = float(conversion["numeric_toefl"]) >= parsed["toefl_min"]
        elif test == "toeic" and parsed["toeic_min"] is not None:
            direct_req = f"TOEIC {parsed['toeic_min']:g}"
            direct_pass = float(conversion["numeric_toeic"]) >= parsed["toeic_min"]
        elif test == "cefr" and parsed["cefr_min"] is not None:
            direct_req = f"CEFR {parsed['cefr_min']}"
            direct_pass = user_cefr_rank >= CEFR_RANK[parsed["cefr_min"]]

        if direct_pass is True:
            entry["matched_rule"] = f"明確列載 {direct_req}"
            direct_matches.append(entry)
        elif direct_pass is False:
            below_threshold_count += 1
        else:
            # Check if another English metric is explicitly listed on this partner school
            has_any_eng = any(
                parsed[k] is not None for k in ("ielts_min", "toefl_min", "toeic_min", "cefr_min")
            )
            if not has_any_eng:
                unconfirmed_or_other_count += 1
            else:
                # Evaluate whether user's converted English band meets one of the listed English thresholds
                eq_passes: list[str] = []
                if parsed["cefr_min"] is not None and user_cefr_rank >= CEFR_RANK[parsed["cefr_min"]]:
                    eq_passes.append(f"CEFR {parsed['cefr_min']}")
                if parsed["ielts_min"] is not None and float(conversion["numeric_ielts"]) >= parsed["ielts_min"]:
                    eq_passes.append(f"IELTS {parsed['ielts_min']:g}")
                if parsed["toefl_min"] is not None and float(conversion["numeric_toefl"]) >= parsed["toefl_min"]:
                    eq_passes.append(f"TOEFL {parsed['toefl_min']:g}")
                if parsed["toeic_min"] is not None and float(conversion["numeric_toeic"]) >= parsed["toeic_min"]:
                    eq_passes.append(f"TOEIC {parsed['toeic_min']:g}")
                if eq_passes:
                    entry["matched_rule"] = f"列載其他英檢（{'／'.join(eq_passes[:2])}），須確認是否採計替代檢定"
                    equiv_matches.append(entry)
                else:
                    below_threshold_count += 1

    return {
        "home_id": home.id,
        "home_name": home.school_name,
        "home_short_name": home.short_name,
        "home_school_url": f"/schools/{home.id}",
        "home_planner_url": "/?" + urlencode({"home": home.school_name}) + "#partners",
        "home_official_url": home.official_url,
        "total_partner_pages": len(grouped),
        "direct_match_count": len(direct_matches),
        "equiv_match_count": len(equiv_matches),
        "below_threshold_count": below_threshold_count,
        "unconfirmed_or_other_count": unconfirmed_or_other_count,
        "direct_samples": direct_matches[:12],
        "equiv_samples": equiv_matches[:8],
    }


# ---------------------------------------------------------------------------
# 4. Exchange Budget Calculator Logic (with Bundled FX + ±10% Sensitivity)
# ---------------------------------------------------------------------------

BUDGET_COUNTRY_TEMPLATES: dict[str, dict[str, Any]] = {
    "japan": {
        "name": "日本（東京／關西參考模板）",
        "currency": "JPY",
        "months": 5,
        "housing": 58000,
        "food": 42000,
        "transport": 10000,
        "other": 15000,
        "one_time_twd": 32000,
        "note": "含日本國民健康保險與日常開支估算；若抽中大學直營寮，住宿費可能低於校外共立寮或租屋。",
    },
    "south-korea": {
        "name": "韓國（首爾圈參考模板）",
        "currency": "KRW",
        "months": 4,
        "housing": 500000,
        "food": 450000,
        "transport": 70000,
        "other": 150000,
        "one_time_twd": 28000,
        "note": "含韓國國民健康保險（NHIS 外國留學生納保）估算；校內雙人房宿舍通常較校外考試院或 One-room 節省。",
    },
    "germany": {
        "name": "德國（一般大學城參考模板）",
        "currency": "EUR",
        "months": 5,
        "housing": 480,
        "food": 280,
        "transport": 60,
        "other": 180,
        "one_time_twd": 52000,
        "note": "含德國公立學生健康保險（約 120–130 歐元／月，歸入雜支醫保）；慕尼黑等高房租城市建議將住宿調高至 650–850 歐元。",
    },
    "france": {
        "name": "法國（巴黎以外／含房補前估算）",
        "currency": "EUR",
        "months": 5,
        "housing": 520,
        "food": 260,
        "transport": 55,
        "other": 150,
        "one_time_twd": 50000,
        "note": "巴黎地區房租常達 700–950 歐元；CAF 房補核發需數月等待期，行前準備金不宜預先扣除房補。",
    },
    "united-kingdom": {
        "name": "英國（倫敦以外地區參考模板）",
        "currency": "GBP",
        "months": 5,
        "housing": 680,
        "food": 260,
        "transport": 80,
        "other": 150,
        "one_time_twd": 58000,
        "note": "交換一學期（6 個月內）與全學年簽證及醫療附加費（IHS）規定不同，倫敦地區住宿建議上調至 900–1,200 英鎊。",
    },
    "united-states": {
        "name": "美國（州立大學校區參考模板）",
        "currency": "USD",
        "months": 5,
        "housing": 950,
        "food": 550,
        "transport": 100,
        "other": 250,
        "one_time_twd": 68000,
        "note": "美國多數大學強制投保校方指定醫療保險（常達每學期 800–1,800 美元）並可能綁定校內 Meal Plan，務必先查 Fact Sheet。",
    },
    "netherlands": {
        "name": "荷蘭（阿姆斯特丹／烏特勒支等參考）",
        "currency": "EUR",
        "months": 5,
        "housing": 650,
        "food": 280,
        "transport": 80,
        "other": 150,
        "one_time_twd": 52000,
        "note": "荷蘭學生房源相當緊俏，獲提名後應立即透過校方合作住房平台登記並留意仲介服務費。",
    },
    "czechia": {
        "name": "捷克（布拉格／布爾諾參考模板）",
        "currency": "CZK",
        "months": 5,
        "housing": 7500,
        "food": 6500,
        "transport": 550,
        "other": 3000,
        "one_time_twd": 48000,
        "note": "捷克大學雙人房學生宿舍費用相對西歐親民，惟長期簽證審核期長且需購買合規醫療保險。",
    },
    "singapore": {
        "name": "新加坡（校內外混合參考模板）",
        "currency": "SGD",
        "months": 5,
        "housing": 850,
        "food": 500,
        "transport": 100,
        "other": 180,
        "one_time_twd": 24000,
        "note": "新加坡校內宿舍抽籤競爭高；若未抽中校內宿位而改租校外公寓雅房，月租常上升至 1,200–1,800 新幣。",
    },
    "australia": {
        "name": "澳洲（雪梨／墨爾本／布里斯本參考）",
        "currency": "AUD",
        "months": 5,
        "housing": 1250,
        "food": 550,
        "transport": 160,
        "other": 220,
        "one_time_twd": 54000,
        "note": "澳洲學生簽證強制要求投保海外學生健康保險（OSHC），房租多以「每週」計價，換算月租時請乘以 4.33 週。",
    },
    "canada": {
        "name": "加拿大（溫哥華／多倫多／蒙特婁參考）",
        "currency": "CAD",
        "months": 5,
        "housing": 1050,
        "food": 520,
        "transport": 120,
        "other": 200,
        "one_time_twd": 58000,
        "note": "冬季學期需預留禦寒衣物預算，並確認接待校省分醫療保險或校內強制醫保費用。",
    },
    "spain": {
        "name": "西班牙（馬德里／巴塞隆納／瓦倫西亞參考）",
        "currency": "EUR",
        "months": 5,
        "housing": 520,
        "food": 250,
        "transport": 45,
        "other": 140,
        "one_time_twd": 50000,
        "note": "馬德里與巴塞隆納市區合租雅房（Piso compartido）租金較其他城市高，簽約時須留意押金退還條款。",
    },
}


def calculate_exchange_budget(
    *,
    country_key: str = "japan",
    months: int | None = None,
    currency: str | None = None,
    fx_rate: float | None = None,
    housing: float | None = None,
    food: float | None = None,
    transport: float | None = None,
    other: float | None = None,
    one_time_twd: float | None = None,
    scholarship_twd: float | None = None,
) -> dict[str, Any]:
    tpl = BUDGET_COUNTRY_TEMPLATES.get(country_key) or BUDGET_COUNTRY_TEMPLATES["japan"]
    if country_key not in BUDGET_COUNTRY_TEMPLATES:
        country_key = "japan"

    fx_bundle = fx_reference()
    rates = fx_bundle.get("rates", {})
    cur = (currency or tpl["currency"]).strip().upper()
    if cur != "TWD" and cur not in rates:
        cur = tpl["currency"]

    bundled_rate = 1.0 if cur == "TWD" else float(rates.get(cur, 1.0))
    rate = float(fx_rate) if (fx_rate is not None and fx_rate > 0) else bundled_rate

    m = max(1, min(12, int(months if months is not None else tpl["months"])))
    h = max(0.0, float(housing if housing is not None else tpl["housing"]))
    f = max(0.0, float(food if food is not None else tpl["food"]))
    t = max(0.0, float(transport if transport is not None else tpl["transport"]))
    o = max(0.0, float(other if other is not None else tpl["other"]))
    one_time = max(0.0, float(one_time_twd if one_time_twd is not None else tpl["one_time_twd"]))
    schol = max(0.0, float(scholarship_twd if scholarship_twd is not None else 0.0))

    monthly_foreign = h + f + t + o
    semester_foreign = monthly_foreign * m

    scenarios = []
    for label, factor in (("匯率 -10%（台幣較強）", 0.9), ("基準參考匯率（0%）", 1.0), ("匯率 +10%（外幣升值緩衝）", 1.1)):
        r = rate * factor
        monthly_twd = round(monthly_foreign * r)
        living_total_twd = round(semester_foreign * r)
        gross_total_twd = round(living_total_twd + one_time)
        net_self_twd = max(0, round(gross_total_twd - schol))
        scenarios.append({
            "label": label,
            "factor": factor,
            "rate": round(r, 4),
            "monthly_twd": monthly_twd,
            "living_total_twd": living_total_twd,
            "gross_total_twd": gross_total_twd,
            "net_self_twd": net_self_twd,
        })

    base_sc = scenarios[1]
    high_sc = scenarios[2]
    emergency_reserve_twd = round(base_sc["monthly_twd"] * 1.0)

    return {
        "country_key": country_key,
        "template_name": tpl["name"],
        "template_note": tpl["note"],
        "currency": cur,
        "bundled_rate": round(bundled_rate, 4),
        "fx_fetched_date": str(fx_bundle.get("fetched_at", ""))[:10] or "2026-10-02",
        "rate": round(rate, 4),
        "months": m,
        "housing": h,
        "food": f,
        "transport": t,
        "other": o,
        "monthly_foreign": monthly_foreign,
        "semester_foreign": semester_foreign,
        "one_time_twd": round(one_time),
        "scholarship_twd": round(schol),
        "scenarios": scenarios,
        "base_monthly_twd": base_sc["monthly_twd"],
        "base_gross_twd": base_sc["gross_total_twd"],
        "base_net_twd": base_sc["net_self_twd"],
        "fx_buffer_delta_twd": high_sc["gross_total_twd"] - base_sc["gross_total_twd"],
        "emergency_reserve_twd": emergency_reserve_twd,
    }


# ---------------------------------------------------------------------------
# 5. Real 71-School Deadlines & Reverse Timeline + .ics Generator
# ---------------------------------------------------------------------------

TERM_OPTIONS: dict[str, dict[str, Any]] = {
    "2027-fall": {
        "label": "2027 秋季班出發（預計 2027 年 8–9 月出國）",
        "default_anchor": date(2026, 12, 1),
        "departure_date": date(2027, 9, 1),
    },
    "2028-spring": {
        "label": "2028 春季班出發（預計 2028 年 1–4 月出國）",
        "default_anchor": date(2027, 5, 15),
        "departure_date": date(2028, 2, 15),
    },
    "2028-fall": {
        "label": "2028 秋季班出發（預計 2028 年 8–9 月出國）",
        "default_anchor": date(2027, 11, 15),
        "departure_date": date(2028, 9, 1),
    },
}

PERIOD_STATUS_ZH: dict[str, str] = {
    "open": "受理中",
    "upcoming": "即將開放",
    "closed": "本梯次已截止",
    "action_required": "待辦確認",
    "reference_only": "歷年梯次參考",
    "needs_confirmation": "待確認／依校方公告",
}

DATE_STATUS_ZH: dict[str, str] = {
    "verified_exact": "已核對確切期限",
    "reference_only": "歷史／梯次參考日期",
    "needs_confirmation": "待確認（依校方公告）",
    "not_applicable": "依個別方案",
}


def _load_home_application_periods(u: UniversityProfile) -> list[ApplicationPeriodItem]:
    """Load sourced home_application periods for any of the 71 universities without touching private sessions."""
    if u.id == "cgu":
        card = get_verified_school_window_card("cgu")
        return [
            ApplicationPeriodItem(
                title=card.cycle_label,
                details=[card.online_deadline.value_text, card.paper_deadline.value_text],
                source={
                    "title": card.online_deadline.source_title,
                    "source_url": card.online_deadline.source_url,
                },
                scope="home_application",
                program_types=["exchange", "dual_degree"],
                academic_year="116",
                application_round="第 1 學期（2027 秋季班）",
                opens_at=datetime(2026, 11, 2, 9, 0, tzinfo=TAIPEI_TZ),
                deadline_at=card.primary_deadline_at,
                date_status=ApplicationPeriodDateStatus.VERIFIED_EXACT if card.primary_deadline_at else ApplicationPeriodDateStatus.NEEDS_CONFIRMATION,
                status=ApplicationPeriodStatus.OPEN if card.window_status == "open" else ApplicationPeriodStatus.NEEDS_CONFIRMATION,
                status_note=card.window_badge,
                deadline_note=card.online_deadline.value_text[:480],
                checked_at=datetime.strptime(card.online_deadline.last_checked_at, "%Y-%m-%d").replace(tzinfo=TAIPEI_TZ),
            )
        ]
    builder = getattr(_api_mod, f"build_{u.id}_student_dashboard", None)
    if builder is None:
        return []
    dashboard = builder(partner_universities=[])
    return [p for p in dashboard.application_periods if p.scope == "home_application"]


_DEADLINES_CACHE: list[dict[str, Any]] | None = None


def build_all_71_school_deadlines() -> list[dict[str, Any]]:
    """Build sourced deadline rows covering all 71 supported Taiwanese universities."""
    global _DEADLINES_CACHE
    if _DEADLINES_CACHE is not None:
        return _DEADLINES_CACHE

    rows: list[dict[str, Any]] = []
    status_priority = {
        "open": 0,
        "upcoming": 1,
        "action_required": 2,
        "needs_confirmation": 3,
        "closed": 4,
        "reference_only": 5,
    }

    for u in SUPPORTED_UNIVERSITIES:
        periods = _load_home_application_periods(u)
        window_card = get_verified_school_window_card(u.id)
        is_pub = is_public_university(u)

        if not periods:
            src_url = safe_https_or_http_url(window_card.online_deadline.source_url) or safe_https_or_http_url(u.official_url)
            rows.append({
                "school_id": u.id,
                "school_name": u.school_name,
                "short_name": u.short_name,
                "sector": "公立" if is_pub else "私立",
                "round_title": window_card.cycle_label,
                "deadline_iso": window_card.primary_deadline_date,
                "deadline_display": window_card.primary_deadline_date or "待確認（依校方公告）",
                "month": int(window_card.primary_deadline_date[5:7]) if window_card.primary_deadline_date else None,
                "status_code": "needs_confirmation",
                "status_label": "待確認／依校方公告",
                "date_status_code": "needs_confirmation",
                "date_status_label": "待確認（依校方公告）",
                "note": window_card.online_deadline.value_text,
                "study_plan_note": window_card.study_plan_limit.value_text,
                "paper_note": window_card.paper_deadline.value_text,
                "source_url": src_url,
                "source_title": window_card.online_deadline.source_title,
                "checked_date": window_card.online_deadline.last_checked_at,
                "all_months": [int(window_card.primary_deadline_date[5:7])] if window_card.primary_deadline_date else [],
                "rounds_summary": [window_card.cycle_label],
            })
            continue

        # Sort periods so open/upcoming verified rounds surface as primary while keeping all months discoverable
        sorted_periods = sorted(
            periods,
            key=lambda p: (
                status_priority.get(p.status.value, 9),
                0 if p.deadline_at is not None else 1,
                p.deadline_at.isoformat() if p.deadline_at else "9999",
            ),
        )
        primary = sorted_periods[0]
        all_months = sorted({
            p.deadline_at.astimezone(TAIPEI_TZ).month
            for p in periods
            if p.deadline_at is not None
        })
        rounds_summary = []
        for p in sorted_periods[:3]:
            if p.deadline_at is not None:
                dt_local = p.deadline_at.astimezone(TAIPEI_TZ)
                d_txt = dt_local.strftime("%Y-%m-%d %H:%M")
            else:
                d_txt = "日期待確認"
            rounds_summary.append(f"{p.title}：{d_txt}（{PERIOD_STATUS_ZH.get(p.status.value, p.status.value)}）")

        if primary.deadline_at is not None:
            dt_tw = primary.deadline_at.astimezone(TAIPEI_TZ)
            deadline_iso = dt_tw.strftime("%Y-%m-%d")
            deadline_display = dt_tw.strftime("%Y-%m-%d %H:%M")
            primary_month: int | None = dt_tw.month
        else:
            deadline_iso = None
            deadline_display = "待確認（依校方公告）"
            primary_month = all_months[0] if all_months else None

        src_url = (
            safe_https_or_http_url(primary.source.source_url if primary.source else None)
            or safe_https_or_http_url(u.official_url)
        )
        src_title = (primary.source.title if primary.source and primary.source.title else f"{u.school_name}國際處交換公告")
        checked_str = (
            primary.checked_at.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d")
            if primary.checked_at
            else window_card.online_deadline.last_checked_at
        )
        note_text = primary.deadline_note or primary.status_note or "請查閱母校國際處最新簡章"

        rows.append({
            "school_id": u.id,
            "school_name": u.school_name,
            "short_name": u.short_name,
            "sector": "公立" if is_pub else "私立",
            "round_title": primary.title,
            "deadline_iso": deadline_iso,
            "deadline_display": deadline_display,
            "month": primary_month,
            "status_code": primary.status.value,
            "status_label": PERIOD_STATUS_ZH.get(primary.status.value, primary.status.value),
            "date_status_code": primary.date_status.value,
            "date_status_label": DATE_STATUS_ZH.get(primary.date_status.value, primary.date_status.value),
            "note": note_text,
            "study_plan_note": window_card.study_plan_limit.value_text,
            "paper_note": window_card.paper_deadline.value_text,
            "source_url": src_url,
            "source_title": src_title,
            "checked_date": checked_str,
            "all_months": all_months,
            "rounds_summary": rounds_summary,
        })

    _DEADLINES_CACHE = rows
    return rows


def build_reverse_timeline(
    school_id: str = "ntu",
    term_key: str = "2027-fall",
    custom_deadline: str | None = None,
) -> dict[str, Any]:
    try:
        uni = resolve_university(school_id) or SUPPORTED_UNIVERSITIES[0]
    except Exception:
        uni = SUPPORTED_UNIVERSITIES[0]

    if term_key not in TERM_OPTIONS:
        term_key = "2027-fall"
    term_info = TERM_OPTIONS[term_key]

    all_deadlines = build_all_71_school_deadlines()
    school_row = next((r for r in all_deadlines if r["school_id"] == uni.id), all_deadlines[0])

    anchor_date: date | None = None
    anchor_source_label = ""
    is_official_date = False

    if custom_deadline:
        try:
            anchor_date = datetime.strptime(custom_deadline.strip(), "%Y-%m-%d").date()
            anchor_source_label = "使用者自訂試算基準日（非校方公告日期，實際截止日以母校最新官方公告為準）"
        except ValueError:
            anchor_date = None

    if anchor_date is None:
        rec_iso = school_row["deadline_iso"]
        if rec_iso and term_key == "2027-fall" and school_row["date_status_code"] == "verified_exact" and rec_iso >= "2026-08-01":
            anchor_date = datetime.strptime(rec_iso, "%Y-%m-%d").date()
            anchor_source_label = f"帶入資料庫已核對期限（{school_row['round_title']}；送件前請再次核對國際處最新公告）"
            is_official_date = True
        else:
            anchor_date = term_info["default_anchor"]
            anchor_source_label = (
                "資料庫對該目標學期尚無當期確切截止日（或僅有歷史梯次參考），"
                "先以台灣大專校院常見收件期程作為個人倒推規劃基準；實際期限以母校最新官方公告為準"
            )

    departure_date: date = term_info["departure_date"]
    if departure_date <= anchor_date + timedelta(days=60):
        departure_date = anchor_date + timedelta(days=240)

    milestones = [
        {
            "id": "lang-exam",
            "offset": "截止前 180 天",
            "date": (anchor_date - timedelta(days=180)).isoformat(),
            "title": "確認目標語組門檻並報考語言檢定（預留重考緩衝）",
            "detail": "核對母校與目標姊妹校是否要求 IELTS Academic、TOEFL iBT、TOEIC 或 JLPT，確認成績單於校內截止日與姊妹校提名日皆在 2 年效期內。",
        },
        {
            "id": "partner-shortlist",
            "offset": "截止前 90 天",
            "date": (anchor_date - timedelta(days=90)).isoformat(),
            "title": "盤點母校合作校清單、授課語言與學分抵免規則",
            "detail": f"至 UniWay {uni.short_name}合作校頁面比對可申請學制、學院限制與歷年名額狀態，並向系辦確認海外學分採認原則。",
        },
        {
            "id": "recommendation-plan",
            "offset": "截止前 45 天",
            "date": (anchor_date - timedelta(days=45)).isoformat(),
            "title": "聯繫師長邀約推薦信、列出志願序與讀書計畫大綱",
            "detail": "提前至少 4 至 6 週禮貌詢問授課教授或導師推薦信意願，附上成績單與擬申請學校方向，同步查詢姊妹校課綱（Syllabus）。",
        },
        {
            "id": "study-plan-draft",
            "offset": "截止前 21 天",
            "date": (anchor_date - timedelta(days=21)).isoformat(),
            "title": "完成中／外文讀書計畫（Study Plan）與履歷初稿",
            "detail": f"母校讀書計畫規定參考：{school_row['study_plan_note']}",
        },
        {
            "id": "transcript-stamps",
            "offset": "截止前 10 天",
            "date": (anchor_date - timedelta(days=10)).isoformat(),
            "title": "申請歷年中英文成績單、在學證明並辦理系所核章",
            "detail": f"母校送件與核章規定參考：{school_row['paper_note']}",
        },
        {
            "id": "system-upload-check",
            "offset": "截止前 3 天",
            "date": (anchor_date - timedelta(days=3)).isoformat(),
            "title": "完成線上報名系統填報、PDF 檔案規格與報名費確認",
            "detail": "避開截止當日系統壅塞，逐一檢查上傳 PDF 檔案大小上限、簽名欄是否親簽，以及語言成績單掃描清晰度。",
        },
        {
            "id": "internal-deadline",
            "offset": "校內截止基準日",
            "date": anchor_date.isoformat(),
            "title": f"{uni.short_name}校內交換申請截止基準日（{'已核對紀錄' if is_official_date else '個人規劃基準，須查校方公告'}）",
            "detail": f"{school_row['note']}（官方來源：{school_row['source_url'] or uni.official_url}）",
        },
        {
            "id": "nomination-visa",
            "offset": "預計出發前 120 天",
            "date": (departure_date - timedelta(days=120)).isoformat(),
            "title": "獲母校提名後完成姊妹校網報、宿舍登記與簽證／役男出境申請",
            "detail": "校內錄取僅代表獲得母校推薦提名資格，仍須於姊妹校申請截止前繳交指定文件，收到正式入學許可（LoA）後辦理簽證與住宿。",
        },
    ]

    ics_query = urlencode({
        "school": uni.id,
        "term": term_key,
        "deadline": anchor_date.isoformat(),
    })

    return {
        "school_id": uni.id,
        "school_name": uni.school_name,
        "short_name": uni.short_name,
        "official_url": school_row["source_url"] or uni.official_url,
        "term_key": term_key,
        "term_label": term_info["label"],
        "anchor_date": anchor_date.isoformat(),
        "departure_date": departure_date.isoformat(),
        "is_official_date": is_official_date,
        "anchor_source_label": anchor_source_label,
        "school_recorded_round": school_row["round_title"],
        "school_recorded_deadline": school_row["deadline_display"],
        "school_recorded_status": school_row["status_label"],
        "school_checked_date": school_row["checked_date"],
        "milestones": milestones,
        "ics_url": f"/tools/timeline-generator.ics?{ics_query}",
    }


def _ics_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def build_reverse_timeline_ics(
    school_id: str = "ntu",
    term_key: str = "2027-fall",
    custom_deadline: str | None = None,
) -> tuple[str, str]:
    plan = build_reverse_timeline(school_id=school_id, term_key=term_key, custom_deadline=custom_deadline)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cal_name = f"UniWay {plan['short_name']} 交換申請倒推時程（{plan['term_key']}）"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//UniWay Taiwan//Exchange Reverse Timeline Generator//ZH-TW",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_ics_escape(cal_name)}",
        "X-WR-TIMEZONE:Asia/Taipei",
    ]
    source_url = plan["official_url"]
    for item in plan["milestones"]:
        start = datetime.strptime(item["date"], "%Y-%m-%d").date()
        end = start + timedelta(days=1)
        uid = f"uniway-timeline-{plan['school_id']}-{plan['term_key']}-{item['id']}-{start.strftime('%Y%m%d')}@app.uniway-tw.com"
        summary = f"[{plan['short_name']}交換規劃] {item['title']}"
        desc = (
            f"{item['detail']}\n"
            f"基準說明：{plan['anchor_source_label']}\n"
            f"母校官方來源：{source_url}\n"
            f"{MANDATORY_DISCLAIMER}"
        )
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{_ics_escape(uid)}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
            f"SUMMARY:{_ics_escape(summary)}",
            f"DESCRIPTION:{_ics_escape(desc)}",
            f"URL:{_ics_escape(source_url)}",
            "BEGIN:VALARM",
            "TRIGGER:-P3D",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_ics_escape(summary)}",
            "END:VALARM",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    filename = f"uniway-{plan['school_id']}-{plan['term_key']}-timeline.ics"
    return filename, "\r\n".join(lines) + "\r\n"


# ---------------------------------------------------------------------------
# 6. All-71-School Exchange Resource Overview Aggregator
# ---------------------------------------------------------------------------

def summarize_71_schools_overview(
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
) -> dict[str, Any]:
    """Compute real partner counts, country coverage, and language threshold stats across all 71 universities."""
    school_rows: list[dict[str, Any]] = []
    all_countries: set[str] = set()
    all_foreign_keys: set[str] = set()
    total_partner_pages = 0
    total_programme_rows = 0

    for u in SUPPORTED_UNIVERSITIES:
        partners, source = catalogue_loader(u)
        grouped: dict[str, list[PartnerUniversity]] = {}
        countries: set[str] = set()
        for p in partners:
            pid = partner_group_id(p)
            grouped.setdefault(pid, []).append(p)
            c_norm = canonical_country(p.country) or (p.country or "").strip()
            if c_norm:
                countries.add(c_norm)
                all_countries.add(c_norm)
            all_foreign_keys.add(f"{c_norm}|{school_identity_key(p.school_name)}")

        eng_toefl_ielts_count = 0
        toeic_count = 0
        jlpt_count = 0
        cefr_count = 0
        unconfirmed_lang_count = 0
        open_listed_count = 0

        for rows in grouped.values():
            if any(r.availability_status == "open" for r in rows):
                open_listed_count += 1
            parsed = extract_partner_language_thresholds(rows)
            if parsed["ielts_min"] is not None or parsed["toefl_min"] is not None:
                eng_toefl_ielts_count += 1
            if parsed["toeic_min"] is not None:
                toeic_count += 1
            if parsed["jlpt_min"] is not None:
                jlpt_count += 1
            if parsed["cefr_min"] is not None:
                cefr_count += 1
            if not parsed["has_any_parsed"]:
                unconfirmed_lang_count += 1

        total_partner_pages += len(grouped)
        total_programme_rows += len(partners)
        checked_dates = [p.checked_at for p in partners if p.checked_at is not None]
        latest_checked = (
            max(checked_dates).astimezone(TAIPEI_TZ).strftime("%Y-%m-%d")
            if checked_dates
            else (
                source.last_success_at.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d")
                if source and source.last_success_at
                else CATALOG_LAST_CHECKED_AT
            )
        )

        school_rows.append({
            "school_id": u.id,
            "school_name": u.school_name,
            "short_name": u.short_name,
            "english_name": u.english_name,
            "sector": "公立" if is_public_university(u) else "私立",
            "partner_page_count": len(grouped),
            "programme_row_count": len(partners),
            "country_count": len(countries),
            "open_listed_count": open_listed_count,
            "reference_or_pending_count": len(grouped) - open_listed_count,
            "eng_toefl_ielts_count": eng_toefl_ielts_count,
            "toeic_count": toeic_count,
            "jlpt_count": jlpt_count,
            "cefr_count": cefr_count,
            "unconfirmed_lang_count": unconfirmed_lang_count,
            "official_url": safe_https_or_http_url(u.official_url),
            "school_path": f"/schools/{u.id}",
            "latest_checked": latest_checked,
        })

    return {
        "university_count": len(school_rows),
        "public_count": sum(1 for r in school_rows if r["sector"] == "公立"),
        "private_count": sum(1 for r in school_rows if r["sector"] == "私立"),
        "total_partner_pages": total_partner_pages,
        "total_programme_rows": total_programme_rows,
        "unique_foreign_institutions": len(all_foreign_keys),
        "unique_countries": len(all_countries),
        "schools": school_rows,
    }
