"""Source scope and conditional forms must survive the NCU catalogue build."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).parents[1]
SOURCE=ROOT/'sources/ncu/2026-10-11'
BUNDLE=ROOT/'src/exchange_info/official_data/ncu'


def records():
    return json.loads((SOURCE/'reviewed-host-records.json').read_text())


def test_ktu_visual_pages_keep_blank_native_layer_and_exact_original_bytes():
    raw=json.loads(gzip.decompress((SOURCE/'resume-ktu-meiji-original-responses.json.gz').read_bytes()))
    evidence={r['id']:r for r in json.loads(gzip.decompress((BUNDLE/'source-evidence.json.gz').read_bytes()))}
    assert len(raw)==13
    for r in raw:
        assert hashlib.sha256(base64.b64decode(r['raw_base64'])).hexdigest()==r['receipt']['sha256']==evidence[r['source_id']]['sha256']
    r=evidence['ncu-091-resume-ktu-facts']
    assert len(r['pages'])==9
    assert sum(bool(p['text'].strip()) for p in r['pages'])==1
    assert r['reading_status']=='full_visual_and_native_reviewed'
    assert r['visual_review']['pdf_pages_reviewed']==list(range(1,10))
    assert r['content_status']['all_pages_read'] is True
    assert r['content_status']['all_pages_have_text'] is False
    for image in r['visual_review']['rendered_pages']:
        assert hashlib.sha256((ROOT/image['artifact']).read_bytes()).hexdigest()==image['render_sha256']
    assert any('2025/2026' in p['text'] for p in r['page_transcriptions'])


def test_ktu_versions_and_degree_migration_are_not_promoted_to_exchange_rules():
    r=records()['ncu-091']; f=r['fields']
    assert '2021' in f['host_deadline']['points'][1]
    assert 'June30' in f['host_deadline']['points'][0]
    assert 'new degree students' in f['visa']['points'][0]
    assert f['visa']['gap_only'] and f['tuition']['gap_only']
    assert '79.20' in f['housing']['points'][0]
    assert '109.62' in f['housing']['points'][1]
    project=next(d for d in r['host_documents'] if d['name']=='Final degree project application form')
    assert project['conditional'] and not project.get('official_form_verified')
    assert '未取得' in project['condition']


def test_meiji_school_specific_language_forms_and_coe_timing_survive_workflow():
    r=records()['ncu-138'];f=r['fields']
    assert any('2026/1/21' in p and '80／4.5' in p for p in f['language']['points'])
    assert any('母校章與簽名' in p for p in f['host_documents']['points'])
    assert '2027/2/2–3/8' in f['host_deadline']['points'][0]
    assert '2026Spring' in f['host_deadline']['points'][1]
    assert 'lateMarch2027' in f['courses']['points'][0] and 'August2027' in f['courses']['points'][0]
    assert '84,900' in f['housing']['points'][0] and 'May2026' in f['housing']['points'][0]
    w=next(json.loads(line) for line in (BUNDLE/'application_workflows.jsonl').read_text().splitlines() if 'Meiji University' in json.loads(line)['school_name'])
    host=next(s for s in w['steps'] if s['rule_id']=='ncu-138-host-apply')
    assert len(host['document_requirements'])==11
    plans=[d for d in host['document_requirements'] if d.get('official_form_url','').endswith('.docx')]
    assert len(plans)==4 and all(d['conditional'] and d['official_form_verified'] for d in plans)
    assert len({d['condition'] for d in plans})==4
    coe=next(s for s in w['steps'] if s['rule_id']=='ncu-138-host-coe-after-online')
    assert len(coe['document_requirements'])==2
    assert all(d['stage']=='after_application' and d['conditional'] for d in coe['document_requirements'])
    assert '不是錄取後' in coe['timing']
    assert w['review_status']=='pending_review'
    assert all(not s.get('deadline_reminder_eligible') for s in w['steps'] if s['rule_id'].startswith('ncu-138-host'))
