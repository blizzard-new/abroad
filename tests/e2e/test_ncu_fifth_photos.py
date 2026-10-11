"""New original photographs and their exact grants reach the real interface."""
import re
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu
from .test_open_catalog import wait_until

@pytest.mark.parametrize('query,width,author,licence',[
 ('蘭斯',390,'Gérald Garitan','CC BY-SA 4.0'),
 ('阿沙芬堡',1280,'Aschaffenburczyk','CC BY-SA 3.0'),
 ('巴登-',390,'Wladyslaw Sojka','FAL'),
 ('巴登-',1280,'Wladyslaw Sojka','FAL'),
 ('韓國天主教',390,'poly','CC0'),
 ('南洋理工商管',390,'Sengkang','Copyrighted free use'),
 ('布勞爪哇',1280,'Lorrainevyu','CC BY 4.0'),
 ('艾爾朗加',1280,'antonov0002','CC BY 3.0'),
])
def test_fifth_photo_licence_and_campus_caption(page,live_server,query,width,author,licence, tmp_path):
    OUTPUT = tmp_path / 'browser'
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_viewport_size({'width':width,'height':1050});page.emulate_media(reduced_motion='reduce')
    select_ncu(page,live_server)
    page.locator('[data-partner-view="list"]').click();page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    wait_until(page,"document.querySelector('#partner-table .school-photo img')?.naturalWidth > 0",timeout=30)
    s=page.locator('#partner-table .partner-card > summary').first
    if s.is_visible():s.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    page.locator('#detail-tab-life').click();page.locator('#detail-life .life-official-guide > summary').click()
    figure=page.locator('.student-guide-photo-grid figure');expect(figure).to_have_count(1)
    caption=figure.locator('figcaption');expect(caption).to_contain_text(author);expect(caption).to_contain_text('授權：'+licence);expect(caption).to_contain_text('116錄取校區仍待確認')
    licence_link=caption.get_by_role('link',name='圖片授權');expect(licence_link).to_be_visible()
    if licence=='FAL':
        expect(licence_link).to_have_attribute('href','https://commons.wikimedia.org/wiki/Commons:Free_Art_License_1.3')
        expect(caption.get_by_role('link',name='攝影者網站')).to_have_attribute('href','https://www.sojka.photo/')
        expect(caption).to_contain_text('Lörrach')
    elif licence=='Copyrighted free use':
        expect(licence_link).to_have_attribute('href',re.compile(r'^https://commons\.wikimedia\.org/wiki/File:.*#Licensing$'))
        expect(caption).not_to_contain_text('授權：Public domain')
    elif query=='韓國天主教':expect(caption).to_contain_text('不是Bucheon Songsim')
    elif query=='艾爾朗加':expect(caption).to_contain_text('不能當作已核拍攝日')
    wait_until(page,"document.querySelector('.student-guide-photo-grid img')?.naturalWidth > 0",timeout=30)
    OUTPUT.mkdir(parents=True,exist_ok=True);figure.screenshot(path=str(OUTPUT/f'{query}-{width}-photo.png'));page.screenshot(path=str(OUTPUT/f'{query}-{width}-life.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
