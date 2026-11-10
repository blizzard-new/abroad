"""Demo isolation and conservative, source-backed catalogue contract."""
import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info import cgu_demo


def test_demo_factory_never_initializes_production_services(tmp_path):
    script = '''
import os, sys
from pathlib import Path
from fastapi.testclient import TestClient
from exchange_info.cgu_demo import create_demo_app
root = Path(sys.argv[1])
os.environ.update(EXCHANGE_INFO_DATA_DIR=str(root / 'production-data'),
                  EXCHANGE_ENVIRONMENT='production',
                  EXCHANGE_ACCOUNT_REPOSITORY='supabase')
with TestClient(create_demo_app()) as client:
    assert client.get('/').status_code == 200
    assert client.get('/demo/content').status_code == 200
assert 'exchange_info.api' not in sys.modules
assert 'exchange_info.repositories' not in sys.modules
assert not (root / 'production-data').exists()
'''
    subprocess.run([sys.executable, '-c', script, str(tmp_path)], check=True)


def test_demo_read_only_boundary_and_headers():
    with TestClient(cgu_demo.create_demo_app()) as client:
        client.cookies.set('session', 'synthetic-ignored')
        for path in ['/', '/cgu', '/demo/content', '/health', '/robots.txt', *[f'/static/{name}' for name in cgu_demo.ASSETS]]:
            response = client.get(path)
            assert response.status_code == 200
            assert 'noindex' in response.headers['x-robots-tag']
            assert response.headers['cache-control'] == 'no-store'
            assert "form-action 'none'" in response.headers['content-security-policy']
            assert 'set-cookie' not in response.headers
        for path in ['/auth/session', '/auth/register', '/account/workspace', '/account/vault/documents', '/static/app.js', '/static/content-review.html', '/openapi.json']:
            assert client.get(path).status_code == 404
            assert client.post(path, json={'demo': True}).status_code == (405 if path.startswith('/static/') else 404)
        assert client.post('/demo/content', json={}).status_code == 405
        assert client.delete('/demo/content').status_code == 405
        assert client.get('/robots.txt').text == 'User-agent: *\nDisallow: /\n'


def test_catalogue_reuses_snapshot_without_open_claims():
    catalogue = cgu_demo.demo_catalogue()
    assert len(catalogue['schools']) == 3
    assert catalogue['status'] == 'reference'
    for school in catalogue['schools']:
        assert school['name'] in cgu_demo.CURATED_SCHOOLS
        assert school['source_url'].startswith('https://www.cgu.edu.tw/')
        assert '待確認' in school['status']
        assert 'availability_status' not in school
        assert 'quota' not in school  # historical value uses reference_quota
    assert catalogue['snapshot_at'].startswith('2026-10-11')


def test_missing_corrupt_and_tampered_catalogue_fail_closed(tmp_path):
    path = tmp_path / 'snapshot.json'
    assert cgu_demo.demo_catalogue(path)['schools'] == []
    path.write_text('{invalid')
    assert cgu_demo.demo_catalogue(path)['status'] == 'unavailable'
    snapshot = json.loads(cgu_demo.BUNDLED_SNAPSHOT.read_text())
    snapshot['records'][0]['quota'] = '999'
    path.write_text(json.dumps(snapshot))
    assert cgu_demo.demo_catalogue(path)['schools'] == []


def test_editorial_tasks_are_unique_and_source_references_exist():
    content = json.loads(cgu_demo.CONTENT.read_text())
    sources = {item['id'] for item in content['sources']}
    assert len(content['stages']) == 6
    ids = []
    for stage in content['stages']:
        assert stage['source'] in sources
        for task in stage['tasks']:
            ids.append(task['id'])
            assert task.get('source') is None or task['source'] in sources
    assert len(set(ids)) == len(ids) == 15
    for rule in content['rules']:
        assert rule['source'] in sources


def test_content_unavailable_returns_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setattr(cgu_demo, 'CONTENT', tmp_path / 'missing.json')
    with TestClient(cgu_demo.create_demo_app()) as client:
        response = client.get('/demo/content')
        assert response.status_code == 503
        assert '重試' in response.json()['detail']
