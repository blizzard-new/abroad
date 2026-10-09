"""Classify the original 67 gaps and preserve every pre-follow-up field state.

Reads the immutable 89217e1 matrix through git, never edits that commit/evidence.
An exhausted public search is bounded to listed pages/queries, not a statement
that a university has not announced or will not provide the material.
"""
from __future__ import annotations

import json
import csv
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'src/exchange_info/official_data/tku'
BASELINE = '89217e19d55f3ff615964594e5f83eeb6156ba85'
MAPPED = {('seikei', 'transport'), ('seikei', 'host_study_period'),
          ('uec', 'host_programme_mapping'), ('nagasaki', 'living_costs')}
CONFLICT_KEYS = {'home_eligibility', 'department_to_oicsa_deadline'}
EXTRA_CONFLICTS = {('ritsumeikan', 'living_costs'), ('nagasaki', 'host_study_period'),
    ('nagasaki', 'host_documents'), ('nagasaki', 'latest_forms'),
    ('seikei', 'host_calendar'), ('uec', 'host_language')}
FOLLOWUP = {
    'ritsumeikan': ['ritsumeikan-howto-2027', 'ritsumeikan-2027-guide', 'ritsumeikan-fees',
                    'ritsumeikan-kinugasa-housing', 'ritsumeikan-bkc-housing', 'ritsumeikan-oic-housing'],
    'nagasaki': ['nagasaki-nics-2027', 'nagasaki-form-a-online', 'nagasaki-pledge',
                 'nagasaki-form-c', 'nagasaki-programmes-followup', 'nagasaki-dual-degree-excluded', 'nagasaki-calendar', 'nagasaki-courses'],
    'seikei': ['seikei-2027-sheet', 'seikei-host-followup', 'seikei-calendar-followup'],
    'uec': ['jp-revision-attachment-2', 'uec-application-followup', 'uec-courses-followup',
            'uec-program', 'uec-costs', 'uec-residence', 'uec-national-insurance', 'uec-private-insurance'],
}
DEPARTMENTS = {
    'tku-finance-department-original': ('財務金融學系', '2026-09-16T12:00:00+08:00', 'B1001', None),
    'tku-im-department-original': ('資訊管理學系', '2026-09-16', '系辦', '2026-09-17T17:00:00+08:00'),
    'tku-ins-department-original': ('保險學系', '2026-09-16T12:00:00+08:00', '系辦／系主任簽章', None),
    'tku-ai-department-original': ('人工智慧學系', '2026-09-16T17:00:00+08:00', '系辦', None),
    'tku-ic-department-original': ('資訊傳播學系', None, '傳播館O304', None),
}
SEARCHES = [
    dict(query='site:tku.edu.tw "2027-2028" "第二次" "9月30" "系"', outcome='中央更正可核實；未取得上述五系更正後收件或送國際處日期。'),
    dict(query='site:fedu.uec.ac.jp "JUSST" "2027"', outcome='未取得JUSST2027專屬表單、行事曆、提名及到校通知；MEXT2027學位入學不同計畫，排除。'),
    dict(query='site:seikei.ac.jp "2027" "exchange" "application" "housing"', outcome='2027 information sheet可用；一般申請表內容及精確住房截止仍未取得。'),
    dict(query='site:nagasaki-gaigo.ac.jp "NICS" "2027" "奨学金"', outcome='核對NICS2027及受入計畫總覽；二重學位2025獎學金排除，未核實NICS本期獎助。'),
    dict(query='site:ritsumei.ac.jp "SKP" "2027" "housing" "deadline"', outcome='2027簡章與申請頁；正式住宿申請錄取後另通知，未取得確切日。RWJP短期語言課不同計畫，排除。'),
]


