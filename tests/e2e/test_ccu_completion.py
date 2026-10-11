"""Real CCU reference-school screens, licensed image requests and mobile layout."""
import json
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities

HOME = "國立中正大學"


@pytest.mark.parametrize("width", [390, 1440])
def test_sungshin_current_medical_template_and_stale_nomination_year_are_visible(page, live_server, width):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 49)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    receiving = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(receiving.locator("[data-ccu-field]")).to_have_count(17, timeout=30_000)
    forms = receiving.locator('[data-ccu-field="application_forms"]')
    forms.locator("> summary").click()
    expect(forms).to_contain_text("來源矛盾")
    expect(forms).to_contain_text("2025-12-01")
    calendar = receiving.locator('[data-ccu-field="academic_calendar"]')
    calendar.locator("> summary").click()
    expect(calendar).to_contain_text("2027-03-02")
    expect(calendar).to_contain_text("2027-02-17")
    page.locator('#detail-tab-application').click()
    step = page.locator("#detail-application .workflow-step").filter(
        has=page.locator(".workflow-documents li b").filter(has_text="Personal Medical Assessment")
    )
    step.locator("> summary").click()
    medical = step.locator(".workflow-documents li").filter(has_text="Personal Medical Assessment")
    expect(medical).to_contain_text("自填健康評估")
    expect(medical).to_contain_text("學生")
    expect(medical.locator("a")).to_have_attribute("href", "https://www.sungshin.ac.kr/bbs/int/3828/113856/download.do#page=2")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_uel_undated_language_and_current_calendar_conflicts_remain_reference(page, live_server, width):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 66)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    reference = page.locator("#detail-overview .ccu-reference-host")
    expect(reference).to_contain_text("中正本期未開放", timeout=30_000)
    expect(reference.locator("[data-ccu-reference-field]")).to_have_count(17)
    language = reference.locator('[data-ccu-reference-field="language"]')
    language.locator("> summary").click()
    expect(language).to_contain_text("IELTS ≥6.0")
    expect(language.locator("> summary")).to_contain_text("待確認")
    calendar = reference.locator('[data-ccu-reference-field="academic_calendar"]')
    calendar.locator("> summary").click()
    expect(calendar.locator("> summary")).to_contain_text("來源矛盾")
    expect(calendar).to_contain_text("2026-03-15")
    housing = reference.locator('[data-ccu-reference-field="housing"]')
    housing.locator("> summary").click()
    expect(housing).to_contain_text("per6months")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("ccu_page", [92, 112])
