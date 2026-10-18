"""Layout regressions and dependent official department choices, using isolated accounts."""
from datetime import date, timedelta
from uuid import uuid4

import pytest
import requests
from playwright.sync_api import expect

from .conftest import login_through_web, expand_details
from .test_glass_theme import capture, verified_login
from .test_planning_workspace import create_target
from .test_web_next_phase import _auth_headers


@pytest.mark.parametrize("width", [390, 1754])
def test_matching_actions_are_readable_and_aligned(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    create_target(page, live_server)
    expand_details(page, "#application-plan-details")
    page.mouse.move(width-10, 10)
    buttons = page.locator(".planning-match-actions > :is(button,a):visible").evaluate_all("""items => items.map(el => {
      const box = el.getBoundingClientRect();
      return {height:box.height, y:box.y, width:box.width, scroll:el.scrollWidth, client:el.clientWidth};
    })""")
    capture(page, f"recommendations-refined-{width}.png")
    assert all(button["height"] >= 40 and button["width"] >= 80 for button in buttons), buttons
    assert all(button["scroll"] <= button["client"] for button in buttons)
    assert all(abs(buttons[index]["y"] - buttons[index+1]["y"]) < 1 for index in range(0,len(buttons),2))
    if width == 1754:
        groups = page.locator('#recommended-match-list .match-group').evaluate_all("""groups=>groups.map(group=>
          [...group.querySelectorAll('.planning-match-actions')].filter(el=>el.getClientRects().length && !el.closest('details:not([open])'))
            .map(el=>el.getBoundingClientRect().y))""")
        assert all(not rows or max(rows)-min(rows) < 1 for rows in groups)
    capture(page, f"recommendations-refined-{width}.png")
    page.evaluate("location.hash='#advisor'")
    expect(page.locator(".advisor-school-card").first).to_be_visible()
    geometry = page.locator(".advisor-school-card:visible").evaluate_all("""cards => cards.map(card=> {
      const bounds=card.getBoundingClientRect();
      return [...card.querySelectorAll('button')].every(button=> {
        const box=button.getBoundingClientRect();
        return box.width>=80 && box.height>=40 && box.right<=bounds.right && box.left>=bounds.left && button.scrollWidth<=button.clientWidth;
      });
    })""")
    assert all(geometry)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    capture(page, f"advisor-refined-{width}.png")


@pytest.mark.parametrize("width", [390, 1754])
def test_calendar_appears_first_and_tools_still_work(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    session = verified_login(page, live_server)
    # Test today's reminder without assuming the account's default reminder schedule.
    response = requests.patch(f"{live_server.base_url}/auth/me", headers=_auth_headers(session), json={"notification_preferences": {"web_enabled": True, "deadline_reminder_days": [0]}})
    assert response.ok, response.text
    page.reload()
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=30_000)
    page.evaluate("location.hash='#calendar'")
    expect(page.locator(".calendar-day")).to_have_count(42)
    expect(page.locator("#catalogue-source-status")).to_be_hidden()
    capture(page, f"calendar-initial-{width}.png")
    month = page.locator(".calendar-month-panel").bounding_box()
    # The whole month, including its last row, must fit in the initial viewport.
    assert month["y"] + month["height"] <= page.viewport_size["height"]
    expect(page.locator("#deadline-reminder-center")).to_be_hidden()
    page.locator("#calendar-next-month").click()
    page.locator("#calendar-today").click()
    page.locator('[data-calendar-panel=".calendar-quick-add"]').click()
    page.locator('#calendar-event-form input[name="title"]').fill("準備英文讀書計畫")
    page.locator('#calendar-event-form input[name="date"]').fill(date.today().isoformat())
    page.locator('#calendar-event-form input[name="preparation_days"]').fill("0")
    page.locator('#calendar-event-form button[type="submit"]').click()
    expect(page.locator("#calendar-alert-brief")).to_contain_text("截止提醒")
    page.locator('#calendar-alert-brief button').click()
    expect(page.locator("#deadline-reminder-center")).to_contain_text("準備英文讀書計畫")
    page.locator("#calendar-insights > summary").click()
    page.locator("#calendar-sync-button").click()
    expect(page.locator("#calendar-sync-status")).to_be_visible()
    page.locator("#calendar-sync-panel > summary").click()
    page.locator("#calendar-today").click()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    capture(page, f"calendar-refined-{width}.png")


@pytest.mark.parametrize("university,college,department,other", [
    ("國立臺北大學", "法律學院", "法律學系", "商學院"),
    ("長庚大學", "工學院", "資訊工程學系", "醫學院"),
])
def test_department_follows_college_and_saved_profile(page, live_server, university, college, department, other):
    email=f"academic-{uuid4().hex[:8]}@example.com"
    session=live_server.register(email)
    live_server.verify_student(session["profile"]["id"], university=university, department=department)
    login_through_web(page, live_server, email)
    page.evaluate("location.hash='#advisor'")
    page.locator("#advisor-college").select_option(college)
    page.locator("#advisor-department").select_option(department)
    page.locator("#advisor-degree").select_option("大學部")
    expand_details(page, "#advisor-qualification-fields")
    page.locator("#advisor-academic-score").fill("85")
    page.locator("#advisor-language-test").select_option("ielts")
    page.locator("#advisor-language-score").fill("7")
    with page.expect_response(lambda response: response.url.endswith('/advisor/plan') and response.request.method=='POST') as result:
        page.locator("#advisor-submit").click()
    assert result.value.ok
    expect(page.locator("#advisor-profile-status")).to_have_text("已保存條件")
    page.reload()
    expect(page.locator("#advisor-department")).to_have_value(department)
    page.evaluate("location.hash='#eligibility'")
    expect(page.locator("#advisor-department")).to_have_value(department)
    page.locator("#advisor-college").select_option(other)
    # A late workspace response must not replace the student's in-progress selection.
    page.evaluate("renderAccountWorkspaceState()")
    expect(page.locator("#advisor-college")).to_have_value(other)
    expect(page.locator("#advisor-department")).to_have_value("")
    assert department not in page.locator("#advisor-department option").all_text_contents()
    page.locator("#advisor-college").select_option("")
    expect(page.locator("#advisor-department")).to_be_disabled()
    page.locator("#advisor-college").select_option(college)
    expect(page.locator("#advisor-department")).to_be_enabled()
    assert department in page.locator("#advisor-department option").all_text_contents()
    capture(page, f"department-refined-{university}.png")
    page.locator("#account-button").click()
    page.locator("#logout-button").click()
    expect(page.locator("#advisor-department")).to_have_value("")
    expect(page.locator("#advisor-department")).to_be_disabled()


def test_calendar_preparation_and_completion_through_tools(page, live_server):
    create_target(page, live_server)
    page.evaluate("location.hash='#calendar'")
    page.locator('[data-calendar-panel=".calendar-quick-add"]').click()
    title = "整合準備時程驗證"
    deadline = date.today() + timedelta(days=12)
    page.locator('#calendar-event-form input[name="title"]').fill(title)
    page.locator('#calendar-event-form input[name="date"]').fill(deadline.isoformat())
    page.locator('#calendar-event-form input[name="preparation_days"]').fill("12")
    page.locator('#calendar-event-form button[type="submit"]').click()
    page.locator('[data-calendar-panel="#calendar-insights"]').first.click()
    schedule = page.locator("#calendar-task-schedule-list")
    expect(schedule).to_contain_text(title, timeout=15000)
    page.locator(f'[data-calendar-task-date="{date.today().isoformat()}"]').first.click()
    expect(page.locator("#calendar-agenda-list")).to_contain_text(f"開始準備：{title}")
    page.locator(f'[data-calendar-task-deadline="{deadline.isoformat()}"]').first.click()
    task = page.locator("#calendar-agenda-list .calendar-agenda-item").filter(has_text=title)
    task.locator("[data-calendar-task-status]").select_option("ready")
    expect(schedule).to_contain_text("已完成", timeout=15000)
    page.locator(f'[data-calendar-task-date="{date.today().isoformat()}"]').first.click()
    expect(page.locator("#calendar-agenda-list")).not_to_contain_text(f"開始準備：{title}")
