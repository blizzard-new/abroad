"""First-time application entry and progressive disclosure, using isolated data."""
import pytest
from playwright.sync_api import expect

from .test_glass_theme import capture, verified_login
from .conftest import expand_details


@pytest.mark.parametrize("width,theme", [(390, "light"), (1440, "light"), (390, "dark")])
def test_first_visit_has_a_clear_start_and_optional_tools(page, live_server, width, theme):
    page.set_viewport_size({"width": width, "height": 960})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school', '長庚大學')")
    page.add_init_script(f"localStorage.setItem('exchange-guide-theme', '{theme}')")
    page.goto(f"{live_server.base_url}/#advisor")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#advisor-form")).to_be_visible()
    expect(page.locator("#advisor-title")).to_have_text("先從認識你開始")
    expect(page.locator("#advisor-academic-score")).to_be_hidden()
    expect(page.locator("#advisor-question")).to_be_hidden()
    expect(page.locator("#application-workspace-tools")).to_be_hidden()
    expect(page.get_by_role("link", name="還沒有方向？先逛交換學校")).to_have_attribute("href", "#partners")
    page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    capture(page, f"01-entry-{width}-{theme}.png")
    summary = page.locator("#application-workspace-tool-menu > summary")
    summary.focus()
    page.keyboard.press("Enter")
    page.get_by_role("link", name="當期資格與志願", exact=True).click()
    expect(page.locator("#advisor-academic-score")).to_be_visible()
    assert page.evaluate("Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_preparation_prioritizes_next_action_and_retains_secondary_tools(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 960})
    page.emulate_media(reduced_motion="reduce")
    verified_login(page, live_server)
    expect(page.locator("#page-status .status-message")).to_have_count(0)
    page.evaluate("location.hash='#overview'")
    expect(page.locator("#overview")).to_be_visible()
    expect(page.locator("#planning-next-action")).to_contain_text("從你的條件開始")
    assert page.locator("#planning-next-action").bounding_box()["y"] < page.locator("#my-applications").bounding_box()["y"]
    expect(page.locator("#tracker-stats")).to_be_hidden()
    expect(page.locator("#personal-plan-snapshot")).to_be_hidden()
    expect(page.locator("#journey-availability-form")).to_be_hidden()
    capture(page, f"02-preparation-{width}.png")
    expand_details(page, "#application-plan-details")
    expect(page.locator("#personal-plan-snapshot")).to_be_visible()
    expand_details(page, "#application-schedule-details")
    expand_details(page, "#journey-capacity-settings")
    expect(page.locator("#journey-availability-form")).to_be_visible()
    page.evaluate("location.hash='#application-center'")
    expect(page.locator("#application-center")).to_be_visible()
    expect(page.locator(".application-center-steps strong").first).to_be_visible()
    assert page.evaluate("Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) <= innerWidth")
    capture(page, f"03-documents-{width}.png")
    subsidy = page.locator('#application-context-form input[name="subsidy"]')
    expect(subsidy).not_to_be_checked()
    subsidy.focus()
    page.keyboard.press("Space")
    expect(subsidy).to_be_checked()


def test_invalid_optional_field_is_revealed_and_draft_is_kept(page, live_server):
    verified_login(page, live_server)
    page.evaluate("location.hash='#advisor'")
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-degree").select_option("大學部")
    expand_details(page, "#advisor-qualification-fields")
    score = page.locator("#advisor-academic-score")
    score.fill("101")
    page.locator("#advisor-qualification-fields > summary").click()
    page.locator("#advisor-submit").click()
    expect(score).to_be_visible()
    expect(score).to_be_focused()
    expect(score).to_have_value("101")
    score.fill("85")
    page.locator("#advisor-qualification-fields > summary").click()
    with page.expect_response(lambda r: r.url.endswith("/advisor/plan") and r.request.method == "POST") as saved:
        page.locator("#advisor-submit").click()
    assert saved.value.ok
    assert saved.value.request.post_data_json["academic_score"] == 85
    assert saved.value.request.post_data_json["language_score"] is None
    expect(page.locator("#advisor-result-content [data-planning-target]").first).to_be_visible()
