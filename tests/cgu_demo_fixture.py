"""The demo must initialize in a fresh process, never in the normal test API process."""
import os
import socket
import subprocess
import sys
import time

import pytest
import requests


@pytest.fixture(scope='module')
def demo_url(tmp_path_factory, request):
    root = tmp_path_factory.mktemp('cgu-demo-process')
    sentinel = root / 'formal-data'
    sentinel.mkdir()
    (sentinel / 'marker').write_text('must not be read or changed')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('EXCHANGE_', 'SUPABASE', 'GOOGLE_OAUTH', 'SMTP_', 'OPENAI_API_KEY'))}
    env['EXCHANGE_INFO_DATA_DIR'] = str(sentinel)
    env['CGU_DEMO_SECURE_COOKIE'] = '0'
    env.pop('CGU_DEMO_PUBLIC_ORIGIN', None)
    env.update(getattr(request, 'param', {}))
    url = f'http://127.0.0.1:{port}'
    with (root / 'server.log').open('w+') as log:
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'exchange_info.cgu_demo:create_demo_app',
            '--factory', '--host', '127.0.0.1', '--port', str(port), '--no-proxy-headers'], env=env, stdout=log, stderr=log)
        try:
            for _ in range(240):
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(log.read()[-4000:])
                try:
                    if requests.get(url + '/health', timeout=1).ok:
                        break
                except requests.RequestException:
                    pass
                time.sleep(.5)
            else:
                pytest.fail('CGU demo did not start')
            yield url
        finally:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    assert sorted(p.name for p in sentinel.iterdir()) == ['marker']
    assert (sentinel / 'marker').read_text() == 'must not be read or changed'
