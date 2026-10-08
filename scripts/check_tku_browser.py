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
            page=browser.new_page(viewport={"width":1280,"height":900})
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
            page.set_viewport_size({"width":390,"height":844})
            page.wait_for_timeout(300)
            assert page.locator("#partner-table").get_attribute("data-result-count")=="4"
            page.screenshot(path="/tmp/tku-browser-mobile.png",full_page=True)
            result={"status":"passed","home_school":page.evaluate("state.dashboard.school_name"),"listed_records":4,
                    "open_filter_records":0,"closed_filter_records":4,"east_asia_filter_records":4,
                    "viewports":[[1280,900],[390,844]],"page_errors":errors}
            Path("/tmp/tku-browser-result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
            print(json.dumps(result,ensure_ascii=False))
            assert not errors,errors
            browser.close()
    finally:
        server.should_exit=True; thread.join(timeout=5)
