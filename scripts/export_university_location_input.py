"""Export public, current partnership identities for offline coordinate enrichment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

from exchange_info.settings import DEFAULT_DATA_DIR
from exchange_info.storage import load_partner_research


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8767")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    research = load_partner_research(args.data_dir, include_bundled_baseline=True)
    universities = requests.get(base + "/universities", timeout=90)
    universities.raise_for_status()
    rows = {}
    for university in universities.json():
        school = university["school_name"]
        response = requests.get(base + "/student-dashboard", params={"school": school}, timeout=90)
        response.raise_for_status()
        for partner in response.json()["partner_universities"]:
            match = next((r for r in research if r.school_name == partner["school_name"] and r.home_university == school), None)
            row = {
                "school_name": partner["school_name"], "country": partner.get("country"),
                "website": (match.official_website if match else None) or partner.get("website"),
                "research_name": match.research_name if match else None,
            }
            rows[(row["school_name"], row["country"])] = row
        home = {"school_name": school, "country": "臺灣", "website": university.get("official_url"), "research_name": university.get("english_name")}
        rows[(school, "臺灣")] = home
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(list(rows.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"Exported {len(rows)} public location identities to {args.output}")


if __name__ == "__main__":
    main()
