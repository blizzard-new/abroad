from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exchange_info.models import PartnerProgramOption, PartnerUniversity
from exchange_info.seo import EDITORIAL_PATHS, SeoSettings, create_seo_router, partner_details, partner_id


def partner(**updates):
    values = dict(school_name="測試大學", country="日本", program_type="交換", source_url="https://www.cgu.edu.tw/test",
                  eligibility="GPA 3.0；語言 IELTS 6.5。", study_period="一學期", tuition_info="免繳合作校學費")
    return PartnerUniversity(**{**values, **updates})


def test_identical_program_option_is_removed_but_distinct_conditions_survive():
    p = partner()
    duplicate = PartnerProgramOption(**{k: v for k, v in p.model_dump().items() if k in PartnerProgramOption.model_fields})
    changed = duplicate.model_copy(update={"program_type": "另一方案", "eligibility": "GPA 3.5"})
    p = p.model_copy(update={"program_options": [duplicate, changed, changed]})
    html = partner_details(p)
    assert html.count("GPA 3.0") == 1
    assert html.count("GPA 3.5") == 1
    assert html.count("免繳合作校學費") == 1
    assert "另一方案：方案差異" in html


def test_mixed_quota_is_not_promoted_to_confirmed_current_seats():
    soup = BeautifulSoup(partner_details(partner(quota="2 2027 春梯次暫估 1 名（以一學期交換為原則）")), "html.parser")
    values = {dt.get_text(): dt.find_next_sibling("dd").get_text() for dt in soup.select("dt")}
    assert values["來源列載數字（年度與口徑待確認）"] == "2"
    assert values["來源中的目標梯次暫估（非核定）"].startswith("2027 春梯次暫估 1 名")
    assert values["當期名額確認狀態"] == "待確認"
    assert "不可相加" in values["名額閱讀提醒"]
    assert values["來源適用學年度"] == "來源未明確標示，待確認"


def test_source_provenance_survives_same_facts_in_different_program():
    p = partner()
    alternative = PartnerProgramOption(program_type=p.program_type, eligibility=p.eligibility, source_url="https://other.edu/program")
    html = partner_details(p.model_copy(update={"program_options": [alternative]}))
    assert "https://other.edu/program" in html and html.count("GPA 3.0") == 1


def test_topic_pages_are_crawlable_linked_and_specific_to_each_home():
    app = FastAPI()
    p = partner()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), lambda _: ([p], None)))
    with TestClient(app) as client:
        assert "全台大學交換學生" in client.get("/schools").text
        sitemap = client.get("/sitemaps/pages.xml").text
        for path in EDITORIAL_PATHS:
            assert "https://example.com" + path in sitemap
            response = client.get(path)
            soup = BeautifulSoup(response.text, "html.parser")
            assert response.status_code == 200 and len(soup.select("h1")) == 1
            assert soup.select_one('link[rel="canonical"]')["href"] == "https://example.com" + path
        country = client.get("/destinations/japan").text
        assert f"/schools/cgu/partners/{partner_id(p)}" in country
        assert f"/schools/ntu/partners/{partner_id(p)}" in country
        assert "生活費" in country and "不是當期名額" in country
        detail = client.get(f"/schools/cgu/partners/{partner_id(p)}").text
        assert "/destinations/japan" in detail and "/guides/exchange-budget" in detail
        assert "申請資格與語言" in detail and "研修期間與申請期限" in detail
        assert client.get("/destinations/unknown").status_code == 404
        assert client.get("/guides/unknown").status_code == 404


def test_long_text_is_split_without_changing_or_executing_source_content():
    html = partner_details(partner(eligibility="第一項。第二項；<script>alert(1)</script>"))
    soup = BeautifulSoup(html, "html.parser")
    assert not soup.select("script")
    assert soup.find("p", string="第一項。") and soup.find("p", string="第二項；")
    assert "<script>alert(1)</script>" in soup.get_text()


