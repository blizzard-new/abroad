"""Wave 3 database-driven annual open data pages (/data/...) — 4 comprehensive datasets.

Implements:
1. /data/toeic-friendly-partners  — 採計多益（TOEIC）交換合作校公開清單
2. /data/destination-costs        — 熱門交換國家一學期預算與官方補助比較總表
3. /data/english-taught-partners  — 歐陸與日韓英語授課交換合作校資料庫
4. /data/scholarships-taiwan      — 台灣交換學生獎學金與各國補助總表
"""
from __future__ import annotations

import re
import threading
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from html import escape
from time import monotonic
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from . import api as _api_mod
from .cross_school_partners import COUNTRY_SLUGS, build_cross_school_entity_index
from .destination_tips import canonical_country
from .models import CatalogueSourceStatus, PartnerUniversity
from .school_identity import school_identity_key
from .seo_guides import country_slug as destination_country_slug
from .tools_and_data_core import (
    BUDGET_COUNTRY_TEMPLATES,
    MANDATORY_DISCLAIMER,
    TAIPEI_TZ,
    PageMetaSpec,
    calculate_exchange_budget,
    extract_partner_language_thresholds,
    is_public_university,
    partner_group_id,
    render_compliance_strip,
    render_core_summary_and_citation_box,
    render_faq_section,
    safe_https_or_http_url,
)
from .tools_and_data_wave2 import OFFICIAL_SCHOLARSHIP_CATALOG
from .tools_wave3 import classify_region
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university
from .verified_window_deadlines import CATALOG_LAST_CHECKED_AT


WAVE3_DATA_SPECS: dict[str, PageMetaSpec] = {
    "/data/toeic-friendly-partners": PageMetaSpec(
        path="/data/toeic-friendly-partners",
        slug="toeic-friendly-partners",
        kind="data",
        short_title="多益友善交換學校清單",
        title="只考多益也能申請的交換學校清單｜全台 71 校列載 TOEIC 門檻合作校｜UniWay",
        h1="採計多益（TOEIC）交換合作校公開清單",
        description="從全台 71 所公私立大學交換合作校資料庫自動篩選明確列載多益（TOEIC）分數門檻之海外大學，支援依母校、多益分數上限與國家查詢。",
        core_conclusion="篩選全台 71 所大學資料庫中明確列載 TOEIC 分數門檻之海外合作校與國家分布，實際資格以各校最新官方公告為準。",
    ),
    "/data/destination-costs": PageMetaSpec(
        path="/data/destination-costs",
        slug="destination-costs",
        kind="data",
        short_title="各國交換預算與補助總表",
        title="熱門交換國家一學期預算與獎學金補助比較總表｜12 國生活費對照｜UniWay",
        h1="熱門交換國家一學期預算與官方補助比較總表",
        description="並排比較日本、韓國、德國、法國、英國、美國、荷蘭、捷克、新加坡、澳洲、加拿大與西班牙一學期住宿、伙食、保險、匯率緩衝與官方補助管道。",
        core_conclusion="並排比較十二個熱門交換國家一學期住宿、伙食、交通醫保預估費用與可對接官方獎助管道，實際收費標準以各校最新官方公告為準。",
    ),
    "/data/english-taught-partners": PageMetaSpec(
        path="/data/english-taught-partners",
        slug="english-taught-partners",
        kind="data",
        short_title="歐陸日韓英語授課名校庫",
        title="歐陸與日韓「英語授課」交換名校資料庫｜免第二外語檢定合作校整理｜UniWay",
        h1="歐陸與日韓英語授課交換合作校資料庫",
        description="彙整日本、韓國、德國、法國、荷蘭、捷克、北歐等非英語系國家中，明確列載英語檢定門檻或英語授課交換組別之海外大學與台灣締約母校清單。",
        core_conclusion="彙整非英語系國家中明確列載英語檢定門檻或英語授課交換方案之海外合作大學與締約母校，實際資格以各校最新官方公告為準。",
    ),
    "/data/scholarships-taiwan": PageMetaSpec(
        path="/data/scholarships-taiwan",
        slug="scholarships-taiwan",
        kind="data",
        short_title="台灣交換獎學金總表",
        title="台灣交換學生獎學金與補助總表｜學海飛颺・惜珠・各國政府與 71 校補助｜UniWay",
        h1="台灣交換學生獎學金與各國補助總表",
        description="完整整理教育部學海飛颺、學海惜珠、日本 JASSO、交流協會、韓國 GKS、歐盟 Erasmus+、德國 DAAD 及全台 71 所大學校內交換獎助資訊與官方連結。",
        core_conclusion="彙整教育部學海系列、各國政府與全台 71 校交換獎助管道、申請身分條件及官方連結，實際資格以各校最新官方公告為準。",
    ),
}

for _d3_path, _d3_spec in WAVE3_DATA_SPECS.items():
    if not (40 <= len(_d3_spec.core_conclusion) <= 60):
        raise ValueError(f"{_d3_path} core_conclusion length {len(_d3_spec.core_conclusion)} must be 40..60")


ENGLISH_PRIMARY_SLUGS = {
    "united-states",
    "united-kingdom",
    "canada",
    "australia",
    "new-zealand",
    "ireland",
}

