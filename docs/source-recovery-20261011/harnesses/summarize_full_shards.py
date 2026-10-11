"""Verify every collected node ran in exactly one shard at one clean fixed SHA."""
from pathlib import Path
from collections import Counter
import json,sys,xml.etree.ElementTree as ET
root=Path('/workspace/recovery-evidence-20261011');prefix=sys.argv[1]
records=[];allnodes=[];allcases=[]
for i in range(4):
 p=root/f'{prefix}-full-shard-{i}';m=json.loads((p/'metadata.json').read_text());assert m['test_result']!='running'
 assert m['start_guard']==m['end_guard'] and not m['start_guard']['status'],(p,m)
 part=json.loads((p/'shard-coverage/partition.json').read_text());nodes=(p/'shard-coverage/collect-nodeids.txt').read_text().splitlines();assert len(nodes)==part['case_counts_per_shard'][i]
 node_lookup={}
 for node in nodes:
  parts=node.split('::');classname=parts[0][:-3].replace('/','.')+('\x2e'+'.'.join(parts[1:-1]) if len(parts)>2 else '')
  key=(classname,parts[-1]);assert key not in node_lookup;node_lookup[key]=node
 xml=ET.parse(p/'result.xml');cases=[]
 for c in xml.findall('.//testcase'):
  status='failed' if c.find('failure') is not None else 'error' if c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed'
  item={'nodeid':node_lookup[(c.attrib['classname'],c.attrib['name'])],'result':status,'seconds':float(c.attrib['time'])}
  if status!='passed':
   child=c.find('failure') if status=='failed' else c.find(status if status=='error' else 'skipped');item.update(message=child.attrib.get('message'),detail=child.text)
  cases.append(item)
 assert set(nodes)=={c['nodeid'] for c in cases},(i,'JUnit/collected node mismatch',set(nodes)-{c['nodeid'] for c in cases},{c['nodeid'] for c in cases}-set(nodes))
 assert len(nodes)==len(cases)
 records.append({'shard':i,'run':p.name,'sha':m['start_guard']['sha'],'tree':m['start_guard']['tree'],'result':m['test_result'],'exit_code':m['exit_code'],'counts':dict(Counter(c['result'] for c in cases)),'collected':len(nodes),'started_at':m['started_at'],'finished_at':m['finished_at']});allnodes+=nodes;allcases+=cases
assert len(allnodes)==len(set(allnodes))==part['total_cases']
assert len({r['sha'] for r in records})==len({r['tree'] for r in records})==1
count=Counter(c['result'] for c in allcases);report={'sha':records[0]['sha'],'tree':records[0]['tree'],'status':'failed' if count['failed'] or count['error'] else 'passed','counts':dict(count),'collected_unique_cases':len(allnodes),'all_collected_nodes_accounted_exactly_once':True,'all_shards_same_clean_fixed_sha':True,'notrun':0,'shards':records,'nonpassing_cases':[c for c in allcases if c['result']!='passed']}
(root/f'{prefix}-full-suite-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['shards','nonpassing_cases']},ensure_ascii=False));print(json.dumps([{'nodeid':c['nodeid'],'result':c['result'],'message':(c.get('message') or '')[:250]} for c in report['nonpassing_cases']],ensure_ascii=False,indent=2))
