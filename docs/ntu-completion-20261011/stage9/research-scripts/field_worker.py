"""Frozen429 field-specific conclusions; no source fetching or shared writes."""
from pathlib import Path
import sys,json,hashlib,datetime,re
H=Path(__file__).parent;sys.path.insert(0,str(H.parent/'stage8'))
from research_curator import Curator
OUTCOMES={'verified_scoped_reference','not_applicable_to_exchange_scope','insufficient_existing_source','version_conflict','officially_unannounced','external_information_required'}
class Worker(Curator):
 def __init__(self,name):
  super().__init__();self.name=name;self.folder=H/'workers'/name;self.assigned=json.loads((self.folder/'assigned-fields.json').read_text());self.rows={(r['portal_id'],r['field']):r for r in self.assigned};self.snapshot=json.loads((H/'base-1373.json').read_text());self.schools={s['portal_id']:s for s in self.snapshot['schools']};self.sources=self.snapshot['public_source_reviews'];self.base_ids={o['observation_id'] for s in self.schools.values() for o in s['observations']};self.base_life={s['portal_id']:list(s['life_evidence']) for s in self.schools.values()};self.decisions={};self.body_rows=[]
 def fact(self,*args,**kwargs):
  pid,sid,field=args[:3];assert (pid,field) in self.rows
  row=self.rows[pid,field];assert sid in row['readable_candidate_source_ids'] or any(o['source_id']==sid for o in self.schools[pid]['observations'] if o['observation_id'] in self.base_ids)
  d=self.read_source(sid);old=self.sources.get(sid)
  assert not old or old['sha256']==d['sha256'],'Do not overwrite another source version'
  return super().fact(*args,**kwargs)
 def finish(self,pid,field,conclusion,note,source_notes,missing_items=None,necessary_links=None,full_read_flags=None):
  assert conclusion in OUTCOMES and (pid,field) in self.rows
  row=self.rows[pid,field];sids=row['readable_candidate_source_ids'];full_read_flags=full_read_flags or {};assert set(source_notes)==set(sids),(pid,field,'Every existing readable candidate needs field-fitness reason')
  sources=[]
  for sid in sids:
   d=self.read_source(sid);assert d.get('access_status')=='content_available' and d.get('sha256')
   sources.append({'source_id':sid,'url':d['url'],'checked_at':d['checked_at'],'sha256':d['sha256'],'document_type':d.get('document_type'),'pdf_page_count':d.get('pdf_page_count'),'field_fitness_note_zh':source_notes[sid]})
   self.body_rows.append({'portal_id':pid,'school_name':self.schools[pid]['school_name'],'field':field,'source_id':sid,'source_url':d['url'],'body_sha256':d['sha256'],'source_checked_at':d['checked_at'],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'full_extracted_text_read_for_field':full_read_flags.get(sid,True),'review_scope':'Fixed429 existing-candidate field-specific interpretation; prior full reads reused or cached body read' if full_read_flags.get(sid,True) else 'Source identity and relevant field context only; no complete-body-reading claim','text_chars':len(d['text']),'pdf_page_count':d.get('pdf_page_count'),'note_zh':source_notes[sid],'target_cycle_requirement_verified':False,'independent_worker':self.name})
  facts=[o for o in self.schools[pid]['observations'] if o['field']==field]
  self.decisions[pid,field]={'portal_id':pid,'school_name':self.schools[pid]['school_name'],'field':field,'outcome':conclusion,'note_zh':note,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':sources,'review_method':'Manual field-specific final interpretation within frozen429 existing candidates; no discovery expansion','full_current_cycle_requirement_verified':False,'bounded_field_conclusion_complete':True,'frozen_batch':'stage9_fixed429','missing_current_cycle_items':missing_items or [],'necessary_public_links_not_fetched':necessary_links or [],'independent_worker':self.name,'scoped_observation_ids':[o['observation_id'] for o in facts]}
  self.save()
 def save(self):
  facts=[{'portal_id':s['portal_id'],'school_name':s['school_name'],**o} for s in self.schools.values() for o in s['observations'] if o['observation_id'] not in self.base_ids];used={o['quote_source_id'] for o in facts};pids={r['portal_id'] for r in self.assigned};life={pid:[e for e in self.schools[pid]['life_evidence'] if e not in self.base_life[pid]] for pid in pids}
  bundle={'worker':self.name,'base_source_sha256':hashlib.sha256((H/'base-1373.json').read_bytes()).hexdigest(),'assigned_field_keys':[list(k) for k in self.rows],'completed_field_keys':[list(k) for k in self.decisions],'field_conclusions':list(self.decisions.values()),'new_observations':facts,'new_life_evidence':life,'public_source_reviews':{sid:self.sources[sid] for sid in used},'full_body_reviews':self.body_rows,'new_fetches':0,'shared_files_written':False,'merge_or_deploy':False}
  p=self.folder/'field-review-bundle.json';tmp=p.with_suffix('.json.tmp');tmp.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
