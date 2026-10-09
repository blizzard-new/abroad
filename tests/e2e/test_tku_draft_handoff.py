"""Unsaved, explicitly typed drafts can follow sign-in without a cloud write."""
import json
from uuid import uuid4

import pytest
import requests
from playwright.sync_api import expect

from .conftest import enter_public_site


def type_guest_draft(page, server, home):
    page.add_init_script(f"localStorage.setItem('exchange-guide-home-school', {json.dumps(home)})")
    enter_public_site(page, server, "advisor")
    details = page.locator("#advisor-form details").first
    if details.get_attribute("open") is None:
        details.locator("summary").click()
    page.locator("#advisor-academic-score").fill("93")
    if home == "淡江大學":
        page.locator("#advisor-jlpt-level").select_option("N1")
    page.locator("#advisor-question").fill("合成未保存草稿，請核對當期文件。")
    page.locator("#advisor-submit").click()
    expect(page.locator("#auth-dialog")).to_be_visible()
    assert page.evaluate("state.eligibilityProfile") is None
    assert page.evaluate("localStorage.getItem('exchange-guide-eligibility-profile')") is None


def complete_sign_in(page, server, email):
    page.locator('[data-auth-mode="login"]').click()
    page.locator("#login-form input[name=email]").fill(email)
    page.locator("#login-form input[name=password]").fill("CodexE2E!2026")
    with page.expect_response(lambda r: r.url == f"{server.base_url}/auth/login" and r.request.method == "POST") as response:
        page.locator("#login-form button[type=submit]").click()
    assert response.value.ok
    expect(page.locator("#auth-dialog")).to_be_hidden()
    page.wait_for_function("() => !state.homeSchoolLoading && state.accountWorkspaceLoadingCount === 0")
    page.evaluate("() => state.periodOptionsReady")


@pytest.mark.parametrize("home", ["長庚大學", "淡江大學"])
def test_same_session_guest_draft_follows_sign_in_but_is_not_saved(page, live_server, home):
    email = f"draft-{uuid4().hex[:10]}@example.com"
    session = live_server.register(email)
    live_server.verify_student(session["profile"]["id"], university=home)
    calls = []
    page.on("request", lambda r: calls.append(r.url) if r.method == "POST" and r.url.endswith("/advisor/plan") else None)
    type_guest_draft(page, live_server, home)
    complete_sign_in(page, live_server, email)
    expect(page.locator("#advisor-academic-score")).to_have_value("93")
    expect(page.locator("#advisor-jlpt-level")).to_have_value("N1" if home == "淡江大學" else "")
    expect(page.locator("#advisor-question")).to_have_value("合成未保存草稿，請核對當期文件。")
    expect(page.locator("#advisor-profile-status")).to_contain_text("仍未保存")
    assert page.evaluate("state.eligibilityProfile") is None
    cloud = requests.get(f"{live_server.base_url}/account/workspace", params={"home_school": home},
        headers={"Authorization": f"Bearer {session['access_token']}"}, timeout=10)
    cloud.raise_for_status()
    assert not (cloud.json()["workspace"].get("selection_conditions") or {}).get("profile")
    assert calls == []
    page.locator("#account-button").click()
    page.locator("#logout-button").click()
    expect(page.locator("#account-button-label")).to_have_text("登入")
    expect(page.locator("#advisor-academic-score")).to_have_value("")
    expect(page.locator("#advisor-jlpt-level")).to_have_value("")
    expect(page.locator("#advisor-question")).to_have_value("")
    assert page.evaluate("localStorage.getItem('exchange-guide-eligibility-profile')") is None


def test_guest_draft_is_discarded_when_sign_in_changes_mother_school(page, live_server):
    email = f"draft-other-home-{uuid4().hex[:10]}@example.com"
    session = live_server.register(email)
    live_server.verify_student(session["profile"]["id"], university="淡江大學")
    type_guest_draft(page, live_server, "長庚大學")
    complete_sign_in(page, live_server, email)
    expect(page.locator("#school-switcher-label")).to_have_text("淡江大學")
    expect(page.locator("#advisor-academic-score")).to_have_value("")
    expect(page.locator("#advisor-jlpt-level")).to_have_value("")
    expect(page.locator("#advisor-question")).to_have_value("")
    assert page.evaluate("state.eligibilityProfile") is None
