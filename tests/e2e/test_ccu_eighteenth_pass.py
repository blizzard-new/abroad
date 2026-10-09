"""Submit the actual shared conditions form through both modes and real APIs."""

from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities

from .conftest import enter_public_site
from .test_open_catalog import attach_session, sign_in_cookie, wait_until

HOME = "國立中正大學"


def at(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


@pytest.mark.parametrize("width", [390, 1440])
def test_actual_degree_select_and_current_year_in_both_modes(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    session = sign_in_cookie(live_server, school=HOME)
    live_server.verify_student(session["profile"]["id"], university=HOME)
    attach_session(page, live_server, session)
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    enter_public_site(page, live_server, "application-center")
    partner = at(34)
    wait_until(page, "homeCollegeOptions().includes('教育學院') && homeCollegeOptions().includes('法學院')")
    page.locator("#application-target-school").select_option(partner.school_name)
    wait_until(page, "state.applicationContext.target_school === " + repr(partner.school_name))
    for college, degree, year, status in [
        ("法學院", "研究所", "博士班", "fail"),
        ("法學院", "研究所", "", "needs_confirmation"),
        ("法學院", "研究所", "碩士班", "pass"),
        ("法學院", "碩士班", "碩士班", "pass"),
        ("法學院", "博士班", "博士班", "fail"),
        ("教育學院", "大學部", "大三", "pass"),
        ("教育學院", "研究所", "", "pass"),
    ]:
        page.evaluate("location.hash='#advisor'")
        expect(page.locator("#advisor-form")).to_be_visible()
        page.locator("#advisor-college").select_option(college)
        department = page.locator("#advisor-department")
        if department.evaluate("node=>node.tagName") == "SELECT":
            wait_until(page, "document.querySelector('#advisor-department').options.length > 1")
            value = department.locator("option").evaluate_all("rows=>rows.find(row=>row.value).value")
            department.select_option(value)
        else:
            department.fill("法律學系" if college == "法學院" else "教育學系")
        page.locator("#advisor-degree").select_option(degree)
        extra = page.locator("#advisor-current-year").locator("xpath=ancestor::details")
        if not extra.evaluate("node=>node.open"):
            extra.locator("> summary").click()
        page.locator("#advisor-current-year").select_option(year)
        page.locator("#advisor-academic-score").fill("85")
        page.locator("#advisor-academic-gpa").fill("3.5")
        page.locator("#advisor-language-test").select_option("ielts")
        page.locator("#advisor-language-score").fill("7")
        with page.expect_response(lambda r: r.url.endswith("/advisor/plan") and r.request.method == "POST") as updated:
            page.locator("#advisor-submit").click()
        assert updated.value.ok
        assert updated.value.request.post_data_json["degree_level"] == degree
        assert updated.value.request.post_data_json["current_year"] == (year or None)
        target = updated.value.json()["target_match"]
        assert ("符合目前學制" in target["reasons"]) is (status == "pass")
        expect(page.locator("#advisor-profile-status")).to_have_text("已保存條件")
        frontend = page.evaluate("name=>partnerMatch(state.dashboard.partner_universities.find(p=>p.school_name===name))", partner.school_name)
        assert ("符合目前學制" in frontend["reasons"]) is (status == "pass")
        if status == "fail":
            assert any("配對不符" in s for s in frontend["risks"])
        elif status == "needs_confirmation":
            assert any("尚未區分碩博士" in s for s in frontend["risks"])
            assert not any("配對不符" in s for s in frontend["risks"])
        page.evaluate("location.hash='#eligibility'")
        page.locator("#eligibility-academic-year").select_option("115")
        page.locator("#eligibility-application-round").select_option("第二梯次")
        page.locator("#eligibility-preference-1").select_option(partner.school_name)
        with page.expect_response(lambda r: r.url.endswith("/application-plan/evaluate") and r.request.method == "POST" and "current_year" in r.request.post_data_json) as checked:
            page.locator("#advisor-submit").click()
        assert checked.value.ok
        payload = checked.value.request.post_data_json
        assert payload["degree_level"] == degree and payload["current_year"] == year
        check = next(c for c in checked.value.json()["choices"][0]["checks"] if c["code"] == "degree_level")
        assert check["status"] == status
        expect(page.locator("#eligibility-result")).to_contain_text(check["detail"])
        if status == "needs_confirmation":
            expect(page.locator("#eligibility-result")).to_contain_text("尚未區分碩博士")
        expect(page.locator("#advisor-submit")).to_be_enabled(timeout=30_000)
    output = Path("/tmp/ccu-eighteenth-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"nagoya-real-form-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


@pytest.mark.parametrize("width", [390, 1440])
def test_hcmute_email_sender_and_pilsen_transfers_render(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(at(68).school_name))
    expect(page.locator("#detail-tab-application")).to_be_visible(timeout=30_000)
    page.locator("#detail-tab-application").click()
    steps = page.locator("details.workflow-step")
    for index in [3, 4]:
        step = steps.nth(index)
        step.locator("> summary").click()
        expect(step).to_contain_text("電子郵件 送件")
        expect(step).not_to_contain_text("混合送件")
        expect(step).to_contain_text("母校")
        expect(step).to_contain_text("oia@hcmute.edu.vn")
    nomination_docs = steps.nth(3).locator(".workflow-documents li b")
    expect(nomination_docs).to_have_count(8)  # Seven host items and the unchanged CCU second-stage entry.
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(at(109).school_name))
    expect(page.locator("#detail-tab-life")).to_be_visible(timeout=30_000)
    page.locator("#detail-tab-life").click()
    life = page.locator("#detail-life")
    expect(life).to_contain_text("B線至Florenc再轉巴士")
    expect(life).to_contain_text("轉C線到Hlavní Nádraží（中央車站），再搭火車")
    expect(life).to_contain_text("適用年度或條件待確認")
    output = Path("/tmp/ccu-eighteenth-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"pilsen-transfers-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
