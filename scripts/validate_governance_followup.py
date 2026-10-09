"""Bounded real-RPC regressions; only the harness's synthetic loopback services."""
from datetime import datetime, timezone
import json
import multiprocessing
import time
from types import SimpleNamespace

import requests

from exchange_info import governance_commands as commands
from exchange_info.content_governance import (SupabaseContentGovernanceStore,
    stage_workflow_refresh, workflow_review_source_urls, workflow_review_rule_keys)
from exchange_info.destination_profile_review import (REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS,
    build_destination_profile_review_queue, record_destination_profile_review)
from exchange_info.models import DestinationProfile, SourceReference, DestinationProfileReviewSubmitRequest


def _worker(base,token,envelope,barrier,output):
    barrier.wait(timeout=20)
    started=time.monotonic()
    response=requests.post(base+'/rpc/exchange_commit_application_workflow_revision',
        headers={'Authorization':'Bearer '+token},json=envelope,timeout=30)
    output.put({'instance':base,'pid':multiprocessing.current_process().pid,'started':started,'finished':time.monotonic(),
        'http_status':response.status_code,'response':response.json(),'envelope':envelope})


def validate_followup(context,*,psql,first,second,destination_store,snapshot,calls,transport):
    from validate_governance_runtime import workflow,approve,require
    checks=[]
    replays=[]
    for kind in ('workflow','destination'):
        original=next(row for row in calls if 'envelope' in row and row['http_status']==200 and
            row['envelope']['p_change_summary']['governance_command']['kind']==kind)
        before=snapshot()
        response=first._request('POST','/rest/v1/rpc/exchange_commit_application_workflow_revision',json=original['envelope'])
        require(response.json()==original['response'] and snapshot()==before,'original envelope replay changed data/audit or response')
        replays.append({'kind':kind,'original_envelope':original['envelope'],'same_response':True,'all_snapshots_unchanged':True})
    checks.append('exact_original_workflow_and_destination_envelope_replay_no_mutations')

    legacy=workflow('Synthetic legacy original').model_copy(update={'school_name':'Synthetic legacy host','version':1})
    legacy_store=SupabaseContentGovernanceStore('https://runtime-supabase.invalid',context.service_token,
        fallback=SimpleNamespace(load_published_workflows=lambda:[legacy]),request_func=transport(context.postgrest_url))
    public_before=[row.model_dump_json() for row in legacy_store.load_published_workflows()]
    raw_before=psql(context,'select jsonb_agg(published_payload order by workflow_key) from public.application_workflows where published_payload is not null;')
    pending=stage_workflow_refresh(legacy_store,legacy.model_copy(update={
        'steps':[legacy.steps[0].model_copy(update={'title':'Synthetic legacy changed'})]})).revision
    legacy_rows=[row for row in second.list_revisions() if row.workflow_key==pending.workflow_key]
    require(len(legacy_rows)==2 and {row.status.value for row in legacy_rows}=={'superseded','pending_review'} and
        all(not row.review_approvals for row in legacy_rows),'legacy refresh did not create reference and pending atomically')
    require(public_before==[row.model_dump_json() for row in legacy_store.load_published_workflows()] and raw_before==
        psql(context,'select jsonb_agg(published_payload order by workflow_key) from public.application_workflows where published_payload is not null;'),
        'legacy refresh changed public payload')
    legacy_evidence={'revisions':[row.model_dump(mode='json') for row in legacy_rows],'fallback_public_unchanged':True,'DB_public_payloads_unchanged':True}
    checks.append('legacy_fallback_refresh_superseded_reference_pending_public_unchanged')

    concurrent=stage_workflow_refresh(first,workflow('Synthetic overlapping CAS').model_copy(update={'school_name':'Synthetic overlapping host'})).revision
    buffers=[commands.WorkflowCommandBuffer(first),commands.WorkflowCommandBuffer(second)]
    envelopes=[]
    for buffer,actor in zip(buffers,('synthetic-a','synthetic-b')):
        row=approve(buffer,concurrent,actor)
        revision={**first._revision_row(row),'required_source_urls':workflow_review_source_urls(row.workflow),
            'required_rule_keys':workflow_review_rule_keys(row.workflow)}
        envelopes.append(commands.rpc_command_parameters({'kind':'workflow','expected':buffer.expected,
            'revisions':[revision],'published':[],'operation':'approve_workflow_revision','actor':actor}))
    psql(context,"""create function public.runtime_governance_overlap() returns trigger language plpgsql as $$
        begin perform pg_sleep(0.3); return new; end $$;
        create trigger runtime_governance_overlap before update of review_approvals on public.application_workflow_revisions
        for each row execute function public.runtime_governance_overlap();""")
    before=json.loads(snapshot());mp=multiprocessing.get_context('fork' if 'fork' in multiprocessing.get_all_start_methods() else 'spawn');barrier=mp.Barrier(2);output=mp.Queue()
    processes=[mp.Process(target=_worker,args=(base,context.service_token,envelope,barrier,output))
        for base,envelope in zip((context.postgrest_url,context.postgrest_secondary_url),envelopes)]
    try:
        for process in processes:process.start()
        race=[output.get(timeout=40) for _ in processes]
        for process in processes:process.join(timeout=5);require(process.exitcode==0,'CAS child process failed')
    finally:
        for process in processes:
            if process.is_alive():process.terminate();process.join(timeout=5)
        psql(context,'drop trigger runtime_governance_overlap on public.application_workflow_revisions; drop function public.runtime_governance_overlap();')
    require(sorted(row['http_status'] for row in race)==[200,409] and
        max(row['started'] for row in race)<min(row['finished'] for row in race),'CAS RPC requests did not truly overlap with one winner')
    after=json.loads(snapshot());winner=next(row for row in race if row['http_status']==200)
    require(len(next(row for row in second.list_revisions() if row.id==concurrent.id).review_approvals)==1,'CAS lost or duplicated approval')
    calls.extend({'method':'POST','path':'/rest/v1/rpc/exchange_commit_application_workflow_revision',**row} for row in race)
    before_replay=snapshot();first._request('POST','/rest/v1/rpc/exchange_commit_application_workflow_revision',json=winner['envelope'])
    require(snapshot()==before_replay,'winner exact-envelope replay changed evidence')
    race_delta={key:{'before':before[key],'after':after[key]} for key in before if before[key]!=after[key]}
    checks.append('truly_overlapping_processes_exact_CAS_one_winner_and_envelope_replay')

    # Seed three legitimate candidate/review records before applying an isolated
    # role-local PostgREST cap. Restore that setting in finally; no production URL.
    capped=[]
    for index in range(3):
        capped.append(stage_workflow_refresh(first,workflow('Synthetic cap candidate').model_copy(update={'school_name':f'Synthetic cap host {index}'})).revision)
        profile=DestinationProfile(home_university='Synthetic cap home',school_name=f'Synthetic cap host {index}',
            coverage_status='official_partial',coverage_note='Synthetic bounded cap check',
            sources=[SourceReference(title='Synthetic source',source_url='https://synthetic.edu/exchange')],
            last_checked=datetime(2026,10,9,tzinfo=timezone.utc))
        queue=build_destination_profile_review_queue([profile],home_university=profile.home_university,review_events=destination_store.list_events())
        request=DestinationProfileReviewSubmitRequest(home_university=profile.home_university,school_name=profile.school_name,
            expected_snapshot=queue.snapshot_fingerprint,expected_profile_content_hash=queue.items[0].profile_content_hash,
            decision='approve',note='Synthetic complete cap fixture review',reviewed_source_urls=[source.source_url for source in profile.sources],
            reviewed_section_keys=[row.key for row in REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS])
        record_destination_profile_review(destination_store,[profile],request,reviewer_id='synthetic-cap-reviewer',reviewer_display_name='Synthetic cap')
    settings_before=psql(context,"select coalesce(rolconfig::text,'') from pg_roles where rolname='authenticator';")
    try:
        psql(context,"alter role authenticator set pgrst.db_max_rows='2'; notify pgrst,'reload config';")
        for _ in range(30):
            probe=first._request('GET','/rest/v1/application_workflow_revisions',headers={'Prefer':'count=exact'},params={'select':'id','order':'id.asc'})
            if len(probe.json())==2:break
            time.sleep(.1)
        else:raise RuntimeError('Isolated PostgREST cap=2 did not actually take effect')
        revisions,public,expected=first.command_snapshot();destination_rows,destination_expected=destination_store.command_snapshot()
        counts=json.loads(psql(context,"""select jsonb_build_object('revisions',(select count(*) from public.application_workflow_revisions),
            'workflows',(select count(*) from public.application_workflows),'reviews',(select count(*) from public.destination_profile_review_events),
            'promotions',(select count(*) from public.destination_profile_promotion_events),'rollbacks',(select count(*) from public.destination_profile_rollback_events));"""))
        require(len(revisions)==counts['revisions'] and len(expected['workflows'])==counts['workflows'] and
            all(len(destination_expected[key])==counts[key] for key in destination_expected),'cap=2 silently truncated governance snapshot')
        approve(first,capped[0],'synthetic-cap-reviewer')
        cap_evidence={'raw_cap_rows':len(probe.json()),'raw_content_range':probe.headers['Content-Range'],
            'seeded_candidates':3,'seeded_reviews':3,'actual_DB_counts':counts,'complete_snapshot_counts':
            {'revisions':len(revisions),'workflows':len(expected['workflows']),**{key:len(rows) for key,rows in destination_expected.items()}},
            'normal_write_after_complete_capped_snapshot':True}
    finally:
        psql(context,"alter role authenticator reset pgrst.db_max_rows; notify pgrst,'reload config';")
        require(psql(context,"select coalesce(rolconfig::text,'') from pg_roles where rolname='authenticator';")==settings_before,
            'isolated PostgREST role cap was not restored')
    checks.append('actual_postgrest_cap2_complete_five_table_snapshot_and_normal_write')
    return {'checks':checks,'original_envelope_replays':replays,'legacy_refresh':legacy_evidence,
        'overlapping_processes':race,'overlap_full_audit_delta':race_delta,'capped_snapshot':cap_evidence,'isolated_cap_restored':True}
