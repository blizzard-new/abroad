"""The four-stage deck in the application guide: it moves on its own only when that is safe, and the reader is always in control."""
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site

INTERVAL_MS = 8000
PLAYING = re.compile(r"\bis-playing\b")


def open_deck(browser, live_server, **options):
    """Open the guide with a fake clock, so a test can jump the eight-second timer instead of waiting for it."""
    context = browser.new_context(**options)
    page = context.new_page()
    page.clock.install()
    enter_public_site(page, live_server, "guide=how-to-use")
    deck = page.locator("[data-stage-deck]")
    expect(deck).to_be_visible()
    deck.scroll_into_view_if_needed()
    freeze(page)
    return context, page, deck


def freeze(page):
    """Render the guide afresh, so the eight-second timer starts now, and stop time until the test moves it."""
    page.evaluate("window.UniWayGuide.show('how-to-use')")
    page.clock.pause_at(page.evaluate("Date.now()") / 1000 + 0.05)  # Playwright takes seconds


def active(page) -> int:
    return page.evaluate("[...document.querySelectorAll('[data-deck-card]')].findIndex(card => card.hasAttribute('data-active'))")


def tick(page, times=1):
    for _ in range(times):
        page.clock.fast_forward(INTERVAL_MS + 100)


def test_four_stages_with_the_first_one_open(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    try:
        heads = deck.locator(".pr-deck-head")
        expect(heads).to_have_count(4)
        expect(heads.locator(".pr-deck-title")).to_have_text(["找學校", "準備校內甄選", "完成合作校申請", "安排出發"])
        expect(heads.nth(0)).to_have_attribute("aria-expanded", "true")
        for index in (1, 2, 3):
            expect(heads.nth(index)).to_have_attribute("aria-expanded", "false")
            # A closed card's link is neither visible nor reachable with Tab.
            expect(deck.locator(".pr-deck-body a").nth(index)).to_be_hidden()
        link = deck.locator(".pr-deck-body a").first
        expect(link).to_be_visible()
        expect(link).to_have_attribute("href", "#partners")
        expect(deck.locator(".pr-deck-body a").nth(1)).to_have_attribute("href", "#eligibility")
        expect(deck.locator(".pr-deck-body a").nth(2)).to_have_attribute("href", "#application-center")
        expect(deck.locator(".pr-deck-body a").nth(3)).to_have_attribute("href", "#budget")
    finally:
        context.close()


def test_open_card_moves_on_every_eight_seconds_and_wraps_around(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 1280, "height": 900})
    try:
        expect(deck).to_have_class(PLAYING)
        assert active(page) == 0
        tick(page)
        assert active(page) == 1
        expect(deck.locator(".pr-deck-head").nth(1)).to_have_attribute("aria-expanded", "true")
        expect(deck.locator(".pr-deck-head").nth(0)).to_have_attribute("aria-expanded", "false")
        tick(page, 3)
        assert active(page) == 0
    finally:
        context.close()


def test_pause_button_stops_and_resumes_the_deck(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 1280, "height": 900})
    try:
        pause = deck.get_by_role("button", name="暫停自動播放")
        expect(pause).to_be_visible()
        pause.click()
        resume = deck.get_by_role("button", name="繼續自動播放")
        expect(resume).to_have_attribute("aria-pressed", "true")
        expect(deck).not_to_have_class(PLAYING)
        tick(page, 3)
        assert active(page) == 0
        resume.click()
        expect(deck.get_by_role("button", name="暫停自動播放")).to_have_attribute("aria-pressed", "false")
        expect(deck).to_have_class(PLAYING)
        tick(page)
        assert active(page) == 1
    finally:
        context.close()


