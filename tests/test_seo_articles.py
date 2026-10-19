"""Editorial publishing contracts: content, indexing, provenance and asset delivery."""
import json
from datetime import timedelta
from pathlib import Path
from xml.etree import ElementTree

import pytest
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

from exchange_info.seo import SeoSettings, create_seo_router
from exchange_info.models import PartnerUniversity
from exchange_info.seo_articles import ARTICLES, Article, render_article


@pytest.fixture
def client():
    app = FastAPI()
    partner = PartnerUniversity(school_name="測試合作校", country="日本", program_type="交換", source_url="https://example.edu/exchange")
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), lambda _: ([partner], None)))
    with TestClient(app) as client:
        yield client


def test_article_inventory_retains_existing_urls_and_has_distinct_search_intents():
    assert {"exchange-budget", "exchange-application", "exchange-eligibility"} <= ARTICLES.keys()
    assert len(ARTICLES) >= 10
    assert len({a.title for a in ARTICLES.values()}) == len(ARTICLES)
    assert len({a.description for a in ARTICLES.values()}) == len(ARTICLES)
    assert len({a.sections[0].paragraphs[0] for a in ARTICLES.values()}) == len(ARTICLES)


@pytest.mark.parametrize("slug", ARTICLES)
def test_article_is_complete_crawlable_and_has_consistent_metadata(client, slug):
    a = ARTICLES[slug]
    response = client.get("/guides/" + slug)
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    assert len(soup.select("h1")) == 1
    assert soup.h1.get_text() == a.title
    assert soup.select_one('link[rel="canonical"]')["href"] == "https://example.com/guides/" + slug
    assert soup.select_one('meta[property="og:type"]')["content"] == "article"
    assert soup.select_one('meta[property="og:image"]')["content"] == "https://example.com" + a.image_path
    assert soup.select_one('meta[name="robots"]')["content"].startswith("index, follow")
    assert soup.select_one('meta[name="description"]')["content"] == a.description
    schemas = [json.loads(s.string) for s in soup.select('script[type="application/ld+json"]')]
    graph = next(s for s in schemas if s["@type"] == "Article")
    assert graph["dateModified"] == str(a.modified)
    assert graph["mainEntityOfPage"] == "https://example.com/guides/" + slug
    assert graph["citation"] == [s.url for s in a.sources]
    assert any(s["@type"] == "BreadcrumbList" for s in schemas)
    assert len(soup.select(".article-faq")) >= 2
    assert len(soup.select(".article-diagram")) >= 1
    assert len(soup.select(".article-table table")) >= 1
    assert len(soup.select_one(".article-body").get_text()) > 1500
    ids = [element["id"] for element in soup.select("[id]")]
    assert len(ids) == len(set(ids))
    for link in soup.select('a[href^="#"]'):
        if link["href"] != "#partners":
            assert link["href"][1:] in ids
    figure = soup.select_one(".article-illustration")
    assert figure.find_previous("section") and figure.find_next("section")
    for img in soup.select(".editorial img"):
        assert img["width"] == "1536" and img["height"] == "1024"
        assert img["loading"] == "lazy"
    assert figure.img["alt"] and "情境插圖" in figure.figcaption.get_text()
    assert len(soup.select("#related .editorial-card")) >= 2


def test_local_images_are_valid_small_and_packagable():
    root = Path(__file__).parents[1] / "src/exchange_info"
    for path in {a.image_path for a in ARTICLES.values()}:
        file = root / path.lstrip("/")
        assert file.is_file() and file.stat().st_size < 450_000
        with Image.open(file) as image:
            assert image.format == "WEBP" and image.size == (1536, 1024)


