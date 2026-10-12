from pathlib import Path
import json,hashlib,re,datetime
from field_worker import Worker,OUTCOMES,H
R=Path('/workspace/abroad-ntu-completion-20261011');S=R/'sources/ntu';D=R/'docs/ntu-completion-20261011/stage9';D.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text());write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();norm=lambda x:re.sub(r'\s+',' ',x).strip()
base=H/'base-1373.json';snap=read(base);schools={s['portal_id']:s for s in snap['schools']};c=Worker('root');manual={(r['portal_id'],r['field']):r for r in read(H/'base-semantic625.json')};oldledger=read(H/'base-ledger2229.json');ledger={(r['portal_id'],r['field'],r['source_id'],r['body_sha256']):r for r in oldledger};oldids={o['observation_id'] for s in schools.values() for o in s['observations']};fixed=read(H/'fixed429-field-roster.json');roster={(r['portal_id'],r['field']):r for r in fixed};done={};delta=[];receipts=[];newread=[]
for worker in ['a1','a2','a3','a4','a5','a6','root']:
 p=H/'workers'/worker/'field-review-bundle.json';b=read(p);assigned={tuple(k) for k in b['assigned_field_keys']};completed={tuple(k) for k in b['completed_field_keys']};assert assigned==completed and b['base_source_sha256']==sha(base) and not b['new_fetches'] and not b['shared_files_written'] and not b['merge_or_deploy'],worker
 assert not assigned&done.keys()
 for d in b['field_conclusions']:
  key=d['portal_id'],d['field'];assert key in assigned and d['outcome'] in OUTCOMES and d['bounded_field_conclusion_complete'] and d['full_current_cycle_requirement_verified'] is False
  assert {s['source_id'] for s in d['sources']}==set(roster[key]['readable_candidate_source_ids'])
  for s in d['sources']:
   raw=c.read_source(s['source_id']);assert raw['sha256']==s['sha256'] and raw['url']==s['url'] and raw['checked_at']==s['checked_at'] and len(s['field_fitness_note_zh'])>=12
  if key in manual:d['prior_semantic_decision']=manual[key]
  manual[key]=d;done[key]=d;schools[key[0]].setdefault('field_review_conclusions',[]).append(d)
 for o in b['new_observations']:
  pid=o['portal_id'];assert (pid,o['field']) in assigned and o['observation_id'] not in oldids
  d=c.read_source(o['source_id']);q=o['original_quote'];assert norm(q) in norm(d['text']) and d['sha256']==o['raw_body_sha256'] and len(q.split())<=25
  assert o['selection_rule_confirmed'] is False and o['applicability_status'] in {'target_year_explicit','older_year_reference','undated_public_reference','version_conflict','explicitly_pending_announcement'}
  if d.get('document_type')=='pdf':
   from pypdf import PdfReader
   page=o['pdf_page'];text=next(x['text'] for x in d['pages'] if x['page']==page) if d.get('pages') else PdfReader(d['_folder']/(o['source_id']+'.pdf')).pages[page-1].extract_text() or ''
   assert norm(q) in norm(text),(worker,pid,page,q)
  source=b['public_source_reviews'][o['quote_source_id']];prior=snap['public_source_reviews'].get(o['quote_source_id']);assert not prior or prior['sha256']==source['sha256']
  if not prior:snap['public_source_reviews'][o['quote_source_id']]=source
  schools[pid]['observations'].append({k:v for k,v in o.items() if k not in ['portal_id','school_name']});oldids.add(o['observation_id']);delta.append(o)
 for pid,items in b['new_life_evidence'].items():
  for e in items:
   if e not in schools[pid]['life_evidence']:schools[pid]['life_evidence'].append(e)
 for row in b['full_body_reviews']:
  assert (row['portal_id'],row['field']) in assigned
  raw=c.read_source(row['source_id']);assert raw['sha256']==row['body_sha256'] and len(raw['text'])==row['text_chars']
  key=row['portal_id'],row['field'],row['source_id'],row['body_sha256']
  if key not in ledger:ledger[key]=row;newread.append(row)
 receipts.append({'worker':worker,'bundle_sha256':sha(p),'assigned_fields':len(assigned),'completed_fields':len(completed),'new_observations':len(b['new_observations']),'new_fetches':0})

