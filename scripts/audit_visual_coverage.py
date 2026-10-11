"""Audit six-school public visual data independently of application test results.

Use saved public dashboard snapshots, or an explicitly supplied local/test URL.
No collector, geocoder, account write, database write or deployment is performed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from exchange_info.school_identity import VisualRecordIndex, school_identity_key
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES

STATIC = Path(__file__).resolve().parents[1] / "src/exchange_info/static"


def marker_available(location):
    if not location or location.get("geocode_status") != "verified":
        return False
    lat, lng = location.get("latitude"), location.get("longitude")
    return (
        isinstance(lat, (float, int)) and not isinstance(lat, bool)
        and isinstance(lng, (float, int)) and not isinstance(lng, bool)
        and math.isfinite(lat) and math.isfinite(lng)
        and abs(lat) <= 90 and abs(lng) <= 180
    )


def image_index(rows):
    return VisualRecordIndex({
        (school_identity_key(row["school_name"]), row.get("country") or ""): row
        for row in rows if row.get("school_name")
    })


def photo_evidence(row, static_root=STATIC):
    if not row:
        return {"status": "missing", "file_ok": False, "hash_ok": False,
                "license_metadata": "missing", "explicit_identity_source": False,
                "reason": "沒有對應照片清冊記錄。"}
    relative = urlsplit(row.get("local_path") or "").path.removeprefix("/static/")
    path = (static_root / relative).resolve()
    file_ok = bool(relative and path.is_relative_to(static_root.resolve()) and path.is_file())
    hash_ok = bool(file_ok and row.get("content_hash") and hashlib.sha256(path.read_bytes()).hexdigest() == row["content_hash"])
    license_name = str(row.get("license_name") or "").strip()
    artist = str(row.get("artist") or "").strip()
    documented = bool(license_name and row.get("official_page_url") and row.get("checked_at"))
    if license_name.startswith("CC BY"):
        documented = documented and bool(row.get("license_url") and artist and artist.casefold() not in {"unknown", "see below", "n/a", "not provided"})
    return {"status": row.get("status") or "missing", "file_ok": file_ok, "hash_ok": hash_ok,
            "license_metadata": "documented" if documented else "pending",
            "explicit_identity_source": bool(row.get("identity_source_url")),
            "license_name": license_name or None, "license_url": row.get("license_url"),
            "artist": artist or None, "source_url": row.get("official_page_url"),
            "identity_source_url": row.get("identity_source_url"),
            "local_path": row.get("local_path"), "checked_at": row.get("checked_at"),
            "reason": row.get("note") or "尚無照片來源／授權說明。"}


def audit_school(dashboard, home, visuals, static_root=STATIC):
    records = []
    for partner in dashboard["partner_universities"]:
        location = partner.get("location") or {}
        visual = visuals.get((partner["school_name"], partner.get("country") or ""))
        photo = photo_evidence(visual, static_root)
        api_photo = partner.get("image_status") == "verified" and bool(partner.get("image_url"))
        issues = []
        if not marker_available(location):
            issues.append("location_" + location.get("geocode_status", "missing"))
        if not api_photo:
            issues.append("photo_" + str(partner.get("image_status") or "missing"))
        if api_photo and (not photo["file_ok"] or not photo["hash_ok"]):
            issues.append("photo_file_or_hash_invalid")
        if photo["license_metadata"] != "documented":
            issues.append("photo_license_" + photo["license_metadata"])
        if visual and not photo["explicit_identity_source"]:
            issues.append("photo_explicit_identity_link_missing")
        records.append({"school_name": partner["school_name"], "country": partner.get("country"),
                        "availability_status": partner.get("availability_status"), "quota": partner.get("quota"),
                        "partnership_source": partner.get("source_url"), "location": location,
                        "expected_marker": marker_available(location), "api_photo_available": api_photo,
                        "photo": photo, "issues": issues})
    location = (home or {}).get("location") or {}
    return {
        "school_name": dashboard["school_name"], "catalog_count": len(records),
        "official_roster_completeness": "not_established_by_visual_audit",
        "home": {"expected_marker_count": 1, "available_marker_count": int(marker_available(location)), "location": location},
        "marker_available": sum(r["expected_marker"] for r in records),
        "location_statuses": dict(Counter(r["location"].get("geocode_status", "missing") for r in records)),
        "api_photos_available": sum(r["api_photo_available"] for r in records),
        "photo_files_and_hashes_valid": sum(r["api_photo_available"] and r["photo"]["file_ok"] and r["photo"]["hash_ok"] for r in records),
        "photos_with_license_metadata": sum(r["api_photo_available"] and r["photo"]["license_metadata"] == "documented" for r in records),
        "photos_with_explicit_identity_link": sum(r["api_photo_available"] and r["photo"]["explicit_identity_source"] for r in records),
        "availability_statuses": dict(Counter(r["availability_status"] for r in records)),
        "records": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--base-url", help="Explicit read-only API URL; prefer isolated local server")
    source.add_argument("--snapshot-dir", type=Path, action="append", help="Repeat for separate observation batches")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=STATIC / "assets/school-images.json")
    parser.add_argument("--static-root", type=Path, default=STATIC)
    args = parser.parse_args()
    dashboards, homes = {}, {}
    if args.base_url:
        import requests
        base = args.base_url.rstrip("/")
        response = requests.get(base + "/universities", timeout=90)
        response.raise_for_status()
        homes = {r["school_name"]: r for r in response.json()}
        for university in SUPPORTED_UNIVERSITIES:
            response = requests.get(base + "/student-dashboard", params={"school": university.school_name}, timeout=90)
            response.raise_for_status()
            dashboards[university.school_name] = response.json()
    else:
        for folder in args.snapshot_dir:
            if (folder / "universities.json").exists():
                homes.update({r["school_name"]:r for r in json.loads((folder / "universities.json").read_text())})
            for path in folder.glob("*-dashboard.json"):
                payload = json.loads(path.read_text())
                dashboards[payload["school_name"]] = payload
            observations = folder / "observations.json"
            if observations.exists():
                for case in json.loads(observations.read_text()).get("cases", []):
                    homes[case["school"]] = case["home"]
    manifest = json.loads(args.manifest.read_text())
    visuals = image_index(manifest["schools"])
    audits = [audit_school(dashboards[u.school_name], homes.get(u.school_name), visuals, args.static_root)
              for u in SUPPORTED_UNIVERSITIES if u.school_name in dashboards]
    result = {"generated_at": datetime.now(timezone.utc).isoformat(), "software_test_result": "not_run_by_data_audit",
              "license_note": "Documented metadata is not an independent legal or image-identity review.",
              "missing_school_snapshots": [u.school_name for u in SUPPORTED_UNIVERSITIES if u.school_name not in dashboards],
              "schools": audits}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "coverage.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    for university, audit in [(u, a) for u in SUPPORTED_UNIVERSITIES for a in audits if u.school_name == a["school_name"]]:
        (args.output / f"{university.id}-gaps.json").write_text(json.dumps([r for r in audit["records"] if r["issues"]], ensure_ascii=False, indent=2) + "\n")
    for row in audits:
        print(json.dumps({key:row[key] for key in ["school_name", "catalog_count", "marker_available", "api_photos_available", "photo_files_and_hashes_valid", "photos_with_license_metadata"]}, ensure_ascii=False))
    if result["missing_school_snapshots"]:
        print("INCOMPLETE snapshots:", ", ".join(result["missing_school_snapshots"]))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
