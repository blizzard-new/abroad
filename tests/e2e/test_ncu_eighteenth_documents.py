"""Reviewed course, calendar and insurance nuances remain visible in the browser."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu


@pytest.mark.parametrize('width', [390, 1440])
def test_em_normandie_full_documents(page, live_server, tmp_path, width):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    select_ncu(page, live_server)
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill('諾曼第')
    trigger = '.school-detail-trigger[data-school-name$="Ecole of Management de Normandie"]'
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    if width < 700:
        page.locator('#partner-table .partner-card').filter(has=page.locator(trigger)).first.locator(':scope > summary').click()
    page.locator(f'#partner-table {trigger}:visible').first.click()
    page.locator('#detail-tab-life').click()
    page.evaluate('() => document.fonts.ready')
    page.wait_for_timeout(350)
    for slug, heading, terms in [
        ('seasons', '課業與教學', ['杜拜', 'BBA4', '都柏林']),
        ('grading', '課業與教學', ['7<12', '10<12', '不能自行修正']),
        ('short-term', '課業與教學', ['少於90天', '秋春皆標短期']),
        ('insurance', '安全、醫療與保險', ['居留程序完成', '空窗']),
    ]:
        card = page.locator('#life-content .life-card').filter(has=page.locator('h3').filter(has_text=heading))
        for term in terms:
            expect(card).to_contain_text(term)
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
            throw new Error('Visible evidence marker missing: ' + needle);
        }''', terms[0])
        page.screenshot(path=str(tmp_path / f'normandie-{width}-{slug}.png'))
    assert all('中文翻譯尚未完成' not in t for t in page.locator('#life-content .life-evidence-text').all_text_contents())
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
