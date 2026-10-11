from pathlib import Path
import json,hashlib,re,datetime
from research_curator import Curator,ROOT
R=Path('/workspace/abroad-ntu-completion-20261011');S=R/'sources/ntu';D=R/'docs/ntu-completion-20261011/stage8'
read=lambda p:json.loads(p.read_text());write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();norm=lambda t:re.sub(r'\s+',' ',t).strip()
base=ROOT/'parallel-base-747.json';snap=read(base);school={s['portal_id']:s for s in snap['schools']};c=Curator();manual={(x['portal_id'],x['field']):x for x in read(ROOT/'parallel-base-semantic.json')};ledger={(x['portal_id'],x['field'],x['source_id'],x['body_sha256']):x for x in read(ROOT/'parallel-base-ledger.json')};originals=read(ROOT/'prior-700.json');oldids={o['observation_id'] for s in originals['schools'] for o in s['observations']};ids={o['observation_id'] for s in school.values() for o in s['observations']};assign=read(ROOT/'parallel-assignments.json');bundle_receipts=[];completed=[];delta=[]
allowed={'eligibility','language','documents','deadlines','calendar','housing','cost','courses','insurance_visa'};periods={'target_year_explicit','older_year_reference','undated_public_reference','version_conflict','explicitly_pending_announcement'}
for worker,pids in assign.items():
 p=ROOT/'workers'/worker/'review-bundle.json'
 if not p.exists():continue
 b=read(p);assert b['base_source_sha256']==sha(base) and b['assigned_school_ids']==pids and not b['shared_runtime_written'] and not b['merge_or_deploy'];done=set(b['completed_school_ids']);assert done<=set(pids);completed+=list(done);new=[]
 for o in b['new_observations']:
  pid=o['portal_id'];assert pid in pids
  if pid not in done:continue
  assert o['field'] in allowed and not o['selection_rule_confirmed'] and o['applicability_status'] in periods,(worker,pid,o)
  sid=o['source_id'];d=c.read_source(sid);q=o['original_quote'];assert norm(q) in norm(d['text']),(worker,pid,sid,q);assert d['sha256']==o['raw_body_sha256']
  if re.search(r'[a-zA-Z]',q):assert len(q.split())<=25,(worker,pid,'quote too long',q)
  if d.get('document_type')=='pdf':
   assert isinstance(o.get('pdf_page'),int),(worker,pid,sid,'page missing')
   if d.get('pages'):text=next(x['text'] for x in d['pages'] if x['page']==o['pdf_page'])
   else:
    from pypdf import PdfReader
    text=PdfReader(d['_folder']/(sid+'.pdf')).pages[o['pdf_page']-1].extract_text() or ''
   assert norm(q) in norm(text),(worker,pid,sid,'page mismatch')
  r=b['public_source_reviews'][o['quote_source_id']];assert r['sha256']==d['sha256'] and norm(r['original_quote']) in norm(d['text'])
  prior=snap['public_source_reviews'].get(o['quote_source_id'])
  if prior:assert prior['sha256']==r['sha256'],(worker,pid,sid,'source version would overwrite')
  else:snap['public_source_reviews'][o['quote_source_id']]=r
  if o['observation_id'] in ids:continue
  school[pid]['observations'].append({k:v for k,v in o.items() if k not in ['portal_id','school_name']});ids.add(o['observation_id']);new.append(o);delta.append(o)
 for pid,life in b['new_life_evidence'].items():
  assert pid in pids
  if pid in done:
   for entry in life:
    if entry not in school[pid]['life_evidence']:school[pid]['life_evidence'].append(entry)
 for x in b['full_body_reviews']:
  assert x['portal_id'] in pids
  if x['portal_id'] in done:
   d=c.read_source(x['source_id']);assert x['body_sha256']==d['sha256'] and x['text_chars']==len(d['text'])
   key=(x['portal_id'],x['field'],x['source_id'],x['body_sha256'])
   if key not in ledger:ledger[key]=x
 for x in b['semantic_decisions']:
  if x['portal_id'] not in done:continue
  key=x['portal_id'],x['field'];prior=manual.get(key)
  if prior:
   x['prior_review_outcome']=prior['outcome'];x['prior_review_note_zh']=prior['note_zh']
   x['sources']=list({(z['source_id'],z['sha256']):z for z in prior['sources']+x['sources']}.values())
  manual[key]=x
 bundle_receipts.append({'worker':worker,'bundle_sha256':sha(p),'assigned_school_ids':pids,'completed_school_ids':sorted(done),'new_observations_integrated':len(new)})
assert len(completed)==len(set(completed))
all_delta=[{'portal_id':s['portal_id'],'school_name':s['school_name'],**o} for s in snap['schools'] for o in s['observations'] if o['observation_id'] not in oldids]
count=sum(len(s['observations']) for s in snap['schools']);snap['reviewed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();snap['scope']=f'All288 NTU partners; {count} scoped reviewed public-reference observations prepared for Draft PR9 only; no promotion to formal host/home selection rule; unmerged/undeployed.';snap['integration_stage']={'stage':'stage8_original_priority_source_fitness','previous_source_sha256':sha(ROOT/'prior-700.json'),'new_observations':len(all_delta),'candidate_reference_only':True,'formal_selection_rules_promoted':False,'merged_or_deployed':False}
write(S/'completion-2026-10-11.json',snap);write(S/'semantic-review-current-2026-10-11.json',list(manual.values()));write(ROOT/'full-body-field-review-ledger.json',list(ledger.values()));write(D/'本批新增參考增量.json',all_delta);write(D/'獨立批次整合收據.json',{'root_base_source_sha256':sha(base),'previous_runtime_count':700,'new_count':count,'root_new_references':47,'worker_new_references':len(delta),'completed_worker_schools':len(completed),'batches':bundle_receipts,'all_new_quotes_raw_hash_and_pdf_pages_verified':True,'current_cycle_full_fields_promoted':0,'merged_or_deployed':False})
print(json.dumps({'count':count,'delta':len(all_delta),'worker_complete':len(completed),'ledger':len(ledger),'manual':len(manual),'source_quotes':len(snap['public_source_reviews'])},ensure_ascii=False))
