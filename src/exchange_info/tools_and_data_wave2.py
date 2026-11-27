"""Wave 2 public SEO tools (/tools/...) and database-driven annual data pages (/data/...).

Implements:
1. /tools/partner-compare              — 海外姊妹校並排 PK 比較器 (+ .json live endpoint)
2. /tools/military-service-exit-checker — 台灣男生「役男出境交換」時程與文件檢查器 (+ .ics download)
3. /tools/scholarship-finder           — 獎學金與補助資格快速篩選器
4. /data/language-requirements         — 交換語言門檻大調查（各分數段可申請校數）
5. /data/top-partner-universities      — 全台最多台灣大學簽約的海外名校 Top 50

Strictly adheres to zero-fabrication, SSR-first + progressive JS enhancement, CSP safety,
40-60 character core conclusions, JSON-LD structured data, and low-noise UI design.
"""
from __future__ import annotations

import json
import threading
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime, timedelta, timezone
from html import escape
from time import monotonic
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from .cross_school_partners import (
    COUNTRY_DEFAULT_CURRENCY_HINT,
    COUNTRY_SLUGS,
    build_cross_school_entity_index,
    resolve_partner_cross_school_path,
)
from .destination_tips import canonical_country
from .models import CatalogueSourceStatus, PartnerUniversity
from .school_identity import school_identity_key
from .seo_guides import country_slug as destination_country_slug
from .tools_and_data_core import (
    BUDGET_COUNTRY_TEMPLATES,
    CEFR_RANK,
    JLPT_LEVEL_INFO,
    MANDATORY_DISCLAIMER,
    TAIPEI_TZ,
    PageMetaSpec,
    _ics_escape,
    calculate_exchange_budget,
    dataset_schema,
    extract_partner_language_thresholds,
    faq_page_schema,
    partner_group_id,
    render_compliance_strip,
    render_core_summary_and_citation_box,
    render_faq_section,
    safe_https_or_http_url,
    web_application_schema,
)
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university
from .verified_window_deadlines import CATALOG_LAST_CHECKED_AT


WAVE2_SPECS: dict[str, PageMetaSpec] = {
    "/tools/partner-compare": PageMetaSpec(
        path="/tools/partner-compare",
        slug="partner-compare",
        kind="tool",
        short_title="姊妹校並排 PK 比較器",
        title="海外姊妹校並排 PK 比較器｜語言門檻、名額狀態、學期與生活費對照｜UniWay",
        h1="海外姊妹校並排 PK 比較器",
        description="免登入挑選 2 至 3 所海外交換合作校並排比對語言檢定門檻、當期名額狀態、可申請學制、學期制與當地生活費參考，支援一鍵分享網址與下載比較圖卡。",
        core_conclusion="免登入並排比較二至三所海外姊妹校之語言門檻、名額狀態、學期與生活費參考，實際資格與名額以各校最新官方公告為準。",
    ),
    "/tools/military-service-exit-checker": PageMetaSpec(
        path="/tools/military-service-exit-checker",
        slug="military-service-exit-checker",
        kind="tool",
        short_title="役男出境交換檢查器",
        title="台灣男生役男出境交換時程與文件檢查器｜專案核准 vs 短期出境對照｜UniWay",
        h1="役男出境交換時程與文件檢查器",
        description="依出境與返國日期自動核算停留天數，釐清 4 個月短期出境與學校推薦出國交換專案核准差異，排定校內送件倒推節點並支援下載 .ics 行事曆。",
        core_conclusion="依出返國日期區分四個月內短期出境與學校推薦交換專案核准程序及必備文件，實際規定以內政部役政司與各校最新官方公告為準。",
    ),
    "/tools/scholarship-finder": PageMetaSpec(
        path="/tools/scholarship-finder",
        slug="scholarship-finder",
        kind="tool",
        short_title="交換獎學金快速篩選器",
        title="交換學生獎學金與補助資格篩選器｜學海飛颺、學海惜珠、JASSO 與各國補助｜UniWay",
        h1="交換獎學金與補助資格篩選器",
        description="依學籍國籍身分、交換目的地與研修期程快速篩選教育部學海飛颺、學海惜珠、日本 JASSO、交流協會、韓國 GKS、歐盟 Erasmus+ 與母校校內補助管道。",
        core_conclusion="依學籍身分、交換地區與期程快速篩選教育部學海系列、外國政府與校內補助方案，實際資格與金額以各校最新官方公告為準。",
    ),
    "/data/language-requirements": PageMetaSpec(
        path="/data/language-requirements",
        slug="language-requirements",
        kind="data",
        short_title="交換語言門檻大調查",
        title="台灣交換學生語言門檻大調查｜多益・雅思・托福・日檢各分數段可申請校數｜UniWay",
        h1="交換語言門檻各分數段統計",
        description="讀取全台 71 所大學海外合作校真實紀錄，統計多益 750/800/860、雅思 6.0/6.5、托福 79/88 與日檢 N2/N1 各分數段明確列載可達標之合作校規模與國家分布。",
        core_conclusion="統計全台 71 所大學海外合作校於多益、雅思、托福、CEFR 與日檢各分數段列載校數，實際資格以各校最新官方公告為準。",
    ),
    "/data/top-partner-universities": PageMetaSpec(
        path="/data/top-partner-universities",
        slug="top-partner-universities",
        kind="data",
        short_title="全台締約海外名校 Top 50",
        title="全台最多台灣大學簽約的海外名校 Top 50｜跨校合作排行與母校連結｜UniWay",
        h1="全台締約最多海外姊妹校 Top 50",
        description="依全台 71 所公私立大學公開交換合作名單自動歸併統計，揭曉最多台灣大學締約之海外姊妹校前 50 名排行、國家分布與各台灣母校直達連結。",
        core_conclusion="依全台 71 所大學公開名單統計締約校數最多之海外大學 Top 50 排行，實際資格與名額以各校最新官方公告為準。",
    ),
}

WAVE2_PATHS: tuple[str, ...] = tuple(WAVE2_SPECS.keys())

for _w2_path, _w2_spec in WAVE2_SPECS.items():
    if not (40 <= len(_w2_spec.core_conclusion) <= 60):
        raise ValueError(f"{_w2_path} core_conclusion length {len(_w2_spec.core_conclusion)} must be 40..60")


# ---------------------------------------------------------------------------
# 1. Partner Side-by-Side PK Comparator (/tools/partner-compare)
# ---------------------------------------------------------------------------

def _country_budget_reference(country_zh: str) -> str:
    slug = COUNTRY_SLUGS.get(country_zh, "")
    if slug in BUDGET_COUNTRY_TEMPLATES:
        calc = calculate_exchange_budget(country_key=slug)
        return (
            f"約 {calc['currency']} {calc['monthly_foreign']:,.0f}／月"
            f"（折合 NT$ {calc['base_monthly_twd']:,}／月，依規劃模板估算）"
        )
    if country_zh in COUNTRY_DEFAULT_CURRENCY_HINT:
        return COUNTRY_DEFAULT_CURRENCY_HINT[country_zh]
    return "尚未建立國家參考模板，請查閱接待校 Fact Sheet"


def _summarize_partner_for_compare(
    home: UniversityProfile,
    pid: str,
    rows: Sequence[PartnerUniversity],
    availability_labels: Mapping[str, str],
) -> dict[str, Any]:
    primary = rows[0]
    c_zh = canonical_country(primary.country) or (primary.country or "國家待確認").strip()
    c_slug = COUNTRY_SLUGS.get(c_zh, "")
    parsed_lang = extract_partner_language_thresholds(rows)

    lang_badges: list[str] = []
    if parsed_lang["ielts_min"] is not None:
        lang_badges.append(f"IELTS {parsed_lang['ielts_min']:g}")
    if parsed_lang["toefl_min"] is not None:
        lang_badges.append(f"TOEFL iBT {parsed_lang['toefl_min']:g}")
    if parsed_lang["toeic_min"] is not None:
        lang_badges.append(f"TOEIC {parsed_lang['toeic_min']:g}")
    if parsed_lang["cefr_min"] is not None:
        lang_badges.append(f"CEFR {parsed_lang['cefr_min']}")
    if parsed_lang["jlpt_min"] is not None:
        lang_badges.append(f"JLPT {parsed_lang['jlpt_min']}")

    statuses = "、".join(
        dict.fromkeys(availability_labels.get(r.availability_status, r.availability_status) for r in rows)
    )
    quotas = "；".join(dict.fromkeys(r.quota.strip() for r in rows if r.quota and r.quota.strip())) or "未單獨列載（請查當期簡章）"
    degrees = "；".join(dict.fromkeys(r.degree_levels.strip() for r in rows if r.degree_levels and r.degree_levels.strip())) or "依母校與接待校簡章確認"
    periods = "；".join(
        dict.fromkeys(
            val.strip()
            for r in rows
            for val in (r.study_period, r.semester_dates)
            if val and val.strip()
        )
    ) or "一學期或一學年（依當期公告）"
    tuition = next((r.tuition_info.strip() for r in rows if r.tuition_info and r.tuition_info.strip()), "") or "依雙邊交換協議與當期簡章確認"
    housing = next((r.housing_info.strip() for r in rows if r.housing_info and r.housing_info.strip()), "") or "依接待校宿舍公告另行申請"
    if len(tuition) > 95:
        tuition = tuition[:94].rstrip() + "…"
    if len(housing) > 95:
        housing = housing[:94].rstrip() + "…"

    return {
        "pid": pid,
        "school_name": primary.school_name,
        "country": c_zh,
        "country_slug": c_slug if c_slug in BUDGET_COUNTRY_TEMPLATES else "japan",
        "destination_path": f"/destinations/{c_slug}" if destination_country_slug(c_zh) else "",
        "availability": statuses,
        "quota": quotas,
        "language_badges": " ／ ".join(lang_badges) if lang_badges else "依簡章條文確認",
        "language_snippet": parsed_lang["snippet"],
        "degree_levels": degrees,
        "study_period": periods[:110] + ("…" if len(periods) > 110 else ""),
        "tuition_info": tuition,
        "housing_info": housing,
        "budget_ref": _country_budget_reference(c_zh),
        "partner_url": f"/schools/{home.id}/partners/{pid}",
        "cross_school_url": resolve_partner_cross_school_path(primary),
        "source_url": safe_https_or_http_url(primary.source_url) or safe_https_or_http_url(home.official_url),
        "website": safe_https_or_http_url(primary.website),
    }


