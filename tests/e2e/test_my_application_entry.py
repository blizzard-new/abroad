"""The map and scheduling have separate, direct navigation entries."""
from playwright.sync_api import expect
from .conftest import open_navigation

NTPU = '國立臺北大學'
ENTRY = '.uniway-public-nav a[data-public-route="my-application"]'


def test_new_student_selects_a_school_then_reaches_the_map_login(page, live_server):
    page.goto(f'{live_server.base_url}/#home')
    page.wait_for_load_state('networkidle', timeout=60000)
    open_navigation(page)
    page.locator(ENTRY).click()
    expect(page.locator('#school-onboarding')).to_be_visible()
    page.locator(f'[data-home-school="{NTPU}"]').click()
    expect(page.locator('#application-path')).to_be_visible()
    expect(page.locator('[data-path-login]')).to_be_visible()
    assert page.evaluate('location.hash') == '#my-application'


def test_returning_student_can_open_scheduling_independently(page, live_server):
    page.add_init_script(f"localStorage.setItem('exchange-guide-home-school', '{NTPU}')")
    page.goto(f'{live_server.base_url}/#partners')
    page.wait_for_load_state('networkidle')
    # 準備與時程 is the 時程 tab of 我的申請; the old address still works and nothing needs a plan first.
    page.evaluate('location.hash = "#overview"')
    expect(page.locator('#overview')).to_be_visible()
    expect(page.locator('#tracker-title')).to_have_text('待辦與期限')
    assert page.evaluate('location.hash') == '#my-application?view=schedule'
    expect(page.locator('.uniway-public-nav [data-public-route="overview"]')).to_have_count(0)
    open_navigation(page)
    page.locator(ENTRY).click()
    expect(page.locator('#application-path')).to_be_visible()
    expect(page.locator('#overview')).to_be_hidden()


def test_the_application_entry_has_no_dropdown_and_tools_keep_their_pages(page, live_server):
    page.add_init_script(f"localStorage.setItem('exchange-guide-home-school', '{NTPU}')")
    page.goto(f'{live_server.base_url}/#advisor')
    page.wait_for_load_state('networkidle')
    expect(page.locator('#application-tools, #application-journey-steps')).to_have_count(0)
    expect(page.locator('#advisor-form')).to_be_visible()
    expect(page.locator(ENTRY)).to_have_attribute('aria-current','page')
    page.goto(f'{live_server.base_url}/#calendar')
    expect(page.locator('#calendar')).to_be_visible()
    expect(page.locator(ENTRY)).to_have_attribute('aria-current','page')
