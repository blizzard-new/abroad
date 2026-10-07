"""The 用戶評價 page: leave a message, be told what happened, and the administrator reads it in the inbox."""
import json
import re
from uuid import uuid4

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, login_through_web

SCHOOL = "長庚大學"


def start(page, live_server, route="feedback"):
    page.add_init_script(f"localStorage.setItem('exchange-guide-home-school', '{SCHOOL}')")
    enter_public_site(page, live_server, route)
    page.wait_for_function("() => document.querySelector('#boot-splash') === null", timeout=60_000)


def fill(page, text="希望學校搜尋可以直接比較學費，這樣比較方便。"):
    page.locator("#feedback-message").fill(text)


def test_the_menu_has_a_user_reviews_entry_that_opens_the_page(page, live_server):
    start(page, live_server, "home")
    entry = page.locator('.uniway-public-nav a[data-public-route="feedback"]')
    expect(entry).to_have_text("用戶評價")
    entry.click()
    expect(page).to_have_url(re.compile(r"#feedback$"))
    expect(page.locator("#feedback")).to_be_visible()
    expect(page.locator("#feedback-title")).to_be_focused()
    expect(entry).to_have_attribute("aria-current", "page")
    expect(page).to_have_title("用戶評價 | UniWay")
    expect(page.locator("#guide")).to_be_hidden()


def test_a_message_that_is_too_short_is_not_sent(page, live_server):
    start(page, live_server)
    sent = []
    page.on("request", lambda request: sent.append(request.url) if request.url.endswith("/feedback") else None)
    fill(page, "好")
    page.locator("#feedback-submit").click()
    expect(page.locator("#feedback-status")).to_contain_text("請至少寫 5 個字")
    expect(page.locator("#feedback-message")).to_be_focused()
    assert sent == []


def test_the_counter_the_stars_and_the_clear_button_work(page, live_server):
    page.emulate_media(reduced_motion="reduce")  # colours change at once instead of fading
    start(page, live_server)
    fill(page, "一二三四五六七八")
    expect(page.locator("#feedback-count")).to_have_text("8 / 2000")
    expect(page.locator("#feedback-clear-rating")).to_be_hidden()
    page.locator('label[for="feedback-star-4"]').click()
    assert page.evaluate("document.querySelector('#feedback-star-4').checked")
    expect(page.locator("#feedback-clear-rating")).to_be_visible()
    page.locator("#feedback-clear-rating").click()
    assert page.evaluate("document.querySelectorAll('#feedback-form input[name=rating]:checked').length") == 0
    # three stars: the first three are lit, the last two are not
    page.locator('label[for="feedback-star-3"]').click()
    page.mouse.move(5, 5)
    colours = page.evaluate("[1, 2, 3, 4, 5].map(n => getComputedStyle(document.querySelector('label[for=feedback-star-' + n + ']')).color)")
    assert len(set(colours[:3])) == 1 and colours[3] == colours[4] and colours[0] != colours[3], colours


def test_sending_a_message_thanks_the_visitor_and_sends_what_was_typed(page, live_server):
    start(page, live_server, "partners")
    page.locator('.uniway-public-nav a[data-public-route="feedback"]').click()
    page.locator('#feedback-form label:has-text("問題回報")').click()
    page.locator('label[for="feedback-star-4"]').click()
    fill(page, "手機上的篩選按鈕有點小，不太好按。")
    page.locator('#feedback-form input[name="contact"]').fill("student@example.com")
    with page.expect_request(lambda request: request.url.endswith("/feedback") and request.method == "POST") as sent:
        page.locator("#feedback-submit").click()
    body = json.loads(sent.value.post_data)
    assert body == {
        "kind": "bug", "rating": 4, "message": "手機上的篩選按鈕有點小，不太好按。", "contact": "student@example.com",
        "website": "", "route": "partners", "home_school": SCHOOL,
    }
    expect(page.locator("#feedback-thanks")).to_be_visible()
    expect(page.locator("#feedback-form")).to_be_hidden()
    expect(page.locator("#feedback-thanks h2")).to_be_focused()
    page.locator("#feedback-again").click()
    expect(page.locator("#feedback-form")).to_be_visible()
    expect(page.locator("#feedback-message")).to_have_value("")
    expect(page.locator("#feedback-message")).to_be_focused()


@pytest.mark.parametrize("status,body,message", [
    (429, "{}", "送出得太頻繁了"),
    (503, "{}", "暫時無法送出"),
    (422, '{"detail": "請不要在內容裡放太多連結。"}', "請不要在內容裡放太多連結。"),
    (422, '{"detail": [{"msg": "too short"}]}', "內容的格式不符"),
])
def test_when_sending_fails_the_visitor_is_told_why_and_keeps_what_was_typed(page, live_server, status, body, message):
    start(page, live_server)
    page.route("**/feedback", lambda route: route.fulfill(status=status, content_type="application/json", body=body))
    fill(page, "這是一則寫得很用心的長留言，不能因為送出失敗就不見。")
    page.locator("#feedback-submit").click()
    expect(page.locator("#feedback-status")).to_contain_text(message)
    expect(page.locator("#feedback-status")).to_have_class(re.compile("is-error"))
    expect(page.locator("#feedback-message")).to_have_value("這是一則寫得很用心的長留言，不能因為送出失敗就不見。")
    expect(page.locator("#feedback-submit")).to_be_enabled()
    expect(page.locator("#feedback-thanks")).to_be_hidden()


