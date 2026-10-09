import json,xml.etree.ElementTree as E,hashlib
from pathlib import Path
root=Path('/tmp/tku-ci-browser-3ccbf7c');artifact=root/'remote-artifacts'
ids={'pr':[11590068725,11590222489,11590271662,11590526575],'push':[11590169856,11590253245,11590846443,11590781796]}
summary={'head_sha':'3ccbf7c3de75b47f2f93f7aa56e96143e2e48a38','pr_merge_sha':'d738f5434ff56ad559fbd2a9e85a8546bd31c9f5','tree_equivalence':'ad78d384e7b270f4765987aae9cf0dbe0cdb8725','all_checks_passed':False,'acceptance_waiver':False,'runs':{}}
for kind,rows in ids.items():
 total={k:0 for k in ['passed','failed','skipped','error']};collected=[];actual=[];shards=[];controlcounts=dict(total)
 for aid in rows:
  r=artifact/str(aid);nodes=(r/'collect-nodeids.txt').read_text().splitlines();collected+=nodes
  aliases={(n.rsplit('::',1)[0].replace('.py','').replace('/','.').replace('::','.'),n.rsplit('::',1)[1]):n for n in nodes}
  counts={k:0 for k in total};tested=[]
  for c in E.parse(r/'suite.xml').getroot().findall('.//testcase'):
   status='failed' if c.find('failure') is not None else 'error' if c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed';counts[status]+=1
   node=aliases.get((c.attrib['classname'],c.attrib['name']))
   if node:tested.append(node);actual.append({'id':node,'status':status,'shard':len(shards)})
   else:assert c.attrib['classname']=='pytest' and c.attrib['name']=='internal',c.attrib
  control={k:0 for k in total}
  for c in E.parse(r/'main-control/suite.xml').getroot().findall('.//testcase'):
   status='failed' if c.find('failure') is not None else 'error' if c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed';control[status]+=1
  for k in total:total[k]+=counts[k];controlcounts[k]+=control[k]
  shards.append({'artifact_id':aid,'archive_bytes':(artifact/f'{aid}.zip').stat().st_size,'archive_sha256':hashlib.sha256((artifact/f'{aid}.zip').read_bytes()).hexdigest(),'result':json.loads((r/'result.json').read_text()),'counts':counts,'collected':len(nodes),'exercised':len(tested),'unrun_nodes':sorted(set(nodes)-set(tested)),'main_control_counts':control,'main_control':json.loads((r/'main-control/result.json').read_text())})
 assert len(collected)==1757 and len(set(collected))==1757
 summary['runs'][kind]={'run_id':37870196346 if kind=='pr' else 37870191848,'counts':total,'collected':1757,'exercised':len(actual),'missing':len(set(collected)-{x['id'] for x in actual}),'complete':False,'reason':'shard 0 logging BlockingIOError ended pytest with exit 3; original internal-error JUnit retained','main_control_counts':controlcounts,'shards':shards}
 (root/f'{kind}-case-results.json').write_text(json.dumps(actual,ensure_ascii=False,indent=2)+'\n')
summary['original_remote_junit_count']=8;summary['original_main_control_junit_count']=8
(root/'complete-evidence-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print({n:{k:v[k] for k in ['counts','exercised','missing','main_control_counts']} for n,v in summary['runs'].items()})