def build():
    old = json.loads(subprocess.check_output(['git', 'show',
        f'{BASELINE}:src/exchange_info/official_data/tku/completeness_matrix.json'], cwd=ROOT))
    current = json.loads((BUNDLE / 'completeness_matrix.json').read_text())
    sources = {s['id']: s for s in json.loads((BUNDLE / 'sources.json').read_text())}
    schools = {s['id']: s for s in current['schools']}

    def evidence(source_id):
        s = sources[source_id]
        return {key: s.get(key) for key in ['id', 'source_url', 'applicable_year', 'role',
            'checked_at', 'http_status', 'open_status', 'sha256', 'local_file', 'review_note']}

    rows = []
    for school in old['schools']:
        if school['selection_status'] != 'listed':
            continue
        slug = school['id'].rsplit('-', 1)[-1]
        cells = {c['key']: c for c in schools[school['id']]['fields']}
        for cell in school['fields']:
            if cell['status'] == 'verified':
                continue
            key = cell['key']; pair = slug, key
            initial = 4 if pair in MAPPED else 2 if key in CONFLICT_KEYS or pair in EXTRA_CONFLICTS else 1 if key == 'latest_forms' and slug in {'ritsumeikan', 'seikei'} else 3
            after = cells[key]
            resolved = after['status'] == 'verified'
            if resolved:
                category = 4
                action = '已補映射；核實範圍及仍未知的子項見current_field.reason/value，不代表全部申請準備完成。'
            elif key in CONFLICT_KEYS or key == 'department_deadline' or pair in EXTRA_CONFLICTS:
                category = 2
                action = '需淡江或外校承辦提供適用本梯的書面釐清；不能以優先順序或猜測消除矛盾。'
            else:
                category = 1
                action = '在列出的公開來源與本次搜尋範圍內未取得足以升級當期狀態的內容；須承辦／提名者通知／新版原件，或於官網更新後再查。'
            ids = list(FOLLOWUP[slug])
            if key.startswith('department_') or key == 'home_eligibility':
                ids = ['jp-revision', 'jp-revision-attachment-1', 'jp-revision-attachment-2', *DEPARTMENTS]
            if key == 'visa_residence':
                ids = ['tku-visa-followup', 'japan-student-visa']
            rows.append(dict(partner_id=school['id'], school_name=school['school_name'], key=key,
                initial_category=initial, category_after_review=category, resolved=resolved,
                original_field=cell, current_field=after, public_entries_checked=[evidence(s) for s in ids],
                checked_at='2026-10-08', next_action=action,
                non_announcement_claim=False, human_contact_performed=False))
    assert len(rows) == 67 and len({(r['partner_id'], r['key']) for r in rows}) == 67
    assert sum(r['resolved'] for r in rows) == len(MAPPED)
    departments = [dict(department=name, source=evidence(s), original_student_deadline=deadline,
        original_delivery_location=location, original_forwarding_deadline=forward,
        applicability='原公告時程；中央9/16更正為9/23–9/30，未核實本系更正後時程。',
        current_student_deadline=None, current_forwarding_deadline=None, status='needs_confirmation')
        for s, (name, deadline, location, forward) in DEPARTMENTS.items()]
    payload = dict(baseline_commit=BASELINE, checked_at='2026-10-08', original_gap_count=67,
        category_definitions={1:'已查列出的公開來源仍無適用內容；限定此次查核範圍，不代表官方尚未公告或永遠無法取得。',
            2:'來源矛盾／更正後適用性待官方釐清。', 3:'仍可查核，優先追查。', 4:'原官方內容可用但未正確映射；已修正。'},
        initial_counts=dict(Counter(r['initial_category'] for r in rows)),
        after_review_counts=dict(Counter(r['category_after_review'] for r in rows)),
        resolved_count=sum(r['resolved'] for r in rows), remaining_count=sum(not r['resolved'] for r in rows),
        official_not_announced_claims=[], all_fields=rows, department_schedule_review=departments,
        public_searches=[dict(checked_at='2026-10-08', **s) for s in SEARCHES],
        methodology='保留89217e1的67個完整原始欄位。新增12個全文來源快照與限定官方網域搜尋；不聲稱每個關鍵字涵蓋所有公開網站。一般／舊年度來源不改為2027新版；原件提供途徑與內容核實分開。')
    (BUNDLE / 'gap_triage.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    with (ROOT/'docs/tku-source-link-check-2026-10-08.csv').open('w', newline='') as handle:
        columns = ['source_id','official_url','http_status','open_status','applicable_year','checked_at','local_file','sha256','error']
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        for s in sources.values():
            writer.writerow(dict(source_id=s['id'], official_url=s['source_url'], **{key:s.get(key,'') for key in columns[2:]}))
    print(json.dumps({k: payload[k] for k in ['original_gap_count', 'initial_counts', 'after_review_counts', 'resolved_count', 'remaining_count']}))


if __name__ == '__main__':
    build()
