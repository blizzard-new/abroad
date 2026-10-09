import sys,time,tempfile,json,threading,subprocess,datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from exchange_info import storage
from exchange_info.content_governance import LocalContentGovernanceStore
root=Path.cwd();sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();label=sys.argv[1];out=Path('/tmp/ncu-performance-profile-ded2ed1');out.mkdir(exist_ok=True);tmp=Path(tempfile.mkdtemp(prefix='ncu-concurrency-'));storage.ensure_data_dirs(tmp)
orig=storage._cached_workflows;records=[];guard=threading.Lock()
def wrapped(key,build):
 def counted():
  started=time.perf_counter()
  try:return build()
  finally:
   with guard:records.append({'kind':key[0],'elapsed_s':time.perf_counter()-started})
 return orig(key,counted)
storage._cached_workflows=wrapped
store=LocalContentGovernanceStore(tmp,include_bundled_baseline=True);barrier=threading.Barrier(3)
def get():
 barrier.wait();start=time.perf_counter();rows=store.load_published_workflows();return {'elapsed_s':time.perf_counter()-start,'count':len(rows),'home_counts':dict(Counter(w.home_university for w in rows))}
start=time.perf_counter()
with ThreadPoolExecutor(max_workers=3)as pool: results=list(pool.map(lambda _:get(),range(3)))
report={'tested_sha':sha,'label':label,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cold_process':True,'three_concurrent_reads':results,'builds':records,'total_elapsed_s':time.perf_counter()-start,'end_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'worktree':subprocess.check_output(['git','status','--porcelain'],text=True)}
(out/f'{label}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
