"""Source applicability, complete original-gap ledger, and ordinal JLPT checks."""
import json

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import AccountSelectionConditions, AdvisorProfile, PersonalApplicationPlanRequest
from exchange_info.tku_data import BUNDLE, load_tku_records, load_tku_sources


def test_original_67_gaps_are_preserved_and_bounded_review_resolves_only_four():
    ledger = json.loads((BUNDLE / 'gap_triage.json').read_text())
    rows = ledger['all_fields']
    assert len(rows) == len({(r['partner_id'], r['key']) for r in rows}) == 67
    assert ledger['remaining_count'] == 63 and ledger['resolved_count'] == 4
    assert ledger['initial_counts'] == {'3': 47, '2': 14, '1': 2, '4': 4}
    assert ledger['after_review_counts'] == {'1': 45, '2': 18, '4': 4}
    assert not ledger['official_not_announced_claims']
    sources = {s['id']: s for s in load_tku_sources()}
    for row in rows:
        assert row['original_field']['status'] != 'verified'
        assert row['original_field']['evidence'] and row['public_entries_checked']
        assert not row['non_announcement_claim'] and not row['human_contact_performed']
        if row['resolved']:
            assert row['current_field']['status'] == 'verified'
            for e in row['current_field']['evidence']:
                if not e['quote']:
                    continue
                source = sources[e['source_id']]
                text = source.get('text', '') + ' '.join(p['text'] for p in source.get('pages', []))
                assert ' '.join(e['quote'].split()) in ' '.join(text.split())
    assert sum(f.status == 'verified' for r in load_tku_records() for f in r.fields.values()) == 89


def test_original_department_deadlines_are_not_promoted_to_corrected_round():
    ledger = json.loads((BUNDLE / 'gap_triage.json').read_text())
    assert len(ledger['department_schedule_review']) == 5
    for row in ledger['department_schedule_review']:
        assert row['source']['http_status'] == 200 and row['source']['sha256']
        assert row['status'] == 'needs_confirmation'
        assert row['current_student_deadline'] is None and row['current_forwarding_deadline'] is None
    assert all(r.fields['department_deadline'].value is None for r in load_tku_records())


@pytest.mark.parametrize('partner,level,status,minimum', [
    ('seikei','N1','pass','N2'), ('seikei','N2','pass','N2'), ('seikei','N3','fail','N2'),
    ('ritsumeikan','N1','pass','N1'), ('ritsumeikan','N2','fail','N1'),
    ('uec','N1','needs_confirmation',None),
])
def test_jlpt_is_ordinal_home_only_and_never_reopens_closed_round(tmp_path, partner, level, status, minimum):
    client = TestClient(create_app(tmp_path))
    response = client.post('/tku/eligibility-check', json=dict(partner_id=partner, jlpt_level=level,
        academic_average=85, degree_level='大學部', year_of_study=3))
    assert response.status_code == 200
    result = response.json()
    assert result['language_status'] == status and result['jlpt_minimum'] == minimum
    assert result['application_status'] == 'closed' and result['evidence']
    assert response.headers['cache-control'] == 'no-store'


def test_unknown_round_and_invalid_level_cannot_borrow_current_jlpt_rule(tmp_path):
    client = TestClient(create_app(tmp_path))
    result = client.post('/tku/eligibility-check', json={'round_id':'2028-2029/第一梯次','jlpt_level':'N1'}).json()
    assert result['home_status'] == 'needs_confirmation' and result['application_status'] == 'not_verified_new'
    assert result['evidence'] == [] and result['academic_year'] is None and result['application_round'] is None
    assert client.post('/tku/eligibility-check', json={'jlpt_level':1}).status_code == 422
    assert client.post('/tku/eligibility-check', json={'jlpt_level':'N0'}).status_code == 422


def test_jlpt_profile_survives_models_without_a_numeric_english_score():
    conditions = AccountSelectionConditions(profile={'jlpt_level':'N1'})
    assert AccountSelectionConditions.model_validate_json(conditions.model_dump_json()).profile.jlpt_level == 'N1'
    profile = AdvisorProfile(school_name='淡江大學', jlpt_level='N2')
    assert profile.language_score is None and profile.jlpt_level == 'N2'
    request = PersonalApplicationPlanRequest(home_school='淡江大學', jlpt_level='N1',
        preferences=[{'rank':1,'school_name':'成蹊大學 Seikei University'}])
    assert request.jlpt_level == 'N1' and request.language_test is None


@pytest.mark.parametrize('year,round_name', [(None,None), ('2028-2029','第一梯次'), ('2027-2028','第一梯次')])
def test_advisor_does_not_borrow_latest_jlpt_rule_for_unknown_year_or_round(year, round_name):
    from types import SimpleNamespace
    from exchange_info.advisor import _qualification_summary
    summary = _qualification_summary(AdvisorProfile(school_name='淡江大學',academic_year=year,
        application_round=round_name,jlpt_level='N1',academic_score=90),SimpleNamespace(school_name='淡江大學', academic_gpa_minimum=None))
    assert '尚未核實新版' in summary[0]
    assert not any('符合已知門檻' in line for line in summary)


def test_tku_coverage_includes_own_bundled_profiles_with_year_cautions(tmp_path):
    client = TestClient(create_app(tmp_path))
    coverage = client.get('/coverage', params={'school':'TKU'}).json()
    assert coverage['total_partner_schools'] == 4 and coverage['destination_profile_count'] == 4
    assert all(r['destination_status'] == 'official_partial' for r in coverage['partners'])
