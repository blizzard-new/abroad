"""Verify NCU source scope, host documents and life content in real Chromium."""

from pathlib import Path
import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until, sign_in_cookie, attach_session


@pytest.mark.parametrize("school,life_text,source_text,filename", [
    ("南京信息工程", "中文「僅限」", "Twin Room | 2,000—2,500 CNY per year", "ncu-nuist-versions-390.png"),
    ("濟南大學", "不能住國際生宿舍", "31/10/2024", "ncu-ujn-hk-scope-390.png"),
])
def test_ncu_nuist_versions_and_ujn_hong_kong_scope_reach_visible_mobile_content(page, live_server, school, life_text, source_text, filename):
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
    source = page.locator("#ncu-source-audit-body > details").filter(has_text=source_text).first
    source.locator(":scope > summary").click()
    part = source.locator("details").filter(has_text=source_text).first
    part.locator(":scope > summary").click()
    expect(part.locator("pre")).to_be_visible()
    expect(part.locator("pre")).to_contain_text(source_text)
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_contain_text("家長同意書")
    expect(page.locator("#detail-application")).to_contain_text("待確認")
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    point = page.locator("#destination-official-content li").filter(has_text=life_text).first
    expect(point).to_be_visible()
    point.scroll_into_view_if_needed()
    expect(page.locator("#detail-life")).to_contain_text("116")
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / filename))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_ncu_tju_application_and_arrival_files_and_conversion_note_reach_mobile_ui(page, live_server):
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
    page.locator("#partner-search").fill("天津")
    expect(page.locator("#partner-table")).to_contain_text("本期名額待公告")
    page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    page.locator("#detail-tab-application").click()
    workflow = page.locator("#detail-application")
    application = workflow.locator(".workflow-step").filter(has_text="2027春臺灣參考：個人簡歷").first
    application.locator(":scope > summary").click()
    expect(application.get_by_text("2027春臺灣參考：個人簡歷", exact=False).first).to_be_visible()
    arrival = workflow.locator(".workflow-step").filter(has_text="依外校報到通知繳交到校文件").first
    arrival.locator(":scope > summary").click()
    expect(arrival).to_contain_text("來校報到後才提交，非初次host附件")
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    insurance = arrival.get_by_text("2027春臺灣參考：保險單據影本（來校報到後才提交，非初次host附件）", exact=False).first
    expect(insurance).to_be_visible()
    insurance.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-tju-arrival-390.png"))
    page.locator("#detail-tab-overview").click()
    page.locator("#ncu-source-audit > summary").click()
    source = page.locator("#ncu-source-audit-body > details").filter(has=page.locator(":scope > summary").filter(has_text="天津港澳臺申請空白表")).first
    source.locator(":scope > summary").click()
    expect(source).to_contain_text("轉為DOCX")
    expect(source).to_contain_text("固定PDF頁")
    source.locator("details > summary").first.click()
    expect(source.locator("pre").first).to_contain_text("申请人签字")
    source.locator("pre").first.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-tju-source-390.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_ncu_chd_workbook_and_tju_document_catalog_are_visible(page, live_server):
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
    page.locator("#partner-search").fill("長安")
    page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    page.locator("#ncu-source-audit > summary").click()
    source = page.locator("#ncu-source-audit-body > details").filter(has=page.locator(":scope > summary").filter(has_text="2023交換提名Excel")).first
    source.locator(":scope > summary").click()
    expect(source).to_contain_text("空白工作表另保留")
    expect(source.locator("details > summary").nth(1)).to_contain_text("sheet2.xml（無PDF頁碼）")
    source.locator("details > summary").nth(1).click()
    blank = source.locator("pre").nth(1)
    expect(blank).to_be_visible()
    expect(blank).to_contain_text("沒有非空儲存格")
    blank.scroll_into_view_if_needed()
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / "ncu-chd-workbook-390.png"))
    page.evaluate("location.hash='#application-center'")
    target = page.locator("#application-target-school")
    expect(target).to_be_visible()
    value = target.locator("option").filter(has_text="Tianjin University").first.get_attribute("value")
    target.select_option(value)
    expect(page.locator("#application-requirement-summary")).to_contain_text("0 項已確認")
    groups = page.locator("#application-requirement-list .application-requirement-group")
    host = groups.filter(has=page.locator(":scope > summary").filter(has_text="合作校申請"))
    host.locator(":scope > summary").click()
    expect(host.locator(".application-requirement-item")).to_have_count(7)
    expect(host).to_contain_text("2027春臺灣參考：個人簡歷")
    arrival = groups.filter(has=page.locator(":scope > summary").filter(has_text="抵達後"))
    arrival.locator(":scope > summary").click()
    item = arrival.locator(".application-requirement-item").filter(has_text="非初次host附件")
    expect(item).to_be_visible()
    expect(item).to_contain_text("待確認")
    item.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-tju-catalog-390.png"))
    assert page.locator("#application-requirement-list").get_by_text("下載校方正式表格", exact=True).count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


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


