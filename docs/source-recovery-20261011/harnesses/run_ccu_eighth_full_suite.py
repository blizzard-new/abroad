"""Run the unchanged full-suite shard harness at a single clean candidate."""
from pathlib import Path
import concurrent.futures, json, subprocess

app=Path('/workspace/abroad-globe-20261011')
raw=Path('/workspace/recovery-evidence-20261011')
prefix='integration-next2'
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=app,text=True).strip()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=app).strip()
def run(i):
    name=f'{prefix}-full-shard-{i}'
    tmp=Path('/tmp')/(name+'-tmp');tmp.mkdir(exist_ok=False)
    env=['EXCHANGE_TEST_POSTGRES=1',f'TMPDIR={tmp}',
         'PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/workspace/integration-tools/browsers/chromium-1234/chrome-linux64/chrome']
    for variable,suffix in [('VISUAL_EVIDENCE_DIR','images'),('TKU_CENSUS_ASSET_EVIDENCE','tku-images'),
            ('TKU_ACCEPTANCE_OUTPUT','tku-acceptance-images'),('CCU_ACCEPTANCE_OUTPUT','ccu-images'),
            ('NCU_NEXT3_BROWSER_OUT','ncu-images'),('NCU_RESUME_BROWSER_OUTPUT','ncu-resume-images'),
            ('CCU_PRIORITY_SCREENSHOTS','ccu-priority-images'),('NTU_REFERENCE_SCREENSHOTS','ntu-reference-images'),('CCU_ROUND8_SCREENSHOTS','ccu-round8-images')]:
        env.append(f'{variable}={raw}/{name}-{suffix}')
    command=['python','/workspace/recovery-tools-20261011/run_check.py','--cwd',str(app),
             '--name',name,'--timeout','3600','--','env',*env,
             '/workspace/abroad-six-final/.venv/bin/python','scripts/run_web_quality_tests.py',
             '--shard',str(i),'--shards','4','--junitxml',str(raw/name/'result.xml'),
             '--evidence-dir',str(raw/name/'shard-coverage')]
    result=subprocess.run(command,cwd=app,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    print(json.dumps({'shard':i,'sha':sha,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr}),flush=True)
    return result.returncode
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    codes=list(pool.map(run,range(4)))
assert not any(codes),codes
