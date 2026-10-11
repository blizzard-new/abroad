"""Decode every newly reviewed NTU photo through the actual scoped catalogue."""
import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site, open_navigation


@pytest.mark.parametrize('width', [390, 1440])
def test_ntu_nineteen_reviewed_photo_bytes_load_with_matching_credit(page, live_server, width):
    reviewed = [r for r in json.loads(Path('sources/ntu/completion-2026-10-11.json').read_text())['schools'] if r.get('photo')]
    assert len(reviewed) == 19
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    enter_public_site(page,live_server,'partners')
    open_navigation(page)
    page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立臺灣大學"]').click()
    page.locator('#confirm-school').click()
    page.wait_for_function("state.dashboard?.school_name==='國立臺灣大學' && !state.partnerDataLoading")
    results=page.evaluate('''async reviews => {
      const results=[];
      for(const review of reviews) {
        const partner=state.dashboard.partner_universities.find(p=>p.school_name===review.school_name);
        const visual=schoolImageFor(partner.school_name,partner.country);
        const response=await fetch(partner.image_url);
        const bitmap=await createImageBitmap(await response.blob());
        results.push({name:partner.school_name,country:partner.country,status:response.status,
          width:bitmap.width,height:bitmap.height,api:partner.image_url,visual:visual.local_path,
          credit:visual.note,license:visual.license_name,license_url:visual.license_url});
        bitmap.close();
      }
      return results;
    }''',reviewed)
    for source,actual in zip(reviewed,results):
        photo=source['photo']
        assert actual['name']==source['school_name'] and actual['country']==source['country']
        assert actual['status']==200 and actual['width']==photo['width'] and actual['height']==photo['height']
        assert actual['api'].endswith(photo['local_path']) and actual['visual']==photo['local_path']
        assert photo['artist'] in actual['credit'] and actual['license_url']==photo['license_url']
        assert actual['license']==photo['license_name']
    assert not errors
    output=Path(os.environ.get('VISUAL_EVIDENCE_DIR','/tmp/integrated-reviewed-photos'));output.mkdir(parents=True,exist_ok=True)
    (output/f'ntu-19-decoded-{width}.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
