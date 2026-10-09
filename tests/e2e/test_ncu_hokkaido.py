"""Hokkaido's two agreements, programme documents and life content reach students."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until


@pytest.mark.parametrize('width',[390,1440])
@pytest.mark.parametrize('level',['院級','校級'])
def test_ncu_hokkaido_two_agreements_documents_scope_and_life(page,live_server,width,level):
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    enter_public_site(page,live_server,'partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page);page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click();page.locator('#confirm-school').click()
    wait_until(page,"state.dashboard?.school_name === '國立中央大學'",timeout=60)
    if width<700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':
        page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(f'北海道大學({level})')
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    if width<700:page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#detail-overview .partner-student-summary')).to_contain_text('2027春')
    expect(page.locator('#detail-overview .partner-student-summary')).to_contain_text('不得修讀與日本語／日本學無關的課程')
    if level == '院級':
        expect(page.locator('#detail-overview .partner-student-summary')).to_contain_text('Internship program')
        expect(page.locator('#detail-overview .partner-student-summary')).to_contain_text('僅A學術交流')
    page.locator('#ncu-source-audit > summary').click()
    source=page.locator('#ncu-source-audit-body > details').filter(has_text='HUSTEP2026春syllabus83頁').first
    expect(source.locator(':scope > summary')).to_be_visible(timeout=60_000)
    source.locator(':scope > summary').click()
    scope=source.locator('.ncu-source-reading-scope')
    expect(scope).to_contain_text('原件83頁')
    expect(scope).to_contain_text('只原生讀PDF1、2、3、4')
    expect(scope).to_contain_text('其餘79頁未全文讀')
    assert source.locator('a').first.get_attribute('href')=='https://isc.high.hokudai.ac.jp/wp25/wp-content/uploads/2026/02/HUSTEP-Course-Syllabus-2026-Spring.pdf'
    out=Path('/tmp/ncu-audit/browser');out.mkdir(parents=True,exist_ok=True)
    scope.scroll_into_view_if_needed();page.screenshot(path=str(out/f'ncu-hokkaido-{level}-reading-scope-{width}.png'))
    page.locator('#detail-tab-application').click()
    def step(title):
        return page.locator('#detail-application .workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=title)).first
    general=step('七類初次參考');general.locator(':scope > summary').click()
    expect(general.locator('.workflow-documents > li')).to_have_count(7)
    expect(general.locator('.workflow-documents')).to_contain_text('SRS僅if any')
    expect(general.locator('.workflow-documents')).to_contain_text('大學＋研究所')
    expect(general.locator('.workflow-documents')).not_to_contain_text('簽署：本人')
    pss=step('PSS預先內諾');pss.locator(':scope > summary').click()
    expect(pss.locator('.workflow-documents > li')).to_have_count(6)
    expect(pss).to_contain_text('一般非必繳')
    if level=='校級':
        for title,count in [('HUSTEP：學生六件',6),('HUSTEP：母校四件',4),('JLCSP：學生五件',5),('JLCSP：母校三件',3)]:
            group=step(title);group.locator(':scope > summary').click()
            expect(group.locator('.workflow-documents > li')).to_have_count(count)
        mother=step('JLCSP：母校三件')
        expect(step('JLCSP：學生五件')).to_contain_text('即使母校要求亦不允許')
        expect(step('HUSTEP：學生六件')).not_to_contain_text('不得修讀與日本語／日本學無關的課程')
        expect(mother).to_contain_text('母校系所／國際事務承辦簽名')
        expect(mother).to_contain_text('Official Stamp')
        expect(mother).not_to_contain_text('簽署：本人')
        form=mother.get_by_role('link',name='官方參考表格（當期適用待確認）').first
        assert form.get_attribute('href')=='https://isc.high.hokudai.ac.jp/wp-content/uploads/2024/05/Certificate-of-Enrollment.pdf'
        form.scroll_into_view_if_needed();expect(form).to_be_visible()
    else:
        expect(page.locator('#detail-application')).not_to_contain_text('僅校級JLCSP：學生五件')
        general.locator('.workflow-documents').scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'ncu-hokkaido-{level}-programme-documents-{width}.png'))
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    housing=page.locator('#destination-official-content li').filter(has_text='英文807').first
    expect(housing).to_be_visible();expect(housing).to_contain_text('日文806')
    for text in ['50000','2300','日中寫含稅','英文寫＋稅','資格確認書','在留卡剩餘>3月','17920']:
        expect(page.locator('#destination-official-content')).to_contain_text(text)
    housing.scroll_into_view_if_needed();page.screenshot(path=str(out/f'ncu-hokkaido-{level}-housing-cost-{width}.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