def test_cross_school_pages_render_short_and_long_quotas_for_all_homes(monkeypatch):
    from exchange_info import cross_school_partners, seo
    from exchange_info.university_registry import resolve_university

    homes = (resolve_university("cgu"), resolve_university("ntu"))
    quotas = {"cgu": "2", "ntu": "名額條件" * 97 + "名額"}
    monkeypatch.setattr(cross_school_partners, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(seo, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(cross_school_partners, "_ENTITY_INDEX_CACHE", {})

    def catalogue(home):
        return ([partner(school_name="範例大學 Example University", quota=quotas[home.id])], None)

    app = FastAPI()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), catalogue))
    with TestClient(app) as client:
        for home in homes:
            response = client.get(f"/partners/japan/example-university?home={home.id}")
            assert response.status_code == 200
            soup = BeautifulSoup(response.text, "html.parser")
            assert soup.select_one("#cs-quota-summary").get_text(strip=True) == quotas[home.id]
            assert soup.select_one('link[rel="canonical"]')["href"] == "https://example.com/partners/japan/example-university"
            assert soup.select_one("main h1")


def test_legacy_cross_school_id_redirects_only_to_unique_equivalent(monkeypatch):
    from exchange_info import cross_school_partners, seo
    from exchange_info.university_registry import resolve_university

    homes = (resolve_university("cgu"), resolve_university("ntu"))
    old = partner(school_name="測試大學", quota="2")
    current = partner(school_name="測試大學 Example University", quota="3")
    monkeypatch.setattr(cross_school_partners, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(seo, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(cross_school_partners, "_ENTITY_INDEX_CACHE", {})

    def catalogue(home):
        return ([old if home.id == "cgu" else current], None)

    app = FastAPI()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), catalogue))
    old_path = f"/partners/japan/inst-{partner_id(old)[:12]}"
    with TestClient(app) as client:
        response = client.get(old_path, params={"home": "cgu"}, follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/partners/japan/example-university?home=cgu"
        destination = client.get(response.headers["location"])
        soup = BeautifulSoup(destination.text, "html.parser")
        assert destination.status_code == 200
        assert soup.select_one("#cs-quota-summary").get_text(strip=True) == "2"
        assert soup.select_one('link[rel="canonical"]')["href"] == "https://example.com/partners/japan/example-university"
        assert client.get("/partners/japan/inst-ffffffffffff", follow_redirects=False).status_code == 404


def test_ambiguous_legacy_cross_school_id_is_not_guessed(monkeypatch):
    from exchange_info import cross_school_partners as cross

    common = dict(country_slug="japan", country_name_zh="日本", school_name_zh="測試大學", school_name_en="Example University")
    first_row, second_row = partner(school_name="First"), partner(school_name="Second")
    first = cross.AggregatedPartnerEntity(**common, institution_slug="first", home_rows={"cgu": [first_row]})
    second = cross.AggregatedPartnerEntity(**common, institution_slug="second", home_rows={"ntu": [second_row]})
    monkeypatch.setattr(cross, "_legacy_partner_id", lambda row: "123456789abc" + ("0" * 8 if row.school_name == "First" else "1" * 8))
    monkeypatch.setattr(cross, "build_cross_school_entity_index", lambda _, **_kw: ({("japan", "first"): first, ("japan", "second"): second}, {}))
    assert cross.build_cross_school_partner_page_data(
        country="japan", institution="inst-123456789abc", selected_home=None, catalogue_loader=lambda _: ([], None)
    ) is None


def test_canonical_cross_school_slug_takes_precedence_over_another_entity_alias(monkeypatch):
    from exchange_info import cross_school_partners as cross
    from exchange_info.university_registry import resolve_university

    home = resolve_university("cgu")
    first = cross.AggregatedPartnerEntity(
        country_slug="japan", country_name_zh="日本", institution_slug="example",
        school_name_zh="第一所大學", school_name_en="First University",
        home_rows={home.id: [partner(school_name="第一所大學 First University", quota="2")]},
    )
    second = cross.AggregatedPartnerEntity(
        country_slug="japan", country_name_zh="日本", institution_slug="example-2",
        school_name_zh="第二所大學", school_name_en="Second University",
        home_rows={home.id: [partner(school_name="第二所大學 Second University", quota="3")]},
    )
    monkeypatch.setattr(cross, "SUPPORTED_UNIVERSITIES", (home,))
    monkeypatch.setattr(cross, "build_cross_school_entity_index", lambda _, **_kw: (
        {("japan", "example"): first, ("japan", "example-2"): second},
        {("japan", "example"): ("japan", "example-2")},
    ))
    page_data = cross.build_cross_school_partner_page_data(
        country="japan", institution="example", selected_home="cgu", catalogue_loader=lambda _: ([], None)
    )
    assert page_data is not None
    assert page_data.canonical_path == "/partners/japan/example"
    assert page_data.school_name_en == "First University"


def test_cross_school_public_pages_and_sitemap_do_not_hide_catalogue_failure(monkeypatch):
    from fastapi import HTTPException
    from exchange_info import cross_school_partners, seo
    from exchange_info.university_registry import resolve_university

    homes = (resolve_university("cgu"), resolve_university("ntu"))
    monkeypatch.setattr(cross_school_partners, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(seo, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(cross_school_partners, "_ENTITY_INDEX_CACHE", {})

    def catalogue(home):
        if home.id == "ntu":
            raise HTTPException(503, "source unavailable", headers={"Retry-After": "60"})
        return [partner(school_name="測試大學 Example University")], None

    app = FastAPI()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), catalogue))
    with TestClient(app) as client:
        for path in ("/partners", "/partners/japan", "/partners/japan/example-university", "/sitemaps/partners.xml"):
            response = client.get(path)
            assert response.status_code == 503
            assert response.headers["Retry-After"] == "60"


