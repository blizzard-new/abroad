"""「合作構想示意」: three static, fictional pages served only by the CGU demo.

These tests pin the hard requirements (banner, no API/script/form, no school
emblem, no "官方合作" wording) and keep the hard-coded sample data internally
consistent (statistics vs table rows, cited sources vs content.json).
"""
import json
import re
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup
import pytest
import requests

from cgu_demo_fixture import demo_url
from exchange_info.cgu_demo import CONTENT, PREVIEW_DIR, PREVIEW_PAGES, STATIC, platform_html

BANNER = '示意畫面・虛構資料・尚未與校方串接'
PAGES = ('office', 'inquiry', 'report')
STATUSES = {'已收件', '待補件', '初審通過'}


def soup_of(name: str) -> BeautifulSoup:
    return BeautifulSoup((PREVIEW_DIR / f'{name}.html').read_text(encoding='utf-8'), 'html.parser')


def fetch(demo_url: str, name: str) -> requests.Response:
    response = requests.get(f'{demo_url}/preview/{name}')
    assert response.status_code == 200, response.text
    return response


def test_page_registry_matches_the_requested_three_pages():
    assert tuple(PREVIEW_PAGES) == PAGES
    for filename in PREVIEW_PAGES.values():
        assert (PREVIEW_DIR / filename).is_file()


@pytest.mark.parametrize('name', PAGES)
def test_pages_are_served_read_only_and_leave_no_session(demo_url, name):
    response = fetch(demo_url, name)
    assert response.headers['content-type'].startswith('text/html')
    assert 'noindex' in response.headers['x-robots-tag']
    assert 'no-store' in response.headers['cache-control']
    assert 'content-security-policy' in response.headers
    assert 'set-cookie' not in response.headers  # no demo workspace is created or touched
    assert response.text == (PREVIEW_DIR / PREVIEW_PAGES[name]).read_text(encoding='utf-8')  # served verbatim: static


def test_unknown_pages_and_traversal_attempts_are_not_served(demo_url):
    for path in ('/preview/nope', '/preview/office.html', '/preview/..%2fcontent', '/preview/%2e%2e/content.json',
                 '/preview/..\\office'):
        response = requests.get(demo_url + path)
        assert response.status_code == 404, path
        assert BANNER not in response.text


def test_pages_accept_no_writes(demo_url):
    client = requests.Session()
    client.headers['Origin'] = demo_url
    for name in PAGES:
        for method in ('post', 'put', 'patch', 'delete'):
            response = getattr(client, method)(f'{demo_url}/preview/{name}', json={'x': 1})
            assert response.status_code == 403, (name, method)


def test_preview_is_not_part_of_the_production_app(tmp_path):
    from fastapi.testclient import TestClient
    from exchange_info.api import create_app
    from exchange_info.storage import ensure_data_dirs

    data_dir = tmp_path / 'data'
    ensure_data_dirs(data_dir)
    client = TestClient(create_app(data_dir))
    for name in PAGES:
        assert BANNER not in client.get(f'/preview/{name}').text


@pytest.mark.parametrize('name', PAGES)
def test_every_page_is_pure_static_html(name):
    page = soup_of(name)
    raw = (PREVIEW_DIR / f'{name}.html').read_text(encoding='utf-8')
    # Nothing that can run, submit, embed, or phone home.
    assert not page.select('script, form, iframe, object, embed, img, picture, svg, video, audio, canvas, link[rel=preload]')
    assert not [tag.name for tag in page.find_all(True) if any(attr.startswith('on') for attr in tag.attrs)]
    assert not [tag.name for tag in page.find_all(True) if tag.has_attr('style')]
    assert not re.search(r'fetch\(|XMLHttpRequest|sendBeacon|WebSocket|javascript:', raw)
    # Only inputs that cannot be edited or submitted.
    for control in page.select('input, textarea, select, button'):
        assert control.has_attr('disabled') or control.has_attr('readonly'), control
    # Only the shared platform styles; no external or data: resources.
    styles = [link['href'].split('?')[0] for link in page.select('link[rel=stylesheet]')]
    assert styles == ['/static/brand-tokens.css', '/static/typography.css', '/static/cgu-demo-preview.css']
    for style in styles:
        assert (STATIC / style.removeprefix('/static/')).is_file()
    for link in page.select('link[href]'):
        assert link['href'].startswith('/static/')
    # Links: local pages, or a cited source that opens safely.
    sources = {item['url'] for item in json.loads(CONTENT.read_text(encoding='utf-8'))['sources']}
    for anchor in page.select('a[href]'):
        href = anchor['href']
        if href.startswith('/'):
            assert href == '/' or href.removeprefix('/preview/') in PAGES, href
        else:
            assert href in sources, href
            assert 'noopener' in anchor['rel'] and 'noreferrer' in anchor['rel'] and anchor['target'] == '_blank'


