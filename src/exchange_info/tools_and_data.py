"""Server-rendered SEO tools (/tools/...) and database-driven annual data pages (/data/...)."""
from __future__ import annotations

import json
import threading
from collections.abc import Callable, Mapping
from html import escape
from time import monotonic
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from .models import CatalogueSourceStatus, PartnerUniversity
from .tools_and_data_core import (
    BUDGET_COUNTRY_TEMPLATES,
    ECTS_SYSTEM_LABELS,
    ENGLISH_CONCORDANCE_BANDS,
    GPA_SCALE_TABLE,
    JLPT_LEVEL_INFO,
    MANDATORY_DISCLAIMER,
    TERM_OPTIONS,
    WAVE1_PATHS,
    WAVE1_SPECS,
    PageMetaSpec,
    build_all_71_school_deadlines,
    build_reverse_timeline,
    build_reverse_timeline_ics,
    calculate_exchange_budget,
    convert_credits,
    convert_gpa_summary,
    convert_language_score,
    dataset_schema,
    faq_page_schema,
    match_partner_schools_for_home,
    render_compliance_strip,
    render_core_summary_and_citation_box,
    render_faq_section,
    safe_https_or_http_url,
    summarize_71_schools_overview,
    web_application_schema,
)
from .data_wave3 import register_wave3_data_routes
from .tools_and_data_wave2 import register_wave2_routes
from .tools_wave3 import register_wave3_tool_routes
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university


