"""Date conflicts, new dorm rates and conditional paperwork remain references."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.ncu_student_view import fetch_ncu_partner_universities

ROOT = Path(__file__).parents[1]
S = ROOT / 'sources/ncu/2026-10-11'
B = ROOT / 'src/exchange_info/official_data/ncu'
D = ROOT / 'docs/data/ncu-completion-20261011/resume/thirteenth'


def unpack(p):
    return json.loads(gzip.decompress(p.read_bytes()))


def test_raw_documents_and_all_66_reviewed_pdf_pages_are_sha_bound():
    sources = {s['id']: s for s in unpack(B / 'source-evidence.json.gz')}
    originals = unpack(S / 'resume-thirteenth-original-responses.json.gz')
    manifest = json.loads((D / 'reading-manifest.json').read_text())
    assert len(originals) == len(manifest['new_source_ids']) == 13
    pages = 0
    for original in originals:
        source = sources[original['source_id']]
        assert hashlib.sha256(base64.b64decode(original['raw_base64'])).hexdigest() == source['sha256']
        assert source['reading_review']['source_sha256'] == source['sha256']
        assert not source.get('current_116_applicability_verified', False)
        if source['format'] == 'pdf':
            assert source['reading_review']['full_document_read']
            assert source['reading_review']['pages_reviewed'] == list(range(1, len(source['pages']) + 1))
            for page in source['visual_review']['rendered_pages']:
                assert hashlib.sha256((ROOT / page['artifact']).read_bytes()).hexdigest() == page['render_sha256']
                pages += 1
        else:
            assert not source['reading_review']['full_document_read']
    assert pages == 66
    for sid in manifest['old_candidate_readings']:
        assert sources[sid]['reading_review']['source_sha256'] == sources[sid]['sha256']
    for sid in ['ncu-136-resume13-self', 'ncu-151-resume13-form']:
        assert sources[sid]['format'] == 'docx'
        assert 'word/document.xml' in sources[sid]['pages'][0]['text']


@pytest.mark.parametrize('row,name,documents,stages', [('ncu-136','Tsukuba',18,6), ('ncu-151','Sookmyung',7,2)])
@pytest.mark.parametrize('admission,housing', [('unknown','unknown'), ('accepted','on_campus')])
def test_packets_do_not_activate_current_quota_deadlines_or_downloads(tmp_path,row,name,documents,stages,admission,housing):
    partner = next(p for p in fetch_ncu_partner_universities() if name in p.school_name)
    assert partner.quota is None and partner.availability_status == 'agreement_only'
    client = TestClient(create_app(tmp_path))
    response = client.get('/application-workflow', params={'home_school':'NCU','school':partner.school_name,'academic_year':'116'})
    assert response.status_code == 200
    workflow = response.json()
    assert workflow['review_status'] == 'pending_review' and workflow['published_at'] is None
    host = [s for s in workflow['steps'] if s['rule_id'].startswith(row+'-host-')]
    assert len(host) == stages + 1
    assert all(s['deadline_at'] is None and not s['deadline_reminder_eligible'] for s in host)
    catalog = client.get('/application-center/catalog',params={'school':'NCU','target_school':partner.school_name,'academic_year':'116','host_admission_status':admission,'housing_choice':housing}).json()
    conditional = [d for d in catalog['items'] if d['applicability']]
    assert len(conditional) == documents
    assert all(d['applicability']['status'] == 'needs_confirmation' and not d['download_available'] for d in conditional)
    if name == 'Tsukuba':
        coe = next(s for s in host if s['rule_id'].endswith('-coe-reference'))
        assert len(coe['document_requirements']) == 11
        raw = json.loads((S / 'reviewed-host-records.json').read_text())[row]
        sponsor = [d for s in raw['host_document_stages'] for d in s['document_requirements'] if 'CoE選Supporter' in d.get('condition','')]
        assert len(sponsor) == 5 and all(d['conditional'] for d in sponsor)
        deadline = partner.application_deadline
        assert all(term in deadline for term in ['2027/3/5', '3/6', '衝突'])
        text = partner.tuition_info
        assert all(term in text for term in ['2027/4/1','33,040','92,750','51,980','48,410','8,600','既有居住期'])
    else:
        assert '男女皆可' in partner.eligibility
        assert '未列交換入學英／韓檢定門檻' in partner.eligibility
        assert '未標年annual' in partner.application_deadline
        assert '醫療檢查表尚未email取得' in partner.application_info
        assert '自動豁免' in partner.tuition_info
