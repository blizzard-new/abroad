"""Public, server-rendered catalogue pages; never reads a visitor's workspace."""
from __future__ import annotations

import hashlib
import json
import logging
import os
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

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from .models import CatalogueSourceStatus, PartnerUniversity
from .school_identity import school_identity_key
from .seo_changes import ContentChanges
from .seo_quality import digest, material_content
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile

DEFAULT_ORIGIN = "https://app.uniway-tw.com"
HOME_TITLE = "UniWay｜交換學生申請、合作學校與選校資訊"
HOME_DESCRIPTION = "UniWay 整理臺灣大學交換學生申請與海外合作校資訊，協助比較學校、查詢資格與名額、準備申請文件及規劃時程。公開資料免登入，申請規定以各校最新官方公告為準。"
NOTICE = "UniWay 是獨立資訊整理平台，並非校方。合作關係不等於當期開放申請；資格、名額、期限與文件請以母校國際處及合作校最新公告為準。"
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


def metadata(settings: SeoSettings, title: str, description: str, path: str) -> str:
    url, image = settings.origin + path, settings.origin + "/static/assets/brand/apple-touch-icon.png"
    tags = [f'<meta name="description" content="{escape(description)}">',
            f'<link rel="canonical" href="{escape(url)}">',
            f'<meta name="robots" content="{"index, follow, max-image-preview:large" if settings.indexable else "noindex, nofollow"}">']
    for prop, value in (("og:type", "website"), ("og:site_name", "UniWay"), ("og:locale", "zh_TW"),
                        ("og:title", title), ("og:description", description), ("og:url", url),
                        ("og:image", image), ("og:image:alt", "UniWay 標誌")):
        tags.append(f'<meta property="{prop}" content="{escape(value)}">')
    for name, value in (("twitter:card", "summary"), ("twitter:title", title),
                        ("twitter:description", description), ("twitter:image", image)):
        tags.append(f'<meta name="{name}" content="{escape(value)}">')
    if path == "/" and settings.verification:
        tags.append(f'<meta name="google-site-verification" content="{escape(settings.verification)}">')
    return "\n".join(tags)


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
    return f'<a href="{escape(url or "")}" rel="noopener noreferrer">{escape(label)}</a>' if safe else escape(label + "（連結待確認）")


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
         breadcrumbs: list[tuple[str, str]]) -> HTMLResponse:
    navigation = " / ".join(f'<a href="{escape(p)}">{escape(name)}</a>' for name, p in breadcrumbs)
    schema = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": name, "item": settings.origin + p}
        for i, (name, p) in enumerate(breadcrumbs, 1)]}
    html = f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)}</title>
{metadata(settings, title, description, path)}{structured_data(schema)}
<link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="/static/seo.css?v=20261019-1"></head>
<body><a class="skip" href="#content">跳到內容</a><header><a class="brand" href="/">UniWay</a>
<nav aria-label="主導覽"><a href="/schools">交換學校指南</a><a href="/#partners">開啟選校工具</a></nav></header>
<main id="content"><nav class="breadcrumbs" aria-label="麵包屑">{navigation}</nav>{body}
<aside class="notice">{NOTICE}</aside></main><footer><a href="/">UniWay 首頁</a>
<a href="/schools">學校指南</a><a href="/privacy">隱私權政策</a><a href="/terms">使用條款</a></footer></body></html>'''
    return HTMLResponse(html, headers={"Cache-Control": "public, max-age=60"})


def partner_details(partner: PartnerUniversity) -> str:
    rows = [("資料狀態", AVAILABILITY[partner.availability_status]),
            ("狀態說明", partner.availability_note),
            ("名額狀態", {"published": "來源已列載，仍需確認適用年度", "zero": "零名額", "not_published": "未列載／待確認",
                          "reference_only": "參考名額", "fee_paying": "自費"}.get(partner.quota_status, "待確認")),
            ("母校受理時窗", {"open": "受理中（依來源時窗）", "closed": "已截止", "needs_confirmation": "待確認"}.get(partner.application_window_status, "待確認"))]
    rows.extend((label, getattr(partner, field)) for field, label in FIELDS)
    if partner.checked_at:
        rows.append(("資料查核時間", display_time(partner.checked_at)))
    details = "".join(f'<dt>{escape(label)}</dt><dd>{escape(str(value))}</dd>' for label, value in rows if value)
    labels = dict(FIELDS)
    evidence = "".join(
        f'<li><strong>{escape(labels.get(key, "補充條件"))}</strong>：{EVIDENCE[item.status]}；{escape(item.note or "")} '
        f'{source_link(item.source_url, "查閱來源")} '
        f'{escape(item.academic_year or "")} {escape(item.application_round or "")} '
        f'（查核：{escape(display_time(item.checked_at))}）</li>'
        for key, item in partner.field_evidence.items())
    references = "".join(f'<dt>{escape(key)}</dt><dd>{escape(value)}</dd>' for key, value in partner.reference_data.items())
    options = "".join('<h3>' + escape(option.program_type) + '</h3><dl>' + "".join(
        f'<dt>{escape(label)}</dt><dd>{escape(str(getattr(option, key)))}</dd>'
        for key, label in FIELDS if getattr(option, key, None)) + '</dl>'
        + source_link(option.source_url, "此方案來源") for option in partner.program_options)
    return f'''<section class="programme"><h2>{escape(partner.program_type)}</h2><dl>{details}</dl>
