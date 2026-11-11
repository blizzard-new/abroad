"""CGU edition of the existing UniWay platform, in a dedicated demo process."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sys
import tempfile
import threading
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

STATIC = Path(__file__).parent / "static"
CONTENT = Path(__file__).parent / "demo_data/content.json"
COOKIE = "uniway_cgu_demo_session"
HOME = "長庚大學"

HERO_ONEPAGER_HTML = """
<div id="cgu-hero-onepager" class="cgu-hero-onepager" aria-label="長庚 116-1 校內申請重點總覽">
  <div class="cgu-onepager-grid">
    <article class="cgu-onepager-card is-highlight">
      <span class="cgu-onepager-kicker">校內申請期間</span>
      <strong>11/02–12/21 17:00</strong>
      <p>2026/11/02 開放線上表單，12/21 17:00 截止；紙本資料須於截止日前繳交國際事務處（預計 2027 秋季出國）。</p>
    </article>
    <article class="cgu-onepager-card">
      <span class="cgu-onepager-kicker">校內基本門檻</span>
      <strong>學業平均 70 分、多益 700</strong>
      <p>英文可採多益 700、IELTS 5.5、TOEFL iBT 72 或 Duolingo 105 等同級檢定；合作校門檻更高或未列多益者依該校規定。</p>
    </article>
    <article class="cgu-onepager-card">
      <span class="cgu-onepager-kicker">志願數與甄選流程</span>
      <strong>最多 2 個志願</strong>
      <div class="cgu-flow-steps" aria-label="申請流程">
        <span>校內甄選</span><i aria-hidden="true">→</i><span>學校提名</span><i aria-hidden="true">→</i><span>合作校申請</span>
      </div>
    </article>
    <article class="cgu-onepager-card is-wide">
      <span class="cgu-onepager-kicker">校內應備 5 份文件</span>
      <ol class="cgu-doc-pills">
        <li><b>1</b>線上申請表</li>
        <li><b>2</b>家長同意書</li>
        <li><b>3</b>語文證明</li>
        <li><b>4</b>含班級排名的中文成績單</li>
        <li><b>5</b>1 頁讀書計畫</li>
      </ol>
    </article>
  </div>
  <div class="cgu-onepager-foot">
    <div class="cgu-onepager-sources">
      <span>官方來源：</span>
      <a href="https://www.cgu.edu.tw/oia-ch/Subject/Detail/85785?nodeId=15817" target="_blank" rel="noopener noreferrer">116-1 交換及雙聯申請公告 ↗</a>
      <span aria-hidden="true">·</span>
      <a href="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656" target="_blank" rel="noopener noreferrer">校內申請選送須知 ↗</a>
      <small>查核日期：2026-11-11</small>
    </div>
    <div class="cgu-onepager-actions">
      <button type="button" class="cgu-hero-cta is-primary" data-cgu-scroll="#cgu-dept-finder">我是哪個系？（36 系所）</button>
      <a class="cgu-hero-cta" href="#partners">搜尋 78 所合作校</a>
      <button type="button" class="cgu-hero-cta" data-cgu-scroll="#cgu-navigator-card">領航者補助說明</button>
    </div>
  </div>
