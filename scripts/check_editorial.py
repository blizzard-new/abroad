#!/usr/bin/env python3
"""Offline editorial release gate; source claims still require reading primary sources."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.seo_articles import ARTICLES, render_article  # noqa: E402


def meaningful_content(data: dict) -> dict:
    # Source rechecks alone must not refresh Google's content modification date.
    return {k: v for k, v in data.items() if k not in {"checked", "modified"}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", help="Compare material revisions and lastmod with a Git base, e.g. origin/main")
    args = parser.parse_args()
    errors, report = [], []
    if args.base_ref:
        base = subprocess.run(["git", "rev-parse", "--verify", args.base_ref + "^{commit}"], cwd=ROOT, capture_output=True, text=True)
        if base.returncode:
            parser.error("base-ref is not an available commit")
        base_sha = base.stdout.strip()
    for slug, article in ARTICLES.items():
        soup = BeautifulSoup(render_article(article), "html.parser")
        body = soup.select_one(".article-body")
        text_length = len(body.get_text("", strip=True))
        if text_length < 1500:
            errors.append(f"{slug}: article is too thin; write useful original content, not filler")
        for table in body.select("table"):
            if not table.caption or not table.select("th[scope=col]"):
                errors.append(f"{slug}: table needs a caption and column headers")
        asset = ROOT / "src/exchange_info" / article.image_path.lstrip("/")
        if not asset.is_file():
            errors.append(f"{slug}: missing illustration {asset.name}")
            asset_bytes = 0
        else:
            asset_bytes = asset.stat().st_size
            with Image.open(asset) as image:
                if image.format != "WEBP" or image.size != (1536, 1024):
                    errors.append(f"{slug}: use 1536×1024 WebP to match image metadata")
            if asset_bytes > 450_000:
                errors.append(f"{slug}: illustration exceeds 450 KB; optimize encoding")
        if args.base_ref:
            path = f"src/exchange_info/editorial/{slug}.json"
            previous = subprocess.run(["git", "show", base_sha + ":" + path], cwd=ROOT, capture_output=True, text=True)
            if previous.returncode == 0:
                old, new = json.loads(previous.stdout), article.model_dump(mode="json")
                changed = meaningful_content(old) != meaningful_content(new)
                if old["published"] != new["published"]:
                    errors.append(f"{slug}: preserve the original publication date")
                if changed and new["modified"] < old["modified"]:
                    errors.append(f"{slug}: modification date cannot move backwards")
                if not changed and old["modified"] != new["modified"]:
                    errors.append(f"{slug}: do not refresh lastmod without material changes")
                # Date precision permits multiple real edits on the same day.
                if changed and new["modified"] == old["modified"]:
                    from datetime import datetime
                    from zoneinfo import ZoneInfo
                    if new["modified"] != datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat():
                        errors.append(f"{slug}: material change needs its actual modification date")
        report.append({"slug": slug, "body_characters": text_length, "sources": len(article.sources),
                       "illustration_bytes": asset_bytes, "modified": str(article.modified)})
    print(json.dumps({"ok": not errors, "article_count": len(report), "articles": report, "errors": errors,
                      "scope": "Editorial structure/assets/revision dates; not proof of factual accuracy, indexing or rankings"}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
