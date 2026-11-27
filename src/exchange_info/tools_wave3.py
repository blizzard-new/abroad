"""Wave 3 public SEO tools (/tools/...) — 10 interactive, SSR-first, zero-fabrication tools.

Implements:
1. /tools/test-validity-checker        — 語言檢定成績效期檢查器
2. /tools/eligibility-matcher          — 30 秒交換選校雷達 (+ .json live endpoint)
3. /tools/reverse-partner-search       — 海外名校反查器 (+ .json live endpoint)
4. /tools/preference-ranker            — 志願序風險配比檢查器 (+ .json live endpoint)
5. /tools/fx-budget-planner            — 外幣換匯分批成本與資金缺口計算機
6. /tools/deadline-timezone-converter  — 海外截止時間跨時區＋夏令時間台灣換算器
7. /tools/application-checklist        — 申請文件與行前必備核對清單產生器（支援列印／PDF）
8. /tools/study-plan-checker           — 英文讀書計畫（Study Plan）結構與字數體檢器
9. /tools/fact-sheet-worksheet         — 姊妹校 Fact Sheet 12 欄互動重點整理表
10. /tools/email-template-generator    — 教授推薦信邀約／國際處詢問信中英範本產生器
"""
from __future__ import annotations

import re
import threading
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime, timedelta
from html import escape
from time import monotonic
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse

from . import api as _api_mod
from .cost_estimates import fx_reference
from .cross_school_partners import (
    COUNTRY_SLUGS,
    build_cross_school_entity_index,
    resolve_partner_cross_school_path,
)
from .destination_tips import canonical_country
from .models import CatalogueSourceStatus, PartnerUniversity
from .tools_and_data_core import (
    BUDGET_COUNTRY_TEMPLATES,
    CEFR_RANK,
    JLPT_LEVEL_INFO,
    MANDATORY_DISCLAIMER,
    TAIPEI_TZ,
    PageMetaSpec,
    build_all_71_school_deadlines,
    calculate_exchange_budget,
    convert_language_score,
    extract_partner_language_thresholds,
    partner_group_id,
    render_compliance_strip,
    render_core_summary_and_citation_box,
    render_faq_section,
    safe_https_or_http_url,
)
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university


WAVE3_TOOL_SPECS: dict[str, PageMetaSpec] = {
    "/tools/test-validity-checker": PageMetaSpec(
        path="/tools/test-validity-checker",
        slug="test-validity-checker",
        kind="tool",
        short_title="語檢成績效期檢查器",
        title="語言檢定成績效期檢查器｜托福・雅思・多益 2 年效期與提名日比對｜UniWay",
        h1="語言檢定成績效期檢查器",
        description="輸入語言檢定考試日期，自動比對台灣母校校內截止日與海外姊妹校提名網報日之 2 年效期，並試算官方成績單加發寄送緩衝日。",
        core_conclusion="依考試日期自動比對母校校內截止日與姊妹校提名日之兩年效期及寄送緩衝，實際規定以各校最新官方公告為準。",
    ),
    "/tools/eligibility-matcher": PageMetaSpec(
        path="/tools/eligibility-matcher",
        slug="eligibility-matcher",
        kind="tool",
        short_title="30 秒交換選校雷達",
        title="30 秒交換選校雷達｜母校＋語檢＋GPA＋預算＋洲別免登入即時篩選｜UniWay",
        h1="30 秒交換選校雷達",
        description="免登入選擇台灣母校並輸入語言檢定分數、GPA、學期預算與目標洲別，即時從全台 71 校真實資料庫篩選明確列載達標之海外合作校。",
        core_conclusion="結合就讀母校、語言檢定成績、GPA、預算上限與洲別即時篩選資料庫合作校，實際資格與名額以各校最新官方公告為準。",
    ),
    "/tools/reverse-partner-search": PageMetaSpec(
        path="/tools/reverse-partner-search",
        slug="reverse-partner-search",
        kind="tool",
        short_title="海外名校反查器",
        title="海外名校反查器｜輸入國外大學反查台灣哪些大學有簽交換與門檻｜UniWay",
        h1="海外姊妹校締約母校反查器",
        description="輸入早稻田、慕尼黑工大、延世、加州大學等海外學校名稱，即時反查全台 71 所公私立大學中哪幾所母校列載交換合作、名額狀態與語檢門檻。",
        core_conclusion="輸入海外大學名稱即可反查全台 71 所大學中哪些台灣母校列載合作關係與門檻，實際資格與名額以各校最新官方公告為準。",
    ),
    "/tools/preference-ranker": PageMetaSpec(
        path="/tools/preference-ranker",
        slug="preference-ranker",
        kind="tool",
        short_title="志願序風險檢查器",
        title="交換學生志願序風險配比檢查器｜夢幻・落點・保底排序與零名額提醒｜UniWay",
        h1="交換志願序風險配比檢查器",
        description="將母校合作校排入志願序並標記夢幻、落點與保底層級，自動檢查零名額、待確認、高門檻集中與志願倒掛風險，支援上下調整順序與複製清單。",
        core_conclusion="依夢幻、落點與保底層級檢視交換志願序排序，即時標示零名額、待確認與高門檻集中風險，實際名額以各校最新官方公告為準。",
    ),
    "/tools/fx-budget-planner": PageMetaSpec(
        path="/tools/fx-budget-planner",
        slug="fx-budget-planner",
        kind="tool",
        short_title="外幣分批換匯計算機",
        title="外幣換匯分批成本與交換資金缺口計算機｜日圓・歐元・美元批次均價｜UniWay",
        h1="外幣換匯分批成本與資金缺口計算機",
        description="記錄已分批換入的日圓、歐元、美元或韓元金額與匯率，自動計算持有外幣加權平均成本、尚缺外幣金額，以及不同匯率情境下補齊缺口所需台幣。",
        core_conclusion="彙算已換外幣批次均價與尚缺交換資金之台幣需求，並試算匯率波動對總自備款影響，實際收費標準以各校最新官方公告為準。",
    ),
    "/tools/deadline-timezone-converter": PageMetaSpec(
        path="/tools/deadline-timezone-converter",
        slug="deadline-timezone-converter",
        kind="tool",
        short_title="跨時區截止時間換算器",
        title="海外交換截止時間跨時區＋夏令時間換算器｜歐美日韓轉台灣時間｜UniWay",
        h1="海外截止時間跨時區與夏令時間換算器",
        description="輸入海外姊妹校網報或宿舍申請截止日期與當地時刻，自動套用歐美與澳洲冬夏令時間（DST）規則換算準確台灣時間與提前 24 小時安全送件線。",
        core_conclusion="自動依海外姊妹校時區與冬夏令時間規則換算正確台灣截止時刻，並標示安全送件緩衝時間，實際期限以各校最新官方公告為準。",
    ),
    "/tools/application-checklist": PageMetaSpec(
        path="/tools/application-checklist",
        slug="application-checklist",
        kind="tool",
        short_title="申請與行前核對清單",
        title="交換學生申請文件與行前必備核對清單產生器｜依國家與階段列印 PDF｜UniWay",
        h1="交換申請文件與行前必備核對清單",
        description="依交換目的地國家、申請階段（校內甄選／姊妹校網報／簽證住宿行前）與役男身分動態產生檢核清單，支援瀏覽器暫存勾選進度與列印存成 PDF。",
        core_conclusion="依交換目的地國家與申請階段整理校內甄選、姊妹校網報及簽證行前必備文件清單並支援列印，實際規定以各校最新官方公告為準。",
    ),
    "/tools/study-plan-checker": PageMetaSpec(
        path="/tools/study-plan-checker",
        slug="study-plan-checker",
        kind="tool",
        short_title="英文讀書計畫體檢器",
        title="交換學生英文讀書計畫（Study Plan）結構與字數體檢器｜四大要素檢查｜UniWay",
        h1="英文讀書計畫結構與字數體檢器",
        description="貼上英文或中文交換讀書計畫草稿，即時檢查字數上限、段落配置、長句可讀性與動機、目標課程對應、學術背景及返國銜接四大核心要素。",
        core_conclusion="即時統計英文讀書計畫字數、段落數與動機、課程對應、學術背景及返國規劃四大結構要素，實際格式以各校最新官方公告為準。",
    ),
    "/tools/fact-sheet-worksheet": PageMetaSpec(
        path="/tools/fact-sheet-worksheet",
        slug="fact-sheet-worksheet",
        kind="tool",
        short_title="Fact Sheet 重點整理表",
        title="海外姊妹校 Fact Sheet 互動重點整理表｜12 項必讀欄位對照與匯出｜UniWay",
        h1="姊妹校 Fact Sheet 互動重點整理表",
        description="閱讀國外大學交換簡章（Fact Sheet）時，依提名期限、單科語檢、選課限制、最低 ECTS、強制保險與住宿截止等 12 項關鍵欄位逐一填寫並匯出對照表。",
        core_conclusion="提供姊妹校簡章十二項關鍵欄位互動填寫與多校並排對照匯出，協助逐項核對門檻與期限，實際規定以各校最新官方公告為準。",
    ),
    "/tools/email-template-generator": PageMetaSpec(
        path="/tools/email-template-generator",
        slug="email-template-generator",
        kind="tool",
        short_title="推薦信與國際處信件範本",
        title="交換學生推薦信邀約與國際處詢問信範本產生器｜中英雙語一鍵複製｜UniWay",
        h1="推薦信邀約與國際處詢問信範本產生器",
        description="輸入收件師長稱謂、修課名稱、目標交換大學與截止日期，即時生成得體的中英雙語教授推薦信邀約信、禮貌提醒信及國內外國際處詢問信草稿。",
        core_conclusion="依收件稱謂、修課名稱與截止日期產生中英雙語推薦信邀約及國際處詢問信草稿，實際規定以各校最新官方公告為準。",
    ),
}

for _w3_path, _w3_spec in WAVE3_TOOL_SPECS.items():
    if not (40 <= len(_w3_spec.core_conclusion) <= 60):
        raise ValueError(f"{_w3_path} core_conclusion length {len(_w3_spec.core_conclusion)} must be 40..60")


# ---------------------------------------------------------------------------
# Region Mapping & Shared Helpers
# ---------------------------------------------------------------------------

ASIA_COUNTRIES = {
    "日本", "韓國", "大陸地區", "香港", "澳門", "新加坡", "馬來西亞", "泰國", "越南",
    "印度", "印尼", "菲律賓", "以色列", "土耳其", "阿拉伯聯合大公國", "哈薩克", "蒙古",
    "緬甸", "柬埔寨", "巴基斯坦", "烏茲別克", "約旦", "阿曼", "尼泊爾", "汶萊", "台灣",
    "孟加拉", "斯里蘭卡", "伊朗",
}
EUROPE_COUNTRIES = {
    "德國", "法國", "英國", "荷蘭", "瑞士", "瑞典", "西班牙", "義大利", "奧地利",
    "比利時", "波蘭", "捷克", "芬蘭", "丹麥", "挪威", "愛爾蘭", "葡萄牙", "匈牙利",
    "俄羅斯", "立陶宛", "拉脫維亞", "羅馬尼亞", "斯洛伐克", "冰島", "愛沙尼亞", "希臘",
    "斯洛維尼亞", "克羅埃西亞", "科索沃", "安道爾", "烏克蘭", "列支敦士登", "摩納哥",
    "賽普勒斯", "盧森堡", "阿爾巴尼亞",
}
AMERICAS_COUNTRIES = {
    "美國", "加拿大", "墨西哥", "巴西", "智利", "秘魯", "哥倫比亞", "多明尼加",
    "巴拿馬", "巴哈馬", "阿根廷", "瓜地馬拉", "哥斯大黎加", "巴拉圭", "烏拉圭",
    "安地卡及巴布達", "厄瓜多", "聖克里斯多福及尼維斯",
}
OCEANIA_COUNTRIES = {"澳洲", "紐西蘭", "巴布亞紐幾內亞", "索羅門群島", "法屬玻里尼西亞"}

REGION_OPTIONS: dict[str, str] = {
    "all": "全部地區",
    "asia": "亞洲（日・韓・星・港等）",
    "europe": "歐洲（德・法・英・荷・捷等）",
    "americas": "美洲（美國・加拿大・拉美）",
    "oceania": "大洋洲（澳洲・紐西蘭）",
}


def classify_region(country_zh: str) -> str:
    if country_zh in ASIA_COUNTRIES:
        return "asia"
    if country_zh in EUROPE_COUNTRIES:
        return "europe"
    if country_zh in AMERICAS_COUNTRIES:
        return "americas"
    if country_zh in OCEANIA_COUNTRIES:
        return "oceania"
    return "other"


def _add_two_calendar_years(d: date) -> date:
    try:
        return d.replace(year=d.year + 2)
    except ValueError:
        return date(d.year + 2, 2, 28)


