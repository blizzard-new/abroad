"""Homepage scroll choreography stays optional and never owns routing or progress."""
import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site


def center_stage(page, number):
    page.locator(".pr-stages > li").nth(number).evaluate(
        "el => window.scrollTo({top: scrollY + el.getBoundingClientRect().top + el.offsetHeight / 2 - innerHeight * .52, behavior: 'instant'})"
    )
    expect(page.locator(".hm-route-index")).to_have_text(f"{number + 1:02d} / 04")


def test_scroll_story_is_reversible_and_keeps_real_navigation(page, live_server):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server)
    original_plan = page.locator("#home-plan-steps").inner_text()
    center_stage(page, 0)
    first_plane = page.locator(".hm-route-plane").get_attribute("transform")
    center_stage(page, 1)
    sticky_top = page.locator(".hm-journey-intro").bounding_box()["y"]
    center_stage(page, 2)
    assert page.locator(".hm-route-plane").get_attribute("transform") != first_plane
    assert abs(page.locator(".hm-journey-intro").bounding_box()["y"] - sticky_top) < 2
    expect(page.locator(".hm-route-title")).to_have_text("完成合作校申請")
    center_stage(page, 1)
    expect(page.locator(".hm-route-title")).to_have_text("準備校內甄選")
    # The illustration describes the section being read, never changes the saved plan.
    assert page.locator("#home-plan-steps").inner_text() == original_plan
    page.locator(".pr-stages > li").first.get_by_role("link").click()
    expect(page.locator("#partners")).to_be_visible()
    assert page.evaluate(
        "() => !document.getAnimations().some(a => a.id === 'uniway:home-reveal')"
    )
    page.go_back()
    expect(page.locator("#home-landing")).to_be_visible()
    center_stage(page, 2)
    assert not errors


@pytest.mark.parametrize("width,theme", [(1440, "light"), (834, "dark"), (393, "light"), (360, "dark")])
def test_home_motion_fits_and_remains_readable(browser, live_server, width, theme):
    context = browser.new_context(viewport={"width": width, "height": 900})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(f"localStorage.setItem('exchange-guide-theme', '{theme}')")
    try:
        enter_public_site(page, live_server)
        page.get_by_role("button", name="往下探索你的交換旅程").click()
        expect(page.locator("#home-guides-title")).to_be_in_viewport()
        for selector in [".pr-features", ".pr-map-band", ".pr-journey", ".pr-forum-preview", ".pr-footer"]:
            page.locator(selector).scroll_into_view_if_needed()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        center_stage(page, 2)
        if width <= 700:
            expect(page.locator(".hm-route-card")).to_be_hidden()
            assert page.locator(".hm-journey-intro").evaluate("el => getComputedStyle(el).position") == "static"
        expect(page.locator(".pr-stages > li").nth(2).get_by_role("link")).to_be_visible()
        assert not errors
    finally:
        context.close()


def test_live_reduced_motion_and_unavailable_motion_script_are_readable(page, live_server):
    enter_public_site(page, live_server)
    center_stage(page, 2)
    page.emulate_media(reduced_motion="reduce")
    expect(page.locator(".pr-stages > li[data-reading]")).to_have_count(0)
    assert page.locator(".hm-journey-intro").evaluate("el => getComputedStyle(el).position") == "static"
    assert page.evaluate("() => !document.getAnimations().some(a => a.id === 'uniway:home-reveal')")
    page.locator(".pr-editorial").scroll_into_view_if_needed()
    for card in page.locator(".pr-guide-card").all():
        expect(card).to_have_css("opacity", "1")
        expect(card).to_have_css("transform", "none")
    page.emulate_media(reduced_motion="no-preference")
    center_stage(page, 1)
    page.route("**/home-motion.js*", lambda route: route.abort())
    page.reload()
    page.locator("#boot-splash").wait_for(state="hidden")
    assert page.evaluate("typeof window.UniWayHomeMotion") == "undefined"
    for selector in [".pr-guide-card", ".pr-tile", ".pr-stages > li"]:
        for item in page.locator(selector).all():
            expect(item).to_have_css("opacity", "1")
    page.locator(".pr-stages > li").first.get_by_role("link").click()
    expect(page.locator("#partners")).to_be_visible()
