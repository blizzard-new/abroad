"""Annual calendars, old factsheets and gated forms remain scoped in the UI."""
import os
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("ccu_page", [56, 59, 75])
def test_convergence_reference_years_and_access_survive_rendering(page, live_server, width, ccu_page):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == ccu_page)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote("國立中正大學") + "#school=" + quote(partner.school_name))
    reference = page.locator("#detail-overview .ccu-reference-host")
    expect(reference).to_contain_text("中正本期未開放", timeout=30_000)
    expect(reference.locator("[data-ccu-reference-field]")).to_have_count(17)
    key = "application_forms" if ccu_page == 59 else "academic_calendar"
    field = reference.locator(f'[data-ccu-reference-field="{key}"]')
    field.locator("> summary").click()
    if ccu_page == 56:
        expect(field).to_contain_text("2026/27")
        expect(field).to_contain_text("05-04至17")
        expect(field).to_contain_text("學程例外")
        expect(field.locator('a[href*="000000000017784742948701Lcf4"]')).to_have_attribute(
            "href", "https://www.eduhk.hk/re/uploads/docs/000000000017784742948701Lcf4#page=2")
    elif ccu_page == 59:
        expect(field.locator("> summary")).to_contain_text("待確認")
        expect(field).to_contain_text("未取得表格正文")
        expect(field).to_contain_text("未註冊/登入/填送")
    else:
        expect(field.locator("> summary")).to_contain_text("參考")
        expect(field).to_contain_text("2021")
        expect(field).to_contain_text("不是2027")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if folder := os.environ.get("CCU_ROUND9_SCREENSHOTS"):
        target = Path(folder)
        target.mkdir(parents=True, exist_ok=True)
        reference.screenshot(path=str(target / f"p{ccu_page}-{width}.png"))
