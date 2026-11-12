"""Shared-platform fidelity, synthetic account isolation and conservative CGU data."""
import json
import os
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup
import pytest
import requests

from cgu_demo_fixture import demo_url
from exchange_info.cgu_demo import CONTENT, STATIC, platform_html, public_origin
from exchange_info.cgu_demo_content import FrozenCatalogue


def visitor(url):
    client = requests.Session()
    client.headers['Origin'] = url
    assert client.get(url + '/').ok
    return client


def create(client, url, revision=0):
    response = client.post(url + '/account/application-paths', json=dict(revision=revision,
        home_school='長庚大學', target_school='林肯大學 Lincoln University', academic_year='116',
        departure_year='2027', semester='fall'))
    assert response.status_code == 201, response.text
    return response.json()


def test_exact_shared_assets_and_main_dom():
    original = BeautifulSoup((STATIC / 'index.html').read_text(), 'html.parser')
    demo = BeautifulSoup(platform_html(), 'html.parser')
    for selector, attribute in [('script[src]', 'src'), ('link[rel=stylesheet]', 'href')]:
        before = [node[attribute] for node in original.select(selector)]
        after = [node[attribute] for node in demo.select(selector) if 'cgu-demo' not in node[attribute] and '/demo/' not in node[attribute]]
        assert before == after
    assert [node.get('id') for node in original.select('main')] == [node.get('id') for node in demo.select('main')]
    assert {item['data-home-school'] for item in demo.select('[data-home-school]')} == {'長庚大學'}
    assert demo.select_one('#school-switcher').has_attr('disabled')
    assert original.select_one('.pr-supported') is not None
    assert demo.select_one('.pr-supported') is None
    assert demo.select_one('[data-home-discover]') is not None
    assert demo.select_one('#cgu-home-deadline-banner') is not None
    assert '長庚 116-1 申請一頁看完' in demo.select_one('#home-landing-title').get_text()
    onepager = demo.select_one('#cgu-hero-onepager')
    assert onepager is not None
    onepager_text = onepager.get_text()
    for phrase in (
        '11/02–12/21 17:00',
        '學業平均 70 分、多益 700',
        '線上申請表',
        '家長同意書',
        '語文證明',
        '含班級排名的中文成績單',
        '1 頁讀書計畫',
        '最多 2 個志願',
        '校內甄選',
        '學校提名',
        '合作校申請',
    ):
        assert phrase in onepager_text
    assert demo.select_one('#cgu-dept-finder') is not None
    assert demo.select_one('#cgu-navigator-card') is not None
    assert demo.select_one('#cgu-scholarships-navigator-card') is not None
    assert demo.select_one('#cgu-program-tabs') is not None
    assert demo.select_one('#cgu-mgmt-channel-notice') is not None
    assert demo.select_one('#cgu-college-quick-bar') is not None
    assert '生物醫學工程學系' in demo.select_one('#cgu-demo-strip').get_text()
    assert '多益 750' in demo.select_one('#cgu-demo-strip').get_text()
    pref_legend = demo.select_one('.application-preference-fields legend')
    assert pref_legend is not None and '最多兩所' in pref_legend.text
    assert '最多五所' not in demo.get_text()
    for rank in (3, 4, 5):
        assert demo.select_one(f'#eligibility-preference-{rank}').find_parent('label').has_attr('hidden')
    assert demo.select_one('#advisor-target-term option[value="2027-fall"]').text == '2027 秋季（116-1）'
    assert demo.select_one('#partner-term-tile option[value="fall"]').text == '2027 秋季（116-1）'


