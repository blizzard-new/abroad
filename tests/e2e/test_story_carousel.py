"""The forum's story strip shows only approved write-ups, never moves by itself, and is absent when there is nothing to show."""
from datetime import timedelta

import pytest
from playwright.sync_api import expect

from exchange_info.models import CommunityIdentityMode, ExperienceSubmission, ModerationStatus, utc_now
from exchange_info.storage import save_experience_submissions

from .conftest import enter_public_site

LINCOLN = "林肯大學 Lincoln University"
LONG_SUMMARY = "宿舍要在錄取後很短的時間內申請，出發前先確認繳費與入住日期。" * 8


def story(title, *, status=ModerationStatus.APPROVED, minutes_ago=0, **extra):
    fields = {
        "school_name": LINCOLN, "home_university": "長庚大學", "summary": "每月房租與交通是最大的兩筆支出，先查宿舍再決定。",
        "exchange_year": "2025", "themes": ["housing"], **extra,
    }
    return ExperienceSubmission(title=title, status=status, created_at=utc_now() - timedelta(minutes=minutes_ago), **fields)


@pytest.fixture
def seed(live_server):
    def save(*rows):
        save_experience_submissions(list(rows), live_server.data_dir)
    yield save
    save_experience_submissions([], live_server.data_dir)


def open_forum(browser, live_server, **options):
    context = browser.new_context(**options)
    page = context.new_page()
    enter_public_site(page, live_server, "forum")
    return context, page


def scroll_left(page) -> float:
    return page.locator("#forum-story-track").evaluate("el => el.scrollLeft")


def test_only_approved_stories_appear_and_authors_are_not_identified(browser, live_server, seed):
    seed(
        story("林肯住宿與交通", summary=LONG_SUMMARY, author_id="account-secret-id", minutes_ago=1,
              source_url="https://example.com/my-story"),
        story("具名分享", identity_mode=CommunityIdentityMode.REAL_NAME, display_name="王小華", minutes_ago=2),
        story("匿名分享", identity_mode=CommunityIdentityMode.ANONYMOUS, display_name="陳小明", minutes_ago=3),
        story("還在審核", status=ModerationStatus.PENDING),
        story("已被隱藏", status=ModerationStatus.HIDDEN),
    )
    context, page = open_forum(browser, live_server, viewport={"width": 1440, "height": 900})
    try:
        strip = page.locator("#forum-stories")
        expect(strip).to_be_visible()
        expect(strip.locator(".pr-story h3")).to_have_text(["林肯住宿與交通", "具名分享", "匿名分享"])
        text = strip.inner_text()
        assert "還在審核" not in text and "已被隱藏" not in text
        assert "陳小明" not in text and "account-secret-id" not in page.content()
        expect(strip.locator(".pr-story-by span")).to_have_text(["匿名投稿者", "王小華", "匿名投稿者"])
        link = strip.locator(".pr-story-source")
        expect(link).to_have_count(1)
        expect(link).to_have_attribute("rel", "noopener noreferrer nofollow ugc")
        expect(link).to_have_attribute("target", "_blank")
    finally:
        context.close()


def test_the_strip_is_absent_when_no_story_is_approved(browser, live_server, seed):
    seed(story("還在審核", status=ModerationStatus.PENDING), story("已被隱藏", status=ModerationStatus.HIDDEN))
    context, page = open_forum(browser, live_server, viewport={"width": 1440, "height": 900})
    try:
        expect(page.locator("#forum-stories")).to_be_hidden()
        assert page.locator("#forum-story-track").evaluate("el => el.children.length") == 0
    finally:
        context.close()


def test_the_strip_is_only_for_the_story_view(browser, live_server, seed):
    seed(story("林肯住宿與交通"))
    context, page = open_forum(browser, live_server, viewport={"width": 1440, "height": 900})
    try:
        expect(page.locator("#forum-stories")).to_be_visible()
        page.locator('[data-forum-mode="question"]').click()
        expect(page.locator("#forum-stories")).to_be_hidden()
        page.locator('[data-forum-mode="story"]').click()
        expect(page.locator("#forum-stories")).to_be_visible()
    finally:
        context.close()


@pytest.mark.parametrize("reduced_motion", ["reduce", "no-preference"])
def test_arrows_move_the_strip_and_nothing_moves_on_its_own(browser, live_server, seed, reduced_motion):
    seed(*(story(f"心得 {n}", minutes_ago=n) for n in range(1, 6)))
    context, page = open_forum(browser, live_server, viewport={"width": 390, "height": 844}, reduced_motion=reduced_motion)
    try:
        expect(page.locator("#forum-stories")).to_be_visible()
        prev, following = page.locator('[data-stories-step="-1"]'), page.locator('[data-stories-step="1"]')
        count = page.locator("#forum-stories-count")
        expect(count).to_have_text("1 / 5")
        expect(prev).to_be_disabled()
        expect(following).to_be_enabled()
        page.wait_for_timeout(2500)  # a carousel that auto-plays would have moved by now
        assert scroll_left(page) == 0
        following.click()
        expect(count).to_have_text("2 / 5")
        expect(prev).to_be_enabled()
        assert scroll_left(page) > 0
        prev.click()
        expect(count).to_have_text("1 / 5")
        for _ in range(4):
            following.click()
        expect(count).to_have_text("5 / 5")
        expect(following).to_be_disabled()
    finally:
        context.close()


def test_the_focused_strip_scrolls_with_the_keyboard(browser, live_server, seed):
    seed(*(story(f"心得 {n}", minutes_ago=n) for n in range(1, 6)))
    context, page = open_forum(browser, live_server, viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    try:
        strip = page.locator("#forum-story-track")
        expect(strip).to_have_attribute("tabindex", "0")
        strip.focus()
        page.keyboard.press("ArrowRight")
        page.wait_for_function("() => document.querySelector('#forum-story-track').scrollLeft > 0")
        expect(page.locator("#forum-stories-count")).not_to_have_text("1 / 5")
    finally:
        context.close()


def test_long_summaries_can_be_expanded_and_collapsed(browser, live_server, seed):
    seed(story("長篇心得", summary=LONG_SUMMARY, minutes_ago=1), story("短篇心得", minutes_ago=2))
    context, page = open_forum(browser, live_server, viewport={"width": 1440, "height": 900})
    try:
        cards = page.locator(".pr-story")
        more = cards.nth(0).locator("[data-story-more]")
        expect(more).to_be_visible()
        expect(cards.nth(1).locator("[data-story-more]")).to_be_hidden()
        clamped = cards.nth(0).locator(".pr-story-summary").evaluate("el => el.clientHeight")
        more.click()
        expect(more).to_have_attribute("aria-expanded", "true")
        assert cards.nth(0).locator(".pr-story-summary").evaluate("el => el.clientHeight") > clamped
        more.click()
        expect(more).to_have_attribute("aria-expanded", "false")
    finally:
        context.close()


def test_slides_are_labelled_for_screen_readers(browser, live_server, seed):
    seed(story("心得 A", minutes_ago=1), story("心得 B", minutes_ago=2))
    context, page = open_forum(browser, live_server, viewport={"width": 1440, "height": 900})
    try:
        expect(page.locator("#forum-stories")).to_have_attribute("aria-roledescription", "carousel")
        slides = page.locator(".pr-story")
        expect(slides.nth(0)).to_have_attribute("aria-roledescription", "slide")
        expect(slides.nth(0)).to_have_attribute("aria-label", "第 1 則，共 2 則")
        expect(slides.nth(1)).to_have_attribute("aria-label", "第 2 則，共 2 則")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    finally:
        context.close()
