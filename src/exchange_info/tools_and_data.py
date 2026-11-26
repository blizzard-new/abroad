"""Server-rendered SEO tools (/tools/...) and database-driven annual data pages (/data/...)."""
from __future__ import annotations

import json
import threading
from collections.abc import Callable, Mapping
from html import escape
from time import monotonic
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from .models import CatalogueSourceStatus, PartnerUniversity
from .tools_and_data_core import (
    BUDGET_COUNTRY_TEMPLATES,
    ENGLISH_CONCORDANCE_BANDS,
    ECTS_SYSTEM_LABELS,
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
        return f'<span class="uw-muted-text">{escape(label)}（連結待確認）</span>'
    return f'<a href="{escape(safe)}" rel="noopener noreferrer" data-official-source>{escape(label)}</a>'


def append_tools_and_data_llms(origin: str) -> list[str]:
    """Return Markdown sections for /llms.txt and /llms-full.txt."""
    lines = ["", "## 交換學生免費工具", ""]
    for path in (
        "/tools",
        "/tools/ects-credit-converter",
        "/tools/gpa-converter",
        "/tools/language-score-converter",
        "/tools/exchange-budget-calculator",
        "/tools/timeline-generator",
    ):
        spec = WAVE1_SPECS[path]
        lines.append(f"- [{spec.h1}]({origin}{spec.path}): {spec.description}")
    lines += ["", "## 年度公開交換數據", ""]
    for path in ("/data", "/data/taiwan-exchange-overview", "/data/deadlines"):
        spec = WAVE1_SPECS[path]
        lines.append(f"- [{spec.h1}]({origin}{spec.path}): {spec.description}")
    return lines


# ---------------------------------------------------------------------------
# Page FAQs (3-5 per page, strictly factual and compliant)
# ---------------------------------------------------------------------------

FAQS_TOOLS_HUB: tuple[tuple[str, str], ...] = (
    (
        "使用 UniWay 的交換學生小工具需要註冊或登入帳號嗎？",
        "不需要。所有公開換算與試算工具皆免登入即可直接在瀏覽器或無 JavaScript 環境使用，亦不會讀取個人隱私資料；若後續想長期儲存個人選校清單與文件進度，再切換至站內申請工作台即可。",
    ),
    (
        "工具算出的學分、GPA 或語言對照結果可以直接當作學校審查結論嗎？",
        "不行。各大學教務處、國際處與海外接待校各有獨立採計標準與單科門檻，試算結果僅供選校初篩與準備規劃參考，實際資格、名額與期限以各校最新官方公告為準。",
    ),
    (
        "語言檢定分數換算器裡的合作校數量是怎麼算出來的？",
        "系統直接讀取 UniWay 現有全台 71 所大學之合作校公開資料，將「明確列載該檢定且門檻低於或等於輸入分數」與「列載同語系其他檢定／待確認」分開統計，不推論未公告的採計規則。",
    ),
    (
        "倒推時程表匯出的 .ics 檔案支援哪些行事曆軟體？",
        "匯出檔案採用國際標準 iCalendar（RFC 5545）格式，可直接匯入 Apple 行事曆、Google Calendar、Microsoft Outlook 與常見手機行事曆應用程式，並內建提前提醒。",
    ),
)

FAQS_ECTS: tuple[tuple[str, str], ...] = (
    (
        "歐洲 1 個 ECTS 學分通常可以抵免台灣大學幾學分？",
        "台灣多數大專校院與歐洲姊妹校對照時，常見基準為 2 ECTS 折算台灣 1 學分（即歐洲一學期全日制 30 ECTS 約對應台灣 15 學分）；但部分學校會依實際授課時數（Contact Hours）審核，出發前務必先填寫校內抵免預審表並以母校教務處最新官方公告為準。",
    ),
    (
        "去歐洲交換一學期最少要修多少 ECTS 才符合規定？",
        "需同時確認兩端門檻：第一是台灣母校國際處規定的交換期間最低修課學分（常見為每學期至少折合台灣 6 至 9 學分，即約 12 至 18 ECTS，或至少修習 2 至 3 門課）；第二是歐洲接待校與簽證居留要求的全日制負擔（常見為 20 至 30 ECTS）。兩者取較高者準備最穩妥。",
    ),
    (
        "為什麼建議比最低學分門檻多選 1 門課（約 5 至 6 ECTS）？",
        "歐洲大學常將整學期成績集中於期末筆試或口試（一試定生死），若僅剛好選滿母校最低學分，一旦其中一科未通過或臨時停開，就可能違反母校交換規定或影響獎學金核銷，因此多選 1 門課作為安全緩衝較為安心。",
    ),
    (
        "歐洲姊妹校開設的密集語言課（Intensive Language Course）可以算進學分嗎？",
        "視台灣母校與所屬系所規定而定。部分母校允許將學期中或學期前的當地語言課計入交換最低修課學分或一般選修，也有系所規定須為專業學部課程才可抵免，實際採計以各校最新官方公告為準。",
    ),
)

FAQS_GPA: tuple[tuple[str, str], ...] = (
    (
        "我的母校採用 4.3 制 GPA，申請要求 4.0 制 3.0 的海外姊妹校時可以直接等比例換算嗎？",
        "切勿直接將 4.3 制數字乘以 4.0/4.3。在多數國際成績轉換慣例（如 WES 或北美大學對照表）中，4.3 制的 A+（4.3）與 A（4.0）轉為 4.0 制時皆記為 4.0，其餘等第（如 B=3.0、B+=3.3）多維持相同積點；最準確做法是依每門課等第逐科重新加權計算，並以接待校最新官方公告為準。",
    ),
    (
        "什麼是德國巴伐利亞公式（Modifizierte Bayerische Formel）？分數越低越好嗎？",
        "是的，德國大學成績採 1.0 至 5.0 制，1.0 代表最優異、4.0 代表剛好及格、超過 4.0 為不及格。巴伐利亞公式為 1 + 3 × (最高分 - 你的分數) ÷ (最高分 - 最低及格分)，計算結果通常直接取至小數點後第 1 位且不四捨五入。",
    ),
    (
        "拿「歷年百分制總平均」直接查表轉 GPA，跟「逐科轉 GPA 再加權平均」為什麼數字不同？",
        "因為百分制區間轉等第屬於非線性階梯函數。舉例來說，一門 3 學分 95 分與一門 3 學分 75 分，百分制平均為 85 分（直接套表看似 4.0），但逐科轉 4.0 制分別為 4.0 與 3.0，加權平均實為 3.50。正式審查均以母校英文成績單列印數值或接待校指定算法為準。",
    ),
    (
        "交換申請表填寫 GPA 時可以自己四捨五入嗎？",
        "多數國內外大學（例如早稻田大學等姊妹校簡章）明文規定 GPA 不得自行四捨五入進位（例如 2.98 不可填為 3.0）。請如實填寫母校正式英文成績單上的數值，實際資格以各校最新官方公告為準。",
    ),
)

FAQS_LANGUAGE: tuple[tuple[str, str], ...] = (
    (
        "我有考多益（TOEIC）850 分，可以直接申請只寫 IELTS 6.0 或 TOEFL iBT 79 的歐美學校嗎？",
        "不一定，多數歐美英語系或歐陸大學在交換簡章中僅採計學術型測驗（TOEFL iBT 或 IELTS Academic），不接受 TOEIC 替代。因此本工具將「明確列載該檢定達標」與「列載其他英檢之同級參考」嚴格分開統計，報名前務必逐校核對簡章。",
    ),
    (
        "TOEFL iBT 的 MyBest Scores（拼分）或 Home Edition（在家考）可以用來申請交換嗎？",
        "許多台灣母校與海外接待校（如日本與歐洲多所名校）明文規定不採計 TOEFL MyBest Scores、Home Edition、Essentials，亦不採計 IELTS One Skill Retake 或 General Training 組別。報考前請先查閱母校國際處與目標校 Fact Sheet。",
    ),
    (
        "除了語言總分達標之外，還需要檢查哪些語言門檻細節？",
        "請特別留意三件事：第一是聽說讀寫「單科最低門檻」（例如總分 IELTS 6.5 且單科不低於 6.0）；第二是「成績單 2 年效期」須同時涵蓋母校收件日與次年姊妹校網報日；第三是擬選修學院是否有更高門檻（如商管、法學或傳播學院）。",
    ),
    (
        "為什麼日檢 JLPT 沒有直接換算成托福或雅思分數？",
        "JLPT 評量日語能力，而 IELTS、TOEFL 與 TOEIC 評量英語能力，兩者分屬不同授課語組，在交換申請上不可互相替代。切換至 JLPT 時，系統會改為篩選母校合作校名單中明確列載日檢 N1–N5 門檻之學校。",
    ),
)

FAQS_BUDGET: tuple[tuple[str, str], ...] = (
    (
        "出國交換期間還要繳海外姊妹校的學費嗎？",
        "若透過母校「校際／院際交換學生計畫（免繳接待校學費名額）」錄取，通常僅需繳交台灣母校原本的學雜費，免繳海外接待校學費；但若選擇「自費研修（Visiting / Fee-paying）」方案，則須另付海外學費。實際收費標準以各校最新官方公告為準。",
    ),
    (
        "為什麼交換預算一定要做 ±10% 匯率波動試算？",
        "從校內報名到實際出國往往相隔 8 至 12 個月，期間日圓、歐元、美元或英鎊匯率波動達 5%–10% 相當常見。預先檢視匯率上漲 10% 的總支出，可避免出發前因匯差產生數萬元新台幣的資金缺口，並可提前規劃分批換匯。",
    ),
    (
        "姊妹校簡章上的「財力證明金額」就等於實際會花掉的生活費嗎？",
        "兩者用途不同。財力證明是接待校或簽證機關審核入境資格的法定存款下限，通常不含機票、安家採買、跨國旅遊與初期押金；實際生活支出仍取決於所在城市物價與是否抽中校內學生宿舍。",
    ),
    (
        "教育部學海飛颺或校內交換獎學金會在出國前全部拿到嗎？",
        "多數交換獎學金採「出國前核發第一期款（約 70%–80%），返國完成心得報告與學分採認後核銷尾款」的機制，且機票、簽證與宿舍押金皆須在出國前先行墊付，建議行前自備款不要過度依賴尚未入帳的補助尾款。",
    ),
)

FAQS_TIMELINE: tuple[tuple[str, str], ...] = (
    (
        "想去大三上（秋季班，8–9 月）出國交換，通常什麼時候就要參加母校校內甄選？",
        "台灣大多數大學會在「出國前一年」的 9 月至 12 月舉辦次年秋季班（含全學年）校內第一梯次甄選；換言之，想大三上出國，大二升大三的暑假就應考出語言檢定成績，大二上學期開學後立即關注國際處簡章。",
    ),
    (
        "通過母校校內交換甄選，就代表已經被國外姊妹校錄取了嗎？",
        "不是。通過校內甄選代表取得「母校推薦提名資格（Nomination）」，後續仍須在海外接待校規定的網報期限前提交正式申請文件，經接待校審查核發入學許可（Letter of Acceptance）後才算正式錄取；實際資格與期限以各校最新官方公告為準。",
    ),
    (
        "如果資料庫裡我的母校目前顯示「待確認／依校方公告」，倒推時程表還能用嗎？",
        "可以。當母校尚未公布新一期確切收件日時，工具會明確標示「待確認」，並提供台灣大學常見收件月份或讓你自行輸入預估截止日來倒推語檢與備審節點；待國際處正式公告後，再微調最終送件日即可。",
    ),
    (
        "男生出國交換在時程上需要多注意什麼步驟？",
        "尚未服役之具役男身分學生，須在收到姊妹校入學許可並完成校內程序後，預留時間由母校承辦單位協助造冊向內政部役政司／移民署申請「役男出國研修核准」，切勿在尚未核准出境前直接持一般觀光方式離境。",
    ),
)

FAQS_DATA_HUB: tuple[tuple[str, str], ...] = (
    (
        "UniWay 公開數據頁的資料來源是什麼？多久更新一次？",
        "所有數據皆直接彙整自 UniWay 收錄之全台 71 所公私立大學國際事務處公開網頁、交換甄選簡章與合作校名冊，每筆學校紀錄均保留官方來源網址與系統查核日期，絕不人工捏造數字。",
    ),
    (
        "媒體報導、部落格文章或學術報告可以免費引用 `/data` 頁面的統計表格嗎？",
        "歡迎免費引用。引用時請使用頁面頂部提供的標準引用格式（標明出處 UniWay 與本頁完整網址），並一併保留「合作校頁面數不等於當期開放名額，實際資格、名額與期限以各校最新官方公告為準」之語境說明。",
    ),
    (
        "為什麼「合作校頁面數」不能直接當作「當期可申請名額數」？",
        "各大學公開的姊妹校資料同時包含「當期開放甄選名單」「校際締約總名錄（未必每學期開缺）」「院系級合作參考」與「零名額／待確認」等不同狀態，因此合作校總數反映的是跨國締約廣度，當期實際名額仍須逐校查閱簡章。",
    ),
    (
        "如果發現某所大學剛公布了最新一學期的交換簡章或截止日更動，該如何回報？",
        "可隨時透過站內問題回報功能提供母校名稱與國際處最新官方公告網址，團隊查核原始文件後即會更新資料庫基準。",
    ),
)

FAQS_OVERVIEW_DATA: tuple[tuple[str, str], ...] = (
    (
        "《全台 71 所大學交換資源總覽表》中的「合作校頁面數」是如何去重計算的？",
        "同一所台灣母校對同一所海外大學若同時設有多個方案（例如一般交換組、日語專修組或不同學院協議），系統會依「國家＋標準化外國機構識別碼」歸併為 1 個合作校頁面，同時在旁列出原始方案總列數，避免重複灌水。",
    ),
    (
        "表格裡的「列載多益（TOEIC）」或「列載日檢（JLPT）」數字代表什麼意義？",
        "代表該母校公開的合作校條件欄位中，有明確寫出 TOEIC 或 JLPT 分數／級別文字的合作校數量。若母校將語檢門檻統一寫在甄選簡章總則而未逐校重複標註，個別合作校欄位會歸入「待確認／依簡章總則」，請搭配母校簡章閱讀。",
    ),
    (
        "合作校數量較多的大學，交換申請競爭就比較小嗎？",
        "不一定。合作校總數較多代表可選國家與學校廣度較大，但熱門國家（如英美名校、日本早慶與舊帝大、德國理工名校）在各大學往往仍集中大量第一志願，建議同時對照當期實際開缺名額與院系限制。",
    ),
    (
        "這份 71 校總覽表包含大陸地區與港澳的交換合作學校嗎？",
        "若該台灣母校公開的赴外／兩岸交換名冊中包含大陸地區、香港或澳門合作高校，系統皆依原始公開來源一併納入統計；實際當期是否開放選填與申辦規定，以各校最新官方公告為準。",
    ),
)

FAQS_DEADLINES_DATA: tuple[tuple[str, str], ...] = (
    (
        "台灣各大學的交換學生校內申請截止日主要集中在幾月？",
        "依資料庫收錄之全台 71 校歷次與當期甄選時程觀察，校內收件明顯呈現雙高峰：第一波高峰落在每年 9 月至 12 月（主要選送次年秋季班與全學年交換生），第二波高峰落在每年 2 月至 3 月（主要選送次年春季班或二招補選）。",
    ),
    (
        "為什麼有些學校的截止時間是中午 12:00 或下午 16:00／17:00，而不是晚上 23:59？",
        "許多台灣大學國際處配合行政上班與系所收件核章時間，將線上系統關閉時間設定在下午 15:00、16:00、17:00 或中午 12:00。當官方公告未寫明關閉時刻時，本表絕不自行補寫 23:59，請務必提前至少 1 至 2 天完成送件。",
    ),
    (
        "表格標示「本梯次已截止」或「歷年梯次參考」時該怎麼運用？",
        "交換甄選具高度年度週期性。若當期梯次剛截止而下一期簡章尚未公布，可參考該校上一期的截止月份往後推算下一年度準備節點，並點擊「產生倒推時程」提前半年準備語言檢定與讀書計畫。",
    ),
    (
        "「線上報名截止日」與「紙本核章送件截止日」一定是同一天嗎？",
        "不一定。部分學校採全線上免紙本，部分學校要求同一期限前完成線上填報與系辦／國際處紙本收件，也有學校規定系所初審收件比國際處截止日更早。實際資格、名額與期限以各校最新官方公告為準。",
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
        tool_paths = (
            "/tools/ects-credit-converter",
            "/tools/gpa-converter",
            "/tools/language-score-converter",
            "/tools/exchange-budget-calculator",
            "/tools/timeline-generator",
        )
        badges = {
            "/tools/ects-credit-converter": "學分與選課規劃",
            "/tools/gpa-converter": "成績與德制換算",
            "/tools/language-score-converter": "連動 71 校資料庫",
            "/tools/exchange-budget-calculator": "12 國模板＋匯率情境",
            "/tools/timeline-generator": "支援 .ics 行事曆下載",
        }
        cards_html = ""
        for p in tool_paths:
            ts = WAVE1_SPECS[p]
            cards_html += f"""<li class="uw-hub-card">
  <span class="uw-card-tag">{escape(badges[p])}</span>
  <h2><a href="{escape(ts.path)}">{escape(ts.short_title)}</a></h2>
  <p>{escape(ts.description)}</p>
  <a class="uw-card-cta" href="{escape(ts.path)}">立即開啟工具 <span aria-hidden="true">→</span></a>
</li>"""

        body = f"""<p class="eyebrow">UNIWAY FREE TOOLS · 免登入交換申請工具箱</p>
<h1>{escape(spec.h1)}</h1>
<p class="lead">把繁瑣的學分折算、GPA 對照、語檢篩校、出國預算與申請倒數濃縮成免登入線上工具，無須註冊即可試算、複製與分享。</p>
{render_core_summary_and_citation_box(settings.origin, spec)}
<section class="uw-section">
  <h2>第 1 波開放實用工具（共 5 項）</h2>
  <ul class="uw-hub-grid">{cards_html}</ul>
</section>
<section class="uw-section">
  <h2>各工具適用階段與輸出格式對照表</h2>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="UniWay 交換免費工具對照表，可橫向捲動">
    <table class="uw-data-table">
      <caption>UniWay 交換學生五大免登入工具功能與適用情境一覽</caption>
      <thead>
        <tr>
          <th scope="col">工具名稱</th>
          <th scope="col">建議使用時機</th>
          <th scope="col">輸入條件</th>
          <th scope="col">輸出結果與匯出支援</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th scope="row"><a href="/tools/timeline-generator">交換申請倒推時程產生器</a></th>
          <td>出國前 8–14 個月（起心動念期）</td>
          <td>台灣母校、預計出發學期、基準截止日</td>
          <td>8 大關鍵準備節點日期＋標準 <code>.ics</code> 行事曆檔下載</td>
        </tr>
        <tr>
          <th scope="row"><a href="/tools/language-score-converter">語言檢定換算與選校查詢</a></th>
          <td>報考語檢前後、初篩志願名單</td>
          <td>IELTS / TOEFL / TOEIC / CEFR / JLPT 分數＋母校</td>
          <td>跨測驗參考級距＋母校資料庫達標合作校數量與清單連結</td>
        </tr>
        <tr>
          <th scope="row"><a href="/tools/gpa-converter">台灣大學 GPA 換算器</a></th>
          <td>核對母校與歐洲／德國姊妹校成績門檻</td>
          <td>百分制、4.3 制、4.0 制或逐科學分成績</td>
          <td>4.0／4.3 對照、德國巴伐利亞公式分數、逐科加權精算</td>
        </tr>
        <tr>
          <th scope="row"><a href="/tools/exchange-budget-calculator">交換學生預算試算器</a></th>
          <td>與家人討論經費、比較目的地城市成本</td>
          <td>12 國模板或自訂外幣月費、期程、獎學金</td>
          <td>±10% 匯率波動敏感度總表、淨自備款估算、明細與網址分享</td>
        </tr>
        <tr>
          <th scope="row"><a href="/tools/ects-credit-converter">歐洲 ECTS 學分換算器</a></th>
          <td>撰寫讀書計畫選課表、辦理學分抵免預審</td>
          <td>ECTS 或台／美／日學分、母校最低修課規定</td>
          <td>跨制學分折算、預估學習總時數、建議最少選課門數</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>
<section class="uw-section uw-cross-links">
  <h2>搭配公開數據與母校指南一起查核</h2>
  <p><a href="/data">瀏覽台灣交換學生年度公開數據總覽</a> · <a href="/data/taiwan-exchange-overview">全台 71 校交換資源總覽表</a> · <a href="/data/deadlines">全台 71 校校內截止日總表</a> · <a href="/schools">依母校查閱合作校</a></p>
</section>
{render_faq_section(FAQS_TOOLS_HUB)}
{render_compliance_strip()}"""
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
                (2.0, "2.0 ECTS = 1 台灣學分（台灣多數大學常見基準）"),
                (1.5, "1.5 ECTS = 1 台灣學分（部分學校／院系採計比例）"),
                (1.0, "1.0 ECTS = 1 台灣學分（特殊密集或時數對等審定）"),
            )
        )

        ref_rows = ""
        for ects_v, note in (
            (3, "歐洲小型工作坊、語言選修或實驗模組"),
            (5, "北歐、德國、荷蘭常見單門專業課標準學分"),
            (6, "法國、義大利、西班牙常見單門專業課標準學分"),
            (12, "約折合台灣 6 學分（部分母校交換期間最低修課下限）"),
            (15, "約折合台灣 7.5 學分（歐洲半學期或輕量修課負荷）"),
            (18, "約折合台灣 9 學分（多數台灣大學大一至大三學期低標）"),
            (24, "約折合台灣 12 學分（歐洲交換生常見穩健選課總量：4–5 門課）"),
            (30, "歐洲大學全日制標準一學期總學分（約 5–6 門課）"),
            (60, "歐洲大學全日制標準一學年總學分"),
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
            f"目前已換算學分（{res['ects']:g} ECTS）已達你設定的母校最低門檻（{res['required_ects_for_home']:g} ECTS）。"
            if res["meets_home_min"]
            else f"注意：目前已換算學分（{res['ects']:g} ECTS）低於母校最低門檻（需至少 {res['required_ects_for_home']:g} ECTS）。"
        )

        body = f"""<p class="eyebrow"><a href="/tools">交換免費工具</a> / 學分換算與選課</p>
<h1>{escape(spec.h1)}</h1>
<p class="lead">規劃歐洲交換選課表（Learning Agreement）或返國學分抵免時，快速對照歐洲 ECTS、台灣學期學分、美國學分與日本単位，並試算最低選課門數。</p>
{render_core_summary_and_citation_box(settings.origin, spec)}

<section class="uw-tool-card" aria-labelledby="ects-calc-heading">
  <div class="uw-tool-header">
    <h2 id="ects-calc-heading">即時學分與最低修課門檻換算器</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製此試算連結</button>
  </div>
  <form method="get" action="/tools/ects-credit-converter" class="uw-form-grid" data-tool-form="ects">
    <label class="uw-field">
      <span>輸入學分制度</span>
      <select name="system" id="ects-system">{sys_options}</select>
    </label>
    <label class="uw-field">
      <span>輸入學分數量</span>
      <input type="number" name="amount" id="ects-amount" value="{res['input_amount']:g}" min="0" max="240" step="0.5" required>
    </label>
    <label class="uw-field">
      <span>母校 ECTS 折算台灣學分比例</span>
      <select name="ratio" id="ects-ratio">{ratio_options}</select>
    </label>
    <label class="uw-field">
      <span>母校規定交換每學期最低修課（台灣學分）</span>
      <input type="number" name="min_tw" id="ects-min-tw" value="{res['min_home_tw_credits']:g}" min="0" max="30" step="0.5">
    </label>
    <div class="uw-form-actions">
      <button type="submit" class="uw-btn uw-btn-primary">計算學分對照</button>
    </div>
  </form>

  <div class="uw-kpi-grid" id="ects-results" aria-live="polite">
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">歐洲學分（ECTS）</span>
      <strong class="uw-kpi-value" data-out="ects">{res['ects']:g} ECTS</strong>
      <small data-out="workload">預估總學習時數：{res['workload_hours_low']}–{res['workload_hours_high']} 小時</small>
    </div>
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">折合台灣大學學分</span>
      <strong class="uw-kpi-value" data-out="tw">{res['tw_credits']:g} 學分</strong>
      <small data-out="ratio-note">依 {res['ects_per_tw']:g} ECTS = 1 台灣學分計算</small>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">美國學分對照（Semester / Quarter）</span>
      <strong class="uw-kpi-value" data-out="us">{res['us_semester_credits']:g} 學期學分</strong>
      <small data-out="us-q">約對應學季制（Quarter）{res['us_quarter_credits']:g} 學分</small>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">日本大學學分（単位）參考</span>
      <strong class="uw-kpi-value" data-out="jp">{res['jp_credits']:g} 単位</strong>
      <small>一般講授課常見 1 単位 ≈ 45 學習時數 ≈ 1.5–2 ECTS</small>
    </div>
  </div>

  <div class="uw-insight-panel" id="ects-min-panel">
    <h3>交換期間最低選課門檻與安全緩衝建議</h3>
    <p data-out="min-status"><strong>{escape(status_msg)}</strong></p>
    <ul>
      <li>滿足母校每學期 <strong><span data-out="min-tw-val">{res['min_home_tw_credits']:g}</span> 台灣學分</strong>，至少需修滿 <strong><span data-out="req-ects">{res['required_ects_for_home']:g}</span> ECTS</strong>（約 <span data-out="c5">{res['courses_5_ects']}</span> 門 5-ECTS 課程，或 <span data-out="c6">{res['courses_6_ects']}</span> 門 6-ECTS 課程）。</li>
      <li>安全緩衝建議：建議選修至 <strong><span data-out="buf-ects">{res['recommended_ects_with_buffer']:g}</span> ECTS</strong> 以上（多預留 1 門課），並同時確認歐洲接待校 Fact Sheet 是否另訂交換生最低 20 或 24 ECTS 下限。</li>
    </ul>
  </div>
</section>

<section class="uw-section">
  <h2>換算公式與各國學分制度原理</h2>
  <p><strong>歐洲學分互認系統（European Credit Transfer and Accumulation System, ECTS）</strong>以「學生完成課程所需的總學習工作量（含正課講授、討論課 Seminar、讀書準備、作業與期末考試）」為計算核心：</p>
  <ul>
    <li><strong>歐洲標準學年與學期：</strong>全日制 1 學年標準為 <strong>60 ECTS</strong>（總學習工作量約 1,500–1,800 小時），1 學期標準為 <strong>30 ECTS</strong>；因此 <strong>1 ECTS 約代表 25 至 30 小時的總學習投入</strong>。</li>
    <li><strong>ECTS ↔ 台灣／美國學期學分公式：</strong>台灣與美國學期制（Semester System）全日制一學期基準多為 15 學分，故國際交換最常見折算公式為 <code>台灣／美國學分 = ECTS ÷ 2</code>。部分學校會額外檢視每學期實際面授時數（如滿 18 小時折 1 學分）。</li>
    <li><strong>美國學季制（Quarter System）換算：</strong>1 個 Semester Credit 約等於 1.5 個 Quarter Units，即 <code>Quarter Credits = Semester Credits × 1.5</code>。</li>
    <li><strong>日本大學「単位」對照：</strong>日本文部科學省定義 1 単位標準為 45 小時學修（含課堂與自習），多數歐日大學交換協議採 <code>1 日本単位 ≈ 1.5 至 2 ECTS</code>，台日姊妹校間則多為 1 単位對 1 台灣學分（語學實習課或演習課另依時數認定）。</li>
  </ul>
</section>

<section class="uw-section">
  <h2>常見 ECTS 與台灣／美國／日本學分快速對照表</h2>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="ECTS 與台灣美國日本學分對照表，可橫向捲動">
    <table class="uw-data-table">
      <caption>以常見基準 2 ECTS = 1 台灣／美國學期學分估算（實際抵免依母校教務處與系所審定）</caption>
      <thead>
        <tr>
          <th scope="col">歐洲 ECTS</th>
          <th scope="col">台灣學分（÷2）</th>
          <th scope="col">美國 Semester</th>
          <th scope="col">日本単位（參考）</th>
          <th scope="col">預估總學習時數</th>
          <th scope="col">常見對應課程規模</th>
        </tr>
      </thead>
      <tbody>{ref_rows}</tbody>
    </table>
  </div>
</section>

<section class="uw-section uw-cross-links">
  <h2>下一步選校與成績準備工具</h2>
  <p><a href="/tools/gpa-converter">台灣大學 GPA 與德國巴伐利亞公式換算器</a> · <a href="/tools/language-score-converter">語檢分數換算＋可申請合作校查詢</a> · <a href="/destinations/germany">德國交換指南</a> · <a href="/partners">跨校外國大學查詢</a></p>
</section>
{render_faq_section(FAQS_ECTS)}
{render_compliance_strip()}"""
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
                ("percent", "台灣百分制總平均（0–100 分）"),
                ("gpa43", "台灣 4.3 制 GPA（如臺大／臺師大／政大等）"),
                ("gpa40", "標準 4.0 制 GPA（如清大／成大或北美制）"),
            )
        )

        gpa_rows = "".join(
            f"<tr><th scope='row'>{escape(letter)}</th><td>{escape(pct)}</td><td>{g43:.1f}</td><td>{g40:.1f}</td><td>{escape(bav)}</td></tr>"
            for letter, pct, g43, g40, bav in GPA_SCALE_TABLE
        )

        body = f"""<p class="eyebrow"><a href="/tools">交換免費工具</a> / 成績與門檻換算</p>
<h1>{escape(spec.h1)}</h1>
<p class="lead">一次對照台灣大學常見百分制、4.3 制、4.0 制 GPA 與德國交換必備的「巴伐利亞公式（Modifizierte Bayerische Formel）」，並提供多科目學分加權精算表。</p>
{render_core_summary_and_citation_box(settings.origin, spec)}

<section class="uw-tool-card" aria-labelledby="gpa-calc-heading">
  <div class="uw-tool-header">
    <h2 id="gpa-calc-heading">模式一：歷年總平均快速對照＋德國巴伐利亞公式</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製此試算連結</button>
  </div>
  <form method="get" action="/tools/gpa-converter" class="uw-form-grid" data-tool-form="gpa">
    <label class="uw-field">
      <span>原始成績制度</span>
      <select name="scale" id="gpa-scale">{scale_opts}</select>
    </label>
    <label class="uw-field">
      <span>輸入你的成績數值</span>
      <input type="number" name="value" id="gpa-value" value="{res['input_value']:g}" min="0" max="100" step="0.01" required>
    </label>
    <label class="uw-field">
      <span>德國公式：滿分標準（Nmax）</span>
      <input type="number" name="max_score" id="gpa-max" value="{res['max_score']:g}" min="4" max="100" step="0.1">
    </label>
    <label class="uw-field">
      <span>德國公式：最低及格分（Nmin，大學部常為 60）</span>
      <input type="number" name="min_pass" id="gpa-min" value="{res['min_pass']:g}" min="0" max="90" step="0.1">
    </label>
    <div class="uw-form-actions">
      <button type="submit" class="uw-btn uw-btn-primary">換算各制 GPA</button>
    </div>
  </form>

  <div class="uw-kpi-grid" id="gpa-results" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">4.0 制 GPA（細分加減號對照）</span>
      <strong class="uw-kpi-value" data-gpa-out="gpa40pm">{res['gpa_40_plusminus']:.2f} / 4.0</strong>
      <small data-gpa-out="gpa40std">傳統四等第（80/70/60）參考：{res['gpa_40_standard']:.2f}</small>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">4.3 制 GPA 對照</span>
      <strong class="uw-kpi-value" data-gpa-out="gpa43">{res['gpa_43']:.2f} / 4.3</strong>
      <small data-gpa-out="pct">對應百分制參考區間中位：約 {res['approx_percent']:.1f} 分</small>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">德國巴伐利亞公式（1.0 最優～4.0 及格）</span>
      <strong class="uw-kpi-value" data-gpa-out="bavarian">{escape(res['bavarian_grade'])}</strong>
      <small>依德國 uni-assist 慣例取至小數第 1 位不進位</small>
    </div>
  </div>
</section>

<section class="uw-tool-card" aria-labelledby="gpa-course-heading">
  <div class="uw-tool-header">
    <h2 id="gpa-course-heading">模式二：逐科學分加權 GPA 精算表（避免總平均直接套表誤差）</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" id="gpa-add-row">+ 新增一門課程</button>
  </div>
  <p class="uw-muted-text">正式英文成績單的 GPA 是「先將每一科成績轉為等第積點，乘上該科學分數加總後，再除以總學分」。若啟用瀏覽器互動功能，可在下方逐科輸入學分與百分制分數即時比對：</p>
  <div class="uw-table-wrap">
    <table class="uw-data-table" id="gpa-course-table">
      <caption>逐科學分加權試算（預設載入 3 門範例課程，可直接修改數值）</caption>
      <thead>
        <tr>
          <th scope="col">課程名稱（選填）</th>
          <th scope="col">學分數</th>
          <th scope="col">百分制成績（0–100）</th>
          <th scope="col">對應 4.3 積點</th>
          <th scope="col">對應 4.0 積點</th>
        </tr>
      </thead>
      <tbody id="gpa-course-tbody">
        <tr>
          <td><input type="text" value="範例科目 A" aria-label="課程名稱"></td>
          <td><input type="number" class="gpa-c-credit" value="3" min="0.5" max="15" step="0.5" aria-label="學分數"></td>
          <td><input type="number" class="gpa-c-score" value="92" min="0" max="100" step="1" aria-label="百分制成績"></td>
          <td class="gpa-c-43">4.3</td>
          <td class="gpa-c-40">4.0</td>
        </tr>
        <tr>
          <td><input type="text" value="範例科目 B" aria-label="課程名稱"></td>
          <td><input type="number" class="gpa-c-credit" value="3" min="0.5" max="15" step="0.5" aria-label="學分數"></td>
          <td><input type="number" class="gpa-c-score" value="83" min="0" max="100" step="1" aria-label="百分制成績"></td>
          <td class="gpa-c-43">3.7</td>
          <td class="gpa-c-40">3.7</td>
        </tr>
        <tr>
          <td><input type="text" value="範例科目 C" aria-label="課程名稱"></td>
          <td><input type="number" class="gpa-c-credit" value="2" min="0.5" max="15" step="0.5" aria-label="學分數"></td>
          <td><input type="number" class="gpa-c-score" value="75" min="0" max="100" step="1" aria-label="百分制成績"></td>
          <td class="gpa-c-43">3.0</td>
          <td class="gpa-c-40">3.0</td>
        </tr>
      </tbody>
    </table>
  </div>
  <p class="uw-weighted-summary" id="gpa-weighted-summary">
    範例加權結果：總學分 <strong>8.0</strong>｜加權百分制平均 <strong>84.38</strong>｜逐科加權 4.3 制 GPA <strong>3.75</strong>｜逐科加權 4.0 制 GPA <strong>3.64</strong>（德制巴伐利亞分數：<strong>2.1</strong>）
  </p>
</section>

<section class="uw-section">
  <h2>換算公式說明與德國巴伐利亞公式詳解</h2>
  <ul>
    <li><strong>逐科學分加權 GPA 公式：</strong><code>GPA = Σ（單科等第積點 × 單科學分數）÷ Σ 總修習學分數</code>。申請交換時應優先採用母校教務處核發之英文成績單原載數值。</li>
    <li><strong>4.3 制轉 4.0 制原則：</strong>依北美 WES（World Education Services）及常見大學審核標準，4.3 制中的 <code>A+ (4.3)</code> 與 <code>A (4.0)</code> 對應至 4.0 制時均記為 <code>4.0</code>，<code>A- (3.7)</code> 維持 <code>3.7</code>，不可直接把總 GPA 乘以 <code>4.0 / 4.3</code>（否則滿分 4.0 的科目會被低估成 3.72）。</li>
    <li><strong>德國巴伐利亞公式（Modifizierte Bayerische Formel）：</strong>德國高等教育使用 1.0（極優 Sehr gut）至 4.0（及格 Ausreichend）評分，換算式為：<br>
      <code>德制成績 = 1 + 3 × (Nmax - Nd) ÷ (Nmax - Nmin)</code><br>
      其中 <code>Nmax</code> 為母校滿分（百分制為 100），<code>Nmin</code> 為最低及格標準（台灣大學部一般為 60 分、研究所常見為 70 分，請依母校學則設定），<code>Nd</code> 為你的實際平均成績，算出後直接捨去小數點第 2 位以後數字。</li>
  </ul>
</section>

<section class="uw-section">
  <h2>台灣常見等第制（4.3 制／4.0 制／百分制／德國巴伐利亞制）對照參考表</h2>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="台灣大學 GPA 與百分制及德國巴伐利亞分數對照表，可橫向捲動">
    <table class="uw-data-table">
      <caption>台灣大專校院常見等第區間對照參考（各校分數切點可能微調，請對照母校成績單背面說明）</caption>
      <thead>
        <tr>
          <th scope="col">等第（Letter Grade）</th>
          <th scope="col">常見百分制區間</th>
          <th scope="col">4.3 制積點</th>
          <th scope="col">4.0 制積點（含加減號）</th>
          <th scope="col">德國巴伐利亞制（及格 60 分計）</th>
        </tr>
      </thead>
      <tbody>{gpa_rows}</tbody>
    </table>
  </div>
</section>

<section class="uw-section uw-cross-links">
  <h2>相關工具與申請指南</h2>
  <p><a href="/tools/ects-credit-converter">歐洲 ECTS 學分換算器</a> · <a href="/tools/language-score-converter">語檢分數換算與合作校查詢</a> · <a href="/guides/exchange-eligibility">如何核對交換申請資格與成績門檻</a> · <a href="/schools">查看全台 71 校交換規定</a></p>
</section>
{render_faq_section(FAQS_GPA)}
{render_compliance_strip()}"""
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
                ("ielts", "IELTS 雅思學術組（4.0–9.0）"),
                ("toefl", "TOEFL iBT 托福網路測驗（0–120）"),
                ("toeic", "TOEIC 多益聽讀測驗（10–990）"),
                ("cefr", "CEFR 歐洲語言分級（A2 / B1 / B2 / C1 / C2）"),
                ("jlpt", "JLPT 日本語能力試驗（N5 / N4 / N3 / N2 / N1）"),
            )
        )
        home_options = "".join(
            f'<option value="{escape(u.id)}"{" selected" if u.id == uni.id else ""}>{escape(u.school_name)}（{escape(u.short_name)}）</option>'
            for u in SUPPORTED_UNIVERSITIES
        )

        def _render_sample_items(items: list[dict[str, Any]], empty_text: str) -> str:
            if not items:
                return f'<p class="uw-muted-text">{escape(empty_text)}</p>'
            lis = "".join(
                f"""<li class="uw-partner-mini-card">
  <div class="uw-partner-mini-top">
    <a href="{escape(item['partner_url'])}"><strong>{escape(item['school_name'])}</strong></a>
    <span class="uw-mini-country">{escape(item['country'])}</span>
  </div>
  <p class="uw-mini-rule"><span class="uw-tag-ok">{escape(item['matched_rule'])}</span> · 狀態：{escape(item['availability'])}</p>
  <p class="uw-mini-snippet">來源記載：{escape(item['snippet'])}</p>
</li>"""
                for item in items
            )
            return f'<ul class="uw-partner-mini-grid">{lis}</ul>'

        direct_html = _render_sample_items(
            matched["direct_samples"],
            f"目前 {uni.school_name} 公開合作校欄位中，尚無直接以 {conv['input_display']} 單獨列載且低於此分數的條目（可能寫於母校簡章語組總則，或改列其他檢定，請查看下方同級參考與母校總覽頁）。",
        )
        equiv_section = ""
        if not conv["is_japanese"]:
            equiv_items_html = _render_sample_items(
                matched["equiv_samples"],
                "目前無額外列載其他同級英語檢定的合作校條目。",
            )
            equiv_section = f"""<div class="uw-sub-result" id="lang-equiv-block">
  <h4>列載其他英語檢定且同級達標參考（共 <span data-lang-out="equiv-count">{matched['equiv_match_count']}</span> 所，須逐校確認是否接受替代檢定）</h4>
  <div id="lang-equiv-list">{equiv_items_html}</div>
</div>"""

        concordance_rows = "".join(
            f"<tr><th scope='row'>CEFR {escape(b['cefr'])}</th>"
            f"<td>{b['ielts_min']:.1f}" + ("" if b["ielts_min"] == b["ielts_max"] else f" – {b['ielts_max']:.1f}") + "</td>"
            f"<td>{b['toefl_min']} – {b['toefl_max']}</td>"
            f"<td>{escape(b['toefl_new'])}</td>"
            f"<td>{b['toeic_min']} – {b['toeic_max']}</td>"
            f"<td>{escape(b['summary'])}</td></tr>"
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

        body = f"""<p class="eyebrow"><a href="/tools">交換免費工具</a> / 語檢對照與選校雷達</p>
<h1>{escape(spec.h1)}</h1>
<p class="lead">輸入你的 IELTS、TOEFL iBT、TOEIC、CEFR 或日檢 JLPT 成績並選擇就讀母校，同時查看跨測驗對照級距與 UniWay 真實資料庫中的合作校門檻分布。</p>
{render_core_summary_and_citation_box(settings.origin, spec)}

<section class="uw-tool-card" aria-labelledby="lang-calc-heading">
  <div class="uw-tool-header">
    <h2 id="lang-calc-heading">語言分數對照＋母校合作校即時比對</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製此查詢連結</button>
  </div>
  <form method="get" action="/tools/language-score-converter" class="uw-form-grid" data-tool-form="language">
    <label class="uw-field">
      <span>選擇你的就讀母校（全台 71 校真實資料連動）</span>
      <select name="home" id="lang-home">{home_options}</select>
    </label>
    <label class="uw-field">
      <span>選擇語言檢定類別</span>
      <select name="test" id="lang-test">{test_options}</select>
    </label>
    <label class="uw-field">
      <span>輸入分數或等級（如 6.5、85、800、B2、N2）</span>
      <input type="text" name="score" id="lang-score" value="{escape(raw_score_display)}" required>
    </label>
    <div class="uw-form-actions">
      <button type="submit" class="uw-btn uw-btn-primary">換算並查詢合作校</button>
    </div>
  </form>

  <div class="uw-kpi-grid" id="lang-conv-results" aria-live="polite">
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">對應 CEFR 能力分級</span>
      <strong class="uw-kpi-value" data-lang-out="cefr">{escape(conv['cefr'])}</strong>
      <small data-lang-out="input-display">輸入基準：{escape(conv['input_display'])}</small>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">IELTS 雅思學術組參考區間</span>
      <strong class="uw-kpi-value" data-lang-out="ielts">{escape(conv['ielts_range'])}</strong>
      <small>留意各校是否另設單科不低於 5.5 / 6.0 限制</small>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">TOEFL iBT 托福參考區間</span>
      <strong class="uw-kpi-value" data-lang-out="toefl">{escape(conv['toefl_range'])}</strong>
      <small data-lang-out="toefl-new">2026 新制 6 分制參考：{escape(conv['toefl_new'])}</small>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">TOEIC 聽讀參考區間</span>
      <strong class="uw-kpi-value" data-lang-out="toeic">{escape(conv['toeic_range'])}</strong>
      <small>歐美多數學校不收多益，報名前請核對採計清單</small>
    </div>
  </div>

  <div class="uw-db-match-panel" id="lang-db-panel" aria-live="polite">
    <div class="uw-db-match-head">
      <div>
        <h3><span data-lang-out="home-name">{escape(matched['home_name'])}</span> 合作校語言門檻比對結果</h3>
        <p class="uw-muted-text">母校合作校總數：<strong data-lang-out="total-pages">{matched['total_partner_pages']}</strong> 所（統計單位為去重後合作校頁面，非當期錄取名額；未單獨列載數字者歸入待確認）</p>
      </div>
      <div class="uw-btn-group">
        <a class="uw-btn uw-btn-primary" id="lang-home-link" href="{escape(matched['home_school_url'])}">查看{escape(matched['home_short_name'])}完整合作校名單</a>
        <a class="uw-btn uw-btn-outline" id="lang-planner-link" href="{escape(matched['home_planner_url'])}">開啟互動選校篩選</a>
      </div>
    </div>

    <div class="uw-stat-strip">
      <div class="uw-stat-pill uw-stat-ok">
        <span>明確列載此檢定且達標</span>
        <strong data-lang-out="direct-count">{matched['direct_match_count']} 所</strong>
      </div>
      <div class="uw-stat-pill">
        <span>列載其他同語系檢定達標（參考）</span>
        <strong data-lang-out="equiv-stat">{matched['equiv_match_count']} 所</strong>
      </div>
      <div class="uw-stat-pill">
        <span>高於目前輸入分數</span>
        <strong data-lang-out="below-count">{matched['below_threshold_count']} 所</strong>
      </div>
      <div class="uw-stat-pill">
        <span>門檻待確認／依母校語組總則或他語種</span>
        <strong data-lang-out="unconfirmed-count">{matched['unconfirmed_or_other_count']} 所</strong>
      </div>
    </div>

    <div class="uw-sub-result">
      <h4>明確列載該檢定且分數達標之合作校範例（前 12 筆，點擊查看完整條件與官方來源）</h4>
      <div id="lang-direct-list">{direct_html}</div>
    </div>
    {equiv_section}
  </div>
</section>

<section class="uw-section">
  <h2>英語檢定官方研究對照參考表（CEFR / IELTS / TOEFL iBT / TOEIC）</h2>
  <p>下表綜合整理自 ETS（TOEFL 與 TOEIC 主辦機構）、IELTS 官方與 CEFR 公布之能力級距研究。各大學設定交換門檻時常依院系需求微調（例如規定 IELTS 6.5 對應 TOEFL iBT 80、88 或 90），因此<strong>跨檢定換算僅供選校方向參考，不可用來主張免交指定檢定</strong>。</p>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="英語檢定與 CEFR 分數對照表，可橫向捲動">
    <table class="uw-data-table">
      <caption>IELTS Academic、TOEFL iBT（含 6 分制對照）、TOEIC L&R 與 CEFR 參考區間</caption>
      <thead>
        <tr>
          <th scope="col">CEFR 等級</th>
          <th scope="col">IELTS Academic</th>
          <th scope="col">TOEFL iBT（0–120）</th>
          <th scope="col">TOEFL 6 分制參考</th>
          <th scope="col">TOEIC L&R（聽讀）</th>
          <th scope="col">交換申請常見對應場景</th>
        </tr>
      </thead>
      <tbody>{concordance_rows}</tbody>
    </table>
  </div>
</section>

<section class="uw-section">
  <h2>日本語能力試驗（JLPT）與交換申請常見級別對照表</h2>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="日檢 JLPT 與 CEFR 參考級別表，可橫向捲動">
    <table class="uw-data-table">
      <caption>日本國際交流基金會（JF）公布之 JLPT 與 CEFR 參考對應關係及赴日交換常見門檻</caption>
      <thead>
        <tr>
          <th scope="col">JLPT 級別</th>
          <th scope="col">JF / CEFR 參考對應</th>
          <th scope="col">赴日交換常見適用學部與方案</th>
        </tr>
      </thead>
      <tbody>{jlpt_rows}</tbody>
    </table>
  </div>
</section>

<section class="uw-section uw-cross-links">
  <h2>延伸數據與工具</h2>
  <p><a href="/data/taiwan-exchange-overview">全台 71 所大學交換資源與語檢分布總表</a> · <a href="/tools/gpa-converter">台灣大學 GPA 換算器</a> · <a href="/tools/timeline-generator">交換申請倒推時程產生器</a> · <a href="/guides/exchange-eligibility">交換資格與語檢準備指南</a></p>
</section>
{render_faq_section(FAQS_LANGUAGE)}
{render_compliance_strip()}"""
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
                f"<td>{escape(tpl['currency'])}（參考匯率 {row_calc['bundled_rate']:g}）</td>"
                f"<td>{tpl['currency']} {row_calc['monthly_foreign']:,.0f}</td>"
                f"<td>約 NT$ {row_calc['base_monthly_twd']:,}</td>"
                f"<td>NT$ {tpl['one_time_twd']:,}</td>"
                f"<td>約 NT$ {row_calc['base_gross_twd']:,}（{tpl['months']} 個月）</td></tr>"
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
            f"・每月外幣生活費：{calc['currency']} {calc['monthly_foreign']:,.0f}（住宿 {calc['housing']:,.0f}／飲食 {calc['food']:,.0f}／交通 {calc['transport']:,.0f}／醫保雜支 {calc['other']:,.0f}）\n"
            f"・基準匯率（1 {calc['currency']} = {calc['rate']:g} TWD）總支出：NT$ {calc['base_gross_twd']:,}（含機票簽證等一次性 NT$ {calc['one_time_twd']:,}）\n"
            f"・扣除預估補助 NT$ {calc['scholarship_twd']:,} 後淨自備款：NT$ {calc['base_net_twd']:,}\n"
            f"・匯率 +10% 安全緩衝需多準備：NT$ {calc['fx_buffer_delta_twd']:,}\n"
            f"・試算工具：{settings.origin}{spec.path}（{MANDATORY_DISCLAIMER}）"
        )

        body = f"""<p class="eyebrow"><a href="/tools">交換免費工具</a> / 留學預算與匯率規劃</p>
<h1>{escape(spec.h1)}</h1>
<p class="lead">內建 12 個熱門交換國家估算起點模板與站內參考匯率，分開計算每月外幣生活費、行前一次性台幣支出、獎學金折抵，以及正負 10% 匯率波動對自備款的影響。</p>
{render_core_summary_and_citation_box(settings.origin, spec)}
{_safe_json_block("uw-budget-templates", js_templates)}

<section class="uw-tool-card" aria-labelledby="budget-calc-heading">
  <div class="uw-tool-header">
    <h2 id="budget-calc-heading">互動交換預算與匯率敏感度計算機</h2>
    <div class="uw-btn-group">
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-target="budget-summary-copy">複製預算明細</button>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製分享網址</button>
    </div>
  </div>
  <form method="get" action="/tools/exchange-budget-calculator" class="uw-form-grid" data-tool-form="budget">
    <label class="uw-field">
      <span>選擇目的地國家參考模板</span>
      <select name="country" id="b-country">{country_opts}</select>
    </label>
    <label class="uw-field">
      <span>交換停留月數（1–12 個月）</span>
      <input type="number" name="months" id="b-months" value="{calc['months']}" min="1" max="12" step="1">
    </label>
    <label class="uw-field">
      <span>參考匯率（1 <span data-b-out="cur-code">{escape(calc['currency'])}</span> 兌新台幣，可自訂）</span>
      <input type="number" name="rate" id="b-rate" value="{calc['rate']:g}" min="0.0001" max="500" step="any">
    </label>
    <label class="uw-field">
      <span>每月住宿與水電（<span data-b-out="cur-code-2">{escape(calc['currency'])}</span>）</span>
      <input type="number" name="housing" id="b-housing" value="{calc['housing']:g}" min="0" step="any">
    </label>
    <label class="uw-field">
      <span>每月飲食與日用（{escape(calc['currency'])}）</span>
      <input type="number" name="food" id="b-food" value="{calc['food']:g}" min="0" step="any">
    </label>
    <label class="uw-field">
      <span>每月當地交通（{escape(calc['currency'])}）</span>
      <input type="number" name="transport" id="b-transport" value="{calc['transport']:g}" min="0" step="any">
    </label>
    <label class="uw-field">
      <span>每月強制醫保、電信與學期雜支（{escape(calc['currency'])}）</span>
      <input type="number" name="other" id="b-other" value="{calc['other']:g}" min="0" step="any">
    </label>
    <label class="uw-field">
      <span>行前一次性支出：來回機票＋簽證＋安家（TWD）</span>
      <input type="number" name="one_time" id="b-onetime" value="{calc['one_time_twd']}" min="0" step="500">
    </label>
    <label class="uw-field">
      <span>預估獎學金或補助折抵總額（TWD）</span>
      <input type="number" name="scholarship" id="b-scholarship" value="{calc['scholarship_twd']}" min="0" step="1000">
    </label>
    <div class="uw-form-actions">
      <button type="submit" class="uw-btn uw-btn-primary">更新預算試算</button>
    </div>
  </form>

  <p class="uw-muted-text" id="b-template-note">模板說明：{escape(calc['template_note'])}（預設匯率讀取自站內參考匯率檔 {escape(calc['fx_fetched_date'])}，非銀行即時牌告價）。</p>

  <div class="uw-kpi-grid" aria-live="polite">
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">每月外幣生活費小計</span>
      <strong class="uw-kpi-value" data-b-out="monthly-foreign">{escape(calc['currency'])} {calc['monthly_foreign']:,.0f}</strong>
      <small data-b-out="monthly-twd">基準匯率折合約 NT$ {calc['base_monthly_twd']:,}／月</small>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">交換總支出（生活費＋一次性行前）</span>
      <strong class="uw-kpi-value" data-b-out="gross-twd">NT$ {calc['base_gross_twd']:,}</strong>
      <small data-b-out="months-label">以 {calc['months']} 個月＋行前 NT$ {calc['one_time_twd']:,} 估算</small>
    </div>
    <div class="uw-kpi-box uw-kpi-highlight">
      <span class="uw-kpi-label">扣除補助後「淨自備款需求」</span>
      <strong class="uw-kpi-value" data-b-out="net-twd">NT$ {calc['base_net_twd']:,}</strong>
      <small data-b-out="fx-delta">若外幣升值 +10%，需多備 NT$ {calc['fx_buffer_delta_twd']:,}</small>
    </div>
    <div class="uw-kpi-box">
      <span class="uw-kpi-label">建議額外緊急預備金（1 個月生活費）</span>
      <strong class="uw-kpi-value" data-b-out="reserve-twd">NT$ {calc['emergency_reserve_twd']:,}</strong>
      <small>支應初期租屋押金（常為 1–3 個月租金）與突發醫療</small>
    </div>
  </div>

  <h3>±10% 匯率波動情境敏感度對照表</h3>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="正負10%匯率波動敏感度試算表，可橫向捲動">
    <table class="uw-data-table" id="b-scenario-table">
      <caption>外幣匯率變動 -10%、0%、+10% 對整學期總支出與自備款之影響</caption>
      <thead>
        <tr>
          <th scope="col">匯率情境</th>
          <th scope="col">試算匯率</th>
          <th scope="col">每月生活費（TWD）</th>
          <th scope="col">整期生活費小計</th>
          <th scope="col">含機票簽證總支出</th>
          <th scope="col">扣補助後淨自備款</th>
        </tr>
      </thead>
      <tbody id="b-scenario-tbody">{sc_rows}</tbody>
    </table>
  </div>
  <pre id="budget-summary-copy" class="uw-copy-preview">{escape(share_summary_text)}</pre>
</section>

<section class="uw-section">
  <h2>預算計算結構與五大常見漏算項目</h2>
  <p>交換預算核心公式：<code>淨自備資金 =（每月外幣生活費 × 停留月數 × 匯率）＋ 行前一次性台幣支出 － 已確認獎助學金</code>。規劃時請額外檢查以下五項隱形成本：</p>
  <ol>
    <li><strong>初期住宿押金與仲介／清潔費：</strong>歐洲與日韓宿舍常在入住前收取 1 至 3 個月租金作為可退押金（Deposit），日本校外物件另可能有禮金或保證會社費用，雖部分可於退宿後退還，但出國前必須先有現金週轉。</li>
    <li><strong>強制醫療保險（Mandatory Health Insurance）：</strong>德國公立學生醫保（約 120–130 歐元／月）、美國大學強制校保（常達每學期 800–1,800 美元）、澳洲 OSHC 與英國年簽 IHS 皆為硬性支出。</li>
    <li><strong>學期雜費與學生會費（Semester Contribution）：</strong>免繳「學費（Tuition）」不等於免繳「學期行政／交通票費」（例如德國各邦大學每學期常收 85–350 歐元 Semesterbeitrag）。</li>
    <li><strong>跨國電匯手續費與海外刷卡手續費：</strong>跨國繳納宿舍費常產生台灣端郵電費與中轉行手續費（每次約 NT$ 600–1,200）。</li>
    <li><strong>獎學金撥款時間差：</strong>學海系列與校內補助尾款多於返國完成學分抵免後才撥付，出發前仍需備足全額週轉金。</li>
  </ol>
</section>

<section class="uw-section">
  <h2>12 個熱門交換國家一學期參考估算起點總表</h2>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="12個熱門交換國家一學期預算參考對照表，可橫向捲動">
    <table class="uw-data-table">
      <caption>各國規劃起點模板概覽（未扣獎學金；實際支出視城市物價、校內宿位中籤與個人消費習慣而異）</caption>
      <thead>
        <tr>
          <th scope="col">目的地參考模板</th>
          <th scope="col">幣別與參考匯率</th>
          <th scope="col">模板每月外幣小計</th>
          <th scope="col">折合每月新台幣</th>
          <th scope="col">行前機票簽證估算</th>
          <th scope="col">一學期參考總支出</th>
        </tr>
      </thead>
      <tbody>{tpl_overview_rows}</tbody>
    </table>
  </div>
</section>

<section class="uw-section uw-cross-links">
  <h2>深入閱讀各國費用指南與補助資訊</h2>
  <p><a href="/guides/exchange-budget">交換預算與費用清單完整指南</a> · <a href="/guides/japan-exchange-cost">日本交換費用指南</a> · <a href="/guides/korea-exchange-cost">韓國交換費用指南</a> · <a href="/guides/germany-exchange-cost">德國交換費用指南</a> · <a href="/destinations">國家專區比較</a></p>
</section>
{render_faq_section(FAQS_BUDGET)}
{render_compliance_strip()}"""
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
    <p>{escape(m['detail'])}</p>
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

        body = f"""<p class="eyebrow"><a href="/tools">交換免費工具</a> / 時程規劃與行事曆匯出</p>
<h1>{escape(spec.h1)}</h1>
<p class="lead">選擇你的台灣母校與預計出國學期，系統自動對照國際處收錄紀錄並倒推 8 個關鍵準備節點，支援一鍵匯出標準 <code>.ics</code> 行事曆檔匯入 Google / Apple / Outlook 行事曆。</p>
{render_core_summary_and_citation_box(settings.origin, spec)}
{_safe_json_block("uw-timeline-schools", {"schools": js_school_map, "terms": js_terms})}

<section class="uw-tool-card" aria-labelledby="tl-calc-heading">
  <div class="uw-tool-header">
    <h2 id="tl-calc-heading">母校交換申請倒推時程計算機</h2>
    <div class="uw-btn-group">
      <a class="uw-btn uw-btn-primary uw-btn-sm" id="tl-ics-link" href="{escape(plan['ics_url'])}">下載 .ics 行事曆檔</a>
      <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製此時程連結</button>
    </div>
  </div>

  <form method="get" action="/tools/timeline-generator" class="uw-form-grid" data-tool-form="timeline">
    <label class="uw-field">
      <span>選擇就讀母校（全台 71 校）</span>
      <select name="school" id="tl-school">{school_opts}</select>
    </label>
    <label class="uw-field">
      <span>預計出發交換學期</span>
      <select name="term" id="tl-term">{term_opts}</select>
    </label>
    <label class="uw-field">
      <span>校內截止基準日（可依當期最新簡章手動微調）</span>
      <input type="date" name="deadline" id="tl-deadline" value="{escape(plan['anchor_date'])}">
    </label>
    <div class="uw-form-actions">
      <button type="submit" class="uw-btn uw-btn-primary">重新倒推時程</button>
    </div>
  </form>

  <div class="uw-insight-panel" id="tl-school-record" aria-live="polite">
    <h3>母校資料庫目前收錄紀錄：<span data-tl-out="school-name">{escape(plan['school_name'])}</span></h3>
    <ul>
      <li><strong>收錄梯次：</strong><span data-tl-out="rec-round">{escape(plan['school_recorded_round'])}</span></li>
      <li><strong>資料庫記載期限：</strong><strong data-tl-out="rec-deadline">{escape(plan['school_recorded_deadline'])}</strong>（狀態：<span data-tl-out="rec-status">{escape(plan['school_recorded_status'])}</span>｜查核日：<span data-tl-out="rec-checked">{escape(plan['school_checked_date'])}</span>）</li>
      <li><strong>本表倒推基準說明：</strong><span data-tl-out="anchor-note">{escape(plan['anchor_source_label'])}</span></li>
      <li><strong>母校官方公告連結：</strong><a id="tl-official-link" href="{escape(plan['official_url'])}" rel="noopener noreferrer" data-official-source>前往查閱母校國際處官方來源</a> · <a id="tl-school-page-link" href="/schools/{escape(plan['school_id'])}">查看母校合作校頁面</a></li>
    </ul>
  </div>

  <h3>自動倒推 8 大申請與行前準備節點</h3>
  <ol class="uw-timeline-list" id="tl-milestone-list" aria-live="polite">{milestone_items}</ol>
</section>

<section class="uw-section">
  <h2>台灣大學生出國交換「秋季班 vs 春季班」標準倒推時程對照表</h2>
  <p>交換申請最大的陷阱是「以為大三才要開始準備大三交換」。實際上從考出語言檢定、校內甄選、母校提名到姊妹校核發入學許可，完整週期長達 <strong>10 至 14 個月</strong>：</p>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="秋季班與春季班交換申請標準時程對照表，可橫向捲動">
    <table class="uw-data-table">
      <caption>台灣大專校院常見兩季出國交換申請階段參考時程（各校確切月份請查《全台 71 校截止日總表》）</caption>
      <thead>
        <tr>
          <th scope="col">準備階段</th>
          <th scope="col">秋季班出發（當年 8–9 月出國）</th>
          <th scope="col">春季班出發（次年 1–4 月出國）</th>
          <th scope="col">階段核心檢核項目</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th scope="row">1. 語言檢定衝刺與應考</th>
          <td>前一年 5 月 – 9 月</td>
          <td>前一年 10 月 – 當年 1 月</td>
          <td>取得 2 年效期內之正式成績單（預留至少 1 次重考時間）</td>
        </tr>
        <tr>
          <th scope="row">2. 讀書計畫與推薦信準備</th>
          <td>前一年 9 月 – 10 月</td>
          <td>當年 1 月 – 2 月</td>
          <td>查閱目標校課綱、邀約師長推薦信、確認字數與頁數規定</td>
        </tr>
        <tr>
          <th scope="row">3. 母校校內甄選送件截止</th>
          <td>前一年 10 月 – 12 月（主高峰）</td>
          <td>當年 2 月 – 5 月（或併入前一年秋甄）</td>
          <td>完成線上報名、繳費與系所／導師紙本或掃描核章</td>
        </tr>
        <tr>
          <th scope="row">4. 校內放榜、志願分發與母校提名</th>
          <td>前一年 12 月 – 當年 3 月</td>
          <td>當年 4 月 – 9 月</td>
          <td>繳交錄取確認書與保證金，由國際處向接待校發送 Nomination</td>
        </tr>
        <tr>
          <th scope="row">5. 姊妹校網報與宿舍申請</th>
          <td>當年 2 月 – 5 月</td>
          <td>當年 9 月 – 11 月</td>
          <td>依接待校通知上傳護照、英文成績單、財力證明並搶先登記宿舍</td>
        </tr>
        <tr>
          <th scope="row">6. 入學許可、簽證與役男出境</th>
          <td>當年 5 月 – 8 月</td>
          <td>當年 11 月 – 次年 1 月</td>
          <td>收到正式 LoA 後辦理學生簽證、機票、保險、選課抵免預審與役男核准</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>

<section class="uw-section uw-cross-links">
  <h2>搭配截止日總表與文件指南</h2>
  <p><a href="/data/deadlines">查看《全台 71 校交換校內申請截止日行事曆總表》</a> · <a href="/guides/exchange-application">交換申請流程完整指南</a> · <a href="/guides/exchange-study-plan">讀書計畫撰寫指南</a> · <a href="/tools">返回交換免費工具總覽</a></p>
</section>
{render_faq_section(FAQS_TIMELINE)}
{render_compliance_strip()}"""
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
        exact_deadline_count = sum(1 for r in deadlines if r["deadline_iso"] is not None)

        top5_schools = sorted(overview["schools"], key=lambda r: (-r["partner_page_count"], r["school_id"]))[:5]
        top5_rows = "".join(
            f"<tr><th scope='row'><a href='{escape(r['school_path'])}'>{escape(r['school_name'])}</a></th>"
            f"<td>{escape(r['sector'])}</td>"
            f"<td>{r['partner_page_count']} 所（{r['programme_row_count']} 筆方案）</td>"
            f"<td>{r['country_count']} 國／地區</td>"
            f"<td>{_official_link(r['official_url'], '國際處來源')}</td></tr>"
            for r in top5_schools
        )

        body = f"""<p class="eyebrow">UNIWAY OPEN DATA · 台灣交換學生年度公開數據庫</p>
<h1>{escape(spec.h1)}</h1>
<p class="lead">直接由 UniWay 現有全台 {overview['university_count']} 所大專校院與海外合作校資料庫自動統計生成，每筆數據附母校國際處官方來源連結與查核狀態，提供學生、媒體與研究者透明可查證的公開基準。</p>
{render_core_summary_and_citation_box(settings.origin, spec)}

<section class="uw-kpi-grid" aria-label="公開資料庫核心規模">
  <div class="uw-kpi-box uw-kpi-highlight">
    <span class="uw-kpi-label">收錄台灣大專校院數</span>
    <strong class="uw-kpi-value">{overview['university_count']} 所</strong>
    <small>公立 {overview['public_count']} 所 · 私立 {overview['private_count']} 所</small>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">跨校去重海外合作機構數</span>
    <strong class="uw-kpi-value">{overview['unique_foreign_institutions']:,} 所</strong>
    <small>各母校合作校頁面合計 {overview['total_partner_pages']:,} 頁</small>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">涵蓋海外國家與地區</span>
    <strong class="uw-kpi-value">{overview['unique_countries']} 個</strong>
    <small>依標準化國家地區名稱歸併統計</small>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">收錄校內甄選時程紀錄</span>
    <strong class="uw-kpi-value">{len(deadlines)} 校</strong>
    <small>其中 {exact_deadline_count} 校載有具體日期紀錄（含當期與歷次基準）</small>
  </div>
</section>

<section class="uw-section">
  <h2>年度公開數據報告（第 1 波）</h2>
  <ul class="uw-hub-grid">
    <li class="uw-hub-card">
      <span class="uw-card-tag">資料庫即時統計 · 71 校完整比較</span>
      <h3><a href="/data/taiwan-exchange-overview">全台 71 所大學交換資源總覽表</a></h3>
      <p>橫向比較全台 71 所公私立大學之海外合作校頁面數、涵蓋國家地區數、TOEFL/IELTS、多益 TOEIC、日檢 JLPT 門檻列載分布與官方來源，支援關鍵字篩選與多欄位排序。</p>
      <a class="uw-card-cta" href="/data/taiwan-exchange-overview">查看完整 71 校數據表 <span aria-hidden="true">→</span></a>
    </li>
    <li class="uw-hub-card">
      <span class="uw-card-tag">校內甄選行事曆 · 月份篩選</span>
      <h3><a href="/data/deadlines">全台 71 校交換校內申請截止日行事曆總表</a></h3>
      <p>彙整全台 71 校校級出國交換申請梯次、線上收件期限、日期查核狀態與國際處簡章連結，支援依月份（1–12 月）、受理狀態與學校快速檢索。</p>
      <a class="uw-card-cta" href="/data/deadlines">查看 71 校截止日行事曆 <span aria-hidden="true">→</span></a>
    </li>
  </ul>
</section>

<section class="uw-section">
  <h2>資料庫重點預覽：合作校頁面規模前 5 大台灣母校</h2>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="合作校頁面規模前5大台灣母校預覽表，可橫向捲動">
    <table class="uw-data-table">
      <caption>依各母校去重後海外合作校頁面數排序前 5 校（完整 71 校名單見總覽表；合作校數不等於當期開放名額）</caption>
      <thead>
        <tr>
          <th scope="col">台灣母校</th>
          <th scope="col">屬性</th>
          <th scope="col">合作校頁面數（方案總筆數）</th>
          <th scope="col">涵蓋國家／地區數</th>
          <th scope="col">官方來源</th>
        </tr>
      </thead>
      <tbody>{top5_rows}</tbody>
    </table>
  </div>
</section>

<section class="uw-section">
  <h2>資料編製方法與引用準則</h2>
  <ul>
    <li><strong>真實資料庫直連：</strong>所有表格均由系統讀取各母校已建檔之公開合作校名冊與甄選時程即時運算，絕不人工填補未公告之名額或截止時刻。</li>
    <li><strong>區分締約規模與當期名額：</strong>各校國際處公布之名單可能包含「當期開放選填名單」與「歷年締約姊妹校總表」，閱讀與引用時應同時參考狀態欄位。</li>
    <li><strong>搭配免費工具試算：</strong>查完數據後可直接前往 <a href="/tools/language-score-converter">語言檢定選校查詢器</a>、<a href="/tools/timeline-generator">倒推時程產生器</a> 或 <a href="/partners">跨校外國大學頁</a> 深入比對。</li>
  </ul>
</section>
{render_faq_section(FAQS_DATA_HUB)}
{render_compliance_strip()}"""
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
                ("all", f"全部學校（共 {overview['university_count']} 校）"),
                ("public", f"國立／市立大學（{overview['public_count']} 校）"),
                ("private", f"私立大學（{overview['private_count']} 校）"),
            )
        )
        sort_opts = "".join(
            f'<option value="{k}"{" selected" if sort == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("partners", "依合作校頁面數（由多到少）"),
                ("countries", "依涵蓋國家／地區數（由多到少）"),
                ("toeic", "依明確列載 TOEIC 校數（由多到少）"),
                ("jlpt", "依明確列載日檢 JLPT 校數（由多到少）"),
                ("name", "依學校名稱筆畫／字碼排序"),
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
            lang_summary = " · ".join(lang_parts) if lang_parts else "依母校語組總則"
            if r["unconfirmed_lang_count"]:
                lang_summary += f"（待確認/見簡章 {r['unconfirmed_lang_count']}）"

            tbody_html += f"""<tr data-row-sector="{escape(r['sector'])}" data-row-name="{escape(r['school_name'])} {escape(r['short_name'])} {escape(r['school_id'])}" data-partners="{r['partner_page_count']}" data-countries="{r['country_count']}" data-toeic="{r['toeic_count']}" data-jlpt="{r['jlpt_count']}">
  <td>{idx}</td>
  <th scope="row"><a href="{escape(r['school_path'])}">{escape(r['school_name'])}</a><span class="uw-cell-sub">{escape(r['short_name'])} · {escape(r['sector'])}</span></th>
  <td><strong>{r['partner_page_count']}</strong><span class="uw-cell-sub">{r['programme_row_count']} 筆方案</span></td>
  <td><strong>{r['country_count']}</strong></td>
  <td>當期列載 {r['open_listed_count']}<span class="uw-cell-sub">參考/待確認 {r['reference_or_pending_count']}</span></td>
  <td>{escape(lang_summary)}</td>
  <td>{_official_link(r['official_url'], '國際處來源')}<span class="uw-cell-sub">查核：{escape(r['latest_checked'])}</span></td>
</tr>"""

        if not tbody_html:
            tbody_html = "<tr><td colspan='7'>找不到符合篩選條件的大學，請調整關鍵字或學校屬性後重試。</td></tr>"

        latest_mod = max((r["latest_checked"] for r in overview["schools"]), default="2026-10-28")

        body = f"""<p class="eyebrow"><a href="/data">年度公開數據</a> / 全台大專校院交換資源普查</p>
<h1>{escape(spec.h1)}</h1>
<p class="lead">直接讀取 UniWay 資料庫內全台 {overview['university_count']} 所公私立大學之海外交換合作紀錄，統一計算去重後合作校頁面數、涵蓋國家數、方案狀態與語言門檻標註情形。</p>
{render_core_summary_and_citation_box(settings.origin, spec, checked_date=latest_mod)}

<section class="uw-kpi-grid" aria-label="全台交換資源統計摘要">
  <div class="uw-kpi-box uw-kpi-highlight">
    <span class="uw-kpi-label">統計母校總數</span>
    <strong class="uw-kpi-value">{overview['university_count']} 所大學</strong>
    <small>公立 {overview['public_count']} 所 · 私立 {overview['private_count']} 所</small>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">各校合作校頁面總計</span>
    <strong class="uw-kpi-value">{overview['total_partner_pages']:,} 頁</strong>
    <small>跨校歸併後對應 {overview['unique_foreign_institutions']:,} 所海外機構</small>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">全球涵蓋國家與地區</span>
    <strong class="uw-kpi-value">{overview['unique_countries']} 個</strong>
    <small>橫跨歐洲、美洲、亞洲與大洋洲</small>
  </div>
  <div class="uw-kpi-box">
    <span class="uw-kpi-label">目前篩選顯示筆數</span>
    <strong class="uw-kpi-value" id="overview-visible-count">{len(rows)} 校</strong>
    <small>支援無 JS 伺服器篩選與即時前端排序</small>
  </div>
</section>

<section class="uw-tool-card" aria-labelledby="overview-filter-heading">
  <div class="uw-tool-header">
    <h2 id="overview-filter-heading">篩選與排序全台 71 校交換資源數據</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製目前篩選網址</button>
  </div>
  <form method="get" action="/data/taiwan-exchange-overview" class="uw-form-grid" data-data-filter="overview">
    <label class="uw-field">
      <span>搜尋學校名稱或英文縮寫（如 臺大、政大、NCCU）</span>
      <input type="search" name="q" id="ov-q" value="{escape(q_clean)}" placeholder="輸入校名關鍵字…">
    </label>
    <label class="uw-field">
      <span>公立／私立篩選</span>
      <select name="sector" id="ov-sector">{sector_opts}</select>
    </label>
    <label class="uw-field">
      <span>排序方式</span>
      <select name="sort" id="ov-sort">{sort_opts}</select>
    </label>
    <div class="uw-form-actions">
      <button type="submit" class="uw-btn uw-btn-primary">套用篩選排序</button>
      <a class="uw-btn uw-btn-outline" href="/data/taiwan-exchange-overview">重設全部</a>
    </div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="全台 71 所大學交換資源總覽表，可橫向捲動">
    <table class="uw-data-table" id="overview-data-table">
      <caption>全台 {overview['university_count']} 所大學海外交換合作規模、國家數與語檢門檻列載統計（{escape(MANDATORY_DISCLAIMER)}）</caption>
      <thead>
        <tr>
          <th scope="col">#</th>
          <th scope="col">台灣母校（屬性）</th>
          <th scope="col">合作校頁面數</th>
          <th scope="col">涵蓋國家數</th>
          <th scope="col">資料狀態分布</th>
          <th scope="col">公開欄位列載語檢統計（校數）</th>
          <th scope="col">官方來源與查核日</th>
        </tr>
      </thead>
      <tbody id="overview-tbody">{tbody_html}</tbody>
    </table>
  </div>
</section>

<section class="uw-section">
  <h2>欄位口徑與閱讀注意事項</h2>
  <ul>
    <li><strong>合作校頁面數 vs 方案筆數：</strong>同一海外大學在單一母校下若拆為「英語組」「日語組」或不同學院方案，歸併計為 1 個合作校頁面，避免因分組拆列造成校數虛增。</li>
    <li><strong>當期名單列載 vs 參考／待確認：</strong>「當期列載」指來源標記為當期選填名單（仍須核對母校收件時窗）；「參考／待確認」包含校際締約總名錄、院系合作參考、歷史梯次或名額待確認紀錄，不可直接視為當期保證開缺。</li>
    <li><strong>語言門檻統計口徑：</strong>僅統計該母校公開合作校欄位中有明確寫出 TOEFL/IELTS、TOEIC、JLPT 或 CEFR 數值之合作校；若母校採「全校統一語組門檻（寫於簡章總則而未逐校重複標示）」，則歸入「待確認／見簡章」。想直接用自己的分數查達標學校，請使用 <a href="/tools/language-score-converter">語言檢定分數換算與選校查詢器</a>。</li>
  </ul>
</section>
{render_faq_section(FAQS_OVERVIEW_DATA)}
{render_compliance_strip()}"""
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

        # Monthly distribution across all 71 schools (counting all recorded home_application months)
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

        # Sort: open/upcoming with earliest upcoming deadline first, then months, then pending
        order_map = {"open": 0, "upcoming": 1, "action_required": 2, "needs_confirmation": 3, "closed": 4, "reference_only": 5}
        filtered.sort(
            key=lambda r: (
                order_map.get(r["status_code"], 9),
                r["deadline_iso"] or "9999-99-99",
                r["school_id"],
            )
        )

        month_pills = f'<a class="uw-month-pill{" is-active" if month_clean == "all" else ""}" href="/data/deadlines">全部月份（71 校）</a>'
        for m in range(1, 13):
            active_cls = " is-active" if selected_month_int == m else ""
            month_pills += f'<a class="uw-month-pill{active_cls}" href="/data/deadlines?month={m}">{m} 月（{month_counts[m]}）</a>'
        month_pills += (
            f'<a class="uw-month-pill{" is-active" if month_clean == "pending" else ""}" '
            f'href="/data/deadlines?month=pending">日期待確認（{pending_count}）</a>'
        )

        month_select_opts = f'<option value="all"{" selected" if month_clean == "all" else ""}>全部月份</option>'
        for m in range(1, 13):
            month_select_opts += (
                f'<option value="{m}"{" selected" if selected_month_int == m else ""}>{m} 月截止（{month_counts[m]} 校有紀錄）</option>'
            )
        month_select_opts += f'<option value="pending"{" selected" if month_clean == "pending" else ""}>尚未公布確切日期／待確認（{pending_count} 校）</option>'

        status_opts = "".join(
            f'<option value="{k}"{" selected" if status_clean == k else ""}>{lbl}</option>'
            for k, lbl in (
                ("all", "全部受理狀態"),
                ("active", "受理中／即將開放／待辦確認"),
                ("pending", "當期時程待確認（依校方公告）"),
                ("closed", "本梯次已截止／歷年梯次參考"),
            )
        )

        month_summary_cells = "".join(
            f"<td><strong>{month_counts[m]}</strong> 校</td>" for m in range(1, 13)
        )
        month_summary_headers = "".join(f"<th scope='col'>{m}月</th>" for m in range(1, 13))

        tbody_html = ""
        for r in filtered:
            months_attr = ",".join(str(m) for m in r["all_months"]) if r["all_months"] else "pending"
            extra_rounds_html = ""
            if len(r["rounds_summary"]) > 1:
                extra_rounds_html = "<div class='uw-cell-sub'>同校其他梯次：" + escape("；".join(r["rounds_summary"][1:])) + "</div>"

            badge_cls = (
                "uw-tag-ok"
                if r["status_code"] in {"open", "upcoming"}
                else "uw-tag-warn"
                if r["status_code"] == "needs_confirmation"
                else "uw-tag-muted"
            )
            note_short = r["note"] if len(r["note"]) <= 120 else r["note"][:119].rstrip() + "…"

            tbody_html += f"""<tr data-dl-months="{escape(months_attr)}" data-dl-status="{escape(r['status_code'])}" data-dl-name="{escape(r['school_name'])} {escape(r['short_name'])} {escape(r['school_id'])} {escape(r['round_title'])}">
  <th scope="row"><a href="/schools/{escape(r['school_id'])}">{escape(r['school_name'])}</a><span class="uw-cell-sub">{escape(r['short_name'])} · {escape(r['sector'])}</span></th>
  <td>{escape(r['round_title'])}{extra_rounds_html}</td>
  <td><strong>{escape(r['deadline_display'])}</strong><span class="uw-cell-sub">{escape(r['date_status_label'])}</span></td>
  <td><span class="{badge_cls}">{escape(r['status_label'])}</span></td>
  <td>{escape(note_short)}</td>
  <td>
    {_official_link(r['source_url'], '官方簡章／公告')}
    <span class="uw-cell-sub">查核：{escape(r['checked_date'])} · <a href="/tools/timeline-generator?school={escape(r['school_id'])}">倒推時程(.ics)</a></span>
  </td>
</tr>"""

        if not tbody_html:
            tbody_html = "<tr><td colspan='6'>目前沒有符合此月份與篩選條件的學校紀錄，請切換其他月份或重設篩選。</td></tr>"

        latest_checked = max((r["checked_date"] for r in all_rows if r["checked_date"]), default="2026-10-28")

        body = f"""<p class="eyebrow"><a href="/data">年度公開數據</a> / 校內申請截止日行事曆</p>
<h1>{escape(spec.h1)}</h1>
<p class="lead">完整收錄全台 {len(all_rows)} 所大學出國交換校內甄選期限、日期查核狀態與國際處公告來源。點擊任一學校右側的「倒推時程(.ics)」即可自動建立個人準備行事曆。</p>
{render_core_summary_and_citation_box(settings.origin, spec, checked_date=latest_checked)}

<section class="uw-section">
  <h2>全台 71 校交換甄選截止月份分布統計（1–12 月）</h2>
  <p>同一所大學若分設秋季甄選與春季甄選兩梯次，會分別計入對應截止月份；可觀察到台灣大專校院交換收件高度集中於 <strong>9–12 月（秋季第一梯次）</strong>與 <strong>2–3 月（春季第二梯次）</strong>：</p>
  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="全台71校交換截止月份分布統計表，可橫向捲動">
    <table class="uw-data-table">
      <caption>資料庫已記載具體日期之各月份收件學校數統計（未公告確切日期者標為待確認，絕不推估日期）</caption>
      <thead><tr>{month_summary_headers}</tr></thead>
      <tbody><tr>{month_summary_cells}</tr></tbody>
    </table>
  </div>
</section>

<section class="uw-tool-card" aria-labelledby="dl-filter-heading">
  <div class="uw-tool-header">
    <h2 id="dl-filter-heading">依月份、受理狀態與學校檢索截止日（目前顯示 <span id="dl-visible-count">{len(filtered)}</span> 校）</h2>
    <button type="button" class="uw-btn uw-btn-sm uw-btn-outline" data-copy-share-url>複製目前篩選網址</button>
  </div>

  <nav class="uw-month-pills" aria-label="依月份快速切換">{month_pills}</nav>

  <form method="get" action="/data/deadlines" class="uw-form-grid" data-data-filter="deadlines">
    <label class="uw-field">
      <span>搜尋學校名稱或梯次關鍵字</span>
      <input type="search" name="q" id="dl-q" value="{escape(q_clean)}" placeholder="例如：臺大、政大、長庚、春季…">
    </label>
    <label class="uw-field">
      <span>截止月份</span>
      <select name="month" id="dl-month">{month_select_opts}</select>
    </label>
    <label class="uw-field">
      <span>受理狀態</span>
      <select name="status" id="dl-status">{status_opts}</select>
    </label>
    <div class="uw-form-actions">
      <button type="submit" class="uw-btn uw-btn-primary">套用篩選</button>
      <a class="uw-btn uw-btn-outline" href="/data/deadlines">顯示全部 71 校</a>
    </div>
  </form>

  <div class="uw-table-wrap" tabindex="0" role="region" aria-label="全台 71 校交換校內申請截止日總表，可橫向捲動">
    <table class="uw-data-table" id="deadlines-data-table">
      <caption>全台 {len(all_rows)} 所大學出國交換校內甄選期限與官方來源一覽表（{escape(MANDATORY_DISCLAIMER)}）</caption>
      <thead>
        <tr>
          <th scope="col">台灣母校</th>
          <th scope="col">收錄甄選梯次</th>
          <th scope="col">記載截止期限（臺灣時間）</th>
          <th scope="col">目前狀態</th>
          <th scope="col">收件與補件重點摘要</th>
          <th scope="col">官方來源與時程工具</th>
        </tr>
      </thead>
      <tbody id="deadlines-tbody">{tbody_html}</tbody>
    </table>
  </div>
</section>

<section class="uw-section uw-cross-links">
  <h2>延伸工具與數據表</h2>
  <p><a href="/tools/timeline-generator">交換申請倒推時程表產生器（匯出 .ics）</a> · <a href="/data/taiwan-exchange-overview">全台 71 校交換資源總覽表</a> · <a href="/tools/language-score-converter">語檢分數換算與選校查詢</a> · <a href="/schools">瀏覽各母校交換專頁</a></p>
</section>
{render_faq_section(FAQS_DEADLINES_DATA)}
{render_compliance_strip()}"""
        return render_data_page(
            spec,
            body,
            [("首頁", "/"), ("年度公開數據", "/data"), ("全台 71 校交換截止日總表", spec.path)],
            FAQS_DEADLINES_DATA,
            variables=("校內線上報名截止日", "甄選梯次狀態", "日期核實狀態", "國際處官方公告網址"),
            keywords=("大學交換申請截止日", "出國交換行事曆", "全台71校交換簡章時間", "交換生報名期限"),
            date_modified=latest_checked,
        )
