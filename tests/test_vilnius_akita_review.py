"""Check intake isolation, replay and live providers; not source truth by itself."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import shutil

import pytest

from exchange_info.application_rules import _partner_language_threshold
from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PartnerUniversity, UniversityApplicationWorkflow, DestinationProfile
from exchange_info.vilnius_akita_review import ARCHIVE_KEY, MANIFEST, COST_MANIFEST, apply_vilnius_akita_review, load_manifest
from exchange_info.cost_estimates import budget_fit, extract_monthly_estimates
from exchange_info.school_completeness import build_school_completeness

ROOT = Path(__file__).resolve().parents[1]
HOMES = ('ntu','ncu','ntnu','nsysu','ntut','ncku','nycu','nthu','wzu')


def rows(path):
    return [json.loads(line) for line in path.read_text('utf8').splitlines() if line.strip()]


@pytest.mark.parametrize('home', HOMES)
def test_live_partner_providers_keep_host_scope_and_do_not_auto_pass(home):
    module = importlib.import_module(f'exchange_info.{home}_student_view')
    loaded = {p.school_name:p for p in getattr(module,f'fetch_{home}_partner_universities')()}
    scopes = [s for s in load_manifest(ROOT)['rows'] if s['home_id'] == home and s['file'].endswith('partners.jsonl')]
    for scope in scopes:
        partner = loaded[scope['school_name']]
        assert partner.field_evidence['language_requirement'].status in ('reference_only','conflict')
        assert _partner_language_threshold(partner, 'toeic') is None
        assert _partner_language_threshold(partner, 'toefl') is None
        assert partner.language_review_note
        assert 'Listening & Reading' in partner.language_requirement
        if scope['host'] == 'akita':
            assert '2027 年 4 月' in partner.language_requirement
            assert 'AUSF' in partner.language_requirement and '不能以日語成績單獨取代' in partner.language_requirement
            assert partner.field_evidence['host_agreement_reference'].status == 'reference_only'
        if home in ('wzu','nycu'):
            assert partner.academic_year == '115'
            assert partner.availability_status != 'open'


def test_distinct_mother_rules_and_degree_conflicts_survive():
    def partner(home, prefix):
        return next(r for r in rows(ROOT/f'src/exchange_info/official_data/{home}/partners.jsonl') if r['school_name'].startswith(prefix))
    nthu=partner('nthu','維爾紐斯')
    assert '不接受 MyBest Scores、TOEIC' in nthu['language_requirement']
    assert '不會取消清大校內限制' in nthu['language_review_note']
    ntnu=partner('ntnu','維爾紐斯')
    assert 'ITP 543' in ntnu['language_requirement']
    assert '不能自行把ITP543視為已獲接待校接受或拒絕' in ntnu['language_review_note']
    vu=partner('ncku','維爾紐斯大學 '); ak=partner('ncku','秋田大學 ')
    assert '讀寫785' in vu['language_requirement'] and '聽讀）785' in vu['language_requirement']
    assert '博士資格須由雙方確認' in vu['degree_levels']
    assert '研究生是否可申請須由雙方確認' in ak['degree_levels']
    assert '不得把兩學期AUAJ當成可選' in ak['language_review_note']


def test_all_patches_are_model_valid_and_originals_are_preserved():
    models={'partners.jsonl':PartnerUniversity,'application_workflows.jsonl':UniversityApplicationWorkflow,
            'destination_profiles.jsonl':DestinationProfile}
    manifest=load_manifest(ROOT)
    assert len(manifest['rows']) == 36 and len(manifest['school_audit']) == 12
    for scope in manifest['rows']:
        row=next(r for r in rows(ROOT/scope['file']) if (r['school_name'],r.get('country')) == (scope['school_name'],scope['country']))
        models[Path(scope['file']).name].model_validate(row)
        archive=row['reference_data'][ARCHIVE_KEY]
        if isinstance(archive,str):archive=json.loads(archive)
        for patch in scope['patches']:
            parent,key=pointer_parent(row,patch['pointer'])
            assert parent[key] == patch['value']
            assert archive[patch['pointer']]['existed'] != patch['expected_missing']
            if not patch['expected_missing']:
                assert archive[patch['pointer']]['value'] in patch['expected_values']
        if scope['host'] == 'akita' and scope['file'].endswith('destination_profiles.jsonl'):
            assert '80,000' in row['cost_summary'] and '非秋季費用確認' in row['cost_summary']
            assert '20,000' in row['housing_summary'] and '偏好房型' in row['housing_summary']
            section=next(s for s in row['student_guide_sections'] if s['key']=='host-source-review-r45')
            assert any('不是只修8學分' in point for point in section['points'])
            assert any('不是領事館簽證處理時間' in point for point in section['points'])
    assert not any(p['pointer'].endswith('deadline_at') for s in manifest['rows'] for p in s['patches'])


@pytest.mark.parametrize('home', ('ntu','ncu'))
def test_custom_output_replay_is_exact_and_retains_independent_changes(tmp_path, home):
    manifest=load_manifest(ROOT)
    (tmp_path/Path(MANIFEST).parent).mkdir(parents=True)
    shutil.copy2(ROOT/MANIFEST,tmp_path/MANIFEST)
    shutil.copy2(ROOT/COST_MANIFEST,tmp_path/COST_MANIFEST)
    output=tmp_path/'custom-output';output.mkdir()
    scopes=[s for s in manifest['rows'] if s['home_id']==home]
    cost_scopes=[s for s in json.loads((ROOT/COST_MANIFEST).read_text('utf8'))['rows'] if s['home_id']==home]
    grouped={}
    for scope in scopes:
        row=next(r for r in rows(ROOT/scope['file']) if (r['school_name'],r.get('country'))==(scope['school_name'],scope['country']))
        row['reference_data'].pop(ARCHIVE_KEY)
        row.pop('cost_evidence',None)
        for patch in reversed(scope['patches']):
            parent,key=pointer_parent(row,patch['pointer'])
            if patch['expected_missing']:parent.pop(key)
            else:parent[key]=deepcopy(patch['expected_values'][0])
        grouped.setdefault(Path(scope['file']).name,[]).append(row)
    sentinel={'school_name':'Unrelated university','country':'Other','untouched':True}
    for filename, records in grouped.items():
        (output/filename).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records+[sentinel]),'utf8')
    assert apply_vilnius_akita_review(tmp_path,home,bundle=output)==sum(len(s['patches']) for s in scopes+cost_scopes)
    before={p.name:p.read_bytes() for p in output.iterdir()}
    assert apply_vilnius_akita_review(tmp_path,home,bundle=output)==0
    assert {p.name:p.read_bytes() for p in output.iterdir()}==before
    assert not (tmp_path/'src/exchange_info/official_data').exists()
    for filename in grouped:assert rows(output/filename)[-1]==sentinel
    p=output/'partners.jsonl';records=rows(p);records[0]['language_requirement']='Independent later evidence'
    p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),'utf8')
    assert apply_vilnius_akita_review(tmp_path,home,bundle=output)==0
    assert rows(p)[0]['language_requirement']=='Independent later evidence'
    # An ambiguous identity must fail before changing any of the bundle files.
    p.write_text(p.read_text('utf8')+json.dumps(records[0],ensure_ascii=False)+'\n','utf8')
    before={p.name:p.read_bytes() for p in output.iterdir()}
    with pytest.raises(ValueError,match='exactly once'):apply_vilnius_akita_review(tmp_path,home,bundle=output)
    assert {p.name:p.read_bytes() for p in output.iterdir()}==before


@pytest.mark.parametrize('home', ('ntu','ntut','ncku'))
def test_spring_cost_reference_cannot_pass_budget_for_unspecified_intake(home):
    profile=next(DestinationProfile.model_validate(r) for r in rows(ROOT/f'src/exchange_info/official_data/{home}/destination_profiles.jsonl')
                 if r['school_name'] in ('秋田大學','秋田大學 Akita University'))
    estimates=extract_monthly_estimates(profile)
    assert estimates and estimates[0].low==80000
    assert estimates[0].source_urls==(profile.cost_evidence.source_url,)
    result=budget_fit(estimates,1000000)
    assert result['status']=='unknown'
    assert result['estimate']['applicability_status']=='reference_only'
    assert '2027年4月' in result['reason']
    assert result['estimate']['twd_per_unit'] is None
    partner=next(PartnerUniversity.model_validate(r) for r in rows(ROOT/f'src/exchange_info/official_data/{home}/partners.jsonl')
                 if r['school_name']==profile.school_name)
    completeness=build_school_completeness(partner,profile,None,home_university=profile.home_university)
    cost=next(item for item in completeness.items if item.key=='cost')
    assert cost.status=='needs_confirmation'
    assert cost.source_urls==[profile.cost_evidence.source_url]


def test_cost_evidence_does_not_change_legacy_profile_serialization():
    profile=DestinationProfile(school_name='Example',cost_summary='每月生活費 USD 800')
    assert 'cost_evidence' not in profile.model_dump(mode='json')
    assert budget_fit(extract_monthly_estimates(profile),1000000)['status']=='within'


@pytest.mark.parametrize('status', ('reference_only','conflict','needs_confirmation','missing','explicit_not_announced','verified_current'))
def test_cost_evidence_requires_current_applicability_for_budget_fit(status):
    profile=DestinationProfile(school_name='Synthetic fixture',cost_summary='每月生活費 USD 800',
        cost_evidence={'source_url':'https://example.edu/costs','checked_at':'2026-10-21T04:00:00Z',
                       'status':status,'note':'Test-only applicability note'})
    result=budget_fit(extract_monthly_estimates(profile),1000000)
    assert result['status']==('within' if status=='verified_current' else 'unknown')