def _safe_json_block(element_id: str, payload: Any) -> str:
    encoded = (
        json.dumps(payload, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return f'<script type="application/json" id="{escape(element_id)}">{encoded}</script>'


def _official_link(url: str | None, label: str) -> str:
    safe = safe_https_or_http_url(url)
    if not safe:
        return f"<span>{escape(label)}（待確認）</span>"
    return f'<a href="{escape(safe)}" rel="noopener noreferrer" data-official-source>{escape(label)}</a>'


_SWITCHER_GROUPS: tuple[tuple[str, str, str, tuple[tuple[str, str], ...]], ...] = (
    (
        "成績與效期（4 款）",
        "成績與效期",
        "/tools/ects-credit-converter",
        (
            ("/tools/ects-credit-converter", "ECTS 學分換算器"),
            ("/tools/gpa-converter", "台灣大學 GPA 換算器"),
            ("/tools/language-score-converter", "語言檢定換算與選校查詢"),
            ("/tools/test-validity-checker", "語檢成績效期檢查器"),
        ),
    ),
    (
        "選校雷達與志願（4 款）",
        "選校與志願",
        "/tools/eligibility-matcher",
        (
            ("/tools/eligibility-matcher", "30 秒交換選校雷達"),
            ("/tools/reverse-partner-search", "海外名校反查器"),
            ("/tools/partner-compare", "姊妹校並排 PK 比較器"),
            ("/tools/preference-ranker", "志願序風險檢查器"),
        ),
    ),
    (
        "預算換匯與獎助（3 款）",
        "預算與獎助",
        "/tools/exchange-budget-calculator",
        (
            ("/tools/exchange-budget-calculator", "交換學生預算試算器"),
            ("/tools/fx-budget-planner", "外幣換匯分批成本計算機"),
            ("/tools/scholarship-finder", "交換獎學金快速篩選器"),
        ),
    ),
    (
        "時程・兵役與備審（7 款）",
        "時程與備審",
        "/tools/timeline-generator",
        (
            ("/tools/timeline-generator", "交換申請倒推時程產生器"),
            ("/tools/deadline-timezone-converter", "海外截止跨時區換算器"),
            ("/tools/military-service-exit-checker", "役男出境交換檢查器"),
            ("/tools/application-checklist", "申請與行前必備核對清單"),
            ("/tools/study-plan-checker", "英文讀書計畫體檢器"),
            ("/tools/fact-sheet-worksheet", "姊妹校 Fact Sheet 整理表"),
            ("/tools/email-template-generator", "推薦信與國際處信件範本"),
        ),
    ),
    (
        "年度公開交換數據（8 頁）",
        "公開數據 (8)",
        "/data",
        (
            ("/data/taiwan-exchange-overview", "全台 71 校交換資源總覽表"),
            ("/data/deadlines", "全台 71 校交換截止日總表"),
            ("/data/language-requirements", "交換語言門檻各分數段統計"),
            ("/data/top-partner-universities", "全台締約海外名校 Top 50"),
            ("/data/toeic-friendly-partners", "多益友善交換學校清單"),
            ("/data/destination-costs", "熱門交換國家預算與補助總表"),
            ("/data/english-taught-partners", "歐陸與日韓英語授課名校庫"),
            ("/data/scholarships-taiwan", "台灣交換獎學金與補助總表"),
        ),
    ),
)


def _render_switcher(current_path: str) -> str:
    cat_pills = [
        f'<a class="uw-tool-tab" href="/tools"'
        + (' aria-current="page"' if current_path == "/tools" else "")
        + ">全部工具 (18)</a>"
    ]
    optgroups = [
        '<optgroup label="總覽入口">'
        + f'<option value="/tools"{" selected" if current_path == "/tools" else ""}>交換免費工具總覽（18 款）</option>'
        + f'<option value="/data"{" selected" if current_path == "/data" else ""}>台灣交換公開數據總覽（8 頁）</option>'
        + "</optgroup>"
    ]
    for group_title, pill_label, lead_path, items in _SWITCHER_GROUPS:
        member_paths = {p for p, _ in items} | ({lead_path} if lead_path == "/data" else set())
        is_exact = current_path == lead_path
        is_in_group = current_path in member_paths
        cls = "uw-tool-tab" + (" is-cat-active" if (is_in_group and not is_exact) else "")
        aria = ' aria-current="page"' if is_exact else ""
        cat_pills.append(f'<a class="{cls}" href="{escape(lead_path)}"{aria}>{escape(pill_label)}</a>')

        opts_html = "".join(
            f'<option value="{escape(p)}"{" selected" if p == current_path else ""}>{escape(lbl)}</option>'
            for p, lbl in items
        )
        optgroups.append(f'<optgroup label="{escape(group_title)}">{opts_html}</optgroup>')

    return (
        '<div class="uw-tool-switcher">'
        f'<nav class="uw-tool-tabs" aria-label="工具與數據分類">{"".join(cat_pills)}</nav>'
        '<div class="uw-tool-jump">'
        f'<select id="uw-quick-jump" data-quick-jump-select aria-label="快速切換任一工具或公開數據頁">{"".join(optgroups)}</select>'
        "</div>"
        "</div>"
    )


def append_tools_and_data_llms(origin: str) -> list[str]:
    """Return Markdown sections for /llms.txt and /llms-full.txt."""
    lines = ["", "## 交換學生免費工具", ""]
    tool_paths = [
        "/tools",
        *(
            p
            for _, _, lead, items in _SWITCHER_GROUPS
            if lead != "/data"
            for p, _ in items
        ),
    ]
    for path in tool_paths:
        spec = WAVE1_SPECS[path]
        lines.append(f"- [{spec.h1}]({origin}{spec.path}): {spec.description}")
    lines += ["", "## 年度公開交換數據", ""]
    data_paths = ["/data", *(p for p, _ in _SWITCHER_GROUPS[-1][3])]
    for path in data_paths:
        spec = WAVE1_SPECS[path]
        lines.append(f"- [{spec.h1}]({origin}{spec.path}): {spec.description}")
    return lines


# ---------------------------------------------------------------------------
# Page FAQs (3-5 per page, strictly factual and compliant)
# ---------------------------------------------------------------------------

FAQS_TOOLS_HUB: tuple[tuple[str, str], ...] = (
    (
        "使用交換學生小工具需要註冊或登入帳號嗎？",
        "不需要。所有公開換算與試算工具皆免登入即可直接在瀏覽器使用，亦不會讀取個人隱私資料；若後續想儲存個人選校清單與文件進度，再切換至站內申請工作台即可。",
    ),
    (
        "工具算出的學分、GPA 或語言對照結果可以直接當作學校審查結論嗎？",
        "不行。各大學教務處、國際處與海外接待校各有獨立採計標準與單科門檻，試算結果僅供選校初篩與準備規劃參考，實際資格、名額與期限以各校最新官方公告為準。",
    ),
    (
        "語言檢定分數換算器裡的合作校數量是怎麼算出來的？",
        "系統直接讀取全台 71 所大學之合作校公開資料，將「明確列載該檢定且門檻低於或等於輸入分數」與「列載同語系其他檢定／待確認」分開統計，不推論未公告的採計規則。",
    ),
    (
        "倒推時程表匯出的 .ics 檔案支援哪些行事曆軟體？",
        "匯出檔案採用國際標準 iCalendar（RFC 5545）格式，可直接匯入 Apple 行事曆、Google Calendar、Microsoft Outlook 與常見手機行事曆應用程式，並內建提前提醒。",
    ),
)

FAQS_ECTS: tuple[tuple[str, str], ...] = (
    (
        "歐洲 1 個 ECTS 學分通常可以抵免台灣大學幾學分？",
        "台灣多數大專校院與歐洲姊妹校對照時，常見基準為 2 ECTS 折算台灣 1 學分（歐洲一學期全日制 30 ECTS 約對應台灣 15 學分）；部分學校會依實際授課時數審核，實際抵免以各校最新官方公告為準。",
    ),
    (
        "去歐洲交換一學期最少要修多少 ECTS 才符合規定？",
        "需同時確認台灣母校國際處最低修課規定（常見折合台灣 6 至 9 學分，即約 12 至 18 ECTS）與歐洲接待校簽證要求（常見 20 至 30 ECTS），兩者取較高者準備最穩妥。",
    ),
    (
        "為什麼建議比最低學分門檻多選 1 門課（約 5 至 6 ECTS）？",
        "歐洲大學常將整學期成績集中於期末筆試或口試，若僅剛好選滿最低門檻，一旦單科未通過或停開，可能影響母校交換規定或獎學金核銷，多選 1 門課較安心。",
    ),
    (
        "歐洲姊妹校開設的密集語言課可以算進學分嗎？",
        "視台灣母校與所屬系所規定而定。部分母校允許計入交換最低修課學分或一般選修，也有系所規定須為專業學部課程才可抵免，實際採計以各校最新官方公告為準。",
    ),
)

FAQS_GPA: tuple[tuple[str, str], ...] = (
    (
        "母校採用 4.3 制 GPA，申請 4.0 制海外姊妹校時可以直接等比例換算嗎？",
        "切勿直接乘以 4.0/4.3。在多數國際成績轉換慣例中，4.3 制的 A+（4.3）與 A（4.0）轉為 4.0 制時皆記為 4.0，其餘等第多維持相同積點；建議展開逐科學分加權精算表比對，並以接待校最新官方公告為準。",
    ),
    (
        "什麼是德國巴伐利亞公式？分數越低越好嗎？",
        "是的，德國大學成績採 1.0 至 5.0 制，1.0 代表最優異、4.0 代表及格。公式為 1 + 3 × (最高分 - 你的分數) ÷ (最高分 - 最低及格分)，計算結果直接取至小數點後第 1 位不進位。",
    ),
    (
        "總平均直接套表轉 GPA，跟逐科轉 GPA 再加權平均為什麼不同？",
        "因為百分制轉等第屬於階梯區間。正式審查均以母校英文成績單列印數值或接待校指定算法為準。",
    ),
    (
        "交換申請表填寫 GPA 時可以自己四捨五入嗎？",
        "多數國內外大學明文規定 GPA 不得自行四捨五入進位。請如實填寫母校正式英文成績單上的數值，實際資格以各校最新官方公告為準。",
    ),
)

FAQS_LANGUAGE: tuple[tuple[str, str], ...] = (
    (
        "多益（TOEIC）850 分可以直接申請只寫 IELTS 6.0 或 TOEFL 79 的歐美學校嗎？",
        "不一定，多數歐美大學在交換簡章中僅採計學術型測驗（TOEFL iBT 或 IELTS Academic），不接受 TOEIC 替代。報名前務必逐校核對簡章。",
    ),
    (
        "TOEFL MyBest Scores（拼分）或 Home Edition 可以用來申請交換嗎？",
        "許多台灣母校與海外接待校明文規定不採計 TOEFL MyBest Scores、Home Edition，亦不採計 IELTS One Skill Retake 或 General Training 組別，報考前請先查閱簡章。",
    ),
    (
        "除了語言總分達標之外，還需要檢查哪些細節？",
        "請確認聽說讀寫單科最低門檻、成績單 2 年效期是否涵蓋母校收件日與姊妹校網報日，以及擬選修學院是否有更高門檻。",
    ),
    (
        "為什麼日檢 JLPT 沒有換算成托福或雅思分數？",
        "JLPT 評量日語能力，與英語檢定分屬不同授課語組，不可互相替代。選擇 JLPT 時，系統會篩選合作校名單中明確列載日檢 N1–N5 門檻之學校。",
    ),
)

FAQS_BUDGET: tuple[tuple[str, str], ...] = (
    (
        "出國交換期間還要繳海外姊妹校的學費嗎？",
        "透過母校免學費交換名額錄取者，通常僅需繳交台灣母校原本學雜費；若選擇自費研修（Visiting）方案則須另付海外學費。實際收費標準以各校最新官方公告為準。",
    ),
    (
        "為什麼交換預算要做 ±10% 匯率波動試算？",
        "從校內報名到出國常相隔 8 至 12 個月，外幣匯率波動 5%–10% 相當常見，預留匯差緩衝可避免行前產生資金缺口。",
    ),
    (
        "姊妹校簡章上的財力證明金額就等於實際生活費嗎？",
        "財力證明是簽證或入學審查的存款下限，通常不含來回機票、安家採買與初期租屋押金，實際支出視城市物價與宿位而定。",
    ),
    (
        "學海飛颺或校內交換獎學金會在出國前全部拿到嗎？",
        "多數獎學金於出國前核發約 70%–80%，尾款須待返國完成學分採認與心得後核銷，機票與押金仍須先行備妥週轉金。",
    ),
)

FAQS_TIMELINE: tuple[tuple[str, str], ...] = (
    (
        "想在大三上（秋季班）出國交換，什麼時候要參加母校校內甄選？",
        "多數台灣大學會在出國前一年的 9 月至 12 月舉辦次年秋季班校內甄選；建議大二升大三暑假前考出語言檢定成績。",
    ),
    (
        "通過母校校內交換甄選，就代表已經被國外姊妹校錄取了嗎？",
        "通過校內甄選代表取得母校提名資格（Nomination），後續仍須向海外接待校完成網報並取得正式入學許可（LoA）；實際資格與期限以各校最新官方公告為準。",
    ),
    (
        "母校尚未公布新一期確切截止日時，倒推時程表怎麼用？",
        "可先用系統預設收件月份或自行輸入預估截止日倒推語檢與備審節點，待國際處正式公告後再微調基準日。",
    ),
    (
        "具役男身分的學生在時程上要注意什麼？",
        "收到姊妹校入學許可後，須預留時間由母校協助造冊申請役男出國研修核准，切勿在核准前直接持觀光方式出境。",
    ),
)

FAQS_DATA_HUB: tuple[tuple[str, str], ...] = (
    (
        "公開數據頁的資料來源是什麼？",
        "直接彙整自全台 71 所公私立大學國際事務處公開網頁、交換甄選簡章與合作校名冊，每筆紀錄保留官方來源網址與查核日期。",
    ),
    (
        "媒體報導或報告可以引用本頁統計表格嗎？",
        "歡迎免費引用，請展開頁面下方引用格式標明出處與網址，並保留「合作校頁面數不等於當期開放名額，實際資格、名額與期限以各校最新官方公告為準」說明。",
    ),
    (
        "為什麼合作校頁面數不等於當期可申請名額數？",
        "各校公開名單可能同時包含當期甄選名單、歷年締約總表與院系級參考，實際開缺名額仍須查閱當期簡章。",
    ),
)

FAQS_OVERVIEW_DATA: tuple[tuple[str, str], ...] = (
    (
        "「合作校頁面數」是如何去重計算的？",
        "同一母校對同一海外大學若設有多個語組或學院方案，系統歸併為 1 個合作校頁面，避免重複計算。",
    ),
    (
        "表格裡的 TOEIC 或 JLPT 校數代表什麼？",
        "代表該母校公開合作校欄位中有明確寫出該檢定門檻的合作校數量；若統一寫於母校簡章總則，則歸入依簡章確認。",
    ),
    (
        "合作校數量較多的大學競爭就比較小嗎？",
        "不一定，熱門國家名校仍常集中大量第一志願，建議同時對照當期開缺名額與院系限制。",
    ),
)

FAQS_DEADLINES_DATA: tuple[tuple[str, str], ...] = (
    (
        "台灣各大學交換校內申請截止日主要集中在幾月？",
        "第一波主高峰落在每年 9 月至 12 月（次年秋季班／全學年），第二波落在 2 月至 3 月（春季班或二招）。",
    ),
    (
        "為什麼有些學校截止時間在下午 16:00 或中午 12:00？",
        "許多學校國際處配合行政上班與核章時間設定系統關閉時刻；未公告時刻者本表不自行推估 23:59，建議提前 1 至 2 天送件。",
    ),
    (
        "線上報名截止日與紙本核章截止日一定是同一天嗎？",
        "不一定，部分學校要求系所初審更早收件。實際資格、名額與期限以各校最新官方公告為準。",
    ),
)


# ---------------------------------------------------------------------------
# Router Registration & HTML Builders
# ---------------------------------------------------------------------------

def register_tools_and_data_routes(
    router: APIRouter,
    *,
    settings: Any,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    page_renderer: Callable[..., HTMLResponse],
    structured_data_fn: Callable[[dict], str],
    availability_labels: Mapping[str, str],
    assets_head: str,
) -> None:
    overview_lock = threading.Lock()
    overview_cache: dict[str, Any] = {"at": 0.0, "data": None}

    def get_cached_71_overview() -> dict[str, Any]:
        with overview_lock:
            if overview_cache["data"] is not None and monotonic() - overview_cache["at"] < 60.0:
                return overview_cache["data"]
            computed = summarize_71_schools_overview(catalogue_loader)
            overview_cache["at"] = monotonic()
            overview_cache["data"] = computed
            return computed

    def render_tool_page(
        spec: PageMetaSpec,
        body: str,
        breadcrumbs: list[tuple[str, str]],
        faqs: tuple[tuple[str, str], ...],
    ) -> HTMLResponse:
        schemas = (
            structured_data_fn(web_application_schema(settings.origin, spec))
            + structured_data_fn(faq_page_schema(settings.origin, spec.path, faqs))
        )
        return page_renderer(
            settings,
            spec.title,
            spec.description,
            spec.path,
            body,
            breadcrumbs,
            extra_head=assets_head + schemas,
        )

    def render_data_page(
        spec: PageMetaSpec,
        body: str,
        breadcrumbs: list[tuple[str, str]],
        faqs: tuple[tuple[str, str], ...],
        *,
        variables: tuple[str, ...],
        keywords: tuple[str, ...],
        date_modified: str | None = None,
    ) -> HTMLResponse:
        ds = dataset_schema(
            settings.origin,
            spec,
            variables=variables,
            keywords=keywords,
            date_modified=date_modified or "2026-10-28",
        )
        schemas = structured_data_fn(ds) + structured_data_fn(faq_page_schema(settings.origin, spec.path, faqs))
        return page_renderer(
            settings,
            spec.title,
            spec.description,
            spec.path,
            body,
            breadcrumbs,
            extra_head=assets_head + schemas,
        )

    # -----------------------------------------------------------------------
    # 1. /tools — Tools Hub
    # -----------------------------------------------------------------------
    @router.api_route("/tools", methods=["GET", "HEAD"])
    def tools_hub() -> HTMLResponse:
        spec = WAVE1_SPECS["/tools"]
        cards = (
            ("/tools/eligibility-matcher", "選校雷達", "30 秒交換選校雷達", "母校＋語檢＋GPA＋預算＋洲別即時篩選達標合作校"),
            ("/tools/reverse-partner-search", "雙向反查", "海外姊妹校締約母校反查器", "輸入國外名校，反查全台 71 校哪幾所大學有簽約"),
            ("/tools/partner-compare", "選校對決", "海外姊妹校並排 PK 比較器", "2～3 校並排比較門檻・名額・預算並匯出圖卡"),
            ("/tools/preference-ranker", "策略排序", "交換志願序風險配比檢查器", "夢幻・落點・保底排序檢查零名額與志願倒掛"),
            ("/tools/ects-credit-converter", "學分折抵", "ECTS 學分換算器", "歐洲・台灣・美加・日韓學分即時換算"),
            ("/tools/gpa-converter", "成績對照", "台灣大學 GPA 換算器", "百分制・4.3・4.0・德國巴伐利亞公式"),
            ("/tools/language-score-converter", "71 校比對", "語言檢定換算與選校查詢", "輸入托福・雅思・多益・日檢查達標合作校"),
            ("/tools/test-validity-checker", "效期把關", "語言檢定成績效期檢查器", "比對校內收件日與海外提名日之 2 年效期緩衝"),
            ("/tools/exchange-budget-calculator", "12 國模板", "交換學生預算試算器", "月生活費・機票簽證・±10% 匯率波動試算"),
            ("/tools/fx-budget-planner", "分批換匯", "外幣換匯分批成本與缺口計算機", "彙算已換外幣批次均價與待補外幣台幣需求"),
            ("/tools/scholarship-finder", "官方獎助", "交換獎學金與補助資格篩選器", "依身分與地區篩選學海飛颺・惜珠・JASSO 等補助"),
            ("/tools/timeline-generator", ".ics 行事曆", "交換申請倒推時程產生器", "依母校與出發學期自動排定 8 個準備節點"),
            ("/tools/deadline-timezone-converter", "冬夏令時差", "海外截止跨時區與夏令時間換算器", "歐美日韓澳截止時刻自動換算準確台灣時間"),
            ("/tools/military-service-exit-checker", "役政檢核", "役男出境交換時程與文件檢查器", "區分 4 個月短期出境與學校推薦專案核准程序"),
            ("/tools/application-checklist", "支援列印 PDF", "交換申請文件與行前必備核對清單", "依國家與三階段動態產生檢核表並暫存進度"),
            ("/tools/study-plan-checker", "結構診斷", "英文讀書計畫結構與字數體檢器", "即時檢查字數、句長與動機／選課／返國四大要素"),
            ("/tools/fact-sheet-worksheet", "12 欄對照", "姊妹校 Fact Sheet 互動重點整理表", "逐項填寫國外簡章 12 大關鍵條件並匯出 Markdown"),
            ("/tools/email-template-generator", "中英雙語", "推薦信邀約與國際處詢問信範本", "輸入師長稱謂與截止日一鍵產生得體中英信件"),
        )
        cards_html = "".join(
            f"""<li class="uw-hub-card">
  <div>
    <span class="uw-card-tag">{escape(tag)}</span>
    <h2><a href="{escape(path)}">{escape(title)}</a></h2>
    <p>{escape(desc)}</p>
  </div>
  <a class="uw-card-cta" href="{escape(path)}">開啟 <span aria-hidden="true">→</span></a>
</li>"""
            for path, tag, title, desc in cards
        )
        summary_rows = "".join(
            f"<tr><th scope='row'><a href='{escape(path)}'>{escape(title)}</a></th><td>{escape(tag)}</td><td>{escape(desc)}</td></tr>"
            for path, tag, title, desc in cards
        )

        body = f"""<h1>{escape(spec.h1)}</h1>
{_render_switcher(spec.path)}
<ul class="uw-hub-grid">{cards_html}</ul>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>18 款免登入交換工具功能與用途一覽表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="交換免費工具對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">UniWay 交換學生十八款免登入工具功能一覽</caption>
          <thead>
            <tr>
              <th scope="col">工具名稱</th>
              <th scope="col">定位類別</th>
              <th scope="col">核心用途與輸出</th>
            </tr>
          </thead>
          <tbody>{summary_rows}</tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_TOOLS_HUB)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(spec, body, [("首頁", "/"), ("交換免費工具", "/tools")], FAQS_TOOLS_HUB)

    # -----------------------------------------------------------------------
    # 2. /tools/ects-credit-converter
    # -----------------------------------------------------------------------
    @router.api_route("/tools/ects-credit-converter", methods=["GET", "HEAD"])
    def tool_ects_converter(
        amount: float = Query(default=30.0, ge=0.0, le=240.0),
        system: str = Query(default="ects"),
        ratio: float = Query(default=2.0, ge=1.0, le=4.0),
        min_tw: float = Query(default=6.0, ge=0.0, le=30.0),
    ) -> HTMLResponse:
        spec = WAVE1_SPECS["/tools/ects-credit-converter"]
        res = convert_credits(amount=amount, source_system=system, ects_per_tw=ratio, min_home_tw_credits=min_tw)

        sys_options = "".join(
            f'<option value="{escape(k)}"{" selected" if res["source_system"] == k else ""}>{escape(v)}</option>'
            for k, v in ECTS_SYSTEM_LABELS.items()
        )
        ratio_options = "".join(
            f'<option value="{val}"{" selected" if abs(res["ects_per_tw"] - val) < 0.05 else ""}>{label}</option>'
            for val, label in (
                (2.0, "2 ECTS = 1 台灣學分（最常見）"),
                (1.5, "1.5 ECTS = 1 台灣學分"),
                (1.0, "1 ECTS = 1 台灣學分"),
            )
        )

        ref_rows = ""
        for ects_v, note in (
            (3, "小型工作坊或語言選修"),
            (5, "北歐、德國、荷蘭單門專業課"),
            (6, "法國、義大利、西班牙單門專業課"),
            (12, "約台灣 6 學分（部分母校低標）"),
            (18, "約台灣 9 學分（常見學期低標）"),
            (24, "歐洲交換常見選課量（4–5 門課）"),
            (30, "歐洲全日制標準一學期"),
            (60, "歐洲全日制標準一學年"),
        ):
            r_item = convert_credits(ects_v, "ects", 2.0, 6.0)
            ref_rows += (
                f"<tr><th scope='row'>{ects_v} ECTS</th>"
                f"<td>{r_item['tw_credits']:g} 學分</td>"
                f"<td>{r_item['us_semester_credits']:g} 學分</td>"
                f"<td>{r_item['jp_credits']:g} 単位</td>"
                f"<td>{r_item['workload_hours_low']}–{r_item['workload_hours_high']} 小時</td>"
                f"<td>{escape(note)}</td></tr>"
            )

        status_msg = (
            f"已達母校最低門檻（至少 {res['required_ects_for_home']:g} ECTS）"
            if res["meets_home_min"]
            else f"尚未達母校最低門檻（需至少 {res['required_ects_for_home']:g} ECTS）"
        )

        body = f"""<h1>{escape(spec.h1)}</h1>
{_render_switcher(spec.path)}

<section class="uw-tool-card" aria-labelledby="ects-calc-heading">
  <div class="uw-tool-header">
    <h2 id="ects-calc-heading">輸入學分即時換算</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製試算連結</button>
  </div>
  <form method="get" action="/tools/ects-credit-converter" class="uw-form-grid" data-tool-form="ects">
    <label class="uw-field">
      <span>學分制度</span>
      <select name="system" id="ects-system">{sys_options}</select>
    </label>
    <label class="uw-field">
      <span>學分數</span>
      <input type="number" name="amount" id="ects-amount" value="{res['input_amount']:g}" min="0" max="240" step="0.5" required>
    </label>
    <label class="uw-field">
      <span>折算比例</span>
      <select name="ratio" id="ects-ratio">{ratio_options}</select>
    </label>
    <label class="uw-field">
      <span>母校最低學分（台灣）</span>
      <input type="number" name="min_tw" id="ects-min-tw" value="{res['min_home_tw_credits']:g}" min="0" max="30" step="0.5">
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">計算</button>
    </div>
  </form>

  <div class="uw-kpi-grid" id="ects-results" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">台灣大學學分</span>
      <strong class="uw-kpi-value" data-out="tw">{res['tw_credits']:g} 學分</strong>
      <span class="uw-kpi-tag" data-out="ratio-note">{res['ects_per_tw']:g} ECTS = 1 學分</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">歐洲 ECTS</span>
      <strong class="uw-kpi-value" data-out="ects">{res['ects']:g} ECTS</strong>
      <span class="uw-kpi-tag" data-out="workload">{res['workload_hours_low']}–{res['workload_hours_high']} 小時</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">美國學期學分</span>
      <strong class="uw-kpi-value" data-out="us">{res['us_semester_credits']:g} 學分</strong>
      <span class="uw-kpi-tag" data-out="us-q">學季制 {res['us_quarter_credits']:g} 學分</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">日本大學単位</span>
      <strong class="uw-kpi-value" data-out="jp">{res['jp_credits']:g} 単位</strong>
    </div>
  </div>

  <div class="uw-status-bar" id="ects-min-panel">
    <strong data-out="min-status">{escape(status_msg)}</strong>
    <span>母校門檻 <strong data-out="req-ects">{res['required_ects_for_home']:g} ECTS</strong> · 建議選修 <strong data-out="buf-ects">{res['recommended_ects_with_buffer']:g} ECTS</strong> 以上</span>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>常見 ECTS 與台灣／美國／日本學分對照表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="ECTS 與台灣美國日本學分對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">以常見基準 2 ECTS = 1 台灣學分估算之對照表</caption>
          <thead>
            <tr>
              <th scope="col">歐洲 ECTS</th>
              <th scope="col">台灣學分</th>
              <th scope="col">美國 Semester</th>
              <th scope="col">日本単位</th>
              <th scope="col">總學習時數</th>
              <th scope="col">常見課程規模</th>
            </tr>
          </thead>
          <tbody>{ref_rows}</tbody>
        </table>
      </div>
    </div>
  </details>

  <details class="uw-drawer">
    <summary>換算公式與各國學分制度說明</summary>
    <div class="uw-drawer-body">
      <ul>
        <li><strong>歐洲 ECTS：</strong>全日制 1 學年為 60 ECTS、1 學期為 30 ECTS，1 ECTS 約代表 25–30 小時總學習工作量。</li>
        <li><strong>台灣／美國學期制：</strong>最常見折算為 <code>台灣／美國學分 = ECTS ÷ 2</code>；美國學季制（Quarter）約為 <code>Semester × 1.5</code>。</li>
        <li><strong>日本単位：</strong>1 単位標準為 45 小時學修，歐日交換多採 <code>1 単位 ≈ 1.5–2 ECTS</code>。</li>
      </ul>
    </div>
  </details>

  {render_faq_section(FAQS_ECTS)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), ("ECTS 學分換算器", spec.path)],
            FAQS_ECTS,
        )

    # -----------------------------------------------------------------------
    # 3. /tools/gpa-converter
    # -----------------------------------------------------------------------
    @router.api_route("/tools/gpa-converter", methods=["GET", "HEAD"])
    def tool_gpa_converter(
        value: float = Query(default=82.5, ge=0.0, le=100.0),
        scale: str = Query(default="percent"),
        max_score: float = Query(default=100.0, ge=1.0, le=100.0),
        min_pass: float = Query(default=60.0, ge=0.0, le=90.0),
    ) -> HTMLResponse:
        spec = WAVE1_SPECS["/tools/gpa-converter"]
        res = convert_gpa_summary(value=value, scale=scale, max_score=max_score, min_pass=min_pass)

        scale_opts = "".join(
            f'<option value="{k}"{" selected" if res["scale"] == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("percent", "百分制（0–100 分）"),
                ("gpa43", "4.3 制 GPA"),
                ("gpa40", "4.0 制 GPA"),
            )
        )

        gpa_rows = "".join(
            f"<tr><th scope='row'>{escape(letter)}</th><td>{escape(pct)}</td><td>{g43:.1f}</td><td>{g40:.1f}</td><td>{escape(bav)}</td></tr>"
            for letter, pct, g43, g40, bav in GPA_SCALE_TABLE
        )

        body = f"""<h1>{escape(spec.h1)}</h1>
{_render_switcher(spec.path)}

<section class="uw-tool-card" aria-labelledby="gpa-calc-heading">
  <div class="uw-tool-header">
    <h2 id="gpa-calc-heading">總平均快速對照</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製試算連結</button>
  </div>
  <form method="get" action="/tools/gpa-converter" class="uw-form-grid" data-tool-form="gpa">
    <label class="uw-field">
      <span>成績制度</span>
      <select name="scale" id="gpa-scale">{scale_opts}</select>
    </label>
    <label class="uw-field">
      <span>輸入成績</span>
      <input type="number" name="value" id="gpa-value" value="{res['input_value']:g}" min="0" max="100" step="0.01" required>
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">換算</button>
    </div>
    <details class="uw-inline-drawer">
      <summary>德國巴伐利亞公式參數（預設滿分 100／及格 60）</summary>
      <div class="uw-inline-drawer-grid">
        <label class="uw-field">
          <span>滿分標準（Nmax）</span>
          <input type="number" name="max_score" id="gpa-max" value="{res['max_score']:g}" min="4" max="100" step="0.1">
        </label>
        <label class="uw-field">
          <span>最低及格分（Nmin）</span>
          <input type="number" name="min_pass" id="gpa-min" value="{res['min_pass']:g}" min="0" max="90" step="0.1">
        </label>
      </div>
    </details>
  </form>

  <div class="uw-kpi-grid" id="gpa-results" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">4.0 制 GPA</span>
      <strong class="uw-kpi-value" data-gpa-out="gpa40pm">{res['gpa_40_plusminus']:.2f} / 4.0</strong>
      <span class="uw-kpi-tag" data-gpa-out="gpa40std">四等第 {res['gpa_40_standard']:.2f}</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">4.3 制 GPA</span>
      <strong class="uw-kpi-value" data-gpa-out="gpa43">{res['gpa_43']:.2f} / 4.3</strong>
      <span class="uw-kpi-tag" data-gpa-out="pct">約 {res['approx_percent']:.1f} 分</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">德國巴伐利亞制（1.0 最優）</span>
      <strong class="uw-kpi-value" data-gpa-out="bavarian">{escape(res['bavarian_grade'])}</strong>
    </div>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>逐科學分加權 GPA 精算表（多科目計算）</summary>
    <div class="uw-drawer-body">
      <div class="uw-tool-header">
        <strong>輸入各科學分與百分制成績</strong>
        <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" id="gpa-add-row">+ 新增科目</button>
      </div>
      <div class="uw-table-wrap">
        <table class="uw-data-table" id="gpa-course-table">
          <caption class="uw-sr-only">逐科學分加權試算表</caption>
          <thead>
            <tr>
              <th scope="col">課程名稱</th>
              <th scope="col">學分數</th>
              <th scope="col">百分制成績</th>
              <th scope="col">4.3 積點</th>
              <th scope="col">4.0 積點</th>
            </tr>
          </thead>
          <tbody id="gpa-course-tbody">
            <tr>
              <td><input type="text" value="科目 1" aria-label="課程名稱"></td>
              <td><input type="number" class="gpa-c-credit" value="3" min="0.5" max="15" step="0.5" aria-label="學分數"></td>
              <td><input type="number" class="gpa-c-score" value="92" min="0" max="100" step="1" aria-label="百分制成績"></td>
              <td class="gpa-c-43">4.3</td>
              <td class="gpa-c-40">4.0</td>
            </tr>
            <tr>
              <td><input type="text" value="科目 2" aria-label="課程名稱"></td>
              <td><input type="number" class="gpa-c-credit" value="3" min="0.5" max="15" step="0.5" aria-label="學分數"></td>
              <td><input type="number" class="gpa-c-score" value="83" min="0" max="100" step="1" aria-label="百分制成績"></td>
              <td class="gpa-c-43">3.7</td>
              <td class="gpa-c-40">3.7</td>
            </tr>
            <tr>
              <td><input type="text" value="科目 3" aria-label="課程名稱"></td>
              <td><input type="number" class="gpa-c-credit" value="2" min="0.5" max="15" step="0.5" aria-label="學分數"></td>
              <td><input type="number" class="gpa-c-score" value="75" min="0" max="100" step="1" aria-label="百分制成績"></td>
              <td class="gpa-c-43">3.0</td>
              <td class="gpa-c-40">3.0</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="uw-weighted-summary" id="gpa-weighted-summary">
        總學分 <strong>8.0</strong> ｜ 平均 <strong>84.38</strong> ｜ 4.3 制 <strong>3.75</strong> ｜ 4.0 制 <strong>3.64</strong> ｜ 德制 <strong>2.1</strong>
      </p>
    </div>
  </details>

  <details class="uw-drawer">
    <summary>台灣常見等第制（4.3／4.0／百分制／德國制）對照表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="GPA 與德國分數對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">台灣大專校院常見等第區間對照表</caption>
          <thead>
            <tr>
              <th scope="col">等第</th>
              <th scope="col">百分制區間</th>
              <th scope="col">4.3 制</th>
              <th scope="col">4.0 制</th>
              <th scope="col">德國巴伐利亞制</th>
            </tr>
          </thead>
          <tbody>{gpa_rows}</tbody>
        </table>
      </div>
    </div>
  </details>

  <details class="uw-drawer">
    <summary>換算公式說明</summary>
    <div class="uw-drawer-body">
      <ul>
        <li><strong>加權 GPA：</strong><code>Σ（單科積點 × 學分）÷ 總學分</code>，優先以母校英文成績單原載數值為準。</li>
        <li><strong>4.3 轉 4.0 制：</strong><code>A+ (4.3)</code> 與 <code>A (4.0)</code> 均對應 <code>4.0</code>，勿直接乘以 <code>4.0 / 4.3</code>。</li>
        <li><strong>德國巴伐利亞公式：</strong><code>1 + 3 × (Nmax - Nd) ÷ (Nmax - Nmin)</code>，取至小數第 1 位不進位。</li>
      </ul>
    </div>
  </details>

  {render_faq_section(FAQS_GPA)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), ("台灣大學 GPA 換算器", spec.path)],
            FAQS_GPA,
        )

    # -----------------------------------------------------------------------
    # 4. /tools/language-score-converter (+ JSON live endpoint)
    # -----------------------------------------------------------------------
    @router.get("/tools/language-score-converter.json")
    def tool_language_converter_json(
        home: str = Query(default="nccu"),
        test: str = Query(default="ielts"),
        score: str = Query(default="6.5"),
    ) -> JSONResponse:
        uni = resolve_university(home)
        if uni is None:
            raise HTTPException(404, "找不到這所母校")
        partners, _ = catalogue_loader(uni)
        conv = convert_language_score(test, score)
        matched = match_partner_schools_for_home(uni, partners, conv, availability_labels)
        return JSONResponse(
            {"conversion": conv, "match": matched},
            headers={"Cache-Control": "public, max-age=60", "X-Robots-Tag": "noindex, nofollow"},
        )

    @router.api_route("/tools/language-score-converter", methods=["GET", "HEAD"])
    def tool_language_converter(
        home: str = Query(default="nccu"),
        test: str = Query(default="ielts"),
        score: str = Query(default="6.5"),
    ) -> HTMLResponse:
        spec = WAVE1_SPECS["/tools/language-score-converter"]
        uni = resolve_university(home) or resolve_university("nccu") or SUPPORTED_UNIVERSITIES[0]
        partners, _ = catalogue_loader(uni)
        conv = convert_language_score(test, score)
        matched = match_partner_schools_for_home(uni, partners, conv, availability_labels)

        test_options = "".join(
            f'<option value="{k}"{" selected" if conv["test"] == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("ielts", "IELTS 雅思（4.0–9.0）"),
                ("toefl", "TOEFL iBT 托福（0–120）"),
                ("toeic", "TOEIC 多益（10–990）"),
                ("cefr", "CEFR 分級（A2–C2）"),
                ("jlpt", "JLPT 日檢（N5–N1）"),
            )
        )
        home_options = "".join(
            f'<option value="{escape(u.id)}"{" selected" if u.id == uni.id else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )

        def _render_sample_items(items: list[dict[str, Any]], empty_text: str) -> str:
            if not items:
                return f"<p>{escape(empty_text)}</p>"
            lis = "".join(
                f"""<li class="uw-partner-mini-card">
  <div class="uw-partner-mini-top">
    <a href="{escape(item['partner_url'])}"><strong>{escape(item['school_name'])}</strong></a>
    <span class="uw-mini-country">{escape(item['country'])}</span>
  </div>
  <p class="uw-mini-rule"><span class="uw-tag-ok">{escape(item['matched_rule'])}</span> · {escape(item['availability'])}</p>
