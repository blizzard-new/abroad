"""Travel accents keep real search, collection and progress behavior intact."""
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, quote
from uuid import uuid4

from playwright.sync_api import expect

from .conftest import enter_public_site, login_through_web
from .test_partner_globe import LINCOLN, MEIJI, inject_dashboard, open_partners
from .test_discovery_workspace import setup_catalog
from .test_web_next_phase import _wait_for_workspace


ARTIFACTS = Path("output/travel-theme")


def capture_sizes(page, name):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for width in (393, 834, 1440):
        page.set_viewport_size({"width": width, "height": 940})
        page.evaluate("scrollTo({top: 0, behavior: 'instant'})")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (name, width)
        page.screenshot(path=str(ARTIFACTS / f"{name}-{width}.png"), full_page=True, animations="disabled")


def test_home_search_navigation_school_switcher_and_responsive(page, live_server):
    setup_catalog(page)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_partners(page, live_server, {"view": "list"})
    page.locator(".uniway-public-nav").get_by_role("link", name="論壇", exact=True).click()
    home_url = page.url
    expect(page.locator("#travel-home")).to_have_count(0)
    expect(page.locator("#school-switcher-label")).to_have_text("長庚大學")
    expect(page.get_by_role("heading", level=1)).to_have_text("最新留學討論")
    page.locator('.uniway-public-nav a[data-public-route="partners"]').click()
    page.locator("#partner-search").fill("日本")
    expect(page.locator(".desktop-partner-table .school-detail-trigger")).to_have_text(MEIJI)
    assert parse_qs(urlsplit(page.url).query)["view"] == ["list"]
    page.locator("#page-back").click()
    expect(page).to_have_url(home_url)
    expect(page.locator("#community-hub-title")).to_be_focused()
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立臺北大學"]').click()
    page.locator("#confirm-school").click()
    expect(page.locator("#school-switcher-label")).to_have_text("國立臺北大學")
    expect(page.locator("#page-status .status-message")).to_be_hidden(timeout=15000)
    capture_sizes(page, "home")
    page.locator("#theme-toggle").click()
    capture_sizes(page, "home-dark")
    page.locator(".uniway-public-nav").get_by_role("link", name="社群討論", exact=True).click()
    expect(page.get_by_role("heading", level=1)).to_have_text("公共留學板")
    assert not errors


def test_ticket_collection_and_destination_stamp_missing_city(page, live_server):
    setup_catalog(page)
    # Explicit fixture cities prove the stamp derives from this school's record.
    def locations(payload):
        for school in payload["partner_universities"]:
            if school["school_name"] == LINCOLN:
                school["location"]["city"] = "林肯"
            elif school["school_name"] == MEIJI:
                school["location"] = None
    inject_dashboard(page, locations)
    open_partners(page, live_server, {"view": "list"})
    for school in (LINCOLN, MEIJI):
        page.locator(f'.desktop-partner-table .favorite-toggle[data-school-name="{school}"]').click()
    page.goto(f"{live_server.base_url}/#favorites")
    expect(page.locator(".travel-saved-ticket")).to_have_count(2)
    expect(page.locator(".travel-ticket-number")).to_have_text(["01", "02"])
    capture_sizes(page, "favorites")
    page.locator("#theme-toggle").click()
    capture_sizes(page, "favorites-dark")
    page.locator("#theme-toggle").click()
    page.locator(f'.discovery-candidate .school-detail-trigger[data-school-name="{LINCOLN}"]').click()
    expect(page.locator("#school-destination-stamp")).to_contain_text("紐西蘭")
    expect(page.locator(".travel-stamp-city")).to_have_text("林肯")
    expect(page.locator(".travel-task-stamp")).to_have_count(0)
    expect(page.locator(".progress-checkbox").first).to_be_disabled()
    capture_sizes(page, "school")
    page.locator("#back-to-schools").click()
    page.locator(f'.discovery-candidate .school-detail-trigger[data-school-name="{MEIJI}"]').click()
    expect(page.locator("#school-destination-stamp strong")).to_have_text("日本")
    expect(page.locator(".travel-stamp-city")).to_have_count(0)
    page.locator("#theme-toggle").click()
    capture_sizes(page, "school-dark")


def test_completed_stamp_persists_and_unchecking_removes_it(page, live_server):
    email = f"travel-{uuid4().hex[:10]}@example.com"
    session = live_server.register(email)
    page.add_init_script("localStorage.setItem('exchange-guide-home-school', '長庚大學')")
    setup_catalog(page)
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text("已同步", timeout=15000)
    page.goto(f"{live_server.base_url}/#school={quote(LINCOLN)}")
    checkbox = page.locator("#application-tracker .progress-checkbox").first
    expect(checkbox).to_be_enabled()
    step = checkbox.get_attribute("data-progress-step")
    checkbox.check()
    expect(checkbox).to_be_focused()
    expect(page.locator(".travel-task-stamp")).to_have_text("完成")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    page.locator("#application-tracker").screenshot(path=str(ARTIFACTS / "completed-stamp.png"), animations="disabled")
    _wait_for_workspace(live_server, session, lambda value: value.get("workspace", {}).get("application_progress", {}).get(LINCOLN, {}).get(step) is True)
    page.reload()
    expect(checkbox).to_be_checked()
    expect(page.locator(".travel-task-stamp")).to_have_text("完成")
    expect(page.locator(".travel-task-stamp.is-new")).to_have_count(0)
    page.emulate_media(reduced_motion="reduce")
    checkbox.uncheck()
    expect(page.locator(".travel-task-stamp")).to_have_count(0)
    checkbox.check()
    assert page.locator(".travel-task-stamp").evaluate("el => getComputedStyle(el).animationName") == "none"
    checkbox.uncheck()
    _wait_for_workspace(live_server, session, lambda value: value.get("workspace", {}).get("application_progress", {}).get(LINCOLN, {}).get(step) is False)
    page.reload()
    expect(checkbox).not_to_be_checked()
    expect(page.locator(".travel-task-stamp")).to_have_count(0)


def test_school_switcher_without_selected_school(page, live_server):
    enter_public_site(page, live_server)
    expect(page.locator("#school-switcher-label")).to_have_text("選擇就讀學校")
    page.locator("#school-switcher").click()
    expect(page.locator("#school-onboarding")).to_be_visible()
