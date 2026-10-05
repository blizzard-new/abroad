"""Clicking 我的申請 in the left rail opens 選校與確認 first, whoever is clicking."""
from playwright.sync_api import expect

from .conftest import open_navigation

NTPU = "國立臺北大學"
ENTRY = '.uniway-public-nav a[data-public-route="overview"]'


def assert_selection_page(page) -> None:
    expect(page.locator("#advisor")).to_be_visible()
    expect(page.locator('#application-journey-steps [aria-current="step"]')).to_contain_text("選校與確認")
    assert page.evaluate("location.hash") == "#advisor"


def test_new_student_picks_a_school_and_lands_on_selection_and_confirmation(page, live_server):
    page.goto(f"{live_server.base_url}/#home")
    page.wait_for_load_state("networkidle", timeout=60_000)
    open_navigation(page)
    page.locator(ENTRY).click()
    expect(page.locator("#school-onboarding")).to_be_visible()
    page.locator(f'[data-home-school="{NTPU}"]').click()
    page.locator("#confirm-school").click()
    expect(page.locator("#school-onboarding")).to_be_hidden()
    assert_selection_page(page)


def test_returning_student_with_a_school_goes_straight_there_from_any_page(page, live_server):
    page.add_init_script(f"window.localStorage.setItem('exchange-guide-home-school', '{NTPU}')")
    page.goto(f"{live_server.base_url}/#partners")
    page.wait_for_load_state("networkidle", timeout=60_000)
    open_navigation(page)
    page.locator(ENTRY).click()
    assert_selection_page(page)
    # From the preparation stage the same door still leads back to selection, and the other stages stay one click away.
    page.locator('#application-journey-steps [data-workspace-stage="preparation"]').click()
    expect(page.locator("#overview")).to_be_visible()
    open_navigation(page)
    page.locator(ENTRY).click()
    assert_selection_page(page)
    page.locator('#application-journey-steps [data-workspace-stage="documents"]').click()
    expect(page.locator('#application-journey-steps [aria-current="step"]')).to_contain_text("文件與送件")


def test_the_rail_entry_is_highlighted_on_the_selection_page_and_the_dropdown_still_offers_every_stage(page, live_server):
    page.add_init_script(f"window.localStorage.setItem('exchange-guide-home-school', '{NTPU}')")
    page.goto(f"{live_server.base_url}/#advisor")
    page.wait_for_load_state("networkidle", timeout=60_000)
    open_navigation(page)
    expect(page.locator(ENTRY)).to_have_attribute("aria-current", "page")
    page.locator("#application-tools summary .application-nav-chevron").click()
    panel = page.locator(".application-tools-panel")
    expect(panel.locator("a").nth(0)).to_have_text("選校與確認")
    expect(panel.locator("a").nth(1)).to_have_text("準備與時程")
    panel.locator("a", has_text="準備與時程").click()
    expect(page.locator("#overview")).to_be_visible()
