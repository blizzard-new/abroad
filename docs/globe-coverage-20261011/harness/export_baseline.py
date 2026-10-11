import json
import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient
sys.path.insert(0,'/workspace/globe-baseline-59a20f2/src')
from exchange_info.api import create_app
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES

out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
with TestClient(create_app(Path(os.environ['EXCHANGE_INFO_DATA_DIR']))) as client:
    response=client.get('/universities');response.raise_for_status()
    (out/'universities.json').write_text(json.dumps(response.json(),ensure_ascii=False,indent=2)+'\n')
    for university in SUPPORTED_UNIVERSITIES:
        response=client.get('/student-dashboard',params={'school':university.school_name});response.raise_for_status()
        (out/f'{university.id}-dashboard.json').write_text(json.dumps(response.json(),ensure_ascii=False,indent=2)+'\n')
        print(university.id,len(response.json()['partner_universities']),flush=True)
