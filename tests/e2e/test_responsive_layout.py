"""In a real browser at phone and tablet sizes: the page does not scroll sideways, nothing is squeezed to a sliver, and
fields are big enough that a phone does not zoom in when one is tapped."""
import pytest

PHONES_AND_TABLETS = [(320, 640), (375, 812), (414, 896), (768, 1024), (812, 375)]
ROUTES = ["#home", "#forum", "#partners", "#advisor", "#overview", "#application-center", "#favorites", "#calendar", "#budget", "#eligibility"]

AUDIT = """
async (routes) => {
  const vw = innerWidth, problems = [];
  const name = (el) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\\s+/)[0] : '');
  for (const route of routes) {
    location.hash = route; await new Promise((done) => setTimeout(done, 700));
    if (document.documentElement.scrollWidth > vw) problems.push(`${route}: the page scrolls sideways (${document.documentElement.scrollWidth} > ${vw})`);
    for (const el of document.body.querySelectorAll('*')) {
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.display === 'inline' || style.visibility === 'hidden' || el.closest('[hidden]')) continue;
      const own = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join('');
      if (!own || !el.clientWidth) continue;
      if (own.length >= 8 && el.getBoundingClientRect().width < 64) problems.push(`${route}: ${name(el)} is ${Math.round(el.getBoundingClientRect().width)}px wide for "${own.slice(0, 12)}"`);
      if (el.scrollWidth - el.clientWidth > 3 && style.overflowX === 'visible' && !['INPUT', 'SELECT'].includes(el.tagName)) problems.push(`${route}: ${name(el)} spills out of its box ("${own.slice(0, 12)}")`);
    }
  }
  return [...new Set(problems)];
}
"""

SMALL_FIELDS = """
() => [...document.querySelectorAll('input:not([type=checkbox]):not([type=radio]):not([type=hidden]):not([type=file]):not([type=range]), select, textarea')]
  .filter((el) => parseFloat(getComputedStyle(el).fontSize) < 16).map((el) => (el.id || el.name || el.type) + ' ' + getComputedStyle(el).fontSize)
"""


@pytest.mark.parametrize("width,height", PHONES_AND_TABLETS)
def test_no_page_breaks_at_phone_and_tablet_sizes(browser, live_server, width, height):
    context = browser.new_context(viewport={"width": width, "height": height}, has_touch=True)
    page = context.new_page()
    try:
        page.goto(f"{live_server.base_url}/?home=%E9%95%B7%E5%BA%9A%E5%A4%A7%E5%AD%B8#home")
        page.wait_for_load_state("networkidle", timeout=60_000)
        problems = page.evaluate(AUDIT, ROUTES)
        assert problems == [], "\n".join(problems)
    finally:
        context.close()


@pytest.mark.parametrize("width,height", [(375, 812), (768, 1024)])
def test_every_field_is_at_least_16px_so_phones_do_not_zoom_in(browser, live_server, width, height):
    context = browser.new_context(viewport={"width": width, "height": height}, has_touch=True)
    page = context.new_page()
    try:
        page.goto(f"{live_server.base_url}/?home=%E9%95%B7%E5%BA%9A%E5%A4%A7%E5%AD%B8#budget")
        page.wait_for_load_state("networkidle", timeout=60_000)
        assert page.evaluate(SMALL_FIELDS) == []
    finally:
        context.close()


def test_the_compose_button_shows_its_words_on_a_tablet(page, live_server):
    page.set_viewport_size({"width": 768, "height": 1024})
    page.goto(f"{live_server.base_url}/#forum")
    page.wait_for_load_state("networkidle", timeout=60_000)
    button = page.locator("#global-community-compose")
    button.wait_for(state="visible")
    assert button.evaluate("el => el.scrollWidth - el.clientWidth") <= 3
    assert button.bounding_box()["width"] > 100
