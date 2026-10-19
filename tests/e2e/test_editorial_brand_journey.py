"""The reading section is discoverable from the app and shares its visual identity."""
import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation


@pytest.mark.parametrize("width", [320, 390, 1440])
def test_platform_to_article_and_back(page, live_server, width, tmp_path):
    page.set_viewport_size({"width": width, "height": 900})
    enter_public_site(page, live_server)
    expect(page.locator(".pr-guide-entry")).to_be_visible()
    expect(page.locator("#home-guides-title")).to_be_visible()
    assert page.locator(".pr-guide-card").count() == 3
    palette = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--uw-navy')")
    font = page.locator("body").evaluate("el => getComputedStyle(el).fontFamily")
    for image in page.locator(".pr-guide-card img").all():
        image.scroll_into_view_if_needed()
        expect(image).to_have_js_property("complete", True)
        assert image.evaluate("el => el.naturalWidth") > 0
    page.locator(".pr-editorial").evaluate("el => window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 90)")
    page.screenshot(path=str(tmp_path / f"home-guides-{width}.png"))
    page.evaluate("window.scrollTo(0, 0)")
    page.screenshot(path=str(tmp_path / f"platform-{width}.png"))
    if width < 901:
        entry = page.locator(".glass-mobile-header .mobile-guide-link")
        expect(entry).to_be_in_viewport()
    else:
        entry = page.locator('.uniway-public-nav a[href="/guides"]')
        entry.focus()
    entry.click()
    expect(page).to_have_url(live_server.base_url + "/guides")
    expect(page.locator('.reading-header a[href="/guides"]')).to_have_attribute("aria-current", "page")
    assert page.locator("body").evaluate("el => getComputedStyle(el).fontFamily") == font
    assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--uw-navy')") == palette
    assert page.locator(".brand img").evaluate("el => el.complete && el.naturalWidth > 0")
    page.screenshot(path=str(tmp_path / f"guide-index-{width}.png"))
    page.locator('.editorial-card > a[href="/guides/exchange-application"]').click()
    expect(page.locator("h1")).to_contain_text("交換學生申請流程")
    assert page.locator(".reading-header").bounding_box()["height"] < 150
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(tmp_path / f"article-{width}.png"))
    page.get_by_role("link", name="開啟選校工具", exact=False).first.click()
    expect(page).to_have_url(live_server.base_url + "/#partners")
    expect(page.locator("#partners")).to_be_visible(timeout=30000)
    page.locator("#boot-splash").wait_for(state="hidden", timeout=60000)
    open_navigation(page)
    page.locator('.uniway-public-nav a[href="/guides"]').click()
    expect(page).to_have_url(live_server.base_url + "/guides")


@pytest.mark.parametrize("preference,expected", [("dark", "dark"), ("light", "light"), ("system", "dark")])
def test_reading_honors_and_updates_platform_theme(browser, live_server, preference, expected, tmp_path):
    context = browser.new_context(color_scheme="dark", viewport={"width": 390, "height": 900})
    try:
        page = context.new_page()
        page.goto(live_server.base_url + "/guides")
        page.evaluate("p => localStorage.setItem('exchange-guide-theme', p)", preference)
        page.goto(live_server.base_url + "/guides/exchange-budget")
        expect(page.locator("html")).to_have_attribute("data-theme", expected)
        page.screenshot(path=str(tmp_path / f"article-theme-{preference}.png"))
        opposite = "light" if expected == "dark" else "dark"
        page.locator(".reading-theme-toggle").click()
        expect(page.locator("html")).to_have_attribute("data-theme", opposite)
        assert page.evaluate("localStorage.getItem('exchange-guide-theme')") == opposite
        page.goto(live_server.base_url + "/guides")
        expect(page.locator("html")).to_have_attribute("data-theme", opposite)
    finally:
        context.close()


def test_reading_theme_and_links_work_when_storage_is_blocked(page, live_server):
    page.add_init_script("Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } })")
    page.goto(live_server.base_url + "/guides/exchange-application")
    expect(page.locator("h1")).to_be_visible()
    page.locator(".reading-theme-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.locator('.reading-header a[href="/guides"]').click()
    expect(page.locator(".editorial-card")).to_have_count(10)
