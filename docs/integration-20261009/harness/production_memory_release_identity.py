"""Read deployed public static bytes and compare to the accepted checkout."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import requests

commit, output_name = sys.argv[1:3]
base = 'https://uniway-1167.onrender.com'
proof = {'commit': commit, 'started_at': datetime.now(timezone.utc).isoformat(),
         'mode': 'Sequential public GETs only; certificate verification enabled', 'files': []}
index = Path('src/exchange_info/static/index.html')
assert '20261009-stable-icons-1' in index.read_text()
for remote, local in [('/', index),
                      ('/static/app.js?v=20261009-stable-icons-1', Path('src/exchange_info/static/app.js'))]:
    response = requests.get(base + remote, timeout=90)
    response.raise_for_status()
    actual = hashlib.sha256(response.content).hexdigest()
    expected = hashlib.sha256(local.read_bytes()).hexdigest()
    assert actual == expected, (remote, actual, expected)
    proof['files'].append({'url_path': remote, 'status': response.status_code,
                           'bytes': len(response.content), 'sha256': actual, 'candidate_identical': True})
proof.update(status='passed', finished_at=datetime.now(timezone.utc).isoformat())
Path('/workspace/integration-evidence', output_name + '-result.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof))
