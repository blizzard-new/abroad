"""In a real browser: the Google button does nothing until the terms are ticked, then goes on with the version attached."""
import json

from playwright.sync_api import expect

from exchange_info.legal_pages import TERMS_VERSION

from .conftest import open_navigation

PROVIDERS = [
    {"provider": "email", "enabled": False},
    {"provider": "google", "enabled": True},
    {"provider": "facebook", "enabled": False},
    {"provider": "apple", "enabled": False},
]
ACCOUNT_BUTTON = "#account-button:visible, #global-mobile-account-button:visible, #mobile-account-button:visible"


def prepare(page, live_server):
    """Google offered as the only method, and the start address answered locally so no real sign-in is attempted."""
    started: list[str] = []
    page.route("**/auth/providers**", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(PROVIDERS)))

    def stub(route):
        started.append(route.request.url)
        route.fulfill(status=200, content_type="text/html", body="<h1>stub</h1>")

    page.route("**/auth/oauth/google/start**", stub)
    return started


def open_dialog(page, live_server):
    page.goto(f"{live_server.base_url}/#home")
    page.reload()  # the same address twice is not a navigation, so a dialog left open would stay open
    page.wait_for_load_state("networkidle", timeout=60_000)
    open_navigation(page)
    page.locator(ACCOUNT_BUTTON).first.click()
    expect(page.locator("#auth-dialog")).to_be_visible()


def test_google_waits_for_the_tick_then_goes_on_with_the_version(page, live_server):
    started = prepare(page, live_server)
    open_dialog(page, live_server)
    box, hint, google = page.locator("#terms-consent"), page.locator("#terms-consent-hint"), page.locator('[data-oauth-provider="google"]')
    expect(google).to_be_enabled()
    expect(box).not_to_be_checked()
    expect(page.locator("#auth-dialog a[href='/terms']")).to_be_visible()
    expect(page.locator("#auth-dialog a[href='/privacy']")).to_be_visible()

    google.click()
    expect(hint).to_be_visible()
    expect(box).to_be_focused()
    assert started == [], "nothing was requested without the tick"
    assert "/auth/oauth/" not in page.url

    box.check()
    expect(hint).to_be_hidden()
    google.click()
    page.wait_for_url(f"**/auth/oauth/google/start?terms={TERMS_VERSION}")
    assert len(started) == 1 and started[0].endswith(f"?terms={TERMS_VERSION}")


def test_a_returning_browser_finds_the_current_version_already_ticked(page, live_server):
    prepare(page, live_server)
    open_dialog(page, live_server)
    page.locator("#terms-consent").check()
    page.locator('[data-oauth-provider="google"]').click()
    page.wait_for_url(f"**/auth/oauth/google/start?terms={TERMS_VERSION}")

    open_dialog(page, live_server)
    expect(page.locator("#terms-consent")).to_be_checked()

    # A newer version of the terms means ticking again.
    page.evaluate("window.localStorage.setItem('uniway-terms-accepted', '2000-01-01')")
    open_dialog(page, live_server)
    expect(page.locator("#terms-consent")).not_to_be_checked()


def test_when_the_server_turns_a_sign_in_away_the_dialog_reopens_with_a_reminder(page, live_server):
    prepare(page, live_server)
    page.goto(f"{live_server.base_url}/#auth=terms")
    page.wait_for_load_state("networkidle", timeout=60_000)
    expect(page.locator("#auth-dialog")).to_be_visible()
    expect(page.locator("#terms-consent-hint")).to_be_visible()
    assert page.evaluate("location.hash") != "#auth=terms"
