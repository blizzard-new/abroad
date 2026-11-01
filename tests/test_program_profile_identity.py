"""Route identity checks do not establish factual accuracy of school content."""
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info import storage
from exchange_info.api import create_app
from exchange_info.application_rules import select_application_workflow, _matches_partner
from exchange_info.destination_profile_review import (
    LocalDestinationProfileReviewStore, apply_destination_profile_promotions,
    build_destination_profile_review_queue, record_destination_profile_review,
    promote_destination_profile, REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS,
)
from exchange_info.models import (ApplicationRuleContext, CollectionAudit, DestinationProfile,
    DestinationProfileReviewSubmitRequest, DestinationProfilePromotionRequest, SourceReference)
from exchange_info.school_identity import school_identity_key, school_program_identity_key, same_school_program

ROOT=Path(__file__).resolve().parents[1]
HOME='天主教輔仁大學'
NAMES=(
    '聖心女子大學 University of the Sacred Heart, Tokyo',
    '(語言密集課程)聖心女子大學 University of the Sacred Heart, Tokyo',
    '梅光學院大學 Baiko Gakuin University',
    '(自費)梅光學院大學 Baiko Gakuin University',
)


def raw_profiles():
    path=ROOT/'src/exchange_info/official_data/fju/destination_profiles.jsonl'
    return [DestinationProfile.model_validate_json(line) for line in path.read_text('utf8').splitlines()]


def test_program_annotations_remain_distinct_without_changing_institutions():
    for plain, labelled in zip(NAMES[::2],NAMES[1::2]):
        assert school_identity_key(plain)==school_identity_key(labelled)
        assert school_program_identity_key(plain)!=school_program_identity_key(labelled)
        assert not same_school_program(plain,labelled)
        assert not _matches_partner([plain],labelled)
    assert school_program_identity_key('（自費）梅光學院大學 Ｂａｉｋｏ Gakuin University')==school_program_identity_key(NAMES[3])
    assert same_school_program('(自費)Baiko Gakuin University',NAMES[3])
    assert school_program_identity_key('(原EISTI) CY塞爾吉-巴黎大學 CY Cergy Paris University-CY Tech')==school_identity_key('(原EISTI) CY塞爾吉-巴黎大學 CY Cergy Paris University-CY Tech')
    assert same_school_program('聖心女子大學 University of the Sacred Heart, Tokyo','University of the Sacred Heart, Tokyo')


def test_all_supported_bundles_keep_every_profile_and_raw_content():
    from exchange_info.university_registry import SUPPORTED_UNIVERSITIES
    profiles=storage.load_destination_profiles(include_bundled_baseline=True)
    assert len(profiles)==9026
    added_homes = {u.school_name for u in SUPPORTED_UNIVERSITIES if u.id in {"ncue", "nknu", "tmu", "csmu", "cmu", "kmu", "mcu", "ntub", "ncnu", "ndhu", "thu", "shu", "pu", "usc", "nuk", "ncyu", "nutc", "nfu", "utaipei", "ntcu", "tnua", "ntua", "ntue", "ncut", "npust"}}
    assert sum(p.home_university not in added_homes for p in profiles)==4588
    for home in SUPPORTED_UNIVERSITIES:
        path=ROOT/f'src/exchange_info/official_data/{home.id}/destination_profiles.jsonl'
        expected={json.loads(line)['school_name'] for line in path.read_text('utf8').splitlines()}
        actual={p.school_name for p in profiles if p.home_university==home.school_name}
        assert actual==expected,home.id
    assert len([p for p in profiles if p.home_university==HOME])==237
    assert len(apply_destination_profile_promotions(profiles,[],[]))==9026


def test_upsert_and_collection_audit_preserve_sibling_routes_and_other_homes(tmp_path):
    selected=[p for p in raw_profiles() if p.school_name in NAMES]
    other=selected[-1].model_copy(update={'home_university':'Synthetic other home'})
    storage.save_destination_profiles([*selected,other],tmp_path)
    edited=selected[-1].model_copy(update={'cost_summary':'Synthetic route-specific update'})
    storage.upsert_destination_profile(edited,tmp_path)
    actual=storage.load_destination_profiles(tmp_path,include_bundled_baseline=False)
    assert len(actual)==5
    for old in [*selected,other]:
        fresh=next(p for p in actual if (p.home_university,p.school_name)==(old.home_university,old.school_name))
        assert fresh==(edited if old is selected[-1] else old)
    for name in NAMES:
        storage.upsert_collection_audit(CollectionAudit(home_university=HOME,school_name=name,collector='destinations',
            status='official_partial',result_count=1),tmp_path)
    assert {a.school_name for a in storage.load_collection_audits(tmp_path)}==set(NAMES)


