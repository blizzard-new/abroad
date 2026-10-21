"""Bind generated cross-school corrections to the first readable runtime snapshot."""
from __future__ import annotations

import collections
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.cross_school_partners import build_cross_school_entity_index, _synthesize_cross_school_intelligence
from exchange_info.models import CrossSchoolHomeAgreement, PartnerUniversity
from audit_university_data import digest
from university_review_ledger import append_decisions


def main():
    directory = ROOT / "docs/data-verification-20261021"
    inventory = ROOT / "output/data-verification-20261021/runtime-review-20261021"
    manifest_path = directory / "round32-cross-school-provenance-review.json"
    old_manifest = json.loads(manifest_path.read_text("utf8")) if manifest_path.exists() else None
    reviewed_at = old_manifest["reviewed_at"] if old_manifest else datetime.now(timezone.utc).isoformat()
    catalogues, old_cross = collections.defaultdict(list), {}
    with gzip.open(inventory / "records.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            if record["kind"] == "partner":
                catalogues[record["home_id"]].append(PartnerUniversity.model_validate(record["data"]))
            elif record["kind"] == "cross_school":
                old_cross[record["key"]] = record
    entities, _ = build_cross_school_entity_index(lambda u: (catalogues[u.id], None))
    assert {f"{country}/{slug}" for country, slug in entities} == set(old_cross)
    code = "src/exchange_info/cross_school_partners.py"
    base = "b662dced2607bc67c3354c95b7aaad202448bea7"
    source = f"https://github.com/blizzard-new/abroad/blob/{base}/{code}"
    code_hash = hashlib.sha256((ROOT / code).read_bytes()).hexdigest()
    decisions, counts = [], collections.Counter()
    for (country, slug), entity in entities.items():
        record = old_cross[f"{country}/{slug}"]
        data = record["data"]
        agreements = [CrossSchoolHomeAgreement.model_validate(a) for a in data["agreements"] if a["has_agreement"]]
        groups = _synthesize_cross_school_intelligence(entity, agreements)
        for field, points in zip(("living_cost", "housing", "courses", "experience"), groups):
            assert len(data[field]) == len(points), (record["key"], field)
            for index, point in enumerate(points):
                value = data[field][index]
                new = point.model_dump(mode="json")
                # Existing curated prose remains queued for individual external review.
                if entity.curated is not None and field != "experience":
                    continue
                if field == "experience" and new["source_published_at"] is None:
                    continue
                pointer = f"/{field}/{index}"
                counts[field] += 1
                decisions.append({
                    "review_id": digest(["cross-school-provenance-round32", record["record_id"], pointer])[:28],
                    "base_record_id": record["record_id"], "pointer": pointer,
                    "base_value": value, "base_value_sha256": digest(value),
                    "base_status": "needs_confirmation", "expected_value_or_interpretation": new,
                    "reason": "Generated country or mother-school material does not establish current host-school rules; a deadline review or report publication date is not a host-fact review date. Original contributing conditions and lookup sources remain available.",
                    "source_url": source, "source_sha256": code_hash,
                    "source_locator": "_synthesize_cross_school_intelligence; _match_bundled_digests_for_entity; _render_structured_points_html; see current_code_sha256 for reviewed implementation",
                    "retrieved_at": reviewed_at, "reviewed_at": reviewed_at,
                    "source_type": "repository_generator", "method": "implementation_provenance_review",
                    "baseline_inventory": str(inventory.relative_to(ROOT)).replace("\\", "/"),
                    "whole_record_verified": False,
                })
    # Pin every immutable pre-review output, including the newly readable 2,010 pages.
    manifest = {
        "reviewed_at": reviewed_at, "base_commit": base,
        "inventory": str(inventory.relative_to(ROOT)).replace("\\", "/"),
        "inventory_files": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
            for p in sorted(inventory.iterdir()) if p.is_file()],
        "current_code_sha256": code_hash, "cross_school_records": len(old_cross),
        "changed_points": dict(counts), "field_decisions": len(decisions),
        "facts_verified_by_this_implementation_review": 0,
        "limitations": ["The original baseline could not extract these pages; bindings use the explicitly named later snapshot.",
            "Existing curated prose is retained pending separate official-source review.",
            "Original mother-school conditions, agreements, years and deadlines are not certified by this correction."],
    }
    # The public URL identifies the original generator; its hash must identify that
    # blob rather than the amended local implementation.
    import subprocess
    original = subprocess.check_output(["git", "show", f"{base}:{code}"], cwd=ROOT)
    source_hash = hashlib.sha256(original).hexdigest()
    manifest["original_generator_sha256"] = source_hash
    for decision in decisions:
        decision["source_sha256"] = source_hash
    if old_manifest is not None and old_manifest != manifest:
        raise ValueError("Round 32 evidence changed; create a new review rather than overwrite it")
    added = append_decisions(directory, decisions)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf8")
    print(json.dumps({"decisions": len(decisions), "added": added, "points": dict(counts)}))


if __name__ == "__main__":
    main()
