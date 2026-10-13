"""69-candidate coverage, scoped host facts, historical years and line safety."""
import gzip
import json
from collections import Counter
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.tku_data import BUNDLE
from scripts.tku_capture_io import read_bytes


def data(name):return json.loads((BUNDLE/name).read_text())
def captured(identifier):return json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(identifier+'.json.gz'))))


def test_all_fixed_candidates_are_accounted_without_promoting_shells_and_degree_forms():
    reviews=data('milestone4_candidate_content_reviews.json')
    assert [r['ordinal'] for r in reviews]==list(range(1,70))
    assert Counter(r['http_status'] for r in reviews)=={200:68,404:1}
    assert sum(r['complete_programme_content_reviewed'] for r in reviews)==64
    assert [r['ordinal'] for r in reviews if r['status'].startswith('partial_')]==[3,19,22,24]
    assert all(r['exclude_from_semester_reference_index'] for r in reviews)
    assert reviews[35]['status']=='full_degree' and '2027' in reviews[35]['applicable_year']
    assert reviews[28]['body_review_status']=='not_obtained'
    for r in reviews:
        s=captured(r['source_id'])
        assert r['content_sha256']==s['sha256']
        if r['quote']:assert r['quote'] in s['text']


def test_manual_facts_keep_exact_evidence_and_no_home_quota_or_documents():
    rows=data('milestone4_reviewed_host_facts.json')
    assert len(rows)==8 and sum(len(r['fields']) for r in rows)==45
    for row in rows:
        assert not {'quota','home_eligibility','home_language','home_deadline','documents'}.intersection(row['fields'])
        for f in row['fields'].values():
            assert f['status']=='reference_only' and f['reason'] and isinstance(f['source_period_verified'],bool)
            for e in f['evidence']:
                s=captured(e['source_id'])
                assert e['content_sha256']==s['sha256'] and e['quote'] in s['text']
                assert e['checked_at'] and e['source_url'] and e['applicable_year'] and e['locator']


def test_host_programme_conflicts_historical_prices_and_template_years_remain_visible():
    rows={r['id']:r['fields'] for r in data('milestone4_reviewed_host_facts.json')}
    assert '未列淡江' in rows['tku-sister-19']['host_eligibility']['value']
    assert '2026/27' in rows['tku-sister-19']['study_period']['value']
    assert '來源矛盾' in rows['tku-sister-16']['host_language']['value']
    assert 'à venir' in rows['tku-sister-16']['study_period']['value']
    assert not rows['tku-sister-16']['host_language']['source_period_verified']
    assert not any(f['source_period_verified'] for f in rows['tku-sister-211'].values())
    assert '不是2027' in rows['tku-sister-211']['housing_costs']['value']
    u=rows['tku-sister-54']
    assert '2027/1/14' in u['host_deadline']['value'] and '2027/7/1' in u['host_deadline']['value'] and '矛盾' in u['host_deadline']['value']
    assert len(u['latest_forms']['attachment_checks'])==3
    for a in u['latest_forms']['attachment_checks']:
        assert a['http_status']==200 and a['content_reviewed']
        assert read_bytes(BUNDLE/'host_census_sources'/a['local_file']).startswith((b'%PDF',b'PK'))
        if a['local_file'].endswith('.docx'):assert 'undated' in a['applicable_year']


def test_reference_gap_handoff_distinguishes_actual_readability_and_bounded_asset_search():
    limits=data('milestone4_remaining_source_limits.json')
    assert len(limits['schools'])==len({r['id'] for r in limits['schools']})==98
    assert limits['now_without_reference']==90
    assert sorted(limits['baseline_groups'].values())==[20,24,54]
    assert sum(limits['current_statuses'].values())==98
    assets=data('milestone4_asset_source_limits.json')
    assert len(assets['schools'])==39 and assets['photo_gaps']==assets['coordinate_gaps']==23
    assert all(not r['global_safe_source_exhaustion_proven'] for r in assets['schools'])
    assert all(r['all_photo_source_checks'] and r['photo_evidence'] for r in assets['schools'] if r.get('photo_reason'))
    adelaide=next(r for r in assets['schools'] if r['id']=='tku-sister-319')
    assert 'not body-reviewed' in adelaide['named_map_review_status']


def test_pdf_unicode_line_separators_do_not_break_jsonl_or_api(tmp_path):
    rows=list(map(json.loads,(BUNDLE/'partner_enrichment.jsonl').read_text().splitlines()))
    profiles=list(map(json.loads,(BUNDLE/'destination_profiles.jsonl').read_text().splitlines()))
    assert len(rows)==len(profiles)==287
    client=TestClient(create_app(tmp_path))
    dashboard=client.get('/student-dashboard',params={'school':'TKU'}).json()
    assert len(dashboard['partner_universities'])==287
    for identifier in ['tku-sister-54','tku-sister-19','tku-sister-16','tku-sister-211']:
        r=client.get('/tku/partner-census/'+identifier).json()
        assert r['fields']['quota']['status']!='verified_current'
        assert r['fields']['host_deadline']['status']!='verified_current'
    audit=client.get('/tku/partner-census').json()
    assert audit['currently_open_home_applications']==0 and audit['latest_round_quota']==7
