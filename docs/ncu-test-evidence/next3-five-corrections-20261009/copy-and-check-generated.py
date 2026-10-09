import csv, gzip, io, json, shutil, subprocess
from pathlib import Path
root=Path('/workspace/abroad-ncu');bundle=root/'src/exchange_info/official_data/ncu';generated=Path('/workspace/ncu-p1-five-20261009/generated');baseline='bb4cecd8030946e59bed494509d206c356e5c210'
def old(path):return subprocess.check_output(['git','show',baseline+':'+str(path.relative_to(root))],cwd=root)
def rows(raw,file):return [json.loads(l)for l in raw.splitlines()]if file.endswith('.jsonl')else json.loads(raw)
names={'名古屋外國語大學 Nagoya University of Foreign Studies','熊本大學 Kumamoto University','龍谷大學 Ryukoku University'}
report={'baseline_sha':baseline,'allowed_schools':sorted(names),'files':{}}
for file in ['field-audit.json','partners.jsonl','application_workflows.jsonl','destination_profiles.jsonl']:
 a=rows(old(bundle/file),file);b=rows((generated/file).read_bytes(),file)
 assert len(a)==len(b)==214
 assert [x['school_name']for x in a]==[x['school_name']for x in b]
 changed=[x['school_name']for x,y in zip(a,b)if x!=y];assert set(changed)<=names,(file,changed)
 report['files'][file]={'changed_schools':changed,'unchanged_schools':214-len(changed)}
a=json.loads(gzip.decompress(old(bundle/'source-evidence.json.gz')));b=json.loads(gzip.decompress((generated/'source-evidence.json.gz').read_bytes()));assert len(a)==len(b)==1455
changes=[]
for x,y in zip(a,b):
 assert x['id']==y['id']
 if x!=y:
  assert x['id']=='host-kumamoto-next3-ug-brochure'
  keys=[k for k in set(x)|set(y)if x.get(k)!=y.get(k)]
  assert set(keys)=={'page_transcriptions','visual_review'}
  assert x['pages']==y['pages'] and x['sha256']==y['sha256']
  changes.append({'id':x['id'],'changed_keys':keys,'native_text_and_original_sha_unchanged':True})
report['source_changes']=changes;report['unchanged_sources']=len(a)-len(changes)
for file in ['catalog-completeness.json']:
 assert old(bundle/file)==(generated/file).read_bytes(),file
old_csv=list(csv.DictReader(io.StringIO(old(bundle/'field-coverage.csv').decode())))
new_csv=list(csv.DictReader(io.StringIO((generated/'field-coverage.csv').read_text())))
assert len(old_csv)==len(new_csv)
csv_changed=[y for x,y in zip(old_csv,new_csv)if x!=y]
assert all(x['學校／track']in names for x in csv_changed)
report['field_coverage_csv_changed_rows']=len(csv_changed)
report['coverage_unchanged']=True
for path in generated.iterdir():
 if (bundle/path.name).exists()and(bundle/path.name).read_bytes()==path.read_bytes():continue
 shutil.copy2(path,bundle/path.name)
Path('/workspace/ncu-p1-five-20261009/generated-scope.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
