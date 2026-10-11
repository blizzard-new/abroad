"""Inventory every NCU exchange item and every raw official agreement identity.

Counts are evidence states, not an inference that an agreement is currently open.
This audit never promotes historical host information to the 116 application.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.school_identity import school_identity_key


def inventory():
    bundle = ROOT / "src/exchange_info/official_data/ncu"
    partners = [json.loads(line) for line in (bundle / "partners.jsonl").read_text().splitlines()]
    audit = json.loads((bundle / "field-audit.json").read_text())
    locations = [json.loads(line) for line in (bundle.parent / "university_locations.jsonl").read_text().splitlines()]
    images = json.loads((ROOT / "src/exchange_info/static/assets/school-images.json").read_text())["schools"]
    identity = lambda row: (school_identity_key(row["school_name"]), row.get("country"))
    lm, im = {identity(row): row for row in locations}, {identity(row): row for row in images}
    if (bundle / "campus-locations.json").exists():
        for row in json.loads((bundle / "campus-locations.json").read_text())["locations"]:
            previous = lm.get(identity(row), {})
            if row.get("geocode_status") == "verified" or previous.get("geocode_status") != "verified":
                lm[identity(row)] = row
    if (bundle / "campus-assets.json").exists():
        # This scoped list contains only reviewed identities and licence proofs.
        im = {identity(row): row for row in json.loads((bundle / "campus-assets.json").read_text())["photos"]}
    rows = []
    for partner, record in zip(partners, audit, strict=True):
        assert partner["school_name"] == record["school_name"]
        fields = {key: {**{k: value[k] for k in ("label", "status", "note", "source_urls", "unresolved", "reference_status", "current_applicability_status") if k in value},
                       "gap": value["status"] != "available",
                       "original_locators": [{k: evidence[k] for k in ("source_id", "source_url", "page", "sheet", "applicability", "checked_at") if k in evidence}
                                             for evidence in value.get("original_evidence", [])]}
                  for key, value in record["fields"].items()}
        location = lm.get(identity(partner), {})
        image = im.get(identity(partner), {})
        fields["coordinates"] = {
            "label": "校名／國家／校區核對之地球座標",
            "status": "available" if location.get("geocode_status") == "verified" else "missing",
            "gap": location.get("geocode_status") != "verified", "existing_record": location,
            "note": location.get("note", "尚無已核對的校區或校級代表座標；不以城市中心代替。"),
            "source_urls": [url for url in [location.get("source_url"), location.get("identity_source_url")] if url],
        }
        licensed = image.get("status") == "verified" and bool(image.get("license_url") and image.get("author"))
        fields["campus_photo"] = {
            "label": "對應校園且具可用授權之照片", "status": "available" if licensed else "missing",
            "gap": not licensed, "existing_record": image,
            "note": image.get("caption_zh", "校園參考照片與授權已核對；116录取校區待確認。") if licensed else "既有圖像有來源但缺授權證據，尚不可算可用校園照片。" if image else "尚無已核對的校園照片及可用授權。",
            "source_urls": [url for url in [image.get("image_page_url"), image.get("official_page_url"), image.get("image_source_url")] if url],
        }
        rows.append({"school_name": partner["school_name"], "country": partner["country"],
                     "source_rows": record["source_rows"], "availability_status": partner["availability_status"],
                     "fields": fields,
                     "read_sources": [{k: source[k] for k in ("id", "url", "title", "sha256", "authority_kind", "content_status", "status", "applicability") if k in source}
                                      for source in record["read_sources"]],
                     "collection_attempts": record.get("collection_attempts", []),
                     "unretrieved_sources": record["unretrieved_sources"]})
    keys = list(rows[0]["fields"])
    return {
        "home_university": "國立中央大學", "base_sha": "59a20f27fcee00fb597abc79e75ec11778317422",
        "checked_at": "2026-10-11", "exchange_item_denominator": len(rows),
        "denominator_note": "115歷史名單的214個交換目錄項目；含院級／自費等不同項目，非214個當期可申請學校。",
        "current_host_fully_verified": 0,
        "counts": {key: {"total": len(rows), "gap": sum(row["fields"][key]["gap"] for row in rows),
                         "states": dict(Counter(row["fields"][key]["status"] for row in rows))} for key in keys},
        "schools": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    with args.output.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["school_name", "country", "source_rows", *result["counts"]])
        for row in result["schools"]:
            writer.writerow([row["school_name"], row["country"], ";".join(row["source_rows"]),
                             *(row["fields"][key]["status"] for key in result["counts"])])
    print(json.dumps({key: value for key, value in result.items() if key != "schools"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