# The frozen candidate roster contains two raw versions of one UM source ID.
# Both versions receive a reason; never treat an ID as a version substitute.
import zipfile
archivebase=read(H/'base-body-manifest1228.json');archiveindex={(e['source_id'],e['sha256']):e for e in archivebase['entries']}
for extra in read(H/'workers/a5/additional-version-field-notes.json'):
 key=extra['portal_id'],extra['field'];assert key in done and extra['source_id'] in roster[key]['readable_candidate_source_ids']
 entry=archiveindex[extra['source_id'],extra['sha256']]
 with zipfile.ZipFile(S/entry['archive_file']) as z:
  raw=z.read(entry['archive_body_path']);text=z.read('extractions/'+extra['source_id']+'.txt')
 assert hashlib.sha256(raw).hexdigest()==extra['sha256'] and hashlib.sha256(text).hexdigest()==extra['text_sha256']
 assert entry['checked_at']==extra['checked_at'] and entry['url']==extra['url']
 version={k:extra[k] for k in ['source_id','url','checked_at','sha256','field_fitness_note_zh']};version['document_type']='html';version['pdf_page_count']=None
 done[key]['sources'].append(version)
 lr={'portal_id':extra['portal_id'],'school_name':extra['school_name'],'field':extra['field'],'source_id':extra['source_id'],'source_url':extra['url'],'body_sha256':extra['sha256'],'source_checked_at':extra['checked_at'],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'full_extracted_text_read_for_field':extra['full_read'],'review_scope':'Complete old cached source version read; separate from newer same-ID version','text_chars':extra['text_char_count'],'pdf_page_count':None,'note_zh':extra['field_fitness_note_zh'],'target_cycle_requirement_verified':False,'independent_worker':'a5'}
 lk=extra['portal_id'],extra['field'],extra['source_id'],extra['sha256']
 if lk not in ledger:ledger[lk]=lr;newread.append(lr)

assert set(done)==set(roster) and len(done)==429
for d in done.values():
 if d['outcome']=='officially_unannounced':
  obs=[o for o in schools[d['portal_id']]['observations'] if o['field']==d['field']]
  assert any(o['applicability_status']=='explicitly_pending_announcement' for o in obs),d
snap['reviewed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();count=sum(len(s['observations']) for s in schools.values());snap['scope']=f'All288 NTU partners; {count} scoped public-reference observations and429 terminal existing-candidate field conclusions; Draft PR9 only; no complete current-cycle selection verification.'
snap['bounded_field_review']={'frozen_batch':'stage9_fixed429','field_denominator':429,'school_denominator':121,'discovery_expansion':False,'new_fetches':0,'prior_source_sha256':sha(base),'all_fields_concluded':True,'field_roster':[{k:r[k] for k in ['portal_id','field','readable_candidate_source_ids']} for r in fixed]}
snap['integration_stage']={'stage':'stage9_fixed429_field_conclusions','previous_source_sha256':sha(base),'new_observations':len(delta),'candidate_reference_only':True,'formal_selection_rules_promoted':False,'merged_or_deployed':False}
write(S/'completion-2026-10-11.json',snap);write(S/'semantic-review-current-2026-10-11.json',list(manual.values()));write(S/'full-body-review-current-2026-10-11.json',list(ledger.values()));write(D/'本批新增參考增量.json',delta);write(D/'429欄最終結論.json',list(done.values()));write(D/'固定429欄原始集合.json',fixed);write(D/'獨立批次整合收據.json',{'base_source_sha256':sha(base),'prior_observations':1373,'observations':count,'new_observations':len(delta),'field_conclusions':429,'batches':receipts,'prior2229_ledger_unchanged':all(x in ledger.values() for x in oldledger),'body_context_read_only_count':sum(not r['full_extracted_text_read_for_field'] for b in receipts for r in read(H/'workers'/b['worker']/'field-review-bundle.json')['full_body_reviews']),'new_fetches':0,'merge_or_deploy':False});write(H/'new-body-ledger.json',newread)
print(json.dumps({'observations':count,'delta':len(delta),'conclusions':len(done),'manual':len(manual),'ledger':len(ledger),'newledger':len(newread),'source_quotes':len(snap['public_source_reviews'])}))
