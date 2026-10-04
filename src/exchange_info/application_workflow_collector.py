from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

import requests
from bs4 import BeautifulSoup

from .experience_collector import school_search_name
from .ntpu_student_view import (
    NTPU_116_ANNOUNCEMENT_URL,
    NTPU_116_GUIDELINES_URL,
    NTPU_FILES_URL,
)
from .models import (
    ApplicationSourceRole,
    ApplicationStep,
    ApplicationSubmissionDetails,
    ApplicationSubmissionMethod,
    ApplicationWorkflowSource,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)
from .university_registry import NTPU, require_university
from .web_search import search_text
from .workflow_structuring import structure_application_workflow


CGU_PARTNER_LIST_URL = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554"
CGU_SELECTION_URL = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656"
CGU_SUBSIDY_URL = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15724"
CGU_CREDIT_FORM_URL = (
    "https://www.cgu.edu.tw/academic-en/ServerFile/Get/"
    "b7031ca7-1be8-4431-846b-68f64e90c9f1?isCms=False&nodeId=10672&sId=30890"
)

LINCOLN_INCOMING_URL = (
    "https://www.lincoln.ac.nz/study/study-abroad-and-student-exchange/"
    "coming-to-lincoln-on-exchange/"
)
LINCOLN_STUDY_ABROAD_URL = (
    "https://www.lincoln.ac.nz/study/study-abroad-and-student-exchange/"
    "study-abroad-at-lincoln-university/"
)
LINCOLN_INBOUND_PROGRAMME_URL = (
    "https://www.lincoln.ac.nz/study/study-programmes/programme-search/"
    "international-exchange-inbound/"
)
LINCOLN_VISA_URL = "https://www.lincoln.ac.nz/study/apply-and-enrol/apply/visa-requirements/"

KNOWN_OFFICIAL_PAGES = {
    "lincoln.ac.nz": [
        ("Lincoln University incoming exchange", LINCOLN_INCOMING_URL),
        ("Lincoln University study abroad application", LINCOLN_STUDY_ABROAD_URL),
        ("Lincoln University inbound exchange programme", LINCOLN_INBOUND_PROGRAMME_URL),
        ("Lincoln University visa requirements", LINCOLN_VISA_URL),
    ]
}

EXCLUDED_PATH_TERMS = (
    "outbound",
    "outgoing",
    "going-on-exchange",
    "students-going",
    "asdfasdf",
)
STRONG_OFFICIAL_PAGE_TERMS = (
    "incoming",
    "inbound",
    "exchange",
    "study-abroad",
    "visa",
    "erasmus",
    "nomination",
    "international affairs",
    "international students",
)
SUPPORTING_OFFICIAL_PAGE_TERMS = ("apply", "application", "mobility")
EXCLUDED_OFFICIAL_TITLE_TERMS = re.compile(
    r"sakura exchange science program|\b(?:student )?exchange event\b",
    re.IGNORECASE,
)
OFFICIAL_TRACKING_QUERY_KEYS = {
    "fbclid",
    "gad_source",
    "gclid",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}
ACADEMIC_PUBLIC_SUFFIXES = {
    "ac.jp",
    "ac.kr",
    "ac.nz",
    "ac.th",
    "ac.uk",
    "edu.au",
    "edu.cn",
    "edu.hk",
    "edu.my",
    "edu.pl",
    "edu.sg",
    "edu.tw",
}