def build_partner_comparison(
    home_id: str,
    partners: Sequence[PartnerUniversity],
    availability_labels: Mapping[str, str],
    *,
    p1: str | None = None,
    p2: str | None = None,
    p3: str | None = None,
) -> dict[str, Any]:
    home = resolve_university(home_id) or resolve_university("ntu") or SUPPORTED_UNIVERSITIES[0]
    grouped: dict[str, list[PartnerUniversity]] = {}
    for p in partners:
        grouped.setdefault(partner_group_id(p), []).append(p)

    # Sort options cleanly: open listed first, then by country & school_name
    ordered_pids = sorted(
        grouped.keys(),
        key=lambda k: (
            0 if any(r.availability_status == "open" for r in grouped[k]) else 1,
            canonical_country(grouped[k][0].country) or grouped[k][0].country or "",
            grouped[k][0].school_name,
        ),
    )

    options = [
        {
            "pid": pid,
            "school_name": grouped[pid][0].school_name,
            "country": canonical_country(grouped[pid][0].country) or grouped[pid][0].country or "海外",
            "label": f"[{canonical_country(grouped[pid][0].country) or grouped[pid][0].country or '海外'}] {grouped[pid][0].school_name}",
        }
        for pid in ordered_pids
    ]

    # Pick clean defaults from distinct countries when p1/p2 are omitted or invalid
    default_picks: list[str] = []
    seen_countries: set[str] = set()
    for opt in options:
        if opt["country"] not in seen_countries:
            default_picks.append(opt["pid"])
            seen_countries.add(opt["country"])
        if len(default_picks) >= 3:
            break
    for opt in options:
        if len(default_picks) >= 3:
            break
        if opt["pid"] not in default_picks:
            default_picks.append(opt["pid"])

    sel1 = p1 if (p1 and p1 in grouped) else (default_picks[0] if len(default_picks) >= 1 else "")
    sel2 = p2 if (p2 and p2 in grouped and p2 != sel1) else next((x for x in default_picks if x != sel1), sel1)
    sel3 = p3 if (p3 and p3 in grouped and p3 not in {sel1, sel2}) else ""

    selected_ids = [pid for pid in (sel1, sel2, sel3) if pid and pid in grouped]
    selected_cards = [
        _summarize_partner_for_compare(home, pid, grouped[pid], availability_labels)
        for pid in selected_ids
    ]

    return {
        "home_id": home.id,
        "home_name": home.school_name,
        "home_short_name": home.short_name,
        "home_official_url": safe_https_or_http_url(home.official_url),
        "total_options": len(options),
        "options": options,
        "p1": sel1,
        "p2": sel2,
        "p3": sel3,
        "selected": selected_cards,
    }


# ---------------------------------------------------------------------------
# 2. Military Service Exit Checker (/tools/military-service-exit-checker)
# ---------------------------------------------------------------------------

MILITARY_STATUS_OPTIONS: dict[str, str] = {
    "draft_male": "尚未服役之在學役男（年滿 19 歲當年 1/1 至 36 歲當年 12/31）",
    "turning_19": "出國或交換期間將跨入「年滿 19 歲當年 1 月 1 日」之男子",
    "pre_19": "全程均未滿 19 歲之年男子（尚未屆役齡）",
    "exempt_or_done": "已服役畢／免役／替代役備役／非役男身分",
}


