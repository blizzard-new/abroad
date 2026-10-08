"""Niigata reference periods and route-specific files reach actual browser views."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until


@pytest.mark.parametrize('width', [390, 1440])
def test_ncu_niigata_iec_graduate_finance_and_source_scope(page, live_server, width):
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
    page.locator('[data-partner-view="list"]').click(); page.locator('#partner-search').fill('新潟')
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    if width < 700:
        page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#detail-overview .partner-student-summary')).to_contain_text('不是一般GPA2.3')
    expect(page.locator('#detail-application')).to_contain_text('IEC No.1／2')
    page.locator('#ncu-source-audit > summary').click()
    blank = page.locator('#ncu-source-audit-body > details').filter(has_text='新潟2027春網站失敗時備用申請XLSX').first
    expect(blank.locator(':scope > summary')).to_be_visible(timeout=60_000)
    blank.locator(':scope > summary').click()
    scope = blank.locator('.ncu-source-scope').filter(has_text='原件4張、已讀3張')
    expect(scope).to_be_visible()
    part = blank.locator('details').first; part.locator(':scope > summary').click()
    expect(part.locator('pre')).to_contain_text('Spring Semester 2027')
    expect(part.locator('pre')).not_to_contain_text('6th year / 6年ネン')
    out = Path('/tmp/ncu-audit/browser'); out.mkdir(parents=True, exist_ok=True)
    scope.evaluate('el=>el.scrollIntoView({block:"start"})')
    page.evaluate('scrollBy(0,-150)')
    page.screenshot(path=str(out / f'ncu-niigata-blank-sheet-scope-{width}.png'))
    page.locator('#detail-tab-application').click()
    def step(title):
        return page.locator('#detail-application .workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=title)).first
    iec = step('僅確認IEC No.1／2：初次六類學生文件'); iec.locator(':scope > summary').click()
    expect(iec.locator('.workflow-documents > li')).to_have_count(6)
    expect(iec).to_contain_text('初次繳、不貼照片')
    expect(iec).to_contain_text('簽署：檢查醫師')
    mother = step('僅IEC母校合一提名'); mother.locator(':scope > summary').click()
    expect(mother).to_contain_text('簽名或公印擇一')
    expect(mother).not_to_contain_text('簽署：本人')
    graduate = step('僅研究科No.3–11：初次基本資訊'); graduate.locator(':scope > summary').click()
    expect(graduate.locator('.workflow-documents > li')).to_have_count(1)
    expect(graduate).to_contain_text('非入學申請書')
    expect(graduate).not_to_contain_text('IEC No.1／2初次學生六類')
    graduate.locator('.workflow-documents').scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-niigata-graduate-basic-only-{width}.png'))
    for title, count in [('僅IEC本人支應：一份本人存款', 1), ('僅IEC他人支應：四份支應文件', 4)]:
        finance = step(title); finance.locator(':scope > summary').click()
        expect(finance.locator('.workflow-documents > li')).to_have_count(count)
        expect(finance).to_contain_text('89000')
    page.locator('#detail-tab-life').click(); page.locator('#detail-life .life-official-guide > summary').click()
    housing = page.locator('#destination-official-content li').filter(has_text='一次初期67500').first
    expect(housing).to_be_visible()
    expect(housing).not_to_contain_text('【中央115歷史名單')
    booking = page.locator('#destination-official-content li').filter(has_text='as ofFeb2023').first
    expect(booking).to_contain_text('不是2027確認截止')
    expect(page.locator('#destination-official-content')).to_contain_text('2027/1/4')
    housing.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-niigata-housing-cost-scope-{width}.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
