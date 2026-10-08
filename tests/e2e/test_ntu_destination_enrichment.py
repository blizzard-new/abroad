from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until


@pytest.mark.parametrize("width", [390, 1440])
def test_ntu_photos_globe_data_and_bundled_life_are_visible_without_refresh(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors, refreshes = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: refreshes.append(request.url) if "/school-life-context/refresh" in request.url else None)
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立臺灣大學"]').click()
    page.locator("#confirm-school").click()
    if width < 700 and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '國立臺灣大學' && state.dashboard.partner_universities.length === 288")
    assert page.evaluate("state.dashboard.partner_universities.filter(p => p.location?.geocode_status === 'verified').length") == 269
    assert page.evaluate("state.dashboard.partner_universities.filter(p => p.image_status === 'verified').length") == 286
    # Exercise the actual globe with local vendor/data assets.
    page.locator('[data-partner-view="map"]').click()
    expect(page.locator("#partner-globe canvas")).to_be_visible(timeout=30000)
    expect(page.locator("#partner-map-status")).to_be_hidden(timeout=30000)
    assert page.locator("#map-school-select option").count() >= 269
    output = Path("/tmp/ntu-destinations-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"globe-{width}.png"), full_page=True)
    page.locator("#map-school-select").select_option("聖保羅大學")
    expect(page.locator("#partner-map-preview")).to_be_visible()
    expect(page.locator("#partner-map-preview")).to_contain_text("聖保羅大學")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("聖保羅大學")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#school-detail-view")).to_be_visible()
    photo = page.locator("#school-detail-view .school-photo img").first
    expect(photo).to_be_visible()
    assert photo.evaluate("image => image.complete && image.naturalWidth > 0")
    expect(page.locator("#school-detail-view")).to_contain_text("圖片授權")
    page.get_by_role("tab", name="生活情報", exact=True).click()
    expect(page.locator('[data-life-theme="housing"]')).to_contain_text("USP iFriends")
    expect(page.locator("#life-research-status")).to_contain_text("部分資料已更新")
    expect(page.locator("#life-content")).to_contain_text("適用校區與年度請核對來源")
    page.screenshot(path=str(output / f"life-{width}.png"), full_page=True)
    assert not refreshes  # Reading shipped references must not start background scraping.
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
