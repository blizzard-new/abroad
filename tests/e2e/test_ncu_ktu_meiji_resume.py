import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu


@pytest.mark.parametrize('query,width,rid',[('考納斯',390,'ncu-091'),('考納斯',1280,'ncu-091'),('明治',390,'ncu-138'),('明治',1280,'ncu-138')])
def test_source_years_documents_and_cost_scopes_in_actual_browser(page,live_server,query,width,rid, tmp_path):
    OUTPUT = tmp_path / 'browser'
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_viewport_size({'width':width,'height':1050})
    page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server)
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(query)
    summary=page.locator('#partner-table .partner-card > summary').first
    if summary.is_visible():summary.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    page.locator('#ncu-source-audit > summary').click()
    expect(page.locator('#ncu-source-audit-body')).to_contain_text('2025/26' if rid=='ncu-091' else '2026/1/21',timeout=60_000)
    page.locator('#detail-tab-application').click()
    expect(page.locator('#detail-application')).to_contain_text('仍需確認')
    step=page.locator('#detail-application .workflow-step').filter(has_text='核對外校當期文件並依通知申請').first
    step.locator(':scope > summary').click()
    expect(step.locator('.workflow-documents > li')).to_have_count(5 if rid=='ncu-091' else 11)
    expect(step.locator('[data-step-rule-id]')).to_have_attribute('data-step-rule-id',rid+'-host-apply')
    if rid=='ncu-138':
        coe=page.locator('#detail-application .workflow-step').filter(has_text='明治CoE及擇一財力文件').first
        coe.locator(':scope > summary').click()
        expect(coe.locator('.workflow-documents > li')).to_have_count(2)
        expect(coe).to_contain_text('不等錄取')
    expect(page.locator('#detail-application')).to_contain_text('Final degree project' if rid=='ncu-091' else 'PG英語Research Plan')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(OUTPUT/f'{rid}-{width}-application.png'))
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    expect(page.locator('#destination-official-content')).to_contain_text('109.62' if rid=='ncu-091' else '84,900')
    expect(page.locator('#destination-official-content')).to_contain_text('不標保證' if rid=='ncu-091' else '不可拒特定宿舍')
    page.screenshot(path=str(OUTPUT/f'{rid}-{width}-life.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
