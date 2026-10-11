"""Campus identity and independently named points are kept distinct from current offers."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

S = Path(__file__).parents[1] / 'sources/ncu/2026-10-11'


def unpack(name):
    return json.loads(gzip.decompress((S / name).read_bytes()))


def test_eleventh_coordinates_have_replayable_named_source_and_official_identity():
    rows = json.loads((S / 'resume-eleventh-location-review.json').read_text())['coordinate_decisions']
    pack = unpack('resume-eleventh-visual-sourcepack.json.gz')
    for row in rows:
        for receipt in [row['official_identity_receipt'], row['coordinate_receipt']]:
            source = next(x for x in pack if x['receipt']['sha256'] == receipt['sha256'])
            if source.get('reuse_pack'):
                source = next(x for x in unpack(source['reuse_pack']) if x['receipt']['sha256'] == receipt['sha256'])
            if 'raw_utf8' in source:
                assert hashlib.sha256(source['raw_utf8'].encode()).hexdigest() == receipt['sha256']
            else:
                assert source['full_original_archived_in_public_repo'] is False
                assert source['original_excerpt'] and len(source['original_excerpt'].split()) <= 25
        assert row['published_record']['precision'] == 'representative'
        assert row['published_record']['current_exchange_campus_confirmed'] is False
        assert '116' in row['published_record']['note']


def test_eleventh_mons_uses_current_university_identity_and_building_not_camera():
    rows = json.loads((S / 'resume-eleventh-location-review.json').read_text())['coordinate_decisions']
    mons = next(x for x in rows if x['capture_row_id'] == 'ncu-053')
    assert mons['country'] == '比利時' and mons['previous_record']['geocode_status'] == 'needs_review'
    assert (mons['published_record']['latitude'], mons['published_record']['longitude']) == (50.459072565, 3.950398812)
    assert mons['published_record']['latitude'] != mons['previous_record']['latitude']
    raw = next(x['raw_utf8'] for x in unpack('resume-tenth-visual-sourcepack.json.gz') if x['capture'] == 'mons-warocque-waze.html')
    assert '50.459072565' in raw and '3.950398812' in raw and 'Warocqu' in raw
    identity = next(x for x in unpack('resume-eleventh-visual-sourcepack.json.gz') if x['capture'] == 'mons-museum-warocque.html')
    assert identity['article_modified'].startswith('2025-04-11') and 'UMONS' in identity['original_excerpt']


def test_eleventh_weishui_is_same_operator_and_point_inside_named_campus_polygon():
    raw = {x['capture']: x for x in unpack('resume-eleventh-visual-sourcepack.json.gz')}
    element = json.loads(raw['changan-osm-way.json']['raw_utf8'])['elements'][0]
    assert element['id'] == 271773865 and element['version'] == 9
    assert element['tags']['name'] == '长安大学渭水校区'
    assert element['tags']['operator'] == '长安大学' and element['tags']['website'] == 'https://www.chd.edu.cn/'
    place = json.loads(raw['changan-weishui-osm.html']['raw_utf8'])[0]
    assert place['address']['country_code'] == 'cn' and place['osm_id'] == element['id']
    x, y = float(place['lon']), float(place['lat'])
    polygon = place['geojson']['coordinates'][0]
    inside = False
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:]):
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
    assert inside and 'ODbL' in place['licence']
    plan = raw['changan-plan-4.jpg']
    original = next(r for r in unpack(plan['reuse_pack']) if r['receipt']['sha256'] == plan['receipt']['sha256'])
    assert hashlib.sha256(base64.b64decode(original['raw_base64'])).hexdigest() == plan['receipt']['sha256']
    paper = raw['changan-weishui-study.pdf']
    assert paper['adopted_as_coordinates'] is False and paper['full_document_read'] is False


def test_eleventh_failed_photo_searches_are_not_licensed_assets_or_absence_proof():
    attempts = unpack('resume-eleventh-photo-searches.json.gz')
    assert len(attempts) == 12 and all(x['receipt']['status'] == 403 and x['adopted'] is False for x in attempts)
    assert all('Noassertion' in x['reason'] for x in attempts)
