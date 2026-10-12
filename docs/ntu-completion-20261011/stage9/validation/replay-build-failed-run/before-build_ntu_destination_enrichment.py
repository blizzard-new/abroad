"""Replay reviewed NTU destination overlays without network or production writes."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from exchange_info.life_context import LifeResearchSnapshot, reviewed_life_snapshot
from exchange_info.school_image_collector import SchoolImageRecord
from exchange_info.school_identity import school_identity_key
from exchange_info.university_locations import UniversityLocation, location_key

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "sources/ntu/destinations-2026-10-08.json.gz"
PHOTO_REVIEW = ROOT / "sources/ntu/photo-license-review-2026-10-09.json"
PACKAGE = ROOT / "src/exchange_info"


def build(snapshot_path: Path = SNAPSHOT) -> dict:
    snapshot = json.loads(gzip.decompress(snapshot_path.read_bytes()))
    review = json.loads(PHOTO_REVIEW.read_text())
    if hashlib.sha256(snapshot_path.read_bytes()).hexdigest() != review["frozen_snapshot_sha256"]:
        raise ValueError("Photo permission review belongs to a different snapshot")
    pending = {(r["school_name"], r["country"]): r for r in review["rows"]}
    for row in snapshot["photos"]:
        if decision := pending.get((row["school_name"], row["country"])):
            if decision["content_hash"] != row["content_hash"]:
                raise ValueError("Photo permission review hash mismatch")
            row.update(status="needs_review", local_path=None, note=decision["reason"])
    manifest_path = PACKAGE / "static/assets/school-images.json"
    manifest = json.loads(manifest_path.read_text())
    images = {(school_identity_key(r["school_name"]), r["country"]): r for r in manifest["schools"]}
    for row in snapshot["photos"]:
        record = SchoolImageRecord(**row)
        if record.status == "verified":
            relative = record.local_path.split("?", 1)[0].removeprefix("/static/")
            file = PACKAGE / "static" / relative
            if hashlib.sha256(file.read_bytes()).hexdigest() != record.content_hash:
                raise ValueError(f"Photo hash mismatch: {record.school_name}")
        elif record.status not in {"missing", "needs_review"} or record.local_path:
            raise ValueError("Only reviewed photographs or explicit missing records may be bundled")
        images[(school_identity_key(record.school_name), record.country)] = row
    manifest["schools"] = list(images.values())
    manifest["updated_at"] = snapshot["reviewed_at"]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    location_path = PACKAGE / "official_data/university_locations.jsonl"
    locations = {location_key(r.school_name, r.country): r for r in
                 map(UniversityLocation.model_validate_json, location_path.read_text().splitlines())}
    for raw in snapshot["locations"]:
        record = UniversityLocation.model_validate(raw)
        locations[location_key(record.school_name, record.country)] = record
    location_path.write_text("".join(r.model_dump_json() + "\n" for _, r in sorted(locations.items())))
    life = [reviewed_life_snapshot(LifeResearchSnapshot.model_validate(r)) for r in snapshot["life"]]
    keys = [(r.school_name, r.country) for r in life]
    if len(keys) != 288 or len(set(keys)) != 288:
        raise ValueError("All 288 NTU destinations must have a distinct research result")
    (PACKAGE / "official_data/ntu/student_life.jsonl").write_text("".join(r.model_dump_json() + "\n" for r in life))
    translations_path = PACKAGE / "official_data/life_translations_zh.json"
    translations = {(r["url"], r["original"]): r for r in json.loads(translations_path.read_text())}
    for row in snapshot.get("translations", []):
        translations[(row["url"], row["original"])] = row
    translations_path.write_text(json.dumps(list(translations.values()), ensure_ascii=False, indent=2) + "\n")
    from exchange_info.ntu_completion import apply_completion, SOURCE as COMPLETION_SOURCE
    if COMPLETION_SOURCE.exists():
        apply_completion(PACKAGE / "official_data/ntu", apply_assets=True)
    return {"photos": sum(r["status"] == "verified" for r in snapshot["photos"]),
            "locations": sum(r["geocode_status"] == "verified" for r in snapshot["locations"]),
            "life_with_evidence": sum(bool(r.evidence) for r in life)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    print(json.dumps(build(parser.parse_args().snapshot), ensure_ascii=False))
