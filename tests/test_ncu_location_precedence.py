"""NCU campus holds must survive a newer shared catalogue during integration."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ncu_completion import campus_location
from exchange_info.ncu_student_view import build_ncu_student_dashboard
from exchange_info.university_locations import UniversityLocation


@pytest.mark.parametrize('name_fragment',['Hiroshima University','Université De Mons'])
def test_explicit_ncu_campus_hold_shadows_shared_verified_point(tmp_path,name_fragment):
    partner=next(p for p in build_ncu_student_dashboard().partner_universities if name_fragment in p.school_name)
    fallback=UniversityLocation(school_name=partner.school_name,country=partner.country,city='UNREVIEWED SHARED CAMPUS',latitude=34.382222,longitude=132.458056,geocode_status='verified',geocoded_at='2026-10-11T14:57:00Z',source_url='https://www.wikidata.org/wiki/Q115220')
    scoped=campus_location(partner,fallback)
    assert scoped.geocode_status=='needs_review'
    assert scoped.latitude is None and scoped.longitude is None
    (tmp_path/'processed').mkdir()
    (tmp_path/'processed/university_locations.jsonl').write_text(fallback.model_dump_json()+'\n')
    client=TestClient(create_app(tmp_path))
    dashboard=client.get('/student-dashboard',params={'school':'NCU'}).json()
    shown=next(p for p in dashboard['partner_universities'] if p['school_name']==partner.school_name)
    assert shown['location']['geocode_status']=='needs_review'
    assert shown['location']['latitude'] is None and shown['location']['longitude'] is None
    assert sum(p['location']['geocode_status']=='verified' for p in dashboard['partner_universities'])==186
