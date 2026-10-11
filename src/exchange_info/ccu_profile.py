"""CCU-only reviewed geography, academic scopes and separate life evidence."""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from .ccu_sources import BUNDLE, require_usable_source
from .source_integrity import file_sha256
from .models import (
    ExchangeFieldEvidence,
    PartnerProgramOption,
    PartnerUniversity,
    StudentGuideSection,
)
from .university_locations import UniversityLocation

LABELS = {
    "city": "城市與校區",
    "location": "官方校址／聯絡地址",
    "website": "官方網站",
    "degree_levels": "接收學制",
    "colleges": "接收學院範圍",
    "transport": "交通與通勤",
    "campus_life": "校園生活與支援",
}


@lru_cache(maxsize=1)
def reviewed_profiles() -> dict[int, dict]:
    rows = json.loads((BUNDLE / "profile-reviewed-fields.json").read_text())
    if len(rows) != 55 or len({r["ccu_page"] for r in rows}) != 55:
        raise ValueError("CCU profiles must cover 55 distinct receiving identities")
    for row in rows:
        if set(row["fields"]) != set(LABELS):
            raise ValueError("Incomplete CCU profile field matrix")
        for field in [*row["fields"].values(), *row.get("supplementary_life_guidance", [])]:
            if (field["value"] is None) != (field["status"] == "missing"):
                raise ValueError("CCU missing profile facts must remain null")
            if field["value"] and not field["evidence"]:
                raise ValueError("CCU profile fact requires source evidence")
            if field["status"] == "verified_current" and not any(
                ev["status"] == "verified_current" for ev in field["evidence"]
            ):
                raise ValueError("Current CCU profile requires current evidence")
            for ev in field["evidence"]:
                source = json.loads(
                    (
                        BUNDLE / "overseas_sources" / (ev["source_id"] + ".json")
                    ).read_text()
                )
                require_usable_source(source)
                text_hash = hashlib.sha256(
                    json.dumps(
                        source.get("text_pages", []), ensure_ascii=False
                    ).encode()
                ).hexdigest()
                if (
                    source.get("sha256") != ev["content_hash"]
                    or text_hash != ev["text_sha256"]
                ):
                    raise ValueError("Changed CCU profile evidence; rereview source")
                if (
                    source.get("bundled_file")
                    and file_sha256(BUNDLE / source["bundled_file"])
                    != source["sha256"]
                ):
                    raise ValueError("Changed CCU profile source attachment")
                if source.get("access_result") in {
                    "challenge_page",
                    "captcha_required",
                    "empty_response",
                    "unrelated_content_anomaly", "password_protected",
                }:
                    raise ValueError(
                        "Unread or anomalous page cannot support CCU profile facts"
                    )
                pages = ev["source_pages"] or range(1, len(source["text_pages"]) + 1)
                text = " ".join(
                    re.sub(r"\s+", " ", source["text_pages"][p - 1]).strip()
                    for p in pages
                )
                if (
                    not ev["excerpt"]
                    or re.sub(r"\s+", " ", ev["excerpt"]).strip() not in text
                ):
                    raise ValueError(f"CCU profile excerpt absent: {ev['source_id']}")
                if not all(
                    ev.get(k) for k in ["academic_year", "checked_at", "source_url"]
                ):
                    raise ValueError("Incomplete CCU profile provenance")
                if ev["status"] not in {
                    "verified_current", "needs_confirmation", "reference_only",
                    "conflict", "explicit_not_announced",
                }:
                    raise ValueError("Invalid CCU profile evidence status")
    return {row["ccu_page"]: row for row in rows}


def apply_profile(partner: PartnerUniversity) -> PartnerUniversity:
    row = reviewed_profiles().get(partner.source_pages[0])
    if row is None:
        return partner
    if row["school_name"] != partner.school_name:
        raise ValueError("CCU profile school identity disagreement")
    fields = row["fields"]
    if row.get("academic_scope_options"):
        partner.program_options = [
            PartnerProgramOption.model_validate(option)
            for option in row["academic_scope_options"]
        ]
    for key in ["website", "colleges", "degree_levels"]:
        field = fields[key]
        if field["value"]:
            setattr(partner, key, field["value"])
            partner.field_evidence[key] = ExchangeFieldEvidence.model_validate(
                field["evidence"][0]
            )
    city, location = fields["city"], fields["location"]
    if city["value"]:
        ev = location["evidence"][0]
        partner.location = UniversityLocation(
            school_name=partner.school_name,
            country=partner.country,
            city=city["value"],
            geocode_status="pending",
            source_url=ev["source_url"],
            identity_source_url=partner.source_url,
            note=f"查核{ev['checked_at'].split('T')[0]}；{ev['academic_year']}；{location['reason']} 原文：{location['value']}",
        )
        partner.field_evidence["city"] = ExchangeFieldEvidence.model_validate(
            city["evidence"][0]
        )
        partner.field_evidence["location"] = ExchangeFieldEvidence.model_validate(ev)
    return partner


