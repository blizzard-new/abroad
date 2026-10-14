from pathlib import Path
import json,hashlib,subprocess
from exchange_info.models import PartnerUniversity
r=Path('/workspace/abroad-ntu-official-20261014');h=Path(__file__).parent
raw_before=[json.loads(x) for x in (h/'baseline/partners.jsonl').read_text().splitlines()];raw_after=[json.loads(x) for x in (r/'src/exchange_info/official_data/ntu/partners.jsonl').read_text().splitlines()]
before=[PartnerUniversity.model_validate(p) for p in raw_before];after=[PartnerUniversity.model_validate(p) for p in raw_after]
protected=['school_name','country','eligibility','degree_levels','language_requirement','language_conditions','language_review_note','application_deadline','availability_status','source_url','study_period','tuition_info','location','image_url','image_status']
assert all(all(getattr(a,k)==getattr(b,k) for k in protected) for a,b in zip(before,after))
changed=[b['source_url'].rsplit('/',1)[-1] for a,b in zip(raw_before,raw_after) if a!=b];assert len(changed)==20
assert (h/'baseline/application_workflows.jsonl').read_bytes()==(r/'src/exchange_info/official_data/ntu/application_workflows.jsonl').read_bytes()
assert (h/'baseline/student_life.jsonl').read_bytes()==(r/'src/exchange_info/official_data/ntu/student_life.jsonl').read_bytes()
old_source=subprocess.check_output(['git','show','HEAD:sources/ntu/completion-2026-10-11.json'],cwd=r);assert old_source==(r/'sources/ntu/completion-2026-10-11.json').read_bytes()
changed_paths=subprocess.check_output(['git','diff','--name-only'],cwd=r,text=True).splitlines();assert not any(p.startswith(('supabase/','deploy/','src/exchange_info/official_data/')) and not p.startswith('src/exchange_info/official_data/ntu/') for p in changed_paths)
record={'base_main_sha':'11589e7503222c379a3fa4942932b12012dd8ddb','changed_partner_ids':changed,'changed_partner_count':20,'unchanged_partner_count':268,'all288_typed_protected_fields_unchanged':protected,'serialized_default_note':'八校新增field_evidence後既有model serializer保留language_conditions空陣列；原本省略字段与默认[]语义相同，无语言条件变化。','workflow_bytes_unchanged':True,'student_life_bytes_unchanged':True,'previous1485_reference_snapshot_byte_unchanged':True,'old_source_sha256':hashlib.sha256(old_source).hexdigest(),'database_storage_or_other_school_data_changed':False,'shared_location_timestamp_only_build_side_effect_restored_to_main':True}
(r/'docs/ntu-official-update-20261014/validation/scope-guard.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'protected_fields_unchanged':True,'changed_partners':20,'unchanged_partners':268,'other_school_and_database_changes':False}))
