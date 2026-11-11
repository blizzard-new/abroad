"""The forum, school search and application tools share accessible responsive navigation."""
import os
from pathlib import Path
from uuid import uuid4

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, login_through_web, open_navigation, open_partner_filters
from .test_discussion_reader import seed, search
from .test_partner_globe import INSTRUMENT, LINCOLN


def verified_login(page, live_server):
    email = f"glass-{uuid4().hex[:8]}@example.com"
    session = live_server.register(email)
    live_server.verify_student(session["profile"]["id"])
    login_through_web(page, live_server, email)
    return session


def capture(page, name):
    directory = os.environ.get("UNIWAY_GLASS_ARTIFACT_DIR")
    if directory:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(target / name), full_page=True, animations="disabled")


@pytest.mark.parametrize("width", [390, 834, 1754])
def test_home_displays_stored_posts_without_destination_sections(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    marker, posts = seed(live_server, count=3)
    enter_public_site(page, live_server, "forum")
    expect(page.locator(".glass-home-intro, .glass-home-overview, .glass-home-destinations, #glass-home-schools")).to_have_count(0)
    search(page, marker)
    expect(page.locator(".discussion-summary")).to_have_count(3)
    expect(page.locator(".featured-board-card")).to_have_count(3)
    assert page.locator(".discussion-summary").first.bounding_box()["y"] < 956
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    for control in ["theme-toggle", "refresh-button", "account-button"]:
        expect(page.locator(f"#glass-navigation #{control}")).to_have_count(1)
    expect(page.locator('#glass-navigation a[data-public-route="my-application"]')).to_have_count(1)
    expect(page.locator("#glass-navigation #school-switcher")).to_have_count(0)
    expect(page.locator("#main-content .uniway-public-nav, #main-content .topbar-actions")).to_have_count(0)
    expect(page.locator(".page-back-bar #school-switcher")).to_be_visible()
    capture(page, f"discussion-home-{width}.png")
    page.locator(f'[data-discussion-open="{posts[0].id}"]').first.click()
    expect(page.locator("#discussion-article-title")).to_contain_text(marker)
    expect(page.locator("#discussion-comments")).to_contain_text("當年度的提名信")
    page.locator("#discussion-reader-close").click()
    expect(page.locator("#global-community-search")).to_have_value(marker)


@pytest.mark.parametrize("width", [390, 1440])
def test_verified_catalog_search_map_and_saved_school(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script(INSTRUMENT)
    verified_login(page, live_server)
    open_navigation(page)
    page.locator('.uniway-public-nav [data-public-route="my-application"]').click()
    expect(page.locator("#application-path")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    open_navigation(page)
    expect(page.locator(".workspace-sync-control")).to_be_visible()
    if width > 900:
        bar = page.locator("#glass-navigation").bounding_box()
        assert bar["x"] == 0 and bar["width"] == width and bar["height"] <= 76
    expect(page.locator("#account-workspace-sync-label")).to_have_text("已同步")
    page.locator('.uniway-public-nav [data-public-route="partners"]').click()
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("Lincoln")
    open_partner_filters(page)
    page.locator("#country-filter").select_option("紐西蘭")
    expect(page.locator("#partner-table .pr-school-card")).to_have_count(1)
    page.locator("#partner-table .favorite-toggle:visible").first.click()
    expect(page.locator("#partner-table .favorite-toggle:visible").first).to_have_attribute("aria-pressed", "true")
    page.locator('[data-partner-view="map"]').click()
    expect(page.locator("#partner-globe")).to_have_attribute("data-ready", "true", timeout=30000)
    page.wait_for_function("() => window.__testedMap && !window.__testedMap.isMoving() && window.__testedMap.isSourceLoaded('schools')")
    data = page.evaluate("async () => await window.__testedMap.getSource('schools').getData()")
    assert [feature["properties"]["name"] for feature in data["features"]] == [LINCOLN]
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    capture(page, f"verified-map-{width}.png")
    page.locator('[data-partner-view="list"]').click()
    expect(page.locator("#partner-search")).to_have_value("Lincoln")
    expect(page.locator("#country-filter")).to_have_value("紐西蘭")
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#school-detail-title")).to_have_text(LINCOLN)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    capture(page, f"verified-school-{width}.png")
    open_navigation(page)
    if width <= 900:
        page.locator("#glass-menu-close").click()
    page.locator("#back-to-schools").click()
    expect(page.locator("#partner-search")).to_have_value("Lincoln")
    page.locator(".discovery-open-workspace").click()
    expect(page.locator("#favorites")).to_contain_text(LINCOLN)
    expect(page.locator('.application-tools-heading a[href="#my-application"]')).to_be_visible()


@pytest.mark.parametrize("width", [390, 834, 1440])
def test_glass_navigation_and_responsive_routes(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "forum")
    expect(page.locator("#community-hub-title")).to_have_text("學長姐心得")
    nav = page.locator(".uniway-public-nav")
    for theme in ["light", "dark"]:
        if theme == "dark":
            open_navigation(page)
            page.locator("#theme-toggle").click()
            if page.locator("#glass-menu-close").is_visible():
                page.locator("#glass-menu-close").click()
        expect(page.locator("html")).to_have_attribute("data-theme", theme)
        for route in ["forum", "home", "partners", "public-board"]:
            if route == "public-board":
                open_navigation(page)
                nav.locator('[data-public-route="forum"]').click()
                page.locator('#community-feed-tabs a[href="#public-board"]').click()
                expect(nav.locator('[data-public-route="forum"]')).to_have_attribute("aria-current", "page")
            else:
                open_navigation(page)
                nav.locator(f'[data-public-route="{route}"]').click()
            page_id = {"forum": "#community-hub", "public-board": "#community-hub", "home": "#home-landing"}.get(route, f"#{route}")
            expect(page.locator(page_id)).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (width, theme, route)
            if route in ("forum", "home"):
                capture(page, f"{route}-guest-{width}-{theme}.png")
    assert not errors


@pytest.mark.parametrize("width,height", [(390, 620), (834, 956), (1280, 720), (1754, 956)])
def test_application_menu_is_reachable_without_overlapping_the_header(page, live_server, width, height):
    page.set_viewport_size({"width": width, "height": height})
    page.emulate_media(reduced_motion="reduce")
    verified_login(page, live_server)
    open_navigation(page)
    page.locator('.uniway-public-nav [data-public-route="my-application"]').click()
    menu = page.locator("#application-path .ap-menu")
    menu.locator("summary").click()
    expect(menu).to_have_attribute("open", "")
    for selector in ("#new-plan", "#refresh-path"):
        control = menu.locator(selector)
        control.focus()
        expect(control).to_be_focused()
        box = control.bounding_box()
        assert 0 <= box["x"] and box["x"] + box["width"] <= width
        assert 68 <= box["y"] and box["y"] + box["height"] <= height
    menu.locator("#new-plan").click()
    expect(page.locator("#plan-dialog")).to_be_visible()
    expect(menu).not_to_have_attribute("open", "")
    page.keyboard.press("Escape")
    expect(page.locator("#plan-dialog")).to_be_hidden()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_mobile_navigation_focus_escape_and_login(page, live_server):
    page.set_viewport_size({"width": 390, "height": 844})
    enter_public_site(page, live_server)
    expect(page.locator("#glass-navigation")).not_to_be_visible()
    open_navigation(page)
    expect(page.locator("#glass-menu-close")).to_be_focused()
    expect(page.locator("#refresh-button")).to_be_visible()
    expect(page.locator(".workspace-sync-control")).not_to_be_visible()
    assert page.locator("#main-content").evaluate("el => el.inert")
    page.locator("#account-button").focus()
    page.keyboard.press("Tab")
    expect(page.locator("#glass-menu-close")).to_be_focused()
    page.keyboard.press("Shift+Tab")
    expect(page.locator("#account-button")).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.locator("#glass-menu-toggle")).to_be_focused()
    expect(page.locator("#glass-navigation")).not_to_be_visible()
    assert not page.locator("#main-content").evaluate("el => el.inert")
    open_navigation(page)
    page.locator("#account-button").click()
    expect(page.locator("#auth-dialog")).to_be_visible()
    expect(page.locator("#glass-navigation")).not_to_be_visible()
    assert not page.locator("#main-content").evaluate("el => el.inert")
