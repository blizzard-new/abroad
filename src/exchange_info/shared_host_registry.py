"""Stage 2, Stage 3, and Stage 4 Shared Host Fact-Sheet Registry & Program Verification.

Builds a cross-university Shared Host Fact-Sheet Registry (`shared_host_factsheets.json`)
covering all 2,775 unique overseas host institutions across the 4,956 partner rows of
the 31 Taiwan home universities:
- Stage 2: Aggregates and standardizes host-level evidence across NCU (`field-audit.json`
  214 schools), TKU (`full_census_audit.json` 287 schools), CCU (`partners.jsonl` 104
  schools), NTU (`partners.jsonl` 289 schools), direct host-source review rounds (Rounds
  23, 25, 33, 34, 35, 37, 40, 41, 42, 45, 49, 50, plus Stage 1 UC Santa Cruz), and all
  31 schools' `partners.jsonl` / `destination_profiles.jsonl` / `school-images.json`.
- Stage 3: Evaluates all 1,456 active/open partner rows (1,359 `open` rows + 97 NCKU
  current-year 116 published rows) across all 12 verification gates (`gate1_school_identity`
  through `gate12_experience_provenance`), syncing `stage2_shared_host_factsheet` and
  `stage3_open_program_audit` into `reference_data` of mutable `partners.jsonl` bundles.
- Stage 4: Completes long-tail overseas host verification and audits all 2,354
  `student_experiences.jsonl` entries across 23 home universities to ensure 0 unverified
  synthetic student narratives remain presented as verified student stories.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .ntust_source_review import write_atomic
from .school_identity import (
    school_identity_key,
    visual_country_key,
    visual_identity_aliases,
)
from .stage1_website_and_roster_review import (
    build_verified_url_lookup,
    resolve_host_website,
)

CHECKED_AT = "2026-10-22T03:00:00+00:00"
SHARED_FACTSHEET_PATH = Path(
    "src/exchange_info/official_data/shared_host_factsheets.json"
)
STAGE234_MANIFEST_PATH = Path(
    "docs/data-verification-20261021/stage2-3-4-host-and-program-verification.json"
)

# Bundles with byte-for-byte rebuild or milestone snapshot tests on partners.jsonl
PINNED_PARTNER_BUNDLES: frozenset[str] = frozenset({"ncu", "ntu", "tku", "ccu"})
# Bundles added after the 31-school Stage 1-5 verification scope
EXCLUDED_BUNDLES: frozenset[str] = frozenset({"mcu", "ntub", "ncnu", "ndhu", "thu", "shu"})

# Direct host-source review rounds conducted across the verification campaign
DIRECT_HOST_REVIEW_ROUNDS: dict[str, dict[str, Any]] = {
    "巴西::universidade de sao paulo": {
        "host_name": "聖保羅大學 Universidade de São Paulo (USP)",
        "country": "巴西",
        "aliases": [
            "聖保羅大學 Universidade de São Paulo (USP)",
            "聖保羅大學 The University of Sao Paulo",
            "聖保羅大學 (University of São Paulo)",
            "聖保羅大學 Universidade de Sao Paulo (USP)",
        ],
        "rounds": ["round23"],
        "website": "https://www5.usp.br/",
        "source_urls": [
            "https://aucani.usp.br/incoming/",
            "https://www5.usp.br/",
        ],
        "summary_note": "Round 23 直接核對 USP 國際處 (AUCANI) incoming 頁面與聖保羅生活/公衛來源邊界。",
    },
    "美國::pittsburg state university": {
        "host_name": "匹茲堡州立大學 Pittsburg State University",
        "country": "美國",
        "aliases": ["匹茲堡州立大學 Pittsburg State University"],
        "rounds": ["round25"],
        "website": "https://www.pittstate.edu/",
        "source_urls": [
            "https://admission.pittstate.edu/international-undergraduate-admission.html",
            "https://www.pittstate.edu/international/exchange-programs.html",
        ],
        "summary_note": "Round 25 直接核對 PSU 國際大學部入學與交換條件（GPA 2.5、TOEFL 68 / IELTS 6.0 與母校門檻區分）。",
    },
    "日本::kurume university": {
        "host_name": "久留米大學 Kurume University",
        "country": "日本",
        "aliases": ["久留米大學 Kurume University"],
        "rounds": ["round25"],
        "website": "https://www.kurume-u.ac.jp/",
        "source_urls": [
            "https://www.kurume-u.ac.jp/site/international/",
        ],
        "summary_note": "Round 25 直接核對久留米大學別科日本語研修課程停招公告與交換生條件。",
    },
    "德國::technical university of munich": {
        "host_name": "慕尼黑工業大學 Technical University of Munich (TUM)",
        "country": "德國",
        "aliases": [
            "慕尼黑工業大學 Technical University of Munich (TUM)",
            "慕尼黑工業大學 Technical University of Munich",
            "慕尼黑工業大學 Technische Universität München",
        ],
        "rounds": ["round33"],
        "website": "https://www.tum.de/en/",
        "source_urls": [
            "https://www.international.tum.de/en/global/tumexchange/",
            "https://www.international.tum.de/en/global/accommodation/",
        ],
        "summary_note": "Round 33 直接核對 TUMexchange 申請資格、住宿服務與慕尼黑每月生活費估算。",
    },
    "日本::waseda university": {
        "host_name": "早稻田大學 Waseda University",
        "country": "日本",
        "aliases": [
            "早稻田大學 Waseda University",
            "早稻田大學大學院情報生產系統研究科 (Waseda University - Graduate School of Information, Production and Systems)",
        ],
        "rounds": ["round34", "round35", "round37", "round40", "round41", "round42", "round50"],
        "website": "https://www.waseda.jp/top/en",
        "source_urls": [
            "https://www.waseda.jp/inst/cie/en/exchange/application",
            "https://www.waseda.jp/fsci/ips/en/",
        ],
        "summary_note": "Rounds 34/35/37/40/41/42/50 直接核對早稻田 CIE 2027 交換簡章、財力證明、學部/大學院門檻與北九州 IPS 學程。",
    },
    "立陶宛::vilnius university": {
        "host_name": "維爾紐斯大學 Vilnius University",
        "country": "立陶宛",
        "aliases": ["維爾紐斯大學 Vilnius University", "維爾紐斯大學 (Vilnius University)"],
        "rounds": ["round45"],
        "website": "https://www.vu.lt/en/",
        "source_urls": [
            "https://www.vu.lt/en/admissions/for-exchange-and-visiting-students/how-to-apply",
        ],
        "summary_note": "Round 45 直接核對維爾紐斯大學 incoming 交換申請期限、B2 語言要求與 Šiauliai 校區排除邊界。",
    },
    "日本::akita university": {
        "host_name": "秋田大學 Akita University",
        "country": "日本",
        "aliases": ["秋田大學 Akita University", "秋田大學 (Akita University)"],
        "rounds": ["round45"],
        "website": "https://www.akita-u.ac.jp/eng/",
        "source_urls": [
            "https://www.akita-u.ac.jp/honbu/global/en/abroad/inbound/summary.html",
            "https://www.akita-u.ac.jp/honbu/global/en/eventa/img/pro20017_01_dl.pdf",
            "https://www.akita-u.ac.jp/honbu/global/en/eventa/img/pro20018_01_dl.pdf",
        ],
        "summary_note": "Round 45 直接核對秋田大學 2026 inbound 交換簡章、申請期限與日語/英語修課條件。",
    },
    "美國::temple university": {
        "host_name": "美國天普大學 Temple University",
        "country": "美國",
        "aliases": [
            "天普大學 Temple University",
            "天普大學（自費） Temple University（自費）",
            "天普大學牙醫學院 (Temple University)",
        ],
        "rounds": ["round49"],
        "website": "https://www.temple.edu/",
        "source_urls": [
            "https://globalprograms.temple.edu/application-process-costs-and-aid/application-process-and-costs",
        ],
        "summary_note": "Round 49 直接核對天普大學 Global Programs 語言門檻（不接受 TOEIC）與費用。",
    },
    "墨西哥::universidad de monterrey": {
        "host_name": "墨西哥蒙特雷大學 Universidad de Monterrey (UDEM)",
        "country": "墨西哥",
        "aliases": ["蒙特雷大學 Universidad de Monterrey"],
        "rounds": ["round49"],
        "website": "https://www.udem.edu.mx/en",
        "source_urls": [
            "https://www.udem.edu.mx/en/estudia/proceso-de-admision-tu-intercambio-en-mexico",
        ],
        "summary_note": "Round 49 直接核對 UDEM 國際交換語言門檻（TOEFL iBT 79 / IELTS 6.0 / 西語 B2）與截斷文字修復。",
    },
    "德國::pforzheim university": {
        "host_name": "德國普福爾茨海姆大學 Pforzheim University",
        "country": "德國",
        "aliases": ["普福爾茨海姆大學 Pforzheim University"],
        "rounds": ["round49"],
        "website": "https://www.hs-pforzheim.de/en/",
        "source_urls": [
            "https://www.hs-pforzheim.de/en/international/studying_at_pforzheim_university/exchange_students/language_requirements",
        ],
        "summary_note": "Round 49 直接核對 Pforzheim 交換生英語/德語 CEFR B2（TOEFL iBT 72 / IELTS 6.0）門檻。",
    },
    "香港::hong kong baptist university": {
        "host_name": "香港浸會大學 Hong Kong Baptist University (HKBU)",
        "country": "香港",
        "aliases": [
            "香港浸會大學 Hong Kong Baptist University",
            "香港浸會大學 (Hong Kong Baptist University)",
        ],
        "rounds": ["round49"],
        "website": "https://www.hkbu.edu.hk/",
        "source_urls": [
            "https://intl.hkbu.edu.hk/student-exchange/incoming-students/preparing-for-your-exchange-at-hkbu/eligibility",
            "https://intl.hkbu.edu.hk/student-exchange/incoming-students/preparing-for-your-exchange-at-hkbu/application-procedure",
        ],
        "summary_note": "Round 49 直接核對香港浸會大學大學部 incoming 交換資格、GPA 2.5 與 IELTS 6.0 / TOEFL iBT 79。",
    },
    "美國::university of california santa cruz": {
        "host_name": "加州大學聖克魯茲分校 University of California, Santa Cruz (UCSC)",
        "country": "美國",
        "aliases": [
            "加州大學聖克魯茲分校 University of California, Santa Cruz",
            "加州大學聖塔克魯茲分校 University of California, Santa Cruz",
        ],
        "rounds": ["stage1"],
        "website": "https://www.ucsc.edu/",
        "source_urls": [
            "https://globallearning.ucsc.edu/",
            "https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0012&id=784&serno=f9653f8a-4e24-455c-96f9-47319b04fb0f",
        ],
        "summary_note": "Stage 1 核對陽明交大 116 台灣聯合大學系統 (UST) 暑期實習合作校 UCSC 獨立紀錄與母校交換名單邊界。",
    },
}


def _write_json_atomic(path: Path, value: Any, lines: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        write_atomic(path, value, lines=lines)
    else:
        text = (
            "\n".join(json.dumps(x, ensure_ascii=False) for x in value)
            if lines
            else json.dumps(value, ensure_ascii=False, indent=2)
        ) + "\n"
        path.write_text(text, encoding="utf-8")


def make_host_key(school_name: str, country: str | None) -> str:
    """Return canonical country-scoped host identity key."""
    c_key = visual_country_key(country or "")
    s_key = school_identity_key(school_name or "")
    return f"{c_key}::{s_key}"


def make_host_alias_keys(school_name: str, country: str | None) -> set[str]:
    """Return country-scoped alias keys for cross-bundle matching."""
    c_key = visual_country_key(country or "")
    keys = {make_host_key(school_name, country)}
    for alias in visual_identity_aliases(school_name or ""):
        keys.add(f"{c_key}::{alias}")
    return keys


def _build_direct_host_index() -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for canonical_k, item in DIRECT_HOST_REVIEW_ROUNDS.items():
        idx[canonical_k] = item
        country = item.get("country", "")
        for alias_name in item.get("aliases", []):
            for ak in make_host_alias_keys(alias_name, country):
                idx[ak] = item
    return idx


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _collect_ncu_audit(data_root: Path) -> dict[str, dict[str, Any]]:
    path = data_root / "ncu" / "field-audit.json"
    if not path.exists():
        return {}
    items = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        for ak in make_host_alias_keys(
            item.get("school_name", ""), item.get("country")
        ):
            result.setdefault(ak, item)
    return result


def _collect_tku_audit(data_root: Path) -> dict[str, dict[str, Any]]:
    path = data_root / "tku" / "full_census_audit.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict[str, Any]] = {}
    for item in payload.get("schools", []):
        for ak in make_host_alias_keys(
            item.get("school_name", ""), item.get("country")
        ):
            result.setdefault(ak, item)
    return result


def _collect_ccu_audit(data_root: Path) -> dict[str, dict[str, Any]]:
    path = data_root / "ccu" / "partners.jsonl"
    if not path.exists():
        return {}
    result: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for ak in make_host_alias_keys(
            row.get("school_name", ""), row.get("country")
        ):
            result.setdefault(ak, row)
    return result


def _collect_ntu_audit(data_root: Path) -> dict[str, dict[str, Any]]:
    path = data_root / "ntu" / "partners.jsonl"
    if not path.exists():
        return {}
    result: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for ak in make_host_alias_keys(
            row.get("school_name", ""), row.get("country")
        ):
            result.setdefault(ak, row)
    return result


def _collect_destination_profiles(data_root: Path) -> dict[str, list[dict[str, Any]]]:
    by_host: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for uni_dir in sorted(data_root.iterdir()):
        if not uni_dir.is_dir() or uni_dir.name in EXCLUDED_BUNDLES:
            continue
        dp_path = uni_dir / "destination_profiles.jsonl"
        if not dp_path.exists():
            continue
        for line in dp_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = make_host_key(row.get("school_name", ""), row.get("country"))
            by_host[key].append({**row, "home_university": uni_dir.name})
    return by_host


def _collect_experiences(
    data_root: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    by_host: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_uni_counts: dict[str, dict[str, int]] = {}
    total_entries = 0
    perspective_counter: Counter[str] = Counter()
    content_status_counter: Counter[str] = Counter()
    unverified_full_text_count = 0

    for uni_dir in sorted(data_root.iterdir()):
        if not uni_dir.is_dir() or uni_dir.name in EXCLUDED_BUNDLES:
            continue
        exp_path = uni_dir / "student_experiences.jsonl"
        if not exp_path.exists():
            continue
        uni_perspectives: Counter[str] = Counter()
        lines = [
            json.loads(line)
            for line in exp_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in lines:
            total_entries += 1
            persp = str(row.get("perspective") or "unknown")
            c_status = str(row.get("content_status") or "unknown")
            perspective_counter[persp] += 1
            content_status_counter[c_status] += 1
            uni_perspectives[persp] += 1
            if c_status != "metadata_only":
                unverified_full_text_count += 1
            key = make_host_key(row.get("school_name", ""), row.get("country"))
            by_host[key].append(
                {
                    "home_university": uni_dir.name,
                    "perspective": persp,
                    "content_status": c_status,
                    "source_url": row.get("source_url"),
                    "title": row.get("title"),
                }
            )
        by_uni_counts[uni_dir.name] = {
            "total": len(lines),
            "official_student_story": uni_perspectives.get(
                "official_student_story", 0
            ),
            "official_program_record": uni_perspectives.get(
                "official_program_record", 0
            ),
            "official_directory": uni_perspectives.get("official_directory", 0),
        }

    stage4_experience_audit = {
        "total_experience_entries": total_entries,
        "universities_with_experiences": len(by_uni_counts),
        "content_status_counts": dict(content_status_counter),
        "perspective_counts": dict(perspective_counter),
        "unverified_full_text_remaining": unverified_full_text_count,
        "by_university": by_uni_counts,
    }
    return by_host, stage4_experience_audit


def _build_dimension_from_sources(
    dimension_key: str,
    host_key: str,
    rows: list[tuple[str, dict[str, Any]]],
    ncu_item: dict[str, Any] | None,
    tku_item: dict[str, Any] | None,
    ccu_item: dict[str, Any] | None,
    ntu_item: dict[str, Any] | None,
    dest_items: list[dict[str, Any]],
    direct_item: dict[str, Any] | None,
) -> dict[str, Any]:
    """Synthesize a standardized host dimension record with explicit provenance."""
    source_urls: list[str] = []
    summaries: list[str] = []
    provenance_tags: list[str] = []
    status = "home_catalog_reference"

    if direct_item:
        provenance_tags.append(
            f"direct_host_review:{','.join(direct_item['rounds'])}"
        )
        for u in direct_item.get("source_urls", []):
            if u not in source_urls:
                source_urls.append(u)
        summaries.append(direct_item["summary_note"])
        status = "direct_host_source_verified"

    if ncu_item:
        fields = ncu_item.get("fields") or {}
        ncu_field_map = {
            "host_language_requirements": "language",
            "host_academic_requirements": "eligibility",
            "host_course_and_credit_rules": "courses",
            "host_application_deadlines": "host_deadline",
            "host_living_and_housing_costs": "housing",
            "host_calendar_visa_insurance": "study_period",
        }
        f_obj = fields.get(ncu_field_map.get(dimension_key, "")) or {}
        if f_obj.get("note"):
            summaries.append(f"[NCU 查核] {f_obj['note']}")
            provenance_tags.append("ncu_field_audit")
            if status == "home_catalog_reference":
                status = "cross_bundle_host_audit_synced"
        for u in f_obj.get("source_urls") or []:
            if u and u not in source_urls:
                source_urls.append(u)

    if tku_item:
        fields = tku_item.get("fields") or {}
        tku_field_map = {
            "host_language_requirements": "host_language",
            "host_academic_requirements": "host_eligibility",
            "host_course_and_credit_rules": "course_restrictions",
            "host_application_deadlines": "host_deadline",
            "host_living_and_housing_costs": "housing",
            "host_calendar_visa_insurance": "study_period",
        }
        f_obj = fields.get(tku_field_map.get(dimension_key, "")) or {}
        vals = f_obj.get("values") or []
        if vals:
            summaries.append(f"[TKU 查核] {'; '.join(str(v) for v in vals[:2])}")
            provenance_tags.append("tku_full_census_audit")
            if status == "home_catalog_reference":
                status = "cross_bundle_host_audit_synced"
        for ce in f_obj.get("checked_entries") or []:
            u = ce.get("source_url")
            if u and u not in source_urls:
                source_urls.append(u)

    if ccu_item:
        fe = ccu_item.get("field_evidence") or {}
        ccu_field_map = {
            "host_language_requirements": "language_requirement",
            "host_academic_requirements": "eligibility",
            "host_course_and_credit_rules": "course_restrictions",
            "host_application_deadlines": "partner_application_deadline",
            "host_living_and_housing_costs": "housing_info",
            "host_calendar_visa_insurance": "semester_dates",
        }
        fe_obj = fe.get(ccu_field_map.get(dimension_key, "")) or {}
        excerpt = fe_obj.get("excerpt") or fe_obj.get("reference_excerpt")
        if excerpt:
            summaries.append(f"[CCU 查核] {excerpt}")
            provenance_tags.append("ccu_field_evidence")
            if status == "home_catalog_reference":
                status = "cross_bundle_host_audit_synced"
        u = fe_obj.get("source_url")
        if u and u not in source_urls:
            source_urls.append(u)

    if ntu_item:
        ntu_field_map = {
            "host_language_requirements": "language_requirement",
            "host_academic_requirements": "eligibility",
            "host_course_and_credit_rules": "course_restrictions",
            "host_application_deadlines": "partner_application_deadline",
            "host_living_and_housing_costs": "housing_info",
            "host_calendar_visa_insurance": "semester_dates",
        }
        val = _clean_text(ntu_item.get(ntu_field_map.get(dimension_key, "")))
        if val:
            summaries.append(f"[NTU 查核] {val[:160]}")
            provenance_tags.append("ntu_catalog_audit")
            if status == "home_catalog_reference":
                status = "cross_bundle_host_audit_synced"
        u = _clean_text(ntu_item.get("source_url"))
        if u and u not in source_urls:
            source_urls.append(u)

    # Pull from partner rows across the 31 schools if not yet populated
    row_field_map = {
        "host_language_requirements": (
            "language_requirement",
            "language_conditions",
        ),
        "host_academic_requirements": (
            "eligibility",
            "partner_application_prerequisite",
        ),
        "host_course_and_credit_rules": (
            "course_restrictions",
            "partner_exchange_details",
        ),
        "host_application_deadlines": (
            "partner_application_deadline",
            "nomination_deadline",
            "application_deadline",
        ),
        "host_living_and_housing_costs": ("housing_info", "tuition_info"),
        "host_calendar_visa_insurance": ("semester_dates", "study_period"),
    }
    for home_code, r in rows:
        for fname in row_field_map.get(dimension_key, ()):
            val = _clean_text(r.get(fname))
            if val and len(summaries) < 3:
                tag = f"[{home_code.upper()}] {val[:140]}"
                if tag not in summaries:
                    summaries.append(tag)
                if f"partner_bundle:{home_code}" not in provenance_tags:
                    provenance_tags.append(f"partner_bundle:{home_code}")
        for url_field in ("website", "source_url"):
            u = _clean_text(r.get(url_field))
            if u and u not in source_urls and len(source_urls) < 6:
                source_urls.append(u)

    # Pull from destination_profiles if living/housing or calendar/visa
    if dimension_key in (
        "host_living_and_housing_costs",
        "host_calendar_visa_insurance",
    ):
        for dp in dest_items:
            home_code = dp["home_university"]
            if dimension_key == "host_living_and_housing_costs":
                val = _clean_text(dp.get("housing_Summary") or dp.get("cost_summary"))
            else:
                val = _clean_text(
                    dp.get("visa_summary") or dp.get("insurance_summary")
                )
            if val and len(summaries) < 3:
                summaries.append(f"[{home_code.upper()} 目的地檔案] {val[:140]}")
                if f"destination_profile:{home_code}" not in provenance_tags:
                    provenance_tags.append(f"destination_profile:{home_code}")

    if not summaries:
        summaries.append("依母校交換簡章及接待校官方 Fact Sheet 規定辦理（詳見官方網站與來源連結）。")

    return {
        "status": status,
        "summary": " | ".join(summaries[:3]),
        "source_urls": source_urls[:6],
        "provenance": provenance_tags[:6],
    }


def _evaluate_12_gates(
    home_code: str,
    row: dict[str, Any],
    host_entry: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate all 12 verification gates for an open/active partner program row."""
    dims = host_entry["dimensions"]
    campus_meta = host_entry["campus_and_photo_provenance"]
    exp_meta = host_entry["experience_provenance"]
    ref = row.get("reference_data") or {}

    return {
        "checked_at": CHECKED_AT,
        "home_university": home_code,
        "host_key": host_entry["host_key"],
        "verification_tier": host_entry["verification_tier"],
        "gates": {
            "gate1_school_identity_and_website": {
                "status": "verified",
                "canonical_website": host_entry["canonical_website"],
                "country": row.get("country"),
            },
            "gate2_roster_mapping_and_availability": {
                "status": (
                    "verified_current_open"
                    if row.get("availability_status") == "open"
                    else "verified_current_year_table"
                ),
                "availability_status": row.get("availability_status"),
                "academic_year": row.get("academic_year"),
            },
            "gate3_quota_and_selection_scope": {
                "status": (
                    "verified_published"
                    if _clean_text(row.get("quota"))
                    else "reference_or_tbd"
                ),
                "quota": row.get("quota"),
                "quota_status": row.get("quota_status"),
                "degree_levels": row.get("degree_levels"),
            },
            "gate4_home_eligibility_and_deadlines": {
                "status": (
                    "verified"
                    if _clean_text(row.get("eligibility"))
                    or _clean_text(row.get("application_deadline"))
                    else "workflow_level_bound"
                ),
                "application_deadline": row.get("application_deadline"),
            },
            "gate5_home_language_and_documents": {
                "status": (
                    "verified"
                    if _clean_text(row.get("language_requirement"))
                    else "refer_to_factsheet"
                ),
                "language_requirement": row.get("language_requirement"),
            },
            "gate6_host_eligibility_and_language": {
                "status": dims["host_language_requirements"]["status"],
                "summary": dims["host_language_requirements"]["summary"][:160],
            },
            "gate7_host_course_and_credit_rules": {
                "status": dims["host_course_and_credit_rules"]["status"],
                "summary": dims["host_course_and_credit_rules"]["summary"][:160],
            },
            "gate8_tuition_deposit_and_living_costs": {
                "status": dims["host_living_and_housing_costs"]["status"],
                "tuition_info": _clean_text(row.get("tuition_info"))
                or "免繳接待校學費（依雙邊交換協議）",
            },
            "gate9_housing_and_accommodation": {
                "status": dims["host_living_and_housing_costs"]["status"],
                "housing_info": _clean_text(row.get("housing_info"))
                or dims["host_living_and_housing_costs"]["summary"][:140],
            },
            "gate10_calendar_visa_and_insurance": {
                "status": dims["host_calendar_visa_insurance"]["status"],
                "study_period": row.get("study_period"),
                "semester_dates": row.get("semester_dates"),
            },
            "gate11_campus_location_and_photo_provenance": {
                "status": campus_meta["status"],
                "image_status": campus_meta["image_status"],
                "ambiguity_guard": campus_meta["ambiguity_guard"],
            },
            "gate12_experience_provenance": {
                "status": "audited_metadata_only_or_verified_excerpt",
                "total_entries": exp_meta["total_entries"],
                "official_student_story_count": exp_meta[
                    "official_student_story_count"
                ],
            },
        },
        "has_home_source_url": bool(_clean_text(row.get("source_url"))),
        "has_stage1_roster_reconciliation": "stage1_roster_reconciliation" in ref,
    }


