"""Apply only CCU/Sungshin's reviewed Spring2027 receiving correction.

The original mirror and mother rules remain archived. Normal source validation
also verifies every current checklist/template response before exposing it.
"""
from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache

from .ccu_completion_sources import validate_completion_source
from .ccu_sources import BUNDLE
from .models import ApplicationDocumentRequirement, ApplicationSubmissionMethod


@lru_cache(maxsize=1)
def reviewed_sungshin_documents():
    row = json.loads((BUNDLE / "completion-sungshin-documents.json").read_text())
    if row["ccu_page"] != 49 or row["academic_year"] != "Spring2027":
        raise ValueError("Unexpected Sungshin programme/year")
    checked = {}
    names = set()
    for item in row["requirements"]:
        requirement = ApplicationDocumentRequirement.model_validate(item["requirement"])
        if requirement.name in names or not item["evidence"]:
            raise ValueError("Duplicate or unsourced Sungshin requirement")
        names.add(requirement.name)
        for ev in item["evidence"]:
            validate_completion_source(BUNDLE, ev, checked)
    for ev in row["evidence"]:
        validate_completion_source(BUNDLE, ev, checked)
    if len(names) != 9:
        raise ValueError("Sungshin checklist requires nine distinct entries")
    return row


def apply_sungshin_summary(partner):
    if partner.source_pages[0] != 49:
        return partner
    row = reviewed_sungshin_documents()
    if partner.school_name != row["school_name"]:
        raise ValueError("Sungshin identity mismatch")
    partner.reference_data["ccu_sungshin_superseded_summary"] = json.dumps({
        "semester_dates": partner.semester_dates,
        "partner_application_deadline": partner.partner_application_deadline,
        "source_id": "p49-mirror", "status": "superseded_by_official_spring2027_call",
    }, ensure_ascii=False)
    fields = partner.partner_exchange_details
    partner.semester_dates = fields["academic_calendar"].value
    partner.partner_application_deadline = fields["application_deadline"].value
    partner.student_summary_zh.study_period = (partner.study_period or "") + "；" + partner.semester_dates
    partner.student_summary_zh.application_deadline = partner.partner_application_deadline
    # This is the receiving school's calendar/deadline, never the closed home window.
    for key, detail in [("semester_dates", "academic_calendar"), ("partner_application_deadline", "application_deadline")]:
        if key in partner.field_evidence:
            ev = fields[detail].evidence[0]
            partner.field_evidence[key] = ev.model_copy(update={"note": fields[detail].reason})
    return partner


def enrich_sungshin_workflow(workflow, partner):
    if partner.source_pages[0] != 49:
        return
    row = reviewed_sungshin_documents()
    if partner.school_name != row["school_name"]:
        raise ValueError("Sungshin workflow identity mismatch")
    application = next(step for step in workflow.steps if step.phase == "合作校申請")
    application.document_requirements = [ApplicationDocumentRequirement.model_validate(item["requirement"])
                                         for item in row["requirements"]]
    application.required_documents = [r.name for r in application.document_requirements]
    application.signature_requirements = list(dict.fromkeys(s for r in application.document_requirements for s in r.signatures))
    application.official_form_urls = [r.official_form_url for r in application.document_requirements if r.official_form_url]
    application.source_urls = list(dict.fromkeys([*application.source_urls, *[e["source_url"] for e in row["evidence"]]]))
    for note in [row["review_note"], "前7項須線上上傳與母校整包郵寄，照片只線上、語言證明optional。公開手冊不代表個人帳號內已核實全部欄位。"]:
        if note not in application.details:
            application.details.append(note)
    application.summary = "依Spring2027官方checklist準備8項必備與1項選附，線上與郵寄並行；健康追加文件差異待校方確認。"
    application.checked_at = datetime.fromisoformat(row["checked_at"])
    workflow.last_checked = application.checked_at
    for ev in [*row["evidence"], *[e for item in row["requirements"] for e in item["evidence"]]]:
        for source in workflow.sources:
            if source.source_url == ev["source_url"]:
                source.content_hash = ev["content_hash"]
    application.submission = application.submission.model_copy(update={
        "method": ApplicationSubmissionMethod.MIXED, "address": row["postal_address"],
        "office": "Sungshin Office of International Affairs and Services；由中正彙整郵寄",
        "portal_url": "https://tis.sungshin.ac.kr/comm/nxui/member/join.do?join=9",
        "deadline_note": "線上2026-10-26至11-23；正本2026-11-23抵校，未載時刻，不產生午夜提醒。",
    })
