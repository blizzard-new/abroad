"""The home route map is drawn from the catalogue: each region is a line, each partner country a station, and the
station board searches the same way the explore page does. Nothing on it is a sample."""
import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site


def _ready(page) -> None:
    expect(page.locator("[data-metro-route]")).to_have_attribute("data-state", "ready", timeout=30_000)


def test_each_country_is_one_station_on_the_line_of_its_region(page, live_server) -> None:
    enter_public_site(page, live_server, "home")
    _ready(page)
    names = page.locator(".mt-station b").all_inner_texts()
    assert len(names) == len(set(names)), "a country is one station"
    assert {"法國", "日本", "美國"} <= set(names)
    europe = page.locator('.mt-line[data-line="europe"] .mt-station b').all_inner_texts()
    assert "法國" in europe and "日本" not in europe
    east_asia = page.locator('.mt-line[data-line="east-asia"] .mt-station b').all_inner_texts()
    assert "日本" in east_asia and "韓國" in east_asia


def test_station_counts_are_the_catalogues_own_numbers(page, live_server) -> None:
    enter_public_site(page, live_server, "home")
    _ready(page)
    dashboard = page.evaluate("fetch('/student-dashboard').then((response) => response.json())")
    france = sum(1 for item in dashboard["partner_universities"] if item["country"] == "法國")
    label = page.locator('.mt-station[data-home-country="法國"] small').inner_text()
    assert f"/ {france} " in label or f"{france} 間" in label, label
    spoken = page.locator('.mt-station[data-home-country="法國"]').get_attribute("aria-label")
    assert f"{france} 間合作校" in spoken


def test_a_station_opens_the_explore_page_for_that_country(page, live_server) -> None:
    enter_public_site(page, live_server, "home")
    _ready(page)
    page.locator('.mt-station[data-home-country="日本"]').click()
    expect(page.locator("#partners")).to_be_visible()
    assert "country=%E6%97%A5%E6%9C%AC" in page.url


def test_the_station_board_fills_the_explore_criteria_before_opening_it(page, live_server) -> None:
    enter_public_site(page, live_server, "home")
    _ready(page)
    page.locator("#mt-board-q").fill("日本")
    page.locator("#mt-board-term").select_option("fall")
    page.locator("#mt-board .mt-board-go").click()
    expect(page.locator("#partners")).to_be_visible()
    assert page.locator("#partner-term-tile").input_value() == "fall"
    assert "q=%E6%97%A5%E6%9C%AC" in page.url


def test_the_language_test_options_mirror_the_explore_page(page, live_server) -> None:
    enter_public_site(page, live_server, "home")
    board = page.locator("#mt-board-test option").all_inner_texts()
    explore = page.locator("#partner-test-tile option").all_inner_texts()
    assert board == explore and len(board) > 1


def test_a_line_tag_focuses_its_line_and_a_second_press_clears_it(page, live_server) -> None:
    enter_public_site(page, live_server, "home")
    _ready(page)
    tag = page.locator('[data-line-tag="europe"]')
    route = page.locator("[data-metro-route]")
    tag.click()
    expect(route).to_have_attribute("data-focus", "europe")
    expect(tag).to_have_attribute("aria-pressed", "true")
    expect(page.locator('.mt-path[data-line="east-asia"]')).to_have_css("opacity", "0.18")
    expect(page.locator('.mt-path[data-line="europe"]')).to_have_css("opacity", "1")
    tag.click()
    expect(route).to_have_attribute("data-focus", "")
    expect(tag).to_have_attribute("aria-pressed", "false")


def test_a_station_says_open_or_on_file_in_words_not_only_in_colour(page, live_server) -> None:
    enter_public_site(page, live_server, "home")
    _ready(page)
    for station in page.locator(".mt-station").all():
        text = station.locator("small").inner_text()
        assert "開放" in text or "待確認" in text or "合作備查" in text, text
        assert station.get_attribute("data-filled") in {"true", "false"}


@pytest.mark.parametrize("width", [320, 390, 768, 1280, 1440, 1920])
def test_the_route_map_never_overflows_the_page(browser, live_server, width) -> None:
    context = browser.new_context(viewport={"width": width, "height": 900})
    page = context.new_page()
    try:
        enter_public_site(page, live_server, "home")
        _ready(page)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        box = page.locator(".mt-stage").bounding_box()
        assert box["x"] >= -1 and box["x"] + box["width"] <= width + 1
    finally:
        context.close()


def test_on_a_phone_the_map_is_a_route_sheet_with_the_first_line_open(browser, live_server) -> None:
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    try:
        enter_public_site(page, live_server, "home")
        _ready(page)
        lines = page.locator(".mt-line")
        assert lines.count() >= 2
        expect(page.locator(".mt-lines")).to_be_hidden()
        expect(lines.first.locator(".mt-stops")).to_be_visible()
        expect(lines.nth(1).locator(".mt-stops")).to_be_hidden()
        lines.nth(1).locator(".mt-line-tag").click()
        expect(lines.nth(1).locator(".mt-stops")).to_be_visible()
        expect(lines.first.locator(".mt-stops")).to_be_hidden()
    finally:
        context.close()


def test_the_night_theme_keeps_the_stations_readable(browser, live_server) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.add_init_script("localStorage.setItem('exchange-guide-theme', 'dark')")
    try:
        enter_public_site(page, live_server, "home")
        _ready(page)
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        ground = page.evaluate("getComputedStyle(document.body).backgroundColor")
        ink = page.evaluate("getComputedStyle(document.querySelector('.mt-label b')).color")
        assert ground != ink
    finally:
        context.close()