def collect_application_workflow(
    partner: PartnerUniversity,
    *,
    home_university: str = "長庚大學",
    max_partner_pages: int = 5,
    timeout_seconds: float = 20.0,
    rate_limit_seconds: float = 1.0,
) -> UniversityApplicationWorkflow:
    home = require_university(home_university)
    checked_at = datetime.now(timezone.utc)
    partner_pages = discover_official_partner_pages(partner, max_pages=max_partner_pages)
    source_text: dict[str, str] = {}
    for index, (_, url) in enumerate(partner_pages):
        if index:
            time.sleep(max(0.0, rate_limit_seconds))
        source_text[url] = fetch_official_page_text(
            url, partner.website, timeout_seconds=timeout_seconds
        )

    sources = _home_sources(home.school_name, checked_at)
    sources.extend(
        ApplicationWorkflowSource(
            title=title,
            source_url=url,
            role=ApplicationSourceRole.PARTNER_UNIVERSITY,
            checked_at=checked_at,
        )
        for title, url in partner_pages
    )

    if home.id != NTPU.id and official_host(partner.website) == "lincoln.ac.nz":
        steps = _lincoln_steps(partner)
        coverage_status = "official_verified"
        coverage_note = (
            "已整合長庚國際處與 Lincoln University 官方流程。兩個 Lincoln 官方頁面的申請日期不同，"
            "系統已分別列出並標記為送件前必須確認。"
        )
    else:
        steps = (
            _ntpu_generic_steps(partner, partner_pages, source_text)
            if home.id == NTPU.id
            else _generic_steps(partner, partner_pages, source_text)
        )
        readable_count = sum(bool(text) for text in source_text.values())
        coverage_status = (
            "official_verified"
            if readable_count >= 2
            else "official_partial"
            if partner_pages
            else "not_found"
        )
        coverage_note = (
            f"已整合{home.short_name}校內流程與 {readable_count} 個可讀取的合作校官方頁；"
            "未公開或無法讀取的細節會標示為需以提名信確認。"
        )

    return structure_application_workflow(
        UniversityApplicationWorkflow(
            home_university=home.school_name,
            school_name=partner.school_name,
            partner_website=partner.website,
            country=partner.country,
            program_type=partner.program_type,
            steps=steps,
            sources=_dedupe_sources(sources),
            last_checked=checked_at,
            coverage_status=coverage_status,
            coverage_note=coverage_note,
            disclaimer=f"截止日與申請方式可能調整；送件前請再核對{home.short_name}國際處、合作校通知信與官方申請頁。",
        )
    )


def build_cgu_reference_workflow(
    partner: PartnerUniversity,
    *,
    partner_sources: list[tuple[str, str]],
    partner_application_summary: str,
    partner_application_details: list[str],
    required_documents: list[str],
    timing: str = "以提名信與合作校交換生入口為準",
    submission_method: ApplicationSubmissionMethod = (
        ApplicationSubmissionMethod.UNKNOWN
    ),
    submission_email: str | None = None,
    portal_url: str | None = None,
    partner_website: str | None = None,
    coverage_note: str | None = None,
    checked_at: datetime | None = None,
) -> UniversityApplicationWorkflow:
    """Build a conservative CGU workflow from manually verified official pages.

    The result intentionally remains a legacy, reference-only workflow. Exact
    deadlines are not inferred from recurring month/day text, and every partner
    application detail remains confirmation-gated until a reviewed workflow is
    formally published.
    """

    checked_at = checked_at or datetime.now(timezone.utc)
    if not partner_sources:
        raise ValueError("partner_sources must include at least one official page")
    effective_partner = partner.model_copy(
        update={"website": partner_website or partner.website}
    )
    source_urls = list(dict.fromkeys(url for _, url in partner_sources if url))
    primary_url = portal_url or source_urls[0]
    steps = _generic_steps(effective_partner, partner_sources, {})
    partner_step_data = steps[3].model_dump()
    partner_step_data.update(
        {
            "timing": timing,
            "summary": partner_application_summary,
            "details": partner_application_details,
            "required_documents": required_documents,
            "document_requirements": [],
            "submission": ApplicationSubmissionDetails(
                method=submission_method,
                email=submission_email,
                portal_url=portal_url,
                deadline_note=(
                    "期限僅供來源查核；應以長庚提名信與合作校當期通知為準。"
                ),
            ),
            "action_url": primary_url,
            "source_urls": [effective_partner.source_url, *source_urls],
            "checked_at": checked_at,
            "needs_confirmation": True,
        }
    )
    steps[3] = ApplicationStep.model_validate(partner_step_data)
    sources = _home_sources("長庚大學", checked_at)
    sources.extend(
        ApplicationWorkflowSource(
            title=title,
            source_url=url,
            role=ApplicationSourceRole.PARTNER_UNIVERSITY,
            checked_at=checked_at,
        )
        for title, url in partner_sources
    )
    return structure_application_workflow(
        UniversityApplicationWorkflow(
            home_university="長庚大學",
            school_name=effective_partner.school_name,
            partner_website=effective_partner.website,
            country=effective_partner.country,
            program_type=effective_partner.program_type,
            steps=steps,
            sources=_dedupe_sources(sources),
            last_checked=checked_at,
            coverage_status="official_partial",
            coverage_note=(
                coverage_note
                or "已建立長庚校內流程並連結合作校官方交換資訊；學年度、梯次與個人期限仍須依提名信確認。"
            ),
            disclaimer="此流程是尚未正式發布的參考資料；送件前請核對長庚國際處、合作校提名信與當期官方申請頁。",
        )
    )


