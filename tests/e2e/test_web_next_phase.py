from __future__ import annotations
import pytest

import csv
import json
import time
from datetime import date, timedelta
from io import StringIO
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import requests
from playwright.sync_api import Browser, Locator, Page, expect

from exchange_info.content_governance import (
    LocalContentGovernanceStore,
    stage_workflow_refresh,
    workflow_review_rule_keys,
    workflow_review_source_urls,
)
from exchange_info.storage import save_application_workflow_revisions

from .conftest import LiveServer, enter_public_site, login_through_web, open_navigation


LINCOLN = "林肯大學 Lincoln University"
MEIJI = "明治大學 Meiji University"
UNIVERSITI_MALAYA = "馬來西亞馬來亞大學 Universiti Malaya"
UWM = "威斯康辛大學密爾基分校 University of Wisconsin-Milwaukee"
PARIS_SACLAY = "法國薩克雷大學 University of Paris-Saclay"
THOMAS_MORE = (
    "比利時托馬斯莫爾應用科技大學 "
    "Thomas More University of Applied Sciences"
)
TH_LUEBECK = "德國呂貝克應用科技大學 Technische Hochschule Lübeck"
KANGWON = "韓國江原國立大學 Kangwon National University"
SKEMA = "歐洲知識經濟與管理學院 Skema Business School"
CHANDIGARH = "印度昌迪加爾大學 Chandigarh University"
UNYP = "捷克布拉格紐約大學 University of New York in Prague (UNYP)"
EPF = "法國EPF工程師學校 EPF École d'ingénieurs"
RENNES = "雷恩商學院 Rennes School of Business"
MSU = "馬來西亞管理與科技大學 Management and Science University"
IAE_AIX = (
    "法國艾克斯馬賽大學管理研究所 "
    "IAE Aix-Marseille Graduate School of Management"
)
TU_EINDHOVEN = "荷蘭恩荷芬理工大學 Eindhoven University of Technology"
WUHAN = "武漢大學 Wuhan University"
ICD = "法國ICD商學院 ICD Business School"


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}@example.com"


def _auth_headers(session: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}


def _community_headers(server: LiveServer, session: dict) -> dict[str, str]:
    headers = _auth_headers(session)
    identity = requests.post(
        f"{server.base_url}/auth/community-identity",
        headers=headers,
        timeout=10,
    )
    identity.raise_for_status()
    payload = identity.json()
    return {
        **headers,
        "X-Anonymous-ID": payload["id"],
        "X-Anonymous-Token": payload["access_token"],
    }


def _workspace(
    server: LiveServer,
    session: dict,
    home_school: str = "長庚大學",
) -> dict:
    response = requests.get(
        f"{server.base_url}/account/workspace",
        params={"home_school": home_school},
        headers=_auth_headers(session),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def _wait_for_workspace(
    server: LiveServer,
    session: dict,
    predicate,
    timeout: float = 10,
    *,
    home_school: str = "長庚大學",
) -> dict:
    deadline = time.time() + timeout
    latest: dict = {}
    while time.time() < deadline:
        latest = _workspace(server, session, home_school)
        if predicate(latest):
            return latest
        time.sleep(0.1)
    raise AssertionError(f"Workspace did not reach the expected state: {latest}")


def _seed_quarantined_workspace_state(
    page: Page,
    *,
    favorite_school: str,
    sentinel: str,
) -> None:
    page.evaluate(
        """({ favoriteSchool, sentinel }) => {
          const homeSchool = '長庚大學';
          const storageKey = 'exchange-guide-workspace-sync-v1';
          const metadata = JSON.parse(window.localStorage.getItem(storageKey) || '{}');
          if (!metadata.account_id) throw new Error('missing workspace owner');
          metadata.revisions ||= {};
          metadata.bases ||= {};
          metadata.pending ||= {};
          const base = metadata.bases[homeSchool]
            ? JSON.parse(JSON.stringify(metadata.bases[homeSchool]))
            : window.emptyAccountWorkspace(homeSchool);
          const pending = JSON.parse(JSON.stringify(base));
          pending.home_school = homeSchool;
          pending.revision = Number(metadata.revisions[homeSchool] || base.revision || 0);
          pending.favorite_schools = Array.from(
            new Set([...(pending.favorite_schools || []), favoriteSchool])
          );
          pending.selection_conditions = { profile: { department: sentinel } };
          metadata.pending[homeSchool] = pending;
          window.localStorage.setItem(storageKey, JSON.stringify(metadata));
          window.localStorage.setItem(
            'exchange-guide-favorites',
            JSON.stringify(pending.favorite_schools)
          );
          window.localStorage.setItem(
            'exchange-guide-eligibility-profile',
            JSON.stringify({ department: sentinel })
          );
          window.localStorage.setItem(
            'exchange-guide-anonymous-identity',
            JSON.stringify({
              id: 'quarantined-community-identity',
              access_token: sentinel,
              display_label: sentinel,
            })
          );
          window.localStorage.setItem(
            'exchange-guide-application-profile-memory-v1',
            JSON.stringify({ student_name_zh: sentinel })
          );
          window.localStorage.setItem(
            'exchange-guide-application-profile-memory-enabled',
            'true'
          );
          window.localStorage.setItem(
            'exchange-guide-auth-token',
            'legacy-token-must-not-survive-boot'
          );
          window.sessionStorage.setItem(
            'exchange-guide-application-profile-session',
            JSON.stringify({ student_id: sentinel })
          );
          window.sessionStorage.setItem(
            'exchange-guide-application-answers-session',
            JSON.stringify({ private_answer: sentinel })
          );
        }""",
        {"favoriteSchool": favorite_school, "sentinel": sentinel},
    )


def _select_first_nonempty(select: Locator) -> None:
    expect(select.locator("option").nth(1)).to_be_attached()
    select.select_option(index=1)


def _open_content_review_workbench(
    page: Page,
    server: LiveServer,
    email: str,
    session: dict | None = None,
) -> None:
    if session is None:
        login_through_web(page, server, email)
    else:
        page.context.add_cookies(
            [
                {
                    "name": "exchange_guide_session",
                    "value": session["access_token"],
                    "url": server.base_url,
                }
            ]
        )
    page.goto(f"{server.base_url}/admin/content-review")
    expect(page.locator("#reviewer-email")).to_have_text(email)
    page.locator("#review-status-filter").select_option("pending_review")


def _fill_required_application_fields(page: Page) -> None:
    fields = page.locator("#application-document-form [required]")
    for index in range(fields.count()):
        field = fields.nth(index)
        tag_name = field.evaluate("element => element.tagName.toLowerCase()")
        input_type = field.get_attribute("type") or ""
        name = field.get_attribute("name") or ""
        if tag_name == "select":
            _select_first_nonempty(field)
        elif input_type == "checkbox":
            field.check()
        elif input_type == "file":
            raise AssertionError("The first printable template unexpectedly requires a file.")
        elif input_type == "email":
            field.fill("e2e-student@example.com")
        elif input_type == "tel":
            field.fill("0912345678")
        elif input_type == "date":
            field.fill("2026-09-01")
        elif input_type == "number":
            field.fill("85")
        elif "language_score" in name:
            field.fill("6.5")
        elif tag_name == "textarea":
            field.fill("E2E 自動化驗收用的完整申請內容，僅存在隔離測試資料中。")
        else:
            field.fill("E2E 測試資料")


def test_guest_can_save_device_selections_and_plan_actions_require_login(
    page: Page,
    live_server: LiveServer,
) -> None:
    console_errors: list[str] = []
    failed_resources: list[str] = []
    document_headers: dict[str, str] = {}

    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error"
        else None,
    )

    def capture_main_document(response) -> None:
        if response.status >= 400:
            failed_resources.append(f"{response.status} {response.url}")
        if (
            response.request.resource_type == "document"
            and response.url.rstrip("/") == live_server.base_url.rstrip("/")
        ):
            document_headers.update(response.headers)

    page.on("response", capture_main_document)
    enter_public_site(page, live_server, "partners")
    assert "script-src 'self'" in document_headers["content-security-policy"]
    assert "script-src-attr 'none'" in document_headers["content-security-policy"]
    assert document_headers["x-frame-options"] == "DENY"
    expect(page.locator("#partner-search")).to_be_visible()
    expect(page.locator("#partner-table")).to_have_attribute("aria-busy", "false", timeout=15_000)

    # This flow needs a selected mother school; browse-first alone is global.
    open_navigation(page)
    page.locator('#glass-navigation a[data-public-route="overview"]').click()
    expect(page.locator("#school-onboarding")).to_be_visible()
    page.locator('#school-options [data-home-school="長庚大學"]').click()
    page.locator("#confirm-school").click()
    expect(page.locator("#school-onboarding")).to_be_hidden()
    page.wait_for_function("() => !state.homeSchoolLoading && !state.partnerDataLoading")
    page.evaluate("window.location.hash = '#overview'")
    page.locator('.planning-documents a').click()
    page.locator('#application-workspace-tools a[href="#documents"]').click()
    expect(page.locator("#documents")).to_be_visible()
    document_progress = page.locator(
        "#document-workspace-list [data-document-status]"
    ).first
    expect(document_progress).to_be_visible()
    expect(document_progress).to_be_disabled()
    expect(page.locator("#document-workspace-list")).to_contain_text(
        "登入後才能更新並同步送件資料狀態"
    )
    page.evaluate("window.location.hash = '#partners'")

    page.locator("#partner-search").fill("林肯")
    favorite = page.locator(
        f'#partner-table .favorite-toggle[data-school-name="{LINCOLN}"]'
    ).first
    expect(favorite).to_be_visible(timeout=15_000)
    expect(favorite).to_have_attribute("aria-label", f"加入比較{LINCOLN}")
    favorite.click()
    expect(favorite).to_have_attribute("aria-pressed", "true")
    page.locator("#partner-search").fill("")
    visible_favorites = page.locator("#partner-table .favorite-toggle")
    second_favorite = next(
        visible_favorites.nth(index)
        for index in range(visible_favorites.count())
        if visible_favorites.nth(index).get_attribute("data-school-name") != LINCOLN
    )
    second_favorite.click()

    page.evaluate("window.location.hash = '#favorites'")
    expect(page.locator("#favorites-title")).to_be_visible()
    expect(page.locator("#selection-workspace")).to_contain_text(LINCOLN)
    expect(page.locator("#discovery-comparison")).to_contain_text(LINCOLN)
    assert page.evaluate(
        "JSON.parse(window.localStorage.getItem('exchange-guide-favorites') || '[]')"
    ) == []
    assert page.evaluate(
        "JSON.parse(window.localStorage.getItem('exchange-guide-applications') || '[]')"
    ) == []

    favorite_card = page.locator(
        f'.discovery-candidate:has(.school-detail-trigger[data-school-name="{LINCOLN}"])'
    )
    favorite_card.locator(
        f'.school-detail-trigger[data-school-name="{LINCOLN}"]'
    ).click()
    expect(page.locator("#detail-favorite-button")).to_contain_text("已加入比較")
    expect(page.locator("#detail-application-button")).to_contain_text(
        "登入建立計畫"
    )
    page.locator("#detail-tab-application").click()
    progress = page.locator("#application-tracker .progress-checkbox").first
    expect(progress).to_be_visible(timeout=15_000)
    expect(progress).to_be_disabled()
    expect(page.locator("#application-tracker")).to_contain_text(
        "登入以保存進度"
    )
    page.locator("#detail-application-button").click()
    expect(page.locator("#auth-dialog")).to_be_visible()
    expect(page.locator('[data-auth-mode="register"]')).to_have_attribute(
        "aria-selected", "true"
    )
    page.locator("[data-close-auth]").last.click()
    expect(page.locator("#auth-dialog")).to_be_hidden()

    page.locator("#back-to-schools").click()
    page.evaluate("window.location.hash = '#budget'")
    expect(page.locator("#budget-title")).to_be_visible()
    page.locator("#budget-school").select_option(LINCOLN)
    page.locator("#budget-housing").fill("12300")
    expect(page.locator("#budget-result")).to_contain_text("12,300")
    expect(page.locator("#budget-save-button")).to_contain_text("登入後儲存估算")
    page.locator("#budget-save-button").click()
    expect(page.locator("#auth-dialog")).to_be_visible()
    expect(page.locator("#budget-save-note")).to_contain_text("試算不需登入")
    assert page.evaluate(
        "JSON.parse(window.localStorage.getItem('exchange-guide-budget-plans') || '{}')"
    ) == {}
    page.locator("[data-close-auth]").last.click()

    page.evaluate("window.location.hash = '#calendar'")
    expect(page.locator("#application-calendar-title")).to_be_visible()
    quick_add = page.locator(".calendar-quick-add")
    quick_add.locator("summary").click()
    quick_add.locator('input[name="title"]').fill("訪客不應保存的任務")
    quick_add.locator('input[name="date"]').fill("2027-10-08")
    quick_add.locator('button[type="submit"]').click()
    expect(page.locator("#auth-dialog")).to_be_visible()
    expect(quick_add.locator(".form-status")).to_contain_text(
        "登入後才會建立並同步個人任務"
    )
    assert page.evaluate(
        "JSON.parse(window.localStorage.getItem('exchange-guide-calendar-events') || '[]')"
    ) == []
    page.locator("[data-close-auth]").last.click()

    anonymous = requests.get(f"{live_server.base_url}/auth/session", timeout=10)
    assert anonymous.status_code == 200
    assert anonymous.json() is None
    assert console_errors == [], failed_resources


