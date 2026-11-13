"""「合作構想示意」 in a real browser: the strip menu, the fixed banner, and zero API traffic."""
from __future__ import annotations

import pytest
from playwright.sync_api import sync_playwright, expect

from cgu_demo_fixture import demo_url

expect.set_options(timeout=30000)

BANNER = '示意畫面・虛構資料・尚未與校方串接'
PAGES = [('office', '國際處收件匣'), ('inquiry', '問答與轉承辦'), ('report', '返國心得')]


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
    page = context.new_page()
    page.set_default_timeout(90000)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    # The shared platform's home page always asks for private documents; the demo isolation answers 403 by design.
    page.on('console', lambda message: errors.append(message.text) if message.type == 'error'
            and not message.location['url'].endswith('/account/vault/documents') else None)
    yield page
    assert errors == []
    context.close()


def home(page, url):
    page.goto(url + '/', wait_until='domcontentloaded')
    page.locator('#boot-splash').wait_for(state='hidden')
    page.evaluate('appReady')
    expect(page.locator('#school-switcher-label')).to_have_text('長庚大學')


def test_strip_menu_opens_upward_and_reaches_all_three_pages(page, demo_url):
    home(page, demo_url)
    menu = page.locator('#cgu-demo-strip #cgu-preview-menu')
    expect(menu.locator('summary')).to_have_text('合作構想示意')
    expect(menu.locator('a')).to_have_count(3)  # present in the DOM
    expect(menu.locator('a').first).not_to_be_visible()  # collapsed until opened
    for slug, label in PAGES:
        menu.locator('summary').click()
        link = menu.get_by_role('link', name=label)
        expect(link).to_be_visible()
        strip_box = page.locator('#cgu-demo-strip').bounding_box()
        assert link.bounding_box()['y'] + link.bounding_box()['height'] <= strip_box['y'] + 1  # opens above the strip
        with page.expect_navigation(wait_until='domcontentloaded'):
            link.click()
        assert page.url == f'{demo_url}/preview/{slug}'
        expect(page.locator('.pv-banner')).to_have_text(BANNER)
        expect(page.locator('main h1')).to_contain_text('示意')
        page.get_by_role('link', name='← 回平台首頁').click()
        page.locator('#boot-splash').wait_for(state='hidden')
        expect(page.locator('#cgu-demo-strip')).to_be_visible()


def test_strip_menu_closes_with_escape_and_outside_click_and_keeps_other_controls_working(page, demo_url):
    home(page, demo_url)
    menu = page.locator('#cgu-preview-menu')
    menu.locator('summary').focus()
    page.keyboard.press('Enter')
    expect(menu.get_by_role('link', name='返國心得')).to_be_visible()
    page.keyboard.press('Tab')
    expect(menu.get_by_role('link', name='國際處收件匣')).to_be_focused()
    page.keyboard.press('Escape')
    expect(menu.get_by_role('link', name='國際處收件匣')).not_to_be_visible()
    expect(menu.locator('summary')).to_be_focused()
    menu.locator('summary').click()
    expect(menu.get_by_role('link', name='問答與轉承辦')).to_be_visible()
    page.locator('#home-landing-title').click()
    expect(menu.get_by_role('link', name='問答與轉承辦')).not_to_be_visible()
    # The existing strip buttons are unaffected by the addition.
    page.locator('#cgu-demo-info').click()
    expect(page.locator('#cgu-demo-dialog')).to_contain_text('第一階段')
    expect(page.locator('#cgu-demo-dialog a')).to_have_count(6)
    page.keyboard.press('Escape')


def test_banner_stays_fixed_and_pages_move_between_each_other(page, demo_url):
    page.goto(demo_url + '/preview/office', wait_until='networkidle')
    for slug, label in PAGES:
        page.locator('nav[aria-label="合作構想示意"]').get_by_role('link', name=label).click()
        page.wait_for_url(f'{demo_url}/preview/{slug}')
        banner = page.locator('.pv-banner')
        expect(banner).to_have_text(BANNER)
        expect(page.locator('nav[aria-label="合作構想示意"] [aria-current=page]')).to_have_text(label)
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(150)
        assert page.evaluate('window.scrollY') > 0
        box = banner.bounding_box()
        assert box['y'] == 0 and box['width'] == 1440  # still pinned to the top of the viewport after scrolling


