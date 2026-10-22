"""SCU degree scope comes from the explicit degree line, never a broad default."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .host_source_review_round25 import apply_review_manifest

MANIFEST = "docs/data-verification-20261021/round29-scu-degree-source-review.json"
MANIFEST_SHA256 = "ee51e3bcc2036621064d8674f87d54e33527abb6232349f6d8d96cb91ce2a41b"

DEGREE_SCOPES = {
    "學士、研究生": "學士／研究生（東吳原表未分碩、博士；具體接收學制待確認）",
    "僅受理學士生申請": "大學部（僅學士生可申請）",
    "僅受理碩士生申請": "碩士班（僅碩士生可申請）",
    "目前學士二年級、研究所一年級(含)以上之學生": "申請時學士二年級以上／研究所一年級以上（原表未分碩、博士）",
}


def degree_scope(first_eligibility_line: str) -> str:
    first_sentence = re.sub(r"\s+", "", first_eligibility_line.split("。", 1)[0])
    if first_sentence not in DEGREE_SCOPES:
        raise ValueError(f"SCU degree wording needs source review: {first_sentence}")
    return DEGREE_SCOPES[first_sentence]


def load_manifest(root: Path):
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("SCU degree source-review manifest hash mismatch")
    return json.loads(raw)


def apply_scu_degree_source_review(root: Path):
    return apply_review_manifest(root, "scu", load_manifest(root), "source_review_round29")