</li>"""
                for item in items
            )
            return f'<ul class="uw-partner-mini-grid">{lis}</ul>'

        direct_html = _render_sample_items(
            matched["direct_samples"],
            f"目前無單獨列載 {conv['input_display']} 且低於此分數的合作校條目，可展開同級參考或查看母校完整名單。",
        )
        equiv_section = ""
        if not conv["is_japanese"]:
            equiv_items_html = _render_sample_items(
                matched["equiv_samples"],
                "目前無其他同級英語檢定合作校條目。",
            )
            equiv_section = f"""<details class="uw-drawer" id="lang-equiv-block">
  <summary>其他同級英語檢定參考合作校（<span data-lang-out="equiv-count">{matched['equiv_match_count']}</span> 所）</summary>
  <div class="uw-drawer-body"><div id="lang-equiv-list">{equiv_items_html}</div></div>
</details>"""

        concordance_rows = "".join(
            f"<tr><th scope='row'>CEFR {escape(b['cefr'])}</th>"
            f"<td>{b['ielts_min']:.1f}" + ("" if b["ielts_min"] == b["ielts_max"] else f" – {b['ielts_max']:.1f}") + "</td>"
            f"<td>{b['toefl_min']} – {b['toefl_max']}</td>"
            f"<td>{escape(b['toefl_new'])}</td>"
            f"<td>{b['toeic_min']} – {b['toeic_max']}</td></tr>"
            for b in ENGLISH_CONCORDANCE_BANDS
        )
        jlpt_rows = "".join(
            f"<tr><th scope='row'>JLPT {lvl}</th><td>{escape(info['cefr_ref'])}</td><td>{escape(info['desc'])}</td></tr>"
            for lvl, info in JLPT_LEVEL_INFO.items()
        )

        raw_score_display = conv["jlpt_level"] if conv["is_japanese"] else (
            conv["cefr"].replace("CEFR ", "") if conv["test"] == "cefr" else (
                f"{conv['numeric_ielts']:.1f}" if conv["test"] == "ielts" else str(int(round(
                    conv["numeric_toefl"] if conv["test"] == "toefl" else conv["numeric_toeic"]
                )))
            )
        )

        body = f"""<h1>{escape(spec.h1)}</h1>
{_render_switcher(spec.path)}