def _parse_iso_date(raw: str | None, fallback: date) -> date:
    if not raw:
        return fallback
    try:
        return datetime.strptime(raw.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return fallback


# ---------------------------------------------------------------------------
# 1. Test Validity Checker Logic
# ---------------------------------------------------------------------------

EXAM_VALIDITY_SPECS: dict[str, dict[str, Any]] = {
    "toefl": {
        "label": "TOEFL iBT 托福測驗",
        "validity_years": 2,
        "delivery_note": "ETS 電子成績單約 4–8 天送達機構；紙本成績單寄送常需 2–4 週",
        "rule_note": "ETS 官方成績效期為考試日起算 2 年；逾期後系統無法調閱或加發正式成績單。",
    },
    "ielts": {
        "label": "IELTS Academic 雅思學術組",
        "validity_years": 2,
        "delivery_note": "電腦考約 3–5 天出分、紙筆考約 13 天出分；電子成績單（e-TRF）約 3–5 個工作天",
        "rule_note": "雅思官方建議效期為考試日起算 2 年；多數國內外大學要求校內收件與姊妹校網報時均未滿 2 年。",
    },
    "toeic": {
        "label": "TOEIC Listening & Reading 多益測驗",
        "validity_years": 2,
        "delivery_note": "公開測驗考後約 15 個工作天寄發成績單；急件或證書申請另需數個工作天",
        "rule_note": "ETS 成績驗證服務為考試日起算 2 年內；各大學國際處普遍規定須檢附 2 年內有效成績證明。",
    },
    "jlpt": {
        "label": "JLPT 日本語能力試驗",
        "validity_years": 0,
        "delivery_note": "每年 7 月、12 月舉辦，考後約 2 個月開放網路查分、約 2.5–3 個月寄發紙本認定書",
        "rule_note": "日本國際交流基金會核發之 JLPT 認定書本身無官方到期日，惟部分母校或日本接待校簡章會另訂「近 2 年或 3 年內應考」限制。",
    },
}


def evaluate_test_validity(
    *,
    exam: str = "toefl",
    test_date_str: str | None = None,
    home_id: str = "ntu",
    home_deadline_str: str | None = None,
    partner_deadline_str: str | None = None,
    buffer_days: int = 14,
) -> dict[str, Any]:
    if exam not in EXAM_VALIDITY_SPECS:
        exam = "toefl"
    spec = EXAM_VALIDITY_SPECS[exam]
    uni = resolve_university(home_id) or SUPPORTED_UNIVERSITIES[0]

    deadlines = build_all_71_school_deadlines()
    school_dl = next((r for r in deadlines if r["school_id"] == uni.id), deadlines[0])
    default_home_dl = date(2026, 12, 1)
    if school_dl["deadline_iso"] and school_dl["deadline_iso"] >= "2026-08-01":
        default_home_dl = _parse_iso_date(school_dl["deadline_iso"], default_home_dl)

    test_dt = _parse_iso_date(test_date_str, date(2025, 3, 15))
    home_dl = _parse_iso_date(home_deadline_str, default_home_dl)
    partner_dl = _parse_iso_date(partner_deadline_str, home_dl + timedelta(days=120))
    buf = max(0, min(60, int(buffer_days)))

    two_yr_expiry = _add_two_calendar_years(test_dt)
    order_by_date = home_dl - timedelta(days=buf)

    if spec["validity_years"] == 0:
        home_ok = test_dt <= home_dl
        partner_ok = test_dt <= partner_dl
        expiry_display = "官方證書無固定到期日"
        expiry_sub = f"2 年參考線：{two_yr_expiry.isoformat()}"
        home_status = "符合（須於收件前取得合格證書）" if home_ok else "考試日晚於校內截止日"
        partner_status = (
            f"官方無效期（距考日 {(partner_dl - test_dt).days} 天；仍請確認簡章是否限近 2 年成績）"
            if partner_ok
            else "考試日晚於提名截止日"
        )
        overall_level = "ok" if (home_ok and partner_dl <= two_yr_expiry) else "warn"
    else:
        home_days_left = (two_yr_expiry - home_dl).days
        partner_days_left = (two_yr_expiry - partner_dl).days
        home_ok = home_days_left >= 0 and test_dt <= home_dl
        partner_ok = partner_days_left >= 0 and test_dt <= partner_dl
        expiry_display = two_yr_expiry.isoformat()
        expiry_sub = f"自 {test_dt.isoformat()} 起算 2 年"
        if test_dt > home_dl:
            home_status = "來不及（考試日晚於校內收件日）"
        elif home_ok:
            home_status = f"有效（截止後尚餘 {home_days_left} 天）"
        else:
            home_status = f"已過期（早於校內截止 {-home_days_left} 天屆滿）"

        if test_dt > partner_dl:
            partner_status = "來不及（考試日晚於姊妹校截止日）"
        elif partner_ok:
            partner_status = f"有效（網報截止後尚餘 {partner_days_left} 天）"
        else:
            partner_status = f"過期風險（早於姊妹校網報 {-partner_days_left} 天失效）"

        if home_ok and partner_ok:
            overall_level = "ok"
        elif home_ok and not partner_ok:
            overall_level = "warn"
        else:
            overall_level = "bad"

    return {
        "exam": exam,
        "exam_label": spec["label"],
        "rule_note": spec["rule_note"],
        "delivery_note": spec["delivery_note"],
        "test_date": test_dt.isoformat(),
        "home_id": uni.id,
        "home_name": uni.school_name,
        "home_short_name": uni.short_name,
        "home_official_url": school_dl["source_url"] or safe_https_or_http_url(uni.official_url),
        "home_deadline": home_dl.isoformat(),
        "partner_deadline": partner_dl.isoformat(),
        "buffer_days": buf,
        "two_yr_expiry": two_yr_expiry.isoformat(),
        "expiry_display": expiry_display,
        "expiry_sub": expiry_sub,
        "order_by_date": order_by_date.isoformat(),
        "home_status": home_status,
        "partner_status": partner_status,
        "overall_level": overall_level,
    }


# ---------------------------------------------------------------------------
# 2. 30-Second Eligibility Matcher Logic
# ---------------------------------------------------------------------------

def _country_semester_twd(country_zh: str) -> int | None:
    slug = COUNTRY_SLUGS.get(country_zh, "")
    if slug in BUDGET_COUNTRY_TEMPLATES:
        calc = calculate_exchange_budget(country_key=slug)
        return int(calc["base_gross_twd"])
    return None


def match_eligibility_radar(
    home: UniversityProfile,
    partners: Sequence[PartnerUniversity],
    availability_labels: Mapping[str, str],
    *,
    test: str = "ielts",
    score: str = "6.5",
    gpa: float = 3.5,
    budget_twd: int = 0,
    region: str = "all",
    open_only: str = "all",
) -> dict[str, Any]:
    conv = convert_language_score(test, score)
    if region not in REGION_OPTIONS:
        region = "all"
    budget_cap = max(0, int(budget_twd))
    gpa_val = round(max(0.0, min(4.3, float(gpa))), 2)

    # Check home university's own documented GPA floor if available
    home_gpa_min: float | None = None
    builder = getattr(_api_mod, f"build_{home.id}_student_dashboard", None)
    if builder is not None:
        dash = builder(partner_universities=[])
        if dash.academic_gpa_minimum is not None:
            home_gpa_min = float(dash.academic_gpa_minimum)
        elif dash.selection_rules and dash.selection_rules.undergraduate_gpa_minimum is not None:
            home_gpa_min = float(dash.selection_rules.undergraduate_gpa_minimum)

    if home_gpa_min is None:
        gpa_check_label = f"輸入 GPA {gpa_val:.2f}（母校採計見簡章）"
    elif gpa_val >= home_gpa_min:
        gpa_check_label = f"達母校基準（{gpa_val:.2f} ≥ {home_gpa_min:g}）"
    else:
        gpa_check_label = f"低於母校基準（{gpa_val:.2f} < {home_gpa_min:g}）"

    grouped: dict[str, list[PartnerUniversity]] = {}
    for p in partners:
        grouped.setdefault(partner_group_id(p), []).append(p)

    user_cefr_rank = CEFR_RANK.get(conv["cefr_code"], 0)
    direct_hits: list[dict[str, Any]] = []
    equiv_hits: list[dict[str, Any]] = []
    region_stats: dict[str, dict[str, int]] = {
        k: {"total": 0, "direct": 0, "equiv": 0, "open": 0}
        for k in ("asia", "europe", "americas", "oceania", "other")
    }
    scoped_total = 0

    for pid, rows in grouped.items():
        primary = rows[0]
        c_zh = canonical_country(primary.country) or (primary.country or "國家待確認").strip()
        reg_key = classify_region(c_zh)
        if region != "all" and reg_key != region:
            continue
        is_open = any(r.availability_status == "open" for r in rows)
        if open_only == "open" and not is_open:
            continue

        est_twd = _country_semester_twd(c_zh)
        if budget_cap > 0 and est_twd is not None and est_twd > budget_cap:
            continue

        scoped_total += 1
        region_stats[reg_key]["total"] += 1
        if is_open:
            region_stats[reg_key]["open"] += 1

        parsed = extract_partner_language_thresholds(rows)
        status_label = availability_labels.get(primary.availability_status, primary.availability_status)
        budget_tag = f"預估約 NT$ {est_twd:,}／學期" if est_twd is not None else "預算依接待校公告"

        item_base = {
            "pid": pid,
            "school_name": primary.school_name,
            "country": c_zh,
            "region": reg_key,
            "availability": status_label,
            "is_open": is_open,
            "budget_tag": budget_tag,
            "partner_url": f"/schools/{home.id}/partners/{pid}",
            "compare_url": f"/tools/partner-compare?{urlencode({'home': home.id, 'p1': pid})}",
        }

        if conv["is_japanese"]:
            req_jlpt = parsed["jlpt_min"]
            if req_jlpt is not None and conv["jlpt_rank"] >= JLPT_LEVEL_INFO[req_jlpt]["rank"]:
                item_base["matched_rule"] = f"明確列載 JLPT {req_jlpt}"
                direct_hits.append(item_base)
                region_stats[reg_key]["direct"] += 1
            continue

        t_code = conv["test"]
        direct_req: str | None = None
        direct_pass: bool | None = None
        if t_code == "ielts" and parsed["ielts_min"] is not None:
            direct_req = f"IELTS {parsed['ielts_min']:g}"
            direct_pass = float(conv["numeric_ielts"]) >= parsed["ielts_min"]
        elif t_code == "toefl" and parsed["toefl_min"] is not None:
            direct_req = f"TOEFL {parsed['toefl_min']:g}"
            direct_pass = float(conv["numeric_toefl"]) >= parsed["toefl_min"]
        elif t_code == "toeic" and parsed["toeic_min"] is not None:
            direct_req = f"TOEIC {parsed['toeic_min']:g}"
            direct_pass = float(conv["numeric_toeic"]) >= parsed["toeic_min"]
        elif t_code == "cefr" and parsed["cefr_min"] is not None:
            direct_req = f"CEFR {parsed['cefr_min']}"
            direct_pass = user_cefr_rank >= CEFR_RANK[parsed["cefr_min"]]

        if direct_pass is True:
            item_base["matched_rule"] = f"明確列載 {direct_req}"
            direct_hits.append(item_base)
            region_stats[reg_key]["direct"] += 1
        elif direct_pass is None:
            eq_passes: list[str] = []
            if parsed["cefr_min"] is not None and user_cefr_rank >= CEFR_RANK[parsed["cefr_min"]]:
                eq_passes.append(f"CEFR {parsed['cefr_min']}")
            if parsed["ielts_min"] is not None and float(conv["numeric_ielts"]) >= parsed["ielts_min"]:
                eq_passes.append(f"IELTS {parsed['ielts_min']:g}")
            if parsed["toefl_min"] is not None and float(conv["numeric_toefl"]) >= parsed["toefl_min"]:
                eq_passes.append(f"TOEFL {parsed['toefl_min']:g}")
            if parsed["toeic_min"] is not None and float(conv["numeric_toeic"]) >= parsed["toeic_min"]:
                eq_passes.append(f"TOEIC {parsed['toeic_min']:g}")
            if eq_passes:
                item_base["matched_rule"] = f"同級英檢參考（{'／'.join(eq_passes[:2])}）"
                equiv_hits.append(item_base)
                region_stats[reg_key]["equiv"] += 1

    direct_hits.sort(key=lambda x: (0 if x["is_open"] else 1, x["country"], x["school_name"]))
    equiv_hits.sort(key=lambda x: (0 if x["is_open"] else 1, x["country"], x["school_name"]))

    return {
        "home_id": home.id,
        "home_name": home.school_name,
        "home_short_name": home.short_name,
        "home_school_url": f"/schools/{home.id}",
        "conversion": conv,
        "gpa": gpa_val,
        "gpa_check_label": gpa_check_label,
        "budget_twd": budget_cap,
        "region": region,
        "open_only": open_only,
        "scoped_total": scoped_total,
        "direct_count": len(direct_hits),
        "equiv_count": len(equiv_hits),
        "direct_samples": direct_hits[:18],
        "equiv_samples": equiv_hits[:9],
        "region_stats": region_stats,
    }


# ---------------------------------------------------------------------------
# 3. Reverse Partner Search Logic
# ---------------------------------------------------------------------------

def search_reverse_partners(
    entities: Mapping[Any, Any],
    availability_labels: Mapping[str, str],
    *,
    q: str = "早稻田",
    country: str = "all",
    limit: int = 12,
) -> dict[str, Any]:
    country_counter: Counter[tuple[str, str]] = Counter()
    for ent in entities.values():
        country_counter[(ent.country_slug, ent.country_name_zh)] += 1
    country_options = [
        {"slug": s, "name": z, "count": c}
        for (s, z), c in sorted(country_counter.items(), key=lambda item: (-item[1], item[0][0]))
    ]
    valid_slugs = {c["slug"] for c in country_options}
    active_country = country if country in valid_slugs else "all"
    q_clean = q.strip()
    q_low = q_clean.casefold()

    matched_entities = []
    for ent in entities.values():
        if active_country != "all" and ent.country_slug != active_country:
            continue
        if q_low:
            raw_names = " ".join(
                rows[0].school_name for rows in ent.home_rows.values() if rows
            )
            haystack = f"{ent.school_name_zh} {ent.school_name_en} {ent.institution_slug} {ent.country_name_zh} {raw_names}".casefold()
            if q_low not in haystack:
                continue
        matched_entities.append(ent)

    matched_entities.sort(
        key=lambda e: (
            -len(e.home_rows),
            -sum(1 for rows in e.home_rows.values() if any(r.availability_status == "open" for r in rows)),
            e.country_slug,
            e.institution_slug,
        )
    )

    results: list[dict[str, Any]] = []
    for ent in matched_entities[:limit]:
        agreements: list[dict[str, Any]] = []
        open_homes = 0
        for u in SUPPORTED_UNIVERSITIES:
            rows = ent.home_rows.get(u.id)
            if not rows:
                continue
            is_open = any(r.availability_status == "open" for r in rows)
            if is_open:
                open_homes += 1
            parsed = extract_partner_language_thresholds(rows)
            badges = []
            if parsed["ielts_min"] is not None:
                badges.append(f"IELTS {parsed['ielts_min']:g}")
            if parsed["toefl_min"] is not None:
                badges.append(f"TOEFL {parsed['toefl_min']:g}")
            if parsed["toeic_min"] is not None:
                badges.append(f"TOEIC {parsed['toeic_min']:g}")
            if parsed["cefr_min"] is not None:
                badges.append(f"CEFR {parsed['cefr_min']}")
            if parsed["jlpt_min"] is not None:
                badges.append(f"JLPT {parsed['jlpt_min']}")
            quota_txt = "；".join(dict.fromkeys(r.quota.strip() for r in rows if r.quota and r.quota.strip())) or "依當期簡章"
            status_txt = availability_labels.get(rows[0].availability_status, rows[0].availability_status)
            agreements.append({
                "home_id": u.id,
                "home_name": u.school_name,
                "short_name": u.short_name,
                "status": status_txt,
                "is_open": is_open,
                "quota": quota_txt[:48],
                "language": " ／ ".join(badges) if badges else "依簡章確認",
                "partner_url": f"/schools/{u.id}/partners/{partner_group_id(rows[0])}",
                "source_url": safe_https_or_http_url(rows[0].source_url) or safe_https_or_http_url(u.official_url) or "",
            })
        results.append({
            "display_title": ent.display_title,
            "school_name_zh": ent.school_name_zh,
            "school_name_en": ent.school_name_en,
            "country_zh": ent.country_name_zh,
            "country_slug": ent.country_slug,
            "canonical_path": ent.canonical_path,
            "contracted_count": len(agreements),
            "open_home_count": open_homes,
            "agreements": agreements,
        })

    return {
        "q": q_clean,
        "country": active_country,
        "matched_total": len(matched_entities),
        "country_options": country_options,
        "results": results,
    }


# ---------------------------------------------------------------------------
# 4. Preference Ranker Logic
# ---------------------------------------------------------------------------

TIER_LABELS: dict[str, str] = {
    "dream": "夢幻衝刺",
    "target": "穩健落點",
    "safety": "保底安心",
}


def evaluate_preference_portfolio(
    home_id: str,
    partners: Sequence[PartnerUniversity],
    availability_labels: Mapping[str, str],
    *,
    slots: Sequence[tuple[str | None, str | None]] = (),
) -> dict[str, Any]:
    home = resolve_university(home_id) or SUPPORTED_UNIVERSITIES[0]
    max_prefs: int | None = None
    builder = getattr(_api_mod, f"build_{home.id}_student_dashboard", None)
    if builder is not None:
        dash = builder(partner_universities=[])
        max_prefs = dash.maximum_preferences

    grouped: dict[str, list[PartnerUniversity]] = {}
    for p in partners:
        grouped.setdefault(partner_group_id(p), []).append(p)

    ordered_pids = sorted(
        grouped.keys(),
        key=lambda k: (
            0 if any(r.availability_status == "open" for r in grouped[k]) else 1,
            canonical_country(grouped[k][0].country) or grouped[k][0].country or "",
            grouped[k][0].school_name,
        ),
    )

    catalog_map: dict[str, dict[str, Any]] = {}
    for pid in ordered_pids:
        rows = grouped[pid]
        primary = rows[0]
        c_zh = canonical_country(primary.country) or (primary.country or "海外").strip()
        parsed = extract_partner_language_thresholds(rows)
        badges = []
        if parsed["ielts_min"] is not None:
            badges.append(f"IELTS {parsed['ielts_min']:g}")
        if parsed["toefl_min"] is not None:
            badges.append(f"TOEFL {parsed['toefl_min']:g}")
        if parsed["toeic_min"] is not None:
            badges.append(f"TOEIC {parsed['toeic_min']:g}")
        if parsed["jlpt_min"] is not None:
            badges.append(f"JLPT {parsed['jlpt_min']}")
        high_gate = bool(
            (parsed["ielts_min"] and parsed["ielts_min"] >= 7.0)
            or (parsed["toefl_min"] and parsed["toefl_min"] >= 95)
            or parsed["jlpt_min"] == "N1"
        )
        raw_status = primary.availability_status
        quota_txt = "；".join(dict.fromkeys(r.quota.strip() for r in rows if r.quota and r.quota.strip())) or "未單獨列載"
        catalog_map[pid] = {
            "pid": pid,
            "school_name": primary.school_name,
            "country": c_zh,
            "label": f"[{c_zh}] {primary.school_name}",
            "status_code": raw_status,
            "status_label": availability_labels.get(raw_status, raw_status),
            "quota": quota_txt[:42],
            "language": " ／ ".join(badges) if badges else "依簡章確認",
            "high_gate": high_gate,
            "partner_url": f"/schools/{home.id}/partners/{pid}",
        }

    default_tiers = ["dream", "target", "target", "safety", ""]
    default_pids = ordered_pids[:4] + [""]
    chosen_rows: list[dict[str, Any]] = []
    used_pids: set[str] = set()

    for idx in range(5):
        req_pid, req_tier = slots[idx] if idx < len(slots) else (None, None)
        tier = req_tier if req_tier in TIER_LABELS else (default_tiers[idx] or "target")
        if req_pid is not None:
            pid = req_pid if req_pid in catalog_map else ""
        else:
            pid = default_pids[idx] if idx < len(default_pids) else ""
        if pid and pid in used_pids:
            pid = ""
        if pid:
            used_pids.add(pid)
            info = dict(catalog_map[pid])
            info["rank"] = len(chosen_rows) + 1
            info["slot_index"] = idx + 1
            info["tier"] = tier
            info["tier_label"] = TIER_LABELS[tier]
            chosen_rows.append(info)

    alerts: list[dict[str, str]] = []
    inactive_codes = {"zero_quota", "not_open", "closed", "agreement_only", "departmental_reference"}
    bad_slots = [r for r in chosen_rows if r["status_code"] in inactive_codes]
    if bad_slots:
        names = "、".join(f"第 {r['rank']} 志願 {r['school_name']}（{r['status_label']}）" for r in bad_slots)
        alerts.append({"level": "warn", "text": f"注意非當期開放或零名額志願：{names}，送出前務必確認當期簡章是否受理。"})

    tier_counts = Counter(r["tier"] for r in chosen_rows)
    if chosen_rows and tier_counts["safety"] == 0:
        alerts.append({"level": "warn", "text": "目前組合缺少「保底安心」志願，若前段熱門校競爭集中，可能有落榜風險。"})

    tier_order_weight = {"dream": 0, "target": 1, "safety": 2}
    inverted = False
    for i in range(len(chosen_rows) - 1):
        if tier_order_weight[chosen_rows[i]["tier"]] > tier_order_weight[chosen_rows[i + 1]["tier"]]:
            inverted = True
            break
    if inverted:
        alerts.append({"level": "warn", "text": "偵測到「志願倒掛」：保底或落點志願排在夢幻志願之前，分發時一旦前序錄取將不會往下分發。"})

    top2_pending = [
        r for r in chosen_rows[:2]
        if r["status_code"] in {"needs_confirmation", "quota_unconfirmed"}
    ]
    if len(chosen_rows) >= 2 and len(top2_pending) == 2:
        alerts.append({"level": "warn", "text": "前兩志願之當期名額狀態均為「待確認」，建議至少搭配一所已明確列載開缺之合作校。"})

    if not alerts and chosen_rows:
        alerts.append({"level": "ok", "text": "志願序層級由夢幻→落點→保底遞進，且已納入保底選項，結構穩健！"})

    return {
        "home_id": home.id,
        "home_name": home.school_name,
        "home_short_name": home.short_name,
        "max_preferences": max_prefs,
        "options": list(catalog_map.values()),
        "chosen": chosen_rows,
        "tier_counts": dict(tier_counts),
        "alerts": alerts,
    }


# ---------------------------------------------------------------------------
# 5. Multi-Tranche FX Budget & Gap Calculator Logic
# ---------------------------------------------------------------------------

FX_CURRENCIES: dict[str, dict[str, Any]] = {
    "JPY": {"name": "日圓 JPY", "default_target": 625000, "b1": (200000, 0.218), "b2": (150000, 0.211)},
    "EUR": {"name": "歐元 EUR", "default_target": 5200, "b1": (1500, 35.4), "b2": (1000, 34.9)},
    "USD": {"name": "美元 USD", "default_target": 9200, "b1": (3000, 32.1), "b2": (2000, 31.8)},
    "KRW": {"name": "韓元 KRW", "default_target": 4800000, "b1": (1500000, 0.0242), "b2": (1000000, 0.0236)},
    "GBP": {"name": "英鎊 GBP", "default_target": 5850, "b1": (2000, 41.5), "b2": (1000, 40.9)},
    "AUD": {"name": "澳幣 AUD", "default_target": 10900, "b1": (3000, 21.4), "b2": (2000, 21.0)},
    "CAD": {"name": "加幣 CAD", "default_target": 9450, "b1": (3000, 23.6), "b2": (2000, 23.2)},
    "SGD": {"name": "新幣 SGD", "default_target": 8150, "b1": (2500, 24.3), "b2": (1500, 24.0)},
    "CZK": {"name": "捷克克朗 CZK", "default_target": 88000, "b1": (30000, 1.40), "b2": (20000, 1.38)},
}


def calculate_fx_tranches(
    *,
    currency: str = "JPY",
    target_foreign: float | None = None,
    tranches: Sequence[tuple[float, float]] | None = None,
    spot_rate: float | None = None,
) -> dict[str, Any]:
    cur = currency.strip().upper()
    if cur not in FX_CURRENCIES:
        cur = "JPY"
    meta = FX_CURRENCIES[cur]
    fx_bundle = fx_reference()
    bundled_rate = float(fx_bundle.get("rates", {}).get(cur, meta["b2"][1]))

    target = max(0.0, float(target_foreign if target_foreign is not None else meta["default_target"]))
    spot = float(spot_rate) if (spot_rate is not None and spot_rate > 0) else bundled_rate

    if tranches is None:
        raw_tranches = [meta["b1"], meta["b2"], (0.0, 0.0)]
    else:
        raw_tranches = list(tranches)
        while len(raw_tranches) < 3:
            raw_tranches.append((0.0, 0.0))

    clean_tranches: list[dict[str, float]] = []
    bought_foreign = 0.0
    spent_twd = 0.0
    for amt, rt in raw_tranches[:5]:
        a = max(0.0, float(amt))
        r = max(0.0, float(rt))
        cost = round(a * r) if (a > 0 and r > 0) else 0
        if a > 0 and r > 0:
            bought_foreign += a
            spent_twd += a * r
        clean_tranches.append({"amount": a, "rate": r, "twd": cost})

    avg_bought_rate = (spent_twd / bought_foreign) if bought_foreign > 0 else 0.0
    gap_foreign = max(0.0, target - bought_foreign)
    progress_pct = min(100.0, (bought_foreign / target * 100.0) if target > 0 else 100.0)

    scenarios = []
    for label, factor in (
        ("匯率回落 -5%（分批逢低買進）", 0.95),
        ("目前參考現價（0%）", 1.00),
        ("外幣升值 +5%", 1.05),
        ("外幣急升 +10%（壓力測試）", 1.10),
    ):
        sr = spot * factor
        gap_twd = round(gap_foreign * sr)
        total_twd = round(spent_twd + gap_foreign * sr)
        eff_denom = max(target, bought_foreign)
        blended = (total_twd / eff_denom) if eff_denom > 0 else sr
        scenarios.append({
            "label": label,
            "factor": factor,
            "rate": round(sr, 4),
            "gap_twd": gap_twd,
            "total_twd": total_twd,
            "blended_rate": round(blended, 4),
        })

    base_sc = scenarios[1]
    for sc in scenarios:
        sc["delta_twd"] = sc["total_twd"] - base_sc["total_twd"]

    return {
        "currency": cur,
        "currency_label": meta["name"],
        "bundled_rate": round(bundled_rate, 4),
        "fx_date": str(fx_bundle.get("fetched_at", ""))[:10] or "2026-10-02",
        "target_foreign": target,
        "spot_rate": round(spot, 4),
        "tranches": clean_tranches,
        "bought_foreign": bought_foreign,
        "spent_twd": round(spent_twd),
        "avg_bought_rate": round(avg_bought_rate, 4),
        "gap_foreign": gap_foreign,
        "progress_pct": round(progress_pct, 1),
        "base_gap_twd": base_sc["gap_twd"],
        "base_total_twd": base_sc["total_twd"],
        "base_blended_rate": base_sc["blended_rate"],
        "scenarios": scenarios,
    }


# ---------------------------------------------------------------------------
# 6. Overseas Deadline Timezone & DST Converter Logic
# ---------------------------------------------------------------------------

TIMEZONE_CATALOG: dict[str, dict[str, str]] = {
    "Europe/Berlin": {
        "label": "中歐時間 CET/CEST（德國・法國・荷蘭・西班牙・捷克・瑞典）",
        "region_note": "3 月最後週日至 10 月最後週日實施夏令時間（UTC+2），冬季為 UTC+1。",
    },
    "Europe/London": {
        "label": "英國／愛爾蘭時間 GMT/BST（倫敦・愛丁堡・都柏林）",
        "region_note": "夏季為英國夏令時間 BST（UTC+1），冬季回歸格林威治標準時間 GMT（UTC+0）。",
    },
    "Europe/Helsinki": {
        "label": "東歐時間 EET/EEST（芬蘭・愛沙尼亞・立陶宛・希臘）",
        "region_note": "夏季為 UTC+3（與台灣差 5 小時），冬季為 UTC+2（與台灣差 6 小時）。",
    },
    "America/New_York": {
        "label": "北美東部時間 ET（紐約・波士頓・華盛頓・多倫多）",
        "region_note": "3 月第 2 個週日至 11 月第 1 個週日實施夏令時間 EDT（UTC-4），冬季為 EST（UTC-5）。",
    },
    "America/Chicago": {
        "label": "北美中部時間 CT（芝加哥・德州奧斯汀・明尼蘇達）",
        "region_note": "夏季為 CDT（UTC-5，慢台灣 13 小時），冬季為 CST（UTC-6，慢台灣 14 小時）。",
    },
    "America/Los_Angeles": {
        "label": "北美太平洋時間 PT（加州 UC 各校・西雅圖・溫哥華）",
        "region_note": "夏季為 PDT（UTC-7，慢台灣 15 小時），冬季為 PST（UTC-8，慢台灣 16 小時）。",
    },
    "Asia/Tokyo": {
        "label": "日本／韓國標準時間 JST/KST（東京・大阪・首爾・釜山）",
        "region_note": "全年固定 UTC+9（無夏令時間），比台灣快 1 小時！日本 23:59 等於台灣當晚 22:59。",
    },
    "Asia/Singapore": {
        "label": "新加坡／香港／馬來西亞時間 SGT/HKT",
        "region_note": "全年固定 UTC+8，與台灣時間零時差。",
    },
    "Australia/Sydney": {
        "label": "澳洲東部時間 AEST/AEDT（雪梨・墨爾本・坎培拉）",
        "region_note": "南半球 10 月至隔年 4 月實施夏令時間 AEDT（UTC+11，快台灣 3 小時），4–10 月為 UTC+10。",
    },
    "UTC": {
        "label": "國際協調時間 UTC（部分歐盟或跨國線上系統統一標準）",
        "region_note": "全年固定 UTC+0，台灣時間固定為 UTC + 8 小時。",
    },
}


def convert_deadline_timezone(
    *,
    tz_name: str = "Europe/Berlin",
    date_str: str | None = None,
    time_str: str | None = None,
) -> dict[str, Any]:
    if tz_name not in TIMEZONE_CATALOG:
        tz_name = "Europe/Berlin"
    d = _parse_iso_date(date_str, date(2027, 4, 15))
    t_raw = (time_str or "23:59").strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", t_raw)
    hh = min(23, max(0, int(m.group(1)))) if m else 23
    mm = min(59, max(0, int(m.group(2)))) if m else 59

    src_tz = ZoneInfo(tz_name)
    local_dt = datetime(d.year, d.month, d.day, hh, mm, tzinfo=src_tz)
    taipei_dt = local_dt.astimezone(TAIPEI_TZ)
    safe_dt = taipei_dt - timedelta(hours=24)

    dst_delta = local_dt.dst() or timedelta(0)
    is_dst = dst_delta.total_seconds() > 0
    utc_offset_hours = (local_dt.utcoffset() or timedelta(0)).total_seconds() / 3600.0
    diff_vs_taipei = utc_offset_hours - 8.0

    if abs(diff_vs_taipei) < 0.01:
        diff_label = "與台灣零時差（UTC+8）"
    elif diff_vs_taipei > 0:
        diff_label = f"比台灣快 {diff_vs_taipei:g} 小時（注意提早截止！）"
    else:
        diff_label = f"比台灣慢 {-diff_vs_taipei:g} 小時"

    utc_sign = "+" if utc_offset_hours >= 0 else ""
    return {
        "tz_name": tz_name,
        "tz_label": TIMEZONE_CATALOG[tz_name]["label"],
        "region_note": TIMEZONE_CATALOG[tz_name]["region_note"],
        "date_str": d.isoformat(),
        "time_str": f"{hh:02d}:{mm:02d}",
        "local_display": f"{d.isoformat()} {hh:02d}:{mm:02d} ({local_dt.tzname() or tz_name}, UTC{utc_sign}{utc_offset_hours:g})",
        "taipei_display": taipei_dt.strftime("%Y-%m-%d %H:%M"),
        "taipei_weekday": ("週一", "週二", "週三", "週四", "週五", "週六", "週日")[taipei_dt.weekday()],
        "safe_submit_display": safe_dt.strftime("%Y-%m-%d %H:%M"),
        "is_dst": is_dst,
        "dst_badge": "夏令時間（DST 實施中）" if is_dst else "標準冬令／常規時間",
        "diff_label": diff_label,
    }


# ---------------------------------------------------------------------------
# 7. Application & Pre-Departure Checklist Catalog
# ---------------------------------------------------------------------------

CHECKLIST_COUNTRIES: dict[str, str] = {
    "japan": "日本",
    "south-korea": "韓國",
    "germany": "德國",
    "france": "法國",
    "united-kingdom": "英國",
    "united-states": "美國",
    "netherlands": "荷蘭",
    "czechia": "捷克",
    "general": "其他國家通用",
}

CHECKLIST_STAGES: dict[str, str] = {
    "all": "全部階段（校內甄選 → 姊妹校網報 → 簽證行前）",
    "internal": "第一階段：母校校內甄選送件",
    "nomination": "第二階段：獲提名後姊妹校網報",
    "predeparture": "第三階段：簽證・住宿・保險與行前",
}

BASE_CHECKLIST_ITEMS: tuple[dict[str, Any], ...] = (
    {"id": "c-passport", "stage": "internal", "stage_label": "校內甄選", "title": "確認護照效期與英文姓名拼音", "spec": "效期建議涵蓋預計返國日後 6 個月以上，英文成績單與檢定拼音須與護照一致", "timing": "報名前 2 個月"},
    {"id": "c-lang", "stage": "internal", "stage_label": "校內甄選", "title": "有效期限內之語言檢定成績單正本掃描檔", "spec": "確認總分與聽說讀寫單科皆達標，且校內截止與姊妹校網報時均在 2 年效期內", "timing": "校內截止前 1 個月"},
    {"id": "c-transcript", "stage": "internal", "stage_label": "校內甄選", "title": "歷年中、英文成績單（含 GPA 與班／系排名證明）", "spec": "向教務處申請最新正式版，確認是否須附名次證明與分數換算說明頁", "timing": "校內截止前 2 週"},
    {"id": "c-studyplan", "stage": "internal", "stage_label": "校內甄選", "title": "中／外文讀書計畫（Study Plan）與履歷表（CV）", "spec": "依母校字數或頁數規定撰寫申請動機、擬修課對應與返國學分規劃", "timing": "校內截止前 2–3 週"},
    {"id": "c-rec", "stage": "internal", "stage_label": "校內甄選", "title": "師長推薦信（依母校規定封緘紙本或線上填寫）", "spec": "至少提前 4–6 週禮貌邀約授課教授或導師，附上成績單與志願校方向", "timing": "校內截止前 4–6 週"},
    {"id": "c-stamps", "stage": "internal", "stage_label": "校內甄選", "title": "校內線上報名表列印親簽、家長同意書與系所核章", "spec": "部分系所要求系辦先行審核或系主任簽章，切勿壓線當日才跑流程", "timing": "校內截止前 5–7 天"},
    {"id": "c-factsheet", "stage": "nomination", "stage_label": "姊妹校網報", "title": "詳閱錄取姊妹校最新年度 Fact Sheet 與網報信件", "spec": "獲母校提名（Nomination）後留意垃圾郵件匣，記下網報與宿舍獨立截止時刻", "timing": "獲提名後立即確認"},
    {"id": "c-courses", "stage": "nomination", "stage_label": "姊妹校網報", "title": "擬選修課程清單／Learning Agreement 與母校抵免預審", "spec": "核對接待校最低修課學分／ECTS 要求，並先向母校系辦確認學分採認原則", "timing": "姊妹校網報期間"},
    {"id": "c-bank", "stage": "nomination", "stage_label": "姊妹校網報", "title": "英文存款餘額證明（Financial Statement）", "spec": "確認幣別、最低金額門檻與開立日期限制；若使用父母帳戶須附英文資助聲明", "timing": "網報截止前 2 週"},
    {"id": "c-housing", "stage": "predeparture", "stage_label": "簽證行前", "title": "完成校內宿舍申請或校外合規租屋簽約", "spec": "部分國家宿位採先到先得或獨立平台登記，切勿等拿到簽證才找房", "timing": "出發前 3–4 個月"},
    {"id": "c-loa-visa", "stage": "predeparture", "stage_label": "簽證行前", "title": "收到正式入學許可（LoA）並預約辦理交換學生簽證", "spec": "核對 LoA 上姓名、生日與交換起迄日無誤後，立即預約駐台辦事處或簽證中心", "timing": "出發前 2–3 個月"},
    {"id": "c-insure", "stage": "predeparture", "stage_label": "簽證行前", "title": "辦理海外醫療／意外保險與母校註冊選課確認", "spec": "確認是否強制投保接待校／當地法定學生醫保，並維持交換期間台灣母校在學註冊", "timing": "出發前 1 個月"},
)

COUNTRY_SPECIFIC_ITEMS: dict[str, tuple[dict[str, str], ...]] = {
    "japan": (
        {"id": "jp-coe", "stage": "nomination", "stage_label": "姊妹校網報", "title": "提交在留資格認定證明書（CoE）代辦文件與證件照", "spec": "依日方大學指定規格準備照片電子檔、經費支付書與存摺證明以利申請 CoE", "timing": "出發前 3–4 個月"},
        {"id": "jp-visa", "stage": "predeparture", "stage_label": "簽證行前", "title": "持 CoE 至日本台灣交流協會申辦留學簽證", "spec": "收到電子或紙本 CoE 後備齊護照、申請書與身分證正影本送件", "timing": "收到 CoE 後儘速"},
    ),
    "south-korea": (
        {"id": "kr-apostille", "stage": "nomination", "stage_label": "姊妹校網報", "title": "確認英文在學／成績證明是否須辦理公證或駐外驗證", "spec": "部分韓國大學要求入學包裹附經驗證之在學證明與肺結核檢查報告", "timing": "網報前確認"},
        {"id": "kr-d2", "stage": "predeparture", "stage_label": "簽證行前", "title": "持標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換簽證", "spec": "並留意入境韓國後外國人登錄證（ARC）與國民健康保險（NHIS）納保規定", "timing": "出發前 1–2 個月"},
    ),
    "germany": (
        {"id": "de-blocked", "stage": "predeparture", "stage_label": "簽證行前", "title": "開立德國限制提領帳戶（Blocked Account / Sperrkonto）並匯款", "spec": "依德國在台協會最新公告之每月最低生活費標準乘以停留月數辦理財力證明", "timing": "簽證面談前 3–4 週"},
        {"id": "de-tk", "stage": "predeparture", "stage_label": "簽證行前", "title": "申請德國公立學生健康保險證明與預約德國在台協會長期簽證", "spec": "德簽預約名額旺季極為熱門，建議獲母校提名後即密切關注預約時段", "timing": "出發前 2.5–3 個月"},
    ),
    "france": (
        {"id": "fr-eef", "stage": "predeparture", "stage_label": "簽證行前", "title": "完成法國教育中心（Campus France）線上程序與預簽證審核", "spec": "赴法交換生須先通過法國教育中心程序（確認是否免面試條件）再遞交法國簽證", "timing": "收到 LoA 後立即辦理"},
    ),
    "united-kingdom": (
        {"id": "uk-route", "stage": "predeparture", "stage_label": "簽證行前", "title": "確認一學期（6 個月內）Visitor 規定或全學年 Student Visa（CAS＋IHS）", "spec": "交換未滿 6 個月與全學年超過 6 個月之簽證類別、CAS 號碼與醫療附加費完全不同", "timing": "出發前 2–3 個月"},
    ),
    "united-states": (
        {"id": "us-ds2019", "stage": "predeparture", "stage_label": "簽證行前", "title": "核對 DS-2019 表格、繳納 SEVIS I-901 費用並預約 AIT J-1 簽證面談", "spec": "同步檢視美國接待校強制疫苗接種紀錄表（Immunization Form）與校方醫療保險 Waiver 條件", "timing": "出發前 2–3 個月"},
    ),
    "netherlands": (
        {"id": "nl-mvv", "stage": "predeparture", "stage_label": "簽證行前", "title": "配合荷蘭接待校代辦 MVV／VVR 居留程序並第一時間登記學生住宿", "spec": "荷蘭由接待大學統一向移民局（IND）送件，且學生宿位極為緊俏務必準時搶登", "timing": "獲提名後立即追蹤"},
    ),
    "czechia": (
        {"id": "cz-criminal", "stage": "predeparture", "stage_label": "簽證行前", "title": "提早準備良民證／存款證明翻譯認證並預約捷克經濟文化辦事處簽證", "spec": "捷克長期簽證／居留法定審核期較長（常需 60 天以上），務必盡早備齊公證認證文件", "timing": "出發前 3–4 個月"},
    ),
}

MILITARY_EXTRA_ITEM = {
    "id": "mil-approval",
    "stage": "predeparture",
    "stage_label": "簽證行前",
    "title": "【在學役男必辦】持國外入學許可（LoA）向母校辦理推薦出國交換專案核准",
    "spec": "超過 4 個月不得用線上短期出境替代；須於出國前 30–45 天由母校造冊函報縣市政府核准並列印核准單",
    "timing": "出發前 30–45 天",
}


def build_application_checklist(
    *,
    country: str = "japan",
    stage: str = "all",
    military: str = "no",
) -> dict[str, Any]:
    if country not in CHECKLIST_COUNTRIES:
        country = "japan"
    if stage not in CHECKLIST_STAGES:
        stage = "all"
    is_mil = military == "yes"

    items = [dict(x) for x in BASE_CHECKLIST_ITEMS]
    for extra in COUNTRY_SPECIFIC_ITEMS.get(country, ()):
        items.append(dict(extra))
    if is_mil:
        items.append(dict(MILITARY_EXTRA_ITEM))

    stage_rank = {"internal": 0, "nomination": 1, "predeparture": 2}
    items.sort(key=lambda x: stage_rank.get(x["stage"], 9))
    if stage != "all":
        items = [x for x in items if x["stage"] == stage]

    return {
        "country": country,
        "country_label": CHECKLIST_COUNTRIES[country],
        "stage": stage,
        "stage_label": CHECKLIST_STAGES[stage],
        "military": "yes" if is_mil else "no",
        "items": items,
        "total_count": len(items),
    }


# ---------------------------------------------------------------------------
# 8. Study Plan Structure & Word-Count Checker Logic
# ---------------------------------------------------------------------------

DEFAULT_SAMPLE_STUDY_PLAN = (
    "Applying for the Fall 2027 student exchange program at Technical University of Munich (TUM) aligns directly "
    "with my junior-year specialization in embedded systems and sustainable computing.\n\n"
    "During my first five semesters at my home university, I completed core coursework in Data Structures, "
    "Computer Architecture, and Operating Systems, and contributed to an undergraduate research project on low-power edge sensors.\n\n"
    "At TUM, I plan to enroll in three English-taught modules offered by the School of Computation, Information and Technology, "
    "including Hardware/Software Co-Design and Autonomous Systems, totaling approximately 24 ECTS credits.\n\n"
    "Upon returning to Taiwan for my senior year, I will transfer the approved elective credits toward my degree requirements "
    "and integrate the laboratory methodologies into my capstone thesis."
)

STUDY_PLAN_DIMENSIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "motivation",
        "title": "申請動機與目標校契合度（Motivation & Academic Fit）",
        "keywords": ("exchange", "program", "university", "why", "align", "goal", "interest", "academic", "動機", "目標", "申請", "選擇", "交換"),
        "advice": "具體點出「為何是這所姊妹校的特定學系或資源」，避免套用任何學校都能放的空泛讚美。",
    },
    {
        "id": "courses",
        "title": "具體擬修課程與學分規劃（Course Mapping & Credits）",
        "keywords": ("course", "module", "curriculum", "ects", "credit", "seminar", "lecture", "syllabus", "school of", "faculty", "課程", "修習", "學分", "課綱", "選修"),
        "advice": "建議列出 2 至 4 門查詢過課綱（Syllabus）的真實課程名稱與預估修習學分數（如 24 ECTS）。",
    },
    {
        "id": "readiness",
        "title": "個人修課基礎與專題準備（Academic Background）",
        "keywords": ("completed", "project", "research", "coursework", "major", "background", "skill", "laboratory", "experience", "基礎", "專題", "修過", "背景", "研究"),
        "advice": "說明你在母校已修畢哪些先修課或專題經驗，證明具備跟上全外語專業課程的實力。",
    },
    {
        "id": "return_plan",
        "title": "返國學分銜接與未來發展（Post-Exchange Plan）",
        "keywords": ("return", "transfer", "thesis", "capstone", "career", "future", "graduate", "senior", "contribute", "返國", "抵免", "畢業", "未來", "論文", "職涯"),
        "advice": "交代返台後的學分採認、畢業專題或研究所／職涯連結，展現完整學習閉環。",
    },
)


