from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.cross_school_partners import (
    validate_cross_school_partner_compliance,
)
from exchange_info.models import CrossSchoolPartnerPageData


def _client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("EXCHANGE_PUBLIC_BASE_URL", "https://uniway.example")
    monkeypatch.setenv("EXCHANGE_SEO_INDEXABLE", "1")
    return TestClient(create_app(data_dir=tmp_path, seo_state_dir=tmp_path / "seo"))


def test_cross_school_partner_data_and_copyright_compliance(monkeypatch, tmp_path) -> None:
    client = _client(monkeypatch, tmp_path)

    dir_res = client.get("/cross-school-partners?limit=50")
    assert dir_res.status_code == 200
    directory = dir_res.json()
    assert directory["total_partner_count"] >= 10
    assert directory["multi_school_partner_count"] >= 3
    assert len(directory["countries"]) >= 3
    slugs = {(item["country_slug"], item["institution_slug"]) for item in directory["items"]}
    assert ("germany", "technical-university-of-munich") in slugs
    assert ("japan", "waseda-university") in slugs

    for country_slug, inst_slug in [
        ("germany", "technical-university-of-munich"),
        ("japan", "waseda-university"),
        ("germany", "lmu-munich"),
    ]:
        res = client.get(f"/cross-school-partners/{country_slug}/{inst_slug}?home=ntu")
        assert res.status_code == 200
        page = CrossSchoolPartnerPageData.model_validate(res.json())
        assert page.canonical_path == f"/partners/{country_slug}/{inst_slug}"
        assert page.contracted_home_count >= 2
        assert len(page.contracted_home_schools) >= 2
        assert len(page.all_home_agreements) >= 18
        assert len(page.living_cost_references) >= 1
        assert len(page.housing_references) >= 1
        assert len(page.course_direction_references) >= 1
        # Some schools have no matched student report. Generated preparation
        # advice must not satisfy the experience count.
        assert page.experience_digests == []

        violations = validate_cross_school_partner_compliance(page)
        assert violations == [], f"Unexpected compliance violations for {inst_slug}: {violations}"


def test_cross_school_partner_upper_layer_switches_home_university(monkeypatch, tmp_path) -> None:
    client = _client(monkeypatch, tmp_path)

    tum_ntu_res = client.get("/cross-school-partners/germany/technical-university-of-munich?home=ntu")
    assert tum_ntu_res.status_code == 200
    tum_ntu = CrossSchoolPartnerPageData.model_validate(tum_ntu_res.json())
    assert tum_ntu.selected_home_id == "ntu"
    ntu_agreement = tum_ntu.selected_home_agreement
    assert ntu_agreement.home_id == "ntu"
    assert ntu_agreement.deadline_source_url.startswith("https://")
    assert len(ntu_agreement.deadline_last_checked_at) == 10
    assert ntu_agreement.internal_online_deadline
    assert ntu_agreement.study_plan_limit

    tum_cgu_res = client.get("/cross-school-partners/德國/慕尼黑工業大學?home=長庚大學")
    assert tum_cgu_res.status_code == 200
    tum_cgu = CrossSchoolPartnerPageData.model_validate(tum_cgu_res.json())
    assert tum_cgu.canonical_path == "/partners/germany/technical-university-of-munich"
    assert tum_cgu.selected_home_id == "cgu"
    assert tum_cgu.selected_home_agreement.home_id == "cgu"


