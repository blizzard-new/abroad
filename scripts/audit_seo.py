"""Audit bundled catalogue quality without changing data, robots or sitemap membership."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from exchange_info.cgu_catalogue import create_cgu_catalogue
from exchange_info.seo_quality import audit_catalogues
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES


def bundled_catalogues():
    with TemporaryDirectory(prefix="uniway-seo-audit-") as directory:
        for university in SUPPORTED_UNIVERSITIES:
            if university.id == "cgu":
                partners = create_cgu_catalogue(Path(directory)).view(refresh=False).partners
            else:
                module = importlib.import_module(f"exchange_info.{university.id}_student_view")
                partners = getattr(module, f"fetch_{university.id}_partner_universities")()
            yield university, partners


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit_catalogues(bundled_catalogues())
    report["scope"] = "Bundled source snapshot; excludes unpublished drafts and runtime research overlays. Not a live Google report."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("mode", "page_count", "tiers", "scope")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
