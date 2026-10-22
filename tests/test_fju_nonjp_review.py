"""Reference table coverage and source limitations must survive application."""
import json
from pathlib import Path
import shutil
import pytest
from exchange_info.fju_nonjp_review import load_manifest, apply_fju_nonjp_review, ARCHIVE_KEY
from exchange_info.fju_briefing_review import apply_fju_briefing_review
from exchange_info.fju_form_review import apply_fju_form_review, ENROLLMENT
from exchange_info.fju_host_review import load_manifest as host_manifest, apply_fju_host_review
from exchange_info.fju_oct20_updates import apply_fju_oct20_updates
from exchange_info.fju_student_view import fetch_fju_partner_universities
from exchange_info.application_rules import _partner_language_threshold
from exchange_info.host_source_review_round25 import pointer_parent

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'src/exchange_info/official_data/fju'

def partner(prefix):
    return next(p for p in fetch_fju_partner_universities() if p.school_name.startswith(prefix+' '))

def test_57_reviewed_rows_and_114_targets_preserve_every_patch_and_prior_value():
    m=load_manifest(ROOT)
    later={(s['file'],s['school_name'],p['pointer']):p['value']
           for s in host_manifest(ROOT)['rows'] for p in s['patches']}
    assert len(m['table_transcription'])==57 and len(m['rows'])==114
    assert {t['page'] for t in m['table_transcription']}=={1,2,3,4}
    for scope in m['rows']:
        matches=[json.loads(l) for l in (ROOT/scope['file']).read_text('utf8').splitlines()
                 if json.loads(l)['school_name']==scope['school_name']]
        assert len(matches)==1
        row=matches[0];history=row['reference_data'][ARCHIVE_KEY]
        history=json.loads(history) if isinstance(history,str) else history
        for patch in scope['patches']:
            parent,key=pointer_parent(row,patch['pointer'])
            expected=later.get((scope['file'],scope['school_name'],patch['pointer']),patch['value'])
            assert parent[key]==expected
            assert history[patch['pointer']]['existed']!=patch['expected_missing']
            if not patch['expected_missing']:
                assert history[patch['pointer']]['value'] in patch['expected_values']

@pytest.mark.parametrize('name',['蒙特雷大學','普福爾茨海姆大學'])
def test_visibly_clipped_language_is_not_promoted_to_a_complete_requirement(name):
    p=partner(name)
    assert '截斷' in p.language_requirement
    assert p.field_evidence['language_requirement'].status=='needs_confirmation'
    assert _partner_language_threshold(p,'toefl','大學部') is None

def test_degree_conflict_department_limits_and_nonallocated_capacity_are_explicit():
    baptist=partner('香港浸會大學')
    assert baptist.field_evidence['degree_levels'].status=='needs_confirmation'
    assert '前後' in baptist.availability_note and 'L4' in baptist.course_restrictions
    assert 'ICT' in partner('方堤斯應用科技大學').course_restrictions
    assert '商學院' in partner('香港城市大學').course_restrictions
    electrical=partner('電氣通信大學')
    assert '不是輔大獲配名額' in electrical.quota and 'Video Letter' in electrical.language_requirement
    assert '4人/學期 (雙邊) + 1人 (Erasmus+)' in partner('羅馬國際研究大學').quota

def test_current_opening_and_hard_language_thresholds_are_not_inferred_from_reference_rows():
    osaka=partner('大阪商業大學')
    assert '暫停' in osaka.availability_note and '0人' in osaka.quota
    temple=partner('天普大學')
    assert '聽讀各390' in temple.language_requirement
    assert _partner_language_threshold(temple,'toeic','大學部') is None
    salzburg=partner('薩爾斯堡大學')
    assert '不強制' in salzburg.language_requirement
    assert all(partner(t['school_name'].split(' ')[0]).field_evidence['quota'].status=='reference_only'
               for t in load_manifest(ROOT)['table_transcription'])

def test_replaying_current_and_legacy_overlays_preserves_all_reviewed_bytes(tmp_path):
    bundle=tmp_path/'fju';shutil.copytree(B,bundle)
    before={p.name:p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    assert apply_fju_oct20_updates(bundle)['skipped_legacy_snapshot'] is True
    assert apply_fju_form_review(ROOT,bundle=bundle)==0
    assert apply_fju_nonjp_review(ROOT,bundle=bundle)==0
    assert apply_fju_briefing_review(ROOT,bundle=bundle)==0
    assert apply_fju_host_review(ROOT,bundle=bundle)==0
    assert before=={p.name:p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    assert all(ENROLLMENT in p.eligibility for p in fetch_fju_partner_universities())
