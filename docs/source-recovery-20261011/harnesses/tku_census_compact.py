"""Offline TKU agreement/reference adapter; never turns a directory into a round."""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from functools import lru_cache

from .models import (ExchangeFieldEvidence, PartnerExchangeDetailField, PartnerProgramOption,
                     PartnerStudentSummary, PartnerUniversity, SchoolCompletenessItem, SchoolDataCompleteness)
from .tku_data import BUNDLE


class _SchoolAuditIndex(Mapping):
    """Expand one complete audit row per reader; aliases share immutable bytes."""
    def __init__(self, aliases, rows):
        self.aliases = aliases
        self.rows = rows

    def __getitem__(self, name):
        return json.loads(self.rows[self.aliases[name]])

    def __iter__(self):
        return iter(self.aliases)

    def __len__(self):
        return len(self.aliases)


@lru_cache(maxsize=1)
def _snapshot_at(path, mtime_ns, size):
    with Path(path).open(encoding="utf-8") as handle:
        original = json.load(handle)
    rows = {}
    aliases = {}
    for row in original["schools"]:
        identifier = row["id"]
        if identifier in rows:
            raise ValueError("Duplicate TKU census institution ID")
        rows[identifier] = json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode()
        names = {row["school_name"], census_school_name(row)}
        names.update(programme_map()[pid]["fields"]["school_name"]["value"]
                     for pid in row.get("programme_ids", []))
        # Preserve the existing ordered alias overwrite semantics exactly.
        aliases.update({name: identifier for name in names})
    summary = json.dumps({k:v for k,v in original.items() if k != "schools"},
                         ensure_ascii=False, separators=(",", ":")).encode()
    return summary, rows, _SchoolAuditIndex(aliases, rows)


def _snapshot():
    path = BUNDLE / "full_census_audit.json"
    stat = path.stat()
    return _snapshot_at(str(path), stat.st_mtime_ns, stat.st_size)


def census_summary():
    return json.loads(_snapshot()[0])


def census_rows():
    for payload in _snapshot()[1].values():
        yield json.loads(payload)


def census_audit():
    """Retain the full export interface without caching mutable expanded rows."""
    return {**census_summary(), "schools": list(census_rows())}


census_audit.cache_clear = _snapshot_at.cache_clear


def school_audit_by_id(identifier):
    payload = _snapshot()[1].get(identifier)
    return json.loads(payload) if payload is not None else None


def school_identifier(school_name):
    return _snapshot()[2].aliases.get(school_name)


def census_school_name(row):
    return row["school_name"] + (" " + row["english_name"] if row.get("english_name") else "")


@lru_cache(maxsize=1)
def programme_map():
    return {r["id"]: r for name in ("partners_current.jsonl", "partners_reference.jsonl", "earlier_round_programmes.jsonl")
            for r in map(json.loads, (BUNDLE / name).read_text(encoding="utf-8").splitlines()) if r}


def school_audit(school_name):
    return school_index().get(school_name)


def school_index():
    return _snapshot()[2]


school_index.cache_clear = _snapshot_at.cache_clear


def reference_partners(current_partners):
    current_names = {p.school_name for p in current_partners}
    output=[]
    for row in census_rows():
        programmes=[programme_map()[pid] for pid in row.get("programme_ids", [])]
        if any(p["fields"]["school_name"]["value"] in current_names for p in programmes):
            continue
        fields={};details={};reference_data={}
        for key,cell in row["fields"].items():
            public=cell.get("public_reference")
            evidence = public["evidence"][0] if public else (cell["values"][0]["evidence"][0] if cell["values"] else cell["checked_entries"][0])
            value = public.get("value") if public else next((str(f["value"]) for f in cell["values"] if f["value"] is not None), None)
            if value is not None and not isinstance(value,str):
                value=json.dumps(value,ensure_ascii=False)
            fields[key] = ExchangeFieldEvidence(source_url=evidence["source_url"],checked_at=evidence["checked_at"],
                academic_year=evidence.get("applicable_year"),application_round=evidence.get("application_round"),
                status="reference_only" if value is not None else "needs_confirmation",reference_excerpt=value,
                note=cell["reason"] + "；" + evidence.get("locator", "名錄參考"))
            if value is not None:
                reference_data[key]=value
            if key.startswith("host_") or key in {"housing","housing_costs","costs","insurance","living_costs","course_restrictions","latest_forms","transport"}:
                details[key]=PartnerExchangeDetailField(value=value,status="reference_only" if value is not None else "needs_confirmation",
                    reason="接待校來源適用期及淡江提名計畫仍需另核對；一般原文或舊期欄位不作本期資格。",
                    evidence=[fields[key]],research_category="alternative_official_sources_not_fully_checked")
        options=[]
        for programme in programmes:
            values=lambda key:programme["fields"].get(key,{}).get("value")
            options.append(PartnerProgramOption(program_type=f"參考：{programme['academic_year']} {programme['application_round']}（已截止／不得沿用名額）",
                degree_levels=values("degree_levels"),study_period=values("study_period"),quota=str(values("quota")) if values("quota") is not None else None,
                eligibility=values("home_eligibility"),application_info="已結束梯次原文；不等於本期可申請。",
                source_url=programme["fields"]["school_name"]["evidence"][0]["source_url"]))
        name=census_school_name(row)
        note=row["selection_note"]+" 最新日語第二梯已截止；此校沒有核實的本梯開放名額。"
        output.append(PartnerUniversity(school_name=name,country=row["country"],website=row.get("directory_website"),
            program_type="姊妹校協議／歷史計畫參考",availability_status="reference_only" if programmes else "agreement_only",
            availability_note=note,agreement_type="姊妹校協議參考；交換條款及院系範圍需另查",agreement_level=None,
            quota=None,quota_status="reference_only",application_window_status="needs_confirmation",source_url=row["directory_url"],
            checked_at=row.get("detail_checked_at",row["checked_at"]),field_evidence=fields,reference_data=reference_data,
            partner_exchange_details=details,program_options=options,
            student_summary_zh=PartnerStudentSummary(eligibility_points=[note],
                application_steps=["先確認淡江最新年度、梯次及本校對應名額；一般接待校期限不代表淡江接受新申請。"],
                tuition_points=["協議目錄未證明本期互惠免學費，實際費用依提名計畫另核對。"])))
    return output


def census_school_completeness(partner):
    row=school_audit(partner.school_name)
    if row is None:
        raise ValueError("school absent from complete TKU denominator")
    items=[]
    for key,cell in row["fields"].items():
        state=cell["status"]
        status="available" if state in {"verified_current","verified_asset"} else "partial" if state=="reference_only" else "needs_confirmation"
        urls=[e["source_url"] for f in cell["values"] for e in f["evidence"]]
        public=cell.get("public_reference")
        if public:urls += [e["source_url"] for e in public["evidence"]]
        urls += [e["source_url"] for e in cell["checked_entries"]]
        items.append(SchoolCompletenessItem(key=key,label=cell["label"],status=status,
            note=cell["reason"]+f" 查核2026-10-11；狀態{state}，本期核實與參考原文分開計數。",source_urls=list(dict.fromkeys(urls))))
    available=sum(item.status=="available" for item in items)
    return SchoolDataCompleteness(school_name=partner.school_name,country=partner.country,home_university="淡江大學",
        items=items,available_count=available,total_count=len(items),score=available/len(items),
        priority_gaps=[item.label for item in items if item.status!="available"],
        disclaimer="全量機構缺口；一般官方原文及歷史梯次列部分資料，不能計作本期可申請或完整資格。未核實不等於官方明示尚未公告。")