@pytest.mark.parametrize('name', PAGES)
def test_banner_is_first_in_body_and_every_page_navigates_the_set(name):
    page = soup_of(name)
    assert page.html['lang'] == 'zh-Hant'
    assert 'noindex' in page.select_one('meta[name=robots]')['content']
    first = page.body.find(True)
    assert 'pv-banner' in first['class'] and first.get_text(strip=True) == BANNER
    assert len(page.select('.pv-banner')) == 1
    nav = page.select('nav[aria-label="合作構想示意"] a')
    assert [a['href'] for a in nav] == ['/', '/preview/office', '/preview/inquiry', '/preview/report']
    assert [a['href'] for a in nav if a.get('aria-current') == 'page'] == [f'/preview/{name}']
    assert page.select_one('main h1') is not None
    assert '不代表校方採用、認證或合作' in page.select_one('footer').get_text()


def test_banner_stays_fixed_in_the_stylesheet():
    css = (STATIC / 'cgu-demo-preview.css').read_text(encoding='utf-8')
    rule = re.search(r'\.pv-banner\s*\{([^}]*)\}', css).group(1)
    assert 'position: fixed' in rule and 'top: 0' in rule


def test_no_school_emblem_and_no_official_partnership_wording():
    css = (STATIC / 'cgu-demo-preview.css').read_text(encoding='utf-8')
    assert 'url(' not in css and '@import' not in css  # no emblem or any other image can be pulled in via CSS
    strip = BeautifulSoup(platform_html(), 'html.parser').select_one('#cgu-demo-strip').get_text()
    texts = [strip, css] + [(PREVIEW_DIR / f).read_text(encoding='utf-8') for f in PREVIEW_PAGES.values()]
    for text in texts:
        assert '官方合作' not in text
        assert '校徽' not in text
    for name in PAGES:
        page = soup_of(name)
        flat = re.sub(r'\s+', '', page.get_text())
        assert '官方合作' not in flat  # also across tag boundaries


def test_strip_menu_links_the_three_pages_and_leaves_main_navigation_alone():
    original = BeautifulSoup((STATIC / 'index.html').read_text(encoding='utf-8'), 'html.parser')
    demo = BeautifulSoup(platform_html(), 'html.parser')
    menu = demo.select_one('#cgu-demo-strip #cgu-preview-menu')
    assert menu is not None and menu.name == 'details'
    assert menu.select_one('summary').get_text(strip=True) == '合作構想示意'
    assert [a['href'] for a in menu.select('a')] == ['/preview/office', '/preview/inquiry', '/preview/report']
    # The original control order and ids remain; the menu is only an addition.
    assert [b['id'] for b in demo.select('#cgu-demo-strip > button')] == ['cgu-demo-info', 'cgu-demo-seed', 'cgu-demo-reset']
    assert len(demo.select('#cgu-demo-strip span')) == 1  # cgu-demo.js appends the storage notice to the first span
    # Main navigation: identical links, and no preview entry anywhere outside the strip.
    assert [a.get('href') for a in demo.select('nav a')] == [a.get('href') for a in original.select('nav a')]
    outside = [a['href'] for a in demo.select('a[href]') if not a.find_parent(id='cgu-demo-strip') and '/preview/' in a['href']]
    assert outside == []


def test_menu_assets_are_cache_busted_together():
    demo = BeautifulSoup(platform_html(), 'html.parser')
    versions = {tag.get('href', tag.get('src')).split('?v=')[1] for tag in demo.select('[href*="cgu-demo.css"], [src*="cgu-demo.js"]')}
    assert len(versions) == 1 and versions != {'20261112-cgu-ux-2'}


