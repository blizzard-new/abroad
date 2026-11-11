from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, expect

from cgu_demo_fixture import demo_url

expect.set_options(timeout=30000)

EVIDENCE = Path(os.environ.get('CGU_DEMO_EVIDENCE_DIR', str(Path(tempfile.gettempdir()) / 'uniway-cgu-platform-evidence')))


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={'width':1440, 'height':1000}, reduced_motion='reduce')
    page = context.new_page()
    page.set_default_timeout(90000)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    yield page
    screenshot(page, 'last-browser-state.png')
    assert errors == []
    context.close()


def ready(page, url, suffix=''):
    page.goto(url + '/' + suffix, wait_until='domcontentloaded')
    page.locator('#boot-splash').wait_for(state='hidden')
    page.evaluate('appReady')
    expect(page.locator('#school-switcher-label')).to_have_text('長庚大學')


def seed(page):
    page.locator('#cgu-demo-seed').click()
    page.locator('.today-primary').wait_for(state='visible')
    page.locator('#boot-splash').wait_for(state='hidden')


def screenshot(page, name):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(EVIDENCE / name))


def test_shared_home_search_favorite_compare_and_sources(page, demo_url):
    ready(page, demo_url, '?home=國立臺灣大學')
    expect(page.locator('#home-landing-title')).to_contain_text('你能去哪些交換學校')
    expect(page.locator('.pr-supported')).to_have_count(0)
    expect(page.locator('[data-home-discover]')).to_be_visible()
    expect(page.locator('#cgu-home-deadline-banner')).to_contain_text('12/21 17:00')
    expect(page.locator('#home-tile-calendar .pr-mini-dates li').first).to_contain_text('12 月')
    expect(page.locator('#home-tile-calendar .pr-mini-dates li').first).to_contain_text('21')
    expect(page.locator('#home-tile-calendar')).to_contain_text('適用已獲提名者')
    screenshot(page, 'desktop-home.png')
    page.locator('#home-search-input').fill('Lincoln')
    page.locator('#home-search-form button[type=submit]').click()
    expect(page.locator('#partner-table')).to_contain_text('林肯')
    page.locator('#partner-search').fill('')
    expect(page.locator('#partner-result-count')).to_contain_text('78')
    college_bar = page.locator('#cgu-college-quick-bar')
    expect(college_bar).to_be_visible()
    for label in ['醫', '工', '管', '智慧運算']:
        expect(college_bar.locator('[data-cgu-college]', has_text=label)).to_be_visible()
    med_btn = college_bar.locator('[data-cgu-college="醫學院"]')
    med_btn.click()
    expect(med_btn).to_have_attribute('aria-pressed', 'true')
    expect(page.locator('#cgu-college-live-count')).to_contain_text('醫學院可申請：共 45 所')
    expect(page.locator('#partner-result-count')).to_contain_text('共 45 所')
    ai_btn = college_bar.locator('[data-cgu-college="智慧運算學院"]')
    ai_btn.click()
    expect(ai_btn).to_have_attribute('aria-pressed', 'true')
    expect(page.locator('#cgu-college-live-count')).to_contain_text('智慧運算學院可申請：共 43 所')
    expect(page.locator('#partner-result-count')).to_contain_text('共 43 所')
    college_bar.locator('[data-cgu-college=""]').click()
    expect(page.locator('#partner-result-count')).to_contain_text('78')
    expect(page.get_by_role('group', name='交換名額')).to_contain_text('2 名以上')
    deadline_tab = page.locator('[data-partner-sort="deadline"]')
    quota_tab = page.locator('[data-partner-sort="quota"]')
    expect(deadline_tab).to_contain_text('有時程')
    expect(quota_tab).to_contain_text('最多')
    deadline_tab.click()
    expect(deadline_tab).to_have_attribute('aria-selected', 'true')
    first_by_deadline = page.locator('#partner-table .pr-school-card').first.inner_text()
    quota_tab.click()
    expect(quota_tab).to_have_attribute('aria-selected', 'true')
    first_by_quota = page.locator('#partner-table .pr-school-card').first.inner_text()
    assert first_by_deadline != first_by_quota
    page.locator('#partner-search').fill('Lincoln')
    expect(page.locator('#partner-table')).to_contain_text('林肯')
    page.locator('#partner-table .school-detail-trigger').first.click()
    page.locator('#detail-favorite-button').wait_for(state='visible')
    expect(page.locator('#booking-home-deadline')).to_contain_text('2026/12/21')
    expect(page.locator('#booking-home-deadline')).to_contain_text('17:00')
    page.locator('#detail-favorite-button').click()
    expect(page.locator('#detail-favorite-button')).to_contain_text('已收藏')
    expect(page.locator('#detail-compare-button')).to_have_attribute('aria-pressed', 'true')
    page.locator('#detail-compare-button').click()
    expect(page.locator('#detail-compare-button')).to_contain_text('加入比較')
    page.locator('#detail-compare-button').click()
    expect(page.locator('#detail-compare-button')).to_contain_text('移出比較')
    screenshot(page, 'desktop-school.png')
    page.reload(wait_until='domcontentloaded')
    page.locator('#boot-splash').wait_for(state='hidden')
    expect(page.locator('#detail-favorite-button')).to_contain_text('已收藏')
    page.locator('#cgu-demo-info').click()
    expect(page.locator('#cgu-demo-dialog')).to_contain_text('第一階段')
    expect(page.locator('#cgu-demo-dialog a')).to_have_count(3)
    page.keyboard.press('Escape')
    expect(page.locator('#cgu-demo-dialog')).not_to_be_visible()


