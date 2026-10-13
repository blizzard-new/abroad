"""Faculty restrictions and physical PDF pages remain traceable after full reading."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentyeighth'


def test_eight_originals_and_seventeen_physical_pages_are_read():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentyeighth-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 8 and sum(len(r['pages_reviewed']) for r in ledger) == 17
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == source['sha256'] == row['source_sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_nau_sources_stay_with_flagstaff_not_tucson():
    mappings = {r['row_id']: r for r in json.loads((ROOT / 'sources/ncu/2026-10-08/source-map-candidates.json').read_text())}
    nau_ids = {'1Pv7Sy8im0xCmvBGkZQk4JfITr0t3iLMC', '1BXTeoOlQECl9TMR4sISlJQPyUjt6bwU7', '1Bqbinel4T1rSs7y1mw0d6MAsfk1fdfUQ'}
    assert nau_ids <= set(mappings['ncu-105']['files'])
    assert not nau_ids & set(mappings['ncu-109']['files'])
    assert '1AnG1Xklcp86rE396xF6E0C1Uz_Lomeby' in mappings['ncu-109']['files']
    assert all('北亞利桑那' not in item['label'] for item in mappings['ncu-109']['matched_entries'])


def test_new_year_reference_does_not_approve_quota_or_arrival_paperwork():
    from exchange_info import storage
    ws = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    steps = {s.rule_id: s for w in ws for s in w.steps}
    docs = steps['ncu-075-host-apply'].document_requirements
    assert len(docs) == 2
    assert all(d.stage == 'student_application' and d.needs_confirmation and d.applicability_status == 'reference_only' for d in docs)
    assert not any(any(term in d.name for term in ['居留', '住址', '醫保', '簽證']) for d in docs)
    assert all(w.review_status == 'pending_review' for w in ws)
    assert not any(s.deadline_reminder_eligible for w in ws for s in w.steps)
    recs = json.loads((DOCS / 'added-host-records.json').read_text())
    text = lambda rid, key: ' '.join(recs[rid]['fields'][key]['points'])
    assert '房價均未標計價週期' in text('ncu-075', 'housing')
    assert '三個月票不是月票' in text('ncu-075', 'cost')
    assert '不是最低30' in text('ncu-015', 'courses')
    assert '工程學位B2為必要' in text('ncu-068', 'language')
    assert '個人自行買的保單不能豁免' in text('ncu-109', 'insurance')
    assert '最低3.5' in text('ncu-105', 'language')


def test_deusto_image_requirements_have_sha_bound_manual_transcription():
    sources = json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))
    s = next(s for s in sources if s['id'] == '1VjEap3Ca0WyulBsNZ24yNQ8hlIoPH-9C')
    assert 'compulsory for Engineering' not in s['pages'][0]['text']
    assert 'compulsory for Engineering' in s['page_transcriptions'][0]['text']
    assert s['sha256'] == s['visual_review']['source_sha256']
    assert s['content_status']['all_pages_read']
