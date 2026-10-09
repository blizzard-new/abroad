"""Synthetic reader cleanup; never uses production accounts or school content."""
from uuid import uuid4

import pytest
import requests
from playwright.sync_api import expect

from exchange_info.models import CommunityPost, CommunityPostComment
from exchange_info.storage import append_community_post, append_community_post_comment
from .conftest import login_through_web


@pytest.mark.parametrize("late_kind", ["none", "comments", "detail"])
def test_expired_school_reader_closes_and_discards_drafts_and_late_responses(page, live_server, late_kind):
    marker = "合成校板私人正文" + uuid4().hex[:8]
    post = CommunityPost(board_id="tku", board_kind="university_exchange", school_name="淡江大學",
        author_id="synthetic-owner", display_name="匿名學生", title=marker, body=marker + "，僅供隔離驗證。")
    append_community_post(post, live_server.data_dir)
    append_community_post_comment(CommunityPostComment(post_id=post.id, author_id="synthetic-commenter",
        display_name="匿名學生", body="合成校板回覆，僅供隔離驗證。"), live_server.data_dir)
    email = "reader-expiry-" + uuid4().hex[:8] + "@example.com"
    live_server.register(email)
    login_through_web(page, live_server, email)
    page.goto(f"{live_server.base_url}/?discussion={post.id}#university-posts")
    expect(page.locator("#discussion-article-title")).to_have_text(marker)
    expect(page.locator("#discussion-comments")).to_contain_text("合成校板回覆")
    # Permalink boot can still hydrate account/workspace/bookmarks after the
    # first detail renders. Drain those real requests before revoking the cookie,
    # so this case exercises the intended sort/reaction 401 rather than a
    # background request closing the reader during Playwright's selection.
    page.wait_for_function("() => !state.homeSchoolLoading && state.accountWorkspaceLoadingCount === 0", timeout=60_000)
    page.wait_for_load_state("networkidle", timeout=60_000)
    expect(page.locator("#boot-splash")).to_be_hidden()
    expect(page.locator("#auth-dialog")).not_to_be_visible()
    expect(page.locator("#discussion-reader")).to_be_visible()
    assert page.evaluate("state.account !== null")
    page.locator("#discussion-reply-body").fill("合成私人草稿，失效後必須清除。")
    page.wait_for_function("() => Object.keys(sessionStorage).some(k => k.startsWith('uniway-discussion-draft:'))")
    if late_kind != "none":
        page.evaluate("""({id, kind}) => {
          const original = window.fetch;
          let release;
          const gate = new Promise(resolve => { release = resolve; });
          window.__lateReader = { release, captured: false, settled: false, status: null };
          window.fetch = async (...args) => {
            const url = String(args[0]);
            const match = kind === 'comments' ? url.includes(`/community/posts/${id}/comments?`)
              : url.endsWith(`/community/posts/${id}`);
            const response = await original(...args);
            if (match && response.ok && !window.__lateReader.captured) {
              window.__lateReader.captured = true;
              window.__lateReader.status = response.status;
              await gate;
              window.__lateReader.settled = true;
            }
            return response;
          };
        }""", {"id": post.id, "kind": late_kind})
        if late_kind == "comments":
            page.locator("#discussion-comment-sort").select_option("latest")
        else:
            page.evaluate("window.UniWayCommunity.refresh()")
        page.wait_for_function("() => window.__lateReader.captured")
        assert page.evaluate("window.__lateReader.status") == 200
    cookies = {c["name"]: c["value"] for c in page.context.cookies() if c["name"] == "exchange_guide_session"}
    assert requests.post(f"{live_server.base_url}/auth/logout", cookies=cookies, timeout=10).status_code == 204
    with page.expect_response(lambda r: r.status == 401 and "/community/" in r.url):
        if late_kind == "none":
            page.locator("#discussion-comment-sort").select_option("latest")
        elif late_kind == "comments":
            page.locator('#discussion-reader [data-discussion-react="helpful"][data-resource-type="post"]').click()
        else:
            # The original detail has replaced the action controls with its loading
            # state; exercise the same real comments transport while that GET waits.
            page.evaluate("id => { void fetchJson(`/community/posts/${id}/comments?sort=latest&limit=20`).catch(() => {}); }", post.id)
    expect(page.locator("#auth-dialog")).to_be_visible()
    expect(page.locator("#discussion-reader")).not_to_be_visible()
    expect(page.locator("#discussion-reader-body")).to_be_empty()
    assert page.evaluate("state.account") is None
    assert page.evaluate("Object.keys(sessionStorage).filter(k => k.startsWith('uniway-discussion-draft:'))") == []
    page.locator("#login-form input[name=email]").fill(email)
    expect(page.locator("#login-form input[name=email]")).to_have_value(email)
    if late_kind != "none":
        page.evaluate("window.__lateReader.release()")
        page.wait_for_function("() => window.__lateReader.settled")
        # Drain the actual fetchJson consumer, including localization and handlers.
        page.wait_for_timeout(250)
        expect(page.locator("#discussion-reader")).not_to_be_visible()
        expect(page.locator("#discussion-reader-body")).to_be_empty()
        assert marker not in page.locator("#global-community-feed").text_content()
        expect(page.locator("#login-form input[name=email]")).to_have_value(email)
    assert "discussion=" not in page.url