def test_native_preparation_workspace_personal_date_and_notice_preview(page, demo_url):
    ready(page, demo_url)
    seed(page)
    page.locator('.hub-tabs [data-tab=workspace]').click()
    page.locator('[data-ex-new]').click()
    form = page.locator('#exchange-task-form')
    form.locator('[name=title]').fill('確認示範住宿用品')
    form.locator('[name=notes]').fill('展示資料：先整理用品清單，再向住宿單位確認。')
    form.locator('[name=date_kind]').select_option('personal')
    form.locator('[name=due_date]').fill('2027-06-01')
    form.get_by_role('button', name='保存任務', exact=True).click()
    expect(page.locator('#exchange-task-dialog')).not_to_be_visible()
    expect(page.locator('.ex-task')).to_contain_text('個人目標 2027-06-01')
    page.reload(wait_until='domcontentloaded')
    page.evaluate('appReady')
    expect(page.locator('.ex-task')).to_contain_text('確認示範住宿用品')
    screenshot(page, 'desktop-workspace.png')
    page.locator('[data-ex-tab=notice]').click()
    notice = page.locator('#exchange-notice-form')
    notice.locator('[name=source_label]').fill('虛構展示通知')
    notice.locator('[name=text]').fill('展示情境：請於 2027/1/10 前回傳申請書。')
    notice.get_by_role('button', name='整理待辦草稿').click()
    expect(page.locator('[data-ex-preview]')).to_have_count(1)
    expect(page.locator('[data-ex-preview] [name=due_date]')).to_have_value('2027-01-10')
    expect(page.locator('#exchange-notice-file')).to_be_disabled()
    expect(page.locator('[data-ex-extract]')).to_be_disabled()


