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
    expect(page.locator('#home-landing-title')).to_contain_text('長庚 116-1 申請一頁看完')
    expect(page.locator('.pr-supported')).to_have_count(0)
    expect(page.locator('[data-home-discover]')).to_be_visible()
    onepager = page.locator('#cgu-hero-onepager')
    expect(onepager).to_be_visible()
    for phrase in (
        '11/02–12/21 17:00',
        '學業平均 70 分、多益 700',
        '線上申請表',
        '家長同意書',
        '語文證明',
        '含班級排名的中文成績單',
        '1 頁讀書計畫',
        '最多 2 個志願',
        '校內甄選',
        '學校提名',
        '合作校申請',
    ):
        expect(onepager).to_contain_text(phrase)
    expect(page.locator('#cgu-home-deadline-banner')).to_contain_text('12/21 17:00')
    expect(page.locator('#home-tile-calendar .pr-mini-dates li').first).to_contain_text('12 月')
    expect(page.locator('#home-tile-calendar .pr-mini-dates li').first).to_contain_text('21')
    expect(page.locator('#home-tile-calendar')).to_contain_text('適用已獲提名者')

    # Clean homepage: #cgu-dept-finder is completely removed from homepage
    expect(page.locator('#cgu-dept-finder')).to_have_count(0)
    expect(onepager.locator('[data-cgu-scroll="#cgu-dept-finder"]')).to_have_count(0)
    expect(onepager.locator('a.cgu-hero-cta.is-primary[href="#partners"]')).to_be_visible()

    # Item 7:「領航者補助」說明卡 on homepage
    nav_card = page.locator('#cgu-navigator-card')
    expect(nav_card).to_be_visible()
    for nav_text in ('NT$75,000', 'NT$150,000', 'NT$60,000', 'NT$120,000', '+NT$10,000', '班排名前 30%'):
        expect(nav_card).to_contain_text(nav_text)
    expect(nav_card.locator('a[href*="b85add3b-7d9e-43ff-b22f-f0657e11765c"]')).to_be_visible()

    screenshot(page, 'desktop-home.png')
    page.locator('#home-search-input').fill('Lincoln')
    page.locator('#home-search-form button[type=submit]').click()
    expect(page.locator('#partner-table')).to_contain_text('林肯')
    page.locator('#partner-search').fill('')
    expect(page.locator('#partner-result-count')).to_contain_text('78')

    # Prominent relocated「我的條件」(#discovery-criteria) near the top of #partners
    criteria = page.locator('#partners #discovery-criteria')
    expect(criteria).to_be_visible()
    expect(page.locator('#partners .pr-explore-head .discovery-open-workspace')).to_be_visible()
    head_box = page.locator('#partners .pr-explore-head').bounding_box()
    criteria_box = criteria.bounding_box()
    strip_box = page.locator('#cgu-partner-filter-strip').bounding_box()
    search_box = page.locator('#partners .pr-search').bounding_box()
    results_box = page.locator('#partners .journey-search-layout').bounding_box()
    assert head_box and criteria_box and strip_box and search_box and results_box
    assert criteria_box['height'] >= 52
    assert head_box['y'] < criteria_box['y'] < strip_box['y'] < search_box['y'] < results_box['y']

    # Single-row Program + College + Department strip with zero grey boxes or small grey text
    prog_tabs = page.locator('#cgu-program-tabs')
    college_bar = page.locator('#cgu-college-quick-bar')
    expect(prog_tabs).to_be_visible()
    expect(college_bar).to_be_visible()
    prog_box = prog_tabs.bounding_box()
    college_box = college_bar.bounding_box()
    assert prog_box and college_box
    assert abs(prog_box['y'] - college_box['y']) < 8
    assert prog_box['x'] + prog_box['width'] <= college_box['x'] + 4

    expect(page.locator('#cgu-program-tabs .cgu-program-tabs-note')).not_to_be_visible()
    expect(page.locator('#cgu-college-live-count')).not_to_be_visible()
    expect(page.locator('#cgu-college-quick-bar .cgu-college-bar-label')).not_to_be_visible()
    expect(prog_tabs.locator('.cgu-program-tab > span').first).not_to_be_visible()
    expect(college_bar.locator('.cgu-college-btn > span').first).not_to_be_visible()
    inactive_tab_bg = prog_tabs.locator('[data-cgu-program="exchange"]').evaluate('el => getComputedStyle(el).backgroundColor')
    assert inactive_tab_bg in ('rgba(0, 0, 0, 0)', 'transparent')

    # Hovering「我的條件」summary must keep royal-blue gradient + crisp white text (never white-on-white)
    criteria_summary = criteria.locator('summary')
    criteria_summary.hover()
    hover_styles = criteria_summary.evaluate(
        """el => ({
            sumBg: getComputedStyle(el).backgroundColor,
            headingColor: getComputedStyle(el.querySelector('.cgu-criteria-heading')).color,
        })"""
    )
    assert hover_styles['sumBg'] in ('rgba(0, 0, 0, 0)', 'transparent')
    assert hover_styles['headingColor'] == 'rgb(255, 255, 255)'

    screenshot(page, 'desktop-partners.png')

    # Test「我的條件」filtering, grading scale placeholder/max sync & reset
    criteria_summary.click()
    expect(page.locator('#discovery-criteria-form')).to_be_visible()
    screenshot(page, 'desktop-partners-criteria-open.png')
    grade_input = page.locator('#discovery-criteria-form [name="grade"]')
    scale_select = page.locator('#discovery-criteria-form [name="scale"]')
    scale_select.evaluate("el => { el.value = '4.3'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    expect(grade_input).to_have_attribute('max', '4.3')
    expect(grade_input).to_have_attribute('placeholder', '例如 3.6')
    scale_select.evaluate("el => { el.value = '100'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    expect(grade_input).to_have_attribute('max', '100')
    expect(grade_input).to_have_attribute('placeholder', '例如 78')
    page.locator('#discovery-test').evaluate("el => { el.value = 'toeic'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    page.locator('#discovery-score').fill('750')
    grade_input.fill('78')
    page.locator('#discovery-criteria-form [name="degree"]').evaluate("el => { el.value = 'undergraduate'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    page.locator('#discovery-criteria-form button[type="submit"]').click()
    expect(page.locator('#cgu-criteria-summary')).to_contain_text('TOEIC 750')
    expect(page.locator('#cgu-criteria-summary')).to_contain_text('平均 78')
    expect(page.locator('#cgu-criteria-summary')).to_contain_text('大學部')
    expect(page.locator('#discovery-criteria-count')).to_have_text('已套用')
    expect(page.locator('#cgu-criteria-cta-label')).to_have_text('修改條件')
    criteria_summary.click()
    scale_select.evaluate("el => { el.value = '4'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    page.locator('#discovery-clear-criteria').click()
    expect(grade_input).to_have_attribute('max', '100')
    expect(grade_input).to_have_attribute('placeholder', '例如 78')
    criteria_summary.click()
    expect(page.locator('#discovery-criteria-count')).to_have_text('')
    expect(page.locator('#cgu-criteria-cta-label')).to_have_text('設定條件')
    expect(page.locator('#partner-result-count')).to_contain_text('78')

    # Item 4: 雙學位跟交換分開呈現 (#cgu-program-tabs) on the same row
    dual_tab = prog_tabs.locator('[data-cgu-program="dual_degree"]')
    exch_tab = prog_tabs.locator('[data-cgu-program="exchange"]')
    all_tab = prog_tabs.locator('[data-cgu-program=""]')
    dual_tab.click()
    expect(dual_tab).to_have_attribute('aria-selected', 'true')
    expect(page.locator('#partner-result-count')).to_contain_text('共 14 所')
    expect(page.locator('#partner-table')).to_contain_text('瑞典皇家理工學院')
    exch_tab.click()
    expect(exch_tab).to_have_attribute('aria-selected', 'true')
    expect(page.locator('#partner-result-count')).to_contain_text('共 66 所')
    all_tab.click()
    expect(page.locator('#partner-result-count')).to_contain_text('78')

    for label in ['全部學院', '醫學院', '工學院', '管理學院', '智慧運算學院']:
        expect(college_bar.locator('[data-cgu-college]', has_text=label)).to_be_visible()
    med_btn = college_bar.locator('[data-cgu-college="醫學院"]')
    med_btn.click()
    expect(med_btn).to_have_attribute('aria-pressed', 'true')
    expect(page.locator('#partner-result-count')).to_contain_text('共 45 所')
    ai_btn = college_bar.locator('[data-cgu-college="智慧運算學院"]')
    ai_btn.click()
    expect(ai_btn).to_have_attribute('aria-pressed', 'true')
    expect(page.locator('#partner-result-count')).to_contain_text('共 43 所')

    # Department filter inline on the same row (select 工學院 -> 生物醫學工程學系 vs 電機工程學系)
    college_bar.locator('[data-cgu-college="工學院"]').click()
    page.locator('#cgu-partner-dept-select').evaluate(
        "el => { el.value = '生物醫學工程學系'; el.dispatchEvent(new Event('change', { bubbles: true })); }"
    )
    page.locator('#partner-search').fill('香港中文')
    expect(page.locator('#partner-table')).to_contain_text('香港中文大學')
    page.locator('#cgu-partner-dept-select').evaluate(
        "el => { el.value = '電機工程學系'; el.dispatchEvent(new Event('change', { bubbles: true })); }"
    )
    expect(page.locator('#partner-table')).not_to_contain_text('香港中文大學')
    page.locator('#partner-search').fill('')
    assert abs(prog_tabs.bounding_box()['y'] - college_bar.bounding_box()['y']) < 8

    # Item 5: 管理學院的「院級管道」提示
    mgmt_btn = college_bar.locator('[data-cgu-college="管理學院"]')
    mgmt_btn.click()
    expect(page.locator('#cgu-mgmt-channel-notice')).to_be_visible()
    expect(page.locator('#cgu-mgmt-channel-notice')).to_contain_text('管理學院另有院級交換，請洽院國際辦公室')
    expect(page.locator('#cgu-mgmt-channel-notice')).to_contain_text('IAE 艾克斯馬賽')
    expect(page.locator('#cgu-mgmt-channel-notice')).to_contain_text('雷恩商學院')

    college_bar.locator('[data-cgu-college=""]').click()
    expect(page.locator('#cgu-mgmt-channel-notice')).not_to_be_visible()
    expect(page.locator('#partner-result-count')).to_contain_text('78')

    # Verify Map View & Dark Mode keep「我的條件」and single-row strip clean with zero overflow
    page.locator('[data-partner-view="map"]').click()
    expect(page.locator('#partner-map-panel')).to_be_visible()
    expect(criteria).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    screenshot(page, 'desktop-partners-map.png')
    page.locator('[data-partner-view="list"]').click()
    expect(page.locator('#partner-table')).to_be_visible()

    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    screenshot(page, 'desktop-partners-dark.png')
    page.evaluate("delete document.documentElement.dataset.theme")
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

    # Item 6: 從「多益 700」出發看語言門檻（有列多益 vs 此校未列多益）
    page.locator('#partner-search').fill('嘉泉')
    expect(page.locator('#partner-table .pr-school-card').first).to_contain_text('有列多益')
    expect(page.locator('#partner-table .pr-school-card').first).not_to_contain_text('此校未列多益')

    page.locator('#partner-search').fill('Lincoln')
    expect(page.locator('#partner-table')).to_contain_text('林肯')
    expect(page.locator('#partner-table .pr-school-card').first).to_contain_text('此校未列多益')
    page.locator('#partner-table .school-detail-trigger').first.click()
    page.locator('#detail-favorite-button').wait_for(state='visible')
    expect(page.locator('#booking-home-deadline')).to_contain_text('2026/12/21')
    expect(page.locator('#booking-home-deadline')).to_contain_text('17:00')
    expect(page.get_by_role('complementary', name='申請摘要')).to_contain_text('此校未列多益')
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

    # Verify relocated「最近看過」popover in #partners header stays inline, inside viewport, and closes on outside click
    page.evaluate("window.location.hash = '#partners'")
    recents = page.locator('#partners .cgu-explore-head-actions [data-discovery-recents]')
    expect(recents).to_be_visible()
    ws_before = page.locator('#partners .cgu-explore-head-actions .discovery-open-workspace').bounding_box()
    recents.locator('summary').click()
    ws_after = page.locator('#partners .cgu-explore-head-actions .discovery-open-workspace').bounding_box()
    recents_list_box = recents.locator('.discovery-recent-list').bounding_box()
    assert ws_before and ws_after and recents_list_box
    assert abs(ws_after['y'] - ws_before['y']) < 4
    assert recents_list_box['x'] >= 12 and (recents_list_box['x'] + recents_list_box['width']) <= 1440 - 12
    page.locator('#partners-title').click()
    assert not recents.evaluate('el => el.open')

    page.locator('#cgu-demo-info').click()
    expect(page.locator('#cgu-demo-dialog')).to_contain_text('第一階段')
    expect(page.locator('#cgu-demo-dialog a')).to_have_count(6)
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
    # Item 3: 示範學生林小程預設帶入工學院・生物醫學工程學系・大三・多益 750
    expect(page.locator('#advisor-college')).to_have_value('工學院')
    expect(page.locator('#advisor-department')).to_have_value('生物醫學工程學系')
    expect(page.locator('#advisor-current-year')).to_have_value('大三')
    expect(page.locator('#advisor-language-test')).to_have_value('toeic')
    expect(page.locator('#advisor-language-score')).to_have_value('750')
    page.goto(demo_url + '/#scholarships', wait_until='domcontentloaded')
    expect(page.locator('#cgu-scholarships-navigator-card')).to_contain_text('領航者補助作業要點')
    expect(page.locator('#cgu-scholarships-navigator-card')).to_contain_text('NT$75,000')
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
    expect(page.locator('#cgu-hero-onepager')).to_be_visible()
    expect(page.locator('#cgu-dept-finder')).to_have_count(0)
    expect(page.locator('#cgu-navigator-card')).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    page.evaluate("window.location.hash = '#partners'")
    expect(page.locator('#partners #discovery-criteria')).to_be_visible()
    expect(page.locator('#cgu-partner-filter-strip')).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    # Every college & program button must wrap cleanly inside viewport (no right-edge clipping)
    ai_college_box = page.locator('#cgu-college-quick-bar [data-cgu-college="智慧運算學院"]').bounding_box()
    dual_prog_box = page.locator('#cgu-program-tabs [data-cgu-program="dual_degree"]').bounding_box()
    assert ai_college_box and dual_prog_box
    assert 0 <= ai_college_box['x'] and (ai_college_box['x'] + ai_college_box['width']) <= size[0]
    assert 0 <= dual_prog_box['x'] and (dual_prog_box['x'] + dual_prog_box['width']) <= size[0]
    page.locator('#partners #discovery-criteria summary').click()
    expect(page.locator('#discovery-criteria-form')).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    if size[0] == 390:
        screenshot(page, 'mobile-partners.png')
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


def test_demo_script_end_to_end_student_and_oia_workflow(page, demo_url):
    """Covers the full required demo script route:
    學生預檢缺件 → 補齊後送出取得編號 → 切到國際處視角要求補件 → 切回學生端看到通知 → 提問未命中轉承辦 → 承辦回覆
    plus hidden Forum/Reviews, fixed CGU school switcher, 116-1 deadline source, and Spec page.
    """
    ready(page, demo_url)

    # Item 7 fixes: Forum & Reviews hidden (including direct hashes); school switcher fixedly displays 長庚大學
    expect(page.locator('.uniway-public-nav a[data-public-route="forum"]')).not_to_be_visible()
    expect(page.locator('.uniway-public-nav a[data-public-route="feedback"]')).not_to_be_visible()
    for blocked_hash in ('#university-feed', '#cgu-feed', '#board=%E5%9C%8B%E7%AB%8B%E8%87%BA%E7%81%A3%E5%A4%A7%E5%AD%B8'):
        page.goto(f'{demo_url}/{blocked_hash}', wait_until='domcontentloaded')
        expect(page.locator('#community-hub')).not_to_be_visible()
        expect(page.locator('#school-switcher')).to_be_disabled()
        expect(page.locator('#school-switcher-label')).to_have_text('長庚大學')
    expect(page.locator('#school-switcher')).to_contain_text('長庚大學')
    expect(page.locator('#school-switcher')).not_to_contain_text('切換就讀學校')
    expect(page.locator('input[name="home_university"]')).to_have_attribute('readonly', '')

    # Feature 2: 校方介接規格頁
    page.locator('.uniway-public-nav a[data-public-route="school-connector"]').click()
    spec_page = page.locator('#cgu-connector-spec-page')
    expect(spec_page).to_be_visible()
    expect(spec_page).to_contain_text('模擬・尚未與校方串接')
    for method_name in ('submit_application', 'send_inquiry', 'submit_return_report', 'get_status'):
        expect(spec_page.locator('#cgu-connector-spec-table')).to_contain_text(method_name)
    for phase_title in ('不需校方配合', '小型試辦', '需校方資訊單位'):
        expect(spec_page).to_contain_text(phase_title)
    screenshot(page, 'desktop-connector-spec.png')

    # Seed plan & verify 116-1 official deadline + announcement source in 我的申請
    seed(page)
    deadline_panel = page.locator('#today-view .today-panel[aria-label="期限"]')
    expect(deadline_panel).to_contain_text('116-1 校內申請截止')
    expect(deadline_panel).to_contain_text('2026/12/21 17:00')
    expect(deadline_panel.locator('a[href*="85785"]')).to_be_visible()

    # Step 1: 學生預檢缺件（不可送出）
    sim_hub = page.locator('#cgu-my-application-sim')
    expect(sim_hub).to_be_visible()
    expect(sim_hub).to_contain_text('模擬・尚未與校方串接')
    expect(sim_hub).to_contain_text('展示版不保存檔案內容，請勿上傳真實個資')
    expect(sim_hub).to_contain_text('實際申請仍須依國際處公告填線上表單並繳交紙本。')
    expect(page.locator('#cgu-sim-submit-btn')).to_be_disabled()

    # Upload 1 real synthetic file via file input + 1 sample button -> still missing 3 docs
    page.locator('input[data-cgu-sim-upload="online_form"]').set_input_files({
        'name': 'demo_online_form.pdf',
        'mimeType': 'application/pdf',
        'buffer': b'SYNTHETIC-ONLINE-FORM-ONLY-HASHED-IN-RAM',
    })
    expect(sim_hub.locator('[data-doc-row="online_form"]')).to_contain_text('demo_online_form.pdf')
    expect(sim_hub.locator('[data-doc-row="online_form"]')).to_contain_text('SHA-256')

    sim_hub.locator('[data-cgu-sim-sample="parent_consent"]').click()
    expect(sim_hub.locator('[data-doc-row="parent_consent"]')).to_contain_text('已備齊')
    page.locator('#cgu-sim-precheck-btn').click()
    precheck_box = page.locator('#cgu-sim-precheck-box')
    expect(precheck_box).to_contain_text('缺件不可送出')
    expect(precheck_box).to_contain_text('語文證明')
    expect(precheck_box).to_contain_text('含排名的中文歷年成績單')
    expect(precheck_box).to_contain_text('一頁讀書計畫')
    expect(page.locator('#cgu-sim-submit-btn')).to_be_disabled()

    # Step 2: 補齊後送出取得 SIM- 收件編號
    page.locator('#cgu-sim-fill-all').click()
    expect(precheck_box).to_contain_text('完整性預檢通過')
    expect(page.locator('#cgu-sim-submit-btn')).to_be_enabled()
    page.locator('#cgu-sim-submit-btn').click()
    records = page.locator('#cgu-sim-app-records')
    expect(records).to_contain_text('SIM-APP-')
    expect(records).to_contain_text('已送出')
    expect(records).to_contain_text('已收件')
    expect(records).to_contain_text('要求補件／初審通過')

    receipt_text = records.locator('.cgu-submitted-card').first.get_attribute('data-receipt-id')
    assert receipt_text and receipt_text.startswith('SIM-APP-')

    # Step 3: 切到國際處視角要求補件
    oia_toggle = page.locator('#cgu-demo-oia-toggle')
    expect(oia_toggle).to_have_text('切換為國際處視角')
    oia_toggle.click()
    oia_page = page.locator('#cgu-oia-console-page')
    expect(oia_page).to_be_visible()
    expect(oia_toggle).to_have_text('切換回學生視角')
    expect(oia_page).to_contain_text('模擬・尚未與校方串接')
    expect(oia_page).to_contain_text('預載 5 筆明確標示之虛構示範資料')
    expect(oia_page.locator('#cgu-oia-stats-row')).to_contain_text('各校志願數')
    expect(oia_page.locator('#cgu-oia-stats-row')).to_contain_text('缺件／要求補件數')
    expect(oia_page.locator('#cgu-oia-stats-row')).to_contain_text('最常被問的問題')

    # Verify OIA inbox filter tabs keep distinct active/inactive styling and dark-mode contrast
    oia_tab_styles = oia_page.evaluate(
        """el => {
            const active = el.querySelector('.cgu-oia-tabs [data-oia-filter="all"]');
            const inactive = el.querySelector('.cgu-oia-tabs [data-oia-filter="applications"]');
            const light = {
                activeBg: getComputedStyle(active).backgroundColor,
                activeColor: getComputedStyle(active).color,
                inactiveBg: getComputedStyle(inactive).backgroundColor,
            };
            document.documentElement.dataset.theme = 'dark';
            const dark = {
                activeBg: getComputedStyle(active).backgroundColor,
                activeColor: getComputedStyle(active).color,
                inactiveBg: getComputedStyle(inactive).backgroundColor,
                inactiveColor: getComputedStyle(inactive).color,
            };
            delete document.documentElement.dataset.theme;
            return { light, dark };
        }"""
    )
    assert oia_tab_styles['light']['activeBg'] != oia_tab_styles['light']['inactiveBg']
    assert oia_tab_styles['light']['activeColor'] == 'rgb(255, 255, 255)'
    assert oia_tab_styles['dark']['activeBg'] != oia_tab_styles['dark']['inactiveBg']
    assert oia_tab_styles['dark']['activeColor'] == 'rgb(255, 255, 255)'
    assert oia_tab_styles['dark']['inactiveColor'] != 'rgb(0, 0, 0)'

    app_oia_card = oia_page.locator(f'[data-oia-card="{receipt_text}"]')
    expect(app_oia_card).to_be_visible()
    app_oia_card.locator(f'[data-oia-reason-for="{receipt_text}"]').fill('中文歷年成績單未附班級排名百分比，請補交教務處核章版。')
    app_oia_card.locator('[data-oia-act="request_supplement"]').click()
    expect(app_oia_card).to_contain_text('要求補件')
    screenshot(page, 'desktop-oia-console.png')

    # Step 4: 切回學生端看到通知與狀態更新（重新整理後保留）
    oia_toggle.click()
    expect(sim_hub).to_be_visible()
    expect(records.locator(f'[data-receipt-id="{receipt_text}"]')).to_contain_text('要求補件')
    expect(records.locator(f'[data-receipt-id="{receipt_text}"]')).to_contain_text('中文歷年成績單未附班級排名百分比')
    expect(page.locator('#notification-badge')).to_be_visible()
    expect(page.locator('#notification-badge')).to_have_text('1')

    page.locator('#notification-button').click()
    expect(page.locator('#notification-dialog')).to_be_visible()
    expect(page.locator('#notification-center-list')).to_contain_text(receipt_text)
    expect(page.locator('#notification-center-list')).to_contain_text('模擬・尚未與校方串接')
    page.locator('#notification-dialog .dialog-close').click()

    # Reload page -> application supplement status & notification persist
    page.reload(wait_until='domcontentloaded')
    page.locator('#boot-splash').wait_for(state='hidden')
    page.evaluate('appReady')
    expect(page.locator(f'#cgu-sim-app-records [data-receipt-id="{receipt_text}"]')).to_contain_text('要求補件')
    expect(page.locator('#notification-badge')).to_be_visible()

    # Step 5: 學生端「問國際處」— 規則比對命中 + 提問未命中轉承辦 → 承辦回覆
    page.locator('.uniway-public-nav a[data-public-route="ask-oia"]').click()
    ask_page = page.locator('#cgu-ask-oia-page')
    expect(ask_page).to_be_visible()
    expect(ask_page).to_contain_text('規則式比對，非 AI')

    # First test keyword hit, plus escalating via「仍要詢問承辦」
    page.locator('#cgu-ask-input').fill('請問 116-1 校內申請什麼時候截止？需要紙本嗎？')
    page.locator('#cgu-ask-submit-btn').click()
    hit_box = page.locator('#cgu-ask-result-box')
    expect(hit_box).to_contain_text('規則式比對，非 AI')
    expect(hit_box).to_contain_text('2026/12/21')
    expect(hit_box.locator('a[href*="cgu.edu.tw"]').first).to_be_visible()
    page.locator('#cgu-ask-escalate-btn').click()
    expect(page.locator('#cgu-ask-result-box')).to_contain_text('已轉送模擬承辦收件匣')

    # Next test unmatched question -> escalates to simulated OIA inbox
    page.locator('#cgu-ask-input').fill('請問基督城冬季無障礙接駁專車要向哪個窗口預約？')
    page.locator('#cgu-ask-submit-btn').click()
    expect(page.locator('#cgu-ask-result-box')).to_contain_text('未命中現有規則與 FAQ')
    expect(page.locator('#cgu-ask-result-box')).to_contain_text('SIM-INQ-')
    inq_card = page.locator('#cgu-ask-inquiries-list .cgu-inquiry-card').first
    expect(inq_card).to_contain_text('無障礙接駁專車')
    inq_id = inq_card.get_attribute('data-receipt-id')
    assert inq_id and inq_id.startswith('SIM-INQ-')
    expect(inq_card).to_contain_text('待承辦回覆')

    # Step 6: 承辦回覆並加入 FAQ → 學生端看到回覆與通知
    oia_toggle.click()
    inq_oia_card = page.locator(f'#cgu-oia-console-page [data-oia-card="{inq_id}"]')
    expect(inq_oia_card).to_be_visible()
    inq_oia_card.locator(f'[data-oia-reply-for="{inq_id}"]').fill('獲得長庚校內提名後，林肯大學國際學生服務中心會寄發無障礙接機申請連結。')
    inq_oia_card.locator('[data-oia-act="reply_inquiry"]').click()
    expect(inq_oia_card).to_contain_text('已回覆')
    inq_oia_card.locator('[data-oia-act="add_to_faq"]').click()
    expect(inq_oia_card).to_contain_text('已入 FAQ')

    oia_toggle.click()
    expect(ask_page).to_be_visible()
    expect(page.locator(f'#cgu-ask-inquiries-list [data-receipt-id="{inq_id}"]')).to_contain_text('已回覆')
    expect(page.locator(f'#cgu-ask-inquiries-list [data-receipt-id="{inq_id}"]')).to_contain_text('無障礙接機申請連結')
    expect(page.locator('#notification-badge')).to_have_text('3')

    # Verify add_to_faq immediately makes natural Chinese follow-up questions hit the rule-based FAQ!
    page.locator('#cgu-ask-input').fill('請問無障礙接駁專車要找誰？')
    page.locator('#cgu-ask-submit-btn').click()
    expect(page.locator('#cgu-ask-result-box')).to_contain_text('規則式比對，非 AI')
    expect(page.locator('#cgu-ask-result-box')).to_contain_text('無障礙接機申請連結')


def test_return_report_validation_print_approval_mobile_overflow_and_reset(page, demo_url):
    ready(page, demo_url)

    # Navigate to 返國心得
    page.locator('.uniway-public-nav a[data-public-route="return-report"]').click()
    rpt_page = page.locator('#cgu-return-report-page')
    expect(rpt_page).to_be_visible()
    expect(rpt_page).to_contain_text('模擬・尚未與校方串接')

    # Under 300 chars blocked on submit
    page.locator('[data-cgu-report-sec="preparation"]').fill('太短的草稿內容')
    page.locator('#cgu-report-submit-btn').click()
    expect(page.locator('#cgu-report-feedback')).to_contain_text('300 字')

    # Fill 300+ char fictional draft, add video URL, keep consent checked, submit
    page.locator('#cgu-report-fill-sample').click()
    expect(page.locator('[data-cgu-report-count="preparation"]')).to_contain_text('已達標')
    page.locator('#cgu-report-video').fill('https://example.com/lincoln-demo-video')
    page.locator('#cgu-report-submit-btn').click()

    rpt_records = page.locator('#cgu-report-records')
    expect(rpt_records).to_contain_text('SIM-RPT-')
    rpt_id = rpt_records.locator('.cgu-submitted-card').first.get_attribute('data-receipt-id')
    assert rpt_id and rpt_id.startswith('SIM-RPT-')

    # Verify printable page renders in real Chromium page with CSP & zero JS errors
    print_page = page.context.new_page()
    print_errors = []
    print_page.on('pageerror', lambda error: print_errors.append(str(error)))
    print_page.goto(f'{demo_url}/demo/connector/return-reports/{rpt_id}/print', wait_until='domcontentloaded')
    expect(print_page.locator('h1')).to_contain_text('長庚大學出國研修返國學期報告表（展示列印版）')
    expect(print_page.locator('.cgu-sim-badge')).to_have_text('模擬・尚未與校方串接')
    expect(print_page.locator('#cgu-print-trigger')).to_be_visible()
    assert print_errors == []
    print_page.close()

    # Approve in OIA Console -> verify appears on Lincoln University detail page under 學長姐心得（示範資料）
    page.locator('#cgu-demo-oia-toggle').click()
    rpt_oia_card = page.locator(f'#cgu-oia-console-page [data-oia-card="{rpt_id}"]')
    expect(rpt_oia_card).to_be_visible()
    rpt_oia_card.locator('[data-oia-act="approve_report"]').click()
    expect(rpt_oia_card).to_contain_text('已核可公開')

    page.goto(demo_url + '/#school=' + '林肯大學%20Lincoln%20University', wait_until='domcontentloaded')
    public_block = page.locator('#cgu-approved-return-reports')
    expect(public_block).to_be_visible()
    expect(public_block).to_contain_text('學長姐心得（示範資料）')
    expect(public_block).to_contain_text('模擬・尚未與校方串接')
    expect(public_block).to_contain_text(rpt_id)
    expect(public_block.locator('a[href="https://example.com/lincoln-demo-video"]')).to_be_visible()
    page.locator('#detail-tab-experiences').click()
    expect(page.locator('#cgu-approved-return-reports-experiences')).to_be_visible()

    # Navigating to another school in-SPA cleanly removes Lincoln's approved report blocks (zero DOM bleed)
    page.evaluate("location.hash = '#school=' + encodeURIComponent('韓國嘉泉大學 Gachon University')")
    expect(page.locator('#school-detail-view')).to_contain_text('韓國嘉泉大學')
    expect(page.locator('.cgu-public-reports-block')).to_have_count(0)

    # Verify mobile (390x844) has no horizontal overflow across all new routes
    page.set_viewport_size({'width': 390, 'height': 844})
    for route_hash in ('#school-connector', '#ask-oia', '#return-report', '#oia-view'):
        page.goto(f'{demo_url}/{route_hash}', wait_until='domcontentloaded')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), f'overflow on {route_hash}'

    # Reset wipes all newly added data (return reports, public display, notifications)
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.locator('#cgu-demo-reset').click()
    with page.expect_navigation(wait_until='domcontentloaded'):
        page.locator('#cgu-demo-confirm').click()
    page.locator('#boot-splash').wait_for(state='hidden')
    page.evaluate('appReady')

    status_after = page.request.get(demo_url + '/demo/connector/status').json()
    assert status_after['applications'] == []
    assert status_after['inquiries'] == []
    assert status_after['return_reports'] == []
    assert page.request.get(demo_url + '/account/notifications').json()['items'] == []
