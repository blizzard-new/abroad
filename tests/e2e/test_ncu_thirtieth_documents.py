"""Five new host reviews are readable with programme constraints at both widths."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

CASES = [
 ('kansai-homestay', 'Kansai', 'Kansai University', None, ['未明校區與交通方式', '交通費由學生負擔']),
 ('tsu-government-form', 'Tarlac', 'Tarlac State University', None, ['不能漏附實際第2頁', '不保證相同合法停留期限']),
 ('cuk-registration-example', 'Catholic', 'The Catholic University of Korea', None, ['未聲稱整份工作簿已讀', '英文介面不是全英授證據']),
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
