"""The school card fits the globe without a scroll, and the search globe is a pastel toy on the page's own white."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site
from .test_partner_globe import INSTRUMENT, ready

SHOTS = Path('/tmp/globe-card-hero')


@pytest.mark.parametrize('size', [(1440, 900), (1024, 700), (393, 852)])
def test_the_school_card_shows_its_figures_and_never_needs_a_scroll(page, live_server, size):
    page.set_viewport_size({'width': size[0], 'height': size[1]})
    page.add_init_script(INSTRUMENT)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(f'{live_server.base_url}/#partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=90000)
    ready(page)
    page.locator('#map-school-select').select_option(index=2)
    card = page.locator('#partner-map-preview')
    expect(card).to_be_visible()
    page.wait_for_function('() => !window.__testedMap.isMoving()')
    # The figures that decide whether to look further are on the card, and the rest is one button away.
    expect(card.locator('.map-facts dt').first).to_be_visible()
    expect(card).to_contain_text('交換名額')
    expect(card.locator('.school-detail-trigger')).to_have_text('查看完整資料 ↗')
    expect(card.locator('.school-detail-trigger')).to_be_visible()
    # Nothing is cut off and nothing scrolls inside the card.
    metrics = card.evaluate('el => [el.scrollHeight, el.clientHeight]')
    assert metrics[0] <= metrics[1] + 1, metrics
    stage, box = page.locator('.partner-map-stage').bounding_box(), card.bounding_box()
    assert box['y'] >= stage['y'] - 1 and box['y'] + box['height'] <= stage['y'] + stage['height'] + 1, (box, stage)
    assert box['x'] >= stage['x'] - 1 and box['x'] + box['width'] <= stage['x'] + stage['width'] + 1, (box, stage)
    assert box['height'] <= 480, box
    # The pin the card is about stays in view above or beside it.
    pin = page.evaluate('() => { const m = window.__testedMap; const c = m.getCenter(); const p = m.project(c); return [p.x, p.y, m.getCanvas().clientWidth, m.getCanvas().clientHeight]; }')
    assert 0 <= pin[0] <= pin[2] and 0 <= pin[1] <= pin[3], pin
    SHOTS.mkdir(exist_ok=True)
    page.screenshot(path=str(SHOTS / f'card-{size[0]}.png'))
    assert not errors


def test_the_search_globe_is_a_pastel_toy_with_coral_markers_on_the_pages_own_white(page, live_server):
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.add_init_script(INSTRUMENT)
    page.goto(f'{live_server.base_url}/#partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=90000)
    ready(page)
    assert page.evaluate('window.__testedMap.getProjection().type') == 'globe'
    # Not a photograph: no raster Earth, flat tinted countries on a light-blue sea, and no glow around the planet.
    assert page.evaluate("window.__testedMap.getLayer('earth') === undefined && window.__testedMap.getSource('earth') === undefined")
    fill = page.evaluate("window.__testedMap.getPaintProperty('land', 'fill-color')")
    assert fill[0] == 'match' and len({value for value in fill if isinstance(value, str) and value.startswith('#')}) >= 6, fill
    assert page.evaluate("window.__testedMap.getPaintProperty('ocean', 'background-color')") == '#bfe4ff'
    assert page.evaluate("window.__testedMap.getStyle().sky['atmosphere-blend']") == 0
    # The markers are coral with a white ring, so they read on every tint.
    assert page.evaluate("window.__testedMap.getPaintProperty('school-points', 'circle-color')") == '#ff6f91'
    assert page.evaluate("window.__testedMap.getPaintProperty('school-points', 'circle-stroke-color')") == '#ffffff'
    # Its window has no colour of its own: the stage is the same white as the page around it.
    stage = page.locator('.partner-map-stage').evaluate("el => [getComputedStyle(el).backgroundColor, getComputedStyle(el).backgroundImage]")
    assert stage == ['rgb(255, 255, 255)', 'none'], stage
    assert page.evaluate("getComputedStyle(document.body).backgroundColor") == 'rgb(255, 255, 255)'
    # Night repaints the same toy in deeper colours.
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    page.wait_for_function("() => window.__testedMap.getPaintProperty('ocean', 'background-color') === '#2b3f73'")
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    # The photograph is gone from the app; the home's own strip of the Earth is still served.
    assert page.request.get(f'{live_server.base_url}/static/assets/partner-map/earth-mercator.jpg').status == 404
    response = page.request.get(f'{live_server.base_url}/static/assets/partner-map/earth-equirect.jpg')
    assert response.ok and response.headers['content-type'].startswith('image/jpeg')
