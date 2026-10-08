"""Verify NCU source scope, host documents and life content in real Chromium."""

from pathlib import Path
import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until, sign_in_cookie, attach_session


def test_ncu_hiroshima_fee_image_coe_and_departure_stages_reach_mobile_ui(page,live_server):
    page.set_viewport_size({'width':390,'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    enter_public_site(page,live_server,'partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page)
    page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator('#confirm-school').click()
    wait_until(page,"state.dashboard?.school_name === '國立中央大學'",timeout=60.0)
    if page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':
        page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill('廣島')
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    degree=page.locator('#detail-overview .partner-student-summary li').filter(has_text='中央115表另限大學部').first
    expect(degree).to_be_visible()
    page.locator('#ncu-source-audit > summary').click()
    fee=page.locator('#ncu-source-audit-body > details').filter(has_text='2026/7現行費表原圖').first
    expect(fee.locator(':scope > summary')).to_contain_text('1張原文圖片已視覺查核')
    fee.locator(':scope > summary').click()
    part=fee.locator('details').first
    expect(part.locator(':scope > summary')).to_contain_text('原文圖片 1（無PDF頁碼）')
    part.locator(':scope > summary').click()
    expect(part.locator('pre')).to_be_visible()
    expect(part.locator('pre')).to_contain_text('3,120')
    expect(part.locator('pre')).to_contain_text('印度')
    out=Path('/tmp/ncu-audit/browser');out.mkdir(parents=True,exist_ok=True)
    part.locator('pre').scroll_into_view_if_needed()
    page.screenshot(path=str(out/'ncu-hiroshima-fee-image-390.png'))
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    expect(page.locator('#destination-official-content li').filter(has_text='單次3120TWD').first).to_be_visible()
    page.locator('#detail-tab-application').click()
    initial=page.locator('#detail-application .workflow-step').filter(has_text='HUSA現連參考：特別聽講學生申請表').first
    initial.locator(':scope > summary').click()
    expect(initial.locator('.workflow-documents > li')).to_have_count(8)
    expect(initial).to_contain_text('學生及母校承辦皆檢核及簽名')
    coe=page.locator('#detail-application .workflow-step').filter(has_text='錄取後依外校邀請辦理COE與財力證明').first
    coe.locator(':scope > summary').click()
    bank=coe.get_by_text('錄取後COE參考：銀行存款證明',exact=False).first
    expect(bank).to_be_visible();expect(coe).to_contain_text('480000')
    expect(coe).to_contain_text('待確認')
    bank.scroll_into_view_if_needed()
    page.screenshot(path=str(out/'ncu-hiroshima-coe-stage-390.png'))
    departure=page.locator('#detail-application .workflow-step').filter(has_text='如入住池之上，提前一個月提交退居屆並安排點檢').first
    departure.locator(':scope > summary').click()
    form=departure.get_by_text('如入住池之上：退居屆',exact=False).first
    expect(form).to_be_visible();expect(departure).to_contain_text('先確認點檢日')
    expect(departure.locator('.workflow-documents > li.needs-confirmation')).to_contain_text('待官方確認')
    expect(departure).to_contain_text('個人住處仍需核')
    form.scroll_into_view_if_needed()
    page.screenshot(path=str(out/'ncu-hiroshima-departure-stage-390.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors


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
    ("北京師範", "60–80 RMB／天／人", "最低6学分", "近期藍／白底JPEG照", "ncu-bnu-slides-workflow-390.png"),
    ("東南大學", "床品先自備", "無須接機服務者", "先由兩校確認體檢對等互免", "ncu-seu-reciprocal-health-390.png"),
    ("浙江大學", "宿位緊張可能跨校區", "保险单扫描件可待收到入学通知后再提交", "可錄取後補，亦可先備", "ncu-zju-insurance-later-390.png"),
    ("重慶大學", "不一定能提供校內宿舍", "2026年10月30日", "最晚開學報到提供", "ncu-cqu-latest-registration-390.png"),
    ("廈門", "漳州3設計類", "Statement of Health Condition", "健康狀況聲明（實際DOCX", "ncu-xmu-health-docx-390.png"),
    ("西南大學", "不能替PG2人房填同價", "第三頁", "藝術等专业作品集", "ncu-swu-major-portfolio-390.png"),
    ("華中師範", "房型不保证", "最近 6个月内体检报告", "到校後交，行前購買", "ncu-ccnu-arrival-insurance-390.png"),
    ("北京郵電", "不帶淋浴", "二寸藍底", "藍底／白底版本差異待確認", "ncu-bupt-photo-conflict-390.png"),
    ("華南理工", "600–1500", "申請文件電子檔", "空白附表未取得", "ncu-scut-missing-blank-form-390.png"),
    ("廣西大學", "普通疾病不賠", "每年 3 月至次年 7 月", "指定意外醫療保險", "ncu-gxu-local-accident-insurance-390.png"),
])
def test_ncu_new_mainland_batches_reach_visible_mobile_source_workflow_and_life(page, live_server, school, life_text, source_text, application_text, filename):
    page.set_viewport_size({"width": 390, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=60_000)
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator("#confirm-school").click()
    if page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '國立中央大學'", timeout=60.0)
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
    if school == "北京師範":
        expect(part.locator(":scope > summary")).to_contain_text("原文投影片 3（無PDF頁碼）")
    if school == "廈門":
        image_source = page.locator("#ncu-source-audit-body > details").filter(has=page.locator(":scope > summary").filter(has_text="2027國際生en_ba目錄原文圖片")).first
        expect(image_source.locator(":scope > summary")).to_contain_text("1張原文圖片已視覺查核")
        image_source.locator(":scope > summary").click()
        image_part = image_source.locator("details").first
        expect(image_part.locator(":scope > summary")).to_contain_text("原文圖片 1（無PDF頁碼）")
        image_part.locator(":scope > summary").click()
        expect(image_part.locator("pre")).to_contain_text("漳州校区")
        image_part.locator("pre").scroll_into_view_if_needed()
        out = Path("/tmp/ncu-audit/browser")
        out.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out / "ncu-xmu-2027-image-390.png"))
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


