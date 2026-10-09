"""Replay public catalogue endpoints against an owned, local-only app process."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import requests

name = sys.argv[1]
trace = '--trace' in sys.argv
parallel = '--parallel' in sys.argv
root = Path('/workspace/integration-evidence') / name
root.mkdir(exist_ok=True)
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
base = f'http://127.0.0.1:{port}'
env = dict(os.environ)
env['PYTHONPATH'] = str(Path.cwd() / 'src') + ':/workspace/integration-tools'
if trace:
    env['ABROAD_MEMORY_TRACE'] = '1'
rows = []
with tempfile.TemporaryDirectory(prefix='abroad-memory-profile-') as data:
    env['EXCHANGE_INFO_DATA_DIR'] = data
    with (root / 'server.log').open('w') as logs:
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'local_memory_server:app',
                                   '--host', '127.0.0.1', '--port', str(port), '--workers', '1',
                                   '--log-level', 'error'], env=env, stdout=logs, stderr=logs)
        try:
            for _ in range(120):
                if server.poll() is not None:
                    raise RuntimeError('Local app exited before ready')
                try:
                    requests.get(base + '/health', timeout=1).raise_for_status()
                    break
                except requests.RequestException:
                    time.sleep(.25)
            else:
                raise RuntimeError('Local app did not become ready')
            def sample(label, collect=False):
                result = requests.get(base + '/__local_memory_probe__', params={'collect': collect}, timeout=60).json()
                row = {'label': label, 'time': datetime.now(timezone.utc).isoformat(), **result}
                rows.append(row)
                (root / 'memory-samples.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
                print(label, round(row['rss_bytes']/1024/1024, 1), 'MiB', flush=True)
                assert result['rss_bytes'] < 1200 * 1024 * 1024, 'Owned diagnostic process exceeded 1200 MiB guard'
            def get(item):
                path, params = item
                r = requests.get(base + path, params=params, timeout=180)
                assert r.status_code == 200, (path, r.status_code, r.text[:200])
                return {'path': path, 'bytes': len(r.content), 'status': r.status_code}
            sample('startup')
            if '--translations' in sys.argv:
                response = requests.post(base + '/public-translations', json={'entries': [{'text': 'Campus accommodation is not guaranteed.', 'source_url': 'https://example.edu/'}], 'generate': False}, timeout=180)
                assert response.status_code == 200, response.text
                sample('translation-bundle-loaded')
            for iteration in range(1 if '--one-round' in sys.argv else (12 if '--soak' in sys.argv else 3)):
                for school in ('CGU', 'NTPU', 'NTU', 'CCU', 'NCU', 'TKU'):
                    endpoints = [('/student-dashboard', {'school': school}),
                                 ('/application-center/templates', {'school': school, 'program_type': 'exchange'}),
                                 ('/destination-profiles', {'home_school': school, 'compact': 'true'}),
                                 ('/application-period-options', {'home_school': school}),
                                 ('/coverage', {'school': school})]
                    if parallel:
                        with ThreadPoolExecutor(max_workers=5) as pool:
                            list(pool.map(get, endpoints))
                    else:
                        for item in endpoints:
                            get(item)
                    sample(f'round-{iteration}-{school}')
            if '--burst' in sys.argv:
                for batch in range(3):
                    endpoints = [('/student-dashboard', {'school':'CCU'})] * 8
                    with ThreadPoolExecutor(max_workers=8) as pool:
                        responses = list(pool.map(get, endpoints))
                    assert len(responses) == 8
                    sample(f'eight-concurrent-ccu-dashboard-{batch}')
            if '--browser' in sys.argv:
                from types import SimpleNamespace
                from playwright.sync_api import sync_playwright, expect
                sys.path.insert(0, str(Path.cwd()))
                from tests.e2e.conftest import enter_public_site, open_navigation
                from tests.e2e.test_ntu_destination_enrichment import test_ntu_photos_globe_data_and_bundled_life_are_visible_without_refresh
                schools = [('長庚大學',77),('國立臺北大學',206),('國立臺灣大學',288),('國立中正大學',104),('國立中央大學',214),('淡江大學',4)]
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True,args=['--no-sandbox'])
                    for width in ((390,1440) * (3 if '--soak' in sys.argv else 1)):
                        page = browser.new_page(viewport={'width':width,'height':956})
                        page.set_default_timeout(60000)
                        page.emulate_media(reduced_motion='reduce')
                        errors=[]
                        page.on('pageerror',lambda e:errors.append(str(e)))
                        enter_public_site(page,SimpleNamespace(base_url=base),'partners')
                        for school,count in schools:
                            open_navigation(page)
                            page.locator('#school-switcher').click()
                            page.locator(f'[data-home-school="{school}"]').click()
                            page.locator('#confirm-school').click()
                            page.wait_for_function('([s,c]) => state.dashboard?.school_name === s && state.dashboard.partner_universities.length === c',arg=[school,count],timeout=90000)
                            if width<700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':page.locator('#glass-menu-toggle').click()
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                            sample(f'browser-{width}-{school}')
                        assert not errors,errors
                        page.close()
                        page = browser.new_page()
                        test_ntu_photos_globe_data_and_bundled_life_are_visible_without_refresh(page,SimpleNamespace(base_url=base),width)
                        sample(f'ntu-globe-photo-life-{width}')
                        page.close()
                    browser.close()
            sample('after-explicit-gc', collect=True)
        finally:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
print(json.dumps({'samples': len(rows), 'trace': trace, 'parallel': parallel, 'cleanup': 'passed'}))
