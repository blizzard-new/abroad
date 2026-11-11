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
    expect(page.locator('#home-landing-title')).to_contain_text('世界這麼大')
    expect(page.locator('#mt-board-school-name')).to_have_text('長庚大學')
    assert page.locator('#home-search-rows').inner_text().find('截止') == -1
    screenshot(page, 'desktop-home.png')
    page.locator('#mt-board-q').fill('Lincoln')
    page.locator('#mt-board button[type=submit]').click()
    expect(page.locator('#partner-table')).to_contain_text('林肯')
    page.locator('#partner-table .school-detail-trigger').first.click()
    page.locator('#detail-favorite-button').wait_for(state='visible')
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


def test_native_six_stages_keyboard_save_refresh_reset(page, demo_url):
    ready(page, demo_url)
    seed(page)
    expect(page.locator('#today-focus-title')).to_have_text('閱讀長庚校內申請須知')
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
