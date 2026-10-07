from datetime import timedelta
import re
import os
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect
import requests

from exchange_info.models import CommunityPost, CommunityPostComment, utc_now
from exchange_info.storage import append_community_post, append_community_post_comment
from .conftest import enter_public_site, login_through_web


def seed(live_server, *, count=1):
    marker = "討論測試" + uuid4().hex[:8]
    posts = []
    for index in range(count):
        item = CommunityPost(board_id="public-study-abroad", board_kind="public_study_abroad",
            school_name="公共留學板", author_id="private-author", display_name="匿名學生",
            title=f"{marker} 日本交換經驗 {index:02d}",
            body="這是日本交換申請經驗，請核對你申請年度的官方公告。\n第二段分享住宿與簽證準備。",
            country="日本", academic_year="2027 秋季", application_stage="preparing",
            created_at=utc_now() - timedelta(hours=1, minutes=index))
        append_community_post(item, live_server.data_dir)
        posts.append(item)
    append_community_post_comment(CommunityPostComment(post_id=posts[0].id,
        author_id="private-commenter", display_name="匿名學生", body="建議先查看當年度的提名信。"), live_server.data_dir)
    return marker, posts


def search(page, marker):
    page.locator("#global-community-search").fill(marker)
    expect(page).to_have_url(re.compile("discussion_q=.*" + marker[-8:]))
    expect(page.locator(".discussion-summary").first).to_contain_text(marker)


def capture(page, name):
    target = os.environ.get("UNIWAY_DISCUSSION_ARTIFACT_DIR")
    if target:
        directory = Path(target)
        directory.mkdir(parents=True, exist_ok=True)
        page.locator("#discussion-reader").evaluate("el => Promise.all(el.getAnimations().map(animation => animation.finished.catch(() => {})))")
        page.screenshot(path=str(directory / name), full_page=False)


def test_lazy_reader_permalink_saved_and_back_restore(page, live_server):
    marker, posts = seed(live_server, count=24)
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    enter_public_site(page, live_server, "public-board")
    search(page, marker)
    expect(page.locator(".discussion-summary")).to_have_count(20)
    assert not any(f"/community/posts/{posts[0].id}" in url for url in requests)
    # Pagination remains accessible without relying on automatic scroll loading.
    page.locator("#discussion-feed-more").click()
    expect(page.locator(".discussion-summary")).to_have_count(24)
    trigger = page.locator(f'[data-discussion-open="{posts[0].id}"]').first
    trigger.click()
    expect(page.locator("#discussion-reader")).to_be_visible()
    expect(page.locator("#discussion-article-title")).to_contain_text(marker)
    expect(page.locator("#discussion-comments")).to_contain_text("當年度的提名信")
    capture(page, "discussion-desktop.png")
    assert f"discussion={posts[0].id}" in page.url
    assert any(f"/community/posts/{posts[0].id}/comments" in url for url in requests)
    page.locator(f'#discussion-reader [data-discussion-save="{posts[0].id}"]').click()
    expect(page.locator(f'#discussion-reader [data-discussion-save="{posts[0].id}"]')).to_have_attribute("aria-pressed", "true")
    permalink = page.url
    page.locator("#discussion-reader-close").click()
    expect(page.locator("#discussion-reader")).not_to_be_visible()
    expect(page.locator(".discussion-summary")).to_have_count(24)
    expect(page.locator("#global-community-search")).to_have_value(marker)
    page.locator("#discussion-saved-filter").click()
    expect(page.locator(".discussion-summary")).to_have_count(1)
    page.goto(permalink)
    expect(page.locator("#discussion-article-title")).to_contain_text(marker)
    page.locator("#discussion-reader-close").click()
    expect(page.locator("#discussion-reader")).not_to_be_visible()