def test_expanded_country_slugs_eliminate_legacy_hash_countries_and_redirect_old_country_paths(monkeypatch):
    import hashlib
    from exchange_info import cross_school_partners, seo
    from exchange_info.cross_school_partners import COUNTRY_SLUGS, resolve_country_slug_and_zh
    from exchange_info.university_registry import resolve_university

    expected_countries = {
        "智利": ("chile", "智利"),
        "以色列": ("israel", "以色列"),
        "澳門": ("macau", "澳門"),
        "冰島": ("iceland", "冰島"),
        "愛沙尼亞": ("estonia", "愛沙尼亞"),
        "阿拉伯聯合大公國": ("united-arab-emirates", "阿拉伯聯合大公國"),
        "希臘": ("greece", "希臘"),
        "秘魯": ("peru", "秘魯"),
        "巴基斯坦": ("pakistan", "巴基斯坦"),
        "烏茲別克": ("uzbekistan", "烏茲別克"),
        "哥倫比亞": ("colombia", "哥倫比亞"),
        "斯洛維尼亞": ("slovenia", "斯洛維尼亞"),
        "南非": ("south-africa", "南非"),
        "克羅埃西亞": ("croatia", "克羅埃西亞"),
        "埃及": ("egypt", "埃及"),
        "烏克蘭": ("ukraine", "烏克蘭"),
        "盧森堡": ("luxembourg", "盧森堡"),
        "俄羅斯聯邦": ("russia", "俄羅斯"),
        "斯洛法克": ("slovakia", "斯洛伐克"),
        "列支敦斯登": ("liechtenstein", "列支敦士登"),
    }
    for raw_country, expected in expected_countries.items():
        assert resolve_country_slug_and_zh(raw_country) == expected
        legacy_country_hash = f"inst-{hashlib.sha256(raw_country.encode('utf-8')).hexdigest()[:12]}"
        assert resolve_country_slug_and_zh(legacy_country_hash) == expected

    for zh, slug in COUNTRY_SLUGS.items():
        assert not slug.startswith("inst-"), f"{zh} still maps to {slug}"

    homes = (resolve_university("cgu"), resolve_university("ntu"))
    monkeypatch.setattr(cross_school_partners, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(seo, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(cross_school_partners, "_ENTITY_INDEX_CACHE", {})

    rows = [
        partner(country="愛沙尼亞", school_name="塔林大學 Tallinn University"),
        partner(country="澳門", school_name="澳門大學"),
        partner(country="智利", school_name="智利大學 Universidad de Chile"),
        partner(country="俄羅斯聯邦", school_name="聖彼得堡國立大學 Saint Petersburg State University"),
        partner(country="斯洛法克", school_name="布拉提斯拉瓦經濟大學 University of Economics in Bratislava"),
    ]

    app = FastAPI()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), lambda _: (rows, None)))
    macau_inst_slug = f"inst-{partner_id(rows[1])[:12]}"
    estonia_legacy_country = f"inst-{hashlib.sha256('愛沙尼亞'.encode('utf-8')).hexdigest()[:12]}"
    macau_legacy_country = f"inst-{hashlib.sha256('澳門'.encode('utf-8')).hexdigest()[:12]}"

    with TestClient(app) as client:
        sitemap_xml = client.get("/sitemaps/partners.xml").text
        assert "/partners/inst-" not in sitemap_xml
        assert "https://example.com/partners/estonia/tallinn-university" in sitemap_xml
        assert f"https://example.com/partners/macau/{macau_inst_slug}" in sitemap_xml
        assert "https://example.com/partners/chile/universidad-de-chile" in sitemap_xml
        assert "https://example.com/partners/russia/saint-petersburg-state-university" in sitemap_xml
        assert "https://example.com/partners/slovakia/university-of-economics-in-bratislava" in sitemap_xml

        country_redirect = client.get(f"/partners/{estonia_legacy_country}", follow_redirects=False)
        assert country_redirect.status_code == 301
        assert country_redirect.headers["location"] == "/partners/estonia"

        inst_redirect = client.get(
            f"/partners/{estonia_legacy_country}/tallinn-university",
            params={"home": "cgu"},
            follow_redirects=False,
        )
        assert inst_redirect.status_code == 301
        assert inst_redirect.headers["location"] == "/partners/estonia/tallinn-university?home=cgu"

        macau_redirect = client.get(
            f"/partners/{macau_legacy_country}/{macau_inst_slug}",
            follow_redirects=False,
        )
        assert macau_redirect.status_code == 301
        assert macau_redirect.headers["location"] == f"/partners/macau/{macau_inst_slug}"
        assert client.get(macau_redirect.headers["location"], follow_redirects=False).status_code == 200

        assert client.get("/partners/inst-ffffffffffff", follow_redirects=False).status_code == 404
        assert client.get("/partners/inst-ffffffffffff/tallinn-university", follow_redirects=False).status_code == 404