@pytest.mark.parametrize('env', [{'EXCHANGE_ENVIRONMENT':'production'}, {'SUPABASE_URL':'https://invalid.test'}, {'OPENAI_API_KEY':'synthetic-invalid'}])
def test_refuses_service_credentials(env):
    clean = {k:v for k,v in os.environ.items() if not k.startswith(('EXCHANGE_', 'SUPABASE', 'GOOGLE_OAUTH', 'SMTP_', 'OPENAI_API_KEY'))}
    result = subprocess.run([sys.executable, '-c', 'from exchange_info.cgu_demo import create_demo_app; create_demo_app()'],
                            env={**clean, **env}, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'refuses production/service credentials' in result.stderr


def test_frozen_catalogue_stays_offline_and_syncs_platform_partners(tmp_path):
    from exchange_info.cgu_catalogue import CguCatalogue
    catalogue = FrozenCatalogue(tmp_path)
    platform = CguCatalogue(tmp_path / 'unused-platform-cache.json').view(refresh=False)
    view = catalogue.view()
    assert len(view.partners) == 78
    assert view.source.current_cycle_verified is False
    assert not (tmp_path / 'unused-demo-cache.json').exists()
    assert [row.model_dump(mode='json') for row in view.partners] == [row.model_dump(mode='json') for row in platform.partners]
    assert any(row.availability_status == 'open' and row.quota and row.application_deadline for row in view.partners)


def test_missing_snapshot_fails_closed(tmp_path):
    from exchange_info.cgu_catalogue import CguCatalogue
    catalogue = FrozenCatalogue(tmp_path)
    catalogue.store = CguCatalogue(tmp_path / 'missing.json', bundled=None)
    assert catalogue.view().partners == []
    assert catalogue.view().source.status == 'unavailable'


def test_sources_are_explicit_and_tasks_do_not_invent_deadlines():
    data = json.loads(CONTENT.read_text())
    assert len(data['stages']) == 6
    sources = {s['id'] for s in data['sources']}
    for stage in data['stages']:
        for task in stage['tasks']:
            assert task.get('source') is None or task['source'] in sources
            assert 'official_deadline_at' not in task


@pytest.mark.parametrize('value', ['http://demo.example.test', 'https://demo.example.test/path',
    'https://user:secret@demo.example.test', 'https://demo.example.test?query=1',
    'https://demo.example.test#fragment', 'https://demo.example.test:444', 'https://'])
def test_public_origin_rejects_unsafe_or_ambiguous_configuration(value):
    with pytest.raises(ValueError):
        public_origin(value)


def test_public_origin_normalizes_https_default_port():
    assert public_origin(' https://DEMO.example.test:443/ ') == 'https://demo.example.test'
    assert public_origin('') == ''


@pytest.mark.parametrize('demo_url', [{'CGU_DEMO_PUBLIC_ORIGIN':'https://demo.example.test'}], indirect=True)
def test_https_proxy_origin_saves_without_trusting_forwarded_headers(demo_url):
    # The browser sends HTTPS to the edge, which forwards plain HTTP and the
    # original Host to the process. Secure cookies are forwarded by the edge.
    client = requests.Session()
    client.headers.update({'Host':'demo.example.test', 'Origin':'https://demo.example.test'})
    home = client.get(demo_url + '/')
    assert home.ok and 'Secure' in home.headers['set-cookie']
    assert 'Domain=' not in home.headers['set-cookie']
    client.headers['Cookie'] = 'uniway_cgu_demo_session=' + client.cookies.get('uniway_cgu_demo_session')
    plan = create(client, demo_url)
    assert len(plan['stages']) == 6
    for headers in [
        {'Origin':'https://elsewhere.test'},
        {'Host':'elsewhere.test'},
        {'Host':'demo.example.test:444'},
        {'Origin':'http://demo.example.test', 'X-Forwarded-Proto':'https'},
        {'Origin':'https://elsewhere.test', 'X-Forwarded-Host':'demo.example.test'},
    ]:
        assert client.post(demo_url + '/demo/reset', headers=headers).status_code == 403
    assert len(client.get(demo_url + '/account/application-paths').json()['items']) == 1
    assert client.post(demo_url + '/demo/reset').ok


def test_isolated_auth_guards_and_shared_assets(demo_url):
    client = visitor(demo_url)
    profile = client.get(demo_url + '/auth/session').json()
    assert profile['display_name'] == '林小程（展示資料）'
    assert not profile.get('email_verified')
    assert 'uniway_cgu_demo_session' in client.cookies
    assert 'exchange_guide_session' not in client.cookies
    assert requests.get(demo_url + '/auth/session', cookies={'exchange_guide_session':'formal-sentinel'}).json() is None
    for path in ['/auth/login', '/account/vault/documents', '/calendar-sync/enable', '/ai/chat', '/community/posts', '/admin/demo', '/account/application-paths/example/workspace/extract']:
        assert client.post(demo_url + path, json={}).status_code == 403
    assert client.post(demo_url + '/demo/reset', headers={'Origin':'https://elsewhere.test'}).status_code == 403
    for name in ['app.js', 'metro.css', 'application-path.js', 'platform-home.js']:
        response = client.get(demo_url + '/static/' + name)
        assert response.content == (STATIC / name).read_bytes()
    response = client.get(demo_url + '/')
    assert 'noindex' in response.headers['x-robots-tag']
    assert 'no-store' in response.headers['cache-control']
    assert 'HttpOnly' in response.headers['set-cookie']
    assert 'Domain=' not in response.headers['set-cookie']


def test_school_scope_dates_and_native_plan_persistence(demo_url):
    alice, bob = visitor(demo_url), visitor(demo_url)
    dashboard = alice.get(demo_url + '/student-dashboard?school=國立臺灣大學').json()
    assert dashboard['school_name'] == '長庚大學'
    assert len(dashboard['partner_universities']) == 78
    assert any(p['academic_year'] == '116' for p in dashboard['application_periods'])
    assert {s['school_name'] for s in alice.get(demo_url + '/universities').json()} == {'長庚大學'}
    a = create(alice, demo_url)
    b = create(bob, demo_url)
    assert len(a['stages']) == 6
    all_levels = [item for stage in a['stages'] for item in stage['levels']]
    term_level = next(item for item in all_levels if item['id'] == 'term')
    assert term_level['prompt'] == '2027 秋季（116-1）'
    submit_level = next(item for item in all_levels if item['id'] == 'cgu-internal-submit')
    assert submit_level['official_deadline_at'] == '2026-12-21T17:00:00+08:00'
    assert submit_level['deadline_confirmed'] is True
    ics = alice.get(demo_url + '/calendar/school-window.ics')
    assert ics.status_code == 200
    assert 'text/calendar' in ics.headers.get('content-type', '')
    assert 'BEGIN:VCALENDAR' in ics.text and '20261221' in ics.text
    path = '/account/application-paths/' + a['plan']['id']
    saved = alice.put(demo_url + path + '/steps/home?home_school=長庚大學',
        json={'revision':a['revision'], 'step':{'confirmed':True}})
    assert saved.ok, saved.text
    assert saved.json()['progress']['value'] == 1
    assert saved.json()['platform_submitted'] is False
    reloaded = alice.get(demo_url + path + '?home_school=長庚大學').json()
    assert reloaded['plan']['steps']['home']['confirmed']
    assert not bob.get(demo_url + path + '?home_school=長庚大學').json()['plan']['steps']
    assert alice.put(demo_url + path + '/steps/home', json={'revision':1, 'step':{'confirmed':False}}).status_code == 409
    assert alice.post(demo_url + '/demo/reset').ok
    assert alice.get(demo_url + '/account/application-paths').json()['items'] == []
    assert len(bob.get(demo_url + '/account/application-paths').json()['items']) == 1


def test_demo_student_profile_and_navigator_subsidy_sources(demo_url):
    client = visitor(demo_url)
    envelope = client.get(demo_url + '/account/workspace').json()
    assert envelope['exists'] is True
    profile = envelope['workspace']['selection_conditions']['profile']
    assert profile['college'] == '工學院'
    assert profile['department'] == '生物醫學工程學系'
    assert profile['current_year'] == '大三'
    assert profile['degree_level'] == '大學部'
    assert profile['language_test'] == 'toeic'
    assert profile['language_score'] == 750.0
    assert profile['target_term'] == '2027-fall'
    assert profile['academic_year'] == '116'

    dashboard = client.get(demo_url + '/student-dashboard').json()
    navigator = next(
        (item for item in dashboard['document_explanations'] if '2B00004' in item['title']),
        None,
    )
    assert navigator is not None
    joined_points = ' '.join(navigator['key_points'])
    for expected in ('75,000', '150,000', '60,000', '120,000', '10,000', '30%'):
        assert expected in joined_points
    assert 'b85add3b-7d9e-43ff-b22f-f0657e11765c' in navigator['source']['source_url']
    assert 'e3b68a9a-e820-4614-a799-e88023a40161' in navigator['document_url']
    assert len(dashboard['scholarship_info']) >= 1
    req_docs = ' '.join(detail for group in dashboard['required_documents'] for detail in group['details'])
    for doc_name in ('線上申請表', '家長同意書', '外國語文能力證明', '中文歷年成績單', '讀書計畫'):
        assert doc_name in req_docs


def _valid_report_sections(char_len: int = 310) -> dict[str, str]:
    base = '虛構示範返國研修心得段落內容，說明選課準備與海外學習收穫。'
    repeats = (char_len // len(base)) + 2
    text = (base * repeats)[:char_len]
    return {
        'preparation': text,
        'academics': text,
        'daily_life': text,
        'extracurricular': text,
    }


def test_school_connector_interface_and_swappability(tmp_path):
    from exchange_info.cgu_demo import MockCguConnector, SchoolConnector

    assert issubclass(MockCguConnector, SchoolConnector)
    for required_method in ('submit_application', 'send_inquiry', 'submit_return_report', 'get_status'):
        assert callable(getattr(SchoolConnector, required_method))

    class IncompleteConnector(SchoolConnector):
        pass

    with pytest.raises(TypeError):
        IncompleteConnector()

    # Verify swapping SchoolConnector implementation requires only replacing the connector class
    script = """
import os, sys
from fastapi.testclient import TestClient
from exchange_info.cgu_demo import SchoolConnector, create_demo_app

class StubSchoolConnector(SchoolConnector):
    def __init__(self, root):
        self.calls = []
    def submit_application(self, workspace_id, payload):
        self.calls.append(('submit_application', payload.get('preference_1')))
        return {'receipt_id': 'SIM-APP-STUB0001', 'status': 'submitted', 'status_label': '已送出', 'timeline': []}
    def send_inquiry(self, workspace_id, payload):
        self.calls.append(('send_inquiry', payload.get('question')))
        return {'receipt_id': 'SIM-INQ-STUB0001', 'status': 'pending', 'status_label': '待承辦回覆'}
    def submit_return_report(self, workspace_id, payload):
        self.calls.append(('submit_return_report', payload.get('partner_school')))
        return {'receipt_id': 'SIM-RPT-STUB0001', 'status': 'pending_review', 'status_label': '待承辦審核'}
    def get_status(self, workspace_id, receipt_id=None):
        return {'badge': '模擬・尚未與校方串接', 'stub': True, 'calls': len(self.calls)}

app = create_demo_app(connector_factory=StubSchoolConnector)
with TestClient(app, base_url='http://testserver') as client:
    headers = {'Origin': 'http://testserver'}
    assert client.get('/').status_code == 200
    r1 = client.post('/demo/connector/applications', json={'preference_1': '林肯大學 Lincoln University'}, headers=headers)
    assert r1.status_code == 201 and r1.json()['application']['receipt_id'] == 'SIM-APP-STUB0001'
    r2 = client.post('/demo/connector/inquiries', json={'question': '測試問題？'}, headers=headers)
    assert r2.status_code == 201 and r2.json()['inquiry']['receipt_id'] == 'SIM-INQ-STUB0001'
    r3 = client.post('/demo/connector/return-reports', json={'partner_school': '林肯大學 Lincoln University'}, headers=headers)
    assert r3.status_code == 201 and r3.json()['report']['receipt_id'] == 'SIM-RPT-STUB0001'
    st = client.get('/demo/connector/status').json()
    assert st['stub'] is True and st['calls'] == 3
"""
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith(('EXCHANGE_', 'SUPABASE', 'GOOGLE_OAUTH', 'SMTP_', 'OPENAI_API_KEY'))}
    res = subprocess.run([sys.executable, '-c', script], env=clean_env, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr


def test_html_fixes_hidden_community_fixed_school_and_forbidden_terms():
    demo_raw = platform_html()
    assert '官方合作' not in demo_raw
    assert '模擬・尚未與校方串接' in demo_raw

    demo = BeautifulSoup(demo_raw, 'html.parser')
    for hidden_sel in ('[data-public-route="forum"]', '[data-public-route="feedback"]', 'a[href="#forum"]', 'a[href="#feedback"]', '#detail-tab-community'):
        nodes = demo.select(hidden_sel)
        assert nodes, f'expected {hidden_sel} in DOM'
        assert all(n.has_attr('hidden') for n in nodes)

    switcher = demo.select_one('#school-switcher')
    assert switcher is not None
    assert switcher.has_attr('disabled')
    assert '切換就讀學校' not in switcher.get_text()
    assert '選擇就讀學校' not in switcher.get_text()
    assert demo.select_one('#school-switcher-label').get_text(strip=True) == '長庚大學'

    for nav_route in ('ask-oia', 'return-report', 'school-connector'):
        assert demo.select_one(f'.uniway-public-nav a[data-public-route="{nav_route}"]') is not None
    assert demo.select_one('#cgu-demo-oia-toggle') is not None


def test_upload_hashes_in_memory_never_writes_raw_bytes_to_disk_and_forbids_outbound_network(tmp_path):
    script = """
import hashlib, json, os, pathlib, socket
from fastapi.testclient import TestClient

# Block any non-loopback network or DNS activity
orig_connect = socket.socket.connect
orig_connect_ex = socket.socket.connect_ex
orig_getaddrinfo = socket.getaddrinfo

def _check_addr(address):
    host = address[0] if isinstance(address, tuple) else str(address)
    if host not in ('127.0.0.1', 'localhost', '::1', ''):
        raise AssertionError(f'Forbidden outbound socket connect to {address}')

def guarded_connect(self, address):
    _check_addr(address)
    return orig_connect(self, address)

def guarded_connect_ex(self, address):
    _check_addr(address)
    return orig_connect_ex(self, address)

def guarded_getaddrinfo(host, *args, **kwargs):
    if str(host) not in ('127.0.0.1', 'localhost', '::1', 'testserver'):
        raise AssertionError(f'Forbidden DNS lookup for {host}')
    return orig_getaddrinfo(host, *args, **kwargs)

socket.socket.connect = guarded_connect
socket.socket.connect_ex = guarded_connect_ex
socket.getaddrinfo = guarded_getaddrinfo

from exchange_info.cgu_demo import create_demo_app

sentinel = b'TOP_SECRET_PASSPORT_CONTENT_NEVER_TOUCH_DISK_9f8e7d6c5b4a'
expected_sha = hashlib.sha256(sentinel).hexdigest()
temp_root = pathlib.Path(os.environ['TMP'])

app = create_demo_app()
with TestClient(app, base_url='http://testserver') as client:
    headers = {'Origin': 'http://testserver'}
    home = client.get('/')
    assert home.status_code == 200
    assert '官方合作' not in home.text

    up = client.post(
        '/demo/connector/files',
        data={'doc_key': 'online_form'},
        files={'file': ('secret_passport.pdf', sentinel, 'application/pdf')},
        headers=headers,
    )
    assert up.status_code == 200, up.text
    meta = up.json()['file']
    assert meta['filename'] == 'secret_passport.pdf'
    assert meta['size'] == len(sentinel)
    assert meta['content_type'] == 'application/pdf'
    assert meta['sha256'] == expected_sha
    assert set(meta.keys()) == {'doc_key', 'doc_title', 'filename', 'size', 'content_type', 'sha256', 'uploaded_at'}

    # Exercise remaining connector endpoints under the network guard
    assert client.get('/demo/connector/spec').status_code == 200
    assert client.post('/demo/connector/ask', json={'question': '多益 700 分門檻'}, headers=headers).status_code == 200
    assert client.post('/demo/connector/ask', json={'question': '完全未收錄的北極熊接機問題'}, headers=headers).status_code == 200
    assert client.get('/demo/connector/oia/dashboard').status_code == 200

    # Inspect every single file inside TMP while runtime is still live on disk
    scanned_files = 0
    for file_path in temp_root.rglob('*'):
        if file_path.is_file():
            scanned_files += 1
            raw = file_path.read_bytes()
            assert sentinel not in raw, f'Raw upload bytes leaked onto disk at {file_path}'
    assert scanned_files > 0
"""
    isolated_tmp = tmp_path / 'isolated_tmp'
    isolated_tmp.mkdir()
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith(('EXCHANGE_', 'SUPABASE', 'GOOGLE_OAUTH', 'SMTP_', 'OPENAI_API_KEY'))}
    clean_env.update(TMP=str(isolated_tmp), TEMP=str(isolated_tmp), TMPDIR=str(isolated_tmp))
    res = subprocess.run([sys.executable, '-c', script], env=clean_env, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr


def test_connector_spec_precheck_submission_ask_report_oia_and_reset(demo_url):
    alice, bob = visitor(demo_url), visitor(demo_url)

    # 1. Integration Spec endpoint
    spec = alice.get(demo_url + '/demo/connector/spec').json()
    assert spec['badge'] == '模擬・尚未與校方串接'
    assert [m['method'] for m in spec['interfaces']] == [
        'submit_application', 'send_inquiry', 'submit_return_report', 'get_status',
    ]
    assert all(m['current_status'] == '模擬' for m in spec['interfaces'])
    assert [p['phase'] for p in spec['collaboration_phases']] == [
        '不需校方配合', '小型試辦', '需校方資訊單位',
    ]

    # 2. Cross-Origin CSRF check on new connector endpoints
    for endpoint in ('/demo/connector/applications', '/demo/connector/ask', '/demo/connector/inquiries',
                     '/demo/connector/return-reports', '/demo/connector/oia/actions'):
        bad = alice.post(demo_url + endpoint, json={}, headers={'Origin': 'https://evil.example'})
        assert bad.status_code == 403

    # 3. Precheck blocks missing documents (0 of 5, then 3 of 5)
    initial_status = alice.get(demo_url + '/demo/connector/status').json()
    assert initial_status['precheck']['complete'] is False
    assert len(initial_status['precheck']['missing_documents']) == 5

    blocked = alice.post(demo_url + '/demo/connector/applications', json={'preference_1': '林肯大學 Lincoln University'})
    assert blocked.status_code == 422
    assert len(blocked.json()['missing_documents']) == 5

    # Empty upload & unknown doc_key rejected
    assert alice.post(demo_url + '/demo/connector/files', data={'doc_key': 'online_form'},
                      files={'file': ('empty.pdf', b'', 'application/pdf')}).status_code == 422
    assert alice.post(demo_url + '/demo/connector/files', data={'doc_key': 'unknown_doc'},
                      files={'file': ('x.pdf', b'abc', 'application/pdf')}).status_code == 422

    doc_keys = ['online_form', 'parent_consent', 'language_proof', 'transcript', 'study_plan']
    for key in doc_keys[:3]:
        r = alice.post(demo_url + '/demo/connector/files', data={'doc_key': key},
                       files={'file': (f'{key}.pdf', f'sample-{key}'.encode(), 'application/pdf')})
        assert r.status_code == 200
    still_blocked = alice.post(demo_url + '/demo/connector/applications', json={'preference_1': '林肯大學 Lincoln University'})
    assert still_blocked.status_code == 422
    assert {d['key'] for d in still_blocked.json()['missing_documents']} == {'transcript', 'study_plan'}

    # Upload remaining 2 documents and submit
    for key in doc_keys[3:]:
        r = alice.post(demo_url + '/demo/connector/files', data={'doc_key': key},
                       files={'file': (f'{key}.pdf', f'sample-{key}'.encode(), 'application/pdf')})
        assert r.status_code == 200

    submitted = alice.post(demo_url + '/demo/connector/applications', json={
        'preference_1': '林肯大學 Lincoln University',
        'preference_2': '嘉泉大學 Gachon University',
    })
    assert submitted.status_code == 201, submitted.text
    app_rec = submitted.json()['application']
    app_id = app_rec['receipt_id']
    assert app_id.startswith('SIM-APP-')
    assert app_rec['status'] == 'submitted'
    assert [step['label'] for step in app_rec['timeline']] == ['已送出', '已收件', '要求補件／初審通過']

    # 4. OIA Dashboard preloads 5 fictional records & reflects actions to student + notifications
    oia = alice.get(demo_url + '/demo/connector/oia/dashboard').json()
    assert oia['seed_count'] == 5
    assert any(a['receipt_id'] == app_id for a in oia['inboxes']['applications'])
    assert oia['stats']['school_preferences']

    # Missing reason for request_supplement rejected
    assert alice.post(demo_url + '/demo/connector/oia/actions', json={
        'action': 'request_supplement', 'receipt_id': app_id, 'reason': '   ',
    }).status_code == 422

    supp = alice.post(demo_url + '/demo/connector/oia/actions', json={
        'action': 'request_supplement',
        'receipt_id': app_id,
        'reason': '歷年成績單缺少班級排名百分比，請補交教務處核章版。',
    })
    assert supp.status_code == 200
    after_supp = alice.get(demo_url + f'/demo/connector/status?receipt_id={app_id}').json()['record']
    assert after_supp['status'] == 'supplement_requested'
    assert after_supp['status_label'] == '要求補件'
    assert '班級排名' in after_supp['supplement_reason']

    notifs = alice.get(demo_url + '/account/notifications').json()
    assert notifs['unread_count'] >= 1
    assert any(app_id in item['title'] and '補件' in item['title'] for item in notifs['items'])

    # Confirm receipt & initial approval also work
    assert alice.post(demo_url + '/demo/connector/oia/actions', json={
        'action': 'confirm_receipt', 'receipt_id': app_id,
    }).status_code == 200
    assert alice.post(demo_url + '/demo/connector/oia/actions', json={
        'action': 'approve_initial', 'receipt_id': app_id,
    }).status_code == 200
    assert alice.get(demo_url + f'/demo/connector/status?receipt_id={app_id}').json()['record']['status_label'] == '初審通過'

    # 5. Ask OIA: rule hit vs miss -> OIA reply & add_to_faq
    hit = alice.post(demo_url + '/demo/connector/ask', json={'question': '請問 116-1 校內申請截止日與領航者補助金額？'}).json()
    assert hit['matched'] is True
    assert hit['mode_label'] == '規則式比對，非 AI'
    assert hit['inquiry'] is None
    assert any('cgu.edu.tw' in m['source_url'] for m in hit['matches'])

    escalated = alice.post(demo_url + '/demo/connector/inquiries', json={
        'question': '請問 116-1 校內申請截止日與特殊雙重學籍切結？',
        'escalated_from_faq': True,
    })
    assert escalated.status_code == 201
    assert escalated.json()['inquiry']['receipt_id'].startswith('SIM-INQ-')

    miss = alice.post(demo_url + '/demo/connector/ask', json={
        'question': '請問紐西蘭基督城冬季無麩質宿舍廚房預約編號怎麼填？',
    }).json()
    assert miss['matched'] is False
    inq_id = miss['inquiry']['receipt_id']
    assert inq_id.startswith('SIM-INQ-')

    reply_res = alice.post(demo_url + '/demo/connector/oia/actions', json={
        'action': 'reply_inquiry',
        'receipt_id': inq_id,
        'reply': '無麩質飲食需求可於獲得長庚提名後，在林肯大學住宿申請系統勾選特殊飲食欄位。',
    })
    assert reply_res.status_code == 200
    assert alice.post(demo_url + '/demo/connector/oia/actions', json={
        'action': 'add_to_faq',
        'receipt_id': inq_id,
        'keywords': ['無麩質宿舍廚房'],
    }).status_code == 200

    # Asking again now hits the newly added custom FAQ!
    hit_custom = alice.post(demo_url + '/demo/connector/ask', json={'question': '想問無麩質宿舍廚房怎麼申請？'}).json()
    assert hit_custom['matched'] is True
    assert '特殊飲食欄位' in hit_custom['matches'][0]['answer']

    # 6. Return Report: >= 300 chars validation, print view, consent gating on public school detail
    short_sections = _valid_report_sections(310)
    short_sections['daily_life'] = '字數不足測試' * 20  # 120 chars < 300
    bad_rpt = alice.post(demo_url + '/demo/connector/return-reports', json={
        'partner_school': '林肯大學 Lincoln University',
        'sections': short_sections,
        'public_consent': True,
    })
    assert bad_rpt.status_code == 422
    assert {s['key'] for s in bad_rpt.json()['short_sections']} == {'daily_life'}

    # Reject unsafe non-http(s) video_url
    bad_video = alice.post(demo_url + '/demo/connector/return-reports', json={
        'partner_school': '林肯大學 Lincoln University',
        'sections': _valid_report_sections(305),
        'video_url': 'javascript:alert(1)',
        'public_consent': True,
    })
    assert bad_video.status_code == 422

    # Private report (public_consent=False) must NOT appear publicly even after OIA approval
    priv_rpt = alice.post(demo_url + '/demo/connector/return-reports', json={
        'partner_school': '嘉泉大學 Gachon University',
        'sections': _valid_report_sections(305),
        'public_consent': False,
    }).json()['report']
    assert alice.post(demo_url + '/demo/connector/oia/actions', json={
        'action': 'approve_report', 'receipt_id': priv_rpt['receipt_id'],
    }).status_code == 200
    gachon_public = alice.get(demo_url + '/demo/connector/public-reports?school=嘉泉大學 Gachon University').json()['items']
    assert not any(r['receipt_id'] == priv_rpt['receipt_id'] for r in gachon_public)

    # Consented report (public_consent=True) appears after OIA approval + printable HTML works
    pub_rpt = alice.post(demo_url + '/demo/connector/return-reports', json={
        'partner_school': '林肯大學 Lincoln University',
        'sections': _valid_report_sections(312),
        'video_url': 'https://example.com/cgu-demo-share-video',
        'public_consent': True,
    }).json()['report']
    pub_id = pub_rpt['receipt_id']
    assert pub_id.startswith('SIM-RPT-')

    print_res = alice.get(demo_url + f'/demo/connector/return-reports/{pub_id}/print')
    assert print_res.status_code == 200
    assert '模擬・尚未與校方串接' in print_res.text
    assert pub_id in print_res.text

    # Not public before OIA approval
    before_pub = alice.get(demo_url + '/demo/connector/public-reports?school=林肯大學 Lincoln University').json()['items']
    assert not any(r['receipt_id'] == pub_id for r in before_pub)

    # Public after OIA approval
    assert alice.post(demo_url + '/demo/connector/oia/actions', json={
        'action': 'approve_report', 'receipt_id': pub_id,
    }).status_code == 200
    after_pub = alice.get(demo_url + '/demo/connector/public-reports?school=林肯大學 Lincoln University').json()['items']
    assert any(r['receipt_id'] == pub_id for r in after_pub)

    # 7. Visitor isolation: Bob sees none of Alice's records or notifications
    bob_status = bob.get(demo_url + '/demo/connector/status').json()
    assert bob_status['applications'] == []
    assert bob_status['inquiries'] == []
    assert bob_status['return_reports'] == []
    assert bob.get(demo_url + '/account/notifications').json()['unread_count'] == 0

    # 8. Reset wipes ALL newly added data for Alice
    assert alice.post(demo_url + '/demo/reset').ok
    reset_status = alice.get(demo_url + '/demo/connector/status').json()
    assert reset_status['draft_files'] == {}
    assert reset_status['applications'] == []
    assert reset_status['inquiries'] == []
    assert reset_status['return_reports'] == []
    assert alice.get(demo_url + '/account/notifications').json()['items'] == []
    assert alice.post(demo_url + '/demo/connector/ask', json={'question': '想問無麩質宿舍廚房怎麼申請？'}).json()['matched'] is False
