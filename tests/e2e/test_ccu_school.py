"""CCU receiving-source details and all four school grade controls in real pages."""

import json
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities

from .conftest import enter_public_site, open_navigation, expand_details
from .test_open_catalog import wait_until

CCU = "國立中正大學"


@pytest.mark.parametrize("width", [390, 1440])
def test_ccu_deadlines_forms_and_research_progress(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    partner = next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 67
    )
    page.goto(
        live_server.base_url
        + "/?school="
        + quote(CCU)
        + "#school="
        + quote(partner.school_name)
    )
    section = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(section).to_be_visible(timeout=30_000)
    expect(section.locator("[data-ccu-field]")).to_have_count(17)
    deadline = section.locator('[data-ccu-field="application_deadline"]')
    deadline.locator("> summary").click()
    expect(deadline).to_contain_text("當期已核實")
    expect(deadline).to_contain_text("2026-10-15")
    expect(deadline).to_contain_text("3月版10/01保留參考")
    deadline.get_by_text("已查來源與實際結果", exact=True).click()
    expect(deadline).to_contain_text("已取得並逐欄核對")
    arrival = section.locator('[data-ccu-field="arrival"]')
    arrival.locator("> summary").click()
    expect(arrival).to_contain_text("2027-01-08")
    expect(arrival).to_contain_text("未載接機／宿舍入住")
    output = Path("/tmp/ccu-second-pass-browser")
    output.mkdir(exist_ok=True)
    deadline.scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"ccu-deadline-{width}.png"))
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_contain_text(
        "提名信", timeout=15_000
    )
    partner = next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 43
    )
    page.evaluate(
        "location.hash=" + json.dumps("#school=" + quote(partner.school_name))
    )
    forms = page.locator('#detail-overview [data-ccu-field="application_forms"]')
    expect(forms).to_be_visible(timeout=15_000)
    forms.locator("> summary").click()
    expect(forms).to_contain_text("STUDY PLAN [FORM #1]")
    expect(forms).to_contain_text("AFFIDAVIT OF SUPPORT [FORM #2]")
    assert forms.locator('a[href$="#page=14"]').count() == 1
    assert forms.locator('a[href$="#page=15"]').count() == 1
    forms.scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"ccu-forms-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("source_page", [35, 61, 105])
def test_ccu_submission_result_calendar_and_campus_boundaries(
    page, live_server, width, source_page
):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    partner = next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page
    )
    page.goto(
        live_server.base_url
        + "/?school="
        + quote(CCU)
        + "#school="
        + quote(partner.school_name)
    )
    section = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(section).to_be_visible(timeout=30_000)
    key = "application_deadline" if source_page == 35 else "academic_calendar"
    field = section.locator(f'[data-ccu-field="{key}"]')
    field.locator("> summary").click()
    if source_page == 35:
        for text in [
            "提交窗口2026-07-01至10-15 15:00 JST",
            "EarlyNovember",
            "TAO Oct1–Nov15",
            "內部矛盾",
        ]:
            expect(field).to_contain_text(text)
    elif source_page == 61:
        for text in [
            "2027-01-13至05-28",
            "01-11至05-15",
            "registrationday",
            "SIT研究所",
        ]:
            expect(field).to_contain_text(text)
    else:
        for text in [
            "2027-02-08至06-04",
            "本科",
            "研究所",
            "Cyprus",
            "不是exchangeapplication",
        ]:
            expect(field).to_contain_text(text)
    output = Path("/tmp/ccu-latest-browser")
    output.mkdir(exist_ok=True)
    field.scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"ccu-boundary-{source_page}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("width", [390, 1440])
