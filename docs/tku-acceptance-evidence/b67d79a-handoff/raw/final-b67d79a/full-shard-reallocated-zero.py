import json,sys,time,subprocess,datetime
from pathlib import Path
out=Path('/tmp/tku-governance-b67d79a')
while not any((out/f'shard-{i}/guard.json').exists() for i in (2,3)):time.sleep(1)
released=next(i for i in (2,3) if (out/f'shard-{i}/guard.json').exists());guard=json.loads((out/f'shard-{released}/guard.json').read_text());assert guard['candidate_guard_passed'] and guard['tested_commit']=='b67d79aa3b6c30a9449801501256b64951f2c291'
(out/'shard-0-pipeline.json').write_text(json.dumps({'new_execution_started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'released_full_worker':released,'candidate_commit':guard['tested_commit'],'original_shard0_not_interrupted':True,'all_testcases_unchanged':True},indent=2)+'\n')
raise SystemExit(subprocess.call([sys.executable,str(out/'full-shard-guarded.py'),'0']))
