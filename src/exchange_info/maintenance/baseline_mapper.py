"""Phase 1 Shadow Baseline Mapper for all 6 supported home universities (CGU, NTPU, NTU, CCU, NCU, TKU) (Spec Section 16 Phase 1, T05, T30)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from ..school_identity import school_identity_key
from ..university_registry import SUPPORTED_UNIVERSITIES
from .contracts import (
    CycleSpec,
    DataFreshnessStatus,
    OfferingLifecycleStatus,
    PublishedFieldEnvelope,
    QuotaUnit,
    QuotaValue,
    ScopeDimension,
    ScopeEntry,
    ScopeMode,
    ValueState,
    build_scope_key,
)
from .store import InstitutionRecord, MaintenanceStore, OfferingRecord, SourceRegistration


HOME_APPROVED_DOMAINS: dict[str, list[str]] = {
    "cgu": ["www.cgu.edu.tw", "cgu.edu.tw"],
    "ntpu": ["new.ntpu.edu.tw", "ntpu.edu.tw"],
    "ntu": ["studyabroad.ntu.edu.tw", "oia.ntu.edu.tw", "ntu.edu.tw"],
    "ccu": ["oia.ccu.edu.tw", "ccu.edu.tw"],
    "ncu": ["oia.ncu.edu.tw", "ncu.edu.tw"],
    "tku": ["oieie.tku.edu.tw", "tku.edu.tw"],
    "fju": ["iscoie.fju.edu.tw", "oie.fju.edu.tw", "www.fju.edu.tw", "fju.edu.tw"],
    "scu": ["icae.scu.edu.tw", "www.scu.edu.tw", "www-ch.scu.edu.tw", "scu.edu.tw"],
    "ntnu": ["bds.oia.ntnu.edu.tw", "oia.ntnu.edu.tw", "www.ntnu.edu.tw", "ntnu.edu.tw"],
    "cycu": ["oia.cycu.edu.tw", "www.cycu.edu.tw", "cycu.edu.tw"],
    "ntust": ["www.oia.ntust.edu.tw", "oia.ntust.edu.tw", "www.ntust.edu.tw", "ntust.edu.tw"],
    "yzu": ["www.yzu.edu.tw", "cm.yzu.edu.tw", "yzu.edu.tw"],
    "fcu": ["oiasap.fcu.edu.tw", "oia.fcu.edu.tw", "service825.fcu.edu.tw", "www.fcu.edu.tw", "fcu.edu.tw"],
    "nsysu": ["oia.nsysu.edu.tw", "partners.oia.nsysu.edu.tw", "cm.nsysu.edu.tw", "www.nsysu.edu.tw", "nsysu.edu.tw"],
    "nchu": ["www.oia.nchu.edu.tw", "oia.nchu.edu.tw", "oiawp.nchu.edu.tw", "iss.nchu.edu.tw", "www.nchu.edu.tw", "nchu.edu.tw"],
    "ntut": ["oia.ntut.edu.tw", "www.cc.ntut.edu.tw", "www.ntut.edu.tw", "ntut.edu.tw"],
    "nccu": ["outbound.nccu.edu.tw", "oic.nccu.edu.tw", "www.nccu.edu.tw", "nccu.edu.tw"],
    "ncku": ["oia.ncku.edu.tw", "exchange.oia.ncku.edu.tw", "management.oia.ncku.edu.tw", "www.ncku.edu.tw", "ncku.edu.tw"],
    "nycu": ["oia.nycu.edu.tw", "www.nycu.edu.tw", "nycu.edu.tw"],
    "nthu": ["oga.site.nthu.edu.tw", "oga-exchange.vm.nthu.edu.tw", "www.nthu.edu.tw", "nthu.edu.tw"],
    "pccu": ["oima.pccu.edu.tw", "japanese.pccu.edu.tw", "kor.pccu.edu.tw", "french.pccu.edu.tw", "crgarl.pccu.edu.tw", "mccd.pccu.edu.tw", "www.pccu.edu.tw", "pccu.edu.tw"],
    "wzu": ["c015.wzu.edu.tw", "d020.wzu.edu.tw", "www.wzu.edu.tw", "wzu.edu.tw"],
    "nkust": ["oia.nkust.edu.tw", "flec.nkust.edu.tw", "www.nkust.edu.tw", "nkust.edu.tw"],
    "yuntech": ["tdx.yuntech.edu.tw", "admissions-oia.yuntech.edu.tw", "www.yuntech.edu.tw", "yuntech.edu.tw"],
    "ntou": ["oia.ntou.edu.tw", "www.ntou.edu.tw", "ntou.edu.tw"],
    "ncue": ["oicaweb.ncue.edu.tw", "www.ncue.edu.tw", "ncue.edu.tw"],
}


def canonical_host_institution_id(school_name: str, country: str | None = None) -> str:
    """Generate a deterministic canonical host institution ID shared across home universities (Spec 2.1, 4.1, T05)."""
    ident = school_identity_key(school_name)
    country_norm = (country or "und").strip().lower()
    digest = hashlib.sha256(f"{ident}|{country_norm}".encode("utf-8")).hexdigest()[:12]
    return f"host_{digest}"


def parse_college_scope_entry(raw_colleges: str | None, home_colleges: tuple[str, ...] = ()) -> ScopeEntry:
    """Map raw college string into explicit ScopeMode enum without conflating all/unspecified/not_applicable (Spec 2.2, 4.1)."""
    text = (raw_colleges or "").strip()
    if not text or text in {"待確認", "未註明", "--", "—", "unknown"}:
        return ScopeEntry(dimension=ScopeDimension.ACADEMIC_UNIT, mode=ScopeMode.UNSPECIFIED)
    if text.lower() in {"不適用", "n/a", "not_applicable"}:
        return ScopeEntry(dimension=ScopeDimension.ACADEMIC_UNIT, mode=ScopeMode.NOT_APPLICABLE)
    if any(tok in text for tok in ("全校", "不限", "各學院", "四院皆可")) or re.search(r"\ball\b", text, re.I):
        return ScopeEntry(dimension=ScopeDimension.ACADEMIC_UNIT, mode=ScopeMode.ALL)

    matched_ids: list[str] = []
    matched_labels: list[str] = []
    for col in home_colleges:
        if col in text or col.replace("學院", "") in text:
            col_id = "unit_" + hashlib.sha256(col.encode("utf-8")).hexdigest()[:8]
            matched_ids.append(col_id)
            matched_labels.append(col)

    if not matched_ids:
        parts = [p.strip() for p in re.split(r"[、,，/／;；]+", text) if p.strip()]
        for part in parts:
            col_id = "unit_" + hashlib.sha256(part.encode("utf-8")).hexdigest()[:8]
            matched_ids.append(col_id)
            matched_labels.append(part)

    return ScopeEntry(
        dimension=ScopeDimension.ACADEMIC_UNIT,
        mode=ScopeMode.EXPLICIT,
        target_ids=tuple(matched_ids),
        target_labels=tuple(matched_labels),
    )


def parse_degree_scope_entry(raw_degrees: str | None) -> ScopeEntry:
    text = (raw_degrees or "").strip()
    if not text or text in {"待確認", "未註明", "--", "—"}:
        return ScopeEntry(dimension=ScopeDimension.DEGREE_LEVEL, mode=ScopeMode.UNSPECIFIED)
    if text.lower() in {"不適用", "n/a", "not_applicable"}:
        return ScopeEntry(dimension=ScopeDimension.DEGREE_LEVEL, mode=ScopeMode.NOT_APPLICABLE)
    if any(tok in text for tok in ("不限", "全校", "大學部及研究所")):
        return ScopeEntry(dimension=ScopeDimension.DEGREE_LEVEL, mode=ScopeMode.ALL)

    levels: list[tuple[str, str]] = []
    if any(tok in text for tok in ("學士", "大學部", "本科", "undergraduate", "bachelor")):
        levels.append(("deg_bachelor", "學士班"))
    if any(tok in text for tok in ("碩士", "master")):
        levels.append(("deg_master", "碩士班"))
    if any(tok in text for tok in ("博士", "doctoral", "phd")):
        levels.append(("deg_doctoral", "博士班"))
    if not levels and any(tok in text for tok in ("研究所", "研究生", "graduate")):
        levels.append(("deg_graduate", "研究所"))

    if not levels:
        return ScopeEntry(dimension=ScopeDimension.DEGREE_LEVEL, mode=ScopeMode.UNSPECIFIED)

    return ScopeEntry(
        dimension=ScopeDimension.DEGREE_LEVEL,
        mode=ScopeMode.EXPLICIT,
        target_ids=tuple(item[0] for item in levels),
        target_labels=tuple(item[1] for item in levels),
    )


def parse_quota_contract(
    raw_quota: str | None,
    *,
    quota_status: str | None = None,
    shared_pool_id: str | None = None,
) -> QuotaValue:
    """Parse raw quota text into strict QuotaValue contract without filling missing values with zero or guessing unit conversions (Spec 2.1, 4.5, T06)."""
    text = (raw_quota or "").strip()
    if quota_status in {"not_published", "quota_unconfirmed"} or not text or text in {"待確認", "待公布", "未定", "未註明"}:
        return QuotaValue(
            value_state=ValueState.NOT_STATED,
            unit=QuotaUnit.UNSPECIFIED_UNIT,
            shared_pool_id=shared_pool_id,
            original_text=raw_quota,
        )

    if quota_status == "zero" or re.fullmatch(r"0\s*(?:名|人|名額)?", text):
        return QuotaValue(
            value_state=ValueState.KNOWN,
            amount=0,
            unit=QuotaUnit.PERSONS,
            shared_pool_id=shared_pool_id,
            original_text=raw_quota,
        )

    # Check for academic year units vs semester units vs persons (Spec 1.1 & 4.5 / T06)
    year_unit_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:個)?(?:學年名額|年度名額單位|full[- ]year\s*unit)", text, re.I)
    sem_unit_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:個)?(?:學期名額|學期單位|semester\s*unit)", text, re.I)
    person_match = re.search(r"(\d+)\s*(?:名|人|位|students?|persons?)", text, re.I)

    if year_unit_match:
        amt = float(year_unit_match.group(1))
        # T06: Do NOT fabricate person count from academic_year_unit unless explicit conversion_rule_id is given!
        return QuotaValue(
            value_state=ValueState.KNOWN,
            amount=amt,
            unit=QuotaUnit.ACADEMIC_YEAR_UNIT,
            period="academic_year",
            shared_pool_id=shared_pool_id,
            original_text=raw_quota,
            conversion_rule_id=None,
            derived_person_max=None,
        )

    if sem_unit_match:
        amt = float(sem_unit_match.group(1))
        return QuotaValue(
            value_state=ValueState.KNOWN,
            amount=amt,
            unit=QuotaUnit.SEMESTER_UNIT,
            period="semester",
            shared_pool_id=shared_pool_id,
            original_text=raw_quota,
        )

    if person_match:
        amt = float(person_match.group(1))
        return QuotaValue(
            value_state=ValueState.KNOWN,
            amount=amt,
            unit=QuotaUnit.POOL_TOTAL if shared_pool_id else QuotaUnit.PERSONS,
            shared_pool_id=shared_pool_id,
            original_text=raw_quota,
        )

    return QuotaValue(
        value_state=ValueState.LEGACY_UNVERIFIED,
        unit=QuotaUnit.UNSPECIFIED_UNIT,
        shared_pool_id=shared_pool_id,
        original_text=raw_quota,
    )


def register_six_home_universities(store: MaintenanceStore) -> dict[str, InstitutionRecord]:
    """Register all supported home universities (CGU, NTPU, NTU, CCU, NCU, TKU, FJU) and their official entry sources."""
    registered: dict[str, InstitutionRecord] = {}
    for prof in SUPPORTED_UNIVERSITIES:
        inst = InstitutionRecord(
            id=prof.id,
            country_code="TW",
            canonical_name=prof.school_name,
            english_name=prof.english_name,
            institution_type="home",
            official_url=prof.official_url,
            aliases=list(prof.aliases),
            colleges=list(prof.colleges),
        )
        store.register_institution(inst)
        registered[prof.id] = inst

        domains = HOME_APPROVED_DOMAINS.get(prof.id, [])
        if prof.official_url:
            host = (urlsplit(prof.official_url).hostname or "").lower()
            if host and host not in domains:
                domains.append(host)

        src = SourceRegistration(
            id=f"src_{prof.id}_official",
            owner_institution_id=prof.id,
            source_type="official_announcement",
            authority_scope=["quota", "home_deadline", "home_eligibility", "home_language_requirement"],
            approved_domains=domains,
            entry_url=prof.official_url,
            reuse_basis="official_public_fact",
            enabled=True,
            risk_class="high",
        )
        store.sources[src.id] = src
    return registered


def import_legacy_partner_rows_to_shadow_store(
    store: MaintenanceStore,
    *,
    home_id: str,
    partner_rows: list[dict[str, Any]],
    program_label: str = "校級赴外交換學生計畫",
    default_cycle_label: str | None = None,
) -> dict[str, Any]:
    """Import legacy partner rows into shadow store, preserving old->new ID mapping and marking unverified fields as legacy_unverified (Spec Phase 1, T05, T30)."""
    if home_id not in store.institutions:
        register_six_home_universities(store)

    home_inst = store.institutions[home_id]
    program_id = f"prog_{home_id}_exchange"

    old_to_new_mapping: dict[str, str] = {}
    not_stated_quotas = 0
    zero_quotas = 0
    legacy_unverified_count = 0

    for idx, row in enumerate(partner_rows):
        school_name = str(row.get("school_name") or "").strip()
        if not school_name:
            continue
        country = row.get("country") or "UND"
        host_id = canonical_host_institution_id(school_name, country)
        if host_id not in store.institutions:
            store.register_institution(
                InstitutionRecord(
                    id=host_id,
                    country_code=str(country),
                    canonical_name=school_name,
                    institution_type="host",
                    official_url=row.get("website"),
                    aliases=[school_name],
                )
            )

        cycle_label = row.get("academic_year") or default_cycle_label or "未註明"
        cycle = CycleSpec.from_explicit_label(program_id=program_id, label=str(cycle_label))
        store.cycles[cycle.id] = cycle

        campus_scope = ScopeEntry(dimension=ScopeDimension.CAMPUS, mode=ScopeMode.UNSPECIFIED)
        unit_scope = parse_college_scope_entry(row.get("colleges"), tuple(home_inst.colleges))
        degree_scope = parse_degree_scope_entry(row.get("degree_levels"))

        scope_key = build_scope_key(
            home_id=home_id,
            host_id=host_id,
            program_id=program_id,
            cycle_id=cycle.id,
            campus_scope=campus_scope,
            academic_unit_scope=unit_scope,
            degree_level_scope=degree_scope,
        )
        # Ensure uniqueness if multiple legacy options share the same scope_key
        offering_id = scope_key if scope_key not in store.offerings else f"{scope_key}_{idx}"

        q_val = parse_quota_contract(
            row.get("quota"),
            quota_status=row.get("quota_status"),
            shared_pool_id=row.get("shared_pool_id"),
        )
        if q_val.value_state == ValueState.NOT_STATED:
            not_stated_quotas += 1
        elif q_val.value_state == ValueState.KNOWN and q_val.amount == 0:
            zero_quotas += 1

        field_evidence = row.get("field_evidence") or {}
        is_verified_current = bool(
            cycle.year_verified
            and field_evidence.get("quota", {}).get("status") == "verified_current"
        )
        freshness = DataFreshnessStatus.CURRENT if is_verified_current else DataFreshnessStatus.LEGACY_UNVERIFIED
        if freshness == DataFreshnessStatus.LEGACY_UNVERIFIED:
            legacy_unverified_count += 1

        source_url = str(row.get("source_url") or home_inst.official_url or "")
        fields: dict[str, PublishedFieldEnvelope] = {
            "quota": PublishedFieldEnvelope(
                value=q_val.model_dump(mode="json"),
                value_state=q_val.value_state,
                unit=q_val.unit.value,
                effective_scope={
                    "academic_unit_mode": unit_scope.mode.value,
                    "degree_level_mode": degree_scope.mode.value,
                },
                evidence_refs=[{"source_url": source_url, "source_pages": row.get("source_pages", [])}],
                last_verified_at=None,
                freshness_status=freshness,
            ),
            "home_eligibility": PublishedFieldEnvelope(
                value=row.get("eligibility"),
                value_state=ValueState.KNOWN if is_verified_current and row.get("eligibility") else (
                    ValueState.LEGACY_UNVERIFIED if row.get("eligibility") else ValueState.NOT_STATED
                ),
                effective_scope={"academic_unit_mode": unit_scope.mode.value},
                evidence_refs=[{"source_url": source_url}],
                last_verified_at=None,
                freshness_status=freshness,
            ),
            "host_language_requirement": PublishedFieldEnvelope(
                value=row.get("language_requirement"),
                value_state=ValueState.LEGACY_UNVERIFIED if row.get("language_requirement") else ValueState.NOT_STATED,
                effective_scope={"degree_level_mode": degree_scope.mode.value},
                evidence_refs=[{"source_url": source_url}],
                last_verified_at=None,
                freshness_status=freshness,
            ),
        }

        lifecycle = OfferingLifecycleStatus.UNKNOWN
        avail = row.get("availability_status")
        if avail == "open" and is_verified_current:
            lifecycle = OfferingLifecycleStatus.OPEN
        elif avail in {"agreement_only", "reference_only"}:
            lifecycle = OfferingLifecycleStatus.AGREEMENT_ONLY
        elif avail == "closed":
            lifecycle = OfferingLifecycleStatus.CLOSED

        offering = OfferingRecord(
            id=offering_id,
            home_id=home_id,
            host_id=host_id,
            program_id=program_id,
            cycle_id=cycle.id,
            scope_key=offering_id,
            campus_scope=campus_scope,
            academic_unit_scope=unit_scope,
            degree_level_scope=degree_scope,
            lifecycle_status=lifecycle,
            fields=fields,
        )
        store.register_offering(offering)
        legacy_key = f"{home_id}:{school_name}:{cycle_label}:{idx}"
        old_to_new_mapping[legacy_key] = offering.id

    return {
        "home_id": home_id,
        "imported_offerings": len(old_to_new_mapping),
        "not_stated_quotas": not_stated_quotas,
        "zero_quotas": zero_quotas,
        "legacy_unverified_count": legacy_unverified_count,
        "old_to_new_mapping": old_to_new_mapping,
    }


def load_six_school_shadow_summary(official_data_root: Path, store: MaintenanceStore) -> dict[str, Any]:
    """Scan the bundled official_data directories for all supported schools and import sample/full records into the shadow store."""
    register_six_home_universities(store)
    school_reports: dict[str, Any] = {}

    # 1. NTU partners.jsonl (288 rows: 282 pending/not_stated quotas, 6 zero quotas)
    ntu_partners_path = official_data_root / "ntu" / "partners.jsonl"
    if ntu_partners_path.exists():
        ntu_rows = [json.loads(line) for line in ntu_partners_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        school_reports["ntu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ntu", partner_rows=ntu_rows, default_cycle_label="116-1"
        )

    # 2. NCU partners.jsonl (full import)
    ncu_partners_path = official_data_root / "ncu" / "partners.jsonl"
    if ncu_partners_path.exists():
        ncu_rows = [json.loads(line) for line in ncu_partners_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        school_reports["ncu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ncu", partner_rows=ncu_rows, default_cycle_label="116-1"
        )

    # 3. CGU catalogue / workflows (deduplicated outbound partners, excluding inbound TEEP)
    cgu_wf_path = official_data_root / "cgu" / "application_workflows.jsonl"
    cgu_cache_path = official_data_root.parents[2] / "data" / "source_cache" / "cgu_catalogue.json"
    cgu_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    if cgu_cache_path.exists():
        cgu_cache = json.loads(cgu_cache_path.read_text(encoding="utf-8"))
        for rec in cgu_cache.get("records", []):
            school_name = str(rec.get("school_name") or "").strip()
            country = str(rec.get("country") or "").strip()
            if not school_name or country == "來臺蹲點實習計畫 TEEP" or "TEEP" in str(rec.get("program_type") or ""):
                continue
            avail = rec.get("availability_status") or "open"
            cgu_by_key[(school_name, country)] = {
                "school_name": school_name,
                "country": country,
                "academic_year": "115學年度",
                "website": rec.get("website"),
                "colleges": rec.get("colleges"),
                "degree_levels": rec.get("degree_levels"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": avail,
                "field_evidence": {"quota": {"status": "verified_current"}} if avail == "open" else {},
                "source_url": rec.get("source_url") or "https://www.cgu.edu.tw/oia-ch",
            }
    if cgu_wf_path.exists():
        for line in cgu_wf_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            wf = json.loads(line)
            school_name = str(wf.get("school_name") or "").strip()
            country = str(wf.get("country") or "").strip()
            if not school_name or country == "來臺蹲點實習計畫 TEEP" or "TEEP" in str(wf.get("program_type") or ""):
                continue
            key = (school_name, country)
            if key not in cgu_by_key:
                is_open = wf.get("applicability_status") == "current_115_spring"
                cgu_by_key[key] = {
                    "school_name": school_name,
                    "country": country,
                    "academic_year": wf.get("academic_year") or "115學年度",
                    "website": wf.get("partner_website"),
                    "availability_status": "open" if is_open else "agreement_only",
                    "field_evidence": {"quota": {"status": "verified_current"}} if is_open else {},
                    "source_url": (wf.get("sources") or wf.get("official_sources") or [{}])[0].get(
                        "url", "https://www.cgu.edu.tw/oia-ch"
                    ),
                }
    if cgu_by_key:
        school_reports["cgu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="cgu", partner_rows=list(cgu_by_key.values()), default_cycle_label="115學年度"
        )

    # 4. NTPU destination_profiles + workflows (206 unique partner schools, 116 preferred over 115)
    ntpu_dp_path = official_data_root / "ntpu" / "destination_profiles.jsonl"
    ntpu_wf_path = official_data_root / "ntpu" / "application_workflows.jsonl"
    ntpu_wf_by_school: dict[str, dict[str, Any]] = {}
    if ntpu_wf_path.exists():
        for line in ntpu_wf_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            wf = json.loads(line)
            sname = str(wf.get("school_name") or "").strip()
            if not sname:
                continue
            prev = ntpu_wf_by_school.get(sname)
            if prev is None or (wf.get("academic_year") == "116學年度" and prev.get("academic_year") != "116學年度"):
                ntpu_wf_by_school[sname] = wf
    ntpu_rows: list[dict[str, Any]] = []
    if ntpu_dp_path.exists():
        for line in ntpu_dp_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            dp = json.loads(line)
            sname = str(dp.get("school_name") or "").strip()
            wf = ntpu_wf_by_school.get(sname, {})
            acad_year = wf.get("academic_year") or "116學年度"
            is_current_116 = acad_year == "116學年度" and wf.get("applicability_status") != "reference_115"
            ntpu_rows.append(
                {
                    "school_name": sname,
                    "country": dp.get("country") or wf.get("country"),
                    "academic_year": acad_year,
                    "website": wf.get("partner_website"),
                    "availability_status": "open" if is_current_116 else "agreement_only",
                    "field_evidence": {"quota": {"status": "verified_current"}} if is_current_116 else {},
                    "source_url": "https://new.ntpu.edu.tw/oia",
                }
            )
    elif ntpu_wf_by_school:
        for sname, wf in ntpu_wf_by_school.items():
            acad_year = wf.get("academic_year") or "116學年度"
            is_current_116 = acad_year == "116學年度"
            ntpu_rows.append(
                {
                    "school_name": sname,
                    "country": wf.get("country"),
                    "academic_year": acad_year,
                    "website": wf.get("partner_website"),
                    "availability_status": "open" if is_current_116 else "agreement_only",
                    "field_evidence": {"quota": {"status": "verified_current"}} if is_current_116 else {},
                    "source_url": "https://new.ntpu.edu.tw/oia",
                }
            )
    if ntpu_rows:
        school_reports["ntpu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ntpu", partner_rows=ntpu_rows, default_cycle_label="116學年度"
        )

    # 5. CCU partners.jsonl (104 rows: 52 open, 49 reference_only, 3 not_published)
    ccu_partners_path = official_data_root / "ccu" / "partners.jsonl"
    ccu_wf_path = official_data_root / "ccu" / "application_workflows.jsonl"
    if ccu_partners_path.exists():
        ccu_rows = [json.loads(line) for line in ccu_partners_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        school_reports["ccu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ccu", partner_rows=ccu_rows, default_cycle_label="2027春季"
        )
    elif ccu_wf_path.exists():
        ccu_rows = []
        for line in ccu_wf_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            wf = json.loads(line)
            ccu_rows.append(
                {
                    "school_name": wf.get("school_name"),
                    "country": wf.get("country"),
                    "academic_year": wf.get("academic_year") or "2027春季",
                    "source_url": "https://oia.ccu.edu.tw/",
                }
            )
        school_reports["ccu"] = import_legacy_partner_rows_to_shadow_store(store, home_id="ccu", partner_rows=ccu_rows)

    # 6. TKU partners_current + destination_profiles (all 287 partner schools: 4 closed current + 283 agreement_only)
    tku_cur_path = official_data_root / "tku" / "partners_current.jsonl"
    tku_dp_path = official_data_root / "tku" / "destination_profiles.jsonl"
    tku_wf_path = official_data_root / "tku" / "application_workflows.jsonl"
    tku_by_school: dict[str, dict[str, Any]] = {}
    if tku_cur_path.exists():
        for line in tku_cur_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            cur = json.loads(line)
            fields = cur.get("fields") or {}
            sname = str((fields.get("school_name") or {}).get("value") or "").strip()
            if not sname:
                continue
            q_num = cur.get("quota_number")
            tku_by_school[sname] = {
                "school_name": sname,
                "country": (fields.get("country") or {}).get("value") or "日本",
                "academic_year": cur.get("academic_year") or "2027-2028",
                "website": (fields.get("website") or {}).get("value"),
                "quota": f"{q_num} 名" if q_num is not None else (fields.get("quota") or {}).get("value"),
                "quota_status": "published" if q_num is not None else "unknown",
                "eligibility": (fields.get("eligibility") or {}).get("value"),
                "language_requirement": (fields.get("language_requirement") or {}).get("value"),
                "availability_status": "closed",
                "field_evidence": {"quota": {"status": "verified_current"}},
                "source_url": "https://oieie.tku.edu.tw/",
            }
    if tku_dp_path.exists():
        for line in tku_dp_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            dp = json.loads(line)
            sname = str(dp.get("school_name") or "").strip()
            if not sname or sname in tku_by_school:
                continue
            tku_by_school[sname] = {
                "school_name": sname,
                "country": dp.get("country"),
                "academic_year": "115學年度",
                "availability_status": "agreement_only",
                "source_url": "https://oieie.tku.edu.tw/",
            }
    elif tku_wf_path.exists() and not tku_by_school:
        for line in tku_wf_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            wf = json.loads(line)
            sname = str(wf.get("school_name") or "").strip()
            tku_by_school[sname] = {
                "school_name": sname,
                "country": wf.get("country"),
                "academic_year": wf.get("academic_year") or "116學年度",
                "source_url": "https://oieie.tku.edu.tw/",
            }
    if tku_by_school:
        school_reports["tku"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="tku", partner_rows=list(tku_by_school.values()), default_cycle_label="116學年度"
        )

    # 7. FJU partners.jsonl (234 partner schools)
    fju_partners_path = official_data_root / "fju" / "partners.jsonl"
    if fju_partners_path.exists():
        fju_rows = []
        for line in fju_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            fju_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "116學年度",
                "website": rec.get("official_website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "reference_only",
                "source_url": rec.get("source_url") or "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=40",
            })
        school_reports["fju"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="fju", partner_rows=fju_rows, default_cycle_label="116學年度"
        )

    # 8. SCU partners.jsonl (191 partner schools)
    scu_partners_path = official_data_root / "scu" / "partners.jsonl"
    if scu_partners_path.exists():
        scu_rows = []
        for line in scu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            scu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "116學年度",
                "website": rec.get("official_website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intl/2025-2026schools",
            })
        school_reports["scu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="scu", partner_rows=scu_rows, default_cycle_label="116學年度"
        )

    # 9. NTNU partners.jsonl (236 partner schools)
    ntnu_partners_path = official_data_root / "ntnu" / "partners.jsonl"
    if ntnu_partners_path.exists():
        ntnu_rows = []
        for line in ntnu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            ntnu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "116-1",
                "website": rec.get("official_website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://bds.oia.ntnu.edu.tw/bds/web/OUT-QUOTALIST",
            })
        school_reports["ntnu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ntnu", partner_rows=ntnu_rows, default_cycle_label="116-1"
        )

    # 10. CYCU partners.jsonl (89 partner schools)
    cycu_partners_path = official_data_root / "cycu" / "partners.jsonl"
    if cycu_partners_path.exists():
        cycu_rows = []
        for line in cycu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            cycu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115-2",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oia.cycu.edu.tw/?page_id=10128&lang=zh",
            })
        school_reports["cycu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="cycu", partner_rows=cycu_rows, default_cycle_label="115-2"
        )

    # 11. NTUST partners.jsonl (237 partner schools)
    ntust_partners_path = official_data_root / "ntust" / "partners.jsonl"
    if ntust_partners_path.exists():
        ntust_rows = []
        for line in ntust_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            ntust_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115-2",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://www.oia.ntust.edu.tw/p/405-1060-62105,c9035.php?Lang=zh-tw",
            })
        school_reports["ntust"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ntust", partner_rows=ntust_rows, default_cycle_label="115-2"
        )

    # 12. YZU partners.jsonl (90 partner schools)
    yzu_partners_path = official_data_root / "yzu" / "partners.jsonl"
    if yzu_partners_path.exists():
        yzu_rows = []
        for line in yzu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            yzu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115-2",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://www.yzu.edu.tw/admin/ao/index.php/tw/2016-03-28-08-35-08/2016-05-06-03-07-02/1319-2026-09-09-02-40-50",
            })
        school_reports["yzu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="yzu", partner_rows=yzu_rows, default_cycle_label="115-2"
        )

    # 13. FCU partners.jsonl (163 partner schools)
    fcu_partners_path = official_data_root / "fcu" / "partners.jsonl"
    if fcu_partners_path.exists():
        fcu_rows = []
        for line in fcu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            fcu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115-1",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oiasap.fcu.edu.tw/",
            })
        school_reports["fcu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="fcu", partner_rows=fcu_rows, default_cycle_label="115-1"
        )

    # 14. NSYSU partners.jsonl (218 partner schools)
    nsysu_partners_path = official_data_root / "nsysu" / "partners.jsonl"
    if nsysu_partners_path.exists():
        nsysu_rows = []
        for line in nsysu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            nsysu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "116",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
            })
        school_reports["nsysu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="nsysu", partner_rows=nsysu_rows, default_cycle_label="116"
        )

    # 15. NCHU partners.jsonl (226 partner schools)
    nchu_partners_path = official_data_root / "nchu" / "partners.jsonl"
    if nchu_partners_path.exists():
        nchu_rows = []
        for line in nchu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            nchu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "116",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info",
            })
        school_reports["nchu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="nchu", partner_rows=nchu_rows, default_cycle_label="116"
        )

    # 16. NTUT partners.jsonl (206 partner schools)
    ntut_partners_path = official_data_root / "ntut" / "partners.jsonl"
    if ntut_partners_path.exists():
        ntut_rows = []
        for line in ntut_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            ntut_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oia.ntut.edu.tw/p/412-1032-9243.php?Lang=zh-tw",
            })
        school_reports["ntut"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ntut", partner_rows=ntut_rows, default_cycle_label="115"
        )

    # 17. NCCU partners.jsonl (266 partner schools)
    nccu_partners_path = official_data_root / "nccu" / "partners.jsonl"
    if nccu_partners_path.exists():
        nccu_rows = []
        for line in nccu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            nccu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115-1",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://outbound.nccu.edu.tw/student-outgoing-list",
            })
        school_reports["nccu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="nccu", partner_rows=nccu_rows, default_cycle_label="115-1"
        )

    # 18. NCKU partners.jsonl (211 partner schools)
    ncku_partners_path = official_data_root / "ncku" / "partners.jsonl"
    if ncku_partners_path.exists():
        ncku_rows = []
        for line in ncku_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            ncku_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "116-1",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oia.ncku.edu.tw/p/404-1032-227700.php?Lang=zh-tw",
            })
        school_reports["ncku"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ncku", partner_rows=ncku_rows, default_cycle_label="116-1"
        )

    # 19. NYCU partners.jsonl (243 partner schools)
    nycu_partners_path = official_data_root / "nycu" / "partners.jsonl"
    if nycu_partners_path.exists():
        nycu_rows = []
        for line in nycu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            nycu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115-2",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0012&id=792",
            })
        school_reports["nycu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="nycu", partner_rows=nycu_rows, default_cycle_label="115-2"
        )

    # 20. NTHU partners.jsonl (176 partner schools)
    nthu_partners_path = official_data_root / "nthu" / "partners.jsonl"
    if nthu_partners_path.exists():
        nthu_rows = []
        for line in nthu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            nthu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115-2",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oga.site.nthu.edu.tw/p/404-1524-21358.php?Lang=zh-tw",
            })
        school_reports["nthu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="nthu", partner_rows=nthu_rows, default_cycle_label="115-2"
        )

    # 21. PCCU partners.jsonl (135 partner schools)
    pccu_partners_path = official_data_root / "pccu" / "partners.jsonl"
    if pccu_partners_path.exists():
        pccu_rows = []
        for line in pccu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            pccu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115-2",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oima.pccu.edu.tw/p/412-1008-14612.php?Lang=zh-tw",
            })
        school_reports["pccu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="pccu", partner_rows=pccu_rows, default_cycle_label="115-2"
        )

    # 22. WZU partners.jsonl (147 partner schools)
    wzu_partners_path = official_data_root / "wzu" / "partners.jsonl"
    if wzu_partners_path.exists():
        wzu_rows = []
        for line in wzu_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            wzu_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115-2",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://c015.wzu.edu.tw/category/140196",
            })
        school_reports["wzu"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="wzu", partner_rows=wzu_rows, default_cycle_label="115-2"
        )

    # 23. NKUST partners.jsonl (107 partner schools)
    nkust_partners_path = official_data_root / "nkust" / "partners.jsonl"
    if nkust_partners_path.exists():
        nkust_rows = []
        for line in nkust_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            nkust_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oia.nkust.edu.tw/p/412-1030-5591.php?Lang=zh-tw",
            })
        school_reports["nkust"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="nkust", partner_rows=nkust_rows, default_cycle_label="115"
        )

    # 24. YunTech partners.jsonl (112 partner schools)
    yuntech_partners_path = official_data_root / "yuntech" / "partners.jsonl"
    if yuntech_partners_path.exists():
        yuntech_rows = []
        for line in yuntech_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            yuntech_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://admissions-oia.yuntech.edu.tw/oe/index/intro/puid/115-2/lang/zh_TW",
            })
        school_reports["yuntech"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="yuntech", partner_rows=yuntech_rows, default_cycle_label="115-2"
        )

    # 25. NTOU partners.jsonl (123 partner schools)
    ntou_partners_path = official_data_root / "ntou" / "partners.jsonl"
    if ntou_partners_path.exists():
        ntou_rows = []
        for line in ntou_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            ntou_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "115",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oia.ntou.edu.tw/p/404-1021-41879.php?Lang=zh-tw",
            })
        school_reports["ntou"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ntou", partner_rows=ntou_rows, default_cycle_label="115-2"
        )

    # 26. NCUE partners.jsonl (108 partner schools)
    ncue_partners_path = official_data_root / "ncue" / "partners.jsonl"
    if ncue_partners_path.exists():
        ncue_rows = []
        for line in ncue_partners_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            ncue_rows.append({
                "school_name": rec.get("school_name"),
                "country": rec.get("country"),
                "academic_year": "116",
                "website": rec.get("official_website") or rec.get("website"),
                "quota": rec.get("quota"),
                "eligibility": rec.get("eligibility"),
                "language_requirement": rec.get("language_requirement"),
                "availability_status": rec.get("availability_status") or "open",
                "source_url": rec.get("source_url") or "https://oicaweb.ncue.edu.tw/p/406-1019-28981,r174.php?Lang=zh-tw",
            })
        school_reports["ncue"] = import_legacy_partner_rows_to_shadow_store(
            store, home_id="ncue", partner_rows=ncue_rows, default_cycle_label="116"
        )

    if store.current_release_id is None:
        store.create_initial_release(actor_id="system_bootstrap", reason="six_school_shadow_baseline")

    return school_reports


def _sql_str(val: str | None) -> str:
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "''") + "'"


def _sql_jsonb(val: Any) -> str:
    raw = json.dumps(val, ensure_ascii=False, sort_keys=True)
    return "'" + raw.replace("'", "''") + "'::jsonb"


def generate_shadow_sync_sql(store: MaintenanceStore) -> str:
    """Generate idempotent SQL to sync the 6-school shadow store into Postgres exchange_maint_* tables."""
    lines: list[str] = ["BEGIN;"]

    # 1. Institutions
    for inst in store.institutions.values():
        lines.append(
            f"INSERT INTO public.exchange_maint_institutions (id, country_code, canonical_name, english_name, institution_type, official_url, current_revision_id) "
            f"VALUES ({_sql_str(inst.id)}, {_sql_str(inst.country_code)}, {_sql_str(inst.canonical_name)}, {_sql_str(inst.english_name)}, "
            f"{_sql_str(inst.institution_type)}, {_sql_str(inst.official_url)}, {_sql_str(inst.current_revision_id)}) "
            f"ON CONFLICT (id) DO UPDATE SET canonical_name = EXCLUDED.canonical_name, current_revision_id = EXCLUDED.current_revision_id, updated_at = now();"
        )

    # 2. Programs (one university-level program per home university)
    for prof in SUPPORTED_UNIVERSITIES:
        prog_id = f"prog_{prof.id}_exchange"
        lines.append(
            f"INSERT INTO public.exchange_maint_programs (id, home_id, program_type, official_label) "
            f"VALUES ({_sql_str(prog_id)}, {_sql_str(prof.id)}, 'university_level', '校級赴外交換學生計畫') "
            f"ON CONFLICT (id) DO NOTHING;"
        )

    # 3. Cycles
    for cyc in store.cycles.values():
        lines.append(
            f"INSERT INTO public.exchange_maint_cycles (id, program_id, original_label, application_year, target_year_start, target_year_end, term_scope, conversion_rule, year_verified) "
            f"VALUES ({_sql_str(cyc.id)}, {_sql_str(cyc.program_id)}, {_sql_str(cyc.cycle_label_original)}, "
            f"{cyc.application_year if cyc.application_year is not None else 'NULL'}, "
            f"{cyc.target_year_start if cyc.target_year_start is not None else 'NULL'}, "
            f"{cyc.target_year_end if cyc.target_year_end is not None else 'NULL'}, "
            f"{_sql_str(cyc.term_scope)}, {_sql_str(cyc.conversion_rule)}, {'true' if cyc.year_verified else 'false'}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )

    # 4. Sources
    for src in store.sources.values():
        lines.append(
            f"INSERT INTO public.exchange_maint_sources (id, owner_institution_id, source_type, authority_scope, approved_domains, entry_url, terms_url, reuse_basis, enabled, policy_version, risk_class) "
            f"VALUES ({_sql_str(src.id)}, {_sql_str(src.owner_institution_id)}, {_sql_str(src.source_type)}, "
            f"{_sql_jsonb(src.authority_scope)}, {_sql_jsonb(src.approved_domains)}, {_sql_str(src.entry_url)}, "
            f"{_sql_str(src.terms_url)}, {_sql_str(src.reuse_basis)}, {'true' if src.enabled else 'false'}, "
            f"{_sql_str(src.policy_version)}, {_sql_str(src.risk_class.value if hasattr(src.risk_class, 'value') else src.risk_class)}) "
            f"ON CONFLICT (id) DO UPDATE SET approved_domains = EXCLUDED.approved_domains, updated_at = now();"
        )

    # 5. Offerings
    for off in store.offerings.values():
        lc = off.lifecycle_status.value if hasattr(off.lifecycle_status, "value") else str(off.lifecycle_status)
        lines.append(
            f"INSERT INTO public.exchange_maint_offerings (id, home_id, host_id, program_id, cycle_id, scope_key, lifecycle_status, current_revision_id) "
            f"VALUES ({_sql_str(off.id)}, {_sql_str(off.home_id)}, {_sql_str(off.host_id)}, {_sql_str(off.program_id)}, "
            f"{_sql_str(off.cycle_id)}, {_sql_str(off.scope_key)}, {_sql_str(lc)}, {_sql_str(off.current_revision_id)}) "
            f"ON CONFLICT (id) DO UPDATE SET current_revision_id = EXCLUDED.current_revision_id, updated_at = now();"
        )

    # 6. Entity revisions
    for rev in store.entity_revisions.values():
        lines.append(
            f"INSERT INTO public.exchange_maint_entity_revisions (id, entity_type, entity_id, payload_schema_version, payload, provenance_map, revision_hash) "
            f"VALUES ({_sql_str(rev.id)}, {_sql_str(rev.entity_type)}, {_sql_str(rev.entity_id)}, 'v1', "
            f"{_sql_jsonb(rev.payload)}, {_sql_jsonb(rev.provenance_map)}, {_sql_str(rev.revision_hash)}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )

    # 7. Releases & release members
    for rel in store.releases.values():
        lines.append(
            f"INSERT INTO public.exchange_maint_releases (id, previous_release_id, reason, published_by, status, idempotency_key) "
            f"VALUES ({_sql_str(rel.id)}, {_sql_str(rel.previous_release_id)}, {_sql_str(rel.reason)}, {_sql_str(rel.published_by)}, "
            f"{_sql_str(rel.status)}, {_sql_str(rel.idempotency_key)}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
        for member_key, rev_id in rel.members.items():
            ent_type, ent_id = member_key.split(":", 1)
            lines.append(
                f"INSERT INTO public.exchange_maint_release_members (release_id, entity_type, entity_id, revision_id) "
                f"VALUES ({_sql_str(rel.id)}, {_sql_str(ent_type)}, {_sql_str(ent_id)}, {_sql_str(rev_id)}) "
                f"ON CONFLICT (release_id, entity_type, entity_id) DO UPDATE SET revision_id = EXCLUDED.revision_id;"
            )

    if store.current_release_id:
        lines.append(
            f"INSERT INTO public.exchange_maint_publication_head (singleton_id, current_release_id, lock_version) "
            f"VALUES (true, {_sql_str(store.current_release_id)}, {store.publication_lock_version}) "
            f"ON CONFLICT (singleton_id) DO UPDATE SET current_release_id = EXCLUDED.current_release_id, lock_version = EXCLUDED.lock_version, updated_at = now();"
        )

    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"

