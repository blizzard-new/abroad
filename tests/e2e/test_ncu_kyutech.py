"""Kyutech's audited references and document stages reach real student views."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until


@pytest.mark.parametrize('width', [390, 1440])
def test_ncu_kyutech_support_levels_arrival_split_and_reading_scope(page, live_server, width):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, 'partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page); page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click(); page.locator('#confirm-school').click()
    wait_until(page, "state.dashboard?.school_name === '國立中央大學'", timeout=60)
    if width < 700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded') == 'true':
        page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click(); page.locator('#partner-search').fill('九州工業')
    expect(page.locator('#partner-table')).to_contain_text('本期名額待核實')
    if width < 700:
        page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#detail-overview .partner-student-summary')).to_contain_text('非SEIC')
    expect(page.locator('#detail-application')).to_contain_text('校規初次三類')
    page.locator('#ncu-source-audit > summary').click()
    source = page.locator('#ncu-source-audit-body > details').filter(has_text='原件170頁').first
    expect(source.locator(':scope > summary')).to_be_visible(timeout=60_000)
    source.locator(':scope > summary').click()
    scope = source.locator('.ncu-source-reading-scope')
    expect(scope).to_contain_text('只原生讀PDF145–148')
    expect(scope).to_contain_text('其餘166頁未全文讀')
    href = source.locator('a').first.get_attribute('href')
    assert href == 'https://www.tobata.kyutech.ac.jp/wp-content/uploads/2026/03/binran2026.pdf'
    out = Path('/tmp/ncu-audit/browser'); out.mkdir(parents=True, exist_ok=True)
    scope.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-kyutech-original-reading-scope-{width}.png'))
    page.locator('#detail-tab-application').click()

    def step(title):
        return page.locator('#detail-application .workflow-step').filter(
            has=page.locator(':scope > summary').filter(has_text=title)
        ).first

    for title, count in [('校規初次三類', 3), ('指定願書及母校推薦', 2), ('另交誓約書', 1)]:
        group = step(title); group.locator(':scope > summary').click()
        expect(group.locator('.workflow-documents > li')).to_have_count(count)
        expect(group).not_to_contain_text('簽署：本人')
    common = step('五類資料與證件'); common.locator(':scope > summary').click()
    expect(common.locator('.workflow-documents > li')).to_have_count(5)
    expect(common.locator('.workflow-documents')).not_to_contain_text('履修')
    auditing = step('履修登錄票'); auditing.locator(':scope > summary').click()
    expect(auditing.locator('.workflow-documents > li')).to_have_count(1)
    expect(auditing).to_contain_text('僅Special Auditing')
    common.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-kyutech-arrival-five-plus-auditing-{width}.png'))
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    housing = page.locator('#destination-official-content li').filter(has_text='14429').first
    expect(housing).to_be_visible()
    expect(housing).to_contain_text('生效範圍未明')
    expect(page.locator('#destination-official-content')).to_contain_text('7000')
    expect(page.locator('#destination-official-content')).to_contain_text('17920')
    expect(page.locator('#destination-official-content')).to_contain_text('資格確認書')
    housing.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-kyutech-housing-conflict-{width}.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
