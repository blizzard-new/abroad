"""Audit fixed NCU fourth-pass data without moving the active candidate."""
import gzip, hashlib, json, subprocess
from collections import Counter
from pathlib import Path

sha = '358a72e7302476ba8dd19c47c35fc398fc205a47'
previous = '06bfdfa15e9f773533d3f82e1a136faa99f68104'
def blob(path, head=sha):
    return subprocess.check_output(['git', 'show', head + ':' + path])
def obj(path):
    raw = blob(path)
    return json.loads(gzip.decompress(raw) if path.endswith('.gz') else raw)

sources = obj('sources/ncu/2026-10-11/host-web-evidence.json.gz')
by_id = {r['id']: r for r in sources}
assert len(sources) == len(by_id) == 646
status = Counter(r['reading_status'] for r in sources)
assert status['full_native_text_reviewed'] == 45
assert status['full_visual_and_native_reviewed'] == 2
assert sum(v for k, v in status.items() if k != 'not_reviewed') == 237
manual = obj('sources/ncu/2026-10-11/reviewed-host-records.json')
assert len(manual) == 44
for rid, row in manual.items():
    for sid in row['source_ids']:
        assert sid in by_id, (rid, sid)
        assert rid in by_id[sid]['row_ids'], (rid, sid)
for row in sources:
    review = row.get('reading_review')
    if review:
        assert review['source_sha256'] == row['sha256'], row['id']
        assert set(review['pages_reviewed']).issubset({p['page'] for p in row['pages']}), row['id']

path = 'docs/data/ncu-completion-20261011/douglas-public-incoming-browser-capture.json.gz'
raw = gzip.decompress(blob(path))
assert hashlib.sha256(raw).hexdigest() == by_id['ncu-100-p4b-incoming10005']['sha256']
unread = obj('docs/data/ncu-completion-20261011/successful-public-unread-candidates.json.gz')
assert len(unread) == 319
partners = [json.loads(line) for line in blob('src/exchange_info/official_data/ncu/partners.jsonl').splitlines()]
workflows = [json.loads(line) for line in blob('src/exchange_info/official_data/ncu/application_workflows.jsonl').splitlines()]
assert len(partners) == len(workflows) == 214
assert all(r.get('quota') is None and r['availability_status'] == 'agreement_only' for r in partners)
assert all(r['review_status'] == 'pending_review' for r in workflows)
assert all(not s.get('deadline_reminder_eligible', False) for r in workflows for s in r['steps'])
protected = [f'src/exchange_info/official_data/{school}/application_workflows.jsonl' for school in ('cgu','ntpu','ntu')]
protected += ['src/exchange_info/official_data/ncu/campus-assets.json', 'src/exchange_info/official_data/university_locations.jsonl']
for path in protected:
    assert blob(path) == blob(path, previous), path
assert not subprocess.check_output(['git','diff','--name-only',previous,sha,'--','supabase/migrations'],text=True).strip()
report = {
    'source_commit': sha, 'compared_to': previous, 'new_source_records': 646,
    'reading_status': dict(status), 'manual_new_or_supplemented_records': 44,
    'successful_unread_candidates': 319, 'catalogue_tracks': 214,
    'all_quota_null_agreement_only_and_workflows_pending': True,
    'source_id_row_id_and_review_hash_bindings_verified': True,
    'douglas_original_browser_capture_hash_verified': True,
    'native_pdf_body_verification': 'notrun: this Git delivery stores extracted pages and declared original hashes; no claim of independently rehashing all native PDF response bodies',
    'protected_files_unchanged': protected, 'migration_delta': [],
}
Path('/workspace/recovery-evidence-20261011/ncu-fourth-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