<section class="uw-tool-card" aria-labelledby="lang-calc-heading">
  <div class="uw-tool-header">
    <h2 id="lang-calc-heading">輸入成績比對合作校</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製查詢連結</button>
  </div>
  <form method="get" action="/tools/language-score-converter" class="uw-form-grid" data-tool-form="language">
    <label class="uw-field">
      <span>就讀母校</span>
      <select name="home" id="lang-home">{home_options}</select>
    </label>
    <label class="uw-field">
      <span>檢定類別</span>
      <select name="test" id="lang-test">{test_options}</select>
    </label>
    <label class="uw-field">
      <span>分數／等級</span>
      <input type="text" name="score" id="lang-score" value="{escape(raw_score_display)}" placeholder="如 6.5、85、800、B2、N2" required>
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">查詢</button>
    </div>
  </form>

  <div class="uw-kpi-grid" id="lang-conv-results" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">CEFR 能力分級</span>
      <strong class="uw-kpi-value" data-lang-out="cefr">{escape(conv['cefr'])}</strong>
      <span class="uw-kpi-tag" data-lang-out="input-display">{escape(conv['input_display'])}</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">IELTS 參考區間</span>
      <strong class="uw-kpi-value" data-lang-out="ielts">{escape(conv['ielts_range'])}</strong>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">TOEFL iBT 參考區間</span>
      <strong class="uw-kpi-value" data-lang-out="toefl">{escape(conv['toefl_range'])}</strong>
      <span class="uw-kpi-tag" data-lang-out="toefl-new">新制 {escape(conv['toefl_new'])}</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">TOEIC 聽讀參考</span>
      <strong class="uw-kpi-value" data-lang-out="toeic">{escape(conv['toeic_range'])}</strong>
    </div>
  </div>

  <div class="uw-db-match-panel" id="lang-db-panel" aria-live="polite">
    <div class="uw-db-match-head">
      <h3><span data-lang-out="home-name">{escape(matched['home_name'])}</span> 合作校比對（共 <span data-lang-out="total-pages">{matched['total_partner_pages']}</span> 所）</h3>
      <div class="uw-btn-group">
        <a class="uw-btn uw-btn-primary uw-btn-sm" id="lang-home-link" href="{escape(matched['home_school_url'])}">{escape(matched['home_short_name'])}完整名單</a>
        <a class="uw-btn uw-btn-outline uw-btn-sm" id="lang-planner-link" href="{escape(matched['home_planner_url'])}">互動選校</a>
      </div>
    </div>

    <div class="uw-stat-strip">
      <div class="uw-stat-pill uw-stat-ok">
        <span>明確達標</span>
        <strong data-lang-out="direct-count">{matched['direct_match_count']} 所</strong>
      </div>
      <div class="uw-stat-pill">
        <span>同級其他檢定</span>
        <strong data-lang-out="equiv-stat">{matched['equiv_match_count']} 所</strong>
      </div>
      <div class="uw-stat-pill">
        <span>高於目前分數</span>
        <strong data-lang-out="below-count">{matched['below_threshold_count']} 所</strong>
      </div>
      <div class="uw-stat-pill">
        <span>依簡章總則／他語種</span>
        <strong data-lang-out="unconfirmed-count">{matched['unconfirmed_or_other_count']} 所</strong>
      </div>
    </div>

    <div id="lang-direct-list">{direct_html}</div>
  </div>