def test_visiting_all_pages_makes_no_api_calls_and_writes_nothing(page, demo_url):
    requests = []
    page.on('request', lambda request: requests.append((request.method, request.url.removeprefix(demo_url))))
    page.goto(demo_url + '/preview/office', wait_until='networkidle')
    for slug, _ in PAGES:
        page.goto(f'{demo_url}/preview/{slug}', wait_until='networkidle')
        page.keyboard.press('End')
    assert requests, 'expected the pages themselves to be requested'
    assert {method for method, _ in requests} == {'GET'}
    for _, path in requests:
        assert path.startswith(('/preview/', '/static/')), path  # no /account, /auth, /demo, /ai ... calls
    storage = page.evaluate('[localStorage.length, sessionStorage.length, document.cookie]')
    assert storage == [0, 0, '']


def test_readonly_report_form_ignores_typing(page, demo_url):
    page.goto(demo_url + '/preview/report', wait_until='networkidle')
    area = page.locator('fieldset textarea').first
    before = area.input_value()
    area.click()
    page.keyboard.type('試著輸入')
    assert area.input_value() == before
    expect(page.locator('.pv-submit')).to_be_disabled()
    expect(page.locator('.pv-consent input')).to_be_disabled()


@pytest.mark.parametrize('size', [(390, 844), (820, 1180)])
def test_responsive_pages_and_strip_do_not_overflow_or_hide_content(page, demo_url, size):
    page.set_viewport_size({'width': size[0], 'height': size[1]})
    for slug, _ in PAGES:
        page.goto(f'{demo_url}/preview/{slug}', wait_until='networkidle')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), slug
        expect(page.locator('.pv-banner')).to_be_visible()
        banner = page.locator('.pv-banner').bounding_box()
        assert banner['height'] < 60  # one line, never grows into the content
    home(page, demo_url)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    # With the menu in the strip, the last line of the page must still be reachable above it.
    page.keyboard.press('End')
    page.wait_for_timeout(200)
    strip_top = page.locator('#cgu-demo-strip').bounding_box()['y']
    body_bottom = page.evaluate('document.body.getBoundingClientRect().bottom')
    assert body_bottom >= strip_top - 1
    assert page.evaluate('parseFloat(getComputedStyle(document.body).paddingBottom)') >= page.locator('#cgu-demo-strip').bounding_box()['height'] - 1
    page.locator('#cgu-preview-menu summary').click()
    box = page.locator('#cgu-preview-menu ul').bounding_box()
    assert box['x'] >= 0 and box['x'] + box['width'] <= size[0]


def test_dark_color_scheme_keeps_the_banner_and_text_readable(browser, demo_url):
    context = browser.new_context(viewport={'width': 1200, 'height': 900}, color_scheme='dark')
    page = context.new_page()
    page.goto(demo_url + '/preview/office', wait_until='networkidle')

    def luminance(color):
        r, g, b = [int(v) for v in color.removeprefix('rgb(').removeprefix('rgba(').rstrip(')').split(',')[:3]]
        lin = [(c / 255) / 12.92 if c / 255 <= .03928 else (((c / 255) + .055) / 1.055) ** 2.4 for c in (r, g, b)]
        return .2126 * lin[0] + .7152 * lin[1] + .0722 * lin[2]

    def contrast(selector):
        fg, bg = page.evaluate(f"""(() => {{ const e = document.querySelector('{selector}'); let b = e; let bg = 'rgba(0, 0, 0, 0)';
            while (b && /rgba\\(.*, 0\\)$|transparent/.test(bg)) {{ bg = getComputedStyle(b).backgroundColor; b = b.parentElement; }}
            return [getComputedStyle(e).color, bg]; }})()""")
        hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
        return (hi + .05) / (lo + .05)

    for selector in ('.pv-banner', '.pv-main h1', '.pv-pill.is-pending', '.pv-pill.is-passed', '.pv-docs li.is-miss', '.pv-table td'):
        assert contrast(selector) >= 4.5, selector
    context.close()
