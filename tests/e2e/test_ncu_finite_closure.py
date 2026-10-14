"""Final bounded NCU review reaches actual desktop and mobile cards."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

CASES = [
    ('ramon-spain', 'Ramon Llull', 'overview', '西班牙文B2'),
    ('utar-malaysia', 'Tunku', 'overview', 'RM1000'),
    ('kyutech-original', 'Kyushu Institute', 'source', '2026/3/17英文課表'),
    ('aarhus-course', 'Aarhus', 'audit', '一般一學院'),
    ('chuo-agreement', 'Chuo', 'audit', '2026年7月交換協議'),
]


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('slug,query,kind,term', CASES)
def test_final_source_scope_and_identity(page, live_server, tmp_path, width, slug, query, kind, term):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    select_ncu(page, live_server)
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(query)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待核實')
    if width < 700:
        page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    if kind == 'overview':
        card = page.locator('#detail-overview')
        expect(card).to_contain_text(term)
        if slug == 'ramon-spain':
            expect(card).not_to_contain_text('RM1000')
            expect(card).not_to_contain_text('TOEIC')
        else:
            expect(card).not_to_contain_text('西班牙文B2')
    else:
        page.locator('#ncu-source-audit > summary').click()
        card = page.locator('#ncu-source-audit-body')
        expect(card).to_contain_text(term, timeout=60_000)
        if kind == 'source':
            card = card.locator(':scope > details').filter(has_text=term).first
            card.locator(':scope > summary').click()
            expect(card).to_contain_text('全物理頁原生核讀')
            expect(card).to_contain_text('不代表中央116')
    if slug == 'utar-malaysia':
        # The visible Chinese card uses an en dash; avoid the hidden raw source copy.
        card = page.locator('#detail-overview li:visible').filter(has_text='RM1000').first
        expect(card).to_be_visible()
        card.scroll_into_view_if_needed()
    page.evaluate('() => document.fonts.ready')
    card.evaluate('''(node, needle) => {
        const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
        let text;
        while (text = walker.nextNode()) {
            const start = text.textContent.indexOf(needle);
            if (start >= 0) {
                const range = document.createRange();
                range.setStart(text, start); range.setEnd(text, start + needle.length);
                const rect = range.getBoundingClientRect();
                if (!rect.width || !rect.height) continue;
                window.scrollBy({top: rect.top - 200, behavior: 'instant'});
                return;
            }
        }
        throw new Error('Missing marker ' + needle);
    }''', term)
    page.wait_for_timeout(250)
    page.screenshot(path=str(tmp_path / f'{slug}-{width}-final.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
