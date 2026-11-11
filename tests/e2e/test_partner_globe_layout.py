"""Shared search layout: usable map controls, space and both colour themes."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .test_partner_globe import open_partners, ready


@pytest.mark.parametrize("width,height", [(1440, 1000), (1024, 768), (393, 852), (320, 740)])
def test_full_width_globe_and_horizontal_controls(page, live_server, width, height):
    page.set_viewport_size({"width": width, "height": height})
    page.emulate_media(reduced_motion="reduce")
    open_partners(page, live_server)
    ready(page)
    stage = page.locator('.partner-map-stage').bounding_box()
    globe = page.locator('#partner-globe').bounding_box()
    assert abs(globe['x'] - stage['x']) < 1
    assert abs(globe['width'] - stage['width']) < 1
    expect(page.locator('#partner-map-list')).to_have_count(0)
    controls = page.locator('.maplibregl-ctrl-group button')
    boxes = [button.bounding_box() for button in controls.all()]
    assert len(boxes) == 3
    assert max(b['y'] for b in boxes) - min(b['y'] for b in boxes) < 1
    assert all(b['width'] >= 44 and b['height'] >= 44 for b in boxes)
    assert boxes[0]['x'] + boxes[0]['width'] <= boxes[1]['x'] + 1
    if width > 900:
        assert page.locator('.pr-search').bounding_box()['height'] < 80
        assert globe['width'] >= width - 65
        actions = page.locator('.partner-map-actions > div').bounding_box()
        assert actions['x'] + actions['width'] < boxes[0]['x']
    # Keyboard activation of real MapLibre controls still changes the camera.
    zoom = page.evaluate('window.__testedMap.getZoom()')
    controls.first.scroll_into_view_if_needed()
    controls.first.focus()
    expect(controls.first).to_be_focused()
    page.keyboard.press('Enter')
    page.wait_for_function('(zoom) => window.__testedMap.getZoom() > zoom', arg=zoom)
    page.wait_for_function('() => !window.__testedMap.isMoving()')
    zoom = page.evaluate('window.__testedMap.getZoom()')
    controls.nth(1).click()
    page.wait_for_function('(zoom) => window.__testedMap.getZoom() < zoom', arg=zoom)
    page.locator('#map-global').click()
    page.wait_for_function('() => !window.__testedMap.isMoving()')
    # Expanded filters must not cover the toolbar or widen the document.
    drawer = page.locator('.pr-facets')
    drawer.locator('summary').first.click()
    expect(drawer).to_have_attribute('open', '')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    if width > 900:
        criteria = page.locator('.discovery-criteria')
        criteria.locator('summary').click()
        expect(page.locator('#discovery-criteria-form')).to_be_visible()
        form = page.locator('#discovery-criteria-form').bounding_box()
        assert form['y'] >= drawer.bounding_box()['y'] + drawer.bounding_box()['height']
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        criteria.locator('summary').click()
    drawer.locator('summary').first.click()
    page.locator('#partner-globe').scroll_into_view_if_needed()
    out = Path('output/partner-globe-layout')
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / f'app-{width}-light.png'))
    light = page.evaluate("window.__testedMap.getPaintProperty('ocean', 'background-color')")
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    page.wait_for_function("(light) => window.__testedMap.getPaintProperty('ocean', 'background-color') !== light", arg=light)
    page.screenshot(path=str(out / f'app-{width}-dark.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
