"""Run the existing full API membership-policy test for CCU and NCU as well."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path.cwd() / 'src'))
sys.path.insert(0, str(Path.cwd() / 'tests'))
from test_tku_community_boundaries import test_school_board_reads_and_writes_require_verified_email_across_all_views

results = []
for board in ('ccu', 'ncu'):
    with TemporaryDirectory(prefix='six-school-extra-api-') as directory:
        test_school_board_reads_and_writes_require_verified_email_across_all_views(Path(directory), board)
    results.append({'board':board, 'status':'passed', 'scope':'Original full guest/pending/member read, write, comment, global-feed and cache-boundary assertions'})
    print(json.dumps(results[-1]), flush=True)
Path('/workspace/integration-evidence/six-extra-school-api-boundaries-result.json').write_text(json.dumps(results, indent=2)+'\n')