def test_quote_draft_and_cookie_reply(page, live_server):
    marker, posts = seed(live_server)
    email = f"discussion-{uuid4().hex[:8]}@example.com"
    session = live_server.register(email)
    login_through_web(page, live_server, email)
    page.locator('a[href="#forum"]:visible').first.click()
    page.locator('a[href="#public-board"]:visible').first.click()
    search(page, marker)
    page.locator(f'[data-discussion-open="{posts[0].id}"]').first.click()
    expect(page.locator("#discussion-comments")).to_contain_text("當年度的提名信")
    page.locator("[data-discussion-quote]").click()
    expect(page.locator("#discussion-reply-body")).to_have_value("引用 B1：建議先查看當年度的提名信。\n\n")
    draft = "引用 B1：建議先查看當年度的提名信。\n\n我已收到提名信，謝謝你的提醒。"
    page.locator("#discussion-reply-body").fill(draft)
    page.locator("#discussion-reader-close").click()
    expect(page.locator("#discussion-reader")).not_to_be_visible()
    page.locator(f'[data-discussion-open="{posts[0].id}"]').first.click()
    expect(page.locator("#discussion-reply-body")).to_have_value(draft)
    # Another tab rotates the anonymous credential; the Web safely refreshes it
    # once while preserving the same idempotency key and reply payload.
    requests.post(f"{live_server.base_url}/auth/community-identity",
                  headers={"Authorization": f"Bearer {session['access_token']}"}, timeout=10).raise_for_status()
    page.locator('#discussion-reader .post-comment-form button[type="submit"]').click()
    expect(page.locator("#discussion-comments")).to_contain_text("我已收到提名信")
    expect(page.locator("#discussion-reply-body")).to_have_value("")
    page.locator("#discussion-reader-close").click()
    expect(page.locator("#discussion-reader")).not_to_be_visible()
    page.locator(f'[data-discussion-open="{posts[0].id}"]').first.click()
    expect(page.locator("#discussion-reply-body")).to_have_value("")


def test_mobile_reader_keyboard_exit_and_comment_failure_isolated(page, live_server):
    marker, posts = seed(live_server)
    page.set_viewport_size({"width": 390, "height": 844})
    page.route(f"**/community/posts/{posts[0].id}/comments?*", lambda route: route.fulfill(
        status=503, content_type="application/json", body='{"detail":"回覆暫時不可用"}'))
    enter_public_site(page, live_server, "public-board")
    search(page, marker)
    page.locator(f'[data-discussion-open="{posts[0].id}"]').first.click()
    expect(page.locator("#discussion-article-title")).to_contain_text(marker)
    expect(page.locator("#discussion-comments")).to_contain_text("回覆暫時無法載入")
    expect(page.locator("#discussion-reader")).to_have_css("width", "390px")
    page.unroute(f"**/community/posts/{posts[0].id}/comments?*")
    page.locator("[data-discussion-comments-retry]").click()
    expect(page.locator("#discussion-comments")).to_contain_text("當年度的提名信")
    capture(page, "discussion-mobile.png")
    page.keyboard.press("Escape")
    expect(page.locator("#discussion-reader")).not_to_be_visible()


def test_guest_can_enter_login_from_modal_and_resume_article(page, live_server):
    marker, posts = seed(live_server)
    email = f"reader-login-{uuid4().hex[:8]}@example.com"
    live_server.register(email)
    enter_public_site(page, live_server, "public-board")
    search(page, marker)
    page.locator(f'[data-discussion-open="{posts[0].id}"]').first.click()
    page.locator('#discussion-reader [data-open-auth]').click()
    expect(page.locator("#discussion-reader")).not_to_be_visible()
    expect(page.locator("#auth-dialog")).to_be_visible()
    page.locator("#login-form input[name=email]").fill(email)
    page.locator("#login-form input[name=password]").fill("CodexE2E!2026")
    with page.expect_response(lambda response: response.url == f"{live_server.base_url}/auth/login"
                              and response.request.method == "POST", timeout=60_000) as result:
        page.locator("#login-form button[type=submit]").click()
    assert result.value.ok, result.value.text()
    expect(page.locator("#auth-dialog")).not_to_be_visible()
    expect(page.locator("#discussion-reader")).to_be_visible()
    expect(page.locator("#discussion-reply-body")).to_be_visible()

