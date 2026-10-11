from pathlib import Path
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu
from .test_open_catalog import wait_until
OUTPUT=Path('docs/data/ncu-completion-20261011/resume/seventh/browser')

@pytest.mark.parametrize('query,width,author,licence,scope',[
    ('蘇門答臘',390,'Fandiamendra','CC BY-SA 4.0','2019年4月29日'),
    ('胡志明市自然科學',1280,'trungydang','CC BY 3.0','227 Nguyễn Văn Cừ'),
])
def test_seventh_real_photo_and_licence_visible(page,live_server,query,width,author,licence,scope):
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_viewport_size({'width':width,'height':1050});page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server);page.locator('[data-partner-view="list"]').click();page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    wait_until(page,"document.querySelector('#partner-table .school-photo img')?.naturalWidth > 0",timeout=30)
    s=page.locator('#partner-table .partner-card > summary').first
    if s.is_visible():s.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click();page.locator('#detail-tab-life').click();page.locator('#detail-life .life-official-guide > summary').click()
    figure=page.locator('.student-guide-photo-grid figure');expect(figure).to_have_count(1)
    caption=figure.locator('figcaption');expect(caption).to_contain_text(author);expect(caption).to_contain_text('授權：'+licence);expect(caption).to_contain_text(scope)
    expect(caption).to_contain_text('116錄取校區仍待確認');expect(caption.get_by_role('link',name='圖片授權')).to_be_visible()
    wait_until(page,"document.querySelector('.student-guide-photo-grid img')?.naturalWidth > 0",timeout=30)
    OUTPUT.mkdir(parents=True,exist_ok=True);figure.screenshot(path=str(OUTPUT/f'{query}-{width}-photo.png'));page.screenshot(path=str(OUTPUT/f'{query}-{width}-life.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth') and not errors


def test_seventh_nine_named_campus_previews_on_globe(page,live_server):
    import json
    rows=json.loads(Path('sources/ncu/2026-10-11/resume-seventh-location-review.json').read_text())['coordinate_decisions']
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_viewport_size({'width':1280,'height':1050});page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server);page.locator('[data-partner-view="map"]').click()
    expect(page.locator('#partner-map-count')).to_have_text('212 所已定位 / 214 所符合條件',timeout=60_000)
    expect(page.locator('#partner-map-status')).to_be_hidden(timeout=60_000)
    for row in rows:
        name=row['school_name'];page.locator('#map-school-select').select_option(value=name)
        expect(page.locator('#partner-map-preview')).to_contain_text(name)
        expect(page.locator('#partner-map-preview .map-preview-place')).to_contain_text(row['published_record']['city'])
        expect(page.locator('#partner-map-preview')).to_contain_text('本期名額待公告')
        OUTPUT.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(OUTPUT/f"{row['capture_row_id']}-map-preview.png"))
        note=page.locator('#partner-map-preview .map-location-note')
        note.locator('summary').click()
        expect(note.locator('p')).to_contain_text(row['published_record']['note'])
        note.screenshot(path=str(OUTPUT/f"{row['capture_row_id']}-campus-note.png"))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth') and not errors