def test_school_partner_page_links_to_canonical_cross_school_slug_and_redirects_20hex_alias(monkeypatch):
    from exchange_info import cross_school_partners, seo
    from exchange_info.university_registry import resolve_university

    homes = (resolve_university("cgu"), resolve_university("ntu"))
    row = partner(country="大陸地區", school_name="復旦大學 Fudan University", quota="2")
    key_20hex = partner_id(row)
    monkeypatch.setattr(cross_school_partners, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(seo, "SUPPORTED_UNIVERSITIES", homes)
    monkeypatch.setattr(cross_school_partners, "_ENTITY_INDEX_CACHE", {})

    app = FastAPI()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), lambda _: ([row], None)))
    with TestClient(app) as client:
        school_page = client.get(f"/schools/cgu/partners/{key_20hex}")
        assert school_page.status_code == 200
        soup = BeautifulSoup(school_page.text, "html.parser")
        cross_links = [a["href"] for a in soup.select('a[href^="/partners/"]')]
        assert cross_links == [
            "/partners/mainland-china/fudan-university",
            "/partners/mainland-china/fudan-university",
        ]
        assert f"/partners/mainland-china/{key_20hex}" not in school_page.text

        redirect_with_home = client.get(
            f"/partners/mainland-china/{key_20hex}",
            params={"home": "cgu"},
            follow_redirects=False,
        )
        assert redirect_with_home.status_code == 301
        assert redirect_with_home.headers["location"] == "/partners/mainland-china/fudan-university?home=cgu"

        redirect_plain = client.get(
            f"/partners/mainland-china/{key_20hex}",
            follow_redirects=False,
        )
        assert redirect_plain.status_code == 301
        assert redirect_plain.headers["location"] == "/partners/mainland-china/fudan-university"

        assert client.get("/partners/mainland-china/" + ("f" * 20), follow_redirects=False).status_code == 404
