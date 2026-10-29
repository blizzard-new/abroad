"""The space explorer uses the real globe and stays usable across viewports."""
from pathlib import Path

import pytest
from playwright.sync_api import expect
from .test_partner_globe import INSTRUMENT, ready


@pytest.mark.parametrize('size', [(1440, 1000), (393, 852)])
def test_space_globe_drag_zoom_filters_and_route_cleanup(page, live_server, size):
    page.set_viewport_size({'width': size[0], 'height': size[1]})
    page.add_init_script(INSTRUMENT)
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(f'{live_server.base_url}/#partners')
    # The common splash has a 60-second fallback on a software renderer.
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=90000)
    ready(page)
    expect(page.locator('[data-partner-view="map"]')).to_have_attribute('aria-pressed', 'true')
    assert page.evaluate('window.__testedMap.getProjection().type') == 'globe'
    globe = page.locator('#partner-globe')
    globe.scroll_into_view_if_needed()
    page.wait_for_function('() => !window.__testedMap.isMoving()')
    bounds = globe.bounding_box()
    x, y = bounds['x'] + bounds['width'] * .5, bounds['y'] + bounds['height'] * .5
    before = page.evaluate('window.__testedMap.getCenter().toArray()')
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 90, y + 25, steps=12)
    page.mouse.up()
    page.wait_for_function('() => !window.__testedMap.isMoving()')
    assert page.evaluate('window.__testedMap.getCenter().toArray()') != before
    zoom = page.evaluate('window.__testedMap.getZoom()')
    page.mouse.wheel(0, -300)
    page.wait_for_function('zoom => window.__testedMap.getZoom() > zoom + .1', arg=zoom)
    page.locator('#map-global').click()
    page.wait_for_function('() => !window.__testedMap.isMoving()')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    output = Path('/tmp/partner-space')
    output.mkdir(exist_ok=True)
    page.evaluate('scrollTo(0, 0)')
    page.screenshot(path=str(output / f'globe-{size[0]}.png'), full_page=True)
    # The whole route has a space background and no enclosing map surface.
    assert page.locator('#partner-map-panel').evaluate('el => getComputedStyle(el).borderTopWidth') == '0px'
    assert page.locator('#partner-map-panel').evaluate('el => getComputedStyle(el).backgroundColor') == 'rgba(0, 0, 0, 0)'
    assert page.locator('body').evaluate('el => getComputedStyle(el, "::before").backgroundColor') == 'rgb(6, 12, 27)'
    page.locator('.pr-facets > summary').click()
    # Native selects are enhanced; use the visible country combobox.
    country = page.get_by_role('combobox', name='國家', exact=True)
    country.scroll_into_view_if_needed()
    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    country.click()
    page.get_by_role('option', name='紐西蘭', exact=False).click()
    ready(page)
    expect(page.locator('#partner-map-count')).to_contain_text('1 所已定位')
    school = page.get_by_role('combobox', name='定位學校', exact=True)
    school.scroll_into_view_if_needed()
    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    school.click()
    page.get_by_role('option', name='林肯大學 Lincoln University', exact=False).click()
    expect(page.locator('#partner-map-preview')).to_be_visible()
    expect(page.locator('#partner-map-preview h4')).to_have_text('林肯大學 Lincoln University')
    page.locator('[data-close-map-preview]').click()
    page.locator('[data-partner-view="list"]').click()
    expect(page.locator('#partner-table')).to_be_visible()
    expect(page.locator('#country-filter')).to_have_value('紐西蘭')
    page.locator('[data-partner-view="map"]').click()
    ready(page)
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    assert page.locator('body').evaluate('el => getComputedStyle(el, "::before").backgroundColor') == 'rgb(6, 12, 27)'
    page.evaluate("location.hash = '#home'")
    expect(page.locator('#partners')).to_be_hidden()
    assert page.locator('body').evaluate('el => getComputedStyle(el, "::before").backgroundColor') != 'rgb(6, 12, 27)'
    assert not errors
