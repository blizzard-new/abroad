"""New scoped/year-reviewed facts shown on390/1280 actual TKU cards and guide."""
import json,os
from pathlib import Path
import pytest
from playwright.sync_api import expect
from .test_tku_acceptance import start

@pytest.mark.parametrize('width',[390,1280])
def test_new_remaining_scope_references_show_actual_year_and_track(page,live_server,width):
 _,errors=start(page,live_server,width,'partners');out=Path(os.environ.get('TKU_MILESTONE6_UI_EVIDENCE','/tmp/tku-milestone6-ui-evidence'));out.mkdir(parents=True,exist_ok=True);results=[]
 for query,expected in [('青山學院','2026/11/10'),('阿根廷企業','5/15'),('國立金門','國內交換')]:
  page.locator('#partner-search').fill(query);expect(page.locator('#partner-table')).to_have_attribute('data-result-count','1')
  if width<768:page.locator('#partner-table .partner-card > summary').first.click()
  page.locator('#partner-table .school-detail-trigger:visible').first.click();content=page.locator('#school-detail-content')
  page.locator('.tku-source-details > summary').click();expect(content).to_contain_text(expected,timeout=30000);expect(content).to_contain_text('未核實')
  expect(page.locator('#school-detail-primary-facts')).to_contain_text('本期名額未核實')
  page.locator('#detail-tab-life').click();page.locator('.life-official-guide > summary').click();expect(page.locator('#destination-official-content')).to_contain_text(expected)
  card=page.locator('.student-guide-section-card').filter(has_text=expected).first;card.scroll_into_view_if_needed();expect(card).to_be_visible();expect(card).to_contain_text('適用：')
  name=page.evaluate('state.activeSchool');row=page.evaluate('(n)=>state.dashboard.partner_universities.find(p=>p.school_name===n)',name)
  assert row['quota'] is None and row['availability_status'] in ['agreement_only','reference_only']
  results.append(dict(school=name,expected_visible=expected,quota=row['quota'],availability_status=row['availability_status'],official_sources=page.locator('.tku-source-details a').evaluate_all('(xs)=>xs.map(x=>x.href)')))
  page.screenshot(path=str(out/f'remaining-host-{query}-{width}.png'));page.evaluate("location.hash='#partners'");expect(page.locator('#partner-search')).to_be_visible()
 assert not errors,errors
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 (out/f'remaining-host-{width}.json').write_text(json.dumps(dict(status='passed',width=width,schools=results,page_errors=errors),ensure_ascii=False,indent=2)+'\n')
