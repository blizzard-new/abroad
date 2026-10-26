"""Opt-in real WebGL/interaction checks, with no AI calls or social publishing.

OFFICE_BROWSER_TESTS=1 CHROMIUM_PATH=/usr/bin/chromium uv run pytest -q tests/test_coastal_browser.py
Optional OFFICE_SCREENSHOTS directory receives day/night/mobile evidence.
"""
from datetime import datetime
import os
from pathlib import Path
import socket
import threading
import time

import pytest
import uvicorn
from playwright.sync_api import sync_playwright, expect

from office.config import Settings
from office.office import Office
from office.server import create_app

pytestmark = pytest.mark.skipif(os.environ.get('OFFICE_BROWSER_TESTS') != '1', reason='opt-in Chromium/WebGL test')


@pytest.fixture(scope='module')
def live_office(tmp_path_factory):
    home = tmp_path_factory.mktemp('coastal')
    office = Office(Settings.from_env(env={'OFFICE_HOME': str(home), 'OFFICE_BRAINS': 'offline', 'OFFICE_DRY_RUN': '1', 'OFFICE_RENDER_MEDIA': '0'}))
    # No scheduler is started; even approval tests cannot publish anything.
    app = create_app(office.settings, office=office, clock=False)
    sock = socket.socket(); sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level='error'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True); thread.start()
    for _ in range(100):
        if server.started: break
        time.sleep(.05)
    assert server.started
    yield office, f'http://127.0.0.1:{port}'
    server.should_exit = True; thread.join(timeout=5); sock.close()


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        yield browser
        browser.close()


@pytest.fixture(autouse=True)
def close_contexts(browser):
    yield
    for context in browser.contexts:
        context.close()


def capture(page, name):
    if directory := os.environ.get('OFFICE_SCREENSHOTS'):
        path = Path(directory); path.mkdir(parents=True, exist_ok=True)
        page.wait_for_timeout(1200)  # allow the software GPU/compositor to present the settled camera
        page.screenshot(path=str(path / name), full_page=True)
        page.locator('#world-stage').screenshot(path=str(path / f'scene-{name}'))


def ready(page, url):
    page.goto(url, wait_until='networkidle')
    expect(page.locator('body')).to_have_class('coastal world-ready', timeout=30000)
    page.wait_for_timeout(500)


def test_real_clock_departments_staff_cards_and_approval(browser, live_office):
    office, url = live_office
    page = browser.new_page(viewport={'width':1440,'height':1000}, timezone_id='America/New_York')
    errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
    page.clock.install(time=datetime.fromisoformat('2026-10-26T04:00:00+00:00'))
    ready(page, url)
    expect(page.locator('#world-stage')).to_have_attribute('data-phase', 'day')
    expect(page.locator('#world-stage')).to_have_attribute('data-view', 'exterior')
    expect(page.locator('#world-stage')).to_have_attribute('data-lights', 'off')
    expect(page.locator('#world-time')).to_have_text('12:00')
    expect(page.locator('#department-roster [data-person]')).to_have_count(10)
    capture(page, 'day-desktop.png')
    page.locator('#world-enter').click()
    expect(page.locator('#world-stage')).to_have_attribute('data-view', 'interior')
    expect(page.locator('.world-person[data-agent="designer"]')).to_have_attribute('data-floor', '2')
    expect(page.locator('.world-person[data-agent="chief"]')).to_have_attribute('data-floor', '1')
    capture(page, 'interior-desktop.png')
    page.locator('[data-world-view="terrace"]').click()
    expect(page.locator('#world-stage')).to_have_attribute('data-view', 'terrace')
    capture(page, 'garden-desktop.png')
    page.locator('[data-world-department="design"]').click()
    expect(page.locator('#world-stage')).to_have_attribute('data-view', 'interior')
    expect(page.locator('[data-world-department="design"]')).to_have_attribute('aria-pressed','true')
    page.locator('[data-person="designer"]').click()
    expect(page.locator('#agent-card')).to_be_visible()
    expect(page.locator('#agent-card-body h2')).to_contain_text('Mori')
    page.locator('#agent-card .close').click()
    page.locator('#world-reset').click()
    page.locator('[data-world-view="exterior"]').click()
    page.clock.set_system_time(datetime.fromisoformat('2026-10-26T11:00:00+00:00'))
    page.clock.fast_forward(16000)
    expect(page.locator('#world-stage')).to_have_attribute('data-phase','night')
    expect(page.locator('#world-stage')).to_have_attribute('data-lights','on')
    expect(page.locator('#world-time')).to_have_text('19:00')
    capture(page, 'night-desktop.png')
    draft = office.store.add_draft(run_id=None, day='2099-01-01', channel='threads', format='text', title='瀏覽器測試草稿',
        payload={'text':'測試內容','first_reply':'連結','topic_tag':'交換學生'}, status='pending_approval', scheduled_at='2099-01-01T04:30:00+00:00')
    office.draft_changed(draft)
    page.locator('[data-person="boss"]').click()
    expect(page.locator('#view-inbox')).to_be_visible()
    page.locator(f'.pass[data-id="{draft}"] [data-act="edit"]').click()
    page.locator(f'#f-{draft}-text').fill('人工修改內容')
    page.locator(f'.pass[data-id="{draft}"] [data-act="save"]').click()
    expect(page.locator(f'.pass[data-id="{draft}"] .post')).to_have_text('人工修改內容')
    page.locator(f'.pass[data-id="{draft}"] [data-act="approve"]').click()
    expect(page.locator(f'.pass[data-id="{draft}"]')).to_have_count(0)
    assert office.store.draft(draft)['status'] == 'approved'
    assert not errors
    page.close()


