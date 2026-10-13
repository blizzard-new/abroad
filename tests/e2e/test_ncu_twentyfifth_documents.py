"""Five new host reviews are readable with programme constraints at both widths."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

CASES = [
    ('altinbas-documents', 'Altinba', 'Altinba University', None, ['2023/9/20手冊', '完整附件清單']),
    ('altinbas-housing', 'Altinba', 'Altinba University', '住宿與宿舍', ['床位有限', '不宣稱中央116保證住宿']),
    ('altinbas-cost', 'Altinba', 'Altinba University', '每月生活預算', ['不是宿舍月租', '一般餐食與社交150歐元']),
    ('bingol-documents', 'Bingöl', 'Bingöl University', None, ['下載正文卻明寫OUTGOING', '完整初申清單仍待核']),
]


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('slug,query,name,title,terms', CASES)
def test_two_host_official_updates(page, live_server, tmp_path, width, slug, query, name, title, terms):
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
    else:
        page.locator('#ncu-source-audit > summary').click()
        card = page.locator('#ncu-source-audit-body')
    for term in terms:
        expect(card).to_contain_text(term, timeout=60_000)
    page.evaluate('() => document.fonts.ready')
    page.wait_for_timeout(350)
    card.evaluate('''(node, needle) => {
        const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
        let text;
        while (text = walker.nextNode()) {
            const start = text.textContent.indexOf(needle);
            if (start >= 0) {
                const range = document.createRange();
                range.setStart(text, start); range.setEnd(text, start + needle.length);
                window.scrollBy({top: range.getBoundingClientRect().top - 220, behavior: 'instant'});
                return;
            }
        }
        throw new Error('Evidence marker missing: ' + needle);
    }''', terms[0])
    page.screenshot(path=str(tmp_path / f'{slug}-{width}-documents.png'))
    if title:
        assert all('中文翻譯尚未完成' not in t for t in page.locator('#life-content .life-evidence-text').all_text_contents())
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
