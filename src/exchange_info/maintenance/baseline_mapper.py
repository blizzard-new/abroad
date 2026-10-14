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
    """Register all 6 supported home universities (CGU, NTPU, NTU, CCU, NCU, TKU) and their official entry sources."""
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
    """Scan the bundled official_data directories for all 6 schools and import sample/full records into the shadow store."""
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

    # 3. CGU workflows (full import)
    cgu_wf_path = official_data_root / "cgu" / "application_workflows.jsonl"
    if cgu_wf_path.exists():
        cgu_rows = []
        for line in cgu_wf_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            wf = json.loads(line)
            cgu_rows.append(
                {
                    "school_name": wf.get("school_name"),
                    "country": wf.get("country"),
                    "academic_year": wf.get("academic_year"),
                    "source_url": (wf.get("official_sources") or [{}])[0].get("source_url", "https://www.cgu.edu.tw/oia-ch"),
                }
            )
        school_reports["cgu"] = import_legacy_partner_rows_to_shadow_store(store, home_id="cgu", partner_rows=cgu_rows)

    # 4. NTPU workflows (full import)
    ntpu_wf_path = official_data_root / "ntpu" / "application_workflows.jsonl"
    if ntpu_wf_path.exists():
        ntpu_rows = []
        for line in ntpu_wf_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            wf = json.loads(line)
            ntpu_rows.append(
                {
                    "school_name": wf.get("school_name"),
                    "country": wf.get("country"),
                    "academic_year": wf.get("academic_year") or "116學年度",
                    "source_url": "https://new.ntpu.edu.tw/oia",
                }
            )
        school_reports["ntpu"] = import_legacy_partner_rows_to_shadow_store(store, home_id="ntpu", partner_rows=ntpu_rows)

    # 5. CCU workflows (full import)
    ccu_wf_path = official_data_root / "ccu" / "application_workflows.jsonl"
    if ccu_wf_path.exists():
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

    # 6. TKU workflows (full import)
    tku_wf_path = official_data_root / "tku" / "application_workflows.jsonl"
    if tku_wf_path.exists():
        tku_rows = []
        for line in tku_wf_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            wf = json.loads(line)
            tku_rows.append(
                {
                    "school_name": wf.get("school_name"),
                    "country": wf.get("country"),
                    "academic_year": wf.get("academic_year") or "116學年度",
                    "source_url": "https://oieie.tku.edu.tw/",
                }
            )
        school_reports["tku"] = import_legacy_partner_rows_to_shadow_store(store, home_id="tku", partner_rows=tku_rows)

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

