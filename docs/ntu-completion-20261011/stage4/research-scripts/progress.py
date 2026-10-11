from pathlib import Path
import json,datetime
ROOT=Path(__file__).parent
q=json.loads((ROOT/'priority-source-roster.json').read_text())
ledger=json.loads((ROOT/'full-body-field-review-ledger.json').read_text())
done={(r['portal_id'],r['field'],r['source_id']) for r in ledger if r['full_extracted_text_read_for_field']}
original_pairs={(pid,field,sid) for pid,school in q.items() for field,sids in school['fields'].items() for sid in sids}
original_done=done & original_pairs
fields=[]
for pid,school in q.items():
 for field,sids in school['fields'].items():
  missing=[sid for sid in sids if (pid,field,sid) not in done]
  fields.append({'portal_id':pid,'school_name':school['name'],'field':field,
   'original_cached_candidate_body_count':len(sids),'read_count':len(sids)-len(missing),
   'all_original_cached_candidates_read':not missing,'remaining_source_ids':missing,
   'full_current_cycle_requirement_verified':False,'public_followup_links_still_separate':True})
summary={'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'fixed_priority_field_denominator':501,'fixed_priority_school_denominator':117,
 'fixed_priority_unique_body_hash_denominator':890,
 'completed_original_cached_body_sets':sum(f['all_original_cached_candidates_read'] for f in fields),
 'remaining_original_cached_body_sets':sum(not f['all_original_cached_candidates_read'] for f in fields),
 'distinct_original_school_field_body_review_pairs':len(original_done),
 'additional_followup_school_field_body_pairs':len(done-original_pairs),
 'distinct_reviewed_body_hashes':len({r['body_sha256'] for r in ledger if r['full_extracted_text_read_for_field']}),
 'schools_with_completed_original_candidate_sets':len({f['portal_id'] for f in fields if f['all_original_cached_candidates_read']}),
 'current_cycle_fully_verified_fields':0,
 'completion_definition':'Read all original stage3 cached body texts assigned to this school/field; excludes still-unread public links and unverified current-cycle subrequirements.',
 'fields':fields}
(ROOT/'priority-review-progress.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='fields'},ensure_ascii=False))
