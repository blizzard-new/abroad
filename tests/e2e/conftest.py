from __future__ import annotations

import shutil
import hashlib
import json
import os
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import pytest
import requests
import uvicorn
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from exchange_info.api import create_app
from exchange_info.models import AccountNotification, PartnerUniversity, ProcessedPage, PageCategory
from exchange_info.repositories import JsonlAccountRepository
from exchange_info.storage import ensure_data_dirs, load_processed_pages, save_processed_pages


PUBLIC_DATA_FILES = (
    "application_workflows.jsonl",
    "collection_audits.jsonl",
    "exchange_info.json",
    "pages.jsonl",
    "structured_sources.jsonl",
)


@dataclass(frozen=True)
class LiveServer:
    base_url: str
    data_dir: Path

    def register(self, email: str, display_name: str = "E2E 測試學生") -> dict:
        dispatched = requests.post(
            f"{self.base_url}/auth/email-verification/request",
            json={"email": email},
            timeout=10,
        )
        dispatched.raise_for_status()
        code = dispatched.json()["development_code"]
        confirmed = requests.post(
            f"{self.base_url}/auth/email-verification/confirm",
            json={"email": email, "code": code},
            timeout=10,
        )
        confirmed.raise_for_status()
        registered = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "email": email,
                "password": "CodexE2E!2026",
                "display_name": display_name,
                "email_verification_token": confirmed.json()["verification_token"],
                "accept_terms": True,
            },
            timeout=10,
        )
        registered.raise_for_status()
        return registered.json()

    def verify_student(
        self,
        account_id: str,
        *,
        university: str = "長庚大學",
        department: str = "資訊工程學系",
    ) -> None:
        repository = JsonlAccountRepository(self.data_dir)
        account = repository.find_account_by_id(account_id)
        assert account is not None
        repository.save_account(
            account.model_copy(
                update={
                    "student_status_verified": True,
                    "verified_university": university,
                    "verified_department": department,
                    "school_email_verified": True,
                }
            )
        )

    def add_notification(self, account_id: str, *, title: str) -> None:
        JsonlAccountRepository(self.data_dir).save_notification(
            AccountNotification(
                account_id=account_id,
                dedupe_key=f"e2e:{account_id}:{title}",
                channels=["web"],
                title=title,
                body="這是一則只寫入隔離測試資料夾的站內通知。",
                action_url="#deadlines",
                source_key="e2e-deadline",
            )
        )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _copy_public_fixture_data(target: Path) -> None:
    source = Path(__file__).resolve().parents[2] / "data" / "processed"
    processed = target / "processed"
    for name in PUBLIC_DATA_FILES:
        source_file = source / name
        if source_file.exists():
            shutil.copy2(source_file, processed / name)


