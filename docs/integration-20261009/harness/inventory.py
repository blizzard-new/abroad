import collections,hashlib,json,pathlib,subprocess
r=pathlib.Path('/workspace/abroad-integration');o=pathlib.Path('/workspace/integration-evidence/inventory');o.mkdir(exist_ok=True)
refs={'main':'f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59','pr2_provisional':'5d48a01a7a58aad7fe972e7ec1434e0fb74e93c3','pr3':'5eadeb569ea0ae048e2c49450ee8c4012d24d630','pr4':'eddd7af6e700e2d7685be95e3c96484a9fa378b1','pr5':'b8833a6a6ffc8236276fa7870e4c1ff541c34117'}
def g(*a):return subprocess.check_output(['git',*a],cwd=r)
files={k:g('diff','--name-only',refs['main'],v).decode().splitlines() for k,v in refs.items() if k!='main'}
shared={p:[k for k,f in files.items() if p in f] for p,n in collections.Counter(p for f in files.values() for p in f).items() if n>1}
inventory={'refs':refs,'counts':{k:len(v) for k,v in files.items()},'changed_files':files,'shared_paths':shared,'migrations':{},'repo_instructions':{}}
for k,v in refs.items():
 tree=g('ls-tree','-r',v,'supabase/migrations').decode();inventory['migrations'][k]=tree.splitlines()
 paths=g('ls-tree','-r','--name-only',v).decode().splitlines();inventory['repo_instructions'][k]=[p for p in paths if p.endswith(('AGENTS.md','SKILL.md')) or p.startswith('.agents/')]
 for p in shared:
  dest=o/'patches'/k/(p+'.patch');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(g('diff','--unified=8',refs['main'],v,'--',p))
(o/'inventory.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False))
print(json.dumps({'counts':inventory['counts'],'shared':shared,'instructions':inventory['repo_instructions'],'migration_counts':{k:len(v) for k,v in inventory['migrations'].items()}},ensure_ascii=False,indent=2))
