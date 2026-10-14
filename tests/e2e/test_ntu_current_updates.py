"""The updated source scope is visible on mobile and desktop."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site
from .test_open_catalog import wait_until


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('school,fragment,case', [
    ('維也納大學', '1 學年名額（最多 2 人次）', 'quota'),
    ('雪梨科技大學', 'Student Visa (Subclass 500)', 'visa'),
    ('加拿大英屬哥倫比亞大學（卑詩大學）', '2027/9/15', 'UBC'),
])
def test_current_updates_have_visible_year_source_and_guard(page, live_server, width, school, fragment, case):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, 'partners')
    page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立臺灣大學"]').click()
    wait_until(page, "state.dashboard?.school_name === '國立臺灣大學'")
    if width < 700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded') == 'true':
        page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(school)
    if case == 'quota':
        expect(page.locator('#partner-table')).to_contain_text('名額已公告')
        expect(page.locator('#partner-table')).to_contain_text('選填')
    if width < 700:
        page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#school-detail-view')).to_be_visible()
    page.get_by_role('tab', name='生活情報', exact=True).click()
    page.locator('.life-official-guide > summary').click()
    card = page.locator('.student-guide-section-card').filter(has_text='臺大最新來源更新（2026-10-14）')
    expect(card).to_contain_text(fragment)
    if case == 'quota':
        expect(card).to_contain_text('不保證錄取')
        expect(card).to_contain_text('第一學期出國')
    elif case == 'visa':
        expect(card).to_contain_text('臺大新增簽證提醒')
        expect(card).to_contain_text('未獨立核實為新法律或一律禁止')
    else:
        expect(card).to_contain_text('非臺大校內報名期限')
        expect(card).to_contain_text('295.10')
        expect(card).to_contain_text('不重複計為首次發現')
        expect(page.locator('#destination-official-content')).not_to_contain_text('中正的校內資格')
    assert card.locator('a[href*="ntu.edu.tw"]').count() > 0
    card.scroll_into_view_if_needed()
    expect(card).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    partner = page.evaluate('(school) => state.dashboard.partner_universities.find(p=>p.school_name===school)', school)
    assert partner['availability_status'] != 'open'
    if case != 'quota': assert partner['quota'] is None
    assert not errors
    target = Path(os.environ.get('VISUAL_EVIDENCE_DIR', '/tmp/ntu-current-source-browser'))
    target.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(target / f'{case}-{width}.png'))