@pytest.fixture(scope="module")
def live_server(tmp_path_factory) -> LiveServer:
    import exchange_info.api as api_module
    import exchange_info.student_view as student_view_module

    data_dir = tmp_path_factory.mktemp("web-e2e-data")
    ensure_data_dirs(data_dir)
    _copy_public_fixture_data(data_dir)
    # Real official document source, confined to synthetic E2E data. The normal
    # checkout has no processed CGU pages; synchronization needs a document ID.
    document_fixture = json.loads((Path(__file__).resolve().parents[1] / "fixtures" /
                                  "cgu-document-readiness-2026-10-09.json").read_text())
    save_processed_pages([*load_processed_pages(data_dir), ProcessedPage(
        title=document_fixture["title"], source_url=document_fixture["source_url"],
        text=document_fixture["text"], summary=document_fixture["scope"],
        category=PageCategory.EXCHANGE_APPLICATION,
        content_hash=hashlib.sha256(document_fixture["text"].encode()).hexdigest(),
    )], data_dir)
    partners = [
        PartnerUniversity(
            program_type="交換學生",
            country="紐西蘭",
            school_name="林肯大學 Lincoln University",
            website="https://www.lincoln.ac.nz/",
            colleges="四院皆可",
            degree_levels="大學部、研究所",
            study_period="1 學期",
            quota="2",
            eligibility="IELTS 6.0；須先通過校內甄選。",
            application_deadline="第一學期：9 月 30 日；第二學期：3 月 30 日",
            application_info="由本校提名後依合作校通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生",
            country="日本",
            school_name="明治大學 Meiji University",
            website="https://www.meiji.ac.jp/",
            colleges="商管、人文",
            degree_levels="大學部",
            study_period="1 學期",
            quota="2",
            eligibility="依當期公告確認語言條件。",
            application_deadline="待合作校公告",
            application_info="由本校提名。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生",
            country="馬來西亞",
            school_name="馬來西亞馬來亞大學 Universiti Malaya",
            website="https://www.um.edu.my/",
            colleges="依當期校際協議與合作校課程確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校提名。",
            application_deadline="依當期長庚公告與合作校通知",
            application_info="由本校提名後依合作校通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生",
            country="美國",
            school_name="威斯康辛大學密爾基分校 University of Wisconsin-Milwaukee",
            website="https://uwm.edu/",
            colleges="依當期校際協議與合作校課程確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校提名。",
            application_deadline="依當期長庚公告與合作校通知",
            application_info="由本校提名後依合作校通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533",
        ),
        PartnerUniversity(
            program_type="交換學生",
            country="法國",
            school_name="法國薩克雷大學 University of Paris-Saclay",
            website="https://www.universite-paris-saclay.fr/en",
            colleges="依當期校際協議、錄取學院與校區確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校提名。",
            application_deadline="依當期長庚公告與合作校通知",
            application_info="由本校提名後依合作校通知及錄取學院申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生",
            country="比利時",
            school_name=(
                "比利時托馬斯莫爾應用科技大學 "
                "Thomas More University of Applied Sciences"
            ),
            website="https://thomasmore.be/en",
            colleges="依當期校際協議、交換課程與校區確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校提名。",
            application_deadline="依當期長庚公告與合作校通知",
            application_info="由本校提名後依交換課程與錄取校區申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生",
            country="德國",
            school_name=(
                "德國呂貝克應用科技大學 Technische Hochschule Lübeck"
            ),
            website="https://www.th-luebeck.de/en/",
            colleges="依當期校際協議、課程與授課語言確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校提名。",
            application_deadline="依當期長庚公告與合作校通知",
            application_info="由本校提名後依 TH Lübeck CAMS 通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生",
            country="韓國",
            school_name="韓國江原國立大學 Kangwon National University",
            website="https://admission.kangwon.ac.kr/english/contents.do?key=1407",
            colleges="依當期校際協議、Chuncheon 錄取校區與系所限制確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與 KNU 通知",
            application_info="由本校提名後依 KNU Chuncheon 交換通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生",
            country="法國",
            school_name="歐洲知識經濟與管理學院 Skema Business School",
            website="https://www.skema.edu/en/exchange-students",
            colleges="依當期校際協議、programme 與錄取法國校區確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與 SKEMA 2026–2027 通知",
            application_info="由本校提名後依 SKEMA programme 與錄取校區申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生 / 自費研修",
            country="印度",
            school_name="印度昌迪加爾大學 Chandigarh University",
            website="https://www.cuchd.in/international/inbound-exchange.php",
            colleges="依當期校際協議、交換課程與 CU 通知確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與 CU incoming 通知",
            application_info="由本校提名後依 CU 當期交換通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生 / 自費研修",
            country="捷克",
            school_name=(
                "捷克布拉格紐約大學 University of New York in Prague (UNYP)"
            ),
            website="https://www.unyp.cz/inbound-exchange-student-information/",
            colleges="依當期 exchange agreement、課程與長庚提名確認",
            degree_levels="大學部",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與 UNYP exchange 通知",
            application_info="由本校提名後依 UNYP 當期交換通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生 / 自費研修",
            country="法國",
            school_name="法國EPF工程師學校 EPF École d'ingénieurs",
            website="https://www.epf.fr/en/exchange-students-0",
            colleges="依當期校際協議、錄取課程、授課語言與校區確認",
            degree_levels="大學部、研究所",
            study_period="1 學期",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與 EPF exchange 通知",
            application_info="由本校提名後依 EPF 當期交換通知與錄取校區申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生",
            country="法國",
            school_name="雷恩商學院 Rennes School of Business",
            website=(
                "https://www.rennes-sb.com/exchange-programmes/"
                "incoming-exchange-students/"
            ),
            colleges="依當期校際協議、課程 Level、授課學期與錄取校區確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與 Rennes SB exchange 通知",
            application_info="由本校提名後依 Rennes SB 當期交換通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生 / 自費研修",
            country="馬來西亞",
            school_name="馬來西亞管理與科技大學 Management and Science University",
            website="https://www.msu.edu.my/brochure/",
            colleges="依當期校際協議、Global Affairs 確認課程與交換身分",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與 MSU Global Affairs 通知",
            application_info="由本校提名後依 MSU 當期交換通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生 / 自費研修",
            country="荷蘭",
            school_name="荷蘭恩荷芬理工大學 Eindhoven University of Technology",
            website="https://www.tue.nl/en/",
            colleges="依當期校際協議、host department 與可選課程確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與 TU/e incoming 通知",
            application_info="由本校提名後依 TU/e 當期系所與交換通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生 / 自費研修",
            country="中國",
            school_name="武漢大學 Wuhan University",
            website="https://www.whu.edu.cn/",
            colleges="依當期校際協議、錄取學院、課程與 campus 確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="依當期公告",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與武漢大學交換通知",
            application_info="由本校提名後依武漢大學當期交換通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="交換學生 / 自費研修",
            country="法國",
            school_name="法國ICD商學院 ICD Business School",
            website="https://www.icd-bs.com/",
            colleges="依當期校際協議、錄取 campus 與可選課程確認",
            degree_levels="大學部、研究所",
            study_period="1 學期至 1 學年",
            quota="每年 4 名一學期交換名額；仍以長庚當期公告為準",
            eligibility="須先通過長庚校內甄選並由本校正式提名。",
            application_deadline="依當期長庚公告與 ICD campus fact sheet 確認",
            application_info="由本校提名後依 ICD 當期 Paris 或 Toulouse 交換通知申請。",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="管理學院交換參考",
            country="法國",
            school_name=(
                "法國艾克斯馬賽大學管理研究所 "
                "IAE Aix-Marseille Graduate School of Management"
            ),
            website=(
                "https://iae-aix.univ-amu.fr/en/profile-and-students-"
                "international/programme-echange-entrant"
            ),
            colleges="管理學院；須先確認當期院級合作與提名資格",
            degree_levels="學士三年級以上、碩士",
            study_period="1 學期至 1 學年",
            quota="依長庚管理學院當期公告",
            eligibility="只接受合作校正式提名；不接受 free mover 或直接申請。",
            application_deadline="依長庚管理學院與 IAE Aix 當期通知",
            application_info="先向長庚管理學院確認當期是否開放，再由母校提名。",
            source_url=(
                "https://www.cgu.edu.tw/Uploads/upload/"
                "f99d6e28-4248-41e5-98f7-5d89d81161e9.pdf"
            ),
            availability_status="departmental_reference",
            availability_note=(
                "目前只作管理學院院級參考；確認當期合作與提名資格前，"
                "不能建立正式申請計畫。"
            ),
        ),
    ]
    original_fetch = api_module.create_cgu_catalogue
    original_student_fetch = student_view_module.fetch_partner_universities
    original_document_fetch = student_view_module.fetch_document_explanations
    from cgu_catalogue_fixture import fixed_cgu_catalogue
    api_module.create_cgu_catalogue = fixed_cgu_catalogue(lambda: partners)
    student_view_module.fetch_partner_universities = lambda: partners
    student_view_module.fetch_document_explanations = lambda **_: []
    app = create_app(data_dir)
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="error",
            access_log=False,
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            if requests.get(f"{base_url}/health", timeout=1).ok:
                break
        except requests.RequestException:
            time.sleep(0.05)
    else:
        server.should_exit = True
        thread.join(timeout=5)
        api_module.create_cgu_catalogue = original_fetch
        student_view_module.fetch_partner_universities = original_student_fetch
        student_view_module.fetch_document_explanations = original_document_fetch
        raise RuntimeError("E2E server did not start in time.")
    try:
        yield LiveServer(base_url=base_url, data_dir=data_dir)
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        api_module.create_cgu_catalogue = original_fetch
        student_view_module.fetch_partner_universities = original_student_fetch
        student_view_module.fetch_document_explanations = original_document_fetch


