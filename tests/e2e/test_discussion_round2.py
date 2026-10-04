from datetime import timedelta
import re
from uuid import uuid4

import requests
from playwright.sync_api import expect

from exchange_info.models import utc_now
from .conftest import enter_public_site, login_through_web
from .test_discussion_reader import seed, search, capture


def test_reply_thread_reaction_retry_persistence_and_author_delete(page, live_server):
    marker, posts = seed(live_server)
    email = f"thread-{uuid4().hex[:8]}@example.com"
    session = live_server.register(email)
    auth = {"Authorization": f"Bearer {session['access_token']}"}
    identity = requests.post(f"{live_server.base_url}/auth/community-identity", headers=auth, timeout=10).json()
    author = {**auth, "X-Anonymous-ID": identity["id"], "X-Anonymous-Token": identity["access_token"]}
    root = requests.post(f"{live_server.base_url}/community/posts/{posts[0].id}/comments",
        headers=author, json={"body": "此為我提出的住宿申請問題。"}, timeout=10).json()
    login_through_web(page, live_server, email)
    page.locator('a[href="#public-board"]:visible').first.click()
    search(page, marker)
    page.locator(f'[data-discussion-open="{posts[0].id}"]').first.click()
    expect(page.locator(f"#discussion-comment-{root['id']}")).to_be_visible()
    calls = []
    page.on("request", lambda request: calls.append(request.url))
    page.locator(f'[data-discussion-reply="{root["id"]}"]').click()
    expect(page.locator('[data-discussion-reply-target]')).to_contain_text("正在回覆 B2")
    page.locator("#discussion-reply-body").fill("我的串內草稿，請先保存。")
    page.locator('[data-discussion-reply-cancel]').click()
    expect(page.locator("#discussion-reply-body")).to_have_value("")
    page.locator(f'[data-discussion-reply="{root["id"]}"]').click()
    expect(page.locator("#discussion-reply-body")).to_have_value("我的串內草稿，請先保存。")
    page.locator('#discussion-reader .post-comment-form button[type="submit"]').click()
    expect(page.locator(".discussion-child")).to_contain_text("我的串內草稿")
    expect(page.locator(".discussion-child")).to_contain_text("B2-1")
    page.locator(".discussion-child [data-discussion-quote]").click()
    expect(page.locator("#discussion-reply-body")).to_have_value("引用 B2-1：我的串內草稿，請先保存。\n\n")
    page.locator("#discussion-reply-body").fill("")
    page.locator(f'[data-discussion-thread="{root["id"]}"]').click()
    expect(page.locator(".discussion-child")).to_have_count(0)
    page.locator(f'[data-discussion-thread="{root["id"]}"]').click()
    expect(page.locator(".discussion-child")).to_have_count(1)
    assert any("parent_id=" + root["id"] in url for url in calls)
    helpful = page.locator('[data-discussion-react="helpful"][data-resource-type="post"]')
    thanks = page.locator('[data-discussion-react="thanks"][data-resource-type="post"]')
    path = f"**/community/post/{posts[0].id}/reaction"
    page.route(path, lambda route: route.fulfill(status=503, content_type="application/json", body='{"detail":"反應暫時無法儲存"}'))
    helpful.click()
    expect(helpful).to_be_enabled()
    expect(helpful).to_have_attribute("aria-pressed", "false")
    expect(helpful).to_contain_text("0")
    page.unroute(path)
    helpful.click()
    expect(helpful).to_have_attribute("aria-pressed", "true")
    thanks.click()
    expect(thanks).to_have_attribute("aria-pressed", "true")
    expect(helpful).to_have_attribute("aria-pressed", "false")
    expect(helpful).to_contain_text("0")
    page.reload()
    expect(thanks).to_have_attribute("aria-pressed", "true")
    page.locator(f'[data-discussion-thread="{root["id"]}"]').click()
    expect(page.locator(".discussion-child")).to_have_count(1)
    capture(page, "discussion-round2-desktop.png")
    page.set_viewport_size({"width": 390, "height": 844})
    capture(page, "discussion-round2-mobile.png")
    page.locator(f"#discussion-comment-{root['id']}").scroll_into_view_if_needed()
    capture(page, "discussion-round2-mobile-thread.png")
    page.on("dialog", lambda dialog: dialog.accept())
    page.locator(f'[data-discussion-delete="comment"][data-resource-id="{root["id"]}"]').click()
    expect(page.locator(f"#discussion-comment-{root['id']}")).to_contain_text("此留言已刪除")
    page.locator(f'[data-discussion-thread="{root["id"]}"]').click()
    expect(page.locator(".discussion-child")).to_contain_text("我的串內草稿")
    expect(page.locator("#discussion-moderation-open")).not_to_be_visible()


