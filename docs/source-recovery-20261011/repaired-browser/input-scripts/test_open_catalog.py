"""Open catalogue launch: visitors read every school; an account without a school is asked once."""
import time
from uuid import uuid4

import requests
from playwright.sync_api import expect

from exchange_info.repositories import JsonlAccountRepository

from .conftest import enter_public_site

NTPU = "國立臺北大學"


def sign_in_cookie(live_server, school: str | None = None) -> dict:
    session = live_server.register(f"open-{uuid4().hex[:10]}@example.com")
    if school is not None:
        repository = JsonlAccountRepository(live_server.data_dir)
        account = repository.find_account_by_id(session["profile"]["id"])
        repository.save_account(account.model_copy(update={"home_university": school}))
    return session


def attach_session(page, live_server, session) -> None:
    page.context.add_cookies([{
        "name": "exchange_guide_session", "value": session["access_token"],
        "url": live_server.base_url, "httpOnly": True, "sameSite": "Lax",
    }])


def wait_until(page, expression: str, timeout: float = 30.0) -> None:
    # The page's CSP forbids eval, so wait_for_function cannot be used; evaluate() can.
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if page.evaluate(expression):
            return
        time.sleep(0.25)
    raise AssertionError(f"Timed out waiting for: {expression}")


def test_visitor_switches_schools_without_an_account(page, live_server):
    enter_public_site(page, live_server)
    expect(page.locator("#school-switcher")).to_be_enabled()
    page.locator("#school-switcher").click()
    page.locator(f'[data-home-school="{NTPU}"]').click()
    page.locator("#confirm-school").click()
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)
    expect(page.locator("#auth-dialog")).to_be_hidden()
    wait_until(page, "Boolean(state.dashboard && state.dashboard.school_name === '國立臺北大學')")
    assert page.evaluate("state.account") is None


def test_account_without_a_school_is_asked_once_after_google_returns(page, live_server):
    session = sign_in_cookie(live_server, school="尚未選擇")
    attach_session(page, live_server, session)
    page.goto(f"{live_server.base_url}/#auth=success")
    expect(page.locator("#school-onboarding")).to_be_visible(timeout=30_000)
    page.locator(f'[data-home-school="{NTPU}"]').click()
    page.locator("#confirm-school").click()
    expect(page.locator("#school-onboarding")).to_be_hidden()
    expect(page.locator("#school-switcher-label")).to_have_text(NTPU)
    profile = requests.get(
        f"{live_server.base_url}/auth/me",
        headers={"Authorization": f"Bearer {session['access_token']}"}, timeout=10,
    ).json()
    assert (profile["catalog_home_university"], profile["school_basis"]) == (NTPU, "self_declared")

    page.reload()
    page.wait_for_load_state("networkidle", timeout=60_000)
    expect(page.locator("#school-onboarding")).to_be_hidden()


def test_signing_out_keeps_the_catalogue_open(page, live_server):
    session = sign_in_cookie(live_server, school=NTPU)
    attach_session(page, live_server, session)
    page.goto(f"{live_server.base_url}/#partners")
    wait_until(page, "Boolean(state.account && state.dashboard && state.dashboard.school_name === '國立臺北大學')")
    page.evaluate("logoutAccount()")
    wait_until(page, "state.account === null && Boolean(state.dashboard) && state.dashboard.partner_universities.length > 0")
    expect(page.locator("#auth-dialog")).to_be_hidden()