def evaluate_military_service_exit(
    *,
    status: str = "draft_male",
    depart_str: str | None = None,
    return_str: str | None = None,
    school_id: str = "ntu",
) -> dict[str, Any]:
    if status not in MILITARY_STATUS_OPTIONS:
        status = "draft_male"
    uni = resolve_university(school_id) or SUPPORTED_UNIVERSITIES[0]

    default_depart = date(2027, 8, 25)
    default_return = date(2028, 1, 20)
    try:
        depart_dt = datetime.strptime((depart_str or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        depart_dt = default_depart
    try:
        return_dt = datetime.strptime((return_str or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return_dt = default_return

    if return_dt <= depart_dt:
        return_dt = depart_dt + timedelta(days=148)

    stay_days = (return_dt - depart_dt).days
    stay_months = round(stay_days / 30.44, 1)
    exceeds_short_exit = stay_days > 120  # 4-month statutory cap for online short-term exit

    if status == "exempt_or_done":
        route_badge = "一般護照與簽證出境（免辦在學役男專案核准）"
        route_summary = (
            "已完成兵役義務、免役或無役男身分者，無須辦理在學役男出國研修核准；"
            "若屬後備軍人或替代役備役役男出境超過規定月數，仍請依國防部後備指揮部或役政司規定確認備查事項。"
        )
        warning_level = "ok"
    elif status == "pre_19":
        route_badge = "尚未屆役齡（確認返國日未跨入 19 歲當年 1/1）"
        route_summary = (
            "依《兵役法》規定，男子年滿 19 歲之年 1 月 1 日起具役男身分。若出境與返國全程均在屆滿 19 歲之年前，"
            "無須申請役男出境核准；一旦交換返國日跨入 19 歲當年 1 月 1 日以後，返國或再出境即受役男出境規範。"
        )
        warning_level = "ok"
    elif status == "turning_19":
        route_badge = "跨入役齡年度提醒：須辦理學校推薦出國研修專案核准"
        route_summary = (
            "自年滿 19 歲當年 1 月 1 日起即具法定役男身分。若於學期中跨入役齡年度或寒暑假需返台再出境繼續交換，"
            "務必由國內就讀大學依《役男出境處理辦法》辦理推薦出國研究進修專案核准，切勿僅憑未滿 19 歲時出境紀錄往返。"
        )
        warning_level = "warn"
    else:
        if exceeds_short_exit:
            route_badge = "必辦「學校推薦出國交換／研修專案核准」（不可用短期出境替代）"
            route_summary = (
                f"預估境外停留 {stay_days} 天（約 {stay_months} 個月），已超過內政部役政司「線上短期出境」最長 4 個月上限。"
                "必須取得國外姊妹校正式入學許可（LoA）後，提前交由母校國際處與學務處兵役承辦造冊函報縣市政府核准出境。"
            )
            warning_level = "alert"
        else:
            route_badge = "停留 4 個月內：仍建議優先向母校確認「推薦出國研修專案造冊」"
            route_summary = (
                f"預估境外停留 {stay_days} 天（約 {stay_months} 個月）。雖未逾短期出境 4 個月上限，"
                "但正式校際交換生為保障海外就學期間緩徵與延期返國彈性，多數大學仍規定須辦理學校推薦出國研修公文核准；請先洽母校兵役承辦確認。"
            )
            warning_level = "warn"

    timeline = [
        {
            "id": "loa-check",
            "offset": "出發前 60 天",
            "date": (depart_dt - timedelta(days=60)).isoformat(),
            "title": "取得海外接待校正式入學許可（LoA）並確認姓名與研修起迄日",
            "detail": "核對入學許可上之英文姓名與護照一致，並確認母校或戶籍地縣市政府是否要求附中文譯本或重點摘譯。",
        },
        {
            "id": "campus-submit",
            "offset": "出發前 45 天",
            "date": (depart_dt - timedelta(days=45)).isoformat(),
            "title": f"向 {uni.short_name} 國際處與學務處生輔組（兵役承辦）遞交校內申請文件",
            "detail": "國內大學辦理推薦役男出國研修公文會辦與函報戶籍地縣市政府常需 3 至 6 週作業期，多校明訂須於出國前 30–45 日送件。",
        },
        {
            "id": "gov-approval",
            "offset": "出發前 21 天",
            "date": (depart_dt - timedelta(days=21)).isoformat(),
            "title": "確認縣市政府核准公文文號與內政部役男出境核准通知單",
            "detail": "收到學校轉發之縣市政府核准函後，依指示至內政部役政司系統查詢並列印役男出境核准證明，核對核准出境有效期限。",
        },
        {
            "id": "pre-flight",
            "offset": "出發前 7 天",
            "date": (depart_dt - timedelta(days=7)).isoformat(),
            "title": "備妥有效護照（效期逾 6 個月）、簽證、入學許可與役男出境核准單備查",
            "detail": "若交換期間寒暑假需短暫返台並再次出境返回姊妹校，須事先向母校兵役承辦確認再出境申請程序。",
        },
        {
            "id": "depart-day",
            "offset": "預計出境日",
            "date": depart_dt.isoformat(),
            "title": "依核准期限出境赴海外姊妹校報到",
            "detail": "切勿在專案核准公文下來前先行使用 4 個月觀光短期出境離境，以免無法在境外直接轉換為研修期限。",
        },
        {
            "id": "return-report",
            "offset": "預計返國日",
            "date": return_dt.isoformat(),
            "title": "於核准期限屆滿前返國，並向母校辦理返國報到與學分採認",
            "detail": "依《役男出境處理辦法》，推薦出國研修每次核准期間原則最長不得逾 1 年；務必於核准期限內返國以免受催告及限制出境。",
        },
    ]

    ics_query = urlencode({
        "status": status,
        "depart": depart_dt.isoformat(),
        "return_date": return_dt.isoformat(),
        "school": uni.id,
    })

    return {
        "status": status,
        "status_label": MILITARY_STATUS_OPTIONS[status],
        "depart_date": depart_dt.isoformat(),
        "return_date": return_dt.isoformat(),
        "stay_days": stay_days,
        "stay_months": stay_months,
        "exceeds_short_exit": exceeds_short_exit,
        "warning_level": warning_level,
        "route_badge": route_badge,
        "route_summary": route_summary,
        "school_id": uni.id,
        "school_name": uni.school_name,
        "short_name": uni.short_name,
        "school_official_url": safe_https_or_http_url(uni.official_url),
        "timeline": timeline,
        "ics_url": f"/tools/military-service-exit-checker.ics?{ics_query}",
    }


def build_military_exit_ics(
    *,
    status: str = "draft_male",
    depart_str: str | None = None,
    return_str: str | None = None,
    school_id: str = "ntu",
) -> tuple[str, str]:
    res = evaluate_military_service_exit(
        status=status,
        depart_str=depart_str,
        return_str=return_str,
        school_id=school_id,
    )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cal_name = f"UniWay 役男出境交換檢核時程（{res['short_name']}）"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//UniWay Taiwan//Military Service Exit Checker//ZH-TW",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_ics_escape(cal_name)}",
        "X-WR-TIMEZONE:Asia/Taipei",
    ]
    authority_url = "https://www.ris.gov.tw/military-onlineDeparture/"
    for item in res["timeline"]:
        start = datetime.strptime(item["date"], "%Y-%m-%d").date()
        end = start + timedelta(days=1)
        uid = f"uniway-mil-{res['school_id']}-{item['id']}-{start.strftime('%Y%m%d')}@app.uniway-tw.com"
        summary = f"[役男出境交換] {item['title']}"
        desc = (
            f"{item['detail']}\n"
            f"判定摘要：{res['route_badge']}\n"
            f"役政司入口：{authority_url}\n"
            f"實際規定以內政部役政司與各校最新官方公告為準。"
        )
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{_ics_escape(uid)}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
            f"SUMMARY:{_ics_escape(summary)}",
            f"DESCRIPTION:{_ics_escape(desc)}",
            f"URL:{_ics_escape(authority_url)}",
            "BEGIN:VALARM",
            "TRIGGER:-P3D",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_ics_escape(summary)}",
            "END:VALARM",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    filename = f"uniway-military-exit-{res['depart_date']}.ics"
    return filename, "\r\n".join(lines) + "\r\n"


# ---------------------------------------------------------------------------
# 3. Scholarship & Grant Finder (/tools/scholarship-finder)
# ---------------------------------------------------------------------------

SCHOLARSHIP_REGIONS: dict[str, str] = {
    "all": "不限國家／地區",
    "japan": "日本",
    "south-korea": "韓國",
    "germany": "德國",
    "france": "法國",
    "europe_other": "歐洲其他國家（荷蘭、捷克、英國等）",
    "americas_oceania": "美加／紐澳",
    "asia_other": "新加坡與亞洲其他地區",
    "cn_hk_mo": "大陸地區及港澳",
}

SCHOLARSHIP_IDENTITIES: dict[str, str] = {
    "roc_general": "中華民國籍在學學生（一般生）",
    "roc_financial": "中華民國籍在學學生（具低收／中低收等法定證明）",
    "international_student": "在臺就讀之外籍學位生／僑生（無中華民國戶籍）",
    "in_service": "在職專班學生",
}

SCHOLARSHIP_DURATIONS: dict[str, str] = {
    "semester": "一學期交換（約 4–6 個月）",
    "year": "一學年交換（約 9–12 個月）",
}

OFFICIAL_SCHOLARSHIP_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "moe-feiyang",
        "name": "教育部「學海飛颺」選送優秀學生出國研修獎助學金",
        "sponsor": "教育部（由國內母校薦送申請）",
        "channel": "向就讀母校國際處提出校內甄選（不接受個人直接向教育部投件）",
        "regions": ("japan", "south-korea", "germany", "france", "europe_other", "americas_oceania", "asia_other"),
        "identities": ("roc_general", "roc_financial"),
        "durations": ("semester", "year"),
        "funding_note": "依教育部當年度核定母校配額與校內評選核給；依補助要點不得同時兼領我國政府其他出國補助。",
        "eligibility_note": "須具中華民國國籍且在臺灣地區設有戶籍之正式學籍在學生（不含國內及境外在職專班，亦不含赴大陸及港澳）。",
        "official_url": "https://www.studyabroad.moe.gov.tw/",
        "official_label": "教育部國內大專校院選送學生出國研修網站",
    },
    {
        "id": "moe-xizhu",
        "name": "教育部「學海惜珠」選送清寒優秀學生出國研修獎助學金",
        "sponsor": "教育部（由國內母校薦送申請）",
        "channel": "向就讀母校國際處提出申請並檢附法定經濟扶助證明",
        "regions": ("japan", "south-korea", "germany", "france", "europe_other", "americas_oceania", "asia_other"),
        "identities": ("roc_financial",),
        "durations": ("semester", "year"),
        "funding_note": "依教育部專案核定額度補助來回機票與國外生活費；不得同時兼領我國政府提供之其他出國補助。",
        "eligibility_note": "須具中華民國國籍且在臺設籍，並持有各直轄市、縣（市）主管機關認定之低收入戶、中低收入戶或相關法定扶助證明（不含在職專班及大陸港澳）。",
        "official_url": "https://www.studyabroad.moe.gov.tw/",
        "official_label": "教育部學海計畫官方網站",
    },
    {
        "id": "jasso",
        "name": "日本學生支援機構（JASSO）海外留學支援制度（協定接收）",
        "sponsor": "日本學生支援機構 JASSO",
        "channel": "由「日本接收姊妹校」向 JASSO 申請計畫並就錄取交換生進行校內推薦（學生無法自行向 JASSO 投件）",
        "regions": ("japan",),
        "identities": ("roc_general", "roc_financial", "international_student"),
        "durations": ("semester", "year"),
        "funding_note": "JASSO 制度頁列載月額 80,000 日圓；當期該日本姊妹校是否獲配名額與兼領上限，須由兩校承辦確認。",
        "eligibility_note": "赴日本協定大學短期交換，符合前學年成績換算門檻且其他獎學金合計未逾 JASSO 規定上限者。",
        "official_url": "https://www.jasso.go.jp/en/ryugaku/scholarship_j/ukeire.html",
        "official_label": "JASSO 協定接收短期留學支援制度頁",
    },
    {
        "id": "koryu-short",
        "name": "日本台灣交流協會「短期交換留學生獎學金」",
        "sponsor": "公益財團法人日本台灣交流協會",
        "channel": "依交流協會當年度簡章規定管道與推薦程序提出申請",
        "regions": ("japan",),
        "identities": ("roc_general", "roc_financial"),
        "durations": ("semester", "year"),
        "funding_note": "依當期簡章公告之月額生活費等項目核給；須留意不得與日本政府（含 JASSO）或其他指定獎學金重複兼領。",
        "eligibility_note": "具台灣大專校院在學學籍、獲准赴日本合作大學交換留學並符合簡章國籍與成績語檢規定者。",
        "official_url": "https://www.koryu.or.jp/tw/business/scholarship/",
        "official_label": "日本台灣交流協會獎學金公告頁",
    },
    {
        "id": "korea-gks",
        "name": "韓國政府 GKS 外國交換學生支援計畫（Global Korea Scholarship）",
        "sponsor": "韓國國立國際教育院（NIIED）",
        "channel": "由獲選參與當年度 GKS 計畫之「韓國接收姊妹校」推薦提名",
        "regions": ("south-korea",),
        "identities": ("roc_general", "roc_financial", "international_student"),
        "durations": ("semester", "year"),
        "funding_note": "依韓國政府當年度簡章提供每月生活津貼與來回機票補助上限；僅限獲 NIIED 核配名額之韓國大學可提名。",
        "eligibility_note": "獲韓國指定夥伴大學錄取之正式交換生，依成績、修課計畫與語檢表現由韓方大學擇優推薦。",
        "official_url": "https://www.studyinkorea.go.kr/",
        "official_label": "韓國政府 Study in Korea 官方網站",
    },
    {
        "id": "erasmus-icm",
        "name": "歐盟 Erasmus+ International Credit Mobility（ICM）交換獎助",
        "sponsor": "歐盟執委會 Erasmus+ 計畫",
        "channel": "限台灣母校與歐洲夥伴校當期簽有 Erasmus+ ICM 補助專案名額時，由兩校依協議提名",
        "regions": ("germany", "france", "europe_other"),
        "identities": ("roc_general", "roc_financial", "international_student"),
        "durations": ("semester",),
        "funding_note": "依歐盟國家生活費分級提供每月定額生活津貼與國際旅費補助；非所有歐洲姊妹校皆有當期 ICM 經費。",
        "eligibility_note": "錄取具當期 Erasmus+ ICM 專案配額之歐洲夥伴大學交換名額，並簽署 Learning Agreement 者。",
        "official_url": "https://erasmus-plus.ec.europa.eu/",
        "official_label": "歐盟 Erasmus+ 官方入口網站",
    },
    {
        "id": "daad-germany",
        "name": "德國學術交流總署（DAAD）及德國各邦基金會短期交流獎助",
        "sponsor": "德國 DAAD ／ 德國各邦基金會（如巴登符騰堡邦獎學金等）",
        "channel": "依子計畫向 DAAD 台北資訊中心線上投件，或由締約德方大學（如 BW-Stipendium）校內提名",
        "regions": ("germany",),
        "identities": ("roc_general", "roc_financial", "international_student"),
        "durations": ("semester", "year"),
        "funding_note": "依各子計畫當期核定月額核發；申請截止日通常早於出國前半年至一年，須提早查閱 DAAD 獎學金資料庫。",
        "eligibility_note": "赴德國公立或國家認可大學交換、修讀暑期高校課程或執行專題研究之在學學生（依各計畫學制限制）。",
        "official_url": "https://www.daad.org.tw/zh/find-funding/",
        "official_label": "DAAD 德國學術交流資訊中心（台北）",
    },
    {
        "id": "campus-france-caf",
        "name": "法國教育中心獎助資訊與法國 CAF 學生房屋補助制度",
        "sponsor": "法國在台協會 ／ 法國家庭津貼局（CAF）",
        "channel": "獎助金依法國在台協會公告申請；CAF 房補須持合格長期學生簽證入境法國並簽署正式租約後線上申辦",
        "regions": ("france",),
        "identities": ("roc_general", "roc_financial", "international_student"),
        "durations": ("semester", "year"),
        "funding_note": "CAF 屬法國當地居住社會補助而非行前獎學金，審核與撥款常需數月且須開立當地帳戶，行前自備款不宜預先扣除。",
        "eligibility_note": "赴法國高等教育機構交換並持有可辦理居留確認（VLS-TS）之簽證與合規住宿契約者（短期免簽或特定簽證種類不適用）。",
        "official_url": "https://www.taiwan.campusfrance.org/",
        "official_label": "Campus France Taiwan 法國教育中心",
    },
    {
        "id": "home-university-grant",
        "name": "台灣母校校內出國交換生獎助學金／國際交流勵學金",
        "sponsor": "國內就讀大學（校務基金或校友捐助專款）",
        "channel": "於母校校內交換甄選同時或錄取後，依國際處公告時程提出申請",
        "regions": ("japan", "south-korea", "germany", "france", "europe_other", "americas_oceania", "asia_other", "cn_hk_mo"),
        "identities": ("roc_general", "roc_financial", "international_student", "in_service"),
        "durations": ("semester", "year"),
        "funding_note": "各校依交換地區遠近、GPA／班排名與語檢成績分級核給定額或月補助；須查閱母校辦法確認可否與學海飛颺兼領。",
        "eligibility_note": "通過母校校級（部分學校含院系級）交換甄選並維持在學註冊之學生；外籍生、在職專班及赴陸港澳適用與否依各校自訂辦法為準。",
        "official_url": "",
        "official_label": "母校國際處官方網站",
    },
)


def filter_scholarships(
    *,
    home_id: str = "ntu",
    region: str = "all",
    identity: str = "roc_general",
    duration: str = "semester",
) -> dict[str, Any]:
    uni = resolve_university(home_id) or SUPPORTED_UNIVERSITIES[0]
    if region not in SCHOLARSHIP_REGIONS:
        region = "all"
    if identity not in SCHOLARSHIP_IDENTITIES:
        identity = "roc_general"
    if duration not in SCHOLARSHIP_DURATIONS:
        duration = "semester"

    matched: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for item in OFFICIAL_SCHOLARSHIP_CATALOG:
        entry = dict(item)
        if entry["id"] == "home-university-grant":
            entry["name"] = f"{uni.short_name}校內出國交換獎助學金／國際交流補助"
            entry["sponsor"] = f"{uni.school_name}（國際處／校內自籌獎助）"
            entry["official_url"] = safe_https_or_http_url(uni.official_url) or "https://www.studyabroad.moe.gov.tw/"
            entry["official_label"] = f"{uni.short_name}國際處官方網站"

        reasons: list[str] = []
        if region != "all" and region not in entry["regions"]:
            reasons.append(f"不適用「{SCHOLARSHIP_REGIONS[region]}」地區")
        if identity not in entry["identities"]:
            reasons.append(f"不適用「{SCHOLARSHIP_IDENTITIES[identity]}」身分")
        if duration not in entry["durations"]:
            reasons.append(f"不適用「{SCHOLARSHIP_DURATIONS[duration]}」期程")

        if not reasons:
            matched.append(entry)
        else:
            entry["exclude_reason"] = "；".join(reasons)
            excluded.append(entry)

    return {
        "home_id": uni.id,
        "home_name": uni.school_name,
        "home_short_name": uni.short_name,
        "home_official_url": safe_https_or_http_url(uni.official_url),
        "region": region,
        "region_label": SCHOLARSHIP_REGIONS[region],
        "identity": identity,
        "identity_label": SCHOLARSHIP_IDENTITIES[identity],
        "duration": duration,
        "duration_label": SCHOLARSHIP_DURATIONS[duration],
        "matched": matched,
        "excluded": excluded,
    }


