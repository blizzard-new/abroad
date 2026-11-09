"""A gate that reports missing student data asks for that data in place and judges again; it is not a bare confirm."""
import re
from pathlib import Path
from urllib.parse import urlencode

import pytest
from playwright.sync_api import expect

from .test_glass_theme import verified_login

SHOTS = Path('/tmp/application-gates')


def make_plan(page, live_server, home='長庚大學', target='林肯大學 Lincoln University'):
    response = page.request.post(f'{live_server.base_url}/account/application-paths', data={
        'home_school': home, 'target_school': target, 'academic_year': '116',
        'departure_year': '2027', 'semester': 'fall', 'revision': 0})
    assert response.ok, response.text()
    return response.json()


def open_gate(page, live_server, plan, level):
    page.goto(f'{live_server.base_url}/#my-application?' + urlencode(
        {'plan': plan['plan']['id'], 'view': 'level', 'level': level}))
    expect(page.locator('#level-title')).to_be_visible()


def gate_levels(page, live_server, plan, home='長庚大學'):
    data = page.request.get(f'{live_server.base_url}/account/application-paths/{plan["plan"]["id"]}',
                            params={'home_school': home}).json()
    return {l['id']: l for s in data['stages'] for l in s['levels']}


@pytest.mark.parametrize('size', [(1440, 900), (390, 844)])
def test_a_gate_missing_data_asks_for_it_and_the_confirm_button_waits(page, live_server, size):
    page.set_viewport_size({'width': size[0], 'height': size[1]})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    assert gate_levels(page, live_server, plan)['check-college']['missing_inputs'] == ['college', 'department']
    open_gate(page, live_server, plan, 'check-college')
    expect(page.locator('.check-status')).to_contain_text('待確認')
    gate = page.locator('#gate-inputs')
    expect(gate).to_be_visible()
    expect(gate).to_contain_text('補上你的學院與學系')
    # The student is not asked to confirm what the system has not been able to judge.
    confirm = page.get_by_role('button', name='確認內容', exact=True)
    expect(confirm).to_be_disabled()
    expect(page.locator('#save-note')).to_contain_text('補齊上方資料')
    # Saving with nothing typed says what to do instead of saving nothing.
    page.locator('#gate-save').click()
    expect(page.locator('#gate-error')).to_contain_text('請先填寫至少一項資料')
    # Typing in the gate is not the step's own text: no autosave starts.
    page.locator('#gate-college').fill('管理學院')
    page.locator('#gate-department').fill('資訊管理學系')
    expect(page.locator('#save-note')).not_to_have_text('尚未儲存')
    # Typing answers the earlier complaint: it does not stay on screen.
    expect(page.locator('#gate-error')).to_be_hidden()
    SHOTS.mkdir(exist_ok=True)
    page.locator('#level-view').scroll_into_view_if_needed()
    page.screenshot(path=str(SHOTS / f'gate-missing-{size[0]}.png'))
    page.locator('#gate-department').press('Enter')
    # The gate is judged again with what was typed: the missing flag clears and the confirm button wakes.
    expect(page.locator('#gate-inputs[data-state="missing"]')).to_have_count(0)
    expect(page.get_by_role('button', name='確認內容', exact=True)).to_be_enabled()
    expect(page.locator('#toast')).to_contain_text('已儲存')
    levels = gate_levels(page, live_server, plan)
    assert levels['check-college']['missing_inputs'] == []
    assert levels['check-college']['input_values'] == {'college': '管理學院', 'department': '資訊管理學系'}
    page.screenshot(path=str(SHOTS / f'gate-given-{size[0]}.png'))
    # The values are kept: reloading shows them again, editable, and the gate is still this plan's.
    page.reload()
    expect(page.locator('#level-title')).to_be_visible()
    page.locator('.gate-details > summary').click()
    expect(page.locator('#gate-college')).to_have_value('管理學院')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.get_by_role('button', name='確認內容', exact=True).click()
    expect(page.locator('.success-state')).to_be_visible()
    assert not errors


def test_values_from_my_conditions_are_offered_but_only_count_once_saved(page, live_server):
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    # What the student already told 我的條件 lives in their account workspace: it is offered here, not applied.
    current = page.request.get(f'{live_server.base_url}/account/workspace', params={'home_school': '長庚大學'}).json()
    saved = page.request.put(f'{live_server.base_url}/account/workspace', data={
        'home_school': '長庚大學', 'revision': current['workspace']['revision'], 'application_context': {'school_name': '長庚大學'},
        'selection_conditions': {'profile': {'college': '工學院', 'department': '電機工程學系'}}})
    assert saved.ok, saved.text()
    open_gate(page, live_server, plan, 'check-college')
    page.reload()
    expect(page.locator('#level-title')).to_be_visible()
    expect(page.locator('#gate-college')).to_have_value('工學院')
    expect(page.locator('#gate-department')).to_have_value('電機工程學系')
    expect(page.locator('.gate-offered')).to_contain_text('按下儲存後才會用來判斷')
    # Offering them judges nothing: the plan still lacks them and the confirm button still waits.
    assert gate_levels(page, live_server, plan)['check-college']['missing_inputs'] == ['college', 'department']
    expect(page.get_by_role('button', name='確認內容', exact=True)).to_be_disabled()
    page.locator('#gate-save').click()
    expect(page.locator('#gate-inputs[data-state="missing"]')).to_have_count(0)
    assert gate_levels(page, live_server, plan)['check-college']['input_values']['college'] == '工學院'


def test_a_gate_the_school_has_not_settled_asks_for_nothing_and_confirms_as_before(page, live_server):
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    levels = gate_levels(page, live_server, plan)
    open_gate(page, live_server, plan, 'check-availability')
    assert 'input_fields' not in levels['check-availability']
    expect(page.locator('#gate-inputs')).to_have_count(0)
    expect(page.get_by_role('button', name='確認內容', exact=True)).to_be_enabled()


def test_an_impossible_score_is_refused_in_the_gate_and_nothing_is_saved(page, live_server):
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    open_gate(page, live_server, plan, 'check-academic_score')
    expect(page.locator('#gate-inputs')).to_be_visible()
    page.locator('#gate-academic_score').fill('120')
    page.locator('#gate-save').click()
    expect(page.locator('#gate-error')).to_contain_text('介於 0 到 100')
    assert gate_levels(page, live_server, plan)['check-academic_score']['missing_inputs']
