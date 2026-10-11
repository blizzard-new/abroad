"""Reconcile fixed NCU source hunks and retain prior candidate corrections."""
from pathlib import Path
import subprocess,json,re
ours='e16381cf34b365ba8eb9cf5265ab2d9ce9ed1c26';theirs='a2df55b16f72455f7154d7afff44934fc8dbf99d';base='baf98c0df400ef96aa83fb587107eb22513c0b97'
def blob(h,p):return subprocess.check_output(['git','show',h+':'+p])
def obj(h,p):return json.loads(blob(h,p))
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
src='sources/ncu/2026-10-11/';report={'ours':ours,'theirs':theirs,'base':base}
p=src+'campus-locations.json';a=obj(ours,p);b=obj(theirs,p);bm={(x['school_name'],x['country']):x for x in b['locations']}
holds=[x for x in a['locations'] if x['geocode_status']=='needs_review'];assert len(b['locations'])==214
assert all(bm[(x['school_name'],x['country'])]['geocode_status']=='verified' for x in holds)
write(p,b);report['old_holds_replaced_by_independently_reviewed_named_points']=[x['school_name'] for x in holds]
p=src+'document-conditions.json';a=obj(ours,p);b=obj(theirs,p);o=obj(base,p);key=lambda x:(x['school_name'],x['rule_id'],x['requirement_name']);am={key(x):x for x in a};bm={key(x):x for x in b};om={key(x):x for x in o}
for k in am.keys()&bm.keys():
 if am[k]!=bm[k]:
  assert k in om
  if bm[k]==om[k]:bm[k]=am[k]
  else:assert am[k]==om[k],k
for k in am.keys()-bm.keys():assert k not in om;bm[k]=am[k]
write(p,list(bm.values()));report['conditions_union_count']=len(bm)
p=src+'reviewed-host-records.json';a=obj(ours,p);b=obj(theirs,p);o=obj(base,p)
changed=[k for k in a if a[k]!=o.get(k)];assert changed==['ncu-081','ncu-138'],changed
for k in ('ncu-081',):
 assert b[k]['host_documents']==o[k]['host_documents']
 b[k]['host_documents']=a[k]['host_documents']
 b[k]['source_ids']=list(dict.fromkeys(b[k]['source_ids']+a[k]['source_ids']))
 for f,old in a[k]['fields'].items():
  if f not in b[k]['fields']:b[k]['fields'][f]=old;continue
  new=b[k]['fields'][f]
  for fld in ['points','sources']:
   for v in old[fld]:
    if v not in new[fld]:new[fld].append(v)
  if old.get('unresolved') and not new.get('unresolved'):new['unresolved']=old['unresolved']
 for f,old in a[k]['fields'].items():
  assert all(v in b[k]['fields'][f]['points'] for v in old['points'])
text=json.dumps(b['ncu-138'],ensure_ascii=False);assert '首學期約五月全額' in text
b['ncu-138']=json.loads(text.replace('首學期約五月全額','首學期約五個月全額'));assert b['ncu-138']==a['ncu-138']
write(p,b);report['turku_prior_points_and_sources_all_retained']=True;report['meiji_five_months_correction_retained']=True
# Data conflicts below are regenerated from reconciled sources.
for p in subprocess.check_output(['git','diff','--name-only','--diff-filter=U'],text=True).splitlines():
 if p.startswith('src/exchange_info/official_data/ncu/') or p=='docs/data/ncu-completion-20261011/exchange-field-inventory.json.gz':Path(p).write_bytes(blob(theirs,p))
p=Path('tests/e2e/test_ncu_resume_assets.py');s=p.read_text();pat=re.compile(r'<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>>[^\n]+\n',re.S);assert len(pat.findall(s))==1;p.write_text(pat.sub(lambda m:m.group(1),s))
# Newly verified live data must not invalidate the generic missing-data fallback contract.
p=Path('tests/test_ncu_location_holds.py');s=p.read_text();s=s.replace('def test_missing_primary_coordinates_do_not_ban_an_independent_verified_source():','def test_missing_primary_coordinates_do_not_ban_an_independent_verified_source(tmp_path, monkeypatch):\n    source=json.loads(completion.LOCATIONS.read_text())\n    source["locations"]=[r for r in source["locations"] if "Bingöl" not in r["school_name"]]\n    scoped=tmp_path/"missing-primary.json"\n    scoped.write_text(json.dumps(source))\n    monkeypatch.setattr(completion,"LOCATIONS",scoped)');p.write_text(s)
# All screenshot artifacts go outside the candidate, preserving a clean tested SHA.
for p in Path('tests/e2e').glob('test_ncu_*'):
 s=p.read_text()
 if re.search(r"OUTPUT\s*=\s*Path\(['\"]docs/",s):
  if 'import os' not in s:s=s.replace('from pathlib import Path','from pathlib import Path\nimport os')
  s=re.sub(r"OUTPUT\s*=\s*Path\([^\n]+", "OUTPUT = Path(os.environ.get('NCU_RESUME_BROWSER_OUTPUT', '/tmp/ncu-next-browser'))",s);p.write_text(s)
Path('/workspace/recovery-evidence-20261011/ncu-eleventh-merge-resolution.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
