"""Reproducible public-data census; extraction never certifies factual truth.

Read source-controlled public data only. Private/user/production databases are
not queried. All exported leaf values start pending or missing; existing review
labels are retained as evidence to inspect, never accepted as new verification.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
from datetime import datetime, timezone
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DEFAULT_OUT = ROOT / "output/data-verification-20261021/current"
BUNDLE = ROOT / "src/exchange_info/official_data"
URL_RE = re.compile(r"https?://[^\s<>\"'；，。（）、\]）]+")
GAP_RE = re.compile(r"待確認|待核對|待核實|未核實|未確認|未取得|尚未|待補|未提供|未公開|未公布|未公告|依.*規定")
PARTNER_REQUIRED = (
    "country", "school_name", "website", "colleges", "degree_levels",
    "study_period", "quota", "eligibility", "application_deadline",
    "tuition_info", "source_url",
)
DESTINATION_REQUIRED = (
    "city", "housing_summary", "cost_summary", "transport_summary",
    "campus_life_summary",
)


def dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(dump(value).encode("utf-8")).hexdigest()


def url_identity(url: str) -> str | None:
    """Discard anchors for fetching, preserve path/query case and ordering."""
    try:
        parts = urlsplit(url)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
            return None
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))
    except ValueError:
        return None


def urls_in(value: Any) -> set[str]:
    if isinstance(value, str):
        return {u for raw in URL_RE.findall(value) if (u := url_identity(raw))}
    if isinstance(value, dict):
        return set().union(*(urls_in(v) for v in value.values())) if value else set()
    if isinstance(value, (list, tuple)):
        return set().union(*(urls_in(v) for v in value)) if value else set()
    return set()


def leaves(value: Any, pointer: str = ""):
    if isinstance(value, dict) and value:
        for key, child in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from leaves(child, f"{pointer}/{escaped}")
    elif isinstance(value, (list, tuple)) and value:
        for i, child in enumerate(value):
            yield from leaves(child, f"{pointer}/{i}")
    else:
        yield pointer or "/", value


def is_empty(value: Any) -> bool:
    # Zero quota and False boolean are substantive values, never missing.
    return value is None or value == "" or value == [] or value == {}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def as_json(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    return value


class Census:
    def __init__(self, out: Path):
        self.out = out
        out.mkdir(parents=True, exist_ok=True)
        self.records = []
        self.sources = collections.defaultdict(lambda: {"records": set(), "homes": set(), "kinds": set()})
        self.gaps = []
        self.school_stats = []
        self.errors = []
        self.ids = set()

    def add(self, home: str, kind: str, key: str, value: Any, provenance: str):
        value = as_json(value)
        record_id = digest([home, kind, key])[:24]
        if record_id in self.ids:
            raise ValueError(f"duplicate census identity: {home}/{kind}/{key}")
        self.ids.add(record_id)
        source_urls = sorted(urls_in(value))
        record = {
            "record_id": record_id, "home_id": home, "kind": kind, "key": key,
            "provenance": provenance, "value_sha256": digest(value), "data": value,
            "candidate_urls": source_urls, "review_status": "pending_review",
        }
        self.records.append(record)
        for url in source_urls:
            source = self.sources[url]
            source["records"].add(record_id)
            source["homes"].add(home)
            source["kinds"].add(kind)
        required = PARTNER_REQUIRED if kind == "partner" else DESTINATION_REQUIRED if kind == "destination" else ()
        for field in required:
            item = value.get(field)
            if is_empty(item) or (isinstance(item, str) and GAP_RE.search(item)):
                self.gaps.append({
                    "record_id": record_id, "home_id": home, "kind": kind,
                    "school": value.get("school_name", key), "field": field,
                    "status": "missing" if is_empty(item) else "needs_confirmation",
                    "value": item,
                })
        return record

    def save(self):
        import csv
        for filename, rows in (("records.jsonl.gz", self.records),):
            with gzip.GzipFile(filename=str(self.out / filename), mode="wb", mtime=0) as stream:
                for row in rows:
                    stream.write((dump(row) + "\n").encode("utf-8"))
        counts = collections.Counter()
        with gzip.GzipFile(filename=str(self.out / "fields.jsonl.gz"), mode="wb", mtime=0) as stream:
            for record in self.records:
                for pointer, value in leaves(record["data"]):
                    status = "missing" if is_empty(value) else "pending_review"
                    row = {
                        "field_id": digest([record["record_id"], pointer, value])[:32],
                        "record_id": record["record_id"], "home_id": record["home_id"],
                        "pointer": pointer, "value": value, "review_status": status,
                    }
                    counts[status] += 1
                    stream.write((dump(row) + "\n").encode("utf-8"))
        sources = [
            {"url": url, "url_id": hashlib.sha256(url.encode()).hexdigest(),
             "record_ids": sorted(row["records"]), "home_ids": sorted(row["homes"]), "kinds": sorted(row["kinds"])}
            for url, row in sorted(self.sources.items())
        ]
        (self.out / "sources.json").write_text(dump(sources) + "\n", "utf-8")
        with (self.out / "field-gaps.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["record_id", "home_id", "kind", "school", "field", "status", "value"])
            writer.writeheader()
            writer.writerows(self.gaps)
        summary = {
            "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "worktree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "status": "in_progress", "facts_verified_by_extraction": 0,
            "school_count": len(self.school_stats), "schools": self.school_stats,
            "record_counts": dict(collections.Counter(row["kind"] for row in self.records)),
            "leaf_counts": dict(counts), "candidate_source_count": len(sources),
            "required_field_gap_count": len(self.gaps), "extraction_errors": self.errors,
            "limitations": [
                "Leaf census includes metadata and evidence text; it is not a count of distinct factual claims.",
                "Candidate URL association is record-level, not evidence that a URL supports each field.",
                "Missing optional fields require applicability review; do not count all null leaves as product defects.",
                "Official source reading and semantic comparison remain required for every factual claim.",
                "Production database content and authenticated user submissions have not been exported.",
                "Dynamic UI and code-generated assertions require separate coverage reconciliation.",
            ],
        }
        (self.out / "inventory-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", "utf-8")
        brief = {k: v for k, v in summary.items() if k not in {"schools", "limitations", "extraction_errors"}}
        brief["extraction_error_count"] = len(self.errors)
        print(json.dumps(brief, ensure_ascii=False, indent=2))


def inventory(out: Path):
    from exchange_info.university_registry import SUPPORTED_UNIVERSITIES
    from exchange_info.cgu_catalogue import BUNDLED_SNAPSHOT, validate_snapshot
    from exchange_info.models import DestinationProfile
    from exchange_info.verified_window_deadlines import get_verified_school_window_card
    from exchange_info.student_view import build_student_dashboard
    from exchange_info.school_content import complete_destination_profile
    from exchange_info.university_locations import load_university_locations
    from exchange_info.storage import load_partner_research
    from exchange_info.partner_research import apply_partner_research
    from exchange_info.cross_school_partners import (
        build_cross_school_entity_index, _build_home_agreement,
        _synthesize_cross_school_intelligence,
    )

    census = Census(out)
    catalogues = {}
    research = load_partner_research(ROOT / "data", include_bundled_baseline=True)
    locations = load_university_locations(ROOT / "data")
    for university in SUPPORTED_UNIVERSITIES:
        home = university.id
        module_path = "src/exchange_info/student_view.py" if home == "cgu" else f"src/exchange_info/{home}_student_view.py"
        try:
            if home == "cgu":
                partners = list(validate_snapshot(json.loads(BUNDLED_SNAPSHOT.read_text("utf-8"))))
                dashboard = build_student_dashboard([], fetch_partner_sheets=False, fetch_regulation_rules=False)
                # CGU's live/cached page input requires a separate production/current-source comparison.
                census.errors.append({"home_id": home, "scope": "dashboard", "error": "CGU dashboard extracted without live/processed pages; reconcile current source-dependent rules separately."})
            else:
                module = importlib.import_module(f"exchange_info.{home}_student_view")
                partners = getattr(module, f"fetch_{home}_partner_universities")()
                dashboard = getattr(module, f"build_{home}_student_dashboard")(partner_universities=partners)
            partners = apply_partner_research(partners, research, home_university=university.school_name, copy_nested=False)
            catalogues[home] = partners
            census.add(home, "university", home, university, "src/exchange_info/university_registry.py")
            # Partners are exported separately, including all programme rows.
            home_data = dashboard.model_dump(mode="json")
            home_data.pop("partner_universities", None)
            census.add(home, "dashboard", home, home_data, module_path)
            try:
                card = get_verified_school_window_card(home)
                census.add(home, "deadline_card", home, card, "src/exchange_info/verified_window_deadlines.py")
            except KeyError as exc:
                census.errors.append({"home_id": home, "scope": "deadline_card", "error": str(exc)})
            names = collections.Counter()
            for partner in partners:
                identity = f"{partner.country}|{partner.school_name}|{partner.program_type}"
                names[identity] += 1
                census.add(home, "partner", f"{identity}|{names[identity]}", partner, module_path)
            count_by_kind = {}
            for filename, kind in (("application_workflows.jsonl", "workflow"), ("destination_profiles.jsonl", "destination")):
                path = BUNDLE / home / filename
                rows = read_jsonl(path) if path.exists() else []
                count_by_kind[kind] = len(rows)
                for index, row in enumerate(rows):
                    if kind == "destination":
                        row = complete_destination_profile(DestinationProfile.model_validate(row), ROOT / "data", locations=locations).model_dump(mode="json")
                    census.add(home, kind, f"{row.get('id', row.get('school_name', ''))}|{index}", row, path.relative_to(ROOT).as_posix())
            info_path = BUNDLE / home / "exchange_info.json"
            if info_path.exists():
                info = json.loads(info_path.read_text("utf-8"))
                info.pop("partner_universities", None)
                census.add(home, "exchange_info", home, info, info_path.relative_to(ROOT).as_posix())
            census.school_stats.append({
                "home_id": home, "school_name": university.school_name,
                "partner_rows": len(partners), "distinct_partner_names": len({p.school_name for p in partners}),
                "availability": dict(collections.Counter(p.availability_status for p in partners)),
                **count_by_kind,
            })
            print(f"{home}: {len(partners)} partner rows", flush=True)
        except Exception as exc:
            census.errors.append({"home_id": home, "error": f"{type(exc).__name__}: {exc}"})
            print(f"{home}: EXTRACTION ERROR {type(exc).__name__}: {exc}", flush=True)
    if len(catalogues) == len(SUPPORTED_UNIVERSITIES):
        entities, _ = build_cross_school_entity_index(lambda u: (catalogues[u.id], None))
        for (country, slug), entity in entities.items():
            try:
                agreements = [_build_home_agreement(u, entity.home_rows.get(u.id)) for u in SUPPORTED_UNIVERSITIES]
                contracted = [a for a in agreements if a.has_agreement]
                groups = _synthesize_cross_school_intelligence(entity, contracted)
            except Exception as exc:
                census.errors.append({"scope": "cross_school", "key": f"{country}/{slug}", "error": f"{type(exc).__name__}: {exc}"})
                census.add("_shared", "cross_school_extraction_error", f"{country}/{slug}", {
                    "school_name": entity.school_name_zh,
                    "home_ids": list(entity.home_rows),
                    "error": f"{type(exc).__name__}: {exc}",
                }, "src/exchange_info/cross_school_partners.py")
                continue
            census.add("_shared", "cross_school", f"{country}/{slug}", {
                "school_name": entity.school_name_zh,
                "country": entity.country_name_zh,
                "agreements": [a.model_dump(mode="json") for a in agreements],
                "living_cost": [as_json(p) for p in groups[0]],
                "housing": [as_json(p) for p in groups[1]],
                "courses": [as_json(p) for p in groups[2]],
                "experience": [as_json(p) for p in groups[3]],
            }, "src/exchange_info/cross_school_partners.py")
    else:
        census.errors.append({"scope": "cross_school", "error": "Incomplete home catalogues; no partial entity index accepted."})
    for path in sorted((ROOT / "src/exchange_info/editorial").glob("*.json")):
        census.add("_shared", "editorial", path.stem, json.loads(path.read_text("utf-8")), path.relative_to(ROOT).as_posix())
    for name in ("university_locations.jsonl", "school_content_supplements.json", "experience_digests_zh.json", "public_content_translations_zh.json"):
        path = BUNDLE / name
        if path.exists():
            rows = read_jsonl(path) if path.suffix == ".jsonl" else json.loads(path.read_text("utf-8"))
            if isinstance(rows, dict):
                rows = [{"mapping_key": key, "value": value} for key, value in rows.items()]
            for index, row in enumerate(rows):
                census.add("_shared", path.stem, str(index), row, path.relative_to(ROOT).as_posix())
    census.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inventory"])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--repository", type=Path, default=ROOT, help="Checkout to inspect, without modifying it.")
    args = parser.parse_args()
    ROOT = args.repository.resolve()
    BUNDLE = ROOT / "src/exchange_info/official_data"
    sys.path.insert(0, str(ROOT / "src"))
    if (args.output / "records.jsonl.gz").exists():
        parser.error("Output already contains a census; choose a new directory to preserve evidence.")
    inventory(args.output)
