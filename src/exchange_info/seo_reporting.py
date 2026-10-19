"""Read-only Google SEO diagnostics and evidence-based reporting (no indexing requests)."""
from __future__ import annotations

import re
import math
from collections import Counter
from datetime import date, timedelta
from urllib.parse import quote

import requests


class SearchConsole:
    def __init__(self, token: str, site: str = "https://app.uniway-tw.com/"):
        if not token.strip():
            raise ValueError("A read-only Google OAuth access token is required")
        self.site = site
        self.session = requests.Session()
        self.session.headers.update({"Authorization": "Bearer " + token, "User-Agent": "UniWay-SEO-Diagnostics/1.0"})

    def request(self, method, url, **kwargs):
        response = self.session.request(method, url, timeout=45, **kwargs)
        if response.status_code != 200:
            # Do not echo token, response body, queries or request headers into logs.
            raise ValueError(f"Google API returned HTTP {response.status_code}; check scopes, property access and quota")
        return response.json()

    def analytics(self, start: date, end: date, dimension: str | None = None):
        url = "https://www.googleapis.com/webmasters/v3/sites/" + quote(self.site, safe="") + "/searchAnalytics/query"
        body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "type": "web", "dataState": "final",
                "dimensionFilterGroups": [{"filters": [{"dimension": "country", "operator": "equals", "expression": "twn"}]}]}
        if dimension:
            body["dimensions"] = [dimension]
        rows, truncated = [], False
        for offset in range(0, 100_000, 25_000):
            result = self.request("POST", url, json={**body, "rowLimit": 25_000, "startRow": offset})
            batch = result.get("rows", [])
            rows.extend(batch)
            if len(batch) < 25_000:
                break
        else:
            truncated = True
        return {"rows": rows, "truncated": truncated, "dimension": dimension,
                "limitation": "Google may omit anonymized queries and lower-volume rows even when pagination is complete."}

    def sitemaps(self):
        url = "https://www.googleapis.com/webmasters/v3/sites/" + quote(self.site, safe="") + "/sitemaps"
        return {"submitted": self.request("GET", url),
                "index_children": self.request("GET", url, params={"sitemapIndex": self.site.rstrip("/") + "/sitemap.xml"})}

    def ga4_events(self, property_id: str, start: date, end: date):
        if not property_id.isdigit():
            raise ValueError("GA4 property ID must be numeric (not the G- measurement ID)")
        body = {"dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
                "dimensions": [{"name": name} for name in ("eventName", "sessionDefaultChannelGroup", "countryId")],
                "metrics": [{"name": "eventCount"}, {"name": "totalUsers"}],
                "dimensionFilter": {"andGroup": {"expressions": [
                    {"filter": {"fieldName": "sessionDefaultChannelGroup", "stringFilter": {"matchType": "EXACT", "value": "Organic Search"}}},
                    {"filter": {"fieldName": "countryId", "stringFilter": {"matchType": "EXACT", "value": "TW"}}},
                    {"filter": {"fieldName": "eventName", "inListFilter": {"values": ["open_school_planner", "compare_universities", "click_official_source", "view_application_guide"]}}}
                ]}}}
        return self.request("POST", f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport", json=body)

    def inspect(self, url: str):
        return self.request("POST", "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
                            json={"inspectionUrl": url, "siteUrl": self.site, "languageCode": "zh-TW"})

    def collect(self, end: date, urls: list[str]):
        start = end - timedelta(days=27)
        previous_end = start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=27)
        current, previous = {}, {}
        for dimension in (None, "query", "page"):
            key = dimension or "totals"
            current[key] = self.analytics(start, end, dimension)
            previous[key] = self.analytics(previous_start, previous_end, dimension)
        inspections = [{"url": url, **self.inspect(url)} for url in urls]
        return {"schema_version": 1, "site": self.site, "scope": {"search_type": "web", "country": "twn", "data_state": "final"},
                "period": {"start": start.isoformat(), "end": end.isoformat(), "previous_start": previous_start.isoformat(), "previous_end": previous_end.isoformat()},
                "current": current, "previous": previous, "sitemaps": self.sitemaps(), "inspections": inspections}


def inspection_sample(audit: dict, origin: str, limit: int = 30) -> list[str]:
    pages = audit.get("pages", [])
    paths = ["/", "/schools"]
    # One representative per home, then remaining tiers; deterministic and quota bounded.
    for home in dict.fromkeys(p["home"] for p in pages):
        paths.append(next(p["path"] for p in pages if p["home"] == home))
    for tier in ("A", "B", "C"):
        for home in dict.fromkeys(p["home"] for p in pages):
            match = next((p["path"] for p in pages if p["home"] == home and p["tier"] == tier), None)
            if match and match not in paths:
                paths.append(match)
    return [origin.rstrip("/") + path for path in paths[:limit]]


