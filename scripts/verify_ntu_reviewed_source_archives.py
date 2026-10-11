"""Verify portable NTU source bodies, quotation pages and the historic 59-body handoff.

Read-only, offline. Download every archive part listed in the current manifest
into sources/ntu before running this script from the checkout.
"""
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources/ntu"


def verify():
    manifest = json.loads((SOURCES / "reviewed-source-bodies-current-manifest.json").read_text())
    snapshot = json.loads((SOURCES / "completion-2026-10-11.json").read_text())
    entries = {entry["source_id"]: entry for entry in manifest["entries"]}
    assert len(entries) == manifest["source_count"] >= 217
    stage2_path = SOURCES / "reviewed-source-bodies-stage2-manifest.json"
    if stage2_path.exists():
        stage2 = json.loads(stage2_path.read_text())
        assert stage2["source_count"] == 217
        assert all(entries[e["source_id"]] == e for e in stage2["entries"])
    normal = lambda text: re.sub(r"\s+", " ", text).strip()
    with ExitStack() as stack:
        archives = {}
        for part in manifest["archive_files"]:
            path = SOURCES / part["archive_file"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == part["sha256"], path
            archives[path.name] = stack.enter_context(zipfile.ZipFile(path))
        for entry in entries.values():
            body = archives[entry["archive_file"]].read(entry["archive_body_path"])
            assert len(body) == entry["size_bytes"]
            assert hashlib.sha256(body).hexdigest() == entry["sha256"], entry["source_id"]
        for sid, review in snapshot["public_source_reviews"].items():
            entry = entries[sid]
            assert entry["sha256"] == review["sha256"]
            archive = archives[entry["archive_file"]]
            quote = normal(review["original_quote"])
            assert len(quote.split()) <= 25
            assert quote in normal(archive.read(f"extractions/{sid}.txt").decode())
            if page_number := review.get("quote_pdf_page"):
                pages = json.loads(archive.read(f"extractions/{sid}.pages.json"))
                page = next(p for p in pages if p["page"] == page_number)
                assert quote in normal(page["text"]), (sid, page_number)
        manual_path = SOURCES / "semantic-review-current-2026-10-11.json"
        manual = json.loads(manual_path.read_text()) if manual_path.exists() else []
        for row in manual:
            for source in row["sources"]:
                assert entries[source["source_id"]]["sha256"] == source["sha256"]
        home = json.loads((SOURCES / "home-selection-current-2026-10-11.json").read_text())
        entry = entries[home["source_id"]]
        assert entry["sha256"] == home["sha256"]
        pages = json.loads(archives[entry["archive_file"]].read(f"extractions/{home['source_id']}.pages.json"))
        assert normal(home["original_quote"]) in normal(next(p["text"] for p in pages if p["page"] == home["quote_pdf_page"]))
    historical = json.loads((SOURCES / "reviewed-source-bodies-stage1-manifest.json").read_text())
    assert len(historical) == 59
    with zipfile.ZipFile(SOURCES / "reviewed-source-bodies-stage1-2026-10-11.zip") as archive:
        for entry in historical:
            assert hashlib.sha256(archive.read(entry["archive_path"])).hexdigest() == entry["sha256"]
    return {"current_bodies": len(entries), "reviewed_citations": len(snapshot["public_source_reviews"]),
            "current_archive_parts": len(manifest["archive_files"]), "historical_bodies": len(historical),
            "home_source_citations_checked": 1,
            "manual_semantic_rows_checked": len(manual),
            "all_body_and_archive_hashes_match": True, "all_quote_pages_match": True,
            "historical_cached_read_has_not_been_backfilled_with_a_hash": True}


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))
