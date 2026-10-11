"""Faculty restrictions and physical PDF pages remain traceable after full reading."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentyseventh'


def test_five_originals_and_ten_physical_pages_are_read():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentyseventh-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 5 and sum(len(r['pages_reviewed']) for r in ledger) == 10
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == source['sha256'] == row['source_sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_image_tables_keep_original_extraction_and_programme_limits():
    source_pack = json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))
    sources = {s['id']: s for s in source_pack}
    ua = sources['1lvagqWUlDqhK_qQ7Pv9TH2zpIaw716ON']
    uci = sources['1hqaCisXb0JKE2xJnmyzffbaoMi4mdQQv']
    assert '70' not in ua['pages'][0]['text']
    assert not ua['pages'][1]['text'].strip()
    assert not ua['content_status']['all_pages_have_text']
    assert ua['content_status']['all_pages_read']
    assert '79 for Engineering' in ua['page_transcriptions'][0]['text']
    assert '585' not in uci['pages'][1]['text']
    assert '$585/quarter' in uci['page_transcriptions'][0]['text']
    assert uci['visual_review']['include_native_with_selected_passages']
    reviews = json.loads((DOCS / 'added-host-records.json').read_text())
    txt = lambda rid, key: ' '.join(reviews[rid]['fields'][key]['points'])
    assert '只限大學部' in txt('ncu-109', 'eligibility')
    assert '不開放管理學院' in txt('ncu-109', 'eligibility')
    assert '不改成強制購買UCI方案' in txt('ncu-111', 'insurance')
    assert '原件寫「GAP 3.0」' in txt('ncu-111', 'eligibility')
    assert '不把食宿、保險及個人支出全打85折' in txt('ncu-111', 'tuition')


def test_new_reviews_do_not_promote_arrival_document_or_unverified_deadlines():
    from exchange_info import storage
    workflows = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    steps = {s.rule_id: s for w in workflows for s in w.steps}
    comillas = steps['ncu-073-host-apply'].document_requirements
    assert len(comillas) == 1 and comillas[0].stage == 'post_offer'
    assert comillas[0].needs_confirmation and comillas[0].applicability_status == 'reference_only'
    assert steps['ncu-109-host-apply'].document_requirements == []
    assert steps['ncu-111-host-apply'].document_requirements == []
    assert len(steps['ncu-100-host-apply'].document_requirements) == 4
    assert all(w.review_status == 'pending_review' for w in workflows)
    assert not any(s.deadline_reminder_eligible for w in workflows for s in w.steps)
