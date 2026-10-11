"""Resolve only the verified Sungshin medical count overlap; retain batch 7."""
import json, subprocess
from pathlib import Path

root = Path('/workspace/abroad-globe-20261011')
def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)

old = '11項Yes/No/Remarks'.encode()
new = '10項Yes/No/Remarks'.encode()
paths = git('diff', '--name-only', '--diff-filter=U').decode().splitlines()
assert len(paths) == 6
report = []
for path in paths:
    base, ours, theirs = [git('show', f':{stage}:{path}') for stage in (1, 2, 3)]
    assert ours == base.replace(old, new), path
    assert theirs.count(old) in (1, 2), path
    (root/path).write_bytes(theirs.replace(old, new))
    report.append({'path': path, 'ours_vs_base_only_medical_count': True,
                   'incoming_occurrences_corrected': theirs.count(old)})
    git('add', '--', path)
# The new progress report repeats current and previous field values. Its
# immutable seventh baseline is historical evidence and is left unchanged.
path = root/'src/exchange_info/official_data/ccu/completion-seventh-public-progress.json'
data = path.read_bytes()
assert data.count(old) == 1
path.write_bytes(data.replace(old, new))
git('add', '--', str(path))
assert new in (root/'scripts/review_ccu_sungshin_current.py').read_bytes()
Path('/workspace/recovery-evidence-20261011/ccu-seventh-merge-resolution.json').write_text(
    json.dumps({'input': '258ce9bbb38081792658f9720bdb457a5344b2bb',
                'base_candidate': git('rev-parse', 'HEAD').decode().strip(),
                'resolved': report, 'historical_baseline_preserved': True}, indent=2)+'\n')
