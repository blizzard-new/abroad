"""Individually sourced CCU receiving documents with program and stage labels."""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache

from .ccu_sources import BUNDLE
from .models import ApplicationDocumentRequirement


@lru_cache(maxsize=1)
def reviewed_documents() -> dict[int, dict]:
    rows = json.loads((BUNDLE / "partner-document-requirements.json").read_text())
    if len({r["ccu_page"] for r in rows}) != len(rows):
        raise ValueError("Duplicate CCU document school")
    for row in rows:
        names = set()
        for item in row["requirements"]:
            requirement = ApplicationDocumentRequirement.model_validate(
                item["requirement"]
            )
            if requirement.name in names or not item["evidence"]:
                raise ValueError("Duplicate or unsourced CCU document requirement")
            names.add(requirement.name)
            for ev in item["evidence"]:
                source = json.loads(
                    (
                        BUNDLE / "overseas_sources" / (ev["source_id"] + ".json")
                    ).read_text()
                )
                text_hash = hashlib.sha256(
                    json.dumps(
                        source.get("text_pages", []), ensure_ascii=False
                    ).encode()
                ).hexdigest()
                if (
                    source.get("sha256") != ev["content_hash"]
                    or text_hash != ev["text_sha256"]
                ):
                    raise ValueError("Changed CCU document evidence")
                if (
                    source.get("bundled_file")
                    and hashlib.sha256(
                        (BUNDLE / source["bundled_file"]).read_bytes()
                    ).hexdigest()
                    != source["sha256"]
                ):
                    raise ValueError("Changed CCU document attachment")
                pages = ev["source_pages"] or range(1, len(source["text_pages"]) + 1)
                text = " ".join(
                    " ".join(source["text_pages"][p - 1].split()) for p in pages
                )
                if not ev["excerpt"] or " ".join(ev["excerpt"].split()) not in text:
                    raise ValueError("CCU document excerpt absent from source")
                if not all(
                    ev.get(k) for k in ["source_url", "academic_year", "checked_at"]
                ):
                    raise ValueError("Missing CCU document provenance")
                if ev["status"] != row["status"]:
                    raise ValueError("CCU document status disagreement")
            url = requirement.official_form_url
            if url and not re.match(r"https?://", url):
                raise ValueError("CCU official forms must use public HTTP URLs")
    return {row["ccu_page"]: row for row in rows}


def enrich_documents(step, partner):
    row = reviewed_documents().get(partner.source_pages[0])
    if not row:
        return
    if row["school_name"] != partner.school_name:
        raise ValueError("CCU document school identity mismatch")
    if partner.partner_exchange_details["documents"].status != "verified_current":
        raise ValueError(
            "Do not turn historical CCU documents into current requirements"
        )
    step.document_requirements = [
        ApplicationDocumentRequirement.model_validate(item["requirement"])
        for item in row["requirements"]
    ]
    step.required_documents = [r.name for r in step.document_requirements]
    step.official_form_urls = list(
        dict.fromkeys(
            r.official_form_url
            for r in step.document_requirements
            if r.official_form_url
        )
    )
    step.signature_requirements = list(
        dict.fromkeys(name for r in step.document_requirements for name in r.signatures)
    )
    step.details.append(row["review_note"])
    # The current registry explicitly keeps partial lists, conditional routes and
    # later upload/post deadlines; publication remains a separate review process.
    for item in row["requirements"]:
        ev = item["evidence"][0]
        pages = (
            "；PDF第" + "、".join(map(str, ev["source_pages"])) + "頁"
            if ev["source_pages"]
            else "；官方原文"
        )
        step.details.append(
            f"{item['requirement']['name']} · 階段{item['stage']}；{ev['academic_year']}{pages}；查核2026-10-08"
        )
