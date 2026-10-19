"""Import the NTU research snapshot without promoting unconfirmed rules.

Rebuild offline from the tracked source snapshot, or supply replacement source
directories together. Candidate provenance is retained separately from runtime models.
"""
from __future__ import annotations

import argparse
import hashlib
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from exchange_info.models import (
    DestinationProfile, ExchangeInfo, PartnerResearchRecord, PartnerUniversity,
    ProcessedPage, StudentDashboard, UniversityApplicationWorkflow,
)
from exchange_info.ntu_partner_summary import with_ntu_partner_summary
from exchange_info.life_context import LifeResearchSnapshot, reviewed_life_snapshot

SCHOOL = "國立臺灣大學"
GUIDELINES = "https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf"
LIST_URL = "https://oia.ntu.edu.tw/outgoing/school.list/semester/1"
OUTPUT = Path(__file__).resolve().parents[1] / "src/exchange_info/official_data/ntu"
SNAPSHOT = Path(__file__).resolve().parents[1] / "sources/ntu/2026-10-08-import.json.gz"
AUDIT = SNAPSHOT.with_name("2026-10-08-audit.json")
BUILD_INPUTS: dict[str, str] = {}
FIELD_LABELS = {"eligibility": "申請資格／成績", "language": "語言條件", "deadlines": "合作校收件期限",
                "calendar": "學期行事曆", "documents": "提名／申請文件", "housing": "住宿",
                "courses": "課程與修課限制", "cost": "費用", "insurance_visa": "保險及簽證"}


def read(path: Path):
    key = path.as_posix()
    return json.loads(BUILD_INPUTS[key] if key in BUILD_INPUTS else path.read_text(encoding="utf-8"))


def rows(path: Path):
    key = path.as_posix()
    text = BUILD_INPUTS[key] if key in BUILD_INPUTS else path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def write(name: str, value):
    (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rows(name: str, values, model):
    validated = [model.model_validate(value) for value in values]
    if model is PartnerUniversity:
        validated = [with_ntu_partner_summary(row) for row in validated]
    compact = name == "application_workflows.jsonl"
    (OUTPUT / name).write_text("".join(row.model_dump_json(exclude_defaults=compact) + "\n" for row in validated), encoding="utf-8")


def compact_workflow_references(workflow, partner):
    """Keep the original partner text in the catalogue, rather than a second copy."""
    texts = [value for value in partner.values() if isinstance(value, str)]
    for step in workflow["steps"]:
        details = step.get("details", [])
        kept = [detail for detail in details if not (len(detail) >= 100 and any(detail in text for text in texts))]
        if len(kept) != len(details):
            kept.append("合作校參考條件與補充查核請查看本校詳情；本期仍待確認。")
        step["details"] = kept


def clean(value):
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items() if key not in {
            "candidate_only", "user_integration_approval", "publication_status",
        }}
    if isinstance(value, str):
        return value.replace("候選資料未核准接入。", "正式送件以校方系統及當期通知為準。") \
            .replace("與使用者同意", "") \
            .replace("未核准、未接入", "合作校本期條件仍待確認") \
            .replace("未接入正式提醒", "階段適用性須另確認") \
            .replace("，未發布。", "，未完成本期全面確認。")
    return value


