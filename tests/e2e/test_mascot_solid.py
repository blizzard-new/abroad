"""The mascot is a solid with thickness that turns towards the pointer, and it stands in the home page header."""
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site

HERO = ".pr-collage-mascot"


def start(page, live_server, route="home"):
    page.add_init_script("localStorage.setItem('exchange-guide-home-school', '長庚大學')")
    enter_public_site(page, live_server, route)
    page.wait_for_function("() => document.querySelector('#boot-splash') === null", timeout=60_000)


def z_of(page, selector):
    """The depth (px, towards the viewer) at which an element of the mascot sits."""
    return page.evaluate(
        """(selector) => {
          const style = getComputedStyle(document.querySelector(selector));
          const matrix = style.transform !== 'none' ? new DOMMatrix(style.transform).m43 : 0;
          const translate = style.translate && style.translate !== 'none' ? parseFloat(style.translate.split(' ')[2] || '0') : 0;
          return matrix + translate;
        }""",
        selector,
    )


def test_the_mascot_stands_where_the_traveller_drawing_was_on_the_home_page(page, live_server):
    start(page, live_server)
    expect(page.locator(HERO)).to_be_visible()
    assert page.locator(".journey-guide-art").count() == 0
    assert "suitcase.webp" in page.locator(f"{HERO} .uw-mascot-picture").get_attribute("src")
    box = page.locator(HERO).bounding_box()
    text = page.locator("#home-landing-title").bounding_box()
    assert box["x"] > text["x"] + text["width"] * 0.6 or box["y"] > text["y"], "beside or below the heading, not on top of it"


@pytest.mark.parametrize("width", [320, 390, 768, 1280])
def test_the_header_with_the_mascot_never_overflows_or_covers_the_words(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    start(page, live_server)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    mascot = page.locator(HERO).bounding_box()
    for selector in ("#home-landing-title", ".pr-hero-note"):
        words = page.locator(selector).bounding_box()
        overlap_x = min(mascot["x"] + mascot["width"], words["x"] + words["width"]) - max(mascot["x"], words["x"])
        overlap_y = min(mascot["y"] + mascot["height"], words["y"] + words["height"]) - max(mascot["y"], words["y"])
        assert not (overlap_x > 4 and overlap_y > 4), (selector, mascot, words)


def test_it_has_sides_a_front_and_eyes_standing_in_front_of_it(page, live_server):
    start(page, live_server)
    layers = page.locator(f"{HERO} .uw-mascot-slab > i")
    expect(layers).to_have_count(16)
    depths = page.evaluate(
        """(selector) => [...document.querySelectorAll(selector)].map(el => new DOMMatrix(getComputedStyle(el).transform).m43)""",
        f"{HERO} .uw-mascot-slab > i",
    )
    assert depths == sorted(depths) and len(set(round(d, 2) for d in depths)) == 16, "each layer at its own depth"
    front = z_of(page, f"{HERO} .uw-mascot-picture")
    assert front > max(depths), "the front picture stands ahead of every layer of the sides"
    assert depths[-1] - depths[0] > 15, "a real thickness, not a hair"
    assert z_of(page, f"{HERO} .uw-mascot-eyes") > front, "the eyes sit on the front, not behind it"
    assert page.evaluate("getComputedStyle(document.querySelector('.pr-collage-mascot .uw-mascot-body')).transformStyle") == "preserve-3d"
    assert page.evaluate("getComputedStyle(document.querySelector('.pr-collage-mascot')).perspective") == "700px"


def test_the_eyes_stay_in_front_while_they_look_around(page, live_server):
    start(page, live_server)
    names = page.evaluate("document.querySelector('.pr-collage-mascot .uw-mascot-eyes').getAnimations().map(a => a.animationName)")
    assert "uw-mascot-look" in names, "the looking-around animation is running"
    assert z_of(page, f"{HERO} .uw-mascot-eyes") > z_of(page, f"{HERO} .uw-mascot-picture"), "and it did not push them behind the picture"


def test_it_turns_towards_the_pointer_and_back_when_the_pointer_is_gone(page, live_server):
    start(page, live_server)
    box = page.locator(HERO).bounding_box()
    centre = (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    read = "parseFloat(document.querySelector('.pr-collage-mascot').style.getPropertyValue('--uw-tilt-y') || '0')"
    page.mouse.move(40, centre[1])
    page.wait_for_function(f"() => {read} < -5")
    # The hero mascot sits near the right edge, so a pointer at the far right is only a short way from it.
    page.mouse.move(1270, centre[1])
    page.wait_for_function(f"() => {read} > 1")
    page.mouse.move(centre[0], 20)
    page.wait_for_function("() => parseFloat(document.querySelector('.pr-collage-mascot').style.getPropertyValue('--uw-tilt-x') || '0') > 3")
    page.mouse.down()
    page.mouse.up()
    page.wait_for_function(f"() => Math.abs({read}) < 0.5")


def test_a_light_slides_over_it_as_it_turns(page, live_server):
    start(page, live_server)
    sheen = f"{HERO} .uw-mascot-sheen"
    assert page.evaluate("(s) => getComputedStyle(document.querySelector(s)).maskImage || getComputedStyle(document.querySelector(s)).webkitMaskImage", sheen) != "none"
    before = page.evaluate("(s) => getComputedStyle(document.querySelector(s)).backgroundImage", sheen)
    box = page.locator(HERO).bounding_box()
    page.mouse.move(30, box["y"] + box["height"] / 2)
    page.wait_for_function("""(s) => getComputedStyle(document.querySelector(s)).backgroundImage !== arguments[0]""".replace("arguments[0]", repr(before)), arg=sheen)


def test_with_no_motion_it_still_stands_turned_so_it_reads_as_a_solid(page, live_server):
    page.emulate_media(reduced_motion="reduce")
    start(page, live_server)
    box = page.locator(HERO).bounding_box()
    page.mouse.move(30, box["y"] + box["height"] / 2)
    page.wait_for_timeout(400)
    assert page.evaluate("document.querySelector('.pr-collage-mascot').style.getPropertyValue('--uw-tilt-y')") == "", "the pointer does not move it"
    assert page.evaluate("document.querySelector('.pr-collage-mascot .uw-mascot-body').getAnimations().length") == 0
    matrix = page.evaluate("getComputedStyle(document.querySelector('.pr-collage-mascot .uw-mascot-body')).transform")
    assert matrix != "none" and not matrix.startswith("matrix(1, 0, 0, 1"), matrix
    assert z_of(page, f"{HERO} .uw-mascot-eyes") > z_of(page, f"{HERO} .uw-mascot-picture")


def test_tapping_the_header_mascot_still_hops_turns_and_winks(page, live_server):
    start(page, live_server)
    mascot = page.locator(HERO)
    for move in ("hop", "spin", "wink"):
        mascot.click()
        expect(mascot).to_have_class(re.compile(rf"\bis-{move}\b"))
        expect(mascot).not_to_have_class(re.compile(rf"\bis-{move}\b"), timeout=4_000)


def test_the_loading_screen_mascot_is_the_same_solid(page, live_server):
    page.add_init_script("localStorage.setItem('exchange-guide-home-school', '長庚大學')")
    held = []
    page.route("**/student-dashboard**", lambda route: held.append(route))
    page.goto(f"{live_server.base_url}/#home", wait_until="commit")
    page.wait_for_function("() => document.querySelectorAll('#boot-splash .uw-mascot-slab > i').length === 16", timeout=15_000)
    assert z_of(page, "#boot-splash .uw-mascot-eyes") > z_of(page, "#boot-splash .uw-mascot-picture")
