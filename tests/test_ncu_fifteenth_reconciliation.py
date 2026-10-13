"""Bounded public-source closure must preserve source and applicability limits."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

from exchange_info.ncu_student_view import fetch_ncu_partner_universities

ROOT=Path(__file__).parents[1]
S=ROOT/'sources/ncu/2026-10-11'
D=ROOT/'docs/data/ncu-completion-20261011/resume/fifteenth'


def unpack(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def test_finite_queue_does_not_turn_shells_into_read_rules():
    ledger=json.loads((D/'reading-ledger.json').read_text())
    sources={s['id']:s for s in unpack(S/'host-web-evidence.json.gz')}
    assert {r['reading_order_index'] for r in ledger['rows']}==set(range(223))
    assert ledger['still_unassessed_candidates']==0
    read=unavailable=0
    for row in ledger['rows']:
        src=sources[row['id']]
        assert src['sha256']==row['sha256']
        assert not row['full_document_read']
        if row['original_body_reviewed']:
            read+=1
            assert src['reading_review']['source_sha256']==src['sha256']
            assert not src['reading_review']['full_document_read']
        else:
            unavailable+=1
            assert not src.get('reading_review')
    assert (read,unavailable)==(205,18)
    assert sources['ncu-186-site-20261011']['authority_kind']=='discovery_rejected'
    assert 'nju.edu.cn' in sources['ncu-186-site-20261011']['final_url']
    originals=unpack(S/'resume-fifteenth-original-responses.json.gz')
    for raw in originals:
        assert hashlib.sha256(base64.b64decode(raw['raw_base64'])).hexdigest()==raw['receipt']['sha256']


def test_reference_prices_campuses_and_procedures_keep_qualifiers():
    records=json.loads((S/'reviewed-host-records.json').read_text())
    m=records['ncu-084']['fields']
    assert '2026/27' in str(m['cost']) and '€165' in str(m['cost'])
    assert '不足15天' in str(m['housing']) and '差異未解' in str(m['housing'])
    assert '雙人房' in str(m['housing']) and '不是保證' in str(m['housing'])
    assert '強烈建議' in str(m['arrival'])
    lab=records['ncu-080']['fields']
    assert '芬蘭文／英文混授' in str(lab['courses'])
    assert 'Lahti' in str(lab['courses']) and '技術問題' in str(lab['courses'])
    assert '約日期' in str(lab['study_period'])
    assert '不是中央116' in str(records['ncu-086']['fields']['arrival'])
    assert '不適用交換' in str(records['ncu-086']['fields']['visa'])
    assert '指定日期' in str(records['ncu-105']['fields']['transport'])
    assert '不是正式ToR' in str(records['ncu-048']['fields']['courses'])
    assert 'USD4,161' in str(records['ncu-104']['fields']['housing'])
    partners=fetch_ncu_partner_universities()
    assert len(partners)==214
    assert all(p.quota is None and p.availability_status=='agreement_only' for p in partners)


def test_changed_life_text_displays_as_chinese_without_runtime_changes():
    from exchange_info.public_translation import needs_translation
    records=json.loads((S/'reviewed-host-records.json').read_text())
    changes=json.loads((D/'field-reconciliation.json').read_text())['field_changes']
    for c in changes:
        points=records[c['row_id']]['fields'][c['field']]['points']
        assert not needs_translation(' '.join(points)), (c['row_id'],c['field'])
