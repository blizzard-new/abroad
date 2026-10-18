"""One workspace retains drafts, scope and old URLs across application stages."""
import pytest
from playwright.sync_api import expect

from .conftest import expand_details
from .test_planning_workspace import create_target
from .test_glass_theme import capture


@pytest.mark.parametrize("width", [390, 1754])
def test_workspace_navigation_preserves_draft_target_and_old_routes(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    _, target = create_target(page, live_server)
    workspace = page.locator("#application-workspace")
    expect(workspace).to_be_visible()
    expect(workspace.locator("#application-workspace-context")).to_contain_text(target)
    expect(page.locator("#overview > #planning-deadline-settings")).to_have_count(1)
    page.locator("#planning-deadline-settings > summary").click()
    expect(page.locator("#planning-schedule-form")).to_be_hidden()
    workspace.get_by_role("link", name="選校與確認", exact=True).click()
    expect(workspace.locator("#advisor-form")).to_be_visible()
    expand_details(page, "#advisor-form > .advisor-more-fields:not(#advisor-qualification-fields)")
    page.locator("#advisor-question").fill("保留我的問題草稿")
    question_node = page.locator("#advisor-question").evaluate("node=>{window.workspaceDraftNode=node;return true}")
    assert question_node
    workspace.locator("#application-workspace-tool-menu > summary").click()
    workspace.get_by_role("link", name="候選與比較", exact=True).click()
    expect(workspace.locator("#favorites")).to_be_visible()
    workspace.get_by_role("link", name="當期資格與志願", exact=True).click()
    expect(workspace.locator("#eligibility")).to_be_visible()
    expect(page.locator("#eligibility-academic-year")).to_be_visible()
    page.go_back()
    expect(workspace.locator("#favorites")).to_be_visible()
    workspace.get_by_role("link", name="條件與推薦", exact=True).click()
    expect(page.locator("#advisor-question")).to_have_value("保留我的問題草稿")
    assert page.locator("#advisor-question").evaluate("node=>node===window.workspaceDraftNode")
    workspace.get_by_role("link", name="文件與送件", exact=True).click()
    expect(workspace.locator("#application-center")).to_be_visible()
    expect(page.locator("#application-target-school")).to_have_value(target)
    workspace.locator("#application-workspace-tool-menu > summary").click()
    workspace.get_by_role("link", name="檢查文件", exact=True).click()
    expect(workspace.locator("#document-check")).to_be_visible()
    workspace.get_by_role("link", name="官方說明與私人文件", exact=True).click()
    expect(workspace.locator("#documents")).to_be_visible()
    # Existing links/bookmarks still select their correct panel after reload.
    page.reload()
    expect(workspace.locator("#documents")).to_be_visible()
    expect(workspace.locator("#application-workspace-context")).to_contain_text(target)
    page.evaluate("location.hash='#home'")
    expect(workspace).to_be_hidden()
    page.evaluate("location.hash='#documents'")
    workspace.locator("#application-workspace-tool-menu > summary").click()
    expect(workspace.get_by_role("link", name="官方說明與私人文件", exact=True)).to_have_attribute("aria-current", "page")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if width > 900:
        assert workspace.bounding_box()["x"] > page.locator("#glass-navigation").bounding_box()["x"] + page.locator("#glass-navigation").bounding_box()["width"]
    assert errors == []
    capture(page, f"application-workspace-{width}.png")


@pytest.mark.parametrize("width", [390, 1754])
def test_saved_conditions_keep_application_period_when_refreshing_recommendations(page, live_server, width):
    page.set_viewport_size({"width":width,"height":956})
    page.emulate_media(reduced_motion="reduce")
    _, target = create_target(page, live_server)
    workspace = page.locator("#application-workspace")
    workspace.get_by_role("link", name="選校與確認", exact=True).click()
    page.get_by_text("更多偏好", exact=True).click()
    page.locator("#advisor-current-year").select_option("大三")
    with page.expect_response(lambda response: response.url.endswith("/advisor/plan") and response.request.method == "POST") as refreshed:
        page.locator("#advisor-submit").click()
    assert refreshed.value.ok
    expect(page.locator("#advisor-profile-status")).to_contain_text("已保存")
    workspace.locator("#application-workspace-tool-menu > summary").click()
    workspace.get_by_role("link", name="當期資格與志願", exact=True).click()
    department = page.locator("#advisor-department option").evaluate_all("rows=>rows.find(row=>row.value).value")
    page.locator("#advisor-department").select_option(department)
    page.locator("#eligibility-academic-year").select_option("116")
    page.locator("#eligibility-application-round").select_option("第一梯次")
    page.locator("#eligibility-preference-1").select_option(target)
    with page.expect_response(lambda response: response.url.endswith("/application-plan/evaluate") and response.request.method == "POST") as result:
        page.locator("#advisor-form button[type=submit]").click()
    assert result.value.ok
    expect(page.locator("#eligibility-result")).to_contain_text(target)
    workspace.get_by_role("link", name="條件與推薦", exact=True).click()
    expect(page.locator("#advisor-department")).to_have_value(department)
    expect(page.locator("#advisor-current-year")).to_have_value("大三")
    with page.expect_response(lambda response: response.url.endswith("/advisor/plan") and response.request.method == "POST") as refreshed:
        page.locator("#advisor-submit").click()
    assert refreshed.value.ok
    expect(page.locator("#advisor-profile-status")).to_contain_text("已保存")
    workspace.get_by_role("link", name="當期資格與志願", exact=True).click()
    expect(page.locator("#eligibility-academic-year")).to_have_value("116")
    expect(page.locator("#eligibility-application-round")).to_have_value("第一梯次")
    expect(page.locator("#eligibility-preference-1")).to_have_value(target)
    page.wait_for_function("() => document.querySelector('#account-workspace-sync-label').textContent==='已同步'")
    page.reload()
    expect(page.locator("#eligibility-academic-year")).to_have_value("116")
    expect(page.locator("#eligibility-application-round")).to_have_value("第一梯次")
