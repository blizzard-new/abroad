"""Apply dated NTU portal references without approving a selection cycle."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from .models import DestinationProfile, PartnerUniversity, SourceReference
from .ntu_partner_summary import with_ntu_partner_summary

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "sources/ntu/2026-10-10-official-changes.json"
CAUTION = "2026-10-10查核：官方內頁正文已變更；未明列適用年度者為現行參考，116-1最終條件與甄選名額仍待確認。"
SECTION_FIELDS = {
    "申請資格": ("eligibility", "language"), "名額": ("quota",),
    "學校年曆": ("calendar",), "注意事項": ("courses",),
    "特殊學系語檢要求": ("language", "courses"),
    "住宿資訊": ("housing",), "實用資訊": ("cost", "insurance_visa"),
    "生活費與保險資訊": ("cost", "insurance_visa"),
}


def replace_section(value: str | None, heading: str, text: str | None) -> str:
    """Replace only a portal block; preserve independent supplemental evidence."""
    value = value or ""
    pattern = re.compile(r"【" + re.escape(heading) + r"】\n.*?(?=\n\n【|\Z)", re.S)
    replacement = f"【{heading}】\n{text}" if text is not None else ""
    if pattern.search(value):
        return pattern.sub(lambda _: replacement, value, count=1).strip()
    return (value + ("\n\n" + replacement if replacement else "")).strip()


def apply_official_changes(bundle: Path, snapshot_path: Path = SNAPSHOT) -> dict:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot["format_version"] != 1:
        raise ValueError("unsupported official change snapshot")
    changes = {row["portal_id"]: row for row in snapshot["schools"]}
    if len(changes) != 20:
        raise ValueError("the reviewed batch must contain exactly 20 unique schools")
    receipt = snapshot["list_receipt"]
    if (receipt["http_status"] != 200 or len(receipt["rows"]) != 288
            or sum(not row["quota"] for row in receipt["rows"]) != 282
            or sum(row["quota"] == "0 名" for row in receipt["rows"]) != 6):
        raise ValueError("list receipt does not retain the verified inventory")
    partners_path = bundle / "partners.jsonl"
    partners = [PartnerUniversity.model_validate_json(line) for line in partners_path.read_text().splitlines()]
    from .ntu_current_updates import historical_selection_view
    historical = historical_selection_view(partners)
    historical_by_url = {p.source_url: p for p in historical}
    destinations_path = bundle / "destination_profiles.jsonl"
    destinations = [DestinationProfile.model_validate_json(line) for line in destinations_path.read_text().splitlines()]
    ledger_path = bundle / "verification_status.json"
    ledger = json.loads(ledger_path.read_text())
    ledger_map = {row["portal_id"]: row for row in ledger}
    destination_map = {row.school_name: row for row in destinations}
    touched = set()
    result = []
    for partner in partners:
        portal_id = partner.source_url.rsplit("/", 1)[-1]
        update = changes.get(portal_id)
        if update is None:
            result.append(partner)
            continue
        if historical_by_url[partner.source_url].quota is not None or partner.availability_status == "open":
            raise ValueError(f"unexpected selection state for {portal_id}")
        if update["selection_quota"] is not None or update["list_marked_updated"]:
            raise ValueError(f"batch finality boundary changed for {portal_id}")
        if update["official_url"] != partner.source_url or update["school_name"] != partner.school_name:
            raise ValueError(f"school identity mismatch for {portal_id}")
        touched.add(portal_id)
        fields = {}
        reference = update["sections_by_heading"]
        fields["eligibility"] = reference["申請資格"]["text"]
        match = re.search(r"本校([^。]+?)(?:學生|（)", fields["eligibility"].replace("\n", ""))
        if match:
            fields["degree_levels"] = "本校" + match.group(1)
        application = partner.application_info
        destination = destination_map[partner.school_name]
        destination_updates = {}
        for change in update["changed_sections"]:
            heading = change["section"]
            after = reference.get(heading)
            text = after["text"] if after else None
            if text is not None and after.get("links"):
                text += "\n官方連結：" + "；".join(link["url"] for link in after["links"])
            if heading not in {"申請資格", "名額", "註冊繳費"}:
                application = replace_section(application, heading, text)
            if heading in {"實用資訊", "生活費與保險資訊"} and text:
                destination_updates["campus_life_summary"] = replace_section(
                    destination_updates.get("campus_life_summary", destination.campus_life_summary), heading, text)
                destination_updates["cost_summary"] = CAUTION + "\n" + text
            if heading == "住宿資訊" and text:
                destination_updates["housing_summary"] = CAUTION + "\n" + text
        note = CAUTION + "\n當日內頁名額原文（年度待確認，非116-1已確認甄選名額）：" + reference["名額"]["text"]
        if any(change["section"] == "特殊學系語檢要求" and change["after"] is None for change in update["changed_sections"]):
            note += "\n當日內頁已移除特殊學系語檢要求章節；不推論接待校相關要求已取消，仍須確認。"
        # Idempotent when called against an already updated bundle.
        application = re.sub(r"\n\n【官方內頁變更查核，2026-10-10】\n.*\Z", "", application or "", flags=re.S)
        fields["application_info"] = application + "\n\n【官方內頁變更查核，2026-10-10】\n" + note
        result.append(with_ntu_partner_summary(partner.model_copy(update=fields)))
        if destination_updates:
            sources = [source for source in destination.sources if source.title != "臺大官方內頁變更查核（2026-10-10）"]
            destination_updates["sources"] = [*sources, SourceReference(title="臺大官方內頁變更查核（2026-10-10）",
                source_url=partner.source_url, summary=CAUTION)]
            destination_map[partner.school_name] = DestinationProfile.model_validate(
                destination.model_copy(update=destination_updates).model_dump())
        entry = ledger_map[portal_id]
        entry["official_portal_change"] = {key: copy.deepcopy(update[key]) for key in (
            "checked_at", "official_url", "source_sha256", "list_marked_updated", "selection_quota",
            "source_academic_year", "changed_sections", "language_score_alternatives")}
        entry["official_portal_change"]["current_cycle_finality"] = "not_confirmed"
        for change in update["changed_sections"]:
            for key in SECTION_FIELDS.get(change["section"], ()):
                existing = entry["fields"].setdefault(key, {"label": key, "source_urls": [], "remaining_questions": []})
                prior_status = existing.pop("prior_status", None)
                observations = existing.pop("official_portal_observations", [])
                if existing.get("status") in {"not_confirmed_no_text_evidence", "missing"} and key != "quota":
                    prior_status = prior_status or existing["status"]
                    existing["status"] = "partial_official_reference_cycle_unconfirmed"
                if prior_status is not None:
                    existing["prior_status"] = prior_status
                existing["official_portal_observations"] = observations
                observations[:] = [item for item in observations if item.get("section") != change["section"]]
                scoped_year = "2027-2028" if portal_id == "1200" and change["section"] == "學校年曆" else None
                observations.append({"section": change["section"], "source_url": partner.source_url,
                    "checked_at": update["checked_at"], "evidence_academic_year": scoped_year,
                    "status": "section_removed_requires_confirmation" if change["after"] is None else (
                        "reviewed_explicit_year_calendar" if scoped_year else "official_reference_cycle_unconfirmed"),
                    "value": change["after"], "selection_rule_confirmed": False})
    if touched != set(changes):
        raise ValueError("not all reviewed school IDs were found in the bundle")
    historical_result = historical_selection_view(result)
    if sum(p.quota is None for p in historical_result) != 282 or sum(p.quota == "0 名" for p in historical_result) != 6:
        raise ValueError("selection quota guard failed")
    partners_path.write_text("".join(p.model_dump_json() + "\n" for p in result), encoding="utf-8")
    destinations_path.write_text("".join(destination_map[p.school_name].model_dump_json() + "\n" for p in destinations), encoding="utf-8")
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    provenance_path = bundle / "import_provenance.json"
    provenance = json.loads(provenance_path.read_text())
    provenance["official_portal_changes"] = {"source_snapshot": snapshot_path.name,
        "sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(), "school_count": len(changes),
        "checked_at": snapshot["checked_at"], "current_cycle_finality": "not_confirmed"}
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (bundle / "list_verification.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    completeness_path = bundle / "catalog-completeness.json"
    completeness = json.loads(completeness_path.read_text())
    completeness["official_portal_checked_at"] = snapshot["checked_at"]
    completeness["official_portal_changed_school_count"] = 20
    completeness_path.write_text(json.dumps(completeness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"updated_reference_schools": len(touched), "pending_quota_count": 282, "zero_quota_count": 6}
