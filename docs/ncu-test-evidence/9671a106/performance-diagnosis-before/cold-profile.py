import cProfile,pstats,time,tempfile,os,json,sys
from pathlib import Path
from exchange_info.api import create_app
from exchange_info.storage import ensure_data_dirs
out=Path('/tmp/ncu-performance-profile-ded2ed1');out.mkdir(exist_ok=True)
path=Path(tempfile.mkdtemp(prefix='ncu-prof-'));ensure_data_dirs(path);app=create_app(data_dir=path)
routes={r.path:r.endpoint for r in app.routes if hasattr(r,'endpoint')}
case=sys.argv[1]
if case=='workflows':
 fn=lambda: app.state.content_governance_store.load_published_workflows()
elif case=='workflow':
 fn=lambda:routes['/application-workflow'](school='新潟大學 Niigata University',home_school='國立中央大學',academic_year=None,application_round=None,student_stage=None)
elif case=='coverage':fn=lambda:routes['/coverage'](school='長庚大學')
elif case=='audit':
 from exchange_info.ncu_student_view import ncu_field_audit
 fn=lambda:ncu_field_audit('新潟大學 Niigata University')
else:raise ValueError(case)
p=cProfile.Profile();start=time.perf_counter();p.enable()
try:r=fn();err=None
except Exception as e:err=str(e)
p.disable();elapsed=time.perf_counter()-start;p.dump_stats(str(out/f'{case}.prof'))
with (out/f'{case}.txt').open('w') as f:
 print(json.dumps({'case':case,'elapsed_s':elapsed,'error':err}),file=f);pstats.Stats(p,stream=f).strip_dirs().sort_stats('cumulative').print_stats(30)
print(json.dumps({'case':case,'elapsed_s':elapsed,'error':err}))