# ─── /preview/office ───

def office_rows():
    rows = []
    for tr in soup_of('office').select('tbody tr'):
        cells = {td['data-label']: td for td in tr.select('td')}
        docs = tr.select('.pv-docs li')
        rows.append({
            'id': cells['收件編號'].get_text(strip=True),
            'name': cells['申請人'].get_text(strip=True),
            'dept_year': cells['系級'].get_text(' ', strip=True),
            'prefs': [li.get_text(strip=True) for li in cells['志願'].select('li')],
            'missing': [li.get_text(strip=True).removeprefix('✕').removeprefix('缺：') for li in docs if 'is-miss' in li.get('class', [])],
            'docs': len(docs),
            'status': cells['狀態'].get_text(strip=True),
            'summary': cells['文件齊全度'].select_one('.pv-docsum').get_text(strip=True),
        })
    return rows


def test_office_has_five_fictional_applications_with_simulated_receipt_numbers():
    rows = office_rows()
    assert len(rows) == 5
    ids = [row['id'] for row in rows]
    assert all(re.fullmatch(r'SIM-\d{4}-\d{4}', i) for i in ids) and len(set(ids)) == 5
    assert len({row['name'] for row in rows}) == 5
    assert {row['status'] for row in rows} <= STATUSES
    for row in rows:
        assert len(row['prefs']) == 2 and len(set(row['prefs'])) == 2  # school limit is two preferences
        assert row['docs'] == 5  # the five documents CGU requires
        assert row['dept_year'].endswith(('大二', '大三', '大四'))
        done = 5 - len(row['missing'])
        assert row['summary'].startswith(f'{done}／5')
        assert (row['status'] == '待補件') == bool(row['missing']), row  # incomplete files are exactly the 待補件 ones
    assert {row['status'] for row in rows} == STATUSES  # all three states are demonstrated


def test_office_statistics_match_the_table():
    rows = office_rows()
    stats = {dt.get_text(strip=True): dd for dt, dd in ((d.dt, d.dd) for d in soup_of('office').select('.pv-stat'))}
    assert set(stats) == {'申請數', '缺件數', '最多人填的學校'}
    assert int(re.match(r'\d+', stats['申請數'].get_text()).group()) == len(rows)
    missing_docs = sum(len(r['missing']) for r in rows)
    with_missing = [r for r in rows if r['missing']]
    text = stats['缺件數'].get_text(' ', strip=True)
    assert int(re.match(r'\d+', text).group()) == missing_docs
    assert f'涉及 {len(with_missing)} 位申請人' in text
    assert all(r['name'] in text for r in with_missing)
    breakdown = Counter(r['status'] for r in rows)
    assert all(f'{status} {count}' in stats['申請數'].get_text() for status, count in breakdown.items())
    top = Counter(school for r in rows for school in r['prefs']).most_common()
    assert len(top) < 2 or top[0][1] > top[1][1], 'a tie would make "最多人填" ambiguous'
    school, count = top[0]
    assert school in stats['最多人填的學校'].get_text() and f'{count} 位' in stats['最多人填的學校'].get_text()


def test_office_sample_data_does_not_contradict_real_cgu_rules():
    from exchange_info.cgu_demo_content import FrozenCatalogue
    import tempfile
    partners = [p.school_name for p in FrozenCatalogue(Path(tempfile.mkdtemp())).view().partners if '交換' in p.program_type]
    units = (STATIC / 'academic-units.js').read_text(encoding='utf-8')
    cgu_units = units[units.index('"長庚大學"'):units.index('"國立臺北大學"')]
    for row in office_rows():
        dept = re.sub(r'\s*大[一二三四]$', '', row['dept_year'])
        assert f'"{dept}"' in cgu_units, dept  # a real CGU department
        for school in row['prefs']:
            assert any(school in partner for partner in partners), school  # a real exchange partner
        if '香港中文大學' in row['prefs']:
            assert dept == '生物醫學工程學系', 'CUHK exchange seats are limited to the BME department'


# ─── /preview/inquiry ───

