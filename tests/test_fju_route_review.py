"""Reference-table facts must not become confirmed intakes or sibling routes."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from exchange_info.fju_route_review import load_manifest, apply_fju_route_review, ARCHIVE_KEY
from exchange_info.fju_oct20_updates import repair_fju_attachment_links, load_fju_oct20_update_payload
from exchange_info.fju_student_view import fetch_fju_partner_universities, build_fju_student_dashboard
from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PartnerUniversity, UniversityApplicationWorkflow, DestinationProfile
from exchange_info import storage

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'src/exchange_info/official_data/fju'


def rows(path):
    return [json.loads(line) for line in path.read_text('utf8').splitlines() if line.strip()]


def test_table_constraints_remain_reference_and_preserve_distinct_routes():
    manifest=load_manifest(ROOT)
    assert len(manifest['table_transcription'])==30
    assert {r['school_chinese'] for r in manifest['unmatched_source_routes']}=={'東洋大學','南山大學','同志社大學'}
    partners={p.school_name:p for p in fetch_fju_partner_universities()}
    dashboard={p.school_name:p for p in build_fju_student_dashboard().partner_universities}
    for t in manifest['table_transcription']:
        name=t['matched_school_name']
        if not name:continue
        p=partners[name]
        assert dashboard[name]==p
        assert t['language'] in p.language_requirement
        assert t['period'] in p.study_period
        assert p.field_evidence['language_requirement'].status=='reference_only'
        assert p.quota_status=='reference_only' and p.availability_status!='open'
    def get(prefix):return next(p for n,p in partners.items() if n.startswith(prefix+' '))
    assert '碩士僅Type A：JLPT N1' in get('武藏野大學').language_requirement
    assert '基本日語能力' in get('北見工業大學').language_requirement
    assert '優先' in get('北見工業大學').language_requirement
    assert '或JLPT N2' in get('琉球大學').language_requirement
    assert '中止或有條件' in get('近畿大學').availability_note
    assert '只能一學期' in get('同志社大學').study_period
    assert '通常名額（參考用）：1' in get('東洋大學').quota
    for prefix in ('(語言密集課程)聖心女子大學','(自費)梅光學院大學'):
        p=get(prefix)
        assert '不得套用一般交換名額' in p.quota
        assert p.field_evidence['language_requirement'].status=='needs_confirmation'
        assert p.language_conditions==[]


def test_four_profiles_do_not_guarantee_generic_costs_or_housing():
    profiles=storage.load_destination_profiles(home_university='天主教輔仁大學')
    selected=[p for p in profiles if 'Baiko' in p.school_name or 'Sacred Heart' in p.school_name]
    assert len(selected)==4
    for p in selected:
        assert p.cost_evidence.status=='needs_confirmation'
        assert '80,000–130,000' not in p.cost_summary
        assert all('校內宿舍名額有限' not in (s.caution or '') for s in p.student_guide_sections)
    baiko=next(p for p in selected if p.school_name.startswith('梅光'))
    assert '校內無宿舍' in baiko.housing_summary
    assert '2026春季' in baiko.housing_summary and '2027秋季' in baiko.housing_summary
    special=next(p for p in selected if p.school_name.startswith('(自費)'))
    assert '251,500' not in special.cost_summary


def test_scoped_patches_validate_and_replay_without_touching_other_routes(tmp_path):
    bundle=tmp_path/'fju';shutil.copytree(BUNDLE,bundle)
    manifest=load_manifest(ROOT)
    from exchange_info.fju_form_review import load_manifest as form_manifest
    later={(s['file'],s['school_name'],p['pointer']):p['value']
           for s in form_manifest(ROOT)['rows'] for p in s['patches']}
    models={'partners.jsonl':PartnerUniversity,'application_workflows.jsonl':UniversityApplicationWorkflow,
            'destination_profiles.jsonl':DestinationProfile}
    for scope in manifest['rows']:
        name=Path(scope['file']).name
        row=next(r for r in rows(bundle/name) if r['school_name']==scope['school_name'])
        models[name].model_validate(row)
        archive=row['reference_data'][ARCHIVE_KEY]
        archive=json.loads(archive) if isinstance(archive,str) else archive
        for patch in scope['patches']:
            parent,key=pointer_parent(row,patch['pointer'])
            expected=later.get((scope['file'],scope['school_name'],patch['pointer']),patch['value'])
            assert parent[key]==expected
            assert archive[patch['pointer']]['existed']!=patch['expected_missing']
    before={p.name:p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    assert apply_fju_route_review(ROOT,bundle=bundle)==0
    assert before=={p.name:p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    path=bundle/'partners.jsonl';data=rows(path)
    chosen=next(r for r in data if r['school_name'].startswith('聖心'))
    chosen['quota']='Synthetic later independent review'
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data),'utf8')
    assert apply_fju_route_review(ROOT,bundle=bundle)==0
    assert next(r for r in rows(path) if r['school_name']==chosen['school_name'])['quota']==chosen['quota']
    data.append(deepcopy(chosen));path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data),'utf8')
    with pytest.raises(ValueError,match='exactly once'):apply_fju_route_review(ROOT,bundle=bundle)


def test_attachment_repairs_use_actual_downloads_and_keep_historical_archive(tmp_path):
    archive=ROOT/'sources/fju/2026-10-20-official-update.json';before=archive.read_bytes()
    payload=load_fju_oct20_update_payload()
    urls=[s['source_url'] for s in payload['source_manifest'].values()]
    assert sum('DownloadNewsFileServlet' in url for url in urls)==4
    assert archive.read_bytes()==before
    bundle=tmp_path/'fju';shutil.copytree(BUNDLE,bundle)
    manifest=json.loads((ROOT/'docs/data-verification-20261021/round46-fju-attachment-link-review.json').read_text('utf8'))
    for scope in manifest['rows']:
        p=bundle/Path(scope['file']).name
        data=rows(p) if p.suffix=='.jsonl' else json.loads(p.read_text('utf8'))
        for patch in scope['patches']:
            parent,key=pointer_parent(data,patch['pointer']);parent[key]=patch['expected_value']
        text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data) if p.suffix=='.jsonl' else json.dumps(data,ensure_ascii=False)
        p.write_text(text,'utf8')
    assert repair_fju_attachment_links(bundle)==26
    assert repair_fju_attachment_links(bundle)==0
    assert archive.read_bytes()==before
