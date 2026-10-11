"""Named-campus coordinates and the original HKA form retain their precise scope."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
from fastapi.testclient import TestClient
from exchange_info.api import create_app
ROOT=Path(__file__).parents[1]
S=ROOT/'sources/ncu/2026-10-11'
B=ROOT/'src/exchange_info/official_data/ncu'
def read(p):return json.loads(p.read_text())
def unpack(p):return json.loads(gzip.decompress(p.read_bytes()))

def test_tenth_coordinates_use_named_markers_not_original_map_viewport():
    decisions=read(S/'resume-tenth-location-review.json')['coordinate_decisions']
    assert len(decisions)==2
    raw={x['capture']:x for x in unpack(S/'resume-tenth-visual-sourcepack.json.gz')}
    for row in decisions:
        receipt=row['coordinate_receipt']
        source=next(x for x in raw.values() if x['receipt']['sha256']==receipt['sha256'])
        assert hashlib.sha256(source['raw_utf8'].encode()).hexdigest()==receipt['sha256']
        assert row['canonical_source_rows'] and row['published_record']['precision']=='representative'
        assert not row['published_record']['current_exchange_campus_confirmed']
    reims=next(x for x in decisions if x['capture_row_id']=='ncu-023')['published_record']
    assert (reims['latitude'],reims['longitude'])==(49.243810,4.061368)
    assert '2026/7/27' in reims['note'] and 'Moulin de la Housse' in reims['note']
    omu=next(x for x in decisions if x['capture_row_id']=='ncu-132')['published_record']
    assert (omu['latitude'],omu['longitude'])==(34.5477818,135.5076042)
    assert (omu['latitude'],omu['longitude'])!=(34.54837,135.506361)
    assert '12577778258136348155' in raw['omu-named-embed.html']['raw_utf8']
    assert 'lib.omu.ac.jp/nakamozu' in omu['identity_source_url']


def test_tenth_docx_conversion_does_not_become_original_pdf_or_116_form():
    sources={x['id']:x for x in unpack(B/'source-evidence.json.gz')}
    source=sources['ncu-046-resume10-learning-agreement']
    raw=next(x for x in unpack(S/'resume-tenth-original-responses.json.gz') if x.get('source_id')==source['id'])
    assert hashlib.sha256(base64.b64decode(raw['raw_base64'])).hexdigest()==source['sha256']
    assert source['format']=='docx' and source['pages'][0]['page'] is None
    assert not source['reading_review']['full_document_read']
    assert '2026/27' in source['pages'][0]['text'] and 'EWP-Dashboard' in source['pages'][0]['text']
    assert 'Karlsruhe University of Applied Sciences' in source['pages'][0]['text']
    assert hashlib.sha256(base64.b64decode(raw['converted_pdf_base64'])).hexdigest()==source['conversion_review']['converted_pdf_sha256']
    for page in source['conversion_review']['rendered_pages']:
        assert hashlib.sha256((ROOT/page['artifact']).read_bytes()).hexdigest()==page['render_sha256']
    h=read(S/'reviewed-host-records.json')['ncu-046']
    assert len(h['host_documents'])==4
    assert '接收校簽名須在初次申請前完成' in ' '.join(h['fields']['host_documents']['points'])


def test_tenth_existing_host_records_preserved_and_uef_blank_not_invented():
    delta=unpack(ROOT/'docs/data/ncu-completion-20261011/resume/tenth/host-delta.json.gz')
    for rid,row in delta.items():
        old,new=row['before'],row['after']
        assert set(old['source_ids'])<=set(new['source_ids'])
        for key,v in old['fields'].items():
            assert set(v['points'])<=set(new['fields'][key]['points'])
        assert old.get('host_document_stages',[])==new.get('host_document_stages',[])
    rs={x['id']:x for x in unpack(S/'host-web-evidence.json.gz')}
    assert not rs['ncu-078-follow-9b6c999bea'].get('reading_review')
    assert not rs['ncu-106-p3-1f63ac5125'].get('reading_review')
    assert '無remote' in ' '.join(delta['ncu-081']['after']['fields']['arrival']['points'])
    assert delta['ncu-056']['after']['fields']['host_documents']['gap_only']


def test_tenth_public_api_keeps_current_points_and_quota_holds(tmp_path):
    ps=TestClient(create_app(tmp_path)).get('/student-dashboard',params={'school':'NCU'}).json()['partner_universities']
    assert len(ps)==214 and sum(p['location']['geocode_status']=='verified' for p in ps)==214
    assert all(p.get('quota') is None and p['availability_status']=='agreement_only' for p in ps)
    mons=next(p for p in ps if 'De Mons' in p['school_name'])
    assert mons['location']['geocode_status']=='verified' and mons['location']['latitude']==50.459072565
