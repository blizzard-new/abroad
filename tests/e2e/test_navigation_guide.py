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


def test_home_is_the_guide_and_the_forum_is_one_click_away(page, live_server):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    start(page, live_server)
    nav = page.locator(".uniway-public-nav")
    expect(nav.get_by_role("link", name="申請指南", exact=True)).to_have_count(0)
    expect(page.locator("#guide")).to_be_visible()
    expect(page.locator("#page-back")).to_be_visible()
    assert page.locator("#page-back").evaluate("button => button.closest('#main-content') !== null")
    assert page.locator("#page-back").evaluate("button => button.closest('#glass-navigation') === null")
    back = page.locator("#page-back").bounding_box()
    guide = page.locator("#guide").bounding_box()
    assert abs(back["x"] - guide["x"]) <= 1
    assert back["y"] < guide["y"]
    expect(page.locator(".guide-stages > li")).to_have_count(4)
    expect(page.locator("#community-hub")).to_be_hidden()
    expect(nav.locator('[data-public-route="home"]')).to_have_attribute("aria-current", "page")
    expect(page).to_have_title("首頁 | UniWay")
    nav.get_by_role("link", name="論壇", exact=True).click()
    expect(page).to_have_url(f"{live_server.base_url}/#forum")
    expect(page.locator("#community-hub")).to_be_visible()
    expect(page.locator("#community-hub-title")).to_have_text("最新留學討論")
    expect(page.locator("#guide")).to_be_hidden()
    expect(nav.locator('[data-public-route="forum"]')).to_have_attribute("aria-current", "page")
    expect(nav.locator('[data-public-route="home"]')).not_to_have_attribute("aria-current", "page")
    expect(page).to_have_title("論壇 | UniWay")
    page.locator('#community-feed-tabs a[href="#public-board"]').click()
    expect(nav.locator('[data-public-route="forum"]')).to_have_attribute("aria-current", "page")
    nav.get_by_role("link", name="首頁", exact=True).click()
    expect(page).to_have_url(f"{live_server.base_url}/#home")
    expect(page.locator("#guide")).to_be_visible()
    expect(page.locator("#guide-title")).to_be_focused()
    assert not errors


def test_an_old_guide_link_opens_the_home_page(page, live_server):
    start(page, live_server, "guide")
    expect(page).to_have_url(f"{live_server.base_url}/#home")
    expect(page.locator("#guide")).to_be_visible()
    expect(page.locator("#page-back")).to_be_disabled()


def test_an_old_community_link_opens_the_forum(page, live_server):
    start(page, live_server, "community-hub")
    expect(page).to_have_url(f"{live_server.base_url}/#forum")
    expect(page.locator("#community-hub")).to_be_visible()


def test_guide_shared_shell_and_back_forward_without_loops(page, live_server):
    start(page, live_server)
    nav = page.locator(".uniway-public-nav")
    expect(page.locator("#guide")).to_be_visible()
    expect(page.locator("#application-center")).to_be_hidden()
    page.locator("#guide").get_by_role("link", name="準備申請文件", exact=True).click()
    expect(page.locator("#application-center")).to_be_visible()
    expect(nav).to_be_visible()
    expect(page.locator(".sidebar")).to_be_hidden()
    page.locator("#page-back").click()
    expect(page.locator("#guide")).to_be_visible()
    expect(page).to_have_url(f"{live_server.base_url}/#home")
    expect(page.locator("#page-back")).to_be_disabled()
    page.go_forward()
    expect(page.locator("#application-center")).to_be_visible()
    # Reload must retain the known internal history boundary.
    page.reload()
    page.locator("#page-back").click()
    expect(page.locator("#guide")).to_be_visible()


@pytest.mark.parametrize("route", ["budget", "application-center", "school=" + LINCOLN])
def test_direct_entry_back_stays_inside_site(page, live_server, route):
    start(page, live_server, route)
    page.locator(".route-back:visible").click()
    expect(page).to_have_url(f"{live_server.base_url}/#home")
    expect(page.locator("#page-back")).to_be_disabled()
    expect(page.locator("#dashboard-view")).to_be_visible()
    expect(page.locator("#school-detail-view")).to_be_hidden()


def test_every_tool_has_shared_navigation_and_return(page, live_server):
    start(page, live_server, "home")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    routes = ["favorites", "advisor", "application-center", "calendar", "eligibility", "document-check", "documents", "deadlines", "scholarships", "budget"]
    for route in routes:
        page.locator("#application-tools .application-nav-chevron").click()
        if route in ["favorites", "calendar", "eligibility", "document-check", "documents", "deadlines", "scholarships", "budget"] and not page.locator(".application-extra-tools").get_attribute("open") == "":
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
    expect(page.locator("#boot-splash")).to_be_hidden()
    page.wait_for_function("() => !state.homeSchoolLoading && !state.partnerDataLoading")
    page.evaluate("() => state.periodOptionsReady")
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
    back_bar = page.locator(".page-back-bar").bounding_box()
    # The return control belongs to the page header and must stay above sticky detail tabs.
    assert abs(back_bar["x"] - tabs["x"]) <= 1
    assert back_bar["y"] + back_bar["height"] <= tabs["y"]
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
    start(page, live_server, "home")
    expect(page.locator("#guide")).to_be_visible()
    page.locator(".skip-link").focus()
    page.keyboard.press("Enter")
    expect(page).to_have_url(f"{live_server.base_url}/#home")
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
