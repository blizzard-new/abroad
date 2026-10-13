"""Original-year references and conditional paperwork do not establish 116 places."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.ncu_student_view import fetch_ncu_partner_universities
from exchange_info.ncu_source_coverage import indexable_source_text

ROOT=Path(__file__).parents[1]
S=ROOT/'sources/ncu/2026-10-11'
B=ROOT/'src/exchange_info/official_data/ncu'
D=ROOT/'docs/data/ncu-completion-20261011/resume/fourteenth'


def unpack(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def test_fourteenth_originals_and_partial_reading_boundaries():
    sources={r['id']:r for r in unpack(B/'source-evidence.json.gz')}
    originals=unpack(S/'resume-fourteenth-original-responses.json.gz')
    manifest=json.loads((D/'reading-manifest.json').read_text())
    assert len(originals)==len(manifest['new_source_ids'])==45
    assert len(manifest['old_candidate_readings'])==16
    full=visual=0
    for raw in originals:
        r=sources[raw['source_id']]
        assert hashlib.sha256(base64.b64decode(raw['raw_base64'])).hexdigest()==r['sha256']
        assert r['reading_review']['source_sha256']==r['sha256']
        if r['reading_review']['full_document_read']:
            assert r['format']=='pdf'
            assert r['visual_review']['pdf_pages_reviewed']==list(range(1,len(r['pages'])+1))
            full+=1
        for page in r.get('visual_review',{}).get('rendered_pages',[]):
            assert hashlib.sha256((ROOT/page['artifact']).read_bytes()).hexdigest()==page['render_sha256']
            visual+=1
    assert (full,visual)==(7,39)
    cuk=sources['ncu-155-resume14-cuk-factsheet']
    assert not cuk['native_text_available']
    assert not any(p['text'].strip() for p in cuk['pages'])
    assert 'USD 8,453' in indexable_source_text(cuk)
    assert 'Songsim Main Campus' in indexable_source_text(cuk)
    for sid in ['ncu-197-resume14-um-application-guide','ncu-197-resume14-um-visa-guide','ncu-147-resume14-inha-english-track','ncu-155-resume14-cuk-courses']:
        assert not sources[sid]['reading_review']['full_document_read']
    for sid in manifest['old_candidate_readings']:
        assert sources[sid]['reading_review']['source_sha256']==sources[sid]['sha256']
    corrections=json.loads((S/'website-corrections.json').read_text())
    for rid in ['ncu-155','ncu-147']:
        fix=corrections[rid]
        assert fix['country']=='南韓'
        assert sources[fix['identity_source_id']]['sha256']==fix['source_sha256']


@pytest.mark.parametrize('row,name,documents', [('ncu-155','The Catholic University of Korea',9),('ncu-147','Inha University',12),('ncu-197','University of Malaya',12)])
@pytest.mark.parametrize('admission,housing',[('unknown','unknown'),('accepted','on_campus')])
def test_fourteenth_reference_packets_remain_pending(tmp_path,row,name,documents,admission,housing):
    p=next(p for p in fetch_ncu_partner_universities() if name in p.school_name)
    assert p.quota is None and p.availability_status=='agreement_only'
    client=TestClient(create_app(tmp_path))
    w=client.get('/application-workflow',params={'home_school':'NCU','school':p.school_name,'academic_year':'116'}).json()
    assert w['review_status']=='pending_review' and w['published_at'] is None
    host=[s for s in w['steps'] if s['rule_id'].startswith(row+'-host-')]
    assert len(host)==5
    assert all(s['deadline_at'] is None and not s['deadline_reminder_eligible'] for s in host)
    catalog=client.get('/application-center/catalog',params={'school':'NCU','target_school':p.school_name,'academic_year':'116','host_admission_status':admission,'housing_choice':housing}).json()
    items=[d for d in catalog['items'] if d['applicability']]
    assert len(items)==documents
    assert all(d['applicability']['status']=='needs_confirmation' and not d['download_available'] for d in items)
    raw=json.loads((S/'reviewed-host-records.json').read_text())[row]
    initial=next(s for s in raw['host_document_stages'] if s['id']=='initial-reference')
    if row=='ncu-155':
        assert '超過一學期' in p.eligibility and '建議' in p.eligibility
        assert 'USD3,400' in p.application_info and '8,453' in p.application_info
        assert any('父母' in d.get('condition','') and d['conditional'] for d in initial['document_requirements'])
        assert '1,308,000' in p.tuition_info and '16週' in p.tuition_info
    elif row=='ncu-147':
        assert '10/19' in p.application_deadline and '10/21' in p.application_deadline and '衝突' in p.application_deadline
        recommendation=next(d for d in initial['document_requirements'] if '必填推薦函' in d['name'])
        assert not recommendation.get('conditional',False)
        assert any('研究所' in d.get('condition','') for d in initial['document_requirements'])
        assert '1,300,000' in p.tuition_info and '包含住宿和餐食' in p.tuition_info
    else:
        assert 'iBT4' in p.eligibility and 'iBT80' in p.eligibility
        assert '9/16' in p.application_deadline and '9/17' in p.application_deadline
        assert '2026秋校內申請已關閉' in p.tuition_info
        assert len([d for d in initial['document_requirements'] if '確認／推薦函' in d['name']])==1
        assert 'YES' in str(raw['host_document_stages']) and '健康' in str(raw['host_document_stages'])
