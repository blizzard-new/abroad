"""The scoped refresh keeps decisions readable, reachable and honest in both themes."""
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_application_and_search_share_readable_headings_without_overflow(page, live_server, width, theme):
    page.set_viewport_size({"width": width, "height": 900})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script(f"localStorage.setItem('exchange-guide-theme', '{theme}')")
    sizes = []
    left_edges = []
    for route, heading in (("partners", "#partners-title"), ("my-application", "#application-path h1"),
                           ("eligibility", "#eligibility-title"), ("application-center", "#application-center-title")):
        enter_public_site(page, live_server, route, view="list")
        title = page.locator(heading)
        expect(title).to_be_visible()
        sizes.append(title.evaluate("el => parseFloat(getComputedStyle(el).fontSize)"))
        left_edges.append(title.bounding_box()["x"])
        if route in ("partners", "my-application"):
            assert abs(title.bounding_box()["x"] - page.locator("#school-switcher").bounding_box()["x"]) < 1
        assert title.evaluate("el => +getComputedStyle(el).fontWeight") == 700
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (route, width, theme)
    assert max(sizes) - min(sizes) < 1, sizes
    assert max(left_edges) - min(left_edges) < 1, left_edges
    enter_public_site(page, live_server, "eligibility")
    trigger = page.locator("#advisor-form .glide-select__trigger:visible").first
    trigger.focus()
    expect(trigger).to_be_focused()
    assert trigger.bounding_box()["height"] >= 44
    assert trigger.evaluate("el => getComputedStyle(el).outlineStyle") != "none"


def test_detail_separates_missing_information_mismatches_and_closed_places(page, live_server):
    page.emulate_media(reduced_motion="reduce")
    enter_public_site(page, live_server, "partners", view="list")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#school-detail-view")).to_be_visible()
    # Exercise presentation with rule outcomes, including reasons that are NOT qualification checks.
    # Preserve the real catalogue and rule implementation outside each render.
    def show(profile, tone, blocked=False, pending=False):
        page.evaluate("""({profile, tone, blocked, pending}) => {
          const originalMatch = partnerMatch, originalAvailability = partnerAvailabilityMeta;
          const originalProfile = state.eligibilityProfile;
          try {
            state.eligibilityProfile = profile ? { ...originalProfile } : null;
            partnerMatch = () => ({tone, label: tone === 'blocked' ? '語言分數未達門檻' : '條件待補齊',
              reasons: ['位於優先國家', '申請流程已查核'], risks: tone === 'strong' ? [] : ['合作校語言門檻需另查']});
            partnerAvailabilityMeta = () => ({blocked, pending,
              cardLabel: pending ? '本期名額待核實' : '本期未開放',
              reason: pending ? '本期甄選名額尚未核實' : '當期名額為零'});
            window.UniWayDetail.refresh();
          } finally {
            partnerMatch = originalMatch; partnerAvailabilityMeta = originalAvailability;
            state.eligibilityProfile = originalProfile;
          }
        }""", {"profile": profile, "tone": tone, "blocked": blocked, "pending": pending})

    fit = page.locator("#booking-fit")
    for profile, tone, blocked, label in (
        (False, "setup", False, "尚未比對你的條件"),
        (True, "review", False, "資格待確認"),
        (True, "blocked", False, "目前條件不符"),
        (True, "strong", False, "已知條件初步相符"),
        (True, "blocked", True, "本期未開放"),
    ):
        show(profile, tone, blocked)
        expect(fit).to_contain_text(label)
        expect(fit).not_to_contain_text(re.compile(r"符合\s*\d+\s*/\s*\d+"))
        if blocked:
            expect(page.locator(".pr-requirements")).to_contain_text("當期名額為零")
            expect(page.locator(".pr-requirements .ok")).to_have_count(0)
        elif profile and tone == "strong":
            expect(fit).to_contain_text("正式資格以校方認定為準")
    show(True, "strong", pending=True)
    expect(fit).to_have_attribute("data-status", "needs_confirmation")
    expect(fit).to_contain_text("本期名額待核實")
    expect(fit).not_to_contain_text("已知條件初步相符")
    expect(page.locator(".pr-requirements")).to_contain_text("本期甄選名額尚未核實")
    page.set_viewport_size({"width": 390, "height": 844})
    show(False, "setup")
    expect(fit.get_by_role("link", name="填寫條件")).to_be_visible()
    assert page.locator(".pr-booking").bounding_box()["height"] <= 160
    expect(page.locator(".pr-requirements")).to_contain_text("正式結果以校方認定為準")
