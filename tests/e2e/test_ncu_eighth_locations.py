from pathlib import Path
import json
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu
OUTPUT=Path('docs/data/ncu-completion-20261011/resume/eighth/browser')

@pytest.mark.parametrize('width',[390,1280])
def test_eighth_twelve_campus_previews_and_sources_visible(page,live_server,width):
    rows=json.loads(Path('sources/ncu/2026-10-11/resume-eighth-location-review.json').read_text())['coordinate_decisions']
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_viewport_size({'width':width,'height':1050});page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server);page.locator('[data-partner-view="map"]').click()
    expect(page.locator('#partner-map-count')).to_have_text('214 所已定位 / 214 所符合條件',timeout=60_000)
    expect(page.locator('#partner-map-status')).to_be_hidden(timeout=60_000)
    for row in rows:
        page.locator('#map-school-select').select_option(value=row['school_name'])
        expect(page.locator('#partner-map-preview')).to_contain_text(row['school_name'])
        expect(page.locator('#partner-map-preview .map-preview-place')).to_contain_text(row['published_record']['city'])
        expect(page.locator('#partner-map-preview')).to_contain_text('本期名額待公告')
        note=page.locator('#partner-map-preview .map-location-note');note.locator('summary').click()
        expect(note.locator('p')).to_contain_text(row['published_record']['note'])
        OUTPUT.mkdir(parents=True,exist_ok=True);note.screenshot(path=str(OUTPUT/f"{row['capture_row_id']}-{width}-campus-note.png"))
    page.screenshot(path=str(OUTPUT/f'all-twelve-reviewed-{width}.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth') and not errors
