"""Delay real API bytes to test school changes; never invent policy responses."""

import hashlib
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

import pytest
from playwright.sync_api import expect

from .conftest import open_navigation
from .test_ccu_candidate_acceptance import (
    HOME,
    capture,
    choose_home,
    login,
    navigate,
    record_errors,
    school,
    select_target,
)
from .test_ccu_candidate_acceptance import (
    acceptance_server as acceptance_server,  # noqa: PLC0414 -- pytest fixture re-export
)
from .test_open_catalog import wait_until
from .test_web_next_phase import _fill_required_application_fields


class DelayedReads:
    def __init__(self, page, server, predicate, *, per_path_limit=1):
        self.page = page
        self.server = server
        self.predicate = predicate
        self.per_path_limit = per_path_limit
        self.held = []
        self.counts = {}
        self.trace = []
        page.route(server.base_url + "/**", self.handle)

    def handle(self, route):
        url = urlsplit(route.request.url)
        if route.request.method != "GET" or not self.predicate(url.path, parse_qs(url.query)):
            route.continue_()
            return
        count = self.counts.get(url.path, 0) + 1
        self.counts[url.path] = count
        if count > self.per_path_limit:
            route.continue_()
            return
        # This is the actual same local production-data endpoint, with its
        # headers/body unchanged. Only delivery timing is controlled.
        response = route.fetch()
        assert response.ok
        row = {"url": route.request.url, "path": url.path, "sequence": count, "status": response.status, "body_sha256": hashlib.sha256(response.body()).hexdigest(), "released": False}
        self.trace.append(row)
        self.held.append((route, response, row))

    def wait(self, count):
        for _ in range(120):
            if len(self.held) >= count:
                return
            self.page.wait_for_timeout(100)
        raise AssertionError(f"Only {len(self.held)} real responses held, expected {count}")

    def release(self, sequence=None):
        for route, response, row in self.held:
            if row["released"] or (sequence is not None and row["sequence"] != sequence):
                continue
            route.fulfill(response=response)
            row["released"] = True

    def close(self, label, width):
        self.release()
        self.page.unroute(self.server.base_url + "/**", self.handle)
        output = Path(os.environ.get("CCU_ACCEPTANCE_OUTPUT", "/tmp/ccu-delayed-switching"))
        output.mkdir(parents=True, exist_ok=True)
        (output / f"real-response-delay-{label}-{width}.json").write_text(json.dumps({"response_bodies_fabricated": False, "application_state_mocked": False, "trace": self.trace}, ensure_ascii=False, indent=2) + "\n")


def click_home(page, home):
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator(f'[data-home-school="{home}"]').click()
    expect(page.locator("#school-switcher-label")).to_have_text(home)


@pytest.mark.parametrize("width", [390, 1440])
def test_old_home_responses_cannot_finish_newer_a_b_a_load(page, acceptance_server, width):
    server = acceptance_server
    errors = record_errors(page)
    login(page, server, width)
    choose_home(page, "國立臺北大學")
    wait_until(page, "!state.applicationLoading && state.destinationProfiles.length === 206")
    paths = {"/student-dashboard", "/coverage", "/destination-profiles", "/application-center/templates"}
    gate = DelayedReads(page, server, lambda path, query: path in paths and (query.get("school") or query.get("home_school")) == [HOME], per_path_limit=2)
    try:
        click_home(page, HOME)
        gate.wait(4)
        click_home(page, "國立臺北大學")
        wait_until(page, "state.dashboard?.school_name === '國立臺北大學' && !state.applicationLoading")
        click_home(page, HOME)
        gate.wait(8)
        gate.release(sequence=1)
        page.wait_for_timeout(250)
        assert page.evaluate("state.partnerDataLoading && state.applicationLoading")
        assert page.evaluate("state.coverage === null")
        expect(page.locator("#partner-table .skeleton")).to_be_visible()
        gate.release(sequence=2)
        wait_until(page, "state.dashboard?.school_name === '國立中正大學' && !state.applicationLoading && state.coverage?.destination_profile_count === 104")
        assert page.evaluate("state.destinationProfiles.length") == 104
        actual = page.request.get(server.base_url + "/application-center/templates", params={"school": HOME}).json()
        assert set(page.evaluate("state.applicationTemplates.map(t => t.id)")) == {x["id"] for x in actual}
        navigate(page, "application-center")
        select_target(page, school(45))
        expect(page.locator("#application-requirement-list")).to_contain_text("入韓後ARC", timeout=30_000)
        capture(page, "a-b-a-newest-home-document-fields", width)
        assert not errors
    finally:
        gate.close("home", width)


