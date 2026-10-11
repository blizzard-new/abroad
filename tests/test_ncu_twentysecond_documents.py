"""Faculty restrictions and physical PDF pages remain traceable after full reading."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentysecond'


def test_nine_originals_and_nineteen_physical_pages_are_read():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentysecond-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 9 and sum(len(r['pages_reviewed']) for r in ledger) == 19
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == source['sha256'] == row['source_sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_home_restrictions_are_not_erased_by_general_or_old_documents():
    rows = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())
    txt = lambda rid, field: '\n'.join(rows[rid]['fields'][field]['points'])
    assert '至少四學期法語學習' in txt('ncu-024', 'language')
    assert '70%學分在ESTRI、30%在院外' in txt('ncu-024', 'courses')
    assert '標為必修' in txt('ncu-024', 'courses')
    assert '不能將封面年度套到舊日期' in txt('ncu-026', 'study_period')
    assert '只給平均房租380歐元' in txt('ncu-026', 'cost')
    assert rows['ncu-026']['fields']['host_deadline']['sources'] == [{'id': '1KVdmF30Mh8sfc3s3XZ2Ndp4OjVvUXoIa', 'page': 2}]
    assert '大學部已完成至少兩年' in txt('ncu-032', 'eligibility')
    assert '大學部法語B1、碩士法語B2' in txt('ncu-032', 'language')
    assert '無法湊齊完整全英學習協議' in txt('ncu-032', 'courses')
    assert '限外校土木工程學院或媒體學院的媒體研究專業' in txt('ncu-040', 'eligibility')
    assert '德語低於B1的交換生' in txt('ncu-040', 'language')
    assert '註冊日明列必須本人到場' in txt('ncu-040', 'arrival')
    assert '不是學費' in txt('ncu-040', 'tuition')
    assert '分兩組限制' in txt('ncu-065', 'eligibility')
    assert '工業自動化春' in txt('ncu-065', 'courses')
    assert '物聯網秋' in txt('ncu-065', 'courses')
    assert all(rows['ncu-065']['fields'][k]['gap_only'] for k in ['host_deadline', 'host_documents', 'housing', 'cost'])


def test_partial_attachment_evidence_does_not_create_invented_documents():
    from exchange_info import storage
    workflows = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    steps = {s.rule_id: s for w in workflows for s in w.steps}
    docs = steps['ncu-032-host-apply'].document_requirements
    assert len(docs) == 1
    assert '其餘附件待核' in docs[0].name
    rows = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())
    assert all(not rows[rid]['host_documents'] for rid in ['ncu-024', 'ncu-026', 'ncu-040', 'ncu-065'])
    assert all(w.review_status == 'pending_review' for w in workflows)
    assert not any(s.deadline_reminder_eligible for w in workflows for s in w.steps)
    from exchange_info.ncu_student_view import fetch_ncu_partner_universities
    assert all(p.quota is None and p.availability_status == 'agreement_only' for p in fetch_ncu_partner_universities())
