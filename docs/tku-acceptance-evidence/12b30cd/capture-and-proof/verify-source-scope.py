from pathlib import Path
import hashlib,json,subprocess
root=Path('/workspace/abroad-tku-boundaries-fix');out=Path('/tmp/tku-acceptance-12b30cd');sha='12b30cd78a812f829d1ba32d33d72d8df2595e6e';prior='5e010b80b59d274d8a30332aabcab2c46929a313'
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
assert git('rev-parse','HEAD')==sha and not git('status','--porcelain')
changed=git('diff','--name-only',prior,sha).splitlines()
protected=['.agents','.codex','.aws'];assert not any(p.startswith(tuple(protected)) for p in changed)
paths=git('ls-tree','-r','--name-only',sha,'src/exchange_info/official_data').splitlines()
rows=[]
for p in paths:
 if '/tku/' in p:continue
 a=git('rev-parse',f'{prior}:{p}');b=git('rev-parse',f'{sha}:{p}');assert a==b
 rows.append({'path':p,'git_blob':b})
r={'tested_commit':sha,'previous_candidate':prior,'changed_files':changed,'preserved_existing_official_file_count':len(rows),'all_original_cgu_ntpu_ntu_blob_ids_identical':True,'protected_config_paths_changed':[],'candidate_starting_and_ending_sha':sha,'worktree_dirty':git('status','--porcelain')}
assert not r['worktree_dirty'];(out/'change-scope.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
