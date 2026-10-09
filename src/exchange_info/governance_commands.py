"""Atomic command buffers for the existing governance stores and services.

The buffer is a unit of work, not another persistence layer. Existing service
validation runs against it; the real store compares the exact starting snapshot
and commits the resulting revisions, publications and audit together.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
from functools import wraps
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile
import threading
from uuid import uuid4

from . import models as m
from .storage import data_paths, merge_application_workflows, storage_path_lock


def canonical(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        rows = [canonical(item) for item in value]
        return rows
    return value


def fingerprint(rows):
    values = [canonical(row) for row in rows]
    values.sort(key=lambda row: json.dumps(row, sort_keys=True, ensure_ascii=False))
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()


def _bytes(rows):
    return "".join(json.dumps(canonical(row), ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in rows).encode()


def _replace_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _sync_directory(directory):
    if os.name == "posix":
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


_LOCAL_DEPTH = threading.local()


@contextmanager
def local_governance_lock(data_dir):
    """Reentrant thread/process lock; recover a prior interrupted command first."""
    root = Path(data_dir) / "processed"
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".content-governance.lock"
    key = str(lock_path.resolve())
    with storage_path_lock(lock_path):
        active = getattr(_LOCAL_DEPTH, "active", set())
        if key in active:
            yield
            return
        with lock_path.open("a+b") as handle:
            if os.name == "posix":
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            else:
                import msvcrt
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            _LOCAL_DEPTH.active = active | {key}
            try:
                _recover(root)
                yield
            finally:
                _LOCAL_DEPTH.active = active
                if os.name == "posix":
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                else:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


JOURNAL_FILES = frozenset({"application_workflows.jsonl", "application_workflow_revisions.jsonl",
    "application_workflow_audit_log.jsonl", "destination_profile_reviews.jsonl",
    "destination_profile_promotions.jsonl", "destination_profile_rollbacks.jsonl"})


def _recover(root):
    journal = root / ".content-governance-command.json"
    if not journal.exists():
        return
    record = json.loads(journal.read_text())
    if record.get("state") not in {"pending", "committed"} or not record.get("files"):
        raise RuntimeError("治理命令復原資料不完整，已停止讀寫。")
    side = "after" if record["state"] == "committed" else "before"
    for row in record["files"]:
        if row["name"] not in JOURNAL_FILES:
            raise RuntimeError("治理命令復原路徑不合法，已停止讀寫。")
        value = row[side]
        target = root / row["name"]
        if value is None:
            target.unlink(missing_ok=True)
        else:
            decoded = base64.b64decode(value, validate=True)
            if hashlib.sha256(decoded).hexdigest() != row[side + "_sha256"]:
                raise RuntimeError("治理命令復原雜湊不符，已停止讀寫。")
            _replace_bytes(target, decoded)
    _sync_directory(root)
    journal.unlink()
    _sync_directory(root)


def _commit_files(root, replacements):
    """Write-ahead rollback journal with an explicit durable commit marker."""
    journal = root / ".content-governance-command.json"
    files = []
    for name, after in replacements.items():
        assert name in JOURNAL_FILES
        path = root / name
        before = path.read_bytes() if path.exists() else None
        files.append({"name": name, "before": base64.b64encode(before).decode() if before is not None else None,
            "before_sha256": hashlib.sha256(before).hexdigest() if before is not None else None,
            "after": base64.b64encode(after).decode(), "after_sha256": hashlib.sha256(after).hexdigest()})
    record = {"state": "pending", "files": files}
    _replace_bytes(journal, json.dumps(record).encode())
    _sync_directory(root)
    try:
        for name, after in replacements.items():
            _replace_bytes(root / name, after)
        _sync_directory(root)
        record["state"] = "committed"
        _replace_bytes(journal, json.dumps(record).encode())
        _sync_directory(root)
    except BaseException:
        _recover(root)
        raise
    # Once committed, cleanup failure must not report that publication failed.
    try:
        journal.unlink()
        _sync_directory(root)
    except OSError:
        pass  # The next locked read finishes the committed journal.


class WorkflowCommandBuffer:
    _governance_command_buffer = True

    def __init__(self, store):
        self.store = store
        self.backend_name = store.backend_name
        revisions, workflows, self.expected = store.command_snapshot()
        self.original_revisions = [row.model_copy(deep=True) for row in revisions]
        self.original_workflows = [row.model_copy(deep=True) for row in workflows]
        self.revisions = {row.id: row.model_copy(deep=True) for row in revisions}
        self.workflows = [row.model_copy(deep=True) for row in workflows]
        self.changed_workflows = {}

    def list_revisions(self):
        return list(self.revisions.values())

    def load_published_workflows(self):
        return list(self.workflows)

    def save_revision(self, row):
        self.revisions[row.id] = row
        return row

    def publish_workflow(self, workflow, revision_id, *, workflow_key=None):
        from .workflow_identity import workflow_storage_key
        key = workflow_key or workflow_storage_key(workflow)
        if any(workflow_storage_key(row) == key and canonical(row) == canonical(workflow)
               for row in self.workflows):
            return workflow
        self.changed_workflows[key] = workflow
        self.workflows = merge_application_workflows(self.workflows, [workflow])
        return workflow

    def commit(self, operation, actor):
        original = {row.id: row for row in self.original_revisions}
        changed = [row for row in self.revisions.values()
                   if row.id not in original or canonical(row) != canonical(original[row.id])]
        if not changed and not self.changed_workflows:
            return
        self.store.commit_command(self.expected, changed, list(self.changed_workflows.values()),
                                  operation=operation, actor=actor)


def atomic_workflow_command(function):
    @wraps(function)
    def command(store, *args, **kwargs):
        if getattr(store, "_governance_command_buffer", False):
            return function(store, *args, **kwargs)
        if not hasattr(store, "command_snapshot"):
            raise RuntimeError("此治理儲存後端未提供原子命令提交，已停止寫入。")
        buffer = WorkflowCommandBuffer(store)
        result = function(buffer, *args, **kwargs)
        actor = next((kwargs.get(key) for key in ("reviewer_id", "edited_by", "rolled_back_by", "detected_by") if kwargs.get(key)), "automated_refresh")
        buffer.commit(function.__name__, actor)
        return result
    return command


def local_store_command_lock(function):
    @wraps(function)
    def locked(store, *args, **kwargs):
        with local_governance_lock(store.data_dir):
            return function(store, *args, **kwargs)
    return locked


def local_workflow_snapshot(store):
    with local_governance_lock(store.data_dir):
        revisions = store.list_revisions()
        workflows = store.load_published_workflows()
        return revisions, workflows, {"revisions": fingerprint(revisions), "workflows": fingerprint(workflows)}


def local_commit_workflow_command(store, expected, changed, published, *, operation, actor):
    from .storage import read_jsonl
    with local_governance_lock(store.data_dir):
        revisions = store.list_revisions()
        workflows = store.load_published_workflows()
        if expected != {"revisions": fingerprint(revisions), "workflows": fingerprint(workflows)}:
            raise ValueError("治理資料已被其他命令修改，請重新載入目前快照。")
        by_id = {row.id: row for row in revisions}
        by_id.update({row.id: row for row in changed})
        paths = data_paths(store.data_dir)
        replacements = {paths["application_workflow_revisions"].name: _bytes(sorted(by_id.values(), key=lambda row: (row.detected_at, row.id)))}
        if published:
            # Persist only runtime overrides, not copies of the official baseline.
            local = read_jsonl(paths["application_workflows"], m.UniversityApplicationWorkflow)
            replacements[paths["application_workflows"].name] = _bytes(merge_application_workflows(local, published))
        audit_path = paths["application_workflows"].parent / "application_workflow_audit_log.jsonl"
        audit = [json.loads(line) for line in audit_path.read_text().splitlines()] if audit_path.exists() else []
        audit.append({"id": str(uuid4()), "operation": operation, "actor_id": actor,
            "created_at": m.utc_now().isoformat(), "starting_snapshot": expected,
            "revisions_before": [canonical(row) for row in revisions if row.id in {r.id for r in changed}],
            "revisions_after": [canonical(row) for row in changed],
            "published_after": [canonical(row) for row in published]})
        replacements[audit_path.name] = _bytes(audit)
        _commit_files(audit_path.parent, replacements)


REVISION_TOKEN_FIELDS = ('id', 'workflow_key', 'version', 'base_version', 'status', 'content_hash', 'change_summary', 'workflow_payload', 'required_review_count', 'review_approvals', 'edit_history', 'reviewed_by', 'reviewed_at', 'review_note', 'publication_action', 'rolled_back_from_revision_id', 'restored_revision_id', 'detected_by', 'detected_at')
WORKFLOW_TOKEN_FIELDS = ('workflow_key', 'published_version', 'published_payload', 'current_revision_id', 'home_university', 'partner_university', 'program_type', 'academic_year', 'application_round', 'published_at')


def read_governance_snapshot_rows(store, table, *, select, order_key):
    """Read every capped PostgREST page, or fail without treating it as complete.

    Each page requests an exact count and the same unique stable ordering.
    A changed count, repeated identity or inconsistent Content-Range stops the
    command. Changes during otherwise consistent reads still fail the SQL CAS.
    """
    rows, identities, total = [], set(), None
    while total is None or len(rows) < total:
        response = store._request("GET", table, headers={"Prefer": "count=exact"},
            params={"select": select, "order": order_key + ".asc", "offset": len(rows), "limit": 1000})
        page = response.json()
        content_range = response.headers.get("Content-Range", "")
        match = re.fullmatch(r"(?:(\d+)-(\d+)|\*)/(\d+)", content_range)
        if match is None or not isinstance(page, list):
            raise RuntimeError("治理快照缺少可核實的完整筆數，已停止寫入。")
        count = int(match[3])
        if total is None:
            total = count
        elif total != count:
            raise ValueError("治理快照在分頁期間變更，請重新載入。")
        if not page:
            if len(rows) != total:
                raise RuntimeError("治理快照分頁遭截斷，已停止寫入。")
            break
        if match[1] is None or int(match[1]) != len(rows) or int(match[2]) != len(rows) + len(page) - 1:
            raise RuntimeError("治理快照分頁範圍不一致，已停止寫入。")
        for row in page:
            identity = row.get(order_key)
            if identity is None or identity in identities:
                raise RuntimeError("治理快照分頁重複或缺少識別，已停止寫入。")
            identities.add(identity)
        rows.extend(page)
        if len(rows) > total:
            raise RuntimeError("治理快照筆數不一致，已停止寫入。")
    return rows


def supabase_workflow_snapshot(store):
    capability = store._request("GET", "/rest/v1/application_workflow_audit_log", params={
        "select": "id", "metadata->>governance_command_schema": "eq.1", "limit": 1}).json()
    if not capability:
        raise RuntimeError("原子治理命令 migration 尚未可核實，已停止寫入。")
    revision_rows = read_governance_snapshot_rows(store, "/rest/v1/application_workflow_revisions", select="*", order_key="id")
    public_rows = read_governance_snapshot_rows(store, "/rest/v1/application_workflows", select="*", order_key="workflow_key")
    revisions = [store._revision_from_row(row) for row in revision_rows]
    published = [m.UniversityApplicationWorkflow.model_validate(row["published_payload"]) for row in public_rows if row.get("published_payload")]
    fallback = store.fallback.load_published_workflows() if store.fallback is not None else []
    return revisions, merge_application_workflows(fallback, published), {
        "revisions": [{key: row.get(key) for key in REVISION_TOKEN_FIELDS} for row in revision_rows],
        "workflows": [{key: row.get(key) for key in WORKFLOW_TOKEN_FIELDS} for row in public_rows],
    }


def rpc_command_parameters(command):
    """The existing 25-argument, service-only RPC; no new grants or endpoint."""
    return {"p_revision_id": "governance-command", "p_workflow_key": "governance-command",
        "p_version": 1, "p_base_version": None, "p_status": "pending_review",
        "p_content_hash": "0" * 64, "p_change_summary": {"governance_command": command},
        "p_workflow_payload": {}, "p_detected_by": command["actor"], "p_detected_at": m.utc_now().isoformat(),
        "p_required_review_count": 2, "p_review_approvals": [], "p_edit_history": [],
        "p_reviewed_by": None, "p_reviewed_at": None, "p_review_note": None,
        "p_publication_action": "standard", "p_rolled_back_from_revision_id": None, "p_restored_revision_id": None,
        "p_home_university": "", "p_partner_university": "", "p_program_type": None,
        "p_academic_year": None, "p_application_round": None, "p_updated_at": m.utc_now().isoformat()}


def supabase_commit_workflow_command(store, expected, changed, published, *, operation, actor):
    from .content_governance import workflow_review_source_urls, workflow_review_rule_keys
    revision_rows = [{**store._revision_row(row), "required_source_urls": workflow_review_source_urls(row.workflow),
        "required_rule_keys": workflow_review_rule_keys(row.workflow)} for row in changed]
    command = {"kind": "workflow", "expected": expected, "revisions": revision_rows,
        "published": [canonical(row) for row in published], "operation": operation, "actor": actor}
    try:
        store._request("POST", "/rest/v1/rpc/exchange_commit_application_workflow_revision", json=rpc_command_parameters(command))
    except Exception as error:
        response = getattr(error, "response", None)
        if response is not None and response.status_code == 409:
            raise ValueError("治理資料已被其他命令修改，請重新載入目前快照。") from error
        raise


DESTINATION_TYPES = {"reviews": m.DestinationProfileReviewEvent, "promotions": m.DestinationProfilePromotionEvent, "rollbacks": m.DestinationProfileRollbackEvent}


class DestinationCommandBuffer:
    _governance_command_buffer = True

    def __init__(self, store):
        self.store = store
        self.backend_name = store.backend_name
        self.rows, self.expected = store.command_snapshot()
        self.rows = {key: [row.model_copy(deep=True) for row in values] for key, values in self.rows.items()}
        self.added = {key: [] for key in DESTINATION_TYPES}

    def list_events(self):
        return list(self.rows["reviews"])

    def list_promotion_events(self):
        return list(self.rows["promotions"])

    def list_rollback_events(self):
        return list(self.rows["rollbacks"])

    def save(self, key, row):
        self.rows[key].append(row)
        self.added[key].append(row)
        return row

    def save_event(self, row):
        return self.save("reviews", row)

    def save_promotion_event(self, row):
        return self.save("promotions", row)

    def save_rollback_event(self, row):
        return self.save("rollbacks", row)


def atomic_destination_command(function):
    @wraps(function)
    def command(store, profiles, *args, **kwargs):
        if getattr(store, "_governance_command_buffer", False):
            return function(store, profiles, *args, **kwargs)
        if not hasattr(store, "command_snapshot"):
            raise RuntimeError("此生活情報儲存後端未提供原子命令提交，已停止寫入。")
        buffer = DestinationCommandBuffer(store)
        result = function(buffer, profiles, *args, **kwargs)
        if any(buffer.added.values()):
            actor = next(kwargs[key] for key in ("reviewer_id", "promoted_by_id", "rolled_back_by_id") if key in kwargs)
            store.commit_command(buffer.expected, buffer.added, profiles=profiles,
                                 operation=function.__name__, actor=actor)
        return result
    return command


def local_destination_snapshot(store):
    with local_governance_lock(store.data_dir):
        rows = {"reviews": store.list_events(), "promotions": store.list_promotion_events(), "rollbacks": store.list_rollback_events()}
        return rows, {key: fingerprint(value) for key, value in rows.items()}


def local_commit_destination_command(store, expected, added, *, profiles, operation, actor):
    with local_governance_lock(store.data_dir):
        rows, actual = local_destination_snapshot(store)
        if expected != actual:
            raise ValueError("生活情報審查資料已被其他命令修改，請重新載入。")
        paths = {"reviews": store.path, "promotions": store.promotion_path, "rollbacks": store.rollback_path}
        replacements = {paths[key].name: _bytes([*rows[key], *values]) for key, values in added.items() if values}
        audit_path = store.path.parent / "application_workflow_audit_log.jsonl"
        audit = [json.loads(line) for line in audit_path.read_text().splitlines()] if audit_path.exists() else []
        audit.append({"id": str(uuid4()), "operation": operation, "actor_id": actor,
            "created_at": m.utc_now().isoformat(), "starting_snapshot": expected,
            "source_profiles": [canonical(row) for row in profiles],
            "destination_events_before": {key: [canonical(row) for row in values] for key, values in rows.items()},
            "destination_events": {key: [canonical(row) for row in values] for key, values in added.items()}})
        replacements[audit_path.name] = _bytes(audit)
        _commit_files(audit_path.parent, replacements)


DESTINATION_TABLES = {"reviews": "destination_profile_review_events", "promotions": "destination_profile_promotion_events", "rollbacks": "destination_profile_rollback_events"}


def supabase_destination_snapshot(store):
    capability = store._request("GET", "application_workflow_audit_log", params={
        "select": "id", "metadata->>governance_command_schema": "eq.1", "limit": 1}).json()
    if not capability:
        raise RuntimeError("原子治理命令 migration 尚未可核實，已停止寫入。")
    raw = {key: read_governance_snapshot_rows(store, table, select="id,event_payload", order_key="id")
           for key, table in DESTINATION_TABLES.items()}
    expected = {key: [row["event_payload"] for row in values] for key, values in raw.items()}
    return {key: [DESTINATION_TYPES[key].model_validate(row) for row in values] for key, values in expected.items()}, expected


def supabase_commit_destination_command(store, expected, added, *, profiles, operation, actor):
    from .destination_profile_review import _profile_identity_key
    identities = {_profile_identity_key(row.home_university, row.school_name) for values in added.values() for row in values}
    source_profiles = [{"profile_key": _profile_identity_key(row.home_university or "", row.school_name), "profile": canonical(row)} for row in profiles
                       if _profile_identity_key(row.home_university or "", row.school_name) in identities]
    command = {"kind": "destination", "expected": expected, "added": {key: [canonical(row) for row in values] for key, values in added.items()},
        "source_profiles": source_profiles, "operation": operation, "actor": actor}
    try:
        store._request("POST", "rpc/exchange_commit_application_workflow_revision", json=rpc_command_parameters(command))
    except Exception as error:
        response = getattr(error, "response", None)
        if response is not None and response.status_code == 409:
            raise ValueError("生活情報審查資料已被其他命令修改，請重新載入。") from error
        raise
