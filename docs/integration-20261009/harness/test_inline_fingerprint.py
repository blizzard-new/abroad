import hashlib,json,random,subprocess,time,uuid
from pathlib import Path
from governance_inline_fingerprint import fingerprint

name='abroad-hash-proof-'+uuid.uuid4().hex[:8]
image='postgres:17-alpine@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24'
def docker(*args,input=None):
 r=subprocess.run(['docker',*args],input=input,text=True,capture_output=True,timeout=60)
 if r.returncode:raise RuntimeError(r.stderr)
 return r.stdout.strip()
def sql(value):return docker('exec','-i',name,'psql','-U','postgres','-qAt','-v','ON_ERROR_STOP=1',input=value)
rng=random.Random(20261009)
atoms=[None,True,False,0,-3,123,1.25,'','a b','"quote"','\\slash','換行\n測試','é','ä','x\ty',{},[]]
def value(depth):
 if depth==0 or rng.random()<.3:return rng.choice(atoms)
 if rng.random()<.5:return [value(depth-1) for _ in range(rng.randrange(6))]
 keys=['x','long-key','a','z','中','ä','"','space key','_id','0']
 return {k:value(depth-1) for k in rng.sample(keys,rng.randrange(7))}
values=atoms+[value(4) for _ in range(300)]
payload='values '+','.join('($hash_vector$'+json.dumps(v,ensure_ascii=False)+'$hash_vector$::jsonb)' for v in values)
docker('run','--detach','--name',name,'--network','none','--tmpfs','/var/lib/postgresql/data','--env','POSTGRES_PASSWORD=local-hash-proof',image)
try:
 for _ in range(100):
  r=subprocess.run(['docker','exec',name,'pg_isready','-U','postgres'],capture_output=True)
  if not r.returncode:break
  time.sleep(.1)
 migration=Path('/workspace/abroad-pr2/supabase/migrations/20260823160000_atomic_public_community.sql').read_text()
 helpers=migration[migration.index('create or replace function public.exchange_community_canonical_json('):migration.index('create or replace function public.exchange_community_replay(')]
 sql('create role service_role;'+helpers+'revoke all on function public.exchange_community_canonical_json(jsonb),public.exchange_community_request_fingerprint(jsonb) from public,service_role;')
 expr=fingerprint('payload')
 mismatches=sql('select count(*) from ('+payload+') vectors(payload) where public.exchange_community_request_fingerprint(payload) is distinct from '+expr+';')
 assert mismatches=='0',mismatches
 results=sql('set role service_role;select '+expr+' from ('+payload+') vectors(payload);')
 assert len(results.splitlines())==len(values)
 print(json.dumps({'vectors':len(values),'exact_owner_helper_comparisons_passed':len(values),'service_role_builtin_hashes_passed':len(values),'helper_acl_unchanged':True,'production_touched':False,'vectors_sha256':hashlib.sha256(json.dumps(values,ensure_ascii=False).encode()).hexdigest()}))
finally:docker('rm','--force',name)
