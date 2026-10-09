"""Read three Japanese partners' real cards, packet stages and life sections."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until


CASES = [
    ('kuins', '關西國際大學', '11類初次參考件', 11,
     'https://drive.google.com/file/d/13TdQ1U2b_ZrDuvPl876SKV0UpL8KWn9R/view', '無適用年度'),
    ('komazawa', '駒澤大學', '八類初次件', 8,
     'https://drive.google.com/file/d/10GVU2yOeaLgQGUh8ch-IcgzpGKVRsH6w/view', '2025'),
    ('tohoku', '東北大學', '三類初次支援件', 3,
     'https://sup.bureau.tohoku.ac.jp/cmssys/wp-content/uploads/2025/08/Arrival-Guide-for-New-International-Students.pdf', '原件57頁'),
]


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('slug,name,initial,count,source_url,scope_text', CASES)
def test_ncu_japan3_actual_language_packet_read_scope_and_life(
    page, live_server, width, slug, name, initial, count, source_url, scope_text,
):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    enter_public_site(page, live_server, 'partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page)
    page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click()
    page.locator('#confirm-school').click()
    wait_until(page, "state.dashboard?.school_name === '國立中央大學'", timeout=60)
    if width < 700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded') == 'true':
        page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(name)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待公告')
    if width < 700:
        page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    summary = page.locator('#detail-overview .partner-student-summary')
    if slug == 'kuins':
        for text in ['N2或同等能力', 'N3或同等能力', 'JLPT證明if any', '反向套']:
            expect(summary).to_contain_text(text)
    elif slug == 'komazawa':
        for text in ['desirable', '未到N2仍可申請', '不提供Grad']:
            expect(summary).to_contain_text(text)
        programme = page.locator('#detail-overview > details').filter(has=page.locator(':scope > summary').filter(has_text='方案資料'))
        programme.locator(':scope > summary').click()
        expect(programme.locator('.university-facts')).to_contain_text('研究所地理與經營管理是全年')
    else:
        for text in ['GPA2.30／3是獎學金', '臺灣列NTU／CCU／NYCU而未列NCU', '不硬拒博士', 'M1／M2']:
            expect(summary).to_contain_text(text)
    page.locator('#ncu-source-audit > summary').click()
    source = page.locator('#ncu-source-audit-body > details').filter(has=page.locator(f'a[href="{source_url}"]')).first
    expect(source.locator(':scope > summary')).to_be_visible(timeout=60_000)
    source.locator(':scope > summary').click()
    scope = source.locator('.ncu-source-reading-scope')
    expect(scope).to_contain_text(scope_text)
    assert source.get_by_role('link', name='官方公開來源').get_attribute('href') == source_url
    if slug == 'tohoku':
        expect(scope).to_contain_text('仍可繼續公開查核')
    out = Path('/tmp/ncu-audit/browser')
    out.mkdir(parents=True, exist_ok=True)
    scope.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-japan3-{slug}-source-scope-{width}.png'))
    page.locator('#detail-tab-application').click()

    def step(title):
        return page.locator('#detail-application .workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=title)).first

    group = step(initial)
    group.locator(':scope > summary').click()
    expect(group.locator('.workflow-documents > li')).to_have_count(count)
    expect(group.locator('.workflow-rule-meta > strong')).to_have_text('規劃範圍（當期適用待確認）')
    expect(group.locator('.workflow-rule-meta')).to_contain_text('116 學年度')
    if slug == 'kuins':
        expect(group).to_contain_text('if any')
        expect(group).to_contain_text('if applicable')
        expect(group).to_contain_text('未標年度')
    elif slug == 'komazawa':
        expect(group).to_contain_text('母校email全部件')
        expect(group).to_contain_text('700000')
        expect(group).to_contain_text('Original Copy')
    else:
        for title, documents in [('教授事前內諾與四類資料', 4), ('四類指定資料／財力條件', 4), ('日文Pledge', 1)]:
            later = step(title)
            later.locator(':scope > summary').click()
            expect(later.locator('.workflow-documents > li')).to_have_count(documents)
        expect(step('教授事前內諾與四類資料')).to_contain_text('內諾不是錄取')
        expect(step('日文Pledge')).to_contain_text('IPLA排除')
        coe = step('四類指定資料／財力條件')
        expect(coe.locator(':scope > summary')).to_contain_text('校方COE通知後（可早於正式錄取）')
        expect(coe).to_contain_text('收到校方正式COE通知後')
        expect(coe).to_contain_text('並非所有申請人可立即辦理')
        for text in ['再次上傳護照PDF', 'Proceeding', 'ID card／舊護照', 'JASSO證明與資料核定與否皆禁用']:
            expect(coe).to_contain_text(text)
        expect(step('銀行：只有JASSO')).to_be_visible()
        pledge = step('日文Pledge')
        form = pledge.get_by_role('link', name='官方參考表格（當期適用待確認）').first
        assert form.get_attribute('href') == 'https://www.insc.tohoku.ac.jp/english/wp-content/uploads/2024/09/e0425d27f1a8f5efde2a36e0b40b8741.pdf'
    group.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-japan3-{slug}-programme-documents-{width}.png'))
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    life = page.locator('#destination-official-content')
    if slug == 'kuins':
        for text in ['30000–47000', '所得申報', '指定校外宿舍', '2／4年']:
            expect(life).to_contain_text(text)
    elif slug == 'komazawa':
        for text in ['room5000', 'room10000', 'utilities30000', 'utilities20000', 'deposit30000', '不保證全部utilities免費']:
            expect(life).to_contain_text(text)
    else:
        for text in ['38500', '10280', 'I沒有rescue', 'Category B', '只有JASSO', '學位學費調整']:
            expect(life).to_contain_text(text)
    life.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-japan3-{slug}-life-content-{width}.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
