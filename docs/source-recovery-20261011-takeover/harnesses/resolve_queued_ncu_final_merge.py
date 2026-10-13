"""Preserve reviewed integration corrections while accepting fixed NCU additions."""
from pathlib import Path
import argparse
import json
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--ours', required=True)
p.add_argument('--theirs', required=True)
a = p.parse_args()
base = subprocess.check_output(['git', 'merge-base', a.ours, a.theirs], text=True).strip()
assert base == 'a2df55b16f72455f7154d7afff44934fc8dbf99d', base
raw = Path('/workspace/recovery-evidence-20261011')
summary = json.loads((raw/'integration-final7-full-suite-summary.json').read_text())
assert summary['all_shards_same_clean_fixed_sha'] and summary['all_collected_nodes_accounted_exactly_once']
assert subprocess.check_output(['git','rev-parse','MERGE_HEAD'],text=True).strip() == a.theirs

def blob(sha, path):
    return subprocess.check_output(['git', 'show', sha + ':' + path])

def obj(sha, path):
    return json.loads(blob(sha, path))

def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

prefix = 'sources/ncu/2026-10-11/'
path = prefix + 'reviewed-host-records.json'
old, ours, incoming = (obj(sha, path) for sha in [base, a.ours, a.theirs])
changed = [key for key in ours if ours[key] != old.get(key)]
assert set(changed) == {'ncu-081', 'ncu-138'}, changed
for key in changed:
    assert incoming[key] == old[key], (key, 'new overlapping source edit requires fresh hunk review')
    incoming[key] = ours[key]
# a1d6b7aa also updates seven existing records, independently byte-audited.
# Accept those exact upstream edits only where integration still equals base.
incoming_updates = {key for key in old if incoming[key] != old[key] and key not in changed}
assert incoming_updates == {'ncu-085', 'ncu-086', 'ncu-080', 'ncu-084', 'ncu-048', 'ncu-104', 'ncu-105'}
for key, value in ours.items():
    if key in incoming_updates:
        assert value == old[key], (key, 'overlapping edit needs review')
    else:
        assert incoming[key] == value, key
write(path, incoming)
report = {'base': base, 'ours': a.ours, 'theirs': a.theirs,
          'preserved_existing_host_records': len(ours), 'new_host_records': sorted(set(incoming)-set(ours)),
          'preserved_corrected_rows': changed,
          'audited_upstream_existing_updates': sorted(incoming_updates)}

path = prefix + 'document-conditions.json'
key = lambda row: (row['school_name'], row['rule_id'], row['requirement_name'])
old, ours, incoming = ({key(row): row for row in obj(sha, path)} for sha in [base, a.ours, a.theirs])
for k, row in ours.items():
    if k in incoming and incoming[k] != row:
        assert k in old
        if incoming[k] == old[k]:
            incoming[k] = row
        else:
            assert row == old[k], (k, 'both branches changed one condition')
    elif k not in incoming:
        assert k not in old, (k, 'incoming removed an existing condition')
        incoming[k] = row
assert all(incoming[k] == value for k, value in ours.items())
write(path, list(incoming.values()))
report['conditions_union_count'] = len(incoming)
report['all_existing_condition_records_preserved'] = True

conflicts = subprocess.check_output(['git','diff','--name-only','--diff-filter=U'],text=True).splitlines()
resolved_sources = {prefix+'reviewed-host-records.json', prefix+'document-conditions.json'}
for path in conflicts:
    if path in resolved_sources:
        continue
    if path.startswith('src/exchange_info/official_data/ncu/') or path == 'docs/data/ncu-completion-20261011/exchange-field-inventory.json.gz':
        Path(path).write_bytes(blob(a.theirs,path))
        continue  # Regenerated twice from reconciled sources before commit.
    if path.startswith('tests/e2e/test_ncu_'):
        # Upstream tmp_path/browser output repair was separately compared.
        # The visible unknown label stays '待核實', including both integration
        # corrections and stale incoming literals. Assertions remain present.
        source = blob(a.theirs,path).decode()
        Path(path).write_text(source.replace('本期名額待公告','本期名額待核實'))
        continue
    raise AssertionError(('unreviewed merge conflict',path))

report['conflicted_paths'] = conflicts
report['validation_required'] = 'NCU offline rebuild twice; all existing source row preservation; same-SHA complete gates'
(raw/'queued-ncu-final-merge-resolution.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
