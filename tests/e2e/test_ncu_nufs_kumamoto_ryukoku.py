"""Read the three actual student detail, document and life screens at both widths."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect
from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until, sign_in_cookie, attach_session

CASES=[('nufs','名古屋外國語大學','名古屋外國語大學 Nagoya University of Foreign Studies','NUFS初次申請與條件附件',13),
       ('kumamoto','熊本大學','熊本大學 Kumamoto University','熊本由中央取得STEP申請packet',0),
       ('ryukoku','龍谷大學','龍谷大學 Ryukoku University','龍谷初次申請與十項參考文件（JLPT有則附）',10)]


@pytest.mark.parametrize('width',[390,1440])
@pytest.mark.parametrize('slug,name,full_name,title,count',CASES)
def test_next3_reference_packets_and_living_content(page,live_server,width,slug,name,full_name,title,count):
    page.set_viewport_size({'width':width,'height':956});page.emulate_media(reduced_motion='reduce')
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    out=Path(os.environ.get('NCU_NEXT3_BROWSER_OUT','/workspace/ncu-verification-tmp/next3-browser'));out.mkdir(parents=True,exist_ok=True)
    enter_public_site(page,live_server,'partners');expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page);page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click();page.locator('#confirm-school').click()
    wait_until(page,"state.dashboard?.school_name === '國立中央大學'",timeout=60)
    if width<700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded')=='true':page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click();page.locator('#partner-search').fill(name)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待核實')
    trigger=f'.school-detail-trigger[data-school-name="{full_name}"]'
    card_term={'nufs':'GJP不強制JLPT','kumamoto':'非英語母語者須交','ryukoku':'建議300小時或N4'}[slug]
    if width<700:
        card=page.locator('#partner-table .partner-card').filter(has=page.locator(trigger))
        card.locator(':scope > summary').click()
        assert card_term in card.locator('.partner-card-summary').inner_text()
        card.scroll_into_view_if_needed()
    else:
        row=page.locator('#partner-table tr').filter(has=page.locator(trigger))
        row.locator('.partner-condition-disclosure > summary').click()
        assert card_term in row.locator('.partner-condition-disclosure').inner_text()
        row.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'{slug}-{width}-card-or-row.png'))
    page.locator(f'#partner-table {trigger}:visible').first.click()
    assert page.evaluate('new URLSearchParams(location.hash.slice(1)).get("school")')==full_name
    summary=page.locator('#detail-overview .partner-student-summary')
    terms={'nufs':['GJP','N2','N1','2026/10/31','不是所有文件三月內','不能修GJP課程'],
           'kumamoto':['packet','三年級','594,600','平台加總','非英語母語者須交','非日本國籍學生','一次性付款'],
           'ryukoku':['建議','300','N4','JEP','正式結果','證件照','護照照片頁','正式成績單','有則附']}
    for toggle in summary.locator('.partner-summary-more > summary').all():toggle.click()
    for term in terms[slug]:assert term in summary.inner_text(),term
    summary.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-overview.png'),full_page=True)
    page.locator('#ncu-source-audit > summary').click()
    expect(page.locator('#ncu-source-audit-body > p').first).to_contain_text('2026-10-09',timeout=60_000)
    if slug!='nufs':
        ident='host-kumamoto-next3-isa-address' if slug=='kumamoto' else 'host-ryukoku-next3-syllabus-index'
        failure=page.locator(f'.ncu-unretrieved-source[data-source-id="{ident}"]')
        expect(failure).to_be_visible(timeout=60_000)
        expect(failure).to_contain_text('403' if slug=='kumamoto' else '入口')
        failure.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-source-gap.png'))
    page.locator('#detail-tab-application').click();application=page.locator('#detail-application')
    group=application.locator('.workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=title)).first
    group.locator(':scope > summary').click()
    expect(group.locator('.workflow-documents > li')).to_have_count(count)
    expect(group.locator('.workflow-rule-meta > strong')).to_have_text('規劃範圍（當期適用待確認）')
    if slug=='nufs':
        for term in ['擇一','父母帳戶','有病況','無則免','線上宿舍規則同意勾選']:
            expect(group).to_contain_text(term)
    elif slug=='kumamoto':expect(group).to_contain_text('未取得')
    else:
        for term in ['不能Xray可其他結核檢查','正式結果','零學習也交','證件照','護照照片頁','正式成績單','有則附']:
            expect(group).to_contain_text(term)
    group.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-packet.png'))
    titles={'nufs':['NUFS審查與COE代辦','NUFS取得COE後申請學生簽證','NUFS依指定到達安排航班及接送','NUFS入寮、新生說明會、登記與NHI'],
            'kumamoto':['熊本录取後核對COE材料','熊本COE及入學許可後申請學生簽證','熊本指定日自行購票與提供行程','熊本抵達、定址與註冊準備'],
            'ryukoku':['龍谷審查錄取與COE代辦','龍谷收到COE後申請學生簽證','龍谷核對簽證與暫定入寮後安排航班','龍谷到校新生說明會、NHI與銀行扣款']}
    phase_terms=['錄取與COE','簽證準備','機票與行程','到校準備']
    groups=[]
    for stage_title,phase in zip(titles[slug],phase_terms):
        g=application.locator('.workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=stage_title)).first
        expect(g.locator(':scope > summary')).to_contain_text(phase);g.locator(':scope > summary').click();groups.append(g)
    groups[0].scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-coe-visa.png'))
    groups[-1].scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-arrival.png'))
    page.locator('#detail-tab-life').click();page.locator('#detail-life .life-official-guide > summary').click()
    life=page.locator('#destination-official-content')
    living={'nufs':['3.5萬','6,600','NHI','80%'],
            'kumamoto':['plan','9–16','7/17','一月','平台加總','一次性付款','15,000'],
            'ryukoku':['1,960','1,980','5日與7日','1,500–2,000','Pledge','無日本可用帳戶']}
    for term in living[slug]:expect(life).to_contain_text(term)
    life.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{slug}-{width}-life.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors


@pytest.mark.parametrize('width',[390,1440])
def test_ryukoku_corrected_catalog_and_stage_checkboxes_save_to_account(page,live_server,width):
    """Use the existing stage checklist, actual 14 reference items and saved account state."""
    import json
    import requests
    RYU_INITIAL=['證件照（Passport-style ID Photo）','護照照片頁影像','正式成績單（Official Transcript）','JLPT成績證明（有則附；不是全員必交）']
    RYU_HOUSING=['NASIC入寮日期回覆件（申請校方宿舍者；NASIC另送，原件未取得）','NASIC Pledge（申請校方宿舍者；本人簽名，原件未取得）']
    RYU_ARRIVAL=['日本銀行帳戶開戶表（入寮時無日本可用帳戶者；入寮後發，原件未取得）','在留卡影本（入寮時無日本可用帳戶者的開戶附件）']

    session=sign_in_cookie(live_server,school='國立中央大學')
    live_server.verify_student(session['profile']['id'],university='國立中央大學')
    attach_session(page,live_server,session)
    page.set_viewport_size({'width':width,'height':956});page.emulate_media(reduced_motion='reduce')
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    out=Path(os.environ.get('NCU_NEXT3_BROWSER_OUT','/workspace/ncu-verification-tmp/next3-browser'));out.mkdir(parents=True,exist_ok=True)
    enter_public_site(page,live_server,'application-center')
    wait_until(page,"state.dashboard?.school_name === '國立中央大學' && !state.applicationLoading && state.accountWorkspaceLoadingCount === 0",timeout=60)
    target=page.locator('#application-target-school')
    name=target.locator('option').filter(has_text='Ryukoku University').first.get_attribute('value')
    target.select_option(name)
    expect(page.locator('#application-requirement-list [data-document-applicability="needs_confirmation"]')).to_have_count(14)
    for group in page.locator('#application-requirement-list .application-requirement-group').all():
        if group.get_attribute('open') is None:group.locator(':scope > summary').click()
    for document in RYU_INITIAL+RYU_HOUSING+RYU_ARRIVAL:
        item=page.locator('.application-requirement-item').filter(has=page.locator(':scope > div > strong').filter(has_text=document))
        expect(item).to_have_count(1);expect(item).to_be_visible()
        expect(item).to_contain_text('116當期')
        assert item.get_by_text('下載校方正式表格',exact=True).count()==0
    page.locator('#ncu-host-admission').select_option('accepted')
    page.locator('#ncu-housing-choice').select_option('on_campus')
    expect(page.locator('#application-requirement-list [data-document-applicability="needs_confirmation"]')).to_have_count(14)
    page.locator('#application-requirement-list').scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'ryukoku-{width}-corrected-catalog.png'),full_page=True)
    page.evaluate("location.hash='#overview'")
    expect(page.locator('#multi-plan-workspace')).to_be_visible()
    page.locator('#multi-plan-settings > summary').click()
    page.locator('#multi-plan-preferences select').nth(0).select_option(name)
    page.locator('#multi-plan-preferences button').click()
    expect(page.locator('#multi-plan-status')).to_contain_text('1 個志願')
    branch=page.locator('.multi-plan-branch').filter(has=page.locator(':scope > summary').filter(has_text='Ryukoku University'))
    branch.locator(':scope > summary').click()
    saved_ids=[]
    stages=[(RYU_INITIAL,10),(RYU_HOUSING,2),(RYU_ARRIVAL,2)]
    for documents,count in stages:
        task=branch.locator('.multi-plan-task').filter(has=page.locator('.document-applicability > strong').filter(has_text=documents[0]))
        expect(task).to_have_count(1)
        # Pending references stay in the confirmation list, excluded from the
        # active document/tool link until the institutional conditions are met.
        reference=task.locator('.document-applicability[data-document-applicability="needs_confirmation"]')
        expect(reference).to_have_count(count)
        for document in documents:
            item=reference.filter(has=page.locator(':scope > strong').filter(has_text=document))
            expect(item).to_be_visible();expect(item).to_contain_text('116當期')
        checkbox=task.locator('[data-multi-task]');saved_ids.append(checkbox.get_attribute('data-multi-task'))
        checkbox.check();expect(checkbox).to_be_checked()
        wait_until(page,"document.querySelector('#account-workspace-sync-label').textContent === '已同步'",timeout=60)
        expect(page.locator(f'[data-multi-task="{saved_ids[-1]}"]')).to_be_checked()
        page.screenshot(path=str(out/f'ryukoku-{width}-{count}-{len(saved_ids)}-task-checked.png'))
    wait_until(page,"document.querySelector('#account-workspace-sync-label').textContent === '已同步'",timeout=60)
    response=requests.get(f'{live_server.base_url}/account/workspace',headers={'Authorization':f"Bearer {session['access_token']}"},params={'home_school':'國立中央大學'},timeout=10)
    assert response.status_code==200;workspace=response.json()['workspace']
    for key in saved_ids:
        assert workspace['preparation_tasks'][key]['status']=='ready'
        assert workspace['application_progress'][name][key] is True
    (out/f'ryukoku-{width}-saved-checklist.json').write_text(json.dumps({'home_school':'國立中央大學','school':name,'task_ids':saved_ids,'preparation_tasks':{k:workspace['preparation_tasks'][k]for k in saved_ids},'application_progress':{k:workspace['application_progress'][name][k]for k in saved_ids}},ensure_ascii=False,indent=2)+'\n')
    page.reload();expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    expect(page.locator('#multi-plan-status')).to_contain_text('1 個志願')
    branch=page.locator('.multi-plan-branch').filter(has=page.locator(':scope > summary').filter(has_text='Ryukoku University'))
    if branch.get_attribute('open') is None:branch.locator(':scope > summary').click()
    for key in saved_ids:expect(branch.locator(f'[data-multi-task="{key}"]')).to_be_checked()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
