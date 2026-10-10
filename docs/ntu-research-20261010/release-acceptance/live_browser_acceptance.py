"""One public browser session; two viewport checks and one school switch."""
from pathlib import Path
import base64, datetime, hashlib, json, os, subprocess
from playwright.sync_api import sync_playwright, expect

OUT=Path('/workspace/ntu-research-2026-10-10/release-acceptance')
OUT.mkdir(exist_ok=True)
report={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'expected_merge_sha':'59a20f27fcee00fb597abc79e75ec11778317422',
 'mode':'one_anonymous_context_no_account_mutations_no_stress','checks':[],'server_errors':[],'page_errors':[]}
try:
 # Chromium's isolated profile lacks this environment's installed proxy CA.
 # Pin only that CA's public key, rather than disabling all certificate checks.
 cert_path=os.environ['CODEX_PROXY_CERT']
 pubkey=subprocess.run(['openssl','x509','-in',cert_path,'-pubkey','-noout'],capture_output=True,check=True).stdout
 der=subprocess.run(['openssl','pkey','-pubin','-outform','der'],input=pubkey,capture_output=True,check=True).stdout
 ca_spki=base64.b64encode(hashlib.sha256(der).digest()).decode()
 report['browser_environment_ca']={'path':cert_path,'spki_sha256_base64':ca_spki,
   'scope':'only installed execution-environment proxy CA; not a public-site TLS certification'}
 with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True,args=[f'--ignore-certificate-errors-spki-list={ca_spki}'])
    context=browser.new_context(viewport={'width':390,'height':956},timezone_id='Asia/Taipei',reduced_motion='reduce')
    context.add_init_script("window.sessionStorage.setItem('exchange-guide-browse-first','1')")
    page=context.new_page()
    page.on('pageerror',lambda error:report['page_errors'].append(str(error)))
    page.on('response',lambda response:report['server_errors'].append({'url':response.url,'status':response.status}) if response.status>=500 else None)
    page.goto('https://uniway-1167.onrender.com/?home=國立臺灣大學&view=list#partners',wait_until='domcontentloaded',timeout=90000)
    page.locator('#boot-splash').wait_for(state='hidden',timeout=90000)
    expect(page.locator('#school-switcher-label')).to_have_text('國立臺灣大學',timeout=90000)
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill('明斯特大學')
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告',timeout=90000)
    page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#school-detail-view')).to_be_visible(timeout=90000)
    for width in [390,1440]:
        page.set_viewport_size({'width':width,'height':956})
        summary=page.locator('#school-detail-view .partner-student-summary')
        expect(summary).to_contain_text('TOEFL iBT 4.0')
        expect(summary).to_contain_text('TOEFL iBT 80')
        expect(summary).to_contain_text('2026-10-10查核')
        expect(summary).to_contain_text('最終條件與甄選名額仍待確認')
        assert page.evaluate("state.dashboard.partner_universities.find(p=>p.school_name==='明斯特大學').quota") is None
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(OUT/f'live-ntu-reference-{width}.png'))
        report['checks'].append({'viewport':width,'new_and_old_toefl_visible':True,'dated_reference_caution_visible':True,
          'blank_quota_preserved':True,'no_horizontal_overflow':True})
    # Use the normal existing school menu once, at desktop width.
    page.evaluate("location.hash='#partners'")
    page.locator('#school-switcher').click()
    expect(page.locator('#school-options [data-home-school]')).to_have_count(6)
    page.locator('[data-home-school="長庚大學"]').click()
    page.locator('#confirm-school').click()
    expect(page.locator('#school-switcher-label')).to_have_text('長庚大學',timeout=90000)
    expect(page.locator('#partner-table')).not_to_contain_text('明斯特大學',timeout=90000)
    report['checks'].append({'six_school_menu_preserved':True,'switch_back_to_cgu':True})
    assert not report['server_errors'] and not report['page_errors']
    context.close();browser.close()
 report['status']='passed'
except Exception as error:
 report['status']='failed';report['failure_type']=type(error).__name__;report['failure']=str(error)
 raise
finally:
 report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (OUT/'live-browser-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False),flush=True)
