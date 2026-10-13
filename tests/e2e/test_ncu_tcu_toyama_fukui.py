"""Read actual partner cards, pending host packets, source scopes and life details."""
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until

CASES = [('tcu', '東京都市大學', '十一類初次參考件', 11),
         ('toyama', '富山大學', '十類初次參考件', 10),
         ('fukui', '福井大學', '九類初次學生參考件', 9)]


@pytest.mark.parametrize('width', [390, 1440])
@pytest.mark.parametrize('slug,name,title,count', CASES)
def test_ncu_next3_real_year_scope_packet_and_life(page, live_server, width, slug, name, title, count):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    enter_public_site(page, live_server, 'partners')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    open_navigation(page)
    page.locator('#school-switcher').click()
    page.locator('[data-home-school="國立中央大學"]').click()
    wait_until(page, "state.dashboard?.school_name === '國立中央大學'", timeout=60)
    if width < 700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded') == 'true':
        page.locator('#glass-menu-toggle').click()
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill(name)
    expect(page.locator('#partner-table')).to_contain_text('本期名額待核實')
    if width < 700:
        page.locator('#partner-table .partner-card > summary').first.click()
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    summary = page.locator('#detail-overview .partner-student-summary')
    if slug == 'tcu':
        for text in ['master', '本科', 'N2／N1', '禁止打工']:
            expect(summary).to_contain_text(text)
        source_url = 'https://www.tcu.ac.jp/interchange/studentacceptance/'
        source_text = '403'
    elif slug == 'toyama':
        for text in ['AY2024Fall', 'up to2', '10／11', '2/15']:
            expect(summary).to_contain_text(text)
        source_url = 'https://drive.google.com/file/d/1OArbu2MdlYVuBbzi2RGCp7opEGwJNstH/view'
        source_text = 'AY 2024 Fall'
    else:
        for text in ['入學GPA至少2.30／3', 'JASSO', '不硬判所有A', 'JPT525', '600000／1100000']:
            expect(summary).to_contain_text(text)
        source_url = 'https://www.u-fukui.ac.jp/wp/wp-content/uploads/Life-in-Fukui-Guidebok-2024_EN.pdf'
        source_text = 'URL含2024但內頁校曆明列2026'
    page.locator('#ncu-source-audit > summary').click()
    expect(page.locator('#ncu-source-audit-body > p').first).to_contain_text('2026-10-09', timeout=60_000)
    if slug == 'tcu':
        # A 403 attempt has no original document to expand. Read its actual
        # failure and exact attempted URL instead of inventing a source page.
        source = page.locator('.ncu-unretrieved-source[data-source-id="host-tcu-inbound-ja"]')
        expect(source).to_be_visible(timeout=60_000)
        expect(source).to_contain_text('403')
        assert source.get_by_role('link', name='已查網址（本次未取得）').get_attribute('href') == source_url
    else:
        source = page.locator('#ncu-source-audit-body > details').filter(has=page.locator(f'a[href="{source_url}"]')).first
        expect(source.locator(':scope > summary')).to_be_visible(timeout=60_000)
        source.locator(':scope > summary').click()
        expect(source).to_contain_text(source_text)
        assert source.get_by_role('link', name='官方公開來源').get_attribute('href') == source_url
    if slug == 'fukui':
        archive_url = 'https://www.u-fukui.ac.jp/wp/wp-content/uploads/Application_form-3.zip'
        archive = page.locator('#ncu-source-audit-body > details').filter(has=page.locator(f'a[href="{archive_url}"]')).first
        archive.locator(':scope > summary').click()
        members = archive.locator(':scope > details > summary')
        expect(members).to_have_count(4)
        health_member = members.filter(has_text='Form3')
        expect(health_member).to_contain_text('ZIP內檔案，無PDF頁碼')
        health_member.click()
        expect(archive).to_contain_text('6  months  prior  to  the  certification')
        archive.locator(':scope > summary').click()
    out = Path('/tmp/ncu-audit/browser');out.mkdir(parents=True, exist_ok=True)
    source.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-next3-{slug}-source-{width}.png'))
    page.locator('#detail-tab-application').click()
    group = page.locator('#detail-application .workflow-step').filter(has=page.locator(':scope > summary').filter(has_text=title)).first
    group.locator(':scope > summary').click()
    expect(group.locator('.workflow-documents > li')).to_have_count(count)
    expect(group.locator('.workflow-rule-meta > strong')).to_have_text('規劃範圍（當期適用待確認）')
    if slug == 'tcu':
        expect(group).to_contain_text('僅純JP課')
        expect(group).to_contain_text('最新空白未取得')
    elif slug == 'toyama':
        expect(group).to_contain_text('4張4×3cm')
        expect(group).to_contain_text('不代表已錄取')
        expect(page.locator('#detail-application')).to_contain_text('不是精確116截止')
    else:
        expect(group).to_contain_text('certification前6月內')
        expect(group).to_contain_text('不接受本人名')
        link = group.get_by_role('link', name='官方參考表格（當期適用待確認）').first
        assert link.get_attribute('href') == 'https://www.u-fukui.ac.jp/wp/wp-content/uploads/Application_form-3.zip'
        expect(page.locator('#detail-application')).to_contain_text('非學生自行送件')
        assert not page.locator('a[href*="ufdeli.cii.u-fukui.ac.jp"]').count()
    group.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-next3-{slug}-packet-{width}.png'))
    page.locator('#detail-tab-life').click()
    page.locator('#detail-life .life-official-guide > summary').click()
    life = page.locator('#destination-official-content')
    terms = ['no excess', '家屬', '當期'] if slug == 'tcu' else (
        ['19900', '19050', '不可退', '1340', '不給學分'] if slug == 'toyama' else
        ['17600', '20400', '19400', '22700', '自付3割', '二選一', '6000', '網址含2024', '80000']
    )
    for text in terms:
        expect(life).to_contain_text(text)
    life.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-next3-{slug}-life-{width}.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
