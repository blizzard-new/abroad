"""Eighth-round receiving evidence keeps its years, uncertainty and home scope."""
import os
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("ccu_page", [92, 117])
def test_round8_years_and_price_basis_survive_reference_rendering(page, live_server, width, ccu_page):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == ccu_page)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote("國立中正大學") + "#school=" + quote(partner.school_name))
    reference = page.locator("#detail-overview .ccu-reference-host")
    expect(reference).to_contain_text("中正本期未開放", timeout=30_000)
    expect(reference.locator("[data-ccu-reference-field]")).to_have_count(17)
    if ccu_page == 117:
        deadline = reference.locator('[data-ccu-reference-field="application_deadline"]')
        deadline.locator("> summary").click()
        expect(deadline.locator("> summary")).to_contain_text("待確認")
        expect(deadline).to_contain_text("不能直接生成2026-11-15確定提醒")
        insurance = reference.locator('[data-ccu-reference-field="insurance"]')
        insurance.locator("> summary").click()
        expect(insurance).to_contain_text("共7月USD1396.28")
        expect(insurance.locator('a[href*="health-insurance"]')).to_have_count(1)
        arrival = reference.locator('[data-ccu-reference-field="arrival"]')
        arrival.locator("> summary").click()
        expect(arrival.locator("> summary")).to_contain_text("來源矛盾")
    else:
        costs = reference.locator('[data-ccu-reference-field="costs"]')
        costs.locator("> summary").click()
        expect(costs.locator("> summary")).to_contain_text("來源矛盾")
        expect(costs).to_contain_text("EUR300/semester")
        expect(costs).to_contain_text("EUR1050/4.65/41.50")
        expect(costs).to_contain_text("不把年費除2/除月")
        expect(costs.locator('a[href*="260824_TARIFAS_AUTOBUSES_USJ_26_27.pdf"]')).to_have_attribute(
            "href", "https://www.usj.es/sites/default/files/archivos/260824_TARIFAS_AUTOBUSES_USJ_26_27.pdf#page=1"
        )
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if folder := os.environ.get("CCU_ROUND8_SCREENSHOTS"):
        target = Path(folder)
        target.mkdir(parents=True, exist_ok=True)
        reference.screenshot(path=str(target / f"p{ccu_page}-{width}.png"))
