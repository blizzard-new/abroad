"""Exercise motion without replacing real routing, disclosure or account behavior."""
from pathlib import Path
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_partner_globe import LINCOLN, MEIJI, open_partners
from .test_discovery_workspace import setup_catalog

INSTRUMENT = """(() => {
  window.__motionLog = [];
  const original = Element.prototype.animate;
  Element.prototype.animate = function (frames, options) {
    const animation = original.call(this, frames, options);
    window.__motionLog.push({animation, id: this.id, classes: this.className, frames, options});
    return animation;
  };
  localStorage.setItem('exchange-guide-home-school', '長庚大學');
})();"""


def motions(page, kind=None):
    return page.evaluate("kind => __motionLog.filter(x => x.animation.id.startsWith('uniway:') && (!kind || x.animation.id === 'uniway:' + kind)).map(x => ({id:x.id, kind:x.animation.id, frames:x.frames, duration:x.options.duration, delay:x.options.delay}))", kind)


def test_all_routes_share_motion_and_back_retains_working_history(page, live_server):
    page.add_init_script(INSTRUMENT)
    enter_public_site(page, live_server)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    for route in ["forum", "partners", "favorites", "overview", "eligibility", "advisor", "application-center", "document-check", "writing-assistant", "documents", "calendar", "deadlines", "scholarships", "budget", "university-posts"]:
        if route in ["forum", "partners"]:
            link = page.locator(f'.uniway-public-nav a[href="#{route}"]')
        else:
            page.locator("#application-tools .application-nav-chevron").click()
            link = page.locator(f'.application-tools-panel a[href="#{route}"]')
            if page.locator(".application-extra-tools").get_attribute("open") is None and link.locator("xpath=ancestor::details[contains(@class, 'application-extra-tools')]").count():
                page.locator(".application-extra-tools > summary").click()
        before = len(motions(page, "route"))
        link.click()
        expect(page).to_have_url(re.compile(rf"#{route}$"))
        page.wait_for_function("n => __motionLog.filter(x => x.animation.id === 'uniway:route').length > n", arg=before)
        assert all("transform" not in frame for frame in motions(page, "route")[-1]["frames"])
        if route == "calendar":
            month = page.locator("#calendar-month-label").inner_text()
            count = len(motions(page, "result"))
            page.locator("#calendar-next-month").click()
            expect(page.locator("#calendar-month-label")).not_to_have_text(month)
            page.wait_for_function("n => __motionLog.filter(x => x.animation.id === 'uniway:result').length > n", arg=count)
            assert any(x["id"] == "application-calendar-grid" for x in motions(page, "result"))
        page.locator("#page-back").click()
        expect(page).to_have_url(re.compile(r"#home$"))
    assert not errors
    page.wait_for_function("() => !document.getAnimations().some(a => a.id.startsWith('uniway:'))")


@pytest.mark.parametrize("width", [393, 834, 1440])
def test_dialog_menu_details_tabs_and_mobile_layout(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 940})
    page.add_init_script(INSTRUMENT)
    setup_catalog(page)
    enter_public_site(page, live_server)
    # The school switcher is in the page toolbar, outside the navigation drawer.
    page.locator("#school-switcher").click()
    expect(page.locator("#school-onboarding")).to_be_visible()
    page.wait_for_function("() => __motionLog.some(x => x.animation.id === 'uniway:dialog')")
    page.locator("#school-options .school-option.selected").click()
    expect(page.locator("#school-onboarding")).to_be_hidden()
    open_navigation(page)
    page.locator('.uniway-public-nav a[href="#forum"]').click()
    open_navigation(page)
    page.locator('.uniway-public-nav a[href="#home"]').click()
    expect(page.locator("#guide").get_by_role("heading", level=1)).to_be_focused()
    summary = page.locator(".guide-faq summary")
    summary.focus()
    page.keyboard.press("Enter")
    expect(page.locator(".guide-faq")).to_have_attribute("open", "")
    expect(page.locator(".guide-faq p")).to_be_visible()
    page.keyboard.press("Enter")
    expect(page.locator(".guide-faq")).not_to_have_attribute("open", "")
    page.wait_for_function("() => !document.querySelector('.guide-faq').getAnimations({subtree:true}).some(a => a.playState === 'running')")
    expect(summary).to_be_focused()
    # Closing the tools menu must immediately release the page, including Escape.
    open_navigation(page)
    page.locator("#application-tools .application-nav-chevron").click()
    page.keyboard.press("Escape")
    expect(page.locator(".application-tools-panel")).to_be_hidden()
    page.goto(f"{live_server.base_url}/#school={LINCOLN}")
    page.locator('#detail-tab-life').click()
    expect(page.locator("#detail-life")).to_be_visible()
    page.locator('#detail-tab-overview').click()
    expect(page.locator("#detail-overview")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    artifacts = Path("output/system-motion"); artifacts.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(artifacts / f"school-{width}.png"), animations="disabled")


