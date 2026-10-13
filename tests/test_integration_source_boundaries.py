"""Shared-file integration checks for the fixed school-specific data batches."""
import json
from pathlib import Path
import subprocess

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ncu_completion import LOCATIONS, campus_location
from exchange_info.ncu_student_view import fetch_ncu_partner_universities
from exchange_info.university_locations import UniversityLocation


@pytest.mark.parametrize('status', ['pending', 'needs_review', 'verified', 'invalid'])
def test_ncu_sidecar_respects_operator_reviews_in_dashboard_and_life(tmp_path, status):
    reviewed = next(r for r in json.loads(LOCATIONS.read_text())['locations'] if r['geocode_status']=='verified')
    partner = next(p for p in fetch_ncu_partner_universities() if p.school_name==reviewed['school_name'])
    record = dict(reviewed, geocode_status=status, note='local operator review takes priority')
    if status in ('pending','needs_review'):record.update(latitude=None,longitude=None)
    if status == 'verified':record.update(latitude=48.1,longitude=2.1)
    if status == 'invalid':record.update(geocode_status='verified',latitude=1234)
    path=tmp_path/'processed/university_locations.jsonl';path.parent.mkdir();path.write_text(json.dumps(record)+'\n')
    expected=campus_location(partner,UniversityLocation(school_name=partner.school_name),tmp_path)
    client=TestClient(create_app(tmp_path))
    dashboard=client.get('/student-dashboard',params={'school':'NCU'}).json()
    actual=next(r for r in dashboard['partner_universities'] if r['school_name']==partner.school_name)['location']
    assert actual['geocode_status']==('needs_review' if status=='invalid' else status)
    assert actual['latitude']==(48.1 if status=='verified' else None)
    assert actual==expected.model_dump(mode='json')
    life=client.get('/school-life-context',params={'school':partner.school_name,'home_school':'NCU'})
    assert life.status_code==200
    note = life.json()['location_note']
    assert note.startswith('地理參考：' if status == 'verified' else '尚無已核對的校區座標')


def test_scoped_photos_keep_image_and_credit_together_without_cross_school_fallback():
    script=r'''
    const assert=require('node:assert/strict'), fs=require('node:fs');
    const source=fs.readFileSync(process.argv[1],'utf8');
    const state={schoolImages:[{school_name:'Same University',country:'Japan',status:'verified',local_path:'/wrong-shared.jpg'}],
      ncuSchoolImages:[{school_name:'Same University',country:'Japan',status:'verified',local_path:'/ncu.jpg',license_name:'CC BY-SA 4.0',license_url:'https://creativecommons.org/licenses/by-sa/4.0/',note:'攝影：NCU photographer'}]};
    let schoolVisualSource=null,schoolVisualExact=new Map(),schoolVisualAliases=new Map();
    for(const name of ['visualSchoolIdentity','visualCountryIdentity','visualSchoolAliases','schoolVisualRecordFor','schoolImageFor']){
      eval(source.match(new RegExp('^function '+name+'\\([^]*?^}', 'm'))[0]);
    }
    state.dashboard={school_name:'國立中央大學'};
    assert.equal(schoolImageFor('Same University','Japan').local_path,'/ncu.jpg');
    assert.equal(schoolImageFor('Missing University','Japan'),null);
    state.dashboard={school_name:'國立中正大學',partner_universities:[{school_name:'Same University',country:'Japan',image_url:'/ccu.jpg',image_status:'verified',reference_data:{ccu_completion:'{}',ccu_campus_assets:JSON.stringify({photo:{artist:'CCU photographer',license_name:'CC BY-SA 4.0',license_url:'https://creativecommons.org/licenses/by-sa/4.0/',campus_caption:'Reviewed campus'}})}}]};
    const ccu=schoolImageFor('Same University','Japan');assert.equal(ccu.local_path,'/ccu.jpg');assert.match(ccu.note,/CCU photographer/);
    state.dashboard.partner_universities[0].image_status='missing';assert.equal(schoolImageFor('Same University','Japan'),null);
    state.dashboard={school_name:'長庚大學'};assert.equal(schoolImageFor('Same University','Japan').local_path,'/wrong-shared.jpg');
    '''
    result=subprocess.run(['node','-e',script,str(Path('src/exchange_info/static/app.js').resolve())],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('status', ['pending', 'needs_review', 'verified', 'invalid'])
def test_tku_sidecar_respects_operator_review_in_dashboard_and_life(tmp_path, status):
    from exchange_info.tku_assets import campus_locations
    from exchange_info.tku_census import school_audit
    from exchange_info.tku_student_view import fetch_tku_partner_universities
    partner = next(p for p in fetch_tku_partner_universities() if school_audit(p.school_name)['id'] in campus_locations())
    record = dict(school_name=partner.school_name, country=partner.country, geocode_status=status,
                  latitude=35.1 if status=='verified' else None, longitude=135.1 if status=='verified' else None,
                  precision='campus', source_url='https://example.edu/review', geocoded_at='2026-10-11T00:00:00Z', note='operator review')
    if status=='invalid':record.update(geocode_status='verified',latitude=1234,longitude=135)
    path=tmp_path/'processed/university_locations.jsonl';path.parent.mkdir();path.write_text(json.dumps(record)+'\n')
    with TestClient(create_app(tmp_path)) as client:
        rows=client.get('/student-dashboard',params={'school':'TKU'}).json()['partner_universities']
        actual=next(p for p in rows if p['school_name']==partner.school_name)['location']
        assert actual['geocode_status']==('needs_review' if status=='invalid' else status)
        assert actual['latitude']==(35.1 if status=='verified' else None)
        life=client.get('/school-life-context',params={'school':partner.school_name,'home_school':'TKU'})
        assert life.status_code==200
        assert life.json()['location_note'].startswith('地理參考：' if status=='verified' else '尚無已核對的校區座標')
