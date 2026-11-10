from __future__ import annotations

import json
import os
import tempfile
import socket
import threading
import time
from pathlib import Path

import pytest
import requests
import uvicorn
from playwright.sync_api import sync_playwright

from exchange_info import cgu_demo

KEY = 'uniway-cgu-demo:v1'
EVIDENCE = Path(os.environ.get('CGU_DEMO_EVIDENCE_DIR', str(Path(tempfile.gettempdir()) / 'uniway-cgu-demo-evidence')))


@pytest.fixture(scope='module')
def demo_url():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(cgu_demo.create_demo_app(), host='127.0.0.1', port=port, log_level='error'))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{port}'
    for _ in range(150):
        if server.started:
            break
        time.sleep(.1)
    assert server.started
    yield url
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture
def demo_page(demo_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width':1440, 'height':1000}, reduced_motion='reduce')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        yield page, demo_url
        assert errors == []
        context.close()
        browser.close()


def ready(page, url, suffix=''):
    page.goto(url + '/' + suffix)
    page.locator('#loading').wait_for(state='hidden')
    assert page.locator('#load-error').is_hidden()


def start(page):
    page.locator('#explore [data-open-plan]').first.click()
    page.locator('#plan-content').wait_for(state='visible')


def test_complete_demo_journey_persists_and_reset_is_scoped(demo_page):
    page, url = demo_page
    requests_seen = []
    page.on('request', lambda request: requests_seen.append((request.method, request.url)))
    ready(page,url)
    page.evaluate("localStorage.setItem('exchange-guide-favorites', '[\"synthetic-existing\"]')")
    assert page.locator('.school-card').count() == 3
    page.locator('.school-card summary').first.click()
    assert page.get_by_text('歷史名額（不是當期名額）').first.is_visible()
    assert page.locator('.school-card details a').first.get_attribute('href').startswith('https://www.cgu.edu.tw/')
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(EVIDENCE/'desktop-explore.png'),full_page=True)
    start(page)
    assert page.locator('#next-task').inner_text() == '確認目標校語言門檻與當期名額'
    page.locator('#date-check-language').fill('2026-12-01')
    page.locator('#date-check-language').press('Tab')
    page.locator('#task-check-language').check()
    assert page.locator('#next-task').inner_text() == '確認成績單、平均與排名資料'
    page.get_by_role('link',name='資料與來源',exact=True).click()
    page.get_by_text('Lincoln 官網一般申請日為',exact=False).wait_for(state='visible')
    page.reload()
    page.locator('#source-list').wait_for(state='visible')
    page.get_by_role('link',name='我的旅程',exact=True).click()
    assert page.locator('#progress-label').inner_text() == '3 / 15 項完成'
    page.locator('[data-stage="0"]').click()
    assert page.locator('#task-check-language').is_checked()
    assert page.locator('#date-check-language').input_value() == '2026-12-01'
    page.locator('#go-next').click()
    assert page.locator('#task-transcript').evaluate('(e) => e === document.activeElement')
    page.screenshot(path=str(EVIDENCE/'desktop-journey.png'),full_page=True)
    # All six stages have working manual controls and next-step updates.
    for index in range(6):
        page.locator(f'[data-stage="{index}"]').click()
        for checkbox in page.locator('[data-task]').all():
            checkbox.check()
    assert page.locator('#progress-label').inner_text() == '15 / 15 項完成'
    assert '不代表資格核准' in page.locator('#next-detail').inner_text()
    assert page.locator('#go-next').is_hidden()
    page.locator('[data-stage="0"]').click()
    page.locator('#task-check-language').uncheck()
    assert page.locator('#next-task').inner_text() == '確認目標校語言門檻與當期名額'
    page.locator('#reset').click()
    page.get_by_role('button',name='取消',exact=True).click()
    assert page.locator('#plan-content').is_visible()
    page.locator('#reset').click()
    page.get_by_role('button',name='確認重設展示資料').click()
    assert page.locator('#plan-empty').is_visible()
    assert page.evaluate(f'localStorage.getItem({json.dumps(KEY)})') is None
    assert page.evaluate("localStorage.getItem('exchange-guide-favorites')") == '["synthetic-existing"]'
    page.reload()
    page.locator('#plan-empty').wait_for(state='visible')
    page.locator('#plan-empty [data-open-plan]').click()
    assert page.locator('#progress-label').inner_text() == '2 / 15 項完成'
    assert all(method == 'GET' and request_url.startswith(url) for method,request_url in requests_seen)


@pytest.mark.parametrize('width,height',[(1440,1000),(820,1180),(390,844),(320,720)])
def test_responsive_keyboard_and_empty_search(demo_page,width,height):
    page,url = demo_page
    page.set_viewport_size({'width':width,'height':height})
    ready(page,url)
    page.locator('#school-search').fill('不存在的學校')
    assert page.get_by_role('heading',name='沒有符合的參考學校').is_visible()
    page.locator('#school-search').fill('紐西蘭')
    assert page.locator('.school-card').count() == 1
    page.locator('[data-school="school-0"]').focus()
    page.keyboard.press('Enter')
    page.locator('#explore [data-open-plan]').first.focus()
    page.keyboard.press('Enter')
    page.locator('#task-check-language').focus()
    page.keyboard.press('Space')
    assert page.locator('#task-check-language').is_checked()
    assert page.locator('#progress-label').inner_text() == '3 / 15 項完成'
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('#reset').focus()
    page.keyboard.press('Enter')
    assert page.get_by_role('button',name='取消',exact=True).evaluate('(e)=>e === document.activeElement')
    page.keyboard.press('Escape')
    assert not page.locator('#reset-dialog').is_visible()
    if width == 390:
        page.screenshot(path=str(EVIDENCE/'mobile-journey.png'),full_page=True)


