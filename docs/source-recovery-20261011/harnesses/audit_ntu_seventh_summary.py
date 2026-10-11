"""Audit next fixed NTU data and summary without modifying frozen candidate."""
from pathlib import Path
import subprocess,json,re,hashlib
from exchange_info.models import PartnerUniversity
sha='dc9bbcddcf2cd2cf47ef7768e530c6aab6fa4401';base='ed7479073df36deb8fc0393e86fedb102e1cf2b7'
def blob(p,h=sha):return subprocess.check_output(['git','show',h+':'+p])
def obj(p,h=sha):return json.loads(blob(p,h))
normal=lambda t:re.sub(r'\s+',' ',t).strip()
snapshot=obj('sources/ntu/completion-2026-10-11.json');manifest=obj('sources/ntu/reviewed-source-bodies-current-manifest.json')
assert len(snapshot['schools'])==288 and sum(len(s['observations']) for s in snapshot['schools'])==700
entries={(e['source_id'],e['sha256']):e for e in manifest['entries']};assert len(entries)==554 and len(manifest['archive_files'])==19
prior=obj('sources/ntu/reviewed-source-bodies-current-manifest.json',base);assert len(prior['entries'])==345
assert all(entries[(e['source_id'],e['sha256'])]==e for e in prior['entries'])
p='src/exchange_info/official_data/ntu/partners.jsonl';before=[json.loads(x)for x in blob(p,base).splitlines()];after=[json.loads(x)for x in blob(p).splitlines()];assert len(before)==len(after)==288
fields=['school_name','country','quota','eligibility','application_deadline','availability_status','source_url']
assert all({k:a.get(k)for k in fields}=={k:b.get(k)for k in fields}for a,b in zip(before,after))
source=blob('src/exchange_info/ntu_partner_summary.py').decode();ns={'__name__':'exchange_info._next_ntu_summary','__package__':'exchange_info'};exec(compile(source,'fixed-ntu-summary.py','exec'),ns)
by_name={x['school_name']:x for x in after};count=0;visibility=[]
for row in snapshot['schools']:
 partner=PartnerUniversity.model_validate(by_name[row['school_name']]);summary=ns['ntu_partner_summary'](partner);visible=normal('\n\n'.join(summary.application_steps[:10]));size=len(summary.application_steps)
 for o in row['observations']:
  assert o['selection_rule_confirmed'] is False,(row['school_name'],o['observation_id'])
  for k in ['text_zh','scope','source_url']:assert normal(o[k]) in visible,(row['school_name'],o['observation_id'],k)
  count+=1
 visibility.append({'school':row['school_name'],'observations':len(row['observations']),'application_step_count':size,'all_references_in_first_ten':True})
assert count==700
protected=['supabase/migrations','.github/workflows','uv.lock','src/exchange_info/static/app.js','src/exchange_info/static/index.html']
protected += [f'src/exchange_info/official_data/{x}' for x in ['cgu','ntpu','ccu','ncu','tku']]
protected += ['src/exchange_info/official_data/ntu/application_workflows.jsonl']
assert not subprocess.check_output(['git','diff','--name-only',base,sha,'--',*protected]).strip()
a=obj('src/exchange_info/static/assets/school-images.json');b=obj('src/exchange_info/static/assets/school-images.json',base);a.pop('updated_at');b.pop('updated_at');assert a==b
report={'input_sha':sha,'baseline':base,'status':'passed fixed input scope and first-ten summary visibility; archives/manual semantic review pending','partner_rows':288,'all_observations':count,'all_700_text_scope_and_source_visible_in_first_ten':True,'summary_module_sha256':hashlib.sha256(source.encode()).hexdigest(),'prior_345_body_manifest_entries_exactly_preserved':True,'source_body_versions':554,'source_ids':len({sid for sid,_ in entries}),'archive_parts':19,'protected_fields':fields,'protected_paths_unchanged':protected,'photo_catalog_unchanged_except_timestamp':True,'schools':visibility,'not_claimed':'No integrated API/browser or full-source factual acceptance for this input yet.'}
Path('/workspace/recovery-evidence-20261011/ntu-seventh-scope-summary-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='schools'},ensure_ascii=False))
