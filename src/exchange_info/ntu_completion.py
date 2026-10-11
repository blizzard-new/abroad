"""Replay scoped, reviewed NTU additions while keeping selection guards intact."""
from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from .life_context import LifeResearchSnapshot
from .models import DestinationProfile, PartnerUniversity, SourceReference, StudentGuideSection
from .ntu_partner_summary import with_ntu_partner_summary
from .school_identity import school_identity_key
from .university_locations import UniversityLocation, location_key

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "sources/ntu/completion-2026-10-11.json"
PACKAGE = ROOT / "src/exchange_info"
ALLOWED_FIELDS = {"eligibility", "language", "documents", "deadlines", "calendar", "courses", "housing", "cost", "insurance_visa"}
PERIODS = {"target_year_explicit", "undated_public_reference", "older_year_reference",
           "version_conflict", "explicitly_pending_announcement"}
FIELD_LABELS = {"eligibility": "接待校資格參考", "language": "接待校語言參考", "documents": "接待校文件參考",
    "deadlines": "接待校期限參考", "calendar": "行事曆參考", "courses": "課程參考", "housing": "住宿參考",
    "cost": "費用參考", "insurance_visa": "保險與簽證參考"}
SECTION = "【接待校公開來源補查，2026-10-11】"


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def validate(snapshot: dict, partners: list[PartnerUniversity], *, package: Path = PACKAGE) -> None:
    if snapshot.get("format_version") != 1 or snapshot.get("all_current_cycle_fields_verified") is not False:
        raise ValueError("Unsupported completion snapshot or invalid finality claim")
    expected = {p.source_url.rsplit("/", 1)[-1]: p for p in partners}
    entries = snapshot["schools"]
    if len(expected) != 288 or len(entries) != 288 or len({r["portal_id"] for r in entries}) != 288:
        raise ValueError("All 288 distinct NTU school identities are required")
    if set(expected) != {r["portal_id"] for r in entries}:
        raise ValueError("Completion inventory does not match the partner catalog")
    if sum(p.quota is None for p in partners) != 282 or sum(p.quota == "0 名" for p in partners) != 6:
        raise ValueError("Selection baseline changed; source scope must be reviewed")
    receipt = snapshot["list_receipt"]
    inventory = {r["portal_id"]: r for r in receipt["rows"]}
    if (receipt["http_status"] != 200 or len(inventory) != 288 or set(inventory) != set(expected)
            or not re.fullmatch(r"[a-f0-9]{64}", receipt["sha256"])):
        raise ValueError("A fresh all-school official list receipt is required")
    for sn, partner in expected.items():
        if (inventory[sn]["name"] != partner.school_name
                or (inventory[sn]["quota"] or None) != partner.quota):
            raise ValueError("Official list identity or selection quota changed")
    reviews = snapshot["public_source_reviews"]
    for sid, source in reviews.items():
        if source["source_id"] != sid or not source.get("original_quote") or not source.get("checked_at"):
            raise ValueError("A source review needs its original quote and retrieval date")
        if len(source["original_quote"].split()) > 25:
            raise ValueError("Source quote is too long")
        if not source.get("sha256") and source.get("retrieval_method") != "primary_web_tool_cached_read":
            raise ValueError("Source bodies need hashes; web-cache readings must say so")
    for entry in entries:
        partner = expected[entry["portal_id"]]
        if (entry["school_name"], entry["country"]) != (partner.school_name, partner.country):
            raise ValueError("School, country or campus identity mismatch")
        for observation in entry.get("observations", []):
            if observation["field"] not in ALLOWED_FIELDS or observation.get("selection_rule_confirmed") is not False:
                raise ValueError("A reference observation cannot approve a selection rule")
            if not observation.get("text_zh") or not observation.get("checked_at") or not observation.get("scope"):
                raise ValueError("A reviewed observation needs text, scope and retrieval date")
            if urlsplit(observation["source_url"]).scheme != "https":
                raise ValueError("Reviewed references must retain HTTPS sources")
            if observation.get("review_status") != "reviewed_public_reference":
                raise ValueError("Discovery-only paragraphs cannot be imported")
            if observation.get("applicability_status") not in PERIODS:
                raise ValueError("A reference needs its original period classification")
            source = reviews.get(observation.get("quote_source_id"))
            if not source or observation["source_url"] not in {source["url"], source.get("final_url")}:
                raise ValueError("An observation must join its reviewed source and quote")
            datetime.fromisoformat(observation["checked_at"])
            if source.get("document_type") == "pdf" and not (1 <= observation.get("pdf_page", 0) <= source["pdf_page_count"]):
                raise ValueError("A PDF observation needs a valid page locator")
        if photo := entry.get("photo"):
            if (photo.get("school_name"), photo.get("country")) != (partner.school_name, partner.country):
                raise ValueError("Photograph identity belongs to another school or country")
            if photo.get("status") != "verified" or not re.fullmatch(r"CC BY(?:-SA)? [\d.]+|CC0|Public domain", photo.get("license_name", "")):
                raise ValueError("A campus photograph needs an accepted reuse license")
            if not photo.get("official_page_url") or not entry.get("photo_review", {}).get("campus_name"):
                raise ValueError("A campus photograph needs a page and reviewed campus identity")
            if photo["license_name"].startswith("CC BY") and (not photo.get("license_url") or not photo.get("artist")):
                raise ValueError("Attribution and license URL are required")
            relative = photo["local_path"].split("?", 1)[0].removeprefix("/static/")
            asset = (package / "static" / relative).resolve()
            if not asset.is_relative_to((package / "static/assets/schools").resolve()):
                raise ValueError("Photograph path must remain inside the campus asset directory")
            if hashlib.sha256(asset.read_bytes()).hexdigest() != photo["content_hash"]:
                raise ValueError("Reviewed photograph bytes changed")
        if entry.get("location"):
            location = UniversityLocation.model_validate(entry["location"])
            if (location.school_name, location.country) != (partner.school_name, partner.country):
                raise ValueError("Coordinates belong to another school or country")
            if not entry.get("location_review", {}).get("official_campus_source_url"):
                raise ValueError("New coordinates require official campus corroboration")
            if entry["location_review"].get("assigned_exchange_campus_confirmed") is not False:
                raise ValueError("A representative location must not assert exchange assignment")
        if entry.get("life_evidence"):
            from .life_context import LifeEvidence, THEMES
            for raw in entry["life_evidence"]:
                evidence = LifeEvidence.model_validate(raw)
                if evidence.theme not in THEMES or not evidence.sources or not evidence.checked_at or evidence.kind != "official":
                    raise ValueError("Life additions need an official source, date and supported theme")


