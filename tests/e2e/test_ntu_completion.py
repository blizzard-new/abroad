from pathlib import Path
import os

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until


@pytest.mark.parametrize("width", [390, 1440])
def test_dated_host_reference_is_readable_with_pending_home_quota(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立臺灣大學"]').click()
    page.locator("#confirm-school").click()
    if width < 700 and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '國立臺灣大學'")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("愛德華王子島大學")
    expect(page.locator("#partner-table")).to_contain_text("本期名額待核實")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    detail = page.locator("#school-detail-view")
    expect(detail).to_be_visible()
    expect(detail.locator(".partner-student-summary")).to_contain_text("2027/6/15")
    expect(detail.locator(".partner-student-summary")).to_contain_text("2027–2028")
    expect(detail.locator(".partner-student-summary")).to_contain_text("不能視為116-1最終甄選資格")
    assert page.evaluate("state.dashboard.partner_universities.find(p=>p.school_name==='愛德華王子島大學').quota") is None
    page.get_by_role("tab", name="生活情報", exact=True).click()
    expect(page.locator('[data-life-theme="cost"]')).to_contain_text("CAD1,500")
    expect(page.locator('[data-life-theme="safety"]')).to_contain_text("Guard Me")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
    output = Path(os.environ.get("VISUAL_EVIDENCE_DIR", "/tmp/ntu-completion-browser"))
    output.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output / f"upei-reference-{width}.png"))


@pytest.mark.parametrize("width", [390, 1440])
def test_field_conclusion_and_specific_missing_items_remain_visible(page, live_server, width, tmp_path):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立臺灣大學"]').click()
    page.locator("#confirm-school").click()
    if width < 700 and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '國立臺灣大學'")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("國立慶北大學")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    page.get_by_role("tab", name="生活情報", exact=True).click()
    page.locator(".life-official-guide > summary").click()
    card = page.locator(".student-guide-section-card").filter(has_text="公開資訊適用範圍與待確認事項")
    expect(card).to_contain_text("來源版本有差異")
    expect(card).to_contain_text("研究生上限9學分")
    expect(card).to_contain_text("2027–28申寮程序/截止/房價")
    expect(card).to_contain_text("不啟用截止提醒")
    card.scroll_into_view_if_needed()
    expect(card).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.evaluate("state.dashboard.partner_universities.find(p => p.school_name === '國立慶北大學').quota") is None
    output = tmp_path / "browser"
    output.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output / f"knu-field-conclusion-{width}.png"))