def test_choosing_a_card_opens_it_and_stops_the_deck_choosing_for_you(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 1280, "height": 900})
    try:
        deck.locator(".pr-deck-head").nth(2).click()
        assert active(page) == 2
        expect(deck.locator(".pr-deck-body a").nth(2)).to_be_visible()
        expect(deck.get_by_role("button", name="繼續自動播放")).to_have_attribute("aria-pressed", "true")
        tick(page, 3)
        assert active(page) == 2
    finally:
        context.close()


def test_pointing_at_the_deck_or_focusing_inside_it_holds_it_still(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 1280, "height": 900})
    try:
        deck.locator(".pr-deck-cards").hover()
        expect(deck).not_to_have_class(PLAYING)
        tick(page, 2)
        assert active(page) == 0
        page.mouse.move(2, 2)
        expect(deck).to_have_class(PLAYING)
        deck.locator(".pr-deck-head").nth(1).focus()
        expect(deck).not_to_have_class(PLAYING)
        tick(page, 2)
        assert active(page) == 0
        page.evaluate("document.activeElement.blur()")
        expect(deck).to_have_class(PLAYING)
    finally:
        context.close()


def test_the_deck_does_not_play_while_it_is_off_screen(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 1280, "height": 360})
    try:
        expect(deck).to_have_class(PLAYING)
        page.locator(".pr-guide-feedback").scroll_into_view_if_needed()
        page.locator(".pr-guide-pager").scroll_into_view_if_needed()
        expect(deck).not_to_have_class(PLAYING)
        tick(page, 2)
        assert active(page) == 0
    finally:
        context.close()


def test_reduced_motion_never_plays_and_hides_the_pause_button(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    try:
        expect(deck.locator("[data-deck-pause]")).to_be_hidden()
        expect(deck).not_to_have_class(PLAYING)
        tick(page, 2)
        assert active(page) == 0
        assert deck.locator(".pr-deck-card").first.evaluate("el => getComputedStyle(el).transitionDuration") == "0s"
        deck.locator(".pr-deck-head").nth(3).click()
        assert active(page) == 3
    finally:
        context.close()


def test_navigating_away_and_back_does_not_stack_timers(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 1280, "height": 900})
    try:
        page.evaluate("location.hash = '#guide=eligibility'")
        expect(page.locator("#guide-article h1")).to_contain_text("確認資格與排志願")
        expect(page.locator("[data-stage-deck]")).to_have_count(0)
        page.evaluate("location.hash = '#guide=how-to-use'")
        deck = page.locator("[data-stage-deck]")
        expect(deck).to_be_visible()
        deck.scroll_into_view_if_needed()
        freeze(page)
        expect(deck).to_have_class(PLAYING)
        tick(page)
        assert active(page) == 1  # one timer, one step
    finally:
        context.close()


def test_wide_screens_lay_the_cards_in_a_row_with_the_open_one_wider(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 1280, "height": 900})
    try:
        boxes = deck.locator(".pr-deck-card").evaluate_all(
            "cards => cards.map(card => { const r = card.getBoundingClientRect(); return { top: Math.round(r.top), width: r.width }; })")
        assert len({box["top"] for box in boxes}) == 1
        assert boxes[0]["width"] > 2 * max(box["width"] for box in boxes[1:])
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    finally:
        context.close()


def test_phones_stack_the_cards_without_overflow(browser, live_server):
    context, page, deck = open_deck(browser, live_server, viewport={"width": 390, "height": 844})
    try:
        boxes = deck.locator(".pr-deck-card").evaluate_all(
            "cards => cards.map(card => { const r = card.getBoundingClientRect(); return { top: r.top, left: Math.round(r.left), width: Math.round(r.width) }; })")
        assert [box["top"] for box in boxes] == sorted(box["top"] for box in boxes)
        assert len({box["left"] for box in boxes}) == 1 and len({box["width"] for box in boxes}) == 1
        expect(deck.locator(".pr-deck-body a").first).to_be_visible()
        expect(deck.locator(".pr-deck-body a").nth(1)).to_be_hidden()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    finally:
        context.close()
