from pathlib import Path
import collections,datetime,json,re,subprocess
root=Path('/workspace/integration-evidence')
rows=[];shards=[]
for i in range(4):
 p=root/f'memory-full-shard-{i}'
 output=(p/'stdout.log').read_text()
 cases=re.findall(r'WEB_CASE (.*?) (setup|call|teardown) (passed|failed|skipped) ([\d.]+)s',output)
 rows.extend(cases)
 shards.append({'shard':i,'state':json.loads((p/'metadata.json').read_text())['test_result'],'counts':dict(collections.Counter(x[2] for x in cases)),'last':output.splitlines()[-1][-150:] if output else ''})
result={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd='/workspace/abroad-memory',text=True).strip(),'source_status':subprocess.check_output(['git','status','--porcelain=v1'],cwd='/workspace/abroad-memory',text=True).strip(),'counts':dict(collections.Counter(x[2] for x in rows)),'failed':[x[0] for x in rows if x[2]=='failed'],'shards':shards}
(root/'memory-full-live-progress.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
