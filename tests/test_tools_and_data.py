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


def test_main_page_exposes_prominent_tools_and_data_entries(client):
    home = client.get("/")
    assert home.status_code == 200
    soup = BeautifulSoup(home.text, "html.parser")

    nav_routes = [a.get("data-public-route") for a in soup.select(".uniway-public-nav a[data-public-route]")]
    assert "tools" in nav_routes and "data" in nav_routes
    assert soup.select_one('.uniway-public-nav a[href="/tools"]') is not None
    assert soup.select_one('.uniway-public-nav a[href="/data"]') is not None

    hero_hrefs = {a.get("href") for a in soup.select(".pr-hero-tools a[href]")}
    assert {"/tools", "/data"} <= hero_hrefs

    section = soup.select_one("#home-free-tools")
    assert section is not None
    section_hrefs = {a.get("href") for a in section.select("a[href]")}
    expected_paths = {
        "/tools",
        "/tools/ects-credit-converter",
        "/tools/gpa-converter",
        "/tools/language-score-converter",
        "/tools/partner-compare",
        "/tools/exchange-budget-calculator",
        "/tools/scholarship-finder",
        "/tools/timeline-generator",
        "/tools/military-service-exit-checker",
        "/data",
        "/data/taiwan-exchange-overview",
        "/data/deadlines",
        "/data/language-requirements",
        "/data/top-partner-universities",
    }
    assert expected_paths <= section_hrefs


def test_wave2_tools_data_destinations_and_og_image(client):
    from pathlib import Path
    from PIL import Image
    from exchange_info.seo_guides import COUNTRIES

    # 1. Verify 1200x630 og:image static asset and Open Graph / Twitter tags on /, /tools, /data
    og_file = Path("src/exchange_info/static/assets/brand/og-image.png")
    assert og_file.is_file()
    with Image.open(og_file) as img:
        assert img.size == (1200, 630)
    assert client.get("/static/assets/brand/og-image.png").status_code == 200
    for check_path in ("/", "/tools", "/data", "/tools/partner-compare", "/data/top-partner-universities"):
        doc = BeautifulSoup(client.get(check_path).text, "html.parser")
        assert doc.select_one('meta[property="og:image"]')["content"] == "https://app.uniway-tw.com/static/assets/brand/og-image.png"
        assert doc.select_one('meta[property="og:image:width"]')["content"] == "1200"
        assert doc.select_one('meta[property="og:image:height"]')["content"] == "630"
        assert doc.select_one('meta[name="twitter:card"]')["content"] == "summary_large_image"

    # 2. Verify /tools/partner-compare SSR + .json live endpoint
    pk = client.get("/tools/partner-compare?home=ntu")
    assert pk.status_code == 200
    pk_soup = BeautifulSoup(pk.text, "html.parser")
    assert len(pk_soup.select("#pk-compare-thead th")) == 3  # 比較維度 + 2 default partner columns
    pk_json = client.get("/tools/partner-compare.json?home=nccu")
    assert pk_json.status_code == 200
    assert "noindex" in pk_json.headers.get("X-Robots-Tag", "")
    pk_data = pk_json.json()
    assert pk_data["home_id"] == "nccu" and pk_data["total_options"] > 50 and len(pk_data["selected"]) == 2

    # 3. Verify /tools/military-service-exit-checker SSR + .ics export
    mil_long = client.get("/tools/military-service-exit-checker?status=draft_male&depart=2027-08-25&return_date=2028-01-20&school=ntu")
    assert mil_long.status_code == 200
    assert "超過 4 個月" in mil_long.text
    assert "學校推薦出國交換" in mil_long.text
    mil_ics = client.get("/tools/military-service-exit-checker.ics?status=draft_male&depart=2027-08-25&return_date=2028-01-20&school=ntu")
    assert mil_ics.status_code == 200
    assert mil_ics.headers["content-type"].startswith("text/calendar")
    assert "BEGIN:VCALENDAR\r\n" in mil_ics.text and mil_ics.text.count("BEGIN:VEVENT") == 6

    # 4. Verify /tools/scholarship-finder accurate eligibility filtering
    schol_intl = client.get("/tools/scholarship-finder?home=nthu&region=japan&identity=international_student&duration=semester")
    assert schol_intl.status_code == 200
    schol_soup = BeautifulSoup(schol_intl.text, "html.parser")
    matched_ids = {r["data-schol-id"] for r in schol_soup.select("#schol-matched-tbody tr[data-schol-id]")}
    assert "jasso" in matched_ids
    assert "moe-feiyang" not in matched_ids and "moe-xizhu" not in matched_ids  # Excluded for non-ROC household registration
    excluded_text = schol_soup.select_one("#schol-excluded-tbody").get_text()
    assert "學海飛颺" in excluded_text

    # 5. Verify /data/language-requirements & /data/top-partner-universities real DB stats
    lang_survey = client.get("/data/language-requirements?test=toeic")
    assert lang_survey.status_code == 200
    ls_rows = BeautifulSoup(lang_survey.text, "html.parser").select("#lang-survey-tbody tr")
    assert len(ls_rows) == 4 and all(r["data-lang-tier-test"] == "toeic" for r in ls_rows)

    top50 = client.get("/data/top-partner-universities")
    assert top50.status_code == 200
    top_rows = BeautifulSoup(top50.text, "html.parser").select("#top-partners-tbody tr[data-top-name]")
    assert len(top_rows) == 50

    # 6. Verify all 8 /destinations pages (existing 3 + new 5: France, UK, US, Netherlands, Czechia)
    expected_dest_slugs = {"japan", "south-korea", "germany", "france", "united-kingdom", "united-states", "netherlands", "czechia"}
    assert set(COUNTRIES.keys()) == expected_dest_slugs
    dest_index = client.get("/destinations")
    assert dest_index.status_code == 200
    for slug in ("france", "united-kingdom", "united-states", "netherlands", "czechia"):
        assert f'/destinations/{slug}' in dest_index.text
        d_resp = client.get(f"/destinations/{slug}")
        assert d_resp.status_code == 200
        d_soup = BeautifulSoup(d_resp.text, "html.parser")
        assert len(d_soup.select("h1")) == 1
        assert d_soup.select_one('a[href^="/schools/"]') is not None
        d_text = d_soup.get_text(" ", strip=True)
        for forbidden in FORBIDDEN_TERMS:
            assert forbidden not in d_text


