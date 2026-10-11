from pathlib import Path
import os,subprocess,sys,json,hashlib
root=Path('/workspace/memory-fix-probe-20261011')
changed=('json_stream.py','ncu_student_view.py','ccu_overseas.py','ccu_profile.py','life_context.py','source_integrity.py','ccu_completion_sources.py')
print(json.dumps({'diagnostic_only':True,'source_base':'eb4a5cddd03b6fc20a13794fd737780062a4a10c','overlay':{n:hashlib.sha256((root/'src/exchange_info'/n).read_bytes()).hexdigest() for n in changed}},indent=2),flush=True)
os.chdir(root)
raise SystemExit(subprocess.call([sys.executable,'/workspace/recovery-tools-20261011/profile_memory.py',*sys.argv[1:]]))