def analyze_study_plan(raw_text: str, target_words: int = 800) -> dict[str, Any]:
    target = max(200, min(2500, int(target_words)))
    txt = (raw_text or "").strip()
    using_sample = False
    if not txt:
        txt = DEFAULT_SAMPLE_STUDY_PLAN
        using_sample = True

    en_words = re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", txt)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", txt)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", txt) if p.strip()]
    if len(paragraphs) == 1 and "\n" in txt:
        paragraphs = [p.strip() for p in txt.splitlines() if p.strip()]

    sentences = [s.strip() for s in re.split(r"[.!?。！？]+", txt) if s.strip()]
    word_count = len(en_words)
    cjk_count = len(cjk_chars)
    effective_units = word_count if word_count >= cjk_count else cjk_count
    avg_sentence_words = round(word_count / len(sentences), 1) if (word_count > 0 and sentences) else 0.0

    low_txt = txt.casefold()
    dim_results = []
    hit_dims = 0
    for dim in STUDY_PLAN_DIMENSIONS:
        hits = [kw for kw in dim["keywords"] if kw in low_txt]
        passed = len(hits) >= 2
        if passed:
            hit_dims += 1
        dim_results.append({
            "id": dim["id"],
            "title": dim["title"],
            "passed": passed,
            "matched_keywords": "、".join(hits[:4]) if hits else "尚未偵測到明確段落線索",
            "advice": dim["advice"],
        })

    travel_hits = [w for w in ("sightseeing", "tourist", "vacation", "travel around", "美食", "觀光", "旅遊打卡") if w in low_txt]
    ratio_pct = round(effective_units / target * 100.0, 1)
    if effective_units > target:
        length_status = f"超出目標上限（{effective_units} / {target}，建議精簡 {effective_units - target} 字詞）"
    elif effective_units >= int(target * 0.65):
        length_status = f"字數落於理想區間（{effective_units} / {target}，達 {ratio_pct:g}%）"
    else:
        length_status = f"篇幅偏短（{effective_units} / {target}，僅 {ratio_pct:g}%，建議補充具體課程與規劃）"

    return {
        "text": txt,
        "using_sample": using_sample,
        "target_words": target,
        "en_words": word_count,
        "cjk_chars": cjk_count,
        "paragraph_count": len(paragraphs),
        "avg_sentence_words": avg_sentence_words,
        "hit_dims": hit_dims,
        "dimensions": dim_results,
        "length_status": length_status,
        "has_travel_warning": bool(travel_hits),
    }


