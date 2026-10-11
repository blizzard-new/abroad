from pathlib import Path
import hashlib,json,subprocess,os
root=Path('/workspace/abroad-ntu-completion-20261011');base=Path('/workspace/abroad-ntu-baseline-20261011');docs=Path('/workspace/abroad-ntu-completion-20261011/docs/ntu-completion-20261011/stage8/validation');docs.mkdir(exist_ok=True)
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
paths=[p for p in (root/'src/exchange_info/official_data/ntu').iterdir() if p.is_file()]+[root/'src/exchange_info/static/assets/school-images.json',root/'src/exchange_info/official_data/university_locations.jsonl']
before={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
env=os.environ.copy();env['PYTHONPATH']='src'
logs=[]
for script in ['scripts/build_ntu_catalog.py','scripts/build_ntu_destination_enrichment.py']:
 r=subprocess.run(['/workspace/abroad/.venv/bin/python',script],cwd=root,env=env,capture_output=True,text=True);logs.append({'script':script,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr});assert r.returncode==0
replayed={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert before==replayed,'Full replay changed materialized bytes'
old=rows(base/'src/exchange_info/official_data/ntu/partners.jsonl');new=rows(root/'src/exchange_info/official_data/ntu/partners.jsonl');protected=['eligibility','quota','application_deadline','availability_status','source_url','country','school_name']
for a,b in zip(old,new):assert all(a[k]==b[k] for k in protected)
unchanged_homes=[]
for home in (base/'src/exchange_info/official_data').iterdir():
 if home.is_dir() and home.name!='ntu':
  files=[p for p in home.rglob('*') if p.is_file()]
  for p in files:assert p.read_bytes()==(root/p.relative_to(base)).read_bytes()
  unchanged_homes.append({'home':home.name,'files':len(files)})
wf='src/exchange_info/official_data/ntu/application_workflows.jsonl';assert (base/wf).read_bytes()==(root/wf).read_bytes()
imagepath='src/exchange_info/static/assets/school-images.json';oldimages={(r['school_name'],r.get('country')):r for r in json.loads((base/imagepath).read_text())['schools']};newimages={(r['school_name'],r.get('country')):r for r in json.loads((root/imagepath).read_text())['schools']}
imagechanges=[key for key in oldimages.keys()|newimages.keys() if oldimages.get(key)!=newimages.get(key)]
snapshot=json.loads((root/'sources/ntu/completion-2026-10-11.json').read_text());expected={(s['school_name'],s['country']) for s in snapshot['schools'] if s.get('photo')};assert set(imagechanges)==expected
locpath='src/exchange_info/official_data/university_locations.jsonl';oldloc={(r['school_name'],r.get('country')):r for r in rows(base/locpath)};newloc={(r['school_name'],r.get('country')):r for r in rows(root/locpath)};locchanges=[key for key in oldloc.keys()|newloc.keys() if oldloc.get(key)!=newloc.get(key)];assert set(locchanges)=={(s['school_name'],s['country']) for s in snapshot['schools'] if s.get('location')}
receipt={'base_main_sha':snapshot['base_main_sha'],'full_build_replay_byte_idempotent':True,'replayed_files':before,'build_results':logs,'partner_protected_fields':protected,'all_288_protected_partner_fields_identical':True,'ntu_workflows_byte_identical':True,'other_home_catalogs_byte_identical':unchanged_homes,'global_photo_changes':imagechanges,'global_location_changes':locchanges,'shared_app_js_byte_identical':(base/'src/exchange_info/static/app.js').read_bytes()==(root/'src/exchange_info/static/app.js').read_bytes(),'deploy_performed':False}
(docs/'scope-and-rebuild.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['full_build_replay_byte_idempotent','all_288_protected_partner_fields_identical','ntu_workflows_byte_identical','global_photo_changes','global_location_changes','shared_app_js_byte_identical']},ensure_ascii=False))
