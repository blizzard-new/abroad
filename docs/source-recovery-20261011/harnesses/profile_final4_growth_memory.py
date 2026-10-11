"""Replay public catalogue endpoints against an owned, local-only app process."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import hashlib
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
budget_mib = float(sys.argv[sys.argv.index('--budget-mib')+1]) if '--budget-mib' in sys.argv else 512
root = Path('/workspace/recovery-evidence-20261011') / name
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
print(json.dumps({'local_server_helper_sha256':hashlib.sha256(Path('/workspace/integration-tools/local_memory_server.py').read_bytes()).hexdigest(),'defer_budget_failure_until_complete':'--defer-budget' in sys.argv}),flush=True)
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
                assert '--defer-budget' in sys.argv or max(result['peak_rss_bytes'],result['rss_bytes']) < budget_mib * 1024 * 1024, f'Isolated process exceeded the {budget_mib:g} MiB acceptance budget'
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
            if '--source-audits' in sys.argv:
                dashboard=requests.get(base+'/student-dashboard',params={'school':'NCU'},timeout=120).json()
                for query in ('誠信','阿利坎特','符茲堡'):
                    name=next(p['school_name'] for p in dashboard['partner_universities'] if query in p['school_name'])
                    get(('/partner-source-audit',{'school':name,'home_school':'NCU'}))
                    sample('source-audit-NCU-'+query)
            if '--tku-expanded' in sys.argv:
                original=json.loads((Path.cwd()/'src/exchange_info/official_data/tku/full_census_audit.json').read_text())
                response=requests.get(base+'/tku/partner-census',timeout=180)
                assert response.status_code==200 and response.json()=={k:v for k,v in original.items() if k!='schools'}
                sample('source-audit-TKU-summary')
                selected={r['id']:r for r in (original['schools'][0],original['schools'][-1],max(original['schools'],key=lambda r:len(json.dumps(r))))}
                assert len(selected)==3
                for rid,row in selected.items():
                    response=requests.get(base+'/tku/partner-census/'+rid,timeout=180)
                    assert response.status_code==200 and response.json()==row
                    sample('source-audit-TKU-'+rid)
                for batch in range(3):
                    with ThreadPoolExecutor(max_workers=8) as pool:
                        responses=list(pool.map(get,[('/tku/partner-census/'+max(selected,key=lambda k:len(json.dumps(selected[k]))),{})]*8))
                    assert len(responses)==8
                    sample(f'eight-concurrent-tku-source-audit-{batch}')
                del original,selected,response
            if '--menu-race' in sys.argv:
                from types import SimpleNamespace
                from playwright.sync_api import sync_playwright
                sys.path.insert(0,str(Path.cwd()))
                from tests.e2e.conftest import enter_public_site
                with sync_playwright() as playwright:
                    browser=playwright.chromium.launch(headless=True,executable_path='/workspace/integration-tools/browsers/chromium-1234/chrome-linux64/chrome',args=['--no-sandbox'])
                    page=browser.new_page(viewport={'width':390,'height':956})
                    page.emulate_media(reduced_motion='reduce')
                    enter_public_site(page,SimpleNamespace(base_url=base),'partners')
                    scenarios=[]
                    for redraw in (False,True,False):
                        if page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':
                            page.locator('#glass-menu-close').click()
                        box=page.locator('#glass-menu-toggle').bounding_box()
                        page.evaluate('window.__oldMenuIcon=document.querySelector("#glass-menu-toggle svg")')
                        page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
                        page.mouse.down()
                        if redraw:page.evaluate('initIcons()')
                        page.mouse.up()
                        page.wait_for_timeout(100)
                        scenarios.append({'redraw_during_pointer':redraw,'menu_open':page.locator('#glass-menu-toggle').get_attribute('aria-expanded'),'original_icon_connected':page.evaluate('window.__oldMenuIcon?.isConnected')})
                    (root/'menu-icon-race.json').write_text(json.dumps(scenarios,indent=2)+'\n')
                    print('MENU_ICON_RACE',json.dumps(scenarios),flush=True)
                    browser.close()
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
                schools = [('長庚大學',77),('國立臺北大學',206),('國立臺灣大學',288),('國立中正大學',104),('國立中央大學',214),('淡江大學',287)]
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True,executable_path='/workspace/integration-tools/browsers/chromium-1234/chrome-linux64/chrome',args=['--no-sandbox'])
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
                            if school=='淡江大學' and '--tku-expanded' in sys.argv:
                                report=page.evaluate("""async () => {
                                    const rows=state.dashboard.partner_universities;
                                    const photos=rows.filter(r=>r.image_status==='verified');
                                    for (const row of photos) {
                                        const image=new Image();image.src=row.image_url;await image.decode();
                                        if(!image.naturalWidth||!row.reference_data.campus_photo_author||!row.reference_data.campus_photo_license_url) throw Error('Missing TKU image or credit');
                                        const visual=schoolImageFor(row.school_name,row.country);
                                        if(visual.official_page_url!==row.image_page_url||visual.license_url!==row.reference_data.campus_photo_license_url) throw Error('TKU photo source scope mismatch');
                                    }
                                    const map=await import('/static/partner-map.js');
                                    const points=map.pointsFor(rows).features;
                                    return {photos:photos.length,points:points.length,representative:rows.filter(r=>map.hasCoordinates(r)&&r.location.precision==='representative').length};
                                }""")
                                assert report=={'photos':262,'points':264,'representative':255},report
                                sample(f'all-262-tku-photos-and-264-points-{width}')
                        if '--all-school-life' in sys.argv:
                            for school,count in schools:
                                open_navigation(page)
                                page.locator('#school-switcher').click()
                                page.locator(f'[data-home-school="{school}"]').click()
                                page.locator('#confirm-school').click()
                                page.wait_for_function('([s,c]) => state.dashboard?.school_name===s && state.dashboard.partner_universities.length===c && !state.partnerDataLoading',arg=[school,count],timeout=90000)
                                if width<700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':page.locator('#glass-menu-toggle').click()
                                page.locator('[data-partner-view="list"]').click()
                                selected=page.evaluate('() => state.dashboard.partner_universities[0].school_name')
                                page.locator('#clear-partner-filters').click()
                                page.locator('#partner-search').fill(selected)
                                if width<700:page.locator('#partner-table .partner-card > summary').first.click()
                                page.locator('#partner-table .school-detail-trigger:visible').first.click()
                                expect(page.locator('#school-detail-title')).to_have_text(selected)
                                with page.expect_response(lambda response:'/school-life-context?' in response.url,timeout=120000) as life_response:
                                    page.locator('#detail-tab-life').click()
                                assert life_response.value.status==200
                                expect(page.locator('#detail-life')).to_be_visible()
                                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                                sample(f'life-{width}-{school}')
                                page.go_back(wait_until='domcontentloaded')
                        assert not errors,errors
                        page.close()
                        page = browser.new_page()
                        test_ntu_photos_globe_data_and_bundled_life_are_visible_without_refresh(page,SimpleNamespace(base_url=base),width)
                        sample(f'ntu-globe-photo-life-{width}')
                        page.close()
                    browser.close()
            if '--burst-after-browser' in sys.argv:
                for batch in range(3):
                    endpoints = [('/student-dashboard', {'school':'CCU'})] * 8
                    with ThreadPoolExecutor(max_workers=8) as pool:
                        responses = list(pool.map(get, endpoints))
                    assert len(responses) == 8
                    sample(f'after-browser-eight-concurrent-ccu-dashboard-{batch}')
            sample('after-explicit-gc', collect=True)
        finally:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
print(json.dumps({'samples': len(rows), 'trace': trace, 'parallel': parallel, 'cleanup': 'passed'}))

assert max(max(row['rss_bytes'],row['peak_rss_bytes']) for row in rows) < budget_mib*1024*1024, f'Completed workload exceeded {budget_mib:g} MiB acceptance budget'
