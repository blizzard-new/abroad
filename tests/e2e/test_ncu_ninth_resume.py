"""New PDF distinctions are readable in real mobile and desktop student views."""
from pathlib import Path
import json
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

def point_screenshot(target,path):
    for detail in target.locator('xpath=ancestor::details').all():
        if detail.get_attribute('open') is None:
            detail.locator(':scope > summary').click()
    target.screenshot(path=str(path))

@pytest.mark.parametrize('query,width,overview,life',[
    ('拉羅歇爾',390,'不能自行選較低門檻','€850'),
    ('蘇黎世',1280,'TOEIC L&R785','Fully booked只指'),
    ('諾曼第',390,'TOEIC785是Grande École Master畢業要求','2025/26 Welcome p11'),
    ('佛羅里達',1280,'母校承辦帳號','Veterinary Medicine'),
    ('信州',390,'2026春原包已讀','¥95,000'),
    ('關西大學',1280,'2027春初次六類共通','未標年homestay leaflet補充'),
])
def test_ninth_year_scope_and_documents_visible(page,live_server,query,width,overview,life, tmp_path):
    OUT = tmp_path / 'browser'
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_viewport_size({'width':width,'height':1050});page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server);page.locator('[data-partner-view="list"]').click();page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待核實')
    summary=page.locator('#partner-table .partner-card > summary').first
    if summary.is_visible():summary.click()
    trigger=page.locator('#partner-table .school-detail-trigger:visible')
    if query=='關西大學':trigger=trigger.filter(has_text='關西大學 Kansai University')
    trigger.first.click()
    expect(page.locator('#detail-overview')).to_contain_text(overview)
    OUT.mkdir(parents=True,exist_ok=True)
    point_screenshot(page.locator('#detail-overview .partner-student-summary li').filter(has_text=overview).first,OUT/f'{query}-{width}-overview-point.png')
    page.locator('#detail-tab-application').click()
    if query=='諾曼第':
        initial=page.locator('#detail-application .workflow-step').filter(has_text='核對外校當期文件並依通知申請').first
        initial.locator(':scope > summary').click();expect(initial.locator('.workflow-documents > li')).to_have_count(4)
        expect(page.locator('#detail-application')).to_contain_text('EM Normandie錄取後HUB行政註冊')
    if query=='關西大學':expect(page.locator('#detail-application')).to_contain_text('初次僅住校：親屬Dormitory Guarantee')
    page.screenshot(path=str(OUT/f'{query}-{width}-application.png'))
    page.locator('#detail-tab-life').click();page.locator('#detail-life .life-official-guide > summary').click()
    expect(page.locator('#destination-official-content')).to_contain_text(life)
    point_screenshot(page.locator('#destination-official-content li').filter(has_text=life).first,OUT/f'{query}-{width}-life-point.png')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth') and not errors

@pytest.mark.parametrize('width',[390,1280])
def test_ninth_icp_210_partner_globe_and_source_note(page,live_server,width, tmp_path):
    OUT = tmp_path / 'browser'
    d=json.loads(Path('sources/ncu/2026-10-11/resume-ninth-location-review.json').read_text())['coordinate_decisions'][0]
    page.set_viewport_size({'width':width,'height':1050});page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server);page.locator('[data-partner-view="map"]').click()
    expect(page.locator('#partner-map-count')).to_have_text('214 所已定位 / 214 所符合條件',timeout=60_000)
    expect(page.locator('#map-school-select option')).to_have_count(215)
    expect(page.locator('#partner-map-status')).to_be_hidden(timeout=60_000)
    page.locator('#map-school-select').select_option(value=d['school_name'])
    expect(page.locator('#partner-map-preview .map-preview-place')).to_contain_text('Paris / rue d’Assas')
    note=page.locator('#partner-map-preview .map-location-note');note.locator('summary').click()
    expect(note).to_contain_text('2021/12/16');expect(note).to_contain_text('非Reims或Rouen')
    OUT.mkdir(parents=True,exist_ok=True);note.screenshot(path=str(OUT/f'icp-{width}-location.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
