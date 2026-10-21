"""Withdraw specifically reviewed generated claims, preserving source candidates.

Input fingerprints bound this correction to inspected templates. Independently
edited or newly read source material is not overwritten by a blanket policy.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic

MANIFEST = "docs/data-verification-20261021/round19-template-provenance.json"
MANIFEST_SHA = "cb465212f952e23a693e7da0e70e4fe762df3a50e75ba39896ab60b8d7ea7140"
ROUND20_MANIFEST = "docs/data-verification-20261021/round20-template-provenance.json"
ROUND20_MANIFEST_SHA = "ecb6ea5ff2003bb837eb66225b33363bff9d4faf683d34e192c976fe25a6f7cd"
ROUND21_MANIFEST = "docs/data-verification-20261021/round21-life-provenance.json"
ROUND21_MANIFEST_SHA = "50c053d56409efa680f24e2a2153866c6bab7b979459641c89c0937907e96129"
ROUND22_MANIFEST = "docs/data-verification-20261021/round22-life-provenance.json"
ROUND22_MANIFEST_SHA = "9364b608728fe4a11e88b5203eb835ce44bf75139e8da518df7dce3e3e308192"
STORY_NOTE = "僅保留原有心得候選連結；原文尚待逐篇核對，目前沒有可核實的全文摘要。"
PROGRAM_NOTE = "此連結來自錄取或獎助紀錄，不屬於學生生活心得；名單原文與個別紀錄仍待核對。"
LIFE_NOTE = "原有共用範本與國家預設費用尚未逐校核對原文，暫不作生活證據；原始連結及文字留存待查。"


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_manifest(root, *, round_id=19):
    path, expected = {19: (MANIFEST, MANIFEST_SHA),
        20: (ROUND20_MANIFEST, ROUND20_MANIFEST_SHA),
        21: (ROUND21_MANIFEST, ROUND21_MANIFEST_SHA),
        22: (ROUND22_MANIFEST, ROUND22_MANIFEST_SHA)}[round_id]
    raw = (root / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Generated-content provenance manifest hash mismatch")
    return json.loads(raw)


def review_generated_content(root: Path, school: str, *, round_id=19):
    manifest = load_manifest(root, round_id=round_id)
    scope = manifest["schools"][school]
    folder = root / "src/exchange_info/official_data" / school
    read_rows = lambda name: [json.loads(line) for line in (folder / name).read_text("utf8").splitlines() if line.strip()]
    counts = {"stories_changed": 0, "life_changed": 0, "digests_changed": 0}
    story_claims = {(r["school_name"], r["source_url"], r["claim_sha256"]): r for r in scope["stories"]}
    stories = read_rows("student_experiences.jsonl") if scope["stories"] else []
    for row in stories:
        old = {key: row.get(key) for key in manifest["story_fields"]}
        claim = story_claims.get((row["school_name"], row["source_url"], digest(old)))
        if claim is None:
            continue
        row.setdefault("reference_data", {}).setdefault("generated_claims_before_review", old)
        row.update(title=f"{row['school_name']}：原有心得連結待核對", author_name=None,
            summary=STORY_NOTE, summary_zh=STORY_NOTE, original_summary="", themes=[],
            theme_summaries={}, theme_summaries_zh={}, content_status="metadata_only",
            perspective="official_directory", source_kind="other", exchange_term=None)
        if claim.get("action") == "exclude_program_record":
            row.update(title=f"{row['school_name']}：錄取或獎助紀錄待核對",
                summary=PROGRAM_NOTE, summary_zh=PROGRAM_NOTE,
                perspective="official_program_record", source_kind="official_record")
        elif claim.get("action") == "retain_official_excerpt":
            row.update(claim["reviewed_excerpt"])
            row.update(summary_zh=row["summary"], perspective="official_student_story",
                source_kind="personal_story")
            row.setdefault("reference_data", {})["excerpt_review"] = claim["evidence"]
        # A PDF link is still an article source in the existing public model.
        # The original format is retained above; it does not imply PDF reading.
        if row["source_type"] == "pdf":
            row["source_type"] = "article"
        row["content_hash"] = digest([row["school_name"], row["source_url"], "metadata_only", row["summary"]])
        counts["stories_changed"] += 1
    if scope["stories"]:
        write_atomic(folder / "student_experiences.jsonl", stories, True)

    life_hashes = {(r["school_name"], r["country"], value) for r in scope["life"]
        for value in (r["evidence_sha256"], r.get("baseline_evidence_sha256", r["evidence_sha256"]))}
    life = read_rows("student_life.jsonl") if scope["life"] else []
    for row in life:
        if (row["school_name"], row.get("country"), digest(row["evidence"])) not in life_hashes:
            continue
        old = {key: row.get(key) for key in ("evidence", "status", "notes", "checked_at")}
        row.setdefault("reference_data", {}).setdefault("generated_life_before_review", old)
        note = ("原內容混有共用範本、母校專屬規則與尚待逐校核對的摘錄；暫不作跨校共用生活證據，原文及連結保留待查。"
            if round_id in {21, 22} else LIFE_NOTE)
        row.update(evidence=[], status="partial", notes=[note], checked_at=manifest["reviewed_at"])
        counts["life_changed"] += 1
    if scope["life"]:
        write_atomic(folder / "student_life.jsonl", life, True)

    path = folder / "student-experience-digests.json"
    if scope["digests"] and path.exists():
        digests = json.loads(path.read_text("utf8"))
        hashes = {r["key"]: r["claims_sha256"] for r in scope["digests"]}
        for key, row in digests["digests"].items():
            old = {field: row.get(field) for field in ("summary_zh", "themes", "report_count")}
            if hashes.get(key) != digest(old):
                continue
            row.setdefault("reference_data", {}).setdefault("generated_claims_before_review", old)
            row.update(report_count=0, summary_zh=STORY_NOTE, themes={}, status="needs_confirmation", updated_at=manifest["reviewed_at"])
            counts["digests_changed"] += 1
        write_atomic(path, digests)
    return counts