def test_moderator_approve_hide_report_review_and_suspend(page, live_server, monkeypatch):
    admin_email = f"mod-{uuid4().hex[:8]}@example.com"
    student_email = f"reported-{uuid4().hex[:8]}@example.com"
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", admin_email)
    live_server.register(admin_email)
    session = live_server.register(student_email)
    auth = {"Authorization": f"Bearer {session['access_token']}"}
    identity = requests.post(f"{live_server.base_url}/auth/community-identity", headers=auth, timeout=10).json()
    writer = {**auth,"X-Anonymous-ID":identity["id"],"X-Anonymous-Token":identity["access_token"]}
    title = "待查核的保證錄取討論" + uuid4().hex[:8]
    response = requests.post(f"{live_server.base_url}/community/posts", headers=writer,
        json={"board_id":"public-study-abroad","title":title,"body":"請問付費代辦宣稱保證錄取是否可信？"}, timeout=10)
    response.raise_for_status()
    pid = response.json()["id"]
    assert response.json()["status"] == "pending"
    login_through_web(page, live_server, admin_email)
    page.locator('a[href="#public-board"]:visible').first.click()
    expect(page.locator("#discussion-moderation-open")).to_be_visible()
    page.locator("#discussion-moderation-open").click()
    card = page.locator(".discussion-moderation-card").filter(has_text=title)
    card.locator('[data-moderate-id] input[name="note"]').fill("已核對為同學的詢問，並無招生招攬。")
    card.get_by_role("button", name="核准公開").click()
    expect(page.locator(".discussion-audits")).to_contain_text("已核對為同學的詢問")
    page.locator("#discussion-moderation-filter").select_option("approved")
    card = page.locator(".discussion-moderation-card").filter(has_text=title)
    card.locator("summary").click()
    card.locator('[data-suspend-identity] input[name="note"]').fill("反覆違規，先停權七天並保留紀錄。")
    card.locator('[data-suspend-identity] select').select_option("7")
    card.get_by_role("button", name="確認停權").click()
    expect(page.locator(".discussion-audits")).to_contain_text("反覆違規")
    assert requests.put(f"{live_server.base_url}/community/post/{pid}/reaction", headers=auth,
        json={"reaction":"thanks"}, timeout=10).status_code == 403
    reporter_email = f"reporter-{uuid4().hex[:8]}@example.com"
    reporter = live_server.register(reporter_email)
    reporter_auth = {"Authorization":f"Bearer {reporter['access_token']}"}
    reporter_id = requests.post(f"{live_server.base_url}/auth/community-identity", headers=reporter_auth, timeout=10).json()
    reported = requests.post(f"{live_server.base_url}/community/reports",
        headers={**reporter_auth,"X-Anonymous-ID":reporter_id["id"],"X-Anonymous-Token":reporter_id["access_token"]},
        json={"resource_type":"post","resource_id":pid,"reason":"請管理者確認這則代辦資訊。"}, timeout=10)
    reported.raise_for_status()
    page.locator("#discussion-moderation-filter").select_option("pending")
    report = page.locator(".discussion-moderation-card").filter(has=page.locator(f'[data-review-report="{reported.json()["id"]}"]'))
    report.locator('[data-moderate-id] input[name="note"]').fill("查核後決定隱藏代辦討論。")
    report.get_by_role("button", name="隱藏被檢舉內容").click()
    expect(page.locator(".discussion-audits")).to_contain_text("查核後決定隱藏")
    report.locator('[data-review-report] input[name="note"]').fill("已隱藏原文並通知內部處理。")
    report.get_by_role("button", name="標記已處理").click()
    expect(page.locator(".discussion-audits")).to_contain_text("已隱藏原文")
    assert requests.get(f"{live_server.base_url}/community/posts/{pid}", timeout=10).status_code == 404
    capture(page, "discussion-round2-moderation.png")
    page.locator("#discussion-moderation-close").click()
    expect(page.locator("#discussion-moderation")).not_to_be_visible()


