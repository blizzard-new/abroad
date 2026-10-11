"""Isolated decision/storage prototype. NOT imported by the app or any PR.

A complete source batch replaces a prior snapshot atomically; partial/failed
batches only change attempt metadata. All source-row values are preserved.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import threading

HOME_SCHOOL = '長庚大學'
SOURCE_IDS = {'1EAOsiZkw5oWWUpAyXz-04aQWdSMR9f_c3Jup69LeiuA', '1aQiwbtrQu1QOIOkFrOYl9WkzT0mqnZqIwI9KJCXGb4E'}


def records_hash(records):
    return hashlib.sha256(json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate(snapshot):
    if snapshot.get('format_version') != 1 or snapshot.get('home_school') != HOME_SCHOOL:
        raise ValueError('wrong_snapshot_scope_or_schema')
    if snapshot.get('source_state') != 'complete_successful_fetch':
        raise ValueError('not_a_successful_source_snapshot')
    stamp = datetime.fromisoformat(snapshot['fetched_at'])
    if stamp.tzinfo is None:
        raise ValueError('timestamp_requires_timezone')
    receipts = snapshot['source_receipts']
    if len(receipts) != 2 or {r['spreadsheet_id'] for r in receipts} != SOURCE_IDS:
        raise ValueError('incomplete_source_set')
    if any(r.get('http_status') != 200 or not r.get('schema_valid') or r.get('raw_rows', 0) <= 0 for r in receipts):
        raise ValueError('source_failed_invalid_or_empty')
    rows = snapshot['records']
    if not rows or snapshot['record_count'] != len(rows) or snapshot['records_sha256'] != records_hash(rows):
        raise ValueError('invalid_snapshot_payload')
    return snapshot


class Store:
    def __init__(self, path, *, bundled=None, retry_seconds=60):
        self.path = Path(path)
        self.retry_seconds = retry_seconds
        self._state = (None, None)
        self._lock = threading.Lock()
        candidates = [bundled] if bundled else []
        if self.path.exists():
            try:
                candidates.append(json.loads(self.path.read_text()))
            except (OSError, ValueError):
                pass
        valid = []
        for candidate in candidates:
            try:
                valid.append(validate(deepcopy(candidate)))
            except (KeyError, TypeError, ValueError):
                pass
        if valid:
            self._state = (max(valid, key=lambda row: datetime.fromisoformat(row['fetched_at'])), None)

    @property
    def snapshot(self):
        return self._state[0]

    @property
    def attempt(self):
        return self._state[1]

    def view(self):
        snapshot, attempt = self._state
        return deepcopy({
            'records': snapshot['records'] if snapshot else [],
            'source_status': 'unavailable' if snapshot is None else 'fresh' if attempt and attempt['result'] == 'success' else 'stale_reference',
            'last_success_at': snapshot['fetched_at'] if snapshot else None,
            'snapshot_hash': snapshot['records_sha256'] if snapshot else None,
            'last_attempt': attempt,
        })

    def refresh(self, fetch_batch, *, now):
        if not self._lock.acquire(blocking=False):
            return self.view()
        try:
            if self.attempt and (now - datetime.fromisoformat(self.attempt['at'])).total_seconds() < self.retry_seconds:
                return self.view()
            try:
                candidate = deepcopy(fetch_batch())
                validate(candidate)
                if self.snapshot and datetime.fromisoformat(candidate['fetched_at']) < datetime.fromisoformat(self.snapshot['fetched_at']):
                    raise ValueError('older_snapshot_cannot_replace_newer')
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.path.with_suffix(self.path.suffix + '.tmp')
                tmp.write_text(json.dumps(candidate, ensure_ascii=False) + '\n')
                os.replace(tmp, self.path)
                self._state = (candidate, {'at': now.isoformat(), 'result': 'success'})
            except (OSError, KeyError, TypeError, ValueError, RuntimeError) as error:
                self._state = (self.snapshot, {'at': now.isoformat(), 'result': 'failed', 'reason': type(error).__name__})
            return self.view()
        finally:
            self._lock.release()
