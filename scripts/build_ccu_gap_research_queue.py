"""Keep an immutable follow-up baseline and explicit unresolved-research reasons.

Failed requests are evidence about that URL, not proof that a university has no
public information. Access requirements and official non-publication need direct
content evidence; the default is research_incomplete.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ccu"
BASELINE = "cf4d86f22d89ee698315d46177daf00b49dd8706"
COORDINATES = {68, 71, 74, 79, 88, 105, 107, 111, 119}
PHOTOS = {66, 68, 71, 77, 80, 104, 119}
WEBSITES = {44, 72, 96}


def build():
    reviewed = json.loads((BUNDLE / "completion-reviewed-fields.json").read_text())["schools"]
    assets = {r["ccu_page"]: r for r in json.loads((BUNDLE / "campus-assets.json").read_text())["schools"]}
    sources = []
    for path in sorted((BUNDLE / "completion_sources").glob("*.receipt.json")):
        source = json.loads(path.read_text())
        if "ccu_page" not in source:
            if not path.name.startswith("global-"):
                continue
            source = {**source, "ccu_page": 0, "source_id": path.name.removesuffix(".receipt.json")}
        sources.append(source)
    attempts = {}
    for source in sources:
        attempt = {key: source.get(key) for key in ["source_id", "source_url", "checked_at", "http_status", "error", "title", "sha256", "bundled_file"]}
        blocked = any(term in (source.get("title") or "").lower() for term in ["not a bot", "anubis", "access denied"])
        attempt["classification"] = "source_failure" if source.get("error") or source.get("http_status") != 200 or blocked else "acquired_not_policy_verified"
        attempts.setdefault(source["ccu_page"], []).append(attempt)
    rows = []
    for school in reviewed:
        page = school["ccu_page"]
        requested_assets = (["coordinates"] if page in COORDINATES and assets[page]["coordinates"]["status"] != "verified_current" else []) + (["photo"] if page in PHOTOS and assets[page]["photo"]["status"] != "verified_current" else []) + (["website"] if page in WEBSITES and school["general_campus_fields"]["website"]["status"] != "verified_current" else [])
        missing = [key for key, field in school["host_fields"].items() if field["status"] == "missing"]
        if requested_assets or missing:
            rows.append({
                "ccu_page": page, "school_name": school["school_name"], "country": school["country"],
                "availability_status": school["availability_status"], "requested_assets": requested_assets,
                "unresolved_host_fields": [{"field": key, "classification": "research_incomplete", "reason": "尚未完成此欄的當期公開來源研究；已有失敗請求不證明全校資訊不存在。", "official_not_announced": False, "personal_access_required": None} for key in missing],
                "attempted_sources": attempts.get(page, []),
            })
    return {"baseline_commit": BASELINE, "checked_at": "2026-10-11", "scope": "First delivery follow-up baseline; not an exhaustive source search", "classification_definitions": {
        "official_not_announced": "官方正文直接明示適用梯次資料尚未公告，保存原文及頁碼。",
        "personal_access_required": "實際入口要求提名後個人登入／帳號，保存入口及明示文字；不把 HTTP 403 自動視為個人權限。",
        "source_failure": "保存 URL、查核時間、HTTP／TLS／錯誤頁；僅此來源當時不可讀。",
        "research_incomplete": "尚未完成可公開來源研究，或沒有足以證明其他三種分類的直接依據。",
    }, "initial_counts": {"coordinate_gaps": sum("coordinates" in r["requested_assets"] for r in rows), "licensed_photo_gaps": sum("photo" in r["requested_assets"] for r in rows), "website_identity_gaps": sum("website" in r["requested_assets"] for r in rows), "host_missing_fields": sum(len(row["unresolved_host_fields"]) for row in rows)}, "schools": rows, "global_agreements": {"denominator": None, "classification": "source_failure", "reason": "官方全球頁可讀，但Gamma公開應用殼未含清單；匿名snapshot的FORBIDDEN只說明該請求不可讀，未證明完整公開文件需本人權限。", "attempted_sources": attempts.get(0, [])}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    result = build()
    stem = "completion-followup-gap-baseline" if args.baseline else "completion-followup-gap-research"
    target = BUNDLE / (stem + ".json")
    if args.baseline and target.exists():
        raise SystemExit("Preserve the immutable first-delivery follow-up baseline")
    if args.baseline:
        assert result["initial_counts"]["host_missing_fields"] == 702
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    with target.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["ccu_page", "school_name", "country", "availability_status", "gap", "classification", "attempted_source_ids"])
        for school in result["schools"]:
            ids = ";".join(source["source_id"] for source in school["attempted_sources"])
            for gap in school["requested_assets"]:
                writer.writerow([school["ccu_page"], school["school_name"], school["country"], school["availability_status"], gap, "research_incomplete", ids])
            for gap in school["unresolved_host_fields"]:
                writer.writerow([school["ccu_page"], school["school_name"], school["country"], school["availability_status"], gap["field"], gap["classification"], ids])
    print(json.dumps(result["initial_counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