# ---------------------------------------------------------------------------
# 9. Fact Sheet 12-Field Worksheet Spec
# ---------------------------------------------------------------------------

FACT_SHEET_FIELDS: tuple[dict[str, str], ...] = (
    {"id": "fs-nomination", "en": "1. Nomination Deadline", "zh": "母校提名截止日", "hint": "供母校國際處線上提名使用（學生須先通過校內甄選）", "ex_a": "2027-03-15", "ex_b": "2027-04-01"},
    {"id": "fs-app-dl", "en": "2. Application Deadline", "zh": "學生網報截止日與時區", "hint": "獲提名後學生親自上傳文件截止日（留意歐洲 CET 或美西時區）", "ex_a": "2027-04-15 23:59 CEST", "ex_b": "2027-04-30 17:00 JST"},
    {"id": "fs-calendar", "en": "3. Academic Calendar & Orientation", "zh": "學期起迄與強制迎新日", "hint": "確認期末考結束日是否與台灣下學期開學撞期", "ex_a": "2027/10–2028/02（期末考至 2 月中）", "ex_b": "2027/09–2028/01"},
    {"id": "fs-lang", "en": "4. Language Proficiency & Sub-scores", "zh": "語言檢定總分與聽說讀寫單科門檻", "hint": "特別核對是否不收 Home Edition、MyBest Scores 或僅收 Academic", "ex_a": "IELTS 6.5 / TOEFL iBT 88", "ex_b": "JLPT N2 或 TOEFL iBT 79"},
    {"id": "fs-gpa", "en": "5. Minimum GPA Requirement", "zh": "最低 GPA 門檻與計算分制", "hint": "確認以 4.0 制或 4.3 制計，以及是否要求歷年每學期均及格", "ex_a": "3.0 / 4.0", "ex_b": "3.0 / 4.0（或百分制 80 分）"},
    {"id": "fs-restrict", "en": "6. Restricted Faculties / Courses", "zh": "不開放交換生選修之院系與課程", "hint": "醫學、法律、MBA、藝術實作或跨學院選課比例上限（如本系須佔 60%）", "ex_a": "醫學系不開放；主修學院須佔 60% ECTS", "ex_b": "MBA 與臨床課程不開放"},
    {"id": "fs-credits", "en": "7. Minimum & Maximum Workload", "zh": "每學期最低與最高修課學分數", "hint": "須同時滿足接待校簽證要求（如 24–30 ECTS）與台灣母校最低學分", "ex_a": "建議 24–30 ECTS／學期", "ex_b": "最低 7 門課（14 単位）"},
    {"id": "fs-catalogue", "en": "8. Course Catalogue URL", "zh": "英文授課課綱查詢網址", "hint": "撰寫讀書計畫（Study Plan）時直接引用該網址內之真實課程代碼", "ex_a": "已查妥 4 門英語授課專業課", "ex_b": "已確認國際教養學部英文課表"},
    {"id": "fs-housing", "en": "9. On-Campus Accommodation", "zh": "學生宿舍申請方式與保證與否", "hint": "標記保證宿位、抽籤制或先搶先贏，以及獨立住宿申請截止日", "ex_a": "不保證宿位，須自行搶登 Studentenwerk", "ex_b": "5 月初獨立抽籤申請國際學生寮"},
    {"id": "fs-insurance", "en": "10. Mandatory Health Insurance", "zh": "強制指定醫療保險規定", "hint": "美國校內醫保、德國公立醫保、澳洲 OSHC 或日本國民健康保險規定", "ex_a": "30 歲以下須保德國公立學生醫保（約 €125/月）", "ex_b": "入境後投保日本國民健康保險"},
    {"id": "fs-finance", "en": "11. Proof of Financial Resources", "zh": "財力證明金額與形式要求", "hint": "簽證或發放入學許可（LoA/DS-2019/CoE）規定之存款金額與幣別", "ex_a": "限制提領帳戶每月 €992 × 停留月數", "ex_b": "銀行英文存款證明約 80–100 萬日圓"},
    {"id": "fs-transcript", "en": "12. Official Transcript Release", "zh": "交換成績單寄發月份", "hint": "大四／延畢生極重要：若隔年 3–4 月才出成績單，可能影響當學期畢業領證", "ex_a": "隔年 3 月底寄發電子成績單", "ex_b": "隔年 2 月下旬寄送至母校國際處"},
)


# ---------------------------------------------------------------------------
# 10. Bilingual Email Template Generator Logic
# ---------------------------------------------------------------------------

EMAIL_SCENES: dict[str, str] = {
    "prof_rec": "邀請授課教授／導師撰寫交換學生推薦信",
    "prof_followup": "推薦信截止前 7–10 天禮貌提醒師長",
    "oia_home": "向台灣母校國際處詢問簡章資格或選校細節",
    "oia_partner": "向海外姊妹校國際處詢問選課限制或住宿規定",
}