def test_cross_school_partner_html_two_layer_structure_and_seo(monkeypatch, tmp_path) -> None:
    client = _client(monkeypatch, tmp_path)

    # 1. Directory page /partners
    directory_res = client.get("/partners")
    assert directory_res.status_code == 200
    assert "X-Robots-Tag" not in directory_res.headers
    dir_soup = BeautifulSoup(directory_res.text, "html.parser")
    assert dir_soup.find("h1") is not None
    assert "跨校外國合作大學總覽" in dir_soup.find("h1").get_text()
    assert dir_soup.find("a", href="/partners/germany/technical-university-of-munich") is not None
    assert dir_soup.find("a", href="/partners/japan/waseda-university") is not None

    # 2. Country directory page /partners/germany
    country_res = client.get("/partners/germany")
    assert country_res.status_code == 200
    country_soup = BeautifulSoup(country_res.text, "html.parser")
    assert "德國" in country_soup.find("h1").get_text()
    assert country_soup.find("a", href="/partners/germany/technical-university-of-munich") is not None

    # 3. Cross-school partner page /partners/germany/technical-university-of-munich
    tum_res = client.get("/partners/germany/technical-university-of-munich?home=ntu")
    assert tum_res.status_code == 200
    assert "X-Robots-Tag" not in tum_res.headers
    soup = BeautifulSoup(tum_res.text, "html.parser")

    # Canonical always points to clean /partners/germany/technical-university-of-munich
    canonical = soup.find("link", rel="canonical")
    assert canonical is not None
    assert canonical["href"] == "https://uniway.example/partners/germany/technical-university-of-munich"

    # Upper layer (上半部 · 母校規則層)
    upper = soup.find(id="home-rule-layer")
    assert upper is not None
    assert "上半部 · 母校規則層" in upper.get_text()
    active_pill = upper.find("a", attrs={"data-home-switch": "ntu"})
    assert active_pill is not None
    assert "is-active" in active_pill.get("class", [])
    assert upper.find(id="cs-quota-summary") is not None
    assert upper.find(id="cs-language-summary") is not None
    assert upper.find(id="cs-online-deadline") is not None
    assert upper.find(id="cs-paper-deadline") is not None
    assert upper.find(id="cs-study-plan-limit") is not None
    assert upper.find(id="cs-deadline-source-link")["href"].startswith("https://")

    # Conversion hooks (註冊誘因)
    btn_compare = upper.find(id="cs-btn-save-compare")
    btn_draft = upper.find(id="cs-btn-save-draft")
    assert btn_compare is not None
    assert btn_draft is not None
    assert "#partners" in btn_compare["href"]
    assert "#documents" in btn_draft["href"]

    # Lower layer (下半部 · 全台跨校情報層)
    lower = soup.find(id="cross-school-intelligence-layer")
    assert lower is not None
    assert "下半部 · 全台跨校情報層" in lower.get_text()
    assert lower.find(id="cross-school-living-cost") is not None
    assert lower.find(id="cross-school-housing") is not None
    assert lower.find(id="cross-school-courses") is not None
    assert lower.find(id="cross-school-experiences") is not None
    assert lower.find(id="cross-school-contracted-universities") is not None
    assert lower.find("blockquote") is None

    # Every structured source link in lower layer uses https:// or http://
    source_links = lower.select(".cs-intel-source a[data-official-source]")
    assert len(source_links) >= 3
    experiences = lower.find(id="cross-school-experiences")
    assert "尚未收錄可對應本校的資料" in experiences.get_text()
    assert experiences.select(".cs-intel-source a") == []
    for source_link in source_links:
        assert source_link["href"].startswith(("https://", "http://"))

    # Embedded JSON for client-side home switcher and external CSP-safe script
    data_script = soup.find("script", id="cs-home-agreements-data")
    assert data_script is not None
    payload = json.loads(data_script.string)
    assert "ntu" in payload
    assert "nccu" in payload
    assert soup.find("script", src=lambda s: s and s.startswith("/static/partner-page.js")) is not None

    # Chinese path resolves to the same canonical entity
    zh_res = client.get("/partners/日本/早稻田大學?home=nccu")
    assert zh_res.status_code == 200
    zh_soup = BeautifulSoup(zh_res.text, "html.parser")
    assert (
        zh_soup.find("link", rel="canonical")["href"]
        == "https://uniway.example/partners/japan/waseda-university"
    )
    assert "早稻田大學" in zh_soup.find("h1").get_text()


def test_cross_school_partner_sitemap_and_json_api(monkeypatch, tmp_path) -> None:
    client = _client(monkeypatch, tmp_path)

    # Pages sitemap includes /partners
    pages_xml = client.get("/sitemaps/pages.xml")
    assert pages_xml.status_code == 200
    assert "https://uniway.example/partners" in pages_xml.text

    # Dedicated cross-school partners sitemap
    partners_xml = client.get("/sitemaps/partners.xml")
    assert partners_xml.status_code == 200
    root = ET.fromstring(partners_xml.text)
    locs = {
        el.text
        for el in root.findall(
            "{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        )
    }
    assert "https://uniway.example/partners/germany/technical-university-of-munich" in locs
    assert "https://uniway.example/partners/japan/waseda-university" in locs

    # JSON API endpoints
    api_dir = client.get("/cross-school-partners?country=germany&limit=20")
    assert api_dir.status_code == 200
    dir_json = api_dir.json()
    assert dir_json["total_partner_count"] >= 1
    assert any(
        item["institution_slug"] == "technical-university-of-munich"
        for item in dir_json["items"]
    )

    api_page = client.get("/cross-school-partners/japan/waseda-university?home=ntnu")
    assert api_page.status_code == 200
    page_json = api_page.json()
    assert page_json["institution_slug"] == "waseda-university"
    assert page_json["selected_home_id"] == "ntnu"
    assert page_json["contracted_home_count"] >= 2

    for home_id in ("nkust", "yuntech", "ntou"):
        res = client.get(f"/cross-school-partners/japan/waseda-university?home={home_id}")
        assert res.status_code == 200
        assert res.json()["selected_home_id"] == home_id


def test_build_home_agreement_normalizes_single_char_quota_and_language_fields() -> None:
    from exchange_info.cross_school_partners import _build_home_agreement
    from exchange_info.models import PartnerUniversity
    from exchange_info.university_registry import NKUST

    row = PartnerUniversity(
        country="大陸地區",
        school_name="重慶大學 (Chongqing University)",
        program_type="交換學生",
        quota="4",
        language_requirement="無",
        eligibility="無",
        availability_status="open",
        source_url="https://oia.nkust.edu.tw/unit-4-374-21.html",
    )
    agreement = _build_home_agreement(NKUST, [row])
    assert agreement.home_id == "nkust"
    assert agreement.quota_summary == "4"
    assert agreement.language_requirement_summary == "無"
    assert agreement.eligibility_summary == "無"
