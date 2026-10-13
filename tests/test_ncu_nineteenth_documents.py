"""Four newly reviewed hosts keep year, programme and document-stage limits."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/nineteenth'


def test_ten_originals_have_complete_native_and_visual_review():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-nineteenth-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 10 and sum(len(r['pages_reviewed']) for r in ledger) == 29
    assert {r['row_id'] for r in ledger} == {'ncu-005', 'ncu-013', 'ncu-149', 'ncu-158'}
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == row['source_sha256'] == source['sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert row['pages_reviewed'] == list(range(1, len(source['pages']) + 1))
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']
    blank = sources['19MZOxTIb_kO7xm24f0y4qCEig_phWvRX']['pages'][1]
    assert not blank['text'].strip()  # Blank original is reviewed, not fabricated/OCR-filled.


def test_idrac_initial_attachments_and_post_arrival_health_are_separate():
    from exchange_info import storage
    workflows = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    workflow = next(w for w in workflows if w.school_name.startswith('IDRAC'))
    initial = next(s for s in workflow.steps if s.rule_id == 'ncu-013-host-apply')
    assert len(initial.document_requirements) == 4
    assert not any('保險' in d.name or '健保' in d.name for d in initial.document_requirements)
    pre = next(s for s in workflow.steps if s.rule_id.endswith('host-prearrival-insurance'))
    arrival = next(s for s in workflow.steps if s.rule_id.endswith('host-arrival-health-registration'))
    assert pre.phase == '出發準備' and arrival.phase == '抵達後'
    assert initial.order < pre.order < arrival.order
    assert '取得接收校學籍證明後' in arrival.timing
    assert arrival.document_requirements[0].conditional
    assert '非歐盟' in arrival.document_requirements[0].condition
    assert pre.document_requirements[1].signatures == ['學生']
    assert pre.document_requirements[2].conditional
    assert all(w.review_status == 'pending_review' for w in workflows)
    assert not any(s.deadline_reminder_eligible for w in workflows for s in w.steps)


def test_conflicting_years_programmes_and_unknowns_are_retained():
    rows = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())
    txt = lambda rid, field: '\n'.join(rows[rid]['fields'][field]['points'])
    assert not rows['ncu-005']['host_documents'] and not rows['ncu-149']['host_documents']
    assert len(rows['ncu-158']['host_documents']) == 5
    assert '雲端工程與管理雖用英語名稱，原表歸在法授' in txt('ncu-005', 'courses')
    assert '2016下學期費率、2017–18住宿' in txt('ncu-149', 'housing')
    assert '韓語中心舊費率' in txt('ncu-149', 'tuition')
    assert '不是學分' in txt('ncu-013', 'study_period')
    assert 'E雖寫足夠卻未列數值區間' in txt('ncu-013', 'courses')
    assert '研究所課程不開放' in txt('ncu-158', 'eligibility')
    assert '未註計費週期' in txt('ncu-158', 'housing')
    assert '不代表免除韓國國民健康保險' in txt('ncu-158', 'insurance')
    from exchange_info.ncu_student_view import fetch_ncu_partner_universities
    assert all(p.quota is None and p.availability_status == 'agreement_only' for p in fetch_ncu_partner_universities())


def test_four_translated_addresses_keep_their_exact_source(tmp_path):
    from exchange_info.public_translation import cached_translation, standardize_terms
    rows = json.loads((DOCS / 'updated-card-translations.json').read_text())
    assert len(rows) == 4
    for row in rows:
        assert cached_translation(row['original'], row['url'], tmp_path) == (standardize_terms(row['zh']), 'translated')
        assert cached_translation(row['zh'], row['url'], tmp_path) == (standardize_terms(row['zh']), 'translated')
