"""Independently reviewed campus identities and original photo grants survive publication."""
import gzip
import hashlib
import json
from pathlib import Path
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from exchange_info.api import create_app
ROOT=Path(__file__).parents[1]
S=ROOT/'sources/ncu/2026-10-11'


def test_seventh_marker_sources_are_lossless_and_current_exchange_is_not_inferred():
    pack=json.loads(gzip.decompress((S/'resume-seventh-visual-sourcepack.json.gz').read_bytes()))
    raw={x['receipt'].get('sha256'):x['raw_utf8'] for x in pack if 'raw_utf8' in x}
    for sha,text in raw.items():assert hashlib.sha256(text.encode()).hexdigest()==sha
    rows=json.loads((S/'resume-seventh-location-review.json').read_text())['coordinate_decisions']
    assert len(rows)==9
    for d in rows:
        r=d['published_record'];text=raw[r['source_sha256']]
        assert str(r['latitude']) in text and str(r['longitude']) in text
        assert r['precision']=='representative' and r['current_exchange_campus_confirmed'] is False
        assert d['official_identity_receipt']['sha256'] in raw
        assert d['canonical_source_rows']
    by={d['capture_row_id']:d['published_record'] for d in rows}
    assert by['ncu-009']['longitude']==0.125063  # Current Quai Frissard, not the old embed viewport.
    assert by['ncu-100']['latitude']==49.2035681  # Named New Westminster place, not embed bounds.
    assert by['ncu-086']['latitude']==49.8336878  # Address marker, not Mapy viewport.
    assert by['ncu-013']['longitude']==4.8058812  # Place endpoint, not Google @ center.
    assert by['ncu-208']['city']=='Bandung / Ganesha'


def test_seventh_campus_photos_have_original_author_grants_and_visible_identity():
    pack=json.loads(gzip.decompress((S/'resume-seventh-visual-sourcepack.json.gz').read_bytes()))
    raw={x['local_evidence_key']:x['raw_utf8'] for x in pack if 'raw_utf8' in x}
    reviews=json.loads((S/'campus-photo-reviews.json').read_text())['rows']
    for rid,author,licence in [('ncu-209','Fandiamendra','CC BY-SA 4.0'),('ncu-214','trungydang','CC BY 3.0')]:
        r=next(x for x in reviews if x['id']==rid+'-resume-seventh-photo')
        assert author in r['author_html'] and r['license']==licence
        assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256']
        description=BeautifulSoup(raw[f'seventh/photos/{rid}/description.html'],'html.parser').get_text(' ',strip=True)
        assert author in description
        if rid=='ncu-209':assert 'Own work' in description and 'copyright holder' in description
        else:
            assert '28 November 2016' in description and 'Panoramio upload bot' in description
            assert '227 Nguyễn Văn Cừ' in r['campus_caption_zh'] and 'HCMUTE' in r['review_note']


def test_seventh_new_markers_and_photos_reach_ncu_api_without_changing_quota(tmp_path):
    c=TestClient(create_app(tmp_path))
    ps=c.get('/student-dashboard',params={'school':'NCU'}).json()['partner_universities']
    assert len(ps)==214 and all(p.get('quota') is None and p['availability_status']=='agreement_only' for p in ps)
    assert sum(p['location']['geocode_status']=='verified' for p in ps)==212
    assert sum(p['image_status']=='verified' for p in ps)==202
    mons=next(p for p in ps if 'De Mons' in p['school_name'])
    assert mons['location']['geocode_status']=='needs_review'
    assert mons['location'].get('latitude') is None
