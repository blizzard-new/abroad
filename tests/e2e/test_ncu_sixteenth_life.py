"""Reviewed Chinese is visible on real cards at phone and desktop widths."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

CASES = [
    ('normandy', '諾曼第高等', 'Ecole of Management de Normandie', '課業與教學', ['一般交換至少修讀15 ECTS', '不是116學年度']),
    ('namur', '那慕爾', 'University of Namur', '每月生活預算', ['1062', '並非學費']),
    ('zurich', '蘇黎世應用', 'Zurich University of Applied Sciences', '課業與教學', ['並非整個學程額滿', '保留矛盾']),
    ('douglas', '道格拉斯', 'Douglas College', '安全、醫療與保險', ['不在 guard.me 承保範圍', '等待期也須私人保險']),
    ('nau', '北亞利桑那', 'Northern Arizona University', '每月生活預算', ['60%', '並非一半']),
    ('wisconsin', '威斯康辛大學麥迪遜', 'University of Wisconsin-Madison', '每月生活預算', ['23466', '不是實際']),
    ('chuo', '日本中央', 'Chuo University', '課業與教學', ['學期', '矛盾保留']),
    ('kansai', '關西大學', 'Kansai University', '住宿與宿舍', ['債務保證上限', '不是須先存入']),
    ('kyutech', '九州工業', 'Kyushu Institute of Technology', '課業與教學', ['不是85頁全讀', '先備']),
    ('sungshin', '誠信女子', "Sungshin Women's University", '課業與教學', ['博士上限矛盾', '先到先得']),
    ('undip', '迪波內戈羅', 'Universitas Diponegoro', '課業與教學', ['其餘281頁', '尚未逐課核對']),
    ('tuaf', '太原農林', 'THAI NGUYEN UNIVERSITY OF AGRICULTURE AND FORESTRY (TUAF)', '每月生活預算', ['原文僅$符號', '幣別仍待確認']),
]


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('slug,query,name,title,terms', CASES)
def test_complete_legacy_chinese_cards(page, live_server, tmp_path, width, slug, query, name, title, terms):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    select_ncu(page, live_server)
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    trigger = f'.school-detail-trigger[data-school-name$="{name}"]'
    if width < 700:
        page.locator('#partner-table .partner-card').filter(has=page.locator(trigger)).first.locator(':scope > summary').click()
    page.locator(f'#partner-table {trigger}:visible').first.click()
    page.locator('#detail-tab-life').click()
    card = page.locator('#life-content .life-card').filter(has=page.locator('h3').filter(has_text=title))
    expect(card).to_have_count(1)
    body = card.locator('.life-evidence-text').first
    expect(body).not_to_contain_text('中文翻譯尚未完成')
    for term in terms:
        expect(body).to_contain_text(term)
    pending = [value for value in page.locator('#life-content .life-card .life-evidence-text').all_text_contents() if '中文翻譯尚未完成' in value]
    if pending:
        import json
        (tmp_path / 'pending-card-details.json').write_text(json.dumps({'pending': pending, 'contexts': page.evaluate('Array.from(state.lifeContextCache.values())'), 'cards': page.locator('#life-content .life-card').all_text_contents()}, ensure_ascii=False, indent=2))
        page.screenshot(path=str(tmp_path / 'pending-card-debug.png'))
    assert not pending, pending
    card.evaluate('(node)=>{node.scrollIntoView({block:"start"});window.scrollBy(0,-150)}')
    page.screenshot(path=str(tmp_path / f'{slug}-{width}-life.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
