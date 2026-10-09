from pathlib import Path
from collections import Counter
import json,hashlib,xml.etree.ElementTree as ET
ROOT=Path('/tmp/tku-ci-12b30cd'); ART=ROOT/'remote-artifacts'; CODE='12b30cd78a812f829d1ba32d33d72d8df2595e6e'
prior=Path('/tmp/tku-ci-browser-3ccbf7c/remote-artifacts')
old_nodes=set()
for aid in [11590068725,11590222489,11590271662,11590526575]:old_nodes.update((prior/str(aid)/'collect-nodeids.txt').read_text().splitlines())
assert len(old_nodes)==1757
old_failed={x['id'] for x in json.load(open('/tmp/tku-acceptance-4e6cabd/ci-pr-complete-case-results.json')) if x['status']=='failed'};assert len(old_failed)==66
merge=json.load(open(ROOT/'pr-merge-commit.json'));code=json.load(open(ROOT/'code-commit.json'));assert merge['tree']['sha']==code['tree']['sha']
result={'head_sha':CODE,'pr_merge_sha':merge['sha'],'same_code_tree':code['tree']['sha'],'runs':{},'acceptance_waiver':False}
for kind,run_id in [('pr',37887692057),('push',37887687888)]:
 meta=json.load(open(ROOT/(kind+'-artifacts.json')));rows=sorted(meta['artifacts'],key=lambda x:int(x['name'].rsplit('-',1)[1]));assert len(rows)==4
 counts=Counter();controls=Counter();allnodes=[];case_rows=[];control_cases=[];shards=[]
 for row in rows:
  aid=row['id'];folder=ART/str(aid);actual=json.load(open(folder/'result.json'));partition=json.load(open(folder/'partition.json'));nodes=(folder/'collect-nodeids.txt').read_text().splitlines();allnodes+=nodes
  assert actual['tested_commit']==(result['pr_merge_sha'] if kind=='pr' else CODE);assert actual['shard']==partition['shard']
  aliases={(n.rsplit('::',1)[0].replace('.py','').replace('/','.').replace('::','.'),n.rsplit('::',1)[1]):n for n in nodes};shard_counts=Counter();tested=[]
  for c in ET.parse(folder/'suite.xml').getroot().iter('testcase'):
   status='failed' if c.find('failure') is not None else 'error' if c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed'
   node=aliases.get((c.attrib['classname'],c.attrib['name']));shard_counts[status]+=1
   if node is None:
    assert c.attrib['classname']=='pytest' and c.attrib['name']=='internal'
    continue
   tested.append(node)
   cause=c.find('failure');cause=c.find('error') if cause is None else cause
   case_rows.append({'id':node,'status':status,'seconds':float(c.attrib.get('time',0)),'shard':partition['shard'],'message':cause.attrib.get('message','') if cause is not None else ''})
  assert len(tested)==len(set(tested)) and set(tested).issubset(set(nodes))
  ctl=json.load(open(folder/'main-control/result.json'));assert ctl['candidate_commit']==actual['tested_commit'];assert ctl['acceptance_waiver'] is False
  assert ctl['baseline_commit']=='f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59';assert ctl['unchanged_test_source_commit']=='4e6cabd073e4792f94959545efeb4e323fefc3f5';assert all(x.split('::',1)[0] in partition['files_per_shard'][partition['shard']] for x in ctl['cases']);control_cases+=ctl['cases']
  ctl_counts=Counter('failed' if c.find('failure') is not None else 'error' if c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed' for c in ET.parse(folder/'main-control/suite.xml').getroot().iter('testcase'));assert sum(ctl_counts.values())==len(ctl['cases'])
  assert hashlib.sha256((folder/'main-control/pytest.log').read_bytes()).hexdigest()==ctl['log_sha256'];controls.update(ctl_counts);counts.update(shard_counts)
  shards.append({'shard':partition['shard'],'artifact_id':aid,'actual_result':actual,'counts':dict(shard_counts),'collected_nodes':len(nodes),'executed_nodes':len(tested),'missing_nodes':len(set(nodes)-set(tested)),'complete':set(tested)==set(nodes),'archive_sha256':hashlib.sha256((ART/(str(aid)+'.zip')).read_bytes()).hexdigest(),'main_control_counts':dict(ctl_counts),'main_control_actual_exit':ctl['pytest_exit_code'],'same_job_same_runner_control':True})
 assert len({n.split('::',1)[0] for n in allnodes})==184;assert len(allnodes)==len(set(allnodes))==1788;assert not old_nodes-set(allnodes);assert len(set(allnodes)-old_nodes)==31;assert len(control_cases)==len(set(control_cases))==62
 passed={x['id'] for x in case_rows if x['status']=='passed'}; exercised={x['id'] for x in case_rows};failed={x['id'] for x in case_rows if x['status'] in ['failed','error']};unrun=sorted(old_failed-exercised);resolved=sorted(old_failed&passed);remaining=sorted(old_failed&failed);added=sorted(failed-old_failed)
 triage={'original_failed_nodes':66,'resolved_original_nodes':len(resolved),'resolved':resolved,'remaining_original_nodes':len(remaining),'remaining':remaining,'unrun_original_nodes':len(unrun),'unrun_original':unrun,'new_failed_nodes':len(added),'new_failed':added,'acceptance_waiver':False,'criterion':'Original IDs retained in collect. Only actually exercised passing original failures counted resolved; unrun explicitly separate. All-case completeness separately verified against original JUnit.'}
 result['runs'][kind]={'run_id':run_id,'counts':dict(counts),'collected_nodes':1788,'collected_files':184,'executed_nodes':sum(x['executed_nodes'] for x in shards),'all_cases_exercised':all(x['complete'] for x in shards),'missing_nodes':sum(x['missing_nodes'] for x in shards),'unrun_nodes':sorted(set(allnodes)-exercised),'duplicate_nodes':0,'removed_nodes':0,'added_regression_nodes':31,'same_job_main_control_counts':dict(controls),'main_control_nodes':62,'shards':shards,'original_failure_comparison':triage}
 (ROOT/(kind+'-case-results.json')).write_text(json.dumps(case_rows,ensure_ascii=False,indent=2)+'\n');(ROOT/(kind+'-original-failure-triage.json')).write_text(json.dumps(triage,ensure_ascii=False,indent=2)+'\n')
prior_cases=json.load(open('/tmp/tku-acceptance-4e6cabd/ci-pr-complete-case-results.json'));prior_skips={x['id'] for x in prior_cases if x['status']=='skipped'}
for kind in ['pr','push']:
 rows=json.load(open(ROOT/(kind+'-case-results.json')));skips={x['id'] for x in rows if x['status']=='skipped'};result['runs'][kind]['skip_comparison']={'prior_skipped':len(prior_skips),'actual_skipped':len(skips),'added_skipped':sorted(skips-prior_skips),'unrun_prior_skipped':sorted(prior_skips-{r['id'] for r in rows}),'collected_but_not_executed_prior_skips':sorted(prior_skips-skips)}
previous=json.load(open('/tmp/tku-ci-5e010b8/pr-case-results.json'));prev_ids={x['id'] for x in previous};prev_failed={x['id'] for x in previous if x['status']=='failed'}
for kind in ['pr','push']:
 rows=json.load(open(ROOT/(kind+'-case-results.json')));ids={x['id'] for x in rows};passed={x['id'] for x in rows if x['status']=='passed'};failed={x['id'] for x in rows if x['status'] in ['failed','error']}
 assert len(prev_ids)==1776 and not prev_ids-set(allnodes) and len(set(allnodes)-prev_ids)==12
 result['runs'][kind]['previous_5e_comparison']={'previous_nodes':len(prev_ids),'removed':sorted(prev_ids-set(allnodes)),'added_nodes':len(set(allnodes)-prev_ids),'unrun_previous_nodes':sorted(prev_ids-ids),'unrun_previous_failures':sorted(prev_failed-ids),'previous_failures':len(prev_failed),'resolved':sorted(prev_failed & passed),'remaining':sorted(prev_failed & failed),'new_failed':sorted(failed-prev_failed)}
result['original_candidate_junit_count']=8;result['original_main_control_junit_count']=8;result['all_checks_passed']=all(v['counts'].get('failed',0)==v['counts'].get('error',0)==0 for v in result['runs'].values())
(ROOT/'complete-evidence-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:{'counts':v['counts'],'comparison':{x:v['original_failure_comparison'][x] for x in ['resolved_original_nodes','remaining_original_nodes','new_failed_nodes']}} for k,v in result['runs'].items()})