def test_ccu_profile_life_and_individual_document_stages_render(
    page, live_server, width
):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    partner = next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 103
    )
    page.goto(
        live_server.base_url
        + "/?school="
        + quote(CCU)
        + "#school="
        + quote(partner.school_name)
    )
    expect(page.locator("#detail-tab-life")).to_be_visible(timeout=30_000)
    page.locator("#detail-tab-life").click()
    life = page.locator("#detail-life")
    expect(life).to_contain_text("Winterthur", timeout=30_000)
    expect(life).to_contain_text("中央車站步行")
    expect(life).to_contain_text("ALIAS")
    expect(life).to_contain_text("適用年度或條件待確認")
    life.locator("details.life-official-guide > summary").click()
    transport = life.locator('[data-ccu-life-field="transport"]')
    campus = life.locator('[data-ccu-life-field="campus_life"]')
    expect(transport).to_be_visible()
    expect(campus).to_be_visible()
    expect(transport).to_contain_text("中央車站步行")
    expect(campus).to_contain_text("ALIAS")
    transport.scroll_into_view_if_needed()
    output = Path("/tmp/ccu-latest-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"ccu-life-103-{width}.png"))
    partner = next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 53
    )
    page.evaluate(
        "location.hash=" + json.dumps("#school=" + quote(partner.school_name))
    )
    expect(page.locator("#detail-tab-application")).to_be_visible(timeout=30_000)
    page.locator("#detail-tab-application").click()
    application = page.locator("#detail-application")
    expect(application).to_contain_text("12/20上傳；1/15正本抵校", timeout=30_000)
    expect(application).to_contain_text("中正逐校第二階文件：當期已核實")
    home_step = application.locator("details.workflow-step").filter(
        has_text="中正逐校第二階文件：當期已核實"
    )
    home_step.locator("> summary").click()
    expect(home_step.locator(".workflow-documents")).to_be_visible()
    host_step = application.locator("details.workflow-step").filter(
        has_text="12/20上傳；1/15正本抵校"
    )
    host_step.locator("> summary").click()
    document = host_step.locator(".workflow-documents li").filter(
        has_text="12/20上傳；1/15正本抵校"
    )
    expect(document).to_have_count(2)
    expect(document.nth(0)).to_be_visible()
    expect(document.nth(1)).to_be_visible()
    document.nth(0).scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"ccu-documents-53-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("source_page", [34, 68, 95])