def test_inquiry_marks_matching_as_rule_based_and_cites_only_known_sources():
    page = soup_of('inquiry')
    left = page.select_one('[aria-labelledby=pv-qa-title]')
    assert left.select_one('.pv-rule-badge').get_text(strip=True) == '規則式比對，非 AI'
    sources = {item['url']: item for item in json.loads(CONTENT.read_text(encoding='utf-8'))['sources']}
    answers = left.select('.pv-ans:not(.is-nomatch)')
    assert len(answers) >= 2
    for answer in answers:
        anchor = answer.select_one('.pv-source a')
        record = sources[anchor['href']]
        assert anchor.get_text(strip=True) == record['title'] + ' ↗'  # exactly the verified source title
        assert f"查核日期：{record['checked_on']}" in answer.select_one('.pv-source small').get_text()
    nomatch = left.select_one('.pv-ans.is-nomatch')
    assert nomatch is not None and not nomatch.select('a')  # no source, so no invented answer
    assert len(left.select('.pv-q')) == len(answers) + 1


def test_inquiry_answers_repeat_only_facts_from_the_verified_content():
    text = soup_of('inquiry').select_one('[aria-labelledby=pv-qa-title]').get_text(' ', strip=True)
    corpus = json.dumps(json.loads(CONTENT.read_text(encoding='utf-8')), ensure_ascii=False)
    for fact in ('2026/11/02', '2026/12/21 17:00', '最多填列 2 個志願'):
        assert fact in text and fact in corpus
    for document in ('線上申請表', '外國語文能力證明', '1 頁讀書計畫'):
        assert document in text and document in corpus


def test_inquiry_shows_a_transferred_ticket_with_a_clearly_fictional_reply():
    right = soup_of('inquiry').select_one('[aria-labelledby=pv-ticket-title]')
    ticket = right.select_one('.pv-id').get_text(strip=True)
    assert re.fullmatch(r'SIM-Q-\d{4}-\d{4}', ticket)
    assert '已轉承辦' in right.select_one('.pv-pill').get_text()
    assert len(right.select('.pv-steps li')) == 4
    assert '同意轉交承辦' in right.select('.pv-steps li')[2].get_text()
    reply = right.select_one('.pv-reply').get_text(' ', strip=True)
    assert '示意' in reply and '不提供實際規定' in reply
    assert '虛構範例' in right.get_text()
    left = soup_of('inquiry').select_one('[aria-labelledby=pv-qa-title]')
    assert ticket in left.select_one('.is-nomatch').get_text()  # the unanswered question is the transferred one
    assert right.select_one('.pv-quote').get_text(strip=True) == left.select('.pv-q')[-1].get_text(strip=True).removeprefix('林小程（虛構學生）')


# ─── /preview/report ───

SECTIONS = ['出國前準備', '上課情形', '日常生活', '課外活動及其他']


def test_report_form_has_the_four_sections_in_order_and_cannot_be_submitted():
    page = soup_of('report')
    form = page.select_one('[aria-labelledby=pv-form-title]')
    legends = [legend.get_text(strip=True).lstrip('1234') for legend in form.select('fieldset > legend')]
    assert legends == SECTIONS
    areas = form.select('fieldset textarea')
    assert len(areas) == 4 and all(a.has_attr('readonly') and a.get_text(strip=True) for a in areas)
    assert not page.select('form')
    assert form.select_one('button.pv-submit').has_attr('disabled')
    assert form.select_one('input[type=checkbox]').has_attr('disabled')


def test_report_published_card_mirrors_the_form_and_hides_identity():
    page = soup_of('report')
    form = page.select_one('[aria-labelledby=pv-form-title]')
    card = page.select_one('[aria-labelledby=pv-card-title]')
    assert '已公開' in card.select_one('.pv-pill').get_text()
    assert [h.get_text(strip=True) for h in card.select('section > h3')] == SECTIONS
    assert [p.get_text(strip=True) for p in card.select('section > p')] == [a.get_text(strip=True) for a in form.select('textarea')]
    assert '匿名' in card.select_one('.pv-review-sub').get_text()
    assert '虛構範例' in card.get_text()
    assert len(card.select('.pv-review-title')) == 1