# ---------------------------------------------------------------------------
# 4. Language Requirements Benchmark Survey (/data/language-requirements)
# ---------------------------------------------------------------------------

LANGUAGE_SURVEY_TIERS: tuple[dict[str, Any], ...] = (
    {"id": "toeic-550", "test": "toeic", "test_group": "TOEIC 多益", "label": "TOEIC 550 分", "score_param": "550", "threshold": 550.0, "note": "校內初審或部分亞洲合作校基礎門檻"},
    {"id": "toeic-750", "test": "toeic", "test_group": "TOEIC 多益", "label": "TOEIC 750 分", "score_param": "750", "threshold": 750.0, "note": "常見校內英語組報名與亞洲英語學程門檻"},
    {"id": "toeic-800", "test": "toeic", "test_group": "TOEIC 多益", "label": "TOEIC 800 分", "score_param": "800", "threshold": 800.0, "note": "約對應 CEFR B2 初階，涵蓋多數採計多益合作校"},
    {"id": "toeic-860", "test": "toeic", "test_group": "TOEIC 多益", "label": "TOEIC 860 分（金色證書）", "score_param": "860", "threshold": 860.0, "note": "多益金色證書門檻，涵蓋絕大多數接受多益之學校"},
    {"id": "ielts-5.5", "test": "ielts", "test_group": "IELTS 雅思", "label": "IELTS 5.5", "score_param": "5.5", "threshold": 5.5, "note": "部分歐陸與亞洲英語授課交換方案基礎門檻"},
    {"id": "ielts-6.0", "test": "ielts", "test_group": "IELTS 雅思", "label": "IELTS 6.0", "score_param": "6.0", "threshold": 6.0, "note": "歐陸 Erasmus 夥伴校與日韓英語學程主流門檻"},
    {"id": "ielts-6.5", "test": "ielts", "test_group": "IELTS 雅思", "label": "IELTS 6.5", "score_param": "6.5", "threshold": 6.5, "note": "英美加澳與歐洲商管學院最常見標準門檻"},
    {"id": "ielts-7.0", "test": "ielts", "test_group": "IELTS 雅思", "label": "IELTS 7.0", "score_param": "7.0", "threshold": 7.0, "note": "頂尖綜合大學人文社科、法學與傳播學院高門檻"},
    {"id": "toefl-72", "test": "toefl", "test_group": "TOEFL iBT", "label": "TOEFL iBT 72 分", "score_param": "72", "threshold": 72.0, "note": "對應 CEFR B2 基礎門檻，歐陸與亞洲學程常見"},
    {"id": "toefl-79", "test": "toefl", "test_group": "TOEFL iBT", "label": "TOEFL iBT 79–80 分", "score_param": "80", "threshold": 80.0, "note": "北美州立大學與歐亞英語授課主流門檻（79 或 80 分）"},
    {"id": "toefl-88", "test": "toefl", "test_group": "TOEFL iBT", "label": "TOEFL iBT 88–90 分", "score_param": "90", "threshold": 90.0, "note": "歐美名校中堅門檻（涵蓋要求 88 至 90 分校系）"},
    {"id": "toefl-100", "test": "toefl", "test_group": "TOEFL iBT", "label": "TOEFL iBT 100 分", "score_param": "100", "threshold": 100.0, "note": "英語系頂尖名校與高競爭商管法政院系門檻"},
    {"id": "cefr-b1", "test": "cefr", "test_group": "CEFR 分級", "label": "CEFR B1", "score_param": "B1", "threshold": float(CEFR_RANK["B1"]), "note": "部分歐洲夥伴校基礎交換語言要求"},
    {"id": "cefr-b2", "test": "cefr", "test_group": "CEFR 分級", "label": "CEFR B2", "score_param": "B2", "threshold": float(CEFR_RANK["B2"]), "note": "歐洲大學交換簡章最普遍標示之能力等級"},
    {"id": "jlpt-n3", "test": "jlpt", "test_group": "JLPT 日檢", "label": "JLPT N3", "score_param": "N3", "threshold": float(JLPT_LEVEL_INFO["N3"]["rank"]), "note": "部分日本私立大學、地方大學或語學別科門檻"},
    {"id": "jlpt-n2", "test": "jlpt", "test_group": "JLPT 日檢", "label": "JLPT N2", "score_param": "N2", "threshold": float(JLPT_LEVEL_INFO["N2"]["rank"]), "note": "赴日一般學部交換最核心主流門檻"},
    {"id": "jlpt-n1", "test": "jlpt", "test_group": "JLPT 日檢", "label": "JLPT N1", "score_param": "N1", "threshold": float(JLPT_LEVEL_INFO["N1"]["rank"]), "note": "日本舊帝大、頂尖國立與人文社科研究科高門檻"},
)


