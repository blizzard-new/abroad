from research_curator import ROOT
import json

def finish(c,pid,note):
 roster=json.loads((ROOT/'priority-source-roster.json').read_text())[pid]
 for sid in roster['sources']:
  fields=[field for field,sids in roster['fields'].items() if sid in sids]
  c.body_review(pid,sid,fields,note)
 for field,sids in roster['fields'].items():
  facts=[o for o in c.schools[pid]['observations'] if o['field']==field]
  outcome='scoped_public_reference_read_not_whole_current_rule' if facts else 'full_candidate_bodies_read_no_applicable_rule_found'
  c.decision(pid,field,sids,outcome,note+'；本欄相關已匯入參考'+str(len(facts))+'則；不等整欄當期核實。')
 c.save();print(pid,'source sets processed; observations',sum(len(s['observations']) for s in c.schools.values()))