def test_ncu_undip_2027_pending_dates_and_ten_scoped_files_reach_mobile_ui(page, live_server):
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
    page.locator("#partner-search").fill("Universitas Diponegoro")
    page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    application_summary = page.locator("#school-detail-view .partner-summary-group").filter(has_text="合作校申請步驟")
    application_summary.locator(".partner-summary-more > summary").click()
    expect(application_summary.locator("li").filter(has_text="to be announce")).to_be_visible()
    expect(application_summary.locator("li").filter(has_text="不能套用")).to_be_visible()
    page.locator("#ncu-source-audit > summary").click()
    source = page.locator("#ncu-source-audit-body > details").filter(has=page.locator(":scope > summary").filter(has_text="UNDIP FACTSHEET for DEEP 2027")).first
    expect(source.locator(":scope > summary")).to_contain_text("3頁有文字")
    expect(source.locator(":scope > summary")).to_contain_text("1頁已視覺查核")
    source.locator(":scope > summary").click()
    source.locator("details > summary").nth(1).click()
    expect(source.locator("pre").nth(1)).to_contain_text("10 November 2026")
    source.locator("pre").nth(1).scroll_into_view_if_needed()
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / "ncu-undip-source-390.png"))
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_contain_text("英文推薦函")
    expect(page.locator("#detail-application")).to_contain_text("Visa類附件")
    expect(page.locator("#detail-application")).to_contain_text("本人簽名、姓名與日期")
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    cost = page.locator("#destination-official-content li").filter(has_text="IDR2.5000.000").first
    expect(cost).to_be_visible()
    expect(page.locator("#detail-life")).to_contain_text("Data Belum Tersedia")
    expect(page.locator("#detail-life")).to_contain_text("不能抵扣預算")
    cost.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-undip-life-390.png"))
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
    form = page.locator("#ncu-source-audit-body > details").filter(has_text="臺北韓國代表部現連Visa Application Form PDF").first
    expect(form.locator(":scope > summary")).to_contain_text("5頁有文字")
    form.locator(":scope > summary").click()
    form.locator("details > summary").last.click()
    expect(form.locator("pre").last).to_contain_text("SIGNATURE OF APPLICANT")
    form.locator("pre").last.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-uos-visa-form-390.png"))
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
    assert not errors


