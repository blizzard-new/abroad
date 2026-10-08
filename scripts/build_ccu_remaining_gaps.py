"""Offline, per-school gap and acquired-attachment inventory; no exhaustion claim."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ccu"
OUTPUT = BUNDLE / "remaining-gaps.json"
ACCESS_LIMITATIONS = {"empty_response", "challenge_page", "captcha_required", "unrelated_content_anomaly", "password_protected"}


def read(name):
    return json.loads((BUNDLE / name).read_text())


def source_ids(value):
    if isinstance(value, dict):
        if value.get("source_id"):
            yield value["source_id"]
        for child in value.values():
            yield from source_ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from source_ids(child)


def main():
    profiles = read("profile-reviewed-fields.json")
    overseas = {r["ccu_page"]: r for r in read("overseas-reviewed-fields.json")}
    documents = {r["ccu_page"]: r for r in read("partner-document-requirements.json")}
    sources = {
        r["source_id"]: json.loads(
            (BUNDLE / "overseas_sources" / (r["source_id"] + ".json")).read_text()
        ) for r in read("overseas-source-registry.json")
    }
    requests = read("overseas-source-requests.json")
    visited = {r["url"].split("#")[0] for r in requests}
    # A source_checks entry records acquisition, not mapped policy evidence.
    mapped = set(source_ids([
        field["evidence"] for row in profiles for field in row["fields"].values()
    ])) | set(source_ids([
        field["evidence"] for row in overseas.values() for field in row["fields"].values()
    ]))
    mapped |= set(source_ids(list(documents.values())))
    ledger = read("semantic-review-ledger.json")
    read_ids = {
        sid for row in ledger for field in row["fields"].values()
        for sid in field.get("readable_source_ids", [])
    }
    private_steps = {
        23: ("p23-r17-hmt-procedure", "我校将通过邮件", "提名網址寄母校負責人；學生報名系統與母校提名系統分開，2027適用未明示。"),
        98: ("p98-r3-application-web", "STEP 2", "個人PDF須先online送出後生成；不能取得通用空白PDF代替。公開清單和兩份模板已接通。"),
        102: ("p102-r3-exchange-en", "2. You apply online", "host明示提名後才提供申請資訊；已保留公開附件清單，個人online追加欄位未取得。"),
    }
    schools = []
    for profile in profiles:
        page = profile["ccu_page"]
        rows = [s for s in sources.values() if s.get("ccu_page", s.get("page")) == page]
        fields = {
            "college_scope": profile["fields"]["colleges"],
            "degree_scope": profile["fields"]["degree_levels"],
            "transport": profile["fields"]["transport"],
            "campus_life": profile["fields"]["campus_life"],
            "documents": overseas[page]["fields"]["documents"],
            "application_forms": overseas[page]["fields"]["application_forms"],
        }
        gaps = {}
        for key, field in fields.items():
            if field["status"] != "verified_current" or key in {"documents", "application_forms"}:
                gaps[key] = {
                    "status": field["status"], "known_value": field["value"],
                    "reason": field["reason"], "evidence": field["evidence"],
                    "next_public_action": (
                        "核對當期交換院系／學制及協議適用；一般學位目錄不等於incoming可申請範圍。"
                        if "scope" in key else
                        "逐項核對當期清單、模板及公開程序；個人表與母校通用文件分開。"
                        if key in {"documents", "application_forms"} else
                        "續查官方一般服務及校區指引，保留未標年度和交換身分限制。"
                    ),
                }
        candidates = {}
        for source in rows:
            if source.get("access_result") in ACCESS_LIMITATIONS:
                continue
            host = urlsplit(source["source_url"]).hostname or ""
            for link in source.get("links", []):
                url, label = link.get("url", ""), link.get("label", "")
                target = urlsplit(url).hostname or ""
                if (url.startswith(("https://", "http://"))
                    and target == host and url.split("#")[0] not in visited
                    and re.search(r"exchange|incoming|application|fact.?sheet|accommodation|housing|transport|library|交換|申请", label + " " + url, re.IGNORECASE)):
                    candidates[url] = {"url": url, "label": label, "discovered_in_source": source["source_id"]}
        inventory = []
        for source in rows:
            sid = source["source_id"]
            item = {k: source.get(k) for k in [
                "source_id", "source_url", "checked_at", "status", "http_status",
                "access_result", "content_academic_year", "content_applicability",
                "content_review_note", "sha256", "bundled_file",
            ]}
            item["review_state"] = (
                "access_limited_not_policy_content" if source.get("access_result") in ACCESS_LIMITATIONS else
                "mapped_field_evidence_not_whole_document_completion" if sid in mapped else
                "existing_field_review_ledger_not_all_fields_complete" if sid in read_ids else
                "necessary_sections_reviewed_no_current_field_mapping" if source.get("content_review_extent") == "necessary_policy_sections" else
                "extracted_content_not_yet_mapped_requires_scope_year_review" if any(source.get("text_pages", [])) else
                "content_not_obtained"
            )
            inventory.append(item)
        constraints = []
        if page in private_steps:
            sid, needle, note = private_steps[page]
            source = json.loads((BUNDLE / "overseas_sources" / (sid + ".json")).read_text())
            text = " ".join(" ".join(source["text_pages"]).split())
            start = text.index(needle)
            constraints.append({
                "source_id": sid, "source_url": source["source_url"],
                "checked_at": source["checked_at"], "sha256": source["sha256"],
                "academic_year": source.get("content_academic_year"),
                "excerpt": text[start:start + 750], "note": note,
                "scope": "此程序節點，不等於該校所有資料只能登入／聯絡承辦。",
            })
        schools.append({
            "ccu_page": page, "school_name": profile["school_name"],
            "gaps": gaps, "checked_sources": inventory,
            "host_document_count": len(documents.get(page, {}).get("requirements", [])),
            "host_list_completeness": documents.get(page, {}).get("list_completeness", "unverified"),
            "academic_scope_options": profile.get("academic_scope_options", []),
            "document_access_constraints": constraints,
            "unrequested_discovered_links": list(candidates.values()),
            "public_sources_exhausted": False,
            "blocker_note": "HTTP／登入／提名限制只適用逐份來源；未知年度並非官方尚未公告，其他公開來源未宣稱全部查畢。",
        })
    inputs = ["profile-reviewed-fields.json", "overseas-reviewed-fields.json",
              "partner-document-requirements.json", "overseas-source-registry.json",
              "overseas-source-requests.json", "semantic-review-ledger.json"]
    report = {
        "checked_date": "2026-10-08", "academic_year": "115", "round": "2027春季",
        "definition": "逐校實際取得與欄位映射清冊；未映射不自稱未讀，既有逐欄review也不推整份／全部政策已核。候選href不是政策事實或已驗證可開啟。",
        "input_sha256": {name: hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest() for name in inputs},
        "input_source_json_sha256": {
            sid: hashlib.sha256((BUNDLE / "overseas_sources" / (sid + ".json")).read_bytes()).hexdigest()
            for sid in sources
        },
        "school_count": len(schools), "source_count": len(sources),
        "gap_status_counts": dict(Counter(g["status"] for row in schools for g in row["gaps"].values())),
        "schools": schools,
    }
    assert len(schools) == 55 and len({s["ccu_page"] for s in schools}) == 55
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["school_count", "source_count", "gap_status_counts"]}))


if __name__ == "__main__":
    main()
