"""Different free grants must retain their proof and public attribution."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.build_ncu_assets import reviewed_license_url

ROOT = Path(__file__).resolve().parents[1]
ROWS = json.loads((ROOT/'sources/ncu/2026-10-11/campus-photo-reviews.json').read_text())['rows']
GRANTS = [r for r in ROWS if r.get('license_review')]

@pytest.mark.parametrize('source', GRANTS, ids=lambda r:r['id'])
def test_original_grant_is_preserved_with_provenance(source):
    url = reviewed_license_url(source)
    assert source['license'] in {'FAL', 'Copyrighted free use'}
    assert url.startswith('https://commons.wikimedia.org/')
    assert source['license_review']['image_sha256'] == source['sha256']
    if source['license'] == 'FAL':
        assert source['author_html'] == 'Wladyslaw Sojka (Taxiarchos228)'
        assert source['author_url'] == 'https://www.sojka.photo/'
    else:
        assert url == source['page_url'] + '#Licensing'
        assert 'Sengkang' in source['author_html']

@pytest.mark.parametrize('source', GRANTS, ids=lambda r:r['id'])
@pytest.mark.parametrize('failure', ['missing_review','wrong_photo','wrong_page','changed_terms','unapproved_url'])
def test_non_cc_label_alone_cannot_approve_image(source, failure):
    row = deepcopy(source)
    if failure == 'missing_review': row.pop('license_review')
    elif failure == 'wrong_photo': row['license_review']['image_sha256'] = '0'*64
    elif failure == 'wrong_page': row['license_review']['declaration']['url'] = 'https://commons.wikimedia.org/wiki/File:Another_photo.jpg'
    elif failure == 'changed_terms': row['license_review']['terms']['sha256'] = '0'*64
    elif failure == 'unapproved_url': row['license_url'] = 'https://example.com/permission'
    with pytest.raises(ValueError): reviewed_license_url(row)

def test_two_new_locations_keep_named_campus_and_current_scope_separate():
    rows=json.loads((ROOT/'sources/ncu/2026-10-11/resume-fifth-location-review.json').read_text())['coordinate_decisions']
    by_id={r['capture_row_id']:r for r in rows}
    h=by_id['ncu-115'];r=h['published_record']
    assert (r['latitude'],r['longitude'])==(34.4022006,132.713964)
    assert 'Kagamiyama' in r['city'] and not r['current_exchange_campus_confirmed']
    assert h['previous_record']['geocode_status']=='needs_review'
    assert h['original_direction_endpoint_pairs_lon_lat'][0]==['132.4753786','34.397667']
    c=by_id['ncu-154']['published_record']
    assert (c['latitude'],c['longitude'])==(37.485931,126.804622)
    assert c['city']=='Bucheon / Songsim' and not c['current_exchange_campus_confirmed']
    assert c['coordinate_scope']=='official_named_campus_map_center'