def generate_bilingual_emails(
    *,
    scene: str = "prof_rec",
    recipient: str = "王明哲 教授 / Prof. Ming-Che Wang",
    student: str = "資管系三年級 陳宥廷 / Yu-Ting Chen (Junior, Dept. of Information Management)",
    course: str = "資料庫系統（114-1 修習，成績 A+） / Database Systems (Fall 2025, Grade: A+)",
    target_school: str = "德國慕尼黑工業大學（TUM）2027 秋季交換計畫 / Fall 2027 Exchange at Technical University of Munich",
    deadline: str = "2026-11-30",
) -> dict[str, str]:
    if scene not in EMAIL_SCENES:
        scene = "prof_rec"
    rec = recipient.strip() or "教授"
    stu = student.strip() or "王同學"
    crs = course.strip() or "專業必修課程"
    tgt = target_school.strip() or "海外姊妹校交換計畫"
    dl = deadline.strip() or "2026-11-30"

    if scene == "prof_rec":
        zh_subject = f"【出國交換推薦信懇請】{stu} — 擬申請 {tgt}（截止日：{dl}）"
        zh_body = (
            f"{rec} 您好：\n\n"
            f"我是曾修習您開設「{crs}」的學生 {stu}。修課期間受惠於老師在課堂上的啟發，讓我對相關領域的海外進階課程產生濃厚興趣，"
            f"目前正準備參加本校國際處甄選，申請「{tgt}」。\n\n"
            f"冒昧來信，想誠摯請教老師是否方便擔任我的推薦人，協助撰寫一封交換申請推薦信？"
            f"本次校內收件截止日為 {dl}。若蒙老師應允，我將立即整理歷年成績單、英文履歷與讀書計畫初稿供您參考；"
            f"若老師希望先提供推薦信重點摘要草稿或約定簡短面談時間，我也隨時配合。\n\n"
            f"深知老師教學與研究繁忙，無論方便與否都非常感謝您撥冗閱讀。\n\n"
            f"敬祝　教安\n\n學生 {stu} 敬上"
        )
        en_subject = f"[Exchange Recommendation Letter Request] {stu} – {tgt} (Due: {dl})"
        en_body = (
            f"Dear {rec},\n\n"
            f"I hope this email finds you well. My name is {stu}, and I had the privilege of taking your course, {crs}. "
            f"Your lectures greatly strengthened my academic foundation, and I am now applying for the {tgt} through our university's exchange selection.\n\n"
            f"I am writing to kindly ask if you would be willing and available to write a letter of recommendation in support of my application. "
            f"The submission deadline is {dl}.\n\n"
            f"If you are comfortable supporting my application, I would be happy to share my official transcript, CV, and draft Study Plan right away, "
            f"or stop by during your office hours at your convenience.\n\n"
            f"Thank you very much for your time, guidance, and consideration.\n\n"
            f"Sincerely,\n{stu}"
        )
    elif scene == "prof_followup":
        zh_subject = f"【推薦信禮貌提醒】{stu} 出國交換申請（截止日：{dl}）"
        zh_body = (
            f"{rec} 您好：\n\n"
            f"非常感謝您先前應允協助撰寫我申請「{tgt}」的推薦信。因校內申請系統收件截止日（{dl}）即將到來，"
            f"特此來信禮貌向老師確認目前是否需要我再補充任何修課作業、成績證明，或請系統重發線上推薦信連結？\n\n"
            f"期中教學與研究繁忙之際多有打擾，再次感謝老師的提攜與協助！\n\n"
            f"敬祝　順心教安\n\n學生 {stu} 敬上"
        )
        en_subject = f"[Gentle Reminder] Exchange Recommendation Letter for {stu} (Due: {dl})"
        en_body = (
            f"Dear {rec},\n\n"
            f"Thank you again for kindly agreeing to write a recommendation letter for my application to the {tgt}.\n\n"
            f"As the application deadline ({dl}) is approaching, I wanted to send a gentle reminder and check whether you need me to resend the submission link "
            f"or provide any additional course materials. For your convenience, my transcript and Study Plan remain attached.\n\n"
            f"Thank you so much for your generous support during this busy time of the semester.\n\n"
            f"Warm regards,\n{stu}"
        )
    elif scene == "oia_home":
        zh_subject = f"【校級交換申請請益】關於 {tgt} 申請條件與文件規範（{stu}）"
        zh_body = (
            f"國際事務處承辦師長您好：\n\n"
            f"我是本校 {stu}，預計報名本期校內出國交換甄選（截止日：{dl}），目標志願包含「{tgt}」。"
            f"我已先行詳閱本處官網最新簡章與姊妹校一覽表，仍有以下細節想向承辦人確認：\n\n"
            f"1. 該合作校條目所列語言檢定與名額條件，本期是否有最新更新或學院選課限制補充？\n"
            f"2. 關於「{crs}」等相關證明文件，線上系統上傳規範是否有特定合併順序？\n\n"
            f"感謝師長撥冗解答，祝行政順心！\n\n學生 {stu} 敬上"
        )
        en_subject = f"[Inquiry] Outbound Exchange Application Requirements – {tgt} ({stu})"
        en_body = (
            f"Dear Office of International Affairs Team,\n\n"
            f"My name is {stu}, and I am preparing my internal outbound exchange application (deadline: {dl}) with {tgt} among my target partner institutions.\n\n"
            f"After reviewing the current call for applications and partner list on the OIA website, I would like to clarify two brief questions:\n"
            f"1. Are there any updated faculty restrictions or language sub-score requirements for this partner institution in the upcoming cycle?\n"
            f"2. Regarding supporting documents ({crs}), are there specific formatting instructions beyond those stated in the brochure?\n\n"
            f"Thank you very much for your time and assistance.\n\nBest regards,\n{stu}"
        )
    else:
        zh_subject = f"（中文對照稿）受提名／準交換生詢問選課與住宿規定 — {tgt}"
        zh_body = (
            f"【寄給海外姊妹校國際處請優先使用右側英文信件；以下為中文語意對照】\n\n"
            f"{rec}（國際交流中心團隊）您好：\n"
            f"我是來自台灣合作大學的在學生 {stu}，正在準備「{tgt}」（相關截止日：{dl}）。"
            f"我已詳閱貴校官網公布的交換生 Fact Sheet 與課程資訊，想禮貌請教關於「{crs}」是否開放交換生修讀，以及校內宿舍申請時程細節。\n\n"
            f"非常感謝您的協助，期待有機會前往貴校研修！"
        )
        en_subject = f"[Prospective/Nominated Exchange Student Inquiry] Course Enrollment & Housing – {stu}"
        en_body = (
            f"Dear {rec},\n\n"
            f"Greetings from Taiwan. My name is {stu} from one of your partner universities, and I am preparing for the {tgt} (reference deadline: {dl}).\n\n"
            f"I have carefully reviewed your latest Exchange Fact Sheet and online course information, and I would be grateful if you could clarify a quick question regarding {crs}: "
            f"is this module/track open to incoming one-semester exchange students, and are there specific prerequisites or separate registration steps I should note alongside housing application timelines?\n\n"
            f"Thank you very much for your kind assistance.\n\nSincerely,\n{stu}"
        )

    return {
        "scene": scene,
        "recipient": rec,
        "student": stu,
        "course": crs,
        "target_school": tgt,
        "deadline": dl,
        "zh_subject": zh_subject,
        "zh_body": zh_body,
        "en_subject": en_subject,
        "en_body": en_body,
    }


# ---------------------------------------------------------------------------
# Wave 3 Tool FAQs (3-4 concise, strictly factual FAQs per tool)
# ---------------------------------------------------------------------------

FAQS_VALIDITY: tuple[tuple[str, str], ...] = (
    (
        "托福或雅思成績在校內報名時還沒過期，但隔年姊妹校網報時剛好滿 2 年可以嗎？",
        "風險極高。多數海外接待校要求「向該校遞交網報（Application Deadline）」甚至發放入學許可時，語言成績仍須在 2 年有效期限內；若期間屆滿，將需要在獲得提名後緊急重考補件。",
    ),
    (
        "日文檢定（JLPT）合格證書真的永久有效嗎？",
        "日本國際交流基金會核發之 JLPT 認定書本身未印製到期日；但部分台灣母校國際處或日本協定大學簡章會明文要求「檢附近 2 年或 3 年內應考之成績」，報名前仍須逐校核對簡章條文。",
    ),
    (
        "為什麼要在截止日前預留 14 天以上的成績單緩衝期？",
        "部分大學要求由測驗機構直接寄送官方電子或紙本成績單（如 ETS 機構代碼加發），或須攜帶正本至國際處核驗，預留 2 週可避免國際郵遞或連假延誤。",
    ),
)

FAQS_MATCHER: tuple[tuple[str, str], ...] = (
    (
        "選校雷達篩出的「明確列載達標」與「同級英檢參考」有什麼不同？",
        "「明確列載達標」表示該合作校欄位直接寫出你輸入的檢定且分數達標；「同級英檢參考」表示該校列載其他英語檢定（如只寫 IELTS 但你輸入 TOEIC），報名前須查簡章確認是否接受替代檢定。",
    ),
    (
        "為什麼設定學期預算上限後，有些國家的合作校仍會顯示？",
        "系統對已建立 12 國費用模板的目的地依基準總支出篩選；尚未建立國家費用模板的地區不會虛構金額，會標示「預算依接待校公告」保留供你自行核對。",
    ),
    (
        "雷達顯示達標就代表當期一定開放申請嗎？",
        "不代表。合作校名單同時包含當期開缺與歷年締約參考，可勾選「僅看當期名單列載」縮小範圍，並點擊進入官方來源確認最新名額。",
    ),
)

FAQS_REVERSE: tuple[tuple[str, str], ...] = (
    (
        "海外名校反查器適合哪些情境使用？",
        "適合已有夢想海外大學（如早稻田、慕尼黑工大、延世、加州大學等）的高中升大學考生、轉學生、準備考研究所的同學，或想橫向比對各校語言門檻差異的在校生。",
    ),
    (
        "同一所海外大學在不同台灣母校的語言門檻為什麼可能不同？",
        "各台灣大學與海外夥伴校簽署的可能是校級協議或特定商管／工學院級協議，且母校校內初審也可能另設較高門檻，實際資格與名額以各校最新官方公告為準。",
    ),
    (
        "搜尋英文校名縮寫（如 TUM、NUS、KU）找得到嗎？",
        "支援中英文校名關鍵字與常見縮寫檢索；若未找到特定分校，建議改輸入英文主校名或透過國家篩選瀏覽。",
    ),
)

FAQS_RANKER: tuple[tuple[str, str], ...] = (
    (
        "為什麼交換志願序不建議把「保底學校」填在「夢幻學校」前面？",
        "多數大學校內交換分發依評比分數高低，從學生的第 1 志願依序往下檢視是否尚有名額；一旦第 1 志願（保底校）尚有名額即直接錄取結案，系統不會再看後面的夢幻志願。",
    ),
    (
        "夢幻、落點、保底志願通常建議怎麼配比？",
        "常見穩健配置為前 20%–30% 放高競爭名校（夢幻），中段 40%–50% 放門檻與歷年名額穩定的主力校（落點），最後保留至少 1–2 所名額較充裕且明確開缺的合作校（保底）。",
    ),
    (
        "母校可以填幾個交換志願？",
        "各大學上限差異極大（從僅能填 3–5 個志願到可填 20–30 個志願不等），請以母校國際處當期線上報名系統規定為準。",
    ),
)

FAQS_FX: tuple[tuple[str, str], ...] = (
    (
        "準備出國交換的外幣應該一次換齊，還是分批換匯比較好？",
        "確定獲得校內錄取後距離出發通常還有 4–8 個月，採 3 至 4 批分批換入外幣（例如先鎖定前兩批基本住宿生活費，剩餘視匯率區間補齊）有助平滑匯率高低點波動。",
    ),
    (
        "去歐洲或美加交換需要全部換成外幣現鈔帶出國嗎？",
        "切勿攜帶巨額現鈔。多數歐美日韓消費可搭配外幣雙幣卡、國際金融卡跨國提款或開立當地帳戶後電匯；入境各國攜帶超額外幣現鈔亦須依法申報。",
    ),
    (
        "分批換匯計算機的參考匯率從哪裡來？",
        "預設帶入系統收錄之台銀牌告外幣參考匯率作為試算起點，你可隨時手動改為往來銀行網銀即期賣出優惠匯率計算精確成本。",
    ),
)

FAQS_TIMEZONE: tuple[tuple[str, str], ...] = (
    (
        "什麼是歐美與澳洲的夏令時間（Daylight Saving Time, DST）？",
        "歐美多數地區於每年 3 月至 10/11 月將時鐘撥快 1 小時，南半球澳洲則在 10 月至隔年 4 月撥快 1 小時；同一所學校春季班與秋季班網報與台灣的時差會相差 1 小時。",
    ),
    (
        "申請日本或韓國姊妹校時，截止時間最容易犯什麼錯？",
        "日本與韓國（UTC+9）比台灣（UTC+8）快 1 小時！當簡章寫日本時間 23:59 截止時，在台灣晚上 23:00 系統就已經關閉，務必提前一天完成送出。",
    ),
    (
        "如果姊妹校 Fact Sheet 只寫截止日期沒寫幾點幾分怎麼辦？",
        "切勿預設到當地午夜 23:59。許多大學國際處會在當地行政下班時間（如 16:00 或 17:00）手動關閉表單，強烈建議以換算出的「提前 24 小時安全送件線」作為個人死線。",
    ),
)

FAQS_CHECKLIST: tuple[tuple[str, str], ...] = (
    (
        "勾選好的交換申請清單進度會不會上傳到伺服器？",
        "不會。勾選狀態僅儲存在你目前使用的瀏覽器本機空間（localStorage），完全不讀取帳號亦不傳送個人隱私；若想永久保存紙本或跨裝置檢視，請點選「列印／存成 PDF」。",
    ),
    (
        "為什麼拿到母校錄取榜單後還不能馬上辦學生簽證？",
        "母校榜單僅代表取得校內推薦提名資格（Nomination），必須等母校提名並由你完成海外姊妹校網報、收到對方核發的正式入學許可（LoA / CoE / DS-2019）後，使領館才受理簽證。",
    ),
    (
        "出國交換期間台灣母校的學籍需要辦理休學嗎？",
        "絕大多數校際交換計畫規定交換期間必須維持台灣母校「在學註冊並繳交母校學雜費」，不得辦理休學或畢業離校，實際規定以各校最新官方公告為準。",
    ),
)

FAQS_STUDYPLAN: tuple[tuple[str, str], ...] = (
    (
        "交換學生的英文讀書計畫（Study Plan）跟申請國外碩士的 SOP 有什麼不同？",
        "交換讀書計畫重點在於「這一學期／一學年具體要修哪些課、為何該姊妹校適合你、回台灣後如何銜接畢業與未來規劃」，不需像碩博申請長篇幅鋪陳終身學術生涯。",
    ),
    (
        "讀書計畫字數通常寫多少最合適？",
        "若母校或姊妹校簡章有明訂字數（如 500–1,000 字或 A4 一至兩頁內）請嚴格遵守；未特別限制時，英文約 600–900 words（分成 4 段）最便於審查委員快速掌握重點。",
    ),
    (
        "可以在讀書計畫裡寫想體驗當地文化或環歐旅遊嗎？",
        "跨文化交流可簡短點綴於結尾（約佔全文 10% 內），切忌將觀光旅遊、美食打卡寫成主要動機；審查委員最看重明確的修課計畫與學術準備度。",
    ),
)

FAQS_FACTSHEET: tuple[tuple[str, str], ...] = (
    (
        "什麼是海外大學的 Exchange Fact Sheet？去哪裡找？",
        "Fact Sheet 是海外大學國際處每年更新給合作校的「交換生資訊摘要表」（常為 2–4 頁 PDF 或專頁），通常附在母校國際處合作校介紹頁，或搜尋「校名 + Incoming Exchange Fact Sheet」即可找到。",
    ),
    (
        "為什麼大四生一定要看 Fact Sheet 上的「成績單寄發月份（Transcript Issuance）」？",
        "例如日本春學期或德國冬季學期常到隔年 2–3 月才結束考試、4–5 月才寄出正式成績單；大四生若急需抵免畢業學分或銜接研究所報到，務必提前規劃。",
    ),
    (
        "整理表填寫的內容如何匯出分享？",
        "點擊「複製 Markdown 對照表」即可貼入 Notion、Google 文件或筆記軟體，亦可直接點選「列印整理表」輸出成乾淨的 A4 雙校核對表。",
    ),
)

FAQS_EMAIL: tuple[tuple[str, str], ...] = (
    (
        "邀請教授寫交換推薦信，最晚應該在截止日前多久寄信？",
        "建議至少在收件截止日前 4 至 6 週寄出邀約信；若遇期中考、期末改卷或國科會計畫截稿期，太晚開口容易讓師長措手不及。",
    ),
    (
        "寄信邀請教授寫推薦信時，第一封信就要把附件全部寄過去嗎？",
        "可在第一封信附上簡明成績單（標出修過該教授的課與等第）與一頁式申請方向摘要，讓教授快速想起你的表現；待教授回覆同意後再補齊完整讀書計畫與系統連結。",
    ),
    (
        "可以直接寄信問海外姊妹校國際處「我有沒有機會錄取」嗎？",
        "不建議。交換提名權在台灣母校，尚未獲提名時不宜要求對方評估錄取機率；但若官網 Fact Sheet 未寫明某門課是否開放交換生修習，禮貌來信詢問選課規定是合宜的。",
    ),
)


# ---------------------------------------------------------------------------
# Route Registration for Wave 3 Tools
# ---------------------------------------------------------------------------

