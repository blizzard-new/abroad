from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
import requests
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from playwright.sync_api import expect, sync_playwright

from cgu_catalogue_fixture import fixed_cgu_catalogue
from exchange_info.api import create_app

expect.set_options(timeout=30000)

SCREENSHOT_DIR = Path(
    os.environ.get(
        'APP_PARTNER_TEMPLATE_EVIDENCE_DIR',
        str(Path(tempfile.gettempdir()) / 'uniway-app-partner-search-evidence'),
    )
)


@pytest.fixture(scope='module')
def app_url(tmp_path_factory):
    root = tmp_path_factory.mktemp('app-uniway-process')
    data_dir = root / 'app-data'
    repo_data = Path(__file__).resolve().parents[1] / 'data'
    shutil.copytree(repo_data, data_dir)

    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]

    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(('EXCHANGE_', 'SUPABASE', 'GOOGLE_OAUTH', 'SMTP_', 'OPENAI_API_KEY'))
    }
    env['EXCHANGE_INFO_DATA_DIR'] = str(data_dir)
    url = f'http://127.0.0.1:{port}'
    with (root / 'app-server.log').open('w+', encoding='utf-8') as log:
        process = subprocess.Popen(
            [
                sys.executable,
                '-m',
                'uvicorn',
                'exchange_info.api:create_app',
                '--factory',
                '--host',
                '127.0.0.1',
                '--port',
                str(port),
                '--no-proxy-headers',
            ],
            env=env,
            stdout=log,
            stderr=log,
        )
        try:
            for _ in range(240):
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(log.read()[-4000:])
                try:
                    if requests.get(url + '/health', timeout=1).ok:
                        break
                except requests.RequestException:
                    pass
                time.sleep(0.5)
            else:
                pytest.fail('app.uniway test server did not start')
            yield url
        finally:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as driver:
        instance = driver.chromium.launch()
        yield instance
        instance.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    tab = context.new_page()
    tab.set_default_timeout(90000)
    errors: list[str] = []
    tab.on('pageerror', lambda err: errors.append(str(err)))
    yield tab
    assert errors == [], f'Unexpected JS page errors: {errors}'
    context.close()


def save_shot(page, filename: str) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SCREENSHOT_DIR / filename))


def pick_home_school(page, school_name: str) -> None:
    label = page.locator('#school-switcher-label')
    if label.inner_text().strip() == school_name:
        return
    page.locator('#school-switcher').click()
    dialog = page.locator('#school-onboarding')
    expect(dialog).to_be_visible()
    search = page.locator('#school-search')
    search.fill(school_name)
    option = page.locator(f'#school-options [data-home-school="{school_name}"]')
    expect(option).to_be_visible()
    option.click()
    expect(dialog).not_to_be_visible()
    page.locator('#boot-splash').wait_for(state='hidden')
    expect(label).to_have_text(school_name)
    expect(page.locator('#partners-context')).to_contain_text(school_name)
    expect(page.locator('#partner-table')).to_have_attribute('aria-busy', 'false')


