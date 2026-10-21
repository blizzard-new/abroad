from __future__ import annotations

import copy
from datetime import datetime
import json
from pathlib import Path
import shutil

import pytest

from exchange_info.application_rules import build_personal_application_plan
from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PersonalApplicationPlanRequest, UniversityApplicationWorkflow
from exchange_info.ncku_eligibility import ncku_academic_check, ncku_language_check
from exchange_info.ncku_guidelines_review import (
    ARCHIVE_KEY, DISPLAY_MANIFEST, GUIDE_URL, MANIFEST, apply_ncku_guidelines_review,
    current_ncku_application_window, ncku_1161_window,
)
from exchange_info.ncku_student_view import build_ncku_student_dashboard, fetch_ncku_partner_universities
from exchange_info.ntust_source_review import write_atomic

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path('src/exchange_info/official_data/ncku')


@pytest.mark.parametrize('score,gpa,rank,expected', [
    (77,None,None,'pass'), (70,None,50,'pass'), (None,None,50,'pass'),
    (76,4.3,51,'fail'), (None,4.3,None,'needs_confirmation'),
    (76,3.1,None,'needs_confirmation'), (None,None,51,'needs_confirmation'),
])
def test_academic_either_score_or_rank_without_invented_gpa(score,gpa,rank,expected):
    assert ncku_academic_check('學士班',score,gpa,rank)[0] == expected


def test_new_toefl_and_non_english_host_acceptance():
    assert ncku_language_check('toefl_new',4)[0] == 'pass'
    assert ncku_language_check('toefl_new',3.5)[0] == 'fail'
    assert ncku_language_check('toefl_new',72)[0] == 'fail'
    assert ncku_language_check('jlpt',1)[0] == 'needs_confirmation'
    assert ncku_language_check(None,None,partner_country='中國大陸')[0] == 'needs_confirmation'


@pytest.mark.parametrize('instant,expected', [
    ('2026-10-29T23:59:59+08:00','upcoming'),
    ('2026-10-30T00:00:00+08:00','needs_confirmation'),
    ('2026-10-30T23:59:59+08:00','needs_confirmation'),
    ('2026-10-31T00:00:00+08:00','open'),
    ('2026-11-19T08:00:01+00:00','closed'),
])
def test_current_window_is_date_aware_without_inventing_opening_hour(instant,expected):
    now=datetime.fromisoformat(instant)
    assert ncku_1161_window(now)==expected
    dashboard=build_ncku_student_dashboard(reference_time=now)
    assert dashboard.application_periods[0].status.value==expected
    reviewed=[p for p in dashboard.partner_universities if ARCHIVE_KEY in p.reference_data]
    assert len(reviewed)==97 and all(p.application_window_status==expected for p in reviewed)
    assert all(p.availability_status=='needs_confirmation' for p in reviewed)
    assert dashboard.application_periods[0].reminder_eligible == (expected in {'upcoming','open'})
    assert all(p.application_window_status=='closed' for p in dashboard.partner_universities if ARCHIVE_KEY not in p.reference_data)


def test_window_requires_timezone_and_does_not_mutate_cached_rows():
    with pytest.raises(ValueError,match='timezone'):
        ncku_1161_window(datetime(2026,10,21))
    before=fetch_ncku_partner_universities(reference_time=datetime.fromisoformat('2026-10-21T00:00:00+08:00'))
    fetch_ncku_partner_universities(reference_time=datetime.fromisoformat('2027-01-01T00:00:00+08:00'))
    assert all(p.application_window_status=='upcoming' for p in before if ARCHIVE_KEY in p.reference_data)
    current=next(p for p in before if ARCHIVE_KEY in p.reference_data)
    later_cycle=current.model_copy(update={'academic_year':'117'})
    assert current_ncku_application_window(later_cycle,datetime.fromisoformat('2027-01-01T00:00:00+08:00')) is later_cycle


