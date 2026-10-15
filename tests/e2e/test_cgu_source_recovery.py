"""Real browser/API, with a named recorded-source fixture (no live-source claim)."""
import json
import os
from pathlib import Path
import socket
import threading
import time

import pytest
import uvicorn
from playwright.sync_api import expect

from exchange_info import api, cgu_catalogue as cgu
from .test_partner_globe import INSTRUMENT

ARTIFACTS = Path(os.environ.get('VISUAL_EVIDENCE_DIR', 'output/cgu-source-recovery'))


@pytest.fixture
def recovery_server(tmp_path, monkeypatch):
    tick=[0.0]
    def fail():raise cgu.CatalogueFetchError('timeout')
    store=cgu.CguCatalogue(tmp_path/'cache.json',fetcher=fail,clock=lambda:tick[0]);store.refresh()
    monkeypatch.setattr(api,'create_cgu_catalogue',lambda _:store)
    monkeypatch.setattr('exchange_info.student_view.fetch_document_explanations',lambda **_:[])
    app=api.create_app(tmp_path)
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    for _ in range(100):
        if server.started:break
        time.sleep(.05)
    assert server.started
    try:yield f'http://127.0.0.1:{port}',store,tick
    finally:server.should_exit=True;thread.join(10)


@pytest.mark.parametrize('width',[390,1440])
def test_saved_outage_rows_and_detail_show_actual_source_time_then_recover(page,recovery_server,width):
    url,store,tick=recovery_server
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    page.set_viewport_size({'width':width,'height':950});page.emulate_media(reduced_motion='reduce')
    page.add_init_script(INSTRUMENT)
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url+'/?view=list#partners',wait_until='domcontentloaded')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60000)
    assert page.locator('#catalogue-source-status').count()==0
    assert page.evaluate('state.dashboard.partner_universities.length')==77
    page.screenshot(path=str(ARTIFACTS/f'outage-saved-{width}.png'),full_page=True)
    if width < 820: page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#school-detail-view')).to_be_visible()
    assert page.locator('#catalogue-source-status').count()==0
    page.screenshot(path=str(ARTIFACTS/f'outage-detail-{width}.png'),full_page=True)
    store.fetcher=lambda:json.loads(cgu.BUNDLED_SNAPSHOT.read_text());tick[0]=61;store.refresh()
    page.evaluate('loadDashboard({ refreshed: true })')
    expect(page.locator('#partner-result-count')).to_contain_text('77')
    assert page.evaluate('state.dashboard.partner_universities.length')==77
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors


@pytest.mark.parametrize('width',[390,1440])
def test_empty_start_says_unavailable_in_list_map_and_count_then_recovers(page,recovery_server,width):
    url,store,tick=recovery_server
    store._state=(None,(),store._state[2]) # explicit no-bundle/corrupt-cache scenario
    page.set_viewport_size({'width':width,'height':950});page.emulate_media(reduced_motion='reduce')
    page.add_init_script(INSTRUMENT)
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url+'/?view=list#partners',wait_until='domcontentloaded')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60000)
    expect(page.locator('#partner-table')).to_contain_text('合作校來源暫不可用')
    expect(page.locator('#partner-result-count')).to_have_text('來源暫不可用')
    assert page.locator('#coverage-rate').text_content()=='—'
    page.locator('[data-partner-view="map"]').click()
    expect(page.locator('#partner-map-status')).to_contain_text('來源暫不可用')
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(ARTIFACTS/f'no-snapshot-{width}.png'),full_page=True)
    store.fetcher=lambda:json.loads(cgu.BUNDLED_SNAPSHOT.read_text());tick[0]=61;store.refresh()
    page.evaluate('loadDashboard({ refreshed: true })')
    page.locator('[data-partner-view="list"]').click()
    expect(page.locator('#partner-result-count')).to_contain_text('77')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
