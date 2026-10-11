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


@pytest.mark.parametrize("query,width,initial_count,overview,life", [
    ("馬賽中央", 390, 5, "良好", "CampusFrance"),
    ("諾曼第高等", 1280, 4, "母校B2certificate", "1200€"),
    ("傳播與跨文化", 390, 5, "C1", "required"),
    ("魯昂", 1280, 0, "stronglyrecommended", "CROUS"),
    ("霍恩海姆", 390, 6, "不要求提交語言證明", "79€"),
    ("列日", 1280, 6, "HEC與Law至少B2", "2026/9/9"),
    ("威尼斯卡福", 390, 4, "English", "170€"),
    ("諾德", 1280, 5, "recommendedC1", "91014"),
])
def test_ncu_second_public_pass_documents_years_and_life_are_visible(page, live_server, query, width, initial_count, overview, life):
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
    summary = page.locator("#partner-table .partner-card > summary").first
    if summary.is_visible():
        summary.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#detail-overview .partner-student-summary")).to_be_visible()
    expect(page.locator("#detail-overview")).to_contain_text(overview)
    page.locator("#ncu-source-audit > summary").click()
    expect(page.locator("#ncu-source-audit-body")).to_contain_text("116", timeout=60_000)
    if query == "諾曼第高等":
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("4/30–5/15")
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("4/15–4/30")
    if query == "列日":
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("冬考2026錯年")
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("非正式成績也接受")
    if query == "諾德":
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("HTTP403")
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("JS渲染")
    page.locator("#detail-tab-application").click()
    initial = page.locator("#detail-application .workflow-step").filter(has_text="核對外校當期文件並依通知申請").first
    initial.locator(":scope > summary").click()
    expect(initial.locator(".workflow-documents > li")).to_have_count(initial_count)
    if query == "魯昂":
        expect(page.locator("#detail-application")).to_contain_text(re.compile(r"Rouen初次審查後(?:Learning Agreement|修課協議)"))
    if query == "諾曼第高等":
        expect(page.locator("#detail-application")).to_contain_text("錄取後HUB行政註冊")
    if query == "諾德":
        expect(page.locator("#detail-application")).to_contain_text("特定placement犯罪紀錄")
    if query == "威尼斯卡福":
        expect(page.locator("#detail-application")).to_contain_text("抵達後居留文件")
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    expect(page.locator("#destination-official-content")).to_contain_text(life)
    out = Path("/workspace/ncu-completion-20261011/browser-pass2")
    out.mkdir(parents=True, exist_ok=True)
    page.locator("#detail-life").scroll_into_view_if_needed()
    page.screenshot(path=str(out / f"ncu-pass2-{query}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("query,width,initial_count,overview,life,rid", [
    ("紐約州立大學奧斯威格分校 State", 390, 4, "Cambridge B2", "US1080", "ncu-106"),
    ("紐約州立大學奧斯威格分校（自費）", 1280, 4, "fee-paying", "10個月", "ncu-108"),
    ("夏威夷大學馬諾阿分校 University", 1280, 10, "免ELIPT門檻", "22216", "ncu-107"),
    ("夏威夷大學馬諾阿分校（自費）", 390, 10, "Postgraduate", "27340", "ncu-113"),
    ("威斯康辛大學麥迪遜", 1280, 4, "TOEIC685", "fall655", "ncu-114"),
])
def test_ncu_third_public_us_tracks_documents_and_life_reach_ui(page, live_server, query, width, initial_count, overview, life, rid):
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
    summary = page.locator("#partner-table .partner-card > summary").first
    if summary.is_visible():
        summary.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#detail-overview .partner-student-summary")).to_be_visible()
    expect(page.locator("#detail-overview")).to_contain_text(overview)
    page.locator("#ncu-source-audit > summary").click()
    expect(page.locator("#ncu-source-audit-body")).to_contain_text("116", timeout=60_000)
    if "奧斯威格" in query:
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("擁有者未授權下載")
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("earlyJanuary")
    if "夏威夷" in query:
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("舊J1與新F1")
        expect(page.locator("#ncu-source-audit-body")).to_contain_text("records office")
    page.locator("#detail-tab-application").click()
    initial = page.locator("#detail-application .workflow-step").filter(has_text="核對外校當期文件並依通知申請").first
    initial.locator(":scope > summary").click()
    expect(initial.locator(".workflow-documents > li")).to_have_count(initial_count)
    expect(page.locator("#detail-application")).to_contain_text("美國錄取後F1／J1簽證準備")
    expect(initial.locator("[data-step-rule-id]")).to_have_attribute("data-step-rule-id", rid + "-host-apply")
    if "夏威夷" in query:
        expect(initial).to_contain_text("學士文憑")
        expect(page.locator("#detail-application")).to_contain_text("Mānoa錄取後健康與保險清關")
        health = page.locator("#detail-application .workflow-step").filter(has_text="Mānoa錄取後健康與保險清關").first
        health.locator(":scope > summary").click()
        expect(health.locator(".workflow-documents > li")).to_have_count(3)
        expect(health.locator(".workflow-documents > li").filter(has_text="F1 StudentAcknowledgment（含校方保險者）")).to_be_visible()
        expect(health.locator(".workflow-documents > li").filter(has_text="F1 InsuranceProviderCertification（外部醫保）")).to_be_visible()
    if "威斯康辛" in query:
        expect(page.locator("#detail-application")).to_contain_text("VISP錄取後財力與I20申請")
        expect(page.locator("#detail-application")).to_contain_text("VISP錄取後SHIP或合格豁免")
        funding = page.locator("#detail-application .workflow-step").filter(has_text="VISP錄取後財力與I20申請").first
        funding.locator(":scope > summary").click()
        expect(funding.locator(".workflow-documents > li")).to_have_count(5)
        expect(funding.locator(".workflow-documents > li").filter(has_text="Financial Verification Form電子簽署")).to_be_visible()
        expect(funding.locator(".workflow-documents > li").filter(has_text="Personal Information Verification電子簽署")).to_be_visible()
    if "夏威夷" in query or "威斯康辛" in query:
        out = Path("/workspace/ncu-completion-20261011/browser-pass3")
        out.mkdir(parents=True, exist_ok=True)
        (health if "夏威夷" in query else funding).locator(".workflow-documents").scroll_into_view_if_needed()
        page.screenshot(path=str(out / f"ncu-pass3-workflow-{query.split()[0]}-{width}.png"))
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    expect(page.locator("#destination-official-content")).to_contain_text(life)
    out = Path("/workspace/ncu-completion-20261011/browser-pass3")
    out.mkdir(parents=True, exist_ok=True)
    page.locator("#detail-life").scroll_into_view_if_needed()
    page.screenshot(path=str(out / f"ncu-pass3-{query.split()[0]}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
