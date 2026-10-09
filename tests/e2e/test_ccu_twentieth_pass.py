"""Current requirements and pending template versions on actual CCU detail pages."""

from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities

HOME = "國立中正大學"


def at(source_page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page)


def open_detail(page, live_server, width, source_page):
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(at(source_page).school_name))
    expect(page.locator("#detail-tab-application")).to_be_visible(timeout=30_000)


def screenshot(page, label, width):
    output = Path("/tmp/ccu-twentieth-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"{label}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("needle,url_part", [
    ("宿舍申請表", "1xThdiWsgT4IZ5Tco7UZnpUGFDA16Hknf"),
    ("健康／TB", "1NwoAHiWT7p3yJO1s-YqyhZCSRN0YQiBy"),
])
def test_hufs_templates_show_pending_version_and_real_signers(page, live_server, width, needle, url_part):
    open_detail(page, live_server, width, 47)
    page.locator("#detail-tab-application").click()
    step = page.locator("details.workflow-step").filter(
        has=page.locator(".workflow-documents li b").filter(has_text=needle)
    )
    step.locator("> summary").click()
    item = step.locator(".workflow-documents li").filter(has_text=needle)
    expect(item).to_contain_text("學生")
    assert url_part in item.locator("a").get_attribute("href")
    if needle == "宿舍申請表":
        expect(item).to_contain_text("2027模板新版尚未核實")
    else:
        expect(item).to_contain_text("Clinician")
        expect(item).to_contain_text("宿舍分配後")
        expect(item).to_contain_text("Global未明示可用skin")
    screenshot(page, "hufs-health" if needle == "健康／TB" else "hufs-dorm", width)


@pytest.mark.parametrize("width", [390, 1440])
def test_dit_extra_grade_sheet_stays_pending_and_conditional(page, live_server, width):
    open_detail(page, live_server, width, 101)
    page.locator("#detail-tab-application").click()
    step = page.locator("details.workflow-step").filter(
        has=page.locator(".workflow-documents li b").filter(has_text="exam grade sheet")
    )
    step.locator("> summary").click()
    item = step.locator(".workflow-documents li").filter(has_text="exam grade sheet")
    expect(item).to_contain_text("當期適用待確認")
    expect(item).to_contain_text("是否與transcript相同")
    expect(item).to_contain_text("09.2026")
    screenshot(page, "dit-extra-grade", width)


@pytest.mark.parametrize("width", [390, 1440])
def test_hiof_course_conditions_keep_campus_and_semester_scope(page, live_server, width):
    open_detail(page, live_server, width, 114)
    field = page.locator('#detail-overview [data-ccu-field="course_restrictions"]')
    expect(field).to_contain_text("Fredrikstad", timeout=30_000)
    expect(field).to_contain_text("Autumn2027")
    expect(field).to_contain_text("最低人數")
    screenshot(page, "hiof-scope", width)
