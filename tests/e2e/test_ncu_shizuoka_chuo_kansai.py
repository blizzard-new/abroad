"""Read real cards, school-specific documents, source limits and life costs."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until

CASES = [('shizuoka','靜岡大學','一般初次八類與最新空白表缺口',8),
         ('chuo','日本中央大學','Part1七類共通，C1／C2按學制擇一',7),
         ('kansai','關西大學','初次六類共通，並非母校七件',6)]


@pytest.mark.parametrize('width',[390,1440])
@pytest.mark.parametrize('slug,name,title,count',CASES)
def test_ncu_reference_scope_and_student_content(page,live_server,width,slug,name,title,count):
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
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
    page.locator('#partner-search').fill(name)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待核實')
    full_name={'shizuoka':'靜岡大學 Shizuoka University',
               'chuo':'日本中央大學 Chuo University',
               'kansai':'關西大學 Kansai University'}[slug]
    exact_trigger=f'.school-detail-trigger[data-school-name="{full_name}"]'
    if width<700:
        page.locator('#partner-table .partner-card').filter(has=page.locator(exact_trigger)).locator(':scope > summary').click()
    page.locator(f'#partner-table {exact_trigger}:visible').first.click()
    assert page.evaluate('new URLSearchParams(location.hash.slice(1)).get("school")') == full_name
    summary=page.locator('#detail-overview .partner-student-summary')
    terms={'shizuoka':['不是正式申請門檻','10/1','10/14','closed'],
           'chuo':['Tentative','N3','Kenkyusei','五門','六列'],
           'kansai':['500000','11/10','MCL','三月']}
    for term in terms[slug]:expect(summary).to_contain_text(term)
    page.locator('#ncu-source-audit > summary').click()
    expect(page.locator('#ncu-source-audit-body > p').first).to_contain_text('2026-10-09',timeout=60_000)
    if slug=='shizuoka':
        failed=page.locator('.ncu-unretrieved-source[data-source-id="host-shizuoka-housing-current"]')
        expect(failed).to_be_visible(timeout=60_000)
        expect(failed).to_contain_text('English Top')
        assert failed.get_by_role('link',name='已查網址（本次未取得）').get_attribute('href')=='https://www.suoic.shizuoka.ac.jp/english/international/campuslife/housing/'
    else:
        url=('https://www.chuo-u.ac.jp/uploads/2026/09/english_admissions_exchange_semester-or-full-year_05_20260924.xlsx' if slug=='chuo' else
             'https://www.kansai-u.ac.jp/Kokusai/KUGFCourseGuide/2026/#target/page_no=19')
        source=page.locator('#ncu-source-audit-body > details').filter(has=page.locator(f'a[href="{url}"]')).first
        expect(source.locator(':scope > summary')).to_be_visible(timeout=60_000)
        source.locator(':scope > summary').click()
        expect(source).to_contain_text('未逐門' if slug=='chuo' else '未取得PDF第19頁')
        assert source.get_by_role('link',name='官方公開來源').get_attribute('href')==url
    out=Path('/tmp/ncu-audit/browser');out.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(out/f'ncu-shizuoka-chuo-kansai-{slug}-source-{width}.png'))
    page.locator('#detail-tab-application').click()
    group=page.locator('#detail-application .workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=title)).first
    group.locator(':scope > summary').click()
    expect(group.locator('.workflow-documents > li')).to_have_count(count)
    expect(group.locator('.workflow-rule-meta > strong')).to_have_text('規劃範圍（當期適用待確認）')
    application=page.locator('#detail-application')
    if slug=='shizuoka':
        expect(group).to_contain_text('健康、Confirmation、經費新格式未取得')
        expect(application).to_contain_text('修士專業／研究')
        expect(application).to_contain_text('錄取後才通知宿舍')
    elif slug=='chuo':
        visa=application.locator('.workflow-step').filter(has=page.locator(':scope > summary').filter(has_text='行前COE／入學許可與Student visa')).first
        arrival=application.locator('.workflow-step').filter(has=page.locator(':scope > summary').filter(has_text='到校新生說明會及正式選課')).first
        expect(visa.locator(':scope > summary')).to_contain_text('行前準備')
        expect(arrival.locator(':scope > summary')).to_contain_text('抵達後')
        visa.locator(':scope > summary').click()
        arrival.locator(':scope > summary').click()
        expect(visa).to_contain_text('入境日本前須先取得COE、入學許可與Student visa')
        expect(arrival).to_contain_text('期間完成正式選課')
        visa.scroll_into_view_if_needed()
        page.screenshot(path=str(out/f'ncu-freeze-chuo-before-entry-{width}.png'))
        arrival.scroll_into_view_if_needed()
        page.screenshot(path=str(out/f'ncu-freeze-chuo-after-arrival-{width}.png'))
        for term in ['C1本科或C2研究所','Part2 J＋K','Kenkyusei原件明免']:
            expect(application).to_contain_text(term)
        plan=group.locator('.workflow-documents > li').filter(has_text='C1本科或C2')
        expect(plan).to_contain_text('按學制擇一')
        for suffix in ['C1_20260904.docx','C2_20260904.docx']:
            expect(application.locator(f'.workflow-sources a[href$="{suffix}"]').first).to_be_visible()
    else:
        expect(group).to_contain_text('能確認姓名的官方證件')
        expect(group).to_contain_text('不免除赴日簽證所需護照')
        visa=application.locator('.workflow-step').filter(has=page.locator(':scope > summary').filter(has_text='錄取後Welcome Pack／房源結果與visa')).first
        visa.locator(':scope > summary').click()
        expect(visa).to_contain_text('收到錄取及e-COE後申請visa；取得visa後才購票')
        visa.scroll_into_view_if_needed()
        page.screenshot(path=str(out/f'ncu-freeze-kansai-visa-ticket-{width}.png'))
        expect(group).to_contain_text('胸片≤6月')
        expect(group).to_contain_text('medical information')
        expect(group).to_contain_text('不能硬判發照三月')
        for term in ['親屬Dormitory Guarantee','不是要存入的deposit','11/10–19']:
            expect(application).to_contain_text(term)
        assert not group.locator('.workflow-documents > li').filter(has_text='成績').count()
    group.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'ncu-shizuoka-chuo-kansai-{slug}-packet-{width}.png'))
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    life=page.locator('#destination-official-content')
    life_terms={'shizuoka':['27400','23300','13200','2013/1','20日前'],
                'chuo':['350000','1150000','50000','1500','Spring2027'],
                'kansai':['41000','63000','末月','1650','全exchange','500000']}
    for term in life_terms[slug]:expect(life).to_contain_text(term)
    life.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'ncu-shizuoka-chuo-kansai-{slug}-life-{width}.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
