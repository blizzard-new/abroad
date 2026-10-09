"""Read-only guest smoke against the already deployed service (no account mutations)."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import requests
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path.cwd()))
from tests.e2e.test_ntu_destination_enrichment import test_ntu_photos_globe_data_and_bundled_life_are_visible_without_refresh
expect.set_options(timeout=60000)

commit, output_name = sys.argv[1:3]
base = 'https://uniway-1167.onrender.com'
results = {'checked_at': datetime.now(timezone.utc).isoformat(), 'url': base, 'render_commit': commit, 'http': [], 'browser': []}
for path in ['/health', '/student-dashboard?school=CGU', '/student-dashboard?school=NTPU', '/student-dashboard?school=NTU']:
    response = requests.get(base + path, timeout=90)
    response.raise_for_status()
    data = response.json()
    row = {'path': path, 'status': response.status_code}
    if path == '/health':
        row['body'] = data
    else:
        row.update(school_name=data['school_name'], partners=len(data['partner_universities']))
    results['http'].append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/workspace/integration-tools/browsers'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    for width in (390, 1440):
        # Executor HTTPS proxy CA is trusted by requests but absent from Chromium.
        # requests above still validates the public endpoint certificate normally.
        page = browser.new_page(ignore_https_errors=True)
        page.set_default_timeout(60000)
        responses, failures, errors = [], [], []
        page.on('response', lambda response: responses.append({'url': response.url, 'status': response.status}))
        page.on('requestfailed', lambda request: failures.append({'url': request.url, 'failure': request.failure}))
        page.on('pageerror', lambda error: errors.append(str(error)))
        try:
            test_ntu_photos_globe_data_and_bundled_life_are_visible_without_refresh(page, SimpleNamespace(base_url=base), width)
        except Exception:
            diagnostic = {'width': width, 'responses': responses, 'failures': failures, 'errors': errors, 'state': page.evaluate('({school:state.dashboard?.school_name,selected:state.selectedSchool,home:state.homeSchool,partners:state.dashboard?.partner_universities?.length})')}
            Path(f'/workspace/integration-evidence/{output_name}-diagnostic-{width}.json').write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2))
            page.screenshot(path=f'/workspace/integration-evidence/{output_name}-failure-{width}.png', full_page=True)
            print(json.dumps(diagnostic, ensure_ascii=False), flush=True)
            raise
        results['browser'].append({'width': width, 'passed': True})
        print(f'PASS public NTU globe/photo/life at {width}px', flush=True)
        page.close()
    browser.close()
Path(f'/workspace/integration-evidence/{output_name}-result.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
