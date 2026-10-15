"""Replay source-backed NTU updates after the immutable historical overlays."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from .models import DestinationProfile, ExchangeFieldEvidence, PartnerExchangeDetailField, PartnerUniversity, SourceReference, StudentGuideSection
from .ntu_partner_summary import with_ntu_partner_summary

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "sources/ntu/2026-10-14-official-update.json"
SECTION = "【臺大來源更新，2026-10-14】"
LEGACY_SECTION = "【接待校公開來源補查，2026-10-11】"
GUIDE_KEY = "ntu-current-source-update-20261014"
QUOTA_IDS = {
    "998", "1302", "1103", "1194", "71", "72", "74", "69",
    "1286", "1200", "98", "380", "391", "247", "1040", "606", "375", "85", "371", "89",
}
ZERO_UPDATE_IDS = {"599"}
VISA_IDS = {"1307", "206", "313", "1109", "210", "97", "95", "96", "94", "93", "92"}
LIST_URL = "https://oia.ntu.edu.tw/outgoing/school.list"
HISTORICAL_LIST_NAMES = {
    "369": {"夏威夷大學希羅分校", "夏威夷大學希羅分校（E交換學生計畫、V訪問學生計畫）"},
}


def load_update(path: Path = SOURCE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("format_version") != 1 or data.get("academic_year") != "116"
            or data.get("source_academic_year") != "2027/2028" or data.get("outgoing_semester") != 1
            or data.get("application_open_confirmed") is not False
            or data.get("all_current_cycle_fields_verified") is not False):
        raise ValueError("NTU updates cannot approve unverified availability or an entire cycle")
    manifest = data["source_manifest"]
    bodies = {}
    for sid, source in manifest.items():
        target = (ROOT / source["local_file"]).resolve()
        if (not target.is_relative_to((ROOT / "sources/ntu/2026-10-14-official").resolve())
                or source.get("source_id") != sid or source.get("http_status") != 200
                or urlsplit(source["url"]).scheme != "https" or not source.get("checked_at")):
            raise ValueError("Every update requires a dated official source archive")
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError("Official source archive hash changed")
        bodies[sid] = raw
    receipt = data["list_receipt"]
    source = manifest[receipt["source_id"]]
    if (source["url"] != LIST_URL or receipt["url"] != LIST_URL
            or source["sha256"] != receipt["sha256"] or receipt["http_status"] != 200
            or receipt["source_academic_year"] != "2027/2028"):
        raise ValueError("Selection quotas must come from the NTU current-year list")
    soup = BeautifulSoup(bodies[receipt["source_id"]], "html.parser")
    if "2027/2028" not in soup.get_text():
        raise ValueError("The archived list does not establish the selection year")
    actual = {}
    for tr in soup.select("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) != 5 or not cells[4].find("a"):
            continue
        pid = urljoin(LIST_URL, cells[4].find("a")["href"]).rsplit("/", 1)[-1]
        actual[pid] = (cells[0].find("a").get_text(" ", strip=True),
                       cells[2].get_text(" ", strip=True), cells[3].get_text(" ", strip=True))
    rows = {r["portal_id"]: r for r in receipt["rows"]}
    if (len(rows) != 288 or len(receipt["rows"]) != 288
            or actual != {pid: (r["name"], r["quota"], r["headcount"]) for pid, r in rows.items()}):
        raise ValueError("The 288-school receipt must match the archived list cells")
    updates = {r["portal_id"]: r for r in data["quota_updates"]}
    positive = {pid for pid, r in rows.items() if r["quota"] not in ("", "0 名")}
    if positive != QUOTA_IDS or set(updates) != positive or len(data["quota_updates"]) != 20:
        raise ValueError("A changed formal quota inventory requires a new source review")
    for pid, update in updates.items():
        row = rows[pid]
        detail = manifest[update["detail_source_id"]]
        quota = update["quota_academic_years"]
        maximum = update["maximum_persons"]
        if (type(quota) is not int or type(maximum) is not int or quota <= 0 or maximum <= 0
                or update["quota_original"] != row["quota"] or row["quota"] != f"{quota} 名"
                or update["maximum_persons_original"] != row["headcount"] or row["headcount"] != f"{maximum} 名"
                or update["school_name"] != row["name"] or update["country"] != row["country"]
                or update["list_source_id"] != receipt["source_id"]
                or update["application_open_confirmed"] is not False
                or update["quota_display"] != f"{quota} 學年名額（最多 {maximum} 人次）"
                or detail["url"] != f"https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/{pid}"):
            raise ValueError("Quota units, source identity or maximum headcount changed")
        detail_soup = BeautifulSoup(bodies[update["detail_source_id"]], "html.parser")
        sections = {b.select_one(".uninfo-label").get_text(" ", strip=True): b.select_one(".uninfo-content").get_text("\n", strip=True)
                    for b in detail_soup.select(".uninfo-awall") if b.select_one(".uninfo-label") and b.select_one(".uninfo-content")}
        if (sections.get("名額") != update["exchange_duration_original"]
                or not any(
                    token in sections["名額"]
                    for token in (
                        "可選擇交換一學期或一學年，限於本校第一學期出國交換",
                        "可選擇一學期或一學年，限於本校第1學期出國交換",
                        "限定交換一學年人數",
                    )
                )):
            raise ValueError("Exchange duration must retain the official detail-page scope")
    if (sum(r["quota"] == "" for r in rows.values()) != 261
            or sum(r["quota"] == "0 名" for r in rows.values()) != 7
            or sum(r["quota_academic_years"] for r in updates.values()) != 43
            or sum(r["maximum_persons"] for r in updates.values()) != 81):
        raise ValueError("Selection totals changed")
    if {r["portal_id"] for r in data["visa_reminders"]} != VISA_IDS or len(data["visa_reminders"]) != 11:
        raise ValueError("Visa reminder scope changed")
    for reminder in data["visa_reminders"]:
        if (reminder["legal_rule_independently_verified"] is not False or reminder["selection_rule_confirmed"] is not False
                or reminder["original_quote"].split("Student Visa")[0].strip() not in
                " ".join(BeautifulSoup(bodies[reminder["source_id"]], "html.parser").get_text(" ", strip=True).split())):
            raise ValueError("A portal reminder cannot be promoted to an independently verified legal rule")
    ubc = data["ubc_update"]
    if (ubc["portal_id"] != "1" or ubc["source_academic_year"] != "2027/2028"
            or ubc["selection_rule_confirmed"] is not False or ubc["new_fee_amount_first_discovery"] is not False
            or manifest[ubc["source_id"]]["sha256"] != ubc["source_sha256"]
            or ubc["source_sha256"] != "720e42df05035fb9c355dc698b07ee21781a0863ee484f0ffc2728a62138a8b5"
            or any(r["pdf_page"] not in {2, 3, 5, 6} for r in ubc["facts"])):
        raise ValueError("UBC annual reference must retain its document scope")
    return data


def historical_selection_view(partners: list[PartnerUniversity]) -> list[PartnerUniversity]:
    """Validate older immutable snapshots against their original selection cells."""
    if not SOURCE.exists():
        return partners
    loaded = load_update()
    updates = {r["portal_id"]: r for r in loaded["quota_updates"]}
    zero_updates = {r["portal_id"]: r for r in loaded.get("zero_quota_updates", [])}
    result = []
    for partner in partners:
        pid = partner.source_url.rsplit("/", 1)[-1]
        update = updates.get(pid)
        z_update = zero_updates.get(pid)
        if update and partner.quota is not None:
            if partner.quota != update["quota_display"] or partner.quota_status != "published":
                raise ValueError("Only exactly source-backed later NTU quotas may supersede the historical blank")
            result.append(partner.model_copy(update={"quota": None}))
        elif z_update and partner.quota == "0 名":
            result.append(partner.model_copy(update={"quota": None}))
        else:
            result.append(partner)
    return result


def apply_current_updates(bundle: Path, path: Path = SOURCE) -> dict:
    data = load_update(path)  # Validate the complete batch before any write.
    partners = [PartnerUniversity.model_validate_json(line) for line in (bundle / "partners.jsonl").read_text().splitlines()]
    rows = {r["portal_id"]: r for r in data["list_receipt"]["rows"]}
    if len(partners) != 288 or {p.source_url.rsplit("/", 1)[-1] for p in partners} != set(rows):
        raise ValueError("NTU partner identity inventory changed")
    for p in partners:
        pid = p.source_url.rsplit("/", 1)[-1]
        row = rows[pid]
        allowed_names = HISTORICAL_LIST_NAMES.get(pid, {row["name"]})
        if p.school_name not in allowed_names or p.country != row["country"]:
            raise ValueError("NTU identity or country mismatch")
        if pid in QUOTA_IDS:
            allowed = {None, next(r["quota_display"] for r in data["quota_updates"] if r["portal_id"] == pid)}
        elif pid in ZERO_UPDATE_IDS:
            allowed = {None, "0 名"}
        else:
            allowed = {row["quota"] or None}
        if p.quota not in allowed or p.availability_status == "open":
            raise ValueError("Unreviewed selection quota or availability changed")
    quotas = {r["portal_id"]: r for r in data["quota_updates"]}
    zero_quotas = {r["portal_id"]: r for r in data.get("zero_quota_updates", [])}
    visas = {r["portal_id"]: r for r in data["visa_reminders"]}
    references = {r["portal_id"]: r for r in data["reference_updates"]}
    ubc = data["ubc_update"]
    profiles = [DestinationProfile.model_validate_json(line) for line in (bundle / "destination_profiles.jsonl").read_text().splitlines()]
    profile_map = {p.school_name: p for p in profiles}
    ledger = json.loads((bundle / "verification_status.json").read_text())
    ledger_map = {r["portal_id"]: r for r in ledger}
    result = []
    for partner in partners:
        pid = partner.source_url.rsplit("/", 1)[-1]
        points, urls, update_fields = [], [], {}
        current = {}
        if q := quotas.get(pid):
            note = f"臺大116-1／2027–28已公告{q['quota_display']}。名額為學年單位，一學期計0.5；人次是最多人數，不保證錄取。可交換一學期或一學年，限本校第一學期出國；選填系統開放及其他條件仍須確認。"
            update_fields.update(quota=q["quota_display"], quota_status="published", application_window_status="needs_confirmation", availability_note=note)
            evidence = ExchangeFieldEvidence(source_url=LIST_URL, academic_year="116", application_round="116-1", checked_at=q["checked_at"], status="verified_current", excerpt=q["quota_original"] + "／" + q["maximum_persons_original"], note=note)
            update_fields["field_evidence"] = {**partner.field_evidence, "quota": evidence}
            update_fields["reference_data"] = {**partner.reference_data, "selection_quota_academic_years": str(q["quota_academic_years"]), "selection_maximum_persons": str(q["maximum_persons"]), "selection_source_academic_year": "2027/2028", "exchange_duration_original": q["exchange_duration_original"]}
            points.append(note); urls.extend([LIST_URL, q["detail_url"]]); current["quota"] = q
            field = ledger_map[pid]["fields"].setdefault("quota", {"label": "臺大本期甄選名額", "source_urls": [LIST_URL]})
            field.update(remaining_questions=["選填系統實際開放及其他申請條件須另確認；名額公告不代表錄取。"])
            field.pop("status", None)
            field["status"] = "verified_current_home_selection_quota"
            field.pop("current_official_update", None); field["current_official_update"] = copy.deepcopy(q)
            ledger_map[pid].update(selection_quota=q["quota_display"], selection_status="quota_published_application_state_unconfirmed")
        elif zq := zero_quotas.get(pid):
            note = zq["exchange_duration_original"]
            update_fields.update(quota="0 名", availability_note=note)
            evidence = ExchangeFieldEvidence(source_url=LIST_URL, academic_year="116", application_round="116-1", checked_at=zq["checked_at"], status="verified_current", excerpt="0 名／0 名", note=note)
            update_fields["field_evidence"] = {**partner.field_evidence, "quota": evidence}
            points.append(note); urls.extend([LIST_URL, zq["detail_url"]]); current["zero_quota"] = zq
            field = ledger_map[pid]["fields"].setdefault("quota", {"label": "臺大本期甄選名額", "source_urls": [LIST_URL]})
            field.pop("status", None)
            field["status"] = "confirmed_zero_not_open"
            field.pop("current_official_update", None); field["current_official_update"] = copy.deepcopy(zq)
            ledger_map[pid].update(selection_quota="0 名", selection_status="confirmed_zero_not_open")
        if reminder := visas.get(pid):
            points.append(reminder["text_zh"]); urls.extend([reminder["source_url"], reminder["official_external_url"]]); current["visa_reminder"] = reminder
            field = ledger_map[pid]["fields"].setdefault("insurance_visa", {})
            field.pop("current_official_update", None); field["current_official_update"] = copy.deepcopy(reminder)
        application = partner.application_info or ""
        if reference := references.get(pid):
            from .ntu_official_changes import replace_section
            for section in reference["sections"]:
                text = section["text"] + "\n官方連結：" + "；".join(link["url"] for link in section["links"])
                application = replace_section(application, section["heading"], text)
            points.append(reference["note_zh"])
            ref_urls = [
                *(link["url"] for s in reference["sections"] for link in s["links"] if link["url"].startswith("https://")),
                *(link["url"] for link in reference.get("links", []) if link["url"].startswith("https://")),
            ]
            urls.extend([reference["source_url"], *ref_urls])
            current["reference_links"] = reference
        profile = profile_map[partner.school_name]
        if pid == "1":
            current["UBC_annual_reference"] = ubc
            points.extend(f"PDF第{fact['pdf_page']}頁：{fact['text_zh']}" for fact in ubc["facts"])
            urls.extend([partner.source_url, ubc["source_url"]])
            fact_fields = sorted({f["field"] for f in ubc["facts"]})
            details = {key: value for key, value in partner.partner_exchange_details.items() if key not in fact_fields}
            for name in fact_fields:
                facts = [f for f in ubc["facts"] if f["field"] == name]
                evidence = ExchangeFieldEvidence(source_url=ubc["source_url"], source_pages=sorted({f["pdf_page"] for f in facts}), academic_year="2027/2028", checked_at=ubc["checked_at"], status="reference_only", note=ubc["scope"])
                details[name] = PartnerExchangeDetailField(value="\n".join(f["text_zh"] for f in facts), status="reference_only", reason=ubc["scope"], evidence=[evidence], research_category="verified_supported", research_note="年度已核實的海外接收參考，不啟用臺大甄選期限或配額。")
                field = ledger_map[pid]["fields"].setdefault(name, {})
                field.pop("current_official_update", None)
                field["current_official_update"] = {"source_url": ubc["source_url"], "source_sha256": ubc["source_sha256"], "checked_at": ubc["checked_at"], "source_academic_year": "2027/2028", "facts": facts, "selection_rule_confirmed": False}
            update_fields["partner_exchange_details"] = details
            points.append("新要項文件更新日2026-09-10；舊要項、既有費率觀察及衝突判讀保留為歷史，不重複計為首次發現費用。")
            points.append("臺大內頁仍有未標年度的舊費率及2024/25住房連結；先前平台原文保留追溯，2027/28參考請優先核對新要項，不混用不同期間價格。")
            profile_updates = {}
            for summary_field, fact_field in [("cost_summary", "cost"), ("housing_summary", "housing")]:
                prior = getattr(profile, summary_field) or ""
                historical_marker = "\n\n【先前已保存參考；非新年度核定值】\n"
                if historical_marker in prior:
                    prior = prior.split(historical_marker, 1)[1]
                current_text = "UBC2027/28年度接收參考（文件更新2026-09-10）\n" + "\n".join(f"PDF第{f['pdf_page']}頁：{f['text_zh']}" for f in ubc["facts"] if f["field"] == fact_field)
                profile_updates[summary_field] = current_text + "\n來源：" + ubc["source_url"] + historical_marker + prior
            profile = profile.model_copy(update=profile_updates)
        if current:
            application = re.sub(re.escape(SECTION) + r"\n.*?(?=\n\n【|\Z)", "", application, flags=re.S).strip()
            latest = SECTION + "\n" + "\n".join(points) + "\n來源：" + "；".join(dict.fromkeys(urls))
            if "\n\n" + LEGACY_SECTION in application:
                before, old = application.split("\n\n" + LEGACY_SECTION, 1)
                application = before.rstrip() + "\n\n" + latest + "\n\n" + LEGACY_SECTION + old
            else:
                application = application + "\n\n" + latest
            update_fields["application_info"] = application
            sections = [s for s in profile.student_guide_sections if s.key != GUIDE_KEY]
            if pid == "1":
                marker = "2026-10-14已有2027/28新要項；以下保留歷史判讀，當期接收參考優先看最新來源更新。"
                sections = [s.model_copy(update={"summary": s.summary + " " + marker}) if s.key in {"ntu-host-references-20261011", "ntu-field-conclusions-20261011"} and marker not in s.summary else s for s in sections]
            sections.append(StudentGuideSection(key=GUIDE_KEY, title="臺大最新來源更新（2026-10-14）", summary="已核對原件、年度與來源角色；名額公告、接待校參考及臺大簽證提醒分別呈現。", points=points, source_urls=list(dict.fromkeys(urls)), caution="名額不保證錄取或選填系統已開放；接待校參考與簽證提醒不替代臺大甄選規定或個人適用判定。"))
            sources = [s for s in profile.sources if s.title != "臺大來源更新（2026-10-14）"]
            sources.append(SourceReference(title="臺大來源更新（2026-10-14）", source_url=partner.source_url, summary="臺大官方來源；個別新年度PDF另列頁碼与範圍。"))
            profile_map[partner.school_name] = profile.model_copy(update={"student_guide_sections": sections, "sources": sources})
            entry = ledger_map[pid]
            entry.pop("current_official_updates", None)
            entry["current_official_updates"] = copy.deepcopy(current)
        result.append(with_ntu_partner_summary(partner.model_copy(update=update_fields)))
    (bundle / "partners.jsonl").write_text("".join(p.model_dump_json() + "\n" for p in result), encoding="utf-8")
    (bundle / "destination_profiles.jsonl").write_text("".join(profile_map[p.school_name].model_dump_json() + "\n" for p in profiles), encoding="utf-8")
    (bundle / "verification_status.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (bundle / "list_verification.json").write_text(json.dumps(data["list_receipt"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for filename in ["catalog-completeness.json", "import_provenance.json"]:
        payload = json.loads((bundle / filename).read_text())
        payload["current_official_update"] = {"source_snapshot": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "checked_at": data["checked_at"], "counts": data["counts"], "application_open_confirmed": False, "all_current_cycle_fields_verified": False}
        if filename == "catalog-completeness.json":
            payload.update(quota_pending_count=261, zero_quota_count=7, published_positive_quota_count=20, selection_academic_year_slots=43, selection_maximum_persons=81, latest_official_list_checked_at=data["list_receipt"]["checked_at"])
        (bundle / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cp_path = bundle / "college_programmes.json"
    if cp_path.exists():
        cp_list = json.loads(cp_path.read_text(encoding="utf-8"))
        for item in cp_list:
            if item.get("college") == "管理學院":
                existing_urls = {s["url"] for s in item.get("sources", [])}
                for extra_url, extra_hash in (
                    ("https://management.ntu.edu.tw/cm/board_file/22/21322/021322_4.pdf", "48528426fdab1ff388182909d5e8cd6ab4147cb9dbbdbf958667505a0b3a0004"),
                    ("https://management.ntu.edu.tw/cm/board_file/22/0/000000_189.pdf", "56241a3210b842b621417df106c13301eb7d25b37c24fb72053fb56821c07d11"),
                ):
                    if extra_url not in existing_urls:
                        item["sources"].append({
                            "url": extra_url,
                            "retrieved_at": data["checked_at"],
                            "content_hash": extra_hash,
                            "original_file": None,
                            "text_file": None,
                            "pdf_pages_cited": [1, 2],
                        })
        cp_path.write_text(json.dumps(cp_list, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data["counts"]
