"""Acceptance against bundled data and real API/UI; no response or state mocks."""

import json
import os
import re
import socket
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import requests
import uvicorn
from playwright.sync_api import expect

from exchange_info.api import create_app
from exchange_info.ccu_sources import HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.storage import ensure_data_dirs

from .conftest import (
    LiveServer,
    _copy_public_fixture_data,
    enter_public_site,
    open_navigation,
)
from .test_open_catalog import attach_session, sign_in_cookie, wait_until
from .test_web_next_phase import _fill_required_application_fields


@pytest.fixture(scope="module")
def acceptance_server(tmp_path_factory):
    # The usual e2e fixture replaces CGU partners. This server keeps all four
    # bundled school sources and isolates only accounts and saved user data.
    data_dir = tmp_path_factory.mktemp("ccu-acceptance-real-data")
    ensure_data_dirs(data_dir)
    _copy_public_fixture_data(data_dir)  # tracked production public files, unchanged
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(data_dir), host="127.0.0.1", port=port, log_level="error", access_log=False))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            if requests.get(url + "/health", timeout=1).ok:
                break
        except requests.RequestException:
            time.sleep(0.1)
    else:
        server.should_exit = True
        thread.join(timeout=10)
        raise RuntimeError("Real bundled-data acceptance server did not start")
    timings = []
    for home in ["長庚大學", "國立臺北大學", "國立臺灣大學", HOME]:
        started = time.monotonic()
        response = requests.get(url + "/student-dashboard", params={"school": home}, timeout=120)
        response.raise_for_status()
        assert response.json()["school_name"] == home
        timings.append({"home_school": home, "seconds": round(time.monotonic() - started, 3), "partners": len(response.json()["partner_universities"]), "http_status": response.status_code})
    output = Path(os.environ.get("CCU_ACCEPTANCE_OUTPUT", "/tmp/ccu-candidate-acceptance"))
    output.mkdir(parents=True, exist_ok=True)
    (output / "real-dashboard-cold-loads.json").write_text(json.dumps(timings, ensure_ascii=False, indent=2) + "\n")
    try:
        yield LiveServer(base_url=url, data_dir=data_dir)
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def school(source_page):
    return next(p.school_name for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page)


def capture(page, label, width):
    output = Path(os.environ.get("CCU_ACCEPTANCE_OUTPUT", "/tmp/ccu-candidate-acceptance"))
    output.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output / f"{label}-{width}.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def navigate(page, route):
    # Route changes are navigation only; no data or application state injection.
    page.evaluate("hash => {location.hash = hash}", "#" + route)


def choose_home(page, home):
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator(f'[data-home-school="{home}"]').click()
    page.locator("#confirm-school").click()
    expect(page.locator("#school-switcher-label")).to_have_text(home)
    wait_until(page, "Boolean(state.dashboard && state.dashboard.school_name === " + json.dumps(home) + ")")
    query = parse_qs(urlsplit(page.url).query)
    if "home" in query:
        assert query["home"] == [home]


def select_target(page, target):
    previous = page.locator("#application-target-school").input_value()
    page.locator("#application-target-school").select_option(target)
    if previous and previous != target:
        expect(page.locator("#planning-target-change-dialog")).to_be_visible()
        page.locator('#planning-target-change-dialog button[value="confirm"]').click()
    wait_until(page, "state.applicationContext.target_school === " + json.dumps(target))


