from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote, urlsplit
from xml.etree import ElementTree

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.cgu_catalogue import CguCatalogue
from exchange_info.models import ExchangeFieldEvidence, PartnerUniversity
from exchange_info.seo import (
    AI_SEARCH_CRAWLERS, AI_TRAINING_CRAWLERS, EDITORIAL_PATHS, SeoSettings, group_partners, partner_id,
    robots_txt, source_link,
)
from exchange_info.seo_guides import COUNTRIES, GUIDES
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("EXCHANGE_SEO_INDEXABLE", "true")
        patch.setenv("EXCHANGE_PUBLIC_BASE_URL", "https://app.uniway-tw.com")
        patch.setenv("EXCHANGE_GOOGLE_SITE_VERIFICATION", "test-verification-token")
        # Use the real shipped CGU snapshot, without a background network refresh.
        original_view = CguCatalogue.view
        patch.setattr(CguCatalogue, "view", lambda self, **_: original_view(self, refresh=False))
        app = create_app(tmp_path_factory.mktemp("seo"))
        with TestClient(app, base_url="http://internal.invalid") as browser:
            yield browser


def locations(response):
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    root = ElementTree.fromstring(response.content)
    return [node.text for node in root.findall(".//{*}loc")]


def test_home_metadata_is_absolute_and_does_not_trust_request_host(client):
    response = client.get("/", headers={"Host": "attacker.example", "X-Forwarded-Host": "attacker.example"})
    soup = BeautifulSoup(response.text, "html.parser")
    assert soup.select_one('link[rel="canonical"]')["href"] == "https://app.uniway-tw.com/"
    assert len(soup.select('meta[name="description"]')) == 1
    assert soup.select_one('meta[name="google-site-verification"]')["content"] == "test-verification-token"
    assert soup.select_one('meta[property="og:url"]')["content"] == "https://app.uniway-tw.com/"
    assert soup.select_one('meta[name="twitter:card"]')["content"] == "summary"
    graph = json.loads(soup.select_one('script[type="application/ld+json"]').string)["@graph"]
    assert {node["@type"] for node in graph} == {"Organization", "WebSite"}
    organization = next(node for node in graph if node["@type"] == "Organization")
    website = next(node for node in graph if node["@type"] == "WebSite")
    assert organization["@id"] == "https://app.uniway-tw.com/#organization"
    assert organization["logo"]["url"] == "https://app.uniway-tw.com/static/assets/brand/apple-touch-icon.png"
    assert website["publisher"] == {"@id": organization["@id"]}
    assert all(url.startswith("https://") for url in organization["sameAs"])
    assert soup.select_one('a[href="/schools"]')
    assert "seo-head" not in response.text and "attacker.example" not in response.text
    assert client.head("/").status_code == 200


@pytest.mark.parametrize("home", SUPPORTED_UNIVERSITIES, ids=lambda u: u.id)
def test_every_catalogue_has_discoverable_pages_and_a_matching_sitemap(client, home):
    response = client.get(f"/schools/{home.id}")
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    assert home.school_name in soup.h1.get_text()
    links = [a["href"] for a in soup.select(".cards a")]
    assert links and len(links) == len(set(links))
    urls = locations(client.get(f"/sitemaps/{home.id}.xml"))
    assert urls == ["https://app.uniway-tw.com" + p for p in links]
    assert all("#" not in url and "?" not in url for url in urls)
    page = client.get(links[0])
    assert page.status_code == 200
    document = BeautifulSoup(page.text, "html.parser")
    assert home.school_name in document.title.string
    assert document.select_one('link[rel="canonical"]')["href"] == urls[0]
    assert document.select_one(".programme dl").get_text(strip=True)
    assert document.select_one('.programme a[href^="http"]')
    assert len(document.select("h1")) == 1
    assert "請以母校國際處" in page.text
    cta = urlsplit(document.select_one(".button")["href"])
    assert parse_qs(cta.query)["home"] == [home.school_name]
    assert unquote(cta.fragment).startswith("school=")
    breadcrumb = json.loads(document.select_one('script[type="application/ld+json"]').string)
    assert breadcrumb["itemListElement"][-1]["item"] == urls[0]


