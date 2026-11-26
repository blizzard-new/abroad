from __future__ import annotations

import json
from xml.etree import ElementTree

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.cgu_catalogue import CguCatalogue
from exchange_info.tools_and_data_core import (
    FORBIDDEN_TERMS,
    MANDATORY_DISCLAIMER,
    WAVE1_PATHS,
    WAVE1_SPECS,
    bavarian_formula,
)
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("EXCHANGE_SEO_INDEXABLE", "true")
        patch.setenv("EXCHANGE_PUBLIC_BASE_URL", "https://app.uniway-tw.com")
        original_view = CguCatalogue.view
        patch.setattr(CguCatalogue, "view", lambda self, **_: original_view(self, refresh=False))
        app = create_app(tmp_path_factory.mktemp("tools-data-seo"))
        with TestClient(app, base_url="http://internal.invalid") as browser:
            yield browser


@pytest.mark.parametrize("path", WAVE1_PATHS)
def test_wave1_pages_render_without_js_with_valid_jsonld_citation_and_compliance(client, path):
    spec = WAVE1_SPECS[path]
    response = client.get(path)
    assert response.status_code == 200
    assert client.head(path).status_code == 200
    assert "noindex" not in response.headers.get("X-Robots-Tag", "")

    soup = BeautifulSoup(response.text, "html.parser")
    assert soup.select_one('link[rel="canonical"]')["href"] == f"https://app.uniway-tw.com{path}"
    assert 'content="index, follow' in response.text

    # Single H1 and navigation entries
    h1s = soup.select("h1")
    assert len(h1s) == 1
    assert spec.h1 in h1s[0].get_text()
    assert soup.select_one('nav[aria-label="主導覽"] a[href="/tools"]')
    assert soup.select_one('nav[aria-label="主導覽"] a[href="/data"]')

    # Core 40-60 character conclusion + one-click citation box with app.uniway-tw.com URL
    conclusion_el = soup.select_one("[data-core-conclusion]")
    assert conclusion_el is not None
    conclusion_text = conclusion_el.get_text(strip=True)
    assert 40 <= len(conclusion_text) <= 60
    cite_el = soup.select_one("#uw-citation-code")
    assert cite_el is not None
    assert f"https://app.uniway-tw.com{path}" in cite_el.get_text()

    # SSR tables & 3-5 FAQs for no-JS crawlers
    tables = soup.select("main table")
    assert len(tables) >= 1
    for table in tables:
        assert table.find("caption") is not None
        assert len(table.select('th[scope="col"]')) >= 2
    faqs = soup.select("details.uw-faq-item")
    assert 3 <= len(faqs) <= 5

    # Structured data validation
    ld_scripts = soup.select('script[type="application/ld+json"]')
    assert len(ld_scripts) >= 3
    parsed_types = set()
    for node in ld_scripts:
        payload = json.loads(node.string)
        parsed_types.add(payload["@type"])
    expected_primary = "WebApplication" if path.startswith("/tools") else "Dataset"
    assert {"BreadcrumbList", "FAQPage", expected_primary} <= parsed_types

    # Strict CSP compliance: no inline executable scripts, no javascript: links
    exec_scripts = [
        s.get("src", "").split("?")[0]
        for s in soup.select('script:not([type="application/ld+json"]):not([type="application/json"])')
    ]
    assert all(src.startswith("/static/") for src in exec_scripts)
    assert not soup.select('a[href^="javascript:"]')

    # Mandatory disclaimer & zero forbidden words / AI clichés
    full_text = soup.get_text(" ", strip=True)
    assert MANDATORY_DISCLAIMER in full_text
    for forbidden in FORBIDDEN_TERMS:
        assert forbidden not in full_text, f"Forbidden term {forbidden!r} found on {path}"
    assert full_text.count("——") <= 1


def test_sitemap_and_llms_txt_include_all_wave1_urls(client):
    sitemap_resp = client.get("/sitemaps/pages.xml")
    assert sitemap_resp.status_code == 200
    root = ElementTree.fromstring(sitemap_resp.content)
    locs = {node.text for node in root.findall(".//{*}loc")}
    for path in WAVE1_PATHS:
        assert f"https://app.uniway-tw.com{path}" in locs

    llms_resp = client.get("/llms.txt")
    assert llms_resp.status_code == 200
    for path in WAVE1_PATHS:
        assert f"https://app.uniway-tw.com{path}" in llms_resp.text