def register_wave3_tool_routes(
    router: APIRouter,
    *,
    settings: Any,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    render_tool_page: Callable[[PageMetaSpec, str, list[tuple[str, str]], tuple[tuple[str, str], ...]], HTMLResponse],
    render_switcher: Callable[[str], str],
    safe_json_block: Callable[[str, Any], str],
    official_link: Callable[[str | None, str], str],
    availability_labels: Mapping[str, str],
) -> None:
    entity_lock = threading.Lock()
    entity_cache: dict[str, Any] = {"at": 0.0, "entities": None}

    def get_cached_entities() -> Mapping[Any, Any]:
        with entity_lock:
            if entity_cache["entities"] is not None and monotonic() - entity_cache["at"] < 60.0:
                return entity_cache["entities"]
            entities, _ = build_cross_school_entity_index(catalogue_loader, require_complete=True)
            entity_cache["at"] = monotonic()
            entity_cache["entities"] = entities
            return entities

    # 1. /tools/test-validity-checker
    @router.api_route("/tools/test-validity-checker", methods=["GET", "HEAD"])
    def tool_test_validity_checker(
        exam: str = Query(default="toefl"),
        test_date: str | None = Query(default=None),
        home: str = Query(default="ntu"),
        home_deadline: str | None = Query(default=None),
        partner_deadline: str | None = Query(default=None),
        buffer_days: int = Query(default=14, ge=0, le=60),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/test-validity-checker"]
        res = evaluate_test_validity(
            exam=exam,
            test_date_str=test_date,
            home_id=home,
            home_deadline_str=home_deadline,
            partner_deadline_str=partner_deadline,
            buffer_days=buffer_days,
        )
        exam_opts = "".join(
            f'<option value="{escape(k)}"{" selected" if res["exam"] == k else ""}>{escape(v["label"])}</option>'
            for k, v in EXAM_VALIDITY_SPECS.items()
        )
        deadlines = build_all_71_school_deadlines()
        dl_by_id = {r["school_id"]: r["deadline_iso"] or "" for r in deadlines}
        home_opts = "".join(
            f'<option value="{escape(u.id)}"{" selected" if u.id == res["home_id"] else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )
        ref_rows = "".join(
            f"<tr><th scope='row'>{escape(v['label'])}</th><td>{'2 年' if v['validity_years'] == 2 else '證書無固定效期（依簡章）'}</td>"
            f"<td>{escape(v['delivery_note'])}</td><td>{escape(v['rule_note'])}</td></tr>"
            for v in EXAM_VALIDITY_SPECS.values()
        )
        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
{_safe_tv_json(safe_json_block, dl_by_id)}
<section class="uw-tool-card" aria-labelledby="tv-heading">
  <div class="uw-tool-header">
    <h2 id="tv-heading">輸入考試日期與兩階段截止日</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製檢核連結</button>
  </div>
  <form method="get" action="/tools/test-validity-checker" class="uw-form-grid" data-tool-form="test-validity">
    <label class="uw-field">
      <span>檢定種類</span>
      <select name="exam" id="tv-exam">{exam_opts}</select>
    </label>
    <label class="uw-field">
      <span>考試日期（Test Date）</span>
      <input type="date" name="test_date" id="tv-test-date" value="{escape(res['test_date'])}">
    </label>
    <label class="uw-field">
      <span>就讀台灣母校</span>
      <select name="home" id="tv-home">{home_opts}</select>
    </label>
    <label class="uw-field">
      <span>母校校內收件截止日</span>
      <input type="date" name="home_deadline" id="tv-home-dl" value="{escape(res['home_deadline'])}">
    </label>
    <label class="uw-field">
      <span>海外姊妹校網報截止日</span>
      <input type="date" name="partner_deadline" id="tv-partner-dl" value="{escape(res['partner_deadline'])}">
    </label>
    <label class="uw-field">
      <span>加發／寄送緩衝天數</span>
      <input type="number" name="buffer_days" id="tv-buffer" value="{res['buffer_days']}" min="0" max="60">
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">檢核效期</button>
    </div>
  </form>

  <div class="uw-kpi-grid" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">成績 2 年效期屆滿日</span>
      <strong class="uw-kpi-value" data-tv-out="expiry">{escape(res['expiry_display'])}</strong>
      <span class="uw-kpi-tag" data-tv-out="expiry-sub">{escape(res['expiry_sub'])}</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">母校校內截止檢核</span>
      <strong class="uw-kpi-value" data-tv-out="home-status">{escape(res['home_status'])}</strong>
      <span class="uw-kpi-tag">基準：{escape(res['home_short_name'])}</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">姊妹校網報截止檢核</span>
      <strong class="uw-kpi-value" data-tv-out="partner-status">{escape(res['partner_status'])}</strong>
      <span class="uw-kpi-tag">含海外提名階段</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">建議備妥成績單日</span>
      <strong class="uw-kpi-value" data-tv-out="order-by">{escape(res['order_by_date'])}</strong>
      <span class="uw-kpi-tag">提前 {res['buffer_days']} 天申請加發</span>
    </div>
  </div>
  <div class="uw-status-bar">
    <span data-tv-out="rule-note">{escape(res['rule_note'])}</span>
    <span>{official_link(res['home_official_url'], res['home_short_name'] + '國際處公告')} · <a href="/tools/language-score-converter?home={escape(res['home_id'])}">查分數達標校</a></span>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>各語言檢定官方效期與成績單寄送工作天對照表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="語言檢定效期與出分寄送對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">常見交換語言檢定官方效期與成績單寄送工作天參考</caption>
          <thead>
            <tr><th scope="col">檢定項目</th><th scope="col">標準效期</th><th scope="col">出分與加發工作天</th><th scope="col">交換審查提醒</th></tr>
          </thead>
          <tbody>{ref_rows}</tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_VALIDITY)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_VALIDITY,
        )

    # 2. /tools/eligibility-matcher + .json
    @router.api_route("/tools/eligibility-matcher.json", methods=["GET", "HEAD"])
    def tool_eligibility_matcher_json(
        home: str = Query(default="ntu"),
        test: str = Query(default="ielts"),
        score: str = Query(default="6.5"),
        gpa: float = Query(default=3.5, ge=0.0, le=4.3),
        budget: int = Query(default=0, ge=0, le=2000000),
        region: str = Query(default="all"),
        open_only: str = Query(default="all"),
    ) -> JSONResponse:
        uni = resolve_university(home) or SUPPORTED_UNIVERSITIES[0]
        partners, _ = catalogue_loader(uni)
        data = match_eligibility_radar(
            uni,
            partners,
            availability_labels,
            test=test,
            score=score,
            gpa=gpa,
            budget_twd=budget,
            region=region,
            open_only=open_only,
        )
        return JSONResponse(
            data,
            headers={"Cache-Control": "public, max-age=120", "X-Robots-Tag": "noindex, nofollow"},
        )

    @router.api_route("/tools/eligibility-matcher", methods=["GET", "HEAD"])
    def tool_eligibility_matcher(
        home: str = Query(default="ntu"),
        test: str = Query(default="ielts"),
        score: str = Query(default="6.5"),
        gpa: float = Query(default=3.5, ge=0.0, le=4.3),
        budget: int = Query(default=0, ge=0, le=2000000),
        region: str = Query(default="all"),
        open_only: str = Query(default="all"),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/eligibility-matcher"]
        uni = resolve_university(home) or SUPPORTED_UNIVERSITIES[0]
        partners, _ = catalogue_loader(uni)
        res = match_eligibility_radar(
            uni,
            partners,
            availability_labels,
            test=test,
            score=score,
            gpa=gpa,
            budget_twd=budget,
            region=region,
            open_only=open_only,
        )
        home_opts = "".join(
            f'<option value="{escape(u.id)}"{" selected" if u.id == res["home_id"] else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )
        test_opts = "".join(
            f'<option value="{k}"{" selected" if res["conversion"]["test"] == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("ielts", "IELTS 雅思"),
                ("toefl", "TOEFL iBT 托福"),
                ("toeic", "TOEIC 多益"),
                ("cefr", "CEFR 等級"),
                ("jlpt", "JLPT 日檢"),
            )
        )
        budget_opts = "".join(
            f'<option value="{val}"{" selected" if res["budget_twd"] == val else ""}>{lbl}</option>'
            for val, lbl in (
                (0, "不限預算"),
                (200000, "每學期 NT$ 20 萬內"),
                (300000, "每學期 NT$ 30 萬內"),
                (400000, "每學期 NT$ 40 萬內"),
                (550000, "每學期 NT$ 55 萬內"),
            )
        )
        reg_opts = "".join(
            f'<option value="{k}"{" selected" if res["region"] == k else ""}>{escape(v)}</option>'
            for k, v in REGION_OPTIONS.items()
        )
        open_opts = "".join(
            f'<option value="{k}"{" selected" if res["open_only"] == k else ""}>{lbl}</option>'
            for k, lbl in (("all", "全部合作校紀錄"), ("open", "僅看當期名單列載"))
        )

        cards_html = ""
        for item in res["direct_samples"]:
            cards_html += (
                f'<li class="uw-partner-mini-card">'
                f'<div class="uw-partner-mini-top"><a href="{escape(item["partner_url"])}"><strong>{escape(item["school_name"])}</strong></a>'
                f'<span class="uw-mini-country">{escape(item["country"])}</span></div>'
                f'<p class="uw-mini-rule"><span class="uw-tag-ok">{escape(item["matched_rule"])}</span> · {escape(item["budget_tag"])} · '
                f'<a href="{escape(item["compare_url"])}">加入 PK</a></p></li>'
            )
        direct_block = (
            f'<ul class="uw-partner-mini-grid">{cards_html}</ul>'
            if cards_html
            else "<p>目前條件下無單獨列載此檢定且達標的條目，請放寬洲別／預算或展開下方同級參考清單。</p>"
        )

        reg_names = {"asia": "亞洲", "europe": "歐洲", "americas": "美洲", "oceania": "大洋洲", "other": "其他地區"}
        reg_rows = "".join(
            f"<tr><th scope='row'>{reg_names[rk]}</th><td>{st['total']}</td><td><strong>{st['direct']}</strong></td>"
            f"<td>{st['equiv']}</td><td>{st['open']}</td></tr>"
            for rk, st in res["region_stats"].items()
            if st["total"] > 0 or rk in ("asia", "europe", "americas", "oceania")
        )

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="radar-heading">
  <div class="uw-tool-header">
    <h2 id="radar-heading">輸入五項條件即時掃描合作校</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-sm uw-btn-outline" id="radar-school-link" href="{escape(res['home_school_url'])}">{escape(res['home_short_name'])}完整校頁</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製篩選網址</button>
    </div>
  </div>
  <form method="get" action="/tools/eligibility-matcher" class="uw-form-grid" data-tool-form="eligibility-radar">
    <label class="uw-field"><span>就讀母校</span><select name="home" id="rad-home">{home_opts}</select></label>
    <label class="uw-field"><span>語言檢定</span><select name="test" id="rad-test">{test_opts}</select></label>
    <label class="uw-field"><span>分數／級數</span><input type="text" name="score" id="rad-score" value="{escape(str(score))}"></label>
    <label class="uw-field"><span>目前 GPA</span><input type="number" name="gpa" id="rad-gpa" value="{res['gpa']:.2f}" min="0" max="4.3" step="0.05"></label>
    <label class="uw-field"><span>學期預算上限</span><select name="budget" id="rad-budget">{budget_opts}</select></label>
    <label class="uw-field"><span>目標洲別</span><select name="region" id="rad-region">{reg_opts}</select></label>
    <label class="uw-field"><span>名單狀態</span><select name="open_only" id="rad-open">{open_opts}</select></label>
    <div class="uw-form-actions uw-nojs-only"><button type="submit" class="uw-btn uw-btn-primary">開始篩選</button></div>
  </form>

  <div class="uw-kpi-grid" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">明確列載該檢定達標</span>
      <strong class="uw-kpi-value" data-rad-out="direct">{res['direct_count']} 所</strong>
      <span class="uw-kpi-tag" data-rad-out="cefr">對照等級 {escape(res['conversion']['cefr'])}</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">同級其他英檢參考</span>
      <strong class="uw-kpi-value" data-rad-out="equiv">{res['equiv_count']} 所</strong>
      <span class="uw-kpi-tag">須查簡章是否採計替代</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">範圍內合作校總數</span>
      <strong class="uw-kpi-value" data-rad-out="scoped">{res['scoped_total']} 所</strong>
      <span class="uw-kpi-tag" data-rad-out="home-name">{escape(res['home_short_name'])}資料庫</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">母校校內 GPA 檢核</span>
      <strong class="uw-kpi-value" data-rad-out="gpa-check">{escape(res['gpa_check_label'])}</strong>
      <span class="uw-kpi-tag"><a href="/tools/gpa-converter">GPA 換算工具</a></span>
    </div>
  </div>

  <div class="uw-db-match-panel">
    <div class="uw-db-match-head">
      <h3>明確列載達標合作校預覽（前 18 所）</h3>
      <a class="uw-btn uw-btn-sm uw-btn-primary" href="/?{urlencode({'home': res['home_name']})}#partners">前往站內完整選校工作台</a>
    </div>
    <div id="rad-direct-list">{direct_block}</div>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer" open>
    <summary>各洲別達標校數分布統計表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="各洲別達標校數統計表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">篩選結果依洲別分布統計表</caption>
          <thead>
            <tr><th scope="col">洲別</th><th scope="col">範圍內合作校數</th><th scope="col">明確語檢達標</th><th scope="col">同級檢定參考</th><th scope="col">當期名單列載</th></tr>
          </thead>
          <tbody id="rad-region-tbody">{reg_rows}</tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_MATCHER)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_MATCHER,
        )

    # 3. /tools/reverse-partner-search + .json
    @router.api_route("/tools/reverse-partner-search.json", methods=["GET", "HEAD"])
    def tool_reverse_partner_json(
        q: str = Query(default="早稻田"),
        country: str = Query(default="all"),
    ) -> JSONResponse:
        data = search_reverse_partners(get_cached_entities(), availability_labels, q=q, country=country, limit=12)
        return JSONResponse(
            data,
            headers={"Cache-Control": "public, max-age=120", "X-Robots-Tag": "noindex, nofollow"},
        )

    @router.api_route("/tools/reverse-partner-search", methods=["GET", "HEAD"])
    def tool_reverse_partner_search(
        q: str = Query(default="早稻田"),
        country: str = Query(default="all"),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/reverse-partner-search"]
        res = search_reverse_partners(get_cached_entities(), availability_labels, q=q, country=country, limit=12)
        country_opts = f'<option value="all"{" selected" if res["country"] == "all" else ""}>全部國家／地區</option>'
        for c in res["country_options"]:
            sel = " selected" if res["country"] == c["slug"] else ""
            country_opts += f'<option value="{escape(c["slug"])}"{sel}>{escape(c["name"])}（{c["count"]} 校）</option>'

        summary_rows = ""
        for item in res["results"]:
            home_links = "、".join(
                f'<a href="{escape(ag["partner_url"])}">{escape(ag["short_name"])}</a>'
                for ag in item["agreements"][:8]
            )
            if len(item["agreements"]) > 8:
                home_links += f" 等共 {len(item['agreements'])} 校"
            summary_rows += (
                f"<tr><th scope='row'><a href='{escape(item['canonical_path'])}'>{escape(item['display_title'])}</a>"
                f"<span class='uw-inline-badge'>{escape(item['country_zh'])}</span></th>"
                f"<td><strong>{item['contracted_count']} 校</strong></td>"
                f"<td>{item['open_home_count']} 校</td>"
                f"<td>{home_links}</td>"
                f"<td><a href='{escape(item['canonical_path'])}'>跨校門檻總表</a></td></tr>"
            )
        if not summary_rows:
            summary_rows = "<tr><td colspan='5'>找不到符合此關鍵字的海外大學，請嘗試英文校名或切換國家。</td></tr>"

        detail_html = ""
        if res["results"]:
            top = res["results"][0]
            ag_rows = "".join(
                f"<tr><th scope='row'><a href='{escape(ag['partner_url'])}'>{escape(ag['home_name'])}</a></th>"
                f"<td>{escape(ag['status'])}</td><td>{escape(ag['quota'])}</td><td>{escape(ag['language'])}</td>"
                f"<td><a href='{escape(ag['partner_url'])}'>母校方案</a> · {official_link(ag['source_url'], '官方來源')}</td></tr>"
                for ag in top["agreements"]
            )
            detail_html = f"""
  <details class="uw-drawer" open>
    <summary>首筆符合學校「{escape(top['display_title'])}」全台 {top['contracted_count']} 所締約母校門檻明細</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="首筆海外大學各台灣母校締約門檻明細表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">{escape(top['display_title'])} 各台灣締約母校名額與語言門檻對照表</caption>
          <thead>
            <tr><th scope="col">台灣締約母校</th><th scope="col">當期狀態</th><th scope="col">來源名額</th><th scope="col">語言門檻</th><th scope="col">核對連結</th></tr>
          </thead>
          <tbody id="rev-detail-tbody">{ag_rows}</tbody>
        </table>
      </div>
    </div>
  </details>"""

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="rev-heading">
  <div class="uw-tool-header">
    <h2 id="rev-heading">輸入海外大學名稱反查台灣締約母校（符合 <span id="rev-total">{res['matched_total']}</span> 所海外大學）</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製查詢網址</button>
  </div>
  <form method="get" action="/tools/reverse-partner-search" class="uw-form-grid" data-tool-form="reverse-partner">
    <label class="uw-field">
      <span>海外大學名稱（中／英文皆可）</span>
      <input type="search" name="q" id="rev-q" value="{escape(res['q'])}" placeholder="例如：早稻田、慕尼黑、延世、TUM、Amsterdam…">
    </label>
    <label class="uw-field">
      <span>國家／地區篩選</span>
      <select name="country" id="rev-country">{country_opts}</select>
    </label>
    <div class="uw-form-actions uw-nojs-only"><button type="submit" class="uw-btn uw-btn-primary">反查締約母校</button></div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="海外姊妹校反查台灣締約大學結果表">
    <table class="uw-data-table">
      <caption class="uw-sr-only">海外合作大學反查台灣締約母校統計表</caption>
      <thead>
        <tr><th scope="col">海外大學</th><th scope="col">全台締約校數</th><th scope="col">當期列載母校</th><th scope="col">締約台灣母校直達連結</th><th scope="col">跨校專頁</th></tr>
      </thead>
      <tbody id="rev-summary-tbody">{summary_rows}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  {detail_html}
  {render_faq_section(FAQS_REVERSE)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_REVERSE,
        )

    # 4. /tools/preference-ranker + .json
    @router.api_route("/tools/preference-ranker.json", methods=["GET", "HEAD"])
    def tool_preference_ranker_json(home: str = Query(default="ntu")) -> JSONResponse:
        uni = resolve_university(home) or SUPPORTED_UNIVERSITIES[0]
        partners, _ = catalogue_loader(uni)
        data = evaluate_preference_portfolio(uni.id, partners, availability_labels)
        return JSONResponse(
            data,
            headers={"Cache-Control": "public, max-age=120", "X-Robots-Tag": "noindex, nofollow"},
        )

    @router.api_route("/tools/preference-ranker", methods=["GET", "HEAD"])
    def tool_preference_ranker(
        home: str = Query(default="ntu"),
        s1: str | None = Query(default=None),
        t1: str | None = Query(default=None),
        s2: str | None = Query(default=None),
        t2: str | None = Query(default=None),
        s3: str | None = Query(default=None),
        t3: str | None = Query(default=None),
        s4: str | None = Query(default=None),
        t4: str | None = Query(default=None),
        s5: str | None = Query(default=None),
        t5: str | None = Query(default=None),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/preference-ranker"]
        uni = resolve_university(home) or SUPPORTED_UNIVERSITIES[0]
        partners, _ = catalogue_loader(uni)
        res = evaluate_preference_portfolio(
            uni.id,
            partners,
            availability_labels,
            slots=((s1, t1), (s2, t2), (s3, t3), (s4, t4), (s5, t5)),
        )
        home_opts = "".join(
            f'<option value="{escape(u.id)}"{" selected" if u.id == res["home_id"] else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )
        chosen_by_slot = {r["slot_index"]: r for r in res["chosen"]}

        slot_rows_html = ""
        for idx in range(1, 6):
            picked = chosen_by_slot.get(idx)
            sel_pid = picked["pid"] if picked else ""
            sel_tier = picked["tier"] if picked else ("dream" if idx == 1 else ("safety" if idx >= 4 else "target"))
            opt_html = '<option value="">（未選填此志願序）</option>' + "".join(
                f'<option value="{escape(o["pid"])}"{" selected" if o["pid"] == sel_pid else ""}>{escape(o["label"])}</option>'
                for o in res["options"]
            )
            tier_html = "".join(
                f'<option value="{tk}"{" selected" if tk == sel_tier else ""}>{tl}</option>'
                for tk, tl in TIER_LABELS.items()
            )
            st_txt = picked["status_label"] if picked else "—"
            qt_txt = f"{picked['quota']} ｜ {picked['language']}" if picked else "—"
            slot_rows_html += f"""<tr data-pref-row="{idx}">
  <th scope="row">第 {idx} 志願</th>
  <td><select name="s{idx}" class="pref-school-select" aria-label="第 {idx} 志願合作校">{opt_html}</select></td>
  <td><select name="t{idx}" class="pref-tier-select" aria-label="第 {idx} 志願風險定位">{tier_html}</select></td>
  <td class="pref-status-cell">{escape(st_txt)}<div class="uw-cell-sub">{escape(qt_txt)}</div></td>
  <td>
    <div class="uw-btn-group">
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-pref-move="-1" aria-label="將第 {idx} 志願上移">▲</button>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-pref-move="1" aria-label="將第 {idx} 志願下移">▼</button>
    </div>
  </td>
</tr>"""

        alerts_html = "".join(
            f'<li class="{"uw-tag-ok" if a["level"] == "ok" else "uw-tag-warn"}">{escape(a["text"])}</li>'
            for a in res["alerts"]
        )
        max_pref_note = f"{res['max_preferences']} 個" if res["max_preferences"] else "依當期簡章確認"

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
{safe_json_block("uw-pref-options", res["options"])}
<section class="uw-tool-card" aria-labelledby="pref-heading">
  <div class="uw-tool-header">
    <h2 id="pref-heading">排列志願序並檢查配比風險</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製志願組合網址</button>
  </div>
  <form method="get" action="/tools/preference-ranker" data-tool-form="preference-ranker">
    <div class="uw-form-grid">
      <label class="uw-field">
        <span>就讀台灣母校（志願上限紀錄：<strong id="pref-max-note">{escape(max_pref_note)}</strong>）</span>
        <select name="home" id="pref-home">{home_opts}</select>
      </label>
      <div class="uw-form-actions uw-nojs-only"><button type="submit" class="uw-btn uw-btn-primary">重新體檢</button></div>
    </div>

    <div class="uw-kpi-grid" aria-live="polite">
      <div class="uw-kpi-box uw-kpi-highlight">
        <span class="uw-kpi-label">已排志願總數</span>
        <strong class="uw-kpi-value" data-pref-out="count">{len(res['chosen'])} 所</strong>
        <span class="uw-kpi-tag">支援 ▲▼ 即時調整順序</span>
      </div>
      <div class="uw-kpi-box">
        <span class="uw-kpi-label">夢幻 ／ 落點 ／ 保底配比</span>
        <strong class="uw-kpi-value" data-pref-out="ratio">{res['tier_counts'].get('dream', 0)} : {res['tier_counts'].get('target', 0)} : {res['tier_counts'].get('safety', 0)}</strong>
        <span class="uw-kpi-tag">建議至少含 1 所保底校</span>
      </div>
    </div>

    <ul class="uw-alert-list" id="pref-alerts" aria-live="polite">{alerts_html}</ul>

    <div class="uw-table-wrap" tabindex="0" role="region" aria-label="交換志願序模擬排序與風險檢查表">
      <table class="uw-data-table" id="pref-table">
        <caption class="uw-sr-only">{escape(res['home_name'])} 交換志願序模擬排序與名額狀態檢查表</caption>
        <thead>
          <tr><th scope="col">志願序</th><th scope="col">目標海外姊妹校</th><th scope="col">策略定位</th><th scope="col">當期狀態與語檢門檻</th><th scope="col">順序調整</th></tr>
        </thead>
        <tbody id="pref-tbody">{slot_rows_html}</tbody>
      </table>
    </div>
  </form>
</section>

<div class="uw-drawers-stack">
  {render_faq_section(FAQS_RANKER)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_RANKER,
        )

    # 5. /tools/fx-budget-planner
    @router.api_route("/tools/fx-budget-planner", methods=["GET", "HEAD"])
    def tool_fx_budget_planner(
        currency: str = Query(default="JPY"),
        target: float | None = Query(default=None, ge=0.0),
        b1_amt: float | None = Query(default=None, ge=0.0),
        b1_rate: float | None = Query(default=None, ge=0.0),
        b2_amt: float | None = Query(default=None, ge=0.0),
        b2_rate: float | None = Query(default=None, ge=0.0),
        b3_amt: float = Query(default=0.0, ge=0.0),
        b3_rate: float = Query(default=0.0, ge=0.0),
        spot: float | None = Query(default=None, ge=0.0),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/fx-budget-planner"]
        cur_key = currency.strip().upper() if currency.strip().upper() in FX_CURRENCIES else "JPY"
        meta = FX_CURRENCIES[cur_key]
        tranches_in = [
            (b1_amt if b1_amt is not None else meta["b1"][0], b1_rate if b1_rate is not None else meta["b1"][1]),
            (b2_amt if b2_amt is not None else meta["b2"][0], b2_rate if b2_rate is not None else meta["b2"][1]),
            (b3_amt, b3_rate),
        ]
        res = calculate_fx_tranches(currency=cur_key, target_foreign=target, tranches=tranches_in, spot_rate=spot)

        fx_bundle = fx_reference().get("rates", {})
        js_presets = {
            k: {
                "default_target": v["default_target"],
                "bundled_rate": round(float(fx_bundle.get(k, v["b2"][1])), 4),
                "b1": v["b1"],
                "b2": v["b2"],
            }
            for k, v in FX_CURRENCIES.items()
        }
        cur_opts = "".join(
            f'<option value="{k}"{" selected" if res["currency"] == k else ""}>{escape(v["name"])}</option>'
            for k, v in FX_CURRENCIES.items()
        )
        batch_rows = ""
        for idx, b in enumerate(res["tranches"], 1):
            batch_rows += (
                f"<tr><th scope='row'>第 {idx} 批</th>"
                f"<td><input type='number' name='b{idx}_amt' class='fx-b-amt' value='{b['amount']:g}' min='0' step='any' aria-label='第 {idx} 批外幣金額'></td>"
                f"<td><input type='number' name='b{idx}_rate' class='fx-b-rate' value='{b['rate']:g}' min='0' step='any' aria-label='第 {idx} 批成交匯率'></td>"
                f"<td class='fx-b-twd'>NT$ {b['twd']:,}</td></tr>"
            )
        sc_rows = ""
        for sc in res["scenarios"]:
            cls = ' class="uw-row-highlight"' if abs(sc["factor"] - 1.0) < 0.001 else ""
            delta_str = f"+NT$ {sc['delta_twd']:,}" if sc["delta_twd"] > 0 else (f"-NT$ {-sc['delta_twd']:,}" if sc["delta_twd"] < 0 else "基準")
            sc_rows += (
                f"<tr{cls}><th scope='row'>{escape(sc['label'])}</th><td>{sc['rate']:g}</td>"
                f"<td>NT$ {sc['gap_twd']:,}</td><td><strong>NT$ {sc['total_twd']:,}</strong></td>"
                f"<td>{sc['blended_rate']:g}（{delta_str}）</td></tr>"
            )

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
{safe_json_block("uw-fx-presets", js_presets)}
<section class="uw-tool-card" aria-labelledby="fx-heading">
  <div class="uw-tool-header">
    <h2 id="fx-heading">計算分批換匯均價與待補資金缺口</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製試算網址</button>
  </div>
  <form method="get" action="/tools/fx-budget-planner" data-tool-form="fx-planner">
    <div class="uw-form-grid">
      <label class="uw-field"><span>外幣幣別</span><select name="currency" id="fx-currency">{cur_opts}</select></label>
      <label class="uw-field"><span>學期目標外幣總額</span><input type="number" name="target" id="fx-target" value="{res['target_foreign']:g}" min="0" step="any"></label>
      <label class="uw-field"><span>剩餘缺口參考現價匯率</span><input type="number" name="spot" id="fx-spot" value="{res['spot_rate']:g}" min="0.0001" step="any"></label>
      <div class="uw-form-actions uw-nojs-only"><button type="submit" class="uw-btn uw-btn-primary">計算成本</button></div>
    </div>

    <div class="uw-kpi-grid" aria-live="polite">
      <div class="uw-kpi-box uw-kpi-highlight">
        <span class="uw-kpi-label">已換部位加權均價</span>
        <strong class="uw-kpi-value" data-fx-out="avg-rate">{res['avg_bought_rate']:g}</strong>
        <span class="uw-kpi-tag" data-fx-out="bought">已換 {res['currency']} {res['bought_foreign']:,.0f}（進度 {res['progress_pct']:g}%）</span>
      </div>
      <div class="uw-kpi-box">
        <span class="uw-kpi-label">已投入台幣成本</span>
        <strong class="uw-kpi-value" data-fx-out="spent-twd">NT$ {res['spent_twd']:,}</strong>
        <span class="uw-kpi-tag">歷史分批換匯合計</span>
      </div>
      <div class="uw-kpi-box">
        <span class="uw-kpi-label">尚缺外幣資金缺口</span>
        <strong class="uw-kpi-value" data-fx-out="gap-foreign">{res['currency']} {res['gap_foreign']:,.0f}</strong>
        <span class="uw-kpi-tag" data-fx-out="gap-twd">現價補齊約需 NT$ {res['base_gap_twd']:,}</span>
      </div>
      <div class="uw-kpi-box">
        <span class="uw-kpi-label">預估完換總台幣支出</span>
        <strong class="uw-kpi-value" data-fx-out="total-twd">NT$ {res['base_total_twd']:,}</strong>
        <span class="uw-kpi-tag" data-fx-out="blended">整體均價 {res['base_blended_rate']:g}</span>
      </div>
    </div>

    <div class="uw-table-wrap" tabindex="0" role="region" aria-label="已換匯外幣批次紀錄表">
      <table class="uw-data-table" id="fx-batch-table">
        <caption class="uw-sr-only">已購入外幣各批次金額與匯率明細表</caption>
        <thead>
          <tr><th scope="col">批次</th><th scope="col">已換入外幣金額</th><th scope="col">成交匯率（台幣／1 外幣）</th><th scope="col">折合台幣成本</th></tr>
        </thead>
        <tbody id="fx-batch-tbody">{batch_rows}</tbody>
      </table>
    </div>
    <div class="uw-status-bar">
      <span>台銀牌告基準參考日：{escape(res['fx_date'])}（可手動改填網銀即期優惠匯率）</span>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" id="fx-add-batch">＋ 新增換匯批次</button>
    </div>
  </form>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer" open>
    <summary>剩餘外幣缺口匯率波動敏感度情境表（-5% ～ +10%）</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="剩餘外幣缺口匯率敏感度情境表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">尚缺外幣部位於不同匯率變動下之台幣需求與總均價表</caption>
          <thead>
            <tr><th scope="col">匯率情境</th><th scope="col">假設現價</th><th scope="col">補齊缺口台幣</th><th scope="col">學期外幣總台幣成本</th><th scope="col">完換均價與差額</th></tr>
          </thead>
          <tbody id="fx-scenario-tbody">{sc_rows}</tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_FX)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_FX,
        )

    # 6. /tools/deadline-timezone-converter
    @router.api_route("/tools/deadline-timezone-converter", methods=["GET", "HEAD"])
    def tool_deadline_timezone_converter(
        tz: str = Query(default="Europe/Berlin"),
        deadline_date: str | None = Query(default=None),
        deadline_time: str | None = Query(default=None),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/deadline-timezone-converter"]
        res = convert_deadline_timezone(tz_name=tz, date_str=deadline_date, time_str=deadline_time)
        tz_opts = "".join(
            f'<option value="{escape(k)}"{" selected" if res["tz_name"] == k else ""}>{escape(v["label"])}</option>'
            for k, v in TIMEZONE_CATALOG.items()
        )
        ref_rows = ""
        for k in ("Asia/Tokyo", "Europe/Berlin", "Europe/London", "America/New_York", "America/Los_Angeles", "Australia/Sydney"):
            win = convert_deadline_timezone(tz_name=k, date_str="2027-01-15", time_str="23:59")
            sum_r = convert_deadline_timezone(tz_name=k, date_str="2027-06-15", time_str="23:59")
            ref_rows += (
                f"<tr><th scope='row'>{escape(TIMEZONE_CATALOG[k]['label'].split('（')[0])}</th>"
                f"<td>台灣 {escape(win['taipei_display'])}</td>"
                f"<td>台灣 {escape(sum_r['taipei_display'])}</td>"
                f"<td>{escape(TIMEZONE_CATALOG[k]['region_note'])}</td></tr>"
            )

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="tz-heading">
  <div class="uw-tool-header">
    <h2 id="tz-heading">輸入海外姊妹校截止時間換算台灣時刻</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製換算連結</button>
  </div>
  <form method="get" action="/tools/deadline-timezone-converter" class="uw-form-grid" data-tool-form="deadline-tz">
    <label class="uw-field"><span>海外姊妹校所在時區</span><select name="tz" id="tz-select">{tz_opts}</select></label>
    <label class="uw-field"><span>當地截止日期</span><input type="date" name="deadline_date" id="tz-date" value="{escape(res['date_str'])}"></label>
    <label class="uw-field"><span>當地截止時刻（24 小時制）</span><input type="time" name="deadline_time" id="tz-time" value="{escape(res['time_str'])}"></label>
    <div class="uw-form-actions uw-nojs-only"><button type="submit" class="uw-btn uw-btn-primary">換算台灣時間</button></div>
  </form>

  <div class="uw-kpi-grid" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">對應台灣截止時間（UTC+8）</span>
      <strong class="uw-kpi-value" data-tz-out="taipei">{escape(res['taipei_display'])}</strong>
      <span class="uw-kpi-tag" data-tz-out="weekday">{escape(res['taipei_weekday'])} · {escape(res['diff_label'])}</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">當地冬夏令時制判定</span>
      <strong class="uw-kpi-value" data-tz-out="dst">{escape(res['dst_badge'])}</strong>
      <span class="uw-kpi-tag" data-tz-out="local">{escape(res['local_display'])}</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">建議安全送件線（提前 24h）</span>
      <strong class="uw-kpi-value" data-tz-out="safe">{escape(res['safe_submit_display'])}</strong>
      <span class="uw-kpi-tag">避開跨國上傳系統塞車</span>
    </div>
  </div>
  <div class="uw-status-bar">
    <span data-tz-out="note">{escape(res['region_note'])}</span>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer" open>
    <summary>主要交換地區「當地 23:59 截止」冬令與夏令台灣時間速查表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="主要交換地區冬夏令時間換算台灣時間對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">各主要交換地區冬令與夏令時間換算台灣時間對照表</caption>
          <thead>
            <tr><th scope="col">海外時區</th><th scope="col">1 月截止（2027-01-15 23:59）</th><th scope="col">6 月截止（2027-06-15 23:59）</th><th scope="col">時差與夏令時間提醒</th></tr>
          </thead>
          <tbody>{ref_rows}</tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_TIMEZONE)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_TIMEZONE,
        )

    # 7. /tools/application-checklist
    @router.api_route("/tools/application-checklist", methods=["GET", "HEAD"])
    def tool_application_checklist(
        country: str = Query(default="japan"),
        stage: str = Query(default="all"),
        military: str = Query(default="no"),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/application-checklist"]
        res = build_application_checklist(country=country, stage=stage, military=military)
        country_opts = "".join(
            f'<option value="{k}"{" selected" if res["country"] == k else ""}>{escape(v)}</option>'
            for k, v in CHECKLIST_COUNTRIES.items()
        )
        stage_opts = "".join(
            f'<option value="{k}"{" selected" if res["stage"] == k else ""}>{escape(v)}</option>'
            for k, v in CHECKLIST_STAGES.items()
        )
        mil_opts = (
            f'<option value="no"{" selected" if res["military"] == "no" else ""}>免辦役男出境（非役男／已役畢）</option>'
            f'<option value="yes"{" selected" if res["military"] == "yes" else ""}>具在學役男身分（加列兵役專案核准項）</option>'
        )
        rows_html = ""
        for item in res["items"]:
            rows_html += (
                f"<tr data-ck-id='{escape(item['id'])}' data-ck-stage='{escape(item['stage'])}'>"
                f"<td><input type='checkbox' class='uw-ck-box' value='{escape(item['id'])}' aria-label='已備妥 {escape(item['title'])}'></td>"
                f"<td><span class='uw-inline-badge'>{escape(item['stage_label'])}</span></td>"
                f"<th scope='row'><strong>{escape(item['title'])}</strong><div class='uw-cell-sub'>{escape(item['spec'])}</div></th>"
                f"<td>{escape(item['timing'])}</td></tr>"
            )

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="ck-heading">
  <div class="uw-tool-header">
    <h2 id="ck-heading">{escape(res['country_label'])}交換必備核對清單（已完成 <span id="ck-done-count">0</span> / <span id="ck-total-count">{res['total_count']}</span> 項）</h2>
    <div class="uw-btn-group">
      <button type="button" class="uw-btn uw-btn-sm uw-btn-primary" data-print-page>列印 ／ 存成 PDF</button>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" id="ck-reset-btn">清除勾選</button>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製網址</button>
    </div>
  </div>
  <form method="get" action="/tools/application-checklist" class="uw-form-grid" data-tool-form="app-checklist">
    <label class="uw-field"><span>交換目的地國家</span><select name="country" id="ck-country">{country_opts}</select></label>
    <label class="uw-field"><span>顯示申請階段</span><select name="stage" id="ck-stage">{stage_opts}</select></label>
    <label class="uw-field"><span>兵役身分檢核</span><select name="military" id="ck-military">{mil_opts}</select></label>
    <div class="uw-form-actions"><button type="submit" class="uw-btn uw-btn-outline">切換清單</button></div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="交換申請與行前文件核對清單表">
    <table class="uw-data-table uw-checklist-table" id="ck-table">
      <caption class="uw-sr-only">{escape(res['country_label'])}交換申請文件與行前必備核對表</caption>
      <thead>
        <tr><th scope="col">完成</th><th scope="col">階段</th><th scope="col">檢核項目與準備規格</th><th scope="col">建議時點</th></tr>
      </thead>
      <tbody id="ck-tbody">{rows_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  {render_faq_section(FAQS_CHECKLIST)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_CHECKLIST,
        )

    # 8. /tools/study-plan-checker
    @router.api_route("/tools/study-plan-checker", methods=["GET", "HEAD"])
    def tool_study_plan_checker(
        target_words: int = Query(default=800, ge=200, le=2500),
        draft: str = Query(default=""),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/study-plan-checker"]
        res = analyze_study_plan(draft, target_words=target_words)
        target_opts = "".join(
            f'<option value="{w}"{" selected" if res["target_words"] == w else ""}>目標上限 {w} 字詞</option>'
            for w in (500, 800, 1000, 1200, 1500)
        )
        dim_rows = ""
        for d in res["dimensions"]:
            badge = '<span class="uw-tag-ok">已涵蓋線索</span>' if d["passed"] else '<span class="uw-tag-warn">建議補強</span>'
            dim_rows += (
                f"<tr data-sp-dim='{escape(d['id'])}'><th scope='row'>{escape(d['title'])}</th>"
                f"<td class='sp-dim-badge'>{badge}</td>"
                f"<td class='sp-dim-kw'>{escape(d['matched_keywords'])}</td>"
                f"<td>{escape(d['advice'])}</td></tr>"
            )

        textarea_val = "" if res["using_sample"] else res["text"]
        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
{safe_json_block("uw-sp-sample", {"sample": DEFAULT_SAMPLE_STUDY_PLAN, "dimensions": STUDY_PLAN_DIMENSIONS})}
<section class="uw-tool-card" aria-labelledby="sp-heading">
  <div class="uw-tool-header">
    <h2 id="sp-heading">貼上讀書計畫草稿即時體檢（本機計算不留存）</h2>
    <div class="uw-btn-group">
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" id="sp-load-sample">帶入英文範例</button>
      <a class="uw-btn uw-btn-sm uw-btn-primary" href="/#writing-assistant">前往站內申請文件工作台</a>
    </div>
  </div>
  <form method="get" action="/tools/study-plan-checker" data-tool-form="study-plan">
    <div class="uw-form-grid">
      <label class="uw-field"><span>簡章字數上限基準</span><select name="target_words" id="sp-target">{target_opts}</select></label>
      <div class="uw-form-actions uw-nojs-only"><button type="submit" class="uw-btn uw-btn-primary">執行體檢</button></div>
    </div>
    <label class="uw-field uw-field-full">
      <span>讀書計畫草稿（支援英文 Study Plan 或中文讀書計畫）</span>
      <textarea name="draft" id="sp-textarea" rows="8" placeholder="在此貼上你的英文或中文讀書計畫草稿，即時檢查字數、段落與四大要素…">{escape(textarea_val)}</textarea>
    </label>
  </form>

  <div class="uw-kpi-grid" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">英文字數 ／ 中文字數</span>
      <strong class="uw-kpi-value" data-sp-out="words">{res['en_words']} words</strong>
      <span class="uw-kpi-tag" data-sp-out="cjk">中文字元 {res['cjk_chars']} 字</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">四大核心要素涵蓋度</span>
      <strong class="uw-kpi-value" data-sp-out="dims">{res['hit_dims']} / 4 項</strong>
      <span class="uw-kpi-tag">動機・選課・背景・返國</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">段落數與句長可讀性</span>
      <strong class="uw-kpi-value" data-sp-out="paras">{res['paragraph_count']} 段</strong>
      <span class="uw-kpi-tag" data-sp-out="sent">平均每句 {res['avg_sentence_words']} words</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">篇幅狀態評估</span>
      <strong class="uw-kpi-value uw-kpi-value-sm" data-sp-out="len-status">{escape(res['length_status'])}</strong>
    </div>
  </div>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="讀書計畫四大核心結構檢核結果表">
    <table class="uw-data-table">
      <caption class="uw-sr-only">交換讀書計畫四大核心段落要素檢核表</caption>
      <thead>
        <tr><th scope="col">結構維度</th><th scope="col">檢核狀態</th><th scope="col">偵測到之關鍵字詞</th><th scope="col">寫作強化建議</th></tr>
      </thead>
      <tbody id="sp-dim-tbody">{dim_rows}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  {render_faq_section(FAQS_STUDYPLAN)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_STUDYPLAN,
        )

    # 9. /tools/fact-sheet-worksheet
    @router.api_route("/tools/fact-sheet-worksheet", methods=["GET", "HEAD"])
    def tool_fact_sheet_worksheet(
        school_a: str = Query(default="目標校 A（例：德國慕尼黑工大 TUM）"),
        school_b: str = Query(default="目標校 B（例：日本早稻田大學）"),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/fact-sheet-worksheet"]
        rows_html = ""
        md_lines = [f"| 核對欄位 | {school_a} | {school_b} |", "| --- | --- | --- |"]
        for f in FACT_SHEET_FIELDS:
            md_lines.append(f"| {f['zh']} ({f['en']}) | {f['ex_a']} | {f['ex_b']} |")
            rows_html += (
                f"<tr data-fs-row='{escape(f['id'])}'>"
                f"<th scope='row'><strong>{escape(f['zh'])}</strong><div class='uw-cell-sub'>{escape(f['en'])} — {escape(f['hint'])}</div></th>"
                f"<td><input type='text' class='fs-input-a' data-fs-label='{escape(f['zh'])}' value='{escape(f['ex_a'])}' aria-label='{escape(f['zh'])} 目標校 A'></td>"
                f"<td><input type='text' class='fs-input-b' value='{escape(f['ex_b'])}' aria-label='{escape(f['zh'])} 目標校 B'></td></tr>"
            )
        md_preview = "\n".join(md_lines)

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="fs-heading">
  <div class="uw-tool-header">
    <h2 id="fs-heading">邊看國外 Fact Sheet 邊填寫 12 項必查欄位</h2>
    <div class="uw-btn-group">
      <button type="button" class="uw-btn uw-btn-sm uw-btn-primary" data-copy-target="fs-md-output">複製 Markdown 對照表</button>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-print-page>列印整理表</button>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" id="fs-clear-btn">清空重填</button>
    </div>
  </div>
  <form method="get" action="/tools/fact-sheet-worksheet" class="uw-form-grid" data-tool-form="fact-sheet">
    <label class="uw-field"><span>目標姊妹校 A 名稱</span><input type="text" name="school_a" id="fs-school-a" value="{escape(school_a)}"></label>
    <label class="uw-field"><span>目標姊妹校 B 名稱</span><input type="text" name="school_b" id="fs-school-b" value="{escape(school_b)}"></label>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="姊妹校 Fact Sheet 12 項關鍵欄位整理表">
    <table class="uw-data-table" id="fs-table">
      <caption class="uw-sr-only">海外姊妹校交換簡章 Fact Sheet 十二項必讀欄位對照表</caption>
      <thead>
        <tr><th scope="col">Fact Sheet 關鍵欄位與核對重點</th><th scope="col" id="fs-th-a">{escape(school_a)}</th><th scope="col" id="fs-th-b">{escape(school_b)}</th></tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
  <pre class="uw-sr-only" id="fs-md-output">{escape(md_preview)}</pre>
</section>

<div class="uw-drawers-stack">
  {render_faq_section(FAQS_FACTSHEET)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_FACTSHEET,
        )

    # 10. /tools/email-template-generator
    @router.api_route("/tools/email-template-generator", methods=["GET", "HEAD"])
    def tool_email_template_generator(
        scene: str = Query(default="prof_rec"),
        recipient: str = Query(default="王明哲 教授 / Prof. Ming-Che Wang"),
        student: str = Query(default="資管系三年級 陳宥廷 / Yu-Ting Chen"),
        course: str = Query(default="資料庫系統（114-1 修習，成績 A+） / Database Systems"),
        target_school: str = Query(default="德國慕尼黑工業大學（TUM）2027 秋季交換計畫"),
        deadline: str = Query(default="2026-11-30"),
    ) -> HTMLResponse:
        spec = WAVE3_TOOL_SPECS["/tools/email-template-generator"]
        res = generate_bilingual_emails(
            scene=scene,
            recipient=recipient,
            student=student,
            course=course,
            target_school=target_school,
            deadline=deadline,
        )
        scene_opts = "".join(
            f'<option value="{k}"{" selected" if res["scene"] == k else ""}>{escape(v)}</option>'
            for k, v in EMAIL_SCENES.items()
        )
        zh_full = f"主旨：{res['zh_subject']}\n\n{res['zh_body']}"
        en_full = f"Subject: {res['en_subject']}\n\n{res['en_body']}"

        body = f"""<h1>{escape(spec.h1)}</h1>
{render_switcher(spec.path)}
<section class="uw-tool-card" aria-labelledby="em-heading">
  <div class="uw-tool-header">
    <h2 id="em-heading">填寫基本資訊即時產生中英信件草稿</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製範本網址</button>
  </div>
  <form method="get" action="/tools/email-template-generator" class="uw-form-grid" data-tool-form="email-gen">
    <label class="uw-field"><span>信件情境</span><select name="scene" id="em-scene">{scene_opts}</select></label>
    <label class="uw-field"><span>收件師長／單位稱謂</span><input type="text" name="recipient" id="em-recipient" value="{escape(res['recipient'])}"></label>
    <label class="uw-field"><span>系級與學生姓名</span><input type="text" name="student" id="em-student" value="{escape(res['student'])}"></label>
    <label class="uw-field"><span>修課名稱／詢問主題</span><input type="text" name="course" id="em-course" value="{escape(res['course'])}"></label>
    <label class="uw-field"><span>目標交換大學與學期</span><input type="text" name="target_school" id="em-target" value="{escape(res['target_school'])}"></label>
    <label class="uw-field"><span>收件／申請截止日期</span><input type="date" name="deadline" id="em-deadline" value="{escape(res['deadline'])}"></label>
    <div class="uw-form-actions uw-nojs-only"><button type="submit" class="uw-btn uw-btn-primary">產生信件</button></div>
  </form>

  <div class="uw-dual-grid">
    <div class="uw-email-panel">
      <div class="uw-citation-head">
        <strong>繁體中文版信件草稿</strong>
        <button type="button" class="uw-btn uw-btn-sm uw-btn-primary" data-copy-target="em-zh-out">複製中文信件</button>
      </div>
      <pre class="uw-citation-code" id="em-zh-out">{escape(zh_full)}</pre>
    </div>
    <div class="uw-email-panel">
      <div class="uw-citation-head">
        <strong>English Email Draft</strong>
        <button type="button" class="uw-btn uw-btn-sm uw-btn-primary" data-copy-target="em-en-out">複製英文信件</button>
      </div>
      <pre class="uw-citation-code" id="em-en-out">{escape(en_full)}</pre>
    </div>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>寄信前必檢禮儀與建議隨信附件一覽表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="推薦信與詢問信寄件禮儀檢核表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">推薦信邀約與國際處聯繫信件必附附件與禮儀檢核表</caption>
          <thead>
            <tr><th scope="col">聯絡對象</th><th scope="col">建議提前時程</th><th scope="col">建議隨信附件與資訊</th></tr>
          </thead>
          <tbody>
            <tr><th scope="row">授課教授／導師（推薦信）</th><td>截止前 4–6 週</td><td>歷年成績單（標示修課等第）、1 頁式申請方向與讀書計畫摘要、明確截止日與送件方式</td></tr>
            <tr><th scope="row">台灣母校國際處</th><td>收件期間上班日</td><td>註明學號系級、已查閱之簡章頁碼或合作校全名，條列具體問題避免籠統提問</td></tr>
            <tr><th scope="row">海外姊妹校國際處</th><td>獲提名或報名前</td><td>使用正式英文撰寫，先確認 Fact Sheet 未載明後再禮貌詢問課程代碼或宿舍規定</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_EMAIL)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), (spec.short_title, spec.path)],
            FAQS_EMAIL,
        )


def _safe_tv_json(safe_json_block: Callable[[str, Any], str], dl_by_id: Mapping[str, str]) -> str:
    return safe_json_block("uw-tv-school-deadlines", dl_by_id)
