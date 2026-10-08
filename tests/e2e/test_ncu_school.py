"""Verify NCU source scope, host documents and life content in real Chromium."""

from pathlib import Path
import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until, sign_in_cookie, attach_session


@pytest.mark.parametrize("width", [390, 1440])
def test_ncu_content_source_pages_home_host_and_life(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator("#confirm-school").click()
    if (
        width < 700
        and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true"
    ):
        page.locator("#glass-menu-toggle").click()
    wait_until(
        page,
        "state.dashboard?.school_name === '國立中央大學' && state.dashboard.partner_universities.length === 214",
    )
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("史特拉斯堡")
    expect(page.locator("#partner-table")).to_contain_text("本期名額待公告")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(
        page.locator("#school-detail-view .partner-student-summary")
    ).to_contain_text("2025–26")
    expect(
        page.locator("#school-detail-view .partner-student-summary")
    ).to_contain_text("強烈建議")
    page.locator("#ncu-source-audit > summary").click()
    expect(page.locator("#ncu-source-audit-body")).to_contain_text("2027–28價格")
    expect(page.locator("#ncu-source-audit-body")).to_contain_text(
        "Factsheet_Unistra_2027-28"
    )
    home_source = (
        page.locator("#ncu-source-audit-body li")
        .filter(has_text="校內甄選文件")
        .locator("details")
        .first
    )
    home_source.locator(":scope > summary").click()
    expect(home_source.locator("pre")).to_contain_text("國際移動力")
    source = (
        page.locator("#ncu-source-audit-body > details")
        .filter(has_text="Factsheet_Unistra_2027-28")
        .first
    )
    source.locator(":scope > summary").click()
    source.locator("details > summary").last.click()
    expect(source.locator("pre").last).to_contain_text("2025")
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / f"ncu-source-{width}.png"), full_page=True)
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_contain_text("家長同意書")
    expect(page.locator("#detail-application")).to_contain_text("Learning agreement")
    expect(page.locator("#detail-application")).to_contain_text("12/11")
    page.screenshot(path=str(out / f"ncu-workflow-{width}.png"), full_page=True)
    page.locator("#detail-tab-life").click()
    expect(page.locator("#detail-life")).to_contain_text("2025–26")
    expect(page.locator("#detail-life")).to_contain_text("201–550")
    page.screenshot(path=str(out / f"ncu-life-{width}.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_ncu_grade_scale_year_exclusion_and_real_document_form(page, live_server):
    session = sign_in_cookie(live_server, school="國立中央大學")
    live_server.verify_student(session["profile"]["id"], university="國立中央大學")
    attach_session(page, live_server, session)
    enter_public_site(page, live_server, "advisor")
    expect(page.locator("#advisor-academic-score")).to_be_visible()
    expect(page.locator("#advisor-academic-rule")).to_contain_text("60分")
    expect(page.locator("#advisor-academic-rule")).to_contain_text("70分")
    assert page.evaluate(
        "homeAcademicPass({degree:'大學部',currentYear:'大三',academicScore:60})"
    )
    assert not page.evaluate(
        "homeAcademicPass({degree:'大學部',currentYear:'大五',academicScore:99})"
    )
    assert page.evaluate("homeAcademicPass({degree:'在職碩士班',academicScore:70})")
    assert not page.evaluate("homeAcademicPass({degree:'研究所',academicScore:69})")
    page.evaluate("location.hash='#application-center'")
    page.locator(
        '[data-open-application-template="exchange-application-data"]'
    ).first.click()
    expect(page.locator("#application-document-form")).to_be_visible()
    test = page.locator("#application-field-language_test")
    actual = page.locator("#application-field-language_result_date")
    assert test.evaluate("node=>node.required") and actual.evaluate(
        "node=>node.required"
    )
    assert "TOEIC（聽讀）" in test.locator("option").all_text_contents()
    expect(page.locator("#application-document-fields")).to_contain_text("實際考試日期")
    actual.fill("2100-01-01")
    assert actual.evaluate("node=>node.validity.rangeOverflow")
