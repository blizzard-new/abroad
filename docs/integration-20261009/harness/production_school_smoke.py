"""Guest-only public-site school switching. No registration or content writes."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone
from types import SimpleNamespace
import requests
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path.cwd()))
from tests.e2e.conftest import enter_public_site, open_navigation

commit, output_name = sys.argv[1:3]
schools = [('長庚大學', 77), ('國立臺北大學', 206), ('國立臺灣大學', 288), ('國立中正大學', 104)]
if '--ncu' in sys.argv: schools.append(('國立中央大學', 214))
if '--tku' in sys.argv: schools.append(('淡江大學', 4))
base = 'https://uniway-1167.onrender.com'
output = Path('/workspace/integration-evidence') / (output_name + '-result.json')
proof = {'commit': commit, 'checked_at': datetime.now(timezone.utc).isoformat(), 'http': [], 'browser': [], 'browser_proxy_ca_workaround': True}
if '--tku' in sys.argv:
    response = requests.get(base + '/health', timeout=90)
    response.raise_for_status()
    health = response.json()
    assert health['status'] == 'ok'
    assert set(health['supported_schools']) == {school for school, _ in schools}
    proof['health'] = health
    response = requests.get(base + '/openapi.json', timeout=90)
    response.raise_for_status()
    actual_contract = response.json()
    expected_contract = json.loads(Path('docs/api/openapi.json').read_text())
    assert actual_contract == expected_contract, 'Deployed OpenAPI differs from the accepted candidate'
    canonical = json.dumps(actual_contract, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    proof['openapi'] = {'status': response.status_code, 'candidate_equal': True,
                        'canonical_sha256': hashlib.sha256(canonical).hexdigest()}
    print('HEALTH + OPENAPI PASS accepted six-school candidate', flush=True)
for school, count in schools:
    r = requests.get(base + '/student-dashboard', params={'school':school}, timeout=90)
    r.raise_for_status(); payload=r.json()
    assert payload['school_name']==school and len(payload['partner_universities'])==count
    proof['http'].append({'school':school,'count':count,'status':r.status_code})
    print('HTTP PASS', school, count, flush=True)
if '--tku' in sys.argv:
    response = requests.get(base + '/community/boards', timeout=90)
    response.raise_for_status()
    boards = response.json()
    expected = {'cgu','ntpu','ntu','ccu','ncu','tku'}
    assert {row['id'] for row in boards if row['kind']=='university_exchange'} == expected
    assert all(row['can_read'] is False and row['can_post'] is False
               for row in boards if row['kind']=='university_exchange')
    proof['guest_forum'] = []
    for board in sorted(expected):
        response = requests.get(base + '/community/posts', params={'board_id':board}, timeout=90)
        assert response.status_code == 401, (board, response.status_code)
        proof['guest_forum'].append({'board':board,'status':401})
    print('GUEST FORUM PASS all six school reads require authentication', flush=True)
os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/integration-tools/browsers'
expect.set_options(timeout=60000)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    for width in ((1440,) if '--desktop' in sys.argv else (390,1440)):
        page=browser.new_page(ignore_https_errors=True,viewport={'width':width,'height':956})
        page.set_default_timeout(60000);page.emulate_media(reduced_motion='reduce')
        errors=[]; responses=[]; failures=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('response',lambda r: responses.append({'url':r.url,'status':r.status}) if '/static/' not in r.url else None)
        page.on('requestfailed',lambda r: failures.append({'url':r.url,'failure':r.failure}))
        enter_public_site(page,SimpleNamespace(base_url=base),'partners')
        for school,count in schools:
            open_navigation(page);page.locator('#school-switcher').click()
            expect(page.locator('#school-options [data-home-school]')).to_have_count(len(schools))
            page.locator(f'[data-home-school="{school}"]').click();page.locator('#confirm-school').click()
            deadline=time.monotonic()+90
            while time.monotonic()<deadline:
                actual=page.evaluate('({school:state.dashboard?.school_name,count:state.dashboard?.partner_universities.length})')
                if actual=={'school':school,'count':count}: break
                page.wait_for_timeout(200)
            else:
                detail={'school':school,'actual':actual,'errors':errors,'responses':responses,'failures':failures,
                        'state':page.evaluate('({home:state.homeSchool,selected:state.selectedHomeSchool,hasLoaded:state.hasLoaded,loading:state.partnerDataLoading,error:state.partnerDataError})')}
                Path('/workspace/integration-evidence/'+output_name+'-failure.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2))
                raise AssertionError(detail)
            expect(page.locator('#school-switcher-label')).to_have_text(school)
            if width<700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':page.locator('#glass-menu-toggle').click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            proof['browser'].append({'width':width,'school':school,'count':count,'passed':True})
            print('BROWSER PASS',width,school,count,flush=True)
        assert not errors,errors
        page.close()
    browser.close()
output.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
