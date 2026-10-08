"""CCU receiving-source details and all four school grade controls in real pages."""

import json
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities

from .conftest import enter_public_site, open_navigation
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
    expect(deadline).to_contain_text("跨來源矛盾")
    expect(deadline).to_contain_text("2026/10/15")
    expect(deadline).to_contain_text("2026-10-01")
    deadline.get_by_text("已查來源與實際結果", exact=True).click()
    expect(deadline).to_contain_text("已取得並逐欄核對")
    arrival = section.locator('[data-ccu-field="arrival"]')
    arrival.locator("> summary").click()
    expect(arrival).to_contain_text("2026年12月下旬／2027年初")
    output = Path("/tmp/ccu-second-pass-browser")
    output.mkdir(exist_ok=True)
    deadline.scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"ccu-deadline-{width}.png"))
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_contain_text(
        "跨來源矛盾", timeout=15_000
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
@pytest.mark.parametrize("source_page", [34, 68, 95])
def test_ccu_sixth_batch_conflicts_and_amu_alternative_proof(page, live_server, width, source_page):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page)
    page.goto(live_server.base_url + "/?school=" + quote(CCU) + "#school=" + quote(partner.school_name))
    section = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(section).to_be_visible(timeout=30_000)
    key = {34:"academic_calendar", 68:"application_deadline", 95:"language"}[source_page]
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
        assert page.evaluate(
            "item => window.UniWayCcuLanguage.assess(item, 'ielts', '大學部').threshold",
            partner.model_dump(mode="json"),
        ) is None
    field.scroll_into_view_if_needed()
    output = Path("/tmp/ccu-sixth-pass-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"ccu-sixth-{source_page}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_all_four_school_grade_fields_remain_isolated(page, live_server):
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
    ]
    for school, percent, gpa, rank in cases:
        open_navigation(page)
        page.locator("#school-switcher").click()
        expect(page.locator("#school-options [data-home-school]")).to_have_count(4)
        page.locator(f'[data-home-school="{school}"]').click()
        page.locator("#confirm-school").click()
        wait_until(page, "state.dashboard?.school_name === " + json.dumps(school))
        page.evaluate("location.hash='#advisor'")
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
def test_ccu_seventh_current_templates_and_program_deadlines(page, live_server, width, source_page):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page)
    page.goto(live_server.base_url + "/?school=" + quote(CCU) + "#school=" + quote(partner.school_name))
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
        assert forms.locator('a[href$="HU-Study-Plan_Half-Year_2027-Spring.xls"]').count() >= 1
        assert page.evaluate("item => window.UniWayCcuLanguage.assess(item, 'toefl', '大學部').threshold", partner.model_dump(mode="json")) is None
    deadline.scroll_into_view_if_needed()
    output = Path("/tmp/ccu-seventh-pass-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"ccu-seventh-{source_page}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
