"""Actual CCU detail pages preserve dates, conditional phases and private forms."""

from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def open_detail(page, live_server, width, source_page):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page)
    page.set_viewport_size({"width": width, "height": 956})
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote("國立中正大學") + "#school=" + quote(partner.school_name))
    expect(page.locator("#detail-tab-application")).to_be_visible(timeout=30_000)


def show_document(page, needle):
    page.locator("#detail-tab-application").click()
    step = page.locator("details.workflow-step").filter(has=page.locator(".workflow-documents li b").filter(has_text=needle))
    step.locator("> summary").click()
    item = step.locator(".workflow-documents li").filter(has_text=needle)
    item.scroll_into_view_if_needed()
    return item


def screenshot(page, label, width):
    output = Path("/tmp/ccu-twentyfirst-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"{label}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_ryukoku_conflict_and_later_signed_pledge_are_visible(page, live_server, width):
    open_detail(page, live_server, width, 32)
    field = page.locator('#detail-overview [data-ccu-field="arrival"]')
    expect(field).to_contain_text("9/10", timeout=30_000)
    expect(field).to_contain_text("3/25")
    expect(field).to_contain_text("矛盾")
    item = show_document(page, "NASIC誓約書")
    expect(item).to_contain_text("學生")
    expect(item).to_contain_text("初次申請")
    expect(item).to_contain_text("後發")
    screenshot(page, "ryukoku-conflict-pledge", width)


@pytest.mark.parametrize("width", [390, 1440])
def test_fhnw_grant_remains_conditional_and_template_unverified(page, live_server, width):
    open_detail(page, live_server, width, 104)
    item = show_document(page, "SEMP／FHNW worldwide")
    expect(item).to_contain_text("非人人保證獎助")
    expect(item).to_contain_text("LetterofAcceptance")
    expect(item).to_contain_text("當期適用待確認")
    expect(item).to_contain_text("個人期限")
    screenshot(page, "fhnw-conditional-grant", width)


@pytest.mark.parametrize("width", [390, 1440])
def test_sdu_city_specific_reply_days_and_later_contract_are_visible(page, live_server, width):
    open_detail(page, live_server, width, 89)
    field = page.locator('#detail-overview [data-ccu-field="housing_deadline"]')
    expect(field).to_contain_text("Esbjerg住房offer回覆7日", timeout=30_000)
    expect(field).to_contain_text("Odense住房offer回覆6日")
    item = show_document(page, "住房租約／WelcomeLetter")
    expect(item).to_contain_text("無公開2027空白合約")
    expect(item).to_contain_text("初次交換申請")
    screenshot(page, "sdu-city-contract", width)
