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
