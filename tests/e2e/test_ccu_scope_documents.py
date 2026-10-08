"""Public CCU rows and actual document links, including a saved official binary replay."""

import hashlib
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


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("source_page", [104, 37])
def test_real_browser_and_both_apis_keep_pending_scope_neutral(
    page, live_server, width, source_page
):
    page.set_viewport_size({"width": width, "height": 956})
    session = sign_in_cookie(live_server, school=HOME)
    live_server.verify_student(session["profile"]["id"], university=HOME)
    attach_session(page, live_server, session)
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    enter_public_site(page, live_server, "partners")
    wait_until(page, "state.dashboard?.school_name === '國立中正大學'")
    partner = at(source_page)
    for college, degree in [("管理學院", "大學部"), ("工學院", "博士班")]:
        profile = {
            "college": college,
            "degree": degree,
            "academicScore": 85,
            "academicGpa": 3.5,
            "languageTest": "",
            "languageScore": 0,
        }
        result = page.evaluate(
            """({name,profile}) => {
          const item=state.dashboard.partner_universities.find(p=>p.school_name===name);
          state.eligibilityProfile=profile;
          openUniversityDetail(item,{updateHistory:false});
          const match=partnerMatch(item,profile);
          state.college=profile.college;state.degree=profile.degree;
          return {match,stillInFilters:filteredPartners().some(p=>p.school_name===name)};
        }""",
            {"name": partner.school_name, "profile": profile},
        )
        assert result["match"]["tone"] == "review"
        assert not {"符合學院範圍", "符合目前學制"} & set(result["match"]["reasons"])
        assert "合作校學院範圍待確認" in result["match"]["risks"]
        assert "合作校學制範圍待確認" in result["match"]["risks"]
        assert result["stillInFilters"]
        expect(page.locator("#school-detail-primary-facts")).to_contain_text(
            "條件待補齊"
        )
        common = {
            "college": college,
            "degree_level": degree,
            "academic_score": 85,
            "academic_gpa": 3.5,
        }
        response = page.request.post(
            live_server.base_url + "/advisor/plan",
            data=dict(school_name=HOME, target_school=partner.school_name, **common),
        )
        assert response.ok, response.text()
        target = response.json()["target_match"]
        assert not target["blocking_reasons"]
        assert not {"符合學院範圍", "符合目前學制"} & set(target["reasons"])
        response = page.request.post(
            live_server.base_url + "/application-plan/evaluate",
            data=dict(
                home_school=HOME,
                preferences=[{"rank": 1, "school_name": partner.school_name}],
                **common,
            ),
        )
        assert response.ok, response.text()
        checks = {r["code"]: r for r in response.json()["choices"][0]["checks"]}
        assert (
            checks["college"]["status"]
            == checks["degree_level"]["status"]
            == "needs_confirmation"
        )
    output = Path("/tmp/ccu-parent-fixes-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"pending-{source_page}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_actual_template_clicks_and_document_center_stages(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    partner = at(32)
    page.goto(
        live_server.base_url
        + "/?school="
        + quote(HOME)
        + "#school="
        + quote(partner.school_name)
    )
    expect(page.locator("#detail-tab-application")).to_be_visible(timeout=30_000)
    page.locator("#detail-tab-application").click()
    step = page.locator("details.workflow-step").filter(has_text="學習計畫指定表")
    step.locator("> summary").click()
    plan = step.locator(".workflow-documents li").filter(has_text="學習計畫指定表")
    url = "https://intl.ryukoku.ac.jp/zx_documents/application_Form/01_plan_of_Study_w.docx"
    link = plan.locator("a")
    expect(link).to_have_attribute("href", url)
    expect(plan).to_contain_text("流程尚未發布")
    source = json.loads((BUNDLE / "overseas_sources/p32-r7-plan-form.json").read_text())
    binary = (BUNDLE / source["bundled_file"]).read_bytes()
    # Browser navigation is replayed from the actual fetched, hashed official DOCX.
    # Live HTTP availability is checked separately in the validation evidence.
    page.context.route(
        url,
        lambda route: route.fulfill(
            status=200,
            body=binary,
            headers={
                "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "Content-Disposition": 'attachment; filename="ryukoku-plan.docx"',
            },
        ),
    )
    with page.expect_download() as download:
        link.click()
    assert (
        hashlib.sha256(Path(download.value.path()).read_bytes()).hexdigest()
        == source["sha256"]
    )
    page.evaluate("location.hash='#application-center'")
    page.evaluate(
        """async name => {state.applicationContext.target_school=name;await loadApplicationTemplates();}""",
        partner.school_name,
    )
    catalog = page.locator("#application-requirement-list")
    group = catalog.locator("details.application-requirement-group").filter(
        has_text="學習計畫指定表"
    )
    if not group.evaluate("node=>node.open"):
        group.locator("> summary").click()
    item = group.locator("article").filter(has_text="學習計畫指定表")
    expect(item).to_be_visible()
    expect(item).to_contain_text("適用性、完整清單及送件細節仍待確認")
    expect(item.locator("a")).to_have_attribute("href", url)
    with page.expect_download() as download:
        item.locator("a").click()
    assert (
        hashlib.sha256(Path(download.value.path()).read_bytes()).hexdigest()
        == source["sha256"]
    )
    page.evaluate(
        """async name => {state.applicationContext.target_school=name;await loadApplicationTemplates();}""",
        at(53).school_name,
    )
    later = catalog.locator("details.application-requirement-group").filter(
        has=page.locator("summary strong").filter(has_text="合作校申請後補件")
    )
    expect(later).to_have_count(1)
    later.locator("> summary").click()
    expect(later.locator("article")).to_have_count(2)
    expect(later).to_contain_text("12/20上傳；1/15正本抵校")
    expect(later).not_to_contain_text("健康／TB")
    later.scroll_into_view_if_needed()
    output = Path("/tmp/ccu-parent-fixes-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"document-stages-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_seoultech_new_housing_costs_and_second_submission_are_visible(
    page, live_server, width
):
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script(
        "localStorage.setItem('exchange-guide-home-school','國立中正大學')"
    )
    partner = at(48)
    page.goto(
        live_server.base_url
        + "/?school="
        + quote(HOME)
        + "#school="
        + quote(partner.school_name)
    )
    section = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(section).to_be_visible(timeout=30_000)
    for key, expected in [
        ("housing", "不保證"),
        ("costs", "1329120"),
        ("course_restrictions", "最少3"),
    ]:
        field = section.locator(f'[data-ccu-field="{key}"]')
        field.locator("> summary").click()
        expect(field).to_contain_text(expected)
    documents = section.locator('[data-ccu-field="documents"]')
    documents.locator("> summary").click()
    expect(documents).to_contain_text("未列銀行認證")
    expect(documents).not_to_contain_text("在學／成績及銀行正本另需條件認證")
    visa = section.locator('[data-ccu-field="visa"]')
    visa.locator("> summary").click()
    expect(visa).to_contain_text("銀行只列USD6000一期／12000一年資金證明，未列認證")
    page.locator("#detail-tab-application").click()
    second = page.locator("details.workflow-step").filter(
        has_text="合作校第二次文件送件"
    )
    second.locator("> summary").click()
    expect(second).to_contain_text("不猜錄取前後")
    requirements = second.locator(".workflow-documents li")
    expect(requirements).to_have_count(3)
    for item in requirements.all():
        expect(item).to_contain_text("第二次文件送件（時點待確認）")
        expect(item).not_to_contain_text("不等錄取")
    expect(second.locator(".workflow-documents")).to_contain_text("本人銀行")
    expect(second.locator(".workflow-documents")).to_contain_text("韓國簽證")
    response = page.request.get(
        live_server.base_url + "/application-center/catalog",
        params={"school": HOME, "target_school": partner.school_name},
    )
    assert response.ok
    items = [r for r in response.json()["items"] if r["stage"] == "second_submission"]
    assert len(items) == 3 and all(r["phase"] == "合作校第二次文件送件" for r in items)
    bank = next(r for r in items if "銀行" in r["name"])
    assert bank["stamps"] == []
    page.evaluate("location.hash='#application-center'")
    page.evaluate(
        """async name => {state.applicationContext.target_school=name;await loadApplicationTemplates();}""",
        partner.school_name,
    )
    group = page.locator("#application-requirement-list details.application-requirement-group").filter(
        has=page.locator("summary strong").filter(has_text="合作校第二次文件送件")
    )
    expect(group).to_have_count(1)
    if not group.evaluate("node=>node.open"):
        group.locator("> summary").click()
    expect(group.locator("article")).to_have_count(3)
    expect(group).not_to_contain_text("不等錄取")
    output = Path("/tmp/ccu-fourteenth-browser")
    output.mkdir(exist_ok=True)
    group.scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"seoultech-second-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_hcmut_current_deadlines_and_nomination_template_click(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    partner = at(67)
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    section = page.locator("#detail-overview .ccu-receiving-school-details")
    expect(section).to_be_visible(timeout=30_000)
    for key, value in [("nomination_deadline", "2026-09-30"), ("application_deadline", "2026-10-15")]:
        field = section.locator(f'[data-ccu-field="{key}"]')
        field.locator("> summary").click()
        expect(field).to_contain_text(value)
    page.locator("#detail-tab-application").click()
    step = page.locator("details.workflow-step").filter(
        has=page.locator(".workflow-documents li").filter(has=page.locator("b").filter(has_text="提名信"))
    )
    expect(step).to_have_count(1)
    if not step.evaluate("node=>node.open"):
        step.locator("> summary").click()
    nomination = step.locator(".workflow-documents li").filter(has=page.locator("b").filter(has_text="提名信"))
    expect(nomination).to_contain_text("Seal")
    source = json.loads((BUNDLE / "overseas_sources/p67-r16-nomination-template.json").read_text())
    url = source["source_url"]
    link = nomination.locator("a")
    expect(link).to_have_attribute("href", url)
    binary = (BUNDLE / source["bundled_file"]).read_bytes()
    page.context.route(url, lambda route: route.fulfill(
        status=200, body=binary,
        headers={"Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "Content-Disposition": 'attachment; filename="hcmut-nomination.docx"'},
    ))
    with page.expect_download() as download:
        link.click()
    assert hashlib.sha256(Path(download.value.path()).read_bytes()).hexdigest() == source["sha256"]
    output = Path("/tmp/ccu-sixteenth-browser")
    output.mkdir(exist_ok=True)
    step.scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"hcmut-nomination-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