def test_ncu_uny_degree_history_and_empty_exchange_resources_are_visible(page, live_server):
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
    page.locator("#partner-search").fill("Universitas Negeri Yogyakarta")
    expect(page.locator("#partner-table")).to_contain_text("本期名額待公告")
    page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#school-detail-view .partner-student-summary")).to_contain_text("雙聯不是")
    page.locator("#ncu-source-audit > summary").click()
    expect(page.locator("#ncu-source-audit-body")).to_contain_text("2021")
    expect(page.locator("#ncu-source-audit-body")).to_contain_text("USD4000")
    expect(page.locator("#ncu-source-audit-body")).to_contain_text("404")
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_contain_text("家長同意書")
    expect(page.locator("#detail-application")).to_contain_text("未建立為中央交換生必繳清單")
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    housing = page.locator("#destination-official-content li").filter(has_text="沒有保險正文").first
    expect(housing).to_be_visible()
    housing.scroll_into_view_if_needed()
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / "ncu-uny-life-390.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("school,life_text,source_text,application_text,filename", [
    ("南京大學", "10元封頂", "港澳通行證掃描件", "核對外校第二階段補件", "ncu-nju-second-batch-390.png"),
    ("同濟", "統一安排校內住宿", "通行证扫描件", "台胞證／回鄉證掃描", "ncu-tongji-new-list-390.png"),
    ("復旦", "6／8人套間、2人一房", "个人境外保险单", "上海全期醫療／人身意外保單PDF", "ncu-fudan-initial-insurance-390.png"),
])
def test_ncu_new_mainland_batches_reach_visible_mobile_source_workflow_and_life(page, live_server, school, life_text, source_text, application_text, filename):
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
    source = page.locator("#ncu-source-audit-body > details").filter(has_text=source_text).first
    source.locator(":scope > summary").click()
    part = source.locator("details").filter(has_text=source_text).first
    part.locator(":scope > summary").click()
    expect(part.locator("pre")).to_be_visible()
    expect(part.locator("pre")).to_contain_text(source_text)
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    point = page.locator("#destination-official-content li").filter(has_text=life_text).first
    expect(point).to_be_visible()
    page.locator("#detail-tab-application").click()
    step = page.locator("#detail-application .workflow-step").filter(has_text=application_text).first
    step.locator(":scope > summary").click()
    content = step.get_by_text(application_text, exact=False).first
    expect(content).to_be_visible()
    expect(step).to_contain_text("待確認")
    if school == "南京大學":
        content = step.get_by_text("2027春第二批參考：醫療／意外保險證明一份", exact=False).first
        expect(content).to_be_visible()
        expect(step.get_by_text("2027春第二批參考：常規體檢表", exact=False).first).to_be_visible()
    content.scroll_into_view_if_needed()
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / filename))
    if school == "南京大學":
        expect(step).to_contain_text("11/20、早於邀請函")
        expect(step).to_contain_text("胸透必檢")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_ncu_nuist_image_packet_documents_and_taiwan_life_reach_mobile_ui(page, live_server):
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
    page.locator("#partner-search").fill("南京信息工程")
    expect(page.locator("#partner-table")).to_contain_text("本期名額待公告")
    page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    page.locator("#ncu-source-audit > summary").click()
    source = page.locator("#ncu-source-audit-body > details").filter(has=page.locator(":scope > summary").filter(has_text="南京信息工程大学2027春季学期交换学生招生")).first
    expect(source.locator(":scope > summary")).to_contain_text("0頁有文字")
    expect(source.locator(":scope > summary")).to_contain_text("8頁已視覺查核")
    source.locator(":scope > summary").click()
    passage = source.locator(".ncu-visual-passage").filter(has_text="750").first
    passage.locator(":scope > summary").click()
    expect(passage.locator("pre")).to_be_visible()
    expect(passage.locator("pre")).to_contain_text("750")
    passage.locator("pre").scroll_into_view_if_needed()
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / "ncu-nuist-2027-source-390.png"))
    page.locator("#detail-tab-application").click()
    workflow = page.locator("#detail-application .workflow-step").filter(has_text="在學證明（三個月內開立）").first
    workflow.locator(":scope > summary").click()
    proof = workflow.get_by_text("2027春港澳臺參考：在學證明（三個月內開立）", exact=False).first
    expect(proof).to_be_visible()
    expect(workflow).to_contain_text("母校交換生資訊匯總表")
    proof.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-nuist-2027-documents-390.png"))
    page.locator("#detail-tab-life").click()
    page.locator("#detail-life .life-official-guide > summary").click()
    insurance = page.locator("#destination-official-content li").filter(has_text="2027春學校為港澳臺籍交換生購買綜合醫療保險").first
    expect(insurance).to_be_visible()
    expect(page.locator("#detail-life")).to_contain_text("750 RMB/學期")
    expect(page.locator("#detail-life")).to_contain_text("完整總生活費")
    insurance.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-nuist-2027-life-390.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
