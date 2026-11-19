"""Write a reproducible field-presence inventory from the public exchange catalogue."""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib
import io
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from exchange_info.cgu_catalogue import BUNDLED_SNAPSHOT, validate_snapshot
from exchange_info.models import DestinationProfile, PartnerResearchRecord
from exchange_info.partner_research import apply_partner_research
from exchange_info.school_content import complete_destination_profile
from exchange_info.school_identity import public_catalogue_name, school_program_identity_key
from exchange_info.university_locations import load_university_locations
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data"
PARTNER_FIELDS = ("country", "website", "colleges", "degree_levels", "study_period", "quota",
                  "eligibility", "application_info", "application_deadline", "tuition_info", "source_url")
LIFE_FIELDS = ("city", "housing_summary", "cost_summary", "transport_summary", "campus_life_summary")
PENDING = re.compile(r"待確認|待查|待核|待補|尚未|未公布|未公告|未提供|未取得|未核實|須向.{0,15}確認|依合作校規定")
FIELDS = ("home_id", "home", "partner", "programme", "availability", "roster_source", "host_website",
          "profile_status", "life_source_count", "life_source_example", "workflow_versions",
          "max_steps_in_one_version", "max_documents_in_one_version", "workflow_note",
          "empty_fields", "empty_field_evidence", "fields_with_uncertainty_text")


def records(home, filename):
    path = BUNDLE / home / filename
    if path.exists():
        with path.open(encoding="utf-8") as source:
            for line in source:
                if line.strip():
                    yield json.loads(line)


def partner_rows(university, reference):
    if university.id == "cgu":
        return validate_snapshot(json.loads(BUNDLED_SNAPSHOT.read_text(encoding="utf-8")))
    module = importlib.import_module(f"exchange_info.{university.id}_student_view")
    fetch = getattr(module, f"fetch_{university.id}_partner_universities")
    return fetch(reference_time=reference) if university.id in {"ncu", "tku"} else fetch()


def gap_evidence(partner, profile, fields, home):
    result = {}
    for field in fields:
        record_key = "partner_documents" if field == "application_info" else field
        evidence = partner.field_evidence.get(record_key)
        if evidence:
            result[field] = evidence.status + (" — " + evidence.note if evidence.note else "")
            continue
        if field in LIFE_FIELDS:
            result[field] = profile.coverage_note if profile else "名單無對應生活檔案"
        elif home == "ncu" and field in {"colleges", "degree_levels", "study_period", "tuition_info"}:
            positions = re.findall(r"第\s*\d+\s*頁第\s*\d+\s*列", partner.availability_note or "")
            result[field] = (
                "中央 116-1 的 11/17 名單" + "、".join(positions)
                + "沒有獨立列出這一欄；請依該列備註及接待校當期說明，核對此筆仍缺的條件。"
                if positions else partner.availability_note or "當期名單未核對到此方案。"
            )
        elif partner.availability_status != "open" and partner.availability_note:
            result[field] = partner.availability_note
        else:
            result[field] = "本名單的對應欄位無值，須回原始來源核對。"
    return json.dumps(result, ensure_ascii=False, separators=(",", ":")) if result else ""


def school_rows(university, reference, locations):
    home = university.school_name

    def key(name):
        return school_program_identity_key(public_catalogue_name(name, home))

    research = [PartnerResearchRecord.model_validate(row)
                for row in records(university.id, "partner_research.jsonl")]
    partners = apply_partner_research(partner_rows(university, reference), research,
                                      home_university=home, copy_nested=False)
    profiles = {key(row["school_name"]): row for row in records(university.id, "destination_profiles.jsonl")}
    workflows = defaultdict(list)
    for row in records(university.id, "application_workflows.jsonl"):
        steps = row.get("steps", [])
        docs = {doc for step in steps for doc in step.get("required_documents", [])}
        docs.update(doc["name"] for step in steps for doc in step.get("document_requirements", []))
        workflows[key(row["school_name"])].append((len(steps), len(docs)))
    for partner in partners:
        name = key(partner.school_name)
        profile_row = profiles.get(name)
        profile = None
        if profile_row:
            profile = complete_destination_profile(DestinationProfile.model_validate({**profile_row, "home_university": home}),
                                                   ROOT / "data", locations=locations)
        values = {field: getattr(partner, field) for field in PARTNER_FIELDS}
        values.update({field: getattr(profile, field, None) for field in LIFE_FIELDS})
        empty = [field for field, value in values.items() if not (value or "").strip()]
        versions = workflows.get(name, [])
        note = ""
        if not versions:
            note = "no_partner_workflow_in_bundle"
            if partner.availability_status in {"agreement_only", "not_open", "reference_only"}:
                note = "agreement_reference_or_not_open"
        yield {
            "home_id": university.id, "home": home, "partner": partner.school_name,
            "programme": partner.program_type, "availability": partner.availability_status,
            "roster_source": partner.source_url, "host_website": partner.website or "",
            "profile_status": profile.coverage_status if profile else "no_matching_profile",
            "life_source_count": len(profile.sources) if profile else 0,
            "life_source_example": profile.sources[0].source_url if profile and profile.sources else "",
            "workflow_versions": len(versions), "max_steps_in_one_version": max((v[0] for v in versions), default=0),
            "max_documents_in_one_version": max((v[1] for v in versions), default=0), "workflow_note": note,
            "empty_fields": "|".join(empty), "empty_field_evidence": gap_evidence(partner, profile, empty, university.id),
            "fields_with_uncertainty_text": "|".join(f for f, v in values.items() if v and PENDING.search(v)),
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reference-time", type=datetime.fromisoformat, required=True)
    args = parser.parse_args()
    if args.reference_time.utcoffset() is None:
        parser.error("--reference-time needs a UTC offset")
    args.output.mkdir(parents=True, exist_ok=True)
    locations = load_university_locations(ROOT / "data")
    counts = Counter()
    gaps = defaultdict(Counter)
    with (args.output / "catalog.csv.gz").open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
                writer.writeheader()
                for university in SUPPORTED_UNIVERSITIES:
                    for row in school_rows(university, args.reference_time, locations):
                        writer.writerow(row)
                        counts[university.id] += 1
                        for column in ("empty_fields", "fields_with_uncertainty_text"):
                            for field in filter(None, row[column].split("|")):
                                group = gaps[(university.id, field)]
                                group[column] += 1
                                if row["availability"] == "open":
                                    group[column + "_listed_open"] += 1
                    print(f"{university.id} {counts[university.id]}", flush=True)
    with (args.output / "catalog-gaps.csv").open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(("home_id", "partnerships", "field", "empty", "empty_listed_open",
                         "uncertainty_text", "uncertainty_text_listed_open"))
        for (home, field), group in sorted(gaps.items()):
            writer.writerow((home, counts[home], field, group["empty_fields"],
                             group["empty_fields_listed_open"], group["fields_with_uncertainty_text"],
                             group["fields_with_uncertainty_text_listed_open"]))
    print(f"{len(counts)} home universities; {counts.total()} partnerships")


if __name__ == "__main__":
    main()
