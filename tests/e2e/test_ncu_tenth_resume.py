"""Real student views show precise campus and document/year limits."""
from pathlib import Path
import os
import json
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu
from .test_ncu_ninth_resume import point_screenshot
OUT = Path(os.environ.get('NCU_RESUME_BROWSER_OUTPUT', '/tmp/ncu-final-browser'))
@pytest.mark.parametrize('width',[390,1280])
def test_tenth_two_named_campuses(page,live_server,width):
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_viewport_size({'width':width,'height':1050});page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server);page.locator('[data-partner-view="map"]').click()
    expect(page.locator('#partner-map-count')).to_have_text('214 所已定位 / 214 所符合條件',timeout=60_000)
    expect(page.locator('#map-school-select option')).to_have_count(215)
    expect(page.locator('#partner-map-status')).to_be_hidden(timeout=60_000)
    for row in json.loads(Path('sources/ncu/2026-10-11/resume-tenth-location-review.json').read_text())['coordinate_decisions']:
        page.locator('#map-school-select').select_option(value=row['school_name'])
        expect(page.locator('#partner-map-preview .map-preview-place')).to_contain_text(row['published_record']['city'])
        note=page.locator('#partner-map-preview .map-location-note');note.locator('summary').click()
        expect(note).to_contain_text('116');OUT.mkdir(parents=True,exist_ok=True)
        note.screenshot(path=str(OUT/f"{row['capture_row_id']}-{width}-location.png"))
    assert not errors and page.evaluate('document.documentElement.scrollWidth <= innerWidth')

@pytest.mark.parametrize('query,width,phrase',[
 ('卡斯魯爾',390,'2026/27空白DOCX已讀'),('圖爾庫',1280,'2027春迎新1/7–8')])
def test_tenth_host_reference_and_post_offer_scope(page,live_server,query,width,phrase):
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_viewport_size({'width':width,'height':1050});page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server);page.locator('[data-partner-view="list"]').click();page.locator('#partner-search').fill(query)
    summary=page.locator('#partner-table .partner-card > summary').first
    if summary.is_visible():summary.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click();OUT.mkdir(parents=True,exist_ok=True)
    if query=='卡斯魯爾':
        target=page.locator('#detail-overview .partner-student-summary li').filter(has_text=phrase).first
        expect(target).to_contain_text('不自行添成初次門檻');point_screenshot(target,OUT/f'hka-{width}-form-scope.png')
        page.locator('#detail-tab-application').click()
        step=page.locator('#detail-application .workflow-step').filter(has_text='核對外校當期文件並依通知申請').first
        step.locator(':scope > summary').click();expect(step.locator('.workflow-documents > li')).to_have_count(4)
    else:
        page.locator('#detail-tab-life').click();page.locator('#detail-life .life-official-guide > summary').click()
        target=page.locator('#destination-official-content li').filter(has_text=phrase).first
        expect(target).to_contain_text('無remote');point_screenshot(target,OUT/f'turku-{width}-orientation.png')
    assert not errors and page.evaluate('document.documentElement.scrollWidth <= innerWidth')
