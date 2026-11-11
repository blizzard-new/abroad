"""The search dropdown stays readable, the globe speaks Chinese, 我的申請 uses side-by-side boxes, the navigation is a top
bar on every page, and on the metro pages every school's mark has its own colour."""
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


def test_every_school_mark_has_its_own_colour_on_the_metro_pages(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 900})
    enter_public_site(page, live_server, "partners")
    page.locator("#school-switcher").click()
    options = page.locator(".school-option")
    expect(options.first).to_be_visible()
    tints = page.evaluate("[...document.querySelectorAll('.school-option')].slice(0, 14).map((el) => el.style.getPropertyValue('--school-tint'))")
    assert len(tints) >= 12
    assert len(set(tints)) >= 10, tints
    # Neighbours are never the same colour.
    assert all(a != b for a, b in zip(tints, tints[1:])), tints


def test_the_fonts_are_poppins_for_latin_and_genjyuu_for_chinese(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 900})
    enter_public_site(page, live_server, "partners")
    page.wait_for_timeout(1500)
    stack = page.evaluate("getComputedStyle(document.body).fontFamily")
    assert stack.startswith('Poppins, GenJyuuGothic'), stack
    # The faces really load (not only named): Latin from Poppins, a Chinese sentence from 源柔黑體.
    page.evaluate("Promise.all([document.fonts.load('700 20px Poppins', 'UniWay 116'), document.fonts.load('700 20px GenJyuuGothic', '找交換學校')])")
    assert page.evaluate("document.fonts.check('700 20px Poppins', 'UniWay 116')")
    assert page.evaluate("document.fonts.check('700 20px GenJyuuGothic', '找交換學校')")
    for selector in ("#partners h1", ".pr-search-button", "#theme-toggle"):
        assert page.locator(selector).first.evaluate("el => getComputedStyle(el).fontFamily").startswith("Poppins"), selector


@pytest.mark.parametrize("route", ["home", "partners", "forum"])
def test_the_navigation_is_a_top_bar_on_classic_and_metro_pages_alike(page, live_server, route):
    page.set_viewport_size({"width": 1440, "height": 900})
    enter_public_site(page, live_server, route)
    bar = page.locator("#glass-navigation").bounding_box()
    assert bar["x"] == 0 and bar["y"] == 0 and bar["width"] >= 1439 and bar["height"] <= 76
    links = [page.locator(f'#glass-navigation a[data-public-route="{name}"]').bounding_box() for name in ("home", "partners", "forum")]
    assert len({round(box["y"]) for box in links}) == 1 and links[0]["x"] < links[1]["x"] < links[2]["x"]


@pytest.mark.parametrize("width", [901, 1024])
def test_the_top_bar_fits_the_narrowest_desktop_widths(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 800})
    enter_public_site(page, live_server, "home")
    page.wait_for_timeout(800)
    right = page.evaluate("Math.max(...[...document.querySelectorAll('#glass-navigation a[data-public-route], #glass-navigation #theme-toggle, #glass-navigation #account-button')].map((el) => el.getBoundingClientRect().right))")
    assert right <= width, right
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    # Without their labels the links still have names for assistive technology.
    expect(page.locator('#glass-navigation').get_by_role("link", name="論壇", exact=True)).to_have_count(1)


@pytest.mark.parametrize("route", ["home", "partners", "forum", "guide", "feedback"])
def test_the_logo_stays_in_view_while_the_app_scrolls(page, live_server, route):
    for width, selector in ((1440, ".uniway-header-brand"), (393, ".glass-mobile-header a[href='#home']")):
        page.set_viewport_size({"width": width, "height": 800})
        enter_public_site(page, live_server, route)
        page.wait_for_timeout(600)
        page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        page.wait_for_timeout(300)
        box = page.locator(selector).first.bounding_box()
        assert box and 0 <= box["y"] and box["y"] + box["height"] <= 80, (route, width, box)
        expect(page.locator(selector).first).to_be_visible()


@pytest.mark.parametrize("width", [901, 1024, 1440])
def test_the_wordmark_is_always_beside_the_logo_not_only_on_hover(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 800})
    enter_public_site(page, live_server, "home")
    page.mouse.move(width / 2, 600)
    page.wait_for_timeout(600)
    word = page.locator("#glass-navigation .uniway-header-brand strong")
    expect(word).to_be_visible()
    expect(word).to_have_text("UniWay")
    assert word.bounding_box()["width"] > 60
    assert page.locator("#glass-navigation .uniway-header-brand").bounding_box()["width"] > 100
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("size", [(1360, 800), (1100, 800), (1440, 900)])
def test_the_globe_window_is_tall_and_every_button_in_it_is_shown_in_full(page, live_server, size):
    page.set_viewport_size({"width": size[0], "height": size[1]})
    page.add_init_script(INSTRUMENT)
    page.goto(f"{live_server.base_url}/?view=map#partners")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=90000)
    ready(page)
    stage = page.locator(".partner-map-stage").bounding_box()
    assert stage["height"] >= 680, stage
    chips = page.locator(".partner-map-actions button:visible")
    assert chips.count() >= 3
    for index in range(chips.count()):
        box = chips.nth(index).bounding_box()
        # inside the window with room to spare, so no edge clips a border
        assert box["x"] + box["width"] <= stage["x"] + stage["width"] - 12, (index, box, stage)
        assert box["y"] >= stage["y"] and box["y"] + box["height"] <= stage["y"] + stage["height"], (index, box, stage)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    # The globe is sized to fill the window: at least as large as the height of the window it is in.
    expected = page.evaluate("(h) => Math.log2(h * Math.PI / 512)", min(stage["height"], stage["width"] - 260))
    assert page.evaluate("window.__testedMap.getZoom()") >= expected - 0.02


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_search_controls_are_readable_and_the_primary_action_is_clear(page, live_server, theme):
    page.set_viewport_size({"width": 1360, "height": 800})
    page.add_init_script(f"localStorage.setItem('exchange-guide-theme', '{theme}')")
    page.goto(f"{live_server.base_url}/?view=map#partners")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=90000)
    page.wait_for_timeout(800)
    style = "(sel) => { const cs = getComputedStyle(document.querySelector(sel)); return [cs.borderTopWidth, parseFloat(cs.borderTopLeftRadius), cs.backgroundColor]; }"
    for selector in ("#map-global", "#map-home", ".discovery-open-workspace", ".discovery-criteria", ".pr-view-toggle"):
        width, radius, background = page.evaluate(style, selector)
        assert width == "0px" and radius >= 20 and background != "rgba(0, 0, 0, 0)", (selector, width, radius, background)
    for selector in (".pr-search", ".pr-search-button"):
        _, radius, _ = page.evaluate(style, selector)
        assert radius == 12, (selector, radius)
    # The unified fields retain readable text in both themes.
    ink, _ = luminance_and_alpha(page.locator("#partner-search").evaluate("el => getComputedStyle(el).color"))
    bubble, _ = luminance_and_alpha(page.locator(".pr-search .pr-field").first.evaluate("el => getComputedStyle(el).backgroundColor"))
    assert abs(ink - bubble) > 120, (ink, bubble)
