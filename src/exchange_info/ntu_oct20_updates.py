"""Apply the reviewed October 20 NTU OIA school.list and 6 partner detail-page updates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup

from .models import (
    ExchangeFieldEvidence,
    ExchangeInfo,
    PartnerUniversity,
    ProcessedPage,
    StudentDashboard,
)
from .ntu_partner_summary import with_ntu_partner_summary

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "sources/ntu/2026-10-20-official-update.json"
LIST_URL = "https://oia.ntu.edu.tw/outgoing/school.list"
QUOTA_PUBLISHED_IDS = {"1092", "187", "80", "82", "1291", "1093", "604", "90"}
DETAIL_CHANGED_IDS = {"1092", "187", "82", "80", "1187", "978"}
UK_QUOTA_ONLY_IDS = {"1291", "1093", "604", "90"}
DASHBOARD_OVERVIEW_TITLE = "116-1（2027–2028）校級交換學校列表 8 校名額公布與 6 校詳細頁更新（2026-10-20 查核）"
PAGE_TITLE = "國立臺灣大學：" + DASHBOARD_OVERVIEW_TITLE
EXCHANGE_INFO_BULLET = (
    "2026-10-20 查核更新（116-1／2027–2028）：交換列表新增公布 8 校名額（奈梅亨／拉德堡 1 名・最多 2 人、"
    "阿姆斯特丹自由 3 名・最多 4 人、烏特列茲／烏特列支 3 名・最多 6 人、奧斯陸 2 名・最多 4 人、"
    "杜倫 2 名・最多 2 人、肯特 1 名・最多 2 人、愛丁堡 0.5 名・最多 1 人、南安普頓 1 名・最多 2 人）；"
    "共查完 289 校詳細頁（6 頁改變：拉德堡、阿姆斯特丹自由、奧斯陸、烏特列支、近畿、兵庫縣立；283 頁相同，"
    "英國四校僅列表補上名額而詳細頁未變；近畿與兵庫縣立列表名額仍空白；兵庫縣立詳細頁出現大一字樣與臺大中央簡章大二以上要求衝突，不能據此認定大一可申請）。"
)


def load_oct20_update(path: Path = SOURCE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        data.get("format_version") != 1
        or data.get("target_round") != "116-1"
        or data.get("target_academic_year") != "2027/2028"
        or data.get("formal_quota_changed") is not True
        or any(
            data.get(key) is not False
            for key in (
                "application_open_confirmed",
                "all_current_cycle_fields_verified",
                "unverified_forms_and_attachments_treated_as_no_update",
                "hyogo_freshman_eligibility_accepted",
            )
        )
    ):
        raise ValueError("October 20 NTU update must preserve current-cycle, attachment, and Hyogo conflict boundaries")

    counts = data.get("counts", {})
    if counts != {
        "partners": 289,
        "detail_pages_checked": 289,
        "detail_pages_changed": 6,
        "detail_pages_unchanged": 283,
        "list_newly_published_quota_schools": 8,
        "positive_quota_schools_total": 28,
        "blank_quota_schools_total": 254,
        "zero_quota_schools_total": 7,
        "academic_year_units_total": 56.5,
        "maximum_persons_total": 104,
    }:
        raise ValueError("Unexpected October 20 NTU counts")

    manifest = data.get("source_manifest", {})
    expected_sids = {"ntu_school_list_20261020"} | {
        f"ntu_sn_{pid}_20261020" for pid in (QUOTA_PUBLISHED_IDS | DETAIL_CHANGED_IDS)
    }
    if set(manifest) != expected_sids:
        raise ValueError("Unexpected October 20 NTU source manifest")

    bodies: dict[str, bytes] = {}
    for sid, src in manifest.items():
        target = (ROOT / src["local_file"]).resolve()
        if (
            not target.is_relative_to((ROOT / "sources/ntu/2026-10-20-official").resolve())
            or src.get("source_id") != sid
            or src.get("http_status") != 200
            or not src.get("checked_at")
            or not str(src.get("url", "")).startswith("https://")
        ):
            raise ValueError(f"Invalid October 20 source archive entry: {sid}")
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != src["sha256"]:
            raise ValueError(f"October 20 source hash mismatch for {sid}")
        bodies[sid] = raw

    quotas = {item["portal_id"]: item for item in data.get("newly_published_list_quotas", [])}
    if set(quotas) != QUOTA_PUBLISHED_IDS or len(quotas) != 8:
        raise ValueError("Unexpected October 20 newly published quota school set")

    details = {item["portal_id"]: item for item in data.get("changed_detail_pages", [])}
    if set(details) != DETAIL_CHANGED_IDS or len(details) != 6:
        raise ValueError("Unexpected October 20 changed detail page set")

    if set(data.get("uk_quota_only_unchanged_detail_ids", [])) != UK_QUOTA_ONLY_IDS:
        raise ValueError("Unexpected UK quota-only unchanged detail page set")

    # Verify key textual facts in the archived detail HTMLs
    radboud = details["1092"]
    if (
        radboud["pending_warning_present"] is not False
        or radboud["second_exchange_marker_present"] is not True
        or "可選擇交換一學期或一學年" not in radboud["sections"].get("名額", "")
        or "TOEFL iBT 4.0" not in radboud["sections"].get("申請資格", "")
        or "不接受法律學院之學生申請" not in radboud["sections"].get("申請資格", "")
    ):
        raise ValueError("Radboud (sn/1092) detail verification failed")

    vu = details["187"]
    vu_qual = re.sub(r"\s+", "", vu["sections"].get("申請資格", ""))
    if (
        vu["pending_warning_present"] is not False
        or "全學年3名" not in vu["sections"].get("名額", "")
        or "本校大二以上(僅限大學部)學生" not in vu_qual
        or "TOEFLiBT5.0" not in vu_qual
        or "30/08/2027" not in vu["sections"].get("學校年曆", "")
    ):
        raise ValueError("VU Amsterdam (sn/187) detail verification failed")

    oslo = details["82"]
    if (
        oslo["pending_warning_present"] is not False
        or "全學年2名" not in oslo["sections"].get("名額", "")
        or "TOEFL iBT 4.0" not in oslo["sections"].get("申請資格", "")
        or "TOEFL iBT 4.5" not in oslo["sections"].get("申請資格", "")
    ):
        raise ValueError("Oslo (sn/82) detail verification failed")

    utrecht = details["80"]
    if (
        utrecht["pending_warning_present"] is not False
        or "TOEFL iBT 4.5 (讀 4.5 聽 4.5 說 4.5 寫 4.5" not in utrecht["sections"].get("申請資格", "")
        or "biology and biomedical sciences" not in utrecht["sections"].get("注意事項", "")
    ):
        raise ValueError("Utrecht (sn/80) detail verification failed")

    kindai = details["1187"]
    if (
        kindai["pending_warning_present"] is not False
        or kindai["list_quota_after"] != ""
        or "限定交換第一學期人數 1 人" not in kindai["sections"].get("名額", "")
        or "TOEFL iBT 4.5" not in kindai["sections"].get("申請資格", "")
    ):
        raise ValueError("Kindai (sn/1187) detail verification failed")

    hyogo = details["978"]
    if (
        hyogo["pending_warning_present"] is not False
        or hyogo["list_quota_after"] != ""
        or "本校大一/大二學生" not in hyogo["sections"].get("申請資格", "")
    ):
        raise ValueError("Hyogo (sn/978) detail verification failed")

    return data


def apply_oct20_partner_view(
    partners: list[PartnerUniversity],
    path: Path = SOURCE,
) -> list[PartnerUniversity]:
    """Return a copy of the 289 NTU partners with the 2026-10-20 list quotas and 6 detail updates applied."""
    data = load_oct20_update(path)
    quotas = {item["portal_id"]: item for item in data["newly_published_list_quotas"]}
    details = {item["portal_id"]: item for item in data["changed_detail_pages"]}
    out: list[PartnerUniversity] = []
    for p in partners:
        pid = p.source_url.rsplit("/", 1)[-1]
        if pid not in quotas and pid not in details:
            out.append(p)
            continue
        patch: dict = {}
        evidence = dict(p.field_evidence)
        ref_data = dict(p.reference_data)
        if q := quotas.get(pid):
            note = (
                f"臺大116-1／2027–28於2026-10-20公布列表名額：{q['quota_display']}。"
                "名額為學年單位，一學期計0.5；人次是最多人數，不保證錄取；選填系統開放及其他條件仍須確認。"
            )
            patch.update(
                quota=q["quota_display"],
                quota_status="published",
                application_window_status="needs_confirmation",
                availability_note=note,
            )
            evidence["quota"] = ExchangeFieldEvidence(
                source_url=LIST_URL,
                academic_year="116",
                application_round="116-1",
                checked_at=data["checked_at"],
                status="verified_current",
                excerpt=f"{q['quota_after']}／{q['headcount_after']}",
                note=note,
            )
            ref_data.update(
                selection_quota_academic_years=str(q["quota_academic_years"]),
                selection_maximum_persons=str(q["maximum_persons"]),
                selection_source_academic_year="2027/2028",
                quota_published_at_20261020=data["checked_at"],
            )
        if d := details.get(pid):
            secs = d["sections"]
            elig_text = secs.get("申請資格", "")
            if pid == "978":
                elig_text += (
                    "\n【資格衝突提醒（2026-10-20）】詳細頁出現「本校大一/大二學生」字樣，"
                    "但與臺大 116-1 校級甄選簡章規定大學部須「大二以上」衝突，不能據此認定大一可申請。"
                )
            elif d["second_exchange_marker_present"] and "第二次出國交換" not in elig_text:
                elig_text = "此校開放予第二次出國交換之同學選填。\n" + elig_text
            patch["eligibility"] = elig_text
            if "名額" in secs:
                ref_data["portal_detail_quota_reference_20261020"] = secs["名額"]
            ref_data["portal_reference_checked_20261020"] = data["checked_at"]
            ref_data["second_exchange_marker_20261020"] = (
                "present" if d["second_exchange_marker_present"] else "not_stated"
            )
            if pid == "978":
                ref_data["hyogo_freshman_conflict_20261020"] = data["hyogo_conflict_note"]
            evidence["eligibility"] = ExchangeFieldEvidence(
                source_url=d["source_url"],
                checked_at=data["checked_at"],
                status="conflict" if pid == "978" else "reference_only",
                note=(
                    data["hyogo_conflict_note"]
                    if pid == "978"
                    else "2026-10-20詳細頁已移除待確認警語；仍須依列表名額與簡章總則核對。"
                ),
            )
        patch["field_evidence"] = evidence
        patch["reference_data"] = ref_data
        out.append(with_ntu_partner_summary(p.model_copy(update=patch)))
    return out


def apply_oct20_updates(bundle: Path, path: Path = SOURCE) -> dict:
    data = load_oct20_update(path)
    card_details = [
        "交換列表新增公布 8 校原本空白的名額欄（116-1／2027–2028）：拉德堡大學（sn/1092：1 名／最多 2 名）、阿姆斯特丹自由大學（sn/187：3 名／最多 4 名）、烏特列茲／烏特列支大學（sn/80：3 名／最多 6 名）、奧斯陸大學（sn/82：2 名／最多 4 名）、杜倫大學（sn/1291：2 名／最多 2 名）、肯特大學（sn/1093：1 名／最多 2 名）、愛丁堡大學（sn/604：0.5 名／最多 1 名）、南安普頓大學（sn/90：1 名／最多 2 名）。",
        "詳細頁變更（1）：拉德堡大學（sn/1092）移除待確認警語，由一學期改為可一學期或一學年（限第一學期出國），新增「此校開放予第二次出國交換之同學選填」，新增新制 TOEFL iBT 4.0（不接受 Home Edition），並新增排除法律領域（不接受法律學院之學生申請／NOT open to exchange students: Faculty of Law）。",
        "詳細頁變更（2）：阿姆斯特丹自由大學（sn/187）移除待確認警語，年度名額單位 2→3（最多 4 人：一學年 2 人、第一學期 2 人），申請年級由大二/大三放寬至大二以上（僅限大學部），新增新制 TOEFL iBT 5.0（不接受 Home Edition），並更新 2027–2028 學期日期（30/08/2027–28/01/2028、31/01/2028–23/06/2028）及生活費。",
        "詳細頁變更（3）：奧斯陸大學（sn/82）移除待確認警語，年度名額單位 1→2（最多 4 人），新增新制 TOEFL 門檻（學士生 TOEFL iBT 4.0、研究生 TOEFL iBT 4.5，接受 Home Edition）；烏特列茲／烏特列支大學（sn/80）移除待確認警語，新增新制 TOEFL 總分及各科 4.5（讀 4.5 聽 4.5 說 4.5 寫 4.5，不接受 Home Edition），並提醒生物／生醫課程（biology and biomedical sciences）交換名額有限。",
        "詳細頁變更（4，列表名額仍空白）：近畿大學（sn/1187）改為第一學期出國、僅一學期（日語組一學期 1 名、一般組一學期 1 名）並新增一般組語言門檻 TOEFL iBT 4.5（不接受 Home Edition）；兵庫縣立大學（sn/978）詳細頁新增「本校大一/大二學生」字樣，但與臺大中央簡章的大二以上要求衝突，不能據此認定大一可申請。",
        "查核範圍與證據邊界：共查完 289 校詳細頁（6 頁改變、283 頁相同；英國四校 sn/1291、sn/1093、sn/604、sn/90 是列表補上名額，詳細頁無新改動）；部分表單與附件仍未完整核對，不算沒有更新。",
    ]
    detail_urls = [
        "https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/1092",
        "https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/187",
        "https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/82",
        "https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/80",
        "https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/1187",
        "https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/978",
    ]

    # 1. student_dashboard.json
    sd_path = bundle / "student_dashboard.json"
    if sd_path.exists():
        sd = json.loads(sd_path.read_text(encoding="utf-8"))
        overview = [
            item
            for item in sd.get("program_overview", [])
            if item.get("title") != DASHBOARD_OVERVIEW_TITLE
        ]
        overview.append(
            {
                "title": DASHBOARD_OVERVIEW_TITLE,
                "details": card_details,
                "source": {
                    "title": "臺大交換學校一覽表與 6 校詳細頁（2026-10-20 查核）",
                    "source_url": LIST_URL,
                    "category": "partner_school",
                    "summary": "8 校列表名額公布、6 校詳細頁更新、283 校詳細頁未變；兵庫縣立大一字樣與中央簡章衝突不採認。",
                },
            }
        )
        sd["program_overview"] = overview
        StudentDashboard.model_validate(sd)
        sd_path.write_text(
            json.dumps(sd, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    # 2. exchange_info.json
    ei_path = bundle / "exchange_info.json"
    if ei_path.exists():
        ei = json.loads(ei_path.read_text(encoding="utf-8"))
        elig_lines = [
            line
            for line in ei.get("eligibility", [])
            if line != EXCHANGE_INFO_BULLET and "2026-10-20 查核更新（116-1／2027–2028）" not in line
        ]
        elig_lines.append(EXCHANGE_INFO_BULLET)
        ei["eligibility"] = elig_lines
        src_urls = list(ei.get("source_urls", []))
        for u in [LIST_URL, *detail_urls]:
            if u not in src_urls:
                src_urls.append(u)
        ei["source_urls"] = src_urls
        ExchangeInfo.model_validate(ei)
        ei_path.write_text(
            json.dumps(ei, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    # 3. pages.jsonl
    pages_path = bundle / "pages.jsonl"
    if pages_path.exists():
        existing_pages = [
            ProcessedPage.model_validate_json(line)
            for line in pages_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        kept_pages = [p for p in existing_pages if p.title != PAGE_TITLE]
        body_text = "\n".join(card_details) + "\n詳細來源：" + "；".join(detail_urls)
        new_page = ProcessedPage(
            title=PAGE_TITLE,
            source_url=LIST_URL,
            published_at="2026-10-20T00:00:00Z",
            text=body_text,
            summary=body_text,
            category="partner_school",
            attachments=[],
            crawled_at=data["checked_at"],
            content_hash=hashlib.sha256(body_text.encode("utf-8")).hexdigest(),
        )
        kept_pages.append(new_page)
        pages_path.write_text(
            "".join(p.model_dump_json() + "\n" for p in kept_pages),
            encoding="utf-8",
            newline="\n",
        )

    # 4. catalog-completeness.json & import_provenance.json
    meta = {
        "source_snapshot": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "checked_at": data["checked_at"],
        "list_url": LIST_URL,
        "list_sha256": data["source_manifest"]["ntu_school_list_20261020"]["sha256"],
        "formal_quota_changed": True,
        "application_open_confirmed": False,
        "list_newly_published_quota_schools": 8,
        "newly_published_quota_portal_ids": ["1092", "187", "80", "82", "1291", "1093", "604", "90"],
        "partner_detail_pages_checked": 289,
        "partner_detail_pages_changed": 6,
        "partner_detail_pages_unchanged": 283,
        "changed_detail_portal_ids": ["1092", "187", "82", "80", "1187", "978"],
        "uk_quota_only_unchanged_detail_ids": ["1291", "1093", "604", "90"],
        "blank_list_quota_detail_changed_ids": ["1187", "978"],
        "hyogo_freshman_eligibility_accepted": False,
        "hyogo_conflict_note": data["hyogo_conflict_note"],
        "unverified_forms_and_attachments_treated_as_no_update": False,
        "newly_published_list_quotas": data["newly_published_list_quotas"],
    }
    for filename in ("catalog-completeness.json", "import_provenance.json"):
        target_file = bundle / filename
        if target_file.exists():
            payload = json.loads(target_file.read_text(encoding="utf-8"))
            payload["source_update_20261020"] = meta
            target_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )

    from .ntu_oct21_updates import SOURCE as OCT21_SOURCE, apply_oct21_updates
    if OCT21_SOURCE.exists():
        apply_oct21_updates(bundle)

    for item in bundle.iterdir():
        if item.is_file():
            raw_bytes = item.read_bytes()
            if b"\r\n" in raw_bytes:
                item.write_bytes(raw_bytes.replace(b"\r\n", b"\n"))

    return {
        "list_newly_published_quota_schools": 8,
        "detail_pages_changed": 6,
        "detail_pages_unchanged": 283,
        "hyogo_freshman_eligibility_accepted": False,
    }
