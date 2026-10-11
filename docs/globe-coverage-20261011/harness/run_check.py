import argparse, datetime, json, os, pathlib, subprocess, time
p=argparse.ArgumentParser();p.add_argument('--cwd',required=True);p.add_argument('--name',required=True);p.add_argument('--timeout',type=int,default=3600);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
root=pathlib.Path('/workspace/globe-evidence-20261011')/a.name;root.mkdir(parents=True,exist_ok=False)
def git(*args):return subprocess.check_output(['git',*args],cwd=a.cwd,text=True).strip()
def guard():return {'sha':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'status':git('status','--porcelain=v1')}
env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ('SUPABASE','EXCHANGE_','DATABASE_URL','PGPASSWORD','PGHOST','PGPORT','PGUSER'))}
env.update(EXCHANGE_ENVIRONMENT='development',EXCHANGE_INFO_DATA_DIR=str(root/'runtime-data'),UV_CACHE_DIR='/workspace/integration-tools/uv-cache',PLAYWRIGHT_BROWSERS_PATH='/workspace/integration-tools/browsers',PYTHONUNBUFFERED='1',TZ='UTC',PYTHONPATH=str(pathlib.Path(a.cwd)/'src')+os.pathsep+a.cwd)
command=a.command[1:] if a.command and a.command[0]=='--' else a.command
meta={'command':command,'cwd':a.cwd,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'start_guard':guard(),'timeout_seconds':a.timeout,'test_result':'running','isolation':'production EXCHANGE/SUPABASE/DB environment removed; dedicated development data and browser paths'}
(root/'metadata.json').write_text(json.dumps(meta,indent=2))
try:
 with (root/'stdout.log').open('wb') as out,(root/'stderr.log').open('wb') as err:
  result=subprocess.run(command,cwd=a.cwd,env=env,stdout=out,stderr=err,timeout=a.timeout)
 meta.update(exit_code=result.returncode,test_result='passed' if result.returncode==0 else 'failed')
except subprocess.TimeoutExpired:
 meta.update(exit_code=124,test_result='failed',reason='timeout')
finally:
 meta.update(finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),end_guard=guard())
 (root/'metadata.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta,ensure_ascii=False))
raise SystemExit(meta['exit_code'])
