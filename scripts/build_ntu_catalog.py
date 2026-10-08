"""Import the NTU research snapshot without promoting unconfirmed rules.

Run with --candidates-dir and --verification-dir pointing at the collected
source artifacts. The resulting bundle is self-contained at runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from exchange_info.models import (
    DestinationProfile, ExchangeInfo, PartnerResearchRecord, PartnerUniversity,
    ProcessedPage, StudentDashboard, UniversityApplicationWorkflow,
)

SCHOOL = "國立臺灣大學"
GUIDELINES = "https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf"
LIST_URL = "https://oia.ntu.edu.tw/outgoing/school.list/semester/1"
OUTPUT = Path(__file__).resolve().parents[1] / "src/exchange_info/official_data/ntu"
FIELD_LABELS = {"eligibility": "申請資格／成績", "language": "語言條件", "deadlines": "合作校收件期限",
                "calendar": "學期行事曆", "documents": "提名／申請文件", "housing": "住宿",
                "courses": "課程與修課限制", "cost": "費用", "insurance_visa": "保險及簽證"}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write(name: str, value):
    (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rows(name: str, values, model):
    validated = [model.model_validate(value) for value in values]
    (OUTPUT / name).write_text("".join(row.model_dump_json() + "\n" for row in validated), encoding="utf-8")


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates-dir", type=Path, required=True)
    parser.add_argument("--verification-dir", type=Path, required=True)
    parser.add_argument("--list-verification", type=Path)
    args = parser.parse_args()
    base, latest = args.candidates_dir, args.verification_dir
    OUTPUT.mkdir(parents=True, exist_ok=True)
    wrappers = rows(latest / "partners-116-1-updated-candidates.jsonl")
    manual = read(latest / "manually-reviewed-current-evidence.json")
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
                f"{FIELD_LABELS.get(key, key)}：{field['value']}（來源第{','.join(map(str, field.get('pdf_pages', [])))}頁）"
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
    assert len(partner_rows) == 288
    assert sum(row["quota"] is None for row in partner_rows) == 282
    write_rows("partners.jsonl", partner_rows, PartnerUniversity)
    write("verification_status.json", ledger)

    dashboard = clean(read(base / "student-dashboard-candidate.json")["dashboard"])
    dashboard["partner_universities"] = []  # Loaded from the single partner bundle.
    dashboard["academic_score_minimum"] = None  # GPA/rank is not a percentage score.
    dashboard["language_score_minimums"] = {"toefl": 79.0, "toefl_new": 4.0, "ielts": 6.0}
    dashboard["program_overview"][0]["details"][0] = "116學年度第1學期出國（2027年秋季），交換一學期或一學年；實際出國與開學日期依合作校。"
    dashboard["program_overview"][0]["details"].append(
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
    ExchangeInfo.model_validate(info)
    write("exchange_info.json", info)
    workflows = clean(rows(base / "application-workflows-116-1-candidates.jsonl"))
    for workflow in workflows:
        workflow["applicability_note"] = "校內116-1時程已公告；合作校名額與條件尚未全面確認，流程作為準備參考。"
        if workflow["school_name"] in manual_notes:
            note, reviewed = manual_notes[workflow["school_name"]]
            workflow["steps"][0]["details"].append(note)
            workflow["steps"][0]["source_urls"].append(reviewed["source_url"])
        # Integration authorization does not constitute source/content approval.
        workflow["review_status"] = "pending_review"
        workflow["published_at"] = None
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
        ("home-university-rules.json", "home_rules.json"), ("scholarships.json", "scholarships.json"),
        ("documents.json", "documents.json"), ("student-experience-directory.json", "student_experience_directory.json"),
    ]:
        write(target, clean(read(base / source)))
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
    })
    print(f"NTU: {len(partner_rows)} partners, {len(workflows)} workflows, {len(destinations)} destinations; 282 pending / 6 zero quotas")


if __name__ == "__main__":
    main()
