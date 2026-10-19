"""The 我的申請 heading tells a student where they are, what is done and the one thing to do next."""
import pytest
from playwright.sync_api import expect

from .test_glass_theme import capture
from .test_planning_workspace import create_target

STAGES = ["selection", "preparation", "documents"]


def stage_statuses(page) -> list[str]:
    return page.locator("#application-journey-steps [data-workspace-stage]").evaluate_all(
        "links => links.map(link => link.dataset.stageStatus)"
    )


def assert_no_horizontal_scroll(page) -> None:
    assert page.evaluate("Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_first_visit_shows_one_next_step_in_the_same_place_on_every_stage(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 960})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school', '長庚大學')")
    page.goto(f"{live_server.base_url}/#advisor")
    page.wait_for_load_state("networkidle")
    next_step = page.locator("#planning-next-action")
    expect(next_step).to_be_visible()
    expect(next_step).to_contain_text("從你的條件開始")
    expect(next_step).to_contain_text("第 1 步「選校與確認」")
    expect(page.locator("#application-workspace-stage-summary")).to_contain_text("第 1 步")
    assert stage_statuses(page) == ["next", "todo", "todo"]
    # One list of steps: the old three-item aside and the paused-AI notices are gone.
    expect(page.locator("#application-entry-help")).to_have_count(0)
    expect(page.locator("#ai-status-chip")).to_be_hidden()
    expect(page.locator("#ai-fallback-banner")).to_be_hidden()
    expect(page.locator("#application-workspace-tool-menu > summary")).to_contain_text("本階段其他頁面")
    # On the page the step points to, the button takes the student to the first field.
    next_step.get_by_role("button", name="就在這一頁，開始").click()
    expect(page.locator("#advisor-college")).to_be_focused()
    assert_no_horizontal_scroll(page)
    capture(page, f"guide-01-selection-{width}.png")

    page.locator('#application-journey-steps [data-workspace-stage="preparation"]').click()
    expect(page.locator("#overview")).to_be_visible()
    expect(next_step).to_contain_text("從你的條件開始")
    expect(next_step.get_by_role("link", name="填寫條件")).to_have_attribute("href", "#advisor")
    expect(next_step.get_by_role("link", name="還沒有方向？先逛交換學校")).to_have_count(0)
    expect(page.locator("#tracker-title")).to_have_text("我的準備任務")
    expect(page.locator("#tracker-add")).to_be_hidden()
    assert_no_horizontal_scroll(page)
    capture(page, f"guide-02-preparation-{width}.png")

    page.locator('#application-journey-steps [data-workspace-stage="documents"]').click()
    expect(page.locator("#application-center")).to_be_visible()
    expect(next_step).to_contain_text("從你的條件開始")
    # Without an account the shared-profile panel is hidden; the settings form takes its row instead of an empty box.
    widths = page.evaluate("""() => [document.querySelector('#application-context-form').getBoundingClientRect().width,
      document.querySelector('.application-center-setup').getBoundingClientRect().width]""")
    assert widths[0] >= widths[1] - 2
    assert_no_horizontal_scroll(page)
    capture(page, f"guide-03-documents-{width}.png")

    page.evaluate("location.hash='#calendar'")
    expect(page.locator("#calendar")).to_be_visible()
    expect(next_step).to_be_hidden()


@pytest.mark.parametrize("width", [390, 1440])
def test_finished_steps_are_checked_and_the_next_step_moves_forward(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 960})
    page.emulate_media(reduced_motion="reduce")
    create_target(page, live_server)
    next_step = page.locator("#planning-next-action")
    expect(next_step).not_to_contain_text("從你的條件開始")
    stage = page.evaluate("planningNextAction().stage")
    index = STAGES.index(stage)
    expected = ["done"] * index + ["next"] + ["todo"] * (len(STAGES) - index - 1)
    page.wait_for_function(
        "expected => [...document.querySelectorAll('#application-journey-steps [data-workspace-stage]')].map(link => link.dataset.stageStatus).join() === expected",
        arg=",".join(expected),
    )
    for done in page.locator('#application-journey-steps [data-stage-status="done"]').all():
        expect(done).to_contain_text("已完成")
    expect(next_step).to_contain_text(f"第 {index + 1} 步")
    expect(page.locator("#tracker-add")).to_be_visible()
    assert_no_horizontal_scroll(page)
    capture(page, f"guide-04-progress-{width}.png")
