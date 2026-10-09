import json,hashlib,copy,requests
from pathlib import Path
CASE=Path('/tmp/tku-governance-runtime-recovery/missing-published-pre-fix/case-result.json')
TABLES={'workflows':'application_workflows','revisions':'application_workflow_revisions','audit':'application_workflow_audit_log','reviews':'destination_profile_review_events','promotions':'destination_profile_promotion_events','rollbacks':'destination_profile_rollback_events'}
def validate(context,psql):
 case=json.loads(CASE.read_text());assert case['source_commit']=='b8f5e075fe920860492c0eb3e18e06c5da71903b' and case['actual_HTTP']==200 and not case['all_six_snapshots_unchanged']
 # A newly created synthetic DB has only its schema capability marker.
 # Replace this fixture marker with the original six-table snapshot exactly.
 initial_workflows=json.loads(psql(context,"select coalesce(jsonb_agg(workflow_key),'[]'::jsonb) from public.application_workflows;"))
 assert initial_workflows==['__governance_command_schema__']
 psql(context,"delete from public.application_workflow_audit_log; delete from public.application_workflows where workflow_key='__governance_command_schema__';")
 for key,table in TABLES.items():
  rows=case['before_six_tables'][key]
  if rows:psql(context,f"insert into public.{table} overriding system value select * from jsonb_populate_recordset(null::public.{table},$case${json.dumps(rows,ensure_ascii=False)}$case$::jsonb);")
 psql(context,"select setval(pg_get_serial_sequence('public.application_workflow_audit_log','id'),(select max(id) from public.application_workflow_audit_log),true);")
 def snapshot():return psql(context,"select jsonb_build_object("+','.join(f"'{key}',(select jsonb_agg(to_jsonb(t) order by {'workflow_key' if key=='workflows' else 'id'}) from public.{table} t)" for key,table in TABLES.items())+");")
 before=snapshot()
 actual=json.loads(before)
 if actual!=case['before_six_tables']:
  (Path('/tmp/tku-governance-b67d79a')/'missing-array-fixture-comparison.json').write_text(json.dumps({'original':case['before_six_tables'],'seeded':actual},indent=2)+'\n')
 assert actual==case['before_six_tables'],'Original six-table fixture mismatch; inspect saved comparison'
 body=copy.deepcopy(case['envelope']);response=requests.post(context.postgrest_url+'/rpc/exchange_commit_application_workflow_revision',json=body,headers={'apikey':context.service_token,'Authorization':'Bearer '+context.service_token},timeout=30);after=snapshot()
 result={'tested_commit':'b67d79aa3b6c30a9449801501256b64951f2c291','original_source_commit':case['source_commit'],'source_case':str(CASE),'source_case_SHA256':hashlib.sha256(CASE.read_bytes()).hexdigest(),'exact_original_envelope_unchanged':body==case['envelope'],'original_before_six_tables_exactly_seeded':True,'envelope':body,'actual_HTTP':response.status_code,'response':response.json(),'all_six_snapshots_unchanged':before==after,'before_six_tables':json.loads(before),'after_six_tables':json.loads(after),'production_access':False,'scope':'Exact original malformed missing-published service-only command and original six-table synthetic state; not general API reachability.'}
 assert response.status_code==400 and before==after,'Original malformed envelope was not denied without mutation'
 result['status']='passed';return result
