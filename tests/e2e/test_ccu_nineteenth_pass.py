"""New official host forms and current course exclusions on real detail pages."""

from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities

HOME = "國立中正大學"


def at(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("source_page,needle,url_part", [
    (80, "Inbound Exchange", "6818985ddb4fe1746442333.pdf"),
    (107, "Accommodation Letter of Intent", "proof_of_accommodation_140338.pdf"),
])
def test_pending_host_forms_render_correct_role_and_stage(page, live_server, width, source_page, needle, url_part):
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(at(source_page).school_name))
    expect(page.locator("#detail-tab-application")).to_be_visible(timeout=30_000)
    page.locator("#detail-tab-application").click()
    step = page.locator("details.workflow-step").filter(
        has=page.locator(".workflow-documents li b").filter(has_text=needle)
    )
    step.locator("> summary").click()
    item = step.locator(".workflow-documents li").filter(has_text=needle)
    expect(item).to_contain_text("當期適用待確認")
    assert url_part in item.locator("a").get_attribute("href")
    if source_page == 107:
        expect(item).to_contain_text("適用條件：僅需宿舍住宿文件者")
        expect(item).to_contain_text("階段：錄取後")
    else:
        expect(item).to_contain_text("母校")
        assert "6818987ff360e1746442367.pdf" not in page.locator("#detail-application").inner_text()
    output = Path("/tmp/ccu-nineteenth-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"pending-form-{source_page}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_tbu_current_course_restrictions_are_visible(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(at(108).school_name))
    field = page.locator('#detail-overview [data-ccu-field="course_restrictions"]')
    expect(field).to_contain_text("AE8SV", timeout=30_000)
    expect(field).to_contain_text("2026/27不開")
    expect(field).to_contain_text("1PE3E只限Master")
    expect(field).to_contain_text("課程席次")
    output = Path("/tmp/ccu-nineteenth-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"tbu-course-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