</section>

<div class="uw-drawers-stack">
  {equiv_section}
  <details class="uw-drawer">
    <summary>英語檢定（CEFR／IELTS／TOEFL／TOEIC）與日檢 JLPT 對照表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="英語檢定與 CEFR 分數對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">英語檢定與 CEFR 參考區間表</caption>
          <thead>
            <tr>
              <th scope="col">CEFR</th>
              <th scope="col">IELTS</th>
              <th scope="col">TOEFL iBT</th>
              <th scope="col">TOEFL 6 分制</th>
              <th scope="col">TOEIC 聽讀</th>
            </tr>
          </thead>
          <tbody>{concordance_rows}</tbody>
        </table>
      </div>
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="日檢 JLPT 對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">JLPT 日檢與赴日交換門檻表</caption>
          <thead>
            <tr>
              <th scope="col">JLPT 級別</th>
              <th scope="col">CEFR 參考</th>
              <th scope="col">常見適用方案</th>
            </tr>
          </thead>
          <tbody>{jlpt_rows}</tbody>
        </table>
      </div>
    </div>
  </details>

  {render_faq_section(FAQS_LANGUAGE)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), ("語言檢定分數換算器", spec.path)],
            FAQS_LANGUAGE,
        )

    # -----------------------------------------------------------------------
    # 5. /tools/exchange-budget-calculator
    # -----------------------------------------------------------------------
    @router.api_route("/tools/exchange-budget-calculator", methods=["GET", "HEAD"])
    def tool_budget_calculator(
        country: str = Query(default="japan"),
        months: int | None = Query(default=None, ge=1, le=12),
        rate: float | None = Query(default=None, gt=0.0, le=500.0),
        housing: float | None = Query(default=None, ge=0.0),
        food: float | None = Query(default=None, ge=0.0),
        transport: float | None = Query(default=None, ge=0.0),
        other: float | None = Query(default=None, ge=0.0),
        one_time: float | None = Query(default=None, ge=0.0),
        scholarship: float | None = Query(default=None, ge=0.0),
    ) -> HTMLResponse:
        spec = WAVE1_SPECS["/tools/exchange-budget-calculator"]
        calc = calculate_exchange_budget(
            country_key=country,
            months=months,
            fx_rate=rate,
            housing=housing,
            food=food,
            transport=transport,
            other=other,
            one_time_twd=one_time,
            scholarship_twd=scholarship,
        )

        country_opts = "".join(
            f'<option value="{escape(k)}"{" selected" if calc["country_key"] == k else ""}>{escape(v["name"])}（{escape(v["currency"])}）</option>'
            for k, v in BUDGET_COUNTRY_TEMPLATES.items()
        )

        sc_rows = "".join(
            f"""<tr{" class='uw-row-highlight'" if sc['factor'] == 1.0 else ""}>
  <th scope="row">{escape(sc['label'])}</th>
  <td>1 {escape(calc['currency'])} = {sc['rate']:g} TWD</td>
  <td>NT$ {sc['monthly_twd']:,}</td>
  <td>NT$ {sc['living_total_twd']:,}</td>
  <td>NT$ {sc['gross_total_twd']:,}</td>
  <td><strong>NT$ {sc['net_self_twd']:,}</strong></td>
</tr>"""
            for sc in calc["scenarios"]
        )

        tpl_overview_rows = ""
        for k, tpl in BUDGET_COUNTRY_TEMPLATES.items():
            row_calc = calculate_exchange_budget(country_key=k)
            tpl_overview_rows += (
                f"<tr><th scope='row'>{escape(tpl['name'])}</th>"
                f"<td>{escape(tpl['currency'])}（{row_calc['bundled_rate']:g}）</td>"
                f"<td>{tpl['currency']} {row_calc['monthly_foreign']:,.0f}</td>"
                f"<td>NT$ {row_calc['base_monthly_twd']:,}</td>"
                f"<td>NT$ {tpl['one_time_twd']:,}</td>"
                f"<td>NT$ {row_calc['base_gross_twd']:,}</td></tr>"
            )

        js_templates = {
            k: {
                **v,
                "bundled_rate": calculate_exchange_budget(country_key=k)["bundled_rate"],
            }
            for k, v in BUDGET_COUNTRY_TEMPLATES.items()
        }

        share_summary_text = (
            f"【UniWay 交換預算試算】{calc['template_name']}（{calc['months']} 個月）\n"
            f"・每月外幣生活費：{calc['currency']} {calc['monthly_foreign']:,.0f}\n"
            f"・基準匯率（1 {calc['currency']} = {calc['rate']:g} TWD）總支出：NT$ {calc['base_gross_twd']:,}（含機票簽證等一次性 NT$ {calc['one_time_twd']:,}）\n"
            f"・扣除預估補助 NT$ {calc['scholarship_twd']:,} 後淨自備款：NT$ {calc['base_net_twd']:,}\n"
            f"・匯率 +10% 安全緩衝需多準備：NT$ {calc['fx_buffer_delta_twd']:,}\n"
            f"・試算工具：{settings.origin}{spec.path}（{MANDATORY_DISCLAIMER}）"
        )

        body = f"""<h1>{escape(spec.h1)}</h1>
{_render_switcher(spec.path)}
{_safe_json_block("uw-budget-templates", js_templates)}

<section class="uw-tool-card" aria-labelledby="budget-calc-heading">
  <div class="uw-tool-header">
    <h2 id="budget-calc-heading">選擇國家與月數即時估算</h2>
    <div class="uw-btn-group">
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-target="budget-summary-copy">複製明細</button>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製網址</button>
    </div>
  </div>
  <form method="get" action="/tools/exchange-budget-calculator" class="uw-form-grid" data-tool-form="budget">
    <label class="uw-field">
      <span>目的地國家</span>
      <select name="country" id="b-country">{country_opts}</select>
    </label>
    <label class="uw-field">
      <span>交換月數</span>
      <input type="number" name="months" id="b-months" value="{calc['months']}" min="1" max="12" step="1">
    </label>
    <label class="uw-field">
      <span>參考匯率（1 <span data-b-out="cur-code">{escape(calc['currency'])}</span> 兌台幣）</span>
      <input type="number" name="rate" id="b-rate" value="{calc['rate']:g}" min="0.0001" max="500" step="any">
    </label>
    <label class="uw-field">
      <span>預估補助折抵（TWD）</span>
      <input type="number" name="scholarship" id="b-scholarship" value="{calc['scholarship_twd']}" min="0" step="1000">
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">計算</button>
    </div>

    <details class="uw-inline-drawer">
      <summary>自訂細項費用（住宿・飲食・交通・醫保・機票簽證）</summary>
      <div class="uw-inline-drawer-grid">
        <label class="uw-field">
          <span>每月住宿（<span data-b-out="cur-code-2">{escape(calc['currency'])}</span>）</span>
          <input type="number" name="housing" id="b-housing" value="{calc['housing']:g}" min="0" step="any">
        </label>
        <label class="uw-field">
          <span>每月飲食日用</span>
          <input type="number" name="food" id="b-food" value="{calc['food']:g}" min="0" step="any">
        </label>
        <label class="uw-field">
          <span>每月當地交通</span>
          <input type="number" name="transport" id="b-transport" value="{calc['transport']:g}" min="0" step="any">
        </label>
        <label class="uw-field">
          <span>每月醫保與雜支</span>
          <input type="number" name="other" id="b-other" value="{calc['other']:g}" min="0" step="any">
        </label>
        <label class="uw-field">
          <span>機票簽證一次性（TWD）</span>
          <input type="number" name="one_time" id="b-onetime" value="{calc['one_time_twd']}" min="0" step="500">
        </label>
      </div>
    </details>
  </form>

  <div class="uw-kpi-grid" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">扣補助後淨自備款</span>
      <strong class="uw-kpi-value" data-b-out="net-twd">NT$ {calc['base_net_twd']:,}</strong>
      <span class="uw-kpi-tag" data-b-out="fx-delta">匯率 +10% 多備 NT$ {calc['fx_buffer_delta_twd']:,}</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">交換總支出</span>
      <strong class="uw-kpi-value" data-b-out="gross-twd">NT$ {calc['base_gross_twd']:,}</strong>
      <span class="uw-kpi-tag" data-b-out="months-label">{calc['months']} 個月＋行前費用</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">每月外幣生活費</span>
      <strong class="uw-kpi-value" data-b-out="monthly-foreign">{escape(calc['currency'])} {calc['monthly_foreign']:,.0f}</strong>
      <span class="uw-kpi-tag" data-b-out="monthly-twd">約 NT$ {calc['base_monthly_twd']:,}／月</span>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">建議緊急預備金</span>
      <strong class="uw-kpi-value" data-b-out="reserve-twd">NT$ {calc['emergency_reserve_twd']:,}</strong>
    </div>
  </div>
  <pre id="budget-summary-copy" hidden>{escape(share_summary_text)}</pre>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>±10% 匯率波動情境敏感度表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="正負10%匯率波動敏感度試算表">
        <table class="uw-data-table" id="b-scenario-table">
          <caption class="uw-sr-only">外幣匯率變動 -10%、0%、+10% 對總支出與自備款影響</caption>
          <thead>
            <tr>
              <th scope="col">匯率情境</th>
              <th scope="col">試算匯率</th>
              <th scope="col">每月台幣</th>
              <th scope="col">整期生活費</th>
              <th scope="col">總支出</th>
              <th scope="col">淨自備款</th>
            </tr>
          </thead>
          <tbody id="b-scenario-tbody">{sc_rows}</tbody>
        </table>
      </div>
    </div>
  </details>

  <details class="uw-drawer">
    <summary>12 個熱門交換國家一學期參考費用總表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="12國一學期預算參考對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">12 國規劃起點模板概覽</caption>
          <thead>
            <tr>
              <th scope="col">目的地</th>
              <th scope="col">幣別與匯率</th>
              <th scope="col">每月外幣</th>
              <th scope="col">每月新台幣</th>
              <th scope="col">行前費用</th>
              <th scope="col">一學期總支出</th>
            </tr>
          </thead>
          <tbody>{tpl_overview_rows}</tbody>
        </table>
      </div>
    </div>
  </details>

  {render_faq_section(FAQS_BUDGET)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), ("交換學生預算試算器", spec.path)],
            FAQS_BUDGET,
        )

    # -----------------------------------------------------------------------
    # 6. /tools/timeline-generator (+ .ics calendar endpoint)
    # -----------------------------------------------------------------------
    @router.get("/tools/timeline-generator.ics", response_class=PlainTextResponse)
    def tool_timeline_ics(
        school: str = Query(default="ntu"),
        term: str = Query(default="2027-fall"),
        deadline: str | None = Query(default=None),
    ) -> PlainTextResponse:
        filename, content = build_reverse_timeline_ics(
            school_id=school,
            term_key=term,
            custom_deadline=deadline,
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

    @router.api_route("/tools/timeline-generator", methods=["GET", "HEAD"])
    def tool_timeline_generator(
        school: str = Query(default="ntu"),
        term: str = Query(default="2027-fall"),
        deadline: str | None = Query(default=None),
    ) -> HTMLResponse:
        spec = WAVE1_SPECS["/tools/timeline-generator"]
        plan = build_reverse_timeline(school_id=school, term_key=term, custom_deadline=deadline)
        all_deadlines = build_all_71_school_deadlines()

        school_opts = "".join(
            f'<option value="{escape(u.id)}"{" selected" if u.id == plan["school_id"] else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )
        term_opts = "".join(
            f'<option value="{escape(k)}"{" selected" if k == plan["term_key"] else ""}>{escape(v["label"])}</option>'
            for k, v in TERM_OPTIONS.items()
        )

        milestone_items = "".join(
            f"""<li class="uw-timeline-step">
  <div class="uw-timeline-date">
    <span class="uw-timeline-offset">{escape(m['offset'])}</span>
    <time datetime="{escape(m['date'])}">{escape(m['date'])}</time>
  </div>
  <div class="uw-timeline-content">
    <h4>{escape(m['title'])}</h4>
  </div>