def test_current_usj_czu_receiving_rules_remain_reference_tracks(page, live_server, width, ccu_page):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == ccu_page)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    reference = page.locator("#detail-overview .ccu-reference-host")
    expect(reference).to_contain_text("中正本期未開放", timeout=30_000)
    expect(reference.locator("[data-ccu-reference-field]")).to_have_count(17)
    deadline = reference.locator('[data-ccu-reference-field="application_deadline"]')
    deadline.locator("> summary").click()
    expect(deadline.locator("> summary")).to_contain_text("待確認")
    calendar = reference.locator('[data-ccu-reference-field="academic_calendar"]')
    calendar.locator("> summary").click()
    forms = reference.locator('[data-ccu-reference-field="application_forms"]')
    forms.locator("> summary").click()
    if ccu_page == 112:
        expect(deadline).to_contain_text("不能直接複用6月日期")
        expect(calendar).to_contain_text("2027-02-01至06-30")
        expect(calendar).to_contain_text("To be specified")
        expect(forms).to_contain_text("non-Erasmus專用")
        courses = reference.locator('[data-ccu-reference-field="course_restrictions"]')
        courses.locator("> summary").click()
        expect(courses).to_contain_text("最多30ECTS")
        expect(courses).to_contain_text("主要faculty至少50%")
    else:
        expect(deadline).to_contain_text("2026-12-15")
        expect(calendar).to_contain_text("07-03")
        expect(calendar).to_contain_text("07-02")
        expect(calendar.locator("> summary")).to_contain_text("來源矛盾")
        expect(forms).to_contain_text("正文无年度")
        expect(forms.locator('a[href$="Mobility.docx"]')).to_have_count(1)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_fges_faculty_and_parent_conflicts_are_visible_with_both_sources(page, live_server, width):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 88)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    receiving = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(receiving.locator("[data-ccu-field]")).to_have_count(17, timeout=30_000)
    deadline = receiving.locator('[data-ccu-field="application_deadline"]')
    expect(deadline.locator("> summary")).to_contain_text("來源矛盾")
    deadline.locator("> summary").click()
    expect(deadline).to_contain_text("2026-11-15")
    expect(deadline).to_contain_text("October15,2025")
    assert len({a.get_attribute("href") for a in deadline.locator("a").all()}) >= 2
    language = receiving.locator('[data-ccu-field="language"]')
    language.locator("> summary").click()
    expect(language).to_contain_text("advised")
    expect(language).to_contain_text("minimum")
    expect(language).to_contain_text("不能把FLSH心理學")
    forms = receiving.locator('[data-ccu-field="application_forms"]')
    forms.locator("> summary").click()
    expect(forms).to_contain_text("提名後個人入口")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_qut_2027_fees_and_reference_status_do_not_create_an_exchange_offer(page, live_server, width):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 120)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    reference = page.locator("#detail-overview .ccu-reference-host")
    expect(reference).to_contain_text("中正本期未開放", timeout=30_000)
    tuition = reference.locator('[data-ccu-reference-field="host_tuition"]')
    tuition.locator("> summary").click()
    expect(tuition).to_contain_text("AUD9900")
    expect(tuition).to_contain_text("AUD13200")
    expect(tuition).to_contain_text("免QUT tuition")
    expect(tuition).to_contain_text("排除exchange")
    costs = reference.locator('[data-ccu-reference-field="costs"]')
    costs.locator("> summary").click()
    expect(costs).to_contain_text("來源矛盾")
    expect(costs).to_contain_text("4095")
    calendar = reference.locator('[data-ccu-reference-field="academic_calendar"]')
    calendar.locator("> summary").click()
    expect(calendar).to_contain_text("2027-02-15")
    language = reference.locator('[data-ccu-reference-field="language"]')
    language.locator("> summary").click()
    expect(language).to_contain_text("未自行換算")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_iit_bombay_current_receiving_policy_preserves_closed_home_status(page, live_server, width):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 72)
    assert partner.availability_status == "not_open" and partner.quota is None
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    reference = page.locator("#detail-overview .ccu-reference-host")
    expect(reference).to_contain_text("中正本期未開放", timeout=30_000)
    expect(reference.locator("[data-ccu-reference-field]")).to_have_count(17)
    deadline = reference.locator('[data-ccu-reference-field="application_deadline"]')
    deadline.locator("> summary").click()
    expect(deadline).to_contain_text("2026-09-30")
    expect(deadline).to_contain_text("Project申請全年受理")
    expect(deadline.locator("a").first).to_have_attribute("href", partner.website + "sites/default/files/2026-08/IITB%20IR%20Fact%20Sheet%202026-2027.pdf#page=3")
    forms = reference.locator('[data-ccu-reference-field="application_forms"]')
    forms.locator("> summary").click()
    expect(forms).to_contain_text("待確認")
    expect(forms).to_contain_text("到校後")
    housing = reference.locator('[data-ccu-reference-field="housing"]')
    housing.locator("> summary").click()
    expect(housing).to_contain_text("不是事前保證床位")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_closed_reference_school_shows_separate_current_host_tracks_and_credited_campus(page, live_server, width):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 81)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    attribution = page.locator("#detail-overview .ccu-campus-attribution")
    expect(attribution).to_be_visible(timeout=30_000)
    expect(attribution).to_contain_text("Patrick")
    expect(attribution).to_contain_text("CC BY-SA 4.0")
    expect(attribution).to_contain_text("Loyola")
    expect(attribution.locator("p").first).not_to_contain_text("Grade School")
    assert page.request.get(live_server.base_url + partner.image_url).status == 200
    reference = page.locator("#detail-overview .ccu-reference-host")
    expect(reference).to_contain_text("中正本期未開放")
    expect(reference.locator("[data-ccu-reference-field]")).to_have_count(17)
    deadline = reference.locator('[data-ccu-reference-field="application_deadline"]')
    deadline.locator("> summary").click()
    expect(deadline).to_contain_text("本科2026-09-30")
    expect(deadline).to_contain_text("研究所2026-09-01")
    language = reference.locator('[data-ccu-reference-field="language"]')
    language.locator("> summary").click()
    expect(language).to_contain_text("iBT79")
    expect(language).to_contain_text("iBT80")
    assert len({a.get_attribute("href") for a in deadline.locator("a").all()}) >= 2
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    output = Path("/tmp/ccu-completion-browser")
    output.mkdir(exist_ok=True)
    deadline.scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"ateneo-reference-{width}.png"))
    assert not errors


@pytest.mark.parametrize("width", [390, 1440])
def test_current_partner_has_correct_school_of_engineering_photo_and_primary_coordinate(page, live_server, width):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 103)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    attribution = page.locator("#detail-overview .ccu-campus-attribution")
    expect(attribution).to_be_visible(timeout=30_000)
    expect(attribution).to_contain_text("School of Engineering")
    expect(attribution).to_contain_text("Technikumstrasse 9")
    expect(attribution).to_contain_text("CC BY-SA 4.0")
    assert partner.location.latitude == 47.4972243
    assert json.loads(partner.reference_data["ccu_campus_assets"])["photo"]["artist"]
    assert page.request.get(live_server.base_url + partner.image_url).status == 200
    expect(page.locator("#detail-overview .ccu-receiving-school-details [data-ccu-field]")).to_have_count(17)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
