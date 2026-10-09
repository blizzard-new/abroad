"""School detail screens show confirmed delivery scope and later public forms."""

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
    page.locator("#detail-tab-application").click()


def screenshot(page, label, width):
    output = Path("/tmp/ccu-twentysecond-browser")
    output.mkdir(exist_ok=True)
    page.screenshot(path=str(output / f"{label}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
def test_nasic_delivery_is_unknown_despite_email_notices(page, live_server, width):
    open_detail(page, live_server, width, 32)
    step = page.locator("details.workflow-step").filter(has_text="NASIC誓約書")
    step.locator("> summary").click()
    expect(step.locator(".workflow-submission")).to_contain_text("送件方式待確認")
    expect(step.locator(".workflow-submission")).not_to_contain_text("電子郵件 送件")
    step.locator(".workflow-submission").scroll_into_view_if_needed()
    screenshot(page, "nasic-delivery-unknown", width)


@pytest.mark.parametrize("width", [390, 1440])
def test_khu_second_submission_does_not_wait_for_admission(page, live_server, width):
    open_detail(page, live_server, width, 45)
    step = page.locator("details.workflow-step").filter(has_text="Google Form確切期限TBA")
    step.locator("> summary").click()
    expect(step).to_contain_text("未明示須等錄取")
    expect(step.locator(".workflow-submission")).to_contain_text("混合送件")
    expect(step.locator(".workflow-submission")).to_contain_text("非OECD")
    expect(step).to_contain_text("第二次文件送件")
    step.locator(".workflow-submission").scroll_into_view_if_needed()
    screenshot(page, "khu-neutral-google-followup", width)


@pytest.mark.parametrize("width", [390, 1440])
def test_jena_extension_form_has_both_signatures_and_stamps(page, live_server, width):
    open_detail(page, live_server, width, 99)
    step = page.locator("details.workflow-step").filter(has_text="Jena交换延期申请及双方确认")
    step.locator("> summary").click()
    item = step.locator(".workflow-documents li").filter(has_text="Jena交换延期申请及双方确认")
    expect(item).to_contain_text("母校International Office")
    expect(item).to_contain_text("Jena International Office")
    expect(item).to_contain_text("核章")
    expect(item).to_contain_text("當期適用待確認")
    expect(item.locator("a")).to_have_attribute("href", "https://www.uni-jena.de/unijenamedia/66670/gaststud-verlaengerung.doc")
    item.scroll_into_view_if_needed()
    screenshot(page, "jena-later-extension-form", width)
