"""The three reference packets remain clear on mobile and desktop."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu
from .test_open_catalog import wait_until,sign_in_cookie,attach_session
from .conftest import enter_public_site

CASES=[
 ('cuk','韓國天主教大學','韓國天主教大學 The Catholic University of Korea','天主教大學八類申請與父母帳戶條件件',9,9,['2027春','建議','超過一學期'],['USD3,400','8,453','父母'],['1,308,000','16週','優先']),
 ('inha','仁荷大學','仁荷大學 Inha University','仁荷九項清單與研究所條件件',11,12,['10/19','10/21','衝突'],['研究所','所有人','500KB'],['1,500,000','1,300,000','TB']),
 ('um','馬來亞大學','馬來亞大學 University of Malaya','馬來亞初次六類資料與母校模板',6,12,['iBT4','iBT80','9/16'],['JPEG','母校','條件'],['申請已關閉','750','2,800']),
]


@pytest.mark.parametrize('width',[390,1440])
@pytest.mark.parametrize('slug,query,name,title,initial,total,overview_terms,doc_terms,life_terms',CASES)
def test_fourteenth_packet_life_and_confirmation(page,live_server,tmp_path,width,slug,query,name,title,initial,total,overview_terms,doc_terms,life_terms):
    out=tmp_path/'browser';out.mkdir()
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    select_ncu(page,live_server)
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    trigger=f'.school-detail-trigger[data-school-name="{name}"]'
    if width<700:page.locator('#partner-table .partner-card').filter(has=page.locator(trigger)).locator(':scope > summary').click()
    page.locator(f'#partner-table {trigger}:visible').first.click()
    overview=page.locator('#detail-overview .partner-student-summary')
    for toggle in overview.locator('.partner-summary-more > summary').all():toggle.click()
    for term in overview_terms:expect(overview).to_contain_text(term)
    overview.get_by_text(overview_terms[0],exact=False).last.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-overview.png'))
    page.locator('#detail-tab-application').click()
    group=page.locator('#detail-application .workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=title)).first
    group.locator(':scope > summary').click()
    expect(group.locator('.workflow-documents > li')).to_have_count(initial)
    expect(group.locator('.workflow-rule-meta > strong')).to_have_text('規劃範圍（當期適用待確認）')
    for term in doc_terms:expect(group).to_contain_text(term)
    group.locator('.workflow-documents > li').first.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-documents.png'))
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    life=page.locator('#destination-official-content')
    for term in life_terms:expect(life).to_contain_text(term)
    for title in ['住宿與宿舍','每月生活預算']:
        card=page.locator('#life-content .life-card').filter(has=page.locator('h3').filter(has_text=title))
        expect(card).to_have_count(1)
        assert '中文翻譯尚未完成' not in card.locator('.life-evidence-text').inner_text()
        card.locator('.life-evidence-text').evaluate('(node)=>{node.scrollIntoView({block:"start"});window.scrollBy(0,-150)}')
        page.screenshot(path=str(out/f'{slug}-{width}-{ "housing" if title=="住宿與宿舍" else "budget"}.png'))
    session=sign_in_cookie(live_server,school='國立中央大學')
    live_server.verify_student(session['profile']['id'],university='國立中央大學')
    attach_session(page,live_server,session)
    enter_public_site(page,live_server,'application-center')
    wait_until(page,"state.dashboard?.school_name === '國立中央大學' && !state.applicationLoading && state.accountWorkspaceLoadingCount === 0",timeout=60)
    page.locator('#application-target-school').select_option(name)
    refs=page.locator('#application-requirement-list [data-document-applicability="needs_confirmation"]')
    expect(refs).to_have_count(total)
    page.locator('#ncu-host-admission').select_option('accepted')
    page.locator('#ncu-housing-choice').select_option('on_campus')
    expect(refs).to_have_count(total)
    for section in page.locator('#application-requirement-list .application-requirement-group').all():
        if section.get_attribute('open') is None:section.locator(':scope > summary').click()
    assert all('116當期' in r.inner_text()for r in refs.all())
    refs.first.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-confirmation.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
