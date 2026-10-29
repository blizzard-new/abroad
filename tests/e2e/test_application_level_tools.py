"""Real account map saves, nested tools and native form semantics of Glide Select."""
from pathlib import Path
from urllib.parse import urlencode

import pytest
from playwright.sync_api import expect
from .test_glass_theme import verified_login


def test_level_tools_keep_forms_and_plan_progress_across_routes_and_reload(page, live_server):
    errors=[]
    page.on('pageerror',lambda error: errors.append(str(error)))
    verified_login(page,live_server)
    context=dict(home_school='長庚大學',target_school='林肯大學 Lincoln University',
                 academic_year='116',departure_year='2027',semester='fall',revision=0)
    response=page.request.post(f'{live_server.base_url}/account/application-paths',data=context)
    assert response.ok,response.text()
    created=response.json();plan_id=created['plan']['id']
    path=f'{live_server.base_url}/#my-application?'+urlencode(dict(plan=plan_id,view='level',level='target'))
    page.goto(path)
    expect(page.locator('#level-title')).to_have_text('確認交換目標')
    page.get_by_role('link',name='條件與推薦',exact=True).click()
    expect(page.locator('#path-tool-host #advisor-form')).to_be_visible()
    page.locator('#advisor-form > .advisor-more-fields:not(#advisor-qualification-fields) > summary').click()
    page.locator('#advisor-question').fill('關卡內尚未送出的問題')
    page.get_by_role('link',name='資格與志願',exact=True).click()
    expect(page.locator('#path-tool-host #eligibility #advisor-form')).to_be_visible()
    page.get_by_role('link',name='條件與推薦',exact=True).click()
    expect(page.locator('#advisor-question')).to_have_value('關卡內尚未送出的問題')
    page.get_by_role('link',name='收合工具',exact=True).click()
    page.locator('#self-confirm').check()
    page.get_by_role('button',name='完成這一關',exact=True).click()
    expect(page.locator('.success-state')).to_be_visible()
    page.reload()
    expect(page.locator('#self-confirm')).to_be_checked()
    # A second term shares the same school but has no completed target step.
    registry=page.request.get(f'{live_server.base_url}/account/application-paths?home_school=長庚大學').json()
    other=page.request.post(f'{live_server.base_url}/account/application-paths',data={**context,'semester':'spring','revision':registry['revision']})
    assert other.ok,other.text()
    assert other.json()['plan']['steps']=={}
    # Document forms are mounted under the same level, not copied or linked to a detached page.
    current=page.request.get(f'{live_server.base_url}/account/application-paths/{plan_id}?home_school=長庚大學').json()
    document=next(l for s in current['stages'] for l in s['levels'] if l['kind']=='file')
    page.goto(f'{live_server.base_url}/#my-application?'+urlencode(dict(plan=plan_id,view='level',level=document['id'],tool='application-center')))
    page.get_by_role('button',name='載入本計畫的文件工具',exact=True).click()
    expect(page.locator('#path-tool-host #application-center')).to_be_visible(timeout=30000)
    expect(page.locator('#application-context-form [name="semester"]')).to_have_value('第一學期')
    page.get_by_role('button',name='填寫校內申請資料',exact=True).click()
    expect(page.locator('#path-tool-host [data-university-page="application-form"]')).to_be_visible()
    assert 'tool=application-form' in page.url
    expect(page.locator('#application-journey-steps')).to_have_count(0)
    assert not errors


def test_glide_required_disabled_multiple_reset_and_programmatic_sync(page):
    page.set_content('''<form id="form"><label for="one">目的地</label><select id="one" name="one" required>
      <option value="">請選擇</option><option disabled value="blocked">不可選</option><option value="jp">日本</option></select>
      <label for="many">任務</label><select id="many" name="many" multiple><option value="a">文件</option><option value="b">簽證</option></select>
      <button type="submit">保存</button><button type="reset">重設</button></form>''')
    static=Path(__file__).parents[2]/'src/exchange_info/static'
    page.add_style_tag(path=str(static/'glide-select.css'))
    page.add_script_tag(path=str(static/'application-path-select.js'))
    page.get_by_role('button',name='保存',exact=True).click()
    one=page.get_by_role('combobox',name='目的地',exact=True)
    expect(one).to_have_attribute('aria-invalid','true')
    expect(one).to_be_focused()
    one.press('Enter');one.press('ArrowDown');one.press('Enter')
    expect(page.locator('#one')).to_have_value('jp')
    multi=page.get_by_role('combobox',name='任務',exact=True);multi.click()
    for name in ['文件','簽證']:page.get_by_role('listbox',name='任務',exact=True).get_by_role('option',name=name,exact=True).click()
    assert page.locator('#many').evaluate('s=>[...s.selectedOptions].map(o=>o.value)')==['a','b']
    multi.press('Escape');expect(multi).to_have_attribute('aria-expanded','false')
    page.get_by_role('button',name='重設',exact=True).click()
    expect(one).to_contain_text('請選擇');expect(multi).to_contain_text('選擇選項')
    page.evaluate("document.querySelector('#one').value='jp'")
    expect(one).to_contain_text('日本')
    page.evaluate("document.querySelector('#one').disabled=true")
    expect(one).to_be_disabled()


def test_alternative_recommendation_opens_a_new_plan_without_retargeting_the_current_one(page, live_server):
    from .test_planning_workspace import create_target

    _, target = create_target(page, live_server)
    context = dict(home_school='長庚大學', target_school=target, academic_year='116', departure_year='2027', semester='fall', revision=0)
    created = page.request.post(f'{live_server.base_url}/account/application-paths', data=context)
    assert created.ok, created.text()
    original_id = created.json()['plan']['id']
    route = '#my-application?' + urlencode(dict(plan=original_id, view='level', level='target', tool='advisor'))
    page.evaluate('(route)=>location.hash=route', route)
    expect(page.locator('#path-tool-host #advisor-form')).to_be_visible()
    alternative = page.locator('#advisor-result-content [data-planning-target]').nth(1)
    other_name = alternative.get_attribute('data-planning-target')
    assert other_name != target
    alternative.click()
    expect(page.get_by_role('dialog', name='新增申請計畫')).to_be_visible()
    expect(page.locator('#create-target')).to_have_value(other_name)
    expect(page.locator('#create-departure')).to_have_value('2027')
    page.get_by_role('button', name='建立計畫', exact=True).click()
    expect(page.get_by_role('dialog', name='新增申請計畫')).to_be_hidden()
    expect(page.locator('#plan-select')).not_to_have_value(original_id)
    original = page.request.get(f'{live_server.base_url}/account/application-paths/{original_id}?home_school=長庚大學').json()
    assert original['plan']['context']['target_school'] == target
    assert original['plan']['steps'] == {}


def test_public_partner_page_uses_glide_without_changing_its_switcher_behavior(page, live_server):
    page.goto(f'{live_server.base_url}/partners/germany/technical-university-of-munich?home=cgu')
    switcher = page.get_by_role('combobox', name='選擇你的就讀母校', exact=True)
    switcher.click()
    page.get_by_role('listbox', name='選擇你的就讀母校').get_by_role('option', name='國立臺北大學', exact=False).click()
    expect(page.locator('#partner-home-switcher')).to_have_value('ntpu')
    expect(page.locator('#cs-home-badge')).to_have_text('國立臺北大學')
    assert page.locator('select:not(.glide-select__native)').count() == 0
