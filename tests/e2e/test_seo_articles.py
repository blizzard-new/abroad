"""Exercise the reading journey and actual asset delivery at mobile/desktop sizes."""
import pytest
from playwright.sync_api import expect

from exchange_info.seo_articles import ARTICLES


@pytest.mark.parametrize("width", [390, 1440])
def test_article_journey_without_javascript(browser, live_server, width, tmp_path):
    context = browser.new_context(java_script_enabled=False, viewport={"width": width, "height": 900})
    try:
        page = context.new_page()
        page.goto(live_server.base_url + "/guides")
        expect(page.get_by_role("heading", level=1)).to_contain_text("交換學生指南")
        assert page.locator(".editorial-card").count() == len(ARTICLES)
        page.locator('.editorial-card > a[href="/guides/exchange-budget"]').click()
        page.get_by_role("navigation", name="文章目錄").get_by_role("link", name="一學期試算", exact=False).click()
        expect(page.locator("#worked-example")).to_be_in_viewport()
        page.locator(".article-faq summary").first.click()
        expect(page.locator(".article-faq[open] p")).to_be_visible()
        image = page.locator(".article-illustration img")
        image.scroll_into_view_if_needed()
        expect(image).to_be_visible()
        expect(image).to_have_js_property("complete", True)
        assert image.evaluate("image => image.naturalWidth") == 1536
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(tmp_path / f"article-budget-{width}.png"), full_page=True)
        page.locator('#related a[href="/guides/japan-exchange-cost"]').click()
        expect(page.get_by_role("heading", level=1)).to_contain_text("日本交換")
        page.get_by_role("link", name="比較日本交換選項與各母校方案").click()
        expect(page).to_have_url(live_server.base_url + "/destinations/japan")
    finally:
        context.close()


@pytest.mark.parametrize("slug", ARTICLES)
def test_every_article_has_no_mobile_overflow_and_loads_illustration(page, live_server, slug):
    page.set_viewport_size({"width": 390, "height": 844})
    response = page.goto(live_server.base_url + "/guides/" + slug)
    assert response.status == 200
    assert response.headers.get("x-robots-tag") != "noindex"
    image = page.locator(".article-illustration img")
    image.scroll_into_view_if_needed()
    expect(image).to_have_js_property("complete", True)
    assert image.evaluate("image => image.naturalWidth") > 0
    for table in page.locator(".article-table").all():
        table.focus()
        assert table.evaluate("el => el.clientWidth <= window.innerWidth")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
