"""The shared source disclosure preserves originals and visible year limits."""
import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site


@pytest.mark.parametrize("width", [390, 1280])
def test_original_source_facts_are_available_without_hiding_current_cost_limits(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script("localStorage.setItem('exchange-guide-home-school', '長庚大學')")
    enter_public_site(page, live_server, "partners")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("Kangwon")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    trigger = page.locator('#partner-table .school-detail-trigger[data-school-name="韓國江原國立大學 Kangwon National University"]:visible').first
    trigger.click()
    page.locator("#detail-tab-life").click()
    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    facts = official.locator(".destination-facts")
    expect(facts).to_be_visible()
    expect(facts).to_contain_text("2019")
    expect(facts).to_contain_text("不能當作現行交換預算")
    original = official.locator(".destination-original-summary")
    expect(original).not_to_be_visible()
    official.locator(".destination-source-library > summary").click()
    expect(original).to_be_visible()
    expect(original).to_contain_text("As of 2019")
    expect(original).to_contain_text("不能當作現行交換預算")
    source_links = official.locator(".destination-source-card a")
    assert source_links.count() == 4
    assert all(link.startswith("https://") for link in source_links.evaluate_all("links => links.map(link => link.href)"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
