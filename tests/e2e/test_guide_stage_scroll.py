"""The guide index keeps the cards of the stage being read in view on wide screens, and stays plain content elsewhere."""
import pytest
from playwright.sync_api import expect

from exchange_info.seo_articles import ARTICLES, STAGE_NOTES

STAGES = len([category for category in STAGE_NOTES if any(a.category == category for a in ARTICLES.values())])


def active_stage(page) -> int:
    return page.evaluate(
        "[...document.querySelectorAll('[data-stage-block]')].findIndex(block => block.hasAttribute('data-active'))")


def panel_opacities(page) -> list[float]:
    return page.evaluate(
        "[...document.querySelectorAll('[data-stage-cards]')].map(el => Number(getComputedStyle(el).opacity))")


def open_guides(browser, live_server, **options):
    context = browser.new_context(**options)
    page = context.new_page()
    page.goto(live_server.base_url + "/guides")
    return context, page


def test_wide_screen_tracks_the_stage_in_the_middle_of_the_viewport(browser, live_server):
    context, page = open_guides(browser, live_server, viewport={"width": 1440, "height": 900})
    try:
        expect(page.locator("[data-stage-scroll]")).to_have_attribute("data-stage-scroll", "ready")
        assert active_stage(page) == 0
        # The panels cross-fade, so wait for each opacity to settle instead of reading it mid-transition.
        panels = page.locator("[data-stage-cards]")
        expect(panels.nth(0)).to_have_css("opacity", "1")
        for other in range(1, STAGES):
            expect(panels.nth(other)).to_have_css("opacity", "0")
        for index in range(1, STAGES):
            page.locator("[data-stage-copy]").nth(index).evaluate("el => el.scrollIntoView({ block: 'center' })")
            page.wait_for_function(
                "index => document.querySelectorAll('[data-stage-block]')[index].hasAttribute('data-active')", arg=index)
            for other in range(STAGES):
                expect(panels.nth(other)).to_have_css("opacity", "1" if other == index else "0")
        # Cards stay put while the stage list scrolls past them: the panel is pinned near the top of the viewport.
        top = page.locator("[data-stage-cards]").nth(STAGES - 1).evaluate("el => el.getBoundingClientRect().top")
        assert 0 <= top <= 80
    finally:
        context.close()


def test_every_card_is_present_once_and_clicking_a_stage_brings_it_into_view(browser, live_server):
    context, page = open_guides(browser, live_server, viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    try:
        assert page.locator(".editorial-card").count() == len(ARTICLES)
        page.locator("[data-stage-copy]").nth(STAGES - 1).locator("h2").click()
        page.wait_for_function(
            "index => document.querySelectorAll('[data-stage-block]')[index].hasAttribute('data-active')", arg=STAGES - 1)
        expect(page.locator("[data-stage-cards]").nth(STAGES - 1).locator(".editorial-card a").first).to_be_visible()
        # The category chips at the top are real anchors to the same stages.
        page.locator(".editorial-categories a").first.click()
        page.wait_for_function("() => document.querySelectorAll('[data-stage-block]')[0].hasAttribute('data-active')")
    finally:
        context.close()


def test_keyboard_focus_reveals_the_cards_of_its_stage(browser, live_server):
    context, page = open_guides(browser, live_server, viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    try:
        # Cards of other stages are only faded out, never removed from the tab order.
        page.locator("[data-stage-cards]").nth(1).locator(".editorial-card a").first.focus()
        page.wait_for_function("() => document.querySelectorAll('[data-stage-block]')[1].hasAttribute('data-active')")
        expect(page.locator("[data-stage-cards]").nth(1)).to_have_css("opacity", "1")
        expect(page.locator("[data-stage-cards]").nth(1).locator(".editorial-card a").first).to_be_in_viewport()
    finally:
        context.close()


@pytest.mark.parametrize("options", [
    {"viewport": {"width": 390, "height": 844}},
    {"viewport": {"width": 1024 - 1, "height": 900}},
    {"viewport": {"width": 1440, "height": 900}, "java_script_enabled": False},
], ids=["phone", "just-below-wide", "no-javascript"])
def test_stacked_layout_shows_every_stage_without_the_scroll_panel(browser, live_server, options):
    context, page = open_guides(browser, live_server, **options)
    try:
        assert page.locator("[data-stage-scroll]").get_attribute("data-stage-scroll") in ("", None)
        assert panel_opacities(page) == [1] * STAGES
        assert page.evaluate("[...document.querySelectorAll('[data-stage-cards]')].every(el => getComputedStyle(el).position === 'static')")
        for index in range(STAGES):
            expect(page.locator("[data-stage-copy] h2").nth(index)).to_be_visible()
            expect(page.locator("[data-stage-cards]").nth(index).locator(".editorial-card").first).to_be_visible()
        assert page.locator(".stage-desc").count() == STAGES
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    finally:
        context.close()


def test_resizing_between_layouts_enables_and_disables_the_panel(browser, live_server):
    context, page = open_guides(browser, live_server, viewport={"width": 1440, "height": 900})
    try:
        expect(page.locator("[data-stage-scroll]")).to_have_attribute("data-stage-scroll", "ready")
        page.set_viewport_size({"width": 700, "height": 900})
        page.wait_for_function("() => document.querySelector('[data-stage-scroll]').dataset.stageScroll === ''")
        assert panel_opacities(page) == [1] * STAGES
        assert page.locator("[data-stage-block][data-active]").count() == 0
        page.set_viewport_size({"width": 1440, "height": 900})
        expect(page.locator("[data-stage-scroll]")).to_have_attribute("data-stage-scroll", "ready")
        assert active_stage(page) >= 0
    finally:
        context.close()


def test_reduced_motion_removes_the_stage_transitions(browser, live_server):
    context, page = open_guides(browser, live_server, viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    try:
        cards = page.locator("[data-stage-cards]").first
        copy = page.locator("[data-stage-copy]").first
        assert cards.evaluate("el => getComputedStyle(el).transitionDuration") == "0s"
        assert copy.evaluate("el => getComputedStyle(el).transitionDuration") == "0s"
    finally:
        context.close()
    context, page = open_guides(browser, live_server, viewport={"width": 1440, "height": 900}, reduced_motion="no-preference")
    try:
        assert page.locator("[data-stage-cards]").first.evaluate("el => getComputedStyle(el).transitionDuration") != "0s"
    finally:
        context.close()
