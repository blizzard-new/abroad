"""New source limits and stage-specific documents reach actual desktop/mobile UI."""
from pathlib import Path
import os
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

OUT = Path(os.environ.get('NCU_RESUME_BROWSER_OUTPUT', '/tmp/ncu-final-browser'))

@pytest.mark.parametrize('query,width,overview,life,count,later',[
    ('信州',390,'特別研究生','¥95,000',9,'信州COE系統再次提交文件'),
    ('烏迪內',1280,'bilateral agreement','自行提前找住宿',4,'烏迪內離校證明與成績單'),
    ('特魯瓦',390,'free mover','€333–600',1,'UTT抵達文件與住宿安排'),
    ('駒澤',1280,'不單靠協議年','14間',0,None),
])
def test_sixth_year_programme_forms_and_life_visible(page,live_server,query,width,overview,life,count,later):
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_viewport_size({'width':width,'height':956});page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server);page.locator('[data-partner-view="list"]').click();page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待核實')
    summary=page.locator('#partner-table .partner-card > summary').first
    if summary.is_visible():summary.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#detail-overview')).to_contain_text(overview)
    page.locator('#ncu-source-audit > summary').click();expect(page.locator('#ncu-source-audit-body')).to_contain_text('116',timeout=60_000)
    OUT.mkdir(parents=True,exist_ok=True)
    page.locator('#detail-tab-application').click()
    initial=page.locator('#detail-application .workflow-step').filter(has_text='核對外校當期文件並依通知申請').first
    initial.locator(':scope > summary').click();expect(initial.locator('.workflow-documents > li')).to_have_count(count)
    if later:expect(page.locator('#detail-application')).to_contain_text(later)
    if query=='信州':
        expect(initial).to_contain_text('已持有');expect(initial).to_contain_text('不申請也選No');expect(initial).to_contain_text('Sheet7')
    if query=='烏迪內':expect(initial).not_to_contain_text('Attendance Certificate')
    page.screenshot(path=str(OUT/f'{query}-{width}-application.png'))
    page.locator('#detail-tab-life').click();page.locator('#detail-life .life-official-guide > summary').click()
    expect(page.locator('#destination-official-content')).to_contain_text(life)
    expect(page.locator('#destination-official-content')).to_contain_text('116')
    page.screenshot(path=str(OUT/f'{query}-{width}-life.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
