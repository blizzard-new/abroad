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


def test_second_resume_provenance_rows_raw_points_and_country_rejections():
    audits=json.loads((ROOT/'src/exchange_info/official_data/ncu/field-audit.json').read_text())
    canonical={r['school_name']:r['source_rows'] for r in audits}
    for prefix in ['resume-second','resume-discovery']:
        review=json.loads((SOURCE/(prefix+'-review.json')).read_text())
        pack=json.loads(gzip.decompress((SOURCE/(prefix+'-sourcepack.json.gz')).read_bytes()))
        bodies={r['receipt'].get('sha256'):r['raw_utf8'] for r in pack if 'raw_utf8' in r}
        for digest,raw in bodies.items():
            assert hashlib.sha256(raw.encode()).hexdigest()==digest
        for row in review['photo_decisions']+review['coordinate_decisions']:
            assert row['canonical_source_rows']==canonical[row['school_name']]
            record=row.get('published_record')
            if not record:continue
            raw=bodies[record['source_sha256']]
            if row.get('qid'):
                entity=json.loads(raw)['entities'][row['qid']]
                claims=[c for c in entity['claims']['P625'] if c.get('rank')!='deprecated' and 'datavalue' in c.get('mainsnak',{})]
                qualifier=row.get('selected_campus_qualifier')
                if qualifier:
                    claims=[c for c in claims if any(q.get('datavalue',{}).get('value',{}).get('id')==qualifier for q in c.get('qualifiers',{}).get('P518',[]))]
                points={(c['mainsnak']['datavalue']['value']['latitude'],c['mainsnak']['datavalue']['value']['longitude']) for c in claims}
                assert points=={(record['latitude'],record['longitude'])}
            else:
                assert str(record['latitude']) in raw and str(record['longitude']) in raw
            assert record['current_exchange_campus_confirmed'] is False
    discovery=json.loads((SOURCE/'resume-discovery-review.json').read_text())
    held={r['capture_row_id'] for r in discovery['coordinate_decisions'] if r['decision']=='pending_not_published'}
    assert {'ncu-078','ncu-080','ncu-098','ncu-154','ncu-205','ncu-208'} <= held
    photos=json.loads((ROOT/'src/exchange_info/official_data/ncu/campus-assets.json').read_text())['photos']
    assert not any('Suleyman Demirel' in r['school_name'] for r in photos)
    assert all('<' not in r['photographed_at_original'] for r in photos)
