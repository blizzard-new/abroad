"""Full-read additions reach the actual NCU cards on both screen sizes."""
import re
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

CASES = [
    ('pknu', '釜慶', 'Pukyong National University', '課業與教學', ['65–59', '不自行修正']),
    ('ipsa', '航太工程', 'Institute of Polytechnic Science and Aeronautics(IPSA)', '課業與教學', ['僅春季英語組', '不能把舊學年']),
    ('shinshu', '信州', 'Shinshu University', '課業與教學', ['依學生需求才寄母校', '不能承諾自動']),
    ('strasbourg', '史特拉斯堡', 'Universite de Strasbourg', '文化適應與交朋友', ['國際處行政窗口', '不是全部院系']),
    ('sungshin', '誠信女子', "Sungshin Women's University", None, ['原件抵達日', '不將自評問題當作自動錄取排除']),
]


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('slug,query,name,title,terms', CASES)
def test_full_read_details_on_actual_page(page, live_server, tmp_path, width, slug, query, name, title, terms):
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
    if title:
        page.locator('#detail-tab-life').click()
        card = page.locator('#life-content .life-card').filter(has=page.locator('h3').filter(has_text=title))
        body = card.locator('.life-evidence-text').first
        for term in terms:
            expect(body).to_contain_text(term)
        if slug in {'pknu', 'shinshu'}:
            expect(body).not_to_contain_text(re.compile(r'Fall|Spring|orientation|factsheet'))
        assert all('中文翻譯尚未完成' not in value for value in page.locator('#life-content .life-evidence-text').all_text_contents())
    else:
        page.locator('#ncu-source-audit > summary').click()
        card = page.locator('#ncu-source-audit-body')
        for term in terms:
            expect(card).to_contain_text(term, timeout=60_000)
    card.evaluate('(node)=>{node.scrollIntoView({block:"start"});window.scrollBy(0,-150)}')
    page.screenshot(path=str(tmp_path / f'{slug}-{width}-document.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
