"""Reviewed receiving-school evidence for CCU; never promote an unversioned PDF."""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache

from .ccu_sources import (
    BUNDLE,
    CHECKED_AT,
    HOME,
    describe_evidence,
    describe_evidence_list,
    require_usable_source,
)
from .models import (
    ApplicationDocumentRequirement,
    ApplicationStep,
    ApplicationWorkflowSource,
    DestinationProfile,
    ExchangeFieldEvidence,
    PageCategory,
    PartnerExchangeDetailField,
    PartnerLanguageCondition,
    PartnerUniversity,
    SourceReference,
    StudentGuideSection,
)

LABELS = {
    "program_scope": "接收計畫、學制及校區",
    "eligibility": "合作校接收資格",
    "language": "合作校語言條件與替代證明",
    "nomination_deadline": "合作校提名截止",
    "application_deadline": "合作校申請截止",
    "documents": "合作校文件要求（僅列已核實項目）",
    "application_forms": "合作校申請表取得方式",
    "academic_calendar": "合作校校曆及考試",
    "course_restrictions": "課程與學分限制",
    "housing": "住宿與床位",
    "housing_deadline": "住宿申請／付款截止",
    "costs": "住宿與生活費用",
    "insurance": "保險",
    "visa": "簽證與居留",
    "arrival": "抵達與迎新",
    "host_tuition": "合作校學費",
    "exchange_duration": "交換期間及延長限制",
}
STATUS_LABELS = {
    "verified_current": "當期已核實",
    "reference_only": "其他年度／梯次參考，不能作本期申請依據",
    "missing": "本期未核實／來源未載",
    "needs_confirmation": "適用年度或條件待確認",
    "conflict": "來源矛盾，待確認",
    "explicit_not_announced": "官方明示尚未公告",
}


