"""October 17 references stay readable and pending on phones and desktops."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site
from .test_open_catalog import wait_until


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("school,markers", [
    ("里約熱內盧天主教大學", ["2027/4/15", "檔名2026", "非臺大"]),
    ("安地斯大學", ["2026/27", "18,400,000–27,700,000", "17,100,000–25,300,000", "不蓋過臺大B2"]),
    ("肯特大學", ["116-1", "Autumn Term", "不證明一律禁止"]),
    ("奧塔哥大學", ["期限前", "deadline"]),
])
def test_oct17_reference_conditions_and_years(page, live_server, width, school, markers):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立臺灣大學"]').click()
    if width < 700 and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '國立臺灣大學'")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill(school)
    expect(page.locator("#partner-table")).to_contain_text("本期名額待核實")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    detail = page.locator("#school-detail-view")
    expect(detail).to_be_visible()
    expect(page.locator("#booking-home-deadline")).to_contain_text("2026-11-09 16:00")
    expect(page.locator("#booking-partner-deadline")).not_to_contain_text("2026/11/09")
    expect(detail).to_contain_text("欄位資料與官方依據")
    expect(detail).not_to_contain_text("中正校內資格")
    summary = detail.get_by_role("region", name="合作校條件", exact=True)
    for marker in markers:
        expect(summary).to_contain_text(marker)
    expect(summary).to_contain_text("尚未全面核實")
    receiving = detail.get_by_role("region", name="合作校接收資料", exact=True)
    expect(receiving).to_contain_text("臺大的校內資格")
    expect(receiving).not_to_contain_text("中正的校內資格")
    field = "deadlines" if "里約" in school else "cost" if "安地斯" in school else "calendar" if school == "肯特大學" else "housing"
    reference = receiving.locator(f'[data-ccu-field="{field}"]')
    reference.locator(":scope > summary").click()
    expect(reference.locator(":scope > p").first).to_be_visible()
    expect(reference).to_contain_text("來源矛盾" if field == "cost" else "尚未確認臺大本期適用")
    reference.scroll_into_view_if_needed()
    assert page.evaluate(
        "(name) => state.dashboard.partner_universities.find(p => p.school_name.includes(name)).quota", school,
    ) is None
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
    destination = Path(os.environ.get("NTU_OCT17_SCREENSHOTS", "/tmp/ntu-oct17-browser"))
    destination.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(destination / f"{school}-{width}.png"))
