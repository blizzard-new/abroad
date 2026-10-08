"""The third school uses its own catalogue, pending labels and grade scale."""
import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until
from .test_open_catalog import attach_session, sign_in_cookie
from .test_web_next_phase import _wait_for_workspace


@pytest.mark.parametrize("width", [390, 1440])
def test_visitor_can_browse_ntu_filter_details_and_switch_back(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    expect(page.locator("#school-options [data-home-school]")).to_have_count(3)
    page.locator('[data-home-school="國立臺灣大學"]').click()
    page.locator("#confirm-school").click()
    if width < 700 and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    expect(page.locator("#school-switcher-label")).to_have_text("國立臺灣大學")
    wait_until(page, "state.dashboard?.school_name === '國立臺灣大學' && state.dashboard.partner_universities.length === 288")
    page.evaluate("location.hash='#partners'")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("蒙大拿州立大學")
    expect(page.locator("#partner-table")).to_contain_text("蒙大拿州立大學")
    expect(page.locator("#partner-table")).to_contain_text("本期未公告")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#school-detail-view")).to_be_visible()
    expect(page.locator("#school-detail-view")).to_contain_text("蒙大拿州立大學")
    expect(page.locator("#school-detail-view")).to_contain_text("待確認")
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_be_visible()
    expect(page.locator("#detail-application")).to_contain_text("臺大")
    page.evaluate("location.hash='#advisor'")
    expect(page.locator("#advisor-academic-score")).to_be_hidden()
    expect(page.locator("#advisor-academic-gpa")).to_be_visible()
    expect(page.locator("#advisor-class-rank")).to_be_visible()
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-department").fill("機械工程學系")
    expect(page.locator("#advisor-department")).to_have_value("機械工程學系")
    expect(page.locator("#advisor-academic-rule")).to_contain_text("研究生無校內成績門檻")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="長庚大學"]').click()
    page.locator("#confirm-school").click()
    if width < 700 and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '長庚大學'")
    page.evaluate("location.hash='#advisor'")
    expect(page.locator("#advisor-academic-score")).to_be_visible()
    expect(page.locator("#advisor-academic-gpa")).to_be_hidden()
    assert page.locator("#advisor-department").evaluate("node => node.tagName") == "SELECT"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_ntu_saved_conditions_keep_gpa_and_rank_without_percent_conversion(page, live_server):
    session = sign_in_cookie(live_server, school="國立臺灣大學")
    attach_session(page, live_server, session)
    enter_public_site(page, live_server, "advisor")
    expect(page.locator("#advisor-academic-gpa")).to_be_visible()
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-department").fill("機械工程學系")
    page.locator("#advisor-degree").select_option("大學部")
    page.locator("#advisor-academic-gpa").fill("2.3")
    page.locator("#advisor-class-rank").fill("30")
    page.locator("#advisor-language-test").select_option("toefl_new")
    page.locator("#advisor-language-score").fill("4")
    with page.expect_response(lambda response: response.url.endswith("/advisor/plan") and response.request.method == "POST") as response:
        page.locator("#advisor-submit").click()
    assert response.value.ok
    payload = response.value.request.post_data_json
    assert payload["academic_score"] is None
    assert payload["academic_gpa"] == 2.3 and payload["class_rank_percent"] == 30
    assert "符合校內成績擇一門檻" in str(response.value.json())
    saved = _wait_for_workspace(live_server, session, lambda item:
        ((item.get("workspace", {}).get("selection_conditions") or {}).get("profile") or {}).get("class_rank_percent") == 30,
        home_school="國立臺灣大學"
    )["workspace"]["selection_conditions"]["profile"]
    assert saved["academic_gpa"] == 2.3 and saved["academic_score"] is None
    page.reload()
    expect(page.locator("#advisor-academic-gpa")).to_have_value("2.3")
    expect(page.locator("#advisor-class-rank")).to_have_value("30")
