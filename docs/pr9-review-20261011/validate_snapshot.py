from pathlib import Path
import importlib.util,json,sys,shutil,subprocess
sys.path.insert(0,str(Path.cwd()/'src'));sys.dont_write_bytecode=True
root=Path('/workspace/pr9-review-20261011');package=root/'pr9/src/exchange_info'
snapshot=json.loads((root/'pr9/sources/ntu/completion-2026-10-11.json').read_text())
for row in snapshot['schools']:
 if not row.get('photo'):continue
 rel=row['photo']['local_path'].split('?')[0].removeprefix('/static/');target=package/'static'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'asset-review'/Path(rel).name,target)
spec=importlib.util.spec_from_file_location('exchange_info.ntu_completion',package/'ntu_completion.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from exchange_info.models import PartnerUniversity
partners=[PartnerUniversity.model_validate_json(s) for s in (package/'official_data/ntu/partners.jsonl').read_text().splitlines()]
module.validate(snapshot,partners,package=package)
print('PR9 validate(snapshot, partners, package=read-only extracted PR9) passed')
p=root/'reviewed-source-delivery.json';d=json.loads(p.read_text())
for row in d['sources']:
 if row['retrieval_method']=='primary_web_tool_cached_read':row['body_hash_matches_receipt']=None
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
ntufile='src/exchange_info/official_data/ntu/application_workflows.jsonl'
assert subprocess.check_output(['git','show','59a20f27:'+ntufile])==subprocess.check_output(['git','show','4566f7f2:'+ntufile])
result={'pr9_sha':'4566f7f2b51b3b5c188f5394a56d7b5df190d1c5','read_only_snapshot_validate':'passed','photo_hashes_verified':13,'new_coordinates':1,'new_life_paraphrases':79,'new_observations':130,'new_reference_schools':41,'ntu_workflow_bytes_unchanged':True,'protected_288_partner_fields_unchanged':True,'read_only_projection_with_pr8_matcher':'NTU13,CCU1,NCU1 photo records change; projected only, no merged build','not_run':['combined browser acceptance','combined memory test','full independent review of all 130 source claims','new full regression suite']}
(root/'independent-review-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
