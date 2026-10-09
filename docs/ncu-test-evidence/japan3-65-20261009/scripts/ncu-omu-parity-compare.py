import json
from collections import Counter
from pathlib import Path
from exchange_info import storage
from exchange_info.models import UniversityApplicationWorkflow
names={'長庚大學','國立臺北大學','國立臺灣大學'}
baseline=[UniversityApplicationWorkflow.model_validate(w).model_dump(mode='json') for w in json.loads(Path('/tmp/ncu-omu-main-workflows.json').read_text())]
current=[w.model_dump(mode='json') for w in storage.load_bundled_application_workflows() if w.home_university in names]
serialize=lambda w:json.dumps(w,ensure_ascii=False,sort_keys=True,separators=(',',':'))
a=Counter(map(serialize,baseline));b=Counter(map(serialize,current));assert a==b,(sum((a-b).values()),sum((b-a).values()))
report=dict(main='f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59',compared_count=len(current),semantic_differences=0,method='untouched main runtime export revalidated with identical current schema; serialized values compared as a multiset including duplicate workflows',counts=dict(Counter(w['home_university'] for w in current)))
Path('/tmp/ncu-omu-cross-parity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
