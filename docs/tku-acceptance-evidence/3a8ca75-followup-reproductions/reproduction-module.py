import json,requests,tempfile
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
from exchange_info import governance_commands as commands
from exchange_info.content_governance import SupabaseContentGovernanceStore,LocalContentGovernanceStore,stage_workflow_refresh,workflow_content_hash,structure_application_workflow
from exchange_info.models import ApplicationWorkflowReviewStatus,ApplicationWorkflowRevision
from exchange_info.workflow_identity import workflow_storage_key
from exchange_info.storage import save_application_workflows
from validate_governance_runtime import workflow,approve

def run_case(context,*,psql,kind):
 def transport(method,url,**kwargs):
  parsed=urlsplit(url);assert parsed.hostname=='runtime-supabase.invalid'
  return requests.request(method,context.postgrest_url+parsed.path.removeprefix('/rest/v1'),**kwargs)
 def snapshot():
  return psql(context,"select jsonb_build_object('workflows',(select jsonb_agg(to_jsonb(t) order by workflow_key) from public.application_workflows t),'revisions',(select jsonb_agg(to_jsonb(t) order by id) from public.application_workflow_revisions t),'audit',(select jsonb_agg(to_jsonb(t) order by id) from public.application_workflow_audit_log t),'reviews',(select jsonb_agg(to_jsonb(t) order by id) from public.destination_profile_review_events t),'promotions',(select jsonb_agg(to_jsonb(t) order by id) from public.destination_profile_promotion_events t),'rollbacks',(select jsonb_agg(to_jsonb(t) order by id) from public.destination_profile_rollback_events t));")
 store=SupabaseContentGovernanceStore('https://runtime-supabase.invalid',context.service_token,request_func=transport)
 result={'kind':kind,'production_access':False,'expected':'reject forged approval with all snapshots unchanged' if kind=='forge' else 'superseded baseline and pending; public unchanged'}
 out=Path('/tmp/tku-governance-followup-repro')/kind;out.mkdir(parents=True,exist_ok=True)
 if kind=='forge':
  candidate=stage_workflow_refresh(store,workflow('Synthetic original')).revision;approve(store,candidate,'synthetic-a')
  buffer=commands.WorkflowCommandBuffer(store);one=next(x for x in buffer.list_revisions() if x.id==candidate.id)
  assert len(one.review_approvals)==1 and one.review_approvals[0].reviewer_id=='synthetic-a'
  second=one.review_approvals[0].model_copy(update={'reviewer_id':'synthetic-b'})
  public=one.workflow.model_copy(update={'governance_key':one.workflow_key,'review_status':ApplicationWorkflowReviewStatus.PUBLISHED,'published_at':datetime.now(timezone.utc)})
  forced=one.model_copy(update={'status':ApplicationWorkflowReviewStatus.PUBLISHED,'workflow':public,'reviewed_by':'synthetic-a','reviewed_at':datetime.now(timezone.utc),'review_approvals':[one.review_approvals[0],second]})
  before=snapshot();error=None
  try:store.commit_command(buffer.expected,[forced],[public],operation='publish_workflow_revision',actor='synthetic-a')
  except Exception as e:error=str(e)
  after=snapshot();result.update(accepted=error is None,error=error,snapshot_unchanged=before==after,before=json.loads(before),after=json.loads(after))
  (out/'case-result.json').write_text(json.dumps(result,indent=2)+'\n')
  assert error is not None and before==after,'Reproduced: second reviewer string was forged only in publish payload, accepted and changed persisted snapshot'
 elif kind=='pagination':
  for i in range(3):
   content=structure_application_workflow(workflow('Synthetic capped row').model_copy(update={'school_name':f'Synthetic capped host {i}'}))
   store.save_revision(ApplicationWorkflowRevision(workflow_key=workflow_storage_key(content),version=1,content_hash=workflow_content_hash(content),workflow=content))
  revisions,public,expected=store.command_snapshot();actual=int(psql(context,'select count(*) from public.application_workflow_revisions;'))
  result.update(actual_revision_count=actual,returned_revision_count=len(revisions),returned_snapshot_revision_count=len(expected['revisions']),truncation_explicitly_detected=False)
  (out/'case-result.json').write_text(json.dumps(result,indent=2)+'\n');assert len(revisions)==actual,'Reproduced: capped snapshot silently omitted persisted rows'
 else:
  with tempfile.TemporaryDirectory(prefix='tku-legacy-refresh-repro-',dir='/tmp') as directory:
   legacy=workflow('Synthetic legacy public');legacy.version=1;save_application_workflows([legacy],Path(directory))
   store.fallback=LocalContentGovernanceStore(Path(directory));assert store.list_revisions()==[]
   public_before=[x.model_dump_json() for x in store.load_published_workflows()];before=snapshot();error=None;response=None
   try:response=stage_workflow_refresh(store,workflow('Synthetic legacy changed'))
   except Exception as e:error=str(e);result['actual_http_response']=e.response.text if isinstance(e,requests.HTTPError) else None
   after=snapshot();public_after=[x.model_dump_json() for x in store.load_published_workflows()]
   result.update(accepted=error is None,error=error,snapshot_unchanged=before==after,public_unchanged=public_before==public_after,before=json.loads(before),after=json.loads(after),statuses=[x.status.value for x in store.list_revisions()])
   (out/'case-result.json').write_text(json.dumps(result,indent=2)+'\n')
   assert error is None and sorted(result['statuses'])==['pending_review','superseded'] and public_before==public_after,'Reproduced: legacy refresh rejected rather than atomically creating superseded baseline and pending'
 return result
