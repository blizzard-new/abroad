"""The school card fits the globe without a scroll, the globe is the real Earth, and the home says its one sentence in the middle."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site
from .test_partner_globe import INSTRUMENT, ready

SHOTS = Path('/tmp/globe-card-hero')
SLOGAN = '世界這麼大，別讓資訊限制你的選擇。'


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


def test_the_home_says_its_one_sentence_in_the_middle_over_the_earth(page, live_server):
    page.set_viewport_size({'width': 1440, 'height': 900})
    enter_public_site(page, live_server, 'home')
    title = page.locator('#home-landing-title')
    expect(title).to_contain_text(SLOGAN)
    sky = page.locator('.mt-sky')
    t, s = title.bounding_box(), sky.bounding_box()
    assert abs((t['x'] + t['width'] / 2) - (s['x'] + s['width'] / 2)) <= 2, (t, s)
    assert title.evaluate('el => getComputedStyle(el).textAlign') == 'center'
    assert float(title.evaluate('el => parseFloat(getComputedStyle(el).fontSize)')) >= 56
    # The search board sits under the sentence, the Earth under the board, all in the first screen.
    board, earth = page.locator('#mt-board').bounding_box(), page.locator('.mt-earth').bounding_box()
    assert t['y'] + t['height'] <= board['y'] and board['y'] + board['height'] <= earth['y'] + 1, (t, board, earth)
    assert earth['y'] < 900
    assert 'earth-equirect' in page.locator('.mt-earth-strip').evaluate('el => getComputedStyle(el).backgroundImage')
    # It opens over Asia and turns; with reduced motion it holds still.
    assert page.locator('.mt-earth-strip').evaluate('el => getComputedStyle(el).animationName') == 'mt-earth-spin'
    SHOTS.mkdir(exist_ok=True)
    page.screenshot(path=str(SHOTS / 'home-1440.png'))
    # The sentences that only restated a heading are gone.
    home = page.locator('#home-landing')
    for text in ('公開資料不登入就能看', '先讀懂，再開始規劃', '站的順序依合作校數量排列', '往下探索你的交換旅程', '追蹤即時情報'):
        expect(home).not_to_contain_text(text)
    # The official accounts are still on the home page.
    expect(page.locator('.mt-sky .pr-hero-socials a')).to_have_count(2)


@pytest.mark.parametrize('width', [320, 393, 768])
def test_the_home_sentence_never_leaves_a_lone_character_on_a_phone(page, live_server, width):
    page.set_viewport_size({'width': width, 'height': 852})
    enter_public_site(page, live_server, 'home')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    lines = page.locator('#home-landing-title span').evaluate(
        """el => { const r = document.createRange(); r.selectNodeContents(el); return [...r.getClientRects()].map(x => Math.round(x.top)); }""")
    # Two balanced lines at most for the second half of the sentence, and a line is never one stray character.
    widths = page.locator('#home-landing-title span').evaluate(
        """el => { const r = document.createRange(); r.selectNodeContents(el); return [...r.getClientRects()].map(x => Math.round(x.width)); }""")
    assert len(set(lines)) <= 2, lines
    assert min(widths) > 40, widths
