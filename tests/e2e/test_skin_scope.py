"""School search and 我的申請 are drawn in the metro world; every other page keeps the look it had, under the same top bar."""
import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site

METRO = ["partners", "search", "my-application", "eligibility", "application-center", "calendar", "deadlines", "budget",
         "scholarships", "favorites", "document-check", "guide"]
CLASSIC = ["home", "forum", "public-board", "feedback"]
BAND = "data:image/svg+xml"


def skin(page):
    return page.evaluate("document.documentElement.dataset.skin || ''")


def backdrop(page) -> str:
    return page.locator("body").evaluate('el => getComputedStyle(el, "::before").backgroundImage')


def token(page, name: str) -> str:
    return page.evaluate("(name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim().toLowerCase()", name)


@pytest.mark.parametrize("route", METRO)
def test_school_search_and_my_application_are_in_the_metro_world(page, live_server, route):
    enter_public_site(page, live_server, route)
    assert skin(page) == "metro"
    # The five-line band across the top is the world's own, and the names the older stylesheets read point at its ink.
    assert BAND in backdrop(page)
    assert token(page, "--uw-accent") == token(page, "--mt-ink")


@pytest.mark.parametrize("route", CLASSIC)
def test_every_other_page_keeps_its_own_look(page, live_server, route):
    enter_public_site(page, live_server, route)
    assert skin(page) == ""
    # Its own soft backdrop is still there, where the metro pages draw the band.
    assert "radial-gradient" in backdrop(page) and BAND not in backdrop(page)
    # The names the older stylesheets read are not re-pointed here: the accent is still the midnight blue, not the metro ink.
    assert token(page, "--uw-accent") != token(page, "--mt-ink")


def test_the_home_is_the_one_visitors_already_know(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 900})
    enter_public_site(page, live_server, "home")
    expect(page.locator("#home-landing-title")).to_contain_text("你能去哪些交換學校")
    expect(page.locator("#home-plan-steps li")).to_have_count(4)
    expect(page.locator(".pr-collage-mascot")).to_be_visible()
    # Labels above headings and the lines under them belong to this look; the metro pages hide them.
    expect(page.locator("#home-landing .pr-kicker").first).to_be_visible()
    assert page.locator(".mt-board, .mt-earth").count() == 0
    # The switcher still says what it does.
    expect(page.locator("#school-switcher small")).to_be_visible()


def test_the_top_bar_is_the_same_on_a_classic_page_and_a_metro_page(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 900})
    seen = {}
    for route in ("home", "partners"):
        enter_public_site(page, live_server, route)
        seen[route] = page.evaluate(
            """() => {
              const bar = document.querySelector('#glass-navigation'), style = getComputedStyle(bar);
              const box = (el) => { const r = el.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; };
              const link = bar.querySelector('a[data-public-route="forum"]'), linkStyle = getComputedStyle(link);
              return { bar: box(bar), position: style.position, rule: style.borderBottomWidth + ' ' + style.borderBottomColor,
                       ground: style.backgroundColor, brand: box(bar.querySelector('.uniway-header-brand')),
                       link: [linkStyle.color, linkStyle.fontWeight, linkStyle.fontSize, box(link)[3]], account: box(bar.querySelector('#account-button')) };
            }"""
        )
    assert seen["home"] == seen["partners"], seen
    # A classic page keeps body::before for its backdrop, so there the band is the top edge of the bar.
    enter_public_site(page, live_server, "home")
    assert BAND in page.locator("#glass-navigation").evaluate("el => getComputedStyle(el).backgroundImage")


def test_on_a_phone_a_classic_page_keeps_its_own_header_and_drawer(page, live_server):
    page.set_viewport_size({"width": 393, "height": 852})
    enter_public_site(page, live_server, "forum")
    header = page.locator(".glass-mobile-header")
    assert header.evaluate("el => getComputedStyle(el).borderTopLeftRadius") != "0px", "the rounded glass header"
    assert header.evaluate("el => getComputedStyle(el).borderBottomWidth") == "1px"
    enter_public_site(page, live_server, "partners")
    assert header.evaluate("el => getComputedStyle(el).borderBottomWidth") == "2px", "the metro header rule"


def test_moving_between_pages_switches_the_world_and_back(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 900})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "home")
    assert skin(page) == ""
    page.locator('#glass-navigation a[data-public-route="partners"]').click()
    expect(page.locator("#partners")).to_be_visible()
    assert skin(page) == "metro"
    # The school page opened from the search belongs to it.
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#school-detail-view")).to_be_visible()
    assert skin(page) == "metro"
    page.go_back()
    expect(page.locator("#partners")).to_be_visible()
    assert skin(page) == "metro"
    page.locator('#glass-navigation a[data-public-route="forum"]').click()
    expect(page.locator("#community-hub")).to_be_visible()
    assert skin(page) == "" and "radial-gradient" in backdrop(page)
    page.go_back()
    expect(page.locator("#partners")).to_be_visible()
    assert skin(page) == "metro" and BAND in backdrop(page)
    page.locator('#glass-navigation a[data-public-route="home"]').click()
    expect(page.locator("#home-landing")).to_be_visible()
    assert skin(page) == ""
    assert not errors


def test_the_world_follows_the_page_on_screen_not_the_address(page, live_server):
    # An address the app does not know opens 我的申請; it must be drawn as 我的申請, not left half in the classic look.
    enter_public_site(page, live_server, "no-such-page")
    assert page.evaluate("document.body.dataset.activeUniversityPage") == "overview"
    assert skin(page) == "metro"


def test_school_marks_keep_their_one_blue_on_the_classic_pages(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 900})
    enter_public_site(page, live_server, "home")
    page.locator("#school-switcher").click()
    expect(page.locator(".school-option").first).to_be_visible()
    tints = page.evaluate("[...document.querySelectorAll('.school-option')].map((el) => el.style.getPropertyValue('--school-tint'))")
    # Only the schools given a colour of their own differ; the rest share the blue they always had.
    assert tints.count("200") > len(tints) / 2, tints
