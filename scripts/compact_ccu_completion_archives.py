"""Losslessly archive CCU response bodies without relabelling their hashes.

Keep acquisition digests over original server bytes. Repair binary responses
incorrectly treated as HTML candidates and discard only their bogus derived text.
No pre-existing official evidence is touched.
"""
from __future__ import annotations

import gzip
import hashlib
import json

from fetch_ccu_completion_sources import BUNDLE as B, OUT


def main():
    log = []
    for path in sorted(OUT.glob("*.receipt.json")):
        receipt = json.loads(path.read_text())
        if not receipt.get("source_id"):
            continue  # Independently acquired home documents use their original receipts.
        file = B / receipt.get("bundled_file", "NOFILE")
        if not file.is_file():
            continue
        if file.suffix == ".gz":
            compressed = file.read_bytes()
            if (hashlib.sha256(compressed).hexdigest() != receipt["stored_sha256"]
                    or hashlib.sha256(gzip.decompress(compressed)).hexdigest() != receipt["sha256"]):
                raise ValueError(f"Changed CCU compressed body {path.name}")
            log.append({"source_id": receipt["source_id"], "original_sha256": receipt.get("sha256"),
                        "bundled_file": receipt.get("bundled_file"), "archive_encoding": receipt.get("archive_encoding"),
                        "format_review_note": receipt.get("format_review_note")})
            continue
        raw = file.read_bytes()
        if receipt.get("sha256") and hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
            raise ValueError(f"Changed CCU acquisition body {path.name}")
        if file.suffix == ".html" and (raw.startswith(b"%PDF-") or raw.startswith(b"PK") or raw.startswith(b"\xd0\xcf\x11\xe0")):
            suffix = ".pdf" if raw.startswith(b"%PDF-") else ".zip" if raw.startswith(b"PK") else ".doc"
            target = file.with_suffix(suffix)
            if target.exists() and target.read_bytes() != raw:
                raise ValueError(f"Non-identical duplicate {target}")
            target.write_bytes(raw)
            file.unlink()
            text = file.with_suffix(".txt")
            if text.exists():
                text.unlink()  # Binary-as-HTML garbage is not source evidence.
            receipt.pop("text_sha256", None)
            receipt.pop("title", None)
            receipt.pop("links", None)
            receipt["format_review_note"] = "Preserved original bytes/hash; detected binary signature. Bogus HTML text extraction removed."
            receipt["bundled_file"] = str(target.relative_to(B))
            file = target
        if file.suffix == ".html":
            target = file.with_suffix(".html.gz")
            compressed = gzip.compress(raw, mtime=0)
            target.write_bytes(compressed)
            if gzip.decompress(target.read_bytes()) != raw:
                raise ValueError("Lossless archival check failed")
            file.unlink()
            receipt["bundled_file"] = str(target.relative_to(B))
            receipt["archive_encoding"] = "gzip; sha256 is over original HTTP response bytes"
            receipt["stored_sha256"] = hashlib.sha256(compressed).hexdigest()
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        log.append({"source_id": receipt["source_id"], "original_sha256": receipt.get("sha256"),
                    "bundled_file": receipt.get("bundled_file"), "archive_encoding": receipt.get("archive_encoding"),
                    "format_review_note": receipt.get("format_review_note")})
    if log:
        (B / "completion-archive-layout.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print("archive layout records", len(log))


if __name__ == "__main__":
    main()
