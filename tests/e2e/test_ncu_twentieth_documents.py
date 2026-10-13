"""Five new host reviews are readable with programme constraints at both widths."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

CASES = [
    ('umlp', '瑪麗路易', 'Université Marie et Louis Pasteur (UMLP)', None, ['B2或C1', '不能因此消除特定方案C1要求']),
    ('uspn', '索邦北巴黎', 'Université Sorbonne Paris Nord', None, ['LLSHS人文語言學院', 'DELF B2', '不能用一般教師信替代']),
    ('liu', '林雪坪', 'Linkoping University', '住宿與宿舍', ['非歐盟學生分配優先', '不保證住宿', '380歐元']),
    ('xamk', '東南芬蘭', 'South-Eastern Finland University of Applied Sciences(XAMK)', '課業與教學', ['B為77–88', 'C為65–77', '小於51']),
    ('brno', '布爾諾理工', 'Brno University of Technology', '校園活動與社交', ['冬季迎新9/7–11', '原件有矛盾', '不能自行平移日期']),
]


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('slug,query,name,title,terms', CASES)
def test_five_new_host_reviews(page, live_server, tmp_path, width, slug, query, name, title, terms):
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
