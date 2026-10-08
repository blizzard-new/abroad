"""Verify NCU source scope, host documents and life content in real Chromium."""

from pathlib import Path
import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until, sign_in_cookie, attach_session


@pytest.mark.parametrize("width", [390, 1440])
def test_ncu_content_source_pages_home_host_and_life(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator("#confirm-school").click()
    if (
        width < 700
        and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true"
    ):
        page.locator("#glass-menu-toggle").click()
    wait_until(
        page,
        "state.dashboard?.school_name === '國立中央大學' && state.dashboard.partner_universities.length === 214",
    )
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("史特拉斯堡")
    expect(page.locator("#partner-table")).to_contain_text("本期名額待公告")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    page.locator("#school-detail-view .school-data-completeness > summary").click()
    expect(page.locator("#school-data-completeness-body")).to_contain_text(
        "2 / 17 項本期已核實"
    )
    expect(page.locator("#school-data-completeness-body")).to_contain_text(
        "城市與校區位置"
    )
    expect(page.locator("#school-data-completeness-body")).to_contain_text(
        "抵達與日常交通"
    )
    expect(
        page.locator("#school-detail-view .partner-student-summary")
    ).to_contain_text("2025–26")
    expect(
        page.locator("#school-detail-view .partner-student-summary")
    ).to_contain_text("強烈建議")
    page.locator("#ncu-source-audit > summary").click()
    expect(page.locator("#ncu-source-audit-body")).to_contain_text("2027–28價格")
    expect(page.locator("#ncu-source-audit-body")).to_contain_text(
        "Factsheet_Unistra_2027-28"
    )
    home_source = (
        page.locator("#ncu-source-audit-body li")
        .filter(has_text="校內甄選文件")
        .locator("details")
        .first
    )
    home_source.locator(":scope > summary").click()
    expect(home_source.locator("pre")).to_contain_text("國際移動力")
    source = (
        page.locator("#ncu-source-audit-body > details")
        .filter(has_text="Factsheet_Unistra_2027-28")
        .first
    )
    source.locator(":scope > summary").click()
    source.locator("details > summary").last.click()
    expect(source.locator("pre").last).to_contain_text("2025")
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / f"ncu-source-{width}.png"), full_page=True)
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_contain_text("家長同意書")
    expect(page.locator("#detail-application")).to_contain_text("Learning agreement")
    expect(page.locator("#detail-application")).to_contain_text("12/11")
    page.screenshot(path=str(out / f"ncu-workflow-{width}.png"), full_page=True)
    page.locator("#detail-tab-life").click()
    expect(page.locator("#detail-life")).to_contain_text("2025–26")
    expect(page.locator("#detail-life")).to_contain_text("201–550")
    page.screenshot(path=str(out / f"ncu-life-{width}.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_ncu_grade_scale_year_exclusion_and_real_document_form(page, live_server):
    session = sign_in_cookie(live_server, school="國立中央大學")
    live_server.verify_student(session["profile"]["id"], university="國立中央大學")
    attach_session(page, live_server, session)
    enter_public_site(page, live_server, "advisor")
    expect(page.locator("#advisor-academic-score")).to_be_visible()
    expect(page.locator("#advisor-academic-rule")).to_contain_text("60分")
    expect(page.locator("#advisor-academic-rule")).to_contain_text("70分")
    assert page.evaluate(
        "homeAcademicPass({degree:'大學部',currentYear:'大三',academicScore:60})"
    )
    assert not page.evaluate(
        "homeAcademicPass({degree:'大學部',currentYear:'大五',academicScore:99})"
    )
    assert page.evaluate("homeAcademicPass({degree:'在職碩士班',academicScore:70})")
    assert not page.evaluate("homeAcademicPass({degree:'研究所',academicScore:69})")
    page.evaluate("location.hash='#application-center'")
    page.locator(
        '[data-open-application-template="exchange-application-data"]'
    ).first.click()
    expect(page.locator("#application-document-form")).to_be_visible()
    test = page.locator("#application-field-language_test")
    actual = page.locator("#application-field-language_result_date")
    assert test.evaluate("node=>node.required") and actual.evaluate(
        "node=>node.required"
    )
    assert "TOEIC（聽讀）" in test.locator("option").all_text_contents()
    expect(page.locator("#application-document-fields")).to_contain_text("實際考試日期")
    actual.fill("2100-01-01")
    assert actual.evaluate("node=>node.validity.rangeOverflow")


@pytest.mark.parametrize(
    "school,application_text,life_text,audit_text",
    [
        ("圖爾庫", "A1–C2六級", "EUR120000", "guardian joint account"),
        (
            "太原農林",
            "現連DOCX實際是已填2024–25範例",
            "60／年",
            "未複製姓名、生日、地址、證件號碼",
        ),
    ],
)
def test_ncu_new_host_forms_insurance_and_arrival_reach_mobile_ui(
    page, live_server, school, application_text, life_text, audit_text
):
    page.set_viewport_size({"width": 390, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator("#confirm-school").click()
    if page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(
        page,
        "state.dashboard?.school_name === '國立中央大學' && state.dashboard.partner_universities.length === 214",
    )
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill(school)
    expect(page.locator("#partner-table")).to_contain_text("本期名額待公告")
    page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    page.locator("#ncu-source-audit > summary").click()
    expect(page.locator("#ncu-source-audit-body")).to_contain_text(audit_text)
    if school == "太原農林":
        visual = page.locator("#ncu-source-audit-body > details").filter(has_text="TUAF2026交換program PDF").first
        expect(visual.locator(":scope > summary")).to_contain_text("1頁已視覺查核")
        source = (
            page.locator("#ncu-source-audit-body > details")
            .filter(has_text="僅必要欄位摘錄")
            .first
        )
        source.locator(":scope > summary").click()
        source.locator("details > summary").click()
        expect(source).to_contain_text("250 words")
        expect(source).to_contain_text("必要欄位摘錄（無固定PDF頁碼）")
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_contain_text("家長同意書")
    expect(page.locator("#detail-application")).to_contain_text(application_text)
    page.locator("#detail-tab-life").click()
    expect(page.locator("#detail-life")).to_contain_text(life_text)
    page.locator("#detail-life .life-official-guide > summary").click()
    insurance = (
        page.locator("#destination-official-content li")
        .filter(has_text=life_text)
        .first
    )
    expect(insurance).to_be_visible()
    insurance.scroll_into_view_if_needed()
    expect(page.locator("#detail-life")).to_contain_text(
        "4天" if school == "圖爾庫" else "24working hours"
    )
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(
        path=str(out / f"ncu-{'turku' if school == '圖爾庫' else 'tuaf'}-390.png"),
        full_page=False,
    )
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("school,source_label,old_year,life_text", [
    ("上海財經", "26-27学年_上海财经大学来校交换生信息手册.pdf PDF", "2025--2026", "1000–1500"),
    ("上海大學", "上海大学港澳台交换生申请指南.pdf PDF", "2020", "10元人民幣"),
])
def test_ncu_shanghai_visual_versions_and_life_are_visible(page, live_server, school, source_label, old_year, life_text):
    page.set_viewport_size({"width": 390, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator("#confirm-school").click()
    if page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '國立中央大學'")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill(school)
    expect(page.locator("#partner-table")).to_contain_text("本期名額待公告")
    page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    page.locator("#ncu-source-audit > summary").click()
    source = page.locator("#ncu-source-audit-body > details").filter(has_text=source_label).first
    expect(source.locator(":scope > summary")).to_contain_text("8頁已視覺查核")
    source.locator(":scope > summary").click()
    passage = source.locator(".ncu-visual-passage").filter(has_text=old_year).first
    passage.locator(":scope > summary").click()
    expect(passage.locator("pre")).to_be_visible()
    passage.scroll_into_view_if_needed()
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / f"ncu-{'sufe' if school == '上海財經' else 'shu'}-visual-390.png"))
    page.locator("#detail-tab-application").click()
    if school == "上海財經":
        expect(page.locator("#detail-application")).to_contain_text("成績管理部門公章")
        expect(page.locator("#detail-application")).to_contain_text("提名後提供模板")
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    life = page.locator("#destination-official-content li").filter(has_text=life_text).first
    expect(life).to_be_visible()
    life.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f"ncu-{'sufe' if school == '上海財經' else 'shu'}-life-390.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_ncu_uos_visual_evidence_and_conditional_housing_form_are_visible(page, live_server):
    page.set_viewport_size({"width": 390, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator("#confirm-school").click()
    if page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '國立中央大學'")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("University of Seoul")
    page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#school-detail-view .partner-student-summary")).to_contain_text("2027/3/1–4/15")
    page.locator("#ncu-source-audit > summary").click()
    old = page.locator("#ncu-source-audit-body > details").filter(has_text="UOS Partner Information_Web.pdf").first
    old.locator(":scope > summary").click()
    expect(old.locator(":scope > summary")).to_contain_text("0頁有文字")
    expect(old.locator(":scope > summary")).to_contain_text("11頁已視覺查核")
    passage = old.locator(".ncu-visual-passage").filter(has_text="原PDF第3頁")
    passage.locator(":scope > summary").click()
    expect(passage.locator("pre")).to_be_visible()
    expect(passage.locator("pre")).to_contain_text("Academic Year 2023")
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    passage.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-uos-visual-390.png"))
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_contain_text("家長同意書")
    expect(page.locator("#detail-application")).to_contain_text("核對外校錄取後與住宿行前文件")
    expect(page.locator("#detail-application")).to_contain_text("校內住宿者：英文MMR兩劑")
    expect(page.locator("#detail-application")).to_contain_text("Health & Medical Clearance Form")
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    bus = page.locator("#destination-official-content li").filter(has_text="6002").first
    expect(bus).to_be_visible()
    bus.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-uos-transport-390.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