def discover_official_partner_pages(
    partner: PartnerUniversity, *, max_pages: int = 5
) -> list[tuple[str, str]]:
    host = official_host(partner.website)
    if not host:
        return []
    candidates = list(KNOWN_OFFICIAL_PAGES.get(host, []))
    if not candidates:
        candidates.extend(_search_official_pages(partner, host, max_pages * 2))
    if partner.website:
        candidates.append((f"{partner.school_name} official website", partner.website))

    ranked: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    official_home = normalize_official_url(partner.website) if partner.website else ""
    for title, url in candidates:
        title = clean_official_page_title(title)
        normalized = normalize_official_url(url)
        path = urlparse(normalized).path.lower()
        if not is_official_partner_url(normalized, partner.website):
            continue
        if any(term in path for term in EXCLUDED_PATH_TERMS):
            continue
        if EXCLUDED_OFFICIAL_TITLE_TERMS.search(title):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        page_identity = f"{title} {path}".lower()
        strong_score = sum(term in page_identity for term in STRONG_OFFICIAL_PAGE_TERMS)
        supporting_score = sum(
            term in page_identity for term in SUPPORTING_OFFICIAL_PAGE_TERMS
        )
        if strong_score == 0 and normalized.rstrip("/") != official_home.rstrip("/"):
            continue
        score = strong_score * 2 + supporting_score
        ranked.append((score, title.strip() or partner.school_name, normalized))
    ranked.sort(
        key=lambda row: (
            -row[0],
            _official_language_rank(row[2]),
            len(urlparse(row[2]).path),
        )
    )
    selected: list[tuple[str, str]] = []
    seen_titles: set[str] = set()
    for _, title, url in ranked:
        title_key = re.sub(r"\W+", " ", title.casefold()).strip()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        selected.append((title, url))
        if len(selected) >= max_pages:
            break
    return selected


def _official_language_rank(url: str) -> int:
    path = urlparse(url).path.casefold()
    if path.startswith(("/en/", "/eng/", "/english/")):
        return 0
    if path.startswith(("/br/", "/cn/", "/de/", "/es/", "/fr/", "/jp/", "/pt/", "/zh/")):
        return 2
    return 1


def build_official_search_queries(partner: PartnerUniversity, host: str) -> list[str]:
    name = school_search_name(partner.school_name)
    return [
        f"{name} {host} incoming exchange application deadline",
        f"{name} {host} exchange nomination required documents",
        f"{name} {host} exchange student visa insurance accommodation",
    ]