def test_search_updates_are_bounded_and_rapid_navigation_cancels_old_motion(page, live_server):
    page.add_init_script(INSTRUMENT)
    setup_catalog(page)
    open_partners(page, live_server, {"view": "list"})
    page.locator("#partner-search").fill("Lincoln")
    expect(page.locator(".desktop-partner-table .school-detail-trigger")).to_have_text(LINCOLN)
    page.locator("#partner-search").fill("Meiji")
    expect(page.locator(".desktop-partner-table .school-detail-trigger")).to_have_text(MEIJI)
    assert all(x["delay"] <= 90 for x in motions(page, "result"))
    # User navigation may arrive before the previous animation completes.
    for route in ("forum", "home", "partners", "forum"):
        page.locator(f'.uniway-public-nav a[href="#{route}"]').first.click()
    expect(page.locator("#community-hub")).to_be_visible()
    # Routing queues its animation in requestAnimationFrame. An empty current
    # animation list can precede that queued frame, so drain actual frames first.
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    page.wait_for_function("() => !document.getAnimations().some(a => a.id.startsWith('uniway:')) && getComputedStyle(document.querySelector('#community-hub')).opacity === '1'")
    assert page.locator("#community-hub").evaluate("el => getComputedStyle(el).opacity") == "1"


def test_reduced_motion_live_change_and_missing_runtime_are_usable(page, live_server):
    page.add_init_script(INSTRUMENT)
    page.emulate_media(reduced_motion="reduce")
    enter_public_site(page, live_server)
    page.locator(".guide-faq summary").click()
    assert motions(page) == []
    assert page.locator(".guide-faq").evaluate("el => getComputedStyle(el, '::details-content').transitionDuration") == "0s"
    page.emulate_media(reduced_motion="no-preference")
    open_navigation(page)
    page.locator('.uniway-public-nav a[href="#forum"]').click()
    page.wait_for_function("() => __motionLog.some(x => x.animation.id === 'uniway:route')")
    page.emulate_media(reduced_motion="reduce")
    page.wait_for_function("() => !document.getAnimations().some(a => a.id.startsWith('uniway:'))")
    page.locator("#school-switcher").click()
    # Visitors pick their school without signing in.
    expect(page.locator("#school-onboarding")).to_be_visible()
    expect(page.locator("#auth-dialog")).to_be_hidden()
    page.locator('[data-home-school="長庚大學"]').click()
    expect(page.locator("#school-onboarding")).to_be_hidden()
    # Progressive enhancement must not become a dependency for using the app.
    page.route("**/motion.js?*", lambda route: route.abort())
    page.reload()
    open_navigation(page)
    page.locator('.uniway-public-nav a[href="#home"]').click()
    expect(page.locator("#guide")).to_be_visible()
    # Move out of the expanding rail before using a page control behind it.
    page.mouse.move(1000, 24)
    expect(page.locator("#glass-navigation")).to_have_css("width", "76px")
    page.locator("#page-back").click()
    expect(page.locator("#community-hub")).to_be_visible()
