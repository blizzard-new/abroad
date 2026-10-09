import json
from pathlib import Path
from exchange_info import storage
names={'長庚大學','國立臺北大學','國立臺灣大學'}
rows=[w.model_dump(mode='json') for w in storage.load_bundled_application_workflows() if w.home_university in names]
Path('/tmp/ncu-omu-main-workflows.json').write_text(json.dumps(rows,ensure_ascii=False))
print('main exported workflows',len(rows))