@pytest.mark.parametrize("width", [390, 1440])
def test_late_target_catalog_cannot_replace_current_conditions_and_saved_draft(page, acceptance_server, width):
    server = acceptance_server
    errors = record_errors(page)
    login(page, server, width)
    navigate(page, "application-center")
    select_target(page, school(34))
    wait_until(page, "!state.applicationLoading")
    old, current = school(45), school(99)
    gate = DelayedReads(page, server, lambda path, query: path == "/application-center/catalog" and query.get("target_school") == [old])
    try:
        select_target(page, old)
        gate.wait(1)
        select_target(page, current)
        expect(page.locator("#application-requirement-list")).to_contain_text("延長", timeout=30_000)
        gate.release()
        page.wait_for_timeout(250)
        expect(page.locator("#application-target-school")).to_have_value(current)
        expect(page.locator("#application-requirement-list")).not_to_contain_text("入韓後ARC")
        expect(page.locator("#application-requirement-list")).to_contain_text("延長")
        page.locator(".application-template-open").first.click()
        _fill_required_application_fields(page)
        field = page.locator("#application-document-fields input[type=text]").first
        name = field.get_attribute("name")
        field.fill("延遲切換仍保留的中正草稿")
        page.locator("#application-document-form button[type=submit]").click()
        expect(page.locator("#application-document-form-status")).to_contain_text("儲存")
        page.reload()
        expect(page.locator(f'#application-document-fields [name="{name}"]')).to_have_value("延遲切換仍保留的中正草稿", timeout=30_000)
        navigate(page, "application-center")
        expect(page.locator("#application-target-school")).to_have_value(current)
        expect(page.locator("#application-requirement-list")).to_contain_text("延長", timeout=30_000)
        capture(page, "late-target-source-and-draft-reloaded", width)
        assert not errors
    finally:
        gate.close("target", width)


@pytest.mark.parametrize("width", [390, 1440])
def test_late_detail_evidence_cannot_replace_new_target_workflow_or_life(page, acceptance_server, width):
    server = acceptance_server
    errors = record_errors(page)
    login(page, server, width)
    old, current = school(45), school(34)
    paths = {"/application-workflow", "/destination-profile", "/school-data-completeness"}
    gate = DelayedReads(page, server, lambda path, query: path in paths and query.get("school") == [old])
    try:
        navigate(page, "school=" + quote(old))
        gate.wait(3)
        navigate(page, "school=" + quote(current))
        expect(page.locator("#school-detail-title")).to_have_text(current)
        wait_until(page, "state.activeWorkflow?.school_name === " + json.dumps(current))
        gate.release()
        page.wait_for_timeout(250)
        expect(page.locator("#school-detail-title")).to_have_text(current)
        assert page.evaluate("state.activeWorkflow.school_name") == current
        page.locator("#detail-tab-application").click()
        expect(page.locator("#detail-application")).not_to_contain_text("入韓後ARC")
        page.locator("#detail-tab-overview").click()
        scope = page.locator('#detail-overview [data-ccu-field="program_scope"]')
        expect(scope).to_contain_text("NUPACE")
        expect(scope).to_contain_text("National Chung Cheng University")
        capture(page, "late-detail-keeps-newest-qualification-source", width)
        assert not errors
    finally:
        gate.close("detail", width)


@pytest.mark.parametrize("width", [390, 1440])
def test_queued_form_save_keeps_original_home_when_switching_before_debounce(page, acceptance_server, width):
    server = acceptance_server
    errors = record_errors(page)
    login(page, server, width)
    navigate(page, "application-center")
    select_target(page, school(99))
    page.locator(".application-template-open").first.click()
    _fill_required_application_fields(page)
    # Control browser time, rather than replacing application state or API
    # bytes, so the 650ms save cannot fire before the school switch.
    page.clock.install()
    page.clock.pause_at(page.evaluate("Date.now() + 1000"))
    field = page.locator("#application-document-fields input[type=text]").first
    field_name = field.get_attribute("name")
    template_id = page.evaluate("state.activeApplicationTemplateId")
    value = "切校前排入中正的草稿"
    field.fill(value)
    click_home(page, "國立臺北大學")
    page.clock.run_for(1000)
    page.clock.resume()
    wait_until(page, "state.dashboard?.school_name === '國立臺北大學' && !state.applicationLoading")
    source = page.request.get(server.base_url + "/account/application-drafts", params={"home_school": HOME}).json()["items"]
    draft = next((item for item in source if item["template_id"] == template_id), None)
    assert draft is not None, "Queued CCU save must survive a home change"
    assert value in json.dumps({"profile": draft["profile"], "answers": draft["answers"]}, ensure_ascii=False)
    foreign = page.request.get(server.base_url + "/account/application-drafts", params={"home_school": "國立臺北大學"}).json()["items"]
    assert value not in json.dumps(foreign, ensure_ascii=False)
    choose_home(page, HOME)
    navigate(page, "application-form=" + quote(template_id))
    page.reload()
    expect(page.locator(f'#application-document-fields [name="{field_name}"]')).to_have_value(value, timeout=30_000)
    capture(page, "queued-save-original-home-reloaded", width)
    assert not errors
