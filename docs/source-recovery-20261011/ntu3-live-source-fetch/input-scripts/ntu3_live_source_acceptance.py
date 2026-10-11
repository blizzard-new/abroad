"""Normal public GETs only. No fixture bodies or request interception."""
from datetime import datetime, timezone
import json
from pathlib import Path
from exchange_info.cgu_catalogue import CguCatalogue, BUNDLED_SNAPSHOT

root=Path('/workspace/recovery-evidence-20261011/ntu3-live-source-acceptance');root.mkdir(exist_ok=True)
store=CguCatalogue(root/'runtime-snapshot.json')
started=datetime.now(timezone.utc).isoformat()
view=store.refresh()
report={'test_kind':'live_public_two_source_fetch','started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),'source':view.source.model_dump(mode='json'),'displayed_rows':len(view.partners),'not_current_cycle_verification':True}
if store.path.exists():
    snapshot=json.loads(store.path.read_text());report['source_receipts']=snapshot['source_receipts']
    seed=json.loads(BUNDLED_SNAPSHOT.read_text());report['same_records_as_dated_seed']=snapshot['records_sha256']==seed['records_sha256']
(root/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
assert view.source.status=='retrieved' and view.source.last_attempt_result=='success'
assert len(view.partners)>0
