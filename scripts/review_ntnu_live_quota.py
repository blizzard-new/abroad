"""Bind all NTNU 116-1 public pages to the archived contracts and displayed quota fields.

The receipt cache is read-only. This creates a new, immutable review manifest;
it does not certify host admission conditions or modify the official bundle.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/data-verification-20261021"
OUTPUT = ROOT / "output/data-verification-20261021"
LIST_URL = "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist"
GUIDE_URL = "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf"


def hash_value(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def reviewed_pages():
    receipts = [json.loads(s) for s in (DOCS / "round39-source-receipts.jsonl").read_text("utf8").splitlines() if s.strip()]
    pages, sources = {}, {}
    for receipt in receipts:
        url = receipt["url"]
        if url != LIST_URL and "/api/v1/oe/requirementHistory?" not in url:
            continue
        raw = gzip.decompress((OUTPUT / "source-cache/bodies" / (receipt["sha256"] + ".gz")).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == receipt["sha256"]
        assert receipt["transport_result"] == "retrieved" and receipt["status_code"] == 200
        if url == LIST_URL:
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', raw.decode(), re.S)
            data = json.loads(match.group(1))["props"]["pageProps"]["pageData"]
            page = 1
        else:
            response = json.loads(raw)
            assert response["header"]["status"] == "OK"
            data = response["body"]
            page = int(parse_qs(urlparse(url).query)["pageNo"][0])
        assert str(data["term"]) == "1161"
        assert data["pageMeta"] == {"total_page": 29, "current_page_no": page, "item_per_page": 10}
        assert len(data["schools"]) == (5 if page == 29 else 10)
        assert page not in pages
        pages[page], sources[page] = data["schools"], receipt
    assert sorted(pages) == list(range(1, 30))
    live = [row for page in range(1, 30) for row in pages[page]]
    archive_path = ROOT / "sources/ntnu/quotalist_1161.json"
    archive = json.loads(archive_path.read_text("utf8"))
    assert live == archive, "Re-review changed current contracts before generating corrections"
    keys = [(r["school_no"], r["contract_level"], r["organizer"]) for r in live]
    assert len(keys) == len(set(keys)) == 285
    return live, sources, next(r for r in reversed(receipts) if r["url"] == GUIDE_URL)


def strings(value, pointer=""):
    if isinstance(value, str):
        yield pointer, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from strings(item, f"{pointer}/{index}")
    elif isinstance(value, dict):
        for key, item in value.items():
            if key == "reference_data":
                continue
            key = key.replace("~", "~0").replace("/", "~1")
            yield from strings(item, f"{pointer}/{key}")


def main():
    target = DOCS / "round39-ntnu-live-quota-review.json"
    assert not target.exists(), "Do not overwrite an earlier review"
    live, receipts, guide = reviewed_pages()
    now = datetime.now(timezone.utc).isoformat()
    groups = defaultdict(list)
    page_by_key = {}
    for index, row in enumerate(live):
        groups[row["school_no"]].append(row)
        page_by_key[(row["school_no"], row["contract_level"], row["organizer"])] = index // 10 + 1
    files = {}
    for name in ("partners.jsonl", "application_workflows.jsonl", "destination_profiles.jsonl"):
        relative = "src/exchange_info/official_data/ntnu/" + name
        files[relative] = [json.loads(s) for s in (ROOT / relative).read_text("utf8").splitlines() if s.strip()]
    partners = files["src/exchange_info/official_data/ntnu/partners.jsonl"]
    by_name = {r["school_name"]: r for r in partners}
    schools, scopes = [], []
    reason = "116-1 全部 29 頁已比對；-- 是名額待確認、0 是該合約不開放；不同辦理單位名額不能視為全校通用。"
    for school_no, contracts in groups.items():
        full_name = f"{contracts[0]['school_name_ch'].strip()} {contracts[0]['school_name_en'].strip()}"
        matches = [p for p in partners if p["school_name"] == full_name]
        assert len(matches) == 1, (school_no, full_name)
        partner = matches[0]
        quota_values = [str(c["school_quota"]).strip() for c in contracts]
        positive = any(q.isdigit() and int(q) > 0 for q in quota_values)
        pending = any(q == "--" for q in quota_values)
        assert all(q == "--" or q.isdigit() for q in quota_values)
        category = "mixed_positive_pending" if positive and pending else "positive_only" if positive else "pending" if pending else "zero_only"
        quota_status = "published" if positive else "not_published" if pending else "zero"
        availability = "needs_confirmation" if pending else "open" if positive else "zero_quota"
        details = []
        for c, q in zip(contracts, quota_values):
            label = f"{c['contract_level']}（{c['organizer']}）"
            details.append(label + ("名額待確認" if q == "--" else "0 名，本期不開放" if q == "0" else f"{q} 名"))
        quota = "116-1：" + "；".join(details) + "。各合約分開適用，不將不同院系名額合併為可共用名額。"
        note = "2026-10-21 核對臺師大 116-1 官方名額列表。" + quota
        if pending:
            note += "含待確認合約，須先確認自己所屬的校級／院系管道。"
        note += "校級線上申請排定 2026/11/01–11/15；院系所自行辦理的期限須另洽該單位。名額與申請時間、資格審查分開判斷。"
        only_university = all(c["contract_level"] == "校級" for c in contracts)
        # The reviewed PDF is a university-level call. It does not establish
        # the deadline of every departmental agreement in this mixed directory.
        window = "upcoming" if only_university else "needs_confirmation"
        school = {"school_no": school_no, "school_name": partner["school_name"], "country": partner["country"],
                  "category": category, "quota_status": quota_status, "availability_status": availability,
                  "application_window_status": window, "contract_rows": contracts,
                  "source_pages": [page_by_key[(c["school_no"], c["contract_level"], c["organizer"])] for c in contracts]}
        schools.append(school)
        old_quota = partner["quota"]
        for relative, records in files.items():
            for row in records:
                if (row["school_name"], row.get("country")) != (partner["school_name"], partner.get("country")):
                    continue
                changes = {pointer: (value, value.replace(old_quota, quota)) for pointer, value in strings(row)
                           if old_quota in value and old_quota != quota}
                if relative.endswith("/partners.jsonl"):
                    for key, value in {"quota": quota, "quota_status": quota_status, "availability_status": availability,
                                       "availability_note": note, "application_window_status": window}.items():
                        if row.get(key) != value:
                            changes["/" + key] = (row.get(key), value)
                if relative.endswith("/application_workflows.jsonl"):
                    # Publication is preserved, but this source comparison
                    # cannot certify the entire inherited workflow.
                    for key, value in {"applicability_status": "needs_confirmation", "coverage_status": "official_partial",
                                       "applicability_note": "本輪只核對 116-1 名額與校級申請日期；學程資格及完整流程尚未逐項核實。"}.items():
                        if row.get(key) != value:
                            changes["/" + key] = (row.get(key), value)
                if not changes:
                    continue
                patches = []
                for pointer, (old, new) in changes.items():
                    window_patch = pointer == "/application_window_status"
                    patches.append({"pointer": pointer, "expected_values": [old], "expected_missing": old is None,
                                    "value": new, "reason": reason if not window_patch else "甄選簡章只明列校級申請；11/1 開始，不能標作已開放，也不能套到所有院系所。",
                                    "source_url": GUIDE_URL if window_patch else LIST_URL,
                                    "source_sha256": guide["sha256"] if window_patch else receipts[school["source_pages"][0]]["sha256"],
                                    "source_locator": "PDF p.3 (printed p.2)" if window_patch else f"1161 contract pages {school['source_pages']}; school_no={school_no}"})
                scopes.append({"home_id": "ntnu", "school_name": row["school_name"], "country": row.get("country"),
                               "file": relative, "patches": patches})
    manifest = {"reviewed_at": now, "scope": "Live NTNU 116-1 contract identity/quota comparison; not full host requirements",
                "all_pages": [{"page": page, **r} for page, r in sorted(receipts.items())], "guidelines": guide,
                "guideline_visual_pages": [3], "archive_file": "sources/ntnu/quotalist_1161.json",
                "archive_sha256": hashlib.sha256((ROOT / "sources/ntnu/quotalist_1161.json").read_bytes()).hexdigest(),
                "archive_equals_live_including_program_fields": True, "contracts": 285, "schools": schools,
                "contract_quota_counts": dict(Counter(str(c["school_quota"]) for c in live)),
                "school_categories": dict(Counter(s["category"] for s in schools)),
                "rows": scopes, "patch_count": sum(len(s["patches"]) for s in scopes), "whole_schools_verified": 0,
                "limitations": ["Source fidelity is not independent verification of every host condition.",
                                "The 116-1 PDF covers university-level selection, not all departmental deadlines.",
                                "115-2/115-1 program conditions remain historical; round38 markers are preserved."]}
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf8")
    with (DOCS / "round39-ntnu-contract-quota-scope.csv").open("w", encoding="utf-8-sig", newline="") as f:
        columns = ["school_no", "school_name_ch", "school_country", "contract_level", "organizer", "school_quota"]
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows({k: row[k] for k in columns} for row in live)
    print(json.dumps({"manifest_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                      "patches": manifest["patch_count"], "rows": len(scopes), "categories": manifest["school_categories"]}))


if __name__ == "__main__":
    main()