def test_ects_gpa_and_budget_ssr_calculations(client):
    ects = client.get("/tools/ects-credit-converter?amount=24&system=ects&ratio=2.0&min_tw=9")
    assert ects.status_code == 200
    assert "12 學分" in ects.text
    assert "18 ECTS" in ects.text

    assert bavarian_formula(82.5, 100.0, 60.0) == 2.3
    assert bavarian_formula(100.0, 100.0, 60.0) == 1.0
    assert bavarian_formula(60.0, 100.0, 60.0) == 4.0
    assert bavarian_formula(55.0, 100.0, 60.0) is None
    gpa = client.get("/tools/gpa-converter?value=82.5&scale=percent&max_score=100&min_pass=60")
    assert gpa.status_code == 200
    assert "3.70 / 4.3" in gpa.text
    assert "2.3" in gpa.text

    budget = client.get("/tools/exchange-budget-calculator?country=germany&months=5&scholarship=50000")
    assert budget.status_code == 200
    assert "匯率 -10%" in budget.text and "匯率 +10%" in budget.text
    assert "EUR 1,000" in budget.text


def test_language_converter_links_real_partner_database(client):
    page = client.get("/tools/language-score-converter?home=scu&test=jlpt&score=N2")
    assert page.status_code == 200
    soup = BeautifulSoup(page.text, "html.parser")
    assert "東吳大學" in soup.get_text()
    partner_links = [a["href"] for a in soup.select('#lang-direct-list a[href^="/schools/scu/partners/"]')]
    assert len(partner_links) >= 1

    api_resp = client.get("/tools/language-score-converter.json?home=nccu&test=ielts&score=6.5")
    assert api_resp.status_code == 200
    assert "noindex" in api_resp.headers.get("X-Robots-Tag", "")
    data = api_resp.json()
    assert data["match"]["home_id"] == "nccu"
    assert data["match"]["total_partner_pages"] > 100
    assert data["match"]["direct_match_count"] > 0


def test_timeline_generator_and_valid_ics_export(client):
    page = client.get("/tools/timeline-generator?school=cgu&term=2027-fall")
    assert page.status_code == 200
    assert "長庚大學" in page.text
    assert "/tools/timeline-generator.ics?" in page.text

    ics = client.get("/tools/timeline-generator.ics?school=cgu&term=2027-fall&deadline=2026-12-21")
    assert ics.status_code == 200
    assert ics.headers["content-type"].startswith("text/calendar")
    assert "noindex" in ics.headers.get("X-Robots-Tag", "")
    raw = ics.text
    assert raw.startswith("BEGIN:VCALENDAR\r\n")
    assert raw.endswith("END:VCALENDAR\r\n")
    assert raw.count("BEGIN:VEVENT") == 8
    assert "BEGIN:VALARM" in raw
    assert "實際資格、名額與期限以各校最新官方公告為準" in raw


def test_data_pages_reflect_all_71_universities_and_filters(client):
    overview = client.get("/data/taiwan-exchange-overview")
    assert overview.status_code == 200
    soup = BeautifulSoup(overview.text, "html.parser")
    rows = soup.select("#overview-tbody tr[data-row-name]")
    assert len(rows) == len(SUPPORTED_UNIVERSITIES) == 71

    pub = client.get("/data/taiwan-exchange-overview?sector=public&sort=countries")
    pub_soup = BeautifulSoup(pub.text, "html.parser")
    pub_rows = pub_soup.select("#overview-tbody tr[data-row-name]")
    assert 0 < len(pub_rows) < 71
    assert all(r["data-row-sector"] == "公立" for r in pub_rows)

    deadlines = client.get("/data/deadlines")
    assert deadlines.status_code == 200
    dl_soup = BeautifulSoup(deadlines.text, "html.parser")
    dl_rows = dl_soup.select("#deadlines-tbody tr[data-dl-name]")
    assert len(dl_rows) == 71

    nov = client.get("/data/deadlines?month=11")
    nov_soup = BeautifulSoup(nov.text, "html.parser")
    nov_rows = nov_soup.select("#deadlines-tbody tr[data-dl-name]")
    assert 1 <= len(nov_rows) < 71
    assert all("11" in r["data-dl-months"].split(",") for r in nov_rows)


def test_tools_and_data_do_not_access_private_sessions(client, monkeypatch):
    def forbid_session(*_a, **_kw):
        pytest.fail("Public tools/data routes must never read user sessions")

    monkeypatch.setattr(client.app.state.account_repository, "find_session_by_token_hash", forbid_session)
    anon = client.get("/tools/gpa-converter").content
    with_cookie = client.get("/tools/gpa-converter", headers={"Cookie": "exchange_session=fake-token"})
    assert with_cookie.content == anon