def test_plan_scopes_home_rules_and_checks_host_degree_separately():
    partner=next(p for p in fetch_ncku_partner_universities() if p.school_name.startswith('因斯布魯克大學 '))
    workflow=UniversityApplicationWorkflow.model_validate(next(json.loads(l) for l in
        (ROOT/BUNDLE/'application_workflows.jsonl').read_text('utf8').splitlines()
        if json.loads(l)['school_name']==partner.school_name))
    request=PersonalApplicationPlanRequest(home_school='國立成功大學',academic_year='116',application_round='116-1',
        degree_level='博士班',current_year='博二',academic_score=95,language_test='toefl_new',language_score=4,
        preferences=[{'rank':1,'school_name':partner.school_name}])
    plan=build_personal_application_plan(request,[partner],[workflow],academic_score_minimum=77)
    checks={c.code:c for c in plan.choices[0].checks}
    assert checks['degree_level'].status=='pass'
    assert checks['partner_degree_level'].status=='needs_confirmation'
    assert checks['academic_score'].source_url==GUIDE_URL
    # Hypothetical fully verified host scope tests rejection independently of
    # the actual mother-table-only record, which must remain pending.
    evidence=dict(partner.field_evidence)
    evidence['degree_levels']=evidence['degree_levels'].model_copy(update={'status':'verified_current'})
    verified_partner=partner.model_copy(update={'field_evidence':evidence})
    verified_plan=build_personal_application_plan(request,[verified_partner],[workflow],academic_score_minimum=77)
    assert next(c for c in verified_plan.choices[0].checks if c.code=='partner_degree_level').status=='fail'
    for year,round_ in [('117','116-1'),('116','116-2')]:
        plan=build_personal_application_plan(request.model_copy(update={'academic_year':year,'application_round':round_}),
            [partner],[workflow],academic_score_minimum=77)
        checks={c.code:c for c in plan.choices[0].checks}
        assert all(checks[k].status=='needs_confirmation' for k in ['degree_level','academic_score','home_language_score','source_cycle'])


def test_all_current_displays_have_corrected_fee_and_return_rules():
    for filename in ['partners.jsonl','application_workflows.jsonl','destination_profiles.jsonl']:
        for line in (ROOT/BUNDLE/filename).read_text('utf8').splitlines():
            row=json.loads(line)
            if ARCHIVE_KEY not in row.get('reference_data',{}):continue
            visible={k:v for k,v in row.items() if k not in {'reference_data','field_evidence'}}
            text=json.dumps(visible,ensure_ascii=False)
            assert '互惠免繳接待校學費' not in text
            assert '返國後 2 個月內須上傳' not in text
            assert '獎助學金（11萬–24萬）' not in text
            if filename=='destination_profiles.jsonl':
                assert 'em50961@email.ncku.edu.tw' in text
                if row['school_name'] == '秋田大學 Akita University':
                    assert '2027年4月簡章參考，非秋季費用確認' in row['cost_summary']
                    assert 'source_review_round45' in row['reference_data']
                else:
                    assert '未確認當期適用' in row['cost_summary']


def test_replay_and_independent_edits_are_preserved(tmp_path):
    manifests=[json.loads((ROOT/p).read_text('utf8')) for p in [MANIFEST,DISPLAY_MANIFEST]]
    paths={s['file'] for m in manifests for s in m['rows']+m.get('singletons',[])}
    for path in list(paths)+[MANIFEST,DISPLAY_MANIFEST]:
        (tmp_path/path).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/path,tmp_path/path)
    assert apply_ncku_guidelines_review(tmp_path)==0
    data={p:([json.loads(l) for l in (tmp_path/p).read_text('utf8').splitlines()] if p.endswith('.jsonl')
             else json.loads((tmp_path/p).read_text('utf8'))) for p in paths}
    unrelated={p:copy.deepcopy([x for x in d if ARCHIVE_KEY not in x.get('reference_data',{})]) for p,d in data.items() if p.endswith('.jsonl')}
    for m in reversed(manifests):
        for scope in m['rows']+m.get('singletons',[]):
            target=(next(x for x in data[scope['file']] if x['school_name']==scope['school_name'])
                    if scope['file'].endswith('.jsonl') else data[scope['file']])
            for patch in reversed(scope['patches']):
                parent,key=pointer_parent(target,patch['pointer'])
                if patch['expected_missing']:parent.pop(key,None)
                else:parent[key]=copy.deepcopy(patch['expected_values'][0])
            target.get('reference_data',{}).pop(ARCHIVE_KEY,None)
            target.get('reference_data',{}).pop('source_review_round44_display',None)
    for path,value in data.items():write_atomic(tmp_path/path,value,path.endswith('.jsonl'))
    assert apply_ncku_guidelines_review(tmp_path)==2646
    assert apply_ncku_guidelines_review(tmp_path)==0
    for path,old in unrelated.items():
        current=[json.loads(l) for l in (tmp_path/path).read_text('utf8').splitlines()]
        assert [x for x in current if ARCHIVE_KEY not in x.get('reference_data',{})]==old
    path=BUNDLE/'student_dashboard.json'
    dashboard=json.loads((tmp_path/path).read_text('utf8'))
    dashboard['academic_score_rule']='Independent later official review'
    write_atomic(tmp_path/path,dashboard)
    assert apply_ncku_guidelines_review(tmp_path)==0
    assert json.loads((tmp_path/path).read_text('utf8'))['academic_score_rule']=='Independent later official review'
