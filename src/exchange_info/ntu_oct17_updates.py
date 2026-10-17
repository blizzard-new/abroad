"""Apply the reviewed October 17 references without changing NTU selection capacity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import (DestinationProfile, ExchangeFieldEvidence, PartnerExchangeDetailField,
                     PartnerUniversity, SourceReference, StudentGuideSection)
from .ntu_partner_summary import with_ntu_partner_summary
from .ntu_official_changes import replace_section

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "sources/ntu/2026-10-17-official-update.json"
IDS = {"1115", "974", "931", "1061", "1075", "115", "5", "3", "4", "2", "1", "60",
       "1283", "903", "432", "18", "10", "11", "1291", "1093", "604", "90", "326", "1002", "203"}
UK_IDS = {"1291", "1093", "604", "90"}
SECTION = "【臺大來源補查，2026-10-17】"
GUIDE_KEY = "ntu-source-update-20261017"
LABELS = {"calendar": "行事曆", "deadlines": "接待校提名／申請期限", "language": "接待校語言參考",
          "documents": "接待校文件", "courses": "課程限制", "cost": "費用版本差異", "insurance_visa": "保險／簽證", "housing": "住宿"}


def portal_sections(raw: bytes) -> list[dict]:
    soup = BeautifulSoup(raw, "html.parser")
    return [{"heading": block.select_one(".uninfo-label").get_text(" ", strip=True),
             "text": block.select_one(".uninfo-content").get_text("\n", strip=True),
             "links": [{"text": a.get_text(" ", strip=True), "url": urljoin("https://oia.ntu.edu.tw", a["href"])}
                       for a in block.select_one(".uninfo-content").select("a[href]")]}
            for block in soup.select(".uninfo-awall") if block.select_one(".uninfo-label") and block.select_one(".uninfo-content")]


def load_update(path: Path = SOURCE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("format_version") != 1 or data.get("target_round") != "116-1" or data.get("target_academic_year") != "2027/2028"
            or any(data.get(key) is not False for key in ("formal_quota_changed", "application_open_confirmed", "all_current_cycle_fields_verified"))):
        raise ValueError("October 17 references cannot publish selection availability")
    if data["counts"] != {"partners": 289, "positive": 20, "blank": 262, "zero": 7,
                          "academic_year_units": 43, "maximum_persons": 81}:
        raise ValueError("Unreviewed selection summary")
    bodies = {}
    for sid, src in data["source_manifest"].items():
        target = (ROOT / src["local_file"]).resolve()
        if (not target.is_relative_to((ROOT / "sources/ntu/2026-10-17-official").resolve())
                or src.get("source_id") != sid or src.get("http_status") != 200 or not src.get("checked_at")
                or not src["url"].startswith("https://")):
            raise ValueError("Invalid dated source archive")
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != src["sha256"]:
            raise ValueError("October 17 original source hash changed")
        if target.suffix == ".pdf" and not raw.startswith(b"%PDF-"):
            raise ValueError("PDF source contains a non-PDF response")
        bodies[sid] = raw
    receipt = data["list_receipt"]
    soup = BeautifulSoup(bodies[receipt["source_id"]], "html.parser")
    actual = {}
    for tr in soup.select("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) == 5 and cells[4].find("a"):
            pid = cells[4].find("a")["href"].rsplit("/", 1)[-1]
            actual[pid] = (cells[0].find("a").get_text(" ", strip=True), cells[2].get_text(" ", strip=True), cells[3].get_text(" ", strip=True))
    rows = {r["portal_id"]: r for r in receipt["rows"]}
    old = json.loads((ROOT / "sources/ntu/2026-10-14-official-update.json").read_text())
    prior = {r["portal_id"]: (r["name"], r["quota"], r["headcount"]) for r in old["list_receipt"]["rows"]}
    if (len(rows) != 289 or len(receipt["rows"]) != 289 or actual != prior or "2027/2028" not in soup.get_text()
            or receipt["source_academic_year"] != "2027/2028"
            or actual != {pid: (r["name"], r["quota"], r["headcount"]) for pid, r in rows.items()}
            or receipt["sha256"] != data["source_manifest"][receipt["source_id"]]["sha256"]):
        raise ValueError("Formal selection cells changed; review a new capacity batch")
    if (sum(r["quota"] == "" for r in rows.values()) != 262 or sum(r["quota"] == "0 名" for r in rows.values()) != 7
            or sum(float(r["quota"].removesuffix(" 名")) for r in rows.values() if r["quota"]) != 43
            or sum(int(r["headcount"].removesuffix(" 名")) for r in rows.values() if r["headcount"]) != 81):
        raise ValueError("Formal quota denominator or units changed")
    schools = {s["portal_id"]: s for s in data["schools"]}
    if set(schools) != IDS or len(data["schools"]) != 25:
        raise ValueError("Unreviewed school scope")
    for pid, school in schools.items():
        sections = portal_sections(bodies[school["source_id"]])
        text = BeautifulSoup(bodies[school["source_id"]], "html.parser").get_text()
        pending = "適用於116學年度第1學期之資訊將於甄選開跑前更新完成" in text
        qualification = next(s["text"] for s in sections if s["heading"] == "申請資格")
        if (school["sections"] != sections or school["pending_warning_present"] != pending or pending != (pid not in UK_IDS)
                or school["whole_cycle_confirmed"] is not False or school["formal_selection_quota"] is not None
                or school["platform_after"]["eligibility"] != qualification
                or school["url"] != f"https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/{pid}"
                or data["source_manifest"][school["source_id"]]["url"] != school["url"]
                or data["source_manifest"][school["source_id"]]["sha256"] != school["sha256"]):
            raise ValueError("Portal warning, exact wording or field scope changed")
        if set(school["platform_after"]) != {"eligibility", "degree_levels", "study_period"}:
            raise ValueError("Unreviewed platform field scope")
        expected_year = "2027/2028" if pid == "1291" else "116-1" if pid == "1093" else None
        if school["calendar_academic_year"] != expected_year:
            raise ValueError("A warning-free page does not establish every field year")
    periods = {"974": "2027", "115": "2027/2028", "2": "2026/2027", "1283": "2026/2027", "60": "2027"}
    if {r["portal_id"] for r in data["receiving_references"]} != set(periods):
        raise ValueError("Receiving reference inventory changed")
    for ref in data["receiving_references"]:
        if (ref["source_academic_year"] != periods[ref["portal_id"]] or ref["selection_rule_confirmed"] is not False
                or ref["source_url"] != data["source_manifest"][ref["source_id"]]["url"]
                or ref["source_sha256"] != data["source_manifest"][ref["source_id"]]["sha256"]):
            raise ValueError("Receiving document period or authority changed")
        for fact in ref["facts"]:
            expected = "2026/2027" if ref["portal_id"] == "115" and fact["field"] == "insurance_visa" else ref["source_academic_year"]
            if (fact["academic_year"] != expected or fact["field"] not in LABELS
                    or (fact["page"] is not None and not 1 <= fact["page"] <= ref["page_count"])):
                raise ValueError("Old prices or document pages cannot be relabelled as target-cycle facts")
    event = data["event"]
    if (event["portal_id"] != "1289" or event["registration_deadline"] is not None
            or event["reminder_eligible"] is not False or event["treated_as_application_deadline"] is not False
            or event["home_selection_rule_changed"] is not False
            or event["title"] not in BeautifulSoup(bodies[event["source_id"]], "html.parser").get_text()):
        raise ValueError("An information session cannot become a selection deadline")
    return data


def apply_updates(bundle: Path, path: Path = SOURCE) -> dict:
    data = load_update(path)
    partners = [PartnerUniversity.model_validate_json(r) for r in (bundle / "partners.jsonl").read_text().splitlines()]
    profiles = [DestinationProfile.model_validate_json(r) for r in (bundle / "destination_profiles.jsonl").read_text().splitlines()]
    ledger = json.loads((bundle / "verification_status.json").read_text())
    schools = {s["portal_id"]: s for s in data["schools"]}
    rows = {r["portal_id"]: r for r in data["list_receipt"]["rows"]}
    if len(partners) != 289 or {p.source_url.rsplit("/", 1)[-1] for p in partners} != set(rows):
        raise ValueError("Unexpected partner inventory")
    for p in partners:
        pid = p.source_url.rsplit("/", 1)[-1]; row = rows[pid]
        if p.availability_status == "open" or (row["quota"] == "" and p.quota is not None) or (row["quota"] == "0 名" and p.quota != "0 名"):
            raise ValueError("Selection availability must remain unchanged")
        if row["quota"] not in ("", "0 名"):
            expected = f"{row['quota'].removesuffix(' 名')} 學年名額（最多 {row['headcount'].removesuffix(' 名')} 人次）"
            if p.quota != expected or p.quota_status != "published":
                raise ValueError("Previously published formal capacity changed")
        if pid in schools:
            for key, after in schools[pid]["platform_after"].items():
                if getattr(p, key) not in (schools[pid]["platform_before"][key], after):
                    raise ValueError("Unreviewed platform field baseline")
    by_profile = {p.school_name: p for p in profiles}; by_ledger = {s["portal_id"]: s for s in ledger}
    refs = {r["portal_id"]: r for r in data["receiving_references"]}
    result = []
    for p in partners:
        pid = p.source_url.rsplit("/", 1)[-1]
        school = schools.get(pid)
        if not school and pid != data["event"]["portal_id"]:
            result.append(p); continue
        profile = by_profile[p.school_name]; patch = {}; points = []; urls = [p.source_url]
        if school:
            patch.update(school["platform_after"])
            points = [school["note_zh"], "內頁明示116-1條件尚待確認；正式名額仍以列表為準。" if school["pending_warning_present"] else "內頁無待確認警語；仍逐欄核對年度，正式列表名額空白，不能推論本期開放。"]
            application = p.application_info or ""
            for sec in school["sections"]:
                if sec["heading"] in {"注意事項", "學校年曆", "住宿資訊", "實用資訊", "生活費與保險資訊", "特殊學系語檢要求"}:
                    text = sec["text"] + ("\n官方連結：" + "；".join(x["url"] for x in sec["links"]) if sec["links"] else "")
                    application = replace_section(application, sec["heading"], text)
            patch["reference_data"] = {**p.reference_data, "portal_reference_checked_20261017": school["checked_at"],
                "portal_detail_quota_reference_20261017": next(s["text"] for s in school["sections"] if s["heading"] == "名額"),
                "second_exchange_marker_20261017": "present" if school["second_exchange_marker_present"] else "not_stated"}
            evidence = dict(p.field_evidence)
            for key in ("eligibility", "language"):
                evidence.pop(key, None)
                evidence[key] = ExchangeFieldEvidence(source_url=p.source_url, checked_at=school["checked_at"], status="reference_only", note=points[1])
            patch["field_evidence"] = evidence
            if pid in {"4", "1002"}:
                patch["language_review_note"] = "新制TOEFL明列為對照分數、接待校尚未公布，不能當已公布host門檻。"
                if pid == "1002":
                    patch["language_review_note"] += "Does not accept TOEFL限個別研究所課程，須逐課核對。"
            by_ledger[pid].pop("portal_update_20261017", None)
            by_ledger[pid]["portal_update_20261017"] = school
        else:
            application = p.application_info or ""
        details = dict(p.partner_exchange_details)
        current_fields = {}
        if school and pid in {"1291", "1093", "326", "203"}:
            field = "calendar" if pid in UK_IDS else "housing"
            text = next(s["text"] for s in school["sections"] if s["heading"] == ("學校年曆" if field == "calendar" else "住宿資訊"))
            if field == "housing": text = "保證以期限前完成申請為條件，不表示個人已獲配。\n" + text
            current_fields[field] = PartnerExchangeDetailField(value=text, status="reference_only", reason=points[1], research_category="verified_supported", evidence=[ExchangeFieldEvidence(source_url=p.source_url, checked_at=school["checked_at"], status="reference_only", academic_year=school["calendar_academic_year"] if field == "calendar" else None, note="年度只適用此欄位，不能推及整頁。")])
        if ref := refs.get(pid):
            urls.append(ref["source_url"])
            for field in sorted({f["field"] for f in ref["facts"]}):
                facts = [f for f in ref["facts"] if f["field"] == field]
                text = "\n".join(f["text_zh"] for f in facts)
                status = "conflict" if pid == "1283" and field == "cost" else "reference_only"
                evidence = [ExchangeFieldEvidence(source_url=ref["source_url"], source_pages=sorted({f["page"] for f in facts if f["page"]}), academic_year=facts[0]["academic_year"], checked_at=ref["checked_at"], status=status, excerpt="；".join(f["source_excerpt"] for f in facts), note="海外接收參考；依文件自身年度／段落，不替代臺大甄選或名額。")]
                if status == "conflict":
                    evidence.append(ExchangeFieldEvidence(source_url=p.source_url, checked_at=school["checked_at"], status="conflict", note="臺大HTML仍為舊預算；年份不同，不選一方當本期金額。"))
                current_fields[field] = PartnerExchangeDetailField(value=text, status=status, reason="海外接收參考，非臺大本期甄選規則；保留來源期間與版本。", evidence=evidence, research_category="unresolved_source_conflict" if status == "conflict" else "verified_supported")
                for f in facts:
                    location = f"PDF第{f['page']}頁" if f["page"] else f"段落{f['section']}"
                    points.append(f"{location}（{f['academic_year']}接收參考）：{f['text_zh']}")
            by_ledger[pid].pop("receiving_reference_20261017", None)
            by_ledger[pid]["receiving_reference_20261017"] = ref
        for field in sorted(current_fields):
            details.pop(field, None); details[field] = current_fields[field]
            entry = by_ledger[pid]["fields"].setdefault(field, {"label": LABELS[field], "source_urls": [], "remaining_questions": []})
            entry.pop("source_update_20261017", None)
            entry["source_update_20261017"] = current_fields[field].model_dump(mode="json")
        if current_fields: patch["partner_exchange_details"] = details
        if pid == data["event"]["portal_id"]:
            event = data["event"]
            points = ["交換相關活動：哥廷根大學說明會，2026/10/30 12:30–14:00（Asia/Taipei），臺大禮賢樓7樓國際事務處。",
                      "講者Dr. Frank Stiller；臺大官方首頁提供活動報名表連結。",
                      "表單未見報名截止日；不構成甄選名額、資格或截止異動，不啟用正式申請期限提醒。"]
            urls = [event["homepage_url"], event["registration_url"]]
            by_ledger[pid].pop("information_session_20261017", None)
            by_ledger[pid]["information_session_20261017"] = event
        application = re.sub(re.escape(SECTION) + r"\n.*?(?=\n\n【|\Z)", "", application, flags=re.S).strip()
        patch["application_info"] = SECTION + "\n" + "\n".join(points) + "\n來源：" + "；".join(urls) + "\n\n" + application
        guides = [g for g in profile.student_guide_sections if g.key != GUIDE_KEY]
        guides.append(StudentGuideSection(key=GUIDE_KEY, title="臺大來源補查（2026-10-17）", summary="按欄位年度與來源角色保存；正式名額及校內截止未變。", points=points, source_urls=urls, caution="待確認、舊年度、對照分數及來源衝突各自保留；不表示錄取或本期開放。"))
        sources = [s for s in profile.sources if s.title != "臺大來源補查（2026-10-17）"]
        sources.append(SourceReference(title="臺大來源補查（2026-10-17）", source_url=urls[0], summary="原件與欄位適用期間另列；非全面116-1核准。"))
        by_profile[p.school_name] = profile.model_copy(update={"student_guide_sections": guides, "sources": sources})
        result.append(with_ntu_partner_summary(p.model_copy(update=patch)))
    outputs = {"partners.jsonl": "".join(p.model_dump_json() + "\n" for p in result),
               "destination_profiles.jsonl": "".join(by_profile[p.school_name].model_dump_json() + "\n" for p in profiles),
               "verification_status.json": json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
               "list_verification.json": json.dumps(data["list_receipt"], ensure_ascii=False, indent=2) + "\n"}
    for filename in ("catalog-completeness.json", "import_provenance.json"):
        payload = json.loads((bundle / filename).read_text())
        payload["source_update_20261017"] = {"source_snapshot": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "checked_at": data["checked_at"], "detail_pages": 25, "pending_warning_pages": 21, "warning_free_UK_pages": 4, "formal_quota_changed": False, "all_current_cycle_fields_verified": False}
        if filename == "catalog-completeness.json": payload["latest_official_list_checked_at"] = data["list_receipt"]["checked_at"]
        outputs[filename] = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for filename, content in outputs.items(): (bundle / filename).write_text(content, encoding="utf-8")
    return {"updated_portals": 25, "receiving_references": len(refs), "information_sessions": 1, "formal_quota_changed": False}