def test_advisor_waits_for_login_and_clears_private_conditions_on_logout(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("advisor-privacy")
    session = live_server.register(email, "E2E 顧問隱私學生")
    live_server.verify_student(session["profile"]["id"])
    advisor_requests: list[str] = []
    page.on(
        "request",
        lambda request: advisor_requests.append(request.url)
        if request.method == "POST" and request.url.endswith("/advisor/plan")
        else None,
    )
    enter_public_site(page, live_server, "advisor")

    page.evaluate(
        "window.localStorage.setItem('exchange-guide-eligibility-profile', "
        "JSON.stringify({ department: '舊帳號不應顯示' }))"
    )
    page.reload()
    page.locator("#school-onboarding").wait_for(state="hidden")
    page.wait_for_load_state("networkidle", timeout=60_000)
    assert page.evaluate(
        "window.localStorage.getItem('exchange-guide-eligibility-profile')"
    ) is None
    expect(page.locator("#advisor-department")).to_have_value("")
    expect(page.locator("#advisor-submit")).to_contain_text("登入後產生方案")
    expect(page.locator("#advisor-profile-status")).to_have_text(
        "未登入，不會保存條件"
    )

    page.locator("#advisor-form details summary").click()
    page.locator("#advisor-academic-score").fill("84")
    page.locator("#advisor-language-test").select_option("ielts")
    page.locator("#advisor-language-score").fill("6.5")
    page.locator("#advisor-question").fill("日本交換的申請文件怎麼準備？")
    page.locator("#advisor-submit").click()

    expect(page.locator("#auth-dialog")).to_be_visible()
    expect(page.locator('[data-auth-mode="register"]')).to_have_attribute(
        "aria-selected", "true"
    )
    assert advisor_requests == []
    assert page.evaluate(
        "window.localStorage.getItem('exchange-guide-eligibility-profile')"
    ) is None
    expect(page.locator("#advisor-department")).to_have_value("")
    expect(page.locator("#advisor-academic-score")).to_have_value("84")
    expect(page.locator("#advisor-question")).to_have_value(
        "日本交換的申請文件怎麼準備？"
    )

    page.locator('[data-auth-mode="login"]').click()
    page.locator("#login-form input[name=email]").fill(email)
    page.locator("#login-form input[name=password]").fill("CodexE2E!2026")
    with page.expect_response(
        lambda response: response.url == f"{live_server.base_url}/auth/login"
        and response.request.method == "POST",
        timeout=60_000,
    ) as login_response_info:
        page.locator("#login-form button[type=submit]").click()
    assert login_response_info.value.ok
    page.locator("#auth-dialog").wait_for(state="hidden", timeout=10_000)
    expect(page.locator("#advisor-department")).to_have_value("")
    expect(page.locator("#advisor-academic-score")).to_have_value("84")
    expect(page.locator("#advisor-submit")).to_contain_text("產生我的申請方案")
    page.wait_for_load_state("networkidle")
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-degree").select_option("大學部")
    page.locator("#advisor-department").select_option("資訊工程學系")

    with page.expect_response(
        lambda response: response.url == f"{live_server.base_url}/advisor/plan"
        and response.request.method == "POST",
        timeout=60_000,
    ) as advisor_response_info:
        page.locator("#advisor-submit").click()
    assert advisor_response_info.value.ok
    expect(page.locator("#advisor-result-content")).not_to_be_empty()
    page.wait_for_function(
        "() => window.localStorage.getItem('exchange-guide-eligibility-profile') !== null"
    )
    assert len(advisor_requests) == 1

    page.locator("#account-button").click()
    expect(page.locator("#profile-dialog")).to_be_visible()
    page.locator("#logout-button").click()
    expect(page.locator("#profile-dialog")).to_be_hidden(timeout=10_000)
    expect(page.locator("#account-button-label")).to_have_text("登入")
    expect(page.locator("#advisor-department")).to_have_value("")
    expect(page.locator("#advisor-academic-score")).to_have_value("")
    expect(page.locator("#advisor-result-content")).to_be_empty()
    expect(page.locator("#advisor-assistant")).to_have_attribute("data-state", "idle")
    assert page.evaluate(
        "window.localStorage.getItem('exchange-guide-eligibility-profile')"
    ) is None


def test_partial_destination_profile_is_not_rendered_as_fully_verified(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("馬來亞")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{UNIVERSITI_MALAYA}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(UNIVERSITI_MALAYA)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("2026 秋季")
    expect(official).to_contain_text("查看本頁全部查核來源（3）")


def test_second_destination_batch_preserves_housing_availability_warning(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("密爾基")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{UWM}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(UWM)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("2026-05-01")
    expect(official).to_contain_text("候補")
    expect(official).to_contain_text("查看本頁全部查核來源（6）")


def test_third_destination_batch_does_not_present_stale_costs_as_current(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("薩克雷")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{PARIS_SACLAY}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(PARIS_SACLAY)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("2021／2021-22")
    expect(official).to_contain_text("不能把其中金額當成 2026/27 預算")
    expect(official).to_contain_text("48 小時")
    expect(official).to_contain_text("查看本頁全部查核來源（5）")


def test_fourth_destination_batch_keeps_multicampus_cost_limits_visible(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("托馬斯莫爾")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{THOMAS_MORE}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(THOMAS_MORE)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("EUR 850–1,150")
    expect(official).to_contain_text("不含學費與交通")
    expect(official).to_contain_text("依交換課程／校區")
    expect(official).to_contain_text("查看本頁全部查核來源（5）")


def test_fifth_destination_batch_does_not_reuse_expired_welcome_dates(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("呂貝克")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{TH_LUEBECK}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(TH_LUEBECK)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("EUR 900–1,000")
    expect(official).to_contain_text("EUR 394.30")
    expect(official).to_contain_text("2026-03-10 至 03-21 的已過日期")
    expect(official).to_contain_text("下一梯次日期須等校方更新")
    expect(official).to_contain_text("查看本頁全部查核來源（5）")


def test_sixth_destination_batch_keeps_stale_dorm_prices_out_of_current_budget(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("江原")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{KANGWON}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(KANGWON)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("交換生宿舍有保障")
    expect(official).to_contain_text("As of 2019")
    expect(official).to_contain_text("不能當作現行交換預算")
    expect(official).to_contain_text("限定 Chuncheon Campus")
    expect(official).to_contain_text("查看本頁全部查核來源（4）")


def test_seventh_destination_batch_does_not_apply_paris_budget_to_every_campus(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("Skema")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{SKEMA}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(SKEMA)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("法國校區待確認")
    expect(official).to_contain_text("EUR 900–1,800")
    expect(official).to_contain_text("不能套到 Lille 或 Sophia Antipolis")
    expect(official).to_contain_text("都沒有校內住宿")
    expect(official).to_contain_text("查看本頁全部查核來源（3）")


def test_eighth_destination_batch_does_not_present_2021_free_housing_as_current(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("昌迪加爾")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{CHANDIGARH}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(CHANDIGARH)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("Mohali")
    expect(official).to_contain_text("一般國際學生費率")
    expect(official).to_contain_text("2021 fact sheet 的免費住宿")
    expect(official).to_contain_text("不能當現況")
    expect(official).to_contain_text("查看本頁全部查核來源（4）")


def test_ninth_destination_batch_does_not_make_optional_housing_package_mandatory(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("布拉格紐約")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{UNYP}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(UNYP)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("USD 6,000")
    expect(official).to_contain_text("不是所有交換生的必付費用")
    expect(official).to_contain_text("沒有自己的校內宿舍")
    expect(official).to_contain_text("兩種路徑不能混為同一項住宿承諾")
    expect(official).to_contain_text("2026-04-17")
    expect(official).to_contain_text("已在本次查核日前截止")
    expect(official).to_contain_text("查看本頁全部查核來源（4）")


def test_tenth_destination_batch_keeps_campus_and_summer_program_limits_visible(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("EPF")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{EPF}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(EPF)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("只適用 2026 暑期法語工程師課程")
    expect(official).to_contain_text("不能拿來估算一般學期交換住宿")
    expect(official).to_contain_text("不保證配到宿舍")
    expect(official).to_contain_text("不能跨校區套用交通資訊")
    expect(official).to_contain_text("秋季只開放五年級課程")
    expect(official).to_contain_text("查看本頁全部查核來源（4）")


def test_eleventh_destination_batch_keeps_campus_conflict_and_housing_limits_visible(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("雷恩商學院")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{RENNES}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(RENNES)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("EUR 450–700")
    expect(official).to_contain_text("不能套用 Paris")
    expect(official).to_contain_text("不是保證床位")
    expect(official).to_contain_text("Level 2")
    expect(official).to_contain_text("兩個官方來源不一致")
    expect(official).to_contain_text("不能自行判定 Level 2 春季可申請")
    expect(official).to_contain_text("查看本頁全部查核來源（4）")


def test_twelfth_destination_batch_keeps_old_prices_and_local_housing_separate(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("馬來西亞管理與科技大學")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{MSU}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(MSU)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("March 2023")
    expect(official).to_contain_text("不能當成 2026/27 現價")
    expect(official).to_contain_text("LOCAL STUDENT ONLY")
    expect(official).to_contain_text("長庚交換生不能用這個較低價格估算")
    expect(official).to_contain_text("最短租六個月")
    expect(official).to_contain_text("不能據此宣稱 2026 已正式營運")
    expect(official).to_contain_text("不能直接建立 2026/27 提醒")
    expect(official).to_contain_text("查看本頁全部查核來源（5）")


def test_thirteenth_destination_batch_keeps_department_scope_and_housing_limits_visible(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("IAE Aix")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{IAE_AIX}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(IAE_AIX)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("只作長庚管理學院的院級交換參考")
    expect(official).to_contain_text("free mover 或直接申請不符合資格")
    expect(official).to_contain_text("學士三年級且年滿 21 歲")
    expect(official).to_contain_text("課程全部為 Master’s level")
    expect(official).to_contain_text("EUR 260")
    expect(official).to_contain_text("EUR 450–800")
    expect(official).to_contain_text("120 小時")
    expect(official).to_contain_text("EUR 70")
    expect(official).to_contain_text("不能選宿舍或房型")
    expect(official).to_contain_text("查看本頁全部查核來源（4）")


def test_fourteenth_destination_batch_keeps_old_department_rules_out_of_current_exchange(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("恩荷芬")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{TU_EINDHOVEN}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(TU_EINDHOVEN)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("EUR 1,200／月")
    expect(official).to_contain_text("一般學位生參考，不是長庚交換帳單")
    expect(official).to_contain_text("2023–24 Chemical Engineering and Chemistry")
    expect(official).to_contain_text("free mover")
    expect(official).to_contain_text("非常有限")
    expect(official).to_contain_text("先到先得")
    expect(official).to_contain_text("約短缺 1,500 個學生住宿單位")
    expect(official).to_contain_text("不能直接建立 2026/27 提醒")
    expect(official).to_contain_text("查看本頁全部查核來源（4）")


def test_fifteenth_destination_batch_keeps_old_wuhan_costs_and_transport_out_of_current_plan(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("武漢")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{WUHAN}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(WUHAN)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("June 2016")
    expect(official).to_contain_text("沒有列出長庚大學")
    expect(official).to_contain_text("RMB 600–1,400／月")
    expect(official).to_contain_text("不能當成 2026/27 預算或帳單")
    expect(official).to_contain_text("沒有公開長庚交換生的房型")
    expect(official).to_contain_text("2022 校園文章曾寫 school bus 調整為免費")
    expect(official).to_contain_text("2026 Campus Card")
    expect(official).to_contain_text("不能把 2022 免費校車當成現行交換生權益")
    expect(official).to_contain_text("不能支持 workflow 內的 15 April／15 October")
    expect(official).to_contain_text("查看本頁全部查核來源（5）")


def test_sixteenth_destination_batch_keeps_icd_campuses_costs_and_deadlines_separate(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server, "partners")
    page.locator("#partner-search").fill("ICD")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{ICD}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(ICD)
    page.locator("#detail-tab-life").click()

    page.locator(".life-official-guide > summary").click()
    official = page.locator("#destination-official-content")
    expect(official).to_be_visible()
    expect(official).to_contain_text("官方生活資訊已查核", timeout=15_000)
    expect(official).not_to_contain_text("官方生活資訊部分查核")
    expect(official).to_contain_text("巴黎 或 圖盧茲")
    expect(official).to_contain_text("只公開 巴黎 與 圖盧茲")
    expect(official).to_contain_text("EUR 5,495／學期")
    expect(official).to_contain_text("不適用交換生")
    expect(official).to_contain_text("不代表生活成本免費")
    expect(official).to_contain_text("EUR 900–1,200／月")
    expect(official).to_contain_text("EUR 500–700")
    expect(official).to_contain_text("不保證床位")
    expect(official).to_contain_text("EUR 90.80／月")
    expect(official).to_contain_text("EUR 15.50／月")
    expect(official).to_contain_text("15 November")
    expect(official).to_contain_text("1 November")
    expect(official).to_contain_text("不能直接建立提醒")
    expect(official).to_contain_text("查看本頁全部查核來源（5）")


def test_multi_plan_calendar_detects_same_day_conflicts_and_syncs_school_identity(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("calendar-conflict")
    session = live_server.register(email, "E2E 多計畫學生")
    live_server.verify_student(session["profile"]["id"])
    saved = requests.put(
        f"{live_server.base_url}/account/workspace",
        headers=_auth_headers(session),
        json={
            "home_school": "長庚大學",
            "revision": 0,
            "favorite_schools": [LINCOLN, MEIJI],
            "application_schools": [LINCOLN, MEIJI],
            "application_context": {"school_name": "長庚大學"},
        },
        timeout=10,
    )
    saved.raise_for_status()
    login_through_web(page, live_server, email)

    page.evaluate("window.location.hash = '#calendar'")
    expect(page.locator("#application-calendar-title")).to_be_visible()
    page.locator("#calendar-insights > summary").click()
    expect(page.locator("#calendar-conflict-center")).to_be_visible()
    for school in (LINCOLN, MEIJI):
        expect(
            page.locator(f'#calendar-event-school option[value="{school}"]')
        ).to_be_attached()

    for school, title in (
        (LINCOLN, "E2E Lincoln 紙本送達"),
        (MEIJI, "E2E Meiji 校內送件"),
    ):
        page.locator(".calendar-quick-add").evaluate("element => { element.open = true; }")
        page.locator('#calendar-event-form input[name="title"]').fill(title)
        page.locator('#calendar-event-form input[name="date"]').fill("2027-10-08")
        page.locator("#calendar-event-school").select_option(school)
        page.locator('#calendar-event-form button[type="submit"]').click()

    expect(page.locator("#calendar-conflict-list")).to_contain_text(
        "同一天有多校任務",
        timeout=15_000,
    )
    expect(page.locator("#calendar-conflict-list")).to_contain_text(LINCOLN)
    expect(page.locator("#calendar-conflict-list")).to_contain_text(MEIJI)
    expect(page.locator("#calendar-alert-brief")).to_contain_text("組申請時程需要協調")
    page.locator('[data-calendar-conflict-date="2027-10-08"]').first.click()
    expect(page.locator("#calendar-agenda-list")).to_contain_text(
        "E2E Lincoln 紙本送達"
    )
    expect(page.locator("#calendar-agenda-list")).to_contain_text(
        "E2E Meiji 校內送件"
    )
    expect(page.locator("#calendar-agenda-list .calendar-conflict-badge")).to_have_count(2)

    workspace = _wait_for_workspace(
        live_server,
        session,
        lambda item: len(item.get("workspace", {}).get("deadline_events", [])) == 2,
    )["workspace"]
    assert {event["school_name"] for event in workspace["deadline_events"]} == {
        LINCOLN,
        MEIJI,
    }


def test_calendar_task_schedule_uses_student_days_and_completion_stops_start_marker(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("calendar-schedule")
    session = live_server.register(email, "E2E 任務排程學生")
    live_server.verify_student(session["profile"]["id"])
    saved = requests.put(
        f"{live_server.base_url}/account/workspace",
        headers=_auth_headers(session),
        json={
            "home_school": "長庚大學",
            "revision": 0,
            "favorite_schools": [LINCOLN],
            "application_schools": [LINCOLN],
            "application_context": {"school_name": "長庚大學"},
        },
        timeout=10,
    )
    saved.raise_for_status()
    login_through_web(page, live_server, email)

    today = date.today()
    deadline = today + timedelta(days=12)
    title = "E2E 完成英文讀書計畫"
    page.evaluate("window.location.hash = '#calendar'")
    page.locator("#calendar-insights > summary").click()
    expect(page.locator("#calendar-task-schedule-center")).to_be_visible()
    page.locator(".calendar-quick-add").evaluate("element => { element.open = true; }")
    page.locator('#calendar-event-form input[name="title"]').fill(title)
    page.locator('#calendar-event-form input[name="date"]').fill(deadline.isoformat())
    page.locator('#calendar-event-form input[name="preparation_days"]').fill("12")
    page.locator("#calendar-event-school").select_option(LINCOLN)
    page.locator('#calendar-event-form button[type="submit"]').click()

    schedule = page.locator("#calendar-task-schedule-list")
    expect(schedule).to_contain_text(title, timeout=15_000)
    expect(schedule).to_contain_text(today.isoformat())
    expect(schedule).to_contain_text("現在應開始")
    page.locator(
        f'[data-calendar-task-date="{today.isoformat()}"]'
    ).first.click()
    expect(page.locator("#calendar-agenda-list")).to_contain_text(
        f"開始準備：{title}"
    )

    workspace = _wait_for_workspace(
        live_server,
        session,
        lambda item: any(
            event.get("title") == title
            and event.get("preparation_days") == 12
            and event.get("status") == "todo"
            for event in item.get("workspace", {}).get("deadline_events", [])
        ),
    )["workspace"]
    assert not any(event.get("generated_from_event_id") for event in workspace["deadline_events"])

    notifications = requests.get(
        f"{live_server.base_url}/account/notifications",
        headers=_auth_headers(session),
        timeout=10,
    )
    notifications.raise_for_status()
    assert any(
        item["source_key"].startswith("calendar-start:")
        for item in notifications.json()["items"]
    )

    page.locator(
        f'[data-calendar-task-deadline="{deadline.isoformat()}"]'
    ).first.click()
    task = page.locator("#calendar-agenda-list .calendar-agenda-item").filter(
        has_text=title
    )
    task.locator("[data-calendar-task-status]").select_option("ready")
    expect(schedule).to_contain_text("已完成", timeout=15_000)
    completed_workspace = _wait_for_workspace(
        live_server,
        session,
        lambda item: any(
            event.get("title") == title and event.get("status") == "ready"
            for event in item.get("workspace", {}).get("deadline_events", [])
        ),
    )["workspace"]
    assert next(
        event for event in completed_workspace["deadline_events"] if event["title"] == title
    )["preparation_days"] == 12

    page.locator(
        f'[data-calendar-task-date="{today.isoformat()}"]'
    ).first.click()
    expect(page.locator("#calendar-agenda-list")).not_to_contain_text(
        f"開始準備：{title}"
    )


def test_public_free_calendar_sync_is_locked_but_old_url_can_be_revoked(
    page: Page,
    live_server: LiveServer,
    monkeypatch,
) -> None:
    email = _email("calendar-entitlement")
    session = live_server.register(email, "E2E 免費方案學生")
    enabled = requests.post(
        f"{live_server.base_url}/calendar-sync/enable",
        headers=_auth_headers(session),
        timeout=10,
    )
    enabled.raise_for_status()
    feed_url = enabled.json()["subscription_url"]
    assert requests.get(feed_url, timeout=10).status_code == 200

    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    login_through_web(page, live_server, email)
    page.evaluate("window.location.hash = '#calendar'")
    expect(page.locator("#calendar-sync-panel")).to_be_visible()
    page.locator("#calendar-sync-panel").evaluate("element => { element.open = true; }")
    expect(page.locator("#calendar-sync-summary")).to_have_text(
        "目前方案未包含外部日曆同步"
    )
    expect(page.locator("#calendar-sync-status")).to_contain_text(
        "外部日曆同步是進階功能"
    )
    expect(page.locator("#calendar-sync-status")).to_contain_text(
        "Web 站內基本截止提醒仍可使用"
    )
    expect(page.locator('[data-calendar-provider="google"]')).to_be_disabled()
    assert requests.get(feed_url, timeout=10).status_code == 404

    page.once("dialog", lambda dialog: dialog.accept())
    with page.expect_response(
        lambda response: response.url == f"{live_server.base_url}/calendar-sync"
        and response.request.method == "DELETE",
    ) as revoke_response_info:
        page.locator("[data-revoke-calendar-sync]").click()
    assert revoke_response_info.value.ok
    expect(page.locator("#calendar-sync-status")).to_contain_text(
        "外部日曆同步是進階功能"
    )
    assert requests.get(feed_url, timeout=10).status_code == 404


def test_public_free_application_center_keeps_official_forms_but_locks_generation(
    page: Page,
    live_server: LiveServer,
    monkeypatch,
) -> None:
    email = _email("application-entitlement")
    live_server.register(email, "E2E 免費文件學生")
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    login_through_web(page, live_server, email)

    page.evaluate("window.location.hash = '#application-center'")
    expect(page.locator("#application-center-title")).to_be_visible()
    expect(page.locator("#application-generation-gate")).to_be_visible()
    expect(page.locator("#application-generation-gate")).to_contain_text(
        "自動填表與申請文件套件是進階功能"
    )
    expect(page.locator("#application-generation-gate")).to_contain_text(
        "下載官方表格"
    )
    expect(page.locator("#application-profile-panel")).to_be_hidden()
    expect(page.locator("#download-application-packet")).to_be_disabled()

    page.locator('#application-context-form select[name="program_type"]').select_option(
        "short_term_credit"
    )
    official = page.locator(".application-template-official").first
    expect(official).to_be_visible(timeout=15_000)
    assert official.get_attribute("href").startswith("https://www.cgu.edu.tw/")

    locked = page.locator(".application-template-open").first
    expect(locked).to_have_attribute("aria-disabled", "true")
    locked.click(force=True)
    assert "#application-form=" not in page.url


def test_document_check_uses_non_ai_rules_and_is_subscription_gated(
    page: Page,
    live_server: LiveServer,
    monkeypatch,
) -> None:
    email = _email("document-check-entitlement")
    live_server.register(email, "E2E 文件檢查學生")
    login_through_web(page, live_server, email)

    page.evaluate("window.location.hash = '#document-check'")
    expect(page.locator("#document-check-title")).to_be_visible()
    expect(page.locator("#document-check-gate")).to_be_hidden()
    expect(page.locator("#document-check-content")).to_be_visible()
    expect(page.locator('#document-check-form input[name="use_ai"]')).to_be_disabled()
    expect(page.locator(".document-check-toggle.is-paused")).to_contain_text(
        "不會把文字傳給外部 AI"
    )
    document_check_requests: list[str] = []

    def record_document_check(request) -> None:
        if (
            request.url == f"{live_server.base_url}/document-check"
            and request.method == "POST"
        ):
            document_check_requests.append(request.url)

    page.on("request", record_document_check)

    page.locator("#document-check-file").set_input_files(
        {
            "name": "讀書計畫.txt",
            "mimeType": "text/plain",
            "buffer": ("申請動機、預計修課內容、返國後學習規劃。" * 30).encode(),
        }
    )
    consent = page.locator("#document-check-consent")
    expect(consent).not_to_be_checked()
    page.locator("#document-check-submit").click()
    expect(consent).to_be_focused()
    assert document_check_requests == []

    consent.check()
    with page.expect_response(
        lambda response: response.url == f"{live_server.base_url}/document-check"
        and response.request.method == "POST",
    ) as review_response_info:
        page.locator("#document-check-submit").click()
    assert review_response_info.value.ok
    assert review_response_info.value.headers["cache-control"] == "no-store"
    assert len(document_check_requests) == 1
    expect(page.locator("#document-check-status")).to_have_text("檢查完成")
    expect(page.locator("#document-check-result")).to_contain_text("完整度")
    expect(page.locator("#document-check-result")).not_to_contain_text("AI 深度檢查")

    page.locator("#document-check-file").set_input_files(
        {
            "name": "第二份讀書計畫.txt",
            "mimeType": "text/plain",
            "buffer": ("第二份文件內容。" * 80).encode(),
        }
    )
    expect(consent).not_to_be_checked()
    page.locator("#document-check-form").dispatch_event("submit")
    expect(page.locator("#document-check-status")).to_contain_text("同意")
    assert len(document_check_requests) == 1

    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    page.reload()
    page.evaluate("window.location.hash = '#document-check'")
    expect(page.locator("#document-check-gate")).to_be_visible()
    expect(page.locator("#document-check-gate")).to_contain_text(
        "文件完整性檢查是進階功能"
    )
    expect(page.locator("#document-check-content")).to_be_hidden()


def test_writing_assistant_is_fail_closed_while_local_ai_is_not_ready(
    page: Page,
    live_server: LiveServer,
) -> None:
    rewrite_requests: list[str] = []
    page.on(
        "request",
        lambda request: rewrite_requests.append(request.url)
        if request.method == "POST" and request.url.endswith("/ai/rewrite-document")
        else None,
    )
    enter_public_site(page, live_server, "writing-assistant")

    expect(page.locator("#writing-assistant-title")).to_have_text("文件改寫暫緩")
    expect(page.locator('#writing-assistant-form textarea[name="text"]')).to_be_disabled()
    expect(page.locator("#writing-assistant-submit")).to_be_disabled()
    expect(page.locator("#writing-assistant-status")).to_contain_text(
        "AI 功能暫緩"
    )
    expect(page.locator("#writing-assistant-result")).to_contain_text(
        "本地 AI 尚未設定"
    )

    page.locator("#writing-assistant-form").dispatch_event("submit")
    expect(page.locator("#writing-assistant-status")).to_contain_text(
        "現在無法送出文字"
    )
    assert rewrite_requests == []


def test_authenticated_plan_notifications_and_progress_sync_across_devices(
    page: Page,
    browser: Browser,
    live_server: LiveServer,
    request,
) -> None:
    # Isolated, explicitly applicable source fixture: this tests synchronization,
    # not whether bundled historical sources match a student's selected round.
    from test_notifications import _content_workflow
    from exchange_info.models import ApplicationSubmissionDetails
    from exchange_info.storage import load_application_workflows, save_application_workflows, replace_application_workflow

    original = load_application_workflows(live_server.data_dir)
    request.addfinalizer(lambda: save_application_workflows(original, live_server.data_dir))
    workflow = _content_workflow("E2E 文件送件", version=1)
    workflow = workflow.model_copy(update={"academic_year":"115", "steps":[
        workflow.steps[0].model_copy(update={"submission":ApplicationSubmissionDetails(method="online")})
    ]})
    replace_application_workflow(workflow, live_server.data_dir)
    email = _email("plan")
    session = live_server.register(email, "E2E 計畫學生")
    live_server.verify_student(session["profile"]["id"])
    live_server.add_notification(
        session["profile"]["id"],
        title="E2E 交換申請期限提醒",
    )
    login_through_web(page, live_server, email)

    expect(page.locator("#notification-button")).to_be_visible()
    page.locator("#notification-button").click()
    expect(page.locator("#notification-dialog")).to_be_visible()
    expect(page.locator("#notification-center-list")).to_contain_text(
        "E2E 交換申請期限提醒"
    )
    page.locator("[data-close-notifications]").last.click()

    page.evaluate("window.location.hash = '#overview'")
    page.locator('.planning-documents a').click()
    page.locator('#application-workspace-tools a[href="#documents"]').click()
    expect(page.locator("#documents")).to_be_visible()
    document_progress = page.locator(
        "#document-workspace-list [data-document-status]"
    ).first
    expect(document_progress).to_be_enabled()
    document_id = document_progress.get_attribute("data-document-status")
    assert document_id
    document_progress.select_option("preparing")
    _wait_for_workspace(live_server, session, lambda item:
        item.get("exists") and item["workspace"].get("document_readiness", {}).get(document_id) == "preparing")
    page.evaluate("window.location.hash = '#overview'")
    expect(page.locator('#planning-document-status')).to_contain_text("準備中")
    page.locator('.planning-documents a').click()
    page.locator('#application-workspace-tools a[href="#documents"]').click()
    document_progress.select_option("ready")
    _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("exists")
        and item["workspace"].get("document_readiness", {}).get(document_id)
        == "ready",
    )

    page.evaluate("window.location.hash = '#partners'")
    page.locator("#partner-search").fill("林肯")
    favorite = page.locator(
        f'#partner-table .favorite-toggle[data-school-name="{LINCOLN}"]'
    ).first
    expect(favorite).to_have_attribute("aria-label", f"收藏{LINCOLN}")
    favorite.click()
    expect(favorite).to_have_attribute("aria-pressed", "true")
    _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("exists")
        and LINCOLN in item["workspace"]["favorite_schools"],
    )

    page.evaluate("window.location.hash = '#eligibility'")
    expect(page.locator("#eligibility-title")).to_be_visible()
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-department").select_option("資訊工程學系")
    _select_first_nonempty(page.locator("#advisor-degree"))
    page.locator("#eligibility-academic-year").select_option("115")
    page.locator("#eligibility-application-round").select_option("第一梯次")
    page.locator("#advisor-academic-score").fill("85")
    page.locator("#advisor-language-test").select_option("ielts")
    page.locator("#advisor-language-score").fill("6.5")
    page.locator("#advisor-target-term").select_option("2027-fall")
    expect(
        page.locator(f'#eligibility-preference-1 option[value="{LINCOLN}"]')
    ).to_be_attached()
    page.locator("#eligibility-preference-1").select_option(LINCOLN)
    page.locator("#advisor-form button[type=submit]").click()
    expect(page.locator("#eligibility-result h3")).to_contain_text("申請清單")

    synced = _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("exists")
        and LINCOLN in item["workspace"]["application_schools"],
    )["workspace"]
    assert synced["application_context"]["department"] == "資訊工程學系"
    assert synced["application_context"]["application_round"] == "第一梯次"

    page.evaluate("window.location.hash = '#budget'")
    expect(page.locator("#budget-title")).to_be_visible()
    page.locator("#budget-school").select_option(LINCOLN)
    page.locator("#budget-currency").select_option("NZD")
    page.locator("#budget-months").fill("5")
    page.locator("#budget-housing").fill("12300")
    page.locator("#budget-food").fill("6700")
    page.locator("#budget-onetime").fill("52000")
    expect(page.locator("#budget-save-button")).to_contain_text("儲存並同步估算")
    page.locator("#budget-save-button").click()
    budget_workspace = _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("exists")
        and item["workspace"].get("budget_plans", {}).get(LINCOLN, {}).get("housing")
        == 12300,
    )["workspace"]
    assert budget_workspace["budget_plans"][LINCOLN]["currency"] == "NZD"
    assert budget_workspace["budget_plans"][LINCOLN]["one_time"] == 52000

    page.evaluate("window.location.hash = '#partners'")
    expect(page.locator("#partner-search")).to_be_visible()
    page.locator("#partner-search").fill("林肯")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{LINCOLN}"]'
    ).first.click()
    expect(page.locator("#school-detail-title")).to_have_text(LINCOLN)
    page.locator("#detail-tab-life").click()
    expect(page.locator("#destination-official-content")).to_contain_text(
        "官方生活資訊已查核",
        timeout=15_000,
    )
    expect(page.locator("#destination-official-content")).to_contain_text(
        "來源（2）"
    )
    page.locator("#detail-tab-application").click()
    application_progress = page.locator("#application-tracker .progress-checkbox").first
    expect(application_progress).to_be_enabled()
    progress_step = application_progress.get_attribute("data-progress-step")
    assert progress_step
    application_progress.check()
    _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("exists")
        and item["workspace"].get("application_progress", {})
        .get(LINCOLN, {})
        .get(progress_step)
        is True,
    )
    actionable = page.locator(".workflow-progress:not(.is-disabled)").first
    actionable_step = actionable.locator("xpath=ancestor::details[1]")
    if actionable_step.get_attribute("open") is None:
        actionable_step.locator("summary").click()
    expect(actionable).to_be_visible()
    actionable.locator('[data-submission-action="start"]').click()
    expect(page.locator(".workflow-progress.status-preparing").first).to_contain_text(
        "準備中"
    )
    progress_workspace = _wait_for_workspace(
        live_server,
        session,
        lambda item: any(
            row["status"] == "preparing"
            for row in item.get("workspace", {}).get("submission_progress", {}).values()
        ),
    )["workspace"]
    assert any(
        row["status"] == "preparing"
        for row in progress_workspace["submission_progress"].values()
    )

    second_context = browser.new_context(viewport={"width": 390, "height": 844})
    second_page = second_context.new_page()
    try:
        login_through_web(second_page, live_server, email)
        second_page.evaluate("window.location.hash = '#documents'")
        expect(second_page.locator(f'[data-document-status="{document_id}"]')).to_have_value("ready")
        second_page.evaluate("window.location.hash = '#eligibility'")
        expect(second_page.locator("#advisor-department")).to_have_value(
            "資訊工程學系"
        )
        expect(second_page.locator("#eligibility-preference-1")).to_have_value(LINCOLN)
        second_page.evaluate("window.location.hash = '#budget'")
        expect(second_page.locator("#budget-school")).to_have_value(LINCOLN)
        expect(second_page.locator("#budget-currency")).to_have_value("NZD")
        expect(second_page.locator("#budget-housing")).to_have_value("12300")
        expect(second_page.locator("#budget-food")).to_have_value("6700")
        expect(second_page.locator("#budget-onetime")).to_have_value("52000")
    finally:
        second_context.close()


def test_verified_student_reports_workflow_issue_and_admin_closes_it(
    page: Page,
    browser: Browser,
    live_server: LiveServer,
    monkeypatch,
) -> None:
    student_email = _email("workflow-issue-student")
    student_session = live_server.register(student_email, "E2E 規定回報學生")
    live_server.verify_student(student_session["profile"]["id"])
    login_through_web(page, live_server, student_email)

    page.evaluate("window.location.hash = '#partners'")
    expect(page.locator("#partner-search")).to_be_visible()
    page.locator("#partner-search").fill("林肯")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{LINCOLN}"]'
    ).first.click()
    page.locator("#detail-tab-application").click()

    report_button = page.locator("[data-workflow-issue-report]").first
    expect(report_button).to_be_visible(timeout=15_000)
    report_button.click()
    dialog = page.locator("#workflow-issue-report-dialog")
    expect(dialog).to_be_visible()
    expect(dialog).to_contain_text("回報不會直接修改學生看到的正式規定")

    description = "官方頁面的截止日期與目前流程不同，請重新核對後續正式修正。"
    dialog.locator('select[name="category"]').select_option("deadline")
    dialog.locator('textarea[name="description"]').fill(description)
    dialog.locator('input[name="official_source_url"]').fill(
        "https://www.lincoln.ac.nz/study/international-students/"
    )
    dialog.locator('input[name="confirm_boundary"]').check()
    with page.expect_response(
        lambda response: response.url
        == f"{live_server.base_url}/application-workflow-issue-reports"
        and response.request.method == "POST"
    ) as submitted_response_info:
        dialog.locator('button[type="submit"]').click()
    submitted_response = submitted_response_info.value
    assert submitted_response.status == 202
    report = submitted_response.json()
    assert report["status"] == "pending"
    assert report["description"] == description
    expect(dialog).to_be_hidden()
    expect(page.locator("#page-status")).to_contain_text(
        "回報已送出。管理員會先核對"
    )

    reviewer_email = _email("workflow-issue-reviewer")
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", reviewer_email)
    reviewer_session = live_server.register(reviewer_email, "E2E 規定核對管理員")
    admin_context = browser.new_context(viewport={"width": 390, "height": 844})
    admin_page = admin_context.new_page()
    try:
        _open_content_review_workbench(
            admin_page,
            live_server,
            reviewer_email,
            reviewer_session,
        )
        card = admin_page.locator(
            f'[data-workflow-issue-report-id="{report["id"]}"]'
        )
        expect(card).to_be_visible(timeout=15_000)
        expect(card).to_contain_text(description)
        expect(card).to_contain_text("回報成立只會關閉本案")
        card.locator("[data-workflow-issue-report-note]").fill(
            "已核對學生提供的官方頁面，確認截止日期需要另開 revision 修正。"
        )
        with admin_page.expect_response(
            lambda response: response.url
            == (
                f"{live_server.base_url}/admin/"
                f"application-workflow-issue-reports/{report['id']}"
            )
            and response.request.method == "PATCH"
        ) as reviewed_response_info:
            card.locator('[data-workflow-issue-review="resolved"]').click()
        reviewed_response = reviewed_response_info.value
        assert reviewed_response.status == 200
        expect(admin_page.locator("#review-announcement")).to_contain_text(
            "正式規定尚未變更"
        )
        expect(card).to_be_hidden()
    finally:
        admin_context.close()

    closed = requests.get(
        f"{live_server.base_url}/admin/application-workflow-issue-reports",
        params={"status": "resolved"},
        headers=_auth_headers(reviewer_session),
        timeout=10,
    )
    closed.raise_for_status()
    assert "no-store" in closed.headers["Cache-Control"]
    closed_report = next(row for row in closed.json() if row["id"] == report["id"])
    assert closed_report["status"] == "resolved"
    assert closed_report["review"]["note"].startswith("已核對學生提供的官方頁面")


def test_workflow_issue_report_keeps_same_mutation_when_accepted_body_is_unverifiable(
    page: Page,
    live_server: LiveServer,
) -> None:
    student_email = _email("workflow-issue-unknown-result")
    student_session = live_server.register(student_email, "E2E 回報結果不明學生")
    live_server.verify_student(student_session["profile"]["id"])
    login_through_web(page, live_server, student_email)

    mutation_ids: list[str] = []

    def return_unverifiable_success(route) -> None:
        mutation_ids.append(
            route.request.headers.get("x-content-report-mutation-id", "")
        )
        request_payload = route.request.post_data_json
        route.fulfill(
            status=202,
            content_type="application/json",
            body=json.dumps(
                {
                    **request_payload,
                    "id": "wrong-report-from-another-request",
                    "status": "pending",
                    "category": "source",
                }
            ),
        )

    page.route("**/application-workflow-issue-reports", return_unverifiable_success)
    page.evaluate("window.location.hash = '#partners'")
    page.locator("#partner-search").fill("林肯")
    page.locator(
        f'#partner-table .school-detail-trigger[data-school-name="{LINCOLN}"]'
    ).first.click()
    page.locator("#detail-tab-application").click()

    report_button = page.locator("[data-workflow-issue-report]").first
    expect(report_button).to_be_visible(timeout=15_000)
    report_button.click()
    dialog = page.locator("#workflow-issue-report-dialog")
    description = "官方頁面與目前申請期限不同，這次要驗證結果不明時不能產生第二筆。"
    dialog.locator('select[name="category"]').select_option("deadline")
    dialog.locator('textarea[name="description"]').fill(description)
    dialog.locator('input[name="official_source_url"]').fill(
        "https://www.lincoln.ac.nz/study/international-students/"
    )
    dialog.locator('input[name="confirm_boundary"]').check()
    dialog.locator('button[type="submit"]').click()

    expect(dialog).to_be_visible()
    expect(dialog.locator("#workflow-issue-report-status")).to_contain_text(
        "結果尚未確認"
    )
    pending = json.loads(
        page.evaluate(
            "window.sessionStorage.getItem('exchange-guide-workflow-issue-report-pending-v1')"
        )
    )
    assert pending["mutation_id"] == mutation_ids[0]
    dialog.locator("[data-close-workflow-issue-report]").first.click()
    expect(dialog).to_be_hidden()

    report_button.click()
    expect(dialog).to_contain_text("先前回報結果尚未確認")
    expect(dialog.locator('textarea[name="description"]')).to_have_value(description)
    dialog.locator('input[name="confirm_boundary"]').check()
    dialog.locator('button[type="submit"]').click()
    expect(dialog.locator("#workflow-issue-report-status")).to_contain_text(
        "結果尚未確認"
    )
    assert mutation_ids == [pending["mutation_id"], pending["mutation_id"]]


def test_offline_workspace_change_syncs_on_reconnect_and_reaches_fresh_context(
    page: Page,
    browser: Browser,
    live_server: LiveServer,
) -> None:
    email = _email("workspace-offline")
    session = live_server.register(email, "E2E 離線同步學生")
    login_through_web(page, live_server, email)

    initial = _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("exists") is True,
    )["workspace"]
    assert LINCOLN not in initial["favorite_schools"]
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    page.evaluate("window.location.hash = '#partners'")
    page.locator("#partner-search").fill("林肯")
    favorite = page.locator(
        f'.favorite-toggle[data-school-name="{LINCOLN}"]'
    ).first
    expect(favorite).to_have_attribute("aria-pressed", "false")
    page.evaluate(
        """() => {
          window.__workspaceOnlineEvents = 0;
          window.addEventListener("online", () => {
            window.__workspaceOnlineEvents += 1;
          });
        }"""
    )

    page.context.set_offline(True)
    try:
        page.wait_for_function("() => navigator.onLine === false")
        expect(page.locator("#account-workspace-sync-label")).to_have_text(
            "離線，稍後同步"
        )
        favorite.click()
        expect(favorite).to_have_attribute("aria-pressed", "true")
        page.wait_for_function(
            """school => {
              const metadata = JSON.parse(
                window.localStorage.getItem("exchange-guide-workspace-sync-v1") || "{}"
              );
              return Object.values(metadata.pending || {}).some(
                (workspace) => (workspace.favorite_schools || []).includes(school)
              );
            }""",
            arg=LINCOLN,
        )
        assert LINCOLN not in _workspace(live_server, session)["workspace"][
            "favorite_schools"
        ]

        with page.expect_response(
            lambda response: response.url
            == f"{live_server.base_url}/account/workspace"
            and response.request.method == "PUT"
            and response.status == 200,
            timeout=15_000,
        ):
            page.context.set_offline(False)
        page.wait_for_function("() => window.__workspaceOnlineEvents > 0")
    finally:
        page.context.set_offline(False)

    synced = _wait_for_workspace(
        live_server,
        session,
        lambda item: LINCOLN
        in item.get("workspace", {}).get("favorite_schools", []),
    )["workspace"]
    assert synced["revision"] > initial["revision"]
    page.wait_for_function(
        """() => {
          const metadata = JSON.parse(
            window.localStorage.getItem("exchange-guide-workspace-sync-v1") || "{}"
          );
          return Object.keys(metadata.pending || {}).length === 0;
        }"""
    )
    expect(page.locator("#account-workspace-sync-label")).to_have_text("已同步")

    second_context = browser.new_context(viewport={"width": 390, "height": 844})
    second_page = second_context.new_page()
    try:
        login_through_web(second_page, live_server, email)
        expect(second_page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )
        second_page.evaluate("window.location.hash = '#partners'")
        second_page.locator("#partner-search").fill("林肯")
        expect(
            second_page.locator(
                f'.favorite-toggle[data-school-name="{LINCOLN}"]'
            ).first
        ).to_have_attribute("aria-pressed", "true")
        assert second_page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
    finally:
        second_context.close()


def test_session_restore_outage_quarantines_private_state_then_recovers_same_owner(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("session-restore-outage")
    session = live_server.register(email, "E2E 離線重載學生")
    live_server.verify_student(session["profile"]["id"])
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    _seed_quarantined_workspace_state(
        page,
        favorite_school=LINCOLN,
        sentinel="只屬於同一帳號的私人資料",
    )
    workspace_puts: list[str] = []

    def record_workspace_put(request) -> None:
        if (
            urlparse(request.url).path == "/account/workspace"
            and request.method == "PUT"
        ):
            workspace_puts.append(request.url)

    def abort_session_restore(route) -> None:
        route.abort("internetdisconnected")

    page.on("request", record_workspace_put)
    page.route("**/auth/session", abort_session_restore)
    try:
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("() => state.authRestoreState === 'unavailable'")
        expect(page.locator("#account-button-label")).to_have_text("離線")
        expect(page.locator("#account-button")).to_have_attribute(
            "aria-label", "目前離線，私人資料已隱藏"
        )
        assert page.evaluate("state.account === null")
        assert page.evaluate("state.favorites.size") == 0
        assert page.evaluate("state.eligibilityProfile === null")
        assert page.evaluate("state.anonymousIdentity === null")
        assert page.evaluate("Object.keys(state.applicationProfile).length") == 0
        assert page.evaluate("Object.keys(state.applicationAnswers).length") == 0
        assert page.evaluate(
            "window.localStorage.getItem('exchange-guide-auth-token')"
        ) is None
        assert LINCOLN in page.evaluate(
            "JSON.parse(window.localStorage.getItem('exchange-guide-favorites') || '[]')"
        )
        assert page.evaluate(
            "JSON.parse(window.localStorage.getItem('exchange-guide-anonymous-identity')).access_token"
        ) == "只屬於同一帳號的私人資料"
        quarantined = page.evaluate(
            """() => JSON.parse(
              window.localStorage.getItem('exchange-guide-workspace-sync-v1') || '{}'
            )"""
        )
        assert quarantined["account_id"] == session["profile"]["id"]
        assert LINCOLN in quarantined["pending"]["長庚大學"]["favorite_schools"]
        assert workspace_puts == []

        page.unroute("**/auth/session", abort_session_restore)
        with page.expect_response(
            lambda response: response.url == f"{live_server.base_url}/auth/session"
            and response.status == 200,
            timeout=15_000,
        ):
            page.evaluate("window.dispatchEvent(new Event('online'))")
        expect(page.locator("#account-button-label")).to_have_text(
            "E2E 離線重載學生", timeout=15_000
        )
        recovered = _wait_for_workspace(
            live_server,
            session,
            lambda item: LINCOLN
            in item.get("workspace", {}).get("favorite_schools", []),
            timeout=15,
        )["workspace"]
        assert LINCOLN in recovered["favorite_schools"]
        page.wait_for_function(
            """() => {
              const metadata = JSON.parse(
                window.localStorage.getItem('exchange-guide-workspace-sync-v1') || '{}'
              );
              return Object.keys(metadata.pending || {}).length === 0;
            }"""
        )
        assert page.evaluate("state.favorites.has(%s)" % json.dumps(LINCOLN))
        assert page.evaluate("state.eligibilityProfile.department") == (
            "只屬於同一帳號的私人資料"
        )
        assert page.evaluate("state.anonymousIdentity !== null")
        assert workspace_puts
    finally:
        page.unroute("**/auth/session", abort_session_restore)


def test_revoked_session_clears_quarantine_without_uploading_pending_workspace(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("session-restore-revoked")
    session = live_server.register(email, "E2E 已撤銷重載學生")
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    _seed_quarantined_workspace_state(
        page,
        favorite_school=MEIJI,
        sentinel="撤銷後必須清除的私人資料",
    )
    workspace_puts: list[str] = []

    def record_workspace_put(request) -> None:
        if (
            urlparse(request.url).path == "/account/workspace"
            and request.method == "PUT"
        ):
            workspace_puts.append(request.url)

    def abort_session_restore(route) -> None:
        route.abort("internetdisconnected")

    page.on("request", record_workspace_put)
    page.route("**/auth/session", abort_session_restore)
    try:
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("() => state.authRestoreState === 'unavailable'")
        expect(page.locator("#account-button-label")).to_have_text("離線")
        assert workspace_puts == []
        assert MEIJI not in _workspace(live_server, session)["workspace"][
            "favorite_schools"
        ]

        browser_session_cookie = next(
            cookie
            for cookie in page.context.cookies()
            if cookie["name"] == "exchange_guide_session"
        )
        revoked = requests.post(
            f"{live_server.base_url}/auth/logout",
            cookies={
                browser_session_cookie["name"]: browser_session_cookie["value"]
            },
            timeout=10,
        )
        assert revoked.status_code == 204
        page.unroute("**/auth/session", abort_session_restore)
        with page.expect_response(
            lambda response: response.url == f"{live_server.base_url}/auth/session"
            and response.status == 200,
            timeout=15_000,
        ):
            page.evaluate("window.dispatchEvent(new Event('online'))")
        page.wait_for_function("() => state.authRestoreState === 'anonymous'")
        expect(page.locator("#account-button-label")).to_have_text("登入")
        assert workspace_puts == []
        for key in (
            "exchange-guide-auth-token",
            "exchange-guide-workspace-sync-v1",
            "exchange-guide-favorites",
            "exchange-guide-eligibility-profile",
            "exchange-guide-anonymous-identity",
            "exchange-guide-application-profile-memory-v1",
            "exchange-guide-application-profile-memory-enabled",
        ):
            assert page.evaluate(
                "storageKey => window.localStorage.getItem(storageKey)", key
            ) is None, key
        for key in (
            "exchange-guide-application-profile-session",
            "exchange-guide-application-answers-session",
        ):
            assert page.evaluate(
                "storageKey => window.sessionStorage.getItem(storageKey)", key
            ) is None, key
    finally:
        page.unroute("**/auth/session", abort_session_restore)


def test_late_workspace_success_keeps_newer_pending_until_it_is_synced(
    page: Page,
    browser: Browser,
    live_server: LiveServer,
) -> None:
    email = _email("workspace-race")
    session = live_server.register(email, "E2E 同步競態學生")
    login_through_web(page, live_server, email)
    initial = _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("exists") is True,
    )["workspace"]
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    page.evaluate("window.location.hash = '#partners'")
    page.locator("#partner-search").fill("林肯")
    lincoln = page.locator(
        f'.favorite-toggle[data-school-name="{LINCOLN}"]'
    ).first
    expect(lincoln).to_have_attribute("aria-pressed", "false")

    page.evaluate(
        """() => {
          const originalFetch = window.fetch.bind(window);
          let releaseFirst;
          const firstGate = new Promise((resolve) => {
            releaseFirst = resolve;
          });
          window.__workspaceRace = {
            putCount: 0,
            firstServerDone: false,
            firstStatus: null,
            laterAttempts: 0,
            allowLater: false,
            secondQueuedAt: 0,
            releaseFirst,
            restore: () => { window.fetch = originalFetch; },
          };
          window.fetch = async (input, init = {}) => {
            const request = input instanceof Request ? input : null;
            const url = request ? request.url : String(input);
            const method = String(init.method || request?.method || "GET").toUpperCase();
            const pathname = new URL(url, window.location.href).pathname;
            if (pathname === "/account/workspace" && method === "PUT") {
              const sequence = ++window.__workspaceRace.putCount;
              if (sequence === 1) {
                const response = await originalFetch(input, init);
                window.__workspaceRace.firstStatus = response.status;
                window.__workspaceRace.firstServerDone = true;
                await firstGate;
                return response;
              }
              window.__workspaceRace.laterAttempts += 1;
              if (!window.__workspaceRace.allowLater) {
                throw new TypeError("E2E held newer workspace sync");
              }
            }
            return originalFetch(input, init);
          };
        }"""
    )

    second_context = None
    try:
        lincoln.click()
        page.wait_for_function(
            "() => window.__workspaceRace.firstServerDone === true"
        )
        assert page.evaluate("window.__workspaceRace.firstStatus") == 200

        page.locator("#partner-search").fill("明治")
        meiji = page.locator(
            f'.favorite-toggle[data-school-name="{MEIJI}"]'
        ).first
        expect(meiji).to_have_attribute("aria-pressed", "false")
        meiji.click()
        expect(meiji).to_have_attribute("aria-pressed", "true")
        page.evaluate("window.__workspaceRace.secondQueuedAt = performance.now()")
        page.wait_for_function(
            """schools => {
              const metadata = JSON.parse(
                window.localStorage.getItem("exchange-guide-workspace-sync-v1") || "{}"
              );
              const hasLatest = Object.values(metadata.pending || {}).some(
                (workspace) => schools.every(
                  (school) => (workspace.favorite_schools || []).includes(school)
                )
              );
              return hasLatest
                && performance.now() - window.__workspaceRace.secondQueuedAt > 500;
            }""",
            arg=[LINCOLN, MEIJI],
        )
        assert page.evaluate("window.__workspaceRace.putCount") == 1

        page.evaluate("window.__workspaceRace.releaseFirst()")
        page.wait_for_function("() => window.__workspaceRace.laterAttempts > 0")
        expect(page.locator("#account-workspace-sync-label")).to_have_text(
            "同步失敗", timeout=10_000
        )
        expect(page.locator("#account-workspace-sync-retry")).to_be_visible()
        page.context.set_offline(True)
        page.wait_for_function("() => navigator.onLine === false")
        pending = page.evaluate(
            """() => JSON.parse(
              window.localStorage.getItem("exchange-guide-workspace-sync-v1") || "{}"
            )"""
        )
        pending_workspace = next(iter(pending["pending"].values()))
        assert LINCOLN in pending_workspace["favorite_schools"]
        assert MEIJI in pending_workspace["favorite_schools"]
        assert pending_workspace["revision"] > initial["revision"]
        expect(meiji).to_have_attribute("aria-pressed", "true")
        first_remote = _workspace(live_server, session)["workspace"]
        assert LINCOLN in first_remote["favorite_schools"]
        assert MEIJI not in first_remote["favorite_schools"]

        page.evaluate("window.__workspaceRace.allowLater = true")
        with page.expect_response(
            lambda response: response.url
            == f"{live_server.base_url}/account/workspace"
            and response.request.method == "PUT"
            and response.status == 200,
            timeout=15_000,
        ):
            page.context.set_offline(False)

        final = _wait_for_workspace(
            live_server,
            session,
            lambda item: all(
                school in item.get("workspace", {}).get("favorite_schools", [])
                for school in (LINCOLN, MEIJI)
            ),
        )["workspace"]
        assert final["revision"] > first_remote["revision"]
        page.wait_for_function(
            """() => {
              const metadata = JSON.parse(
                window.localStorage.getItem("exchange-guide-workspace-sync-v1") || "{}"
              );
              return Object.keys(metadata.pending || {}).length === 0;
            }"""
        )
        expect(page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步"
        )

        page.evaluate("window.__workspaceRace.restore()")
        second_context = browser.new_context(viewport={"width": 390, "height": 844})
        second_page = second_context.new_page()
        login_through_web(second_page, live_server, email)
        expect(second_page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )
        second_page.evaluate("window.location.hash = '#partners'")
        for query, school in (("林肯", LINCOLN), ("明治", MEIJI)):
            second_page.locator("#partner-search").fill(query)
            expect(
                second_page.locator(
                    f'.favorite-toggle[data-school-name="{school}"]'
                ).first
            ).to_have_attribute("aria-pressed", "true")
    finally:
        page.context.set_offline(False)
        page.evaluate(
            """() => {
              if (!window.__workspaceRace) return;
              window.__workspaceRace.allowLater = true;
              window.__workspaceRace.releaseFirst();
              window.__workspaceRace.restore();
            }"""
        )
        if second_context is not None:
            second_context.close()


def test_workspace_conflict_preserves_remote_addition_and_local_removal(
    page: Page,
    browser: Browser,
    live_server: LiveServer,
) -> None:
    email = _email("workspace-three-way")
    session = live_server.register(email, "E2E 三方合併學生")
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    page.evaluate("window.location.hash = '#partners'")
    page.locator("#partner-search").fill("林肯")
    lincoln = page.locator(
        f'#partner-table .favorite-toggle[data-school-name="{LINCOLN}"]:visible'
    ).first
    expect(lincoln).to_have_attribute("aria-pressed", "false")
    lincoln.click()
    _wait_for_workspace(
        live_server,
        session,
        lambda item: LINCOLN
        in item.get("workspace", {}).get("favorite_schools", []),
    )
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )

    second_context = browser.new_context(viewport={"width": 1280, "height": 900})
    second_page = second_context.new_page()
    try:
        login_through_web(second_page, live_server, email)
        expect(second_page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )
        second_page.evaluate("window.location.hash = '#partners'")
        second_page.locator("#partner-search").fill("明治")
        meiji_on_second = second_page.locator(
            f'#partner-table .favorite-toggle[data-school-name="{MEIJI}"]:visible'
        ).first
        expect(meiji_on_second).to_have_attribute("aria-pressed", "false")
        meiji_on_second.click()
        remote_with_both = _wait_for_workspace(
            live_server,
            session,
            lambda item: all(
                school in item.get("workspace", {}).get("favorite_schools", [])
                for school in (LINCOLN, MEIJI)
            ),
        )["workspace"]
        expect(second_page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )

        page.locator("#partner-search").fill("林肯")
        expect(lincoln).to_have_attribute("aria-pressed", "true")
        with page.expect_response(
            lambda response: response.url
            == f"{live_server.base_url}/account/workspace"
            and response.request.method == "PUT"
            and response.status == 409,
            timeout=15_000,
        ):
            lincoln.click()
        expect(lincoln).to_have_attribute("aria-pressed", "false")
        expect(page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )
        merged = _wait_for_workspace(
            live_server,
            session,
            lambda item: LINCOLN
            not in item.get("workspace", {}).get("favorite_schools", [])
            and MEIJI in item.get("workspace", {}).get("favorite_schools", []),
        )["workspace"]
        assert merged["revision"] > remote_with_both["revision"]

        page.locator("#partner-search").fill("明治")
        meiji_on_first = page.locator(
            f'#partner-table .favorite-toggle[data-school-name="{MEIJI}"]:visible'
        ).first
        expect(meiji_on_first).to_have_attribute("aria-pressed", "true")
        page.locator("#partner-search").fill("威斯康辛")
        uwm = page.locator(
            f'#partner-table .favorite-toggle[data-school-name="{UWM}"]:visible'
        ).first
        expect(uwm).to_have_attribute("aria-pressed", "false")
        uwm.click()
        final = _wait_for_workspace(
            live_server,
            session,
            lambda item: set(
                item.get("workspace", {}).get("favorite_schools", [])
            )
            == {MEIJI, UWM},
        )["workspace"]
        assert set(final["favorite_schools"]) == {MEIJI, UWM}
        expect(page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )

        second_page.reload()
        expect(second_page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )
        second_page.evaluate("window.location.hash = '#partners'")
        for query, school, expected in (
            ("林肯", LINCOLN, "false"),
            ("明治", MEIJI, "true"),
            ("威斯康辛", UWM, "true"),
        ):
            second_page.locator("#partner-search").fill(query)
            expect(
                second_page.locator(
                    f'#partner-table .favorite-toggle[data-school-name="{school}"]:visible'
                ).first
            ).to_have_attribute("aria-pressed", expected)
        assert set(_workspace(live_server, session)["workspace"]["favorite_schools"]) == {
            MEIJI,
            UWM,
        }
    finally:
        second_context.close()


def test_workspace_conflict_retry_keeps_remote_fields_during_new_ui_change(
    page: Page,
    browser: Browser,
    live_server: LiveServer,
) -> None:
    email = _email("workspace-conflict-ui-race")
    session = live_server.register(email, "E2E 衝突期間操作學生")
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )

    second_context = browser.new_context(viewport={"width": 1280, "height": 900})
    second_page = second_context.new_page()
    try:
        login_through_web(second_page, live_server, email)
        expect(second_page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )
        second_page.evaluate("window.location.hash = '#partners'")
        second_page.locator("#partner-search").fill("明治")
        remote_favorite = second_page.locator(
            f'#partner-table .favorite-toggle[data-school-name="{MEIJI}"]'
        ).first
        remote_favorite.click()
        _wait_for_workspace(
            live_server,
            session,
            lambda item: MEIJI
            in item.get("workspace", {}).get("favorite_schools", []),
        )

        page.evaluate("window.location.hash = '#partners'")
        page.evaluate(
            """() => {
              const originalFetch = window.fetch.bind(window);
              let releaseRetry;
              const retryGate = new Promise((resolve) => { releaseRetry = resolve; });
              window.__workspaceConflictUiRace = {
                putCount: 0,
                firstStatus: 0,
                retryServerDone: false,
                releaseRetry,
                restore: () => { window.fetch = originalFetch; },
              };
              window.fetch = async (input, init = {}) => {
                const request = input instanceof Request ? input : null;
                const url = new URL(request ? request.url : String(input), window.location.href);
                const method = String(init.method || request?.method || 'GET').toUpperCase();
                if (url.pathname === '/account/workspace' && method === 'PUT') {
                  const sequence = ++window.__workspaceConflictUiRace.putCount;
                  const response = await originalFetch(input, init);
                  if (sequence === 1) {
                    window.__workspaceConflictUiRace.firstStatus = response.status;
                    return response;
                  }
                  if (sequence === 2) {
                    window.__workspaceConflictUiRace.retryServerDone = true;
                    await retryGate;
                    return response;
                  }
                  return response;
                }
                return originalFetch(input, init);
              };
            }"""
        )
        page.locator("#partner-search").fill("林肯")
        local_favorite = page.locator(
            f'#partner-table .favorite-toggle[data-school-name="{LINCOLN}"]'
        ).first
        local_favorite.click()
        page.wait_for_function(
            """() => window.__workspaceConflictUiRace.firstStatus === 409
              && window.__workspaceConflictUiRace.retryServerDone === true"""
        )

        page.locator("#partner-search").fill("明治")
        expect(
            page.locator(f'#partner-table .favorite-toggle[data-school-name="{MEIJI}"]').first
        ).to_have_attribute("aria-pressed", "true")
        page.locator("#partner-search").fill("威斯康辛")
        newer_favorite = page.locator(
            f'#partner-table .favorite-toggle[data-school-name="{UWM}"]'
        ).first
        expect(newer_favorite).to_have_attribute("aria-pressed", "false")
        newer_favorite.click()
        page.wait_for_function(
            """schools => {
              const metadata = JSON.parse(
                window.localStorage.getItem('exchange-guide-workspace-sync-v1') || '{}'
              );
              return Object.values(metadata.pending || {}).some((workspace) =>
                schools.every((school) =>
                  (workspace.favorite_schools || []).includes(school)
                )
              );
            }""",
            arg=[MEIJI, LINCOLN, UWM],
        )
        page.evaluate("window.__workspaceConflictUiRace.releaseRetry()")
        final = _wait_for_workspace(
            live_server,
            session,
            lambda item: set(
                item.get("workspace", {}).get("favorite_schools", [])
            )
            == {MEIJI, LINCOLN, UWM},
            timeout=15,
        )["workspace"]
        assert set(final["favorite_schools"]) == {MEIJI, LINCOLN, UWM}
        expect(page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )
    finally:
        page.evaluate(
            """() => {
              if (!window.__workspaceConflictUiRace) return;
              window.__workspaceConflictUiRace.releaseRetry();
              window.__workspaceConflictUiRace.restore();
            }"""
        )
        second_context.close()


def test_switching_cookie_account_cannot_import_previous_accounts_private_state(
    page: Page,
    live_server: LiveServer,
) -> None:
    email_a = _email("workspace-owner-a")
    session_a = live_server.register(email_a, "E2E 帳號 A")
    live_server.verify_student(session_a["profile"]["id"])
    login_through_web(page, live_server, email_a)
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    page.evaluate("window.location.hash = '#partners'")
    page.locator("#partner-search").fill("林肯")
    favorite = page.locator(
        f'.favorite-toggle[data-school-name="{LINCOLN}"]'
    ).first
    favorite.click()
    _wait_for_workspace(
        live_server,
        session_a,
        lambda item: LINCOLN
        in item.get("workspace", {}).get("favorite_schools", []),
    )
    page.evaluate(
        """() => {
          window.localStorage.setItem(
            'exchange-guide-eligibility-profile',
            JSON.stringify({ department: 'A 帳號私人科系' })
          );
          window.localStorage.setItem(
            'exchange-guide-application-profile-memory-v1',
            JSON.stringify({ student_name_zh: 'A 帳號私人姓名' })
          );
          window.localStorage.setItem(
            'exchange-guide-application-profile-memory-enabled',
            'true'
          );
          window.sessionStorage.setItem(
            'exchange-guide-application-profile-session',
            JSON.stringify({ student_id: 'A-PRIVATE-ID' })
          );
        }"""
    )

    email_b = _email("workspace-owner-b")
    session_b = live_server.register(email_b, "E2E 帳號 B")
    live_server.verify_student(session_b["profile"]["id"])
    page.context.add_cookies(
        [
            {
                "name": "exchange_guide_session",
                "value": session_b["access_token"],
                "url": live_server.base_url,
            }
        ]
    )
    page.reload()
    expect(page.locator("#account-button-label")).to_have_text(
        "E2E 帳號 B", timeout=15_000
    )
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    workspace_b = _wait_for_workspace(
        live_server,
        session_b,
        lambda item: item.get("exists") is True,
    )["workspace"]
    assert LINCOLN not in workspace_b["favorite_schools"]
    assert LINCOLN in _workspace(live_server, session_a)["workspace"][
        "favorite_schools"
    ]

    metadata = page.evaluate(
        """() => JSON.parse(
          window.localStorage.getItem('exchange-guide-workspace-sync-v1') || '{}'
        )"""
    )
    assert metadata["account_id"] == session_b["profile"]["id"]
    assert page.evaluate(
        "JSON.parse(window.localStorage.getItem('exchange-guide-favorites') || '[]')"
    ) == []
    for key in (
        "exchange-guide-eligibility-profile",
        "exchange-guide-application-profile-memory-v1",
        "exchange-guide-application-profile-memory-enabled",
    ):
        assert page.evaluate(
            "key => window.localStorage.getItem(key)", key
        ) is None, key
    assert page.evaluate(
        """() => JSON.parse(
          window.sessionStorage.getItem('exchange-guide-application-profile-session') || '{}'
        )"""
    ) == {}
    page.evaluate("window.location.hash = '#partners'")
    page.locator("#partner-search").fill("林肯")
    expect(
        page.locator(f'.favorite-toggle[data-school-name="{LINCOLN}"]').first
    ).to_have_attribute("aria-pressed", "false")


def test_reload_drains_pending_workspace_for_inactive_home_school(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("workspace-multi-school")
    session = live_server.register(email, "E2E 多校續傳學生")
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    page.evaluate(
        """school => {
          const storageKey = 'exchange-guide-workspace-sync-v1';
          const metadata = JSON.parse(window.localStorage.getItem(storageKey) || '{}');
          const workspace = {
            home_school: school,
            revision: 0,
            favorite_schools: [%s],
            application_schools: [],
            application_progress: {},
            document_readiness: {},
            application_context: {
              school_name: school,
              target_school: '',
              target_country: '',
              program_type: 'exchange',
              college: '',
              department: '',
              degree_level: '',
              academic_year: '',
              application_round: '',
              semester: '',
              flags: [],
            },
            application_selections: {},
            submission_progress: {},
            budget_plans: {},
            deadline_events: [],
          };
          metadata.revisions ||= {};
          metadata.bases ||= {};
          metadata.pending ||= {};
          metadata.revisions[school] = 0;
          metadata.bases[school] = { ...workspace, favorite_schools: [] };
          metadata.pending[school] = workspace;
          window.localStorage.setItem(storageKey, JSON.stringify(metadata));
        }"""
        % json.dumps(MEIJI),
        "國立臺北大學",
    )
    page.reload()
    expect(page.locator("#account-button-label")).to_have_text(
        "E2E 多校續傳學生", timeout=15_000
    )
    ntpu_workspace = _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("exists") is True
        and MEIJI in item.get("workspace", {}).get("favorite_schools", []),
        timeout=15,
        home_school="國立臺北大學",
    )["workspace"]
    assert ntpu_workspace["home_school"] == "國立臺北大學"
    page.wait_for_function(
        """() => {
          const metadata = JSON.parse(
            window.localStorage.getItem('exchange-guide-workspace-sync-v1') || '{}'
          );
          return Object.keys(metadata.pending || {}).length === 0;
        }"""
    )
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )


def test_success_in_one_school_does_not_hide_another_schools_sync_error(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("workspace-keyed-error")
    session = live_server.register(email, "E2E 分校錯誤學生")
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    page.evaluate(
        """([lincoln, meiji]) => {
          const originalFetch = window.fetch.bind(window);
          window.__workspaceKeyedErrorRestore = () => { window.fetch = originalFetch; };
          window.fetch = async (input, init = {}) => {
            const request = input instanceof Request ? input : null;
            const url = new URL(request ? request.url : String(input), window.location.href);
            const method = String(init.method || request?.method || 'GET').toUpperCase();
            if (url.pathname === '/account/workspace' && method === 'PUT') {
              const body = JSON.parse(String(init.body || '{}'));
              if (body.home_school === '長庚大學') {
                return new Response(
                  JSON.stringify({ detail: 'E2E 不可重試的分校同步錯誤' }),
                  { status: 422, headers: { 'Content-Type': 'application/json' } }
                );
              }
            }
            return originalFetch(input, init);
          };
          const cgu = window.emptyAccountWorkspace('長庚大學');
          cgu.favorite_schools = [lincoln];
          const ntpu = window.emptyAccountWorkspace('國立臺北大學');
          ntpu.favorite_schools = [meiji];
          Promise.allSettled([
            window.saveAccountWorkspace({ homeSchool: '長庚大學', payload: cgu }),
            window.saveAccountWorkspace({ homeSchool: '國立臺北大學', payload: ntpu }),
          ]).then(() => { window.__workspaceKeyedErrorSettled = true; });
        }""",
        [LINCOLN, MEIJI],
    )
    try:
        page.wait_for_function("() => window.__workspaceKeyedErrorSettled === true")
        expect(page.locator("#account-workspace-sync-label")).to_have_text(
            "同步失敗", timeout=15_000
        )
        expect(page.locator("#account-workspace-sync-retry")).to_be_visible()
        metadata = page.evaluate(
            """() => JSON.parse(
              window.localStorage.getItem('exchange-guide-workspace-sync-v1') || '{}'
            )"""
        )
        assert set(metadata["pending"]) == {"長庚大學"}
        assert LINCOLN in metadata["pending"]["長庚大學"]["favorite_schools"]
        ntpu = _workspace(live_server, session, "國立臺北大學")
        assert MEIJI in ntpu["workspace"]["favorite_schools"]
    finally:
        page.evaluate("window.__workspaceKeyedErrorRestore?.()")


def test_repeated_workspace_conflicts_advance_merge_base_before_retry(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("workspace-repeated-conflict")
    live_server.register(email, "E2E 連續衝突學生")
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    page.evaluate(
        """([lincoln, meiji]) => {
          const school = '長庚大學';
          const key = window.accountWorkspaceKey(school);
          const base = window.emptyAccountWorkspace(school);
          base.revision = 1;
          base.favorite_schools = [lincoln];
          const remoteOne = window.emptyAccountWorkspace(school);
          remoteOne.revision = 2;
          remoteOne.favorite_schools = [lincoln, meiji];
          const remoteTwo = window.emptyAccountWorkspace(school);
          remoteTwo.revision = 3;
          remoteTwo.favorite_schools = [];
          const local = window.emptyAccountWorkspace(school);
          local.revision = 1;
          local.favorite_schools = [];
          state.accountWorkspaceBases[key] = base;
          state.accountWorkspaceRevisions[key] = 1;
          window.persistAccountWorkspaceSyncMetadata();

          const originalFetch = window.fetch.bind(window);
          let conflictSequence = 0;
          window.__workspaceRepeatedConflictRestore = () => {
            window.fetch = originalFetch;
            window.clearTimeout(state.accountWorkspaceRetryTimer);
            state.accountWorkspaceRetryTimer = null;
          };
          window.fetch = async (input, init = {}) => {
            const request = input instanceof Request ? input : null;
            const url = new URL(request ? request.url : String(input), window.location.href);
            const method = String(init.method || request?.method || 'GET').toUpperCase();
            if (url.pathname === '/account/workspace' && method === 'PUT') {
              conflictSequence += 1;
              const current = conflictSequence === 1 ? remoteOne : remoteTwo;
              return new Response(
                JSON.stringify({
                  detail: {
                    code: 'workspace_revision_conflict',
                    message: 'E2E 連續版本衝突',
                    current_workspace: current,
                  },
                }),
                { status: 409, headers: { 'Content-Type': 'application/json' } }
              );
            }
            return originalFetch(input, init);
          };
          window.saveAccountWorkspace({ homeSchool: school, payload: local }).finally(() => {
            window.__workspaceRepeatedConflictSettled = true;
          });
        }""",
        [LINCOLN, MEIJI],
    )
    try:
        page.wait_for_function("() => window.__workspaceRepeatedConflictSettled === true")
        metadata = page.evaluate(
            """() => JSON.parse(
              window.localStorage.getItem('exchange-guide-workspace-sync-v1') || '{}'
            )"""
        )
        pending = metadata["pending"]["長庚大學"]
        base = metadata["bases"]["長庚大學"]
        assert pending["revision"] == 3
        assert pending["favorite_schools"] == []
        assert base["revision"] == 3
        assert base["favorite_schools"] == []
        expect(page.locator("#account-workspace-sync-label")).to_have_text(
            "同步失敗", timeout=15_000
        )
    finally:
        page.evaluate("window.__workspaceRepeatedConflictRestore?.()")


def test_workspace_load_advances_base_before_put_conflict(
    page: Page,
    browser: Browser,
    live_server: LiveServer,
) -> None:
    email = _email("workspace-load-base")
    session = live_server.register(email, "E2E 載入基準學生")
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    page.evaluate("window.location.hash = '#partners'")
    page.locator("#partner-search").fill("林肯")
    page.locator(f'#partner-table .favorite-toggle[data-school-name="{LINCOLN}"]').first.click()
    _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("workspace", {}).get("favorite_schools", [])
        == [LINCOLN],
    )

    second_context = browser.new_context(viewport={"width": 1280, "height": 900})
    second_page = second_context.new_page()
    try:
        login_through_web(second_page, live_server, email)
        expect(second_page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )
        second_page.evaluate("window.location.hash = '#partners'")
        second_page.locator("#partner-search").fill("明治")
        meiji_on_second = second_page.locator(
            f'#partner-table .favorite-toggle[data-school-name="{MEIJI}"]'
        ).first
        meiji_on_second.click()
        _wait_for_workspace(
            live_server,
            session,
            lambda item: set(
                item.get("workspace", {}).get("favorite_schools", [])
            )
            == {LINCOLN, MEIJI},
        )

        page.evaluate(
            """() => {
              const storageKey = 'exchange-guide-workspace-sync-v1';
              const key = '長庚大學';
              const metadata = JSON.parse(window.localStorage.getItem(storageKey) || '{}');
              const base = metadata.bases[key];
              if (!base || !(base.favorite_schools || []).includes(%s)) {
                throw new Error('missing expected local merge base');
              }
              metadata.pending[key] = { ...base, favorite_schools: [] };
              window.localStorage.setItem(storageKey, JSON.stringify(metadata));
              window.localStorage.setItem('exchange-guide-favorites', '[]');
            }"""
            % json.dumps(LINCOLN)
        )
        page.add_init_script(
            """(() => {
              const originalFetch = window.fetch.bind(window);
              let releaseWorkspaceGet;
              const workspaceGetGate = new Promise((resolve) => {
                releaseWorkspaceGet = resolve;
              });
              window.__workspaceLoadBaseRace = {
                captured: false,
                release: releaseWorkspaceGet,
              };
              window.fetch = async (input, init = {}) => {
                const request = input instanceof Request ? input : null;
                const url = new URL(request ? request.url : String(input), window.location.href);
                const method = String(init.method || request?.method || 'GET').toUpperCase();
                if (
                  !window.__workspaceLoadBaseRace.captured
                  && url.pathname === '/account/workspace'
                  && method === 'GET'
                ) {
                  const response = await originalFetch(input, init);
                  window.__workspaceLoadBaseRace.captured = true;
                  await workspaceGetGate;
                  return response;
                }
                return originalFetch(input, init);
              };
            })();"""
        )
        page.reload()
        page.wait_for_function("() => window.__workspaceLoadBaseRace.captured === true")

        second_page.locator("#partner-search").fill("明治")
        expect(meiji_on_second).to_have_attribute("aria-pressed", "true")
        meiji_on_second.click()
        _wait_for_workspace(
            live_server,
            session,
            lambda item: item.get("workspace", {}).get("favorite_schools", [])
            == [LINCOLN],
        )
        page.evaluate("window.__workspaceLoadBaseRace.release()")

        final = _wait_for_workspace(
            live_server,
            session,
            lambda item: item.get("workspace", {}).get("favorite_schools", [])
            == [],
            timeout=15,
        )["workspace"]
        assert final["favorite_schools"] == []
        expect(page.locator("#account-workspace-sync-label")).to_have_text(
            "已同步", timeout=15_000
        )
        page.evaluate("window.location.hash = '#partners'")
        for query, school in (("林肯", LINCOLN), ("明治", MEIJI)):
            page.locator("#partner-search").fill(query)
            expect(
                page.locator(
                    f'#partner-table .favorite-toggle[data-school-name="{school}"]'
                ).first
            ).to_have_attribute("aria-pressed", "false")
    finally:
        page.evaluate("window.__workspaceLoadBaseRace?.release?.()")
        second_context.close()


def test_workspace_load_fallback_cannot_reapply_after_logout(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("workspace-load-logout")
    session = live_server.register(email, "E2E 載入登出邊界學生")
    login_through_web(page, live_server, email)
    _wait_for_workspace(
        live_server,
        session,
        lambda item: item.get("exists") is True,
    )
    expect(page.locator("#account-workspace-sync-label")).to_have_text(
        "已同步", timeout=15_000
    )
    page.evaluate("window.location.hash = '#partners'")
    page.locator("#partner-search").fill("林肯")
    favorite = page.locator(
        f'.favorite-toggle[data-school-name="{LINCOLN}"]'
    ).first
    expect(favorite).to_have_attribute("aria-pressed", "false")
    page.evaluate(
        """() => {
          const originalFetch = window.fetch.bind(window);
          let releasePut;
          const putGate = new Promise((resolve) => { releasePut = resolve; });
          window.__workspaceLoadLogout = {
            getCompleted: false,
            putCaptured: false,
            loadSettled: false,
            releasePut,
            restore: () => { window.fetch = originalFetch; },
          };
          window.fetch = async (input, init = {}) => {
            const request = input instanceof Request ? input : null;
            const url = request ? request.url : String(input);
            const method = String(init.method || request?.method || "GET").toUpperCase();
            const parsed = new URL(url, window.location.href);
            if (parsed.pathname === "/account/workspace" && method === "GET") {
              const response = await originalFetch(input, init);
              window.__workspaceLoadLogout.getCompleted = true;
              return response;
            }
            if (
              parsed.pathname === "/account/workspace"
              && method === "PUT"
              && !window.__workspaceLoadLogout.putCaptured
            ) {
              const response = await originalFetch(input, init);
              window.__workspaceLoadLogout.putCaptured = true;
              await putGate;
              return response;
            }
            return originalFetch(input, init);
          };
        }"""
    )

    try:
        favorite.click()
        page.evaluate(
            """() => {
              window.loadAccountWorkspace().finally(() => {
                window.__workspaceLoadLogout.loadSettled = true;
              });
            }"""
        )
        page.wait_for_function(
            """() => window.__workspaceLoadLogout.getCompleted
              && window.__workspaceLoadLogout.putCaptured"""
        )
        page.locator("#account-button").click()
        expect(page.locator("#profile-dialog")).to_be_visible()
        page.locator("#logout-button").click()
        expect(page.locator("#profile-dialog")).to_be_hidden(timeout=10_000)
        expect(page.locator("#account-button-label")).to_have_text("登入")
        assert page.evaluate(
            "window.localStorage.getItem('exchange-guide-workspace-sync-v1')"
        ) is None

        page.evaluate("window.__workspaceLoadLogout.releasePut()")
        page.wait_for_function("() => window.__workspaceLoadLogout.loadSettled === true")
        expect(page.locator("#account-button-label")).to_have_text("登入")
        expect(page.locator("#account-workspace-sync-control")).to_be_hidden()
        for key in (
            "exchange-guide-workspace-sync-v1",
            "exchange-guide-favorites",
            "exchange-guide-applications",
            "exchange-guide-application-progress",
            "exchange-guide-document-readiness",
        ):
            assert page.evaluate(
                "storageKey => window.localStorage.getItem(storageKey)", key
            ) is None, key
    finally:
        page.evaluate(
            """() => {
              if (!window.__workspaceLoadLogout) return;
              window.__workspaceLoadLogout.releasePut();
              window.__workspaceLoadLogout.restore();
            }"""
        )


def test_expired_session_and_logout_clear_private_browser_state(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("session-boundary")
    live_server.register(email, "E2E Session 邊界學生")
    login_through_web(page, live_server, email)

    page.wait_for_function(
        "() => window.localStorage.getItem('exchange-guide-workspace-sync-v1') !== null"
    )
    page.evaluate(
        """() => {
          window.localStorage.setItem(
            'exchange-guide-eligibility-profile',
            JSON.stringify({ department: '不應留在共用裝置' })
          );
          window.localStorage.setItem(
            'exchange-guide-application-profile-memory-v1',
            JSON.stringify({ student_name_zh: '不應留在共用裝置' })
          );
          window.localStorage.setItem(
            'exchange-guide-application-profile-memory-enabled',
            'true'
          );
          window.sessionStorage.setItem(
            'exchange-guide-application-profile-session',
            JSON.stringify({ student_id: 'private-session-value' })
          );
          window.sessionStorage.setItem(
            'exchange-guide-application-answers-session',
            JSON.stringify({ private: 'answer' })
          );
        }"""
    )
    assert page.evaluate(
        "window.localStorage.getItem('exchange-guide-auth-token')"
    ) is None
    browser_session_cookie = next(
        cookie
        for cookie in page.context.cookies()
        if cookie["name"] == "exchange_guide_session"
    )
    revoked = requests.post(
        f"{live_server.base_url}/auth/logout",
        cookies={
            browser_session_cookie["name"]: browser_session_cookie["value"]
        },
        timeout=10,
    )
    assert revoked.status_code == 204

    # Hold the actual public reload until the expiry notice and private purge
    # are visible, then finish it to detect a late dashboard erasing the notice.
    page.evaluate("""() => {
      const originalFetch = window.fetch.bind(window);
      let release;
      const gate = new Promise(resolve => { release = resolve; });
      window.__expiredCatalog = { captured: false, settled: false, release };
      window.fetch = async (...args) => {
        const response = await originalFetch(...args);
        if (String(args[0]).includes('/student-dashboard?')) {
          window.__expiredCatalog.captured = true;
          await gate;
          window.__expiredCatalog.settled = true;
        }
        return response;
      };
    }""")
    page.locator("#notification-button").click()
    expect(page.locator("#auth-dialog")).to_be_visible(timeout=10_000)
    expect(page.locator('[data-auth-mode="login"]')).to_have_attribute(
        "aria-selected", "true"
    )
    expect(page.locator("#account-button-label")).to_have_text("登入")
    expect(page.locator("#page-status")).to_contain_text("登入已過期")
    for key in (
        "exchange-guide-auth-token",
        "exchange-guide-workspace-sync-v1",
        "exchange-guide-favorites",
        "exchange-guide-applications",
        "exchange-guide-application-progress",
        "exchange-guide-document-readiness",
        "exchange-guide-eligibility-profile",
        "exchange-guide-calendar-events",
        "exchange-guide-budget-plans",
        "exchange-guide-application-context",
        "exchange-guide-application-selections",
        "exchange-guide-submission-progress",
        "exchange-guide-application-profile-memory-v1",
        "exchange-guide-application-profile-memory-enabled",
    ):
        assert page.evaluate(
            "key => window.localStorage.getItem(key)", key
        ) is None, key
    for key in (
        "exchange-guide-application-profile-session",
        "exchange-guide-application-answers-session",
    ):
        assert page.evaluate(
            "key => window.sessionStorage.getItem(key)", key
        ) is None, key

    page.wait_for_function("() => window.__expiredCatalog.captured")
    page.evaluate("window.__expiredCatalog.release()")
    page.wait_for_function("() => window.__expiredCatalog.settled && !state.partnerDataLoading")
    expect(page.locator("#page-status")).to_contain_text("登入已過期")

    page.locator("#login-form input[name=email]").fill(email)
    page.locator("#login-form input[name=password]").fill("CodexE2E!2026")
    with page.expect_response(
        lambda response: response.url == f"{live_server.base_url}/auth/login"
        and response.request.method == "POST",
        timeout=60_000,
    ) as relogin_response_info:
        page.locator("#login-form button[type=submit]").click()
    assert relogin_response_info.value.ok
    page.locator("#auth-dialog").wait_for(state="hidden", timeout=10_000)
    page.wait_for_function(
        "() => window.localStorage.getItem('exchange-guide-workspace-sync-v1') !== null"
    )
    expect(page.locator("#page-status")).not_to_contain_text("登入已過期")
    page.evaluate(
        "window.localStorage.setItem('exchange-guide-eligibility-profile', "
        "JSON.stringify({ department: 'logout-private-value' }))"
    )
    page.evaluate(
        """() => {
          const originalFetch = window.fetch.bind(window);
          let releaseWorkspace;
          const workspaceGate = new Promise((resolve) => {
            releaseWorkspace = resolve;
          });
          window.__staleWorkspaceCaptured = false;
          window.__staleWorkspaceSettled = false;
          window.__releaseStaleWorkspace = () => releaseWorkspace();
          window.fetch = async (...args) => {
            const requestUrl = String(args[0]);
            const requestMethod = String(args[1]?.method || 'GET').toUpperCase();
            if (
              !window.__staleWorkspaceCaptured
              && requestMethod === 'GET'
              && requestUrl.includes('/account/workspace?')
            ) {
              const response = await originalFetch(...args);
              window.__staleWorkspaceCaptured = true;
              await workspaceGate;
              return response;
            }
            return originalFetch(...args);
          };
          window.loadAccountWorkspace().finally(() => {
            window.__staleWorkspaceSettled = true;
          });
        }"""
    )
    page.wait_for_function("() => window.__staleWorkspaceCaptured === true")
    page.locator("#account-button").click()
    expect(page.locator("#profile-dialog")).to_be_visible()
    page.locator("#logout-button").click()
    expect(page.locator("#profile-dialog")).to_be_hidden(timeout=10_000)
    expect(page.locator("#account-button-label")).to_have_text("登入")
    assert page.evaluate(
        "window.localStorage.getItem('exchange-guide-workspace-sync-v1')"
    ) is None
    assert page.evaluate(
        "window.localStorage.getItem('exchange-guide-eligibility-profile')"
    ) is None
    page.evaluate("window.__releaseStaleWorkspace()")
    page.wait_for_function("() => window.__staleWorkspaceSettled === true")
    expect(page.locator("#account-button-label")).to_have_text("登入")
    for key in (
        "exchange-guide-workspace-sync-v1",
        "exchange-guide-favorites",
        "exchange-guide-applications",
        "exchange-guide-application-progress",
        "exchange-guide-document-readiness",
        "exchange-guide-eligibility-profile",
    ):
        assert page.evaluate(
            "key => window.localStorage.getItem(key)", key
        ) is None, key


def test_application_form_sync_review_and_pdf_download(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("form")
    session = live_server.register(email, "E2E 表單學生")
    live_server.verify_student(session["profile"]["id"])
    login_through_web(page, live_server, email)

    page.evaluate("window.location.hash = '#application-center'")
    expect(page.locator("#application-center-title")).to_be_visible()
    first_template = page.locator(".application-template-open").first
    expect(first_template).to_be_visible()
    first_template.click()
    expect(page.locator("#application-document-form")).to_be_visible()

    _fill_required_application_fields(page)
    page.locator("#application-document-form button[type=submit]").click()
    expect(page.locator("#application-document-form-status")).to_have_text("已儲存")
    expect(page.locator("#application-draft-sync-status")).to_contain_text(
        "一般欄位已加密同步",
        timeout=15_000,
    )

    review = page.locator("[data-application-review-template]")
    expect(review).to_be_enabled(timeout=15_000)
    review.check()
    download_button = page.locator("#download-single-application-document")
    expect(download_button).to_be_enabled(timeout=15_000)
    with page.expect_download(timeout=30_000) as download_info:
        download_button.click()
    download = download_info.value
    assert download.failure() is None
    assert download.suggested_filename.endswith(".pdf")
    expect(page.locator("#application-download-dialog")).to_be_visible()
    expect(page.locator("#application-download-dialog")).to_contain_text(
        "伺服器不會永久保存"
    )

    drafts = requests.get(
        f"{live_server.base_url}/account/application-drafts",
        params={"home_school": "長庚大學"},
        headers=_auth_headers(session),
        timeout=10,
    )
    drafts.raise_for_status()
    assert drafts.json()["items"]
    serialized = str(drafts.json())
    assert "passport_number" not in serialized
    assert "data_url" not in serialized


def test_permissions_sensitive_consent_and_account_deletion_are_fail_closed(
    page: Page,
    live_server: LiveServer,
) -> None:
    email = _email("privacy")
    session = live_server.register(email, "E2E 隱私學生")
    headers = _community_headers(live_server, session)

    guest_boards = requests.get(f"{live_server.base_url}/community/boards", timeout=10)
    assert guest_boards.status_code == 200
    assert all(item["can_read"] == (item["kind"] != "university_exchange") for item in guest_boards.json())
    assert all(not item["can_post"] for item in guest_boards.json())

    public_post = requests.post(
        f"{live_server.base_url}/community/posts",
        headers=headers,
        json={
            "board_id": "public-study-abroad",
            "post_type": "question",
            "title": "E2E 公共板申請問題",
            "body": "這是一篇用來確認一般學生帳號可以在公共板發文的隔離測試文章。",
        },
        timeout=10,
    )
    assert public_post.status_code == 201

    university_payload = {
        "board_id": "university:cgu",
        "post_type": "discussion",
        "title": "E2E 長庚交換板測試",
        "body": "這是一篇用來確認已驗證 Email 會員可跨校發文的隔離測試文章。",
    }
    from exchange_info.repositories import JsonlAccountRepository
    from exchange_info.models import UserAccount, AccountSessionRecord, utc_now
    import hashlib
    repository = JsonlAccountRepository(live_server.data_dir)
    account = repository.find_account_by_id(session["profile"]["id"])
    assert account is not None and account.email_verified and not account.student_status_verified
    # Seed an actually unverified synthetic account. Normal profile writes must
    # preserve a committed email verification, so changing the owner would not
    # create the intended permission precondition.
    pending = UserAccount(display_name="E2E 未驗證 Email 會員", email_verified=False)
    pending_token = uuid4().hex
    repository.save_account(pending)
    repository.save_session(AccountSessionRecord(account_id=pending.id,
        token_hash=hashlib.sha256(pending_token.encode()).hexdigest(),
        expires_at=utc_now()+timedelta(days=1)))
    pending_headers = _community_headers(live_server, {"access_token":pending_token})
    denied_unverified = requests.post(
        f"{live_server.base_url}/community/posts",
        headers=pending_headers,
        json=university_payload,
        timeout=10,
    )
    assert denied_unverified.status_code == 403
    assert requests.get(f"{live_server.base_url}/community/posts", params={"board_id":"cgu"},
                        headers=pending_headers, timeout=10).status_code == 403

    allowed_verified = requests.post(
        f"{live_server.base_url}/community/posts",
        headers=headers,
        json=university_payload,
        timeout=10,
    )
    assert allowed_verified.status_code == 201
    university_post_id = allowed_verified.json()["id"]
    denied_other_school = requests.post(
        f"{live_server.base_url}/community/posts",
        headers=headers,
        json={
            **university_payload,
            "board_id": "university:ntpu",
            "title": "E2E 已驗證 Email 跨校發文",
        },
        timeout=10,
    )
    assert denied_other_school.status_code == 201
    live_server.verify_student(session["profile"]["id"])

    vault_data = {
        "label": "E2E 校內交換申請表",
        "category": "application_form",
        "purpose": "application_preparation",
        "retention_days": "30",
    }
    denied_vault = requests.post(
        f"{live_server.base_url}/account/vault/documents",
        headers=_auth_headers(session),
        data={**vault_data, "consent": "false"},
        files={"file": ("application.pdf", b"%PDF-1.4\nE2E\n%%EOF", "application/pdf")},
        timeout=10,
    )
    assert denied_vault.status_code == 422
    accepted_vault = requests.post(
        f"{live_server.base_url}/account/vault/documents",
        headers=_auth_headers(session),
        data={**vault_data, "consent": "true"},
        files={"file": ("application.pdf", b"%PDF-1.4\nE2E\n%%EOF", "application/pdf")},
        timeout=10,
    )
    assert accepted_vault.status_code == 201

    viewer_email = _email("privacy-reader")
    viewer_session = live_server.register(viewer_email, "E2E 已驗證 Email 讀者")
    viewer_headers = _auth_headers(viewer_session)
    assert requests.patch(f"{live_server.base_url}/auth/me", headers=viewer_headers,
                          json={"home_university":"長庚大學"}, timeout=10).status_code == 200
    deleted = requests.delete(
        f"{live_server.base_url}/auth/me",
        headers=_auth_headers(session),
        timeout=10,
    )
    assert deleted.status_code == 204
    assert requests.get(
        f"{live_server.base_url}/account/vault/documents",
        headers=_auth_headers(session),
        timeout=10,
    ).status_code == 401

    public_threads = requests.get(
        f"{live_server.base_url}/community/posts",
        params={"school": "長庚大學"},
        headers=viewer_headers,
        timeout=10,
    )
    public_threads.raise_for_status()
    retained = next(
        item["post"]
        for item in public_threads.json()
        if item["post"]["id"] == university_post_id
    )
    assert retained["display_name"] == "已刪除帳號"
    assert not retained["author_id"]

    assert requests.get(f"{live_server.base_url}/community/posts", params={"school":"長庚大學"}, timeout=10).status_code == 401
    login_through_web(page, live_server, viewer_email)
    page.evaluate("window.location.hash = '#university-posts'")
    expect(page.locator("#global-community-feed")).to_contain_text(
        "E2E 長庚交換板測試"
    )
    expect(page.locator("#global-community-feed")).to_contain_text("已刪除帳號")


@pytest.mark.skip(reason="Phase C")
def test_content_admin_explicitly_stages_one_review_batch_without_publication(
    page: Page,
    live_server: LiveServer,
    monkeypatch,
    request,
) -> None:
    reviewer_email = _email("batch-stage-reviewer")
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", reviewer_email)
    reviewer = live_server.register(reviewer_email, "批次建立審查者")
    reviewer_headers = _auth_headers(reviewer)
    store = LocalContentGovernanceStore(
        live_server.data_dir,
        include_bundled_baseline=True,
    )
    revisions_before = store.list_revisions()
    request.addfinalizer(
        lambda: save_application_workflow_revisions(
            revisions_before,
            live_server.data_dir,
        )
    )
    public_before = [
        workflow.model_dump_json()
        for workflow in store.load_published_workflows()
    ]

    _open_content_review_workbench(
        page,
        live_server,
        reviewer_email,
        reviewer,
    )
    page.locator("#review-status-filter").select_option("backlog")
    with page.expect_download() as batch_download_info:
        page.locator("#review-batch-export").click()
    batch_rows = list(
        csv.DictReader(
            StringIO(
                batch_download_info.value.path().read_bytes().decode("utf-8-sig")
            )
        )
    )
    first_batch_rows = [
        row
        for row in batch_rows
        if row["審查批次"] == batch_rows[0]["審查批次"]
    ]
    assert len(first_batch_rows) == 10
    page.goto(f"{live_server.base_url}{first_batch_rows[0]['批次工作台路徑']}")
    stage_button = page.locator("#stage-workflow-review-batch")
    expect(stage_button).to_be_visible(timeout=15_000)
    expect(stage_button).to_contain_text("10 筆")

    dismissed_messages: list[str] = []

    def dismiss_batch_stage(dialog) -> None:
        dismissed_messages.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", dismiss_batch_stage)
    stage_button.click()
    assert dismissed_messages
    assert "不會核准、發布" in dismissed_messages[0]
    pending_before_confirmation = requests.get(
        f"{live_server.base_url}/admin/application-workflow-revisions",
        params={"status": "pending_review"},
        headers=reviewer_headers,
        timeout=15,
    )
    pending_before_confirmation.raise_for_status()
    assert pending_before_confirmation.json() == []

    page.once("dialog", lambda dialog: dialog.accept())
    stage_button.click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "新建立 10 筆、沿用 0 筆",
        timeout=30_000,
    )
    expect(page.locator("#workflow-deep-link-description")).to_contain_text(
        "已建立待審 10"
    )
    first_pending = requests.get(
        f"{live_server.base_url}/admin/application-workflow-revisions",
        params={"status": "pending_review"},
        headers=reviewer_headers,
        timeout=15,
    )
    first_pending.raise_for_status()
    assert len(first_pending.json()) == 10
    assert all(row["review_approvals"] == [] for row in first_pending.json())
    first_revision_ids = {row["id"] for row in first_pending.json()}

    page.once("dialog", lambda dialog: dialog.accept())
    stage_button.click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "新建立 0 筆、沿用 10 筆",
        timeout=30_000,
    )
    repeated_pending = requests.get(
        f"{live_server.base_url}/admin/application-workflow-revisions",
        params={"status": "pending_review"},
        headers=reviewer_headers,
        timeout=15,
    )
    repeated_pending.raise_for_status()
    assert {row["id"] for row in repeated_pending.json()} == first_revision_ids
    first_batch_workflow_keys = {row["workflow_key"] for row in first_batch_rows}
    outside_batch = next(
        row for row in batch_rows
        if row["workflow_key"] not in first_batch_workflow_keys
    )
    outside_stage = requests.post(
        f"{live_server.base_url}/admin/application-workflow-review-backlog/"
        f"{requests.utils.quote(outside_batch['workflow_key'], safe='')}/stage",
        headers=reviewer_headers,
        timeout=15,
    )
    outside_stage.raise_for_status()

    page.set_viewport_size({"width": 390, "height": 844})
    batch_review_button = page.locator("#open-workflow-review-batch")
    expect(batch_review_button).to_be_visible()
    expect(batch_review_button).to_contain_text("10 筆")
    batch_review_button.click()
    expect(page.locator("#review-status-filter")).to_have_value(
        "pending_review",
        timeout=15_000,
    )
    expect(page.locator("#workflow-review-owner-filter")).to_have_value(
        "mine_unreviewed"
    )
    expect(page.locator("#review-queue")).to_have_attribute(
        "aria-busy",
        "false",
        timeout=30_000,
    )
    expect(page.locator("#workflow-review-focus-filter")).to_be_visible()
    expect(page.locator("#workflow-review-focus-description")).to_contain_text(
        first_batch_rows[0]["審查批次"]
    )
    expect(page.locator("#workflow-review-focus-description")).to_contain_text(
        "我的待辦 10 筆"
    )
    expect(page.locator("#workflow-review-focus-description")).to_contain_text(
        "可開始真人核對 0 筆、須先補資料 10 筆"
    )
    expect(page.locator("#review-count")).to_have_text("10")
    assert page.locator("[data-revision-id]").count() == 10
    next_review_button = page.locator("#open-next-workflow-review")
    expect(next_review_button).to_be_visible()
    expect(next_review_button).to_contain_text("開啟第一筆待辦（10 筆）")
    readiness_filter = page.locator("#workflow-review-readiness-filter")
    expect(readiness_filter).to_be_visible()
    readiness_filter.select_option("correction_ready")
    expect(page.locator("#review-count")).to_have_text("0")
    expect(next_review_button).to_be_disabled()
    expect(next_review_button).to_contain_text("目前沒有可開始核對項目")
    readiness_filter.select_option("correction_blocked")
    expect(page.locator("#review-count")).to_have_text("10")
    expect(next_review_button).to_be_enabled()
    expect(next_review_button).to_contain_text("開啟第一筆待補資料（10 筆）")
    readiness_filter.select_option("")
    expect(page.locator("#review-count")).to_have_text("10")
    batch_location = parse_qs(urlparse(page.url).query)
    assert batch_location["review_status"] == ["pending_review"]
    assert batch_location["review_batch"] == [first_batch_rows[0]["審查批次"]]
    assert batch_location["batch_size"] == ["10"]
    assert batch_location["review_snapshot"] == [
        first_batch_rows[0]["審查內容指紋"]
    ]
    assert "workflow_revision" not in batch_location
    assert page.evaluate("document.documentElement.scrollWidth") <= 390

    next_review_button.click()
    expect(page.locator("#review-count")).to_have_text("1")
    expect(page.locator("[data-revision-id]")).to_have_count(1)
    first_focused_revision = page.locator("[data-revision-id]").get_attribute(
        "data-revision-id"
    )
    assert first_focused_revision
    correction_summary = page.locator(
        f'[data-revision-id="{first_focused_revision}"] .review-correction-summary'
    )
    expect(correction_summary).to_contain_text("先補資料才能核准")
    expect(correction_summary).to_contain_text("來源年度缺漏或不一致")
    correction_summary.locator("[data-review-jump-corrections]").click()
    expect(
        page.locator(
            f'[data-revision-id="{first_focused_revision}"] .applicability-editor'
        )
    ).to_have_attribute("open", "")
    focused_card = page.locator(f'[data-revision-id="{first_focused_revision}"]')
    expect(focused_card.locator("[data-applicability-progress]")).to_contain_text(
        "已選擇 0 /"
    )
    expect(focused_card.locator("[data-review-applicability-save]")).to_be_disabled()
    expect(page.locator("#review-announcement")).to_contain_text(
        "系統不會替你猜值"
    )
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    expect(page.locator("#show-workflow-review-batch")).to_be_visible()
    focused_location = parse_qs(urlparse(page.url).query)
    assert focused_location["workflow_revision"] == [first_focused_revision]
    assert focused_location["review_batch"] == [first_batch_rows[0]["審查批次"]]

    next_review_button.click()
    expect(page.locator("[data-revision-id]")).to_have_count(1)
    second_focused_revision = page.locator("[data-revision-id]").get_attribute(
        "data-revision-id"
    )
    assert second_focused_revision
    assert second_focused_revision != first_focused_revision
    assert parse_qs(urlparse(page.url).query)["workflow_revision"] == [
        second_focused_revision
    ]

    page.locator("#show-workflow-review-batch").click()
    expect(page.locator("#review-count")).to_have_text("10")
    expect(page.locator("[data-revision-id]")).to_have_count(10)
    assert "workflow_revision" not in parse_qs(urlparse(page.url).query)
    next_review_button.click()
    expect(page.locator("[data-revision-id]")).to_have_count(1)
    reloaded_focus_revision = page.locator("[data-revision-id]").get_attribute(
        "data-revision-id"
    )
    assert reloaded_focus_revision

    page.reload()
    expect(page.locator("#reviewer-email")).to_have_text(
        reviewer_email,
        timeout=15_000,
    )
    expect(page.locator("#workflow-review-focus-description")).to_contain_text(
        "重新整理仍會重新驗證並維持此批次"
    )
    expect(page.locator("#review-queue")).to_have_attribute(
        "aria-busy",
        "false",
        timeout=30_000,
    )
    expect(page.locator("#review-count")).to_have_text("1")
    expect(page.locator("[data-revision-id]")).to_have_count(1)
    assert page.locator("[data-revision-id]").get_attribute(
        "data-revision-id"
    ) == reloaded_focus_revision

    reloaded_card = page.locator(
        f'[data-revision-id="{reloaded_focus_revision}"]'
    )
    reloaded_card.locator(".applicability-editor > summary").click()
    reloaded_card.locator("[data-applicability-academic-year]").fill("115")
    secure_source_rows = reloaded_card.locator(
        '[data-applicability-source-row][data-source-url^="https://"]'
    )
    assert secure_source_rows.count() > 0
    corrected_source_row = secure_source_rows.first
    corrected_source_row.locator("[data-applicability-source]").check()
    corrected_source_row.locator("[data-source-academic-year]").fill("115")
    if corrected_source_row.get_attribute("data-source-metadata-complete") == "false":
        corrected_source_row.locator("[data-source-title]").fill(
            "E2E 批次失效人工來源"
        )
        corrected_source_row.locator("[data-source-role]").select_option(
            "home_university"
        )
        corrected_source_row.locator("[data-source-authority]").select_option(
            "home_official_notice"
        )
    reloaded_card.locator("[data-applicability-note]").fill(
        "E2E 明確儲存候選修正後，舊批次必須立即失效並清除單筆定位。"
    )
    applicability_save = reloaded_card.locator(
        "[data-review-applicability-save]"
    )
    expect(applicability_save).to_be_enabled()
    applicability_save.click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "候選內容已改變審查指紋，原批次因此過期",
        timeout=30_000,
    )
    expect(page.locator("#workflow-review-focus-description")).to_contain_text(
        "指定的審查批次已過期",
        timeout=15_000,
    )
    expect(page.locator("#review-queue")).to_have_attribute(
        "aria-busy",
        "false",
        timeout=30_000,
    )
    expect(page.locator("#review-count")).to_have_text("11")
    assert "workflow_revision" not in parse_qs(urlparse(page.url).query)
    assert parse_qs(urlparse(page.url).query)["review_batch"] == [
        first_batch_rows[0]["審查批次"]
    ]
    expect(page.locator("#open-next-workflow-review")).to_be_hidden()
    expect(page.locator("#show-workflow-review-batch")).to_be_hidden()
    page.locator("#clear-workflow-review-focus").click()
    expect(page.locator("#workflow-review-focus-filter")).to_be_hidden()
    expect(page.locator("#review-count")).to_have_text("11")
    cleared_location = parse_qs(urlparse(page.url).query)
    assert "review_batch" not in cleared_location
    assert "batch_size" not in cleared_location
    assert "review_snapshot" not in cleared_location
    assert [
        workflow.model_dump_json()
        for workflow in store.load_published_workflows()
    ] == public_before


@pytest.mark.skip(reason="Phase C")
def test_content_admins_independently_attest_every_source_before_publish(
    page: Page,
    browser: Browser,
    live_server: LiveServer,
    monkeypatch,
) -> None:
    reviewer_a_email = _email("content-reviewer-a")
    reviewer_b_email = _email("content-reviewer-b")
    monkeypatch.setenv(
        "EXCHANGE_CONTENT_ADMIN_EMAILS",
        f"{reviewer_a_email},{reviewer_b_email}",
    )
    reviewer_a = live_server.register(reviewer_a_email, "內容審查者 A")
    reviewer_b = live_server.register(reviewer_b_email, "內容審查者 B")
    reviewer_a_headers = _auth_headers(reviewer_a)
    reviewer_b_headers = _auth_headers(reviewer_b)

    backlog = requests.get(
        f"{live_server.base_url}/admin/application-workflow-review-backlog",
        headers=reviewer_a_headers,
        timeout=15,
    )
    backlog.raise_for_status()
    backlog_payload = backlog.json()
    assert backlog_payload["source_metadata_gap_reference_count"] == 215
    assert backlog_payload["distinct_source_metadata_gap_url_count"] == 6
    assert len(backlog_payload["source_metadata_gap_groups"]) == 6
    assert all(
        group["research_candidate"] is not None
        for group in backlog_payload["source_metadata_gap_groups"]
    )
    assert sum(
        group["research_candidate"]["research_status"]
        == "verified_exact_source"
        for group in backlog_payload["source_metadata_gap_groups"]
    ) == 5
    assert sum(
        group["research_candidate"]["research_status"] == "source_unavailable"
        for group in backlog_payload["source_metadata_gap_groups"]
    ) == 1
    assert all(
        group["research_candidate"]["can_prefill"] is False
        for group in backlog_payload["source_metadata_gap_groups"]
    )
    readiness = requests.get(
        f"{live_server.base_url}/admin/web-release-readiness",
        headers=reviewer_a_headers,
        timeout=15,
    )
    readiness.raise_for_status()
    readiness_payload = readiness.json()
    assert readiness_payload["release_ready"] is False
    assert readiness_payload["blocking_check_count"] == 9
    assert readiness_payload["total_workflow_count"] == 280
    assert readiness_payload["published_workflow_count"] == 0
    assert readiness_payload["critical_rule_count"] == 7067
    assert readiness_payload["total_destination_profile_count"] == 280
    assert readiness_payload["pending_destination_profile_review_count"] == 143
    assert len(readiness_payload["snapshot_fingerprint"]) == 64

    _open_content_review_workbench(
        page,
        live_server,
        reviewer_a_email,
        reviewer_a,
    )
    page.locator("#review-status-filter").select_option("backlog")
    expect(page.locator("#release-readiness-status")).to_have_text(
        "NOT READY",
        timeout=15_000,
    )
    expect(page.locator("#release-readiness-total")).to_have_text("280")
    expect(page.locator("#release-readiness-published")).to_have_text("0")
    expect(page.locator("#release-readiness-rules")).to_have_text("7067")
    expect(page.locator("#release-readiness-destinations")).to_have_text("280")
    expect(page.locator("#release-readiness-destination-pending")).to_have_text("143")
    expect(page.locator("#release-readiness-blockers")).to_have_text("9")
    expect(page.locator("#release-readiness-fingerprint")).to_have_text(
        readiness_payload["snapshot_fingerprint"]
    )
    with page.expect_download() as batch_download_info:
        page.locator("#review-batch-export").click()
    batch_download = batch_download_info.value
    assert batch_download.suggested_filename.startswith("workflow-dual-review-")
    batch_rows = list(
        csv.DictReader(
            StringIO(batch_download.path().read_bytes().decode("utf-8-sig"))
        )
    )
    assert len(batch_rows) == 280
    assert len({row["審查批次"] for row in batch_rows}) == 28
    assert {row["發布狀態指紋"] for row in batch_rows} == {
        readiness_payload["application_workflow_snapshot_fingerprint"]
    }
    review_content_fingerprints = {
        row["審查內容指紋"] for row in batch_rows
    }
    assert len(review_content_fingerprints) == 1
    review_content_fingerprint = review_content_fingerprints.pop()
    assert review_content_fingerprint != readiness_payload["snapshot_fingerprint"]
    assert sum(int(row["關鍵規定數"]) for row in batch_rows) == 7067
    assert {row["已核准人數"] for row in batch_rows} == {"0"}
    assert {row["所需核准人數"] for row in batch_rows} == {"2"}
    assert {row["雙審進度"] for row in batch_rows} == {
        "尚未達發布人數門檻"
    }
    assert all(row["審查者 A"] == "" for row in batch_rows)
    assert all(row["審查者 B"] == "" for row in batch_rows)
    assert all("不能匯入" in row["重要聲明"] for row in batch_rows)
    first_workbench_path = batch_rows[0]["工作台路徑"]
    assert (
        f"review_snapshot={review_content_fingerprint}"
        in first_workbench_path
    )
    stale_workbench_path = first_workbench_path.replace(
        review_content_fingerprint,
        "0" * 64,
    )
    page.goto(f"{live_server.base_url}{stale_workbench_path}")
    expect(page.locator("#workflow-deep-link-filter")).to_be_visible(timeout=15_000)
    expect(page.locator("#workflow-deep-link-description")).to_contain_text(
        "這份分工清單已過期"
    )
    expect(page.locator("#review-count")).to_have_text("280")
    expect(page.locator("[data-workflow-key]")).to_have_count(25)
    page.locator("#clear-workflow-deep-link").click()
    expect(page.locator("#workflow-deep-link-filter")).to_be_hidden()
    assert "review_snapshot" not in page.url
    first_batch_path = batch_rows[0]["批次工作台路徑"]
    page.goto(f"{live_server.base_url}{first_batch_path}")
    expect(page.locator("#workflow-deep-link-filter")).to_be_visible(timeout=15_000)
    expect(page.locator("#workflow-deep-link-description")).to_contain_text(
        batch_rows[0]["審查批次"]
    )
    expect(page.locator("#review-count")).to_have_text("10")
    expect(page.locator("[data-workflow-key]")).to_have_count(10)
    with page.expect_download() as rule_download_info:
        page.locator("#review-batch-rule-export").click()
    rule_download = rule_download_info.value
    assert rule_download.suggested_filename.startswith("workflow-rule-review-")
    rule_rows = list(
        csv.DictReader(
            StringIO(rule_download.path().read_bytes().decode("utf-8-sig"))
        )
    )
    expected_batch_rules = sum(
        int(row["關鍵規定數"])
        for row in batch_rows
        if row["審查批次"] == batch_rows[0]["審查批次"]
    )
    assert len(rule_rows) == expected_batch_rules
    assert len({row["workflow_key"] for row in rule_rows}) == 10
    assert {row["發布狀態指紋"] for row in rule_rows} == {
        readiness_payload["application_workflow_snapshot_fingerprint"]
    }
    assert {row["審查內容指紋"] for row in rule_rows} == {
        review_content_fingerprint
    }
    assert all(row["規定鍵"] for row in rule_rows)
    assert all(row["規定名稱"] for row in rule_rows)
    assert all(row["審查者 A 已核對"] == "" for row in rule_rows)
    assert all(row["審查者 B 已核對"] == "" for row in rule_rows)
    assert all("不能匯入" in row["重要聲明"] for row in rule_rows)
    page.locator("#clear-workflow-deep-link").click()
    expect(page.locator("#review-batch-rule-export")).to_be_hidden()
    expect(page.locator("#review-count")).to_have_text("280")
    assert "review_batch" not in page.url
    assert "batch_size" not in page.url
    page.goto(f"{live_server.base_url}{first_workbench_path}")
    expect(page.locator("#workflow-deep-link-filter")).to_be_visible(timeout=15_000)
    expect(page.locator("#review-count")).to_have_text("1")
    expect(page.locator("[data-workflow-key]")).to_have_count(1)
    page.locator("#clear-workflow-deep-link").click()
    expect(page.locator("#workflow-deep-link-filter")).to_be_hidden()
    expect(page.locator("#review-count")).to_have_text("280")
    evidence_summary = page.locator("#source-evidence-gap-summary")
    expect(evidence_summary).to_be_visible(timeout=15_000)
    expect(page.locator("#source-evidence-gap-description")).to_contain_text(
        "215 筆流程來源證據缺口集中在 6 個完全相同的網址"
    )
    evidence_groups = page.locator(".source-evidence-gap-group")
    expect(evidence_groups).to_have_count(6)
    research_candidates = page.locator(".source-metadata-research-candidate")
    expect(research_candidates).to_have_count(6)
    expect(page.locator(".source-metadata-research-candidate.is-exact-source")).to_have_count(5)
    expect(page.locator(".source-metadata-research-candidate.is-unavailable")).to_have_count(1)
    expect(page.locator(".source-metadata-research-candidate.is-unavailable")).to_contain_text(
        "HTTP 200 只代表請求成功"
    )
    expect(page.locator(".source-metadata-research-candidate button")).to_have_count(0)
    largest_group = backlog_payload["source_metadata_gap_groups"][0]
    source_export_href = evidence_groups.first.locator(
        ".source-evidence-export"
    ).get_attribute("href")
    assert source_export_href
    source_export_query = parse_qs(urlparse(source_export_href).query)
    assert source_export_query["source_url"] == [largest_group["source_url"]]
    assert source_export_query["expected_snapshot"] == [
        largest_group["source_evidence_snapshot_fingerprint"]
    ]
    with page.expect_download() as download_info:
        evidence_groups.first.locator(".source-evidence-export").click()
    download = download_info.value
    assert download.suggested_filename == (
        "source-evidence-review-"
        f"{largest_group['source_evidence_snapshot_fingerprint'][:12]}.csv"
    )
    exported_rows = list(
        csv.DictReader(
            StringIO(download.path().read_bytes().decode("utf-8-sig"))
        )
    )
    assert len(exported_rows) == largest_group["workflow_count"]
    assert {
        row["來源證據快照指紋"] for row in exported_rows
    } == {largest_group["source_evidence_snapshot_fingerprint"]}
    assert sum(int(row["關鍵規定數"]) for row in exported_rows) == (
        largest_group["critical_rule_reference_count"]
    )
    assert {row["研究狀態"] for row in exported_rows} == {"已核對原始來源"}
    assert {row["候選正式標題"] for row in exported_rows} == {
        largest_group["research_candidate"]["proposed_title"]
    }
    assert {row["可自動填入"] for row in exported_rows} == {"否"}
    assert all(row["自動研究證據"] for row in exported_rows)
    assert all(row["人工檢查事項"] for row in exported_rows)
    assert all("不能取代工作台" in row["重要聲明"] for row in exported_rows)
    evidence_groups.first.locator("[data-source-evidence-group-index]").click()
    expect(page.locator("#review-count")).to_have_text(
        str(largest_group["workflow_count"])
    )
    expect(page.locator("#source-evidence-gap-description")).to_contain_text(
        f"目前只顯示引用這個網址的 {largest_group['workflow_count']} 筆流程"
    )
    page.locator("#clear-source-evidence-filter").click()
    expect(page.locator("#review-count")).to_have_text("215")

    target = next(
        row
        for row in sorted(
            backlog_payload["items"],
            key=lambda item: item["source_count"],
        )
        if not row["has_pending_revision"]
        and row["source_count"] > 0
        and row["academic_year_ready"]
        and row["effective_round_ready"]
        and row["critical_rule_source_gap_count"] == 0
        and row["insecure_source_count"] == 0
    )
    staged = requests.post(
        f"{live_server.base_url}/admin/application-workflow-review-backlog/{target['workflow_key']}/stage",
        headers=reviewer_a_headers,
        timeout=15,
    )
    staged.raise_for_status()
    staged_payload = staged.json()
    revision_id = staged_payload["id"]
    staged_backlog = requests.get(
        f"{live_server.base_url}/admin/application-workflow-review-backlog",
        headers=reviewer_a_headers,
        timeout=15,
    )
    staged_backlog.raise_for_status()
    staged_item = next(
        row
        for row in staged_backlog.json()["items"]
        if row["workflow_key"] == target["workflow_key"]
    )
    assert staged_item["version"] == staged_payload["workflow"]["version"]
    assert staged_item["review_approval_count"] == 0
    assert staged_item["required_review_count"] == 2
    assert staged_item["review_ready_to_publish"] is False

    page.locator("#review-status-filter").select_option("pending_review")
    card = page.locator(f'[data-revision-id="{revision_id}"]')
    expect(card).to_be_visible(timeout=15_000)
    expect(card.locator(".review-metadata-blocker")).to_contain_text(
        "來源年度缺漏或不一致"
    )
    card.locator(".applicability-editor > summary").click()
    applicability_progress = card.locator("[data-applicability-progress]")
    expect(applicability_progress).to_contain_text(
        f"已選擇 0 / {target['source_count']} 個來源"
    )
    expect(card.locator("[data-review-applicability-save]")).to_be_disabled()
    applicability_draft_status = card.locator(
        "[data-workflow-applicability-draft-status]"
    )
    expect(applicability_draft_status).to_contain_text("尚未建立補正草稿")
    card.locator("[data-applicability-academic-year]").fill(target["academic_year"])
    applicability_rows = card.locator("[data-applicability-source-row]")
    assert applicability_rows.count() == target["source_count"]
    first_applicability_row = applicability_rows.first
    expect(
        first_applicability_row.locator("[data-applicability-source-progress]")
    ).to_contain_text("本次未選取，不會儲存這列欄位")
    draft_note = "E2E 尚未送出的逐頁補正草稿，不得形成後端證據。"
    card.locator("[data-applicability-note]").fill(draft_note)
    first_applicability_row.locator("[data-applicability-source]").check()
    first_source_progress = first_applicability_row.locator(
        "[data-applicability-source-progress]"
    )
    expect(first_source_progress).to_contain_text(
        "本次補正尚未完成：缺少 3 位數來源適用學年度"
    )
    next_issue_button = card.locator("[data-applicability-next-issue]")
    expect(next_issue_button).to_be_visible()
    next_issue_button.click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "已前往下一個尚未完成的補正欄位"
    )
    first_source_year = first_applicability_row.locator(
        "[data-source-academic-year]"
    )
    expect(first_source_year).to_be_focused()
    first_source_year.fill(target["academic_year"])
    if first_applicability_row.get_attribute("data-source-metadata-complete") == "false":
        expect(first_source_progress).to_contain_text("缺少來源名稱")
        first_applicability_row.locator("[data-source-title]").fill(
            "E2E 未送出補正草稿來源"
        )
        first_applicability_row.locator("[data-source-role]").select_option(
            "home_university"
        )
        first_applicability_row.locator("[data-source-authority]").select_option(
            "home_official_notice"
        )
    expect(first_source_progress).to_contain_text("本次補正欄位完成")
    expect(applicability_draft_status).to_contain_text(
        "已在此分頁工作階段暫存補正內容"
    )
    expect(
        card.locator("[data-workflow-applicability-draft-clear]")
    ).to_be_visible()
    unsaved_draft_response = requests.get(
        f"{live_server.base_url}/admin/application-workflow-revisions",
        params={"status": "pending_review"},
        headers=reviewer_a_headers,
        timeout=15,
    )
    unsaved_draft_response.raise_for_status()
    unsaved_draft_revision = next(
        row for row in unsaved_draft_response.json() if row["id"] == revision_id
    )
    assert unsaved_draft_revision["workflow"] == staged_payload["workflow"]

    page.reload()
    expect(card).to_be_visible(timeout=15_000)
    expect(card.locator(".applicability-editor")).to_have_attribute("open", "")
    applicability_rows = card.locator("[data-applicability-source-row]")
    first_applicability_row = applicability_rows.first
    expect(first_applicability_row.locator("[data-applicability-source]")).to_be_checked()
    expect(first_applicability_row.locator("[data-source-academic-year]")).to_have_value(
        target["academic_year"]
    )
    expect(card.locator("[data-applicability-note]")).to_have_value(draft_note)
    expect(card.locator("[data-workflow-applicability-draft-status]")).to_contain_text(
        "已從此分頁工作階段恢復補正草稿"
    )
    expect(card.locator("[data-applicability-progress]")).to_contain_text(
        f"已選擇 1 / {target['source_count']} 個來源"
    )
    expect(
        first_applicability_row.locator("[data-applicability-source-progress]")
    ).to_contain_text("本次補正欄位完成")
    card.locator("[data-workflow-applicability-draft-clear]").click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "已清除這個待審版本尚未送出的補正草稿"
    )
    expect(first_applicability_row.locator("[data-applicability-source]")).not_to_be_checked()
    expect(
        first_applicability_row.locator("[data-applicability-source-progress]")
    ).to_contain_text("本次未選取，不會儲存這列欄位")
    expect(card.locator("[data-applicability-note]")).to_have_value("")
    expect(card.locator("[data-workflow-applicability-draft-status]")).to_contain_text(
        "尚未建立補正草稿"
    )
    expect(card.locator("[data-workflow-applicability-draft-clear]")).to_be_hidden()

    card.locator("[data-applicability-academic-year]").fill(target["academic_year"])
    for index in range(applicability_rows.count()):
        source_row = applicability_rows.nth(index)
        source_row.locator("[data-applicability-source]").check()
        source_row.locator("[data-source-academic-year]").fill(
            target["academic_year"]
        )
        if source_row.get_attribute("data-source-metadata-complete") == "false":
            source_row.locator("[data-source-title]").fill(
                "E2E 人工查核官方來源"
            )
            source_row.locator("[data-source-role]").select_option(
                "home_university"
            )
            source_row.locator("[data-source-authority]").select_option(
                "home_official_notice"
            )
    card.locator("[data-applicability-note]").fill(
        "E2E 逐頁補齊全部來源的適用年度與缺少的來源證據資料。"
    )
    expect(applicability_progress).to_contain_text(
        f"已選擇 {target['source_count']} / {target['source_count']} 個來源"
    )
    expect(applicability_progress).to_contain_text(
        "可儲存本次逐頁補正；未勾選來源保持不變"
    )
    expect(card.locator("[data-applicability-source-row].is-ready")).to_have_count(
        target["source_count"]
    )
    expect(card.locator("[data-applicability-next-issue]")).to_be_hidden()
    applicability_save = card.locator("[data-review-applicability-save]")
    expect(applicability_save).to_be_enabled()
    applicability_save.click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "待審修正已保存",
        timeout=15_000,
    )
    corrected_backlog = requests.get(
        f"{live_server.base_url}/admin/application-workflow-review-backlog",
        headers=reviewer_a_headers,
        timeout=15,
    )
    corrected_backlog.raise_for_status()
    corrected_item = next(
        row
        for row in corrected_backlog.json()["items"]
        if row["workflow_key"] == target["workflow_key"]
    )
    assert corrected_item["source_year_missing_count"] == 0
    assert corrected_item["source_metadata_missing_count"] == 0
    assert corrected_item["review_approval_count"] == 0

    current_batches = requests.get(
        f"{live_server.base_url}/admin/application-workflow-review-batches.csv",
        params={"batch_size": 2},
        headers=reviewer_a_headers,
        timeout=15,
    )
    current_batches.raise_for_status()
    current_batch_rows = list(
        csv.DictReader(StringIO(current_batches.content.decode("utf-8-sig")))
    )
    target_batch_row = next(
        row
        for row in current_batch_rows
        if row["workflow_key"] == target["workflow_key"]
    )
    target_batch_id = target_batch_row["審查批次"]
    target_batch_rows = [
        row for row in current_batch_rows if row["審查批次"] == target_batch_id
    ]
    assert len(target_batch_rows) == 2
    staged_batch = requests.post(
        f"{live_server.base_url}/admin/application-workflow-review-batches/"
        f"{requests.utils.quote(target_batch_id, safe='')}/stage",
        json={
            "expected_snapshot": target_batch_row["審查內容指紋"],
            "batch_size": 2,
        },
        headers=reviewer_a_headers,
        timeout=30,
    )
    staged_batch.raise_for_status()
    staged_batch_payload = staged_batch.json()
    assert staged_batch_payload["created_count"] == 1
    assert staged_batch_payload["existing_count"] == 1
    page.goto(
        f"{live_server.base_url}{target_batch_row['批次工作台路徑']}"
        f"&review_status=pending_review&workflow_revision={revision_id}"
    )
    expect(page.locator("#workflow-review-owner-filter")).to_have_value(
        "mine_unreviewed",
        timeout=15_000,
    )
    expect(page.locator("#review-queue")).to_have_attribute(
        "aria-busy",
        "false",
        timeout=30_000,
    )
    expect(page.locator("#workflow-review-focus-description")).to_contain_text(
        "待審版本 2 筆、我的待辦 2 筆"
    )

    card = page.locator(f'[data-revision-id="{revision_id}"]')
    expect(card).to_be_visible(timeout=15_000)
    expect(card.locator("[data-workflow-applicability-draft-status]")).to_contain_text(
        "尚未建立補正草稿"
    )
    expect(card.locator("[data-workflow-applicability-draft-clear]")).to_be_hidden()
    expect(card.locator(".review-correction-summary")).to_contain_text(
        "資料門檻完成，可開始真人核對"
    )
    expect(card.locator(".review-metadata-blocker")).to_have_count(0)
    approve = card.locator(
        '[data-review-action="approve"]:not([data-approval-submit-next])'
    )
    approve_and_next = card.locator("[data-approval-submit-next]")
    expect(approve).to_be_disabled()
    expect(approve_and_next).to_be_disabled()
    card.locator("[data-review-comparison]").click()
    source_checks = card.locator("[data-approval-source]")
    expect(source_checks.first).to_be_enabled(timeout=15_000)
    source_count = source_checks.count()
    assert source_count > 0
    initial_rule_count = card.locator("[data-approval-rule]").count()
    assert initial_rule_count > 0
    approval_completion = card.locator("[data-approval-completion]")
    expect(approval_completion).to_contain_text(
        f"官方來源 0／{source_count}"
    )
    expect(approval_completion).to_contain_text(
        f"關鍵規定 0／{initial_rule_count}"
    )
    expect(approval_completion).to_contain_text("查核說明未填寫")
    next_approval_issue = card.locator("[data-approval-next-issue]")
    expect(next_approval_issue).to_have_text("前往下一個未確認來源")
    next_approval_issue.click()
    expect(source_checks.first).to_be_focused()
    expect(page.locator("#review-announcement")).to_contain_text(
        "下一個尚未確認的官方來源"
    )
    draft_source = source_checks.first
    draft_source_id = draft_source.get_attribute("id")
    assert draft_source_id
    card.locator(f'label[for="{draft_source_id}"]').click()
    draft_rule = card.locator("[data-approval-rule]").first
    draft_rule_id = draft_rule.get_attribute("id")
    assert draft_rule_id
    card.locator(f'label[for="{draft_rule_id}"]').click()
    card.locator("[data-review-note]").fill(
        "這是尚未送出的申請流程人工查核暫存，重新整理後仍應恢復。"
    )
    expect(
        card.locator("[data-workflow-review-draft-status]")
    ).to_contain_text("已在此分頁工作階段暫存")
    expect(approval_completion).to_contain_text("查核說明已填寫")
    expect(approve).to_be_disabled()

    page.reload()
    expect(page.locator("#reviewer-email")).to_have_text(
        reviewer_a_email,
        timeout=15_000,
    )
    expect(page.locator("#review-status-filter")).to_have_value("pending_review")
    assert parse_qs(urlparse(page.url).query)["review_status"] == [
        "pending_review"
    ]
    card = page.locator(f'[data-revision-id="{revision_id}"]')
    expect(card).to_be_visible(timeout=15_000)
    expect(
        card.locator("[data-workflow-review-draft-status]")
    ).to_contain_text("已從此分頁工作階段恢復暫存")
    card.locator("[data-review-comparison]").click()
    source_checks = card.locator("[data-approval-source]")
    expect(source_checks.first).to_be_enabled(timeout=15_000)
    expect(source_checks.first).to_be_checked()
    expect(card.locator("[data-approval-rule]").first).to_be_checked()
    expect(card.locator("[data-review-note]")).to_have_value(
        "這是尚未送出的申請流程人工查核暫存，重新整理後仍應恢復。"
    )
    expect(card.locator("[data-approval-completion]")).to_contain_text(
        "查核說明已填寫"
    )
    expect(
        card.locator(
            '[data-review-action="approve"]:not([data-approval-submit-next])'
        )
    ).to_be_disabled()
    card.locator("[data-workflow-review-draft-clear]").click()
    expect(source_checks.first).not_to_be_checked()
    expect(card.locator("[data-approval-rule]").first).not_to_be_checked()
    expect(card.locator("[data-review-note]")).to_have_value("")
    expect(card.locator("[data-approval-completion]")).to_contain_text(
        "查核說明未填寫"
    )
    expect(
        card.locator("[data-workflow-review-draft-clear]")
    ).to_be_hidden()
    expect(page.locator("#review-announcement")).to_contain_text(
        "後端核准與發布紀錄沒有變更"
    )
    approve = card.locator(
        '[data-review-action="approve"]:not([data-approval-submit-next])'
    )
    source_count = source_checks.count()
    for index in range(source_count):
        checkbox = source_checks.nth(index)
        checkbox_id = checkbox.get_attribute("id")
        assert checkbox_id
        card.locator(f'label[for="{checkbox_id}"]').click()
        expect(checkbox).to_be_checked()
    source_states = source_checks.evaluate_all(
        "checkboxes => checkboxes.map((checkbox) => ({id: checkbox.id, checked: checkbox.checked, url: checkbox.dataset.sourceUrl}))"
    )
    assert all(row["checked"] for row in source_states), source_states
    expect(card.locator("[data-approval-source-status]")).to_contain_text(
        f"{source_count} / {source_count}"
    )
    expect(approve).to_be_disabled()
    rule_checks = card.locator("[data-approval-rule]")
    rule_count = rule_checks.count()
    assert rule_count > 0
    expect(card.locator("[data-approval-next-issue]")).to_have_text(
        "前往下一個未確認規定"
    )
    card.locator("[data-approval-next-issue]").click()
    expect(rule_checks.first).to_be_focused()
    expect(page.locator("#review-announcement")).to_contain_text(
        "下一個尚未確認的關鍵規定"
    )
    expect(card.locator(".rule-source-links").first).to_contain_text("對應來源：")
    assert card.locator(".rule-source-links a").count() >= rule_count
    for index in range(rule_count):
        checkbox = rule_checks.nth(index)
        checkbox_id = checkbox.get_attribute("id")
        assert checkbox_id
        card.locator(f'label[for="{checkbox_id}"]').click()
        expect(checkbox).to_be_checked()
    expect(card.locator("[data-approval-rule-status]")).to_contain_text(
        f"{rule_count} / {rule_count}"
    )
    expect(approve).to_be_disabled()
    expect(card.locator("[data-approval-completion]")).to_contain_text(
        "核對項目已完成；請填寫本次查核說明"
    )
    expect(card.locator("[data-approval-next-issue]")).to_have_text(
        "前往查核說明"
    )
    card.locator("[data-approval-next-issue]").click()
    review_note = card.locator("[data-review-note]")
    expect(review_note).to_be_focused()
    expect(page.locator("#review-announcement")).to_contain_text(
        "已前往本次查核說明"
    )
    review_note.fill("   ")
    expect(card.locator("[data-approval-completion]")).to_contain_text(
        "查核說明未填寫"
    )
    expect(approve).to_be_disabled()
    review_note.fill(
        "E2E 審查者 A 已逐頁核對隔離測試版本的全部官方來源。"
    )
    expect(card.locator("[data-approval-completion]")).to_contain_text(
        "本頁已具備獨立核准送出條件"
    )
    expect(card.locator("[data-approval-next-issue]")).to_be_hidden()
    expect(approve).to_be_enabled()
    expect(approve_and_next).to_be_enabled()
    approve_and_next.click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "已前往此批次下一筆我的待辦",
        timeout=15_000,
    )
    expect(page.locator("[data-revision-id]")).to_have_count(1)
    next_revision_id = page.locator("[data-revision-id]").get_attribute(
        "data-revision-id"
    )
    assert next_revision_id
    assert next_revision_id != revision_id
    expect(page.locator(f'[data-revision-id="{next_revision_id}"]')).to_be_focused()
    assert parse_qs(urlparse(page.url).query)["workflow_revision"] == [
        next_revision_id
    ]
    expect(page.locator("#workflow-review-focus-description")).to_contain_text(
        "我的待辦 1 筆"
    )
    expect(page.locator("#workflow-review-focus-description")).to_contain_text(
        "我已核准 1 筆"
    )
    owner_filter = page.locator("#workflow-review-owner-filter")
    owner_filter.select_option("mine_approved")
    expect(page.locator("#review-count")).to_have_text("1")
    card = page.locator(f'[data-revision-id="{revision_id}"]')
    expect(card).to_be_visible()
    expect(card.locator(".approval-row")).to_contain_text(
        f"已逐頁確認 {source_count} 個來源",
    )
    expect(card.locator(".approval-row")).to_contain_text(
        f"已逐項確認 {rule_count} 個關鍵規定"
    )
    expect(
        card.locator("[data-workflow-review-draft-clear]")
    ).to_be_hidden()
    expect(
        card.locator("[data-workflow-review-draft-status]")
    ).to_contain_text("尚未建立本頁暫存")
    owner_filter.select_option("mine_unreviewed")
    expect(page.locator("#review-count")).to_have_text("1")
    expect(card).to_be_hidden()
    owner_filter.select_option("")
    expect(page.locator("#review-count")).to_have_text("2")
    expect(card).to_be_visible()
    one_approval_backlog = requests.get(
        f"{live_server.base_url}/admin/application-workflow-review-backlog",
        headers=reviewer_a_headers,
        timeout=15,
    )
    one_approval_backlog.raise_for_status()
    one_approval_payload = one_approval_backlog.json()
    one_approval_item = next(
        row
        for row in one_approval_payload["items"]
        if row["workflow_key"] == target["workflow_key"]
    )
    assert one_approval_item["review_approval_count"] == 1
    assert one_approval_item["review_ready_to_publish"] is False
    assert one_approval_payload["review_partially_approved_count"] == 1

    pending_after_batch_test = requests.get(
        f"{live_server.base_url}/admin/application-workflow-revisions",
        params={"status": "pending_review"},
        headers=reviewer_a_headers,
        timeout=15,
    )
    pending_after_batch_test.raise_for_status()
    extra_batch_revisions = [
        row
        for row in pending_after_batch_test.json()
        if row["id"] != revision_id
    ]
    assert len(extra_batch_revisions) == 1
    extra_workflow_key = extra_batch_revisions[0]["workflow_key"]
    batch_test_store = LocalContentGovernanceStore(
        live_server.data_dir,
        include_bundled_baseline=True,
    )
    save_application_workflow_revisions(
        [
            row
            for row in batch_test_store.list_revisions()
            if row.workflow_key != extra_workflow_key
        ],
        live_server.data_dir,
    )
    page.goto(
        f"{live_server.base_url}/admin/content-review"
        f"?review_status=pending_review&workflow_revision={revision_id}"
    )
    expect(page.locator(f'[data-revision-id="{revision_id}"]')).to_be_visible(
        timeout=15_000
    )

    context_b = browser.new_context(viewport={"width": 390, "height": 844})
    page_b = context_b.new_page()
    try:
        _open_content_review_workbench(
            page_b,
            live_server,
            reviewer_b_email,
            reviewer_b,
        )
        page_b.locator("#review-status-filter").select_option("backlog")
        expect(page_b.locator("#source-evidence-gap-summary")).to_be_visible(
            timeout=15_000
        )
        assert page_b.evaluate("document.documentElement.scrollWidth") <= 390
        page_b.locator("#backlog-gap-filter").select_option("review_partial")
        expect(page_b.locator("#review-count")).to_have_text("1")
        backlog_card_b = page_b.locator(
            f'[data-workflow-key="{target["workflow_key"]}"]'
        )
        expect(backlog_card_b).to_contain_text("待第二位核准 1/2")
        backlog_card_b.locator('[data-backlog-action="open"]').click()
        expect(page_b.locator("#review-status-filter")).to_have_value(
            "pending_review"
        )
        review_location = parse_qs(urlparse(page_b.url).query)
        assert review_location["review_status"] == ["pending_review"]
        assert review_location["workflow_revision"] == [revision_id]
        expect(page_b.locator("#workflow-review-focus-filter")).to_be_visible()
        expect(page_b.locator("#workflow-review-focus-description")).to_contain_text(
            target["school_name"]
        )
        page_b.reload()
        expect(page_b.locator("#reviewer-email")).to_have_text(
            reviewer_b_email,
            timeout=15_000,
        )
        expect(page_b.locator("#review-status-filter")).to_have_value(
            "pending_review"
        )
        expect(page_b.locator("#workflow-review-focus-filter")).to_be_visible()
        card_b = page_b.locator(f'[data-revision-id="{revision_id}"]')
        expect(card_b).to_be_visible(timeout=15_000)
        owner_filter_b = page_b.locator("#workflow-review-owner-filter")
        owner_filter_b.select_option("mine_unreviewed")
        expect(page_b.locator("#review-count")).to_have_text("1")
        expect(card_b).to_be_visible()
        owner_filter_b.select_option("mine_approved")
        expect(page_b.locator("#review-count")).to_have_text("0")
        expect(card_b).to_be_hidden()
        owner_filter_b.select_option("")
        expect(page_b.locator("#review-count")).to_have_text("1")
        expect(card_b).to_be_visible()
        card_b.locator("[data-review-comparison]").click()
        source_checks_b = card_b.locator("[data-approval-source]")
        expect(source_checks_b.first).to_be_enabled(timeout=15_000)
        assert source_checks_b.count() == source_count
        for index in range(source_count):
            checkbox = source_checks_b.nth(index)
            checkbox_id = checkbox.get_attribute("id")
            assert checkbox_id
            card_b.locator(f'label[for="{checkbox_id}"]').click()
            expect(checkbox).to_be_checked()
        rule_checks_b = card_b.locator("[data-approval-rule]")
        assert rule_checks_b.count() == rule_count
        for index in range(rule_count):
            checkbox = rule_checks_b.nth(index)
            checkbox_id = checkbox.get_attribute("id")
            assert checkbox_id
            card_b.locator(f'label[for="{checkbox_id}"]').click()
            expect(checkbox).to_be_checked()
        card_b.locator("[data-review-note]").fill(
            "E2E 審查者 B 已獨立逐頁複核全部官方來源。"
        )
        card_b.locator('[data-review-action="approve"]').click()
        publish = card_b.locator('[data-review-action="publish"]')
        expect(publish).to_be_enabled(timeout=15_000)
        owner_filter_b.select_option("mine_publishable")
        expect(page_b.locator("#review-count")).to_have_text("1")
        expect(card_b).to_be_visible()
        two_approval_backlog = requests.get(
            f"{live_server.base_url}/admin/application-workflow-review-backlog",
            headers=reviewer_b_headers,
            timeout=15,
        )
        two_approval_backlog.raise_for_status()
        two_approval_payload = two_approval_backlog.json()
        two_approval_item = next(
            row
            for row in two_approval_payload["items"]
            if row["workflow_key"] == target["workflow_key"]
        )
        assert two_approval_item["review_approval_count"] == 2
        assert two_approval_item["review_ready_to_publish"] is True
        assert two_approval_payload["review_ready_count"] == 1
        card_b.locator("[data-review-note]").fill("E2E 雙審完成後發布。")
        publish.click()
        expect(card_b).to_be_hidden(timeout=15_000)
        assert "workflow_revision" not in page_b.url
    finally:
        context_b.close()

    published = requests.get(
        f"{live_server.base_url}/admin/application-workflow-revisions",
        params={"status": "published"},
        headers=reviewer_b_headers,
        timeout=15,
    )
    published.raise_for_status()
    revision = next(row for row in published.json() if row["id"] == revision_id)
    assert len(revision["review_approvals"]) == 2
    assert all(
        len(approval["reviewed_source_urls"]) == source_count
        and len(approval["reviewed_rule_keys"]) == rule_count
        and approval["reviewed_content_hash"] == revision["content_hash"]
        for approval in revision["review_approvals"]
    )
    published_backlog = requests.get(
        f"{live_server.base_url}/admin/application-workflow-review-backlog",
        headers=reviewer_b_headers,
        timeout=15,
    )
    published_backlog.raise_for_status()
    assert target["workflow_key"] not in {
        row["workflow_key"] for row in published_backlog.json()["items"]
    }

    content_store = LocalContentGovernanceStore(live_server.data_dir)
    first_publication = next(
        row for row in content_store.list_revisions() if row.id == revision_id
    )
    first_title = first_publication.workflow.steps[0].title
    mistaken_workflow = first_publication.workflow.model_copy(
        update={
            "steps": [
                first_publication.workflow.steps[0].model_copy(
                    update={"title": "E2E 誤發布、必須立即撤回的流程內容"}
                ),
                *first_publication.workflow.steps[1:],
            ]
        }
    )
    second_publication = stage_workflow_refresh(
        content_store,
        mistaken_workflow,
        detected_by=reviewer_a["profile"]["id"],
    ).revision
    assert second_publication is not None
    for headers, note in (
        (reviewer_a_headers, "E2E 審查者 A 核對第二個隔離發布版本。"),
        (reviewer_b_headers, "E2E 審查者 B 獨立核對第二個隔離發布版本。"),
    ):
        approval = requests.post(
            f"{live_server.base_url}/admin/application-workflow-revisions/{second_publication.id}/approve",
            headers=headers,
            json={
                "expected_content_hash": second_publication.content_hash,
                "reviewed_source_urls": workflow_review_source_urls(
                    second_publication.workflow
                ),
                "reviewed_rule_keys": workflow_review_rule_keys(
                    second_publication.workflow
                ),
                "note": note,
            },
            timeout=15,
        )
        approval.raise_for_status()
    second_publish = requests.post(
        f"{live_server.base_url}/admin/application-workflow-revisions/{second_publication.id}/publish",
        headers=reviewer_b_headers,
        json={"note": "E2E 建立第二個發布版本，用來驗證安全復原。"},
        timeout=15,
    )
    second_publish.raise_for_status()

    page.locator("#reload-review-queue").click()
    publication_history = page.locator("#workflow-publication-history")
    publication_history.locator("summary").click()
    expect(page.locator("#workflow-publication-history-summary")).to_contain_text(
        "1 筆可安全恢復舊版",
        timeout=15_000,
    )
    workflow_card = page.locator(".workflow-publication-card").filter(
        has_text=target["school_name"]
    ).first
    expect(workflow_card).to_be_visible()
    expect(workflow_card).to_contain_text(
        f"目前版本 {second_publication.version}"
    )
    target_select = workflow_card.locator("[data-workflow-rollback-target]")
    expect(target_select.locator(f'option[value="{revision_id}"]')).to_have_count(1)
    target_select.select_option(revision_id)
    workflow_card.locator("[data-workflow-rollback-note]").fill(
        "E2E 發現第二版內容有重大疑義，立即恢復先前完整雙審版本。"
    )
    workflow_card.locator("[data-workflow-rollback-confirm]").check()
    workflow_card.locator("[data-workflow-rollback-submit]").click()
    restored_version = second_publication.version + 1
    expect(page.locator("#review-announcement")).to_contain_text(
        f"已安全恢復並建立公開版本 {restored_version}",
        timeout=15_000,
    )
    expect(workflow_card).to_contain_text(f"目前版本 {restored_version}")
    expect(workflow_card).to_contain_text("目前使用復原後的新版本")

    rollback_history = requests.get(
        f"{live_server.base_url}/admin/application-workflow-publications",
        headers=reviewer_a_headers,
        timeout=15,
    )
    rollback_history.raise_for_status()
    restored_state = next(
        row
        for row in rollback_history.json()["items"]
        if row["workflow_key"] == target["workflow_key"]
    )
    assert restored_state["current_publication_action"] == "rollback"
    assert restored_state["publication_history"][0]["restored_revision_id"] == revision_id
    assert (
        restored_state["publication_history"][0]["rolled_back_from_revision_id"]
        == second_publication.id
    )
    restored_public = next(
        row
        for row in LocalContentGovernanceStore(
            live_server.data_dir
        ).load_published_workflows()
        if row.governance_key == target["workflow_key"]
    )
    assert restored_public.version == restored_version
    assert restored_public.steps[0].title == first_title


@pytest.mark.skip(reason="Phase C")
def test_content_admin_downloads_snapshot_bound_destination_profile_review_queue(
    page: Page,
    live_server: LiveServer,
    monkeypatch,
) -> None:
    reviewer_email = _email("destination-reviewer")
    second_reviewer_email = _email("destination-second-reviewer")
    monkeypatch.setenv(
        "EXCHANGE_CONTENT_ADMIN_EMAILS",
        f"{reviewer_email},{second_reviewer_email}",
    )
    live_server.register(reviewer_email, "生活情報審查者")
    second_reviewer = live_server.register(
        second_reviewer_email,
        "生活情報第二審查者",
    )
    second_reviewer_headers = _auth_headers(second_reviewer)
    public_before = requests.get(
        f"{live_server.base_url}/destination-profiles",
        params={"home_school": "長庚大學"},
        timeout=15,
    )
    public_before.raise_for_status()

    login_through_web(page, live_server, reviewer_email)
    page.goto(f"{live_server.base_url}/admin/content-review")
    expect(page.locator("#reviewer-email")).to_have_text(reviewer_email)
    summary = page.locator("#destination-profile-review-summary")
    expect(summary).to_be_visible(timeout=15_000)
    expect(summary).to_contain_text("共有 77 筆生活情報")
    expect(summary).to_contain_text("19 筆完整查核、58 筆待人工續審")
    expect(summary).to_contain_text("46 筆明確等待第二位真人")
    expect(summary).to_contain_text("246 個官方來源")

    workbench = page.locator("#destination-profile-review-workbench")
    workbench.locator(":scope > summary").click()
    home_university = page.locator("#destination-review-home-university")
    home_university.select_option("國立臺北大學")
    expect(summary).to_contain_text("國立臺北大學共有 203 筆生活情報")
    expect(summary).to_contain_text("118 筆完整查核、85 筆待人工續審")
    expect(summary).to_contain_text("0 筆明確等待第二位真人")
    expect(summary).to_contain_text("224 個官方來源")
    expect(page.locator("#destination-publication-history-summary")).to_contain_text(
        "國立臺北大學"
    )

    with page.expect_download() as ntpu_download_info:
        summary.locator("#download-destination-profile-review").click()
    ntpu_download = ntpu_download_info.value
    ntpu_download_params = parse_qs(urlparse(ntpu_download.url).query)
    assert ntpu_download_params["home_university"] == ["國立臺北大學"]
    assert len(ntpu_download_params["expected_snapshot"][0]) == 64
    ntpu_rows = list(
        csv.DictReader(
            StringIO(ntpu_download.path().read_bytes().decode("utf-8-sig"))
        )
    )
    assert len(ntpu_rows) == 85
    assert all(row["母校"] == "國立臺北大學" for row in ntpu_rows)

    with page.expect_download() as ntpu_batch_download_info:
        summary.locator("#download-destination-profile-review-batches").click()
    ntpu_batch_download = ntpu_batch_download_info.value
    assert ntpu_batch_download.suggested_filename.startswith(
        "destination-dual-review-"
    )
    ntpu_batch_params = parse_qs(urlparse(ntpu_batch_download.url).query)
    assert ntpu_batch_params["home_university"] == ["國立臺北大學"]
    assert ntpu_batch_params["batch_size"] == ["10"]
    ntpu_batch_rows = list(
        csv.DictReader(
            StringIO(ntpu_batch_download.path().read_bytes().decode("utf-8-sig"))
        )
    )
    assert len(ntpu_batch_rows) == 85
    assert len({row["審查批次"] for row in ntpu_batch_rows}) == 9
    assert all(row["母校"] == "國立臺北大學" for row in ntpu_batch_rows)
    first_batch_id = ntpu_batch_rows[0]["審查批次"]
    first_batch_rows = [
        row for row in ntpu_batch_rows if row["審查批次"] == first_batch_id
    ]
    assert len(first_batch_rows) == 10
    first_batch_path = first_batch_rows[0]["批次工作台路徑"]
    first_batch_query = parse_qs(urlparse(first_batch_path).query)
    assert first_batch_query["destination_home"] == ["國立臺北大學"]
    assert first_batch_query["destination_batch"] == [first_batch_id]
    assert len(first_batch_query["destination_snapshot"][0]) == 64

    page.goto(f"{live_server.base_url}{first_batch_path}")
    summary = page.locator("#destination-profile-review-summary")
    expect(summary).to_contain_text(
        "國立臺北大學共有 203 筆生活情報",
        timeout=15_000,
    )
    workbench = page.locator("#destination-profile-review-workbench")
    expect(workbench).to_have_attribute("open", "")
    batch_filter = page.locator("#destination-review-batch-filter")
    expect(batch_filter).to_be_visible()
    expect(batch_filter).to_contain_text(
        f"目前從生活情報分工清單定位：{first_batch_id}"
    )
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(10)
    for batch_row in (first_batch_rows[0], first_batch_rows[-1]):
        expect(
            page.locator(
                f'[data-destination-profile-hash="{batch_row["生活情報內容指紋"]}"]'
            )
        ).to_be_visible()
    expect(page.locator("#destination-review-batch-description")).to_contain_text(
        "我的待辦 10"
    )
    expect(page.locator("#destination-review-batch-description")).to_contain_text(
        "可選擇核可 0"
    )
    expect(page.locator("#destination-review-batch-description")).to_contain_text(
        "只能要求修正 10"
    )
    readiness_filter = page.locator("#destination-review-readiness-filter")
    readiness_filter.select_option("approval_blocked")
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(10)
    next_destination_todo = page.locator("#open-next-destination-review")
    expect(next_destination_todo).to_be_visible()
    expect(next_destination_todo).to_have_text("開啟第一筆我的待辦（10 筆）")
    readiness_filter.select_option("approval_ready")
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(0)
    expect(page.locator("#destination-profile-review-items")).to_contain_text(
        "目前核可門檻篩選沒有待審生活情報"
    )
    expect(next_destination_todo).to_be_disabled()
    expect(next_destination_todo).to_have_text("目前門檻篩選沒有我的待辦")
    readiness_filter.select_option("")
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(10)
    expect(next_destination_todo).to_be_enabled()
    expect(next_destination_todo).to_have_text("開啟第一筆我的待辦（10 筆）")
    next_destination_todo.click()
    first_destination_card = page.locator(
        f'[data-destination-profile-hash="{first_batch_rows[0]["生活情報內容指紋"]}"]'
    )
    expect(
        first_destination_card.locator(".destination-review-detail")
    ).to_have_attribute("open", "")
    expect(
        first_destination_card.locator(".destination-review-detail > summary")
    ).to_be_focused()
    blocked_gate = first_destination_card.locator(
        "[data-destination-review-approval-gate]"
    )
    expect(blocked_gate).to_contain_text("目前只能要求修正，不能核可")
    blocked_decision = first_destination_card.locator(
        "[data-destination-review-decision]"
    )
    expect(blocked_decision).to_have_value("changes_required")
    assert (
        blocked_decision.locator('option[value="approve"]').get_attribute("disabled")
        == ""
    )
    expect(page.locator("#review-announcement")).to_contain_text(
        "已開啟此批次第 1／10 筆我的待辦"
    )
    expect(next_destination_todo).to_have_text("開啟下一筆我的待辦（10 筆）")
    next_destination_todo.click()
    second_destination_card = page.locator(
        f'[data-destination-profile-hash="{first_batch_rows[1]["生活情報內容指紋"]}"]'
    )
    expect(
        second_destination_card.locator(".destination-review-detail")
    ).to_have_attribute("open", "")
    expect(
        second_destination_card.locator(".destination-review-detail > summary")
    ).to_be_focused()
    expect(page.locator("#review-announcement")).to_contain_text(
        "已開啟此批次第 2／10 筆我的待辦"
    )
    page.locator("#show-destination-review-batch").click()
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(10)
    expect(page.locator(".destination-review-detail[open]")).to_have_count(0)
    expect(page.locator("#review-announcement")).to_contain_text(
        "已顯示此批次的完整『我的待辦』清單"
    )
    expect(next_destination_todo).to_have_text("開啟第一筆我的待辦（10 筆）")
    progress_filter = page.locator("#destination-review-progress-filter")
    progress_filter.select_option("mine_unreviewed")
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(10)
    progress_filter.select_option("mine_reviewed")
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(0)
    expect(page.locator("#destination-profile-review-items")).to_contain_text(
        "目前篩選條件沒有待審生活情報"
    )
    progress_filter.select_option("")
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(10)

    draft_profile_hash = first_batch_rows[0]["生活情報內容指紋"]
    draft_card = page.locator(
        f'[data-destination-profile-hash="{draft_profile_hash}"]'
    )
    draft_card.locator(".destination-review-detail > summary").click()
    draft_source_checks = draft_card.locator("[data-destination-review-source]")
    had_source_check = draft_source_checks.count() > 0
    checklist_progress = draft_card.locator(
        "[data-destination-review-check-progress]"
    )
    expect(checklist_progress).to_contain_text(
        f"官方來源 0／{draft_source_checks.count()}"
    )
    expect(checklist_progress).to_contain_text("內容區塊 0／12")
    expect(checklist_progress).to_contain_text("審查說明 0 字（至少 10 字）")
    submit_review = draft_card.locator("[data-destination-review-submit]")
    submit_next_review = draft_card.locator(
        "[data-destination-review-submit-next]"
    )
    expect(submit_review).to_be_disabled()
    expect(submit_next_review).to_be_disabled()
    next_unchecked = draft_card.locator(
        "[data-destination-review-next-unchecked]"
    )
    expect(next_unchecked).to_be_visible()
    next_unchecked.click()
    if had_source_check:
        expect(draft_source_checks.first).to_be_focused()
        expect(page.locator("#review-announcement")).to_contain_text(
            "下一個尚未核對的官方來源"
        )
        draft_source_checks.first.check()
        expect(checklist_progress).to_contain_text(
            f"官方來源 1／{draft_source_checks.count()}"
        )
    else:
        expect(
            draft_card.locator("[data-destination-review-section]").first
        ).to_be_focused()
    draft_card.locator("[data-destination-review-section]").first.check()
    expect(checklist_progress).to_contain_text("內容區塊 1／12")
    draft_card.locator("[data-destination-review-note]").fill(
        "這是尚未送出的分頁人工查核暫存，重新整理後仍應恢復。"
    )
    expect(
        draft_card.locator("[data-destination-review-draft-status]")
    ).to_contain_text("已在此分頁工作階段暫存")
    expect(submit_review).to_be_disabled()
    expect(submit_next_review).to_be_disabled()
    draft_card.locator("[data-destination-review-decision]").evaluate(
        """select => {
          select.querySelector('option[value="approve"]').disabled = false;
          select.value = 'approve';
          select.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )

    page.reload()
    expect(page.locator("#destination-profile-review-summary")).to_contain_text(
        "國立臺北大學共有 203 筆生活情報",
        timeout=15_000,
    )
    expect(page.locator("#destination-review-batch-filter")).to_be_visible()
    draft_card = page.locator(
        f'[data-destination-profile-hash="{draft_profile_hash}"]'
    )
    draft_card.locator(".destination-review-detail > summary").click()
    expect(
        draft_card.locator("[data-destination-review-decision]")
    ).to_have_value("changes_required")
    assert (
        draft_card.locator(
            '[data-destination-review-decision] option[value="approve"]'
        ).get_attribute("disabled")
        == ""
    )
    if had_source_check:
        expect(
            draft_card.locator("[data-destination-review-source]").first
        ).to_be_checked()
        expect(
            draft_card.locator("[data-destination-review-check-progress]")
        ).to_contain_text(f"官方來源 1／{draft_source_checks.count()}")
    expect(
        draft_card.locator("[data-destination-review-section]").first
    ).to_be_checked()
    expect(
        draft_card.locator("[data-destination-review-check-progress]")
    ).to_contain_text("內容區塊 1／12")
    expect(
        draft_card.locator("[data-destination-review-submit]")
    ).to_be_disabled()
    expect(draft_card.locator("[data-destination-review-note]")).to_have_value(
        "這是尚未送出的分頁人工查核暫存，重新整理後仍應恢復。"
    )
    expect(
        draft_card.locator("[data-destination-review-draft-status]")
    ).to_contain_text("已從此分頁工作階段恢復暫存")
    draft_card.locator("[data-destination-review-draft-clear]").click()
    if had_source_check:
        expect(
            draft_card.locator("[data-destination-review-source]").first
        ).not_to_be_checked()
    expect(
        draft_card.locator("[data-destination-review-section]").first
    ).not_to_be_checked()
    expect(
        draft_card.locator("[data-destination-review-check-progress]")
    ).to_contain_text("內容區塊 0／12")
    expect(draft_card.locator("[data-destination-review-note]")).to_have_value("")
    expect(
        draft_card.locator("[data-destination-review-check-progress]")
    ).to_contain_text("審查說明 0 字（至少 10 字）")
    expect(
        draft_card.locator("[data-destination-review-submit]")
    ).to_be_disabled()
    expect(
        draft_card.locator("[data-destination-review-decision]")
    ).to_have_value("changes_required")
    expect(
        draft_card.locator("[data-destination-review-draft-clear]")
    ).to_be_hidden()
    expect(page.locator("#review-announcement")).to_contain_text(
        "後端真人審查證據沒有變更"
    )

    checklist_link = page.locator("#download-destination-review-batch-checklist")
    expect(checklist_link).to_be_visible()
    assert checklist_link.get_attribute("href") == first_batch_rows[0][
        "批次逐項查核表路徑"
    ]
    with page.expect_download() as checklist_download_info:
        checklist_link.click()
    checklist_download = checklist_download_info.value
    assert checklist_download.suggested_filename.startswith(
        "destination-review-checklist-"
    )
    checklist_rows = list(
        csv.DictReader(
            StringIO(checklist_download.path().read_bytes().decode("utf-8-sig"))
        )
    )
    expected_source_rows = sum(int(row["官方來源數"]) for row in first_batch_rows)
    assert len(checklist_rows) == 120 + expected_source_rows
    assert sum(row["查核項目類型"] == "內容區塊" for row in checklist_rows) == 120
    assert sum(row["查核項目類型"] == "官方來源" for row in checklist_rows) == (
        expected_source_rows
    )
    assert {
        row["生活情報內容指紋"] for row in checklist_rows
    } == {row["生活情報內容指紋"] for row in first_batch_rows}
    for profile_hash in {row["生活情報內容指紋"] for row in first_batch_rows}:
        assert len(
            [
                row
                for row in checklist_rows
                if row["生活情報內容指紋"] == profile_hash
                and row["查核項目類型"] == "內容區塊"
            ]
        ) == 12
    assert all(row["審查者 A 已核對"] == "" for row in checklist_rows)
    assert all(row["審查者 B 已核對"] == "" for row in checklist_rows)
    assert all("不能匯入" in row["重要聲明"] for row in checklist_rows)

    draft_card = page.locator(
        f'[data-destination-profile-hash="{draft_profile_hash}"]'
    )
    source_checks = draft_card.locator("[data-destination-review-source]")
    for index in range(source_checks.count()):
        source_checks.nth(index).check()
    section_checks = draft_card.locator("[data-destination-review-section]")
    assert section_checks.count() == 12
    for index in range(section_checks.count()):
        section_checks.nth(index).check()
    expect(
        draft_card.locator("[data-destination-review-check-progress]")
    ).to_contain_text("核對項目已完成；審查說明尚需 10 字")
    expect(
        draft_card.locator("[data-destination-review-next-unchecked]")
    ).to_have_text("前往審查說明")
    draft_card.locator("[data-destination-review-next-unchecked]").click()
    note_field = draft_card.locator("[data-destination-review-note]")
    expect(note_field).to_be_focused()
    expect(page.locator("#review-announcement")).to_contain_text(
        "已前往審查說明"
    )
    note_field.fill("123456789")
    expect(
        draft_card.locator("[data-destination-review-check-progress]")
    ).to_contain_text("審查說明尚需 1 字")
    expect(draft_card.locator("[data-destination-review-submit]")).to_be_disabled()
    note_field.fill(
        "已逐一核對目前年度、校區、來源與全部生活情報內容區塊。"
    )
    expect(
        draft_card.locator("[data-destination-review-check-progress]")
    ).to_contain_text("本頁已具備送出條件")
    expect(
        draft_card.locator("[data-destination-review-next-unchecked]")
    ).to_be_hidden()
    expect(draft_card.locator("[data-destination-review-submit]")).to_be_enabled()
    expect(
        draft_card.locator("[data-destination-review-submit-next]")
    ).to_be_enabled()
    blocked_decision = draft_card.locator("[data-destination-review-decision]")
    blocked_decision.evaluate(
        """select => {
          select.querySelector('option[value="approve"]').disabled = false;
          select.value = 'approve';
        }"""
    )
    draft_card.locator("[data-destination-review-submit]").click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "這筆目前只能要求修正"
    )
    expect(blocked_decision).to_have_value("changes_required")
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(10)
    submit_next = draft_card.locator("[data-destination-review-submit-next]")
    expect(submit_next).to_be_visible()
    submit_next.click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "已前往此批次下一筆我的待辦",
        timeout=15_000,
    )
    expect(page.locator("#review-announcement")).to_contain_text(
        "這不代表雙審或發布完成"
    )
    expect(page.locator("#destination-review-progress-filter")).to_have_value(
        "mine_unreviewed"
    )
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(9)
    expect(
        page.locator(f'[data-destination-profile-hash="{draft_profile_hash}"]')
    ).to_have_count(0)
    next_profile_hash = first_batch_rows[1]["生活情報內容指紋"]
    next_card = page.locator(
        f'[data-destination-profile-hash="{next_profile_hash}"]'
    )
    expect(next_card).to_be_visible()
    expect(next_card.locator(".destination-review-detail")).to_have_attribute(
        "open", ""
    )
    expect(next_card.locator(".destination-review-detail > summary")).to_be_focused()
    expect(batch_filter).to_be_visible()

    page.locator("#clear-destination-review-batch").click()
    expect(batch_filter).to_be_hidden()
    expect(checklist_link).to_be_hidden()
    assert "destination_batch" not in page.url

    home_university = page.locator("#destination-review-home-university")
    home_university.select_option("長庚大學")
    expect(summary).to_contain_text("長庚大學共有 77 筆生活情報")
    expect(summary).to_contain_text("19 筆完整查核、58 筆待人工續審")
    expect(summary).to_contain_text("46 筆明確等待第二位真人")
    expect(summary).to_contain_text("246 個官方來源")
    expect(page.locator("#destination-publication-history-summary")).to_contain_text(
        "長庚大學"
    )

    with page.expect_download() as download_info:
        summary.locator("#download-destination-profile-review").click()
    download = download_info.value
    assert download.suggested_filename.startswith("destination-profile-review-")
    rows = list(
        csv.DictReader(
            StringIO(download.path().read_bytes().decode("utf-8-sig"))
        )
    )
    assert len(rows) == 58
    assert all(row["審查者 A"] == "" for row in rows)
    assert all(row["審查者 B"] == "" for row in rows)
    assert all("不能匯入" in row["重要聲明"] for row in rows)
    icd = next(
        row for row in rows if row["合作校"] == "法國ICD商學院 ICD Business School"
    )
    assert icd["目前查核狀態"] == "official_partial"
    assert "second_review_required" in icd["審查缺口代碼"]
    assert len(icd["官方來源網址"].split(" || ")) == 5

    with page.expect_download() as cgu_batch_download_info:
        summary.locator("#download-destination-profile-review-batches").click()
    cgu_batch_rows = list(
        csv.DictReader(
            StringIO(
                cgu_batch_download_info.value.path().read_bytes().decode("utf-8-sig")
            )
        )
    )
    icd_batch_row = next(
        row
        for row in cgu_batch_rows
        if row["合作校"] == "法國ICD商學院 ICD Business School"
    )
    icd_batch_id = icd_batch_row["審查批次"]
    page.goto(f"{live_server.base_url}{icd_batch_row['批次工作台路徑']}")
    summary = page.locator("#destination-profile-review-summary")
    expect(summary).to_contain_text(
        "長庚大學共有 77 筆生活情報",
        timeout=15_000,
    )
    batch_filter = page.locator("#destination-review-batch-filter")
    expect(batch_filter).to_contain_text(
        f"目前從生活情報分工清單定位：{icd_batch_id}"
    )
    expect(page.locator("[data-destination-profile-hash]")).to_have_count(10)

    page.locator("#destination-review-readiness-filter").select_option(
        "approval_ready"
    )
    page.locator("#destination-review-search").fill("ICD Business School")
    card = page.locator("[data-destination-school-name*='ICD Business School']")
    expect(card).to_be_visible()
    card.locator(".destination-review-detail > summary").click()
    ready_gate = card.locator("[data-destination-review-approval-gate]")
    expect(ready_gate).to_contain_text("目前具備可選擇核可的資料門檻")
    ready_decision = card.locator("[data-destination-review-decision]")
    expect(ready_decision).to_have_value("approve")
    assert (
        ready_decision.locator('option[value="approve"]').get_attribute("disabled")
        is None
    )
    source_checks = card.locator("[data-destination-review-source]")
    section_checks = card.locator("[data-destination-review-section]")
    assert source_checks.count() == 5
    assert section_checks.count() == 12
    for index in range(source_checks.count()):
        source_checks.nth(index).check()
    for index in range(section_checks.count()):
        section_checks.nth(index).check()
    card.locator("[data-destination-review-note]").fill(
        "已逐頁核對 Paris 與 Toulouse 校區、住宿、費用與五個官方來源。"
    )
    card.locator("[data-destination-review-submit]").click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "獨立審查證據已保存"
    )
    expect(summary).to_contain_text("目前 1 筆已有真人證據")
    refreshed_card = page.locator(
        "[data-destination-school-name*='ICD Business School']"
    )
    expect(refreshed_card).to_contain_text("已完成一位，等待第二位")
    expect(refreshed_card).to_contain_text("有效核可 1／2")
    expect(
        refreshed_card.locator("[data-destination-review-draft-clear]")
    ).to_be_hidden()
    expect(
        refreshed_card.locator("[data-destination-review-draft-status]")
    ).to_contain_text("尚未建立本頁暫存")

    public_after_first_review = requests.get(
        f"{live_server.base_url}/destination-profiles",
        params={"home_school": "長庚大學"},
        timeout=15,
    )
    public_after_first_review.raise_for_status()
    assert public_after_first_review.json() == public_before.json()

    second_queue = requests.get(
        f"{live_server.base_url}/admin/destination-profile-review-queue",
        headers=second_reviewer_headers,
        params={"home_university": "長庚大學"},
        timeout=15,
    )
    second_queue.raise_for_status()
    second_queue_payload = second_queue.json()
    second_icd = next(
        row
        for row in second_queue_payload["items"]
        if row["school_name"] == "法國ICD商學院 ICD Business School"
    )
    second_review = requests.post(
        f"{live_server.base_url}/admin/destination-profile-reviews",
        headers=second_reviewer_headers,
        json={
            "home_university": second_icd["home_university"],
            "school_name": second_icd["school_name"],
            "expected_snapshot": second_queue_payload["snapshot_fingerprint"],
            "expected_profile_content_hash": second_icd["profile_content_hash"],
            "decision": "approve",
            "note": "已獨立核對兩個校區、住宿費用界線與全部五個官方來源。",
            "reviewed_source_urls": second_icd["source_urls"],
            "reviewed_section_keys": [
                section["key"]
                for section in second_queue_payload["review_sections"]
            ],
        },
        timeout=15,
    )
    second_review.raise_for_status()

    page.reload()
    # The public count changes only after the explicit promotion below, so the
    # summary remains 19/58 until the current reviewer confirms that action.
    expect(summary).to_contain_text(
        "19 筆完整查核、58 筆待人工續審",
        timeout=15_000,
    )
    expect(batch_filter).to_contain_text(
        f"目前從生活情報分工清單定位：{icd_batch_id}"
    )
    workbench = page.locator("#destination-profile-review-workbench")
    if workbench.get_attribute("open") is None:
        workbench.locator(":scope > summary").click()
    page.locator("#destination-review-search").fill("ICD Business School")
    promotable_card = page.locator(
        "[data-destination-school-name*='ICD Business School']"
    )
    expect(promotable_card).to_contain_text("兩位已完成")
    promotable_card.locator(".destination-review-detail > summary").click()
    expect(promotable_card.locator(".destination-promotion-panel")).to_be_visible()
    promotable_card.locator("[data-destination-promotion-note]").fill(
        "確認兩位真人的獨立核可完整，升級目前鎖定的生活情報版本。"
    )
    promotable_card.locator("[data-destination-promotion-confirm]").check()
    promotable_card.locator("[data-destination-promotion-submit]").click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "已依兩位真人核可證據升級為完整查核"
    )
    expect(page.locator("#review-announcement")).to_contain_text(
        "原生活情報批次因內容指紋或待審成員改變而過期"
    )
    expect(batch_filter).to_contain_text("這份生活情報分工批次已過期")
    expect(
        page.locator("#download-destination-review-batch-checklist")
    ).to_be_hidden()
    assert parse_qs(urlparse(page.url).query)["destination_batch"] == [
        icd_batch_id
    ]
    expect(summary).to_contain_text("20 筆完整查核、57 筆待人工續審")
    expect(promotable_card).to_have_count(0)

    page.locator("#clear-destination-review-batch").click()
    expect(batch_filter).to_be_hidden()
    assert "destination_batch" not in page.url

    public_after_promotion = requests.get(
        f"{live_server.base_url}/destination-profiles",
        params={"home_school": "長庚大學"},
        timeout=15,
    )
    public_after_promotion.raise_for_status()
    promoted_icd = next(
        row
        for row in public_after_promotion.json()
        if row["school_name"] == "法國ICD商學院 ICD Business School"
    )
    assert promoted_icd["coverage_status"] == "official_verified"
    assert "兩位不同內容審查者" in promoted_icd["coverage_note"]

    publication_history = page.locator("#destination-publication-history")
    publication_history.locator(":scope > summary").click()
    publication_summary = page.locator("#destination-publication-history-summary")
    expect(publication_summary).to_contain_text("1 筆生活情報曾執行升級")
    expect(publication_summary).to_contain_text("目前 1 筆使用已核准公開版本")
    expect(publication_summary).to_contain_text("1 筆升級與 0 筆復原事件")
    publication_card = page.locator(
        "[data-publication-school-name*='ICD Business School']"
    )
    expect(publication_card).to_contain_text("目前使用直接升級版本")
    publication_card.locator("[data-destination-rollback-note]").fill(
        "發現這次升級需要撤回複查，立即回到升級前的安全公開快照。"
    )
    publication_card.locator("[data-destination-rollback-confirm]").check()
    publication_card.locator("[data-destination-rollback-submit]").click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "已復原到上一個公開快照"
    )
    expect(summary).to_contain_text("19 筆完整查核、58 筆待人工續審")
    expect(publication_summary).to_contain_text("目前 0 筆使用已核准公開版本")
    expect(publication_summary).to_contain_text("1 筆升級與 1 筆復原事件")
    restored_card = page.locator(
        "[data-publication-school-name*='ICD Business School']"
    )
    expect(restored_card).to_contain_text("目前為已復原版本")
    expect(restored_card.locator("[data-destination-rollback-submit]")).to_have_count(0)

    page.locator("#destination-review-search").fill("ICD Business School")
    re_review_card = page.locator(
        "[data-destination-school-name*='ICD Business School']"
    )
    expect(re_review_card).to_contain_text("尚未開始")
    expect(re_review_card).to_contain_text("有效核可 0／2")

    public_after_rollback = requests.get(
        f"{live_server.base_url}/destination-profiles",
        params={"home_school": "長庚大學"},
        timeout=15,
    )
    public_after_rollback.raise_for_status()
    restored_icd = next(
        row
        for row in public_after_rollback.json()
        if row["school_name"] == "法國ICD商學院 ICD Business School"
    )
    assert restored_icd["coverage_status"] == "official_partial"


@pytest.mark.skip(reason="Phase C")
def test_content_admin_replaces_insecure_source_only_in_pending_revision(
    page: Page,
    live_server: LiveServer,
    monkeypatch,
) -> None:
    reviewer_email = _email("source-replacement-reviewer")
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", reviewer_email)
    reviewer = live_server.register(reviewer_email, "來源修正審查者")
    headers = _auth_headers(reviewer)

    backlog = requests.get(
        f"{live_server.base_url}/admin/application-workflow-review-backlog",
        headers=headers,
        timeout=15,
    )
    backlog.raise_for_status()
    backlog_payload = backlog.json()
    candidate_workflow_count = backlog_payload[
        "workflows_with_source_replacement_candidates"
    ]
    candidate_count = backlog_payload["source_replacement_candidate_count"]
    transport_blocked_count = backlog_payload[
        "transport_blocked_source_replacement_candidate_count"
    ]
    assert candidate_workflow_count == len(
        [
            row
            for row in backlog_payload["items"]
            if row["source_replacement_candidate_count"] > 0
        ]
    )
    assert candidate_count == sum(
        row["source_replacement_candidate_count"]
        for row in backlog_payload["items"]
    )
    assert candidate_workflow_count > 0
    assert candidate_count >= candidate_workflow_count
    assert transport_blocked_count == 2
    target = next(
        row
        for row in backlog_payload["items"]
        if (
            not row["has_pending_revision"]
            and row["insecure_source_count"] == 1
            and row["source_replacement_candidate_count"] > 0
            and row["transport_blocked_source_replacement_candidate_count"] == 0
            and row["school_name"] == "梨花女子大學"
        )
    )
    blocked_target = next(
        row
        for row in backlog_payload["items"]
        if (
            not row["has_pending_revision"]
            and row["transport_blocked_source_replacement_candidate_count"] > 0
        )
    )

    login_through_web(page, live_server, reviewer_email)
    page.goto(f"{live_server.base_url}/admin/content-review")
    expect(page.locator("#reviewer-email")).to_have_text(reviewer_email)
    candidate_summary = page.locator("#source-replacement-candidate-summary")
    expect(candidate_summary).to_be_visible(timeout=15_000)
    expect(candidate_summary).to_contain_text(
        f"目前 {candidate_workflow_count} 筆流程共有 {candidate_count} 個研究候選"
    )
    expect(candidate_summary).to_contain_text(
        f"傳輸阻擋 {transport_blocked_count}"
    )
    with page.expect_download() as candidate_download_info:
        candidate_summary.locator(
            "#download-source-replacement-candidates"
        ).click()
    candidate_download = candidate_download_info.value
    assert candidate_download.suggested_filename.startswith(
        "source-replacement-review-"
    )
    candidate_rows = list(
        csv.DictReader(
            StringIO(
                candidate_download.path().read_bytes().decode("utf-8-sig")
            )
        )
    )
    assert len(candidate_rows) == candidate_count
    assert len({row["workflow_key"] for row in candidate_rows}) == (
        candidate_workflow_count
    )
    assert all(row["人工檢查事項"] for row in candidate_rows)
    assert sum(row["傳輸安全狀態"] == "會轉回 HTTP" for row in candidate_rows) == 2
    assert sum(row["可填入待審欄位"] == "否" for row in candidate_rows) == 2
    assert all(row["審查者 A"] == "" for row in candidate_rows)
    assert all(row["審查者 B"] == "" for row in candidate_rows)
    assert all(row["自動核准"] == "否" for row in candidate_rows)
    assert all(row["學生資料已變更"] == "否" for row in candidate_rows)
    candidate_summary.locator("#filter-source-replacement-candidates").click()
    expect(page.locator("#review-count")).to_have_text(
        str(candidate_workflow_count)
    )
    expect(page.locator("[data-workflow-key]")).to_have_count(
        candidate_workflow_count
    )
    expect(
        page.locator(f'[data-workflow-key="{target["workflow_key"]}"]')
    ).to_contain_text("已研究來源候選")

    staged = requests.post(
        f"{live_server.base_url}/admin/application-workflow-review-backlog/{target['workflow_key']}/stage",
        headers=headers,
        timeout=15,
    )
    staged.raise_for_status()
    revision = staged.json()
    revision_id = revision["id"]
    old_url = next(
        source["source_url"]
        for source in revision["workflow"]["sources"]
        if source["source_url"].casefold().startswith("http://")
    )
    candidates = requests.get(
        f"{live_server.base_url}/admin/application-workflow-source-replacement-candidates",
        headers=headers,
        timeout=15,
    )
    candidates.raise_for_status()
    candidate = next(
        row
        for row in candidates.json()
        if row["revision_id"] == revision_id and row["current_url"] == old_url
    )
    assert candidate["transport_status"] == "verified_https"
    assert candidate["can_prefill"] is True
    replacement_url = candidate["candidate_url"]
    public_before = requests.get(
        f"{live_server.base_url}/application-workflow",
        params={
            "school": target["school_name"],
            "home_school": target["home_university"],
        },
        timeout=15,
    )
    public_before.raise_for_status()
    public_before_payload = public_before.json()
    assert old_url in json.dumps(public_before_payload, ensure_ascii=False)

    page.goto(f"{live_server.base_url}/admin/content-review")
    expect(page.locator("#reviewer-email")).to_have_text(reviewer_email)
    page.locator("#review-status-filter").select_option("pending_review")
    card = page.locator(f'[data-revision-id="{revision_id}"]')
    expect(card).to_be_visible(timeout=15_000)
    expect(card.locator(".rule-source-blocker")).to_contain_text("非 HTTPS 來源")
    insecure_source_checkbox = card.locator(
        f'[data-approval-source][data-source-url="{old_url}"]'
    )
    expect(insecure_source_checkbox).to_be_disabled()
    expect(card.locator('[data-review-action="approve"]')).to_be_disabled()

    card.locator(".applicability-editor > summary").click()
    source_rows = card.locator("[data-applicability-source-row]")
    source_row_index = source_rows.evaluate_all(
        "(rows, url) => rows.findIndex((row) => row.dataset.sourceUrl === url)",
        old_url,
    )
    assert source_row_index >= 0
    source_row = source_rows.nth(source_row_index)
    candidate_panel = source_row.locator(".source-replacement-candidate")
    expect(candidate_panel).to_contain_text("人工審核候選")
    expect(candidate_panel).to_contain_text("人工必查")
    expect(candidate_panel.locator(f'a[href="{replacement_url}"]').first).to_be_visible()
    expect(source_row.locator("[data-applicability-source]")).not_to_be_checked()
    candidate_panel.locator("[data-apply-source-replacement-candidate]").click()
    expect(source_row.locator("[data-source-replacement-url]")).to_have_value(
        replacement_url
    )
    expect(source_row.locator("[data-applicability-source]")).not_to_be_checked()
    unsaved = requests.get(
        f"{live_server.base_url}/admin/application-workflow-revisions",
        params={"status": "pending_review"},
        headers=headers,
        timeout=15,
    )
    unsaved.raise_for_status()
    unsaved_revision = next(
        row for row in unsaved.json() if row["id"] == revision_id
    )
    assert replacement_url not in json.dumps(
        unsaved_revision["workflow"], ensure_ascii=False
    )
    card.locator("[data-applicability-academic-year]").fill(
        target["academic_year"] or "115"
    )
    source_row.locator("[data-applicability-source]").check()
    source_row.locator("[data-source-academic-year]").fill(
        target["academic_year"] or "115"
    )
    card.locator("[data-applicability-note]").fill(
        "E2E 僅驗證待審版安全網址替換與引用同步，不代表真人內容核准。"
    )
    expect(card.locator("[data-applicability-progress]")).to_contain_text(
        "可儲存本次逐頁補正；未勾選來源保持不變"
    )
    applicability_save = card.locator("[data-review-applicability-save]")
    expect(applicability_save).to_be_enabled()
    applicability_save.click()
    expect(page.locator("#review-announcement")).to_contain_text(
        "待審修正已保存",
        timeout=15_000,
    )

    updated_card = page.locator(f'[data-revision-id="{revision_id}"]')
    expect(updated_card.locator(f'a[href="{replacement_url}"]').first).to_be_visible()
    expect(updated_card.locator(".rule-source-blocker")).to_have_count(0)
    pending = requests.get(
        f"{live_server.base_url}/admin/application-workflow-revisions",
        params={"status": "pending_review"},
        headers=headers,
        timeout=15,
    )
    pending.raise_for_status()
    updated = next(row for row in pending.json() if row["id"] == revision_id)
    workflow_json = json.dumps(updated["workflow"], ensure_ascii=False)
    assert replacement_url in workflow_json
    assert old_url not in workflow_json
    assert updated["review_approvals"] == []

    candidate_backlog = requests.get(
        f"{live_server.base_url}/admin/application-workflow-review-backlog",
        headers=headers,
        timeout=15,
    )
    candidate_backlog.raise_for_status()
    candidate_item = next(
        row
        for row in candidate_backlog.json()["items"]
        if row["workflow_key"] == target["workflow_key"]
    )
    assert candidate_item["insecure_source_count"] == 0
    assert candidate_item["version"] == updated["workflow"]["version"]
    assert candidate_item["review_approval_count"] == 0
    public_after = requests.get(
        f"{live_server.base_url}/application-workflow",
        params={
            "school": target["school_name"],
            "home_school": target["home_university"],
        },
        timeout=15,
    )
    public_after.raise_for_status()
    assert public_after.json() == public_before_payload
    public_after_json = json.dumps(public_after.json(), ensure_ascii=False)
    assert old_url in public_after_json
    assert replacement_url not in public_after_json

    blocked_staged = requests.post(
        f"{live_server.base_url}/admin/application-workflow-review-backlog/{blocked_target['workflow_key']}/stage",
        headers=headers,
        timeout=15,
    )
    blocked_staged.raise_for_status()
    blocked_revision = blocked_staged.json()
    blocked_candidates = requests.get(
        f"{live_server.base_url}/admin/application-workflow-source-replacement-candidates",
        headers=headers,
        timeout=15,
    )
    blocked_candidates.raise_for_status()
    blocked_candidate = next(
        row
        for row in blocked_candidates.json()
        if (
            row["revision_id"] == blocked_revision["id"]
            and row["can_prefill"] is False
        )
    )
    assert blocked_candidate["transport_status"] == "downgrades_to_http"
    assert blocked_candidate["transport_final_url"].startswith("http://")
    assert blocked_candidate["research_leads"]
    assert all(
        lead["eligible_as_replacement"] is False
        for lead in blocked_candidate["research_leads"]
    )

    page.goto(f"{live_server.base_url}/admin/content-review")
    page.locator("#review-status-filter").select_option("pending_review")
    blocked_card = page.locator(
        f'[data-revision-id="{blocked_revision["id"]}"]'
    )
    expect(blocked_card).to_be_visible(timeout=15_000)
    blocked_card.locator(".applicability-editor > summary").click()
    blocked_source_rows = blocked_card.locator("[data-applicability-source-row]")
    blocked_source_row_index = blocked_source_rows.evaluate_all(
        "(rows, url) => rows.findIndex((row) => row.dataset.sourceUrl === url)",
        blocked_candidate["current_url"],
    )
    assert blocked_source_row_index >= 0
    blocked_source_row = blocked_source_rows.nth(blocked_source_row_index)
    blocked_panel = blocked_source_row.locator(".source-replacement-candidate")
    expect(blocked_panel).to_contain_text("會轉回 HTTP")
    expect(blocked_panel.locator(".source-candidate-research-leads")).to_contain_text(
        "安全研究線索（不可直接替代）"
    )
    research_lead_rows = blocked_panel.locator(".source-candidate-research-lead")
    expect(research_lead_rows).to_have_count(len(blocked_candidate["research_leads"]))
    for index in range(len(blocked_candidate["research_leads"])):
        expect(research_lead_rows.nth(index)).to_contain_text("不可直接替代")
    blocked_apply = blocked_panel.locator(
        "[data-apply-source-replacement-candidate]"
    )
    expect(blocked_apply).to_be_disabled()
    expect(blocked_apply).to_have_text("傳輸安全未通過，禁止填入")
    expect(blocked_source_row.locator("[data-source-replacement-url]")).to_have_value("")