def test_sitemap_index_and_directory_cover_all_schools(client):
    urls = locations(client.get("/sitemap.xml"))
    assert len(urls) == len(SUPPORTED_UNIVERSITIES) + 2
    assert "https://app.uniway-tw.com/sitemaps/partners.xml" in urls
    roots = locations(client.get("/sitemaps/pages.xml"))
    assert len(roots) == len(SUPPORTED_UNIVERSITIES) + 2 + len(EDITORIAL_PATHS)
    directory = BeautifulSoup(client.get("/schools").text, "html.parser")
    assert len(directory.select(".cards a")) == len(SUPPORTED_UNIVERSITIES)
    for path in ("/sitemap.xml", "/sitemaps/pages.xml", "/robots.txt", "/schools"):
        response = client.head(path)
        assert response.status_code == 200 and not response.content
    assert "lastmod" not in client.get("/sitemaps/ntpu.xml").text  # no invented modification dates


def test_editorial_pages_are_indexable_through_the_real_app_middleware(client):
    for path in EDITORIAL_PATHS:
        response = client.get(path)
        assert response.status_code == 200
        assert "noindex" not in response.headers.get("X-Robots-Tag", "")
        assert 'content="index, follow' in response.text


def test_invalid_school_or_partner_is_a_real_noindex_404(client):
    for path in ("/schools/unknown", "/schools/NTU", "/schools/ntu/partners/unknown", "/sitemaps/unknown.xml"):
        response = client.get(path)
        assert response.status_code == 404
        assert "noindex" in response.headers["X-Robots-Tag"]


def test_public_pages_do_not_read_sessions_or_personal_workspaces(client, monkeypatch):
    def private_read(*args, **kwargs):
        pytest.fail("SEO must not access private account state")
    monkeypatch.setattr(client.app.state.account_repository, "find_session_by_token_hash", private_read)
    anonymous = client.get("/schools/ntpu").content
    signed_in = client.get("/schools/ntpu", headers={"Authorization": "Bearer not-a-real-session", "Cookie": "exchange_session=not-real"})
    assert signed_in.content == anonymous
    assert signed_in.headers["cache-control"].startswith("public")


def test_robots_and_noindex_headers_keep_api_and_private_routes_out(client):
    robots = client.get("/robots.txt").text
    assert "Sitemap: https://app.uniway-tw.com/sitemap.xml" in robots
    assert "Disallow: /account/" in robots and "Disallow: /calendar/" in robots
    assert "Disallow: /static/" not in robots
    for path in ("/auth/me", "/account/workspace", "/docs", "/static/index.html", "/universities"):
        assert "noindex" in client.get(path).headers["X-Robots-Tag"]
    assert "noindex" not in client.get("/schools").headers.get("X-Robots-Tag", "")


def test_robots_states_a_policy_for_each_ai_crawler_and_keeps_private_paths_closed(client):
    robots = client.get("/robots.txt").text
    groups = [group.strip().splitlines() for group in robots.strip().split("\n\n")]
    by_agent = {line.split(": ", 1)[1]: group for group in groups for line in group if line.startswith("User-agent: ")}
    for bot in (*AI_SEARCH_CRAWLERS, *AI_TRAINING_CRAWLERS):
        assert "Allow: /" in by_agent[bot] and "Disallow: /" not in by_agent[bot]
        # A named group replaces the "*" group, so the private paths must be repeated in it.
        assert {"Disallow: /account/", "Disallow: /auth/", "Disallow: /admin/", "Disallow: /calendar/"} <= set(by_agent[bot])
    assert robots.rstrip().endswith("Sitemap: https://app.uniway-tw.com/sitemap.xml")


