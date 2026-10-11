"""One guest browser, sequential public reads; never writes account/server data."""
import collections
import datetime
import json
import os
from pathlib import Path
import sys
import traceback

from playwright.sync_api import sync_playwright, expect

ROOT = Path('/workspace/abroad-globe-20261011')
sys.path.insert(0, str(ROOT))
from tests.e2e.test_partner_globe import INSTRUMENT
from tests.e2e.conftest import open_navigation

OUT = Path('/workspace/globe-evidence-20261011') / (sys.argv[1] if len(sys.argv)>1 else 'production-before')
OUT.mkdir(parents=True, exist_ok=True)
SCHOOLS = [('cgu','長庚大學'),('ntpu','國立臺北大學'),('ntu','國立臺灣大學'),('ccu','國立中正大學'),('ncu','國立中央大學'),('tku','淡江大學')]
if len(sys.argv)>2:
    SCHOOLS=[s for s in SCHOOLS if s[0] in sys.argv[2].split(',')]
proof = {'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'baseline_sha':'59a20f27fcee00fb597abc79e75ec11778317422', 'base_url':'https://uniway-1167.onrender.com', 'browser_proxy_ca_workaround':True, 'cases':[], 'page_errors':[], 'request_failures':[]}
def save():
    (OUT/'observations.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')

os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/integration-tools/browsers'
expect.set_options(timeout=90000)
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/workspace/integration-tools/browsers/chromium-1234/chrome-linux64/chrome',args=['--no-sandbox'])
    page=browser.new_page(ignore_https_errors=True,viewport={'width':1440,'height':1000})
    page.set_default_timeout(90000)
    page.emulate_media(reduced_motion='reduce')
    page.add_init_script(INSTRUMENT.replace('長庚大學',SCHOOLS[0][1]))
    page.on('pageerror',lambda error:proof['page_errors'].append(str(error)))
    page.on('requestfailed',lambda request:proof['request_failures'].append({'url':request.url,'failure':request.failure}))
    try:
        page.goto(proof['base_url']+'/?view=map#partners',wait_until='domcontentloaded',timeout=180000)
        expect(page.locator('#boot-splash')).to_be_hidden(timeout=180000)
        expect(page.locator('#school-onboarding')).to_be_hidden()
        for slug, school in SCHOOLS:
            print('BEGIN',slug,flush=True)
            if slug != SCHOOLS[0][0]:
                open_navigation(page)
                page.locator('#school-switcher').click(no_wait_after=True)
                page.locator(f'[data-home-school="{school}"]').click(no_wait_after=True)
                page.locator('#confirm-school').click(no_wait_after=True)
            page.wait_for_function('(school)=>state.dashboard?.school_name===school && !state.partnerDataLoading',arg=school)
            if page.locator('#glass-menu-toggle').is_visible() and page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':
                page.locator('#glass-menu-toggle').click()
            page.locator('[data-partner-view="map"]').click(no_wait_after=True)
            expect(page.locator('#partner-globe')).to_have_attribute('data-ready','true')
            page.wait_for_function("() => window.__testedMap && !window.__testedMap.isMoving() && window.__testedMap.isSourceLoaded('schools')")
            payload=page.evaluate('state.dashboard')
            (OUT/f'{slug}-dashboard.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
            case=page.evaluate("""async () => ({home:activeUniversityProfile(),filter:{query:state.partnerQuery,country:state.country,availability:state.availability},filtered:filteredPartners().map(p=>({school_name:p.school_name,country:p.country,location:p.location,image_status:p.image_status,image_url:p.image_url,client_visual:schoolImageFor(p.school_name,p.country)||null})),geojson:await window.__testedMap.getSource('schools').getData(),home_marker_count:document.querySelectorAll('.map-home-marker').length,home_button_disabled:document.querySelector('#map-home').disabled,count:document.querySelector('#partner-map-count').textContent,missing:document.querySelector('#partner-map-missing').textContent})""")
            case.update(slug=slug,school=school,partner_count=len(payload['partner_universities']))
            for width in (1440,390):
                page.set_viewport_size({'width':width,'height':1000 if width==1440 else 844})
                page.locator('#partner-map-panel').scroll_into_view_if_needed()
                page.wait_for_function('() => !window.__testedMap.isMoving()')
                page.screenshot(path=str(OUT/f'{slug}-map-{width}.png'),full_page=True)
            page.set_viewport_size({'width':1440,'height':1000})
            page.locator('[data-partner-view="list"]').click(no_wait_after=True)
            expect(page.locator('#partner-table')).to_be_visible()
            page.locator('#partner-table').scroll_into_view_if_needed()
            page.screenshot(path=str(OUT/f'{slug}-list-1440.png'),full_page=True)
            case['photo_dom']=page.locator('.school-photo img').evaluate_all('(images)=>images.map(i=>({alt:i.alt,src:i.currentSrc,loaded:i.complete&&i.naturalWidth>0}))')
            case['actual_feature_count']=len(case['geojson']['features'])
            case['api_photo_status_counts']=dict(collections.Counter(p.get('image_status') for p in payload['partner_universities']))
            proof['cases'].append(case)
            save()
            print(json.dumps({k:case[k] for k in ['school','partner_count','actual_feature_count','home_marker_count','api_photo_status_counts']},ensure_ascii=False),flush=True)
        proof['test_result']='passed'
    except Exception:
        proof['test_result']='failed'
        proof['error']=traceback.format_exc()
        try:
            proof['failure_state']=page.evaluate('({school:state.dashboard?.school_name,loading:state.partnerDataLoading,view:state.partnerView,url:location.href})')
            page.screenshot(path=str(OUT/'failure.png'),full_page=True,timeout=15000)
        except Exception as diagnostic_error:
            proof['diagnostic_error']=str(diagnostic_error)
        raise
    finally:
        proof['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        save()
        browser.close()