@pytest.fixture(scope="session")
def playwright_runtime() -> Playwright:
    runtime = sync_playwright().start()
    try:
        yield runtime
    finally:
        runtime.stop()


@pytest.fixture(scope="session")
def browser(playwright_runtime: Playwright) -> Browser:
    executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
    instance = playwright_runtime.chromium.launch(headless=True, **({"executable_path": executable} if executable else {}))
    try:
        yield instance
    finally:
        instance.close()


@pytest.fixture
def page(browser: Browser) -> Page:
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    try:
        yield page
    finally:
        context.close()


def enter_public_site(page: Page, live_server: LiveServer, route: str = "home") -> None:
    page.add_init_script(
        "window.sessionStorage.setItem('exchange-guide-browse-first', '1')"
    )
    page.goto(f"{live_server.base_url}/#{route}")
    page.locator("#school-onboarding").wait_for(state="hidden")
    # The onboarding state settles before the asynchronous Web boot finishes.
    # Let boot-time API calls drain before closing the page or starting login;
    # otherwise rapid destination cases can leave requests queued on the shared
    # E2E server and make a later, unrelated login response time out.
    page.wait_for_load_state("networkidle", timeout=60_000)
    # Rendering the larger offline catalog can continue after network idle.
    # Wait for the real boot overlay to finish before attempting navigation.
    page.locator("#boot-splash").wait_for(state="hidden", timeout=60_000)