def test_search_only_policy_closes_training_crawlers_but_not_search_crawlers():
    robots = robots_txt(SeoSettings("https://example.com", True, ai_crawlers="search-only"))
    groups = [group.strip().splitlines() for group in robots.strip().split("\n\n")]
    by_agent = {line.split(": ", 1)[1]: group for group in groups for line in group if line.startswith("User-agent: ")}
    assert all(by_agent[bot][-1] == "Disallow: /" for bot in AI_TRAINING_CRAWLERS)
    assert all("Allow: /" in by_agent[bot] for bot in AI_SEARCH_CRAWLERS)
    assert robots_txt(SeoSettings("https://example.com", False)) == "User-agent: *\nDisallow: /\n"


def test_ai_crawler_policy_comes_from_environment_and_ignores_typos(caplog):
    base = {"EXCHANGE_PUBLIC_BASE_URL": "https://example.com"}
    assert SeoSettings.from_environment(base).ai_crawlers == "allow"
    assert SeoSettings.from_environment({**base, "EXCHANGE_AI_CRAWLERS": " Search-Only "}).ai_crawlers == "search-only"
    assert SeoSettings.from_environment({**base, "EXCHANGE_AI_CRAWLERS": "blokc"}).ai_crawlers == "allow"
    assert "EXCHANGE_AI_CRAWLERS" in caplog.text


def test_llms_txt_maps_public_pages_with_absolute_urls_and_the_availability_caveat(client):
    response = client.get("/llms.txt")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain") and "noindex" not in response.headers.get("X-Robots-Tag", "")
    lines = response.text.splitlines()
    assert lines[0] == "# UniWay" and lines[2].startswith("> ")
    assert "合作關係不等於當期開放申請" in response.text
    urls = [url for url in re.findall(r"\]\((https?://[^)]+)\)", response.text)]
    assert urls and all(url.startswith("https://app.uniway-tw.com/") for url in urls)
    expected = {f"https://app.uniway-tw.com/schools/{u.id}" for u in SUPPORTED_UNIVERSITIES}
    expected |= {f"https://app.uniway-tw.com/guides/{slug}" for slug in GUIDES}
    expected |= {f"https://app.uniway-tw.com/destinations/{slug}" for slug in COUNTRIES}
    assert expected <= set(urls)
    # Partner pages number in the thousands and belong in the sitemap, not here.
    assert not any("/partners/" in url and "/schools/" in url for url in urls)
    assert client.head("/llms.txt").status_code == 200


def test_llms_txt_is_unavailable_on_preview_builds(tmp_path, monkeypatch):
    monkeypatch.delenv("EXCHANGE_SEO_INDEXABLE", raising=False)
    monkeypatch.setenv("EXCHANGE_ENVIRONMENT", "development")
    with TestClient(create_app(tmp_path)) as preview:
        assert preview.get("/llms.txt").status_code == 404


def test_preview_defaults_to_noindex_without_affecting_public_content(tmp_path, monkeypatch):
    monkeypatch.delenv("EXCHANGE_SEO_INDEXABLE", raising=False)
    monkeypatch.setenv("EXCHANGE_ENVIRONMENT", "development")
    with TestClient(create_app(tmp_path)) as client:
        assert client.get("/robots.txt").text == "User-agent: *\nDisallow: /\n"
        page = client.get("/schools")
        assert page.status_code == 200 and "noindex" in page.headers["X-Robots-Tag"]
        assert 'content="noindex, nofollow"' in page.text


