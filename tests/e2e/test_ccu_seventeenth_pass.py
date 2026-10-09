"""Actual CCU paired filtering and pending official form rendering at two widths."""

import json
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities

from .conftest import enter_public_site
from .test_open_catalog import attach_session, sign_in_cookie, wait_until

HOME = "國立中正大學"


def at(source_page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page)


@pytest.mark.parametrize("width", [390, 1440])
def test_nagoya_pair_filters_use_one_option(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    session = sign_in_cookie(live_server, school=HOME)
    live_server.verify_student(session["profile"]["id"], university=HOME)
    attach_session(page, live_server, session)
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    enter_public_site(page, live_server, "partners")
    wait_until(page, "state.dashboard?.school_name === '國立中正大學'")
    wait_until(page, "homeCollegeOptions().includes('教育學院') && homeCollegeOptions().includes('法學院')")
    for college, degree, allowed in [
        ("法學院", "大學部", False), ("法學院", "博士班", False),
        ("法學院", "碩士班", True), ("教育學院", "大學部", True),
        ("教育學院", "博士班", True),
    ]:
        result = page.evaluate("""({name,college,degree}) => {
            const item=state.dashboard.partner_universities.find(p=>p.school_name===name);
            const profile={college,degree,academicScore:85,academicGpa:3.5,languageTest:'',languageScore:0};
            state.eligibilityProfile=profile;state.college=college;state.degree=degree;
            openUniversityDetail(item,{updateHistory:false});
            return {match:partnerMatch(item,profile),included:filteredPartners().some(p=>p.school_name===name)};
        }""", {"name": at(34).school_name, "college": college, "degree": degree})
        assert result["included"] is allowed
        assert ("符合目前學制" in result["match"]["reasons"]) is allowed
        expect(page.locator("#school-detail-content")).to_contain_text("教育學院")
        expect(page.locator("#school-detail-content")).to_contain_text("法學院")
        if not allowed:
            expect(page.locator("#school-detail-primary-facts")).to_contain_text("配對不符")
    output = Path("/tmp/ccu-seventeenth-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"nagoya-pairs-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("source_page", [98, 102])
def test_unyear_templates_have_separate_applicability_warning(page, live_server, width, source_page):
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    partner = at(source_page)
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    expect(page.locator("#detail-tab-application")).to_be_visible(timeout=30_000)
    page.locator("#detail-tab-application").click()
    step = page.locator("details.workflow-step").filter(
        has=page.locator(".workflow-documents li b").filter(has_text="Learning Agreement")
    )
    step.locator("> summary").click()
    item = step.locator(".workflow-documents li").filter(has_text="Learning Agreement")
    expect(item).to_contain_text("當期適用待確認")
    link = item.locator("a")
    expect(link).to_have_count(1)
    source_id = "p102-r3-learning-agreement-web" if source_page == 102 else "p98-r3-learning-agreement"
    source = json.loads((BUNDLE / "overseas_sources" / f"{source_id}.json").read_text())
    expect(link).to_have_attribute("href", source["source_url"])
    if source_page == 102:
        expect(link).to_contain_text("待核實")
        expect(item).to_contain_text("原檔下載未核實")
    else:
        assert "docx" in link.get_attribute("href").lower()
    page.evaluate("location.hash='#application-center'")
    page.evaluate("async name => {state.applicationContext.target_school=name;await loadApplicationTemplates();}", partner.school_name)
    group = page.locator("#application-requirement-list details.application-requirement-group").filter(has_text="Learning Agreement")
    if not group.evaluate("node=>node.open"):
        group.locator("> summary").click()
    entry = group.locator("article").filter(has_text="Learning Agreement")
    expect(entry).to_contain_text("當期適用待確認")
    expect(entry.locator("a")).to_have_attribute("href", source["source_url"])
    if source_page == 102:
        expect(entry).to_contain_text("原檔下載未核實")
    output = Path("/tmp/ccu-seventeenth-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"pending-forms-{source_page}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
