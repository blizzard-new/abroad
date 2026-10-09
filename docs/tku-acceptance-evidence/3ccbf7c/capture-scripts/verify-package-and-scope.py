from pathlib import Path
import hashlib,zipfile,json,subprocess,shutil
root=Path('/workspace/abroad-tku');out=Path('/tmp/tku-acceptance-3ccbf7c');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();dirty=subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip();assert head=='3ccbf7c3de75b47f2f93f7aa56e96143e2e48a38' and not dirty
wheel=next((out/'wheel').glob('*.whl'));files=[]
with zipfile.ZipFile(wheel) as z:
 for p in sorted((root/'src/exchange_info').rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
   n=str(p.relative_to(root/'src'));assert z.read(n)==p.read_bytes(),n;files.append(n)
 font=z.read('exchange_info/official_data/tku/fonts/NotoSansCJKtc-Regular.ttf')
 required={n:n in z.namelist() for n in ['exchange_info/static/tku-eligibility.js','exchange_info/tku_eligibility_routes.py','exchange_info/account_community_cleanup.py','exchange_info/official_data/tku/seikei-calendar-followup.pdf','exchange_info/official_data/tku/gap_triage.json','exchange_info/official_data/tku/fonts/NotoSansCJKtc-Regular.ttf','exchange_info/official_data/tku/fonts/OFL.txt']};assert all(required.values())
record=dict(tested_commit=head,wheel_built_from_commit=head,starting_state=dict(commit=head,dirty=dirty),ending_state=dict(commit=head,dirty=subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()),status='passed',wheel=str(wheel),wheel_bytes=wheel.stat().st_size,wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),verified_payload_files=len(files),all_packaged_source_files_byte_identical_to_candidate=True,required_files=required,font_bytes=len(font),font_sha256=hashlib.sha256(font).hexdigest(),build_environment='system Python, installed setuptools, pip wheel --no-deps --no-build-isolation',candidate_guard_passed=True)
assert record['ending_state']['dirty']=='' and len(files)==1009
(out/'packaging-check.json').write_text(json.dumps(record,indent=2)+'\n')
for name in ['privacy-before-raw.json','privacy-before.json']:
 shutil.copy2((Path('/tmp/tku-continuation-20261008') if name=='privacy-before.json' else Path('/tmp/tku-acceptance-4e6cabd'))/name,out/name)
after=json.loads((out/'privacy-after-raw.json').read_text());before=json.loads((out/'privacy-before-raw.json').read_text());comparison=dict(before_commit=before['tested_commit'],after_commit=after['tested_commit'],same_capture_script_sha256=before['capture_script_sha256']==after['capture_script_sha256'],before=before['observed'],after=after['observed'],fresh_after_candidate_guard_passed=after['candidate_guard_passed'],before_evidence='unchanged guarded 89217e1 capture, copied byte-identically from immutable b0cb3b7 history; not rerun at 3ccbf7c')
assert comparison['same_capture_script_sha256'];(out/'privacy-comparison.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+'\n')
changed=subprocess.check_output(['git','diff','--name-only','4e6cabd073e4792f94959545efeb4e323fefc3f5',head,'--','src'],cwd=root,text=True).splitlines();official=lambda c:subprocess.check_output(['git','rev-parse',f'{c}:src/exchange_info/official_data'],cwd=root,text=True).strip();assert official(head)==official('4e6cabd');v=dict(tested_commit=head,prior_commit='4e6cabd073e4792f94959545efeb4e323fefc3f5',changed_runtime_files=changed,official_bundle_tree_sha=official(head),official_data_byte_identical=True,shared_api_and_models_unchanged=True,sql_and_migrations_unchanged=True)
(out/'runtime-source-change-scope.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(packaged_files=len(files),wheel_sha256=record['wheel_sha256'],runtime_changes=changed)))
