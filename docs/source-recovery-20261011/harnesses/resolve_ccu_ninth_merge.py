from pathlib import Path
import subprocess,json,hashlib
app=Path('/workspace/abroad-globe-20261011');raw=Path('/workspace/recovery-evidence-20261011')
def git(*a):return subprocess.check_output(['git',*a],cwd=app)
head=git('rev-parse','HEAD').decode().strip();incoming=git('rev-parse','MERGE_HEAD').decode().strip();base=git('merge-base','HEAD','MERGE_HEAD').decode().strip()
assert head=='dbc4afd64b4116e199c218d0d22e4223c9ff2db1' and incoming=='52ed6370c63f053da445a9aff6eb9e2a3d2ad6c8'
assert not git('diff','--name-only','--diff-filter=U').strip()
fixes=[('11項Yes/No/Remarks','10項Yes/No/Remarks')]+[(x['original'],x['replacement']) for x in json.loads((raw/'ccu-eighth-independent-semantic-review.json').read_text())['integration_clarifications_required']]
def normalized(b):
 for a,c in fixes:b=b.replace(a.encode(),c.encode())
 return b
ours=set(git('diff','--name-only',base,'HEAD').decode().splitlines());theirs=set(git('diff','--name-only',base,'MERGE_HEAD').decode().splitlines());overlap=sorted(ours&theirs)
assert len(overlap)==5
for p in overlap:
 assert git('show','HEAD:'+p)==normalized(git('show',base+':'+p)),p
 assert (app/p).read_bytes()==normalized(git('show',incoming+':'+p)),p
bundle=app/'src/exchange_info/official_data/ccu';bp=bundle/'completion-ninth-baseline.json';data=json.loads(bp.read_text());olddata=json.loads(git('show',base+':'+str((bundle/'completion-reviewed-fields.json').relative_to(app))))['schools'];actual=json.loads(git('show','HEAD:'+str((bundle/'completion-reviewed-fields.json').relative_to(app))))['schools'];oldby={r['ccu_page']:r for r in olddata};actualby={r['ccu_page']:r for r in actual}
def fd(f):return hashlib.sha256(json.dumps({k:f[k] for k in ['value','status','evidence']},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
updates=[]
for row in data['prior_fields']:
 for key,field in row['host_fields'].items():
  before=oldby[row['ccu_page']]['host_fields'][key];after=actualby[row['ccu_page']]['host_fields'][key]
  assert field['field_digest']==fd(before)
  assert before['status']==after['status']==field['status']
  if before!=after:
   assert normalized(json.dumps(before,ensure_ascii=False).encode())==json.dumps(after,ensure_ascii=False).encode()
   updates.append({'page':row['ccu_page'],'field':key,'previous_digest':field['field_digest'],'integrated_digest':fd(after)})
   field['field_digest']=fd(after)
   if 'evidence' in field:assert field['evidence']==after['evidence']
assert len(updates)==3
original=git('show',incoming+':'+str(bp.relative_to(app)));data['upstream_prior_commit']=data['prior_commit'];data['upstream_baseline_sha256']=hashlib.sha256(original).hexdigest();data['prior_commit']=head;data['integration_baseline_note']='Bind comparison to the actual predecessor. Preserve prior medical10-items and Oneonta optional transfer housing / up-to16-day insurance clarifications; no additional ninth research claimed.'
bp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(raw/'ccu-ninth-merge-resolution.json').write_text(json.dumps({'base':base,'predecessor':head,'incoming':incoming,'no_git_conflicts':True,'five_full_overlap_files_independently_equal_to_incoming_plus_prior_three_clarifications':overlap,'baseline_digest_updates':updates,'upstream_baseline_sha256':data['upstream_baseline_sha256']},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'overlap_files':len(overlap),'prior_field_digest_updates':updates},ensure_ascii=False))
