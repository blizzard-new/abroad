"""Annual and programme constraints are visible on the actual four-school UI."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

CASES = [
    ('ece', 'ECE巴黎', "ECE Ecole d'Ingenieurs", '課業與教學', ['雲端工程與管理', '法授', '2025–26']),
    ('idrac', 'IDRAC', 'IDRAC Business School', '安全、醫療與保險', ['非歐盟學生抵法', '學籍證明', '不將抵法後證明改為初申必繳']),
    ('kyonggi', '京畿', 'Kyonggi University', '住宿與宿舍', ['2016', '2017–18', '不是2026或116價格']),
    ('sejong', '世宗', 'Sejong University', '課業與教學', ['研究所', '6–18學分', '2026']),
]


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('slug,query,name,title,terms', CASES)
def test_new_reviewed_hosts_visible(page, live_server, tmp_path, width, slug, query, name, title, terms):
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
    page.evaluate('() => document.fonts.ready')
    page.wait_for_timeout(350)
    card = page.locator('#life-content .life-card').filter(has=page.locator('h3').filter(has_text=title))
    for term in terms:
        expect(card).to_contain_text(term)
    card.evaluate('(node)=>{node.scrollIntoView({block:"start",behavior:"instant"});window.scrollBy({top:-150,behavior:"instant"})}')
    page.screenshot(path=str(tmp_path / f'{slug}-{width}-documents.png'))
    assert all('中文翻譯尚未完成' not in t for t in page.locator('#life-content .life-evidence-text').all_text_contents())
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