def apply_completion(bundle: Path, snapshot_path: Path = SOURCE, *, apply_assets: bool = False,
                     package: Path = PACKAGE) -> dict:
    snapshot = json.loads(snapshot_path.read_text())
    partners = [PartnerUniversity.model_validate(r) for r in read_rows(bundle / "partners.jsonl")]
    validate(snapshot, partners, package=package)  # Check the entire batch before writing.
    entries = {r["portal_id"]: r for r in snapshot["schools"]}
    ledger = json.loads((bundle / "verification_status.json").read_text())
    ledger_map = {r["portal_id"]: r for r in ledger}
    profiles = [DestinationProfile.model_validate(r) for r in read_rows(bundle / "destination_profiles.jsonl")]
    profile_map = {r.school_name: r for r in profiles}
    life = [LifeResearchSnapshot.model_validate(r) for r in read_rows(bundle / "student_life.jsonl")]
    life_map = {(r.school_name, r.country): r for r in life}
    updated = []
    observation_count = 0
    for partner in partners:
        entry = entries[partner.source_url.rsplit("/", 1)[-1]]
        observations = entry.get("observations", [])
        if observations:
            lines = ["2026-10-11接待校公開來源補查；以下各項按各自文件期間及校區作參考，不能視為116-1最終甄選資格或截止提醒。"]
            for observation in observations:
                page = f"，PDF第{observation['pdf_page']}頁" if observation.get("pdf_page") else ""
                lines.append(f"{FIELD_LABELS[observation['field']]}：{observation['text_zh']}\n適用範圍：{observation['scope']}{page}；查閱：{observation['checked_at']}\n來源：{observation['source_url']}")
                field = ledger_map[entry["portal_id"]]["fields"].setdefault(observation["field"], {})
                refs = field.pop("completion_observations", [])
                refs[:] = [r for r in refs if r.get("observation_id") != observation["observation_id"]]
                refs.append(copy.deepcopy(observation))
                if field.get("status") in {"missing", "not_confirmed_no_text_evidence"}:
                    field.setdefault("prior_status", field["status"])
                    field["status"] = "reviewed_public_host_reference_cycle_unconfirmed"
                urls = field.setdefault("source_urls", [])
                if observation["source_url"] not in urls:
                    urls.append(observation["source_url"])
                # Historical replay moves its own keys; keep this overlay last.
                field["completion_observations"] = refs
            original = (partner.application_info or "").split("\n\n" + SECTION, 1)[0]
            partner = with_ntu_partner_summary(partner.model_copy(update={"application_info": original + "\n\n" + SECTION + "\n" + "\n\n".join(lines)}))
            profile = profile_map[partner.school_name]
            sections = [r for r in profile.student_guide_sections if r.key != "ntu-host-references-20261011"]
            sections.append(StudentGuideSection(key="ntu-host-references-20261011", title="接待校公開資訊補查",
                summary="依個別官方來源及原文件期間作參考；年度未明列者不認定為116-1最終規定。",
                points=[f"{FIELD_LABELS[r['field']]}：{r['text_zh']}（{r['scope']}）" for r in observations],
                source_urls=list(dict.fromkeys(r["source_url"] for r in observations)),
                caution="校區、交換身分及期限依原來源；待確認內容不啟用截止提醒。"))
            sources = [r for r in profile.sources if not r.title.startswith("接待校公開補查：")]
            sources.extend(SourceReference(title="接待校公開補查：" + label, source_url=url)
                for url, label in {r["source_url"]: r["source_title"] for r in observations}.items())
            profile_map[partner.school_name] = profile.model_copy(update={"student_guide_sections": sections, "sources": sources})
            observation_count += len(observations)
        if entry.get("life_evidence"):
            from .life_context import LifeEvidence
            record = life_map[(partner.school_name, partner.country)]
            additions = [LifeEvidence.model_validate(r) for r in entry["life_evidence"]]
            existing = {(r.theme, r.text, tuple(s.url for s in r.sources)): r for r in record.evidence}
            for addition in additions:
                existing[(addition.theme, addition.text, tuple(s.url for s in addition.sources))] = addition
            life_map[(partner.school_name, partner.country)] = record.model_copy(update={
                "evidence": list(existing.values()), "status": "partial",
                "checked_at": datetime.fromisoformat(snapshot["reviewed_at"])})
        updated.append(partner)
    outputs = {
        "partners.jsonl": "".join(r.model_dump_json() + "\n" for r in updated),
        "destination_profiles.jsonl": "".join(profile_map[r.school_name].model_dump_json() + "\n" for r in profiles),
        "student_life.jsonl": "".join(life_map[(r.school_name, r.country)].model_dump_json() + "\n" for r in life),
        "verification_status.json": json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
        "list_verification.json": json.dumps(snapshot["list_receipt"], ensure_ascii=False, indent=2) + "\n",
    }
    provenance = json.loads((bundle / "import_provenance.json").read_text())
    provenance["completion_review"] = {"source_snapshot": snapshot_path.name,
        "sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(), "checked_at": snapshot["reviewed_at"],
        "inventory_schools": 288, "reviewed_reference_schools": sum(bool(r.get("observations")) for r in entries.values()),
        "observations": observation_count, "current_cycle_finality": "not_confirmed"}
    outputs["import_provenance.json"] = json.dumps(provenance, ensure_ascii=False, indent=2) + "\n"
    completeness = json.loads((bundle / "catalog-completeness.json").read_text())
    completeness["completion_review"] = provenance["completion_review"]
    completeness["latest_official_list_checked_at"] = snapshot["list_receipt"]["checked_at"]
    outputs["catalog-completeness.json"] = json.dumps(completeness, ensure_ascii=False, indent=2) + "\n"
    home = json.loads((bundle / "home_rules.json").read_text())
    home["latest_source_checks"] = snapshot["home_source_checks"]
    outputs["home_rules.json"] = json.dumps(home, ensure_ascii=False, indent=2) + "\n"
    if apply_assets:
        manifest_path = package / "static/assets/school-images.json"
        manifest = json.loads(manifest_path.read_text())
        images = {(school_identity_key(r["school_name"]), r.get("country") or ""): r for r in manifest["schools"]}
        locations_path = package / "official_data/university_locations.jsonl"
        locations = {location_key(r["school_name"], r.get("country")): r for r in read_rows(locations_path)}
        for entry in entries.values():
            if photo := entry.get("photo"):
                images[(school_identity_key(entry["school_name"]), entry["country"])] = photo
            if location := entry.get("location"):
                locations[location_key(entry["school_name"], entry["country"])] = location
        manifest.update(schools=list(images.values()), updated_at=snapshot["reviewed_at"])
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        locations_path.write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for _, r in sorted(locations.items())))
    for name, text in outputs.items():
        (bundle / name).write_text(text)
    return {"schools": len(partners), "reviewed_observations": observation_count,
        "photo_additions": sum(bool(r.get("photo")) for r in entries.values()),
        "location_additions": sum(bool(r.get("location")) for r in entries.values()),
        "fully_verified_current_cycle_schools": 0}