_RE_ENG_TAUGHT = re.compile(
    r"(?:英語授課|英文授課|全英語|英語學程|英語組|英文組|english[- ]taught|taught in english|english track|courses in english)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# 1. TOEIC-Friendly Partners Aggregator
# ---------------------------------------------------------------------------

def build_toeic_friendly_dataset(
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
) -> dict[str, Any]:
    rows_out: list[dict[str, Any]] = []
    unique_foreign: set[str] = set()
    home_counter: Counter[str] = Counter()
    country_counter: Counter[tuple[str, str]] = Counter()
    latest_dates: list[str] = []

    for u in SUPPORTED_UNIVERSITIES:
        partners, source = catalogue_loader(u)
        if source and source.last_success_at:
            latest_dates.append(source.last_success_at.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d"))
        grouped: dict[str, list[PartnerUniversity]] = {}
        for p in partners:
            grouped.setdefault(partner_group_id(p), []).append(p)
            if p.checked_at:
                latest_dates.append(p.checked_at.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d"))

        for pid, p_rows in grouped.items():
            parsed = extract_partner_language_thresholds(p_rows)
            toeic_min = parsed["toeic_min"]
            if toeic_min is None:
                continue
            primary = p_rows[0]
            c_zh = canonical_country(primary.country) or (primary.country or "未標示").strip()
            c_slug = COUNTRY_SLUGS.get(c_zh, "other")
            fkey = f"{c_zh}|{school_identity_key(primary.school_name)}"
            unique_foreign.add(fkey)
            home_counter[u.id] += 1
            country_counter[(c_slug, c_zh)] += 1

            other_tests = []
            if parsed["ielts_min"] is not None:
                other_tests.append(f"IELTS {parsed['ielts_min']:g}")
            if parsed["toefl_min"] is not None:
                other_tests.append(f"TOEFL {parsed['toefl_min']:g}")
            if parsed["jlpt_min"] is not None:
                other_tests.append(f"JLPT {parsed['jlpt_min']}")

            mode_label = (
                "單獨列載 TOEIC"
                if not other_tests
                else f"並列（{'／'.join(other_tests)}）"
            )
            rows_out.append({
                "home_id": u.id,
                "home_name": u.school_name,
                "home_short": u.short_name,
                "pid": pid,
                "partner_name": primary.school_name,
                "country_zh": c_zh,
                "country_slug": c_slug,
                "toeic_min": int(round(toeic_min)),
                "mode_label": mode_label,
                "is_open": any(r.availability_status == "open" for r in p_rows),
                "partner_url": f"/schools/{u.id}/partners/{pid}",
                "source_url": safe_https_or_http_url(primary.source_url) or safe_https_or_http_url(u.official_url) or "",
            })

    rows_out.sort(key=lambda r: (r["toeic_min"], 0 if r["is_open"] else 1, r["country_zh"], r["partner_name"]))
    country_summary = [
        {"slug": slug, "name": zh, "count": cnt}
        for (slug, zh), cnt in sorted(country_counter.items(), key=lambda x: (-x[1], x[0][0]))
    ]
    return {
        "total_rows": len(rows_out),
        "unique_foreign_count": len(unique_foreign),
        "home_with_toeic_count": len(home_counter),
        "under_750_count": sum(1 for r in rows_out if r["toeic_min"] <= 750),
        "countries": country_summary,
        "rows": rows_out,
        "latest_checked": max(latest_dates) if latest_dates else CATALOG_LAST_CHECKED_AT,
    }


# ---------------------------------------------------------------------------
# 2. Destination Costs & Grants Master Table
# ---------------------------------------------------------------------------

COUNTRY_ZH_BY_SLUG: dict[str, str] = {
    "japan": "日本",
    "south-korea": "韓國",
    "germany": "德國",
    "france": "法國",
    "united-kingdom": "英國",
    "united-states": "美國",
    "netherlands": "荷蘭",
    "czechia": "捷克",
    "singapore": "新加坡",
    "australia": "澳洲",
    "canada": "加拿大",
    "spain": "西班牙",
}

COUNTRY_GRANTS_NOTE: dict[str, str] = {
    "japan": "教育部學海飛颺／惜珠、日本 JASSO（月額 8 萬日圓）、日本台灣交流協會獎學金",
    "south-korea": "教育部學海飛颺／惜珠、韓國政府 GKS 交換生獎助、母校校內國際交流補助",
    "germany": "教育部學海飛颺／惜珠、德國 DAAD 及各邦基金會獎學金、歐盟 Erasmus+ ICM",
    "france": "教育部學海飛颺／惜珠、法國在台協會獎助、入境後合規租約可申辦 CAF 房補",
    "united-kingdom": "教育部學海飛颺／惜珠、母校校內歐美地區定額獎助學金",
    "united-states": "教育部學海飛颺／惜珠、母校校內美洲地區交換獎助學金",
    "netherlands": "教育部學海飛颺／惜珠、歐盟 Erasmus+ ICM（視兩校當期專案）、母校校內補助",
    "czechia": "教育部學海飛颺／惜珠、歐盟 Erasmus+ ICM、捷克政府／雙邊交流獎助",
    "singapore": "教育部學海飛颺／惜珠、新加坡接待大學特定合作獎助、母校校內補助",
    "australia": "教育部學海飛颺／惜珠、母校校內大洋洲交換獎助學金",
    "canada": "教育部學海飛颺／惜珠、母校校內美洲地區交換獎助學金",
    "spain": "教育部學海飛颺／惜珠、歐盟 Erasmus+ ICM（視兩校當期專案）、母校校內補助",
}


def build_destination_costs_dataset(
    entities: Mapping[Any, Any],
) -> dict[str, Any]:
    inst_counts: Counter[str] = Counter()
    for ent in entities.values():
        inst_counts[ent.country_slug] += 1

    rows: list[dict[str, Any]] = []
    fx_date = "2026-10-02"
    for slug in BUDGET_COUNTRY_TEMPLATES:
        calc = calculate_exchange_budget(country_key=slug)
        fx_date = calc["fx_fetched_date"]
        c_zh = COUNTRY_ZH_BY_SLUG.get(slug, slug)
        reg = classify_region(c_zh)
        high_total = calc["base_gross_twd"] + calc["fx_buffer_delta_twd"]
        rows.append({
            "slug": slug,
            "country_zh": c_zh,
            "template_name": calc["template_name"],
            "region": reg,
            "months": calc["months"],
            "currency": calc["currency"],
            "rate": calc["rate"],
            "housing": calc["housing"],
            "food": calc["food"],
            "transport_other": calc["transport"] + calc["other"],
            "monthly_foreign": calc["monthly_foreign"],
            "monthly_twd": calc["base_monthly_twd"],
            "one_time_twd": calc["one_time_twd"],
            "semester_twd": calc["base_gross_twd"],
            "high_fx_twd": high_total,
            "partner_inst_count": inst_counts.get(slug, 0),
            "grants_note": COUNTRY_GRANTS_NOTE.get(slug, "教育部學海系列與母校校內補助"),
            "destination_url": f"/destinations/{slug}" if destination_country_slug(c_zh) else f"/partners/{slug}",
            "calc_url": f"/tools/exchange-budget-calculator?country={slug}",
        })

    return {
        "fx_date": fx_date,
        "count": len(rows),
        "min_twd": min(r["semester_twd"] for r in rows),
        "max_twd": max(r["semester_twd"] for r in rows),
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# 3. English-Taught Non-Anglophone Partners Aggregator
# ---------------------------------------------------------------------------

def build_english_taught_dataset(
    entities: Mapping[Any, Any],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    country_counter: Counter[tuple[str, str]] = Counter()
    latest_dates: list[str] = []

    for ent in entities.values():
        if ent.country_slug in ENGLISH_PRIMARY_SLUGS:
            continue

        all_rows: list[PartnerUniversity] = []
        eng_homes: list[dict[str, str]] = []
        explicit_track_cue = False

        for u in SUPPORTED_UNIVERSITIES:
            u_rows = ent.home_rows.get(u.id)
            if not u_rows:
                continue
            for r in u_rows:
                if r.checked_at:
                    latest_dates.append(r.checked_at.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d"))
            u_parsed = extract_partner_language_thresholds(u_rows)
            text_blob = " ".join(
                filter(
                    None,
                    (
                        *(r.program_type for r in u_rows),
                        *(r.language_requirement for r in u_rows),
                        *(r.course_restrictions for r in u_rows),
                        *(r.eligibility for r in u_rows),
                    ),
                )
            )
            has_cue = bool(_RE_ENG_TAUGHT.search(text_blob))
            has_eng_score = any(
                u_parsed[k] is not None for k in ("ielts_min", "toefl_min", "toeic_min", "cefr_min")
            )
            if has_eng_score or has_cue:
                if has_cue:
                    explicit_track_cue = True
                all_rows.extend(u_rows)
                eng_homes.append({
                    "id": u.id,
                    "short_name": u.short_name,
                    "partner_url": f"/schools/{u.id}/partners/{partner_group_id(u_rows[0])}",
                    "source_url": safe_https_or_http_url(u_rows[0].source_url) or safe_https_or_http_url(u.official_url) or "",
                })

        if not eng_homes:
            continue

        agg_parsed = extract_partner_language_thresholds(all_rows)
        badges: list[str] = []
        if agg_parsed["ielts_min"] is not None:
            badges.append(f"IELTS {agg_parsed['ielts_min']:g}")
        if agg_parsed["toefl_min"] is not None:
            badges.append(f"TOEFL {agg_parsed['toefl_min']:g}")
        if agg_parsed["toeic_min"] is not None:
            badges.append(f"TOEIC {agg_parsed['toeic_min']:g}")
        if agg_parsed["cefr_min"] is not None:
            badges.append(f"CEFR {agg_parsed['cefr_min']}")

        country_counter[(ent.country_slug, ent.country_name_zh)] += 1
        items.append({
            "display_title": ent.display_title,
            "school_name_zh": ent.school_name_zh,
            "school_name_en": ent.school_name_en,
            "country_zh": ent.country_name_zh,
            "country_slug": ent.country_slug,
            "canonical_path": ent.canonical_path,
            "eng_home_count": len(eng_homes),
            "homes": eng_homes,
            "ielts_min": agg_parsed["ielts_min"],
            "toefl_min": agg_parsed["toefl_min"],
            "toeic_min": agg_parsed["toeic_min"],
            "badges": " ／ ".join(badges) if badges else "註明英語組／英語授課（門檻見簡章）",
            "explicit_track_cue": explicit_track_cue,
            "primary_source_url": safe_https_or_http_url(ent.official_website) or eng_homes[0]["source_url"],
        })

    items.sort(key=lambda x: (-x["eng_home_count"], x["country_slug"], x["display_title"]))
    country_options = [
        {"slug": s, "name": z, "count": c}
        for (s, z), c in sorted(country_counter.items(), key=lambda item: (-item[1], item[0][0]))
    ]
    return {
        "total_institutions": len(items),
        "country_count": len(country_options),
        "countries": country_options,
        "items": items,
        "latest_checked": max(latest_dates) if latest_dates else CATALOG_LAST_CHECKED_AT,
    }


# ---------------------------------------------------------------------------
# 4. Taiwan Scholarships & 71-School Grants Directory
# ---------------------------------------------------------------------------

EXTRA_SCHOLARSHIP_ENTRIES: tuple[dict[str, str], ...] = (
    {
        "id": "austria-oead",
        "category": "foreign",
        "category_label": "外國政府／機構",
        "name": "奧地利學術交流總署（OeAD）獎學金資料庫（Ernst Mach Grant 等）",
        "sponsor": "奧地利聯邦教育科學研究部 ／ OeAD",
        "eligibility": "赴奧地利合作高等學府或應用科技大學（FH）交換研修之在學生，依各子計畫規定申請。",
        "funding": "依當年度簡章核給每月生活津貼，申請截止日通常早於出發前半年以上。",
        "official_url": "https://grants.at/en/",
        "official_label": "奧地利官方獎學金網 grants.at",
    },
    {
        "id": "fulbright-tw",
        "category": "foreign",
        "category_label": "雙邊基金會",
        "name": "學術交流基金會（Fulbright Taiwan）赴美進修與交流獎助資訊",
        "sponsor": "財團法人學術交流基金會",
        "eligibility": "依各年度公告之學位生、青年學者與專案交流計畫資格辦理（大學部一般交換請先查母校獎助與學海計畫）。",
        "funding": "依各子計畫核定項目補助。",
        "official_url": "https://www.fulbright.org.tw/",
        "official_label": "Fulbright Taiwan 官方網站",
    },
)


def _extract_school_scholarship_summary(u: UniversityProfile) -> tuple[str, str | None, bool]:
    builder = getattr(_api_mod, f"build_{u.id}_student_dashboard", None)
    if builder is None:
        return "請至該校國際處官網查閱當年度出國交換獎助學金辦法與學海飛颺校內甄選公告。", None, False
    dash = builder(partner_universities=[])
    raw = getattr(dash, "scholarship_info", None)
    chunks: list[str] = []
    doc_url: str | None = None
    if isinstance(raw, str) and raw.strip():
        chunks.append(raw.strip())
    elif isinstance(raw, Sequence):
        for elem in raw[:2]:
            if isinstance(elem, str) and elem.strip():
                chunks.append(elem.strip())
            else:
                title_txt = str(getattr(elem, "title", "") or "").strip()
                details_seq = getattr(elem, "details", None)
                detail_txt = ""
                if isinstance(details_seq, Sequence) and not isinstance(details_seq, str) and details_seq:
                    detail_txt = str(details_seq[0] or "").strip()
                else:
                    detail_txt = str(getattr(elem, "summary", "") or getattr(elem, "description", "") or "").strip()
                src_obj = getattr(elem, "source", None)
                if not doc_url and src_obj is not None:
                    doc_url = safe_https_or_http_url(getattr(src_obj, "source_url", None))
                merged = "：".join(p for p in (title_txt, detail_txt) if p)
                if merged:
                    chunks.append(merged)
    text = re.sub(r"\s+", " ", " ； ".join(chunks)).strip().replace("——", "—")
    if not text:
        return "依校內出國交換生獎助辦法與教育部學海計畫校內配額辦理（詳見國際處簡章）。", doc_url, False
    if len(text) > 115:
        text = text[:114].rstrip() + "…"
    return text, doc_url, True


def build_scholarships_taiwan_dataset() -> dict[str, Any]:
    national_and_foreign: list[dict[str, str]] = []
    for item in OFFICIAL_SCHOLARSHIP_CATALOG:
        if item["id"] == "home-university-grant":
            continue
        cat = "moe" if item["id"].startswith("moe-") else "foreign"
        cat_label = "教育部全國計畫" if cat == "moe" else "外國政府／國際機構"
        national_and_foreign.append({
            "id": item["id"],
            "category": cat,
            "category_label": cat_label,
            "name": item["name"],
            "sponsor": item["sponsor"],
            "eligibility": item["eligibility_note"],
            "funding": item["funding_note"],
            "official_url": item["official_url"],
            "official_label": item["official_label"],
        })
    national_and_foreign.extend(EXTRA_SCHOLARSHIP_ENTRIES)

    school_grants: list[dict[str, Any]] = []
    documented_count = 0
    for u in SUPPORTED_UNIVERSITIES:
        summary, doc_url, has_doc = _extract_school_scholarship_summary(u)
        if has_doc:
            documented_count += 1
        school_grants.append({
            "school_id": u.id,
            "school_name": u.school_name,
            "short_name": u.short_name,
            "sector": "公立" if is_public_university(u) else "私立",
            "has_documented_note": has_doc,
            "summary": summary,
            "school_url": f"/schools/{u.id}",
            "official_url": doc_url or safe_https_or_http_url(u.official_url) or "https://www.studyabroad.moe.gov.tw/",
        })

    return {
        "national_and_foreign": national_and_foreign,
        "school_grants": school_grants,
        "documented_school_count": documented_count,
    }


# ---------------------------------------------------------------------------
# Wave 3 Data Page FAQs
# ---------------------------------------------------------------------------

FAQS_TOEIC_DATA: tuple[tuple[str, str], ...] = (
    (
        "表格標示「單獨列載 TOEIC」跟「並列托福／雅思」有什麼差別？",
        "「單獨列載 TOEIC」代表該合作校條目僅出現多益門檻；「並列」則可能是「多益或托福擇一達標即可」，也可能是「不同語組分別要求」，報名前請點擊官方來源核對簡章原文。",
    ),
    (
        "只考多益（TOEIC L&R）可以申請哪些國家的交換學校最多？",
        "資料庫統計顯示，明確列載採計多益成績的合作校主要集中於日本（英語授課學程 JUSST/AIU 等）、韓國、法國商學院、捷克、波蘭與東南亞夥伴大學；英美澳主流綜合大學則多半要求 TOEFL iBT 或 IELTS。",
    ),
    (
        "多益口說與寫作測驗（TOEIC S&W）會被要求嗎？",
        "少數歐洲或亞洲大學若接受多益替代托福雅思，會額外要求檢附 TOEIC Speaking & Writing 成績，請務必展開合作校最新年度 Fact Sheet 確認。",
    ),
)

FAQS_DEST_COSTS: tuple[tuple[str, str], ...] = (
    (
        "哪幾個熱門交換國家的一學期總花費相對親民？",
        "依 12 國規劃模板比較，捷克、韓國、日本（非東京核心區或抽中大學寮）與西班牙的一學期生活費加機票簽證預估總額通常低於英、美、澳、加；若再搭配學海飛颺或 JASSO／Erasmus+ 補助，自備款壓力可進一步降低。",
    ),
    (
        "為什麼美國與澳洲的一學期預估費用特別高？",
        "除當地房租與外食成本較高外，美國大學常強制投保校方指定醫療保險與綁定校園餐費（Meal Plan），澳洲則強制投保 OSHC 海外學生醫保且長程機票簽證規費較高。",
    ),
    (
        "表中的匯率與月生活費多久更新一次？",
        "外幣換算採用系統收錄之台銀牌告參考匯率，並同步列出「外幣升值 +10%」之壓力測試金額；點擊任一國家的「個人化細算」即可手動調整房租與獎學金。",
    ),
)

FAQS_ENG_TAUGHT: tuple[tuple[str, str], ...] = (
    (
        "不會日文、韓文、德文或法文，也能去日本、韓國或歐洲交換嗎？",
        "可以。日本、韓國、德國、法國、荷蘭、北歐與捷克許多大學均設有專為國際交換生開設的「英語授課學程（English-taught Track）」，只要持有效英語檢定成績即可修讀專業學分。",
    ),
    (
        "申請非英語系國家的英語授課組，日常生活完全不會當地語言有影響嗎？",
        "課堂學習與行政溝通可用英文完成，但超市採買、看診與租屋行政若具備 A1–A2 基礎生活會話會順暢許多；許多接待校亦免費提供交換生初級當地語言選修課。",
    ),
    (
        "資料庫如何判定一所非英語系大學提供英語交換機會？",
        "系統掃描全台 71 所大學公開合作校資料，僅收錄「明確列載 IELTS／TOEFL／TOEIC／CEFR 英語門檻」或「方案名稱／限制欄註明英語授課」之紀錄，不臆測未標示校系。",
    ),
)

FAQS_SCHOLARSHIPS_TW: tuple[tuple[str, str], ...] = (
    (
        "教育部「學海飛颺」和「學海惜珠」學生可以直接上網向教育部報名嗎？",
        "不行。學海飛颺與學海惜珠皆由「國內就讀母校國際處」統一受理校內申請、評選並向教育部薦送，截止日與配合款辦法依各大學國際處公告為準。",
    ),
    (
        "可以同時領取教育部學海飛颺和母校校內交換獎學金嗎？",
        "依教育部補助要點，同一研修計畫不得同時兼領我國政府提供之其他出國補助；至於母校自籌校務基金／校友捐助獎學金或外國政府（如 JASSO）可否兼領，須依母校與該外國機構當年度規定核對。",
    ),
    (
        "赴大陸地區或港澳交換可以申請教育部學海飛颺嗎？",
        "依教育部學海計畫要點，選送國家地區不包含大陸地區及香港、澳門；赴陸港澳交換生請改查閱母校校內自辦之出國／兩岸交流獎助學金。",
    ),
)


# ---------------------------------------------------------------------------
# Route Registration for Wave 3 Data Pages
# ---------------------------------------------------------------------------

def register_wave3_data_routes(
    router: APIRouter,
    *,
    settings: Any,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    render_data_page: Callable[..., HTMLResponse],
    render_switcher: Callable[[str], str],
    official_link: Callable[[str | None, str], str],
) -> None:
    cache_lock = threading.Lock()
    state: dict[str, Any] = {
        "toeic_at": 0.0,
        "toeic": None,
        "ent_at": 0.0,
        "entities": None,
        "eng_at": 0.0,
        "eng": None,
        "schol_at": 0.0,
        "schol": None,
    }

    def get_entities() -> Mapping[Any, Any]:
        with cache_lock:
            if state["entities"] is not None and monotonic() - state["ent_at"] < 60.0:
                return state["entities"]
            entities, _ = build_cross_school_entity_index(catalogue_loader, require_complete=True)
            state["entities"] = entities
            state["ent_at"] = monotonic()
            return entities

    def get_toeic_data() -> dict[str, Any]:
        with cache_lock:
            if state["toeic"] is not None and monotonic() - state["toeic_at"] < 60.0:
                return state["toeic"]
            d = build_toeic_friendly_dataset(catalogue_loader)
            state["toeic"] = d
            state["toeic_at"] = monotonic()
            return d

    def get_eng_taught_data() -> dict[str, Any]:
        ents = get_entities()
        with cache_lock:
            if state["eng"] is not None and monotonic() - state["eng_at"] < 60.0:
                return state["eng"]
            d = build_english_taught_dataset(ents)
            state["eng"] = d
            state["eng_at"] = monotonic()
            return d

    def get_schol_data() -> dict[str, Any]:
        with cache_lock:
            if state["schol"] is not None and monotonic() - state["schol_at"] < 60.0:
                return state["schol"]
            d = build_scholarships_taiwan_dataset()
            state["schol"] = d
            state["schol_at"] = monotonic()
            return d

    # 1. /data/toeic-friendly-partners
    @router.api_route("/data/toeic-friendly-partners", methods=["GET", "HEAD"])
    def data_toeic_friendly_partners(
        home: str = Query(default="all"),
        max_score: int = Query(default=990, ge=300, le=990),
        country: str = Query(default="all"),
        q: str = Query(default=""),
    ) -> HTMLResponse:
        spec = WAVE3_DATA_SPECS["/data/toeic-friendly-partners"]
        ds = get_toeic_data()
        rows = list(ds["rows"])

        target_uni = resolve_university(home) if (home and home != "all") else None
        if target_uni:
            rows = [r for r in rows if r["home_id"] == target_uni.id]
        else:
            home = "all"

        valid_countries = {c["slug"] for c in ds["countries"]}
        if country != "all" and country in valid_countries:
            rows = [r for r in rows if r["country_slug"] == country]
        else:
            country = "all"

        rows = [r for r in rows if r["toeic_min"] <= max_score]
        q_clean = q.strip()
        if q_clean:
            ql = q_clean.casefold()
            rows = [
                r for r in rows
                if ql in r["partner_name"].casefold()
                or ql in r["home_name"].casefold()
                or ql in r["country_zh"].casefold()
            ]

        home_opts = '<option value="all">全部 71 所台灣母校</option>' + "".join(
            f'<option value="{escape(u.id)}"{" selected" if target_uni and u.id == target_uni.id else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )
        score_opts = "".join(
            f'<option value="{val}"{" selected" if max_score == val else ""}>{lbl}</option>'
            for val, lbl in (
                (990, "不限多益門檻（全部列載校）"),
                (600, "TOEIC 600 分以內可達標"),
                (750, "TOEIC 750 分以內可達標"),
                (800, "TOEIC 800 分以內可達標"),
                (860, "TOEIC 860 分（金色證書）以內"),
            )
        )
        c_opts = '<option value="all">全部國家／地區</option>' + "".join(
            f'<option value="{escape(c["slug"])}"{" selected" if country == c["slug"] else ""}>{escape(c["name"])}（{c["count"]} 筆）</option>'
            for c in ds["countries"][:30]
        )

        shown = rows[:120]
        tbody_html = ""
        for r in shown:
            tbody_html += (
                f"<tr data-toeic-score='{r['toeic_min']}' data-toeic-country='{escape(r['country_slug'])}' data-toeic-name='{escape(r['partner_name'])} {escape(r['home_name'])} {escape(r['country_zh'])}'>"
                f"<th scope='row'><a href='{escape(r['partner_url'])}'>{escape(r['partner_name'])}</a><span class='uw-inline-badge'>{escape(r['country_zh'])}</span></th>"
                f"<td><a href='/schools/{escape(r['home_id'])}'>{escape(r['home_short'])}</a></td>"
                f"<td><strong>TOEIC {r['toeic_min']}</strong></td>"
                f"<td>{escape(r['mode_label'])}</td>"
                f"<td><a href='{escape(r['partner_url'])}'>合作方案</a> · {official_link(r['source_url'], '官方來源')}</td></tr>"
            )
        if not tbody_html:
            tbody_html = "<tr><td colspan='5'>目前篩選條件下無列載 TOEIC 門檻之紀錄，請放寬分數或切換母校。</td></tr>"

        country_sum_rows = "".join(
            f"<tr><th scope='row'>{escape(c['name'])}</th><td><strong>{c['count']} 筆</strong></td>"
            f"<td><a href='/data/toeic-friendly-partners?country={escape(c['slug'])}'>篩選此國清單</a></td></tr>"
            for c in ds["countries"][:15]
        )

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="tf-heading">
  <div class="uw-tool-header">
    <h2 id="tf-heading">篩選明確列載 TOEIC 門檻之合作校（符合 <span id="toeic-visible-count">{len(rows)}</span> 筆，預覽前 {len(shown)} 筆）</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-sm uw-btn-outline" href="/data/toeic-friendly-partners">重設</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製網址</button>
    </div>
  </div>
  <div class="uw-kpi-grid">
    <div class="uw-kpi-box uw-kpi-highlight"><span class="uw-kpi-label">列載 TOEIC 方案筆數</span><strong class="uw-kpi-value">{ds['total_rows']} 筆</strong><span class="uw-kpi-tag">跨 {ds['home_with_toeic_count']} 所台灣母校</span></div>
    <div class="uw-kpi-box"><span class="uw-kpi-label">去重海外合作大學</span><strong class="uw-kpi-value">{ds['unique_foreign_count']} 所</strong><span class="uw-kpi-tag">明確寫出多益分數</span></div>
    <div class="uw-kpi-box"><span class="uw-kpi-label">750 分以內可達標</span><strong class="uw-kpi-value">{ds['under_750_count']} 筆</strong><span class="uw-kpi-tag">中階多益友善門檻</span></div>
  </div>

  <form method="get" action="/data/toeic-friendly-partners" class="uw-form-grid" data-data-filter="toeic-partners">
    <label class="uw-field"><span>台灣母校</span><select name="home" id="tf-home">{home_opts}</select></label>
    <label class="uw-field"><span>多益分數上限</span><select name="max_score" id="tf-score">{score_opts}</select></label>
    <label class="uw-field"><span>目的地國家</span><select name="country" id="tf-country">{c_opts}</select></label>
    <label class="uw-field"><span>搜尋校名</span><input type="search" name="q" id="tf-q" value="{escape(q_clean)}" placeholder="輸入海外或台灣校名…"></label>
    <div class="uw-form-actions"><button type="submit" class="uw-btn uw-btn-primary">套用篩選</button></div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="採計多益 TOEIC 交換合作校清單">
    <table class="uw-data-table" id="toeic-data-table">
      <caption class="uw-sr-only">全台 71 所大學交換資料庫明確列載 TOEIC 多益門檻合作校清單</caption>
      <thead>
        <tr><th scope="col">海外合作大學</th><th scope="col">台灣母校</th><th scope="col">列載最低多益</th><th scope="col">門檻標示型態</th><th scope="col">詳情與官方來源</th></tr>
      </thead>
      <tbody id="toeic-tbody">{tbody_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>列載多益門檻最多之前 15 大交換國家統計表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="列載多益門檻國家分布表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">列載多益門檻合作校筆數前 15 大國家</caption>
          <thead><tr><th scope="col">國家／地區</th><th scope="col">列載 TOEIC 合作校頁數</th><th scope="col">快速檢視</th></tr></thead>
          <tbody>{country_sum_rows}</tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_TOEIC_DATA)}
  {render_core_summary_and_citation_box(settings.origin, spec, checked_date=ds['latest_checked'])}
  {render_compliance_strip()}
</div>"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data"), (spec.short_title, spec.path)],
            FAQS_TOEIC_DATA,
            variables=("海外合作大學", "列載最低多益分數", "門檻標示型態", "台灣締約母校"),
            keywords=("多益交換學生", "免托福雅思交換學校", "TOEIC交換清單", "多益750交換"),
            date_modified=ds["latest_checked"],
        )

    # 2. /data/destination-costs
    @router.api_route("/data/destination-costs", methods=["GET", "HEAD"])
    def data_destination_costs(
        region: str = Query(default="all"),
        sort: str = Query(default="cost_asc"),
    ) -> HTMLResponse:
        spec = WAVE3_DATA_SPECS["/data/destination-costs"]
        ds = build_destination_costs_dataset(get_entities())
        rows = list(ds["rows"])

        if region in ("asia", "europe", "americas", "oceania"):
            rows = [r for r in rows if r["region"] == region]
        else:
            region = "all"

        if sort == "cost_desc":
            rows.sort(key=lambda r: -r["semester_twd"])
        elif sort == "partners_desc":
            rows.sort(key=lambda r: -r["partner_inst_count"])
        else:
            sort = "cost_asc"
            rows.sort(key=lambda r: r["semester_twd"])

        reg_opts = "".join(
            f'<option value="{k}"{" selected" if region == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("all", "全部 12 個熱門交換國家"),
                ("asia", "亞洲（日本・韓國・新加坡）"),
                ("europe", "歐洲（德・法・英・荷・捷・西）"),
                ("americas", "美洲（美國・加拿大）"),
                ("oceania", "大洋洲（澳洲）"),
            )
        )
        sort_opts = "".join(
            f'<option value="{k}"{" selected" if sort == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("cost_asc", "學期基準總預算（低 → 高）"),
                ("cost_desc", "學期基準總預算（高 → 低）"),
                ("partners_desc", "台灣締約海外大學數（多 → 少）"),
            )
        )

        tbody_html = ""
        for r in rows:
            tbody_html += (
                f"<tr data-dc-region='{escape(r['region'])}' data-dc-cost='{r['semester_twd']}' data-dc-partners='{r['partner_inst_count']}'>"
                f"<th scope='row'><a href='{escape(r['destination_url'])}'><strong>{escape(r['country_zh'])}</strong></a>"
                f"<div class='uw-cell-sub'>{r['months']} 個月模板 · 全台締約 {r['partner_inst_count']} 校</div></th>"
                f"<td>{escape(r['currency'])}（匯率 {r['rate']:g}）</td>"
                f"<td>{r['currency']} {r['monthly_foreign']:,.0f}／月<div class='uw-cell-sub'>約 NT$ {r['monthly_twd']:,}／月（宿 {r['housing']:,.0f}＋食 {r['food']:,.0f}）</div></td>"
                f"<td>NT$ {r['one_time_twd']:,}</td>"
                f"<td><strong>NT$ {r['semester_twd']:,}</strong><div class='uw-cell-sub'>+10% 匯差：NT$ {r['high_fx_twd']:,}</div></td>"
                f"<td>{escape(r['grants_note'])}<div class='uw-cell-sub'><a href='{escape(r['calc_url'])}'>帶入預算試算器 →</a></div></td></tr>"
            )

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="dc-heading">
  <div class="uw-tool-header">
    <h2 id="dc-heading">12 國一學期交換總花費與補助並排對照（顯示 <span id="dc-visible-count">{len(rows)}</span> 國）</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製比較網址</button>
  </div>
  <div class="uw-kpi-grid">
    <div class="uw-kpi-box uw-kpi-highlight"><span class="uw-kpi-label">收錄熱門國家模板</span><strong class="uw-kpi-value">{ds['count']} 國</strong><span class="uw-kpi-tag">外幣匯率參考日：{escape(ds['fx_date'])}</span></div>
    <div class="uw-kpi-box"><span class="uw-kpi-label">親民預算區間起點</span><strong class="uw-kpi-value">NT$ {ds['min_twd']:,}</strong><span class="uw-kpi-tag">未扣獎學金前基準估算</span></div>
    <div class="uw-kpi-box"><span class="uw-kpi-label">高物價英語系區間</span><strong class="uw-kpi-value">NT$ {ds['max_twd']:,}</strong><span class="uw-kpi-tag">含強制醫保與長程機票估算</span></div>
  </div>

  <form method="get" action="/data/destination-costs" class="uw-form-grid" data-data-filter="dest-costs">
    <label class="uw-field"><span>洲別篩選</span><select name="region" id="dc-region">{reg_opts}</select></label>
    <label class="uw-field"><span>排序依據</span><select name="sort" id="dc-sort">{sort_opts}</select></label>
    <div class="uw-form-actions uw-nojs-only"><button type="submit" class="uw-btn uw-btn-primary">套用排序</button></div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="12 國交換學生一學期預算與補助比較總表">
    <table class="uw-data-table" id="dc-data-table">
      <caption class="uw-sr-only">十二個熱門交換國家一學期生活費、機票簽證與官方補助對照總表</caption>
      <thead>
        <tr><th scope="col">交換國家</th><th scope="col">幣別與基準匯率</th><th scope="col">預估月生活費</th><th scope="col">行前一次性費用</th><th scope="col">一學期基準總支出</th><th scope="col">主要可申請官方補助</th></tr>
      </thead>
      <tbody id="dc-tbody">{tbody_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  {render_faq_section(FAQS_DEST_COSTS)}
  {render_core_summary_and_citation_box(settings.origin, spec, checked_date=ds['fx_date'])}
  {render_compliance_strip()}
</div>"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data"), (spec.short_title, spec.path)],
            FAQS_DEST_COSTS,
            variables=("月生活費外幣金額", "行前機票簽證保險估算", "一學期基準總台幣支出", "+10%匯率緩衝總額", "主要官方獎學金"),
            keywords=("出國交換費用比較", "各國交換預算表", "日本德國美國交換花費", "交換學生生活費總表"),
            date_modified=ds["fx_date"],
        )

    # 3. /data/english-taught-partners
    @router.api_route("/data/english-taught-partners", methods=["GET", "HEAD"])
    def data_english_taught_partners(
        country: str = Query(default="all"),
        tier: str = Query(default="all"),
        q: str = Query(default=""),
    ) -> HTMLResponse:
        spec = WAVE3_DATA_SPECS["/data/english-taught-partners"]
        ds = get_eng_taught_data()
        items = list(ds["items"])

        valid_c = {c["slug"] for c in ds["countries"]}
        if country != "all" and country in valid_c:
            items = [x for x in items if x["country_slug"] == country]
        else:
            country = "all"

        if tier == "ielts60":
            items = [x for x in items if x["ielts_min"] is not None and x["ielts_min"] <= 6.0]
        elif tier == "toefl80":
            items = [x for x in items if x["toefl_min"] is not None and x["toefl_min"] <= 80.0]
        elif tier == "toeic":
            items = [x for x in items if x["toeic_min"] is not None]
        else:
            tier = "all"

        q_clean = q.strip()
        if q_clean:
            ql = q_clean.casefold()
            items = [
                x for x in items
                if ql in x["display_title"].casefold()
                or ql in x["school_name_en"].casefold()
                or ql in x["country_zh"].casefold()
            ]

        c_opts = '<option value="all">全部非英語系國家</option>' + "".join(
            f'<option value="{escape(c["slug"])}"{" selected" if country == c["slug"] else ""}>{escape(c["name"])}（{c["count"]} 校）</option>'
            for c in ds["countries"][:30]
        )
        tier_opts = "".join(
            f'<option value="{k}"{" selected" if tier == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("all", "全部英語授課／英檢門檻合作校"),
                ("ielts60", "列載 IELTS ≤ 6.0 可達標"),
                ("toefl80", "列載 TOEFL iBT ≤ 80 可達標"),
                ("toeic", "列載採計 TOEIC 多益成績"),
            )
        )

        shown = items[:100]
        tbody_html = ""
        for it in shown:
            home_links = "、".join(
                f"<a href='{escape(h['partner_url'])}'>{escape(h['short_name'])}</a>"
                for h in it["homes"][:6]
            )
            if len(it["homes"]) > 6:
                home_links += f" 等 {len(it['homes'])} 校"
            tbody_html += (
                f"<tr data-et-country='{escape(it['country_slug'])}' data-et-name='{escape(it['display_title'])} {escape(it['school_name_en'])} {escape(it['country_zh'])}'>"
                f"<th scope='row'><a href='{escape(it['canonical_path'])}'>{escape(it['display_title'])}</a>"
                f"<span class='uw-inline-badge'>{escape(it['country_zh'])}</span></th>"
                f"<td><strong>{it['eng_home_count']} 校</strong></td>"
                f"<td>{escape(it['badges'])}</td>"
                f"<td>{home_links}</td>"
                f"<td><a href='{escape(it['canonical_path'])}'>跨校頁</a> · {official_link(it['primary_source_url'], '官方來源')}</td></tr>"
            )
        if not tbody_html:
            tbody_html = "<tr><td colspan='5'>找不到符合此篩選條件的合作校，請調整國家或語檢條件。</td></tr>"

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="et-heading">
  <div class="uw-tool-header">
    <h2 id="et-heading">檢索非英語系國家之英語交換大學（符合 <span id="et-visible-count">{len(items)}</span> 所，預覽前 {len(shown)} 所）</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-sm uw-btn-outline" href="/data/english-taught-partners">重設</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製網址</button>
    </div>
  </div>
  <div class="uw-kpi-grid">
    <div class="uw-kpi-box uw-kpi-highlight"><span class="uw-kpi-label">收錄非英語系海外大學</span><strong class="uw-kpi-value">{ds['total_institutions']} 所</strong><span class="uw-kpi-tag">具備英語檢定門檻或英語組紀錄</span></div>
    <div class="uw-kpi-box"><span class="uw-kpi-label">涵蓋歐亞非英語系國家</span><strong class="uw-kpi-value">{ds['country_count']} 國</strong><span class="uw-kpi-tag">日・韓・德・法・荷・捷・北歐等</span></div>
  </div>

  <form method="get" action="/data/english-taught-partners" class="uw-form-grid" data-data-filter="eng-taught">
    <label class="uw-field"><span>目的地國家</span><select name="country" id="et-country">{c_opts}</select></label>
    <label class="uw-field"><span>英語門檻快篩</span><select name="tier" id="et-tier">{tier_opts}</select></label>
    <label class="uw-field"><span>關鍵字搜尋</span><input type="search" name="q" id="et-q" value="{escape(q_clean)}" placeholder="早稻田、慕尼黑、阿姆斯特丹…"></label>
    <div class="uw-form-actions"><button type="submit" class="uw-btn uw-btn-primary">套用篩選</button></div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="歐陸與日韓英語授課交換名校資料庫表">
    <table class="uw-data-table" id="et-data-table">
      <caption class="uw-sr-only">非英語系國家明確列載英語門檻或英語授課方案之海外交換大學清單</caption>
      <thead>
        <tr><th scope="col">海外合作大學</th><th scope="col">列載台灣母校數</th><th scope="col">明確列載英語門檻</th><th scope="col">台灣締約母校直達</th><th scope="col">跨校頁與來源</th></tr>
      </thead>
      <tbody id="et-tbody">{tbody_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  {render_faq_section(FAQS_ENG_TAUGHT)}
  {render_core_summary_and_citation_box(settings.origin, spec, checked_date=ds['latest_checked'])}
  {render_compliance_strip()}
</div>"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data"), (spec.short_title, spec.path)],
            FAQS_ENG_TAUGHT,
            variables=("非英語系海外大學", "列載英語檢定門檻", "締約台灣母校數"),
            keywords=("歐洲全英文授課交換", "日本全英授課交換", "韓國英文交換學校", "免二外交換學生"),
            date_modified=ds["latest_checked"],
        )

    # 4. /data/scholarships-taiwan
    @router.api_route("/data/scholarships-taiwan", methods=["GET", "HEAD"])
    def data_scholarships_taiwan(
        category: str = Query(default="all"),
        q: str = Query(default=""),
    ) -> HTMLResponse:
        spec = WAVE3_DATA_SPECS["/data/scholarships-taiwan"]
        ds = get_schol_data()
        nat_rows = list(ds["national_and_foreign"])
        if category in ("moe", "foreign"):
            nat_rows = [r for r in nat_rows if r["category"] == category]
        else:
            category = "all"

        q_clean = q.strip()
        sch_rows = list(ds["school_grants"])
        if q_clean:
            ql = q_clean.casefold()
            sch_rows = [
                s for s in sch_rows
                if ql in s["school_name"].casefold() or ql in s["short_name"].casefold() or ql in s["summary"].casefold()
            ]

        cat_opts = "".join(
            f'<option value="{k}"{" selected" if category == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("all", "全部全國性與外國政府獎助計畫"),
                ("moe", "教育部學海系列計畫"),
                ("foreign", "外國政府／駐台機構／歐盟獎助"),
            )
        )

        nat_html = "".join(
            f"<tr data-st-cat='{escape(r['category'])}'>"
            f"<th scope='row'><strong>{escape(r['name'])}</strong><div class='uw-cell-sub'>{escape(r['sponsor'])}</div></th>"
            f"<td><span class='uw-inline-badge'>{escape(r['category_label'])}</span></td>"
            f"<td>{escape(r['eligibility'])}</td>"
            f"<td>{escape(r['funding'])}</td>"
            f"<td>{official_link(r['official_url'], r['official_label'])}</td></tr>"
            for r in nat_rows
        )

        school_html = "".join(
            f"<tr data-st-school='{escape(s['school_name'])} {escape(s['short_name'])}'>"
            f"<th scope='row'><a href='{escape(s['school_url'])}'>{escape(s['school_name'])}</a><span class='uw-inline-badge'>{escape(s['sector'])}</span></th>"
            f"<td>{escape(s['summary'])}</td>"
            f"<td>{official_link(s['official_url'], s['short_name'] + '國際處')} · <a href='/tools/scholarship-finder?home={escape(s['school_id'])}'>資格快篩</a></td></tr>"
            for s in sch_rows
        )
        if not school_html:
            school_html = "<tr><td colspan='3'>找不到符合關鍵字的台灣大學，請重設搜尋條件。</td></tr>"

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="st-heading">
  <div class="uw-tool-header">
    <h2 id="st-heading">全國性與外國政府機構交換獎學金一覽表</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-sm uw-btn-primary" href="/tools/scholarship-finder">開啟個人資格快篩器</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製網址</button>
    </div>
  </div>
  <form method="get" action="/data/scholarships-taiwan" class="uw-form-grid" data-data-filter="schol-taiwan">
    <label class="uw-field"><span>獎助計畫類別</span><select name="category" id="st-cat">{cat_opts}</select></label>
    <label class="uw-field"><span>搜尋下方 71 校校內獎助</span><input type="search" name="q" id="st-q" value="{escape(q_clean)}" placeholder="臺大、政大、清大、輔大…"></label>
    <div class="uw-form-actions uw-nojs-only"><button type="submit" class="uw-btn uw-btn-primary">套用篩選</button></div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="全國與外國政府交換獎學金總表">
    <table class="uw-data-table" id="st-nat-table">
      <caption class="uw-sr-only">台灣交換學生可申請之教育部與外國政府機構獎學金總表</caption>
      <thead>
        <tr><th scope="col">獎學金計畫與主辦單位</th><th scope="col">類別</th><th scope="col">核心資格條件</th><th scope="col">補助內容與兼領規定</th><th scope="col">官方網站</th></tr>
      </thead>
      <tbody id="st-nat-tbody">{nat_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer" open>
    <summary>全台 71 所大學校內交換獎助資訊與國際處入口總表（顯示 <span id="st-school-count">{len(sch_rows)}</span> 校）</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="全台 71 所大學校內交換獎助入口總表">
        <table class="uw-data-table" id="st-school-table">
          <caption class="uw-sr-only">全台 71 所大學校內出國交換生獎助摘要與官方入口表</caption>
          <thead>
            <tr><th scope="col">台灣母校</th><th scope="col">資料庫收錄校內交換獎助規定摘要</th><th scope="col">國際處與快篩連結</th></tr>
          </thead>
          <tbody id="st-school-tbody">{school_html}</tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_SCHOLARSHIPS_TW)}
  {render_core_summary_and_citation_box(settings.origin, spec, checked_date=CATALOG_LAST_CHECKED_AT)}
  {render_compliance_strip()}
</div>"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data"), (spec.short_title, spec.path)],
            FAQS_SCHOLARSHIPS_TW,
            variables=("獎學金名稱", "主辦機構", "國籍與學籍條件", "補助項目與兼領限制", "71校國際處連結"),
            keywords=("交換學生獎學金總表", "學海飛颺金額", "學海惜珠資格", "日本JASSO獎學金", "出國交換補助"),
            date_modified=CATALOG_LAST_CHECKED_AT,
        )
