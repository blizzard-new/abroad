"""The two final representative points and their actual photo campus reach Chromium."""
import json
from pathlib import Path
import os
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu
from .test_open_catalog import wait_until

OUT = Path(os.environ.get('NCU_RESUME_BROWSER_OUTPUT', '/tmp/ncu-final-browser'))


@pytest.mark.parametrize('width', [390, 1280])
def test_eleventh_named_campuses_and_licensed_photos(page, live_server, width):
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.set_viewport_size({'width': width, 'height': 1050})
    page.emulate_media(reduced_motion='reduce')
    select_ncu(page, live_server)
    rows = json.loads(Path('sources/ncu/2026-10-11/resume-eleventh-location-review.json').read_text())['coordinate_decisions']
    OUT.mkdir(parents=True, exist_ok=True)
    for row in rows:
        page.locator('[data-partner-view="map"]').click()
        expect(page.locator('#partner-map-count')).to_have_text('214 所已定位 / 214 所符合條件', timeout=60_000)
        expect(page.locator('#map-school-select option')).to_have_count(215)
        expect(page.locator('#partner-map-status')).to_be_hidden(timeout=60_000)
        page.locator('#map-school-select').select_option(value=row['school_name'])
        expect(page.locator('#partner-map-preview .map-preview-place')).to_contain_text(row['published_record']['city'])
        note = page.locator('#partner-map-preview .map-location-note')
        note.locator('summary').click()
        expect(note).to_contain_text('116')
        expect(note).to_contain_text('OpenStreetMap contributors' if row['capture_row_id'] == 'ncu-181' else '2025/4/11')
        note.screenshot(path=str(OUT / f"{row['capture_row_id']}-{width}-location.png"))
        page.locator('[data-partner-view="list"]').click()
        page.locator('#partner-search').fill(row['school_name'])
        summary = page.locator('#partner-table .partner-card > summary').first
        if summary.is_visible():
            summary.click()
        page.locator('#partner-table .school-detail-trigger:visible').first.click()
        page.locator('#detail-tab-life').click()
        page.locator('#detail-life .life-official-guide > summary').click()
        figure = page.locator('.student-guide-photo-grid figure').first
        expect(figure).to_contain_text('Devymex' if row['capture_row_id'] == 'ncu-181' else 'GRANDMONT')
        expect(figure).to_contain_text('授權：')
        expect(figure).to_contain_text('116錄取校區仍待確認')
        wait_until(page, "document.querySelector('.student-guide-photo-grid img')?.naturalWidth > 0", timeout=30)
        figure.screenshot(path=str(OUT / f"{row['capture_row_id']}-{width}-photo.png"))
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.go_back()
        page.locator('#partner-search').fill('')
    assert not errors