def summarize_language_requirements_survey(
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    *,
    home_filter: str = "all",
) -> dict[str, Any]:
    target_uni = resolve_university(home_filter) if (home_filter and home_filter != "all") else None
    universities = (target_uni,) if target_uni else tuple(SUPPORTED_UNIVERSITIES)

    # Extract parsed thresholds once per (home, partner_group)
    records: list[dict[str, Any]] = []
    total_partner_pages = 0
    explicitly_parsed_pages = 0
    latest_dates: list[str] = []

    for u in universities:
        partners, source = catalogue_loader(u)
        grouped: dict[str, list[PartnerUniversity]] = {}
        for p in partners:
            grouped.setdefault(partner_group_id(p), []).append(p)
            if p.checked_at:
                latest_dates.append(p.checked_at.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d"))
        if source and source.last_success_at:
            latest_dates.append(source.last_success_at.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d"))

        total_partner_pages += len(grouped)
        for rows in grouped.values():
            primary = rows[0]
            parsed = extract_partner_language_thresholds(rows)
            if parsed["has_any_parsed"]:
                explicitly_parsed_pages += 1
            c_zh = canonical_country(primary.country) or (primary.country or "未標示").strip()
            records.append({
                "home_id": u.id,
                "foreign_key": f"{c_zh}|{school_identity_key(primary.school_name)}",
                "country": c_zh,
                "ielts_min": parsed["ielts_min"],
                "toefl_min": parsed["toefl_min"],
                "toeic_min": parsed["toeic_min"],
                "cefr_rank": CEFR_RANK[parsed["cefr_min"]] if parsed["cefr_min"] else None,
                "jlpt_rank": JLPT_LEVEL_INFO[parsed["jlpt_min"]]["rank"] if parsed["jlpt_min"] else None,
            })

    tier_rows: list[dict[str, Any]] = []
    for tier in LANGUAGE_SURVEY_TIERS:
        t_code = tier["test"]
        thresh = tier["threshold"]
        hit_pages = 0
        hit_insts: set[str] = set()
        hit_homes: set[str] = set()
        country_counter: Counter[str] = Counter()

        for rec in records:
            matched = False
            if t_code == "toeic" and rec["toeic_min"] is not None and rec["toeic_min"] <= thresh:
                matched = True
            elif t_code == "ielts" and rec["ielts_min"] is not None and rec["ielts_min"] <= thresh:
                matched = True
            elif t_code == "toefl" and rec["toefl_min"] is not None and rec["toefl_min"] <= thresh:
                matched = True
            elif t_code == "cefr" and rec["cefr_rank"] is not None and rec["cefr_rank"] <= thresh:
                matched = True
            elif t_code == "jlpt" and rec["jlpt_rank"] is not None and rec["jlpt_rank"] <= thresh:
                matched = True

            if matched:
                hit_pages += 1
                hit_insts.add(rec["foreign_key"])
                hit_homes.add(rec["home_id"])
                country_counter[rec["country"]] += 1

        top_countries_str = " · ".join(f"{c} {n}" for c, n in country_counter.most_common(3)) or "無單獨列載紀錄"
        tool_query = urlencode({
            "home": target_uni.id if target_uni else "nccu",
            "test": t_code,
            "score": tier["score_param"],
        })
        tier_rows.append({
            **tier,
            "partner_page_hits": hit_pages,
            "unique_institutions": len(hit_insts),
            "home_school_count": len(hit_homes),
            "top_countries": top_countries_str,
            "converter_url": f"/tools/language-score-converter?{tool_query}",
        })

    return {
        "selected_home_id": target_uni.id if target_uni else "all",
        "selected_home_label": f"{target_uni.school_name}（{target_uni.short_name}）" if target_uni else f"全台 {len(SUPPORTED_UNIVERSITIES)} 所大學總計",
        "scope_university_count": len(universities),
        "total_partner_pages": total_partner_pages,
        "explicitly_parsed_pages": explicitly_parsed_pages,
        "unparsed_pages": total_partner_pages - explicitly_parsed_pages,
        "latest_checked": max(latest_dates) if latest_dates else CATALOG_LAST_CHECKED_AT,
        "tiers": tier_rows,
    }


# ---------------------------------------------------------------------------
# 5. Top 50 Most-Contracted Foreign Partner Universities (/data/top-partner-universities)
# ---------------------------------------------------------------------------

def summarize_top_partner_universities(
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    *,
    country_filter: str = "all",
    q: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    entities, _ = build_cross_school_entity_index(catalogue_loader, require_complete=True)
    uni_by_id = {u.id: u for u in SUPPORTED_UNIVERSITIES}

    country_counter: Counter[tuple[str, str]] = Counter()
    for ent in entities.values():
        if len(ent.home_rows) >= 2:
            country_counter[(ent.country_slug, ent.country_name_zh)] += 1

    country_options = [
        {"slug": slug, "name": zh, "count": cnt}
        for (slug, zh), cnt in sorted(country_counter.items(), key=lambda x: (-x[1], x[0][0]))
    ]
    valid_country_slugs = {c["slug"] for c in country_options}
    active_country = country_filter if country_filter in valid_country_slugs else "all"
    q_clean = q.strip()
    q_low = q_clean.casefold()

    filtered = []
    latest_dates: list[str] = []
    for ent in entities.values():
        if active_country != "all" and ent.country_slug != active_country:
            continue
        if q_low:
            haystack = f"{ent.school_name_zh} {ent.school_name_en} {ent.country_name_zh}".casefold()
            if q_low not in haystack:
                continue
        filtered.append(ent)

    # Pure objective ranking by contracted Taiwanese university count (descending)
    filtered.sort(
        key=lambda ent: (
            -len(ent.home_rows),
            -sum(
                1 for rows in ent.home_rows.values()
                if any(r.availability_status == "open" for r in rows)
            ),
            ent.country_slug,
            ent.institution_slug,
        )
    )

    top_items: list[dict[str, Any]] = []
    for rank, ent in enumerate(filtered[:limit], 1):
        ordered_homes: list[dict[str, str]] = []
        open_count = 0
        sample_source_url: str | None = safe_https_or_http_url(ent.official_website)
        for u in SUPPORTED_UNIVERSITIES:
            rows = ent.home_rows.get(u.id)
            if not rows:
                continue
            if any(r.availability_status == "open" for r in rows):
                open_count += 1
            for r in rows:
                if r.checked_at:
                    latest_dates.append(r.checked_at.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d"))
                if not sample_source_url:
                    sample_source_url = safe_https_or_http_url(r.source_url)
            ordered_homes.append({
                "id": u.id,
                "short_name": u.short_name,
                "school_name": u.school_name,
                "partner_path": f"/schools/{u.id}/partners/{partner_group_id(rows[0])}",
                "official_url": safe_https_or_http_url(rows[0].source_url) or safe_https_or_http_url(u.official_url) or "",
            })

        top_items.append({
            "rank": rank,
            "display_title": ent.display_title,
            "school_name_zh": ent.school_name_zh,
            "school_name_en": ent.school_name_en,
            "country_slug": ent.country_slug,
            "country_name_zh": ent.country_name_zh,
            "destination_path": f"/destinations/{ent.country_slug}" if destination_country_slug(ent.country_name_zh) else f"/partners/{ent.country_slug}",
            "canonical_path": ent.canonical_path,
            "contracted_count": len(ordered_homes),
            "open_home_count": open_count,
            "homes": ordered_homes,
            "official_website": safe_https_or_http_url(ent.official_website),
            "primary_source_url": sample_source_url or (ordered_homes[0]["official_url"] if ordered_homes else ""),
        })

    return {
        "total_unique_entities": len(entities),
        "multi_school_entities": sum(1 for e in entities.values() if len(e.home_rows) >= 2),
        "matched_total": len(filtered),
        "active_country": active_country,
        "q": q_clean,
        "country_options": country_options,
        "items": top_items,
        "latest_checked": max(latest_dates) if latest_dates else CATALOG_LAST_CHECKED_AT,
    }


# ---------------------------------------------------------------------------
# Wave 2 FAQs (3-5 per page, strictly factual and compliant)
# ---------------------------------------------------------------------------

FAQS_PARTNER_COMPARE: tuple[tuple[str, str], ...] = (
    (
        "並排比較表裡的「名單列載」和「合作協議參考」有什麼差別？",
        "「名單列載」代表該校出現在母校交換名單中，仍須核對當期是否開放收件與實際名額；「合作協議參考」或「院系合作參考」則不代表當期校級甄選可直接填報，選填前請逐一開啟官方來源確認。",
    ),
    (
        "為什麼兩所同國家的姊妹校，語言檢定門檻寫法不一樣？",
        "每所海外接待校採計的檢定種類（如僅收 IELTS／TOEFL iBT，或額外接受 TOEIC、CEFR 證明）由雙邊協議與該校當年度 Fact Sheet 決定；未單獨列載者須回到母校簡章總則核對。",
    ),
    (
        "比較表中的「當地月生活費參考」包含機票與簽證費嗎？",
        "月生活費參考僅涵蓋當地住宿、伙食、市內交通與基本醫保估算，不含來回機票、簽證規費與初期押金；點擊「預算細算」可帶入該國模板試算整學期總支出與 ±10% 匯率緩衝。",
    ),
    (
        "如何把並排比較結果存下來跟家人或師長討論？",
        "可使用右上角「複製比較連結」保留目前選定的母校與 2–3 所目標校網址，或點擊「下載比較圖卡」匯出 PNG 對照圖檔，亦能複製純文字摘要貼至筆記軟體。",
    ),
)

FAQS_MILITARY_EXIT: tuple[tuple[str, str], ...] = (
    (
        "在學役男出國交換一學期（約 4.5 至 5 個月），可以先用網路申請「4 個月短期出境」飛出去嗎？",
        "切勿如此操作。依《役男出境處理辦法》，線上短期出境每次停留最長不得逾 4 個月，且出境後無法直接在境外轉換為學校推薦交換期限；超過 4 個月之交換研修必須在出國前由國內母校完成專案函報核准。",
    ),
    (
        "學校推薦役男出國交換專案核准，通常要提早多久向母校送件？",
        "因須取得國外姊妹校正式入學許可（LoA），並經母校國際處與學務處兵役承辦會辦後發函戶籍地直轄市、縣（市）政府審核，多數大學規定須於預定出國前 30 至 45 日備齊文件送交校內承辦。",
    ),
    (
        "交換期間如果寒暑假想短暫回台灣幾天再飛回姊妹校，需要重新申請出境嗎？",
        "需要特別留意。役男出境核准單通常對應單次或指定核准期間，若中途返台再出境，務必於返台前向母校兵役承辦確認再出境公文或簽章程序，實際規定以內政部役政司與各校最新官方公告為準。",
    ),
    (
        "大一升大二出國時還沒滿 19 歲，但回台灣時已經是滿 19 歲那年的 1 月之後，算役男嗎？",
        "算。依《兵役法》規定，自年滿 19 歲之年 1 月 1 日起（不看生日月份）即進入役齡；若交換期間跨入 19 歲當年 1 月 1 日，建議出國前主動洽詢母校兵役承辦與戶籍地公所役政單位確認。",
    ),
)

FAQS_SCHOLARSHIP_FINDER: tuple[tuple[str, str], ...] = (
    (
        "教育部「學海飛颺」與「學海惜珠」可以由學生自己向教育部報名嗎？",
        "不行。依教育部補助要點，兩項計畫均以國內薦送大學為申請與核撥單位，學生須依就讀母校國際處公告之校內期限、成績語檢門檻與指定文件向母校提出申請。",
    ),
    (
        "可以同時領取「學海飛颺」跟母校自籌的交換獎學金或外國政府獎學金嗎？",
        "教育部要點明定受補助學生不得同時兼領我國政府提供之其他出國補助；至於能否與母校自籌校務基金補助或外國機構獎學金（如日本 JASSO）兼領，須同時核對母校辦法與外方機構之兼領上限規定。",
    ),
    (
        "日本 JASSO 短期交換獎學金（每月 8 萬日圓）要怎麼申請？",
        "JASSO 協定接收獎學金並非所有赴日交換生皆可申請，須該日本姊妹校當年度獲 JASSO 核配計畫名額，並由日方接收學校就錄取交換生擇優推薦；實際有無名額請於姊妹校網報階段確認。",
    ),
    (
        "在臺灣就讀大學的外籍學位生或前往大陸港澳交換，可以申請學海系列嗎？",
        "教育部學海飛颺與學海惜珠限具中華民國國籍且在臺灣地區設有戶籍之學生申請，且補助地區不含大陸地區及港澳；外籍生或赴陸港澳交換生建議優先查詢母校校內專項獎助或接待校支援方案。",
    ),
)

FAQS_LANGUAGE_SURVEY: tuple[tuple[str, str], ...] = (
    (
        "為什麼「明確列載多益 750 分可達標」的校數，比實際能用多益申請的學校少？",
        "因為部分台灣母校將多益門檻統一寫在「校內甄選簡章總則」（例如校內初審統一採計多益），未逐筆重複標註於每間合作校欄位；本表僅統計合作校資料有明確寫出分數者，不對空白欄位做推論。",
    ),
    (
        "考 IELTS 6.5 或 TOEFL iBT 80 分，在選校數量上有明顯差距嗎？",
        "在歐美與日韓英語授課交換名單中，IELTS 6.0–6.5 與 TOEFL iBT 79–80 是最密集的分水嶺；跨過 IELTS 6.5（或 TOEFL 88–90）後，可涵蓋大多數綜合大學商管與理工英語學程，惟仍須留意單科小分門檻。",
    ),
    (
        "赴日交換一定要考日檢 JLPT N2 或 N1 嗎？",
        "若申請日本大學「一般學部／研究科日語授課方案」，多數學校確實列載 JLPT N2 或 N1；但許多日本國立與私立名校另設「全英語授課交換學程（如 JYPE、HUSTEP、PEAK 等）」，改採計托福、雅思或多益成績。",
    ),
)

FAQS_TOP_PARTNERS: tuple[tuple[str, str], ...] = (
    (
        "全台最多台灣大學簽約的海外名校排行是怎麼計算的？",
        "系統將全台 71 所公私立大學公開合作校名單依「國家＋標準化外國機構名稱」歸併為單一跨校實體，統計共有多少所台灣母校將該海外大學列入合作名單，並依締約母校數量由高至低排序。",
    ),
    (
        "締約台灣母校數量越多，代表名額越多或越容易申請嗎？",
        "不代表。各台灣母校與同一所海外大學簽訂的是各自獨立的雙邊交換協議，你只能透過自己就讀母校的校內甄選競爭母校獲配名額；實際資格、名額與期限以各校最新官方公告為準。",
    ),
    (
        "點擊排行表中的海外大學名稱可以看到什麼資訊？",
        "點擊海外校名可進入「跨校外國大學專頁」，上方可切換你的就讀母校查看當期名額與語檢門檻，下方可對照全台各締約大學的門檻差異、生活費參考與修課住宿摘要。",
    ),
)


# ---------------------------------------------------------------------------
# Route Registration for Wave 2 Pages
# ---------------------------------------------------------------------------

def register_wave2_routes(
    router: APIRouter,
    *,
    settings: Any,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    render_tool_page: Callable[..., HTMLResponse],
    render_data_page: Callable[..., HTMLResponse],
    render_switcher: Callable[[str], str],
    safe_json_block: Callable[[str, Any], str],
    official_link: Callable[[str | None, str], str],
    availability_labels: Mapping[str, str],
) -> None:
    survey_lock = threading.Lock()
    survey_cache: dict[str, tuple[float, dict[str, Any]]] = {}
    top_lock = threading.Lock()
    top_cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def get_cached_lang_survey(home_key: str) -> dict[str, Any]:
        norm_key = home_key if (home_key == "all" or resolve_university(home_key)) else "all"
        with survey_lock:
            hit = survey_cache.get(norm_key)
            if hit is not None and monotonic() - hit[0] < 60.0:
                return hit[1]
            computed = summarize_language_requirements_survey(catalogue_loader, home_filter=norm_key)
            survey_cache[norm_key] = (monotonic(), computed)
            return computed

    def get_cached_top_partners(country_key: str, q_str: str) -> dict[str, Any]:
        cache_k = f"{country_key}|{q_str.strip().casefold()}"
        with top_lock:
            hit = top_cache.get(cache_k)
            if hit is not None and monotonic() - hit[0] < 60.0:
                return hit[1]
            computed = summarize_top_partner_universities(catalogue_loader, country_filter=country_key, q=q_str, limit=50)
            top_cache[cache_k] = (monotonic(), computed)
            return computed

    # -----------------------------------------------------------------------
    # W2-1. /tools/partner-compare (+ .json endpoint)
    # -----------------------------------------------------------------------
    @router.get("/tools/partner-compare.json")
    def tool_partner_compare_json(
        home: str = Query(default="ntu"),
        p1: str | None = Query(default=None),
        p2: str | None = Query(default=None),
        p3: str | None = Query(default=None),
    ) -> JSONResponse:
        uni = resolve_university(home)
        if uni is None:
            raise HTTPException(404, "找不到這所母校")
        partners, _ = catalogue_loader(uni)
        data = build_partner_comparison(uni.id, partners, availability_labels, p1=p1, p2=p2, p3=p3)
        return JSONResponse(
            data,
            headers={"Cache-Control": "public, max-age=60", "X-Robots-Tag": "noindex, nofollow"},
        )

    @router.api_route("/tools/partner-compare", methods=["GET", "HEAD"])
    def tool_partner_compare(
        home: str = Query(default="ntu"),
        p1: str | None = Query(default=None),
        p2: str | None = Query(default=None),
        p3: str | None = Query(default=None),
    ) -> HTMLResponse:
        spec = WAVE2_SPECS["/tools/partner-compare"]
        uni = resolve_university(home) or resolve_university("ntu") or SUPPORTED_UNIVERSITIES[0]
        partners, _ = catalogue_loader(uni)
        comp = build_partner_comparison(uni.id, partners, availability_labels, p1=p1, p2=p2, p3=p3)

        home_opts = "".join(
            f'<option value="{escape(u.id)}"{" selected" if u.id == comp["home_id"] else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )

        def _partner_select_opts(selected_pid: str, allow_empty: bool = False) -> str:
            head = f'<option value=""{" selected" if not selected_pid else ""}>不選第 3 所（僅比較 2 校）</option>' if allow_empty else ""
            return head + "".join(
                f'<option value="{escape(opt["pid"])}"{" selected" if opt["pid"] == selected_pid else ""}>{escape(opt["label"])}</option>'
                for opt in comp["options"]
            )

        selected = comp["selected"]
        col_headers = "".join(
            f'<th scope="col"><a href="{escape(c["partner_url"])}">{escape(c["school_name"])}</a><span class="uw-inline-badge">{escape(c["country"])}</span></th>'
            for c in selected
        )

        def _row_cells(title: str, getter: Callable[[dict[str, Any]], str], *, raw_html: bool = False) -> str:
            tds = "".join(
                f"<td>{getter(c) if raw_html else escape(getter(c))}</td>"
                for c in selected
            )
            return f"<tr><th scope='row'>{escape(title)}</th>{tds}</tr>"

        compare_rows_html = (
            _row_cells("國家／地區", lambda c: c["country"])
            + _row_cells("當期資料狀態", lambda c: c["availability"])
            + _row_cells("來源列載名額", lambda c: c["quota"])
            + _row_cells("明確語檢門檻", lambda c: c["language_badges"])
            + _row_cells("語言條件摘錄", lambda c: c["language_snippet"])
            + _row_cells("可申請學制", lambda c: c["degree_levels"])
            + _row_cells("研修期間／學期", lambda c: c["study_period"])
            + _row_cells("當地月生活費參考", lambda c: c["budget_ref"])
            + _row_cells("學費與住宿摘要", lambda c: f"{c['tuition_info']} ／ {c['housing_info']}")
            + _row_cells(
                "深入核對連結",
                lambda c: (
                    f'<a href="{escape(c["partner_url"])}">母校方案頁</a> · '
                    f'<a href="{escape(c["cross_school_url"])}">跨校專頁</a> · '
                    f'<a href="/tools/exchange-budget-calculator?country={escape(c["country_slug"])}">預算細算</a> · '
                    + official_link(c["source_url"], "官方來源")
                ),
                raw_html=True,
            )
        )

        share_lines = [f"【UniWay 海外姊妹校並排比較】母校：{comp['home_name']}"]
        for idx, c in enumerate(selected, 1):
            share_lines.append(
                f"{idx}. {c['school_name']}（{c['country']}）｜狀態：{c['availability']}｜名額：{c['quota']}｜語檢：{c['language_badges']}｜預算參考：{c['budget_ref']}"
            )
        share_q = urlencode({k: v for k, v in (("home", comp["home_id"]), ("p1", comp["p1"]), ("p2", comp["p2"]), ("p3", comp["p3"])) if v})
        share_lines.append(f"並排比較網址：{settings.origin}{spec.path}?{share_q}（{MANDATORY_DISCLAIMER}）")
        share_summary_str = "\n".join(share_lines)

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
{safe_json_block("uw-pk-initial", {"home_name": comp["home_name"], "selected": selected})}

<section class="uw-tool-card" aria-labelledby="pk-calc-heading">
  <div class="uw-tool-header">
    <h2 id="pk-calc-heading">挑選 2～3 所目標姊妹校並排對照</h2>
    <div class="uw-btn-group">
      <button type="button" class="uw-btn uw-btn-primary uw-btn-sm" id="pk-download-card">下載比較圖卡</button>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-target="pk-summary-copy">複製比較摘要</button>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製比較連結</button>
    </div>
  </div>

  <form method="get" action="/tools/partner-compare" class="uw-form-grid" data-tool-form="partner-compare">
    <label class="uw-field">
      <span>就讀母校（共 <span data-pk-out="option-count">{comp['total_options']}</span> 校可選）</span>
      <select name="home" id="pk-home">{home_opts}</select>
    </label>
    <label class="uw-field">
      <span>目標校 1</span>
      <select name="p1" id="pk-p1">{_partner_select_opts(comp['p1'])}</select>
    </label>
    <label class="uw-field">
      <span>目標校 2</span>
      <select name="p2" id="pk-p2">{_partner_select_opts(comp['p2'])}</select>
    </label>
    <label class="uw-field">
      <span>目標校 3（選填）</span>
      <select name="p3" id="pk-p3">{_partner_select_opts(comp['p3'], allow_empty=True)}</select>
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">並排比較</button>
    </div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="海外姊妹校並排比較表">
    <table class="uw-data-table" id="pk-compare-table">
      <caption class="uw-sr-only">{escape(comp['home_name'])}海外合作大學並排條件比較表</caption>
      <thead id="pk-compare-thead">
        <tr>
          <th scope="col">比較維度</th>
          {col_headers}
        </tr>
      </thead>
      <tbody id="pk-compare-tbody">{compare_rows_html}</tbody>
    </table>
  </div>
  <pre id="pk-summary-copy" hidden>{escape(share_summary_str)}</pre>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>填排交換志願序時的 4 個並排檢查重點</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="交換志願並排檢查維度說明表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">志願序並排比較四大檢查維度</caption>
          <thead>
            <tr>
              <th scope="col">檢查項目</th>
              <th scope="col">為什麼重要</th>
              <th scope="col">常見避坑提醒</th>
            </tr>
          </thead>
          <tbody>
            <tr><th scope="row">當期狀態與名額</th><td>區分當期開缺與歷年參考名單</td><td>避免將「零名額」或「院系級限定」誤填進一般校級志願</td></tr>
            <tr><th scope="row">採計語檢種類</th><td>確認接受 IELTS / TOEFL 或 TOEIC / JLPT</td><td>部分歐美學校不收 TOEIC 或不收拼分（MyBest Scores）</td></tr>
            <tr><th scope="row">學期起迄與台灣校曆</th><td>影響回國註冊、實習或兵役畢業時程</td><td>日本春學期（4–8 月）與德國夏學期（4–9 月）常跨暑假</td></tr>
            <tr><th scope="row">住宿與生活總成本</th><td>同國首都圈與大學城租金差距可達 1.5 倍</td><td>免繳海外學費仍須自付住宿、強制醫保與來回機票</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_PARTNER_COMPARE)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), ("海外姊妹校並排 PK 比較器", spec.path)],
            FAQS_PARTNER_COMPARE,
        )

    # -----------------------------------------------------------------------
    # W2-2. /tools/military-service-exit-checker (+ .ics endpoint)
    # -----------------------------------------------------------------------
    @router.get("/tools/military-service-exit-checker.ics", response_class=PlainTextResponse)
    def tool_military_exit_ics(
        status: str = Query(default="draft_male"),
        depart: str | None = Query(default=None),
        return_date: str | None = Query(default=None),
        school: str = Query(default="ntu"),
    ) -> PlainTextResponse:
        filename, content = build_military_exit_ics(
            status=status,
            depart_str=depart,
            return_str=return_date,
            school_id=school,
        )
        return PlainTextResponse(
            content,
            media_type="text/calendar; charset=utf-8",
            headers={
                "Cache-Control": "public, max-age=300",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Robots-Tag": "noindex, nofollow",
            },
        )

    @router.api_route("/tools/military-service-exit-checker", methods=["GET", "HEAD"])
    def tool_military_service_exit_checker(
        status: str = Query(default="draft_male"),
        depart: str | None = Query(default=None),
        return_date: str | None = Query(default=None),
        school: str = Query(default="ntu"),
    ) -> HTMLResponse:
        spec = WAVE2_SPECS["/tools/military-service-exit-checker"]
        res = evaluate_military_service_exit(
            status=status,
            depart_str=depart,
            return_str=return_date,
            school_id=school,
        )

        status_opts = "".join(
            f'<option value="{escape(k)}"{" selected" if res["status"] == k else ""}>{escape(lbl)}</option>'
            for k, lbl in MILITARY_STATUS_OPTIONS.items()
        )
        school_opts = "".join(
            f'<option value="{escape(u.id)}"{" selected" if res["school_id"] == u.id else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )

        timeline_html = "".join(
            f"""<li class="uw-timeline-step">
  <div class="uw-timeline-date">
    <span class="uw-timeline-offset">{escape(item['offset'])}</span>
    <time datetime="{escape(item['date'])}">{escape(item['date'])}</time>
  </div>
  <div class="uw-timeline-content">
    <h4>{escape(item['title'])}</h4>
  </div>
</li>"""
            for item in res["timeline"]
        )

        js_schools = {
            u.id: {
                "school_name": u.school_name,
                "short_name": u.short_name,
                "official_url": safe_https_or_http_url(u.official_url) or "",
            }
            for u in SUPPORTED_UNIVERSITIES
        }

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
{safe_json_block("uw-mil-schools", js_schools)}

<section class="uw-tool-card" aria-labelledby="mil-calc-heading">
  <div class="uw-tool-header">
    <h2 id="mil-calc-heading">核對役男出境管道與校內送件節點</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-primary uw-btn-sm" id="mil-ics-link" href="{escape(res['ics_url'])}">下載 .ics 行事曆</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製檢核連結</button>
    </div>
  </div>

  <form method="get" action="/tools/military-service-exit-checker" class="uw-form-grid" data-tool-form="military-exit">
    <label class="uw-field">
      <span>役齡與兵役身分</span>
      <select name="status" id="mil-status">{status_opts}</select>
    </label>
    <label class="uw-field">
      <span>預計出境日</span>
      <input type="date" name="depart" id="mil-depart" value="{escape(res['depart_date'])}" required>
    </label>
    <label class="uw-field">
      <span>預計返國日</span>
      <input type="date" name="return_date" id="mil-return" value="{escape(res['return_date'])}" required>
    </label>
    <label class="uw-field">
      <span>就讀母校</span>
      <select name="school" id="mil-school">{school_opts}</select>
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">檢核時程</button>
    </div>
  </form>

  <div class="uw-kpi-grid" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">預估境外停留總天數</span>
      <strong class="uw-kpi-value" data-mil-out="stay-days">{res['stay_days']} 天</strong>
      <span class="uw-kpi-tag" data-mil-out="stay-months">約 {res['stay_months']} 個月</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">短期出境 4 個月上限比對</span>
      <strong class="uw-kpi-value" data-mil-out="short-cap">{'超過 4 個月' if res['exceeds_short_exit'] else '4 個月內'}</strong>
      <span class="uw-kpi-tag">法規短期出境上限為 4 個月</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">建議校內送件最晚基準</span>
      <strong class="uw-kpi-value" data-mil-out="submit-by">{escape(res['timeline'][1]['date'])}</strong>
      <span class="uw-kpi-tag">出國前 30–45 日洽母校承辦</span>
    </div>
  </div>

  <div class="uw-status-bar" id="mil-verdict-box" aria-live="polite">
    <div>
      <strong data-mil-out="route-badge">{escape(res['route_badge'])}</strong>
      <p class="uw-compact-note" data-mil-out="route-summary">{escape(res['route_summary'])}</p>
    </div>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-outline uw-btn-sm" href="https://www.ris.gov.tw/military-onlineDeparture/" rel="noopener noreferrer" data-official-source>役政司出境系統 ↗</a>
      <a class="uw-btn uw-btn-outline uw-btn-sm" id="mil-school-link" href="{escape(res['school_official_url'] or '/schools/' + res['school_id'])}" rel="noopener noreferrer" data-official-source><span data-mil-out="short-name">{escape(res['short_name'])}</span>官網 ↗</a>
    </div>
  </div>

  <ol class="uw-timeline-list" id="mil-timeline-list" aria-live="polite">{timeline_html}</ol>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>「學校推薦出國交換專案核准」vs「線上短期出境」法規與必備文件對照表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="役男短期出境與學校推薦出國交換專案核准對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">依《役男出境處理辦法》整理之兩種出境管道差異與必備文件</caption>
          <thead>
            <tr>
              <th scope="col">比較項目</th>
              <th scope="col">學校推薦出國交換／研修專案核准</th>
              <th scope="col">役男線上申請短期出境（觀光等）</th>
            </tr>
          </thead>
          <tbody>
            <tr><th scope="row">法規依據</th><td>《役男出境處理辦法》第 4 條第 1 項第 3 款（推薦出國研究、進修等）</td><td>《役男出境處理辦法》第 4 條第 1 項第 7 款</td></tr>
            <tr><th scope="row">單次最長停留期限</th><td>原則最長不得逾 1 年（依核准公文所載起迄期限為準）</td><td>每次不得逾 4 個月（不可用於超過 4 個月之學期交換）</td></tr>
            <tr><th scope="row">申請窗口與程序</th><td>備妥海外入學許可（LoA）等文件交母校國際處／生輔組造冊函報縣市政府</td><td>出境前 3 至 30 日內由役男本人至役政司網站線上申請</td></tr>
            <tr><th scope="row">常見必備文件</th><td>1. 國外姊妹校入學許可（及中譯本，依各校與縣市政府規定）<br>2. 護照基本資料頁影本<br>3. 校內申請書／切結或家長同意書</td><td>有效護照基本資料（線上核驗無限制出境紀錄即可列印核准單）</td></tr>
            <tr><th scope="row">官方查核來源</th><td><a href="https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0040006" rel="noopener noreferrer" data-official-source>全國法規資料庫《役男出境處理辦法》</a></td><td><a href="https://www.ris.gov.tw/military-onlineDeparture/" rel="noopener noreferrer" data-official-source>內政部役政司役男線上申請短期出境</a></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_MILITARY_EXIT)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip("本頁整理自《兵役法》與《役男出境處理辦法》公開條文，個別役男緩徵、體位、徵兵檢查及再出境規定請逕洽內政部役政司、戶籍地鄉鎮市區公所兵役課與母校學務處兵役承辦人確認。")}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), ("役男出境交換檢查器", spec.path)],
            FAQS_MILITARY_EXIT,
        )

    # -----------------------------------------------------------------------
    # W2-3. /tools/scholarship-finder
    # -----------------------------------------------------------------------
    @router.api_route("/tools/scholarship-finder", methods=["GET", "HEAD"])
    def tool_scholarship_finder(
        home: str = Query(default="ntu"),
        region: str = Query(default="all"),
        identity: str = Query(default="roc_general"),
        duration: str = Query(default="semester"),
    ) -> HTMLResponse:
        spec = WAVE2_SPECS["/tools/scholarship-finder"]
        res = filter_scholarships(home_id=home, region=region, identity=identity, duration=duration)

        home_opts = "".join(
            f'<option value="{escape(u.id)}"{" selected" if u.id == res["home_id"] else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )
        region_opts = "".join(
            f'<option value="{escape(k)}"{" selected" if k == res["region"] else ""}>{escape(v)}</option>'
            for k, v in SCHOLARSHIP_REGIONS.items()
        )
        id_opts = "".join(
            f'<option value="{escape(k)}"{" selected" if k == res["identity"] else ""}>{escape(v)}</option>'
            for k, v in SCHOLARSHIP_IDENTITIES.items()
        )
        dur_opts = "".join(
            f'<option value="{escape(k)}"{" selected" if k == res["duration"] else ""}>{escape(v)}</option>'
            for k, v in SCHOLARSHIP_DURATIONS.items()
        )

        matched_rows_html = ""
        for item in res["matched"]:
            matched_rows_html += f"""<tr data-schol-id="{escape(item['id'])}">
  <th scope="row"><strong>{escape(item['name'])}</strong><div class="uw-cell-sub">{escape(item['sponsor'])}</div></th>
  <td>{escape(item['channel'])}</td>
  <td>{escape(item['eligibility_note'])}</td>
  <td>{escape(item['funding_note'])}</td>
  <td>{official_link(item['official_url'], item['official_label'])}</td>
</tr>"""

        excluded_rows_html = ""
        for item in res["excluded"]:
            excluded_rows_html += f"""<tr>
  <th scope="row">{escape(item['name'])}</th>
  <td><span class="uw-inline-badge">{escape(item['exclude_reason'])}</span></td>
  <td>{official_link(item['official_url'], item['official_label'])}</td>
</tr>"""

        js_catalog_payload = {
            "catalog": list(OFFICIAL_SCHOLARSHIP_CATALOG),
            "schools": {
                u.id: {
                    "school_name": u.school_name,
                    "short_name": u.short_name,
                    "official_url": safe_https_or_http_url(u.official_url) or "https://www.studyabroad.moe.gov.tw/",
                }
                for u in SUPPORTED_UNIVERSITIES
            },
            "regions": SCHOLARSHIP_REGIONS,
            "identities": SCHOLARSHIP_IDENTITIES,
            "durations": SCHOLARSHIP_DURATIONS,
        }

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
{safe_json_block("uw-scholarship-data", js_catalog_payload)}

<section class="uw-tool-card" aria-labelledby="schol-calc-heading">
  <div class="uw-tool-header">
    <h2 id="schol-calc-heading">篩選可評估之交換獎學金（符合 <span id="schol-match-count">{len(res['matched'])}</span> 項）</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-sm uw-btn-outline" href="/guides/exchange-scholarships">閱讀補助申請指南</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製篩選連結</button>
    </div>
  </div>

  <form method="get" action="/tools/scholarship-finder" class="uw-form-grid" data-tool-form="scholarship">
    <label class="uw-field">
      <span>就讀母校</span>
      <select name="home" id="schol-home">{home_opts}</select>
    </label>
    <label class="uw-field">
      <span>目的地國家／地區</span>
      <select name="region" id="schol-region">{region_opts}</select>
    </label>
    <label class="uw-field">
      <span>學籍與國籍身分</span>
      <select name="identity" id="schol-identity">{id_opts}</select>
    </label>
    <label class="uw-field">
      <span>交換研修期程</span>
      <select name="duration" id="schol-duration">{dur_opts}</select>
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">篩選補助</button>
    </div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="符合條件之交換獎學金與補助清單">
    <table class="uw-data-table" id="schol-matched-table">
      <caption class="uw-sr-only">依目前學籍身分、交換地區與期程篩選之官方獎助學金管道</caption>
      <thead>
        <tr>
          <th scope="col">獎助計畫名稱</th>
          <th scope="col">申請窗口與送件方式</th>
          <th scope="col">核心資格要件</th>
          <th scope="col">撥款與兼領提醒</th>
          <th scope="col">官方公告來源</th>
        </tr>
      </thead>
      <tbody id="schol-matched-tbody">{matched_rows_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer" id="schol-excluded-drawer"{" hidden" if not excluded_rows_html else ""}>
    <summary>目前條件暫不適用之其他獎助計畫（<span id="schol-excluded-count">{len(res['excluded'])}</span> 項）</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="目前篩選條件未納入之獎助計畫說明表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">未納入目前條件之獎助計畫及原因對照</caption>
          <thead>
            <tr>
              <th scope="col">獎助計畫</th>
              <th scope="col">未納入原因</th>
              <th scope="col">官方來源</th>
            </tr>
          </thead>
          <tbody id="schol-excluded-tbody">{excluded_rows_html or "<tr><td>無</td><td>目前篩選涵蓋全部收錄計畫</td><td>—</td></tr>"}</tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_SCHOLARSHIP_FINDER)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), ("交換獎學金快速篩選器", spec.path)],
            FAQS_SCHOLARSHIP_FINDER,
        )

    # -----------------------------------------------------------------------
    # W2-4. /data/language-requirements
    # -----------------------------------------------------------------------
    @router.api_route("/data/language-requirements", methods=["GET", "HEAD"])
    def data_language_requirements(
        test: str = Query(default="all"),
        home: str = Query(default="all"),
    ) -> HTMLResponse:
        spec = WAVE2_SPECS["/data/language-requirements"]
        survey = get_cached_lang_survey(home)
        valid_tests = {"all", "toeic", "ielts", "toefl", "cefr", "jlpt"}
        active_test = test if test in valid_tests else "all"

        tiers = [
            t for t in survey["tiers"]
            if active_test == "all" or t["test"] == active_test
        ]

        test_opts = "".join(
            f'<option value="{k}"{" selected" if active_test == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("all", "全部檢定（TOEIC・IELTS・TOEFL・CEFR・JLPT）"),
                ("toeic", "TOEIC 多益聽讀"),
                ("ielts", "IELTS 雅思學術組"),
                ("toefl", "TOEFL iBT 托福"),
                ("cefr", "CEFR 歐洲語言分級"),
                ("jlpt", "JLPT 日本語能力試驗"),
            )
        )
        home_opts = (
            f'<option value="all"{" selected" if survey["selected_home_id"] == "all" else ""}>全台 {len(SUPPORTED_UNIVERSITIES)} 所大學總計</option>'
            + "".join(
                f'<option value="{escape(u.id)}"{" selected" if survey["selected_home_id"] == u.id else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
                for u in SUPPORTED_UNIVERSITIES
            )
        )

        tier_rows_html = ""
        for t in tiers:
            tier_rows_html += f"""<tr data-lang-tier-test="{escape(t['test'])}">
  <th scope="row"><strong>{escape(t['label'])}</strong><span class="uw-inline-badge">{escape(t['test_group'])}</span></th>
  <td><strong>{t['partner_page_hits']:,}</strong> 頁</td>
  <td><strong>{t['unique_institutions']:,}</strong> 所</td>
  <td>{t['home_school_count']} 校</td>
  <td>{escape(t['top_countries'])}</td>
  <td>{escape(t['note'])} · <a href="{escape(t['converter_url'])}">查名單 →</a></td>
</tr>"""

        # Pick headline KPI numbers from full tier list
        by_id = {t["id"]: t for t in survey["tiers"]}
        ielts65 = by_id["ielts-6.5"]["partner_page_hits"]
        toefl80 = by_id["toefl-79"]["partner_page_hits"]
        toeic800 = by_id["toeic-800"]["partner_page_hits"]
        jlptn2 = by_id["jlpt-n2"]["partner_page_hits"]

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}