</div>
"""


def public_origin(value: str) -> str:
    """A configured HTTPS origin, never inferred from forwarded request headers."""
    value = value.strip().rstrip('/')
    if not value:
        return ''
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment or parsed.port not in (None, 443)):
        raise ValueError('CGU_DEMO_PUBLIC_ORIGIN must be an HTTPS origin without a path or credentials')
    host = parsed.hostname.lower()
    return 'https://' + ('[' + host + ']' if ':' in host else host)


def platform_html() -> str:
    """Keep the platform DOM and asset order; only constrain school/identity copy."""
    soup = BeautifulSoup((STATIC / "index.html").read_text(encoding="utf-8"), "html.parser")
    soup.title.string = "UniWay CGU｜長庚大學交換申請平台"
    soup.head.append(soup.new_tag("meta", attrs={"name": "robots", "content": "noindex,nofollow,noarchive"}))
    soup.head.append(soup.new_tag("link", rel="stylesheet", href="/static/cgu-demo.css?v=20261112-cgu-ux-2"))
    script = soup.new_tag("script", src="/demo/bootstrap.js")
    soup.head.insert(0, script)
    # Initial static choices must also be CGU-only, before the registry request resolves.
    for item in soup.select('[data-home-school]'):
        if item.get('data-home-school') != HOME:
            item.decompose()
    for item in soup.select('.pr-supported'):
        item.decompose()
    hero_title = soup.select_one('#home-landing-title')
    if hero_title is not None:
        hero_title.clear()
        hero_title.append('長庚 116-1 申請一頁看完')
        hero_title.append(soup.new_tag('br'))
        sub = soup.new_tag('span')
        sub.string = '2027 秋季出國 · 交換與雙學位校內甄選重點'
        hero_title.append(sub)
        banner = soup.new_tag('div', id='cgu-home-deadline-banner', attrs={'class': 'cgu-home-deadline-banner', 'hidden': ''})
        hero_title.insert_after(banner)
        onepager = BeautifulSoup(HERO_ONEPAGER_HTML, 'html.parser')
        banner.insert_after(onepager)
    hero_section = soup.select_one('#home-landing .pr-hero')
    if hero_section is not None:
        navigator_sec = soup.new_tag(
            'section',
            id='cgu-navigator-card',
            attrs={'class': 'pr-section cgu-navigator-section', 'aria-labelledby': 'cgu-navigator-title'},
        )
        dept_sec = soup.new_tag(
            'section',
            id='cgu-dept-finder',
            attrs={'class': 'pr-section cgu-dept-section', 'aria-labelledby': 'cgu-dept-title'},
        )
        hero_section.insert_after(navigator_sec)
        hero_section.insert_after(dept_sec)
    partners_head = soup.select_one('#partners .pr-explore-head')
    if partners_head is not None:
        mgmt_notice = soup.new_tag(
            'div',
            id='cgu-mgmt-channel-notice',
            attrs={'class': 'cgu-mgmt-notice', 'role': 'status', 'hidden': ''},
        )
        college_bar = soup.new_tag(
            'div',
            id='cgu-college-quick-bar',
            attrs={'class': 'cgu-college-bar', 'role': 'region', 'aria-label': '長庚學院快速篩選'},
        )
        program_tabs = soup.new_tag(
            'div',
            id='cgu-program-tabs',
            attrs={'class': 'cgu-program-tabs', 'role': 'tablist', 'aria-label': '交換與雙學位計畫分頁'},
        )
        partners_head.insert_after(mgmt_notice)
        partners_head.insert_after(college_bar)
        partners_head.insert_after(program_tabs)
    scholarship_summary = soup.select_one('#scholarship-match-summary')
    if scholarship_summary is not None:
        inline_nav = soup.new_tag('div', id='cgu-scholarships-navigator-card', attrs={'class': 'cgu-navigator-inline'})
        scholarship_summary.insert_before(inline_nav)
    for legend in soup.select('.application-preference-fields legend'):
        legend.string = '準備志願序（最多兩所；依長庚官方規定）'
    for selector in (
        '#eligibility-preference-3', '#eligibility-preference-4', '#eligibility-preference-5',
        '#multi-plan-preferences select[name="preference_3"]',
        '#multi-plan-preferences select[name="preference_4"]',
        '#multi-plan-preferences select[name="preference_5"]',
    ):
        for field in soup.select(selector):
            parent_label = field.find_parent('label')
            if parent_label is not None:
                parent_label['hidden'] = ''
    term_labels = {
        '2027-spring': '2027 春季（115-2）',
        '2027-fall': '2027 秋季（116-1）',
        '2028-spring': '2028 春季（116-2）',
        '2028-fall': '2028 秋季（117-1）',
    }
    for value, text in term_labels.items():
        for opt in soup.select(f'#advisor-target-term option[value="{value}"]'):
            opt.string = text
    for opt in soup.select('#partner-term-tile option[value="fall"], #discovery-criteria-form select[name="term"] option[value="fall"]'):
        opt.string = '2027 秋季（116-1）'
    for opt in soup.select('#partner-term-tile option[value="spring"], #discovery-criteria-form select[name="term"] option[value="spring"]'):
        opt.string = '2027 春季（115-2）'
    for item in soup.select('.uniway-header-brand strong'):
        item.string = 'UniWay CGU'
    for item in soup.select('#school-switcher'):
        item['disabled'] = ''
        item['aria-label'] = '長庚大學專屬平台'
    for item in soup.select('#logout-button, #delete-account-button, #calendar-sync-button, #document-tab-vault, input[type=file]'):
        item['disabled'] = ''
        item['title'] = '展示未開放正式登入、私人文件或外部同步'
    for item in soup.select('[data-home-pick-school]'):
        item['disabled'] = ''
        item['title'] = '長庚大學專屬平台'
    snippet = BeautifulSoup('''<aside id="cgu-demo-strip" aria-label="長庚展示控制">
      <span>長庚專屬展示・虛構學生林小程（生物醫學工程學系 大三・多益 750）・重啟後清除・尚未與校方串接</span>
      <button type="button" id="cgu-demo-info">來源與展示說明</button>
      <button type="button" id="cgu-demo-seed">載入示範申請</button>
      <button type="button" id="cgu-demo-reset">重設我的展示資料</button>
      </aside><dialog id="cgu-demo-dialog" aria-label="長庚專屬展示" aria-labelledby="cgu-demo-dialog-title">
      <h2 id="cgu-demo-dialog-title">長庚專屬展示</h2><div id="cgu-demo-dialog-body"></div>
      <p id="cgu-demo-status" role="status"></p><div class="button-row">
      <button type="button" class="primary-button" id="cgu-demo-confirm" hidden>確認重設</button>
      <button type="button" class="secondary-button" id="cgu-demo-close">關閉</button></div></dialog>''', 'html.parser')
    soup.body.append(snippet)
    soup.body.append(soup.new_tag('script', src='/static/cgu-demo.js?v=20261112-cgu-ux-2', defer=''))
    return str(soup)


def create_demo_app() -> FastAPI:
    # The shared module constructs its app on import. Prepare a disposable runtime
    # BEFORE importing it, and refuse use in an already-running normal API process.
    if 'exchange_info.api' in sys.modules:
        raise RuntimeError('CGU demo must run in a separate process; do not mount it in the production app')
    hosted_origin = public_origin(os.environ.get('CGU_DEMO_PUBLIC_ORIGIN', ''))
    if os.environ.get('EXCHANGE_ENVIRONMENT') == 'production' or any(
        value for name, value in os.environ.items()
        if name.startswith(('SUPABASE', 'GOOGLE_OAUTH', 'SMTP_', 'OPENAI_API_KEY'))
    ):
        raise RuntimeError('CGU demo refuses production/service credentials; use an isolated service environment')
    for name in list(os.environ):
        if name.startswith('EXCHANGE_'):
            del os.environ[name]
    runtime = tempfile.TemporaryDirectory(prefix='uniway-cgu-demo-')
    os.environ.update(EXCHANGE_INFO_DATA_DIR=runtime.name, EXCHANGE_ENVIRONMENT='development',
                      EXCHANGE_ANALYTICS='off', EXCHANGE_WARM_CACHES='off', EXCHANGE_AUTH_METHODS='email')
    if hosted_origin:
        os.environ['EXCHANGE_PUBLIC_BASE_URL'] = hosted_origin
    from . import api
    from .cgu_demo_content import FrozenCatalogue, journey_levels, source_dashboard
    from .models import (
        AccountApplicationWorkspace,
        AccountSelectionConditions,
        AccountSelectionProfile,
        AccountSessionRecord,
        ApplicationCenterContext,
        ProductAccessTier,
        UserAccount,
        utc_now,
    )

    catalogue = FrozenCatalogue(Path(runtime.name))
    platform = api.create_app(Path(runtime.name), cgu_catalogue_factory=lambda _: catalogue,
                              application_path_levels=journey_levels, fetch_dashboard_documents=False, university_scope=HOME,
                              cgu_dashboard_transform=source_dashboard)
    repository = platform.state.account_repository
    @asynccontextmanager
    async def lifespan(app):
        try:
            async with platform.router.lifespan_context(platform):
                yield
        finally:
            runtime.cleanup()

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.runtime = runtime  # only this process owns and removes this directory
    app.state.platform = platform
    lock = threading.Lock()

    def session(token):
        return repository.authenticate_by_token_hash(hashlib.sha256(token.encode()).hexdigest()) if token else None

    def new_session():
        if len(repository.list_accounts()) >= 500:
            raise HTTPException(503, '展示工作區已滿，請管理者於預演後重啟展示服務。')
        default_workspace = AccountApplicationWorkspace(
            home_school=HOME,
            application_context=ApplicationCenterContext(
                school_name=HOME,
                college='工學院',
                department='生物醫學工程學系',
                degree_level='大學部',
                academic_year='116',
                application_round='第1學期',
                semester='第一學期',
                flags=['subsidy'],
            ),
            selection_conditions=AccountSelectionConditions(
                profile=AccountSelectionProfile(
                    college='工學院',
                    department='生物醫學工程學系',
                    current_year='大三',
                    degree_level='大學部',
                    academic_score=78.0,
                    language_test='toeic',
                    language_score=750.0,
                    target_term='2027-fall',
                    needs_scholarship=True,
                    academic_year='116',
                    application_round='第1學期',
                ),
            ),
        )
        account = UserAccount(
            display_name='林小程（展示資料）',
            home_university=HOME,
            product_tier=ProductAccessTier.SUBSCRIPTION,
            application_workspaces=[default_workspace],
        )
        repository.save_account(account)
        token = secrets.token_urlsafe(40)
        repository.save_session(AccountSessionRecord(account_id=account.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utc_now() + timedelta(hours=24)))
        return token

    def cookie(response, token, request):
        response.set_cookie(COOKIE, token, httponly=True, samesite='strict', secure=bool(hosted_origin) or os.environ.get('CGU_DEMO_SECURE_COOKIE') == '1' or request.url.scheme == 'https',
                            max_age=86400, path='/')

    @app.middleware('http')
    async def isolation(request: Request, call_next):
        path = request.url.path
        token = request.cookies.get(COOKIE, '')
        # Never forward production session, Authorization or anonymous credentials.
        request.scope['headers'] = [(k,v) for k,v in request.scope['headers']
            if k.lower() not in (b'cookie', b'authorization', b'x-anonymous-token')]
        if token:
            request.scope['headers'].append((b'cookie', f'{api.AUTH_COOKIE_NAME}={token}'.encode()))
        request.state.demo_token = token
        query = dict(parse_qsl(request.scope.get('query_string', b'').decode()))
        for key in ('home_school', 'home_university', 'home'):
            if key in query:
                query[key] = HOME
        if path in ('/student-dashboard', '/coverage', '/sources', '/documents', '/exchange-info',
                    '/deadlines', '/verified-window-deadlines', '/calendar/school-window.ics',
                    '/application-center/templates', '/application-center/catalog', '/network-effects/status'):
            query['school'] = HOME
        if path.startswith('/account/application-') or path == '/account/workspace':
            query['home_school'] = HOME
        if path.startswith('/cross-school-partners'):
            query['home'] = HOME
        request.scope['query_string'] = urlencode(query).encode()
        forbidden = path.startswith(('/admin', '/auth/oauth', '/auth/email', '/auth/register', '/auth/login',
            '/auth/student', '/auth/me', '/account/vault', '/calendar/feed', '/analytics', '/feedback',
            '/maintenance', '/docs', '/redoc', '/openapi.json'))
        plan_write = (path == '/account/application-paths' and request.method == 'POST') or (
            re.fullmatch(r'/account/application-paths/[^/]+/(?:profile|archive|workspace|steps/[^/]+)', path) and request.method == 'PUT') or (
            re.fullmatch(r'/account/application-paths/[^/]+/workspace/preview', path) and request.method == 'POST')
        allowed_write = plan_write or (path == '/account/workspace' and request.method == 'PUT') or (
            path.startswith('/account/application-drafts/') and request.method in ('POST','PUT')) or (
            path in ('/application-plan', '/application-plan/evaluate', '/application-plan/schedule', '/advisor/plan',
                     '/application-center/pdf', '/application-center/docx', '/public-translations', '/auth/community-identity') and request.method == 'POST')
        if forbidden or (request.method not in ('GET','HEAD') and not allowed_write and path != '/demo/reset'):
            response = JSONResponse({'detail':'此展示尚未開放正式登入、私人文件、外部同步或送件。'}, status_code=403)
        elif request.method not in ('GET','HEAD') and (
            request.headers.get('origin') != (hosted_origin or str(request.base_url).rstrip('/'))
            or (hosted_origin and (request.url.hostname != urlsplit(hosted_origin).hostname
                                   or request.url.port not in (None, 443)))
        ):
            response = JSONResponse({'detail':'請由此展示網站操作。'}, status_code=403)
        else:
            if allowed_write:
                body = await request.body()
                if len(body) > 256_000:
                    return JSONResponse({'detail':'展示內容過大。'}, status_code=413)
                try:
                    payload = json.loads(body)
                except (ValueError, TypeError):
                    payload = {}
                if isinstance(payload, dict) and payload.get('home_school', HOME) != HOME:
                    return JSONResponse({'detail':'此站僅提供長庚大學情境。'}, status_code=422)
            response = await call_next(request)
        response.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
        response.headers['Cache-Control'] = ('public, max-age=3600' if path.startswith('/static/')
                                             and not path.endswith('.html') else 'no-store')
        for key, value in api._browser_security_headers().items():
            response.headers.setdefault(key, value)
        # The production cookie name never leaves this service.
        response.raw_headers = [(k,v) for k,v in response.raw_headers if not (
            k.lower() == b'set-cookie' and v.startswith(api.AUTH_COOKIE_NAME.encode() + b'='))]
        return response

    @app.get('/')
    @app.get('/cgu')
    def home(request: Request):
        token = request.state.demo_token
        with lock:
            if session(token) is None:
                token = new_session()
        response = HTMLResponse(platform_html())
        cookie(response, token, request)
        return response

    @app.get('/static/index.html')
    def static_home(request: Request):
        return home(request)

    @app.get('/demo/bootstrap.js')
    def bootstrap():
        return Response((STATIC / 'cgu-demo-bootstrap.js').read_text(encoding='utf-8'), media_type='text/javascript')

    @app.get('/demo/content')
    def content():
        return json.loads(CONTENT.read_text(encoding='utf-8'))

    @app.post('/demo/reset')
    def reset(request: Request):
        with lock:
            found = session(request.state.demo_token)
            if found:
                platform.state.form_draft_service.purge_account(found[0].id)
                repository.delete_account(found[0].id)
            token = new_session()
        response = JSONResponse({'reset': True})
        cookie(response, token, request)
        return response

    @app.get('/universities')
    def universities():
        from .models import SupportedUniversity
        from .university_registry import CGU
        return [SupportedUniversity(id='cgu', school_name=HOME, short_name='長庚',
            english_name=CGU.english_name, official_url=CGU.official_url,
            colleges=list(CGU.colleges), hero_image=CGU.hero_image,
            partner_count=len(catalogue.view().partners),
            coverage_note='78 所合作校已與主站同步（含中央當期名單與院級官方參考）；116-1 校內申請至 2026/12/21 17:00。')]

    @app.get('/auth/providers')
    def providers():
        return []

    @app.get('/health')
    def health():
        return {'status':'ok', 'mode':'cgu-demo', 'ui':'shared-uniway-platform', 'persistence':'isolated-temporary-runtime',
                'revision':os.environ.get('CGU_DEMO_REVISION', 'local')}

    @app.get('/robots.txt')
    def robots():
        return Response('User-agent: *\nDisallow: /\n', media_type='text/plain')

    app.mount('/static', StaticFiles(directory=STATIC), name='shared-static')
    app.mount('/', platform)
    return app
