"""Capture a bounded, source-reviewed TKU follow-up without replacing old evidence.

Capture first, inspect every body, then promote with --promote. No failed URL or
search absence means 'not announced'; pre-correction departmental dates stay old.
"""
from __future__ import annotations

import argparse
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from refresh_tku_sources import read_source

BUNDLE = Path(__file__).resolve().parents[1] / 'src/exchange_info/official_data/tku'
IC_SLUG = '2026-09-12-2027-2028年赴日本姊妹校-日語組-交換生第二次聯合甄選作業簡章'
PAGES = [
    ('tku-ic-department-original', f'https://www.ic.tku.edu.tw/index.php/home/all-news/item/1027-{IC_SLUG}/1027-{IC_SLUG}.html', '2027-2028', 'home_outbound', 'Original 9/12 departmental notice; student receipt at O304 follows 9/14–17 original central schedule. No corrected departmental date verified.'),
    ('nagasaki-programmes-followup', 'https://www.nagasaki-gaigo.ac.jp/studying-abroad/receiving_program/', 'general programme directory', 'directory_reference', 'NICS/JASIN short exchange and regular degree routes distinguished; does not prove TKU graduate nomination to NICS.'),
    ('nagasaki-dual-degree-excluded', 'https://www.nagasaki-gaigo.ac.jp/studying-abroad/receiving_program/dual_degree_program/', 'general dual-degree programme, not NICS exchange', 'directory_reference', 'Third-year regular-degree admission and scholarships belong to dual degree; excluded from NICS scholarship claims.'),
    ('uec-courses-followup', 'https://www.fedu.uec.ac.jp/en/future_students/jusst/course-description/', '2026 course schedules; 2027 not verified', 'host_incoming', 'Latest linked course schedules still 2026; neither current 2027 timetable nor an official non-announcement statement obtained.'),
]
REVIEWS = {
    'tku-finance-department-original': ('2027-2028', 'home_outbound', 'Full 9/9 notice now HTTP200: finance receipt 9/16 noon at B1001, original central 9/14–17 noon. Superseded schedule; revised departmental date not verified. Earlier 502 attempt remains historical.'),
    'tku-im-department-original': ('2027-2028', 'home_outbound', 'Full original notice: departmental title receipt until 9/16, forwarding to OICSA 9/17 17:00. Predates 9/16 central correction; no revised departmental date verified.'),
    'tku-ins-department-original': ('2027-2028', 'home_outbound', 'Full 9/11 notice: department receipt 9/16 noon and original central 9/14–17. Revised departmental date not verified.'),
    'tku-ai-department-original': ('2027-2028', 'home_outbound', 'Full 9/8 notice: department receipt 9/16 17:00. Predates central correction; no revised date verified.'),
    'seikei-host-followup': ('general incoming page linking 2027 information sheet', 'host_incoming', 'Current incoming page and home-coordinator materials route read; no current blank general application forms obtained. COE-specific nominee restriction is kept separate.'),
    'seikei-calendar-followup': ('2026 academic calendar; not 2027', 'host_incoming', 'Actual PDF calendar body read; April 10 Friday matches 2026, not 2027. Linked AY2026 calendar is excluded from exact 2027 dates.'),
    'uec-application-followup': ('general JUSST application updated 2025-10-28; 2027 not verified', 'host_incoming', 'Application body and forms rechecked; generic ver22/ver23 and copyright2023 forms do not establish a 2027 version. Other 2027 MEXT degree admissions are excluded.'),
    'tku-visa-followup': ('general Taiwan-passport/COE visa guidance checked 2026-10-08', 'directory_reference', 'Current general requirements read; holiday year is 2026. This is not proof of fixed 2027 visa rules and remains reference only.'),
    **{row[0]: row[2:] for row in PAGES},
}


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    checked = datetime.now(timezone.utc).isoformat()
    def get(spec):
        source_id, url, year, role, note = spec
        try:
            row = read_source(url, source_id, output, checked)
            row['open_status'] = 'verified_open'
        except Exception as exc:
            row = dict(id=source_id, source_url=url, checked_at=checked,
                       open_status='failed', error=str(exc))
        row.update(applicable_year=year, role=role, review_note=note)
        return row
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(get, PAGES))
    (output / 'sources.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps([dict(id=r['id'], status=r['open_status'], error=r.get('error')) for r in rows]))


def promote(paths):
    rows = json.loads((BUNDLE / 'sources.json').read_text())
    by_id = {r['id']: r for r in rows}
    for path in paths:
        for row in json.loads((path / 'sources.json').read_text()):
            year, role, note = REVIEWS[row['id']]
            row.update(applicable_year=year, role=role, review_note=note,
                       applicability_review_status='reviewed_content' if row['open_status'] == 'verified_open' else 'unavailable_at_check')
            if row['id'] == 'tku-ic-department-original':
                row['text'] = row['text'].split('你的 IP:')[0]
                row['extraction_note'] = 'Visitor counter and echoed request IP excluded; notice and original schedule preserved.'
            if row.get('local_file'):
                shutil.copyfile(path / row['local_file'], BUNDLE / row['local_file'])
            by_id[row['id']] = row
    (BUNDLE / 'sources.json').write_text(json.dumps(list(by_id.values()), ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(sources=len(by_id), added_reviewed_ids=sorted(REVIEWS))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--promote', type=Path, nargs='+')
    args = parser.parse_args()
    if args.promote:
        promote(args.promote)
    else:
        if not args.output:
            parser.error('--output required for capture')
        capture(args.output)