def metrics(payload):
    rows = payload.get("totals", {}).get("rows", [])
    if not rows:
        return {name: None for name in ("clicks", "impressions", "ctr", "position")}
    return {name: rows[0].get(name) for name in ("clicks", "impressions", "ctr", "position")}


def diagnostic(row: dict) -> dict:
    result = row.get("inspectionResult", {}).get("indexStatusResult", {})
    issues = []
    if result.get("googleCanonical") and result.get("userCanonical") and result["googleCanonical"] != result["userCanonical"]:
        issues.append("Google 選擇不同 canonical；先確認內容差異，不直接全部改指母校")
    if result.get("robotsTxtState") == "DISALLOWED":
        issues.append("robots.txt 阻擋")
    if result.get("indexingState") in {"BLOCKED_BY_META_TAG", "BLOCKED_BY_HTTP_HEADER"}:
        issues.append("noindex 阻擋")
    if result.get("pageFetchState") not in {None, "SUCCESSFUL", "PAGE_FETCH_STATE_UNSPECIFIED"}:
        issues.append("抓取狀態：" + result["pageFetchState"])
    if result.get("pageFetchState") == "SUCCESSFUL" and result.get("verdict") not in {None, "PASS"}:
        issues.append("Google 曾成功抓取但尚未通過索引判定；依 coverage 原因檢查內容價值、重複與內部連結，不批量要求重抓")
    return {"url": row.get("url"), "verdict": result.get("verdict"), "coverage": result.get("coverageState"),
            "last_crawl": result.get("lastCrawlTime"), "google_canonical": result.get("googleCanonical"),
            "user_canonical": result.get("userCanonical"), "issues": issues,
            "limitation": "Google indexed-version inspection; not a live URL test or indexing request."}


def build_search_report(raw: dict, audit: dict | None = None, brand_pattern: str = r"uni\s*way|uniway-tw") -> dict:
    current, previous = raw.get("current", {}), raw.get("previous", {})
    brand = re.compile(brand_pattern, re.IGNORECASE)
    nonbrand = [r for r in current.get("query", {}).get("rows", []) if not brand.search(" ".join(r.get("keys", [])))]
    queries_available = bool(current.get("query", {}).get("rows"))
    inspections = [diagnostic(row) for row in raw.get("inspections", [])]
    tiers = {"https://app.uniway-tw.com" + p["path"]: p["tier"] for p in (audit or {}).get("pages", [])}
    sample = [r for r in inspections if tiers.get(r["url"]) == "A" and r["verdict"] is not None]
    return {"site": raw.get("site"), "scope": raw.get("scope"), "period": raw.get("period"),
            "current": metrics(current), "previous": metrics(previous),
            "nonbrand_observed": {"query_rows": len(nonbrand) if queries_available else None,
                                  "impressions": sum(r.get("impressions", 0) for r in nonbrand) if queries_available else None,
                                  "clicks": sum(r.get("clicks", 0) for r in nonbrand) if queries_available else None,
                                  "limitation": "Only returned queries; anonymized/omitted queries mean this is not a full nonbrand total."},
            "a_tier_inspection_sample": {"inspected": len(sample), "pass": sum(r["verdict"] == "PASS" for r in sample),
                                         "pass_rate": sum(r["verdict"] == "PASS" for r in sample) / len(sample) if sample else None,
                                         "limitation": "Sample only, not all A pages or all indexed URLs."},
            "inspections": inspections, "sitemaps": raw.get("sitemaps"),
            "ga4_organic_events": raw.get("ga4_organic_events"),
            "query_rows_truncated": current.get("query", {}).get("truncated"),
            "scope_warning": "Search Console dates use Google's Pacific reporting timezone; do not directly divide by GA4 sessions or mix with Taiwan-day totals."}


def summarize_access_log(lines) -> dict:
    import json
    durations, errors, count, malformed = [], Counter(), 0, 0
    for line in lines:
        try:
            row = json.loads(line)
            agents = row.get("request", {}).get("headers", {}).get("User-Agent", [])
            if isinstance(agents, str):
                agents = [agents]
            if not any("googlebot" in agent.lower() for agent in agents):
                continue
            count += 1
            status = int(row.get("status", 0))
            if status >= 500:
                errors[str(status)] += 1
            if isinstance(row.get("duration"), (int, float)):
                durations.append(row["duration"] * 1000)
        except (ValueError, TypeError, AttributeError):
            malformed += 1
    durations.sort()
    return {"googlebot_user_agent_requests": count, "http_5xx": dict(errors),
            "response_duration_p75_ms": durations[math.ceil(len(durations) * .75) - 1] if durations else None,
            "malformed_lines": malformed, "limitation": "User-agent classification is not verified Googlebot identity. Duration is full response time, not TTFB. No IPs or raw URLs are retained."}