def school_location(
    partner: PartnerUniversity, location: UniversityLocation, data_dir: Path | None = None
) -> UniversityLocation:
    """Use CCU campus reviews before shared aliases; retain local operator reviews."""
    if data_dir is not None and partner.location and partner.location.geocode_status == "verified":
        from .school_identity import school_identity_key
        path = Path(data_dir) / "processed/university_locations.jsonl"
        operator_records = _operator_locations(path, path.stat().st_mtime_ns, path.stat().st_size) if path.exists() else {}
        names = {school_identity_key(partner.school_name)}
        target = _completion_target_names().get(partner.source_pages[0]) if partner.source_pages else None
        if target:
            names.add(school_identity_key(target))
        country = _operator_country(partner.country)
        for name in sorted(names):
            if (name, country) in operator_records:
                operator = operator_records[(name, country)]
                return operator.model_copy(update={"school_name": partner.school_name, "country": partner.country})
        return partner.location
    if (
        partner.location
        and partner.location.city
        and location.geocode_status == "pending"
        and not location.city
        and not location.source_url
        and not location.identity_source_url
    ):
        return partner.location
    return location


def _operator_country(country):
    if not isinstance(country, str):
        return None
    return {"南韓": "韓國", "中國": "中國大陸", "大陸地區": "中國大陸", "台灣": "臺灣"}.get(country, country)


@lru_cache(maxsize=8)
def _operator_locations(path, mtime_ns, size):
    from .school_identity import school_identity_key
    records = {}
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and isinstance(row.get("school_name"), str):
            try:
                record = UniversityLocation.model_validate(row)
            except ValueError:
                record = UniversityLocation(school_name=row["school_name"], country=row.get("country") if isinstance(row.get("country"), str) else None, geocode_status="needs_review")
            if record.geocode_status != "verified":
                record = record.model_copy(update={"latitude": None, "longitude": None})
            records[(school_identity_key(row["school_name"]), _operator_country(row.get("country")))] = record
    return records


@lru_cache(maxsize=1)
def _completion_target_names():
    path = BUNDLE / "completion-targets.json"
    return {row["ccu_page"]: row["canonical_name"] for row in json.loads(path.read_text())} if path.exists() else {}


def profile_life(
    partner: PartnerUniversity,
) -> tuple[dict[str, str | None], list[StudentGuideSection], list[dict]]:
    from .ccu_overseas import STATUS_LABELS

    row = reviewed_profiles().get(partner.source_pages[0])
    if not row:
        return {}, [], []
    fields = row["fields"]
    summaries, sections, evidence = {}, [], []
    for key in ["transport", "campus_life"]:
        field = fields[key]
        summaries[key] = None
        if not field["value"]:
            continue
        ev = field["evidence"][0]
        pages = (
            "；PDF第" + "、".join(map(str, ev["source_pages"])) + "頁"
            if ev["source_pages"]
            else ""
        )
        text = f"{field['value']}（{STATUS_LABELS[field['status']]}；{ev['academic_year']}{pages}；查核{ev['checked_at'].split('T')[0]}）"
        summaries[key] = text
        sections.append(
            StudentGuideSection(
                key=key,
                title=LABELS[key],
                summary=field["value"],
                points=[text],
                source_urls=list(
                    dict.fromkeys(e["source_url"] for e in field["evidence"])
                ),
                evidence_type="official",
                caution=field["reason"],
            )
        )
        evidence.extend(field["evidence"])
    for field in row.get("supplementary_life_guidance", []):
        ev = field["evidence"][0]
        text = (f"{field['value']}（{STATUS_LABELS[field['status']]}；{ev['academic_year']}；"
                f"查核{ev['checked_at'].split('T')[0]}）")
        sections.append(StudentGuideSection(
            key=field["key"], title=field["title"], summary=field["value"],
            points=[text], source_urls=list(dict.fromkeys(e["source_url"] for e in field["evidence"])),
            evidence_type="official", caution=STATUS_LABELS[field["status"]] + "；" + field["reason"],
        ))
        evidence.extend(field["evidence"])
    return summaries, sections, evidence


