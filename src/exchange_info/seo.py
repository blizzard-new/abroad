"""Public, server-rendered catalogue pages; never reads a visitor's workspace."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from html import escape
from urllib.parse import quote, urlencode, urlsplit
from time import monotonic
from xml.etree.ElementTree import Element, SubElement, tostring
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response

from .cross_school_partners import (
    build_cross_school_partner_directory,
    build_cross_school_partner_page_data,
    render_cross_school_partner_directory_body,
    render_cross_school_partner_page_body,
    resolve_country_slug_and_zh,
)
from .models import CatalogueSourceStatus, PartnerUniversity
from .school_identity import school_identity_key
from .seo_changes import ContentChanges
from .seo_quality import digest, material_content
from .seo_guides import COUNTRIES, GUIDES, country_slug
from .seo_articles import ARTICLES, Article, article_schema, guide_index, render_article
from .seo_analytics import analytics_markup
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile

DEFAULT_ORIGIN = "https://app.uniway-tw.com"
HOME_TITLE = "UniWay｜交換學生申請、合作學校與選校資訊"
HOME_DESCRIPTION = "UniWay 整理全台大學交換學生申請與海外合作校資訊，協助比較學校、查詢資格與名額、準備申請文件及規劃時程。公開資料免登入，申請規定以各校最新官方公告為準。"
NOTICE = "UniWay 是獨立資訊整理平台，並非校方。合作關係不等於當期開放申請；資格、名額、期限與文件請以母校國際處及合作校最新公告為準。"
EDITORIAL_PATHS = ("/partners", "/destinations", "/guides", "/editorial-policy", *("/destinations/" + slug for slug in COUNTRIES), *("/guides/" + slug for slug in GUIDES))
AVAILABILITY = {
    "open": "名單列載（請另確認本期受理時窗）", "agreement_only": "合作協議參考，非本期名額",
    "departmental_reference": "院系合作參考", "not_open": "未開放", "needs_confirmation": "待確認",
    "zero_quota": "零名額", "fee_paying": "自費研修", "closed": "已截止",
    "reference_only": "歷史／參考資料", "quota_unconfirmed": "本期名額待確認",
}
EVIDENCE = {
    "verified_current": "已核對適用年度", "reference_only": "僅供參考", "missing": "缺少資料",
    "needs_confirmation": "待確認", "conflict": "來源有衝突", "explicit_not_announced": "官方明示尚未公告",
}
FIELDS = (
    ("academic_year", "適用學年度"), ("application_round", "申請梯次"),
    ("colleges", "可申請學院"), ("degree_levels", "可申請學制"), ("study_period", "研修期間"),
    ("quota", "名額（請連同名額狀態閱讀）"), ("eligibility", "申請資格"),
    ("language_requirement", "語言條件"), ("language_review_note", "語言條件查核說明"),
    ("application_deadline", "來源列載申請期限"), ("nomination_deadline", "提名期限"),
    ("partner_application_deadline", "合作校申請期限"), ("partner_application_prerequisite", "合作校申請前提"),
    ("application_info", "申請說明"), ("tuition_info", "學費資訊"),
    ("semester_dates", "學期日期"), ("housing_info", "住宿資訊"), ("course_restrictions", "課程限制"),
)


@dataclass(frozen=True)
class SeoSettings:
    origin: str
    indexable: bool
    verification: str = ""

    @classmethod
    def from_environment(cls, env: Mapping[str, str] | None = None) -> "SeoSettings":
        env = os.environ if env is None else env
        origin = env.get("EXCHANGE_PUBLIC_BASE_URL", "").strip().rstrip("/") or DEFAULT_ORIGIN
        parsed = urlsplit(origin)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.path or parsed.query or parsed.fragment or any(c.isspace() for c in origin)):
            raise ValueError("SEO requires EXCHANGE_PUBLIC_BASE_URL to be an HTTPS origin without a path")
        # Development and staging must opt in deliberately. Never trust Host or forwarded headers.
        enabled = env.get("EXCHANGE_SEO_INDEXABLE", "").strip().lower()
        indexable = enabled in {"1", "true", "yes", "on"} if enabled else env.get("EXCHANGE_ENVIRONMENT") == "production"
        return cls(origin, indexable, env.get("EXCHANGE_GOOGLE_SITE_VERIFICATION", "").strip())


def structured_data(value: dict) -> str:
    payload = json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f'<script type="application/ld+json">{payload}</script>'


def metadata(settings: SeoSettings, title: str, description: str, path: str, article: Article | None = None) -> str:
    url, image = settings.origin + path, settings.origin + "/static/assets/brand/apple-touch-icon.png"
    if article:
        image = settings.origin + article.image_path
    tags = [f'<meta name="description" content="{escape(description)}">',
            f'<link rel="canonical" href="{escape(url)}">',
            f'<meta name="robots" content="{"index, follow, max-image-preview:large" if settings.indexable else "noindex, nofollow"}">']
    for prop, value in (("og:type", "article" if article else "website"), ("og:site_name", "UniWay"), ("og:locale", "zh_TW"),
                        ("og:title", title), ("og:description", description), ("og:url", url),
                        ("og:image", image), ("og:image:alt", article.image_alt if article else "UniWay 標誌")):
        tags.append(f'<meta property="{prop}" content="{escape(value)}">')
    for name, value in (("twitter:card", "summary_large_image" if article else "summary"), ("twitter:title", title),
                        ("twitter:description", description), ("twitter:image", image)):
        tags.append(f'<meta name="{name}" content="{escape(value)}">')
    if article:
        for prop, value in (("article:published_time", article.published.isoformat()),
                            ("article:modified_time", article.modified.isoformat()),
                            ("og:image:width", "1536"), ("og:image:height", "1024")):
            tags.append(f'<meta property="{prop}" content="{value}">')
    if path == "/" and settings.verification:
        tags.append(f'<meta name="google-site-verification" content="{escape(settings.verification)}">')
    return "\n".join(tags) + analytics_markup()


def homepage_html(template: str, settings: SeoSettings) -> str:
    graph = {"@context": "https://schema.org", "@type": "WebSite", "name": "UniWay",
             "url": settings.origin + "/", "description": HOME_DESCRIPTION, "inLanguage": "zh-Hant"}
    return template.replace("<!-- seo-head -->", metadata(settings, HOME_TITLE, HOME_DESCRIPTION, "/") + structured_data(graph))


def partner_id(partner: PartnerUniversity) -> str:
    # Country and institution identity keep campuses distinct; rows for multiple programmes share one page.
    identity = f"{partner.country or ''}|{school_identity_key(partner.school_name)}"
    return hashlib.sha256(identity.encode()).hexdigest()[:20]


def partner_path(university: UniversityProfile, partner: PartnerUniversity) -> str:
    return f"/schools/{university.id}/partners/{partner_id(partner)}"


def group_partners(partners: Sequence[PartnerUniversity]) -> dict[str, list[PartnerUniversity]]:
    result: dict[str, list[PartnerUniversity]] = {}
    for partner in partners:
        result.setdefault(partner_id(partner), []).append(partner)
    return result


def source_link(url: str | None, label: str) -> str:
    try:
        parsed = urlsplit(url or "")
        safe = parsed.scheme in {"https", "http"} and parsed.hostname and not parsed.username and not parsed.password
    except ValueError:
        safe = False
    return f'<a href="{escape(url or "")}" rel="noopener noreferrer" data-official-source>{escape(label)}</a>' if safe else escape(label + "（連結待確認）")


def application_link(university: UniversityProfile, partner: PartnerUniversity | None = None) -> str:
    fragment = "school=" + quote(partner.school_name, safe="") if partner else "partners"
    return "/?" + urlencode({"home": university.school_name}) + "#" + fragment


def display_time(value: datetime) -> str:
    return value.astimezone(ZoneInfo("Asia/Taipei")).strftime("%Y/%m/%d %H:%M（臺灣時間）")


def source_notice(source: CatalogueSourceStatus | None) -> str:
    if source is None:
        return ""
    checked = display_time(source.last_success_at) if source.last_success_at else "尚無成功擷取紀錄"
    return f'<aside class="notice">合作校資料擷取時間：{escape(checked)}。這是來源擷取時間，不代表本期名額或資格已完成查核。</aside>'


def page(settings: SeoSettings, title: str, description: str, path: str, body: str,
         breadcrumbs: list[tuple[str, str]], *, article: Article | None = None, extra_head: str = "") -> HTMLResponse:
    navigation = '<ol>' + ''.join(
        f'<li><span aria-current="page">{escape(name)}</span></li>' if i == len(breadcrumbs) - 1
        else f'<li><a href="{escape(p)}">{escape(name)}</a></li>'
        for i, (name, p) in enumerate(breadcrumbs)) + '</ol>'
    nav_links = ''.join(
        f'<a href="{p}"' + (' aria-current="page"' if path == p or path.startswith(p + '/') else '')
        + f'>{label}</a>'
        for p, label in (("/guides", "交換指南"), ("/schools", "學校總覽"),
                         ("/destinations", "國家專區"), ("/partners", "跨校大學")))
    schema = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": name, "item": settings.origin + p}
        for i, (name, p) in enumerate(breadcrumbs, 1)]}
    article_head = structured_data(article_schema(article, settings.origin)) if article else ""
    if path == "/guides" or article:
        article_head += '<link rel="stylesheet" href="/static/seo-articles.css?v=20261020-1">'
    if extra_head:
        article_head += extra_head
    select_assets = (
        '<link rel="stylesheet" href="/static/glide-select.css?v=20261029-level-tools-3">'
        '<script src="/static/application-path-select.js?v=20261029-level-tools-3" defer></script>'
        if '<select' in body else ''
    )
    html = f'''<!doctype html><html lang="zh-Hant" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)}</title>
{metadata(settings, title, description, path, article)}{structured_data(schema)}
<link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="/static/brand-tokens.css?v=20261029-midnight-1">
<link rel="stylesheet" href="/static/typography.css?v=20260929-fonts-2">
<link rel="stylesheet" href="/static/seo.css?v=20261020-1">{article_head}
<link rel="stylesheet" href="/static/midnight-theme.css?v=20261029-1">
{select_assets}
<script src="/static/reading-theme.js?v=20261020-1"></script></head>
<body class="reading-shell"><a class="skip" href="#content">跳到內容</a><header class="reading-header">
<a class="brand" href="/#home" aria-label="UniWay 首頁"><img src="/static/assets/brand/uniway-mark.webp?v=20261004-logo-2" alt="" width="40" height="40"><strong>UniWay</strong></a>
<nav aria-label="主導覽">{nav_links}</nav><div class="reading-actions"><button class="reading-theme-toggle" type="button" hidden aria-label="切換為深色模式">深色</button><a class="reading-planner" href="/#partners">開啟選校工具 <span aria-hidden="true">↗</span></a></div></header>
<main id="content"><nav class="breadcrumbs" aria-label="麵包屑">{navigation}</nav>{body}
<aside class="notice">{NOTICE}</aside></main><footer class="reading-footer"><a href="/#home">返回 UniWay 首頁</a>
<a href="/guides">交換指南</a><a href="/schools">學校指南</a><a href="/partners">跨校外國大學</a><a href="/editorial-policy">資料編輯政策</a><a href="/privacy">隱私權政策</a><a href="/terms">使用條款</a></footer></body></html>'''
    return HTMLResponse(html, headers={"Cache-Control": "public, max-age=60"})


def readable_text(value: str) -> str:
    # Preserve wording and punctuation; separate existing list/sentence boundaries, not inferred facts.
    parts = [p.strip() for p in re.split(r"\n+|(?<=；)|(?<=。)|\s+(?=\d+[.、]\s)", str(value)) if p.strip()]
    return "".join(f'<p>{escape(part)}</p>' for part in parts)


def definition_list(rows) -> str:
    return '<dl>' + "".join(f'<dt>{escape(label)}</dt><dd>{readable_text(str(value))}</dd>'
                          for label, value in rows if value) + '</dl>'


def short_text(value: str | None, limit: int = 100) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def quota_rows(partner: PartnerUniversity) -> list[tuple[str, str | None]]:
    status = {"published": "來源已列載，仍需確認適用年度", "zero": "零名額", "not_published": "未列載／待確認",
              "reference_only": "參考名額", "fee_paying": "自費"}.get(partner.quota_status, "待確認")
    rows = [("來源適用學年度", partner.academic_year or "來源未明確標示，待確認"),
            ("來源申請梯次", partner.application_round or "來源未明確標示，待確認"), ("當期名額確認狀態", status)]
    # Separate only explicit source syntax; do not infer which year the leading number belongs to.
    mixed = re.fullmatch(r"(\d+)\s+(\d{4}\s*[^。；]*暫估[^。；]*)", partner.quota or "")
    if mixed:
        rows += [("來源列載數字（年度與口徑待確認）", mixed[1]),
                 ("來源中的目標梯次暫估（非核定）", mixed[2]),
                 ("名額閱讀提醒", "上述數字的適用範圍尚未釐清，不可相加或視為目前可申請名額；請向母校確認。")]
    else:
        rows.append(("來源列載名額（請連同狀態閱讀）", partner.quota or "未列載／待確認"))
    return rows


FIELD_SECTIONS = (
    ("申請資格與語言", ("colleges", "degree_levels", "eligibility", "language_requirement", "language_review_note", "partner_application_prerequisite")),
    ("研修期間與申請期限", ("study_period", "application_deadline", "nomination_deadline", "partner_application_deadline", "semester_dates")),
    ("學費與住宿", ("tuition_info", "housing_info")),
    ("申請步驟、文件與課程限制", ("application_info", "course_restrictions")),
)
DETAIL_LABELS = {"application_documents": "申請文件", "required_documents": "申請文件", "application_process": "申請程序",
                 "living_costs": "生活費", "living_cost": "生活費", "visa": "簽證", "visa_residence": "簽證與居留",
                 "insurance": "保險", "housing": "住宿", "tuition_fees": "學費與費用", "courses": "課程", "academic_calendar": "學期日期"}


def partner_details(partner: PartnerUniversity, section_id: str = "programme") -> str:
    rows = [("資料狀態", AVAILABILITY[partner.availability_status]), ("狀態說明", partner.availability_note),
            ("母校受理時窗", {"open": "受理中（依來源時窗）", "upcoming": "尚未開始受理", "closed": "已截止"}.get(partner.application_window_status, "待確認"))]
    if partner.checked_at:
        rows.append(("資料查核時間", display_time(partner.checked_at)))
    labels = dict(FIELDS)
    details = definition_list(rows) + '<h3>名額與適用年度</h3>' + definition_list(quota_rows(partner))
    for heading, fields in FIELD_SECTIONS:
        values = [(labels[key], getattr(partner, key)) for key in fields if getattr(partner, key, None)]
        if values:
            details += f'<section><h3>{heading}</h3>{definition_list(values)}</section>'
    evidence = "".join(
        f'<li><strong>{escape(labels.get(key, "補充條件"))}</strong>：{EVIDENCE[item.status]}；{escape(item.note or "")} '
        f'{source_link(item.source_url, "查閱來源")} '
        f'{escape(item.academic_year or "")} {escape(item.application_round or "")} '
        f'（查核：{escape(display_time(item.checked_at))}）</li>'
        for key, item in partner.field_evidence.items())
    references = "".join(f'<dt>{escape(key)}</dt><dd>{escape(value)}</dd>' for key, value in partner.reference_data.items())
    options, seen = "", set()
    for option in partner.program_options:
        signature = digest(option.model_dump(mode="json"))
        if signature in seen:
            continue
        seen.add(signature)
        values = [(label, getattr(option, key)) for key, label in FIELDS
                  if getattr(option, key, None) and getattr(option, key) != getattr(partner, key, None)]
        if values or option.program_type != partner.program_type or option.source_url != partner.source_url:
            options += '<h3>' + escape(option.program_type) + '：方案差異</h3>'
            options += definition_list(values) if values else '<p>列載條件與上方相同，請另核對此方案來源。</p>'
            options += source_link(option.source_url, "此方案來源")
    additional = ""
    for key, detail in partner.partner_exchange_details.items():
        if not detail.value:
            continue
        references_html = " · ".join(source_link(ev.source_url, "官方依據") + ' ' + escape('／'.join(filter(None, [ev.academic_year, ev.application_round]))) for ev in detail.evidence)
        additional += f'<section><h3>{escape(DETAIL_LABELS.get(key, key.replace("_", " ")))}</h3><p class="status">{EVIDENCE[detail.status]} · {escape(detail.reason)}</p>{readable_text(detail.value)}<p>{references_html}</p></section>'
    return f'''<section class="programme" id="{section_id}"><h2>{escape(partner.program_type)}</h2>{details}
<p>{source_link(partner.source_url, "母校合作校／名額資料來源")} · {source_link(partner.website, "合作校官方網站")}</p>
{('<details><summary>欄位查核狀態與來源</summary><ul>' + evidence + '</ul></details>') if evidence else ''}
{('<h3>歷史／參考資料（非本期已確認條件）</h3><dl>' + references + '</dl>') if references else ''}{options}{additional}</section>'''


def xml_response(root_name: str, entries: Sequence[str], lastmods: Mapping[str, str] | None = None) -> Response:
    root = Element(root_name, xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for location in entries:
        item = SubElement(root, "sitemap" if root_name == "sitemapindex" else "url")
        SubElement(item, "loc").text = location
        if lastmods and location in lastmods:
            SubElement(item, "lastmod").text = lastmods[location]
    return Response(tostring(root, encoding="utf-8", xml_declaration=True), media_type="application/xml",
                    headers={"Cache-Control": "public, max-age=300"})


def create_seo_router(settings: SeoSettings, catalogue: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
                      changes: ContentChanges | None = None) -> APIRouter:
    router = APIRouter(include_in_schema=False)
    universities = {item.id: item for item in SUPPORTED_UNIVERSITIES}
    snapshots: dict[str, tuple[float, list[PartnerUniversity], CatalogueSourceStatus | None, dict[str, list[PartnerUniversity]]]] = {}
    snapshot_locks = {home_id: threading.Lock() for home_id in universities}
    lastmods: dict[str, str] = {}

    def record_changes(hashes: dict[str, str]) -> dict[str, str]:
        if changes is None:
            return {}
        try:
            return changes.observe(hashes)
        except (OSError, sqlite3.Error):
            # A ledger failure must not break public pages or manufacture dates.
            logging.getLogger(__name__).warning("SEO content ledger unavailable; omitting lastmod", exc_info=True)
            return {}

    def catalogue_for(u: UniversityProfile):
        # A crawler visiting hundreds of partner pages must not parse the same
        # source files hundreds of times. Bounded by the supported registry;
        # refresh at most once per minute, including time-sensitive window state.
        with snapshot_locks[u.id]:
            cached = snapshots.get(u.id)
            if cached and monotonic() - cached[0] < 60:
                return cached[1], cached[2], cached[3]
            partners, source = catalogue(u)
            if not partners:
                raise HTTPException(503, "合作校資料暫不可用，請稍後重試。", headers={"Retry-After": "60"})
            groups = group_partners(partners)
            hashes = {settings.origin + partner_path(u, rows[0]): digest({"layout": 2, "content": material_content(rows)})
                      for rows in groups.values()}
            for url in hashes:
                lastmods.pop(url, None)
            lastmods.update(record_changes(hashes))
            snapshots[u.id] = monotonic(), partners, source, groups
            return partners, source, groups

    def cached_pair_loader(u: UniversityProfile) -> tuple[list[PartnerUniversity], CatalogueSourceStatus | None]:
        partners, source, _ = catalogue_for(u)
        return partners, source

    def university(home_id: str) -> UniversityProfile:
        if home_id not in universities:
            raise HTTPException(404, "找不到這所母校")
        return universities[home_id]

    @router.api_route("/robots.txt", methods=["GET", "HEAD"])
    def robots():
        rules = "User-agent: *\n"
        if settings.indexable:
            rules += "Disallow: /account/\nDisallow: /auth/\nDisallow: /admin/\nDisallow: /calendar/\n"
            rules += f"Sitemap: {settings.origin}/sitemap.xml\n"
        else:
            rules += "Disallow: /\n"
        return PlainTextResponse(rules, headers={"Cache-Control": "public, max-age=300"})

    @router.api_route("/partners", methods=["GET", "HEAD"])
    def partners_directory():
        directory_data = build_cross_school_partner_directory(catalogue_loader=cached_pair_loader, limit=120, require_complete=True)
        body = render_cross_school_partner_directory_body(directory_data)
        return page(
            settings,
            f"跨校外國合作大學總覽｜整合全台 {len(universities)} 所大學門檻與經驗摘要｜UniWay",
            "以國家與外國機構 ID 整合全台各大學海外交換名額、語檢門檻、校內截止日、生活費、住宿與修課方向結構化摘要。",
            "/partners",
            body,
            [("首頁", "/"), ("跨校外國大學", "/partners")],
        )

    @router.api_route("/partners/{country}", methods=["GET", "HEAD"])
    def partners_by_country(country: str):
        c_slug, _c_zh = resolve_country_slug_and_zh(country)
        directory_data = build_cross_school_partner_directory(
            catalogue_loader=cached_pair_loader,
            country=c_slug,
            limit=200,
            require_complete=True,
        )
        if directory_data.total_partner_count == 0:
            raise HTTPException(404, "找不到這個國家的跨校合作大學")
        c_name = directory_data.selected_country_name_zh or country
        canonical_country_path = f"/partners/{directory_data.selected_country_slug or c_slug}"
        body = render_cross_school_partner_directory_body(directory_data)
        return page(
            settings,
            f"{c_name}交換大學跨校門檻與經驗總覽｜UniWay",
            f"聚合全台各大學赴{c_name}交換之合作大學清單、語檢門檻、名額與跨校生活費、住宿、課程方向結構化整理。",
            canonical_country_path,
            body,
            [("首頁", "/"), ("跨校外國大學", "/partners"), (c_name, canonical_country_path)],
        )

    @router.api_route("/partners/{country}/{institution}", methods=["GET", "HEAD"])
    def cross_school_partner_page(
        country: str,
        institution: str,
        home: str | None = Query(default=None),
    ):
        data = build_cross_school_partner_page_data(
            country=country,
            institution=institution,
            selected_home=home,
            catalogue_loader=cached_pair_loader,
            require_complete=True,
        )
        if data is None:
            raise HTTPException(404, "找不到這所外國合作大學")
        if re.fullmatch(r"inst-[0-9a-f]{12}", institution) and f"/partners/{country}/{institution}" != data.canonical_path:
            # Keep the selected home school when a proven legacy ID moves.
            query = "?" + urlencode({"home": home}) if home else ""
            return RedirectResponse(data.canonical_path + query, status_code=301)
        title = (
            f"{data.display_title} 交換門檻、名額與跨校生活費指南｜"
            f"全台 {data.contracted_home_count} 校整合｜UniWay"
        )
        description = (
            f"查詢赴{data.country_name_zh}{data.display_title}交換之各母校當期名額、語檢門檻與校內截止日，"
            f"並瀏覽全台 {data.contracted_home_count} 所締約大學聚合之生活費參考、住宿提醒與修課方向結構化摘要。"
        )
        body = render_cross_school_partner_page_body(data)
        extra_script = '<script src="/static/partner-page.js?v=20261020-1" defer></script>'
        return page(
            settings,
            title,
            description,
            data.canonical_path,
            body,
            [
                ("首頁", "/"),
                ("跨校外國大學", "/partners"),
                (data.country_name_zh, f"/partners/{data.country_slug}"),
                (data.school_name_zh, data.canonical_path),
            ],
            extra_head=extra_script,
        )

    @router.api_route("/schools", methods=["GET", "HEAD"])
    def directory():
        cards = "".join(f'<li><a href="/schools/{u.id}"><strong>{escape(u.school_name)}</strong>'
                        f'<span>{escape(u.english_name)}</span></a><p>{escape(u.coverage_note)}</p></li>' for u in universities.values())
        body = f'<p class="eyebrow">交換學生・從母校開始</p><h1>全台大學交換學生申請指南｜{len(universities)} 所母校合作學校總覽</h1>'
        body += f'<p class="lead">依就讀大學查看海外合作校、名額狀態與申請條件。目前整理 {len(universities)} 所母校的公開資訊。</p><ul class="cards">{cards}</ul>'
        body += '<p><a href="/partners">依外國大學跨校比較門檻與經驗</a> · <a href="/destinations">依國家比較交換選項</a> · <a href="/guides">從資格、文件與預算開始準備</a></p>'
        return page(settings, f"全台大學交換學生申請指南｜{len(universities)} 所母校｜UniWay", HOME_DESCRIPTION, "/schools", body,
                    [("首頁", "/"), ("交換學校指南", "/schools")])

    @router.api_route("/schools/{home_id}", methods=["GET", "HEAD"])
    def home_school(home_id: str):
        u = university(home_id)
        partners, source, groups = catalogue_for(u)
        cards = "".join(f'<li><a href="{partner_path(u, rows[0])}"><strong>{escape(rows[0].school_name)}</strong>'
                        f'<span>{escape(rows[0].country or "國家待確認")}</span></a><p>{escape("、".join(dict.fromkeys(AVAILABILITY[p.availability_status] for p in rows)))}</p></li>'
                        for rows in groups.values())
        title = f"{u.school_name}交換學生申請與合作學校｜UniWay"
        description = f"查詢{u.school_name}海外交換合作校、申請資格、名額與來源。依各方案顯示本期、參考或待確認狀態，申請以校方最新公告為準。"
        body = f'<p class="eyebrow">{escape(u.english_name)}</p><h1>{escape(u.school_name)}交換學生申請與合作學校</h1><p class="lead">{escape(u.coverage_note)}</p>'
        body += f'<p>{source_link(u.official_url, "母校國際處官方資訊")}</p><a class="button" href="{escape(application_link(u))}">開啟{escape(u.short_name)}選校與申請工具</a>'
        body += source_notice(source) + f'<h2>合作校與方案資料</h2><p>共 {len(groups)} 個合作校頁面、{len(partners)} 筆方案資料；此數量不是本期可申請名額。</p><ul class="cards">{cards}</ul>'
        body += '<p><a href="/guides/exchange-eligibility">如何核對交換資格與語言門檻</a> · <a href="/destinations">比較目的地與生活預算</a></p>'
        return page(settings, title, description, f"/schools/{u.id}", body,
                    [("首頁", "/"), ("交換學校指南", "/schools"), (u.school_name, f"/schools/{u.id}")])

    @router.api_route("/schools/{home_id}/partners/{key}", methods=["GET", "HEAD"])
    def partner_school(home_id: str, key: str):
        u = university(home_id)
        partners, source, groups = catalogue_for(u)
        rows = groups.get(key)
        if not rows:
            raise HTTPException(404, "找不到這所合作校")
        partner = rows[0]
        rows = list({digest(material_content([row])): row for row in rows}.values())
        statuses = "、".join(dict.fromkeys(AVAILABILITY[row.availability_status] for row in rows))
        title = f"{partner.school_name}交換申請條件與名額｜{u.school_name}｜UniWay"
        description = f"{u.school_name}赴{partner.country or '海外'}{partner.school_name}的交換與研修資訊，{len(rows)} 筆方案。{statuses}。查看學制、語言、期限與官方來源，以校方公告為準。"
        c_slug, _ = resolve_country_slug_and_zh(partner.country)
        cross_school_url = f"/partners/{c_slug}/{key}?home={u.id}"
        body = f'<p class="eyebrow">{escape(u.school_name)} → {escape(partner.country or "海外合作校")}</p><h1>{escape(partner.school_name)}交換與研修資訊</h1>'
        body += f'<p class="lead">此頁適用母校：{escape(u.school_name)}。不同母校或方案的規定可能不同，請逐項確認。</p>'
        body += f'<a class="button" href="{escape(application_link(u, partner))}">在 UniWay 查看學校與規劃申請</a> · <a class="button secondary" href="{escape(cross_school_url)}">查看跨校外國大學頁（全台締約校與經驗摘要）</a>' + source_notice(source)
        body += '<nav class="jump-links" aria-label="本頁方案">' + ' · '.join(f'<a href="#programme-{i}">{escape(row.program_type)}</a>' for i, row in enumerate(rows, 1)) + '</nav>'
        body += '<section class="overview"><h2>申請前快速核對</h2>' + definition_list([
            ("母校與目的地", f"{u.school_name} → {partner.country or '國家待確認'}"),
            ("可申請學制（各方案可能不同）", "；".join(dict.fromkeys(row.degree_levels for row in rows if row.degree_levels)) or "未列載，請查閱官方來源"),
            ("方案資料狀態", statuses),
            ("核對順序", "先確認母校當期甄選，再核對合作校方案；提名、錄取與名額確認是不同步驟。")]) + '</section>'
        body += "".join(partner_details(row, f"programme-{i}") for i, row in enumerate(rows, 1))
        slug = country_slug(partner.country)
        body += '<section><h2>延伸比較與申請準備</h2><ul>'
        body += f'<li><a href="{escape(cross_school_url)}">跨校比較：{escape(partner.school_name)}全台締約大學門檻、生活費與修課方向</a></li>'
        if slug:
            body += f'<li><a href="/destinations/{slug}">{COUNTRIES[slug]["name"]}交換選項與生活預算核對</a></li>'
        for guide in ("exchange-eligibility", "exchange-application", "exchange-budget"):
            data = GUIDES[guide]
            body += f'<li><a href="/guides/{guide}">{data["title"]}</a></li>'
        related = [group[0] for group in groups.values()
                   if group[0].country == partner.country and partner_id(group[0]) != key][:6]
        body += '</ul>'
        if related:
            body += f'<h3>{escape(u.short_name)}其他同國家合作校</h3><ul>' + "".join(
                f'<li><a href="{partner_path(u, item)}">{escape(item.school_name)}的{escape(u.short_name)}適用方案</a></li>' for item in related) + '</ul>'
        body += '</section>'
        path = partner_path(u, partner)
        return page(settings, title, description, path, body,
                    [("首頁", "/"), ("交換學校指南", "/schools"), (u.school_name, f"/schools/{u.id}"), (partner.school_name, path)])

    @router.api_route("/destinations", methods=["GET", "HEAD"])
    def destinations():
        body = '<h1>交換學生國家專區</h1><p class="lead">先比較目的地的語言、學期與預算，再回到母校確認適用的交換方案。</p><ul class="cards">'
        for slug, data in COUNTRIES.items():
            body += f'<li><a href="/destinations/{slug}"><strong>{data["name"]}交換學生指南</strong></a><p>{data["intro"]}</p></li>'
        body += '</ul><p><a href="/schools">查看全部母校及其他國家的合作校</a></p>'
        return page(settings, "日本、韓國、德國交換學生指南｜UniWay", "比較國家、母校方案與交換生活預算，確認語言、學期、費用及官方來源。", "/destinations", body, [("首頁", "/"), ("國家專區", "/destinations")])

    @router.api_route("/destinations/{slug}", methods=["GET", "HEAD"])
    def destination(slug: str):
        if slug not in COUNTRIES:
            raise HTTPException(404, "找不到國家指南")
        data = COUNTRIES[slug]
        matches = []
        # If any source is unavailable, return a retryable error rather than a misleading complete count.
        for u in universities.values():
            _, _, catalogue_groups = catalogue_for(u)
            groups = [rows for rows in catalogue_groups.values() if country_slug(rows[0].country) == slug]
            if groups:
                matches.append((u, groups))
        count = sum(len(groups) for _, groups in matches)
        name = data["name"]
        body = f'<h1>{name}交換學生：母校選項、申請條件與生活費規劃</h1><p class="lead">{data["intro"]}</p>'
        body += f'<p>目前資料涵蓋 {len(matches)} 所母校、{count} 個母校與合作校頁面；同一海外學校可能重複出現在不同母校，這不是當期名額或錄取數。</p>'
        for heading, text in data["checks"]:
            body += f'<section><h2>{heading}</h2><p>{text}</p></section>'
        body += '<h2>官方規劃參考</h2><ul>' + ''.join(f'<li>{source_link(url, label)}</li>' for label, url in data["sources"]) + '</ul>'
        body += '<p><a href="/guides/exchange-budget">建立費用與補助清單</a> · <a href="/guides/exchange-eligibility">核對語言及資格</a></p>'
        cost_guide = {"japan": "japan-exchange-cost", "south-korea": "korea-exchange-cost", "germany": "germany-exchange-cost"}[slug]
        body += f'<p><a href="/guides/{cost_guide}">閱讀{name}一學期生活費、住宿與預算完整指南</a></p><h2>依母校比較方案</h2>'
        body += '<nav class="jump-links" aria-label="母校快速連結">' + ' · '.join(f'<a href="#home-{u.id}">{escape(u.short_name)}</a>' for u, _ in matches) + '</nav>'
        for u, groups in matches:
            body += f'<section id="home-{u.id}"><h3><a href="/schools/{u.id}">{escape(u.school_name)}</a> · {len(groups)} 個合作校頁面</h3><ul class="cards">'
            for rows in groups:
                row = rows[0]
                status = "、".join(dict.fromkeys(AVAILABILITY[item.availability_status] for item in rows))
                degrees = "；".join(dict.fromkeys(item.degree_levels for item in rows if item.degree_levels)) or "學制待確認"
                body += f'<li><a href="{partner_path(u, row)}"><strong>{escape(row.school_name)}</strong><span>{escape(u.short_name)}適用方案</span></a><p>{escape(degrees)} · {escape(status)}</p><p>共 {len(rows)} 筆方案；資格、語言與費用請逐項查看。</p></li>'
            body += '</ul></section>'
        return page(settings, f"{name}交換學生申請與生活費指南｜依母校比較｜UniWay", f"整理{name}交換學生的母校合作選項、語言與課程核對、住宿生活費規劃及官方來源。各校方案與名額須依當期公告確認。", f"/destinations/{slug}", body, [("首頁", "/"), ("國家專區", "/destinations"), (name, f"/destinations/{slug}")])

    @router.api_route("/guides", methods=["GET", "HEAD"])
    def guides():
        body = guide_index()
        return page(settings, "交換學生資格、費用與文件指南｜UniWay", "依序準備交換學生資格、語言、預算、補助與文件，連結各母校的官方申請資訊。", "/guides", body, [("首頁", "/"), ("申請指南", "/guides")])

    @router.api_route("/guides/{slug}", methods=["GET", "HEAD"])
    def guide(slug: str):
        if slug not in GUIDES:
            raise HTTPException(404, "找不到申請指南")
        article = ARTICLES[slug]
        return page(settings, article.title + "｜UniWay", article.description, f"/guides/{slug}", render_article(article),
                    [("首頁", "/"), ("申請指南", "/guides"), (article.title, f"/guides/{slug}")], article=article)

    @router.api_route("/editorial-policy", methods=["GET", "HEAD"])
    def editorial_policy():
        body = '''<h1>UniWay 資料編輯與更正政策</h1><p class="lead">協助學生找到可核對的交換資訊，並清楚區分已確認條件、參考資料與未知事項。</p>
<h2>來源與適用範圍</h2><p>母校甄選、名額與提名規定以母校國際處公告為準；合作校課程、住宿及入學程序以合作校官方資料為準；簽證以主管機關為準。每個合作校頁保留來源連結，查核欄位另列適用年度、梯次與狀態。</p>
<h2>查核、更新與不確定性</h2><p>資料擷取時間與人工查核時間不同，近期抓取不代表名額仍開放。未知、歷史參考、來源衝突與零名額分開標示；不以合作關係推論當期名額，也不把未公告寫成免要求。</p>
<h2>整理方法</h2><p>網站將既有資料整理為母校與合作校方案頁，合併同一方案的重複文字，保留各方案差異與來源。國家及申請指南提供一般比較方法，不取代校方個案判定；未查證的推論不寫成官方規定。</p>
<h2>文章與照片</h2><p>申請指南區分官方統計、UniWay 整理方法與假設試算，標明來源版本與適用範圍。文章以 AI 輔助起草，配圖採用具使用授權的真實照片，並在圖說列出攝影者與來源。照片用於呈現學習與目的地生活情境，不代表文中申請人、合作校背書或保證提供的住宿房型。文字與來源會在內容修訂時重新核對，更新日期反映實質修改，不因每日排程而刷新。</p>
<h2>更正與學生經驗</h2><p>發現錯誤時，可透過網站的問題回報功能提供頁面網址、官方來源與適用年度，供平台核對。學生心得應標明交換時間與方案並取得作者授權；個人經驗不代表所有學生的費用、資格或錄取結果。</p>
<h2>平台角色</h2><p>UniWay 是獨立資訊整理與申請規劃工具，並非大學或政府單位，不保證名額、錄取或補助。學校與來源連結不代表合作背書。</p>
<p><a href="/schools">查閱母校與合作校資料</a> · <a href="/guides">閱讀申請準備指南</a></p>'''
        return page(settings, "資料來源、編輯與更正政策｜UniWay", "了解 UniWay 如何整理官方交換資料、區分年度與查核狀態，以及處理更正和學生經驗。", "/editorial-policy", body, [("首頁", "/"), ("資料編輯政策", "/editorial-policy")])

    @router.api_route("/sitemap.xml", methods=["GET", "HEAD"])
    def sitemap_index():
        return xml_response("sitemapindex", [settings.origin + "/sitemaps/pages.xml", settings.origin + "/sitemaps/partners.xml"] +
                            [f"{settings.origin}/sitemaps/{u.id}.xml" for u in universities.values()])

    @router.api_route("/sitemaps/pages.xml", methods=["GET", "HEAD"])
    def static_sitemap():
        return xml_response("urlset", [settings.origin + path for path in ("/", "/schools", *EDITORIAL_PATHS)] +
                            [f"{settings.origin}/schools/{u.id}" for u in universities.values()],
                            {f"{settings.origin}/guides/{slug}": article.modified.isoformat() for slug, article in ARTICLES.items()})

    @router.api_route("/sitemaps/partners.xml", methods=["GET", "HEAD"])
    def partners_sitemap():
        directory_data = build_cross_school_partner_directory(catalogue_loader=cached_pair_loader, limit=5000, require_complete=True)
        return xml_response("urlset", [settings.origin + item.canonical_path for item in directory_data.items])

    @router.api_route("/sitemaps/{home_id}.xml", methods=["GET", "HEAD"])
    def school_sitemap(home_id: str):
        u = university(home_id)
        _, _, groups = catalogue_for(u)
        return xml_response("urlset", [settings.origin + partner_path(u, rows[0]) for rows in groups.values()], lastmods)

    return router

