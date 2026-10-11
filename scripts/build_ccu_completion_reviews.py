"""Build source-backed general profiles for the entire CCU exchange-list.

General campus/service evidence and historical mother-list excerpts never imply
current incoming eligibility. Existing 55-school reviews are preserved verbatim.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fetch_ccu_completion_sources import BUNDLE as B
from fetch_ccu_completion_sources import OUT

from exchange_info.models import DestinationProfile

PROFILE_KEYS = ["city", "location", "website", "degree_levels", "colleges", "transport", "campus_life"]
HOST_KEYS = ["program_scope", "eligibility", "language", "nomination_deadline", "application_deadline", "documents", "application_forms", "academic_calendar", "course_restrictions", "housing", "housing_deadline", "costs", "insurance", "visa", "arrival", "host_tuition", "exchange_duration"]
GENERAL = "一般公開校園／官方服務入口，查核2026-10-11；非2027春季接收規定"


def load(name):
    return json.loads((B / name).read_text())


def empty(reason):
    return {"status": "missing", "value": None, "reason": reason, "evidence": []}


def from_receipt(receipt, quote, *, year=GENERAL, pages=None, status="verified_current"):
    return {"source_id": receipt["source_id"], "source_url": receipt["source_url"],
            "source_pages": pages or [], "excerpt": quote, "academic_year": year,
            "application_round": "一般參考；接收梯次另核", "checked_at": receipt["checked_at"],
            "content_hash": receipt["sha256"], "status": status}


def fact(value, ev, reason, status="verified_current"):
    return {"status": status, "value": value, "reason": reason, "evidence": ev}


def main():
    partners = [json.loads(line) for line in (B / "partners.jsonl").read_text().splitlines()]
    profiles = {r["ccu_page"]: r for r in load("profile-reviewed-fields.json")}
    hosts = {r["ccu_page"]: r for r in load("overseas-reviewed-fields.json")}
    targets = {r["ccu_page"]: r for r in load("completion-targets.json")}
    assets = {r["ccu_page"]: r for r in load("campus-assets.json")["schools"]}
    all_rows = []
    for partner in partners:
        page = partner["source_pages"][0]
        profile = {k: empty("尚未從已讀公開正文取得此欄；不是官方明示尚未公告。") for k in PROFILE_KEYS}
        host = {k: empty("未核實2027春季接收政策；本期未開放參考校，不以舊年度補值。") for k in HOST_KEYS}
        if page in profiles:
            profile = profiles[page]["fields"].copy()
            host = hosts[page]["fields"].copy()
        root_label = "root-alternative" if page in {15, 40} else "campus-specific" if page == 51 else "root"
        receipt = load(f"completion_sources/p{page}-{root_label}.receipt.json")
        title = receipt.get("title") or ""
        usable = receipt.get("http_status") == 200 and title and not any(s in title.casefold() for s in ["anubis", "bot challenge", "not a bot", "making sure", "에러", "access denied", "processing"])
        general = {k: empty("尚未從已取得的一般公開校園來源核實；不表示官方明示尚未公告。") for k in PROFILE_KEYS}
        if usable:
            ev = from_receipt(receipt, title)
            general["website"] = fact(targets[page]["website"], [ev], "官方校名／網域與母校名冊身份核對；正文可讀。與接收表單及登入入口分開。")
            text_path = OUT / f"p{page}-{root_label}.txt"
            text = text_path.read_text() if text_path.exists() else ""
            address = re.search(r'(?:地址[：:]\s*|Address\s*[:：]\s*)([^©]{12,160})', text)
            if address:
                quote = address.group(0).split("版权所有")[0].split("電話")[0].split("电话")[0].strip()
                general["location"] = fact(quote, [from_receipt(receipt, quote)], "官方公開聯絡地址；不等於個人接收校區或宿舍分配。")
            service_links = []
            transport_links = []
            for link in receipt.get("links", []):
                label, url = link["label"], link["url"]
                if not label or not url.startswith(("https://", "http://")) or label not in text:
                    continue
                if re.search(r'(?i)^(?:library|libraries|student life|student support|campus living|campus housing|clubs(?: & activities)?|accommodation|sports(?: and fitness)?|health & wellness|campus life|圖書館|图书馆|心理咨询|校医院|校园安全|學生社團|学生会|宿舍|住宿|thư viện|ký túc xá|biblioteca|bibliotecas|studentský život|sport na vut)$', label.strip()) and link not in service_links:
                    service_links.append(link)
                if re.search(r'(?i)^(?:directions|transportation and parking|transportation|交通指南|交通|交通アクセス|오시는길|getting here|getting there|sơ đồ đến trường|transporte)$', label.strip()) and link not in transport_links:
                    transport_links.append(link)
            for key, links in [("campus_life", service_links), ("transport", transport_links)]:
                if links:
                    general[key] = fact("官方公開入口：" + "；".join(l["label"] for l in links[:6]),
                                        [from_receipt(receipt, l["label"]) | {"service_url": l["url"]} for l in links[:6]],
                                        "只核實一般服務／交通入口存在；可用身份、服務時間、費率、交換生床位與2027安排另核，沒有據此推估。")
        coordinate = assets[page]["coordinates"]
        if coordinate["status"] == "verified_current":
            general["city"] = fact(coordinate["value"]["city"], coordinate["evidence"], coordinate["value"]["note"])
        # Mother gray text is explicitly historical, not newly confirmed host policy.
        if page not in hosts:
            mapping = {"eligibility": "eligibility", "language": "language_requirement", "documents": "partner_documents", "application_forms": "fact_sheet", "program_scope": "eligibility", "exchange_duration": "study_period"}
            for key, mother_key in mapping.items():
                ev = partner["field_evidence"].get(mother_key, {})
                quote = ev.get("reference_excerpt")
                if quote:
                    ev = {**ev, "excerpt": quote, "academic_year": "母校名冊灰字历史資料，未核实原適用年度", "application_round": "歷史參考；2027春季本期未開放", "status": "reference_only"}
                    host[key] = fact(quote, [ev], "母校歷史灰字摘錄，只提供既有協議／文件線索；本期不可申請，不作當期必備資料。", "reference_only")
            for key, mother_key in [("degree_levels", "eligibility"), ("colleges", "notes")]:
                ev = partner["field_evidence"].get(mother_key, {})
                quote = ev.get("reference_excerpt")
                if quote:
                    profile[key] = fact(quote, [{**ev, "excerpt": quote, "academic_year": "歷史灰字；學制／院系限制參考", "status": "reference_only"}], "保存原文限制；未解析為当期可選學制／學院。", "reference_only")
        # Fill empty/non-current profile facts with independently dated general evidence.
        for key, field in general.items():
            if field["status"] == "verified_current" and profile[key]["status"] != "verified_current":
                profile[key] = field
        all_rows.append({"ccu_page": page, "school_name": partner["school_name"], "country": partner["country"],
                         "availability_status": partner["availability_status"], "application_window_status": partner["application_window_status"],
                         "profile_fields": profile, "general_campus_fields": general, "host_fields": host,
                         "review_note": "104交換名冊全量逐欄盤點；未開放校即使接待資訊載明2027，也不變更母校當期可選名單。"})
    manual = B / "completion-manual-fields.json"
    if manual.exists():
        for item in json.loads(manual.read_text())["schools"]:
            row = next(r for r in all_rows if r["ccu_page"] == item["ccu_page"])
            for scope in ["host_fields", "profile_fields", "general_campus_fields"]:
                row[scope].update(item.get(scope, {}))
            if item.get("expose_host_overrides"):
                row["host_override_keys"] = sorted(item.get("host_fields", {}))
    (B / "completion-reviewed-fields.json").write_text(json.dumps({"checked_at": "2026-10-11", "schools": all_rows}, ensure_ascii=False, indent=2) + "\n")
    # Preserve every existing 55 profile line byte for byte; append 49 new profiles.
    original_names = {row["school_name"] for row in profiles.values()}
    original_lines = [line for line in (B / "destination_profiles.jsonl").read_bytes().splitlines(keepends=True)
                      if json.loads(line)["school_name"] in original_names]
    if len(original_lines) != 55 or len({json.loads(line)["school_name"] for line in original_lines}) != 55:
        raise ValueError("Preserve exactly 55 independent original CCU profiles before appending references")
    baseline = b"".join(original_lines)
    extra = []
    for row in all_rows:
        if row["ccu_page"] in profiles:
            continue
        fields = row["profile_fields"]
        sources = []
        for key in ["city", "location", "website", "transport", "campus_life"]:
            for ev in fields[key]["evidence"]:
                if ev["source_url"] not in {s["source_url"] for s in sources}:
                    sources.append({"title": "CCU一般校園／生活公開來源", "source_url": ev["source_url"], "category": "partner_school", "summary": fields[key]["reason"]})
        profile = DestinationProfile(home_university="國立中正大學", school_name=row["school_name"], country=row["country"],
                                     city=fields["city"]["value"], transport_summary=fields["transport"]["value"], campus_life_summary=fields["campus_life"]["value"],
                                     sources=sources, last_checked=max([e["checked_at"] for f in row["general_campus_fields"].values() for e in f["evidence"]], default=None),
                                     coverage_status="official_partial", coverage_note="本期未開放交換參考校；已補官方校園及服務資料。當期住宿費用、接收條件和完整文件尚未核實，不能據此申請。")
        extra.append(profile.model_dump_json().encode())
    (B / "destination_profiles.jsonl").write_bytes(baseline + b"\n".join(extra) + b"\n")
    print("reviewed identities", len(all_rows), "destination profiles", len(profiles) + len(extra))


if __name__ == "__main__":
    main()