def test_native_six_stages_keyboard_save_refresh_reset(page, demo_url):
    ready(page, demo_url)
    seed(page)
    expect(page.locator('#today-focus-title')).to_have_text('閱讀長庚校內申請須知')
    expect(page.locator('#plan-meta')).to_contain_text('116-1（2027 秋季出國）')
    expect(page.locator('#plan-meta')).not_to_contain_text('梯次待確認')
    expect(page.locator('#plan-select')).to_contain_text('2027 秋季（116-1）')
    expect(page.locator('#plan-select')).not_to_contain_text('上學期')
    expect(page.locator('#today-view .today-panel[aria-label="期限"]')).to_contain_text('12/21')
    expect(page.locator('#today-view .today-panel[aria-label="期限"]')).to_contain_text('17:00')
    expect(page.locator('#today-view .today-panel[aria-label="期限"]')).to_contain_text('校內截止')
    page.locator('.hub-tabs [data-tab="schedule"]').click()
    expect(page.locator('#schedule-dynamic')).to_contain_text('12/21')
    expect(page.locator('#schedule-dynamic')).to_contain_text('17:00')
    expect(page.locator('#schedule-dynamic')).to_contain_text('校內截止')
    expect(page.locator('#schedule-dynamic')).to_contain_text('2027 秋季（116-1）')
    page.goto(demo_url + '/#calendar', wait_until='domcontentloaded')
    page.locator('#calendar-verified-window-hook .verified-hook-pill').wait_for(state='visible')
    expect(page.locator('#calendar-verified-window-hook .verified-hook-pill')).to_have_text('期限提醒')
    expect(page.locator('#calendar-verified-window-hook')).not_to_contain_text('零失誤')
    expect(page.locator('#calendar-verified-window-hook .is-line')).to_have_count(0)
    expect(page.locator('#calendar-verified-window-hook a[href*="/calendar/school-window.ics"]')).to_be_visible()
    page.goto(demo_url + '/#eligibility', wait_until='domcontentloaded')
    expect(page.locator('.application-preference-fields legend')).to_contain_text('最多兩所')
    expect(page.locator('.application-preference-fields legend')).not_to_contain_text('最多五所')
    page.goto(demo_url + '/#my-application?view=today', wait_until='domcontentloaded')
    page.locator('#today-focus-title').wait_for(state='visible')
    expect(page.locator('.today-track li')).to_have_count(6)
    screenshot(page, 'desktop-journey.png')
    page.locator('.today-primary').focus()
    page.keyboard.press('Enter')
    page.locator('#level-form button[type=submit]').focus()
    page.keyboard.press('Enter')
    expect(page.locator('.success-state')).to_contain_text('已同步')
    page.reload(wait_until='domcontentloaded')
    page.locator('#boot-splash').wait_for(state='hidden')
    expect(page.locator('.level-progress')).to_contain_text('已完成')
    page.locator('a.back-link').click()
    page.locator('a[data-tab=today]:visible').first.click()
    expect(page.locator('#today-focus-title')).to_have_text('整理兩所志願與想修的課程')
    page.locator('#cgu-demo-reset').click()
    page.keyboard.press('Escape')
    expect(page.locator('#today-focus-title')).to_have_text('整理兩所志願與想修的課程')
    page.locator('#cgu-demo-reset').click()
    with page.expect_navigation(wait_until='domcontentloaded'):
        page.locator('#cgu-demo-confirm').click()
    page.locator('#boot-splash').wait_for(state='hidden')
    expect(page.locator('#home-landing-title')).to_be_visible()
    assert page.request.get(demo_url + '/account/application-paths').json()['items'] == []


@pytest.mark.parametrize('size', [(390,844), (820,1180)])
def test_responsive_native_journey(page, demo_url, size):
    page.set_viewport_size({'width':size[0], 'height':size[1]})
    ready(page, demo_url)
    seed(page)
    expect(page.locator('.today-primary')).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    if size[0] == 390:
        screenshot(page, 'mobile-journey.png')
    page.locator('.today-primary').click()
    page.locator('#level-form button[type=submit]').click()
    expect(page.locator('.success-state')).to_contain_text('已同步')


def test_source_service_failure_and_storage_namespace(page, demo_url):
    page.add_init_script("""if (!sessionStorage.getItem('formal-sentinel')) {
      localStorage.setItem('formal-sentinel','keep'); sessionStorage.setItem('formal-sentinel','keep');
      localStorage.setItem('exchange-guide-home-school','國立臺灣大學');
    }""")
    ready(page, demo_url)
    page.route('**/demo/content', lambda route: route.fulfill(status=503, body='unavailable'))
    page.locator('#cgu-demo-info').click()
    expect(page.locator('#cgu-demo-dialog')).to_contain_text('暫時無法載入')
    page.keyboard.press('Escape')
    page.unroute('**/demo/content')
    page.locator('#cgu-demo-info').click()
    expect(page.locator('#cgu-demo-dialog')).to_contain_text('校內申請選送須知')
    page.keyboard.press('Escape')
    page.locator('#cgu-demo-reset').click()
    with page.expect_navigation(wait_until='domcontentloaded'):
        page.locator('#cgu-demo-confirm').click()
    page.locator('#boot-splash').wait_for(state='hidden')
    stored = page.context.storage_state()['origins'][0]['localStorage']
    original = {row['name']:row['value'] for row in stored}
    assert original['formal-sentinel'] == 'keep'
    assert original['exchange-guide-home-school'] == '國立臺灣大學'


def test_storage_denial_keeps_original_ui_usable(page, demo_url):
    page.add_init_script("Object.defineProperty(window,'localStorage',{configurable:true,get(){throw new DOMException('blocked','SecurityError')}})")
    ready(page, demo_url)
    expect(page.locator('#cgu-demo-strip')).to_contain_text('瀏覽器儲存受限')
    seed(page)
    expect(page.locator('.today-primary')).to_be_visible()
