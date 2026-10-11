"""New readable host facts and contradictory years in actual expanded cards."""
import json,os
from pathlib import Path
import pytest
from playwright.sync_api import expect
from .test_tku_acceptance import start

@pytest.mark.parametrize('width',[390,1280])
def test_readable_host_references_render_actual_years_and_conflicts(page,live_server,width):
 _,errors=start(page,live_server,width,'partners');out=Path(os.environ.get('TKU_MILESTONE5_UI_EVIDENCE','/tmp/tku-milestone5-ui-evidence'));out.mkdir(parents=True,exist_ok=True);results=[]
 for query,expected in [('泗水理工','2026/10/15'),('芝浦工業','本科不得選研究所'),('檀國','November15,2025')]:
  page.locator('#partner-search').fill(query);expect(page.locator('#partner-table')).to_have_attribute('data-result-count','1')
  if width<768:page.locator('#partner-table .partner-card > summary').first.click()
  page.locator('#partner-table .school-detail-trigger:visible').first.click();content=page.locator('#school-detail-content')
  page.locator('.tku-source-details > summary').click();expect(content).to_contain_text(expected,timeout=30000);expect(content).to_contain_text('未核實')
  expect(page.locator('#school-detail-primary-facts')).to_contain_text('本期名額未核實')
  assert '中正校內資格' not in content.inner_text()
  page.locator('#detail-tab-life').click();page.locator('.life-official-guide > summary').click()
  expect(page.locator('#destination-official-content')).to_contain_text(expected)
  card=page.locator('.student-guide-section-card').filter(has_text=expected).first;card.scroll_into_view_if_needed();expect(card).to_be_visible();expect(card).to_contain_text('適用：')
  name=page.evaluate('state.activeSchool');r=page.evaluate('(name)=>state.dashboard.partner_universities.find(r=>r.school_name===name)',name)
  assert r['quota'] is None and r['availability_status'] in ['agreement_only','reference_only']
  results.append(dict(school_name=name,expected_visible=expected,quota=r['quota'],availability_status=r['availability_status'],official_sources=page.locator('.tku-source-details a').evaluate_all('(links)=>links.map(a=>a.href)')))
  page.screenshot(path=str(out/f'readable-host-{query}-{width}.png'));page.evaluate("location.hash='#partners'");expect(page.locator('#partner-search')).to_be_visible()
 assert not errors,errors
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 (out/f'readable-host-{width}.json').write_text(json.dumps(dict(status='passed',width=width,schools=results,page_errors=errors),ensure_ascii=False,indent=2)+'\n')
