"""Report the fixed-SHA full run without altering the candidate tree."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

root = Path('/workspace/integration-evidence')
all_cases = []
shards = []
for index in range(4):
    directory = root / f'six-final-full-shard-{index}'
    metadata = json.loads((directory / 'metadata.json').read_text())
    output = (directory / 'stdout.log').read_text()
    cases = re.findall(r'WEB_CASE (.*?) (setup|call|teardown) (passed|failed|skipped) ([\d.]+)s', output)
    all_cases.extend(cases)
    shards.append({'shard': index, 'status': metadata['test_result'],
                   'counts': dict(Counter(row[2] for row in cases)),
                   'last_line': output.splitlines()[-1][-160:]})
sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd='/workspace/abroad-six-final', text=True).strip()
status = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd='/workspace/abroad-six-final', text=True).strip()
result = {'timestamp': datetime.now(timezone.utc).isoformat(), 'sha': sha,
          'source_status': status, 'completed_so_far': len(all_cases),
          'counts': dict(Counter(row[2] for row in all_cases)),
          'status': 'running' if any(s['status'] == 'running' for s in shards) else 'finished',
          'shards': shards,
          'failed_nodeids': [row[0] for row in all_cases if row[2] == 'failed']}
(root / 'final-full-progress.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
