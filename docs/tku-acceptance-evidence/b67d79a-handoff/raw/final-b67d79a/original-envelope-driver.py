from pathlib import Path
from types import SimpleNamespace
import subprocess,sys,socket,time,json,secrets,hashlib,requests
sys.path.insert(0,'/workspace/abroad-tku-governance-array-fixed/scripts')
sys.path.insert(0,'/workspace/abroad-tku-governance-array-fixed/src')
import validate_supabase_runtime as h
from validate_governance_runtime import validate_atomic_governance
root=Path('/workspace/abroad-tku-governance-array-fixed');folder=Path('/tmp/tku-governance-b67d79a/original-envelope-fixed');folder.mkdir(exist_ok=True)
project='tku-governance-diag-'+secrets.token_hex(5)
ports=[h._free_loopback_port() for i in range(2)]
compose=folder/'compose.yml'
compose.write_text(f'''services:
  postgres:
    image: postgres:17.6-alpine@sha256:ef257d85f76e48da1c64832459b59fcaba1a4dac97bf5d7450c77753542eee94
    environment:
      POSTGRES_PASSWORD: synthetic-diagnostic-only
    tmpfs:
      - /var/lib/postgresql/data
  postgrest:
    image: postgrest/postgrest:v14.12@sha256:54000f24847d01a2c2302e0041cf0618b875c57fb48507d743cfa9aaa50bf43c
    environment:
      PGRST_DB_URI: postgres://authenticator:synthetic-diagnostic-only@postgres:5432/postgres
      PGRST_DB_SCHEMAS: public
      PGRST_DB_ANON_ROLE: anon
      PGRST_JWT_SECRET: {h.JWT_SECRET}
    ports:
      - '127.0.0.1:{ports[0]}:3000'
  postgrest_secondary:
    image: postgrest/postgrest:v14.12@sha256:54000f24847d01a2c2302e0041cf0618b875c57fb48507d743cfa9aaa50bf43c
    environment:
      PGRST_DB_URI: postgres://authenticator:synthetic-diagnostic-only@postgres:5432/postgres
      PGRST_DB_SCHEMAS: public
      PGRST_DB_ANON_ROLE: anon
      PGRST_JWT_SECRET: {h.JWT_SECRET}
    ports:
      - '127.0.0.1:{ports[1]}:3000'
''')
base=['docker','compose','-f',str(compose),'-p',project]
def run(args,input=None):
    r=subprocess.run(base+args,input=input,text=True,capture_output=True,timeout=120)
    if r.returncode:raise RuntimeError(r.stderr or r.stdout)
    return r.stdout.strip()
def psql(ctx,sql):return run(['exec','-T','postgres','psql','-U','postgres','-d','postgres','-X','-v','ON_ERROR_STOP=1','-A','-t'],sql)
ctx=SimpleNamespace(postgrest_url=f'http://127.0.0.1:{ports[0]}',postgrest_secondary_url=f'http://127.0.0.1:{ports[1]}',service_token=h._jwt('service_role'))
files=[
'202607280002_application_content_governance.sql','20260729143531_dual_application_workflow_review.sql',
'20260807154026_application_workflow_revision_edit_history.sql','20260819090000_destination_profile_review_events.sql',
'20260819110000_destination_profile_promotion_events.sql','20260819130000_destination_profile_publication_rollbacks.sql',
'20260819150000_application_workflow_publication_rollbacks.sql','20260819170000_application_workflow_publication_integrity.sql',
'20260901100000_atomic_application_content_governance.sql','20261009080000_atomic_governance_commands.sql']
proof={'project':project,'production_access':False,'scope':'Diagnostic subset: ten actual governance migrations and the two original canonical fingerprint functions; not full Supabase runtime or Storage validation','migrations':[],'status':'failed'}
try:
    run(['up','-d','postgres'])
    for i in range(40):
        try:psql(ctx,'select 1;');break
        except RuntimeError:time.sleep(.5)
    psql(ctx,"create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create role authenticator login password 'synthetic-diagnostic-only'; grant anon,authenticated,service_role to authenticator;")
    original=(root/'supabase/migrations/20260823160000_atomic_public_community.sql').read_text()
    functions=original[original.index('create or replace function public.exchange_community_canonical_json('):original.index('create or replace function public.exchange_community_replay(')]
    psql(ctx,functions)
    aclsql="select jsonb_agg(jsonb_build_object('identity',p.oid::regprocedure::text,'acl',p.proacl,'owner',pg_get_userbyid(p.proowner),'security_definer',p.prosecdef,'config',p.proconfig) order by p.proname) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('exchange_commit_application_workflow_revision','exchange_commit_application_workflow_publication');"
    for name in files:
        raw=(root/'supabase/migrations'/name).read_text()
        if name.startswith('20261009'):before=psql(ctx,aclsql)
        psql(ctx,raw)
        proof['migrations'].append({'name':name,'sha256':hashlib.sha256(raw.encode()).hexdigest()})
        print('applied '+name,flush=True)
        if name.startswith('20261009'):
            after=psql(ctx,aclsql);assert before==after
            proof['rpc_permissions_before_after_identical']=True
            proof['rpc_permissions']=json.loads(before)
    run(['up','-d','postgrest','postgrest_secondary'])
    for url in [ctx.postgrest_url,ctx.postgrest_secondary_url]:
        for i in range(60):
            try:
                if requests.get(url,timeout=2).status_code==200:break
            except requests.RequestException:pass
            time.sleep(.5)
        else:raise RuntimeError('PostgREST not ready')
    sys.path.insert(0,'/tmp/tku-governance-runtime-recovery')
    from importlib import import_module
    repro=import_module('rollback-fixed-original-envelope')
    proof['rollback_operation_reproduction']=repro.reproduce(ctx,psql)
    proof['status']='passed'
except Exception as e:
    proof['error']=str(e)
    if isinstance(e,requests.HTTPError):proof['actual_http_error']=e.response.text
    raise
finally:
    try:run(['down','--volumes','--remove-orphans']);proof['cleanup']='passed'
    except Exception as e:proof['cleanup']=str(e)
    (folder/'result.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof),flush=True)
