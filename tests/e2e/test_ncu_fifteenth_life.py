"""Actual life cards, not only their hidden source guide, show reviewed Chinese."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

CASES=[
 ('minho','米尼奧','University of Minho', [('住宿與宿舍',['不足15天','差異未解']),('每月生活預算',['€165','2026/27'])]),
 ('nau','北亞利桑那','Northern Arizona University',[('交通與地點',['指定日期','USD20','非全年'])]),
 ('upper','上奧地利','University of Applied Sciences Upper Austria',[('住宿與宿舍',['€300','自行安排','不含餐食'])]),
 ('lab','LAB','LAB University of Applied Sciences',[('課業與教學',['芬蘭文／英文混授','技術問題','Lahti'])]),
 ('wurzburg','符茲堡','University of Würzburg',[('課業與教學',['不是正式ToR','2026/7/9','醫學系'])]),
 ('uf','佛羅里達','University of Florida',[('住宿與宿舍',['USD4,161','USD3,929','2026/27'])]),
]

@pytest.mark.parametrize('width',[390,1440])
@pytest.mark.parametrize('slug,query,name,cards',CASES)
def test_reference_life_qualifiers(page,live_server,tmp_path,width,slug,query,name,cards):
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    select_ncu(page,live_server)
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待核實')
    trigger=f'.school-detail-trigger[data-school-name*="{name}"]'
    if width<700:page.locator('#partner-table .partner-card').filter(has=page.locator(trigger)).locator(':scope > summary').click()
    page.locator(f'#partner-table {trigger}:visible').first.click()
    page.locator('#detail-tab-life').click()
    for index,(title,terms) in enumerate(cards):
        card=page.locator('#life-content .life-card').filter(has=page.locator('h3').filter(has_text=title))
        expect(card).to_have_count(1)
        text=card.locator('.life-evidence-text').first
        expect(text).not_to_contain_text('中文翻譯尚未完成')
        for term in terms:expect(text).to_contain_text(term)
        card.evaluate('(node)=>{node.scrollIntoView({block:"start"});window.scrollBy(0,-150)}')
        page.screenshot(path=str(tmp_path/f'{slug}-{width}-{index}-life.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