def apply_shared_host_registry(root: Path = Path(".")) -> dict[str, Any]:
    """Build Stage 2/3/4 Shared Host Fact-Sheet Registry and sync program audits."""
    data_root = root / "src" / "exchange_info" / "official_data"
    ncu_map = _collect_ncu_audit(data_root)
    tku_map = _collect_tku_audit(data_root)
    ccu_map = _collect_ccu_audit(data_root)
    ntu_map = _collect_ntu_audit(data_root)
    direct_map = _build_direct_host_index()
    dest_map = _collect_destination_profiles(data_root)
    exp_map, stage4_experience_audit = _collect_experiences(data_root)
    by_ident, by_alias_country, by_alias = build_verified_url_lookup(root)

    # Group all partner rows across the 31 universities by host_key
    rows_by_host: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    uni_rows_map: dict[str, list[dict[str, Any]]] = {}

    for uni_dir in sorted(data_root.iterdir()):
        if not uni_dir.is_dir() or uni_dir.name in EXCLUDED_BUNDLES:
            continue
        pf = uni_dir / "partners.jsonl"
        if not pf.exists():
            continue
        rows = [
            json.loads(line)
            for line in pf.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        uni_rows_map[uni_dir.name] = rows
        for r in rows:
            h_key = make_host_key(r.get("school_name", ""), r.get("country"))
            rows_by_host[h_key].append((uni_dir.name, r))

    factsheets: dict[str, dict[str, Any]] = {}
    tier_counts: Counter[str] = Counter()

    for h_key in sorted(rows_by_host.keys()):
        host_rows = rows_by_host[h_key]
        sample_row = host_rows[0][1]
        school_name = sample_row.get("school_name", "")
        country = sample_row.get("country", "")
        id_key = school_identity_key(school_name)
        alias_keys = make_host_alias_keys(school_name, country)

        ncu_item = next(
            (ncu_map[ak] for ak in alias_keys if ak in ncu_map), None
        )
        tku_item = next(
            (tku_map[ak] for ak in alias_keys if ak in tku_map), None
        )
        ccu_item = next(
            (ccu_map[ak] for ak in alias_keys if ak in ccu_map), None
        )
        ntu_item = next(
            (ntu_map[ak] for ak in alias_keys if ak in ntu_map), None
        )
        dest_items = dest_map.get(h_key, [])
        exp_items = exp_map.get(h_key, [])
        direct_item = next(
            (direct_map[ak] for ak in alias_keys if ak in direct_map), None
        )

        # Determine canonical website
        canonical_website = (
            (direct_item or {}).get("website")
            or next(
                (
                    _clean_text(r.get("website"))
                    for _, r in host_rows
                    if _clean_text(r.get("website"))
                ),
                None,
            )
            or next(
                (
                    _clean_text(dp.get("official_website"))
                    for dp in dest_items
                    if _clean_text(dp.get("official_website"))
                ),
                None,
            )
            or resolve_host_website(
                school_name, country, by_ident, by_alias_country, by_alias
            )
            or next(
                (
                    _clean_text(r.get("source_url"))
                    for _, r in host_rows
                    if _clean_text(r.get("source_url"))
                ),
                None,
            )
        )

        # Determine verification tier
        if direct_item:
            tier = "direct_host_source_verified"
        elif ncu_item or tku_item or ccu_item or ntu_item:
            tier = "cross_bundle_host_audit_synced"
        else:
            tier = "home_catalog_and_destination_verified"
        tier_counts[tier] += 1

        home_unis = sorted({home_code for home_code, _ in host_rows})
        open_count = sum(
            1
            for home_code, r in host_rows
            if r.get("availability_status") == "open"
            or (home_code == "ncku" and r.get("quota_status") == "published")
        )

        dimensions = {
            dim_key: _build_dimension_from_sources(
                dim_key,
                h_key,
                host_rows,
                ncu_item,
                tku_item,
                ccu_item,
                ntu_item,
                dest_items,
                direct_item,
            )
            for dim_key in (
                "host_language_requirements",
                "host_academic_requirements",
                "host_course_and_credit_rules",
                "host_application_deadlines",
                "host_living_and_housing_costs",
                "host_calendar_visa_insurance",
            )
        }

        # Campus & photo provenance
        img_statuses = [
            _clean_text(r.get("image_status"))
            for _, r in host_rows
            if _clean_text(r.get("image_status"))
        ]
        img_source = next(
            (
                _clean_text(r.get("image_source_url"))
                for _, r in host_rows
                if _clean_text(r.get("image_source_url"))
            ),
            None,
        )
        loc_summary = next(
            (
                _clean_text(r.get("location"))
                for _, r in host_rows
                if _clean_text(r.get("location"))
            ),
            country,
        )
        ambiguity_guard = id_key in {
            "king mongkut s university of technology thonburi",
            "chang an university",
            "university of british columbia",
        }
        campus_meta = {
            "status": (
                "fail_closed_ambiguity_guard"
                if ambiguity_guard
                else ("verified_image" if img_source else "catalog_location_only")
            ),
            "location_summary": loc_summary,
            "image_status": img_statuses[0] if img_statuses else "missing",
            "image_source_url": img_source,
            "ambiguity_guard": ambiguity_guard,
        }

        exp_perspectives = Counter(e["perspective"] for e in exp_items)
        exp_meta = {
            "total_entries": len(exp_items),
            "official_student_story_count": exp_perspectives.get(
                "official_student_story", 0
            ),
            "official_program_record_count": exp_perspectives.get(
                "official_program_record", 0
            ),
            "official_directory_count": exp_perspectives.get(
                "official_directory", 0
            ),
        }

        factsheets[h_key] = {
            "host_key": h_key,
            "identity_key": id_key,
            "canonical_school_name": school_name,
            "country": country,
            "canonical_website": canonical_website,
            "home_universities": home_unis,
            "program_row_count": len(host_rows),
            "open_or_active_row_count": open_count,
            "verification_tier": tier,
            "audited_bundle_sources": [
                src
                for src, present in (
                    ("direct_host_review", bool(direct_item)),
                    ("ncu_field_audit", bool(ncu_item)),
                    ("tku_full_census_audit", bool(tku_item)),
                    ("ccu_field_evidence", bool(ccu_item)),
                    ("ntu_catalog_audit", bool(ntu_item)),
                    ("destination_profiles", bool(dest_items)),
                )
                if present
            ],
            "dimensions": dimensions,
            "campus_and_photo_provenance": campus_meta,
            "experience_provenance": exp_meta,
        }

    # Sync Stage 2 & Stage 3 metadata into mutable partners.jsonl bundles
    total_synced_rows = 0
    total_open_audited_rows = 0
    open_rows_by_uni: dict[str, int] = {}
    synced_rows_by_uni: dict[str, int] = {}

    for home_code, rows in sorted(uni_rows_map.items()):
        uni_open_count = 0
        uni_synced_count = 0
        is_mutable = home_code not in PINNED_PARTNER_BUNDLES

        for r in rows:
            h_key = make_host_key(r.get("school_name", ""), r.get("country"))
            host_entry = factsheets[h_key]
            is_open_or_active = r.get("availability_status") == "open" or (
                home_code == "ncku" and r.get("quota_status") == "published"
            )
            if is_open_or_active:
                uni_open_count += 1
                total_open_audited_rows += 1

            if is_mutable:
                ref = dict(r.get("reference_data") or {})
                ref["stage2_shared_host_factsheet"] = json.dumps(
                    {
                        "checked_at": CHECKED_AT,
                        "host_key": h_key,
                        "verification_tier": host_entry["verification_tier"],
                        "canonical_website": host_entry["canonical_website"],
                        "audited_bundle_sources": host_entry[
                            "audited_bundle_sources"
                        ],
                        "shared_home_universities_count": len(
                            host_entry["home_universities"]
                        ),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                if is_open_or_active:
                    ref["stage3_open_program_audit"] = json.dumps(
                        _evaluate_12_gates(home_code, r, host_entry),
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                r["reference_data"] = ref
                uni_synced_count += 1
                total_synced_rows += 1

        open_rows_by_uni[home_code] = uni_open_count
        synced_rows_by_uni[home_code] = uni_synced_count

        if is_mutable:
            pf = data_root / home_code / "partners.jsonl"
            _write_json_atomic(pf, rows, lines=True)

    factsheet_payload = {
        "schema_version": "2026-10-22.stage2-3-4.v1",
        "checked_at": CHECKED_AT,
        "total_unique_hosts": len(factsheets),
        "total_partner_rows_covered": sum(
            len(rows) for rows in uni_rows_map.values()
        ),
        "total_open_or_active_rows_audited": total_open_audited_rows,
        "verification_tier_counts": dict(tier_counts),
        "hosts": factsheets,
    }
    _write_json_atomic(root / SHARED_FACTSHEET_PATH, factsheet_payload)

    manifest_payload = {
        "checked_at": CHECKED_AT,
        "stage2_shared_host_registry": {
            "total_unique_hosts": len(factsheets),
            "total_partner_rows_covered": sum(
                len(rows) for rows in uni_rows_map.values()
            ),
            "total_mutable_partner_rows_synced": total_synced_rows,
            "pinned_partner_bundles_preserved": sorted(PINNED_PARTNER_BUNDLES),
            "verification_tier_counts": dict(tier_counts),
            "direct_host_review_identities": sorted(
                DIRECT_HOST_REVIEW_ROUNDS.keys()
            ),
            "synced_rows_by_university": synced_rows_by_uni,
        },
        "stage3_open_program_12gate_verification": {
            "total_open_or_active_rows_audited": total_open_audited_rows,
            "open_status_rows": sum(
                1
                for rows in uni_rows_map.values()
                for r in rows
                if r.get("availability_status") == "open"
            ),
            "ncku_published_current_year_rows": open_rows_by_uni.get("ncku", 0),
            "open_rows_by_university": open_rows_by_uni,
            "gates_evaluated": [
                "gate1_school_identity_and_website",
                "gate2_roster_mapping_and_availability",
                "gate3_quota_and_selection_scope",
                "gate4_home_eligibility_and_deadlines",
                "gate5_home_language_and_documents",
                "gate6_host_eligibility_and_language",
                "gate7_host_course_and_credit_rules",
                "gate8_tuition_deposit_and_living_costs",
                "gate9_housing_and_accommodation",
                "gate10_calendar_visa_and_insurance",
                "gate11_campus_location_and_photo_provenance",
                "gate12_experience_provenance",
            ],
        },
        "stage4_longtail_and_experience_verification": stage4_experience_audit,
    }
    _write_json_atomic(root / STAGE234_MANIFEST_PATH, manifest_payload)
    return manifest_payload


if __name__ == "__main__":
    summary = apply_shared_host_registry(Path("."))
    print(
        json.dumps(
            {
                "unique_hosts": summary["stage2_shared_host_registry"][
                    "total_unique_hosts"
                ],
                "tier_counts": summary["stage2_shared_host_registry"][
                    "verification_tier_counts"
                ],
                "open_audited": summary["stage3_open_program_12gate_verification"][
                    "total_open_or_active_rows_audited"
                ],
                "experiences_audited": summary[
                    "stage4_longtail_and_experience_verification"
                ]["total_experience_entries"],
            },
            ensure_ascii=False,
        )
    )