def test_index_and_sitemap_include_every_article_and_stable_lastmod(client, monkeypatch):
    index = BeautifulSoup(client.get("/guides").text, "html.parser")
    links = {a["href"] for a in index.select(".editorial-card > a")}
    assert links == {"/guides/" + slug for slug in ARTICLES}
    first = client.get("/sitemaps/pages.xml").text
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries = {node.find("s:loc", ns).text: node.find("s:lastmod", ns) for node in ElementTree.fromstring(first)}
    for slug, article in ARTICLES.items():
        assert entries["https://example.com/guides/" + slug].text == str(article.modified)
    # A new source check with no content changes must not advertise a page update.
    a = ARTICLES["exchange-budget"]
    monkeypatch.setitem(ARTICLES, a.slug, a.model_copy(update={"checked": a.checked + timedelta(days=3)}))
    assert client.get("/sitemaps/pages.xml").text == first


def test_source_check_does_not_require_bumping_content_date():
    data = ARTICLES["exchange-budget"].model_dump()
    data["checked"] = data["modified"] + timedelta(days=1)
    assert Article.model_validate(data).modified == data["modified"]


def test_untrusted_article_text_is_escaped_and_source_urls_are_validated():
    a = ARTICLES["exchange-budget"].model_copy(deep=True)
    a.sections[0].paragraphs = ['<script>alert("x")</script> & <img src=x onerror=alert(1)>']
    soup = BeautifulSoup(render_article(a), "html.parser")
    assert not soup.select("script, img[onerror]")
    assert '<script>alert("x")</script>' in soup.get_text()
    for bad_url in ("javascript:alert(1)", "https://user:secret@example.com/"):
        data = a.model_dump()
        data["sources"][0]["url"] = bad_url
        with pytest.raises(ValidationError):
            Article.model_validate(data)


def test_invalid_citation_and_table_do_not_silently_publish():
    data = ARTICLES["exchange-budget"].model_dump()
    data["sections"][0]["refs"] = ["missing"]
    with pytest.raises(ValidationError, match="citation"):
        Article.model_validate(data)
    data = ARTICLES["exchange-budget"].model_dump()
    data["sections"][0]["table"]["rows"][0].pop()
    with pytest.raises(ValidationError, match="headers"):
        Article.model_validate(data)


def test_staging_still_noindex_and_unknown_guides_remain_404():
    app = FastAPI()
    app.include_router(create_seo_router(SeoSettings("https://example.com", False), lambda _: ([], None)))
    with TestClient(app) as client:
        soup = BeautifulSoup(client.get("/guides/exchange-budget").text, "html.parser")
        assert soup.select_one('meta[name="robots"]')["content"] == "noindex, nofollow"
        assert client.get("/guides/nonexistent-article").status_code == 404


def test_country_pages_point_to_specific_cost_guides(client):
    for country, slug in (("japan", "japan-exchange-cost"), ("south-korea", "korea-exchange-cost"), ("germany", "germany-exchange-cost")):
        soup = BeautifulSoup(client.get("/destinations/" + country).text, "html.parser")
        assert soup.select_one(f'a[href="/guides/{slug}"]')


def test_home_to_articles_and_assets_through_the_production_app(tmp_path, monkeypatch):
    # Exercise create_app, not just an isolated router: a merge can leave all
    # article files intact while accidentally removing the router registration.
    from exchange_info.api import create_app

    monkeypatch.setenv("EXCHANGE_SEO_INDEXABLE", "true")
    monkeypatch.setenv("EXCHANGE_PUBLIC_BASE_URL", "https://app.uniway-tw.com")
    with TestClient(create_app(tmp_path)) as browser:
        home = BeautifulSoup(browser.get("/").text, "html.parser")
        entry = home.select_one('a[href="/guides"]')
        assert entry is not None
        response = browser.get(entry["href"])
        assert response.status_code == 200
        index = BeautifulSoup(response.text, "html.parser")
        paths = {link["href"] for link in index.select(".editorial-card > a")}
        assert paths == {"/guides/" + slug for slug in ARTICLES}
        for path in paths:
            response = browser.get(path)
            assert response.status_code == 200
            assert "noindex" not in response.headers.get("X-Robots-Tag", "")
            page = BeautifulSoup(response.text, "html.parser")
            assert page.select_one('link[rel="canonical"]')["href"] == "https://app.uniway-tw.com" + path
            assert browser.get(page.select_one(".article-illustration img")["src"]).status_code == 200
        assert browser.get("/static/seo-articles.css").status_code == 200