def _flat(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


@lru_cache(maxsize=1)
def reviewed_rows() -> dict[int, dict]:
    rows = json.loads((BUNDLE / "overseas-reviewed-fields.json").read_text())
    if len(rows) != 55 or len({r["ccu_page"] for r in rows}) != 55:
        raise ValueError(
            "CCU overseas review must cover all 55 current/quota-unknown identities"
        )
    for row in rows:
        if set(row["fields"]) != set(LABELS):
            raise ValueError(f"CCU incomplete field matrix: {row['ccu_page']}")
        for field in row["fields"].values():
            if field["status"] == "verified_current" and (
                not field["value"] or not field["evidence"]
                or not any(ev["status"] == "verified_current" for ev in field["evidence"])
            ):
                raise ValueError(
                    "Current overseas fact requires a value and checked evidence"
                )
            if field["value"] is None and field["status"] != "missing":
                raise ValueError("Do not imply a known value for an unknown field")
            for ev in field["evidence"]:
                source = json.loads(
                    (
                        BUNDLE / "overseas_sources" / (ev["source_id"] + ".json")
                    ).read_text()
                )
                require_usable_source(source)
                if ev["status"] == "verified_current" and source.get(
                    "access_result"
                ) in {
                    "challenge_page", "captcha_required", "empty_response",
                    "unrelated_content_anomaly", "password_protected",
                }:
                    raise ValueError(
                        "Unread CCU access response cannot support current policy"
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
                    raise ValueError(
                        "Changed CCU overseas source: review contents before promoting"
                    )
                if source.get("bundled_file"):
                    contents = (BUNDLE / source["bundled_file"]).read_bytes()
                    if hashlib.sha256(contents).hexdigest() != source["sha256"]:
                        raise ValueError("Changed CCU bundled partner form")
                if source.get("status", "").startswith("web_extracted_"):
                    # A browser-tool extraction is not a raw HTTP/PDF download.
                    response = source.get("web_extraction_response", "")
                    if (
                        not response
                        or hashlib.sha256(response.encode()).hexdigest()
                        != source["sha256"]
                    ):
                        raise ValueError("Changed CCU web extraction response")
                pages = ev["source_pages"] or list(
                    range(1, len(source.get("text_pages", [])) + 1)
                )
                text = " ".join(_flat(source["text_pages"][p - 1]) for p in pages)
                if not _flat(ev["excerpt"]) or _flat(ev["excerpt"]) not in text:
                    raise ValueError(
                        f"CCU overseas evidence not in source: {ev['source_id']}"
                    )
                if (
                    not ev["academic_year"]
                    or not ev["checked_at"]
                    or not ev["source_url"]
                ):
                    raise ValueError("Missing overseas provenance")
                # A field can retain both a current rule and an older or
                # unyear policy for comparison. Each excerpt keeps its own
                # applicability rather than inheriting the aggregate state.
                if ev["status"] not in STATUS_LABELS or ev["status"] == "missing":
                    raise ValueError("Invalid CCU overseas evidence status")
    return {row["ccu_page"]: row for row in rows}


def apply_overseas_review(partner: PartnerUniversity) -> PartnerUniversity:
    row = reviewed_rows().get(partner.source_pages[0])
    if not row:
        return partner
    if (
        row["school_name"] != partner.school_name
        or partner.availability_status == "not_open"
    ):
        raise ValueError("CCU overseas school identity or availability mismatch")
    partner.partner_exchange_details = {
        key: PartnerExchangeDetailField.model_validate(value)
        for key, value in row["fields"].items()
    }
    deadline = partner.partner_exchange_details["application_deadline"]
    if deadline.status == "conflict":
        # Preserve the mother's original transcription separately. Every public
        # projection must carry the comparison, not silently choose a later date.
        raw_home = partner.partner_application_deadline
        if raw_home:
            partner.reference_data["partner_application_deadline"] = raw_home
        partner.partner_application_deadline = deadline.value
        partner.student_summary_zh.application_deadline = deadline.value
        home_evidence = partner.field_evidence.get("partner_application_deadline")
        if home_evidence:
            home_evidence.status = "conflict"
            home_evidence.note = deadline.reason + "；" + (deadline.value or "")
    calendar = partner.partner_exchange_details["academic_calendar"]
    if partner.source_pages[0] in {34, 61} and calendar.status == "conflict":
        if partner.semester_dates:
            partner.reference_data["semester_dates"] = partner.semester_dates
        partner.semester_dates = calendar.value
        partner.student_summary_zh.study_period = (
            (partner.study_period or "") + "；" + (calendar.value or "")
        )
        home_evidence = partner.field_evidence.get("semester_dates")
        if home_evidence:
            home_evidence.status = "conflict"
            home_evidence.note = calendar.value
    if partner.source_pages[0] in {32, 35, 37, 61, 87, 105}:
        detail = partner.partner_exchange_details["language"]
        partner.language_review_note = detail.value or detail.reason
        for condition in partner.language_conditions:
            condition.scope_choice_required = True
            condition.additional_conditions.append(partner.language_review_note)
            condition.evidence.note = partner.language_review_note
        partner.student_summary_zh.eligibility_points.append(
            partner.language_review_note
        )
    if partner.source_pages[0] == 95:
        detail = partner.partner_exchange_details["language"]
        partner.language_review_note = detail.value or detail.reason
        home_evidence = partner.field_evidence["language_requirement"]
        home_evidence.status = "needs_confirmation"
        home_evidence.note = partner.language_review_note
        for condition in partner.language_conditions:
            condition.requirement_level = "needs_confirmation"
            condition.scope_choice_required = True
            condition.additional_conditions = [
                "接收校B2證書或母校Rector／Dean／Coordinator確認函為替代路徑；獨立證照僅recommended",
                "中正逐校數字及簡章兩年內有效檢定證明另須確認，母校函不自動豁免校內繳件",
            ]
            condition.evidence.status = "needs_confirmation"
            condition.evidence.note = partner.language_review_note
        alternative = detail.evidence[0]
        partner.language_conditions.append(
            PartnerLanguageCondition(
                test="other",
                requirement_level="needs_confirmation",
                scope_choice_required=True,
                additional_conditions=[
                    "母校Rector／Dean／Coordinator簽署英語B2確認函；中正是否接受替代檢定仍待確認"
                ],
                evidence=ExchangeFieldEvidence(
                    source_url=alternative.source_url,
                    source_pages=alternative.source_pages,
                    academic_year=alternative.academic_year,
                    application_round=alternative.application_round,
                    checked_at=alternative.checked_at,
                    status="needs_confirmation",
                    excerpt=alternative.excerpt,
                    note=partner.language_review_note,
                ),
            )
        )
        partner.student_summary_zh.eligibility_points.append(
            partner.language_review_note
        )
    # The new receiving-school source introduces an alternative certificate or
    # program scope. Do not classify a student's lone test score as mandatory.
    if partner.source_pages[0] in {65, 86, 89}:
        detail = partner.partner_exchange_details["language"]
        partner.language_review_note = (
            (partner.language_review_note or "")
            + "；海外補查："
            + (detail.value or detail.reason)
        )
        for condition in partner.language_conditions:
            condition.scope_choice_required = True
            condition.additional_conditions.append(
                "合作校另有語言證明或計畫分流；須確認中正要求與所選路徑"
            )
    return partner


def describe_field(key: str, field: PartnerExchangeDetailField) -> str:
    scope = "（" + describe_evidence_list(field.evidence) + "）" if field.evidence else ""
    return f"{LABELS[key]} · {STATUS_LABELS[field.status]}：{field.value or field.reason}{scope}"


def enrich_workflow(workflow, partner: PartnerUniversity):
    from .ccu_documents import enrich_documents
    from .ccu_profile import reviewed_profiles

    fields = partner.partner_exchange_details
    if not fields:
        return workflow
    scope = workflow.steps[4].scope
    # The mother's per-school second-stage list is independent of the host's
    # freshly reviewed list. Keep both, without promoting gray historical text.
    home_documents = partner.field_evidence.get("partner_documents")
    if home_documents:
        pages = "、".join(map(str, home_documents.source_pages))
        if home_documents.status == "reference_only":
            text = home_documents.reference_excerpt
            label = "中正逐校第二階文件：歷史灰字參考，尚未核實當期，不作必備文件"
        else:
            text = home_documents.excerpt or partner.application_info
            label = f"中正逐校第二階文件：{STATUS_LABELS[home_documents.status]}"
        if text:
            workflow.steps[3].details.append(
                f"{label}；官方PDF第{pages}頁；"
                f"{home_documents.application_round or '適用年度未核實'}；"
                f"查核2026-10-08：{text}"
            )
            workflow.steps[3].source_urls = list(
                dict.fromkeys(
                    [*workflow.steps[3].source_urls, home_documents.source_url]
                )
            )

    def sources(keys):
        return list(
            dict.fromkeys(ev.source_url for key in keys for ev in fields[key].evidence)
        )

    application_keys = [
        "program_scope",
        "eligibility",
        "language",
        "nomination_deadline",
        "application_deadline",
        "documents",
        "application_forms",
        "course_restrictions",
    ]
    step = workflow.steps[4]
    step.details = [describe_field(key, fields[key]) for key in application_keys]
    step.source_urls = sources(application_keys) or step.source_urls
    deadline = fields["application_deadline"]
    step.timing = describe_field("application_deadline", deadline)
    step.deadline_source_url = (
        deadline.evidence[0].source_url if deadline.evidence else None
    )
    step.deadline_status = "needs_confirmation"
    step.deadline_at = (
        None  # Day-only or multi-program values never fabricate midnight reminders.
    )
    step.required_documents = []
    step.document_requirements = []
    document = fields["documents"]
    if document.status == "verified_current" and document.value:
        step.required_documents = [document.value]
        step.document_requirements = [
            ApplicationDocumentRequirement(
                name=document.value,
                copy_type="unspecified",
                source_urls=sources(["documents"]),
                needs_confirmation=True,
            )
        ]
    # Always show the source gaps: an actual listed requirement is not a promise
    # that every attachment, signature or faculty-specific item is complete.
    step.needs_confirmation = True
    step.support_status = "needs_confirmation"
    life_keys = [
        "academic_calendar",
        "housing",
        "housing_deadline",
        "costs",
        "insurance",
        "visa",
        "arrival",
        "host_tuition",
        "exchange_duration",
    ]
    home_return = workflow.steps[5]
    home_return.order = 7
    life_step = ApplicationStep(
        order=6,
        phase="合作校行前與生活",
        title="核對接收計畫的住宿、保險與抵達安排",
        responsible_party="學生／合作校",
        scope=scope,
        summary="依每欄年度及計畫辦理；歷史參考和矛盾資料不能當作本期確定規定。",
        details=[describe_field(key, fields[key]) for key in life_keys],
        source_urls=sources(life_keys),
        checked_at=CHECKED_AT,
        support_status="needs_confirmation",
        needs_confirmation=True,
        confirmation_contact="國立中正大學國際事務處及合作校提名窗口",
    )
    workflow.steps.insert(5, life_step)
    enrich_documents(workflow, partner)
    from .ccu_sungshin_current import enrich_sungshin_workflow
    enrich_sungshin_workflow(workflow, partner)
    refs = {ev.source_url: ev for field in fields.values() for ev in field.evidence}
    for guide in reviewed_profiles().get(partner.source_pages[0], {}).get("supplementary_life_guidance", []):
        ev = guide["evidence"][0]
        target = home_return if guide["key"] == "return_preparation" else life_step
        target.details.append(f"{guide['title']} · {STATUS_LABELS[guide['status']]}：{guide['value']}"
                              f"（{ev['academic_year']}；查核{ev['checked_at'].split('T')[0]}）")
        target.source_urls = list(dict.fromkeys([*target.source_urls, *[e["source_url"] for e in guide["evidence"]]]))
        refs.update({e["source_url"]: ExchangeFieldEvidence.model_validate(e) for e in guide["evidence"]})
    workflow.sources.extend(
        ApplicationWorkflowSource(
            title="合作校接收資料 · " + describe_evidence(ev),
            source_url=url,
            role="partner_university",
            authority="partner_official",
            priority=2,
            effective_academic_year=ev.academic_year,
            application_round=ev.application_round,
            checked_at=ev.checked_at,
        )
        for url, ev in refs.items()
    )
    workflow.coverage_note = "中正2027春季母校規定已核；55校海外資料按17欄保存查核狀態，已讀原文範圍另见審閱紀錄。仍有公開資料續查、缺值、舊年度、計畫差異與來源矛盾；流程未完成雙人審核發布。"
    return workflow


def destination_profile(partner: PartnerUniversity) -> DestinationProfile:
    from .ccu_profile import profile_life

    fields = partner.partner_exchange_details
    life_keys = [
        "housing",
        "housing_deadline",
        "costs",
        "insurance",
        "visa",
        "arrival",
        "course_restrictions",
        "academic_calendar",
    ]
    refs = {ev.source_url: ev for key in life_keys for ev in fields[key].evidence}
    sections = [
        StudentGuideSection(
            key=key,
            title=LABELS[key],
            summary=fields[key].value or fields[key].reason,
            points=[describe_field(key, fields[key])],
            source_urls=list(dict.fromkeys(e.source_url for e in fields[key].evidence)),
            evidence_type="official",
            caution=STATUS_LABELS[fields[key].status] + "；" + fields[key].reason,
        )
        for key in life_keys
    ]
    life, profile_sections, profile_evidence = profile_life(partner)
    sections.extend(profile_sections)
    refs.update(
        {
            ev["source_url"]: ExchangeFieldEvidence.model_validate(ev)
            for ev in profile_evidence
        }
    )

    def summary(key):
        return describe_field(key, fields[key])

    return DestinationProfile(
        home_university=HOME,
        school_name=partner.school_name,
        country=partner.country,
        city=partner.location.city if partner.location else None,
        cost_summary=summary("costs"),
        housing_summary=summary("housing"),
        transport_summary=life.get("transport"),
        campus_life_summary=life.get("campus_life"),
        student_guide_sections=sections,
        sources=[
            SourceReference(
                title="合作校生活資料 · " + describe_evidence(ev),
                source_url=url,
                category=PageCategory.PARTNER_SCHOOL,
                summary=f"{ev.academic_year}；查核{ev.checked_at.date().isoformat()}；" + (ev.excerpt or ""),
            )
            for url, ev in refs.items()
        ],
        last_checked=CHECKED_AT,
        coverage_status="official_partial"
        if any(fields[k].status == "verified_current" for k in life_keys)
        else "needs_confirmation",
        coverage_note="已查核所列官方附件／頁面內容，仍有未載、未核實新版或矛盾；不能將歷史費率及一般入學資訊當作本期交換規定。",
    )
