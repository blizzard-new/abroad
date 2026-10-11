"""Withdrawn photos and credits absent in real responsive TKU detail pages."""
import json,os
from pathlib import Path
import pytest
from playwright.sync_api import expect
from .test_tku_acceptance import start

@pytest.mark.parametrize('width',[390,1280])
def test_fixed_two_photos_are_not_displayed(page,live_server,width):
 _,errors=start(page,live_server,width,'partners');out=Path(os.environ.get('TKU_FIXED_PHOTO_UI_EVIDENCE','/tmp/tku-fixed-photo-ui-evidence'));out.mkdir(parents=True,exist_ok=True);results=[]
 for query in ['桑德蘭','墨西哥州立自治']:
  page.locator('#partner-search').fill(query);expect(page.locator('#partner-table')).to_have_attribute('data-result-count','1')
  if width<768:page.locator('#partner-table .partner-card > summary').first.click()
  assert page.locator('#partner-table img[src*="tku-sister-65-alternative"], #partner-table img[src*="tku-sister-52-alternative"]').count()==0
  page.locator('#partner-table .school-detail-trigger:visible').first.click();expect(page.locator('#school-detail-photo img')).to_have_count(0)
  assert 'Unknown author' not in page.locator('#school-detail-photo').inner_text()
  name=page.evaluate('state.activeSchool');row=page.evaluate('(n)=>state.dashboard.partner_universities.find(p=>p.school_name===n)',name)
  assert row['image_status']=='missing' and row['image_url'] is None and row['image_page_url'] is None
  page.locator('#detail-tab-life').click();page.locator('.life-official-guide > summary').click();expect(page.locator('#destination-official-content')).to_be_visible()
  assert page.locator('#destination-official-content img[src*="tku-sister-65-alternative"], #destination-official-content img[src*="tku-sister-52-alternative"]').count()==0
  results.append(dict(school=name,image_status=row['image_status'],image_url=row['image_url'],image_page_url=row['image_page_url'],wrong_or_unverified_credit_absent=True))
  page.screenshot(path=str(out/f'withdrawn-{query}-{width}.png'));page.evaluate("location.hash='#partners'");expect(page.locator('#partner-search')).to_be_visible()
 assert not errors,errors
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 (out/f'withdrawn-{width}.json').write_text(json.dumps(dict(status='passed',width=width,schools=results,page_errors=errors),ensure_ascii=False,indent=2)+'\n')
