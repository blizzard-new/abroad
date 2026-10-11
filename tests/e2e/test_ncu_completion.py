"""Read new host rules, original conflicts and photo credits in real Chromium."""
from pathlib import Path
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until


@pytest.mark.parametrize("query, width", [("誠信", 390), ("阿利坎特", 1280), ("東芬蘭", 390), ("符茲堡", 1280), ("巴登", 390), ("托馬斯", 1280)])
def test_ncu_new_rules_photos_and_source_limits_reach_visible_ui(page, live_server, query, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=60_000)
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator("#confirm-school").click()
    wait_until(page, "state.dashboard?.school_name === '國立中央大學'", timeout=60.0)
    if page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill(query)
    expect(page.locator("#partner-table")).to_contain_text("本期名額待公告")
    if query == "阿利坎特":
        picture = page.locator("#partner-table .school-photo img").first
        expect(picture).to_have_attribute("src", re.compile(r"/static/assets/ncu-schools/[a-f0-9]+\.jpg$"))
        wait_until(page, "document.querySelector('#partner-table .school-photo img')?.naturalWidth > 0", timeout=30.0)
    summary = page.locator("#partner-table .partner-card > summary").first
    if summary.is_visible():
        summary.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#detail-overview .partner-student-summary")).to_be_visible()
    if query == "東芬蘭":
        expect(page.locator("#detail-overview")).to_contain_text("不要求語言測驗")
        expect(page.locator("#detail-overview")).to_contain_text("同一校區")
    if query == "誠信":
        expect(page.locator("#detail-overview")).to_contain_text("官方語檢不是外校強制")
        page.locator("#ncu-source-audit > summary").click()
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("2026/5/21", timeout=60_000)
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("6月／7月")
        page.locator("#detail-tab-application").click()
        initial = page.locator("#detail-application .workflow-step").filter(has_text="核對外校當期文件並依通知申請").first
        initial.locator(":scope > summary").click()
        expect(initial.locator(".workflow-documents > li")).to_have_count(8)
        expect(initial).to_contain_text("Personal Medical Assessment")
        expect(initial).to_contain_text("只線上")
    if query == "符茲堡":
        expect(page.locator("#detail-overview")).to_contain_text("Physics只建議")
        page.locator("#detail-tab-application").click()
        initial = page.locator("#detail-application .workflow-step").filter(has_text="核對外校當期文件並依通知申請").first
        initial.locator(":scope > summary").click()
        expect(initial.locator(".workflow-documents > li")).to_have_count(5)
        expect(initial).to_contain_text("語言教師")
        expect(page.locator("#detail-application")).to_contain_text("Würzburg錄取後註冊文件")
        expect(page.locator("#detail-application")).to_contain_text("德國在台協會交換生簽證文件準備")
    if query == "巴登":
        page.locator("#ncu-source-audit > summary").click()
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("Edition September 2022", timeout=60_000)
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("Schengen")
        page.locator("#detail-tab-application").click()
        initial = page.locator("#detail-application .workflow-step").filter(has_text="核對外校當期文件並依通知申請").first
        initial.locator(":scope > summary").click()
        expect(initial.locator(".workflow-documents > li")).to_have_count(8)
    if query == "托馬斯":
        page.locator("#ncu-source-audit > summary").click()
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("host_documents仍missing", timeout=60_000)
        page.locator("#detail-tab-application").click()
        expect(page.locator("#detail-application")).to_contain_text(re.compile(r"Thomas More到校前(?:Learning Agreement|修課協議)"))
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    if query == "阿利坎特":
        expect(page.locator("#destination-official-content")).to_contain_text("€60")
        expect(page.locator("#destination-official-content")).to_contain_text("L2 tram")
        expect(page.locator(".student-guide-photo-grid figcaption").first).to_contain_text("作者：")
        expect(page.locator(".student-guide-photo-grid figcaption").first).to_contain_text("授權：")
        expect(page.locator(".student-guide-photo-grid figcaption").first).to_contain_text("116錄取校區仍待確認")
        expect(page.locator(".student-guide-photo-grid figure")).to_have_count(1)
        wait_until(page, "document.querySelector('.student-guide-photo-grid img')?.naturalWidth > 0", timeout=30.0)
    if query == "東芬蘭":
        expect(page.locator("#destination-official-content")).to_contain_text("150km")
    if query == "誠信":
        expect(page.locator("#destination-official-content")).to_contain_text("KRW80000")
    if query == "符茲堡":
        expect(page.locator("#destination-official-content")).to_contain_text("€182.10")
        expect(page.locator("#destination-official-content")).to_contain_text("Auslandsportal")
    if query == "巴登":
        expect(page.locator("#destination-official-content")).to_contain_text("沒有宿舍")
        expect(page.locator("#destination-official-content")).to_contain_text("German statutory字樣")
    if query == "托馬斯":
        expect(page.locator("#destination-official-content")).to_contain_text("不是先來先得")
        expect(page.locator("#destination-official-content")).to_contain_text("5560")
    out = Path("/workspace/ncu-completion-20261011/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.locator("#detail-life").scroll_into_view_if_needed()
    page.screenshot(path=str(out / f"ncu-{query}-{width}.png"))
    if query == "阿利坎特":
        page.locator(".student-guide-photo-grid figure").first.screenshot(path=str(out / "ncu-alicante-campus-photo-credits.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
