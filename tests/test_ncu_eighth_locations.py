"""Exact campus evidence remains distinct from viewport and similarly named places."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
from fastapi.testclient import TestClient
from exchange_info.api import create_app
ROOT=Path(__file__).parents[1]
S=ROOT/'sources/ncu/2026-10-11'

def records():
    return json.loads((S/'resume-eighth-location-review.json').read_text())['coordinate_decisions']

def test_eighth_original_sources_and_named_campus_coordinates_are_lossless():
    pack=json.loads(gzip.decompress((S/'resume-eighth-visual-sourcepack.json.gz').read_bytes()))
    raw={}
    for x in pack:
        b=x['raw_utf8'].encode() if 'raw_utf8' in x else base64.b64decode(x['raw_base64']) if 'raw_base64' in x else None
        if b is not None:
            assert hashlib.sha256(b).hexdigest()==x['receipt']['sha256']
            raw[x['receipt']['sha256']]=b
    assert len(records())==12
    for d in records():
        p=d['published_record'];text=raw[p['source_sha256']].decode()
        assert str(p['latitude']) in text and str(p['longitude']) in text
        assert p['precision']=='representative' and p['current_exchange_campus_confirmed'] is False
        assert d['official_identity_receipt']['sha256'] in raw and d['canonical_source_rows']
        assert all(r['sha256'] in raw for r in d['supporting_receipts'])

def test_eighth_specific_markers_do_not_promote_viewports_or_conflicting_building_names():
    ds={d['capture_row_id']:d for d in records()}
    assert ds['ncu-124']['published_record']['latitude']==36.69803539999999 # Gofuku, not the combined Sugitani viewport.
    assert ds['ncu-197']['published_record']['longitude']==120.587402 # Phone + domain + Romulo identity checked.
    assert ds['ncu-025']['published_record']['longitude']==5.9866834 # Official !4d place, not @ view.
    assert ds['ncu-098']['coordinate_receipt']['url']=='https://w3.sdu.edu.tr/assets/harita/js/birimler.js'
    assert ds['ncu-098']['published_record']['latitude']==37.82942927985227
    assert 'A-building' in ds['ncu-079']['derivation'] and 'Mikpoli(M)' in ds['ncu-079']['derivation']
    assert ds['ncu-079']['published_record']['coordinate_scope'].endswith('building_label_ambiguous')
    assert 'INCUBA' in ds['ncu-083']['derivation']

def test_eighth_points_reach_api_and_mons_hold_still_wins(tmp_path):
    ps=TestClient(create_app(tmp_path)).get('/student-dashboard',params={'school':'NCU'}).json()['partner_universities']
    assert len(ps)==214
    assert sum(p['location']['geocode_status']=='verified' for p in ps)==214
    assert sum(p['image_status']=='verified' for p in ps)==202
    by={p['school_name']:p for p in ps}
    for d in records():
        p=by[d['school_name']];r=d['published_record']
        assert p['location']['latitude']==r['latitude'] and p['location']['longitude']==r['longitude']
        assert r['note']==p['location']['note']
    assert all(p.get('quota') is None and p['availability_status']=='agreement_only' for p in ps)
    mons=next(p for p in ps if 'De Mons' in p['school_name'])
    assert mons['location']['geocode_status']=='verified' and mons['location']['latitude']==50.459072565
