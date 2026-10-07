"""The loading screen and the mascot, in a real browser: shown while the page waits, gone when it is ready, never stuck."""
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site

DASHBOARD = "**/student-dashboard**"
SCREEN = "#boot-splash"
PREPARE = "localStorage.setItem('exchange-guide-home-school', '長庚大學'); sessionStorage.setItem('exchange-guide-browse-first', '1')"


def animation_names(page, selector=None):
    script = "(selector) => (selector ? document.querySelector(selector).getAnimations({subtree: true}) : document.getAnimations()).map(a => a.animationName)"
    return page.evaluate(script, selector)


def hold_dashboard(page):
    held = []
    page.route(DASHBOARD, lambda route: held.append(route))
    return held


def wait_until_shown(page):
    # Before its stylesheet arrives any element reports opacity 1, so also require the script's mark and real visibility.
    page.wait_for_function(
        """() => { const el = document.querySelector('#boot-splash'); if (!el) return false; const style = getComputedStyle(el);
            return document.documentElement.classList.contains('splash-on') && style.opacity === '1' && style.visibility === 'visible'; }""",
        timeout=15_000,
    )


def test_it_shows_the_mascot_while_the_page_waits_and_goes_when_the_page_is_ready(page, live_server):
    page.add_init_script(PREPARE)
    held = hold_dashboard(page)
    page.goto(f"{live_server.base_url}/#home", wait_until="commit")
    wait_until_shown(page)
    screen = page.locator(SCREEN)
    expect(screen).to_contain_text("正在載入中")
    expect(screen).to_have_attribute("role", "status")
    names = animation_names(page, "#boot-splash .uw-mascot")
    assert "uw-mascot-busy" in names, "hops and turns while loading"
    assert "uw-mascot-blink" in names and "uw-mascot-look" in names, "blinks and looks around"
    assert screen.locator(".uw-mascot-picture").evaluate("img => img.complete && img.naturalWidth === 384")
    # nothing behind it can be clicked while it is up
    assert page.evaluate("document.elementFromPoint(innerWidth / 2, 20).closest('#boot-splash') !== null")
    page.wait_for_function("() => window.UniWaySplash && document.querySelector('#guide')")
    while not held:
        page.wait_for_timeout(100)
    for route in held:
        route.continue_()
    expect(page.locator(SCREEN)).to_have_count(0, timeout=20_000)
    expect(page.locator("#guide")).to_be_visible()
    assert "boot-splash-life" not in animation_names(page)


def test_it_also_goes_when_the_data_cannot_be_loaded(page, live_server):
    page.add_init_script(PREPARE)
    page.route(DASHBOARD, lambda route: route.fulfill(status=500, content_type="application/json", body='{"detail": "down"}'))
    page.goto(f"{live_server.base_url}/#home")
    expect(page.locator(SCREEN)).to_have_count(0, timeout=20_000)
    expect(page.locator("#guide")).to_be_visible()


def test_a_page_that_never_finishes_still_gets_rid_of_it(page, live_server):
    page.add_init_script(PREPARE)
    page.route("**/app.js*", lambda route: route.abort())
    page.clock.install()
    page.goto(f"{live_server.base_url}/#home", wait_until="commit")
    page.wait_for_function("() => window.UniWaySplash", timeout=15_000)  # its give-up timer is set once this script has run
    page.clock.run_for(23_000)
    expect(page.locator(SCREEN)).to_have_count(0, timeout=10_000)


def test_with_every_script_blocked_the_screen_never_covers_the_page(page, live_server):
    page.route("**/*.js*", lambda route: route.abort())
    page.goto(f"{live_server.base_url}/#home")
    page.wait_for_selector(SCREEN, state="attached")
    page.wait_for_timeout(600)
    assert page.evaluate("getComputedStyle(document.querySelector('#boot-splash')).visibility") == "hidden"
    assert page.evaluate("document.elementFromPoint(innerWidth / 2, 20).closest('#boot-splash') === null")


def test_the_stylesheet_alone_takes_it_away_when_no_timer_can_run(page, live_server):
    page.add_init_script("window.setTimeout = () => 0")  # nothing the scripts schedule will ever fire
    page.route("**/app.js*", lambda route: route.abort())
    page.goto(f"{live_server.base_url}/#home", wait_until="commit")
    wait_until_shown(page)
    page.evaluate("document.querySelector('#boot-splash').getAnimations().find(a => a.animationName === 'boot-splash-life').finish()")
    assert page.evaluate("getComputedStyle(document.querySelector('#boot-splash')).visibility") == "hidden"
    assert page.evaluate("document.elementFromPoint(innerWidth / 2, 20).closest('#boot-splash') === null")