<section class="uw-kpi-grid" aria-label="主流檢定分數段達標合作校頁面數">
  <div class="uw-kpi-box uw-kpi-highlight">
    <span class="uw-kpi-label">IELTS 6.5 明確達標</span>
    <strong class="uw-kpi-value">{ielts65:,} 頁</strong>
    <span class="uw-kpi-tag">去重 {by_id['ielts-6.5']['unique_institutions']:,} 所外校</span>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">TOEFL iBT 80 明確達標</span>
    <strong class="uw-kpi-value">{toefl80:,} 頁</strong>
    <span class="uw-kpi-tag">去重 {by_id['toefl-79']['unique_institutions']:,} 所外校</span>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">TOEIC 800 明確達標</span>
    <strong class="uw-kpi-value">{toeic800:,} 頁</strong>
    <span class="uw-kpi-tag">去重 {by_id['toeic-800']['unique_institutions']:,} 所外校</span>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">JLPT N2 明確達標</span>
    <strong class="uw-kpi-value">{jlptn2:,} 頁</strong>
    <span class="uw-kpi-tag">去重 {by_id['jlpt-n2']['unique_institutions']:,} 所外校</span>
  </div>
</section>

<section class="uw-tool-card" aria-labelledby="lang-survey-heading">
  <div class="uw-tool-header">
    <h2 id="lang-survey-heading">{escape(survey['selected_home_label'])}（共 {survey['total_partner_pages']:,} 個合作校頁面）</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-sm uw-btn-outline" href="/data/language-requirements">重設</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製網址</button>
    </div>
  </div>

  <form method="get" action="/data/language-requirements" class="uw-form-grid" data-data-filter="lang-survey">
    <label class="uw-field">
      <span>篩選檢定類別</span>
      <select name="test" id="ls-test">{test_opts}</select>
    </label>
    <label class="uw-field">
      <span>統計母校範圍</span>
      <select name="home" id="ls-home">{home_opts}</select>
    </label>
    <div class="uw-form-actions">
      <button type="submit" class="uw-btn uw-btn-primary">更新統計範圍</button>
    </div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="交換語言門檻各分數段可申請校數統計表">
    <table class="uw-data-table" id="lang-survey-table">
      <caption class="uw-sr-only">{escape(survey['selected_home_label'])}各語言檢定分數段明確列載達標合作校統計</caption>
      <thead>
        <tr>
          <th scope="col">檢定與分數段</th>
          <th scope="col">達標合作校頁面數</th>
          <th scope="col">去重海外大學數</th>
          <th scope="col">涵蓋母校數</th>
          <th scope="col">主要國家前 3 名</th>
          <th scope="col">分數定位與名單查詢</th>
        </tr>
      </thead>
      <tbody id="lang-survey-tbody">{tier_rows_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>統計方法與資料庫欄位覆蓋率說明</summary>
    <div class="uw-drawer-body">
      <ul>
        <li><strong>樣本母體：</strong>目前所選範圍共 {survey['total_partner_pages']:,} 個母校合作校頁面，其中 {survey['explicitly_parsed_pages']:,} 頁於合作校條目明確列載語檢數值，其餘 {survey['unparsed_pages']:,} 頁歸於母校簡章總則或他語種要求。</li>
        <li><strong>不推論原則：</strong>若某海外大學僅寫 <code>IELTS 6.0</code> 而未寫 <code>TOEIC</code>，則只計入 IELTS 6.0 以上分數段，絕不自行換算計入多益欄位。</li>
      </ul>
    </div>
  </details>
  {render_faq_section(FAQS_LANGUAGE_SURVEY)}
  {render_core_summary_and_citation_box(settings.origin, spec, checked_date=survey['latest_checked'])}
  {render_compliance_strip()}
</div>"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data"), ("交換語言門檻大調查", spec.path)],
            FAQS_LANGUAGE_SURVEY,
            variables=("多益各分數段合作校數", "雅思各分數段合作校數", "托福iBT各分數段合作校數", "日檢JLPT各級別合作校數", "CEFR分級合作校數"),
            keywords=("交換學生語言門檻統計", "多益交換學校數量", "雅思6.5交換大學", "日檢N2交換統計"),
            date_modified=survey["latest_checked"],
        )

    # -----------------------------------------------------------------------
    # W2-5. /data/top-partner-universities
    # -----------------------------------------------------------------------
    @router.api_route("/data/top-partner-universities", methods=["GET", "HEAD"])
    def data_top_partner_universities(
        country: str = Query(default="all"),
        q: str = Query(default=""),
    ) -> HTMLResponse:
        spec = WAVE2_SPECS["/data/top-partner-universities"]
        top_data = get_cached_top_partners(country, q)

        country_opts = (
            f'<option value="all"{" selected" if top_data["active_country"] == "all" else ""}>全部國家／地區（跨校締約共 {top_data["multi_school_entities"]:,} 所）</option>'
            + "".join(
                f'<option value="{escape(c["slug"])}"{" selected" if top_data["active_country"] == c["slug"] else ""}>{escape(c["name"])}（{c["count"]} 所跨校合作）</option>'
                for c in top_data["country_options"]
            )
        )

        rows_html = ""
        for item in top_data["items"]:
            preview_homes = item["homes"][:6]
            extra_homes = item["homes"][6:]
            home_links_html = "、".join(
                f'<a href="{escape(h["partner_path"])}">{escape(h["short_name"])}</a>'
                for h in preview_homes
            )
            if extra_homes:
                more_links = "、".join(
                    f'<a href="{escape(h["partner_path"])}">{escape(h["short_name"])}</a>'
                    for h in extra_homes
                )
                home_links_html += (
                    f' <details class="uw-inline-more"><summary>＋其餘 {len(extra_homes)} 校</summary>'
                    f'<span>{more_links}</span></details>'
                )

            rows_html += f"""<tr data-top-name="{escape(item['display_title'])} {escape(item['country_name_zh'])}" data-top-country="{escape(item['country_slug'])}">
  <td><strong>{item['rank']}</strong></td>
  <th scope="row"><a href="{escape(item['canonical_path'])}">{escape(item['school_name_zh'])}</a><div class="uw-cell-sub">{escape(item['school_name_en'])}</div></th>
  <td><a href="{escape(item['destination_path'])}">{escape(item['country_name_zh'])}</a></td>
  <td><strong>{item['contracted_count']}</strong> 校<div class="uw-cell-sub">當期列載 {item['open_home_count']} 校</div></td>
  <td>{home_links_html}</td>
  <td>{official_link(item['primary_source_url'], '官方來源')}</td>
</tr>"""

        if not rows_html:
            rows_html = "<tr><td colspan='6'>找不到符合篩選條件的海外合作大學，請重設國家或關鍵字。</td></tr>"

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}

