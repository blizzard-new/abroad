"""A reviewed mother form does not establish host admission or complete costs."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil

import pytest
from fastapi.testclient import TestClient

from exchange_info import storage
from exchange_info.api import create_app
from exchange_info.application_rules import select_application_workflow
from exchange_info.cost_estimates import budget_fit, extract_monthly_estimates
from exchange_info.fju_form_review import apply_fju_form_review, current_home_submission_step, ENROLLMENT
from exchange_info.fju_missing_routes_review import apply_fju_missing_routes, load_manifest
from exchange_info.fju_oct20_updates import apply_fju_oct20_updates, load_fju_oct20_update_payload
from exchange_info.fju_student_view import fetch_fju_partner_universities
from exchange_info.models import ApplicationRuleContext

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'src/exchange_info/official_data/fju'
NEW=('(自費)東洋大學 Toyo University','(自費)南山大學 Nanzan University','(自費)同志社大學 Doshisha University')


def test_all_237_routes_distinguish_required_and_conditional_form_endorsements():
    workflows=[w for w in storage.load_bundled_application_workflows() if w.home_university=='天主教輔仁大學']
    assert len(workflows)==237
    for w in workflows:
        step=w.steps[1]
        form=step.document_requirements[0]
        assert len(form.signatures)==2
        assert form.stamps==['系所秘書','系主任／所長','院長']
        conditional=next(d for d in step.document_requirements if d.conditional)
        assert '五年級以上' in conditional.condition and '延畢' in conditional.condition
        assert len(conditional.stamps)==2
        assert ENROLLMENT in step.details
        assert 'A113' not in step.summary and 'A113' not in step.title
        assert any('網路查詢成績證明' in text for text in step.details)
    assert all(ENROLLMENT in p.eligibility for p in fetch_fju_partner_universities())


def test_old_import_preserves_later_reviews_byte_for_byte(tmp_path):
    bundle=tmp_path/'fju';shutil.copytree(BUNDLE,bundle)
    before={p.name:p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    result=apply_fju_oct20_updates(bundle)
    assert result['skipped_legacy_snapshot'] is True
    assert before=={p.name:p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    assert apply_fju_form_review(ROOT,bundle=bundle)==0
    assert apply_fju_missing_routes(ROOT,bundle=bundle)==0
    assert before=={p.name:p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    archived=ROOT/'sources/fju/2026-10-20-official-update.json';old=archived.read_bytes()
    payload=load_fju_oct20_update_payload()
    assert payload['actual_system_and_submission_opens_at'] is None
    assert payload['actual_system_and_submission_opens_on']=='2026-11-01'
    assert 'A113' not in payload['paper_required_documents'][0]
    assert archived.read_bytes()==old


def test_missing_build_inputs_fail_before_any_output_write(tmp_path,monkeypatch):
    spec=importlib.util.spec_from_file_location('isolated_fju_builder',ROOT/'scripts/build_fju_catalog.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    bundle=tmp_path/'output';bundle.mkdir();sentinel=bundle/'import_provenance.json';sentinel.write_text('{"preserve":true}','utf8')
    monkeypatch.setattr(module,'SCRATCH_FJU',tmp_path/'missing_inputs')
    monkeypatch.setattr(module,'OFFICIAL_FJU_DIR',bundle)
    monkeypatch.setattr(module,'SOURCES_FJU_DIR',tmp_path/'sources')
    before=sentinel.read_bytes()
    with pytest.raises(FileNotFoundError,match='no output was modified'):module.main()
    assert sentinel.read_bytes()==before
    assert not (tmp_path/'sources').exists()
    assert list(bundle.iterdir())==[sentinel]


def test_added_self_funded_rows_remain_independent_and_explicitly_incomplete():
    partners={p.school_name:p for p in fetch_fju_partner_universities()}
    profiles={p.school_name:p for p in storage.load_destination_profiles(home_university='天主教輔仁大學')}
    workflows=[w for w in storage.load_bundled_application_workflows() if w.home_university=='天主教輔仁大學']
    assert len(partners)==237 and len(profiles)==237
    for name in NEW:
        p=partners[name];general=partners[name.removeprefix('(自費)')]
        assert p.quota_status=='reference_only' and p.availability_status=='agreement_only'
        assert p.location is None and p.image_status=='missing'
        assert p.field_evidence['tuition_info'].status=='reference_only'
        assert budget_fit(extract_monthly_estimates(profiles[name]),1000000)['status']=='unknown'
        for target in (p,general):
            found=select_application_workflow(workflows,ApplicationRuleContext(home_university='天主教輔仁大學',partner_university=target.school_name))
            assert found.school_name==target.school_name
    assert '371,000' in partners[NEW[2]].tuition_info and '703,500' in partners[NEW[2]].tuition_info
    assert '一學年' in partners[NEW[2]].study_period
    assert '只能一學期' in partners[NEW[2].removeprefix('(自費)')].study_period
    assert '500,000' in partners[NEW[0]].tuition_info
    assert '沒有列明收費金額' in partners[NEW[1]].tuition_info


def test_new_routes_are_visible_through_public_partner_profile_and_workflow_paths(tmp_path):
    with TestClient(create_app(tmp_path/'api')) as client:
        listed=client.get('/destination-profiles',params={'home_school':'fju'}).json()
        assert len(listed)==237 and set(NEW).issubset({r['school_name'] for r in listed})
        for name in NEW:
            response=client.get('/destination-profile',params={'home_school':'fju','school':name})
            assert response.status_code==200 and response.json()['school_name']==name
            completeness=client.get('/school-data-completeness',params={'home_school':'fju','school':name})
            assert completeness.status_code==200 and completeness.json()['score']<1


def test_added_route_replay_keeps_later_edits_and_rejects_ambiguous_identity(tmp_path):
    bundle=tmp_path/'fju';shutil.copytree(BUNDLE,bundle)
    path=bundle/'partners.jsonl';rows=[json.loads(l) for l in path.read_text('utf8').splitlines()]
    target=next(r for r in rows if r['school_name']==NEW[0]);target['tuition_info']='Synthetic later independent review'
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),'utf8')
    assert apply_fju_missing_routes(ROOT,bundle=bundle)==0
    assert next(json.loads(l) for l in path.read_text('utf8').splitlines() if json.loads(l)['school_name']==NEW[0])['tuition_info']==target['tuition_info']
    rows.append(deepcopy(target));path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),'utf8')
    with pytest.raises(ValueError,match='Ambiguous'):apply_fju_missing_routes(ROOT,bundle=bundle)
