"""Real browser loading and attribution for the full TKU census assets."""
import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .test_tku_acceptance import start


@pytest.mark.parametrize('width', [390,1280])
def test_tku_census_licensed_photos_load_and_points_keep_scope(page,live_server,width):
    _,errors=start(page,live_server,width,'partners')
    expect(page.locator('#partner-table')).to_have_attribute('data-result-count','287')
    results=page.evaluate('''async () => {
        const rows=state.dashboard.partner_universities;
        const licensed=rows.filter(r=>r.image_status==='verified');
        const photos=[];
        for (const row of licensed) {
            const image=new Image();image.src=row.image_url;await image.decode();
            const visual=schoolImageFor(row.school_name,row.country);
            photos.push({name:row.school_name,width:image.naturalWidth,height:image.naturalHeight,
                source:visual.official_page_url,author:row.reference_data.campus_photo_author,
                license:visual.license_name,license_url:visual.license_url,
                capture_period:row.reference_data.campus_photo_date,
                capture_period_status:row.reference_data.campus_photo_capture_year_status});
        }
        const module=await import('/static/partner-map.js');
        return {photos,points:module.pointsFor(rows).features,
            located:rows.filter(module.hasCoordinates).map(r=>({name:r.school_name,precision:r.location.precision})),
            unavailable:rows.filter(r=>!module.hasCoordinates(r)).length};
    }''')
    assert len(results['photos'])==262
    assert all(p['width']>0 and p['height']>0 and p['author'] and p['license_url'] for p in results['photos'])
    assert all(p['capture_period'] and p['capture_period_status']=='verified_capture_period' for p in results['photos'])
    assert len(results['points'])==len(results['located'])==264
    assert results['unavailable']==287-len(results['points'])
    assert sum(p['precision']=='representative' for p in results['located'])==255
    assert {p['properties']['name'] for p in results['points']}=={p['name'] for p in results['located']}
    page.locator('#partner-search').fill('成蹊')
    expect(page.locator('#partner-table')).to_have_attribute('data-result-count','1')
    if width<768:
        page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#school-detail-photo .school-image-credit')).to_contain_text('CC BY-SA 4.0')
    expect(page.locator('#school-detail-photo')).to_contain_text('李維俊')
    assert page.locator('#school-detail-photo a').filter(has_text='圖片授權').count()==1
    assert page.locator('#school-detail-photo img').evaluate('(image)=>image.complete&&image.naturalWidth>0')
    assert not errors,errors
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    output=Path(os.environ.get('TKU_CENSUS_ASSET_EVIDENCE','/tmp/tku-census-assets-evidence-20261011'))
    output.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(output/f'licensed-campus-detail-{width}.png'))
    (output/f'licensed-campus-detail-{width}.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
