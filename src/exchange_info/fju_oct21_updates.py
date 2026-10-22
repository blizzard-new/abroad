"""Verified 2026-10-21 FJU general partner list (labelID=40) cleanup and continent Google Drive portals.

Applies the official 2026-10-21 Fu Jen Catholic University (天主教輔仁大學) general partner list
update on `https://iscoie.fju.edu.tw/generalServices.jsp?labelID=40`:
- General partner list cleaned from 234 -> 207 entries by removing 27 entries that were previously
  marked expired (`合約到期` / `合約 過期`) or suspended (`暫停交換` / `暫停開班` / `交流 中止`).
- Reorganized individual partner application document links into 5 continent-level Google Drive portals
  (美洲, 歐洲, 亞洲, 大洋洲, 大陸港澳地區).

Key epistemic boundaries:
1. Not 27 schools newly stopping today (`removed_27_entries_are_newly_suspended_today = False`);
   other programs at the same university (e.g., 聖心女子大學, 梅光學院大學) may still remain in the 207 entries.
2. Retained entries' conditions and the four 116-1 PDFs from yesterday (`file=1344`, `1345`, `1346`, `1347`)
   are unchanged (`retained_conditions_and_four_116_1_pdfs_unchanged = True`).
3. New continent Google Drive folder contents were not fully audited (`continent_drive_contents_fully_audited = False`).
4. The 116-1 application window (`2026/11/01` to `2026/12/24 16:30`) remains unchanged.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .models import (
    ExchangeInfo,
    PartnerUniversity,
    ProcessedPage,
    StudentDashboard,
)

ROOT = Path(__file__).resolve().parents[2]
FJU_BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "fju"
UPDATE_JSON_PATH = ROOT / "sources" / "fju" / "2026-10-21-official-update.json"

PARTNER_LIST_40_URL = "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=40"
CHECKED_AT_ISO = "2026-10-21T02:22:00Z"
CHECKED_DATE = "2026-10-21"
DASHBOARD_OVERVIEW_TITLE = (
    "輔大一般合作姊妹校清單整理（234→207 條）與五洲別 Google Drive 入口（2026-10-21 核實）"
)
PAGE_TITLE = "天主教輔仁大學：赴姊妹校交換學生一般合作清單整理與五洲別 Google Drive 入口（labelID=40，2026-10-21）"

COUNTRY_TO_CONTINENT: dict[str, str] = {
    "美國": "美洲",
    "加拿大": "美洲",
    "墨西哥": "美洲",
    "秘魯": "美洲",
    "哥倫比亞": "美洲",
    "智利": "美洲",
    "巴西": "美洲",
    "澳洲": "大洋洲",
    "澳大利亞": "大洋洲",
    "中國大陸": "大陸港澳地區",
    "中國": "大陸港澳地區",
    "香港": "大陸港澳地區",
    "澳門": "大陸港澳地區",
    "日本": "亞洲",
    "韓國": "亞洲",
    "南韓": "亞洲",
    "泰國": "亞洲",
    "菲律賓": "亞洲",
    "越南": "亞洲",
    "印尼": "亞洲",
    "馬來西亞": "亞洲",
    "新加坡": "亞洲",
    "印度": "亞洲",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def normalize_fju_school_title(title: str) -> str:
    cleaned = re.sub(r"\(原名:[^)]+\)", "", title or "")
    cleaned = re.sub(r"\b(985|211)\b", "", cleaned)
    return re.sub(r"\s+", "", cleaned)


def continent_for_country(country: str) -> str:
    return COUNTRY_TO_CONTINENT.get(country, "歐洲")


def load_fju_oct21_update_payload(update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    payload = json.loads(update_json_path.read_text(encoding="utf-8"))
    if payload.get("school_id") != "fju":
        raise ValueError("Invalid FJU Oct 21 update payload school_id")
    if (
        payload.get("general_partner_list_before") != 234
        or payload.get("general_partner_list_after") != 207
        or payload.get("removed_expired_or_suspended_entries_count") != 27
        or len(payload.get("removed_expired_or_suspended_entries", [])) != 27
    ):
        raise ValueError("Unexpected FJU Oct 21 partner list counts (expected 234 -> 207, 27 removed)")
    if payload.get("removed_27_entries_are_newly_suspended_today") is not False:
        raise ValueError("Removed 27 FJU entries were already marked expired/suspended and are not newly suspended today")
    if payload.get("same_school_other_programs_may_remain") is not True:
        raise ValueError("FJU update must note that other programs at the same school may still remain")
    if payload.get("retained_conditions_and_four_116_1_pdfs_unchanged") is not True:
        raise ValueError("FJU retained conditions and four 116-1 PDFs must be marked unchanged")
    if payload.get("continent_drive_contents_fully_audited") is not False:
        raise ValueError("FJU continent Google Drive folder contents were not fully audited")
    portals = payload.get("continent_google_drive_portals", [])
    if len(portals) != 5 or {p["continent"] for p in portals} != {
        "美洲",
        "歐洲",
        "亞洲",
        "大洋洲",
        "大陸港澳地區",
    }:
        raise ValueError("Expected 5 continent Google Drive portals in FJU Oct 21 payload")
    return payload


def validate_fju_oct21_update_snapshot(update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    payload = load_fju_oct21_update_payload(update_json_path)
    manifest = payload["source_manifest"]
    if set(manifest) != {"label_40_partner_list_20261021"}:
        raise ValueError("Expected label_40_partner_list_20261021 in FJU Oct 21 source_manifest")
    for key, meta in manifest.items():
        local_path = ROOT / meta["file"]
        if not local_path.exists():
            raise FileNotFoundError(f"Missing archived FJU Oct 21 source file for {key}: {local_path}")
        raw = local_path.read_bytes()
        if len(raw) != meta["bytes"]:
            raise ValueError(f"Byte count mismatch for {key}: expected {meta['bytes']}, got {len(raw)}")
        if _sha256_bytes(raw) != meta["sha256"]:
            raise ValueError(f"SHA256 mismatch for {key}: expected {meta['sha256']}")
    return payload


def apply_fju_oct21_partner_view(
    partners: list[PartnerUniversity],
    update_json_path: Path = UPDATE_JSON_PATH,
) -> list[PartnerUniversity]:
    """Return the 207 FJU partner entries remaining on labelID=40 after the 2026-10-21 cleanup."""
    payload = load_fju_oct21_update_payload(update_json_path)
    removed_norm = {
        normalize_fju_school_title(item["school_title"])
        for item in payload["removed_expired_or_suspended_entries"]
    }
    drive_by_continent = {
        item["continent"]: item["drive_url"]
        for item in payload["continent_google_drive_portals"]
    }
    out: list[PartnerUniversity] = []
    for p in partners:
        if p.source_url and p.source_url != PARTNER_LIST_40_URL:
            continue
        norm_name = normalize_fju_school_title(p.school_name)
        if norm_name in removed_norm:
            continue
        continent = continent_for_country(p.country)
        ref_data = dict(p.reference_data)
        ref_data.update(
            label_40_status_20261021="retained_in_207",
            continent_portal_20261021=continent,
            continent_google_drive_url_20261021=drive_by_continent[continent],
        )
        out.append(p.model_copy(update={"reference_data": ref_data}))
    if len(out) != 207:
        raise ValueError(f"Expected 207 active FJU entries after Oct 21 filter, got {len(out)}")
    return out


def apply_fju_oct21_updates(
    bundle: Path = FJU_BUNDLE,
    update_json_path: Path = UPDATE_JSON_PATH,
) -> dict[str, Any]:
    payload = validate_fju_oct21_update_snapshot(update_json_path)
    manifest_entry = payload["source_manifest"]["label_40_partner_list_20261021"]
    drive_by_continent = {
        item["continent"]: item["drive_url"]
        for item in payload["continent_google_drive_portals"]
    }
    removed_by_norm = {
        normalize_fju_school_title(item["school_title"]): item
        for item in payload["removed_expired_or_suspended_entries"]
    }

    oct21_meta = {
        "checked_at": payload["checked_at"],
        "partner_list_url": PARTNER_LIST_40_URL,
        "general_partner_list_before": 234,
        "general_partner_list_after": 207,
        "removed_expired_or_suspended_entries_count": 27,
        "removed_27_entries_are_newly_suspended_today": False,
        "same_school_other_programs_may_remain": True,
        "retained_conditions_and_four_116_1_pdfs_unchanged": True,
        "continent_drive_contents_fully_audited": False,
        "application_window_unchanged": payload["application_window_unchanged"],
        "continent_google_drive_portals": payload["continent_google_drive_portals"],
        "source_file": manifest_entry["file"],
        "source_sha256": manifest_entry["sha256"],
        "source_bytes": manifest_entry["bytes"],
    }

    # 1. Update import_provenance.json (keep prov["sources"] length invariant at 18)
    prov_path = bundle / "import_provenance.json"
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    prov["source_update_20261021"] = oct21_meta
    _write_json(prov_path, prov)

    # 2. Update exchange_info.json
    info_path = bundle / "exchange_info.json"
    info = json.loads(info_path.read_text(encoding="utf-8"))
    oct21_period_line = (
        "2026-10-21 查核更新（labelID=40 一般合作清單整理）：一般合作清單由 234 條整理為 207 條，"
        "移除 27 個原本已標示合約到期／過期或暫停交換／暫停開班／交流中止的條目（不是 27 所學校今天新停招，"
        "同校不同方案如聖心女子大學、梅光學院大學一般交換仍保留），並整理為五洲別 Google Drive 入口"
        "（美洲、歐洲、亞洲、大洋洲、大陸港澳地區）。留存條件及 116-1 四份 PDF 與昨日相同；新 Drive 內文未查齊，"
        "2026/11/01～2026/12/24 16:30 申請期不變。"
    )
    info["application_period"] = [
        *[p for p in info["application_period"] if "2026-10-21 查核更新（labelID=40" not in p],
        oct21_period_line,
    ]
    if PARTNER_LIST_40_URL not in info["source_urls"]:
        info["source_urls"].append(PARTNER_LIST_40_URL)
    ExchangeInfo.model_validate(info)
    _write_json(info_path, info)

    # 3. Update student_dashboard.json
    dash_path = bundle / "student_dashboard.json"
    dash = json.loads(dash_path.read_text(encoding="utf-8"))
    overview = [
        item
        for item in dash.get("program_overview", [])
        if item.get("title") != DASHBOARD_OVERVIEW_TITLE
    ]
    overview.append(
        {
            "title": DASHBOARD_OVERVIEW_TITLE,
            "details": [
                "一般合作清單（labelID=40）由 234 條整理為 207 條，移除 27 個原本已標示「合約到期／合約過期」或「暫停交換／暫停開班／交流中止」的條目。",
                "重要邊界：不是 27 所學校今天新停招，同校不同方案（如聖心女子大學、梅光學院大學之一般交換方案）仍保留於清單中。",
                "各校申請資料整理為五洲別 Google Drive 入口：美洲、歐洲、亞洲、大洋洲、大陸港澳地區。",
                "留存條目條件及昨日 116-1 四份 PDF（file=1344、1345、1346、1347）與昨日相同；新 Google Drive 內文未查齊，2026/11/01～12/24 16:30 申請期維持不變。",
            ],
            "source": {
                "title": manifest_entry["title"],
                "source_url": PARTNER_LIST_40_URL,
                "category": "partner_school",
                "summary": "2026-10-21 查核；一般合作清單 234→207 條（移除 27 個原已標到期／暫停條目）並改為五洲別 Google Drive 入口。",
            },
        }
    )
    dash["program_overview"] = overview
    StudentDashboard.model_validate(dash)
    _write_json(dash_path, dash)

    # 4. Update pages.jsonl
    pages_path = bundle / "pages.jsonl"
    pages = [
        json.loads(line)
        for line in pages_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    pages = [p for p in pages if p.get("title") != PAGE_TITLE]
    drive_lines = [
        f"- {p['continent']}：{p['drive_url']}"
        for p in payload["continent_google_drive_portals"]
    ]
    oct21_page_text = (
        "輔仁大學一般合作姊妹校清單與文件入口整理（2026-10-21 查核，labelID=40）：\n"
        "1. 一般合作清單由 234 條整理為 207 條，移除 27 個原本已標到期／暫停的條目。不是 27 所學校今天新停招，同校不同方案可能仍保留。\n"
        "2. 留存條件及 116-1 四份 PDF 與昨日相同；新 Drive 內文未查齊，2026/11/01～2026/12/24 16:30 申請期不變。\n"
        "3. 五洲別 Google Drive 申請資料入口：\n" + "\n".join(drive_lines)
    )
    oct21_page = {
        "title": PAGE_TITLE,
        "source_url": PARTNER_LIST_40_URL,
        "published_at": "2026-10-21T00:00:00Z",
        "text": oct21_page_text,
        "summary": "一般合作清單 234→207 條，移除 27 個原已標到期／暫停條目（非今日新停招），整理為五洲別 Google Drive 入口；新 Drive 內文未查齊，11/1～12/24 16:30 申請期不變。",
        "category": "partner_school",
        "attachments": [],
        "crawled_at": CHECKED_AT_ISO,
        "content_hash": manifest_entry["sha256"],
    }
    ProcessedPage.model_validate(oct21_page)
    pages.append(oct21_page)
    _write_jsonl(pages_path, pages)

    # 5. Update catalog-completeness.json & verification_status.json
    comp_path = bundle / "catalog-completeness.json"
    comp = json.loads(comp_path.read_text(encoding="utf-8"))
    comp["source_update_20261021"] = oct21_meta
    _write_json(comp_path, comp)

    ver_path = bundle / "verification_status.json"
    ver = json.loads(ver_path.read_text(encoding="utf-8"))
    ver["counts"] = comp
    ver["source_update_20261021"] = oct21_meta
    _write_json(ver_path, ver)

    # 6. Annotate partners.jsonl with 2026-10-21 cleanup status and continent Drive URLs
    partners_path = bundle / "partners.jsonl"
    partners = [
        json.loads(line)
        for line in partners_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    retained_count = 0
    removed_count = 0
    for p in partners:
        norm_name = normalize_fju_school_title(p["school_name"])
        continent = continent_for_country(p["country"])
        ref_data = dict(p.get("reference_data") or {})
        ref_data["continent_portal_20261021"] = continent
        ref_data["continent_google_drive_url_20261021"] = drive_by_continent[continent]
        if p.get("source_url") and p.get("source_url") != PARTNER_LIST_40_URL:
            ref_data["label_40_status_20261021"] = "separate_1347_self_funded_route"
        elif removed_entry := removed_by_norm.get(norm_name):
            removed_count += 1
            ref_data["label_40_status_20261021"] = "removed_expired_or_suspended_in_20261021_cleanup"
            ref_data["label_40_prior_contract_quota"] = removed_entry["contract_quota"]
            ref_data["label_40_prior_note"] = removed_entry["note"]
        else:
            retained_count += 1
            ref_data["label_40_status_20261021"] = "retained_in_207"
        p["reference_data"] = ref_data
        PartnerUniversity.model_validate(p)
    if retained_count != 207 or removed_count != 27:
        raise ValueError(
            f"Expected 207 retained and 27 removed FJU partners, got retained={retained_count}, removed={removed_count}"
        )
    _write_jsonl(partners_path, partners)

    return {
        "school_id": "fju",
        "general_partner_list_before": 234,
        "general_partner_list_after": retained_count,
        "removed_expired_or_suspended_entries_count": removed_count,
        "continent_portals_count": len(drive_by_continent),
    }
