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
    page.set_viewport_size(dict(width=width, height=956))
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


def test_all_four_school_grade_fields_remain_isolated(page, live_server):
    page.set_viewport_size(dict(width=1440, height=956))
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
