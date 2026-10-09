import json,sys,time,subprocess,datetime
from pathlib import Path
shard=int(sys.argv[1]);old=Path('/tmp/tku-governance-b8f5e07')/f'shard-{shard}'/'guard.json';out=Path('/tmp/tku-governance-b67d79a')
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
while not old.exists():time.sleep(1)
previous=json.loads(old.read_text());assert previous['tested_commit']=='b8f5e075fe920860492c0eb3e18e06c5da71903b' and previous['candidate_guard_passed']
proof={'shard':shard,'waiting_started_at':started,'new_execution_started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_guard_path':str(old),'prior_actual_exit_code':previous['actual_exit_code'],'prior_logs_preserved':True,'new_tested_commit':'b67d79aa3b6c30a9449801501256b64951f2c291'}
(out/f'shard-{shard}-pipeline.json').write_text(json.dumps(proof,indent=2)+'\n')
raise SystemExit(subprocess.call([sys.executable,str(out/'full-shard-guarded.py'),str(shard)]))
