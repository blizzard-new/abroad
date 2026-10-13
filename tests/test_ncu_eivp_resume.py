import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).parents[1]
SOURCE=ROOT/'sources/ncu/2026-10-11'
BUNDLE=ROOT/'src/exchange_info/official_data/ncu'


def test_eivp_keeps_2026_programme_and_graduation_scope_separate_from_116():
    audit=next(r for r in json.loads((BUNDLE/'field-audit.json').read_text()) if 'EIVP' in r['school_name'])
    f=audit['fields']
    assert f['host_documents']['status']=='missing'
    assert f['cost']['status']=='missing'
    assert 'B1 teacher' in f['language']['note']
    assert 'TOEIC785' in f['language']['note'] and '不作交換入學門檻' in f['language']['note']
    assert '2026/3/31' in f['host_deadline']['note']
    assert 'AY2027' in f['host_deadline']['unresolved']
    assert 'Diploma awarded' in f['courses']['note'] and '須確認' in f['courses']['note']
    assert '€5,055' in f['tuition']['note'] and 'free-movers' in f['tuition']['note']
    assert '不是保證' in f['housing']['note']
    workflow=next(json.loads(x) for x in (BUNDLE/'application_workflows.jsonl').read_text().splitlines() if 'EIVP' in json.loads(x)['school_name'])
    assert workflow['review_status']=='pending_review'
    host=next(s for s in workflow['steps'] if s['rule_id']=='ncu-007-host-apply')
    assert host.get('document_requirements',[])==[]
    assert all(s.get('deadline_at') is None for s in workflow['steps'] if s['rule_id'].startswith('ncu-007-host'))


def test_eivp_exact_raw_sources_and_native_pdf_pages_are_retained():
    records=json.loads(gzip.decompress((SOURCE/'resume-eivp-original-responses.json.gz').read_bytes()))
    evidence={r['id']:r for r in json.loads(gzip.decompress((SOURCE/'host-web-evidence.json.gz').read_bytes()))}
    assert len(records)==6
    for r in records:
        data=base64.b64decode(r['raw_base64']) if 'raw_base64' in r else r['raw_utf8'].encode()
        assert hashlib.sha256(data).hexdigest()==r['receipt']['sha256']==evidence[r['source_id']]['sha256']
    syllabus=evidence['ncu-007-resume-syllabus-2026']
    assert len(syllabus['pages'])==5 and '2026' in syllabus['pages'][2]['text']
    assert syllabus['reading_review']['full_document_read'] is True
    assert syllabus['reading_status']=='full_native_text_reviewed'
    assert len(evidence['ncu-007-resume-brochure-2025']['pages'])==2
    queue=json.loads(gzip.decompress((ROOT/'docs/data/ncu-completion-20261011/successful-public-unread-candidates.json.gz').read_bytes()))
    assert not {'ncu-007-site-20261011','ncu-022-site-20261011'} & {r['id'] for r in queue}
    assert evidence['ncu-023-site-20261011']['reading_status']=='not_reviewed'
    assert evidence['ncu-023-site-20261011']['research_review']['full_document_read'] is False  # Empty HTML is not a successful readable candidate.