</li>"""
            for m in plan["milestones"]
        )

        js_school_map = {
            r["school_id"]: {
                "school_name": r["school_name"],
                "short_name": r["short_name"],
                "official_url": r["source_url"],
                "round_title": r["round_title"],
                "deadline_iso": r["deadline_iso"],
                "deadline_display": r["deadline_display"],
                "status_label": r["status_label"],
                "date_status_code": r["date_status_code"],
                "checked_date": r["checked_date"],
                "note": r["note"],
                "study_plan_note": r["study_plan_note"],
                "paper_note": r["paper_note"],
            }
            for r in all_deadlines
        }
        js_terms = {
            k: {
                "label": v["label"],
                "default_anchor": v["default_anchor"].isoformat(),
                "departure_date": v["departure_date"].isoformat(),
            }
            for k, v in TERM_OPTIONS.items()
        }

        body = f"""<h1>{escape(spec.h1)}</h1>
{_render_switcher(spec.path)}
{_safe_json_block("uw-timeline-schools", {"schools": js_school_map, "terms": js_terms})}

<section class="uw-tool-card" aria-labelledby="tl-calc-heading">
  <div class="uw-tool-header">
    <h2 id="tl-calc-heading">排定 8 個申請準備節點</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-primary uw-btn-sm" id="tl-ics-link" href="{escape(plan['ics_url'])}">下載 .ics 行事曆</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製時程連結</button>
    </div>
  </div>

  <form method="get" action="/tools/timeline-generator" class="uw-form-grid" data-tool-form="timeline">
    <label class="uw-field">
      <span>就讀母校</span>
      <select name="school" id="tl-school">{school_opts}</select>
    </label>
    <label class="uw-field">
      <span>出發學期</span>
      <select name="term" id="tl-term">{term_opts}</select>
    </label>
    <label class="uw-field">
      <span>校內截止基準日</span>
      <input type="date" name="deadline" id="tl-deadline" value="{escape(plan['anchor_date'])}">
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">更新時程</button>
    </div>
  </form>

  <div class="uw-status-bar" id="tl-school-record" aria-live="polite">
    <span><strong data-tl-out="school-name">{escape(plan['school_name'])}</strong> · 資料庫記載：<strong data-tl-out="rec-deadline">{escape(plan['school_recorded_deadline'])}</strong>（<span data-tl-out="rec-status">{escape(plan['school_recorded_status'])}</span>）</span>
    <span><a id="tl-official-link" href="{escape(plan['official_url'])}" rel="noopener noreferrer" data-official-source>國際處公告 ↗</a> · <a id="tl-school-page-link" href="/schools/{escape(plan['school_id'])}">合作校名單</a></span>
  </div>

  <ol class="uw-timeline-list" id="tl-milestone-list" aria-live="polite">{milestone_items}</ol>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>秋季班 vs 春季班標準申請時程對照表</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="秋季班與春季班交換申請標準時程對照表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">台灣大專校院常見兩季出國交換申請階段參考時程</caption>
          <thead>
            <tr>
              <th scope="col">準備階段</th>
              <th scope="col">秋季班出發（8–9 月）</th>
              <th scope="col">春季班出發（1–4 月）</th>
            </tr>
          </thead>
          <tbody>
            <tr><th scope="row">1. 語言檢定應考</th><td>前一年 5 – 9 月</td><td>前一年 10 月 – 當年 1 月</td></tr>
            <tr><th scope="row">2. 讀書計畫與推薦信</th><td>前一年 9 – 10 月</td><td>當年 1 – 2 月</td></tr>
            <tr><th scope="row">3. 校內甄選截止</th><td>前一年 10 – 12 月</td><td>當年 2 – 5 月</td></tr>
            <tr><th scope="row">4. 放榜與母校提名</th><td>前一年 12 月 – 當年 3 月</td><td>當年 4 – 9 月</td></tr>
            <tr><th scope="row">5. 姊妹校網報與宿舍</th><td>當年 2 – 5 月</td><td>當年 9 – 11 月</td></tr>
            <tr><th scope="row">6. 入學許可與簽證</th><td>當年 5 – 8 月</td><td>當年 11 月 – 次年 1 月</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </details>

  {render_faq_section(FAQS_TIMELINE)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_tool_page(
            spec,
            body,
            [("首頁", "/"), ("交換免費工具", "/tools"), ("交換申請倒推時程產生器", spec.path)],
            FAQS_TIMELINE,
        )

    # -----------------------------------------------------------------------
    # 7. /data — Open Data Hub
    # -----------------------------------------------------------------------
    @router.api_route("/data", methods=["GET", "HEAD"])
    def data_hub() -> HTMLResponse:
        spec = WAVE1_SPECS["/data"]
        overview = get_cached_71_overview()
        deadlines = build_all_71_school_deadlines()

        top5_schools = sorted(overview["schools"], key=lambda r: (-r["partner_page_count"], r["school_id"]))[:5]
        top5_rows = "".join(
            f"<tr><th scope='row'><a href='{escape(r['school_path'])}'>{escape(r['school_name'])}</a></th>"
            f"<td>{escape(r['sector'])}</td>"
            f"<td><strong>{r['partner_page_count']}</strong> 所</td>"
            f"<td>{r['country_count']} 國／地區</td>"
            f"<td>{_official_link(r['official_url'], '國際處來源')}</td></tr>"
            for r in top5_schools
        )

        body = f"""<h1>{escape(spec.h1)}</h1>
{_render_switcher(spec.path)}

<section class="uw-kpi-grid" aria-label="公開資料庫規模">
  <div class="uw-kpi-box uw-kpi-highlight">
    <span class="uw-kpi-label">收錄台灣大學</span>
    <strong class="uw-kpi-value">{overview['university_count']} 所</strong>
    <span class="uw-kpi-tag">公立 {overview['public_count']} · 私立 {overview['private_count']}</span>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">去重海外合作校</span>
    <strong class="uw-kpi-value">{overview['unique_foreign_institutions']:,} 所</strong>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">涵蓋國家與地區</span>
    <strong class="uw-kpi-value">{overview['unique_countries']} 個</strong>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">收錄校內截止日</span>
    <strong class="uw-kpi-value">{len(deadlines)} 校</strong>
  </div>
</section>

<ul class="uw-hub-grid">
  <li class="uw-hub-card">
    <div>
      <span class="uw-card-tag">71 校完整比較</span>
      <h2><a href="/data/taiwan-exchange-overview">全台 71 所大學交換資源總覽表</a></h2>
      <p>合作校規模排行、涵蓋國家數、托福／雅思／多益／日檢門檻統計與官方來源。</p>
    </div>
    <a class="uw-card-cta" href="/data/taiwan-exchange-overview">開啟數據表 <span aria-hidden="true">→</span></a>
  </li>
  <li class="uw-hub-card">
    <div>
      <span class="uw-card-tag">依月份查詢</span>
      <h2><a href="/data/deadlines">全台 71 校交換申請截止日總表</a></h2>
      <p>各校線上收件期限、受理狀態與國際處簡章連結，支援一鍵建立倒推時程。</p>
    </div>
    <a class="uw-card-cta" href="/data/deadlines">開啟截止日表 <span aria-hidden="true">→</span></a>
  </li>
  <li class="uw-hub-card">
    <div>
      <span class="uw-card-tag">分數段分布</span>
      <h2><a href="/data/language-requirements">交換語言門檻各分數段統計</a></h2>
      <p>統計多益 750/800/860、雅思 6.0/6.5、托福 79/88 與日檢 N2/N1 明確達標校數。</p>
    </div>
    <a class="uw-card-cta" href="/data/language-requirements">開啟門檻調查 <span aria-hidden="true">→</span></a>
  </li>
  <li class="uw-hub-card">
    <div>
      <span class="uw-card-tag">跨校排行</span>
      <h2><a href="/data/top-partner-universities">全台締約最多海外姊妹校 Top 50</a></h2>
      <p>依跨校締約數統計最受台灣各大學青睞的海外名校排行與各母校直達連結。</p>
    </div>
    <a class="uw-card-cta" href="/data/top-partner-universities">開啟 Top 50 <span aria-hidden="true">→</span></a>
  </li>
  <li class="uw-hub-card">
    <div>
      <span class="uw-card-tag">多益選校</span>
      <h2><a href="/data/toeic-friendly-partners">採計多益（TOEIC）交換合作校清單</a></h2>
      <p>篩選全台 71 校資料庫中明確列載 TOEIC 分數門檻之海外合作大學與國家統計。</p>
    </div>
    <a class="uw-card-cta" href="/data/toeic-friendly-partners">開啟多益清單 <span aria-hidden="true">→</span></a>
  </li>
  <li class="uw-hub-card">
    <div>
      <span class="uw-card-tag">12 國費用</span>
      <h2><a href="/data/destination-costs">熱門交換國家預算與官方補助總表</a></h2>
      <p>並排對照日、韓、德、法、英、美、荷、捷、星、澳、加、西學期生活費與官方補助。</p>
    </div>
    <a class="uw-card-cta" href="/data/destination-costs">開啟預算總表 <span aria-hidden="true">→</span></a>
  </li>
  <li class="uw-hub-card">
    <div>
      <span class="uw-card-tag">免二外交換</span>
      <h2><a href="/data/english-taught-partners">歐陸與日韓英語授課交換名校資料庫</a></h2>
      <p>彙整非英語系國家明確提供英語門檻或英語授課組別之海外大學與締約母校。</p>
    </div>
    <a class="uw-card-cta" href="/data/english-taught-partners">開啟英語名校庫 <span aria-hidden="true">→</span></a>
  </li>
  <li class="uw-hub-card">
    <div>
      <span class="uw-card-tag">獎助總覽</span>
      <h2><a href="/data/scholarships-taiwan">台灣交換學生獎學金與各國補助總表</a></h2>
      <p>整理學海飛颺、學海惜珠、外國政府機構及全台 71 校校內交換獎助資訊與官方入口。</p>
    </div>
    <a class="uw-card-cta" href="/data/scholarships-taiwan">開啟獎學金總表 <span aria-hidden="true">→</span></a>
  </li>
</ul>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>合作校規模前 5 大台灣母校快速預覽</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="合作校頁面規模前5大台灣母校預覽表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">依去重後海外合作校頁面數排序前 5 校</caption>
          <thead>
            <tr>
              <th scope="col">台灣母校</th>
              <th scope="col">屬性</th>
              <th scope="col">合作校頁面數</th>
              <th scope="col">涵蓋國家數</th>
              <th scope="col">官方來源</th>
            </tr>
          </thead>
          <tbody>{top5_rows}</tbody>
        </table>
      </div>
    </div>
  </details>

  {render_faq_section(FAQS_DATA_HUB)}
  {render_core_summary_and_citation_box(settings.origin, spec)}
  {render_compliance_strip()}
</div>"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data")],
            FAQS_DATA_HUB,
            variables=("海外合作校頁面數", "涵蓋國家地區數", "語言檢定門檻列載數", "校內申請截止日"),
            keywords=("台灣交換學生數據", "大學姊妹校統計", "出國交換截止日", "UniWay公開資料"),
        )

    # -----------------------------------------------------------------------
    # 8. /data/taiwan-exchange-overview
    # -----------------------------------------------------------------------
    @router.api_route("/data/taiwan-exchange-overview", methods=["GET", "HEAD"])
    def data_taiwan_exchange_overview(
        sector: str = Query(default="all"),
        sort: str = Query(default="partners"),
        q: str = Query(default=""),
    ) -> HTMLResponse:
        spec = WAVE1_SPECS["/data/taiwan-exchange-overview"]
        overview = get_cached_71_overview()
        rows = list(overview["schools"])

        q_clean = q.strip()
        if sector == "public":
            rows = [r for r in rows if r["sector"] == "公立"]
        elif sector == "private":
            rows = [r for r in rows if r["sector"] == "私立"]
        else:
            sector = "all"

        if q_clean:
            q_low = q_clean.casefold()
            rows = [
                r for r in rows
                if q_low in r["school_name"].casefold()
                or q_low in r["short_name"].casefold()
                or q_low in r["english_name"].casefold()
                or q_low in r["school_id"].casefold()
            ]

        if sort == "countries":
            rows.sort(key=lambda r: (-r["country_count"], -r["partner_page_count"], r["school_id"]))
        elif sort == "toeic":
            rows.sort(key=lambda r: (-r["toeic_count"], -r["partner_page_count"], r["school_id"]))
        elif sort == "jlpt":
            rows.sort(key=lambda r: (-r["jlpt_count"], -r["partner_page_count"], r["school_id"]))
        elif sort == "name":
            rows.sort(key=lambda r: r["school_name"])
        else:
            sort = "partners"
            rows.sort(key=lambda r: (-r["partner_page_count"], -r["country_count"], r["school_id"]))

        sector_opts = "".join(
            f'<option value="{k}"{" selected" if sector == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("all", f"全部（{overview['university_count']} 校）"),
                ("public", f"公立（{overview['public_count']} 校）"),
                ("private", f"私立（{overview['private_count']} 校）"),
            )
        )
        sort_opts = "".join(
            f'<option value="{k}"{" selected" if sort == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("partners", "合作校數（多→少）"),
                ("countries", "國家數（多→少）"),
                ("toeic", "列載 TOEIC 校數"),
                ("jlpt", "列載日檢 JLPT 校數"),
                ("name", "學校名稱排序"),
            )
        )

        tbody_html = ""
        for idx, r in enumerate(rows, 1):
            lang_parts = []
            if r["eng_toefl_ielts_count"]:
                lang_parts.append(f"托福/雅思 {r['eng_toefl_ielts_count']}")
            if r["toeic_count"]:
                lang_parts.append(f"多益 {r['toeic_count']}")
            if r["jlpt_count"]:
                lang_parts.append(f"日檢 {r['jlpt_count']}")
            if r["cefr_count"]:
                lang_parts.append(f"CEFR {r['cefr_count']}")
            lang_summary = " · ".join(lang_parts) if lang_parts else "依簡章總則"

            tbody_html += f"""<tr data-row-sector="{escape(r['sector'])}" data-row-name="{escape(r['school_name'])} {escape(r['short_name'])} {escape(r['school_id'])}" data-partners="{r['partner_page_count']}" data-countries="{r['country_count']}" data-toeic="{r['toeic_count']}" data-jlpt="{r['jlpt_count']}">
  <td>{idx}</td>
  <th scope="row"><a href="{escape(r['school_path'])}">{escape(r['school_name'])}</a><span class="uw-inline-badge">{escape(r['sector'])}</span></th>
  <td><strong>{r['partner_page_count']}</strong></td>
  <td><strong>{r['country_count']}</strong></td>
  <td>{escape(lang_summary)}</td>
  <td>{_official_link(r['official_url'], '官方來源')}</td>
</tr>"""

        if not tbody_html:
            tbody_html = "<tr><td colspan='6'>找不到符合篩選條件的大學，請調整關鍵字或重設。</td></tr>"

        latest_mod = max((r["latest_checked"] for r in overview["schools"]), default="2026-10-28")

        body = f"""<h1>{escape(spec.h1)}</h1>
{_render_switcher(spec.path)}

<section class="uw-tool-card" aria-labelledby="overview-filter-heading">
  <div class="uw-tool-header">
    <h2 id="overview-filter-heading">搜尋與排序（顯示 <span id="overview-visible-count">{len(rows)} 校</span>）</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-sm uw-btn-outline" href="/data/taiwan-exchange-overview">重設</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製網址</button>
    </div>
  </div>
  <form method="get" action="/data/taiwan-exchange-overview" class="uw-form-grid" data-data-filter="overview">
    <label class="uw-field">
      <span>搜尋學校</span>
      <input type="search" name="q" id="ov-q" value="{escape(q_clean)}" placeholder="臺大、政大、NCCU…">
    </label>
    <label class="uw-field">
      <span>公私立</span>
      <select name="sector" id="ov-sector">{sector_opts}</select>
    </label>
    <label class="uw-field">
      <span>排序欄位</span>
      <select name="sort" id="ov-sort">{sort_opts}</select>
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">套用</button>
    </div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="全台 71 所大學交換資源總覽表">
    <table class="uw-data-table" id="overview-data-table">
      <caption class="uw-sr-only">全台 {overview['university_count']} 所大學海外交換合作規模與語檢門檻統計</caption>
      <thead>
        <tr>
          <th scope="col">#</th>
          <th scope="col">台灣母校</th>
          <th scope="col">合作校數</th>
          <th scope="col">國家數</th>
          <th scope="col">列載語檢統計</th>
          <th scope="col">官方來源</th>
        </tr>
      </thead>
      <tbody id="overview-tbody">{tbody_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>欄位統計口徑說明</summary>
    <div class="uw-drawer-body">
      <ul>
        <li><strong>合作校數：</strong>同一母校對同一海外大學之多語組或學院方案歸併計為 1 所合作校，不等於當期開放名額。</li>
        <li><strong>列載語檢統計：</strong>統計公開合作校欄位有明確寫出分數之校數；統一寫於簡章總則者標示為依簡章總則。</li>
      </ul>
    </div>
  </details>
  {render_faq_section(FAQS_OVERVIEW_DATA)}
  {render_core_summary_and_citation_box(settings.origin, spec, checked_date=latest_mod)}
  {render_compliance_strip()}
</div>"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data"), ("全台 71 校交換資源總覽表", spec.path)],
            FAQS_OVERVIEW_DATA,
            variables=("合作校頁面數", "交換方案總筆數", "涵蓋國家地區數", "當期名單列載數", "語檢門檻列載分布"),
            keywords=("全台大學交換學生比較", "71校姊妹校數量排名", "大學出國交換資源總表", "多益日檢交換統計"),
            date_modified=latest_mod,
        )

    # -----------------------------------------------------------------------
    # 9. /data/deadlines
    # -----------------------------------------------------------------------
    @router.api_route("/data/deadlines", methods=["GET", "HEAD"])
    def data_deadlines(
        month: str = Query(default="all"),
        status: str = Query(default="all"),
        q: str = Query(default=""),
    ) -> HTMLResponse:
        spec = WAVE1_SPECS["/data/deadlines"]
        all_rows = build_all_71_school_deadlines()

        month_counts: dict[int, int] = {m: 0 for m in range(1, 13)}
        pending_count = 0
        for r in all_rows:
            if r["all_months"]:
                for m in r["all_months"]:
                    month_counts[m] = month_counts.get(m, 0) + 1
            else:
                pending_count += 1

        filtered = list(all_rows)
        month_clean = month.strip().lower()
        selected_month_int: int | None = None
        if month_clean == "pending":
            filtered = [r for r in filtered if not r["all_months"]]
        elif month_clean.isdigit() and 1 <= int(month_clean) <= 12:
            selected_month_int = int(month_clean)
            filtered = [r for r in filtered if selected_month_int in r["all_months"]]
        else:
            month_clean = "all"

        status_clean = status.strip().lower()
        if status_clean == "active":
            filtered = [r for r in filtered if r["status_code"] in {"open", "upcoming", "action_required"}]
        elif status_clean == "pending":
            filtered = [r for r in filtered if r["status_code"] == "needs_confirmation"]
        elif status_clean == "closed":
            filtered = [r for r in filtered if r["status_code"] in {"closed", "reference_only"}]
        else:
            status_clean = "all"

        q_clean = q.strip()
        if q_clean:
            q_low = q_clean.casefold()
            filtered = [
                r for r in filtered
                if q_low in r["school_name"].casefold()
                or q_low in r["short_name"].casefold()
                or q_low in r["school_id"].casefold()
                or q_low in r["round_title"].casefold()
            ]

        order_map = {"open": 0, "upcoming": 1, "action_required": 2, "needs_confirmation": 3, "closed": 4, "reference_only": 5}
        filtered.sort(
            key=lambda r: (
                order_map.get(r["status_code"], 9),
                r["deadline_iso"] or "9999-99-99",
                r["school_id"],
            )
        )

        month_pills = f'<a class="uw-month-pill{" is-active" if month_clean == "all" else ""}" href="/data/deadlines">全部（71）</a>'
        for m in range(1, 13):
            if month_counts[m] or selected_month_int == m:
                active_cls = " is-active" if selected_month_int == m else ""
                month_pills += f'<a class="uw-month-pill{active_cls}" href="/data/deadlines?month={m}">{m}月（{month_counts[m]}）</a>'
        month_pills += (
            f'<a class="uw-month-pill{" is-active" if month_clean == "pending" else ""}" '
            f'href="/data/deadlines?month=pending">待確認（{pending_count}）</a>'
        )

        month_select_opts = f'<option value="all"{" selected" if month_clean == "all" else ""}>全部月份</option>'
        for m in range(1, 13):
            month_select_opts += (
                f'<option value="{m}"{" selected" if selected_month_int == m else ""}>{m} 月截止（{month_counts[m]} 校）</option>'
            )
        month_select_opts += f'<option value="pending"{" selected" if month_clean == "pending" else ""}>待確認（{pending_count} 校）</option>'

        status_opts = "".join(
            f'<option value="{k}"{" selected" if status_clean == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("all", "全部狀態"),
                ("active", "受理中／即將開放"),
                ("pending", "待確認"),
                ("closed", "已截止／歷年參考"),
            )
        )

        month_summary_cells = "".join(f"<td><strong>{month_counts[m]}</strong></td>" for m in range(1, 13))
        month_summary_headers = "".join(f"<th scope='col'>{m}月</th>" for m in range(1, 13))

        tbody_html = ""
        for r in filtered:
            months_attr = ",".join(str(m) for m in r["all_months"]) if r["all_months"] else "pending"
            badge_cls = (
                "uw-tag-ok"
                if r["status_code"] in {"open", "upcoming"}
                else "uw-tag-warn"
                if r["status_code"] == "needs_confirmation"
                else "uw-tag-muted"
            )

            tbody_html += f"""<tr data-dl-months="{escape(months_attr)}" data-dl-status="{escape(r['status_code'])}" data-dl-name="{escape(r['school_name'])} {escape(r['short_name'])} {escape(r['school_id'])} {escape(r['round_title'])}">
  <th scope="row"><a href="/schools/{escape(r['school_id'])}">{escape(r['school_name'])}</a></th>
  <td>{escape(r['round_title'])}</td>
  <td><strong>{escape(r['deadline_display'])}</strong></td>
  <td><span class="{badge_cls}">{escape(r['status_label'])}</span></td>
  <td>{_official_link(r['source_url'], '簡章公告')} · <a href="/tools/timeline-generator?school={escape(r['school_id'])}">倒推時程</a></td>
</tr>"""

        if not tbody_html:
            tbody_html = "<tr><td colspan='5'>目前沒有符合此條件的學校紀錄，請切換月份或重設。</td></tr>"

        latest_checked = max((r["checked_date"] for r in all_rows if r["checked_date"]), default="2026-10-28")

        body = f"""<h1>{escape(spec.h1)}</h1>
{_render_switcher(spec.path)}

<section class="uw-tool-card" aria-labelledby="dl-filter-heading">
  <div class="uw-tool-header">
    <h2 id="dl-filter-heading">檢索學校截止日（顯示 <span id="dl-visible-count">{len(filtered)}</span> 校）</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-sm uw-btn-outline" href="/data/deadlines">重設</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製網址</button>
    </div>
  </div>

  <nav class="uw-month-pills" aria-label="依月份快速切換">{month_pills}</nav>

  <form method="get" action="/data/deadlines" class="uw-form-grid" data-data-filter="deadlines">
    <label class="uw-field">
      <span>搜尋學校</span>
      <input type="search" name="q" id="dl-q" value="{escape(q_clean)}" placeholder="臺大、政大、長庚…">
    </label>
    <label class="uw-field">
      <span>截止月份</span>
      <select name="month" id="dl-month">{month_select_opts}</select>
    </label>
    <label class="uw-field">
      <span>受理狀態</span>
      <select name="status" id="dl-status">{status_opts}</select>
    </label>
    <div class="uw-form-actions uw-nojs-only">
      <button type="submit" class="uw-btn uw-btn-primary">套用</button>
    </div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="全台 71 校交換校內申請截止日總表">
    <table class="uw-data-table" id="deadlines-data-table">
      <caption class="uw-sr-only">全台 {len(all_rows)} 所大學出國交換校內甄選期限一覽表</caption>
      <thead>
        <tr>
          <th scope="col">台灣母校</th>
          <th scope="col">甄選梯次</th>
          <th scope="col">截止期限</th>
          <th scope="col">狀態</th>
          <th scope="col">官方簡章與時程</th>
        </tr>
      </thead>
      <tbody id="deadlines-tbody">{tbody_html}</tbody>
    </table>
  </div>
</section>

<div class="uw-drawers-stack">
  <details class="uw-drawer">
    <summary>各月份收件校數分布統計（1–12 月）</summary>
    <div class="uw-drawer-body">
      <div class="uw-table-wrap" tabindex="0" role="region" aria-label="各月份收件學校數統計表">
        <table class="uw-data-table">
          <caption class="uw-sr-only">各月份收件學校數統計</caption>
          <thead><tr>{month_summary_headers}</tr></thead>
          <tbody><tr>{month_summary_cells}</tr></tbody>
        </table>
      </div>
    </div>
  </details>
  {render_faq_section(FAQS_DEADLINES_DATA)}
  {render_core_summary_and_citation_box(settings.origin, spec, checked_date=latest_checked)}
  {render_compliance_strip()}
</div>"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data"), ("全台 71 校交換截止日總表", spec.path)],
            FAQS_DEADLINES_DATA,
            variables=("校內線上報名截止日", "甄選梯次狀態", "日期核實狀態", "國際處官方公告網址"),
            keywords=("大學交換申請截止日", "出國交換行事曆", "全台71校交換簡章時間", "交換生報名期限"),
            date_modified=latest_checked,
        )

    register_wave2_routes(
        router,
        settings=settings,
        catalogue_loader=catalogue_loader,
        render_tool_page=render_tool_page,
        render_data_page=render_data_page,
        render_switcher=_render_switcher,
        safe_json_block=_safe_json_block,
        official_link=_official_link,
        availability_labels=availability_labels,
    )
    register_wave3_tool_routes(
        router,
        settings=settings,
        catalogue_loader=catalogue_loader,
        render_tool_page=render_tool_page,
        render_switcher=_render_switcher,
        safe_json_block=_safe_json_block,
        official_link=_official_link,
        availability_labels=availability_labels,
    )
    register_wave3_data_routes(
        router,
        settings=settings,
        catalogue_loader=catalogue_loader,
        render_data_page=render_data_page,
        render_switcher=_render_switcher,
        official_link=_official_link,
    )
