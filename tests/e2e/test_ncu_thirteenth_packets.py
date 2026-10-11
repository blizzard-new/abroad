"""Inspect both new packets and living references on real mobile/desktop UI."""
from pathlib import Path

import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until, sign_in_cookie, attach_session


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('slug,query,name,title', [
    ('tsukuba','筑波大學','筑波大學 University of Tsukuba','筑波Web Entry初次申請與條件文件'),
    ('sookmyung','淑名女子大學',"淑名女子大學 Sookmyung Woman's University",'淑明初次七類申請文件'),
])
def test_thirteenth_public_packet_and_life(page,live_server,width,slug,query,name,title):
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    out=Path('docs/data/ncu-completion-20261011/resume/thirteenth/browser')
    out.mkdir(parents=True,exist_ok=True)
    enter_public_site(page,live_server,'partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page)
    page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator('#confirm-school').click()
    wait_until(page,"state.dashboard?.school_name === '國立中央大學'",timeout=60)
    if width<700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':
        page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    trigger=f'.school-detail-trigger[data-school-name="{name}"]'
    if width<700:
        card=page.locator('#partner-table .partner-card').filter(has=page.locator(trigger))
        card.locator(':scope > summary').click()
    page.locator(f'#partner-table {trigger}:visible').first.click()
    summary=page.locator('#detail-overview .partner-student-summary')
    for toggle in summary.locator('.partner-summary-more > summary').all():toggle.click()
    terms=['3/5','3/6','衝突','recommended','JASSO'] if slug=='tsukuba' else ['男女皆可','未標年annual','5/31','Medical Check-up']
    for term in terms:expect(summary).to_contain_text(term)
    summary.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-overview.png'),full_page=True)
    summary.get_by_text('2027/3/5' if slug=='tsukuba' else '男女皆可',exact=False).last.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-overview-focus.png'))
    page.locator('#detail-tab-application').click()
    application=page.locator('#detail-application')
    group=application.locator('.workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=title)).first
    group.locator(':scope > summary').click()
    expect(group.locator('.workflow-documents > li')).to_have_count(7)
    expect(group.locator('.workflow-rule-meta > strong')).to_have_text('規劃範圍（當期適用待確認）')
    expect(group).to_contain_text('116')
    for term in (['202206','202601','碩士／博士'] if slug=='tsukuba' else ['USD5,000','email','保險']):expect(group).to_contain_text(term)
    group.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-packet.png'))
    group.locator('.workflow-documents > li').first.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-documents.png'))
    if slug=='tsukuba':
        coe=application.locator('.workflow-step').filter(has=page.locator(':scope > summary').filter(has_text='筑波CoE同步申請與資助人條件附件')).first
        coe.locator(':scope > summary').click()
        expect(coe.locator('.workflow-documents > li')).to_have_count(11)
        for term in ['Supporter','收件號','日本國籍','JLPT']:expect(coe).to_contain_text(term)
        coe.scroll_into_view_if_needed()
        page.screenshot(path=str(out/f'{slug}-{width}-coe.png'))
        coe.locator('.workflow-documents > li').nth(6).scroll_into_view_if_needed()
        page.screenshot(path=str(out/f'{slug}-{width}-sponsor-documents.png'))
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    life=page.locator('#destination-official-content')
    terms=['2027/4/1','33,040','92,750','51,980','48,410','8,600','既有居住期'] if slug=='tsukuba' else ['260,000','未標年','自動豁免','10,000']
    for term in terms:expect(life).to_contain_text(term)
    life.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-life.png'))
    for title in ['住宿與宿舍','每月生活預算']:
        card=page.locator('#life-content .life-card').filter(has=page.locator('h3').filter(has_text=title))
        expect(card).to_have_count(1)
        assert '中文翻譯尚未完成' not in card.locator('.life-evidence-text').inner_text()
        if title=='住宿與宿舍':
            expect(card.locator('.life-evidence-text')).to_contain_text('33,040' if slug=='tsukuba' else '260,000')
            card.locator('.life-evidence-text').evaluate('(node) => {node.scrollIntoView({block:"start"}); window.scrollBy(0,-150)}')
            page.screenshot(path=str(out/f'{slug}-{width}-housing.png'))
    session=sign_in_cookie(live_server,school='國立中央大學')
    live_server.verify_student(session['profile']['id'],university='國立中央大學')
    attach_session(page,live_server,session)
    enter_public_site(page,live_server,'application-center')
    wait_until(page,"state.dashboard?.school_name === '國立中央大學' && !state.applicationLoading && state.accountWorkspaceLoadingCount === 0",timeout=60)
    page.locator('#application-target-school').select_option(name)
    refs=page.locator('#application-requirement-list [data-document-applicability="needs_confirmation"]')
    expect(refs).to_have_count(18 if slug=='tsukuba' else 7)
    page.locator('#ncu-host-admission').select_option('accepted')
    page.locator('#ncu-housing-choice').select_option('on_campus')
    expect(refs).to_have_count(18 if slug=='tsukuba' else 7)
    for group in page.locator('#application-requirement-list .application-requirement-group').all():
        if group.get_attribute('open') is None:group.locator(':scope > summary').click()
    assert all('116當期' in item.inner_text() for item in refs.all())
    if slug=='tsukuba':expect(refs.filter(has_text='CoE選Supporter者才需')).to_have_count(5)
    refs.first.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-confirmation.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
