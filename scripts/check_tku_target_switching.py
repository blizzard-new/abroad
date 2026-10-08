"""Real browser regression for document context switching, rerenders and stale replies.

Uses an isolated local server/data directory; never writes accounts or production data.
Run with PLAYWRIGHT_BROWSERS_PATH=/tmp/tku-browsers PYTHONPATH=src .venv/bin/python scripts/check_tku_target_switching.py
"""
from __future__ import annotations

import itertools
import json
import socket
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests
import uvicorn
from playwright.sync_api import sync_playwright

from exchange_info.api import create_app


def check(base, browser, viewport):
    page = browser.new_page(viewport=viewport, reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','淡江大學');sessionStorage.setItem('exchange-guide-browse-first','1')")
    page.goto(base + "/?view=list#application-center", wait_until="domcontentloaded")
    page.wait_for_function("() => !document.querySelector('#boot-splash') && state.dashboard?.school_name === '淡江大學' && !state.applicationLoading", timeout=45000)
    schools = page.evaluate("state.dashboard.partner_universities.map(p => p.school_name)")
    records = []

    def set_year(year):
        field = page.locator("#application-context-form input[name=academic_year]")
        field.fill(year)
        # Commit through the real blur event; a synthetic change leaves a second
        # native change pending and can replace icons during a later mouse click.
        field.press("Tab")
        page.wait_for_function("() => !state.applicationLoading")

    def verify(name):
        try:
            page.wait_for_function("name => state.applicationDocumentCatalog?.context.target_school === name && !state.applicationLoading", arg=name)
        except Exception:
            print(json.dumps({"failed_target":name,"state":page.evaluate("({context:state.applicationContext,catalog:state.applicationDocumentCatalog?.context,error:state.applicationDocumentCatalogError,loading:state.applicationLoading,dialog:document.querySelector('#planning-target-change-dialog').open,input:document.querySelector('#application-target-school').value})"),"page_errors":errors},ensure_ascii=False),flush=True)
            raise
        actual = page.evaluate("({home:activeHomeSchool(), context:state.applicationContext, catalog:state.applicationDocumentCatalog, input:document.querySelector('#application-target-school').value})")
        context = actual["context"]
        response = requests.get(base + "/application-center/catalog", params={
            "school": actual["home"], "target_school": name,
            **{k: context[k] for k in ["college", "department", "degree_level", "academic_year", "application_round"] if context[k]},
        }, timeout=30)
        response.raise_for_status()
        expected = response.json()
        assert actual["input"] == context["target_school"] == name
        assert actual["catalog"]["academic_year"] == expected["academic_year"]
        assert [item["source_urls"] for item in actual["catalog"]["items"]] == [item["source_urls"] for item in expected["items"]]
        assert [item["name"] for item in actual["catalog"]["items"]] == [item["name"] for item in expected["items"]]
        summary = page.locator("#application-requirement-summary").inner_text()
        workspace = page.locator("#application-workspace-context").inner_text()
        assert name in summary and actual["home"] in workspace and name in workspace, (actual["home"], name, summary, workspace, expected["workflow_found"])
        assert expected["academic_year"] in summary, (name, summary)
        page.locator("#application-requirement-list details").evaluate_all("rows => rows.forEach(row => row.open = true)")
        assert page.locator("#application-requirement-list .application-requirement-item").count() == len(expected["items"])
        expected_links = [item["official_form_url"] if item["download_available"] else item["source_urls"][0] for item in expected["items"] if item["download_available"] or item["source_urls"]]
        assert page.locator("#application-requirement-list .application-requirement-source a").evaluate_all("rows => rows.map(row => row.getAttribute('href'))") == expected_links
        if "Electro" in name:
            assert "一般參考／2027版未核實" in page.locator("#application-requirement-list").inner_text()
        records.append({"home": actual["home"], "target": name, "academic_year": expected["academic_year"], "visible_documents": len(expected["items"]), "sources_and_title_match": True})

    def choose(name, cancel=False):
        previous = page.evaluate("state.applicationContext.target_school")
        page.locator("#application-target-school").select_option(name)
        if previous and previous != name:
            page.locator("#planning-target-change-dialog").wait_for(state="visible")
            # Account/draft sync can legitimately rerender this form while modal focus is elsewhere.
            page.evaluate("renderApplicationCenter()")
            value = "cancel" if cancel else "confirm"
            page.locator(f"#planning-target-change-dialog button[value={value}]").click()
            page.wait_for_function("() => !document.querySelector('#planning-target-change-dialog').open")
            page.wait_for_function("() => !document.querySelector('#application-target-school').disabled")
        verify(previous if cancel else name)

    set_year("2027-2028")
    # Every pair in the four-school set exercises A → B → A in the same context.
    for a, b in itertools.combinations(schools, 2):
        choose(a)
        choose(b)
        choose(a)
    choose(schools[1], cancel=True)

    # Release an older HTTP response while B is pending. It must not clear B's
    # loading state or resurrect A's document cards.
    delayed = {}
    target_a, target_b = schools[:2]
    choose(target_a)
    def hold(route):
        target = parse_qs(urlsplit(route.request.url).query).get("target_school", [None])[0]
        if target in [target_a, target_b]:
            delayed[target] = route
        else:
            route.continue_()
    page.route("**/application-center/catalog?**", hold)
    page.evaluate("void loadApplicationTemplates()")
    page.wait_for_function("() => state.applicationLoading")
    for _ in range(100):
        if target_a in delayed:
            break
        page.wait_for_timeout(25)
    assert target_a in delayed, "older catalog request was not intercepted"
    page.locator('#application-target-school').select_option(target_b)
    page.locator('#planning-target-change-dialog').wait_for(state='visible')
    page.evaluate('renderApplicationCenter()')
    page.locator('#planning-target-change-dialog button[value=confirm]').click()
    page.wait_for_function("name => state.applicationContext.target_school === name && state.applicationLoading",arg=target_b)
    for _ in range(100):
        if target_b in delayed:
            break
        page.wait_for_timeout(25)
    assert target_b in delayed, 'newer catalog request was not intercepted'
    assert page.locator('#application-requirement-list .application-requirement-item').count() == 0
    def response_for(name):
        return lambda response: parse_qs(urlsplit(response.url).query).get('target_school') == [name] and '/application-center/catalog?' in response.url
    with page.expect_response(response_for(target_a)) as old:
        delayed.pop(target_a).continue_()
    old.value.json()
    page.wait_for_timeout(100)
    assert page.evaluate('state.applicationLoading && state.applicationDocumentCatalog === null')
    assert target_b in page.locator('#application-requirement-summary').inner_text()
    with page.expect_response(response_for(target_b)) as new:
        delayed.pop(target_b).continue_()
    new.value.json()
    verify(target_b)
    page.unroute("**/application-center/catalog?**", hold)
    set_year('2028-2029')
    assert page.evaluate("state.applicationDocumentCatalog?.context.academic_year === '2028-2029' && state.applicationDocumentCatalog.items.length === 0 && state.applicationTemplates.length === 0")
    assert page.locator('#application-requirement-list .application-requirement-item').count() == 0
    set_year('2027-2028')
    verify(target_b)

    # Real home-school UI, returning to TKU; no prior school's catalog is reused.
    available = page.evaluate("state.supportedUniversities.map(row => row.school_name)")
    for home, year in [("國立臺北大學", "115"), ("長庚大學", "116"), ("國立臺灣大學", "116"), ("淡江大學", "2027-2028")]:
        if home not in available:
            continue
        if viewport["width"] < 900 and not page.evaluate("document.body.classList.contains('glass-menu-open')"):
            page.locator("#glass-menu-toggle").click()
        try:
            page.locator("#school-switcher").click(timeout=5000)
        except Exception:
            print(json.dumps({"failed_home_switch":home,"navigation":page.evaluate("(() => {let rows=[],node=document.querySelector('#school-switcher');while(node){let css=getComputedStyle(node);rows.push({id:node.id,cls:node.className,hidden:node.hidden,inert:node.inert,display:css.display,visibility:css.visibility});node=node.parentElement}return {nodes:rows,aria:document.querySelector('#glass-menu-toggle').getAttribute('aria-expanded'),loading:state.homeSchoolLoading}})()")},ensure_ascii=False),flush=True)
            page.screenshot(path='/tmp/tku-switch-navigation-failure.png',full_page=True)
            raise
        page.locator(f'#school-onboarding [data-home-school="{home}"]').click()
        page.locator("#confirm-school").click()
        page.wait_for_function("home => state.dashboard?.school_name === home && !state.applicationLoading && !state.homeSchoolLoading", arg=home, timeout=60000)
        assert page.locator("#application-requirement-list .application-requirement-item").count() == 0
        set_year(year)
        candidates = page.evaluate("state.dashboard.partner_universities.map(row => row.school_name)")
        candidates.sort(key=lambda name: "Lincoln" not in name)
        name = None
        for candidate in candidates:
            catalog = requests.get(base + "/application-center/catalog", params={"school":home,"target_school":candidate,"academic_year":year}, timeout=30).json()
            if catalog.get("workflow_found") and catalog.get("items"):
                name = candidate
                break
        assert name, f"No document workflow for {home}/{year}"
        choose(name)
    detail_checks = []
    page.evaluate("window.location.hash = '#partners'")
    page.locator('#partner-table').wait_for(state='visible')
    for name in schools:
        if viewport['width'] < 700:
            card = page.locator('#partner-table .partner-card').filter(has_text=name)
            if not card.get_attribute('open'):
                card.locator(':scope > summary').click()
        page.locator(f'#partner-table .school-detail-trigger:visible[data-school-name={json.dumps(name, ensure_ascii=False)}]').click()
        page.locator('#school-detail-view').wait_for(state='visible')
        page.wait_for_function("() => document.querySelector('#workflow-content')?.getAttribute('aria-busy') === 'false' && document.querySelector('#school-data-completeness-body')?.getAttribute('aria-busy') === 'false' && document.querySelector('#destination-official-content')?.getAttribute('aria-busy') === 'false'")
        page.locator('[data-detail-target="detail-application"]').click()
        host = page.locator('#workflow-content .workflow-step').nth(3)
        host.locator('summary').click()
        page.wait_for_function("() => document.querySelector('#workflow-content').innerText.includes('獲母校推薦')")
        assert '條件' in host.inner_text() and '外校申請' in host.inner_text()
        page.locator('[data-detail-target="detail-life"]').click()
        page.locator('.life-official-guide > summary').click()
        page.wait_for_function("() => document.querySelector('#destination-official-content').innerText.includes('保險')")
        assert page.locator('#destination-official-content .student-guide-section-card').count() == 14
        page.locator('[data-detail-target="detail-overview"]').click()
        page.locator('.school-data-completeness > summary').click()
        page.wait_for_function("() => document.querySelector('#school-data-completeness-body').innerText.includes('母校申請期限')")
        assert page.locator('#school-data-completeness-body li[data-completeness-status]').count() == 38
        page.screenshot(path=f"/tmp/tku-detail-switch-{viewport['width']}-{len(detail_checks)}.png",full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        detail_checks.append({'school':name,'host_workflow_expanded':True,'life_sections':14,'completeness_fields':38})
        page.evaluate('closeUniversityDetail()')
    page.screenshot(path=f"/tmp/tku-switch-{viewport['width']}.png", full_page=True)
    assert not errors, errors
    page.close()
    return {"viewport": viewport, "checks": records, "detail_checks":detail_checks, "cancel_keeps_original": True, "stale_response_ignored": True, "wrong_year_does_not_reuse_documents":True, "page_errors": errors}


def main():
    with tempfile.TemporaryDirectory(prefix="tku-switch-data-", dir="/tmp") as data:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(create_app(Path(data)), host="127.0.0.1", port=port, log_level="error"))
        thread = threading.Thread(target=server.run, daemon=True); thread.start()
        base = f"http://127.0.0.1:{port}"
        for _ in range(100):
            try:
                if requests.get(base + "/health", timeout=.5).ok:
                    break
            except requests.RequestException:
                pass
            time.sleep(.1)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                checks = [check(base, browser, view) for view in [{"width":1280,"height":900}, {"width":390,"height":844}]]
                browser.close()
            report = {"status":"passed", "checks":checks}
            Path("/tmp/tku-switch-result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps(report, ensure_ascii=False))
        finally:
            server.should_exit = True; thread.join(timeout=5)


if __name__ == "__main__":
    main()
