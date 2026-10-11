"""Archive screening and exclusions for every newly acquired CCU source.

An HTTP 200, an exchange keyword, or a recent news date is never sufficient to
verify a receiving policy. Actual field decisions remain in the reviewed matrix.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

from fetch_ccu_completion_sources import BUNDLE as B, OUT

EXCLUSIONS = {
    "p34-campus-specific": "Incorrect candidate Q1321805 is Titán, not Nagoya University; excluded. Correct entity Q1191132 separately reviewed.",
    "p69-reference-folder-1": "Initial acquisition used a folder-child key shared by two parent folders. Preserve response but exclude ambiguous provenance; use p69-reference-link-N-file-M instead.",
    "p69-reference-folder-2": "Initial folder-child naming was not unique to the parent; use the exact parent-link child manifest instead.",
    "global-gamma": "Public Gamma HTML is an application shell without the full agreement list; denominator remains unknown.",
    "global-gamma-public-snapshot": "Anonymous public read rejected the query; no agreement content obtained.",
    "global-gamma-public-snapshot-preflight": "HTTP 200 body explicitly returns FORBIDDEN and data.doc=null; no agreement content obtained.",
    "p77-followup-photo-exact": "Campus-vtu.jpg was downloaded and visually reviewed: people-led posed photograph, not a readable campus exterior. Excluded; E-waste-lab.jpg separately verified.",
}


def main():
    used = defaultdict(set)
    for filename, groups in [("completion-reviewed-fields.json", ["host_fields", "profile_fields", "general_campus_fields"]),
                              ("campus-assets.json", ["coordinates", "photo"])]:
        for row in json.loads((B / filename).read_text())["schools"]:
            for group in groups:
                fields = row[group].values() if group.endswith("fields") else [row[group]]
                for field in fields:
                    for ev in field["evidence"]:
                        if ev.get("source_id"):
                            used[ev["source_id"]].add(field["status"])
    results = []
    for path in sorted(OUT.glob("*.receipt.json")):
        receipt = json.loads(path.read_text())
        sid = receipt.get("source_id") or path.name.removesuffix(".receipt.json")
        relative = receipt.get("bundled_file")
        if relative is None:
            candidates = [OUT / (sid + suffix) for suffix in [".html", ".json"]]
            file = next((p for p in candidates if p.exists()), None)
            relative = str(file.relative_to(B)) if file else None
        payload = (B / relative).read_bytes() if relative else None
        if payload is not None and relative.endswith(".gz"):
            if hashlib.sha256(payload).hexdigest() != receipt["stored_sha256"]:
                raise ValueError("Changed compressed archive " + sid)
            payload = gzip.decompress(payload)
        if payload is not None and receipt.get("sha256") != hashlib.sha256(payload).hexdigest():
            raise ValueError("Changed response bytes " + sid)
        title = (receipt.get("title") or "").casefold()
        if sid in EXCLUSIONS:
            decision, reason = "excluded_specific_review", EXCLUSIONS[sid]
        elif receipt.get("error") or receipt.get("http_status") != 200:
            decision, reason = "technical_failure", receipt.get("error") or "Non-200 response; not field evidence."
        elif any(term in title for term in ["anubis", "bot challenge", "not a bot", "making sure", "에러", "access denied", "processing", "just a moment"]):
            decision, reason = "challenge_or_error_page", "HTTP 200 challenge/error title is not university content."
        elif sid in used:
            decision, reason = "used_with_explicit_field_status", "Only the cited field, year, programme and campus are supported; no whole-source current-policy promotion."
        else:
            decision, reason = "acquired_not_policy_verified", "Not used to fill a current field; may be a navigation entry, unrelated news, host outbound route, archive or unreviewed candidate."
        if sid in used and decision != "used_with_explicit_field_status":
            raise ValueError("Excluded/unread source supports a published field: " + sid)
        results.append({"source_id": sid, "ccu_page": receipt.get("ccu_page"),
            "source_url": receipt["source_url"], "resolved_url": receipt.get("resolved_url"),
            "http_status": receipt.get("http_status"), "error": receipt.get("error"),
            "checked_at": receipt["checked_at"], "tls_verify": receipt["tls_verify"],
            "original_sha256": receipt.get("sha256"), "bundled_file": relative,
            "response_bytes_verified": payload is not None, "decision": decision,
            "field_statuses": sorted(used.get(sid, [])), "reason": reason})
    result = {"checked_at": "2026-10-11", "source_count": len(results),
              "decisions": dict(Counter(row["decision"] for row in results)),
              "photo_exclusions": json.loads((B / "campus-photo-review.json").read_text())["initial_exclusions"],
              "sources": results}
    (B / "completion-public-source-screening.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ["source_count", "decisions"]}, indent=2))


if __name__ == "__main__":
    main()