def assert_single_row_filter_strip(page, vw: int, school_name: str) -> dict:
    page.set_viewport_size({'width': vw, 'height': 900})
    page.wait_for_timeout(60)
    metrics = page.evaluate(
        """() => {
            const partners = document.querySelector('#partners').getBoundingClientRect();
            const strip = document.querySelector('#cgu-partner-filter-strip').getBoundingClientRect();
            const progBar = document.querySelector('#cgu-program-tabs');
            const progTabs = progBar && !progBar.hidden ? [...progBar.querySelectorAll('.cgu-program-tab')] : [];
            const colBar = document.querySelector('#cgu-college-quick-bar');
            const colBtns = colBar && !colBar.hidden ? [...colBar.querySelectorAll('.cgu-college-btn')] : [];
            const moreWrap = colBar && !colBar.hidden ? colBar.querySelector('.cgu-more-college-wrap') : null;
            const deptWrap = colBar && !colBar.hidden ? colBar.querySelector('.cgu-dept-inline-select') : null;

            const rectInfo = el => {
                const r = el.getBoundingClientRect();
                return { left: r.left, right: r.right, midY: r.top + r.height / 2, w: r.width, h: r.height, clipped: el.scrollWidth > el.clientWidth + 1 };
            };
            const progRects = progTabs.map(rectInfo);
            const colRects = colBtns.map(rectInfo);
            const mids = [...progRects.map(r => r.midY), ...colRects.map(r => r.midY)];
            let maxRight = Math.max(...colRects.map(r => r.right), ...(progRects.length ? progRects.map(r => r.right) : [0]));
            if (moreWrap) {
                const mr = moreWrap.getBoundingClientRect();
                mids.push(mr.top + mr.height / 2);
                maxRight = Math.max(maxRight, mr.right);
            }
            if (deptWrap) {
                const dr = deptWrap.getBoundingClientRect();
                mids.push(dr.top + dr.height / 2);
                maxRight = Math.max(maxRight, dr.right);
            }
            return {
                partnersLeft: partners.left,
                partnersRight: partners.right,
                stripLeft: strip.left,
                maxRight,
                progCount: progRects.length,
                colCount: colRects.length,
                hasMoreSelect: Boolean(moreWrap),
                hasDeptSelect: Boolean(deptWrap),
                deptWidth: deptWrap ? deptWrap.getBoundingClientRect().width : null,
                moreWidth: moreWrap ? moreWrap.getBoundingClientRect().width : null,
                ySpread: mids.length ? Math.max(...mids) - Math.min(...mids) : 0,
                anyClipped: [...progRects, ...colRects].some(r => r.clipped),
                minBtnWidth: Math.min(...[...progRects, ...colRects].map(r => r.w)),
            };
        }"""
    )
    ctx = f'{school_name}@{vw}px'
    assert metrics['ySpread'] < 8, f'Filter strip wrapped to multiple rows at {ctx}: {metrics}'
    assert not metrics['anyClipped'], f'Pill text clipped at {ctx}: {metrics}'
    assert metrics['minBtnWidth'] >= 50, f'Button squeezed at {ctx}: {metrics}'
    assert metrics['stripLeft'] >= metrics['partnersLeft'] - 1, ctx
    assert metrics['maxRight'] <= metrics['partnersRight'] + 1, f'Strip overflowed #partners at {ctx}: {metrics}'
    assert metrics['maxRight'] <= vw - 10, f'Strip too close to viewport edge at {ctx}: {metrics}'
    if metrics['deptWidth'] is not None:
        assert metrics['deptWidth'] >= 130, f'Dept select squeezed at {ctx}: {metrics}'
    if metrics['moreWidth'] is not None:
        assert metrics['moreWidth'] >= 104, f'More-college select squeezed at {ctx}: {metrics}'
    return metrics


def test_app_partners_html_matches_demo_template(tmp_path, monkeypatch):
    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: []))
    with TestClient(create_app(tmp_path)) as client:
        res = client.get('/')
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, 'html.parser')

    css_links = [link.get('href', '') for link in soup.select('link[rel="stylesheet"]')]
    assert any(href.startswith('/static/partner-search-template.css?v=') for href in css_links)

    head_actions = soup.select_one('#partners .pr-explore-head .cgu-explore-head-actions')
    assert head_actions is not None
    assert head_actions.select_one('[data-discovery-recents]') is not None
    assert head_actions.select_one('a.discovery-open-workspace[href="#favorites"]') is not None
    assert head_actions.select_one('.partner-view-switch') is not None

    criteria = soup.select_one('#partners > .discovery-search-tools > #discovery-criteria')
    assert criteria is not None
    assert soup.select_one('#partners .journey-search-layout #discovery-criteria') is None
    assert criteria.select_one('#cgu-criteria-summary') is not None
    assert criteria.select_one('#cgu-criteria-cta-label') is not None
    grade_input = criteria.select_one('#discovery-criteria-form input[name="grade"]')
    assert grade_input is not None and grade_input.get('placeholder') == '例如 78'

    strip = soup.select_one('#partners #cgu-partner-filter-strip')
    assert strip is not None
    assert strip.select_one('#cgu-program-tabs') is not None
    assert strip.select_one('#cgu-college-quick-bar') is not None
    assert soup.select_one('#partners #cgu-mgmt-channel-notice') is not None