@pytest.mark.parametrize(('activity', 'random_value'), [('nap', 0), ('water', .4), ('exercise', .8)])
def test_idle_activity_is_interrupted_by_real_sse_work_event(browser, live_office, activity, random_value):
    office, url = live_office
    office.bus.emit('strategist', 'status', '待命中', state='idle')
    page = browser.new_page(viewport={'width':1000,'height':900})
    page.add_init_script(f'Math.random = () => {random_value};')  # deterministic selection, no production test hooks
    page.clock.install(time=datetime.fromisoformat('2026-10-26T11:00:00+00:00'))
    ready(page,url)
    page.clock.fast_forward(10000 + int(random_value * 22000))
    expect(page.locator('.world-person[data-agent="strategist"]')).to_have_attribute('data-activity',activity, timeout=20000)
    office.bus.emit('strategist','status','收到新的企劃工作',state='working',screen={'type':'lines','title':'新工作','lines':['查詢交換資料']})
    expect(page.locator('.world-person[data-agent="strategist"]')).to_have_attribute('data-activity','desk', timeout=15000)
    expect(page.locator('.world-person[data-agent="strategist"]')).to_have_attribute('data-state','working')
    page.locator('[data-person="strategist"]').click()
    expect(page.locator('#agent-card-body')).to_contain_text('查詢交換資料')
    assert not office.store.published_since('2000-01-01T00:00:00+00:00')
    page.close()


def test_upstairs_employee_uses_stairs_and_returns_when_work_arrives(browser, live_office):
    office, url = live_office
    office.bus.emit('strategist', 'status', '待命中', state='idle')
    page = browser.new_page(viewport={'width':500, 'height':900})
    page.add_init_script('Math.random = () => .4;')
    page.clock.install(time=datetime.fromisoformat('2026-10-26T04:00:00+00:00'))
    ready(page, url)
    person = page.locator('.world-person[data-agent="strategist"]')
    page.clock.fast_forward(19000)
    expect(person).to_have_attribute('data-location', 'stairs', timeout=60000)
    expect(person).to_contain_text('下樓')
    office.bus.emit('strategist', 'status', '新工作，請回座位', state='working')
    expect(person).to_have_attribute('data-state', 'working')
    expect(person).to_have_attribute('data-activity', 'desk', timeout=60000)
    expect(person).to_have_attribute('data-floor', '2')
    expect(person).to_have_attribute('data-location', 'office')
    page.close()


def test_mobile_six_hires_reduced_motion_and_no_horizontal_overflow(browser,live_office):
    office,url=live_office
    for i in range(6): office.hire(f'研究員{i+1}','研究助理','查詢學校資料',brain='offline')
    page=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,reduced_motion='reduce')
    page.clock.install(time=datetime.fromisoformat('2026-10-26T04:00:00+00:00'))
    ready(page,url)
    expect(page.locator('#department-roster [data-person]')).to_have_count(16)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.clock.fast_forward(60000)
    expect(page.locator('.world-person:not([data-activity="desk"])')).to_have_count(0)
    capture(page,'mobile-exterior.png')
    page.locator('[data-world-view="interior"]').click()
    page.locator('#world-in').click();page.locator('#world-rotate').click();page.locator('#world-reset').click()
    assert page.locator('.world-person.crowded').count() > 0  # dense staff names collapse rather than overlap
    expect(page.locator('.world-person.crowded').first).to_have_css('opacity', '0')
    capture(page,'mobile.png')
    page.locator('[data-person="chief"]').click()
    expect(page.locator('#agent-card-body h2')).to_contain_text('Leo')
    page.close()


def test_webgl_failure_keeps_workflows_available(browser,live_office):
    _,url=live_office
    page=browser.new_page(viewport={'width':1200,'height':900})
    page.add_init_script('''const get = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(type,...args) {
        return String(type).includes('webgl') ? null : get.call(this,type,...args);
      };''')
    page.goto(url,wait_until='networkidle')
    expect(page.locator('body')).to_have_class('coastal world-unavailable')
    assert page.locator('#flat-office').evaluate('(e) => e.open')
    expect(page.locator('#chat-input')).to_be_visible()
    page.locator('#tab-inbox').click();expect(page.locator('#view-inbox')).to_be_visible()
    page.close()
