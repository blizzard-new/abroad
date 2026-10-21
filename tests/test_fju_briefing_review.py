"""Current scoring must distinguish intervals, scales, and admission thresholds."""
import json
from pathlib import Path
import pytest
from exchange_info.fju_eligibility import (fju_internal_language_score_range,
    fju_internal_language_points, fju_language_check, fju_degree_check)
from exchange_info.fju_briefing_review import load_manifest, SCORING_FORMULA, SCORING_TABLE_NOTE, SLIDES_URL
from exchange_info.fju_process_review import load_manifest as process_manifest, apply_fju_process_review
from exchange_info.fju_student_view import fetch_fju_partner_universities
from exchange_info.application_rules import build_personal_application_plan
from exchange_info.models import PersonalApplicationPlanRequest
from exchange_info import storage

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('test,score,expected',[
 ('toefl',78,(50,59)),('toefl',79,(60,69)),('toefl',93,(60,69)),('toefl',94,(70,79)),
 ('toefl',95,(70,79)),('toefl',114,(90,99)),('toefl',115,(100,100)),
 ('toeic',750,(50,59)),('toeic',785,(60,69)),('toeic',990,(80,89)),
 ('ielts',6.5,(60,60)),('toefl_new',4,(60,60)),('toefl_new',4.5,(70,70))])
def test_briefing_score_ranges_and_boundary_changes(test,score,expected):
    assert fju_internal_language_score_range(test,score)==expected
    assert fju_internal_language_points(test,score)==(expected[0] if expected[0]==expected[1] else None)

@pytest.mark.parametrize('test,score',[('toefl',121),('toeic',995),('ielts',6.25),('toefl_new',4.25),('toefl',float('nan'))])
def test_unlisted_scores_do_not_get_invented_exact_points(test,score):
    assert fju_internal_language_score_range(test,score) is None
    assert fju_internal_language_points(test,score) is None

def test_eligibility_and_scoring_have_different_cutoffs_and_require_scale_identity():
    assert fju_language_check('ielts',6.0)[0]=='fail'
    assert fju_internal_language_points('ielts',6.0)==50
    assert fju_language_check('toefl_new',4.0)[0]=='pass'
    assert fju_language_check('toefl_new',3.5)[0]=='fail'
    assert fju_language_check('toefl',4.0)[0]=='needs_confirmation'
    assert fju_language_check('toefl',float('inf'))[0]=='needs_confirmation'
    assert '70–79' in fju_language_check('toefl',95)[1]
    assert '100 分' not in fju_language_check('toefl',95)[1]

def test_application_time_year_and_conditional_graduation_requirements():
    assert fju_degree_check('大學部','大一')[0]=='fail'
    assert fju_degree_check('大學部',None)[0]=='needs_confirmation'
    assert fju_degree_check('大學部','大二')[0]=='pass'
    assert '申請' in fju_degree_check('大學部','大二')[1]
    assert fju_degree_check('大學部','大五')[0]=='needs_confirmation'
    assert fju_degree_check('碩士班','未知')[0]=='needs_confirmation'

def test_current_views_no_longer_publish_obsolete_weights_or_conversion():
    m=load_manifest(ROOT)
    assert m['sources'][SLIDES_URL]['visual_pages_read']==list(range(13,21))
    for filename in ('student_dashboard.json','home_rules.json','exchange_info.json'):
        row=json.loads((ROOT/'src/exchange_info/official_data/fju'/filename).read_text('utf8'))
        text=json.dumps(row,ensure_ascii=False)
        assert '歷年成績 25%' not in text and '佔總分 25%' not in text and '佔外語組總成績 25%' not in text
        assert SCORING_FORMULA in text
    raw=json.loads((ROOT/'src/exchange_info/official_data/fju/student_dashboard.json').read_text('utf8'))
    assert raw['language_requirements'][0]['details'][1]==SCORING_TABLE_NOTE

def test_personal_plan_keeps_reference_host_conditions_unknown_and_links_current_scoring():
    partners=fetch_fju_partner_universities();temple=next(p for p in partners if p.school_name.startswith('天普大學 '))
    plan=build_personal_application_plan(PersonalApplicationPlanRequest(home_school='輔大',academic_year='116',
        application_round='第1學期（秋季班）',degree_level='大學部',current_year='大二',academic_score=85,
        language_test='toefl_new',language_score=4,preferences=[{'rank':1,'school_name':temple.school_name}]),
        partners,storage.load_bundled_application_workflows(),academic_score_minimum=70)
    checks={c.code:c for c in plan.choices[0].checks}
    assert checks['home_language_score'].status=='pass'
    assert checks['home_language_score'].source_url==SLIDES_URL
    assert checks['language_score'].status=='needs_confirmation'


def test_nomination_months_are_not_old_interview_dates_or_final_admission():
    summary=process_manifest(ROOT)['new_selection_summary']
    workflows=[w for w in storage.load_bundled_application_workflows() if w.home_university=='天主教輔仁大學' and len(w.steps)==5]
    assert len(workflows)==234
    for workflow in workflows:
        step=workflow.steps[2]
        assert step.summary==summary and '2027/02' in step.summary and '2027/03' in step.summary
        assert '保證金金額' in step.summary and '待' in step.summary
        assert step.needs_confirmation and step.support_status=='needs_confirmation'
        assert step.deadline_at is None and not step.deadline_reminder_eligible
        assert '校內面試' not in step.title and '12 月底至 1 月初' not in step.summary
    for p in fetch_fju_partner_universities():
        if p.school_name.startswith('(自費)') and p.school_name in {r['school_name'] for r in json.loads((ROOT/'docs/data-verification-20261021/round47-fju-missing-routes.json').read_text('utf8'))['records']}:
            continue
        assert summary in p.application_info


def test_process_overlay_replays_without_rewriting_later_values(tmp_path):
    import shutil
    bundle=tmp_path/'fju';shutil.copytree(ROOT/'src/exchange_info/official_data/fju',bundle)
    path=bundle/'application_workflows.jsonl';rows=[json.loads(l) for l in path.read_text('utf8').splitlines()]
    rows[0]['steps'][2]['summary']='Synthetic later official review'
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),'utf8')
    before={p.name:p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    assert apply_fju_process_review(ROOT,bundle=bundle)==0
    assert before=={p.name:p.read_bytes() for p in bundle.iterdir() if p.is_file()}
