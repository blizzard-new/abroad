"""Validate immutable inventory bindings; this does not establish factual truth."""
from __future__ import annotations

import collections
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

from audit_university_data import digest
from university_review_ledger import iter_decisions

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/data-verification-20261021"


def pointer_value(value, pointer):
    for part in pointer.split("/")[1:]:
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def validate():
    grouped = collections.defaultdict(lambda: collections.defaultdict(list))
    seen, errors = set(), []
    for row in iter_decisions(DOCS):
        if row["review_id"] in seen:
            errors.append({"id": row["review_id"], "error": "duplicate review id"})
        seen.add(row["review_id"])
        inventory = row.get("baseline_inventory", "output/data-verification-20261021/baseline")
        grouped[inventory][row["base_record_id"]].append(row)
    counts, nullable, bound_records = collections.Counter(), 0, 0
    for inventory, wanted in grouped.items():
        found = set()
        with gzip.open(ROOT / inventory / "records.jsonl.gz", "rt", encoding="utf8") as stream:
            for line in stream:
                record = json.loads(line)
                reviews = wanted.get(record["record_id"])
                if not reviews:
                    continue
                found.add(record["record_id"])
                bound_records += 1
                for review in reviews:
                    try:
                        value = pointer_value(record["data"], review["pointer"])
                    except (KeyError, IndexError, TypeError, ValueError):
                        if review["base_value"] is None:
                            nullable += 1
                            value = None
                        else:
                            errors.append({"id": review["review_id"], "error": "pointer missing"})
                            continue
                    if value != review["base_value"] or digest(value) != review["base_value_sha256"]:
                        errors.append({"id": review["review_id"], "error": "original value or digest mismatch"})
                    counts[inventory] += 1
        for missing in wanted.keys() - found:
            errors.append({"id": missing, "error": "original record missing", "inventory": inventory})
    migration = json.loads((DOCS / "review-decisions/migration.json").read_text("utf8"))
    original = hashlib.sha256()
    for part in migration["parts"]:
        raw = (DOCS / "review-decisions" / part["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != part["sha256"]:
            errors.append({"id": part["file"], "error": "migrated ledger part changed"})
        original.update(raw)
    if original.hexdigest() != migration["original_sha256"]:
        errors.append({"error": "migrated ledger concatenation changed"})
    # Later inventories are explicitly separate snapshots, never replacements.
    manifests = [
        ("round31-special-catalog-baseline-manifest.json", "output/data-verification-20261021/special-catalog-baseline"),
    ]
    pinned = {}
    for filename, folder in manifests:
        m = json.loads((DOCS / filename).read_text("utf8"))
        pinned.update({str(Path(folder) / name): expected for name, expected in m["outputs"].items()})
    m = json.loads((DOCS / "round28-workflow-version-reconciliation.json").read_text("utf8"))
    pinned.update(m["inputs"])
    pinned.update(m["outputs"])
    m = json.loads((DOCS / "round32-cross-school-provenance-review.json").read_text("utf8"))
    pinned.update({row["path"]: row["sha256"] for row in m["inventory_files"]})
    for path, expected in pinned.items():
        actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        if actual != expected:
            errors.append({"id": path, "error": "pinned inventory file changed"})
    result = {"validated_at": datetime.now(timezone.utc).isoformat(), "review_decisions": len(seen),
              "bindings_by_inventory": dict(counts), "bound_records": bound_records,
              "absent_optional_null_bindings": nullable, "pinned_inventory_files": len(pinned),
              "original_ledger_sha256": original.hexdigest(), "errors": errors,
              "facts_verified_by_validation": 0}
    (DOCS / "review-evidence-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf8")
    print(json.dumps(result, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    validate()