def test_ncu_housing_and_admission_conditions_are_visible_saved_and_period_scoped(page, live_server):
    session = sign_in_cookie(live_server, school="國立中央大學")
    live_server.verify_student(session["profile"]["id"], university="國立中央大學")
    attach_session(page, live_server, session)
    page.set_viewport_size({"width": 390, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "application-center")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=60_000)
    wait_until(page, "state.dashboard?.school_name === '國立中央大學' && !state.applicationLoading && state.accountWorkspaceLoadingCount === 0")
    target = page.locator("#application-target-school")
    expect(target).to_be_visible()
    value = target.locator("option").filter(has_text="University of Seoul").first.get_attribute("value")
    target.select_option(value)
    expect(page.locator("#ncu-document-state")).to_be_visible()
    panel = page.locator("#application-requirement-list .application-requirement-group").filter(has=page.locator(":scope > summary").filter(has_text="行前準備"))
    panel.locator(":scope > summary").click()
    expect(panel.locator('[data-document-applicability="needs_confirmation"]')).to_have_count(2)
    page.locator("#ncu-host-admission").select_option("not_accepted")
    panel.locator(":scope > summary").click()
    expect(panel.locator('[data-document-applicability="deferred"]')).to_have_count(2)
    page.locator("#ncu-host-admission").select_option("accepted")
    page.locator("#ncu-housing-choice").select_option("on_campus")
    expect(page.locator('#application-requirement-list [data-document-applicability="applicable"]')).to_have_count(2)
    page.locator("#ncu-housing-choice").select_option("off_campus")
    expect(page.locator('#application-requirement-list [data-document-applicability="not_applicable"]')).to_have_count(2)
    panel.locator(":scope > summary").click()
    condition = panel.locator('[data-document-applicability="not_applicable"]').first
    expect(condition).to_be_visible()
    expect(condition).to_contain_text("116當期來源適用性仍待核實")
    condition.scroll_into_view_if_needed()
    out = Path("/tmp/ncu-audit/browser")
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / "ncu-uos-off-campus-390.png"))
    wait_until(page, "document.querySelector('#account-workspace-sync-label').textContent === '已同步'")
    import requests
    saved = requests.get(f"{live_server.base_url}/account/workspace",headers={"Authorization":f"Bearer {session['access_token']}"},params={"home_school":"國立中央大學"},timeout=10).json()["workspace"]
    assert any(row == {"host_admission_status":"accepted","housing_choice":"off_campus"} for row in saved["application_context"]["partner_document_states"].values())
    page.reload()
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=60_000)
    expect(page.locator("#ncu-host-admission")).to_have_value("accepted")
    expect(page.locator("#ncu-housing-choice")).to_have_value("off_campus")
    form = page.locator("#application-context-form")
    form.locator('[name="semester"]').select_option("第二學期")
    expect(page.locator("#ncu-host-admission")).to_have_value("unknown")
    expect(page.locator("#ncu-housing-choice")).to_have_value("unknown")
    expect(page.locator('#application-requirement-list [data-document-applicability="needs_confirmation"]')).to_have_count(2)
    # Changing host requires the existing target-change dialog; use its normal action.
    hust = target.locator("option").filter(has_text="Huazhong University").first.get_attribute("value")
    target.select_option(hust)
    expect(page.locator("#planning-target-change-dialog")).to_be_visible()
    page.locator('#planning-target-change-dialog [value="confirm"]').click()
    expect(page.locator('#application-requirement-list [data-document-applicability="needs_confirmation"]')).to_have_count(1)
    page.locator("#ncu-host-admission").select_option("not_accepted")
    expect(page.locator('#application-requirement-list [data-document-applicability="deferred"]')).to_have_count(1)
    panel.locator(":scope > summary").click()
    deferred = panel.locator('[data-document-applicability="deferred"]')
    expect(deferred).to_be_visible()
    expect(deferred).to_contain_text("近三月健康報告")
    deferred.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-hust-deferred-health-390.png"))
    assert page.locator("#application-requirement-list").get_by_text("下載校方正式表格", exact=True).count() == 0
    page.evaluate("location.hash='#overview'")
    expect(page.locator("#multi-plan-workspace")).to_be_visible()
    page.locator("#multi-plan-settings > summary").click()
    selects = page.locator("#multi-plan-preferences select")
    selects.nth(0).select_option(value)
    selects.nth(1).select_option(hust)
    page.locator("#multi-plan-preferences button").click()
    expect(page.locator("#multi-plan-status")).to_contain_text("2 個志願")
    branch = page.locator(".multi-plan-branch").filter(has=page.locator(":scope > summary").filter(has_text="Huazhong University"))
    branch.locator(":scope > summary").click()
    health = branch.locator('[data-document-applicability="deferred"]')
    expect(health).to_be_visible()
    expect(health).to_contain_text("錄取後再準備")
    expect(branch).to_contain_text("116當期來源適用性仍待核實")
    health.scroll_into_view_if_needed()
    page.screenshot(path=str(out / "ncu-hust-deferred-task-390.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("school,phase,document,filename", [
    ("Xian Jiaotong University", "甄選與提名", "母校填送推薦學生交換信息匯總Excel（學生不用自行代填）", "ncu-xjtu-mother-nomination-390.png"),
    ("Huazhong University", "行前準備", "境外保單證明（行前購買；電子版寄送或到校繳交擇一）", "ncu-hust-insurance-alternatives-390.png"),
])
def test_ncu_mother_nomination_and_insurance_alternatives_are_visible_catalog_items(page, live_server, school, phase, document, filename):
    session = sign_in_cookie(live_server, school="國立中央大學")
    live_server.verify_student(session["profile"]["id"], university="國立中央大學")
    attach_session(page, live_server, session)
    page.set_viewport_size({"width":390,"height":956})
    page.emulate_media(reduced_motion="reduce")
    errors=[]
    page.on("pageerror",lambda error:errors.append(str(error)))
    enter_public_site(page,live_server,"application-center")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=60_000)
    wait_until(page,"state.dashboard?.school_name === '國立中央大學' && !state.applicationLoading && state.accountWorkspaceLoadingCount === 0")
    target=page.locator("#application-target-school")
    target.select_option(target.locator("option").filter(has_text=school).first.get_attribute("value"))
    group=page.locator("#application-requirement-list .application-requirement-group").filter(has=page.locator(":scope > summary").filter(has_text=phase))
    group.locator(":scope > summary").click()
    item=group.locator(".application-requirement-item").filter(has_text=document)
    expect(item).to_have_count(1)
    expect(item).to_be_visible()
    expect(item).to_contain_text("Spring2027")
    expect(item).to_contain_text("待確認")
    expect(item).not_to_contain_text("官方表格")
    if "Jiaotong" in school:
        expect(item).to_contain_text("由母校填送")
        expect(item).to_contain_text("學生不用自行代填")
    else:
        expect(item).to_contain_text("行前購買")
        expect(item).to_contain_text("電子版寄送或到校繳交擇一")
    item.scroll_into_view_if_needed()
    out=Path("/tmp/ncu-audit/browser");out.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(out/filename))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("school,phase,text,filename", [
    ("Southeast University","合作校申請","健康檢查表（須先由兩校確認對等互免）","ncu-seu-health-condition-catalog-390.png"),
    ("Zhejiang University","合作校申請","交换", "ncu-zju-form-alternatives-catalog-390.png"),
    ("SOUTHWEST UNIVERSITY","合作校申請","作品集", "ncu-swu-portfolio-condition-catalog-390.png"),
])
def test_ncu_seu_condition_and_zju_alternative_forms_are_visible_in_document_center(page,live_server,school,phase,text,filename):
    session=sign_in_cookie(live_server,school="國立中央大學")
    live_server.verify_student(session["profile"]["id"],university="國立中央大學")
    attach_session(page,live_server,session)
    page.set_viewport_size({"width":390,"height":956})
    page.emulate_media(reduced_motion="reduce")
    errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
    enter_public_site(page,live_server,"application-center")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=60_000)
    wait_until(page,"state.dashboard?.school_name === '國立中央大學' && !state.applicationLoading && state.accountWorkspaceLoadingCount === 0")
    target=page.locator("#application-target-school")
    target.select_option(target.locator("option").filter(has_text=school).first.get_attribute("value"))
    group=page.locator("#application-requirement-list .application-requirement-group").filter(has=page.locator(":scope > summary").filter(has_text=phase))
    group.locator(":scope > summary").click()
    if school == "Southeast University":
        item=group.locator(".application-requirement-item").filter(has_text=text)
        expect(item).to_have_count(1)
        expect(item.locator('[data-document-applicability="needs_confirmation"]')).to_be_visible()
        expect(item).to_contain_text("不由學生自行豁免")
        expect(item).to_contain_text("未標年度")
    elif school == "SOUTHWEST UNIVERSITY":
        item=group.locator(".application-requirement-item").filter(has_text=text)
        expect(item).to_have_count(1)
        expect(item.locator('[data-document-applicability="needs_confirmation"]')).to_be_visible()
        expect(item).to_contain_text("依申請專業確認")
        expect(item).to_contain_text("音樂、美術、服裝設計、景觀")
    else:
        item=group.locator(".application-requirement-item").filter(has_text="交換申請表（依本科／研究生選相應版本）")
        expect(item).to_have_count(1)
        item.locator(".application-requirement-source details > summary").click()
        expect(item.locator('a[href*="1v7Hjjlt_bcNiIqhi8X720pUlTnPSF-FN"]')).to_be_visible()
        expect(item.locator('a[href*="1UZd3AD5cVmdQ5lBV_gcUT6MUMd2cqRQG"]')).to_be_visible()
        expect(item.locator(".application-requirement-source details a")).to_have_count(2)
        expect(item).to_contain_text("其他參考來源（當期待確認）")
    expect(item).not_to_contain_text("官方表格")
    item.scroll_into_view_if_needed()
    out=Path('/tmp/ncu-audit/browser');out.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(out/filename))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_ncu_science_tokyo_track_coe_health_and_2027_tiec_fee_reach_mobile_content(page,live_server):
    page.set_viewport_size({'width':390,'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    enter_public_site(page,live_server,'partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page);page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click();page.locator('#confirm-school').click()
    wait_until(page,"state.dashboard?.school_name === '國立中央大學'",timeout=60.0)
    if page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click();page.locator('#partner-search').fill('東京科學')
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    page.locator('#partner-table .partner-card > summary').first.click();page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#detail-overview .partner-student-summary li').filter(has_text='限115-2').first).to_be_visible()
    page.locator('#ncu-source-audit > summary').click()
    health=page.locator('#ncu-source-audit-body > details').filter(has_text='東京科學官方：health-part1').first
    expect(health.locator(':scope > summary')).to_contain_text('2頁已視覺查核')
    health.locator(':scope > summary').click()
    part=health.locator('details').filter(has_text='All student').first
    part.locator(':scope > summary').click();expect(part.locator('pre')).to_be_visible()
    expect(part.locator('pre')).to_contain_text('2026. 10')
    out=Path('/tmp/ncu-audit/browser');out.mkdir(parents=True,exist_ok=True)
    part.locator('pre').scroll_into_view_if_needed();page.screenshot(path=str(out/'ncu-science-health-scope-390.png'))
    page.locator('#detail-tab-life').click();page.locator('#detail-life .life-official-guide > summary').click()
    fee=page.locator('#destination-official-content li').filter(has_text='A48000').first
    expect(fee).to_be_visible();expect(fee).to_contain_text('2027/3/1')
    expect(fee).to_contain_text('重新入館改新價')
    fee.scroll_into_view_if_needed();page.screenshot(path=str(out/'ncu-science-tiec2027-fee-390.png'))
    page.locator('#detail-tab-application').click()
    def step(title):
        return page.locator('#detail-application .workflow-step').filter(has=page.locator('summary').filter(has_text=title)).first
    consent=step('僅YSEP非建築：受邀申請前確認研究指導同意');consent.locator(':scope > summary').click()
    expect(consent).to_contain_text('建築及ACAP由校方安排')
    initial=step('核對外校當期文件並依通知申請');initial.locator(':scope > summary').click()
    expect(initial.locator('.workflow-documents > li')).to_have_count(8)
    coe=initial.get_by_text('COE申請Excel',exact=False).last
    expect(coe).to_be_visible();expect(coe).to_contain_text('初次一起交')
    coe.scroll_into_view_if_needed();page.screenshot(path=str(out/'ncu-science-initial-coe-390.png'))
    housing=step('如確認申請TIEC研究生住宿');housing.locator(':scope > summary').click()
    expect(housing.locator('.workflow-documents > li')).to_have_count(8)
    expect(housing).to_contain_text('新渡日者在留卡例外')
    expect(housing).to_contain_text('現連2026表不到116')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
