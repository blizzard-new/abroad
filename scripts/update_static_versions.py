"""Record which version tag each static file is requested with, and refuse a changed file that kept its tag.

Static files requested with ?v= are cached for a year as immutable, so a file whose content changed but whose tag did not
is served stale to every returning visitor. Run this after editing any static JS or CSS and bumping its ?v= tag:

    python scripts/update_static_versions.py          # rewrite tests/static_asset_versions.json
    python scripts/update_static_versions.py --check  # exit 1 if the record is out of date (used by the test)
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src/exchange_info/static"
LOCK = ROOT / "tests/static_asset_versions.json"
SOURCES = [STATIC / "index.html", STATIC / "privacy.html", STATIC / "terms.html", STATIC / "app.js", ROOT / "src/exchange_info/seo.py"]
REFERENCE = re.compile(r"/static/([A-Za-z0-9_./-]+\.(?:js|css))\?v=([A-Za-z0-9._-]+)")


def current() -> dict:
    found: dict[str, set[str]] = {}
    for source in SOURCES:
        for path, tag in REFERENCE.findall(source.read_text(encoding="utf-8")):
            found.setdefault(path, set()).add(tag)
    state = {}
    for path, tags in sorted(found.items()):
        file = STATIC / path
        if file.is_file():
            state[path] = {"v": sorted(tags), "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
    return state


def stale(recorded: dict, now: dict) -> list[str]:
    """Files whose content changed while the tag stayed the same: the one mistake that serves visitors old code."""
    return [path for path, entry in now.items() if path in recorded
            and recorded[path]["sha256"] != entry["sha256"] and recorded[path]["v"] == entry["v"]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    now = current()
    recorded = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    unbumped = stale(recorded, now)
    if unbumped:
        print("Changed without a new ?v= tag (returning visitors would keep the old file):\n  " + "\n  ".join(unbumped))
        return 1
    if args.check:
        if recorded != now:
            print("tests/static_asset_versions.json is out of date: run python scripts/update_static_versions.py")
            return 1
        return 0
    LOCK.write_text(json.dumps(now, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Recorded {len(now)} static files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