<p>{source_link(partner.source_url, "母校合作校／名額資料來源")} · {source_link(partner.website, "合作校官方網站")}</p>
{('<details><summary>欄位查核狀態與來源</summary><ul>' + evidence + '</ul></details>') if evidence else ''}
{('<h3>歷史／參考資料（非本期已確認條件）</h3><dl>' + references + '</dl>') if references else ''}{options}</section>'''


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
    snapshots: dict[str, tuple[float, list[PartnerUniversity], CatalogueSourceStatus | None]] = {}
    snapshot_lock = threading.Lock()
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
        with snapshot_lock:
            cached = snapshots.get(u.id)
            if cached and monotonic() - cached[0] < 60:
                return cached[1], cached[2]
            partners, source = catalogue(u)
            if not partners:
                raise HTTPException(503, "合作校資料暫不可用，請稍後重試。", headers={"Retry-After": "60"})
            hashes = {settings.origin + partner_path(u, rows[0]): digest(material_content(rows))
                      for rows in group_partners(partners).values()}
            for url in hashes:
                lastmods.pop(url, None)
            lastmods.update(record_changes(hashes))
            snapshots[u.id] = monotonic(), partners, source
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

    @router.api_route("/schools", methods=["GET", "HEAD"])
    def directory():
        cards = "".join(f'<li><a href="/schools/{u.id}"><strong>{escape(u.school_name)}</strong>'
                        f'<span>{escape(u.english_name)}</span></a><p>{escape(u.coverage_note)}</p></li>' for u in universities.values())
        body = f'<p class="eyebrow">交換學生・從母校開始</p><h1>臺灣大學交換學生申請指南</h1>'
        body += f'<p class="lead">依就讀大學查看海外合作校、名額狀態與申請條件。目前整理 {len(universities)} 所母校的公開資訊。</p><ul class="cards">{cards}</ul>'
        return page(settings, "交換學生申請與合作學校指南｜UniWay", HOME_DESCRIPTION, "/schools", body,
                    [("首頁", "/"), ("交換學校指南", "/schools")])

    @router.api_route("/schools/{home_id}", methods=["GET", "HEAD"])
    def home_school(home_id: str):
        u = university(home_id)
        partners, source = catalogue_for(u)
        groups = group_partners(partners)
        cards = "".join(f'<li><a href="{partner_path(u, rows[0])}"><strong>{escape(rows[0].school_name)}</strong>'
                        f'<span>{escape(rows[0].country or "國家待確認")}</span></a><p>{escape("、".join(dict.fromkeys(AVAILABILITY[p.availability_status] for p in rows)))}</p></li>'
                        for rows in groups.values())
        title = f"{u.school_name}交換學生申請與合作學校｜UniWay"
        description = f"查詢{u.school_name}海外交換合作校、申請資格、名額與來源。依各方案顯示本期、參考或待確認狀態，申請以校方最新公告為準。"
        body = f'<p class="eyebrow">{escape(u.english_name)}</p><h1>{escape(u.school_name)}交換學生申請與合作學校</h1><p class="lead">{escape(u.coverage_note)}</p>'
        body += f'<p>{source_link(u.official_url, "母校國際處官方資訊")}</p><a class="button" href="{escape(application_link(u))}">開啟{escape(u.short_name)}選校與申請工具</a>'
        body += source_notice(source) + f'<h2>合作校與方案資料</h2><p>共 {len(groups)} 個合作校頁面、{len(partners)} 筆方案資料；此數量不是本期可申請名額。</p><ul class="cards">{cards}</ul>'
        return page(settings, title, description, f"/schools/{u.id}", body,
                    [("首頁", "/"), ("交換學校指南", "/schools"), (u.school_name, f"/schools/{u.id}")])

    @router.api_route("/schools/{home_id}/partners/{key}", methods=["GET", "HEAD"])
    def partner_school(home_id: str, key: str):
        u = university(home_id)
        partners, source = catalogue_for(u)
        rows = group_partners(partners).get(key)
        if not rows:
            raise HTTPException(404, "找不到這所合作校")
        partner = rows[0]
        title = f"{partner.school_name}交換資訊｜{u.school_name}｜UniWay"
        description = f"{u.school_name}學生前往{partner.school_name}的交換與研修資料。{AVAILABILITY[partner.availability_status]}。查閱方案資格、名額、期限與官方來源；以校方最新公告為準。"
        body = f'<p class="eyebrow">{escape(u.school_name)} → {escape(partner.country or "海外合作校")}</p><h1>{escape(partner.school_name)}交換與研修資訊</h1>'
        body += f'<p class="lead">此頁適用母校：{escape(u.school_name)}。不同母校或方案的規定可能不同，請逐項確認。</p>'
        body += f'<a class="button" href="{escape(application_link(u, partner))}">在 UniWay 查看學校與規劃申請</a>' + source_notice(source)
        body += "".join(partner_details(row) for row in rows)
        path = partner_path(u, partner)
        return page(settings, title, description, path, body,
                    [("首頁", "/"), ("交換學校指南", "/schools"), (u.school_name, f"/schools/{u.id}"), (partner.school_name, path)])

    @router.api_route("/sitemap.xml", methods=["GET", "HEAD"])
    def sitemap_index():
        return xml_response("sitemapindex", [settings.origin + "/sitemaps/pages.xml"] +
                            [f"{settings.origin}/sitemaps/{u.id}.xml" for u in universities.values()])

    @router.api_route("/sitemaps/pages.xml", methods=["GET", "HEAD"])
    def static_sitemap():
        return xml_response("urlset", [settings.origin + path for path in ("/", "/schools")] +
                            [f"{settings.origin}/schools/{u.id}" for u in universities.values()])

    @router.api_route("/sitemaps/{home_id}.xml", methods=["GET", "HEAD"])
    def school_sitemap(home_id: str):
        u = university(home_id)
        partners, _ = catalogue_for(u)
        return xml_response("urlset", [settings.origin + partner_path(u, rows[0]) for rows in group_partners(partners).values()], lastmods)

    return router
