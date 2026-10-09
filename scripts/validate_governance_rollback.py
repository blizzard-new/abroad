"""Real negative/positive rollback transactions in the owned disposable harness."""
import copy
import hashlib
import json

import requests

from exchange_info import governance_commands as commands
from exchange_info.content_governance import (
    rollback_published_workflow,stage_workflow_refresh,publish_workflow_revision,
    build_application_workflow_publication_history,workflow_content_hash,
    workflow_review_source_urls,workflow_review_rule_keys,
)
from exchange_info.models import ApplicationWorkflowRollbackRequest


def require(condition,message):
    if not condition:raise RuntimeError('Rollback runtime: '+message)


def envelope(store,request):
    buffer=commands.WorkflowCommandBuffer(store)
    rollback_published_workflow(buffer,request,rolled_back_by='synthetic-a')
    original={row.id:row for row in buffer.original_revisions}
    changed=[row for row in buffer.revisions.values() if row.id not in original or
        commands.canonical(row)!=commands.canonical(original[row.id])]
    revisions=[{**store._revision_row(row),'required_source_urls':workflow_review_source_urls(row.workflow),
        'required_rule_keys':workflow_review_rule_keys(row.workflow)} for row in changed]
    return commands.rpc_command_parameters({'kind':'workflow','expected':buffer.expected,
        'revisions':revisions,'published':[commands.canonical(row) for row in buffer.changed_workflows.values()],
        'operation':'rollback_published_workflow','actor':'synthetic-a'})


def validate_publication_shape_denials(*,first,revision_id,snapshot):
    buffer=commands.WorkflowCommandBuffer(first)
    publish_workflow_revision(buffer,revision_id,reviewer_id='synthetic-a')
    original={row.id:row for row in buffer.original_revisions}
    changed=[row for row in buffer.revisions.values() if row.id not in original or
        commands.canonical(row)!=commands.canonical(original[row.id])]
    valid=commands.rpc_command_parameters({'kind':'workflow','expected':buffer.expected,
        'revisions':[{**first._revision_row(row),'required_source_urls':workflow_review_source_urls(row.workflow),
            'required_rule_keys':workflow_review_rule_keys(row.workflow)} for row in changed],
        'published':[commands.canonical(row) for row in buffer.changed_workflows.values()],
        'operation':'publish_workflow_revision','actor':'synthetic-a'})
    before=snapshot();results=[]
    for key,shape,value,status in [
        (key,shape,value,400) for key in ('published','revisions') for shape,value in
        [('missing',None),('null',None),('object',{}),('string','synthetic-invalid-array')]
    ]+[('published','empty',[],409)]:
        body=copy.deepcopy(valid);command=body['p_change_summary']['governance_command']
        if shape=='missing':del command[key]
        else:command[key]=value
        try:first._request('POST','/rest/v1/rpc/exchange_commit_application_workflow_revision',json=body)
        except requests.HTTPError as error:
            require(error.response.status_code==status,'standard publication '+key+'_'+shape+' returned '+str(error.response.status_code))
            response=error.response.json()
        else:raise RuntimeError('Malformed standard publication accepted: '+key+'_'+shape)
        after=snapshot();require(before==after,'standard publication '+key+'_'+shape+' changed one of six tables')
        results.append({'case':key+'_'+shape,'HTTP_status':status,'response':response,
            'all_six_snapshots_unchanged':True,'before_snapshot_SHA256':hashlib.sha256(before.encode()).hexdigest(),
            'after_snapshot_SHA256':hashlib.sha256(after.encode()).hexdigest()})
    return {'cases':results,'valid_original_publication_envelope':valid,
        'original_six_table_snapshot':json.loads(before),'production_access':False}