<section class="uw-kpi-grid" aria-label="全台跨校海外姊妹校規模摘要">
  <div class="uw-kpi-box uw-kpi-highlight">
    <span class="uw-kpi-label">榜首海外姊妹校締約數</span>
    <strong class="uw-kpi-value">{top_data['items'][0]['contracted_count'] if top_data['items'] else 0} 所台灣母校</strong>
    <span class="uw-kpi-tag">{escape(top_data['items'][0]['school_name_zh']) if top_data['items'] else '—'}</span>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">2 校以上共同締約外校</span>
    <strong class="uw-kpi-value">{top_data['multi_school_entities']:,} 所</strong>
    <span class="uw-kpi-tag">可跨校對照門檻與生活費</span>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">全庫去重海外合作大學</span>
    <strong class="uw-kpi-value">{top_data['total_unique_entities']:,} 所</strong>
    <span class="uw-kpi-tag">整合自全台 {len(SUPPORTED_UNIVERSITIES)} 校名單</span>
  </div>
</section>

<section class="uw-tool-card" aria-labelledby="top-partners-heading">
  <div class="uw-tool-header">
    <h2 id="top-partners-heading">篩選國家與搜尋海外校名（顯示前 <span id="top-visible-count">{len(top_data['items'])}</span> 所）</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-sm uw-btn-outline" href="/data/top-partner-universities">重設</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製網址</button>
    </div>
  </div>

  <form method="get" action="/data/top-partner-universities" class="uw-form-grid" data-data-filter="top-partners">
    <label class="uw-field">
      <span>目的地國家</span>
      <select name="country" id="tp-country">{country_opts}</select>
    </label>
    <label class="uw-field">
      <span>搜尋中英文校名</span>
      <input type="search" name="q" id="tp-q" value="{escape(top_data['q'])}" placeholder="如 早稻田、慕尼黑、UC、延世…">
    </label>
    <div class="uw-form-actions">
      <button type="submit" class="uw-btn uw-btn-primary">套用篩選</button>
    </div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="全台最多台灣大學簽約之海外名校 Top 50 排行表">
    <table class="uw-data-table" id="top-partners-table">
      <caption class="uw-sr-only">依全台 71 所大學公開交換名單統計之締約母校數前 50 大海外合作大學</caption>
      <thead>
        <tr>
          <th scope="col">#</th>
          <th scope="col">海外合作大學</th>
          <th scope="col">國家／地區</th>
          <th scope="col">締約母校數</th>
          <th scope="col">台灣締約母校方案連結</th>
          <th scope="col">來源查核</th>
        </tr>
      </thead>
      <tbody id="top-partners-tbody">{rows_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>跨校機構歸併方法與閱讀提醒</summary>
    <div class="uw-drawer-body">
      <ul>
        <li><strong>歸併基準：</strong>依目的地國家與標準化中英文校名將 71 校公開合作名單歸併為同一外國教育機構，同校多學程或分校區依來源定義保留連結。</li>
        <li><strong>非開放名額保證：</strong>締約母校數包含「當期名單列載」「締約合作參考」與「院系級合作參考」，請點擊對應母校簡稱確認自身學校當期是否開放申請。</li>
      </ul>
    </div>
  </details>
  {render_faq_section(FAQS_TOP_PARTNERS)}
  {render_core_summary_and_citation_box(settings.origin, spec, checked_date=top_data['latest_checked'])}
  {render_compliance_strip()}
</div>"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data"), ("全台締約海外名校 Top 50", spec.path)],
            FAQS_TOP_PARTNERS,
            variables=("全台締約母校數", "當期名單列載母校數", "目的地國家", "各母校合作方案連結"),
            keywords=("海外姊妹校排行", "台灣大學簽約最多外國大學", "交換學生熱門名校Top50", "跨校姊妹校查詢"),
            date_modified=top_data["latest_checked"],
        )
