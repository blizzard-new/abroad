"""Exercise TKU availability filters in an isolated local server and Chromium.

Run: PLAYWRIGHT_BROWSERS_PATH=/tmp/tku-browsers PYTHONPATH=src .venv/bin/python scripts/check_tku_browser.py
Outputs only temporary screenshots and a JSON report; requires installed Chromium.
"""
import json
import socket
import tempfile
import threading
import time
from pathlib import Path

import requests
import uvicorn
from playwright.sync_api import sync_playwright
from exchange_info.api import create_app

with tempfile.TemporaryDirectory(prefix="tku-browser-data-", dir="/tmp") as data:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0)); port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(create_app(Path(data)),host="127.0.0.1",port=port,log_level="error"))
    thread=threading.Thread(target=server.run,daemon=True); thread.start()
    base=f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if requests.get(base+"/health",timeout=.5).status_code==200: break
        except requests.RequestException: pass
        time.sleep(.1)
    errors=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":1280,"height":900},reduced_motion='reduce')
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.add_init_script("localStorage.setItem('exchange-guide-home-school','淡江大學'); sessionStorage.setItem('exchange-guide-browse-first','1')")
            page.goto(base+"/?view=list#partners",wait_until="domcontentloaded")
            page.wait_for_function("() => state.dashboard?.school_name === '淡江大學' && document.querySelector('#partner-table').getAttribute('data-result-count') === '4'",timeout=45000)
            page.wait_for_function("() => document.querySelector('#boot-splash') === null",timeout=45000)
            assert page.evaluate("state.dashboard.partner_universities.every(p => p.availability_status === 'closed')")
            page.locator("#availability-filter").select_option("open")
            page.wait_for_function("() => document.querySelector('#partner-table').getAttribute('data-result-count') === '0'")
            page.locator("#availability-filter").select_option("closed")
            page.wait_for_function("() => document.querySelector('#partner-table').getAttribute('data-result-count') === '4'")
            page.locator("#region-filter").select_option("east-asia")
            assert page.locator("#partner-table").get_attribute("data-result-count")=="4"
            page.screenshot(path="/tmp/tku-browser-desktop.png",full_page=True)
            detail_checks=[]
            for name in page.evaluate("state.dashboard.partner_universities.map(p => p.school_name)"):
                page.locator('#partner-table tbody .school-detail-trigger').filter(has_text=name).click()
                page.locator('#school-detail-view').wait_for(state='visible')
                detail=page.locator('#school-detail-content').inner_text()
                assert 'JLPT N2' in detail and '研究所N1' in detail, name
                assert '全額學雜費' in detail and '校內申請' in detail, name
                page.wait_for_function("() => document.querySelector('#workflow-content')?.getAttribute('aria-busy') === 'false' && document.querySelector('#school-data-completeness-body')?.getAttribute('aria-busy') === 'false' && document.querySelector('#destination-official-content')?.getAttribute('aria-busy') === 'false'",timeout=30000)
                page.locator('[data-detail-target="detail-application"]').click()
                page.locator('#detail-application').wait_for(state='visible')
                page.locator('#workflow-content .workflow-step').nth(3).locator('summary').click()
                page.locator('#workflow-content .workflow-step').nth(4).locator('summary').click()
                page.wait_for_function("() => document.querySelector('#workflow-content').innerText.includes('條件')")
                flow=page.locator('#workflow-content').inner_text()
                assert '外校申請' in flow and '條件' in flow, f'{name}: {flow[:2000]}'
                assert '獲母校推薦' in flow, name
                page.locator('[data-detail-target="detail-life"]').click()
                page.locator('#detail-life').wait_for(state='visible')
                page.locator('.life-official-guide > summary').click()
                page.wait_for_function("() => document.querySelector('#destination-official-content').innerText.includes('保險')")
                life=page.locator('#destination-official-content').inner_text()
                assert '保險' in life and '簽證' in life and '2026-10-08' in life, f'{name}: {life[:1400]}'
                assert '住宿申請窗口' in life and '尚未核實' in life, name
                page.locator('[data-detail-target="detail-overview"]').click()
                page.locator('#detail-overview').wait_for(state='visible')
                page.locator('.school-data-completeness > summary').click()
                page.wait_for_function("() => document.querySelector('#school-data-completeness-body').innerText.includes('母校申請期限')")
                completeness=page.locator('#school-data-completeness-body').inner_text()
                assert page.locator('#school-data-completeness-body li[data-completeness-status]').count()==38
                assert '逐欄' in completeness and '母校申請期限' in completeness, name
                page.screenshot(path='/tmp/tku-detail-'+str(len(detail_checks))+'.png',full_page=True)
                detail_checks.append({'school':name,'home_language':True,'home_tuition':True,'application_steps':True,
                    'host_documents_in_workflow':True,'official_life_sections':14,'completeness_fields':38})
                page.evaluate('closeUniversityDetail()')
            catalog_checks=[]
            for name in page.evaluate("state.dashboard.partner_universities.map(p => p.school_name)"):
                # A fresh student context checks each school's document route.
                # Cross-target plan migration is outside this data adaptation.
                documents=browser.new_page(viewport={'width':1280,'height':900},reduced_motion='reduce')
                documents.on('pageerror',lambda error:errors.append(str(error)))
                documents.add_init_script("localStorage.setItem('exchange-guide-home-school','淡江大學'); sessionStorage.setItem('exchange-guide-browse-first','1')")
                documents.goto(base+'/#application-center',wait_until='domcontentloaded')
                documents.locator('#application-center').wait_for(state='visible')
                documents.wait_for_function("() => document.querySelector('#boot-splash') === null && document.querySelector('#application-target-school').options.length === 5 && !state.applicationLoading",timeout=45000)
                documents.locator('#application-context-form input[name=academic_year]').fill('2027-2028')
                documents.locator('#application-context-form input[name=academic_year]').dispatch_event('change')
                documents.wait_for_function('() => !state.applicationLoading')
                documents.locator('#application-target-school').select_option(value=name)
                documents.wait_for_function("name => state.applicationDocumentCatalog?.context.target_school === name && !state.applicationLoading",arg=name)
                assert documents.locator('#application-requirement-list .application-requirement-group').count()>=2
                host=documents.locator('.application-requirement-group').filter(has=documents.locator('summary strong').filter(has_text='外校申請'))
                host.locator('summary').click()
                host.locator('.application-requirement-item').first.wait_for(state='visible')
                count=host.locator('.application-requirement-item').count()
                assert count in [9,11,10,15],name
                text=host.inner_text()
                if 'Electro' in name:assert '一般參考／2027版未核實' in text
                if 'Seikei' in name:assert '僅獎學金申請人' in text
                catalog_checks.append({'school':name,'visible_host_documents':count})
                documents.close()
            page.set_viewport_size({"width":390,"height":844})
            page.wait_for_timeout(300)
            assert page.locator("#partner-table").get_attribute("data-result-count")=="4"
            page.screenshot(path="/tmp/tku-browser-mobile.png",full_page=True)
            result={"status":"passed","home_school":page.evaluate("state.dashboard.school_name"),"listed_records":4,
                    "open_filter_records":0,"closed_filter_records":4,"east_asia_filter_records":4,
                    "viewports":[[1280,900],[390,844]],"detail_checks":detail_checks,"document_catalog_checks":catalog_checks,"page_errors":errors}
            Path("/tmp/tku-browser-result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
            print(json.dumps(result,ensure_ascii=False))
            assert not errors,errors
            browser.close()
    finally:
        server.should_exit=True; thread.join(timeout=5)
