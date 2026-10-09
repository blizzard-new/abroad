from pathlib import Path
import json,sys,collections,xml.etree.ElementTree as ET,hashlib
root=Path(sys.argv[1]);commit=sys.argv[2]
ids=(root/'collect-nodeids.txt').read_text().splitlines();mapping={(n.rsplit('::',1)[0].replace('.py','').replace('/','.').replace('::','.'),n.rsplit('::',1)[1]):n for n in ids};assert len(ids)==len(set(ids))==len(mapping)
rows=[];guards=[]
for shard in range(4):
 folder=root/f'shard-{shard}';guard=json.loads((folder/'guard.json').read_text());assert guard['tested_commit']==commit and guard['candidate_guard_passed'];guards.append(guard)
 partition=json.loads((folder/'partition.json').read_text());cases=ET.parse(folder/'suite.xml').findall('.//testcase')
 for case in cases:
  key=(case.attrib['classname'],case.attrib['name']);assert key in mapping,key
  status='passed';reason=None
  for tag in ['failure','error','skipped']:
   child=case.find(tag)
   if child is not None:status={'failure':'failed','error':'error','skipped':'skipped'}[tag];reason={'message':child.attrib.get('message'),'text':child.text};break
  rows.append({'nodeid':mapping[key],'shard':shard,'outcome':status,'duration_seconds':float(case.attrib.get('time',0)),'reason':reason})
assert len(rows)==len(ids) and {r['nodeid'] for r in rows}==set(ids);assert len(rows)==len({r['nodeid'] for r in rows})
counts=dict(collections.Counter(r['outcome'] for r in rows));failures=[r for r in rows if r['outcome'] in ('failed','error')]
summary={'tested_commit':commit,'complete_full_suite':True,'unique_collected_ids':len(ids),'executed_testcases':len(rows),'counts':counts,'all_original_093_ids_preserved':not json.loads((root/'all-id-preservation.json').read_text())['removed_ids'],'source_start_end_guards_passed':True,'actual_shard_exit_codes':[g['actual_exit_code'] for g in guards],'full_suite_passed':not failures,'isolated_reruns_do_not_replace_this_result':True,'failure_nodeids':[r['nodeid'] for r in failures],'failure_messages':[r['reason']['message'] for r in failures],'production_access':False,'full34_runtime_and_Storage_not_part_of_this_pytest_result':True}
(root/'full-case-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(root/'full-suite-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');(root/'original-full-failure-details.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False));
