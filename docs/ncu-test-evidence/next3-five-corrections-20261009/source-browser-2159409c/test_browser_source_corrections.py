"""Supplemental read-only capture against fixed 2159409c, no runtime override."""
from pathlib import Path
import pytest
from playwright.sync_api import expect
from e2e.conftest import enter_public_site,open_navigation
from e2e.test_open_catalog import wait_until

OUT=Path('/workspace/ncu-verification-tmp/p1-five-2159409cacb6d8ac36bbafcc3ca6f2925f860fc9/browser-source');OUT.mkdir(exist_ok=True)

@pytest.mark.parametrize('slug,term,full',[('nufs','名古屋外國語','名古屋外國語大學 Nagoya University of Foreign Studies'),('kumamoto','熊本','熊本大學 Kumamoto University'),('ryukoku','龍谷','龍谷大學 Ryukoku University')])
def test_fixed_corrected_passages_and_original_source_ui(page,live_server,slug,term,full):
    page.set_viewport_size({'width':1440,'height':956});page.emulate_media(reduced_motion='reduce')
    enter_public_site(page,live_server,'partners');open_navigation(page)
    page.locator('#school-switcher').click();page.locator('[data-home-school="國立中央大學"]').click();page.locator('#confirm-school').click()
    wait_until(page,"state.dashboard?.school_name === '國立中央大學'",timeout=60)
    page.locator('[data-partner-view="list"]').click();page.locator('#partner-search').fill(term)
    page.locator(f'#partner-table .school-detail-trigger[data-school-name="{full}"]:visible').first.click()
    summary=page.locator('#detail-overview .partner-student-summary')
    for toggle in summary.locator('.partner-summary-more > summary').all():toggle.click()
    terms={'nufs':['不能修GJP課程'], 'kumamoto':['非英語母語者須交','非日本國籍學生','一次性付款'], 'ryukoku':['有則附','NASIC另寄','無日本可用帳戶']}[slug]
    for i,text in enumerate(terms):
        passage=summary.locator('li').filter(has_text=text).first;expect(passage).to_be_visible();assert text in passage.inner_text()
        passage.screenshot(path=str(OUT/f'{slug}-corrected-summary-{i+1}.png'))
    page.locator('#ncu-source-audit > summary').click();expect(page.locator('#ncu-source-audit-body > p').first).to_contain_text('2026-10-09',timeout=60_000)
    source_term={'nufs':'特別聴講プログラム','kumamoto':'ug-brochure','ryukoku':'application'}[slug]
    source=page.locator('#ncu-source-audit-body > details').filter(has=page.locator(':scope > summary').filter(has_text=source_term)).first
    source.locator(':scope > summary').click()
    if slug=='kumamoto':
        part=source.locator('.ncu-visual-passage').filter(has=page.locator(':scope > summary').filter(has_text='原PDF第8頁'))
        part.locator(':scope > summary').click();expect(part).to_contain_text('One-time payment');expect(part).to_contain_text('一括');part.screenshot(path=str(OUT/'kumamoto-original-p8-insurance.png'))
    else:
        source.locator('details > summary').first.click();original=source.locator('pre').first
        expect(original).to_contain_text('Study Abroad Program students cannot take classes in the Global Japan Program.' if slug=='nufs' else '[Official Transcript]')
        original.screenshot(path=str(OUT/f'{slug}-original-application-or-course-page.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
