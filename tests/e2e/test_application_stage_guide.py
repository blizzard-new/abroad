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


@pytest.mark.parametrize("width", [390, 1440])
def test_the_heading_tells_where_you_are_apart_from_what_to_do_next(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 960})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school', '長庚大學')")
    page.goto(f"{live_server.base_url}/#application-center")
    page.wait_for_load_state("networkidle")
    next_step = page.locator("#planning-next-action")
    # On the documents step while the recommended step is the first: the card says so instead of calling both "step N".
    expect(next_step).to_have_attribute("data-scope", "elsewhere")
    expect(next_step).to_contain_text("你在第 3 步 · 建議下一步在第 1 步「選校與確認」")
    expect(next_step).to_contain_text("從你的條件開始")
    expect(page.locator("#application-workspace-stage-summary")).to_contain_text("你在第 3 步")
    assert stage_statuses(page) == ["next", "todo", "todo"]
    expect(page.locator('#application-journey-steps [aria-current="step"]')).to_contain_text("文件與送件")
    # Nothing has been done, so no figure is shown: the plain hints stay and the count is an honest zero.
    expect(page.locator("#application-workspace-progress-count")).to_have_text("已完成 0 / 3 步")
    expect(page.locator("#application-journey-steps small[data-real=true]")).to_have_count(0)
    if width >= 701:
        expect(page.locator('[data-workspace-stage="selection"] .application-stage-flag')).to_have_text("下一步")
        expect(page.locator('[data-workspace-stage="documents"] .application-stage-flag')).to_have_text("你在這裡")
    # The pointer to another step is the quieter button; on its own step the same action is the main one.
    expect(next_step.get_by_role("link", name="填寫條件")).to_have_class("secondary-button")
    page.evaluate("location.hash='#advisor'")
    expect(next_step).to_have_attribute("data-scope", "here")
    expect(next_step).to_contain_text("第 1 步「選校與確認」· 現在先做這件事")
    expect(next_step.get_by_role("button", name="就在這一頁，開始")).to_have_class("primary-button")
    if width >= 701:
        expect(page.locator('[data-workspace-stage="selection"] .application-stage-flag')).to_have_text("你在這裡 · 下一步")
    assert_no_horizontal_scroll(page)


@pytest.mark.parametrize("width", [390, 1440])
def test_figures_on_the_steps_are_what_has_really_been_done(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 960})
    page.emulate_media(reduced_motion="reduce")
    create_target(page, live_server)
    stage = page.evaluate("planningNextAction().stage")
    done = STAGES.index(stage)
    # The count in the heading is the number of steps marked done, not a separate estimate.
    expect(page.locator("#application-workspace-progress-count")).to_have_text(f"已完成 {done} / 3 步")
    assert done == len(page.locator('#application-journey-steps [data-stage-status="done"]').all())
    # Conditions filled, target chosen and the comparison settled: all three of the first step.
    selection = page.locator('[data-workspace-stage="selection"] small')
    expect(selection).to_have_attribute("data-real", "true")
    expect(selection.locator(".stage-detail-value")).to_have_text("3 / 3")
    # Nothing is scheduled or drafted yet, so the later steps keep their plain hints.
    expect(page.locator('[data-workspace-stage="documents"] small')).to_have_text("填表、檢查、列印")
    expect(page.locator('[data-workspace-stage="documents"] small')).not_to_have_attribute("data-real", "true")
    label = page.locator('[data-workspace-stage="selection"] .stage-detail-label')
    if width >= 701:
        expect(label).to_be_visible()
    else:
        expect(label).to_be_hidden()
    # Screen readers get the figure with its words and the step's status.
    expect(page.locator("#application-stage-selection-note")).to_have_text("條件、目標、資格比對 3 / 3（已完成）")
    assert_no_horizontal_scroll(page)


def test_a_step_finished_while_here_is_announced_once_and_stays_quiet_on_return(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 960})
    page.emulate_media(reduced_motion="no-preference")
    create_target(page, live_server)
    live = page.locator("#application-workspace-progress-live")
    expect(live).to_have_text("第 1 步「選校與確認」已完成")
    circle = page.locator('[data-workspace-stage="selection"] .application-stage-number')
    expect(circle).to_have_class("application-stage-number is-just-done")
    assert page.evaluate("getComputedStyle(document.querySelector('.application-stage-number.is-just-done')).animationName") == "stage-check-pop"
    # Coming back to a step that was already done is not celebrated again.
    page.reload()
    page.wait_for_load_state("networkidle")
    page.evaluate("location.hash='#overview'")
    expect(page.locator('#application-journey-steps [data-stage-status="done"]')).to_have_count(1)
    expect(page.locator("#application-workspace-progress-live")).to_have_text("")
    expect(page.locator(".application-stage-number.is-just-done")).to_have_count(0)


def test_the_finished_step_does_not_animate_for_reduced_motion(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 960})
    page.emulate_media(reduced_motion="reduce")
    create_target(page, live_server)
    expect(page.locator("#application-workspace-progress-live")).to_have_text("第 1 步「選校與確認」已完成")
    # The announcement is the same; only the movement is dropped.
    assert page.evaluate("getComputedStyle(document.querySelector('.application-stage-number.is-just-done')).animationName") == "none"