def test_account_bookmarks_sync_between_two_browser_contexts_and_import_legacy(page, live_server):
    marker, posts = seed(live_server)
    email = f"saved-{uuid4().hex[:8]}@example.com"
    session = live_server.register(email)
    profile = requests.get(f"{live_server.base_url}/auth/me", headers={"Authorization":f"Bearer {session['access_token']}"}, timeout=10).json()
    cookie = {"name":"exchange_guide_session","value":session["access_token"],"url":live_server.base_url,"httpOnly":True,"sameSite":"Lax"}
    page.context.add_cookies([cookie])
    # First-round account-local favorites are imported only when the user chooses to sync.
    import json
    page.add_init_script(f"localStorage.setItem({json.dumps('uniway-discussion-saved:'+profile['id'])}, {json.dumps(json.dumps([posts[0].id]))})")
    enter_public_site(page, live_server, "public-board")
    search(page, marker)
    page.locator("#discussion-saved-filter").click()
    expect(page.locator(".discussion-summary")).to_have_count(0)
    expect(page.locator("#discussion-import-saved")).to_be_visible()
    page.locator("#discussion-import-saved").click()
    expect(page.locator(".discussion-summary")).to_have_count(1)
    expect(page.locator("#discussion-bookmark-status")).to_contain_text("登入帳號")
    second = page.context.browser.new_context(viewport={"width":390,"height":844})
    try:
        second.add_cookies([cookie])
        mobile = second.new_page()
        enter_public_site(mobile, live_server, "public-board")
        search(mobile, marker)
        mobile.locator("#discussion-saved-filter").click()
        expect(mobile.locator(".discussion-summary")).to_have_count(1)
        save = mobile.locator(f'[data-discussion-save="{posts[0].id}"]')
        expect(save).to_have_attribute("aria-pressed","true")
        path = f"**/community/posts/{posts[0].id}/bookmark"
        mobile.route(path, lambda route: route.fulfill(status=503,content_type="application/json",body='{"detail":"收藏暫時無法保存"}'))
        save.click()
        expect(save).to_have_attribute("aria-pressed","true")
        mobile.unroute(path)
        save.click()
        expect(mobile.locator(".discussion-summary")).to_have_count(0)
        page.reload()
        expect(page.locator(".discussion-summary")).to_have_count(0)
    finally:
        second.close()


def test_login_from_reader_preserves_valid_fields_while_requests_settle(page, live_server):
    marker, posts = seed(live_server)
    for _ in range(5):
        email = f"settling-{uuid4().hex[:8]}@example.com"
        live_server.register(email)
        page.context.clear_cookies()
        page.goto(live_server.base_url)
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        enter_public_site(page, live_server, "public-board")
        search(page, marker)
        page.locator(f'[data-discussion-open="{posts[0].id}"]').first.click()
        page.locator('#discussion-reader [data-open-auth]').click()
        expect(page.locator("#auth-dialog")).to_be_visible()
        page.evaluate("""() => {
          window.testLoginEvents = [];
          document.addEventListener('submit', event => { if(event.target.id === 'login-form') window.testLoginEvents.push('submit'); }, true);
          document.addEventListener('invalid', event => window.testLoginEvents.push('invalid:' + event.target.name), true);
        }""")
        page.locator('#login-form input[name="email"]').fill(email)
        page.locator('#login-form input[name="password"]').fill("CodexE2E!2026")
        try:
            with page.expect_response(lambda response: response.url == f"{live_server.base_url}/auth/login" and response.request.method == "POST", timeout=10_000) as response:
                page.locator('#login-form button[type="submit"]').click()
            assert response.value.ok
        except Exception:
            diagnostics = page.evaluate("""() => ({events:window.testLoginEvents,
              status:document.querySelector('#login-form .form-status').textContent,
              email:document.querySelector('#login-form input[name=email]').value,
              passwordLength:document.querySelector('#login-form input[name=password]').value.length,
              valid:document.querySelector('#login-form').checkValidity(),
              readerOpen:document.querySelector('#discussion-reader').open,
              authHidden:document.querySelector('#auth-dialog').hidden})""")
            raise AssertionError(diagnostics)
        expect(page.locator("#auth-dialog")).not_to_be_visible()


def test_opening_login_does_not_steal_focus_from_user_selected_field(page, live_server):
    enter_public_site(page, live_server)
    selected = page.evaluate("""() => {
      openAuthDialog();
      document.querySelector('#login-form input[name=password]').focus();
      return new Promise(resolve => setTimeout(() => resolve(document.activeElement.name), 80));
    }""")
    assert selected == "password"


def test_slow_bookmark_response_does_not_erase_new_search_text(page, live_server):
    marker, _ = seed(live_server)
    session = live_server.register(f"search-{uuid4().hex[:8]}@example.com")
    page.context.add_cookies([{"name":"exchange_guide_session","value":session["access_token"],"url":live_server.base_url,"httpOnly":True,"sameSite":"Lax"}])
    enter_public_site(page, live_server, "public-board")
    held = []
    def delay(route):
        held.append(route)
        page.evaluate("window.testBookmarkPending = true")
    page.route("**/community/bookmarks", delay, times=1)
    page.evaluate("() => { window.UniWayCommunity.load({force:true}); }")
    page.wait_for_function("window.testBookmarkPending === true")
    page.locator("#global-community-search").fill(marker)
    held[0].continue_()
    expect(page).to_have_url(re.compile("discussion_q=.*" + marker[-8:]))
    expect(page.locator("#global-community-search")).to_have_value(marker)
    expect(page.locator(".discussion-summary")).to_have_count(1)
