"""Real matching, scheduling and persistence; official date cases use isolated fixtures."""
from datetime import date, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from playwright.sync_api import expect

from exchange_info.models import ApplicationStep, UniversityApplicationWorkflow
from .conftest import expand_details
from .test_glass_theme import capture, verified_login
from .test_web_next_phase import _auth_headers, _fill_required_application_fields, _wait_for_workspace


def workflow_fixture(route, case="valid"):
    params = parse_qs(urlparse(route.request.url).query)
    deadline = date.today() + timedelta(days=40 if case != "expired" else -1)
    workflow = UniversityApplicationWorkflow(
        workflow_id="isolated-planning-fixture",
        school_name=params["school"][0], home_university="長庚大學",
        academic_year="115" if case == "wrong_year" else "116",
        applicability_status="needs_confirmation" if case == "unverified" else "verified",
        review_status="draft" if case == "unpublished" else "published",
        application_round="第二梯次" if case == "wrong_round" else None,
        steps=[ApplicationStep(
            rule_id="fixture-online-submission", order=1, phase="申請",
            title="測試官方送件", responsible_party="學生", summary="隔離測試期限",
            deadline_at=f"{deadline.isoformat()}T23:59:00+08:00",
            deadline_status="verified_exact", deadline_reminder_eligible=True,
            deadline_source_url=None if case == "missing_source" else "https://www.cgu.edu.tw/oia-ch/fixture-source",
            submission={"method":"online"},
        )],
    )
    route.fulfill(json=workflow.model_dump(mode="json"))


def create_target(page, live_server):
    session = verified_login(page, live_server)
    page.evaluate("location.hash='#advisor'")
    expect(page.locator("#advisor-form")).to_be_visible()
    page.wait_for_function("() => document.querySelector('#advisor-college').options.length > 1")
    college = page.locator("#advisor-college option").evaluate_all("items=>items.find(item=>item.value).value")
    page.locator("#advisor-college").select_option(college)
    page.locator("#advisor-degree").select_option("大學部")
    expand_details(page, "#advisor-qualification-fields")
    page.locator("#advisor-academic-score").fill("85")
    page.locator("#advisor-language-test").select_option("ielts")
    page.locator("#advisor-language-score").fill("7")
    with page.expect_response(lambda response: response.url.endswith("/advisor/plan") and response.request.method == "POST") as result:
        page.locator("#advisor-submit").click()
    assert result.value.ok
    plan = result.value.json()
    target = plan["recommendations"][0]["school_name"]
    page.locator("#advisor-result-content [data-planning-target]").first.click()
    expect(page.locator("#overview")).to_be_visible()
    expect(page.locator("#planning-target-summary")).to_contain_text(target)
    expect(page.locator("#application-target-school")).to_have_value(target)
    expect(page.locator("#recommended-match-list [data-planning-target]").first).to_have_attribute("data-planning-target", target)
    page.locator("#planning-deadline-settings > summary").click()
    return session, target


