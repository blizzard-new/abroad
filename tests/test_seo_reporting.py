from datetime import date

from exchange_info.seo_analytics import measurement_id
from exchange_info.seo_reporting import SearchConsole, build_search_report, diagnostic, inspection_sample, summarize_access_log


def test_ga4_requires_an_explicit_enable_and_a_valid_public_id():
    assert measurement_id({}) == ""
    assert measurement_id({"EXCHANGE_GA4_MEASUREMENT_ID": "G-TEST123456"}) == ""
    assert measurement_id({"EXCHANGE_GA4_ENABLED": "true", "EXCHANGE_GA4_MEASUREMENT_ID": '"><script>'}) == ""
    assert measurement_id({"EXCHANGE_GA4_ENABLED": "true", "EXCHANGE_GA4_MEASUREMENT_ID": "G-TEST123456"}) == "G-TEST123456"


def test_google_script_and_csp_are_absent_until_operator_enables(monkeypatch):
    from exchange_info.api import _browser_security_headers
    from exchange_info.seo import SeoSettings, metadata
    monkeypatch.delenv("EXCHANGE_GA4_ENABLED", raising=False)
    monkeypatch.setenv("EXCHANGE_GA4_MEASUREMENT_ID", "G-TEST123456")
    assert "seo-analytics.js" not in metadata(SeoSettings("https://example.com", True), "Title", "Description", "/")
    assert "googletagmanager" not in _browser_security_headers()["Content-Security-Policy"]
    monkeypatch.setenv("EXCHANGE_GA4_ENABLED", "true")
    assert "seo-analytics.js" in metadata(SeoSettings("https://example.com", True), "Title", "Description", "/")
    assert "https://www.googletagmanager.com" in _browser_security_headers()["Content-Security-Policy"]
    assert "unsafe-inline" not in _browser_security_headers()["Content-Security-Policy"].split("script-src ")[1].split(";")[0]


def test_report_does_not_turn_missing_data_into_zero():
    report = build_search_report({})
    assert report["current"]["impressions"] is None
    assert report["nonbrand_observed"]["impressions"] is None
    assert report["a_tier_inspection_sample"]["pass_rate"] is None
    assert report["ga4_organic_events"] is None


def test_query_totals_are_not_used_as_site_totals_or_all_nonbrand_queries():
    raw = {"current": {"totals": {"rows": [{"clicks": 12, "impressions": 120, "ctr": .1, "position": 4.5}]},
                       "query": {"rows": [{"keys": ["UniWay"], "clicks": 5, "impressions": 50},
                                          {"keys": ["日本交換學生"], "clicks": 3, "impressions": 30}], "truncated": False}}}
    report = build_search_report(raw)
    assert report["current"]["clicks"] == 12
    assert report["nonbrand_observed"]["clicks"] == 3
    assert "not a full" in report["nonbrand_observed"]["limitation"]


def test_index_inspection_preserves_reasons_and_diagnoses_canonical_and_noindex():
    result = diagnostic({"url": "https://app.uniway-tw.com/a", "inspectionResult": {"indexStatusResult": {
        "verdict": "NEUTRAL", "coverageState": "Crawled - currently not indexed", "pageFetchState": "SUCCESSFUL",
        "googleCanonical": "https://app.uniway-tw.com/b", "userCanonical": "https://app.uniway-tw.com/a",
        "indexingState": "BLOCKED_BY_META_TAG"}}})
    assert len(result["issues"]) == 3
    assert result["coverage"] == "Crawled - currently not indexed"
    assert "not a live" in result["limitation"]


def test_samples_cover_homes_before_extra_tiers_and_obey_quota():
    audit = {"pages": [{"home": h, "path": f"/schools/{h}/partners/{tier}", "tier": tier} for h in ("cgu", "ntu", "ntpu") for tier in ("B", "A", "C")]}
    urls = inspection_sample(audit, "https://app.uniway-tw.com", 5)
    assert len(urls) == 5 and any("/cgu/" in u for u in urls) and any("/ntu/" in u for u in urls) and any("/ntpu/" in u for u in urls)
    assert inspection_sample(audit, "https://app.uniway-tw.com", 0) == []


def test_collector_uses_final_taiwan_web_data_and_reads_child_sitemaps(monkeypatch):
    client = SearchConsole("synthetic-test-token")
    calls = []
    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return {"rows": []}
    monkeypatch.setattr(client, "request", request)
    result = client.collect(date(2026, 10, 15), ["https://app.uniway-tw.com/schools"])
    assert result["period"]["start"] == "2026-09-18"
    assert result["period"]["previous_end"] == "2026-09-17"
    query = calls[0][2]["json"]
    assert query["dataState"] == "final" and query["type"] == "web"
    assert query["dimensionFilterGroups"][0]["filters"][0]["expression"] == "twn"
    assert calls[-1][2]["params"]["sitemapIndex"] == "https://app.uniway-tw.com/sitemap.xml"
    assert all("publish" not in url and "indexing.googleapis.com" not in url for _, url, _ in calls)


def test_caddy_report_retains_no_ip_or_private_url():
    lines = ['{"request":{"remote_ip":"192.0.2.1","uri":"/account?secret=abc","headers":{"User-Agent":["Googlebot"]}},"status":503,"duration":0.4}',
             '{"request":{"headers":{"User-Agent":["Browser"]}},"status":500,"duration":20}', 'invalid']
    result = summarize_access_log(lines)
    assert result["http_5xx"] == {"503": 1}
    assert result["response_duration_p75_ms"] == 400
    assert result["malformed_lines"] == 1
    assert "192.0.2.1" not in str(result) and "secret" not in str(result)


def test_ga4_read_only_report_filters_organic_search(monkeypatch):
    client = SearchConsole("synthetic-test-token")
    requests = []
    monkeypatch.setattr(client, "request", lambda method, url, **kw: requests.append((url, kw)) or {"rows": []})
    client.ga4_events("123456", date(2026, 9, 1), date(2026, 9, 28))
    url, request = requests[0]
    assert "/properties/123456:runReport" in url
    assert {d["name"] for d in request["json"]["dimensions"]} == {"eventName", "sessionDefaultChannelGroup", "countryId"}
    assert request["json"]["dimensionFilter"]["andGroup"]["expressions"][0]["filter"]["stringFilter"]["value"] == "Organic Search"
