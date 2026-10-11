import datetime,json,os,pathlib,subprocess
root=pathlib.Path(__file__).parent
out=root/'isolated-tests-final';out.mkdir(exist_ok=False)
env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ['EXCHANGE_','SUPABASE','DATABASE_URL','PGPASSWORD','PGHOST','PGUSER'])}
env.update(PYTHONPATH='/workspace/abroad-globe-20261011/src:'+str(root),EXCHANGE_ENVIRONMENT='development',EXCHANGE_INFO_DATA_DIR=str(out/'runtime-data'))
command=['/workspace/abroad-six-final/.venv/bin/python','-m','pytest','-q','test_snapshot_proposal.py','test_existing_cgu_failure.py']
meta={'command':command,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'application_sha':'9927ec1d8765a9772671bbaa68e7f920995f1258','note':'18 standalone proposal-state cases; 2 existing-app characterization cases expect known defects; not an implemented app fix','test_result':'running'}
(out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
with (out/'stdout.log').open('wb') as o,(out/'stderr.log').open('wb') as e:r=subprocess.run(command,cwd=root,env=env,stdout=o,stderr=e,timeout=180)
meta.update(finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=r.returncode,test_result='passed' if r.returncode==0 else 'failed')
(out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
raise SystemExit(r.returncode)
