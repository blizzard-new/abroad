"""Resume checkpoint: real credited photos and source-scoped points reach Chromium."""
from pathlib import Path
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until

OUTPUT = Path('docs/data/ncu-completion-20261011/resume/second/browser')


def select_ncu(page, live_server):
    enter_public_site(page, live_server, 'partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page)
    page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator('#confirm-school').click()
    wait_until(page, "state.dashboard?.school_name === '國立中央大學'", timeout=60)
    if page.locator('#glass-menu-toggle').get_attribute('aria-expanded') == 'true':
        page.locator('#glass-menu-toggle').click()


@pytest.mark.parametrize('query,width,author', [
    ('克萊蒙', 390, 'Benoît Prieur'), ('拉薩爾博舍', 1280, 'LaDivia'),
    ('加州大學爾灣', 390, 'Mikejuinwind123'), ('關西國際', 1280, 'Kirakirameister'),
    ('夏威夷大學馬諾阿分校（自費）', 390, 'Historyrus82'), ('上海財經', 1280, 'MomodaniSakura'),
    ('穆罕默迪亞', 390, 'Mhdfardhan'),
])
def test_resume_photo_bytes_and_actual_attribution_visible(page, live_server, query, width, author):
    errors=[]
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server)
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    picture=page.locator('#partner-table .school-photo img').first
    expect(picture).to_have_attribute('src',re.compile(r'/static/assets/ncu-schools/[a-f0-9]+\.(?:jpg|png)$'))
    wait_until(page,"document.querySelector('#partner-table .school-photo img')?.naturalWidth > 0",timeout=30)
    summary=page.locator('#partner-table .partner-card > summary').first
    if summary.is_visible():summary.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    caption=page.locator('.student-guide-photo-grid figcaption').first
    expect(caption).to_contain_text(author)
    expect(caption).to_contain_text('授權：')
    expect(caption).to_contain_text('116錄取校區仍待確認')
    expect(page.locator('.student-guide-photo-grid figure')).to_have_count(1)
    wait_until(page,"document.querySelector('.student-guide-photo-grid img')?.naturalWidth > 0",timeout=30)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    page.locator('.student-guide-photo-grid figure').first.screenshot(path=str(OUTPUT/f'{query}-{width}-photo.png'))
    page.screenshot(path=str(OUTPUT/f'{query}-{width}-life.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors


def test_resume_mother_marker_and_all_partner_points_reach_real_globe(page,live_server):
    page.set_viewport_size({'width':1280,'height':956})
    page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server)
    page.locator('[data-partner-view="map"]').click()
    expect(page.locator('#partner-map-count')).to_have_text('176 所已定位 / 214 所符合條件',timeout=60_000)
    expect(page.locator('#map-school-select option')).to_have_count(177)
    expect(page.locator('#map-home')).to_be_enabled()
    expect(page.locator('.map-home-marker')).to_contain_text('中央',timeout=60_000)
    page.locator('#map-home').click()
    OUTPUT.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(OUTPUT/'ncu-mother-and-176-points.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