def test_the_slow_wake_up_note_only_appears_after_a_wait(page, live_server):
    page.add_init_script(PREPARE)
    hold_dashboard(page)
    page.clock.install()
    page.goto(f"{live_server.base_url}/#home", wait_until="commit")
    page.wait_for_function("() => window.UniWaySplash", timeout=15_000)
    hint = page.locator("#boot-splash .boot-splash-hint")
    assert page.evaluate("getComputedStyle(document.querySelector('.boot-splash-hint')).opacity") == "0"
    page.clock.run_for(7_000)
    assert page.evaluate("getComputedStyle(document.querySelector('.boot-splash-hint')).opacity") == "0", "not yet"
    page.clock.run_for(1_500)
    page.wait_for_function("() => getComputedStyle(document.querySelector('.boot-splash-hint')).opacity === '1'", timeout=5_000)
    expect(hint).to_contain_text("伺服器剛醒來")


def test_without_motion_it_stands_still_but_still_appears_and_goes(page, live_server):
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script(PREPARE)
    held = hold_dashboard(page)
    page.goto(f"{live_server.base_url}/#home", wait_until="commit")
    wait_until_shown(page)
    names = animation_names(page)
    assert not [name for name in names if name.startswith("uw-mascot")], names
    assert page.evaluate("getComputedStyle(document.querySelector('#boot-splash')).visibility") == "visible"
    while not held:
        page.wait_for_timeout(100)
    for route in held:
        route.continue_()
    expect(page.locator(SCREEN)).to_have_count(0, timeout=20_000)


def test_in_dark_mode_it_is_dark_from_the_start(page, live_server):
    page.add_init_script(PREPARE + "; localStorage.setItem('exchange-guide-theme', 'dark')")
    hold_dashboard(page)
    page.goto(f"{live_server.base_url}/#home", wait_until="commit")
    wait_until_shown(page)
    assert page.evaluate("document.documentElement.dataset.theme") == "dark"
    assert page.evaluate("getComputedStyle(document.querySelector('#boot-splash')).backgroundColor") == "rgb(11, 17, 24)"


@pytest.mark.parametrize("width,height", [(320, 568), (390, 844), (844, 390), (1280, 900)])
def test_it_fits_every_screen_with_the_mascot_and_the_words_in_view(page, live_server, width, height):
    page.set_viewport_size({"width": width, "height": height})
    page.add_init_script(PREPARE)
    hold_dashboard(page)
    page.goto(f"{live_server.base_url}/#home", wait_until="commit")
    wait_until_shown(page)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    for selector in ("#boot-splash .uw-mascot", "#boot-splash .boot-splash-title"):
        box = page.locator(selector).bounding_box()
        assert box["x"] >= 0 and box["y"] >= 0 and box["x"] + box["width"] <= width and box["y"] + box["height"] <= height, (selector, box)


def test_the_mascot_blinks_hops_and_turns_when_tapped_in_the_advisor_card(page, live_server):
    enter_public_site(page, live_server, "advisor")
    mascot = page.locator("#advisor-assistant .uw-mascot")
    expect(mascot).to_be_visible()
    assert {"uw-mascot-idle", "uw-mascot-blink", "uw-mascot-look"} <= set(animation_names(page, "#advisor-assistant .uw-mascot"))
    seen = []
    for expected in ("hop", "spin", "wink", "hop"):
        mascot.click()
        expect(mascot).to_have_class(re.compile(rf"\bis-{expected}\b"))
        seen.append(expected)
        expect(mascot).not_to_have_class(re.compile(rf"\bis-{expected}\b"), timeout=4_000)
    assert seen == ["hop", "spin", "wink", "hop"]
    assert "uw-mascot-idle" in animation_names(page, "#advisor-assistant .uw-mascot"), "back to idling afterwards"


def test_the_mascot_acts_out_each_state_of_the_assistant(page, live_server):
    enter_public_site(page, live_server, "advisor")
    expected = {
        "idle": "uw-mascot-idle",
        "loading": "advisor-mascot-loading-bob",
        "success": "advisor-mascot-success-pop",
        "insufficient": "advisor-mascot-insufficient-tilt",
    }
    for state, animation in expected.items():
        page.evaluate("state => setAdvisorAssistantState(state)", state)
        names = page.evaluate("document.querySelector('#advisor-assistant .uw-mascot-body').getAnimations().map(a => a.animationName)")
        assert animation in names, (state, names)
    page.evaluate("setAdvisorAssistantState('error')")
    names = page.evaluate("document.querySelector('#advisor-assistant .uw-mascot-body').getAnimations().map(a => a.animationName)")
    assert "uw-mascot-idle" not in names, "an error is not met with a cheerful bounce"


def test_the_old_puppy_is_not_anywhere_on_the_page(page, live_server):
    enter_public_site(page, live_server, "advisor")
    sources = page.evaluate("[...document.images].map(img => img.currentSrc || img.src)")
    assert not [src for src in sources if "advisor-mascot" in src], sources
    assert any("assets/mascot/suitcase.webp" in src for src in sources)
