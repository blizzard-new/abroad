"""Five host reviews preserve document phases, programme scope and prices at both widths."""
import pytest
from playwright.sync_api import expect
from .test_ncu_resume_assets import select_ncu

CASES = [
    ('clermont', '克萊蒙', 'Clermont School of Business', None, ['非學位交換可接受B1', '不能把B1擴成所有學位']),
    ('geneva', '日內瓦', 'University of Geneva', '課業與教學', ['不能整份或主學院全部更换', '不是GPA4/4']),
    ('temple', '天普', 'Temple University（自費）', '每月生活預算', ['中央與天普兩校學雜費', '2024–25', '508美元']),
    ('dongguk', '東國', 'Dongguk University', '住宿與宿舍', ['最多一學期含假期', '南山校內雙人房無廚房']),
    ('brawijaya', '布勞爪哇', 'University of Brawijaya', None, ['ITP大於525', '不自行改成大於等於']),
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
    if slug == 'temple':
        page.locator('#detail-tab-life').click()
        page.locator('#detail-life .life-official-guide > summary').click()
        figure = page.locator('.student-guide-photo-grid figure')
        expect(figure).to_have_count(1)
        expect(figure.locator('figcaption')).to_contain_text('Audrey (Wikis Take Philadelphia)')
        expect(figure.locator('figcaption')).to_contain_text('CC BY-SA 3.0')
        expect(figure.locator('figcaption')).to_contain_text('116錄取校區仍待確認')
        expect(figure.get_by_role('link', name='圖片授權')).to_have_attribute('href', 'https://creativecommons.org/licenses/by-sa/3.0')
        page.wait_for_function("document.querySelector('.student-guide-photo-grid img')?.naturalWidth > 0")
        figure.screenshot(path=str(tmp_path / f'{slug}-{width}-photo.png'))
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
