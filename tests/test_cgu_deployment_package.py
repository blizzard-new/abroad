"""Deployment safety: no production services, credentials, or test writes."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / 'deploy/cgu-demo'
spec = importlib.util.spec_from_file_location('cgu_verify', DEPLOY / 'verify_deployment.py')
verify_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_module)


def test_compose_has_one_loopback_demo_without_production_connections():
    if not shutil.which('docker'):
        pytest.skip('Docker Compose CLI is not installed')
    result = subprocess.run(['docker', 'compose', '-p', 'uniway-cgu-demo-check',
        '--project-directory', str(DEPLOY), '--env-file', str(DEPLOY / 'demo.env.example'), '-f',
        str(DEPLOY / 'compose.yml'), 'config', '--format', 'json'], capture_output=True, text=True, check=True)
    config = json.loads(result.stdout)
    assert set(config['services']) == {'demo'}
    demo = config['services']['demo']
    assert set(demo['environment']) == {'CGU_DEMO_PUBLIC_ORIGIN', 'CGU_DEMO_SECURE_COOKIE'}
    assert not demo.get('volumes') and not demo.get('depends_on') and not demo.get('env_file')
    assert all(not value.get('external') for value in config.get('networks', {}).values())
    assert [(p['host_ip'], p['target']) for p in demo['ports']] == [('127.0.0.1', 8000)]
    assert demo['ports'][0]['published'] != '8000'
    assert demo['build']['dockerfile'] == 'deploy/cgu-demo/Dockerfile'
    assert Path(demo['build']['context']) == ROOT


def test_verifier_refuses_a_production_service_before_any_write(monkeypatch):
    calls = []
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {'status':'ok', 'school':'長庚大學'}
    class Client:
        headers = {}
        def request(self, method, url, **kwargs):
            calls.append((method, url))
            return Response()
    monkeypatch.setattr(verify_module.requests, 'Session', Client)
    with pytest.raises(RuntimeError, match='refusing all test writes'):
        verify_module.verify('https://demo.example.test', 'https://demo.example.test')
    assert calls == [('GET', 'https://demo.example.test/health')]


def test_verifier_never_forwards_secure_cookies_to_remote_plain_http():
    with pytest.raises(ValueError, match='loopback'):
        verify_module.verify('http://remote.example.test', 'https://demo.example.test', proxy_check=True)
    with pytest.raises(ValueError, match='exact HTTPS'):
        verify_module.verify('http://demo.example.test', 'https://demo.example.test')


def test_windows_scripts_keep_the_production_stack_and_source_unchanged():
    for path in DEPLOY.glob('*.ps1'):
        text = path.read_text(encoding='ascii')
        assert 'selfhost\\.env' not in text and 'Invoke-Compose' not in text
        assert 'git reset' not in text and 'git checkout' not in text and 'docker system prune' not in text
    publish = (DEPLOY / 'publish-windows.ps1').read_text()
    start = (DEPLOY / 'start-windows.ps1').read_text()
    assert "'--project-directory', $PSScriptRoot" in start
    assert publish.index('if (-not $Apply)') < publish.index('Copy-Item -LiteralPath $CaddyFile -Destination $backup')
    assert publish.index('validate --config $candidate') < publish.index('Copy-Item -LiteralPath $candidate -Destination $CaddyFile')
    assert 'Copy-Item -LiteralPath $backup -Destination $CaddyFile -Force' in publish
