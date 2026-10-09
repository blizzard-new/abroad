"""Read the three actual student detail, document and life screens at both widths."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until

CASES=[('nufs','名古屋外國語大學','名古屋外國語大學 Nagoya University of Foreign Studies','NUFS初次申請與條件附件',13),
       ('kumamoto','熊本大學','熊本大學 Kumamoto University','熊本由中央取得STEP申請packet',0),
       ('ryukoku','龍谷大學','龍谷大學 Ryukoku University','龍谷初次申請與六份指定附件',6)]


@pytest.mark.parametrize('width',[390,1440])
@pytest.mark.parametrize('slug,name,full_name,title,count',CASES)
def test_next3_reference_packets_and_living_content(page,live_server,width,slug,name,full_name,title,count):
    page.set_viewport_size({'width':width,'height':956});page.emulate_media(reduced_motion='reduce')
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    out=Path(os.environ.get('NCU_NEXT3_BROWSER_OUT','/workspace/ncu-verification-tmp/next3-browser'));out.mkdir(parents=True,exist_ok=True)
    enter_public_site(page,live_server,'partners');expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page);page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click();page.locator('#confirm-school').click()
    wait_until(page,"state.dashboard?.school_name === '國立中央大學'",timeout=60)
    if width<700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click();page.locator('#partner-search').fill(name)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    trigger=f'.school-detail-trigger[data-school-name="{full_name}"]'
    card_term={'nufs':'GJP不強制JLPT','kumamoto':'TOEFL iBT61','ryukoku':'建議300小時或N4'}[slug]
    if width<700:
        card=page.locator('#partner-table .partner-card').filter(has=page.locator(trigger))
        card.locator(':scope > summary').click()
        assert card_term in card.locator('.partner-card-summary').inner_text()
        card.scroll_into_view_if_needed()
    else:
        row=page.locator('#partner-table tr').filter(has=page.locator(trigger))
        row.locator('.partner-condition-disclosure > summary').click()
        assert card_term in row.locator('.partner-condition-disclosure').inner_text()
        row.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-card-or-row.png'))
    page.locator(f'#partner-table {trigger}:visible').first.click()
    assert page.evaluate('new URLSearchParams(location.hash.slice(1)).get("school")')==full_name
    summary=page.locator('#detail-overview .partner-student-summary')
    terms={'nufs':['GJP','N2','N1','2026/10/31','不是所有文件三月內'],
           'kumamoto':['packet','三年級','594,600','平台加總'],
           'ryukoku':['建議','300','N4','JEP','正式結果']}
    for toggle in summary.locator('.partner-summary-more > summary').all():toggle.click()
    for term in terms[slug]:assert term in summary.inner_text(),term
    summary.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-overview.png'),full_page=True)
    page.locator('#ncu-source-audit > summary').click()
    expect(page.locator('#ncu-source-audit-body > p').first).to_contain_text('2026-10-09',timeout=60_000)
    if slug!='nufs':
        ident='host-kumamoto-next3-isa-address' if slug=='kumamoto' else 'host-ryukoku-next3-syllabus-index'
        failure=page.locator(f'.ncu-unretrieved-source[data-source-id="{ident}"]')
        expect(failure).to_be_visible(timeout=60_000)
        expect(failure).to_contain_text('403' if slug=='kumamoto' else '入口')
        failure.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-source-gap.png'))
    page.locator('#detail-tab-application').click();application=page.locator('#detail-application')
    group=application.locator('.workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=title)).first
    group.locator(':scope > summary').click()
    expect(group.locator('.workflow-documents > li')).to_have_count(count)
    expect(group.locator('.workflow-rule-meta > strong')).to_have_text('規劃範圍（當期適用待確認）')
    if slug=='nufs':
        for term in ['擇一','父母帳戶','有病況','無則免','線上宿舍規則同意勾選']:
            expect(group).to_contain_text(term)
    elif slug=='kumamoto':expect(group).to_contain_text('未取得')
    else:
        for term in ['不能Xray可其他結核檢查','正式結果','零學習也交']:
            expect(group).to_contain_text(term)
    group.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-packet.png'))
    titles={'nufs':['NUFS審查與COE代辦','NUFS取得COE後申請學生簽證','NUFS依指定到達安排航班及接送','NUFS入寮、新生說明會、登記與NHI'],
            'kumamoto':['熊本录取後核對COE材料','熊本COE及入學許可後申請學生簽證','熊本指定日自行購票與提供行程','熊本抵達、定址與註冊準備'],
            'ryukoku':['龍谷審查錄取與COE代辦','龍谷收到COE後申請學生簽證','龍谷核對簽證與暫定入寮後安排航班','龍谷到校新生說明會、NHI與銀行扣款']}
    phase_terms=['錄取與COE','簽證準備','機票與行程','到校準備']
    groups=[]
    for stage_title,phase in zip(titles[slug],phase_terms):
        g=application.locator('.workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=stage_title)).first
        expect(g.locator(':scope > summary')).to_contain_text(phase);g.locator(':scope > summary').click();groups.append(g)
    groups[0].scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-coe-visa.png'))
    groups[-1].scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-arrival.png'))
    page.locator('#detail-tab-life').click();page.locator('#detail-life .life-official-guide > summary').click()
    life=page.locator('#destination-official-content')
    living={'nufs':['3.5萬','6,600','NHI','80%'],
            'kumamoto':['plan','9–16','7/17','一月','平台加總'],
            'ryukoku':['1,960','1,980','5日與7日','1,500–2,000']}
    for term in living[slug]:expect(life).to_contain_text(term)
    life.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-life.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
