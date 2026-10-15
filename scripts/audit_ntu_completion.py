"""Inspect every NTU partner at a fixed school × field grain.

Presence of reference text is distinct from confirmation for the target cycle.
This script is read-only against the catalog; its outputs are review artifacts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

from exchange_info.school_identity import school_identity_key

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    "home_selection": "母校116-1甄選資格與文件",
    "eligibility": "接待校申請資格",
    "language": "接待校語言要求",
    "quota": "臺大本期甄選名額",
    "deadlines": "接待校提名與申請期限",
    "documents": "最新年度接待校文件",
    "calendar": "接待校學期與行事曆",
    "courses": "課程與選課限制",
    "housing": "住宿資訊",
    "cost": "費用與生活預算",
    "insurance_visa": "保險與簽證",
    "life_sources": "官方生活參考（逐段保留來源範圍）",
    "coordinates": "校名國家與校區核對座標",
    "photos": "校園照片與可用授權",
}
NO_TEXT = {"missing", "not_confirmed_no_text_evidence"}


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def audit(root: Path = ROOT) -> tuple[list[dict], dict]:
    catalog = root / "src/exchange_info/official_data"
    ntu = catalog / "ntu"
    partners = rows(ntu / "partners.jsonl")
    ledger = {r["portal_id"]: r for r in json.loads((ntu / "verification_status.json").read_text())}
    life = {(school_identity_key(r["school_name"]), r["country"]): r for r in rows(ntu / "student_life.jsonl")}
    images = {(school_identity_key(r["school_name"]), r.get("country") or ""): r for r in
              json.loads((root / "src/exchange_info/static/assets/school-images.json").read_text())["schools"]}
    locations = {(school_identity_key(r["school_name"]), r.get("country") or ""): r for r in
                 rows(catalog / "university_locations.jsonl")}
    provenance = json.loads((ntu / "list_verification.json").read_text())
    home = json.loads((ntu / "home_rules.json").read_text())
    identifiers = [p["source_url"].rsplit("/", 1)[-1] for p in partners]
    if len(partners) != 288 or len(set(identifiers)) != 288 or set(identifiers) != set(ledger):
        raise ValueError("NTU denominator or school join changed; inspect before continuing")
    result = []
    for partner in partners:
        portal_id = partner["source_url"].rsplit("/", 1)[-1]
        key = (school_identity_key(partner["school_name"]), partner["country"])
        entry = ledger[portal_id]
        for field, label in FIELDS.items():
            data = entry["fields"].get(field, {})
            status = data.get("status", "missing")
            available = status not in NO_TEXT
            confirmed = False
            urls = data.get("source_urls", [])
            note = "; ".join(data.get("remaining_questions", []))
            checked = None
            observations = data.get("completion_observations", [])
            if observations:
                checked = max(r["checked_at"] for r in observations)
            if field == "home_selection":
                available = home["academic_year"] == "116" and home["outgoing_semester"] == 1
                confirmed = available
                status = "shared_home_current_cycle_rules" if available else "missing"
                urls = [home["authority_order"][0]]
                note = "共通校內規則可用；合作校本期資格、名額與接待校条件另查。"
            elif field == "quota":
                published = partner.get("quota_status") == "published" and partner.get("field_evidence", {}).get("quota", {}).get("status") == "verified_current"
                confirmed = available = partner["quota"] == "0 名" or published
                status = "verified_current_home_selection_quota" if published else "confirmed_zero_not_open" if confirmed else "pending_official_selection_list"
                urls = [provenance["url"]]
                checked = provenance["checked_at"]
                note = partner.get("availability_note") if published else "空白不補成零；內頁參考名額不作臺大本期名額。"
            elif field == "life_sources":
                record = life.get(key, {})
                evidence = record.get("evidence", [])
                available = bool(evidence)
                status = "scoped_official_reference" if available else "no_scoped_life_text"
                urls = sorted({s["url"] for e in evidence for s in e.get("sources", [])})
                checked = record.get("checked_at")
                note = "來源存在不等於十個生活面向完整；依各段原日期與範圍。"
            elif field == "coordinates":
                record = locations.get(key, {})
                available = confirmed = record.get("geocode_status") == "verified"
                status = "reviewed_representative_location" if available else "campus_or_identity_unresolved"
                urls = [u for u in [record.get("source_url"), record.get("identity_source_url")] if u]
                checked = record.get("geocoded_at")
                note = record.get("note", "未取得核對座標；不以城市中心代替學校。")
            elif field == "photos":
                record = images.get(key, {})
                available = confirmed = record.get("status") == "verified" and bool(record.get("local_path"))
                status = "reviewed_licensed_campus_image" if available else record.get("status", "missing")
                urls = [u for u in [record.get("official_page_url"), record.get("license_url")] if u]
                checked = record.get("checked_at")
                note = record.get("note", "未取得與校區身分一致且可重用的照片。")
            result.append({"portal_id": portal_id, "school_name": partner["school_name"], "country": partner["country"],
                "field": field, "label": label, "reference_present": bool(available), "target_requirement_confirmed": confirmed,
                "status": status, "source_urls": urls, "checked_at": checked, "note": note})
            result[-1].update(reviewed_observations=len(observations),
                host_target_year_fact_present=any(r["applicability_status"] == "target_year_explicit" for r in observations),
                observation_periods=sorted({r["applicability_status"] for r in observations}))
    summary = {"checked_at": datetime.now(timezone.utc).isoformat(), "denominator": len(partners),
        "field_count": len(FIELDS), "school_field_rows": len(result), "fields": {},
        "zero_quota_schools": [p["school_name"] for p in partners if p["quota"] == "0 名"],
        "fully_verified_target_cycle_schools": sum(bool(r.get("full_116_1_information_confirmed")) for r in ledger.values()),
        "definition": "reference gap means insufficient text/asset evidence; target confirmation remains separate. Representative coordinates are not an admitted exchange campus.",
        "comparators": {}}
    for field, label in FIELDS.items():
        values = [r for r in result if r["field"] == field]
        summary["fields"][field] = {"label": label, "denominator": len(values),
            "reference_present": sum(r["reference_present"] for r in values),
            "public_evidence_gap": sum(not r["reference_present"] for r in values),
            "target_requirement_unconfirmed": sum(not r["target_requirement_confirmed"] for r in values),
            "host_target_year_fact_present": sum(r["host_target_year_fact_present"] for r in values),
            "statuses": dict(Counter(r["status"] for r in values))}
    for comparator in ("cgu", "ntpu"):
        info = json.loads((catalog / comparator / "catalog-completeness.json").read_text())
        profiles = rows(catalog / comparator / "destination_profiles.jsonl")
        summary["comparators"][comparator] = {"visible_partners": info["partner_count"], "destination_records": len(profiles),
            "workflow_records": len(rows(catalog / comparator / "application_workflows.jsonl")),
            "destination_fields": list(profiles[0]),
            "warning": "Existing populated fields, historical workflows and generated guide text do not prove target-cycle confirmation."}
    return result, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records, summary = audit()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (args.output / "all-school-fields.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    with (args.output / "all-school-fields.csv").open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows({**r, "source_urls": " | ".join(r["source_urls"])} for r in records)
    print(json.dumps({"denominator": summary["denominator"], "school_field_rows": len(records),
        "public_evidence_gaps": {k: v["public_evidence_gap"] for k, v in summary["fields"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