def validate_rollback_denials(context,*,psql,first,rollback,snapshot):
    valid=envelope(first,rollback);expected=snapshot();results=[]
    def denied(body,label,expected_status=409):
        before=snapshot()
        try:first._request('POST','/rest/v1/rpc/exchange_commit_application_workflow_revision',json=body)
        except requests.HTTPError as error:
            require(error.response.status_code==expected_status,label+' returned '+str(error.response.status_code)+' instead of '+str(expected_status))
            response=error.response.json()
        else:raise RuntimeError('Invalid rollback accepted: '+label)
        after=snapshot();require(before==after,label+' changed one of six tables')
        results.append({'case':label,'HTTP_status':expected_status,'response':response,'all_six_snapshots_unchanged':True,
            'before_snapshot_SHA256':hashlib.sha256(before.encode()).hexdigest(),
            'after_snapshot_SHA256':hashlib.sha256(after.encode()).hexdigest(),
            'snapshot_table_counts':{key:len(rows or []) for key,rows in json.loads(before).items()}})
    for label in ['publish_label_on_rollback','standard_action_with_chain','null_rollback_IDs',
                  'missing_restore','current_as_restore','superseded_as_current','wrong_version_chain',
                  'changed_restored_approvals','changed_superseded_companion','reject_label_with_published_row',
                  'duplicate_revision_identity']:
        body=copy.deepcopy(valid);command=body['p_change_summary']['governance_command'];row=next(r for r in command['revisions'] if r['status']=='published');companion=next(r for r in command['revisions'] if r['status']=='superseded')
        if label=='publish_label_on_rollback':command['operation']='publish_workflow_revision'
        elif label=='standard_action_with_chain':row['publication_action']='standard'
        elif label=='null_rollback_IDs':row['rolled_back_from_revision_id']=row['restored_revision_id']=None
        elif label=='missing_restore':row['restored_revision_id']='synthetic-missing-restore'
        elif label=='current_as_restore':row['restored_revision_id']=rollback.expected_current_revision_id
        elif label=='superseded_as_current':row['rolled_back_from_revision_id']=rollback.restore_revision_id
        elif label=='wrong_version_chain':row['version']+=1;row['workflow_payload']['version']=row['version'];command['published'][0]['version']=row['version']
        elif label=='changed_restored_approvals':row['review_approvals'][1]['reviewer_id']='synthetic-unattested'
        elif label=='changed_superseded_companion':companion['review_approvals'][1]['reviewer_id']='synthetic-unattested'
        elif label=='reject_label_with_published_row':command['operation']='reject_workflow_revision';command['published']=[]
        elif label=='duplicate_revision_identity':command['revisions'].append(copy.deepcopy(companion))
        denied(body,label)
    # Each case starts with the complete legitimate envelope; mutate one key.
    # Invalid shape is 400, while an array with an invalid publication is 409.
    for key in ('published','revisions'):
        for shape,value in [('missing',None),('null',None),('object',{}),('string','synthetic-invalid-array')]:
            body=copy.deepcopy(valid);command=body['p_change_summary']['governance_command']
            if shape=='missing':del command[key]
            else:command[key]=value
            denied(body,key+'_'+shape,400)
    body=copy.deepcopy(valid);body['p_change_summary']['governance_command']['published']=[]
    denied(body,'empty_publication_array')
    # Corrupt only the isolated historical row: a valid-looking copied reviewer
    # still lacks an independent recorded approval/publication. Restore every
    # original byte before exercising the legitimate rollback.
    original=psql(context,"select review_approvals::text from public.application_workflow_revisions where id='"+rollback.restore_revision_id+"';")
    forged=json.loads(original);forged[1]['reviewer_id']='synthetic-unattested'
    try:
        psql(context,"update public.application_workflow_revisions set review_approvals=$case$"+json.dumps(forged)+"$case$::jsonb where id='"+rollback.restore_revision_id+"';")
        denied(envelope(first,rollback),'stored_historical_reviewer_without_approval_provenance')
    finally:
        psql(context,"update public.application_workflow_revisions set review_approvals=$case$"+original+"$case$::jsonb where id='"+rollback.restore_revision_id+"';")
    require(snapshot()==expected,'historical fixture restoration changed original state')
    return {'cases':results,'valid_original_rollback_envelope':valid,'original_six_table_snapshot':json.loads(expected),
        'historical_corruption_scope':'Synthetic temporary DB only; exact original review array restored in finally',
        'original_state_fully_restored':True,'production_access':False}


def validate_chained_rollback(*,first,second,restored,snapshot):
    from validate_governance_runtime import workflow,approve
    from exchange_info import content_governance
    candidate=stage_workflow_refresh(first,workflow('Synthetic publication after rollback')).revision
    approve(first,candidate,'synthetic-a');approve(second,candidate,'synthetic-b')
    original_clock=content_governance.utc_now
    try:
        # PostgreSQL renders .120000 as .12; both denote the same stored instant.
        # A legitimate next transaction must preserve it without textual drift.
        content_governance.utc_now=lambda:original_clock().replace(microsecond=120000)
        publish_workflow_revision(first,candidate.id,reviewer_id='synthetic-a')
    finally:content_governance.utc_now=original_clock
    state=next(row for row in build_application_workflow_publication_history(second).items if row.workflow_key==restored.workflow_key)
    request=ApplicationWorkflowRollbackRequest(workflow_key=state.workflow_key,
        expected_current_revision_id=state.current_revision_id,expected_current_version=state.current_version,
        expected_current_content_hash=state.current_content_hash,restore_revision_id=restored.id,
        note='Synthetic legitimate restoration of a previously audited rollback')
    chained=rollback_published_workflow(second,request,rolled_back_by='synthetic-a');before=snapshot()
    require(rollback_published_workflow(first,request,rolled_back_by='synthetic-a').id==chained.id and
        snapshot()==before,'chained rollback retry changed data or audit')
    require(chained.restored_revision_id==restored.id and chained.review_approvals==restored.review_approvals and
        workflow_content_hash(second.load_published_workflows()[0])==restored.content_hash,'chained rollback lost source review lineage')
    return {'new_revision':chained.model_dump(mode='json'),'restored_rollback_revision':restored.model_dump(mode='json'),
        'exact_review_snapshot_preserved':True,'timestamp_roundtrip_with_trailing_fractional_zeros':True,
        'replay_no_mutations':True,'all_six_after':json.loads(before)}
