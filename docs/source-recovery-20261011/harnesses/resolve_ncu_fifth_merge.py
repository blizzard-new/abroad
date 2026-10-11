"""Resolve explicit fifth-input hunks while retaining prior integration semantics."""
from pathlib import Path
import json,re,subprocess
ours='160aeacd15521d63df6a5624bd12821cc5d26cea';theirs='baf98c0df400ef96aa83fb587107eb22513c0b97';base='e25ff02a1ebc69ea126a814d105e88b272539351'
def obj(h,p):return json.loads(subprocess.check_output(['git','show',h+':'+p]))
def write(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
source='sources/ncu/2026-10-11/'
p=source+'campus-locations.json';a=obj(ours,p);b=obj(theirs,p);key=lambda x:(x['school_name'],x['country']);new={key(x):x for x in b['locations']};retained=[x for x in a['locations'] if key(x) not in new];assert len(retained)==10 and all(x['geocode_status']=='needs_review' for x in retained)
b['locations']+=retained;assert len(b['locations'])==199 and sum(x['geocode_status']=='verified' for x in b['locations'])==188
write(p,b)
p=source+'document-conditions.json';a=obj(ours,p);b=obj(theirs,p);old=obj(base,p);key=lambda x:(x['school_name'],x['rule_id'],x['requirement_name']);am={key(x):x for x in a};bm={key(x):x for x in b};om={key(x):x for x in old}
for k in am.keys()&bm.keys():
 if am[k]!=bm[k]:
  assert k in om
  if bm[k]==om[k]:bm[k]=am[k]
  else:assert am[k]==om[k],k
for k in am.keys()-bm.keys():assert k not in om;bm[k]=am[k]
write(p,list(bm.values()))
p=source+'reviewed-host-records.json';r=json.loads(Path(p).read_text());assert r['ncu-081']==obj(ours,p)['ncu-081'];old='首學期約五月全額';new='首學期約五個月全額';assert old in r['ncu-138']['fields']['housing']['points'][2];r['ncu-138']['fields']['housing']['points'][2]=r['ncu-138']['fields']['housing']['points'][2].replace(old,new);write(p,r)
pattern=re.compile(r'<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>>[^\n]+\n',re.S)
p=Path('src/exchange_info/ncu_completion.py');s=p.read_text();s=pattern.sub(lambda m:m.group(2),s);s=s.replace('    holds = set()\n','');start=s.index('        if row.get("allow_shared_fallback") is False:');end=s.index('\n\n\ndef campus_location',start);s=s[:start]+'    return rows'+s[end:];p.write_text(s)
p=Path('src/exchange_info/static/app.js');s=p.read_text();assert len(pattern.findall(s))==1;s=pattern.sub(lambda m:m.group(1).replace('function renderSchoolImageCredit(item) {','function renderSchoolImageCredit(item, includeNote = true) {'),s);p.write_text(s)
for filename in ('src/exchange_info/static/index.html','tests/e2e/test_ncu_resume_assets.py'):
 p=Path(filename);p.write_text(pattern.sub(lambda m:m.group(1),p.read_text()))
p=Path('tests/test_ncu_location_precedence.py');s=p.read_text().replace('import exchange_info.ncu_completion as completion','import exchange_info.ncu_completion as completion\nimport exchange_info.university_locations as locations');s=s.replace("    (tmp_path/'processed').mkdir()\n    (tmp_path/'processed/university_locations.jsonl').write_text(fallback.model_dump_json()+'\\n')","    shared_path=tmp_path/'shared-catalog.jsonl'\n    shared_path.write_text(fallback.model_dump_json()+'\\n')\n    monkeypatch.setattr(locations,'LOCATION_CATALOG',shared_path)");p.write_text(s)
p=Path('tests/test_ncu_location_holds.py');s=p.read_text().replace('import pytest','import pytest\nimport exchange_info.ncu_completion as completion');s=s.replace('def test_hiroshima_explicit_campus_hold_precedes_verified_shared_fallback(tmp_path):','def test_hiroshima_explicit_campus_hold_precedes_verified_shared_fallback(tmp_path, monkeypatch):\n    source=json.loads(completion.LOCATIONS.read_text())\n    row=next(r for r in source["locations"] if "Hiroshima" in r["school_name"])\n    row.update(geocode_status="needs_review", latitude=None, longitude=None, note="校區待審測試")\n    scoped=tmp_path/"scoped-review.json"\n    scoped.write_text(json.dumps(source))\n    monkeypatch.setattr(completion,"LOCATIONS",scoped)');s=s.replace('    ("Chuo", 35.708143, 139.748968, "Korakuen"),','    ("Hiroshima", 34.4022006, 132.713964, "Higashi"),\n    ("Chuo", 35.708143, 139.748968, "Korakuen"),');p.write_text(s)
# New browser writers must keep output outside the candidate, preserving clean-SHA acceptance.
for fn in ('test_ncu_fifth_photos.py','test_ncu_ktu_meiji_resume.py'):
 p=Path('tests/e2e')/fn;s=p.read_text();s=s.replace('from pathlib import Path','from pathlib import Path\nimport os');s=re.sub(r"OUTPUT\s*=\s*Path\([^\n]+",f"OUTPUT = Path(os.environ.get('NCU_RESUME_BROWSER_OUTPUT', '/tmp/ncu-next-browser'))",s);p.write_text(s)
print('Resolved source union, candidate-first lookup, scoped fixture, attribution and external screenshot paths; derived rebuild next.')
