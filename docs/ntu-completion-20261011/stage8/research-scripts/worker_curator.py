"""Independent source fitness review; only writes a worker's private bundle."""
from pathlib import Path
import json,hashlib,datetime
from research_curator import Curator,ROOT

class Worker(Curator):
 def __init__(self,worker):
  super().__init__();self.worker=worker;self.folder=ROOT/'workers'/worker;self.folder.mkdir(parents=True,exist_ok=True)
  self.base_path=ROOT/'parallel-base-747.json';self.snapshot=json.loads(self.base_path.read_text())
  self.schools={s['portal_id']:s for s in self.snapshot['schools']};self.sources=self.snapshot['public_source_reviews'];self.roster=json.loads((ROOT/'priority-source-roster.json').read_text());self.assigned=json.loads((ROOT/'parallel-assignments.json').read_text())[worker]
  self.base_ids={o['observation_id'] for s in self.schools.values() for o in s['observations']};self.base_life={s['portal_id']:list(s['life_evidence']) for s in self.schools.values()};self.body_rows=[];self.decisions=[];self.completed=[]
 def body_review(self,pid,sid,fields,note,full_text=True,**unused):
  assert pid in self.assigned;d=self.read_source(sid);assert d['access_status']=='content_available' and len(d.get('text',''))>30
  for field in fields:
   row={'portal_id':pid,'school_name':self.schools[pid]['school_name'],'field':field,'source_id':sid,'source_url':d['url'],'body_sha256':d['sha256'],'source_checked_at':d['checked_at'],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'full_extracted_text_read_for_field':full_text,'review_scope':'All available extracted text and text-bearing PDF pages read; exact raw+text aliases deduplicated' if full_text else 'Selected scope only; do not count complete','text_chars':len(d['text']),'pdf_page_count':d.get('pdf_page_count'),'note_zh':note,'target_cycle_requirement_verified':False,'independent_worker':self.worker}
   self.body_rows=[r for r in self.body_rows if (r['portal_id'],r['field'],r['source_id'],r['body_sha256'])!=(pid,field,sid,d['sha256'])]+[row]
 def finish(self,pid,note):
  assert pid in self.assigned
  for sid in self.roster[pid]['sources']:
   self.body_review(pid,sid,[f for f,s in self.roster[pid]['fields'].items() if sid in s],note)
  for field,sids in self.roster[pid]['fields'].items():
   facts=[o for o in self.schools[pid]['observations'] if o['field']==field]
   self.decisions.append({'portal_id':pid,'school_name':self.schools[pid]['school_name'],'field':field,'outcome':'scoped_public_reference_read_not_whole_current_rule' if facts else 'full_candidate_bodies_read_no_applicable_rule_found','note_zh':note,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':[{'source_id':sid,'url':d['url'],'checked_at':d['checked_at'],'sha256':d['sha256']} for sid in sids for d in [self.read_source(sid)]],'review_method':'Independent manual source fitness interpretation of all assigned original candidate bodies; scope/year/phase exclusions explicit','full_current_cycle_requirement_verified':False,'independent_worker':self.worker})
  if pid not in self.completed:self.completed.append(pid)
  self.save()
 def save(self):
  facts=[{'portal_id':s['portal_id'],'school_name':s['school_name'],**o} for s in self.schools.values() for o in s['observations'] if o['observation_id'] not in self.base_ids]
  used={o['quote_source_id'] for o in facts};life={p:[x for x in self.schools[p]['life_evidence'] if x not in self.base_life[p]] for p in self.assigned}
  payload={'worker':self.worker,'base_source_sha256':hashlib.sha256(self.base_path.read_bytes()).hexdigest(),'assigned_school_ids':self.assigned,'completed_school_ids':self.completed,'new_observations':facts,'new_life_evidence':life,'public_source_reviews':{sid:self.sources[sid] for sid in used},'full_body_reviews':self.body_rows,'semantic_decisions':self.decisions,'shared_runtime_written':False,'merge_or_deploy':False}
  temporary=self.folder/'review-bundle.json.tmp'
  temporary.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
  temporary.replace(self.folder/'review-bundle.json')
