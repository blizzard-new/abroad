import gzip
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app

ROOT=Path(__file__).parents[1]
SOURCE=ROOT/'sources/ncu/2026-10-11'


def test_resume_coordinates_have_exact_raw_claim_and_dont_claim_current_exchange_campus():
    review=json.loads((SOURCE/'resume-visual-review.json').read_text())
    pack=json.loads(gzip.decompress((SOURCE/'resume-visual-sourcepack.json.gz').read_bytes()))
    bodies={x['receipt'].get('sha256'):x['raw_utf8'] for x in pack if 'raw_utf8' in x}
    for digest,raw in bodies.items():
        assert hashlib.sha256(raw.encode()).hexdigest()==digest
    for decision in review['coordinate_decisions']:
        record=decision.get('published_record')
        if not record:continue
        entity=json.loads(bodies[record['source_sha256']])['entities'][decision['qid']]
        values=[x['mainsnak']['datavalue']['value'] for x in entity['claims']['P625']
                if x.get('rank')!='deprecated' and 'datavalue' in x.get('mainsnak',{})]
        points={(x['latitude'],x['longitude']) for x in values if x['globe'].endswith('/Q2')}
        assert points=={(record['latitude'],record['longitude'])}
        assert record['precision']=='representative'
        assert record['current_exchange_campus_confirmed'] is False
        assert '116實際接收校區另依錄取確認' in record['note']
        assert record['identity_source_url']==decision['identity_source_url']
    held={x['row_id']:x for x in review['coordinate_decisions'] if x['decision']=='pending'}
    assert {'ncu-042','ncu-084','ncu-115','ncu-128','ncu-166'} <= held.keys()
    assert not any(x.get('published_record') for x in held.values())


def test_mother_is_taiwan_ncu_and_namesakes_are_not_borrowed(tmp_path):
    client=TestClient(create_app(tmp_path))
    ncu=next(x for x in client.get('/universities').json() if x['id']=='ncu')
    assert ncu['location']['country']=='臺灣'
    assert ncu['location']['source_url'].endswith('/Q714891')
    assert ncu['location']['latitude']==24.968280555556
    partners=client.get('/student-dashboard',params={'school':'NCU'}).json()['partner_universities']
    assert len(partners)==214
    assert all(x.get('quota') is None and x['availability_status']=='agreement_only' for x in partners)
    can_tho=next(x for x in partners if 'Can Tho' in x['school_name'])
    assert can_tho.get('image_url') is None
    florida=next(x for x in partners if 'University of Florida' in x['school_name'])
    photo=next(x for x in json.loads((ROOT/'src/exchange_info/official_data/ncu/campus-assets.json').read_text())['photos'] if x['school_name']==florida['school_name'])
    assert 'Reitz Union' in photo['title_original']
    assert 'West Florida' not in photo['title_original']
    tracks=[x for x in partners if 'Hokkaido' in x['school_name']]
    assert len(tracks)==2 and tracks[0]['image_url']==tracks[1]['image_url']
    assert tracks[0]['school_name']!=tracks[1]['school_name']
