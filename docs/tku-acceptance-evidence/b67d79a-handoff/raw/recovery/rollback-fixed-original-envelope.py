import copy,hashlib,json,pathlib,requests
RAW=pathlib.Path('/workspace/abroad-tku-evidence-e1c551a/docs/tku-acceptance-evidence/5d48a01/sql-diagnostic/result.json')
CASE=pathlib.Path('/workspace/abroad-tku-evidence-e1c551a/docs/tku-acceptance-evidence/5d48a01-readable/rpc/005.json')
TABLES={'workflows':'application_workflows','revisions':'application_workflow_revisions','audit':'application_workflow_audit_log','reviews':'destination_profile_review_events','promotions':'destination_profile_promotion_events','rollbacks':'destination_profile_rollback_events'}
def reproduce(context,psql):
 source=json.loads(RAW.read_text())['atomic_governance']['rpc_evidence'];case=json.loads(CASE.read_text());assert source[5]==case and case['http_status']==409 and case['snapshot_unchanged']
 rows={key:[] for key in TABLES}
 for call in source[:5]:
  for key,delta in call['full_delta'].items():
   for old in delta['before']:rows[key].remove(old)
   rows[key].extend(delta['after'])
 for key,table in TABLES.items():
  if rows[key]:psql(context,f"insert into public.{table} overriding system value select * from jsonb_populate_recordset(null::public.{table},$case${json.dumps(rows[key],ensure_ascii=False)}$case$::jsonb);")
 psql(context,"select setval(pg_get_serial_sequence('public.application_workflow_audit_log','id'),(select max(id) from public.application_workflow_audit_log),true);")
 def snapshot():return psql(context,"select jsonb_build_object("+','.join(f"'{key}',(select coalesce(jsonb_agg(to_jsonb(t) order by {'workflow_key' if key=='workflows' else 'id'}),'[]'::jsonb) from public.{table} t)" for key,table in TABLES.items())+");")
 before=snapshot();envelope=copy.deepcopy(case['envelope']);headers={'apikey':context.service_token,'Authorization':'Bearer '+context.service_token};url=context.postgrest_url+'/rpc/exchange_commit_application_workflow_revision'
 original=requests.post(url,json=envelope,headers=headers,timeout=30);after_original=snapshot();assert original.status_code==409 and before==after_original
 forged=copy.deepcopy(envelope);forged['p_change_summary']['governance_command']['operation']='rollback_published_workflow';mutated=requests.post(url,json=forged,headers=headers,timeout=30);after_mutated=snapshot()
 expected=copy.deepcopy(envelope);expected['p_change_summary']['governance_command']['operation']='rollback_published_workflow';assert forged==expected
 result={'tested_commit':'b67d79aa3b6c30a9449801501256b64951f2c291','source_case':str(CASE),'source_case_SHA256':hashlib.sha256(CASE.read_bytes()).hexdigest(),'source_case_HTTP':409,'source_case_snapshot_unchanged':True,'scope':'Original saved service-only RPC005 envelope; only operation changed. Isolated ten-governance-migration SQL with original six-table mutation deltas replayed; new schema-capability marker timestamp only. Not a general admin API reachability claim.','original_envelope':envelope,'original_response':{'status':original.status_code,'body':original.json(),'all_six_snapshots_unchanged':before==after_original},'only_operation_changed':True,'relabeled_envelope':forged,'relabeled_response':{'expected_status':409,'actual_status':mutated.status_code,'body':mutated.json(),'all_six_snapshots_unchanged':before==after_mutated},'before_six_tables':json.loads(before),'after_original_six_tables':json.loads(after_original),'after_relabeled_six_tables':json.loads(after_mutated),'production_access':False}
 assert mutated.status_code==409 and before==after_mutated,'Operation-only command was not denied without mutation; inspect actual response'
 result['status']='passed_original_immutable_RPC005_and_operation_only_denial';return result