def test_ccu_sixth_batch_conflicts_and_amu_alternative_proof(
    page, live_server, width, source_page
):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    partner = next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page
    )
    page.goto(
        live_server.base_url
        + "/?school="
        + quote(CCU)
        + "#school="
        + quote(partner.school_name)
    )
    section = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(section).to_be_visible(timeout=30_000)
    key = {34: "academic_calendar", 68: "application_deadline", 95: "language"}[
        source_page
    ]
    field = section.locator(f'[data-ccu-field="{key}"]')
    field.locator("> summary").click()
    if source_page == 34:
        expect(field).to_contain_text("來源差異未解")
        expect(field).to_contain_text("2027-04-09")
        expect(field).to_contain_text("2027-04-12")
        arrival = section.locator('[data-ccu-field="arrival"]')
        arrival.locator("> summary").click()
        expect(arrival).to_contain_text("04-01")
        expect(arrival).to_contain_text("抵達不等開課")
    elif source_page == 68:
        expect(field).to_contain_text("2027-01-25")
        expect(field).to_contain_text("2027-01-04")
        expect(field).to_contain_text("2027-04-12")
        expect(field).to_contain_text("來源矛盾")
    else:
        expect(field).to_contain_text("適用年度或條件待確認")
        expect(field).to_contain_text("Rector／Dean／Coordinator")
        expect(field).to_contain_text("recommended")
        expect(field).to_contain_text("兩年內有效檢定")
        assert (
            page.evaluate(
                "item => window.UniWayCcuLanguage.assess(item, 'ielts', '大學部').threshold",
                partner.model_dump(mode="json"),
            )
            is None
        )
    field.scroll_into_view_if_needed()
    output = Path("/tmp/ccu-sixth-pass-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"ccu-sixth-{source_page}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_all_six_school_grade_fields_remain_isolated(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 956})
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    enter_public_site(page, live_server, "advisor")
    cases = [
        ("國立中正大學", True, True, False),
        ("國立臺灣大學", False, True, True),
        ("國立臺北大學", True, False, False),
        ("長庚大學", True, False, False),
        ("國立中央大學", True, False, False),
        ("淡江大學", True, False, False),
    ]
    for school, percent, gpa, rank in cases:
        open_navigation(page)
        page.locator("#school-switcher").click()
        expect(page.locator("#school-options [data-home-school]")).to_have_count(6)
        assert page.locator("#school-options [data-home-school]").evaluate_all(
            "nodes => nodes.map(node => node.dataset.homeSchool)"
        ) == ["長庚大學", "國立臺北大學", "國立臺灣大學", "國立中正大學", "國立中央大學", "淡江大學"]
        page.locator(f'[data-home-school="{school}"]').click()
        wait_until(page, "state.dashboard?.school_name === " + json.dumps(school))
        page.evaluate("location.hash='#advisor'")
        expand_details(page, "#advisor-qualification-fields")
        for selector, visible in [
            ("#advisor-academic-score", percent),
            ("#advisor-academic-gpa", gpa),
            ("#advisor-class-rank", rank),
        ]:
            if visible:
                expect(page.locator(selector)).to_be_visible()
            else:
                expect(page.locator(selector)).to_be_hidden()
        if school == CCU:
            assert page.locator("#eligibility-preference-4").is_hidden()
        else:
            assert not page.locator("#eligibility-preference-4").evaluate(
                'node => node.closest("label").hidden'
            )


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("source_page", [98, 102, 101])
def test_ccu_new_public_forms_and_source_conflict_categories(
    page, live_server, width, source_page
):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    partner = next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page
    )
    page.goto(
        live_server.base_url
        + "/?school="
        + quote(CCU)
        + "#school="
        + quote(partner.school_name)
    )
    section = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(section).to_be_visible(timeout=30_000)
    expect(section.locator("[data-ccu-field]")).to_have_count(17)
    key = "academic_calendar" if source_page == 101 else "application_forms"
    detail = section.locator(f'[data-ccu-field="{key}"]')
    detail.locator("> summary").click()
    if source_page == 98:
        expect(detail).to_contain_text("正文是summer2027")
        expect(detail).to_contain_text("個人申請PDF")
        expect(detail).to_contain_text("須建立帳號並提交後才產生個人PDF")
        assert detail.locator('a[href*="Accommodation_Request_2026.pdf"]').count() >= 1
        arrival = section.locator('[data-ccu-field="arrival"]')
        arrival.locator("> summary").click()
        expect(arrival).to_contain_text("2027-02-22至02-25")
    elif source_page == 102:
        expect(detail).to_contain_text("當期已核實")
        expect(detail).to_contain_text("SS2027")
        docs = section.locator('[data-ccu-field="documents"]')
        docs.locator("> summary").click()
        expect(docs).to_contain_text("六類")
        expect(docs).to_contain_text("signature AND STAMP")
        expect(docs).to_contain_text("適用年度或條件待確認")
        assert (
            docs.locator('a[href$="Learning-Agreement-Incoming.pdf#page=1"]').count()
            == 1
        )
    else:
        expect(detail).to_contain_text("來源矛盾尚未釐清，公開依據續查")
        expect(detail).to_contain_text("2026")
        expect(detail).not_to_contain_text("須個別通知或校方釐清")
    detail.scroll_into_view_if_needed()
    output = Path("/tmp/ccu-third-pass-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"ccu-public-{source_page}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("source_page", [32, 37])
def test_ccu_seventh_current_templates_and_program_deadlines(
    page, live_server, width, source_page
):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    partner = next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page
    )
    page.goto(
        live_server.base_url
        + "/?school="
        + quote(CCU)
        + "#school="
        + quote(partner.school_name)
    )
    section = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(section).to_be_visible(timeout=30_000)
    expect(section.locator("[data-ccu-field]")).to_have_count(17)
    deadline = section.locator('[data-ccu-field="application_deadline"]')
    deadline.locator("> summary").click()
    if source_page == 32:
        expect(deadline).to_contain_text("2026-11-09 23:59 JST")
        expect(deadline).to_contain_text("2026-11-15")
        expect(deadline).to_contain_text("來源矛盾")
        assert deadline.locator('a[href$="s_exchange_02.html"]').count() >= 1
    else:
        expect(deadline).to_contain_text("2026-10-23")
        expect(deadline).to_contain_text("2026-11-13")
        expect(deadline).to_contain_text("SA/SRS")
        forms = section.locator('[data-ccu-field="application_forms"]')
        forms.locator("> summary").click()
        expect(forms).to_contain_text("表內SpringSemester2027")
        expect(forms).to_contain_text("2026Spring課表tentative")
        assert (
            forms.locator('a[href$="HU-Study-Plan_Half-Year_2027-Spring.xls"]').count()
            >= 1
        )
        assert (
            page.evaluate(
                "item => window.UniWayCcuLanguage.assess(item, 'toefl', '大學部').threshold",
                partner.model_dump(mode="json"),
            )
            is None
        )
    deadline.scroll_into_view_if_needed()
    output = Path("/tmp/ccu-seventh-pass-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"ccu-seventh-{source_page}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
