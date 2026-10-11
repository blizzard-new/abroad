import datetime,json,os,pathlib,subprocess,sys
root=pathlib.Path('/workspace/pr9-review-20261011');code=pathlib.Path(sys.argv[1]);name=sys.argv[2];out=root/name;out.mkdir(exist_ok=False)
env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ['EXCHANGE_','SUPABASE','DATABASE_URL','PGPASSWORD','PGHOST','PGUSER'])}
env.update(PYTHONPATH=str(code/'src')+':'+str(code)+':'+str(root),EXCHANGE_ENVIRONMENT='development',EXCHANGE_INFO_DATA_DIR=str(out/'runtime-data'))
command=['/workspace/abroad-six-final/.venv/bin/python','-m','pytest','-q',*sys.argv[3:],*json.loads((root/'13-tests.json').read_text())]
meta={'command':command,'code_root':str(code),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executable':command[0],'isolation':'dedicated dev runtime; production EXCHANGE/SUPABASE/DB environment excluded','test_result':'running'}
(out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
with (out/'stdout.log').open('wb') as o,(out/'stderr.log').open('wb') as e:r=subprocess.run(command,cwd=code,env=env,stdout=o,stderr=e,timeout=300)
meta.update(finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=r.returncode,test_result='passed' if r.returncode==0 else 'failed');(out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