def test_fetch_failure_retry_and_catalogue_empty(demo_page):
    page,url = demo_page
    page.route('**/demo/content', lambda route: route.fulfill(status=503,body='unavailable'))
    page.goto(url)
    page.get_by_role('heading',name='暫時無法載入展示內容').wait_for()
    page.unroute('**/demo/content')
    page.get_by_role('button',name='重新載入',exact=True).click()
    page.locator('#explore').wait_for(state='visible')
    payload = requests.get(url+'/demo/content').json()
    payload.update(schools=[],status='unavailable',snapshot_at=None)
    page.route('**/demo/content',lambda route: route.fulfill(json=payload))
    ready(page,url)
    assert page.get_by_role('heading',name='參考學校暫時無法載入').is_visible()
    assert page.locator('#explore [data-open-plan]').first.is_disabled()
    assert page.locator('#rules .source-link').count() == 4


def test_missing_source_is_explicit(demo_page):
    page,url = demo_page
    payload=requests.get(url+'/demo/content').json()
    payload['sources']=[source for source in payload['sources'] if source['id'] != 'selection']
    page.route('**/demo/content',lambda route: route.fulfill(json=payload))
    ready(page,url)
    assert page.locator('#rules').get_by_text('來源待確認',exact=True).count() == 3
    assert page.locator('#rules a[href="undefined"]').count() == 0


def test_corrupt_data_requires_explicit_scoped_reset(demo_page):
    page,url = demo_page
    ready(page,url)
    page.evaluate(f'localStorage.setItem({json.dumps(KEY)}, "broken")')
    page.reload()
    page.locator('#loading').wait_for(state='hidden')
    assert '原資料未覆寫' in page.locator('#storage-notice').inner_text()
    assert page.locator('#explore [data-open-plan]').first.is_disabled()
    page.get_by_role('link',name='我的旅程',exact=True).click()
    page.locator('#reset').click()
    page.get_by_role('button',name='確認重設展示資料').click()
    assert page.evaluate(f'localStorage.getItem({json.dumps(KEY)})') is None


def test_storage_unavailable_does_not_claim_saved(demo_page):
    page,url=demo_page
    page.add_init_script("Storage.prototype.setItem = function() { throw new DOMException('blocked','SecurityError'); }; Storage.prototype.getItem = function() { throw new DOMException('blocked','SecurityError'); };")
    ready(page,url)
    start(page)
    page.locator('#task-check-language').check()
    assert '僅暫存在此頁' in page.locator('#storage-notice').inner_text()
    assert '已保存' not in page.locator('#storage-notice').inner_text().replace('請勿把它當成已保存','')
    assert page.locator('#progress-label').inner_text() == '3 / 15 項完成'
    page.reload()
    page.locator('#plan-empty').wait_for(state='visible')


def test_blank_plan_and_selected_school(demo_page):
    page,url=demo_page
    ready(page,url)
    page.locator('[data-school="school-1"]').click()
    page.locator('#blank-plan').click()
    assert page.locator('#progress-label').inner_text() == '0 / 15 項完成'
    assert 'Ravensburg' in page.locator('#plan-school').inner_text()
    page.reload()
    page.locator('#plan-content').wait_for(state='visible')
    assert 'Ravensburg' in page.locator('#plan-school').inner_text()


def test_other_destination_does_not_inherit_lincoln_rules(demo_page):
    page,url=demo_page
    ready(page,url)
    page.locator('[data-school="school-1"]').click()
    page.locator('#blank-plan').click()
    page.locator('[data-stage="3"]').click()
    assert page.get_by_text('目的校當期流程與官方來源待確認',exact=True).is_visible()
    assert page.locator('#stage-content a[href*="lincoln.ac.nz"]').count() == 0
    assert page.locator('#stage-content').get_by_text('此目標校的當期要求與來源待確認。',exact=False).count() == 2


def test_second_tab_cannot_silently_overwrite_new_progress(demo_page):
    page,url=demo_page
    ready(page,url)
    start(page)
    other=page.context.new_page()
    ready(other,url,'#journey')
    other.locator('#task-check-language').check()
    page.wait_for_function("document.querySelector('#storage-notice').textContent.includes('另一個分頁')")
    assert page.locator('#task-check-language').is_disabled()
    page.locator('[data-stage="1"]').click()
    assert page.locator('#task-transcript').is_disabled()
    page.reload()
    page.locator('#loading').wait_for(state='hidden')
    assert page.locator('#progress-label').inner_text() == '3 / 15 項完成'
    other.close()