def test_workflow_selection_keeps_each_program_even_when_sibling_is_newer():
    workflows=[w for w in storage.load_bundled_application_workflows() if w.home_university==HOME and w.school_name in NAMES]
    assert len(workflows)==4
    for target in workflows:
        siblings=[w.model_copy(update={'version':999,'last_checked':datetime(2099,1,1,tzinfo=timezone.utc)})
                  if w.school_name!=target.school_name else w for w in workflows]
        selected=select_application_workflow(siblings,ApplicationRuleContext(home_university=HOME,partner_university=target.school_name))
        assert selected.school_name==target.school_name
    assert select_application_workflow(workflows,ApplicationRuleContext(home_university=HOME,
        partner_university='(其他課程)梅光學院大學 Baiko Gakuin University')) is None


@pytest.fixture(scope='module')
def client(tmp_path_factory):
    with TestClient(create_app(tmp_path_factory.mktemp('program-profile-api'))) as value:
        yield value


def test_public_list_detail_and_coverage_keep_all_four_programs(client):
    for compact in (False,True):
        response=client.get('/destination-profiles',params={'home_school':'fju','compact':str(compact).lower()})
        assert response.status_code==200
        profiles=response.json();assert len(profiles)==237
        assert set(NAMES).issubset({p['school_name'] for p in profiles})
    for name in NAMES:
        response=client.get('/destination-profile',params={'home_school':'fju','school':name})
        assert response.status_code==200 and response.json()['school_name']==name
        assert response.json()['home_university']==HOME
        assert client.get('/school-data-completeness',params={'home_school':'fju','school':name}).json()['school_name']==name
    implicit=client.get('/destination-profile',params={'school':NAMES[-1]})
    assert implicit.status_code==200 and implicit.json()['home_university']==HOME
    assert implicit.json()['school_name']==NAMES[-1]
    coverage=client.get('/coverage',params={'school':'fju'}).json()
    assert coverage['destination_profile_count']==237
    assert client.get('/destination-profile',params={'home_school':'fju','school':'(其他課程)'+NAMES[2]}).status_code==404


def test_review_and_promotion_never_approve_or_replace_the_sibling_program(tmp_path):
    # Synthetic reviews exist only in tmp_path; they do not verify real data.
    profiles=[DestinationProfile(home_university=HOME,school_name=name,country='日本',
        cost_summary=f'Synthetic profile {index}',coverage_status='official_partial',
        last_checked=datetime(2026,10,21,tzinfo=timezone.utc),
        sources=[SourceReference(title='Synthetic test source',source_url=f'https://example.edu/{index}')])
        for index,name in enumerate(NAMES)]
    store=LocalDestinationProfileReviewStore(tmp_path)
    target=profiles[-1]
    def queue():
        return build_destination_profile_review_queue(profiles,home_university=HOME,review_events=store.list_events(),
            promotion_events=store.list_promotion_events(),rollback_events=store.list_rollback_events())
    for reviewer in ('synthetic-a','synthetic-b'):
        q=queue();row=next(r for r in q.items if r.school_name==target.school_name)
        request=DestinationProfileReviewSubmitRequest(home_university=HOME,school_name=target.school_name,
            expected_snapshot=q.snapshot_fingerprint,expected_profile_content_hash=row.profile_content_hash,
            decision='approve',note='Synthetic test-only review of this one route',
            reviewed_source_urls=[s.source_url for s in target.sources],
            reviewed_section_keys=[s.key for s in REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS])
        record_destination_profile_review(store,profiles,request,reviewer_id=reviewer,reviewer_display_name=reviewer)
    q=queue()
    assert next(r for r in q.items if r.school_name==target.school_name).ready_for_promotion
    assert all(not r.ready_for_promotion for r in q.items if r.school_name!=target.school_name)
    row=next(r for r in q.items if r.school_name==target.school_name)
    request=DestinationProfilePromotionRequest(home_university=HOME,school_name=target.school_name,
        expected_snapshot=q.snapshot_fingerprint,expected_profile_content_hash=row.profile_content_hash,
        note='Synthetic test-only promotion of the self-funded route')
    promote_destination_profile(store,profiles,request,promoted_by_id='synthetic-a',promoted_by_display_name='Synthetic A')
    public=apply_destination_profile_promotions(profiles,store.list_promotion_events(),store.list_rollback_events())
    assert len(public)==4
    for old in profiles:
        current=next(p for p in public if p.school_name==old.school_name)
        if old.school_name==target.school_name:assert current.coverage_status=='official_verified'
        else:assert current==old
