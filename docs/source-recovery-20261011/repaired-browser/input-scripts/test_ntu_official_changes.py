"""Today's reference text remains visibly scoped in both responsive views."""
import os
from pathlib import Path
import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until


@pytest.mark.parametrize('width',[390,1440])
def test_current_portal_reference_is_visible_without_opening_quota(page,live_server,width):
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    enter_public_site(page,live_server,'partners')
    open_navigation(page)
    page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立臺灣大學"]').click()
    page.locator('#confirm-school').click()
    if width<700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':
        page.locator('#glass-menu-toggle').click()
    wait_until(page,"state.dashboard?.school_name === '國立臺灣大學'")
    page.evaluate("location.hash='#partners'")
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill('明斯特大學')
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    if width<700:
        page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#school-detail-view')).to_be_visible()
    expect(page.locator('#school-detail-view .partner-student-summary')).to_contain_text('TOEFL iBT 4.0')
    expect(page.locator('#school-detail-view .partner-student-summary')).to_contain_text('TOEFL iBT 80')
    expect(page.locator('#school-detail-view .partner-student-summary')).to_contain_text('2026-10-10查核')
    expect(page.locator('#school-detail-view .partner-student-summary')).to_contain_text('最終條件與甄選名額仍待確認')
    assert page.evaluate("state.dashboard.partner_universities.find(p=>p.school_name==='明斯特大學').quota") is None
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    target = Path(os.environ.get('VISUAL_EVIDENCE_DIR', 'output/ntu-official-changes'))
    target.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(target/f'current-reference-{width}.png'))