def open_partner_filters(page: Page) -> None:
    """On a phone the filter drawer starts closed (a 篩選 pill opens it); open it before using the controls inside."""
    drawer = page.locator("#partners details.pr-facets")
    if drawer.get_attribute("open") is None:
        drawer.locator(":scope > summary").click()


def open_navigation(page: Page) -> None:
    toggle = page.locator("#glass-menu-toggle")
    if toggle.is_visible() and toggle.get_attribute("aria-expanded") == "false":
        toggle.click()
        page.locator("#glass-navigation").wait_for(state="visible")


def login_through_web(page: Page, live_server: LiveServer, email: str) -> None:
    enter_public_site(page, live_server)
    open_navigation(page)
    page.locator(
        "#account-button:visible, "
        "#global-mobile-account-button:visible, "
        "#mobile-account-button:visible"
    ).first.click()
    page.locator("#login-form input[name=email]").fill(email)
    page.locator("#login-form input[name=password]").fill("CodexE2E!2026")
    with page.expect_response(
        lambda response: response.url == f"{live_server.base_url}/auth/login"
        and response.request.method == "POST",
        timeout=60_000,
    ) as login_response_info:
        page.locator("#login-form button[type=submit]").click()
    login_response = login_response_info.value
    assert login_response.ok, (
        f"Web login failed with HTTP {login_response.status}: "
        f"{login_response.text()}"
    )
    page.locator("#auth-dialog").wait_for(state="hidden", timeout=10_000)
    page.wait_for_function("() => !state.homeSchoolLoading && state.accountWorkspaceLoadingCount === 0", timeout=60_000)
    page.evaluate("() => state.periodOptionsReady")
