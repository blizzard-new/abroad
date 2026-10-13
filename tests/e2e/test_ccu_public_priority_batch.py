"""Dated references and unresolved scopes survive desktop/mobile rendering."""
import os
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("ccu_page", [63, 84, 115])
def test_public_priority_fields_keep_closed_home_and_scoped_years(page, live_server, width, ccu_page):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages == [ccu_page])
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote("國立中正大學") + "#school=" + quote(partner.school_name))
    ref = page.locator("#detail-overview .ccu-reference-host")
    expect(ref).to_contain_text("中正本期未開放", timeout=30_000)
    expect(ref.locator("[data-ccu-reference-field]")).to_have_count(17)
    field_name = "application_deadline" if ccu_page == 63 else "language" if ccu_page == 84 else "costs"
    field = ref.locator(f'[data-ccu-reference-field="{field_name}"]')
    field.locator("> summary").click()
    if ccu_page == 63:
        expect(field).to_contain_text("2024-10-03")
        expect(field.locator("> summary")).to_contain_text("參考")
        expect(field).to_contain_text("不是2027")
    elif ccu_page == 84:
        expect(field.locator("> summary")).to_contain_text("來源矛盾")
        expect(field).to_contain_text("English B2")
        expect(field.locator('a[href*="Language-requirements"]')).to_have_count(1)
        dates = ref.locator('[data-ccu-reference-field="nomination_deadline"]')
        dates.locator("> summary").click()
        expect(dates).to_contain_text("2026-10-01")
        expect(dates).to_contain_text("不是中正校內梯次")
    else:
        expect(field.locator("> summary")).to_contain_text("待確認")
        expect(field).to_contain_text("USD11351")
        expect(field).to_contain_text("分期款而非月租")
        expect(field).to_contain_text("Spring單期")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if folder := os.environ.get("CCU_PRIORITY_SCREENSHOTS"):
        target = Path(folder)
        target.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(target / f"p{ccu_page}-{width}.png"), full_page=True)