def main():
    global OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates-dir", type=Path)
    parser.add_argument("--verification-dir", type=Path)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--list-verification", type=Path)
    args = parser.parse_args()
    if bool(args.candidates_dir) != bool(args.verification_dir):
        parser.error("--candidates-dir and --verification-dir must be supplied together")
    BUILD_INPUTS.clear()
    snapshot = json.loads(gzip.decompress(args.snapshot.read_bytes()))
    if snapshot["format_version"] != 1:
        parser.error("unsupported source snapshot format")
    if not args.candidates_dir:
        BUILD_INPUTS.update(snapshot["files"])
        args.candidates_dir, args.verification_dir = Path("candidates"), Path("verification")
        args.list_verification = args.list_verification or Path("ntu-list-refresh.json")
    OUTPUT = args.output_dir
    base, latest = args.candidates_dir, args.verification_dir
    OUTPUT.mkdir(parents=True, exist_ok=True)
    original_home = read(base / "home-university-rules.json")
    home_rules = clean(original_home)
    snapshot_home = json.loads(snapshot["files"]["candidates/home-university-rules.json"])
    for key in ("selection_rules", "language_score_minimums"):
        home_rules.setdefault(key, snapshot_home[key])
    write("import_provenance.json", {
        "source_snapshot": args.snapshot.name,
        "source_snapshot_sha256": hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
        "supplemental_audit": AUDIT.name,
        "supplemental_audit_sha256": hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
        "original_home_flags": {key: original_home.get(key) for key in ("candidate_only", "user_integration_approval", "publication_status")},
        "platform_integration_authorized_at": "2026-10-08",
        "content_verification_status": "partial_current_cycle",
        "note": "使用者授權接入平台不代表合作校資訊已完成當期全面核實；原始旗標保留於來源快照。",
    })
    wrappers = rows(latest / "partners-116-1-updated-candidates.jsonl")
    manual = read(latest / "manually-reviewed-current-evidence.json")
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    for portal_id, update in audit["partners"].items():
        reviewed = manual.setdefault(portal_id, {"checked_fields": {}, "scope": "", "remaining": []})
        reviewed["scope"] += "\n" + update["scope"]
        reviewed.setdefault("source_url", update["source_url"])
        reviewed["checked_fields"].update(update["fields"])
        reviewed["remaining"] = list(dict.fromkeys(reviewed["remaining"] + update["remaining"]))
    partner_rows, ledger = [], []
    manual_notes = {}
    for wrapper in wrappers:
        portal_id = wrapper["portal_id"]
        partner = clean(wrapper["partner"])
        pending = wrapper["selection_status"] == "pending_update"
        # Contract quotas and historical detail quotas are not selection quotas.
        partner["quota"] = None if pending else "0 名"
        partner["availability_status"] = "agreement_only"
        partner["availability_note"] = (
            "116-1本期甄選名額尚未公布，合作校資格及條件待確認；以下詳情為官方參考資料，不能視為本期可申請。"
            if pending else "116-1官方名單已更新為0名額，本期未開放；其他說明僅供參考。"
        )
        duration = re.search(r"可選擇交換([^。\n)]+)", wrapper.get("detail_reference_quota", ""))
        partner["study_period"] = f"官方參考期程：{duration.group(1).strip()}（本期待確認）" if duration else None
        reviewed = manual.get(portal_id)
        note = ""
        if reviewed:
            note = "【補充來源查核】\n" + reviewed["scope"] + "\n" + "\n".join(
                f"{FIELD_LABELS.get(key, key)}：{field['value']}" +
                (f"（來源第{','.join(map(str, field['pdf_pages']))}頁）" if field.get("pdf_pages") else "") +
                ("\n欄位來源：" + "；".join(field["source_urls"]) if field.get("source_urls") else "")
                for key, field in reviewed["checked_fields"].items()
            ) + "\n來源：" + reviewed["source_url"] + "\n待確認：" + "；".join(reviewed["remaining"])
            partner["application_info"] = (partner.get("application_info") or "") + "\n\n" + note
            manual_notes[partner["school_name"]] = (note, reviewed)
        partner_rows.append(partner)
        verification = wrapper.get("latest_verification", {})
        ledger.append({
            "portal_id": portal_id, "school_name": partner["school_name"],
            "selection_status": "pending_official_publication" if pending else "zero_quota",
            "selection_quota": partner["quota"], "source_url": partner["source_url"],
            "full_116_1_information_confirmed": False,
            "fields": {key: {
                "status": field["status"], "label": field["label"],
                "reviewed_partial_value": field.get("reviewed_partial_value"),
                "remaining_questions": field.get("remaining_questions", []),
                "source_urls": [e["source_url"] for e in field.get("best_evidence", [])],
            } for key, field in verification.get("fields", {}).items()},
            "manual_review": reviewed,
        })
        if portal_id in audit["partners"]:
            for key, field in audit["partners"][portal_id]["fields"].items():
                ledger[-1]["fields"][key] = {
                    "status": field["status"], "label": FIELD_LABELS.get(key, key),
                    "reviewed_partial_value": field,
                    "remaining_questions": field["remaining_questions"], "source_urls": field["source_urls"],
                }
    assert len(partner_rows) == 288
    assert sum(row["quota"] is None for row in partner_rows) == 282
    write_rows("partners.jsonl", partner_rows, PartnerUniversity)
    write("verification_status.json", ledger)

    dashboard = clean(read(base / "student-dashboard-candidate.json")["dashboard"])
    dashboard["partner_universities"] = []  # Loaded from the single partner bundle.
    dashboard["academic_score_minimum"] = None  # GPA/rank is not a percentage score.
    dashboard["language_score_minimums"] = home_rules["language_score_minimums"]
    dashboard["selection_rules"] = home_rules["selection_rules"]
    dashboard["scholarship_info"].append(audit["scholarship_explanation"])
    overview = next(item for item in dashboard["program_overview"] if item["title"] == "116-1校級出國交換")
    overview["details"] = [detail for detail in overview["details"] if not detail.startswith("2027年9月起")]
    overview["details"].insert(0, "116學年度第1學期出國（2027年秋季），交換一學期或一學年；實際出國與開學日期依合作校。")
    overview["details"].append(
        "目前282項本期名額待公布，6項為0名額；合作校條件未全部完成116-1確認。"
    )
    colleges = clean(read(base / "college-programmes-candidates.json"))
    for programme in colleges:
        source = programme["sources"][0]
        dashboard["program_overview"].append({
            "title": f"{programme['college']}院級交換（另行甄選）",
            "details": [
                f"申請截止：{programme.get('application_deadline_at', '以院級公告為準')}",
                *programme.get("eligibility", []), *programme.get("warnings", []),
                "院級名額、資格、文件及截止日另依該院公告，不套用校級條件。",
            ],
            "source": {"title": programme["programme"], "source_url": source["url"]},
        })
    StudentDashboard.model_validate(dashboard)
    write("student_dashboard.json", dashboard)
    info = clean(read(base / "exchange-info-candidate.json"))
    info["language_requirement"] = audit["language_requirement"]
    info["scholarship_info"].extend(audit["scholarship_explanation"]["details"])
    ExchangeInfo.model_validate(info)
    write("exchange_info.json", info)
    workflows = clean(rows(base / "application-workflows-116-1-candidates.jsonl"))
    partner_map = {partner["school_name"]: partner for partner in partner_rows}
    for workflow in workflows:
        workflow["applicability_note"] = "校內116-1時程已公告；合作校名額與條件尚未全面確認，流程作為準備參考。"
        if workflow["school_name"] in manual_notes:
            note, reviewed = manual_notes[workflow["school_name"]]
            workflow["steps"][0]["details"].append(note)
            workflow["steps"][0]["source_urls"].append(reviewed["source_url"])
            workflow["steps"][0]["source_urls"].extend(
                url for field in reviewed["checked_fields"].values() for url in field.get("source_urls", [])
                if url not in workflow["steps"][0]["source_urls"]
            )
        # Integration authorization does not constitute source/content approval.
        workflow["review_status"] = "pending_review"
        workflow["published_at"] = None
        compact_workflow_references(workflow, partner_map[workflow["school_name"]])
    write_rows("application_workflows.jsonl", workflows, UniversityApplicationWorkflow)
    destinations = clean(rows(base / "destination-profiles-candidates.jsonl"))
    for destination in destinations:
        for field in ["cost_summary", "housing_summary", "transport_summary", "campus_life_summary"]:
            if not destination.get(field):
                destination[field] = "尚未取得並核對116-1適用資料；請向合作校確認。"
        if destination["school_name"] in manual_notes:
            note, reviewed = manual_notes[destination["school_name"]]
            for field, key in [("cost_summary", "cost"), ("housing_summary", "housing")]:
                if key in reviewed["checked_fields"]:
                    destination[field] = reviewed["checked_fields"][key]["value"] + "（" + reviewed["scope"] + "）"
            destination["sources"].append({"title": "合作校補充查核", "source_url": reviewed["source_url"], "summary": note})
    write_rows("destination_profiles.jsonl", destinations, DestinationProfile)
    write_rows("partner_research.jsonl", rows(base / "partner-research-candidates.jsonl"), PartnerResearchRecord)

    pages = []
    attached_urls = set()
    for field, category in [
        ("program_overview", "exchange_application"), ("eligibility", "exchange_application"),
        ("language_requirements", "exchange_application"), ("required_documents", "exchange_application"),
        ("scholarship_info", "scholarship"),
    ]:
        for item in dashboard[field]:
            body = "\n".join(item["details"])
            url = item["source"]["source_url"]
            attachments = []
            if urlsplit(url).path.lower().endswith(".pdf") and url not in attached_urls:
                attachments.append({"url": url, "filename": unquote(Path(urlsplit(url).path).name), "content_type": "application/pdf"})
                attached_urls.add(url)
            pages.append({
                "title": SCHOOL + "：" + item["title"], "text": body, "summary": body,
                "source_url": item["source"]["source_url"], "category": category,
                "content_hash": hashlib.sha256(body.encode()).hexdigest(),
                "crawled_at": dashboard["last_checked"],
                "attachments": attachments,
            })
    for period in dashboard["application_periods"]:
        body = "臺灣時間：" + (f"{period['opens_at']}起；" if period.get("opens_at") else "") + f"截止{period['deadline_at']}。" + "\n" + "\n".join(period["details"])
        pages.append({"title": SCHOOL + "：" + period["title"], "text": body, "summary": body,
                      "source_url": GUIDELINES, "category": "deadline", "crawled_at": dashboard["last_checked"],
                      "content_hash": hashlib.sha256(body.encode()).hexdigest()})
    write_rows("pages.jsonl", pages, ProcessedPage)
    for source, target in [
        ("scholarships.json", "scholarships.json"),
        ("documents.json", "documents.json"), ("student-experience-directory.json", "student_experience_directory.json"),
    ]:
        payload = clean(read(base / source))
        if target == "scholarships.json":
            payload.update(audit["scholarship_updates"])
        write(target, payload)
    write("home_rules.json", home_rules)
    write("college_programmes.json", colleges)
    if args.list_verification:
        receipt = read(args.list_verification)
        assert receipt["http_status"] == 200 and len(receipt["rows"]) == 288
        assert sum(not row["quota"] for row in receipt["rows"]) == 282
        assert all(not row["quota"] or row["quota"].strip().startswith("0") for row in receipt["rows"])
        write("list_verification.json", receipt)
    write("catalog-completeness.json", {
        "home_university": SCHOOL, "academic_year": "116", "outgoing_semester": 1,
        "partner_count": 288, "quota_pending_count": 282, "zero_quota_count": 6,
        "confirmed_open_count": 0, "fully_verified_current_cycle_count": 0,
        "manually_reviewed_school_count": len(manual), "source_url": LIST_URL,
        "guidelines_url": GUIDELINES, "checked_at": dashboard["last_checked"],
        "limitations": ["合作校本期名額、資格及生活資訊仍待更新與確認。", "校級與院級甄選分開；學生心得目錄尚未逐篇匯入。"],
        "build_inputs": ["NTU candidate collection 2026-10-07", "NTU current verification 2026-10-07"],
        "supplemental_audit": AUDIT.name,
        "documents_status_counts": dict(Counter(row["fields"].get("documents", {}).get("status", "missing") for row in ledger)),
        "missing_information_note": "缺文字證據或尚未找到新版，不等於官方未公告；288校名單核對不代表全部欄位完成當期確認。",
    })
    enrichment = SNAPSHOT.with_name("destinations-2026-10-08.json.gz")
    if enrichment.exists():
        researched = json.loads(gzip.decompress(enrichment.read_bytes()))
        write_rows("student_life.jsonl", [reviewed_life_snapshot(LifeResearchSnapshot.model_validate(row)).model_dump(mode="json") for row in researched["life"]], LifeResearchSnapshot)
    from exchange_info.ntu_official_changes import apply_official_changes, SNAPSHOT as OFFICIAL_CHANGES
    if OFFICIAL_CHANGES.exists():
        apply_official_changes(OUTPUT)
    from exchange_info.ntu_completion import apply_completion, SOURCE as COMPLETION_SOURCE
    if COMPLETION_SOURCE.exists():
        apply_completion(OUTPUT)
    counts = json.loads((OUTPUT / "catalog-completeness.json").read_text(encoding="utf-8"))
    n_total = counts["partner_count"]
    print(f"NTU: {n_total} partners, {n_total} workflows, {n_total} destinations; {counts['quota_pending_count']} pending / {counts['zero_quota_count']} zero / {counts.get('published_positive_quota_count', 0)} published quotas")


if __name__ == "__main__":
    main()
