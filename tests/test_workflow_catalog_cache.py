"""Merging and loading the workflow catalogue: same answers as before, without redoing the work on every request."""
from __future__ import annotations

import random
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from exchange_info import storage
from exchange_info.storage import (
    _application_workflow_key,
    ensure_data_dirs,
    load_application_workflows,
    load_bundled_application_workflows,
    merge_application_workflows,
    save_application_workflows,
)
from exchange_info.workflow_identity import workflow_storage_key


def _reference_merge(baseline, overrides):
    """The merge as it was written before it was indexed: every override scans every row."""
    merged = list(baseline)
    for override in overrides:
        override_key = _application_workflow_key(override)
        governance_key = override.governance_key
        override_scope = (override_key[0], override_key[1], override_key[3], override_key[4])
        merged = [
            row
            for row in merged
            if (
                _application_workflow_key(row) != override_key
                and not (governance_key and workflow_storage_key(row) == governance_key)
                and (
                    bool(override_key[2])
                    or (
                        _application_workflow_key(row)[0],
                        _application_workflow_key(row)[1],
                        _application_workflow_key(row)[3],
                        _application_workflow_key(row)[4],
                    )
                    != override_scope
                )
            )
        ]
        merged.append(override)
    return merged


def _perturbed(rows, rng, count):
    chosen = rng.sample(rows, count)
    result = []
    for row in chosen:
        change = rng.choice(("same", "generic", "other_program", "governed", "other_year", "other_round"))
        if change == "generic":
            row = row.model_copy(update={"program_type": ""})
        elif change == "other_program":
            row = row.model_copy(update={"program_type": f"{row.program_type or 'x'}-b"})
        elif change == "governed":
            target = rng.choice(rows)
            row = row.model_copy(update={"governance_key": workflow_storage_key(target)})
        elif change == "other_year":
            row = row.model_copy(update={"academic_year": f"{row.academic_year or ''}-new"})
        elif change == "other_round":
            row = row.model_copy(update={"application_round": f"{row.application_round or ''}-r2"})
        result.append(row)
    return result


def test_indexed_merge_returns_exactly_what_the_scanning_merge_returned() -> None:
    catalogue = load_bundled_application_workflows()
    assert len(catalogue) > 200
    for seed in range(6):
        rng = random.Random(seed)
        baseline = rng.sample(catalogue, 250)
        overrides = _perturbed(catalogue, rng, 80)
        expected = _reference_merge(baseline, overrides)
        actual = merge_application_workflows(baseline, overrides)
        assert [id(row) for row in actual] == [id(row) for row in expected], seed


def test_a_later_override_can_replace_an_earlier_one() -> None:
    catalogue = load_bundled_application_workflows()
    first = catalogue[0]
    second = first.model_copy(update={"disclaimer": "later wins"})
    merged = merge_application_workflows([], [first, second])
    assert len(merged) == 1 and merged[0] is second


def test_loading_the_bundled_catalogue_is_remembered_but_each_caller_gets_its_own_list(monkeypatch) -> None:
    calls = []
    real = storage.read_jsonl
    monkeypatch.setattr(storage, "read_jsonl", lambda path, model, **kwargs: calls.append(path) or real(path, model, **kwargs))
    storage._workflow_cache.clear()
    first = load_bundled_application_workflows()
    reads = len(calls)
    second = load_bundled_application_workflows()
    assert reads > 0 and len(calls) == reads, "the second load does not read the files again"
    assert first is not second and first == second
    second.clear()
    assert load_bundled_application_workflows() == first, "emptying one caller's list does not touch the others"


def test_local_workflows_are_reread_when_the_file_changes(tmp_path: Path) -> None:
    ensure_data_dirs(tmp_path)
    bundled = load_bundled_application_workflows()
    chosen = bundled[0]
    local = chosen.model_copy(update={"disclaimer": "第一版說明"})
    save_application_workflows([local], tmp_path)
    first = load_application_workflows(tmp_path)
    assert load_application_workflows(tmp_path) == first

    save_application_workflows([chosen.model_copy(update={"disclaimer": "第二版說明，文字長度不同"})], tmp_path)
    after = load_application_workflows(tmp_path)

    texts = {row.disclaimer for row in after if _application_workflow_key(row) == _application_workflow_key(chosen)}
    assert texts == {"第二版說明，文字長度不同"}, "an edited file is read again, not served from the remembered copy"


def test_simultaneous_cold_catalogue_requests_read_each_bundle_once(monkeypatch) -> None:
    storage._workflow_cache.clear()
    calls = []
    first_read = threading.Event()
    release_read = threading.Event()
    barrier = threading.Barrier(3)
    real = storage.read_jsonl

    def read(path, model, **kwargs):
        calls.append(path)
        first_read.set()
        assert release_read.wait(10), "the test must release the cold file read"
        return real(path, model, **kwargs)

    monkeypatch.setattr(storage, "read_jsonl", read)

    def load():
        barrier.wait(timeout=10)
        return load_bundled_application_workflows()

    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = [pool.submit(load) for _ in range(3)]
        try:
            assert first_read.wait(10)
            # Keep the real file read in flight while the other HTTP workers
            # enter the public loader. This reproduces a cold page's requests.
            threading.Event().wait(0.05)
        finally:
            release_read.set()
        rows = [future.result(timeout=30) for future in pending]
    assert len(calls) == len(storage._bundled_workflow_paths())
    assert rows[0] == rows[1] == rows[2]
    assert rows[0] is not rows[1] and rows[1] is not rows[2]
    assert {row.home_university for row in rows[0]} >= {
        "長庚大學", "國立臺北大學", "國立臺灣大學", "國立中央大學"
    }


def test_invalid_local_catalogue_can_be_repaired_after_failed_load(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    path = storage.data_paths(tmp_path)["application_workflows"]
    path.write_text('{"broken":', encoding="utf-8")
    with pytest.raises(ValueError):
        load_application_workflows(tmp_path)
    chosen = load_bundled_application_workflows()[0]
    save_application_workflows([chosen], tmp_path)
    assert len(load_application_workflows(tmp_path)) == 1