def _search_official_pages(
    partner: PartnerUniversity, host: str, max_results: int
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for query in build_official_search_queries(partner, host):
        results = search_text(
            query,
            max_results=max(2, min(5, max_results)),
            timeout_seconds=15,
        )
        for item in results:
            url = str(item.get("href") or item.get("url") or "")
            title = str(item.get("title") or partner.school_name)
            if url:
                rows.append((title, url))
    return rows


def fetch_official_page_text(
    url: str,
    official_website: str | None,
    *,
    timeout_seconds: float = 20.0,
) -> str:
    if not is_official_partner_url(url, official_website):
        return ""
    try:
        response = requests.get(
            url,
            timeout=timeout_seconds,
            headers={"User-Agent": "ExchangeInfoMVP/0.1 (+public academic information index)"},
        )
        response.raise_for_status()
    except requests.RequestException:
        return ""
    if "text/html" not in response.headers.get("content-type", "text/html").lower():
        return ""
    if not response.encoding or response.encoding.casefold() in {
        "iso-8859-1",
        "latin-1",
        "latin1",
    }:
        response.encoding = response.apparent_encoding or "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    for node in soup.select("script, style, nav, footer, header, aside, form, noscript"):
        node.decompose()
    main = soup.select_one("main, article, [role=main]") or soup.body or soup
    return "\n".join(
        dict.fromkeys(
            line.strip()
            for line in main.get_text("\n", strip=True).splitlines()
            if len(line.strip()) >= 3
        )
    )[:60000]


def official_host(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc.lower().removeprefix("www.")
    parts = host.split(".")
    public_suffix = ".".join(parts[-2:]) if len(parts) >= 2 else host
    if len(parts) >= 3 and public_suffix in ACADEMIC_PUBLIC_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def is_official_partner_url(url: str, official_website: str | None) -> bool:
    expected = official_host(official_website)
    actual = official_host(url)
    return bool(expected and actual and actual == expected)


def normalize_official_url(url: str) -> str:
    value = url.strip()
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    query = urlencode(
        [
            (key, item)
            for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if key.casefold() not in OFFICIAL_TRACKING_QUERY_KEYS
        ]
    )
    return parsed._replace(fragment="", query=query).geturl()


def clean_official_page_title(value: str) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    if "..." in compact:
        compact = f"{compact.split('...', 1)[0].rstrip()}..."
    return compact[:180]


def _cgu_sources(checked_at: datetime) -> list[ApplicationWorkflowSource]:
    specs = [
        ("長庚大學締約學校與申請日期", CGU_PARTNER_LIST_URL),
        ("長庚大學出國研修校內甄選", CGU_SELECTION_URL),
        ("長庚大學出國研修補助與行政規定", CGU_SUBSIDY_URL),
        ("長庚大學出國研修課程申請及學分抵免表", CGU_CREDIT_FORM_URL),
    ]
    return [
        ApplicationWorkflowSource(
            title=title,
            source_url=url,
            role=ApplicationSourceRole.HOME_UNIVERSITY,
            checked_at=checked_at,
        )
        for title, url in specs
    ]


def _ntpu_sources(checked_at: datetime) -> list[ApplicationWorkflowSource]:
    specs = [
        ("國立臺北大學 116 學年度赴外交換公告", NTPU_116_ANNOUNCEMENT_URL),
        ("國立臺北大學 116 學年度赴外交換簡章", NTPU_116_GUIDELINES_URL),
        ("國立臺北大學國際事務處檔案下載", NTPU_FILES_URL),
    ]
    return [
        ApplicationWorkflowSource(
            title=title,
            source_url=url,
            role=ApplicationSourceRole.HOME_UNIVERSITY,
            checked_at=checked_at,
        )
        for title, url in specs
    ]


def _home_sources(
    home_university: str,
    checked_at: datetime,
) -> list[ApplicationWorkflowSource]:
    return (
        _ntpu_sources(checked_at)
        if require_university(home_university).id == NTPU.id
        else _cgu_sources(checked_at)
    )


def _standard_opening_steps(partner: PartnerUniversity) -> list[ApplicationStep]:
    eligibility = partner.eligibility or "先確認長庚校內資格、學院、學制與合作校語言門檻。"
    return [
        ApplicationStep(
            order=1,
            phase="校內準備",
            title="確認資格並選擇志願學校",
            responsible_party="學生",
            timing="秋季班通常 11/01–12/20；春季班通常 4/21–6/06",
            summary="先同時核對長庚校內資格與合作校限制；長庚申請表可填 2 個志願。",
            details=[eligibility, f"本校表列名額：{partner.quota or '依當期公告'}。"],
            required_documents=["語言檢定成績或可證明語言能力的文件", "當期長庚申請公告要求的資格證明"],
            action_url=CGU_PARTNER_LIST_URL,
            source_urls=[CGU_PARTNER_LIST_URL, CGU_SELECTION_URL, partner.source_url],
        ),
        ApplicationStep(
            order=2,
            phase="校內申請",
            title="在長庚期限內送出校內申請",
            responsible_party="學生 → 長庚國際處",
            timing="務必在長庚當期公告截止日前完成",
            summary="先完成長庚校內甄選，不要直接向合作校送件。文件以當期公告與申請表為準。",
            details=["依當期公告填寫出國研修申請資料。", "送出前檢查志願順序、語言成績與附件是否完整。"],
            required_documents=["長庚出國研修申請表", "歷年成績單", "語言能力證明", "當期公告要求的其他附件"],
            action_url=CGU_SELECTION_URL,
            source_urls=[CGU_SELECTION_URL],
        ),
        ApplicationStep(
            order=3,
            phase="甄選與提名",
            title="等待校內甄選結果與長庚正式提名",
            responsible_party="長庚國際處",
            timing="通常於學期結束後 2 週內審查，第 3 週公告結果",
            summary="通過校內甄選不等於已被合作校錄取；長庚完成提名後，合作校才會開放下一階段。",
            details=["留意長庚信箱與國際處通知。", "未收到合作校通知前，不要自行建立重複申請。"],
            action_url=CGU_SELECTION_URL,
            source_urls=[CGU_SELECTION_URL],
        ),
    ]


def _ntpu_opening_steps(partner: PartnerUniversity) -> list[ApplicationStep]:
    eligibility = partner.eligibility or "先確認臺北大學校內資格、語組與合作校個別門檻。"
    return [
        ApplicationStep(
            order=1,
            phase="校內準備",
            title="確認資格、語組與最多 5 個志願",
            responsible_party="學生",
            timing="秋季／全學年原則 10/01–10/31；春季原則 4/01–4/30",
            summary="同一梯次只能選英語、日語或中文其中一組，並依當期名額表填列最多 5 個志願。",
            details=[
                eligibility,
                "校內基本門檻為前一學年平均 75 分以上；大學部亦可用班排前 50%。",
                f"本校表列名額：{partner.quota or '依 116 學年度官方名額表'}。",
            ],
            required_documents=["有效官方語言成績（英語組／日語組）", "歷年正式成績單與班級排名"],
            action_url=NTPU_116_ANNOUNCEMENT_URL,
            source_urls=[NTPU_116_ANNOUNCEMENT_URL, NTPU_116_GUIDELINES_URL, partner.source_url],
        ),
        ApplicationStep(
            order=2,
            phase="校內申請",
            title="完成臺北大學線上申請與文件上傳",
            responsible_party="學生 → 臺北大學國際事務處",
            timing="以當期公告截止時間為準",
            summary="在校內系統填寫志願並上傳簽名申請表、語言成績、研修計畫及正式成績單。",
            details=[
                "研修計畫須使用所選語組語言，包含學習背景、申請動機與未來研修規劃，最多 5,000 字。",
                "一年級碩士生另附完整大學成績單。",
            ],
            required_documents=["簽名申請表", "有效語言證明", "交換研修計畫書", "正式成績單與排名"],
            action_url=NTPU_116_ANNOUNCEMENT_URL,
            source_urls=[NTPU_116_ANNOUNCEMENT_URL, NTPU_116_GUIDELINES_URL],
        ),
        ApplicationStep(
            order=3,
            phase="甄選與分發",
            title="完成書審、研修計畫及語組面試",
            responsible_party="臺北大學國際事務處／甄選委員",
            timing="秋季梯次通常 11 月下旬面試、12 月公告；春季梯次通常 5 月面試、6 月公告",
            summary="書審 30%、研修計畫 30%、面試 40%，再依總成績及志願序分發；總分低於 70 分不予推薦。",
            details=["獲校內推薦不等同合作校正式錄取。", "錄取後依通知繳交錄取確認及家長同意資料。"],
            required_documents=["錄取確認資料", "家長同意資料（獲推薦後）"],
            action_url=NTPU_116_GUIDELINES_URL,
            source_urls=[NTPU_116_GUIDELINES_URL],
        ),
    ]


def _lincoln_steps(partner: PartnerUniversity) -> list[ApplicationStep]:
    steps = _standard_opening_steps(partner)
    steps[0].details = [
        "需符合長庚大學「領航者補助作業要點」與校內甄選規定。",
        "Option A：IELTS overall 6.0，單科不得低於 5.5；長庚合作校表建議修 3–4 門大學部課程。",
        "Option B：IELTS overall 5.5，單科不得低於 5.0；可修較少的 100-level 課程，科目數以提名通知確認。",
        f"長庚合作校表列交換名額：{partner.quota or '依當期公告'} 人；研修期間：{partner.study_period or '依當期公告'}。",
    ]
    steps[0].required_documents = [
        "IELTS 或 Lincoln 接受的同等英文能力證明",
        "當期長庚申請公告要求的資格證明",
    ]
    steps.extend(
        [
            ApplicationStep(
                order=4,
                phase="合作校提名",
                title="長庚向 Lincoln University 提名",
                responsible_party="長庚國際處 → Lincoln University",
                timing="Lincoln 官方 Study Abroad 頁：S1 前一年 9/15；S2 當年 3/15",
                summary="學生必須先由母校核准並提名，不能跳過長庚直接以交換生身分申請。",
                details=["確認長庚已將姓名與聯絡資料送交 Lincoln。", "提名完成後，Lincoln 會直接寄送 International Exchange 線上申請指示。"],
                action_url=LINCOLN_STUDY_ABROAD_URL,
                source_urls=[LINCOLN_INCOMING_URL, LINCOLN_STUDY_ABROAD_URL],
            ),
            ApplicationStep(
                order=5,
                phase="合作校申請",
                title="依 Lincoln 信件完成線上申請",
                responsible_party="學生 → Lincoln University",
                timing="官方頁日期不同：9/30、3/30；另一頁列 10/15、4/15",
                summary="收到提名信後，依信中的 International Exchange 入口送件；送出前必須向 Lincoln 確認適用日期。",
                details=["Semester 1：Study Abroad 頁列前一年 9/30；Incoming Exchange 頁列前一年 10/15。", "Semester 2：Study Abroad 頁列當年 3/30；Incoming Exchange 頁列當年 4/15。", "以提名信、MyLinc 顯示與 Lincoln 國際處回覆作最終依據。"],
                required_documents=["經認證的英文歷年成績單", "經認證的護照影本", "英文能力證明"],
                action_url=LINCOLN_INCOMING_URL,
                source_urls=[LINCOLN_INCOMING_URL, LINCOLN_STUDY_ABROAD_URL, partner.source_url],
                needs_confirmation=True,
            ),
            ApplicationStep(
                order=6,
                phase="課程與錄取",
                title="選課並接受 Offer of Place",
                responsible_party="學生 ↔ Lincoln University",
                timing="完成申請後依 Lincoln 通知",
                summary="Lincoln 審查後會寄送 Offer of Place 與選課資訊；交換期間必須維持全時修課。",
                details=["一般建議修讀 60 credits，交換生最低全時負荷為 45 credits。", "登入 MyLinc 接受錄取，核對姓名、學期、課程層級與條件。", "同時向長庚系所辦理出國前課程申請，以利返國抵免。"],
                required_documents=["Offer of Place", "預計修課清單", "長庚出國研修課程申請及學分抵免表"],
                action_url=LINCOLN_INBOUND_PROGRAMME_URL,
                source_urls=[LINCOLN_INCOMING_URL, LINCOLN_INBOUND_PROGRAMME_URL, CGU_CREDIT_FORM_URL],
            ),
            ApplicationStep(
                order=7,
                phase="行前安排",
                title="辦理學生簽證、保險與住宿",
                responsible_party="學生",
                timing="取得 Offer of Place 後立即開始，出發前完成",
                summary="出發前必須取得紐西蘭學生簽證，並完成符合 Lincoln 規定的醫療／旅遊保險與住宿安排。",
                details=["交換生不繳 Lincoln 學費，但仍可能需付學生服務費、保險與住宿費。", "簽證核發時間會變動，取得錄取文件後不要延後辦理。", "比較校內宿舍與校外住宿的費用、餐食、交通與合約日期。"],
                required_documents=["有效護照", "Offer of Place", "簽證財力與其他移民局要求文件", "合格保險證明", "住宿確認"],
                action_url=LINCOLN_VISA_URL,
                source_urls=[LINCOLN_INCOMING_URL, LINCOLN_VISA_URL],
            ),
            ApplicationStep(
                order=8,
                phase="長庚行前行政",
                title="簽署行政契約並完成出國前程序",
                responsible_party="學生 ↔ 長庚國際處／系所",
                timing="出發前",
                summary="確認補助、行政契約、課程預審與出國資料均已完成；變更學校或國家前要先取得核准。",
                details=["依補助規定簽署行政契約。", "若要變更學校、國家或研修期間，先向長庚確認是否影響資格與補助。", "保存所有核准信、收據與正式文件。"],
                required_documents=["行政契約", "課程預審／學分抵免表", "簽證與保險資料", "補助要求文件"],
                action_url=CGU_SUBSIDY_URL,
                source_urls=[CGU_SUBSIDY_URL, CGU_CREDIT_FORM_URL],
            ),
            ApplicationStep(
                order=9,
                phase="返國結案",
                title="返國辦理學分抵免與補助結案",
                responsible_party="學生 → 長庚系所／國際處",
                timing="學分抵免原則上於返校學期開始後 2 週內辦理",
                summary="返國後依期限送交成績與抵免資料；若領有補助，也要完成心得或其他結案義務。",
                details=["取得 Lincoln 正式成績單。", "依長庚核准課程辦理學分抵免。", "核對補助契約要求的心得、成果或核銷文件與期限。"],
                required_documents=["合作校正式成績單", "學分抵免申請資料", "補助結案與心得文件（如適用）"],
                action_url=CGU_CREDIT_FORM_URL,
                source_urls=[CGU_CREDIT_FORM_URL, CGU_SUBSIDY_URL],
            ),
        ]
    )
    return steps


def _generic_steps(
    partner: PartnerUniversity,
    partner_pages: list[tuple[str, str]],
    source_text: dict[str, str],
) -> list[ApplicationStep]:
    steps = _standard_opening_steps(partner)
    official_url = partner_pages[0][1] if partner_pages else partner.website
    source_urls = [url for _, url in partner_pages] or [url for url in [partner.website] if url]
    extracted = _extract_official_signals("\n".join(source_text.values()))
    steps.extend(
        [
            ApplicationStep(
                order=4,
                phase="合作校申請",
                title="依提名信完成合作校申請",
                responsible_party="學生 → 合作校",
                timing=partner.application_deadline or extracted.get("deadline") or "以提名信與合作校入口為準",
                summary=partner.application_info or "長庚提名後，合作校通常會以電子郵件提供申請入口與個人期限。",
                details=["只使用合作校官方網域的申請入口。", "若公開頁與提名信日期不同，以合作校針對交換生寄出的通知為準。"],
                required_documents=extracted.get("documents", []) or ["英文成績單", "護照影本", "語言能力證明（依合作校要求）"],
                action_url=official_url,
                source_urls=[partner.source_url, *source_urls],
                needs_confirmation=True,
            ),
            ApplicationStep(
                order=5,
                phase="錄取與行前",
                title="接受錄取並完成選課、簽證、保險與住宿",
                responsible_party="學生 ↔ 合作校／長庚",
                timing="收到正式錄取後立即辦理",
                summary="核對錄取條件與修課負荷，並在出發前完成長庚課程預審、簽證、保險及住宿。",
                details=["合作校規定會因國家、學期與學制而不同。", "簽證與保險只連到學校或政府官方說明，不使用代辦廣告資料。"],
                required_documents=["正式錄取文件", "預計修課清單", "簽證與保險文件", "住宿確認"],
                action_url=official_url,
                source_urls=[*source_urls, CGU_CREDIT_FORM_URL],
                needs_confirmation=True,
            ),
            ApplicationStep(
                order=6,
                phase="返國結案",
                title="辦理學分抵免與補助結案",
                responsible_party="學生 → 長庚系所／國際處",
                timing="返校學期開始後儘速辦理，學分抵免原則上 2 週內",
                summary="繳交正式成績與抵免文件；若領有補助，依契約完成心得及結案資料。",
                required_documents=["合作校正式成績單", "學分抵免資料", "補助結案與心得文件（如適用）"],
                action_url=CGU_CREDIT_FORM_URL,
                source_urls=[CGU_CREDIT_FORM_URL, CGU_SUBSIDY_URL],
            ),
        ]
    )
    return steps


def _ntpu_generic_steps(
    partner: PartnerUniversity,
    partner_pages: list[tuple[str, str]],
    source_text: dict[str, str],
) -> list[ApplicationStep]:
    steps = _ntpu_opening_steps(partner)
    official_url = partner_pages[0][1] if partner_pages else partner.website
    source_urls = [url for _, url in partner_pages] or [
        url for url in [partner.website] if url
    ]
    extracted = _extract_official_signals("\n".join(source_text.values()))
    steps.extend(
        [
            ApplicationStep(
                order=4,
                phase="合作校提名與申請",
                title="依提名信完成合作校申請",
                responsible_party="臺北大學國際處提名 → 學生向合作校送件",
                timing=partner.application_deadline
                or extracted.get("deadline")
                or "以提名信與合作校交換生入口為準",
                summary=partner.application_info
                or "臺北大學完成提名後，依合作校寄送的帳號、申請入口及個人期限完成第二階段。",
                details=[
                    "只使用合作校官方網域或提名信提供的申請入口。",
                    "公開頁與個人提名信日期不同時，以合作校針對該梯次的通知為準。",
                ],
                required_documents=extracted.get("documents", [])
                or ["英文正式成績單", "護照影本", "語言能力證明", "Learning Agreement／預計修課資料"],
                action_url=official_url,
                source_urls=[partner.source_url, *source_urls],
                needs_confirmation=True,
            ),
            ApplicationStep(
                order=5,
                phase="錄取與行前",
                title="接受合作校錄取並完成選課、簽證、保險與住宿",
                responsible_party="學生 ↔ 合作校／臺北大學系所",
                timing="收到正式錄取文件後立即辦理",
                summary="核對錄取學期、修課負荷及費用，並在出國前完成臺北大學行前選課程序、簽證、保險與住宿。",
                details=[
                    "合作校是否提供宿舍及申請期限須逐校確認。",
                    "簽證與保險資訊只採合作校或目的地政府官方來源。",
                ],
                required_documents=["正式錄取文件", "出國選課行前申請資料", "簽證與保險文件", "住宿確認"],
                action_url=official_url,
                source_urls=[*source_urls, NTPU_FILES_URL],
                needs_confirmation=True,
            ),
            ApplicationStep(
                order=6,
                phase="抵達與返國",
                title="完成抵達回報、交換心得與學分採認",
                responsible_party="學生 → 臺北大學國際處／系所／註冊組",
                timing="抵達及返國後各 1 個月內完成指定回報",
                summary="抵達合作校 1 個月內回報當地聯絡資料；返國 1 個月內繳交交換心得並依正式成績辦理學分採認。",
                details=["保留合作校正式成績單與課程大綱。", "依系所及註冊組規定完成學分採認。"],
                required_documents=["當地聯絡資料", "合作校正式成績單", "課程大綱", "交換心得"],
                action_url=NTPU_FILES_URL,
                source_urls=[NTPU_116_GUIDELINES_URL, NTPU_FILES_URL],
            ),
        ]
    )
    return steps


def _extract_official_signals(text: str) -> dict[str, Any]:
    compact = re.sub(r"\s+", " ", text)
    result: dict[str, Any] = {}
    deadline = re.search(
        r"(?:deadline|application closes?|apply by).{0,80}?(?:\d{1,2}\s+[A-Za-z]+|[A-Za-z]+\s+\d{1,2})",
        compact,
        re.IGNORECASE,
    )
    if deadline:
        result["deadline"] = deadline.group(0)[:150]
    documents: list[str] = []
    document_terms = [
        (r"academic transcript", "英文歷年成績單"),
        (r"passport", "護照影本"),
        (r"english (?:language |proficiency |competency )?(?:test|evidence|certificate)", "英文能力證明"),
        (r"learning agreement", "Learning Agreement／修課協議"),
        (r"motivation letter|statement of purpose", "動機信／讀書計畫"),
    ]
    for pattern, label in document_terms:
        if re.search(pattern, compact, re.IGNORECASE):
            documents.append(label)
    result["documents"] = documents
    return result


def _dedupe_sources(
    sources: list[ApplicationWorkflowSource],
) -> list[ApplicationWorkflowSource]:
    return list({source.source_url: source for source in sources}.values())