def test_partner_status_evidence_and_untrusted_text_are_preserved(tmp_path, monkeypatch):
    partner = PartnerUniversity(
        school_name='測試 </script><script>alert(1)</script> University', country="日本",
        program_type="交換 <b>學生</b>", availability_status="reference_only", quota="5",
        quota_status="reference_only", application_window_status="closed",
        eligibility='GPA 3.0 & 以上', source_url="javascript:alert(1)", website="https://example.edu/",
        field_evidence={"quota": ExchangeFieldEvidence(source_url="https://example.edu/quota", checked_at=datetime(2026, 1, 1, tzinfo=timezone.utc), status="reference_only", note="歷史名額")},
        reference_data={"前期名額": "5"},
    )
    monkeypatch.setattr("exchange_info.api.fetch_ntpu_partner_universities", lambda: [partner])
    with TestClient(create_app(tmp_path)) as client:
        response = client.get(f"/schools/ntpu/partners/{partner_id(partner)}")
        soup = BeautifulSoup(response.text, "html.parser")
        assert response.status_code == 200
        assert soup.h1.get_text().startswith(partner.school_name)
        assert "歷史／參考資料" in soup.get_text() and "已截止" in soup.get_text()
        assert "歷史名額" in soup.get_text() and "GPA 3.0 & 以上" in soup.get_text()
        assert not soup.select('a[href^="javascript:"]')
        # Inline content stays inert; the only executable script is our local theme control.
        assert [s.get("src", "").split("?")[0] for s in soup.select('script:not([type="application/ld+json"])')] == ["/static/reading-theme.js"]
        assert len(soup.select('script:not([src])')) == 1
        json.loads(soup.select_one('script[type="application/ld+json"]').string)


def test_institution_identity_groups_programmes_but_keeps_countries_distinct():
    base = PartnerUniversity(school_name="測試 Test University", country="日本", program_type="交換", source_url="https://example.edu")
    second = base.model_copy(update={"program_type": "雙學位"})
    another = base.model_copy(update={"country": "美國"})
    groups = group_partners([base, second, another])
    assert len(groups) == 2 and len(groups[partner_id(base)]) == 2
    assert partner_id(base) == partner_id(base.model_copy(update={"quota": "25", "academic_year": "118"}))


def test_unavailable_catalogue_fails_closed_in_pages_and_sitemaps(tmp_path, monkeypatch):
    from exchange_info.cgu_catalogue import CatalogueView
    from exchange_info.models import CatalogueSourceStatus
    monkeypatch.setattr(CguCatalogue, "view", lambda *_a, **_kw: CatalogueView([], CatalogueSourceStatus(status="unavailable")))
    with TestClient(create_app(tmp_path)) as client:
        for path in ("/schools/cgu", "/sitemaps/cgu.xml"):
            response = client.get(path)
            assert response.status_code == 503 and response.headers["Retry-After"] == "60"
            assert "noindex" in response.headers["X-Robots-Tag"]


def test_canonical_configuration_and_unsafe_source_urls():
    for url in ("https://user:password@example.com", "https://example.com/path", "https://example.com?q=a", "javascript:alert(1)"):
        with pytest.raises(ValueError):
            SeoSettings.from_environment({"EXCHANGE_PUBLIC_BASE_URL": url})
    assert SeoSettings.from_environment({"EXCHANGE_ENVIRONMENT": "production"}).indexable
    assert not SeoSettings.from_environment({"EXCHANGE_ENVIRONMENT": "production", "EXCHANGE_SEO_INDEXABLE": "false"}).indexable
    assert '<a ' not in source_link("javascript:alert(1)", "官方來源")


def test_catalogue_cache_refreshes_window_status_and_does_not_hide_a_source_failure(monkeypatch):
    from fastapi import FastAPI, HTTPException
    from exchange_info.seo import create_seo_router
    now, calls = [0.0], []
    row = PartnerUniversity(school_name="Cache University", country="日本", program_type="交換",
                            source_url="https://example.edu", application_window_status="open")

    def catalogue(_):
        calls.append(now[0])
        if now[0] >= 122:
            raise HTTPException(503, "source unavailable")
        return [row.model_copy(update={"application_window_status": "closed" if now[0] >= 61 else "open"})], None

    monkeypatch.setattr("exchange_info.seo.monotonic", lambda: now[0])
    app = FastAPI()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), catalogue))
    with TestClient(app) as client:
        path = f"/schools/ntpu/partners/{partner_id(row)}"
        assert "受理中" in client.get(path).text
        client.get("/sitemaps/ntpu.xml")
        assert len(calls) == 1
        now[0] = 61
        assert "已截止" in client.get(path).text and len(calls) == 2
        now[0] = 122
        assert client.get(path).status_code == 503
