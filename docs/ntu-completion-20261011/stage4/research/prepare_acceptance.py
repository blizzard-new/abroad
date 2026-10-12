from pathlib import Path
import json,subprocess,shutil
r=Path('/workspace/abroad-ntu-completion-20261011');target=Path('/workspace/abroad-ntu-pr8-acceptance-20261011');scratch=Path(__file__).parent;pr8=scratch.parent/'stage3/pr8-files';sha='59a20f27fcee00fb597abc79e75ec11778317422'
changed=subprocess.check_output(['git','diff','--name-only',sha],cwd=r,text=True).splitlines();changed+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=r,text=True).splitlines()
for name in changed:
 if name.startswith(('src/','scripts/','tests/','sources/')) and not name.endswith('.zip'):
  p=r/name
  if p.is_file():dest=target/name;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(p,dest)
pr8_names=[x['path'] for x in json.load(open(scratch.parent/'stage3/pr8-file-receipts.json'))];intersection=sorted(set(changed)&set(pr8_names));locations='src/exchange_info/official_data/university_locations.jsonl'
for name in pr8_names:
 if name!=locations:shutil.copyfile(pr8/name,target/name)
load=lambda b:{(x['school_name'],x.get('country')):x for s in b.splitlines() if s.strip() for x in [json.loads(s)]}
b=load(subprocess.check_output(['git','show',sha+':'+locations],cwd=r));o=load((r/locations).read_bytes());t=load((pr8/locations).read_bytes());ours={k for k in b.keys()|o.keys() if b.get(k)!=o.get(k)};theirs={k for k in b.keys()|t.keys() if b.get(k)!=t.get(k)};assert not ours&theirs
merged=dict(o)
for k in theirs:
 if k in t:merged[k]=t[k]
 else:merged.pop(k,None)
(target/locations).write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for k,x in sorted(merged.items())))
receipt={'base_main_sha':sha,'pr8_fixed_head':'9927ec1d8765a9772671bbaa68e7f920995f1258','ntu_source_sha256':__import__('hashlib').sha256((r/'sources/ntu/completion-2026-10-11.json').read_bytes()).hexdigest(),'simulation_worktree':str(target),'actual_PR9_changed_file_intersection':intersection,'location_record_changes_PR9':sorted(ours),'location_record_changes_PR8':sorted(theirs),'location_record_intersection':[],'simulation_only_no_shared_file_change_in_PR9':True,'merged_or_deployed':False}
(scratch/'pr8-intersection.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False))