def test_the_network_going_away_does_not_lose_the_text(page, live_server):
    start(page, live_server)
    page.route("**/feedback", lambda route: route.abort())
    fill(page, "斷線的時候也不要把寫好的內容弄丟。")
    page.locator("#feedback-submit").click()
    expect(page.locator("#feedback-status")).to_contain_text("暫時無法送出")
    expect(page.locator("#feedback-message")).to_have_value("斷線的時候也不要把寫好的內容弄丟。")


def test_the_hidden_field_for_bots_cannot_be_reached_by_a_person(page, live_server):
    start(page, live_server)
    trap = page.locator('#feedback-form input[name="website"]')
    assert trap.get_attribute("tabindex") == "-1" and trap.evaluate("el => el.closest('[aria-hidden=true]') !== null")
    box = trap.evaluate("el => { const r = el.getBoundingClientRect(); return [r.right, r.bottom]; }")
    assert box[0] <= 0 or box[1] <= 0, "off the screen"


@pytest.mark.parametrize("width", [320, 390, 1280])
def test_the_page_fits_every_screen_with_big_enough_targets(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 800})
    start(page, live_server)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    for selector in ("#feedback-submit", 'label[for="feedback-star-1"]', '#feedback-form label:has-text("建議") span'):
        box = page.locator(selector).first.bounding_box()
        assert box["height"] >= 44, (selector, box)
    mascot = page.locator(".feedback-mascot").bounding_box()
    title = page.locator("#feedback-title").bounding_box()
    overlap_x = min(mascot["x"] + mascot["width"], title["x"] + title["width"]) - max(mascot["x"], title["x"])
    overlap_y = min(mascot["y"] + mascot["height"], title["y"] + title["height"]) - max(mascot["y"], title["y"])
    assert not (overlap_x > 4 and overlap_y > 4)


def test_the_administrator_reads_the_message_in_the_inbox_and_marks_it_done(page, live_server, monkeypatch):
    admin_email = f"owner-{uuid4().hex[:8]}@example.com"
    live_server.register(admin_email)
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", admin_email)
    text = f"收件匣測試留言 {uuid4().hex[:6]}：希望加入宿舍資訊。"
    start(page, live_server)
    page.locator('#feedback-form label:has-text("建議")').click()
    fill(page, text)
    page.locator("#feedback-submit").click()
    expect(page.locator("#feedback-thanks")).to_be_visible()

    login_through_web(page, live_server, admin_email)
    page.goto(f"{live_server.base_url}/admin/feedback")
    item = page.locator(".feedback-item", has_text=text)
    expect(item).to_be_visible()
    expect(item).to_contain_text("建議")
    expect(item).to_contain_text("未登入")
    expect(item).to_contain_text(SCHOOL)
    expect(item).to_have_attribute("data-status", "new")
    expect(page.locator("#kpis")).to_contain_text("新的")
    item.locator("select").select_option("done")
    item.locator("input").fill("已排進下一版")
    item.get_by_role("button", name="儲存").click()
    expect(item.locator(".feedback-saved")).to_have_text("已儲存")
    expect(item).to_have_attribute("data-status", "done")
    page.reload()
    again = page.locator(".feedback-item", has_text=text)
    expect(again).to_have_attribute("data-status", "done")
    expect(again.locator("input")).to_have_value("已排進下一版")
    page.locator("#status-filter").select_option("new")
    expect(page.locator(".feedback-item", has_text=text)).to_have_count(0)


def test_an_ordinary_student_cannot_open_the_inbox(page, live_server, monkeypatch):
    student = f"student-{uuid4().hex[:8]}@example.com"
    live_server.register(student)
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", f"someone-else-{uuid4().hex[:6]}@example.com")
    login_through_web(page, live_server, student)
    page.goto(f"{live_server.base_url}/admin/feedback")
    expect(page.locator("#status")).to_contain_text("沒有管理員權限")
    assert page.locator(".feedback-item").count() == 0


def test_a_message_written_in_markup_is_shown_as_plain_text_in_the_inbox(page, live_server, monkeypatch):
    admin_email = f"owner-{uuid4().hex[:8]}@example.com"
    live_server.register(admin_email)
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", admin_email)
    start(page, live_server)
    fill(page, '<img src=x onerror="window.pwned=1"> <b>粗體</b> 的測試留言')
    page.locator("#feedback-submit").click()
    expect(page.locator("#feedback-thanks")).to_be_visible()
    login_through_web(page, live_server, admin_email)
    page.goto(f"{live_server.base_url}/admin/feedback")
    item = page.locator(".feedback-item", has_text="粗體")
    expect(item).to_be_visible()
    expect(item.locator(".feedback-message")).to_contain_text('<img src=x onerror="window.pwned=1"> <b>粗體</b>')
    assert item.locator("img, b").count() == 0
    assert page.evaluate("window.pwned") is None
