"""Exercise navigation as a user, including native history and direct-entry boundaries."""
from pathlib import Path
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_partner_globe import LINCOLN, open_partners


def start(page, live_server, route="home"):
    page.add_init_script("localStorage.setItem('exchange-guide-home-school', '長庚大學')")
    enter_public_site(page, live_server, route)


def test_guide_shared_shell_and_back_forward_without_loops(page, live_server):
    start(page, live_server)
    nav = page.locator(".uniway-public-nav")
    nav.get_by_role("link", name="申請指南", exact=True).click()
    expect(page.locator("#guide")).to_be_visible()
    expect(page.locator(".guide-stages > li")).to_have_count(4)
    expect(page.locator("#application-center")).to_be_hidden()
    expect(page.locator("#guide-title")).to_be_focused()
    page.locator("#guide").get_by_role("link", name="準備申請文件", exact=True).click()
    expect(page.locator("#application-center")).to_be_visible()
    expect(nav).to_be_visible()
    expect(page.locator(".sidebar")).to_be_hidden()
    page.locator("#page-back").click()
    expect(page.locator("#guide")).to_be_visible()
    page.locator("#page-back").click()
    expect(page).to_have_url(f"{live_server.base_url}/#home")
    expect(page.locator("#page-back")).to_be_disabled()
    page.go_forward()
    expect(page.locator("#guide")).to_be_visible()
    page.go_forward()
    expect(page.locator("#application-center")).to_be_visible()
    # Reload must retain the known internal history boundary.
    page.reload()
    page.locator("#page-back").click()
    expect(page.locator("#guide")).to_be_visible()


@pytest.mark.parametrize("route", ["guide", "application-center", "school=" + LINCOLN])
def test_direct_entry_back_stays_inside_site(page, live_server, route):
    start(page, live_server, route)
    page.locator(".route-back:visible").click()
    expect(page).to_have_url(f"{live_server.base_url}/#home")
    expect(page.locator("#page-back")).to_be_disabled()
    expect(page.locator("#dashboard-view")).to_be_visible()
    expect(page.locator("#school-detail-view")).to_be_hidden()


def test_every_tool_has_shared_navigation_and_return(page, live_server):
    start(page, live_server, "guide")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    routes = ["favorites", "advisor", "application-center", "calendar", "eligibility", "document-check", "documents", "deadlines", "scholarships", "budget"]
    for route in routes:
        page.locator("#application-tools .application-nav-chevron").click()
        if route in ["eligibility", "document-check", "documents", "deadlines", "scholarships", "budget"] and not page.locator(".application-extra-tools").get_attribute("open") == "":
            page.locator(".application-extra-tools > summary").click()
        page.locator(f'.application-tools-panel a[href="#{route}"]').click()
        expect(page).to_have_url(re.compile(rf"#{route}$"))
        expect(page.locator(".uniway-public-nav")).to_be_visible()
        expect(page.locator("#page-back")).to_be_visible()
        expect(page.locator("#application-tools")).not_to_have_attribute("open", "")
        if route != "university-posts":
            expect(page.locator(f'section[data-university-page="{route}"]')).to_be_visible()
        page.locator("#page-back").click()
        expect(page.locator("#guide")).to_be_visible()
    assert not errors


def test_school_return_retains_filters_scroll_and_forward(page, live_server):
    page.set_viewport_size({"width": 1280, "height": 600})
    open_partners(page, live_server, {"view": "list", "country": "紐西蘭", "q": "Lincoln"})
    trigger = page.locator('.desktop-partner-table .school-detail-trigger').first
    # Start from a real scroll position even when the compact search header fits above the fold.
    page.evaluate("scrollTo({top: 250, behavior: 'instant'})")
    trigger.scroll_into_view_if_needed()
    page.wait_for_timeout(100)  # Flush the browser scroll event before taking the baseline.
    before_url = page.url
    before_y = page.evaluate("scrollY")
    assert before_y > 0
    trigger.click()
    expect(page.locator("#school-detail-title")).to_have_text(LINCOLN)
    page.evaluate("scrollTo({top: 900, behavior: 'instant'})")
    page.wait_for_function("scrollY > 500")
    tabs = page.locator(".detail-tabs").bounding_box()
    toolbar = page.locator(".route-toolbar").bounding_box()
    assert tabs["y"] >= toolbar["y"] + toolbar["height"]
    page.locator("#back-to-schools").click()
    expect(page).to_have_url(before_url)
    expect(page.locator("#partner-search")).to_have_value("Lincoln")
    expect(page.locator("#country-filter")).to_have_value("紐西蘭")
    page.wait_for_function("y => Math.abs(scrollY - y) < 5", arg=before_y)
    page.go_forward()
    expect(page.locator("#school-detail-title")).to_have_text(LINCOLN)
    page.locator("#back-to-schools").click()
    expect(page).to_have_url(before_url)


@pytest.mark.parametrize("width", [393, 834, 1440])
def test_guide_responsive_menu_keyboard_and_theme(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.emulate_media(reduced_motion="reduce")
    start(page, live_server, "guide")
    expect(page.locator("#guide")).to_be_visible()
    page.locator(".skip-link").focus()
    page.keyboard.press("Enter")
    expect(page).to_have_url(f"{live_server.base_url}/#guide")
    expect(page.locator("#main-content")).to_be_focused()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    open_navigation(page)
    page.locator("#application-tools > summary").focus()
    page.keyboard.press("Enter")
    expect(page.locator(".application-tools-panel")).to_be_visible()
    bounds = page.locator(".application-tools-panel").bounding_box()
    assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= width + 1
    page.keyboard.press("Escape")
    expect(page.locator(".application-tools-panel")).to_be_hidden()
    expect(page.locator("#application-tools > summary")).to_be_focused()
    if page.locator("#glass-menu-close").is_visible():
        page.locator("#glass-menu-close").click()
    page.locator(".guide-faq summary").click()
    expect(page.locator(".guide-faq p")).to_be_visible()
    page.locator(".guide-faq summary").click()
    artifacts = Path("output/navigation-guide")
    artifacts.mkdir(parents=True, exist_ok=True)
    page.evaluate("scrollTo({top: 0, behavior: 'instant'})")
    page.screenshot(path=str(artifacts / f"guide-{width}.png"), full_page=True)
    open_navigation(page)
    page.locator("#theme-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if page.locator("#glass-menu-close").is_visible():
        page.locator("#glass-menu-close").click()
    page.screenshot(path=str(artifacts / f"guide-dark-{width}.png"), full_page=True)
