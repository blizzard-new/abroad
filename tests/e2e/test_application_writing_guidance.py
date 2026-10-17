"""Live character counts, expandable writing guidance, and the Word download beside the PDF one."""
from io import BytesIO
from uuid import uuid4

import pytest
from docx import Document
from playwright.sync_api import expect

from .conftest import login_through_web
from .test_glass_theme import capture
from .test_web_next_phase import _fill_required_application_fields


def open_study_plan(page, live_server, university="長庚大學"):
    email = f"guidance-{uuid4().hex[:8]}@example.com"
    session = live_server.register(email)
    live_server.verify_student(session["profile"]["id"], university=university)
    login_through_web(page, live_server, email)
    page.evaluate("location.hash='#application-form=study-plan'")
    expect(page.locator("#application-document-form")).to_be_visible()
    expect(page.locator('[data-field-counter="motivation"]')).to_be_visible(timeout=15_000)


@pytest.mark.parametrize("width", [390, 1754])
def test_each_long_field_shows_a_live_count_and_opens_plain_language_guidance(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_study_plan(page, live_server)

    counter = page.locator('[data-field-counter="motivation"]')
    expect(counter).to_contain_text("0 / 1,800 字")
    expect(page.locator('[data-field-counter="motivation"] + .application-field-counter-hint')).to_contain_text("建議 300–600 字")
    page.locator('#application-document-fields [name="motivation"]').fill("我開心")
    expect(counter).to_contain_text("3 / 1,800 字")
    page.locator('#application-document-fields [name="motivation"]').fill("字" * 1700)
    expect(counter).to_have_class("application-field-counter is-near")

    toggle = page.locator('[aria-controls="application-guide-motivation"]')
    panel = page.locator("#application-guide-motivation")
    expect(panel).to_be_hidden()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(panel).to_be_visible()
    expect(panel).to_contain_text("怎麼寫")
    expect(panel).to_contain_text("建議架構")
    expect(panel).to_contain_text("示範寫法（請改寫成你自己的內容）")
    expect(panel).to_contain_text("不一定等於學校規定")
    expect(panel).to_contain_text("不是學校規定")
    capture(page, f"writing-guidance-open-{width}.png")
    toggle.click()
    expect(panel).to_be_hidden()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    # No school rule has been checked for the default school, and the page says that plainly.
    notice = page.locator("#application-writing-rules")
    expect(notice).to_contain_text("尚未收錄")
    expect(notice).to_contain_text("不是學校規定")
    expect(page.locator("#application-writing-total")).to_have_count(0)
    assert errors == []


def test_school_word_limit_is_totalled_across_the_fields_it_covers(page, live_server):
    open_study_plan(page, live_server, university="國立臺北大學")
    rules = page.locator("#application-writing-rules")
    expect(rules).to_be_visible()
    expect(rules).to_contain_text("學校對這份文件的規定")
    expect(rules).to_contain_text("合計 5,000 字以內")
    expect(rules).to_contain_text("查核依據：臺北大學 116 學年度赴外交換簡章")
    total = page.locator("#application-writing-total")
    expect(total).to_contain_text("還沒開始寫")
    page.locator('#application-document-fields [name="motivation"]').fill("甲" * 1800)
    page.locator('#application-document-fields [name="school_reason"]').fill("乙" * 1800)
    page.locator('#application-document-fields [name="learning_goals"]').fill("丙" * 1800)
    expect(page.locator("[data-writing-total]")).to_have_text("5,400")
    expect(total).to_have_class("application-writing-total is-over")
    expect(total).to_contain_text("超過上限 400 字")
    capture(page, "writing-rules-over-limit.png")
    # Blanks and line breaks are not counted, matching how schools count written characters.
    page.locator('#application-document-fields [name="learning_goals"]').fill("丙 丙\n丙" * 100)
    expect(page.locator("[data-writing-total]")).to_have_text("3,900")
    expect(total).to_have_class("application-writing-total is-ok")
    expect(total).to_contain_text("目前在字數規定範圍內")
    expect(total).to_contain_text("學校規定的是整份計畫書合計")
    # The field-level panel points back to the school rule instead of inventing a per-field limit.
    page.locator('[aria-controls="application-guide-learning_goals"]').click()
    expect(page.locator("#application-guide-learning_goals")).to_contain_text("整份文件的字數限制")


def test_word_download_follows_the_same_review_gate_as_pdf_and_produces_an_editable_file(page, live_server):
    open_study_plan(page, live_server)
    word = page.locator("#download-single-application-docx")
    pdf = page.locator("#download-single-application-document")
    expect(word).to_be_visible()
    expect(word).to_be_disabled()
    expect(pdf).to_be_disabled()
    _fill_required_application_fields(page)
    page.locator('#application-document-form button[type="submit"]').click()
    review = page.locator("[data-application-review-template]")
    expect(review).to_be_enabled(timeout=15_000)
    review.check()
    expect(word).to_be_enabled()
    expect(pdf).to_be_enabled()
    with page.expect_download() as download_info:
        word.click()
    download = download_info.value
    assert download.suggested_filename.endswith(".docx")
    document = Document(BytesIO(download.path().read_bytes()))
    cells = [cell.text for table in document.tables for row in table.rows for cell in row.cells]
    assert any("E2E 自動化驗收用的完整申請內容" in text for text in cells)
    capture(page, "word-download-buttons.png")
    # Editing after review locks both downloads again until the content is re-checked.
    page.locator('#application-document-fields [name="motivation"]').fill("核對後又改了一次")
    expect(word).to_be_disabled()
    expect(pdf).to_be_disabled()