def align_completeness(result, partner: PartnerUniversity):
    """Keep the public completeness panel consistent with reviewed field statuses."""
    row = reviewed_profiles().get(partner.source_pages[0])
    if not row:
        return result
    statuses = {
        "verified_current": "available",
        "missing": "missing",
        "reference_only": "needs_confirmation",
        "needs_confirmation": "needs_confirmation",
        "conflict": "needs_confirmation",
        "explicit_not_announced": "needs_confirmation",
    }
    items = []
    for item in result.items:
        if item.key in {"city", "transport", "campus_life"}:
            field = row["fields"][item.key]
            item = item.model_copy(
                update={
                    "status": statuses[field["status"]],
                    "note": field["reason"],
                    "source_urls": list(
                        dict.fromkeys(ev["source_url"] for ev in field["evidence"])
                    ),
                }
            )
        elif item.key in {"housing", "cost"}:
            key = "housing" if item.key == "housing" else "costs"
            field = partner.partner_exchange_details[key]
            if field.status != "verified_current":
                item = item.model_copy(
                    update={
                        "status": statuses[field.status],
                        "note": field.reason,
                        "source_urls": list(
                            dict.fromkeys(e.source_url for e in field.evidence)
                        ),
                    }
                )
        elif item.key == "documents":
            item = item.model_copy(
                update={
                    "status": "partial",
                    "note": "母校文件與已核實合作校要求分期整理；個人表、條件文件及院系追加項仍不完整，已取得的公開模板另列。",
                }
            )
        items.append(item)
    weights = {
        "available": 1.0,
        "partial": 0.5,
        "needs_confirmation": 0.25,
        "missing": 0.0,
    }
    return result.model_copy(
        update={
            "items": items,
            "available_count": sum(item.status == "available" for item in items),
            "score": round(sum(weights[item.status] for item in items) / len(items), 3),
            "priority_gaps": [
                item.label
                for item in items
                if item.key
                in {"eligibility", "deadline", "workflow", "documents", "cost"}
                and item.status != "available"
            ],
        }
    )


def align_life_context(context, partner, profile, location):
    """Use each CCU life field's actual sources and preserve local research rows."""
    from .ccu_overseas import STATUS_LABELS, describe_field, reviewed_row
    from .life_context import LifeEvidence, LifeSource

    row = reviewed_profiles().get(partner.source_pages[0])
    host = reviewed_row(partner.source_pages[0])
    if not row or not host:
        return context
    fields = {
        "housing": host["fields"]["housing"],
        "cost": host["fields"]["costs"],
        "transport": row["fields"]["transport"],
        "social": row["fields"]["campus_life"],
    }
    generic_texts = {
        value
        for value in (
            profile.housing_summary,
            profile.cost_summary,
            profile.transport_summary,
            profile.campus_life_summary,
        )
        if value
    }
    categories = []
    for category in context.categories:
        if category.theme not in fields:
            categories.append(category)
            continue
        field = fields[category.theme]
        retained = [
            e
            for e in category.evidence
            if (e.original_text or e.text) not in generic_texts
        ]
        if field["value"] and field["evidence"]:
            ev = field["evidence"][0]
            if category.theme in {"housing", "cost"}:
                key = "housing" if category.theme == "housing" else "costs"
                text = describe_field(key, partner.partner_exchange_details[key])
            else:
                text = f"{field['value']}（{STATUS_LABELS[field['status']]}；{ev['academic_year']}；查核{ev['checked_at'].split('T')[0]}）"
            retained.append(
                LifeEvidence(
                    theme=category.theme,
                    kind="official",
                    text=text,
                    sources=[
                        LifeSource(
                            title="中正逐欄查核來源",
                            url=(
                                e["source_url"].split("#")[0]
                                + f"#page={e['source_pages'][0]}"
                            )
                            if e["source_pages"]
                            else e["source_url"],
                        )
                        for e in field["evidence"]
                    ],
                    checked_at=ev["checked_at"],
                    scope=f"{STATUS_LABELS[field['status']]}；{ev['academic_year']}；{field['reason']}",
                )
            )
        categories.append(
            category.model_copy(update={"evidence": retained, "inference": None})
        )
    note = context.location_note
    if (
        location.geocode_status == "pending"
        and location.city
        and partner.location
        and location.city == partner.location.city
    ):
        field = row["fields"]["city"]
        note = f"官方城市／聯絡地址參考：{location.city}（{field['status']}）。{note} 接收校區按所選計畫另核。"
    return context.model_copy(
        update={
            "categories": categories,
            "location_note": note,
            "source_count": len(
                {s.url for c in categories for e in c.evidence for s in e.sources}
            ),
        }
    )
