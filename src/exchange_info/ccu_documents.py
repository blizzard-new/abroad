"""Individually sourced CCU receiving documents with program and stage labels."""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from urllib.parse import unquote

from .ccu_sources import BUNDLE
from .models import (
    ApplicationDocumentRequirement,
    ApplicationStep,
    ApplicationSubmissionMethod,
)


@lru_cache(maxsize=1)
def reviewed_documents() -> dict[int, dict]:
    rows = json.loads((BUNDLE / "partner-document-requirements.json").read_text())
    if len({r["ccu_page"] for r in rows}) != len(rows):
        raise ValueError("Duplicate CCU document school")
    for row in rows:
        names = set()
        for item in row["requirements"]:
            applicability = item.get("applicability_status", row["status"])
            if applicability not in {"verified_current", "needs_confirmation", "reference_only"}:
                raise ValueError("Invalid CCU document applicability")
            if applicability == "verified_current" and not any(
                ev["status"] == "verified_current" for ev in item["evidence"]
            ):
                raise ValueError("Current CCU document requires current evidence")
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
                if source.get("access_result") in {
                    "unrelated_content_anomaly", "challenge_page", "captcha_required", "empty_response"
                }:
                    raise ValueError("CCU document evidence is not readable official content")
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
                if ev["status"] not in {"verified_current", "needs_confirmation", "reference_only"}:
                    raise ValueError("CCU document status disagreement")
            url = requirement.official_form_url
            if url and not re.match(r"https?://", url):
                raise ValueError("CCU official forms must use public HTTP URLs")
    return {row["ccu_page"]: row for row in rows}


@lru_cache(maxsize=1)
def verified_form_urls() -> set[str]:
    registry = json.loads((BUNDLE / "overseas-source-registry.json").read_text())
    result = set()
    for entry in registry:
        if entry.get("status") not in {"pdf", "docx", "xls", "xlsx", "doc"}:
            continue
        source = json.loads(
            (BUNDLE / "overseas_sources" / (entry["source_id"] + ".json")).read_text()
        )
        file = source.get("bundled_file")
        if (
            file
            and hashlib.sha256((BUNDLE / file).read_bytes()).hexdigest()
            == source["sha256"]
        ):
            result.add(unquote(source["source_url"].split("#")[0]))
    return result


def enrich_documents(workflow, partner):
    row = reviewed_documents().get(partner.source_pages[0])
    if not row:
        return
    if row["school_name"] != partner.school_name:
        raise ValueError("CCU document school identity mismatch")
    if row["status"] not in {"verified_current", "needs_confirmation", "reference_only"}:
        raise ValueError(
            "CCU documents require a reviewed applicability status"
        )
    application = workflow.steps[4]
    application.document_requirements = []
    application.required_documents = []
    life = next(step for step in workflow.steps if step.phase == "合作校行前與生活")
    targets = {
        "student_application": application,
        "conditional_program": application,
        "post_offer": life,
        "after_dorm_assignment": life,
        "nomination": workflow.steps[3],
    }
    if any(item["stage"] == "after_application" for item in row["requirements"]):
        after = ApplicationStep(
            order=6,
            phase="合作校申請後補件（不等錄取）",
            title="申請送出後依期限補件，不等待錄取通知",
            responsible_party="學生／合作校",
            summary="這一階段是申請後補件，與錄取後不同；依逐項原文及校方通知辦理。",
            scope=application.scope,
            support_status="needs_confirmation",
            needs_confirmation=True,
            checked_at=application.checked_at,
            confirmation_contact=application.confirmation_contact,
        )
        workflow.steps.insert(5, after)
        targets["after_application"] = after
        if partner.source_pages[0] == 53:
            after.timing = (
                "2026-12-20上傳；2027-01-15正本送達；錄取信12月底另發，不能等錄取才補件"
            )
        elif partner.source_pages[0] == 47:
            after.timing = (
                "申請期間結束後由校方另發財力表，未載確切補件日；不以錄取通知當作起點"
            )
    if any(item["stage"] == "second_submission" for item in row["requirements"]):
        second = ApplicationStep(
            order=6,
            phase="合作校第二次文件送件",
            title="依提名後通知完成第二次文件送件",
            responsible_party="學生／合作校",
            summary="2027春季factsheet分第一、第二次送件；第二次日期與啟動條件未載。",
            timing="第二次繳韓國簽證copy、航班及銀行證明；未載確切補件日，不猜錄取前後",
            scope=application.scope,
            support_status="needs_confirmation",
            needs_confirmation=True,
            checked_at=application.checked_at,
            confirmation_contact=application.confirmation_contact,
        )
        workflow.steps.insert(5, second)
        targets["second_submission"] = second
    for item in row["requirements"]:
        requirement = ApplicationDocumentRequirement.model_validate(
            dict(
                item["requirement"],
                stage=item["stage"],
                conditional=item["conditional"],
                condition=item.get("condition")
                or (item["requirement"]["name"] if item["conditional"] else None),
                official_form_verified=bool(
                    item["requirement"]["official_form_url"]
                    and unquote(item["requirement"]["official_form_url"].split("#")[0])
                    in verified_form_urls()
                ),
                applicability_status=item.get("applicability_status", row["status"]),
                applicability_year=item.get("applicability_year", item["evidence"][0]["academic_year"]),
                applicability_note=item.get("applicability_note"),
            )
        )
        target = targets[item["stage"]]
        target.document_requirements.append(requirement)
        ev = item["evidence"][0]
        pages = (
            "；PDF第" + "、".join(map(str, ev["source_pages"])) + "頁"
            if ev["source_pages"]
            else "；官方原文"
        )
        target.details.append(
            f"{requirement.name} · 階段{item['stage']}；{ev['academic_year']}{pages}；查核2026-10-08"
        )
        target.source_urls = list(
            dict.fromkeys([*target.source_urls, *requirement.source_urls])
        )
    application.details.append(row["review_note"])
    if row.get("submission_method") == "home_compiled_email":
        nomination = targets["nomination"]
        nomination.title = "母校彙整七項提名資料，以email寄合作校"
        nomination.responsible_party = "學生準備／母校國際事務處彙整與email送件"
        nomination.summary = "母校彙整五項必備與兩項選附資料，寄送提名信至factsheet列明聯絡人之一。"
        application.title = "準備資料交母校彙整，由母校以email送件"
        application.summary = "合作校公開factsheet由母校彙整學生整包資料並寄送提名信；未載學生自行線上申請步驟。"
        application.responsible_party = "學生準備／母校彙整與email送件"
        for step in (nomination, application):
            step.submission = step.submission.model_copy(update={
                "method": ApplicationSubmissionMethod.EMAIL,
                "office": "母校國際事務處彙整與寄送；合作校國際事務處收件",
                "email": "oia@hcmute.edu.vn",
                "portal_url": None,
            })
    elif row.get("submission_method") == "online_generated_pdf_then_home_signature_email":
        application.title = "線上申請後列印PDF，由母校簽名再掃描email"
        application.summary = "公開程序依序要求online申請、列印自動產生的PDF交母校coordinator簽名，再掃描email；流程年度及個人欄位待確認。"
        application.responsible_party = "學生申請／母校coordinator簽名／學生掃描email"
    for order, step in enumerate(workflow.steps, 1):
        step.order = order
        step.required_documents = [r.name for r in step.document_requirements]
        step.official_form_urls = list(
            dict.fromkeys(
                r.official_form_url
                for r in step.document_requirements
                if r.official_form_url
            )
        )
        step.signature_requirements = list(
            dict.fromkeys(
                name for r in step.document_requirements for name in r.signatures
            )
        )