def test_app_uniway_multi_school_partner_search_template(page, app_url):
    page.goto(app_url + '/?view=list#partners', wait_until='domcontentloaded')
    page.locator('#boot-splash').wait_for(state='hidden')
    page.evaluate('appReady')

    # Dismiss school onboarding if opened or pick 長庚大學 first
    if page.locator('#school-onboarding').is_visible():
        page.locator('#school-options [data-home-school="長庚大學"]').click()
        expect(page.locator('#school-onboarding')).not_to_be_visible()
    else:
        pick_home_school(page, '長庚大學')

    # Ensure list/card view is active
    if page.locator('[data-partner-view="list"]').get_attribute('aria-pressed') != 'true':
        page.locator('[data-partner-view="list"]').click()

    expect(page.locator('#partners')).to_be_visible()
    expect(page.locator('#partner-result-count')).to_contain_text('78')

    # 1. Verify exact demo.uniway template hierarchy & styling on 長庚大學 in app.uniway
    head_box = page.locator('#partners .pr-explore-head').bounding_box()
    criteria = page.locator('#partners #discovery-criteria')
    criteria_box = criteria.bounding_box()
    strip_box = page.locator('#cgu-partner-filter-strip').bounding_box()
    search_box = page.locator('#partners .pr-search').bounding_box()
    results_box = page.locator('#partners .journey-search-layout').bounding_box()
    assert head_box and criteria_box and strip_box and search_box and results_box
    assert criteria_box['height'] >= 52
    assert head_box['y'] < criteria_box['y'] < strip_box['y'] < search_box['y'] < results_box['y']

    # Redundant sidebar college filter is hidden when top college bar is visible
    expect(page.locator('#partners .pr-facet-selects label[for="college-filter"]')).not_to_be_visible()

    # Criteria summary hover keeps royal-blue gradient + crisp white heading
    criteria_summary = criteria.locator('summary')
    criteria_summary.hover()
    heading_color = criteria_summary.locator('.cgu-criteria-heading').evaluate('el => getComputedStyle(el).color')
    assert heading_color == 'rgb(255, 255, 255)'

    # CGU term label, program tabs, 5 inline college buttons, 36 departments, TOEIC flags & dual-degree tags
    expect(page.locator('#partner-term-tile option[value="fall"]')).to_have_text('2027 秋季（116-1）')
    prog_tabs = page.locator('#cgu-program-tabs')
    college_bar = page.locator('#cgu-college-quick-bar')
    expect(prog_tabs.locator('.cgu-program-tab')).to_have_count(3)
    expect(college_bar.locator('.cgu-college-btn')).to_have_count(5)
    expect(college_bar.locator('#cgu-more-college-select')).to_have_count(0)
    expect(college_bar.locator('#cgu-partner-dept-select')).to_be_attached()

    prog_tabs.locator('[data-cgu-program="dual_degree"]').click()
    expect(page.locator('#partner-result-count')).to_contain_text('共 14 所')
    expect(page.locator('#partner-table .pr-tags span.is-dual-degree').first).to_be_visible()
    prog_tabs.locator('[data-cgu-program=""]').click()

    college_bar.locator('[data-cgu-college="管理學院"]').click()
    expect(page.locator('#cgu-mgmt-channel-notice')).to_be_visible()
    expect(page.locator('#cgu-mgmt-channel-notice')).to_contain_text('管理學院另有院級交換')
    college_bar.locator('[data-cgu-college=""]').click()
    expect(page.locator('#cgu-mgmt-channel-notice')).not_to_be_visible()

    page.locator('#partner-search').fill('嘉泉')
    expect(page.locator('#partner-table .cgu-lang-flag.is-has-toeic').first).to_contain_text('有列多益')
    page.locator('#partner-search').fill('Lincoln')
    expect(page.locator('#partner-table .cgu-lang-flag.is-no-toeic').first).to_contain_text('此校未列多益')
    page.locator('#partner-search').fill('')

    # Criteria form scale sync + banner summary + reset
    criteria_summary.click()
    scale_sel = page.locator('#discovery-criteria-form [name="scale"]')
    grade_inp = page.locator('#discovery-criteria-form [name="grade"]')
    scale_sel.evaluate("el => { el.value = '4.3'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    expect(grade_inp).to_have_attribute('max', '4.3')
    expect(grade_inp).to_have_attribute('placeholder', '例如 3.6')
    scale_sel.evaluate("el => { el.value = '100'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    page.locator('#discovery-test').evaluate("el => { el.value = 'toeic'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    page.locator('#discovery-score').fill('750')
    grade_inp.fill('80')
    page.locator('#discovery-criteria-form button[type="submit"]').click()
    expect(page.locator('#cgu-criteria-summary')).to_contain_text('TOEIC 750')
    expect(page.locator('#cgu-criteria-summary')).to_contain_text('平均 80')
    expect(page.locator('#cgu-criteria-cta-label')).to_have_text('修改條件')
    criteria_summary.click()
    page.locator('#discovery-clear-criteria').click()
    criteria_summary.click()
    expect(page.locator('#cgu-criteria-cta-label')).to_have_text('設定條件')

    save_shot(page, 'app-cgu-partners.png')

    # 2. Switch to 國立臺灣大學 (12 colleges -> overflow「更多學院（9）」, status program tabs, no dept select)
    pick_home_school(page, '國立臺灣大學')
    expect(page.locator('#partner-term-tile option[value="fall"]')).to_have_text('秋季／上學期')
    expect(prog_tabs).to_be_visible()
    expect(prog_tabs).to_contain_text('本期開放')
    expect(prog_tabs).to_contain_text('備查待確認')
    expect(college_bar.locator('#cgu-more-college-select')).to_be_attached()
    expect(college_bar.locator('#cgu-partner-dept-select')).to_have_count(0)

    # Selecting an overflow college highlights the pill in royal-blue and filters partners
    page.locator('#cgu-more-college-select').evaluate(
        "el => { el.value = '電機資訊學院'; el.dispatchEvent(new Event('change', { bubbles: true })); }"
    )
    expect(college_bar.locator('.cgu-more-college-wrap')).to_have_class(
        'cgu-more-college-wrap has-more-college'
    )
    expect(page.locator('#partner-applied')).to_contain_text('電機資訊學院')
    save_shot(page, 'app-ntu-partners.png')
    college_bar.locator('[data-cgu-college=""]').click()
    expect(page.locator('#partner-applied')).to_have_text('')

    # 3. Switch to 國立陽明交通大學 (20 colleges, 146 depts, multi-program tabs)
    pick_home_school(page, '國立陽明交通大學')
    expect(prog_tabs).to_be_visible()
    expect(prog_tabs).to_contain_text('交換學生')
    expect(college_bar.locator('#cgu-more-college-select')).to_be_attached()
    expect(college_bar.locator('#cgu-partner-dept-select')).to_be_attached()
    expect(college_bar.locator('#cgu-partner-dept-select option').first).to_contain_text('全部 146 系所')
    # Unconfirmed NYCU partner boilerplate ("接待校當期語檢待核對") must NOT stamp a false TOEIC badge
    page.locator('#partner-search').fill('南開大學')
    expect(page.locator('#partner-table .cgu-lang-flag')).to_have_count(0)
    page.locator('#partner-search').fill('')
    for vw in (1042, 1280, 1440):
        assert_single_row_filter_strip(page, vw, '國立陽明交通大學')
    page.set_viewport_size({'width': 1440, 'height': 1000})
    save_shot(page, 'app-nycu-partners.png')

    # 4. Switch to 國立臺北大學 (7 colleges, 29 depts, language-track tabs: 英語組 / 日語組 / 中文組)
    pick_home_school(page, '國立臺北大學')
    expect(prog_tabs).to_be_visible()
    expect(prog_tabs).to_contain_text('英語組')
    expect(prog_tabs).to_contain_text('日語組')
    prog_tabs.locator('[data-cgu-program="lang_ja"]').click()
    expect(page.locator('#partner-applied')).to_contain_text('日語組')
    save_shot(page, 'app-ntpu-partners.png')
    prog_tabs.locator('[data-cgu-program=""]').click()

    # 5. Switch to 天主教輔仁大學 (14 colleges, alias reconciliation 外語學院 <-> 外國語文學院)
    pick_home_school(page, '天主教輔仁大學')
    page.locator('#cgu-more-college-select').evaluate(
        "el => { el.value = '外語學院'; el.dispatchEvent(new Event('change', { bubbles: true })); }"
    )
    fju_dept_opts = page.locator('#cgu-partner-dept-select option').all_inner_texts()
    assert any('英國語文學系' in opt for opt in fju_dept_opts), f'Expected FJU 外語學院 depts, got {fju_dept_opts}'
    college_bar.locator('[data-cgu-college=""]').click()

    # 6. Switch to 國立清華大學 (college/departmental channel notice verification)
    pick_home_school(page, '國立清華大學')
    if prog_tabs.locator('[data-cgu-program="level_dept"]').count() > 0:
        prog_tabs.locator('[data-cgu-program="level_dept"]').click()
        expect(page.locator('#cgu-mgmt-channel-notice')).to_be_visible()
        expect(page.locator('#cgu-mgmt-channel-notice')).to_contain_text('院系級交換管道')
        prog_tabs.locator('[data-cgu-program=""]').click()

    # 7. Switch to 國立臺北護理健康大學 (4 long college names -> overflow combobox prevents wrapping at 1042px–1920px)
    pick_home_school(page, '國立臺北護理健康大學')
    for vw in (1042, 1060, 1150, 1280, 1440, 1920):
        assert_single_row_filter_strip(page, vw, '國立臺北護理健康大學')

    # Mobile 360x740 + Dark Mode check
    page.set_viewport_size({'width': 360, 'height': 740})
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    page.wait_for_timeout(80)
    dark_check = page.evaluate(
        """() => {
            document.querySelector('#discovery-criteria').open = true;
            const criteriaClipped = [...document.querySelectorAll('#discovery-criteria-form > label')].some(l => {
                const lbl = l.querySelector('.glide-select__label, input');
                return lbl ? lbl.scrollWidth > lbl.clientWidth + 1 : false;
            });
            document.querySelector('#discovery-criteria').open = false;
            const docOverflow = document.documentElement.scrollWidth > document.documentElement.clientWidth + 1;
            return { criteriaClipped, docOverflow };
        }"""
    )
    assert not dark_check['criteriaClipped'], f'Mobile dark criteria clipped: {dark_check}'
    assert not dark_check['docOverflow'], f'Mobile dark horizontal overflow: {dark_check}'
    save_shot(page, 'app-mobile-360-dark.png')
