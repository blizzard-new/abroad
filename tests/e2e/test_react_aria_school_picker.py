"""School selection supports keyboard and touch while keeping existing app state."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import attach_session, sign_in_cookie

NTPU = "國立臺北大學"


def capture(page, name):
    target = Path("output/react-aria")
    target.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(target / name))


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("query,school", [
    ("Taipei", NTPU), ("台大", "國立臺灣大學"), ("中央", "國立中央大學"),
])
def test_search_aliases_and_keyboard_activation(page, live_server, width, query, school):
    page.set_viewport_size({"width": width, "height": 900})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server)
    page.locator("#school-switcher").click()
    search = page.get_by_role("searchbox", name="搜尋台灣的大學")
    expect(search).to_be_focused()
    expect(page.get_by_role("dialog", name="你目前就讀哪一所台灣大學？")).to_be_visible()
    expect(page.get_by_role("listbox", name="可選擇的大學")).to_be_visible()
    search.fill(query)
    expect(page.locator("#school-options [role='option']")).to_have_count(1)
    expect(page.locator("#school-options [role='option']")).to_contain_text(school)
    original = page.locator("#school-switcher-label").inner_text()
    search.press("ArrowDown")
    expect(page.locator("#school-options [role='option']")).to_have_attribute("data-focused", "true")
    expect(page.locator("#school-switcher-label")).to_have_text(original)
    expect(search).to_be_focused()
    search.press("Enter")
    expect(page.locator("#school-onboarding")).to_be_hidden()
    expect(page.locator("#school-switcher-label")).to_have_text(school)
    assert page.evaluate("localStorage.getItem('exchange-guide-home-school')") == school
    assert not errors


@pytest.mark.parametrize("width", [390, 1440])
def test_focus_stays_in_dialog_and_cancel_keeps_current_school(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 844})
    page.add_init_script(f"localStorage.setItem('exchange-guide-home-school', '{NTPU}')")
    enter_public_site(page, live_server)
    switcher = page.locator("#school-switcher")
    switcher.click()
    expect(switcher).to_have_attribute("aria-expanded", "true")
    expect(page.get_by_role("searchbox")).to_be_focused()
    assert page.locator("#main-content").evaluate("el => Boolean(el.closest('[inert], [aria-hidden=true]'))")
    for key in ["Tab"] * 6 + ["Shift+Tab"] * 6:
        page.keyboard.press(key)
        assert page.evaluate("Boolean(document.activeElement.closest('#school-onboarding'))")
    if width == 1440:
        capture(page, "desktop-picker-keyboard.png")
    page.keyboard.press("Escape")
    expect(page.locator("#school-onboarding")).to_be_hidden()
    expect(switcher).to_be_focused()
    expect(switcher).to_have_attribute("aria-expanded", "false")
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)
    assert page.evaluate("localStorage.getItem('exchange-guide-home-school')") == NTPU
    assert not page.locator("#main-content").evaluate("el => Boolean(el.closest('[inert], [aria-hidden=true]'))")
    switcher.click()
    page.get_by_role("button", name="關閉學校選擇").click()
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)
    expect(switcher).to_be_focused()
    switcher.click()
    page.mouse.click(3, 3)
    expect(page.locator("#school-onboarding")).to_be_hidden()
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)


def test_empty_results_can_be_cleared_and_reopening_resets_search(page, live_server):
    enter_public_site(page, live_server)
    page.locator("#school-switcher").click()
    search = page.get_by_role("searchbox")
    search.fill("不存在的學校")
    expect(page.locator("#school-options [data-home-school]")).to_have_count(0)
    expect(page.locator("#school-search-empty")).to_contain_text("未找到這所學校")
    page.get_by_role("button", name="清除學校搜尋").click()
    expect(search).to_have_value("")
    expect(search).to_be_focused()
    expect(page.locator("#school-options [role='option']")).to_have_count(6)
    search.fill("Taipei")
    page.get_by_role("button", name="關閉學校選擇").click()
    page.locator("#school-switcher").click()
    expect(page.get_by_role("searchbox")).to_have_value("")
    expect(page.locator("#school-options [role='option']")).to_have_count(6)


def test_mobile_touch_and_dark_theme_are_usable(browser, live_server):
    context = browser.new_context(viewport={"width": 390, "height": 700}, is_mobile=True, has_touch=True)
    page = context.new_page()
    try:
        enter_public_site(page, live_server)
        page.locator("#school-switcher").tap()
        expect(page.get_by_role("searchbox")).to_be_focused()
        capture(page, "mobile-picker-light.png")
        last = page.locator('#school-options [data-home-school="淡江大學"]')
        last.scroll_into_view_if_needed()
        last.tap()
        expect(page.locator("#school-switcher-label")).to_have_text("淡江大學")
        open_navigation(page)
        page.locator("#theme-toggle").tap()
        page.locator("#glass-menu-close").tap()
        page.locator("#school-switcher").tap()
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        expect(page.get_by_role("searchbox")).to_be_focused()
        capture(page, "mobile-picker-dark.png")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert page.locator(".aria-school-modal").bounding_box()["height"] <= 700
        page.get_by_role("button", name="關閉學校選擇").tap()
        expect(page.locator("#school-switcher-label")).to_have_text("淡江大學")
    finally:
        context.close()


def test_delayed_account_save_blocks_duplicate_choices_and_dismissal(page, live_server):
    session = sign_in_cookie(live_server, school="尚未選擇")
    attach_session(page, live_server, session)
    pending = []

    def hold_save(route):
        if route.request.method == "PATCH":
            pending.append(route)
        else:
            route.continue_()

    page.route("**/auth/me", hold_save)
    page.goto(f"{live_server.base_url}/#auth=success")
    expect(page.locator("#school-onboarding")).to_be_visible(timeout=30000)
    expect(page.locator("#onboarding-lock-note")).to_be_visible()
    page.locator(f'#school-options [data-home-school="{NTPU}"]').click()
    expect(page.get_by_role("button", name="關閉學校選擇")).to_be_disabled()
    expect(page.get_by_role("searchbox")).to_be_disabled()
    expect(page.locator(".school-picker-status")).to_contain_text("正在切換學校")
    expect(page.locator('#school-options [data-home-school="國立中央大學"]')).to_have_attribute("aria-disabled", "true")
    page.keyboard.press("Escape")
    expect(page.locator("#school-onboarding")).to_be_visible()
    assert len(pending) == 1
    assert pending[0].request.post_data_json == {"home_university": NTPU}
    pending[0].continue_()
    expect(page.locator("#school-onboarding")).to_be_hidden(timeout=30000)
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)
    page.reload()
    page.locator("#boot-splash").wait_for(state="hidden", timeout=60000)
    expect(page.locator("#school-onboarding")).to_be_hidden()
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)
    assert len(pending) == 1


def test_native_fallback_works_when_react_aria_cannot_load(page, live_server):
    page.route("**/react-aria-school-picker.js?*", lambda route: route.abort())
    enter_public_site(page, live_server)
    assert page.evaluate("typeof window.UniWaySchoolPicker") == "undefined"
    page.locator("#school-switcher").click()
    page.locator("#school-search").fill("Taipei")
    expect(page.locator("#school-options [data-home-school]")).to_have_count(1)
    page.locator(f'#school-options [data-home-school="{NTPU}"]').click()
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)
    page.locator("#school-switcher").click()
    page.get_by_role("button", name="關閉學校選擇").click()
    expect(page.locator("#school-onboarding")).to_be_hidden()
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)


def test_account_save_timeout_releases_the_dialog_without_retrying(page, live_server):
    session = sign_in_cookie(live_server, school="尚未選擇")
    attach_session(page, live_server, session)
    pending = []

    def hold_save(route):
        if route.request.method == "PATCH":
            pending.append(route)
        else:
            route.continue_()

    page.clock.install()
    page.route("**/auth/me", hold_save)
    page.goto(f"{live_server.base_url}/#auth=success")
    page.locator("#boot-splash").wait_for(state="hidden", timeout=60000)
    page.locator(f'#school-options [data-home-school="{NTPU}"]').click()
    expect(page.get_by_role("button", name="關閉學校選擇")).to_be_disabled()
    page.clock.fast_forward(21_000)
    expect(page.locator("#school-onboarding")).to_be_hidden()
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)
    assert len(pending) == 1
    page.locator("#school-switcher").click()
    expect(page.get_by_role("button", name="關閉學校選擇")).to_be_enabled()
    page.get_by_role("button", name="關閉學校選擇").click()
    expect(page.locator("#school-onboarding")).to_be_hidden()


def test_cancelling_personalized_entry_clears_the_deferred_route(page, live_server):
    enter_public_site(page, live_server)
    page.locator('#guide .guide-action[href="#eligibility"]').click()
    expect(page.locator("#school-onboarding")).to_be_visible()
    page.get_by_role("button", name="關閉學校選擇").click()
    expect(page.locator("#guide")).to_be_visible()
    expect(page.locator("#school-switcher-label")).to_have_text("選擇就讀學校")
    page.locator("#school-switcher").click()
    page.locator(f'#school-options [data-home-school="{NTPU}"]').click()
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)
    expect(page.locator("#guide")).to_be_visible()
    assert page.evaluate("location.hash") == "#home"