@pytest.mark.parametrize("width", [390, 1754])
def test_matching_target_schedule_preview_and_idempotent_save(page, live_server, width):
    page.set_viewport_size({"width":width,"height":956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.route("**/application-workflow?**", workflow_fixture)
    session, target = create_target(page, live_server)
    page.locator("#planning-academic-year").fill("116")
    page.locator("#planning-preparation-days").fill("12")
    page.locator("#planning-preview-button").click()
    expect(page.locator("#planning-schedule-preview")).to_contain_text((date.today()+timedelta(days=28)).isoformat())
    expect(page.locator("#planning-confirm")).to_be_visible()
    before = requests.get(f"{live_server.base_url}/account/workspace",params={"home_school":"長庚大學"},headers=_auth_headers(session)).json()
    assert not any(event["id"].startswith("preparation-") for event in before["workspace"].get("deadline_events",[]))
    page.locator("#planning-confirm").click()
    expect(page.locator("#planning-schedule-status")).to_contain_text("已加入 1 項")
    saved = _wait_for_workspace(live_server, session, lambda item: any(event["id"].startswith("preparation-") for event in item["workspace"].get("deadline_events",[])))["workspace"]
    event = next(event for event in saved["deadline_events"] if event["id"].startswith("preparation-"))
    assert event["school_name"] == target and event["preparation_days"] == 12
    page.locator("#planning-preview-button").click()
    expect(page.locator("#planning-schedule-status")).to_contain_text("已存在")
    page.locator("#planning-confirm").click()
    expect(page.locator("#planning-schedule-status")).to_contain_text("沒有重複加入")
    page.locator("#planning-preparation-days").fill("10")
    page.locator("#planning-preview-button").click()
    expect(page.locator("#planning-confirm")).to_be_visible()
    page.locator("#planning-preparation-days").fill("11")
    expect(page.locator("#planning-confirm")).to_be_hidden()
    expect(page.locator("#planning-schedule-status")).to_contain_text("重新預覽")
    page.locator("#planning-preview-button").click()
    expect(page.locator("#planning-confirm")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    capture(page, f"planning-preview-{width}.png")
    page.reload()
    expect(page.locator("#planning-target-summary")).to_contain_text(target)
    expect(page.locator("#recommended-match-list [data-planning-target]").first).to_have_attribute("data-planning-target", target)
    assert not errors


@pytest.mark.parametrize("case", ["expired","unverified","wrong_year","missing_source","wrong_round","unpublished"])
def test_schedule_refuses_unconfirmed_or_unusable_dates(page, live_server, case):
    page.route("**/application-workflow?**", lambda route: workflow_fixture(route, case))
    create_target(page, live_server)
    page.locator("#planning-academic-year").fill("116")
    if case == "wrong_round":
        page.locator("#planning-application-round").fill("第一梯次")
    page.locator("#planning-preview-button").click()
    expect(page.locator("#planning-schedule-status")).to_contain_text("目前")
    expect(page.locator("#planning-confirm")).to_be_hidden()
    expect(page.locator(".planning-timeline-item")).to_have_count(0)


@pytest.mark.parametrize("width", [390, 1754])
def test_print_packet_remains_blocked_until_current_content_review(page, live_server, width):
    page.set_viewport_size({"width":width,"height":956})
    page.emulate_media(reduced_motion="reduce")
    verified_login(page, live_server)
    page.evaluate("location.hash='#application-center'")
    packet = page.locator(".application-packet-panel")
    expect(packet).to_be_visible()
    area = page.locator(".application-template-area").bounding_box()
    packet_bounds = packet.bounding_box()
    if width > 1200:
        assert packet_bounds["x"] >= area["x"] + area["width"]
        assert packet_bounds["height"] <= 956 - 48
    else:
        assert packet_bounds["y"] >= area["y"] + area["height"]
    expect(packet.locator(".application-packet-row")).to_have_count(0)
    checkbox = page.locator(".application-template-stage[open] [data-application-packet-template]").first
    checkbox.check()
    template_id = checkbox.get_attribute("data-application-packet-template")
    expect(page.locator("#application-packet-progress")).to_contain_text("已選 1 項")
    expect(page.locator("#download-application-packet")).to_be_disabled()
    packet.locator(".packet-print-details summary").first.click()
    expect(packet.locator(".application-packet-print").first).to_contain_text("A4")
    packet.locator(".packet-row-controls a").first.click()
    _fill_required_application_fields(page)
    page.locator("#application-document-form button[type=submit]").click()
    review = page.locator("[data-application-review-template]")
    expect(review).to_be_enabled(timeout=15000)
    review.check()
    page.evaluate("location.hash='#application-center'")
    expect(page.locator("#download-application-packet")).to_be_enabled(timeout=15000)
    expect(page.locator("#application-packet-progress")).to_contain_text("1 項可匯出")
    with page.expect_download(timeout=30000) as generated:
        page.locator("#download-application-packet").click()
    download = generated.value
    assert download.failure() is None
    assert download.suggested_filename.endswith(".pdf")
    with open(download.path(), "rb") as pdf:
        assert pdf.read(5) == b"%PDF-"
    expect(page.locator("#application-download-dialog")).to_be_visible()
    page.locator("#application-download-dialog footer [data-close-application-download]").click()
    page.locator(f'[data-application-copy-template="{template_id}"]').fill("2")
    expect(page.locator("#download-application-packet")).to_be_disabled()
    expect(page.locator("#application-packet-status")).to_contain_text("核對")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    capture(page, f"print-packet-{width}.png")
