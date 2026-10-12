"""Verify portable NTU source bodies, quotation pages and the historic 59-body handoff.

Read-only, offline. Download every archive part listed in the current manifest
into sources/ntu before running this script from the checkout.
"""
from contextlib import ExitStack
from io import BytesIO
import hashlib
import json
from pathlib import Path
import re
import zipfile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources/ntu"


def verify():
    manifest = json.loads((SOURCES / "reviewed-source-bodies-current-manifest.json").read_text())
    snapshot = json.loads((SOURCES / "completion-2026-10-11.json").read_text())
    # A URL/source ID can have several archived bodies. Join by the original
    # raw SHA as well, so rechecking a URL never erases its previous version.
    entries = {(entry["source_id"], entry["sha256"]): entry for entry in manifest["entries"]}
    assert len(entries) == manifest["source_count"] >= 217
    stage2_path = SOURCES / "reviewed-source-bodies-stage2-manifest.json"
    if stage2_path.exists():
        stage2 = json.loads(stage2_path.read_text())
        assert stage2["source_count"] == 217
        assert all(entries[(e["source_id"], e["sha256"])] == e for e in stage2["entries"])
    normal = lambda text: re.sub(r"\s+", " ", text).strip()
    raw_pdf_page_fallbacks = 0
    manual_visual_pages = 0
    manual_visual_images = 0
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

        def page_text(archive, entry, page_number):
            nonlocal raw_pdf_page_fallbacks
            path = f"extractions/{entry['source_id']}.pages.json"
            if path in archive.namelist():
                pages = json.loads(archive.read(path))
                return next(p["text"] for p in pages if p["page"] == page_number)
            # Some older immutable parts saved only whole-document extraction.
            # Check the quoted page directly against their verified raw PDF.
            reader = PdfReader(BytesIO(archive.read(entry["archive_body_path"])))
            assert 1 <= page_number <= len(reader.pages)
            raw_pdf_page_fallbacks += 1
            return reader.pages[page_number - 1].extract_text() or ""
        for sid, review in snapshot["public_source_reviews"].items():
            entry = entries[(sid, review["sha256"])]
            archive = archives[entry["archive_file"]]
            quote = normal(review["original_quote"])
            assert len(quote.split()) <= 25
            assert quote in normal(archive.read(f"extractions/{sid}.txt").decode())
            if page_number := review.get("quote_pdf_page"):
                if review.get("quote_verification_method") == "manual_visual_rendered_pdf_with_transcription":
                    # Image-only PDFs retain their manual transcription and
                    # rendered-page evidence; do not invent extracted text.
                    matches = list((ROOT / "docs/ntu-completion-20261011").glob(
                        "stage*/evidence/" + review["visual_evidence_reference"]
                    ))
                    assert len(matches) == 1, sid
                    evidence_path = matches[0]
                    evidence = json.loads(evidence_path.read_text())
                    assert evidence["source_id"] == sid and evidence["raw_pdf_sha256"] == entry["sha256"]
                    assert evidence["quote_pdf_page"] == page_number
                    assert normal(evidence["manually_transcribed_quote"]) == quote
                    transcription_sha = hashlib.sha256((evidence["manually_transcribed_quote"] + "\n").encode()).hexdigest()
                    assert transcription_sha == evidence["transcription_sha256"] == review["visual_quote_transcription_sha256"]
                    visual_manifest = {item["file"]: item for item in json.loads(
                        (evidence_path.parent / "visual-evidence-manifest.json").read_text()
                    )}
                    assert 1 <= page_number <= len(evidence["evidence_files"])
                    for filename in evidence["evidence_files"]:
                        data = (evidence_path.parent / filename).read_bytes()
                        image = visual_manifest[filename]
                        assert len(data) == image["size_bytes"] and hashlib.sha256(data).hexdigest() == image["sha256"]
                        manual_visual_images += 1
                    manual_visual_pages += 1
                else:
                    assert quote in normal(page_text(archive, entry, page_number)), (sid, page_number)
        manual_path = SOURCES / "semantic-review-current-2026-10-11.json"
        manual = json.loads(manual_path.read_text()) if manual_path.exists() else []
        for row in manual:
            for source in row["sources"]:
                assert (source["source_id"], source["sha256"]) in entries
        home = json.loads((SOURCES / "home-selection-current-2026-10-11.json").read_text())
        entry = entries[(home["source_id"], home["sha256"])]
        assert normal(home["original_quote"]) in normal(page_text(archives[entry["archive_file"]], entry, home["quote_pdf_page"]))
    historical = json.loads((SOURCES / "reviewed-source-bodies-stage1-manifest.json").read_text())
    assert len(historical) == 59
    with zipfile.ZipFile(SOURCES / "reviewed-source-bodies-stage1-2026-10-11.zip") as archive:
        for entry in historical:
            assert hashlib.sha256(archive.read(entry["archive_path"])).hexdigest() == entry["sha256"]
    return {"current_bodies": len(entries), "reviewed_citations": len(snapshot["public_source_reviews"]),
            "distinct_source_ids": len({sid for sid, _ in entries}),
            "same_source_id_versions_preserved": True,
            "quote_pages_reextracted_from_verified_raw_PDF": raw_pdf_page_fallbacks,
            "manual_visual_quote_pages_checked": manual_visual_pages,
            "manual_visual_evidence_image_hashes_checked": manual_visual_images,
            "current_archive_parts": len(manifest["archive_files"]), "historical_bodies": len(historical),
            "home_source_citations_checked": 1,
            "manual_semantic_rows_checked": len(manual),
            "all_body_and_archive_hashes_match": True, "all_quote_pages_match": True,
            "historical_cached_read_has_not_been_backfilled_with_a_hash": True}


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))