def login(page, server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    session = sign_in_cookie(server, school=HOME)
    server.verify_student(session["profile"]["id"], university=HOME)
    attach_session(page, server, session)
    enter_public_site(page, server, "partners")
    choose_home(page, HOME)
    return session


def record_errors(page):
    errors = []

    def record(error):
        errors.append(str(error))
        print("BROWSER_ERROR:", error)

    page.on("pageerror", record)
    return errors


@pytest.mark.parametrize("width", [390, 1440])
def test_real_school_search_matching_comparison_plan_reload_and_home_isolation(page, acceptance_server, width):
    server = acceptance_server
    errors = record_errors(page)
    session = login(page, server, width)
    assert set(page.locator("#degree-filter option").evaluate_all("rows => rows.map(row => row.value)")) == {"", "大學部", "碩士班", "博士班", "研究所"}
    names = [school(34), school(45)]
    for name in names:
        page.locator("#partner-search").fill(name)
        if width == 390:
            card = page.locator("#partner-table .partner-card").filter(has_text=name)
            expect(card).to_be_visible()
            card.locator("> summary").click()
        button = page.locator(f'#partner-table .favorite-toggle[data-school-name="{name}"]:visible').first
        expect(button).to_be_visible(timeout=30_000)
        button.click()
        expect(button).to_have_attribute("aria-pressed", "true")
    navigate(page, "favorites")
    expect(page.locator(".discovery-candidate")).to_have_count(2)
    for name in names:
        page.locator(f'[data-compare-school="{name}"]').check()
    comparison = page.locator("#discovery-comparison")
    for name in names:
        expect(comparison).to_contain_text(name)
    capture(page, "real-favorites-comparison", width)
    navigate(page, "application-center")
    select_target(page, names[0])
    navigate(page, "advisor")
    wait_until(page, "homeCollegeOptions().includes('法學院')")
    page.locator("#advisor-college").select_option("法學院")
    department = page.locator("#advisor-department")
    if department.evaluate("node => node.tagName") == "SELECT":
        wait_until(page, "document.querySelector('#advisor-department').options.length > 1")
        department.select_option(department.locator("option").evaluate_all("rows => rows.find(row => row.value).value"))
    else:
        department.fill("法律學系")
    page.locator("#advisor-degree").select_option("碩士班")
    page.locator("#advisor-academic-score").fill("85")
    page.locator("#advisor-academic-gpa").fill("3.5")
    page.locator("#advisor-language-test").select_option("ielts")
    page.locator("#advisor-language-score").fill("7")
    with page.expect_response(lambda r: r.url.endswith("/advisor/plan") and r.request.method == "POST") as result:
        page.locator("#advisor-submit").click()
    assert result.value.ok
    assert result.value.request.post_data_json["school_name"] == HOME
    assert "符合目前學制" in result.value.json()["target_match"]["reasons"]
    expect(page.locator("#advisor-profile-status")).to_have_text("已保存條件")
    capture(page, "real-advisor", width)
    navigate(page, "overview")
    expect(page.locator("#multi-plan-workspace")).to_be_visible()
    page.locator("#multi-plan-settings > summary").click()
    selects = page.locator("#multi-plan-preferences select")
    for index, name in enumerate(names):
        selects.nth(index).select_option(name)
    with page.expect_response(lambda r: r.url.endswith("/application-plan/evaluate") and r.request.method == "POST" and len(r.request.post_data_json["preferences"]) == 2) as planned:
        page.locator("#multi-plan-preferences button").click()
    assert planned.value.ok
    real_plan = planned.value.json()
    assert [c["school_name"] for c in real_plan["choices"]] == names
    assert real_plan["tasks"]  # actual partial workflows, never fabricated dates
    expect(page.locator("#multi-plan-status")).to_contain_text("2 個志願")
    task = real_plan["tasks"][0]
    task_id = task["id"]
    bucket = HOME if task["task_scope"] == "home" else task["school_names"][0]
    if task["task_scope"] != "home":
        branch = page.locator(f'.multi-plan-branch[data-multi-school="{bucket}"]')
        branch.locator("> summary").click()
    progress = page.locator(f'[data-multi-task="{task_id}"]')
    expect(progress).to_be_visible()
    progress.check()
    wait_until(page, "document.querySelector('#account-workspace-sync-label').textContent === '已同步'")
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    saved = requests.get(server.base_url + "/account/workspace", params={"home_school": HOME}, headers=headers, timeout=30)
    saved.raise_for_status()
    workspace = saved.json()["workspace"]
    assert workspace["application_schools"] == names
    assert workspace["application_progress"][bucket][task_id] is True
    page.reload()
    expect(page.locator("#multi-plan-status")).to_contain_text("2 個志願", timeout=30_000)
    expect(page.locator(f'[data-multi-task="{task_id}"]')).to_be_checked()
    capture(page, "real-plan-reloaded", width)
    for home, score, gpa, rank in [("長庚大學", True, False, False), ("國立臺北大學", True, False, False), ("國立臺灣大學", False, True, True), (HOME, True, True, False)]:
        choose_home(page, home)
        navigate(page, "advisor")
        for selector, visible in [("#advisor-academic-score", score), ("#advisor-academic-gpa", gpa), ("#advisor-class-rank", rank)]:
            if visible:
                expect(page.locator(selector)).to_be_visible()
            else:
                expect(page.locator(selector)).to_be_hidden()
        navigate(page, "application-center")
        wait_until(page, "!state.applicationLoading && state.applicationTemplates.length > 0")
        templates = page.request.get(server.base_url + "/application-center/templates", params={"school": home})
        assert templates.ok
        assert set(page.evaluate("state.applicationTemplates.map(t => t.id)")) == {t["id"] for t in templates.json()}
        if home != HOME:
            expect(page.locator("#application-target-school")).not_to_have_value(names[0])
            expect(page.locator("#application-requirement-list")).not_to_contain_text("入韓後ARC")
        capture(page, "home-" + home, width)
    navigate(page, "overview")
    expect(page.locator("#multi-plan-status")).to_contain_text("2 個志願", timeout=30_000)
    expect(page.locator(f'[data-multi-task="{task_id}"]')).to_be_checked()
    navigate(page, "favorites")
    expect(page.locator(".discovery-candidate")).to_have_count(2)
    assert not errors


@pytest.mark.parametrize("width", [390, 1440])
def test_real_document_center_stages_conditions_templates_and_saved_draft(page, acceptance_server, width):
    server = acceptance_server
    errors = record_errors(page)
    login(page, server, width)
    navigate(page, "application-center")
    target = school(45)
    with page.expect_response(lambda r: "/application-center/catalog?" in r.url and parse_qs(urlsplit(r.url).query).get("target_school") == [target]) as response:
        select_target(page, target)
    assert response.value.ok
    items = response.value.json()["items"]
    arc = [r for r in items if "ARC" in r["name"]]
    assert len(arc) == 7 and all(r["conditional"] and r["stage"] == "post_offer" for r in arc)
    catalog = page.locator("#application-requirement-list")
    group = catalog.locator("details.application-requirement-group").filter(has_text="入韓後ARC")
    expect(group).to_have_count(1)
    group.locator("> summary").click()
    form = group.locator("article").filter(has_text="統合申請")
    expect(form).to_contain_text("2022")
    expect(form).to_contain_text("擇一")
    expect(form).to_contain_text("條件")
    link = form.locator('a[href="https://www.hikorea.go.kr/board/BoardApplicationListR.pt?page=1"]')
    expect(link).to_have_count(1)
    expect(form).not_to_contain_text("當期已驗證表格")
    second = catalog.locator("details.application-requirement-group").filter(has=page.locator("summary strong").filter(has_text="第二次文件送件"))
    expect(second).to_have_count(1)
    second.locator("> summary").click()
    expect(second).to_contain_text("非OECD")
    expect(second).not_to_contain_text("入韓後ARC")
    capture(page, "real-document-stages-conditions", width)
    # Jena's public form link belongs to a later conditional extension, not the
    # first exchange application. API and visible control must agree.
    select_target(page, school(99))
    extension = catalog.locator("details.application-requirement-group").filter(has_text="Jena交换延期申请")
    expect(extension).to_have_count(1)
    if not extension.evaluate("node => node.open"):
        extension.locator("> summary").click()
    official = extension.locator('a[href="https://www.uni-jena.de/unijenamedia/66670/gaststud-verlaengerung.doc"]')
    expect(official).to_have_count(1)
    expect(extension).to_contain_text("核章")
    expect(extension).to_contain_text("待確認")
    capture(page, "real-public-extension-template", width)
    # Click the real official control. Network/TLS availability is reported
    # separately from the local rendering gate; no response replay or TLS bypass.
    link_events = {"label": "jena-extension", "official_url": official.get_attribute("href"), "width": width, "failures": [], "downloads": [], "popups": []}
    page.context.on("requestfailed", lambda request: link_events["failures"].append({"url": request.url, "error": request.failure}) if "uni-jena.de" in request.url else None)
    page.on("download", lambda download: link_events["downloads"].append(download.suggested_filename))
    popups = []
    page.on("popup", lambda popup: popups.append(popup))
    official.click()
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline and not link_events["failures"] and not link_events["downloads"]:
        page.wait_for_timeout(250)
    link_events["popups"] = [popup.url for popup in popups]
    link_events["live_external_browser_passed"] = bool(link_events["downloads"])
    output = Path(os.environ.get("CCU_ACCEPTANCE_OUTPUT", "/tmp/ccu-candidate-acceptance"))
    (output / f"external-template-{width}.json").write_text(json.dumps(link_events, ensure_ascii=False, indent=2) + "\n")
    for popup in popups:
        popup.close()
    tool = page.locator(".application-template-open").first
    expect(tool).to_be_visible()
    template_id = tool.get_attribute("data-open-application-template")
    tool.click()
    expect(page.locator("#application-document-form")).to_be_visible()
    _fill_required_application_fields(page)
    field = page.locator("#application-document-fields input[type=text]").first
    field_name = field.get_attribute("name")
    field.fill("中正驗收用的個人草稿")
    page.locator("#application-document-form button[type=submit]").click()
    expect(page.locator("#application-document-form-status")).to_contain_text("儲存")
    page.reload()
    expect(page.locator(f'#application-document-fields [name="{field_name}"]')).to_have_value("中正驗收用的個人草稿", timeout=30_000)
    page.locator("#document-tab-source").click()
    expect(page.locator("#application-form-source")).to_have_attribute("href", re.compile("https://"))
    capture(page, "real-tool-draft-reloaded-" + template_id, width)
    assert not errors
