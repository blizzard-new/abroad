"""The search dropdown stays readable, the globe speaks Chinese, 我的申請 uses side-by-side boxes, the home is one night,
and every school's mark has its own colour."""
import re
from urllib.parse import urlencode

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site
from .test_glass_theme import verified_login
from .test_partner_globe import INSTRUMENT, ready


def luminance_and_alpha(css: str):
    nums = [float(n) for n in re.findall(r"[\d.]+", css)]
    r, g, b = nums[:3]
    return (0.2126 * r + 0.7152 * g + 0.0722 * b), (nums[3] if len(nums) > 3 else 1.0)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_the_highlighted_dropdown_row_never_hides_its_own_text(page, live_server, theme):
    page.set_viewport_size({"width": 1440, "height": 900})
    page.add_init_script(f"localStorage.setItem('exchange-guide-theme', '{theme}')")
    page.goto(f"{live_server.base_url}/?view=list#partners")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=90000)
    page.get_by_role("combobox", name="語言檢定").first.click()
    option = page.locator(".glide-select__menu:popover-open .glide-select__option").nth(2)
    option.hover()
    page.wait_for_timeout(500)
    text, _ = luminance_and_alpha(option.evaluate("el => getComputedStyle(el).color"))
    pill_bg, pill_alpha = luminance_and_alpha(page.locator(".glide-select__menu:popover-open .glide-select__pill").evaluate(
        "el => getComputedStyle(el).backgroundColor"))
    menu_bg, _ = luminance_and_alpha(page.locator(".glide-select__menu:popover-open").evaluate("el => getComputedStyle(el).backgroundColor"))
    # The highlight is a see-through tint over the menu, so the text keeps the contrast it has against the menu itself.
    assert pill_alpha <= 0.3, pill_alpha
    assert abs(text - menu_bg) > 120, (text, menu_bg)
    expect(option).to_be_visible()


def test_the_globe_names_countries_in_chinese(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.add_init_script(INSTRUMENT)
    page.goto(f"{live_server.base_url}/#partners")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=90000)
    ready(page)
    names = page.evaluate("window.__testedMap.getSource('labels').serialize().data.features.map((f) => f.properties.name)")
    assert {"日本", "法國", "臺灣", "美國", "紐西蘭"} <= set(names), names[:12]
    # Natural Earth's names are replaced, not shown beside the Chinese ones.
    assert "Japan" not in names and "France" not in names
    assert page.evaluate("window.__testedMap.getStyle().layers.find((l) => l.id === 'country-labels').layout['text-field'][1]") == "name"


def test_my_application_today_lays_its_boxes_side_by_side_and_says_less(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 900})
    verified_login(page, live_server)
    created = page.request.post(f"{live_server.base_url}/account/application-paths", data={
        "home_school": "長庚大學", "target_school": "林肯大學 Lincoln University", "academic_year": "116",
        "departure_year": "2027", "semester": "fall", "revision": 0}).json()
    page.goto(f"{live_server.base_url}/#my-application?" + urlencode({"plan": created["plan"]["id"], "view": "today"}))
    today = page.locator("#today-view .today")
    expect(today).to_be_visible(timeout=30000)
    cards = today.locator(".today-queue li")
    assert cards.count() >= 2
    first, second = cards.nth(0).bounding_box(), cards.nth(1).bounding_box()
    assert abs(first["y"] - second["y"]) < 4, "the next tasks sit in one row"
    assert first["width"] < 420, first
    # The focus card and the deadline card share a row; the todo form is one row.
    focus, deadline = today.locator(".today-focus").bounding_box(), today.locator(".today-top .today-panel").bounding_box()
    assert abs(focus["y"] - deadline["y"]) < 4
    title, date = today.locator("[data-today-quick] input[name=title]").bounding_box(), today.locator("[data-today-quick] input[type=date]").bounding_box()
    assert abs(title["y"] - date["y"]) < 6
    for gone in ("UniWay 只倒數有官方來源", "還沒有。記下", "下一項可開始的準備", "依已查核的規則比對", "個人準備進度"):
        expect(today).not_to_contain_text(gone)
    # The boundary the product must always state is still there, and "synced" no longer takes a line.
    expect(today.locator(".today-boundary")).to_contain_text("不代表校方受理或錄取")
    expect(page.locator("#sync-message")).to_be_hidden()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_the_home_is_one_night_that_the_earth_rises_out_of(page, live_server, theme):
    page.set_viewport_size({"width": 1440, "height": 900})
    page.add_init_script(f"localStorage.setItem('exchange-guide-theme', '{theme}')")
    enter_public_site(page, live_server, "home")
    page.wait_for_timeout(800)
    assert page.evaluate("getComputedStyle(document.documentElement).backgroundColor") == "rgb(11, 18, 32)"
    assert page.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(11, 18, 32)"
    # No box around the sky: the band is transparent and the Earth fades out along its lower edge.
    assert page.locator(".mt-sky").evaluate("el => getComputedStyle(el).backgroundColor") == "rgba(0, 0, 0, 0)"
    assert "linear-gradient" in page.locator(".mt-earth").evaluate("el => getComputedStyle(el).maskImage || getComputedStyle(el).webkitMaskImage")
    # Text on it is light, not dark on dark.
    ink, _ = luminance_and_alpha(page.locator("#mt-route-title").evaluate("el => getComputedStyle(el).color"))
    assert ink > 200


def test_every_school_mark_has_its_own_colour(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 900})
    enter_public_site(page, live_server, "home")
    page.locator("#mt-board-school").click()
    options = page.locator(".school-option")
    expect(options.first).to_be_visible()
    tints = page.evaluate("[...document.querySelectorAll('.school-option')].slice(0, 14).map((el) => el.style.getPropertyValue('--school-tint'))")
    assert len(tints) >= 12
    assert len(set(tints)) >= 10, tints
    # Neighbours are never the same colour.
    assert all(a != b for a, b in zip(tints, tints[1:])), tints
    # And the names beside them are readable on the night dialog.
    name = page.locator(".school-option-name").nth(3)
    colour, _ = luminance_and_alpha(name.evaluate("el => getComputedStyle(el).color"))
    assert colour > 180
