from pathlib import Path
import hashlib,json,subprocess,tarfile,zipfile,sys
root=Path('/workspace/abroad-tku-boundaries-fix');out=Path('/tmp/tku-acceptance-12b30cd');sha='12b30cd78a812f829d1ba32d33d72d8df2595e6e'
def state():
 return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()}
before=state();assert before=={'commit':sha,'dirty':''}
build=Path('/tmp/tku-package-build-12b30cd');build.mkdir(exist_ok=False)
archive=Path('/tmp/tku-ci-12b30cd/source.tar')
subprocess.run(['git','archive',sha,'-o',str(archive)],cwd=root,check=True)
with tarfile.open(archive) as t:t.extractall(build,filter='data')
with Path('/tmp/tku-ci-12b30cd/package-build.log').open('w') as f:
 subprocess.run([sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--no-cache-dir','-w',str(out/'wheel'),str(build)],stdout=f,stderr=subprocess.STDOUT,check=True)
wheel=next((out/'wheel').glob('*.whl'));files=[]
with zipfile.ZipFile(wheel) as z:
 for p in sorted((build/'src/exchange_info').rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
   n=str(p.relative_to(build/'src'));assert z.read(n)==p.read_bytes(),n;files.append(n)
 assert len(files)==1009
record={'tested_commit':sha,'starting_state':before,'ending_state':state(),'wheel_bytes':wheel.stat().st_size,'wheel_sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'verified_payload_files':len(files),'all_packaged_source_files_byte_identical_to_candidate':True,'status':'passed','build_source':'independent git archive; pip wheel --no-deps --no-build-isolation --no-cache-dir'}
assert record['ending_state']==before
record['candidate_guard_passed']=True
(out/'packaging-check.json').write_text(json.dumps(record,indent=2)+'\n')
previous='5e010b80b59d274d8a30332aabcab2c46929a313';rows=[]
for school in ['cgu','ntpu','ntu','tku']:
 path='src/exchange_info/official_data/'+school
 trees=[subprocess.check_output(['git','rev-parse',f'{c}:{path}'],cwd=root,text=True).strip() for c in [previous,sha]];assert trees[0]==trees[1]
 rows.append({'path':path,'previous_tree':trees[0],'candidate_tree':trees[1],'byte_identical_git_tree':True})
(out/'data-preservation.json').write_text(json.dumps({'tested_commit':sha,'previous_complete_candidate':previous,'official_bundles':rows,'no_official_data_changes':True},indent=2)+'\n')
print(json.dumps(record))
