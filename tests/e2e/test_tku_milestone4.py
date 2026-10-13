"""Actual rendered host references retain programme/year differences."""
import json
import os
from pathlib import Path
import pytest
from playwright.sync_api import expect
from .test_tku_acceptance import start


@pytest.mark.parametrize('width',[390,1280])
def test_new_host_references_render_with_year_and_unverified_home_scope(page,live_server,width):
    _,errors=start(page,live_server,width,'partners')
    results=[]
    out=Path(os.environ.get('TKU_MILESTONE4_UI_EVIDENCE','/tmp/tku-milestone4-ui-evidence'));out.mkdir(parents=True,exist_ok=True)
    for query,expected in [('巴拿馬科技','2027/1/14'),('波昂','未列淡江'),('里昂第三','來源矛盾'),('貴州','不是2027')]:
        page.locator('#partner-search').fill(query)
        expect(page.locator('#partner-table')).to_have_attribute('data-result-count','1')
        if width<768:page.locator('#partner-table .partner-card > summary').first.click()
        page.locator('#partner-table .school-detail-trigger:visible').first.click()
        content=page.locator('#school-detail-content')
        page.locator('.tku-source-details > summary').click()
        expect(content).to_contain_text(expected,timeout=30000)
        expect(content).to_contain_text('未核實')
        expect(page.locator('#school-detail-primary-facts')).to_contain_text('本期名額未核實')
        assert '中正校內資格' not in content.inner_text()
        expect(page.locator('.tku-source-details')).to_contain_text('來源學年度已確認仍不代表淡江本期適用')
        page.locator('#detail-tab-life').click()
        page.locator('.life-official-guide > summary').click()
        expect(page.locator('#destination-official-content')).to_contain_text(expected)
        card=page.locator('.student-guide-section-card').filter(has_text=expected).first
        card.scroll_into_view_if_needed()
        expect(card).to_be_visible()
        expect(card).to_contain_text('適用：')
        name=page.evaluate('state.activeSchool')
        row=page.evaluate('(name)=>state.dashboard.partner_universities.find(r=>r.school_name===name)',name)
        assert row['quota'] is None and row['availability_status'] in ['reference_only','agreement_only']
        results.append(dict(school_name=name,expected_visible=expected,quota=row['quota'],availability_status=row['availability_status'],
            rendered_field_count=page.locator('[data-tku-field]').count(),official_sources=page.locator('.tku-source-details a').evaluate_all('(links)=>links.map(link=>link.href)')))
        page.screenshot(path=str(out/f'host-reference-{query}-{width}.png'))
        page.evaluate("location.hash='#partners'")
        expect(page.locator('#partner-search')).to_be_visible()
    assert not errors,errors
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(out/f'host-reference-render-{width}.png'))
    (out/f'host-reference-render-{width}.json').write_text(json.dumps(dict(width=width,status='passed',page_errors=errors,schools=results),ensure_ascii=False,indent=2)+'\n')
