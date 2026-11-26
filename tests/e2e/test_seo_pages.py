"""The public catalogue is usable on phones and without JavaScript."""
from urllib.parse import parse_qs, unquote, urlsplit

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site


def test_home_keeps_its_search_title_after_javascript_boots(page, live_server):
    enter_public_site(page, live_server, "home")
    expect(page).to_have_title("UniWay｜交換學生申請、合作學校與選校資訊")
    expect(page.locator('.pr-footer-links a[href="/schools"]')).to_be_visible()
    for container in (".pr-hero-socials", ".pr-social-banner", ".pr-footer-socials"):
        expect(page.locator(f'{container} a[href="https://www.instagram.com/uniway.tw/"]')).to_be_visible()
        expect(page.locator(f'{container} a[href="https://www.threads.com/@uniway.tw"]')).to_be_visible()


@pytest.mark.parametrize("width", [390, 1440])
def test_homepage_heading_and_partner_switcher_visuals(browser, live_server, width, tmp_path):
    context = browser.new_context(viewport={"width": width, "height": 900})
    try:
        page = context.new_page()
        enter_public_site(page, live_server, "home")
        expect(page.locator("#home-landing-title")).to_be_visible()
        assert page.locator("h1").all_text_contents() == [page.locator("#home-landing-title").text_content()]
        page.screenshot(path=str(tmp_path / f"homepage-{width}.png"), animations="disabled")
    finally:
        context.close()

    context = browser.new_context(java_script_enabled=False, viewport={"width": width, "height": 900})
    try:
        page = context.new_page()
        response = page.goto(live_server.base_url + "/partners/japan/waseda-university?home=ntu", timeout=120000)
        assert response.ok
        expect(page.get_by_role("heading", level=1)).to_contain_text("早稻田大學")
        expect(page.locator("#cs-home-badge")).to_have_text("國立臺灣大學")
        page.locator("#partner-home-switcher").select_option("nccu")
        page.get_by_role("button", name="查看所選母校").click()
        expect(page.locator("#cs-home-badge")).to_have_text("國立政治大學")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(tmp_path / f"waseda-{width}.png"), animations="disabled")
    finally:
        context.close()


@pytest.mark.parametrize("width", [390, 1280])
def test_catalogue_navigation_without_javascript(browser, live_server, width, tmp_path):
    context = browser.new_context(java_script_enabled=False, viewport={"width": width, "height": 900})
    try:
        page = context.new_page()
        response = page.goto(live_server.base_url + "/schools")
        assert response.status == 200
        expect(page.get_by_role("heading", level=1)).to_contain_text("交換學生")
        page.locator('.cards a[href="/schools/cgu"]').click()
        expect(page.get_by_role("heading", level=1)).to_contain_text("長庚大學")
        page.locator(".cards a").filter(has_text="Lincoln University").click()
        expect(page.get_by_role("heading", level=1)).to_contain_text("Lincoln University")
        expect(page.get_by_text("IELTS 6.0；須先通過校內甄選。", exact=True)).to_be_visible()
        expect(page.get_by_role("link", name="母校合作校／名額資料來源")).to_be_visible()
        href = page.get_by_role("link", name="在 UniWay 查看學校與規劃申請").get_attribute("href")
        assert parse_qs(urlsplit(href).query)["home"] == ["長庚大學"]
        assert unquote(urlsplit(href).fragment) == "school=林肯大學 Lincoln University"
        # Layout measurements in a test still work with page scripts disabled.
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(tmp_path / f"seo-partner-{width}.png"), full_page=True)
        page.get_by_role("navigation", name="麵包屑").get_by_role("link", name="長庚大學", exact=True).click()
        expect(page.get_by_role("heading", level=1)).to_contain_text("長庚大學")
    finally:
        context.close()


@pytest.mark.parametrize("width", [390, 1280])
def test_editorial_navigation_and_country_comparison_without_javascript(browser, live_server, width):
    context = browser.new_context(java_script_enabled=False, viewport={"width": width, "height": 900})
    try:
        page = context.new_page()
        for path in ("/guides/exchange-budget", "/destinations/japan", "/editorial-policy"):
            response = page.goto(live_server.base_url + path)
            assert response.status == 200
            expect(page.get_by_role("heading", level=1)).to_be_visible()
            assert page.locator('nav[aria-label="主導覽"] a[href="/guides"]').count() == 1
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.goto(live_server.base_url + "/schools")
        expect(page.get_by_role("heading", level=1)).to_contain_text("全台大學")
    finally:
        context.close()


def test_public_partner_link_opens_its_application_tab(page, live_server):
    page.goto(live_server.base_url + "/schools/cgu", wait_until="domcontentloaded")
    page.locator(".cards a").filter(has_text="Lincoln University").click()
    page.get_by_role("link", name="查看這所學校的申請方式").first.click()
    expect(page.locator("#school-detail-title")).to_contain_text("Lincoln University", timeout=120000)
    expect(page.locator("#detail-tab-application")).to_have_attribute("aria-selected", "true", timeout=60000)
    expect(page.locator("#detail-application")).to_be_visible(timeout=120000)
