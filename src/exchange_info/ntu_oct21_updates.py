"""Apply the reviewed October 21 NTU OIA school.list (6 quotas) and 28 partner detail-page updates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .models import (
    ExchangeFieldEvidence,
    ExchangeInfo,
    PartnerUniversity,
    ProcessedPage,
    StudentDashboard,
)
from .ntu_oct20_updates import apply_oct20_partner_view
from .ntu_partner_summary import with_ntu_partner_summary

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "sources/ntu/2026-10-21-official-update.json"
LIST_URL = "https://oia.ntu.edu.tw/outgoing/school.list"

QUOTA_PUBLISHED_IDS = {"1301", "392", "601", "67", "63", "535"}
JAPAN_DETAIL_CHANGED_IDS = {"817", "824", "798", "1009", "978", "809", "816", "927", "1004", "955"}
FRANCE_DETAIL_CHANGED_IDS = {"1301", "392", "601", "67", "63", "818"}
LATVIA_DETAIL_CHANGED_IDS = {"535"}
AUSTRALIA_PENDING_IDS = {"313", "1109", "1307", "206", "95", "94", "93", "210", "96", "92"}
CANADA_DETAIL_CHANGED_IDS = {"5"}
DETAIL_CHANGED_IDS = (
    JAPAN_DETAIL_CHANGED_IDS
    | FRANCE_DETAIL_CHANGED_IDS
    | LATVIA_DETAIL_CHANGED_IDS
    | AUSTRALIA_PENDING_IDS
    | CANADA_DETAIL_CHANGED_IDS
)
TOEFL_4_0_IDS = {"1009", "927", "1004", "809", "816", "817", "67", "63", "535"}
TOEFL_4_5_IDS = {"798", "824", "1301", "392", "818"}

DASHBOARD_OVERVIEW_TITLE = (
    "116-1（2027–2028）校級交換學校列表 6 校名額填入與 28 校詳細頁更新（2026-10-21 查核）"
)
PAGE_TITLE = "國立臺灣大學：" + DASHBOARD_OVERVIEW_TITLE
EXCHANGE_INFO_BULLET = (
    "2026-10-21 查核更新（116-1／2027–2028）：一覽表 6 校原空白名額正式填入（依「學年名額單位／最多人數」，非保證錄取人數："
    "巴黎高師 1／2、里爾天主教 3／6、巴黎第十 4／8、特魯瓦科技 3／6、科諾伯勒阿爾卑斯 1／2、拉脫維亞 1／2）；"
    "289 校詳頁均已讀到（28 頁變更、261 頁未變）：日本詳頁（橫濱國立日語／一般組改各第一學期 1 人、金澤一般組 1→0 不開放日語組保留、"
    "長崎日語 1→2 人且兩組僅第一學期、一橋新增社科院保留日語／一般組各第一學期 1 人並允許第二次交換、"
    "兵庫縣立改回大二以上修正昨日矛盾、立命館新增英語 RCE 組第一學期 1 人且兩組 GPA 3.00 各科至少 B 並新增 2027 春起 SKP 5 萬日圓支援費、"
    "廣島／名古屋外國語／日本大學修課規定、多校補新制 TOEFL 4.0／4.5）；法國詳頁（里爾 GPA 2.75→2.95、巴黎第十放寬年級與碩士法語 B2、"
    "特魯瓦學年名額 1→3 並新增國際學院、科諾伯勒新增 GPA 2.80）；澳洲 10 校詳頁調整（全數仍標示待接待校確認、列表名額仍空白，不能當正式開放）；"
    "西門菲沙更新 2027–28 附件連結並新增線上說明會（11/4 00:00–01:00、11/5 08:00–09:00）。附件未完整重核；報名 11/3 10:00～11/9 16:00 維持不變。"
)


def load_oct21_update(path: Path = SOURCE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        data.get("format_version") != 1
        or data.get("target_round") != "116-1"
        or data.get("target_academic_year") != "2027/2028"
        or data.get("formal_quota_changed") is not True
        or data.get("hyogo_freshman_contradiction_resolved") is not True
        or any(
            data.get(key) is not False
            for key in (
                "application_open_confirmed",
                "all_current_cycle_fields_verified",
                "unverified_forms_and_attachments_treated_as_no_update",
                "new_attachment_links_imply_content_verified",
                "japan_detail_changes_mean_list_quota_finalized",
                "australia_detail_changes_treated_as_formally_open",
            )
        )
    ):
        raise ValueError(
            "October 21 NTU update must preserve current-cycle, attachment, Japan list-quota, and Australia pending boundaries"
        )

    counts = data.get("counts", {})
    if counts != {
        "partners": 289,
        "detail_pages_checked": 289,
        "detail_pages_changed": 28,
        "detail_pages_unchanged": 261,
        "list_newly_published_quota_schools": 6,
        "positive_quota_schools_total": 34,
        "blank_quota_schools_total": 248,
        "zero_quota_schools_total": 7,
        "academic_year_units_total": 69.5,
        "maximum_persons_total": 130,
    }:
        raise ValueError("Unexpected October 21 NTU counts")

    toefl_meta = data.get("toefl_new_scale_additions", {})
    if (
        set(toefl_meta.get("score_4_0_portal_ids", [])) != TOEFL_4_0_IDS
        or set(toefl_meta.get("score_4_5_portal_ids", [])) != TOEFL_4_5_IDS
    ):
        raise ValueError("Unexpected October 21 TOEFL new-scale portal ID sets")

    if set(data.get("australia_pending_portal_ids", [])) != AUSTRALIA_PENDING_IDS:
        raise ValueError("Unexpected October 21 Australia pending portal IDs")

    if set(data.get("japan_detail_changed_portal_ids", [])) != JAPAN_DETAIL_CHANGED_IDS:
        raise ValueError("Unexpected October 21 Japan detail changed portal IDs")

    manifest = data.get("source_manifest", {})
    expected_sids = {"ntu_school_list_20261021"} | {
        f"ntu_sn_{pid}_20261021" for pid in DETAIL_CHANGED_IDS
    }
    if set(manifest) != expected_sids:
        raise ValueError("Unexpected October 21 NTU source manifest")

    for sid, src in manifest.items():
        target = (ROOT / src["local_file"]).resolve()
        if (
            not target.is_relative_to((ROOT / "sources/ntu/2026-10-21-official").resolve())
            or src.get("source_id") != sid
            or src.get("http_status") != 200
            or not src.get("checked_at")
            or not str(src.get("url", "")).startswith("https://")
        ):
            raise ValueError(f"Invalid October 21 source archive entry: {sid}")
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != src["sha256"]:
            raise ValueError(f"October 21 source hash mismatch for {sid}")

    quotas = {item["portal_id"]: item for item in data.get("newly_published_list_quotas", [])}
    if set(quotas) != QUOTA_PUBLISHED_IDS or len(quotas) != 6:
        raise ValueError("Unexpected October 21 newly published quota school set")
    if any(item.get("not_guaranteed_admission") is not True for item in quotas.values()):
        raise ValueError("October 21 newly published quotas must mark not_guaranteed_admission=True")

    details = {item["portal_id"]: item for item in data.get("changed_detail_pages", [])}
    if set(details) != DETAIL_CHANGED_IDS or len(details) != 28:
        raise ValueError("Unexpected October 21 changed detail page set")

    # Spot-check key textual facts across the 28 archived detail pages
    if "限定交換第一學期人數 1 人" not in details["817"]["sections"].get("名額", ""):
        raise ValueError("Yokohama National (sn/817) detail verification failed")
    if "一般組本次甄選不開放申請" not in details["824"]["sections"].get("名額", ""):
        raise ValueError("Kanazawa (sn/824) detail verification failed")
    if "限定交換第一學期人數 2 人" not in details["798"]["sections"].get("名額", ""):
        raise ValueError("Nagasaki (sn/798) detail verification failed")
    if (
        "依照合約，此名額保留予社會科學院學生" not in details["1009"]["sections"].get("名額", "")
        or details["1009"]["second_exchange_marker_present"] is not True
    ):
        raise ValueError("Hitotsubashi (sn/1009) detail verification failed")
    if (
        "本校大二學生" not in details["978"]["sections"].get("申請資格", "")
        or "本校大一/大二學生" in details["978"]["sections"].get("申請資格", "")
    ):
        raise ValueError("Hyogo (sn/978) sophomore resolution verification failed")
    if (
        "Regular Courses in English（RCE）" not in details["809"]["sections"].get("申請資格", "")
        or "GPA 達3.00分以上" not in details["809"]["sections"].get("申請資格", "")
        or "50,000" not in details["809"]["sections"].get("注意事項", "")
    ):
        raise ValueError("Ritsumeikan (sn/809) detail verification failed")
    if "GPA 達2.95分以上" not in details["392"]["sections"].get("申請資格", ""):
        raise ValueError("Lille Catho (sn/392) detail verification failed")
    if "B2(中高級)" not in details["601"]["sections"].get("申請資格", ""):
        raise ValueError("Paris Nanterre (sn/601) detail verification failed")
    if (
        "全學年3名" not in details["67"]["sections"].get("名額", "")
        or "國際學院" not in details["67"]["sections"].get("申請資格", "")
    ):
        raise ValueError("UTT Troyes (sn/67) detail verification failed")
    if "GPA 達2.80分以上" not in details["63"]["sections"].get("申請資格", ""):
        raise ValueError("Grenoble Alpes (sn/63) detail verification failed")

    # Verify all 10 Australian schools still carry the pending confirmation warning and blank list quota
    for aus_id in AUSTRALIA_PENDING_IDS:
        aus_entry = details[aus_id]
        if (
            aus_entry["pending_warning_present"] is not True
            or aus_entry["list_quota_after"] != ""
            or "尚待交換學校確認" not in aus_entry["sections"].get("名額", "")
        ):
            raise ValueError(f"Australian school sn/{aus_id} must remain pending host confirmation")

    if "GPA 達3.30分以上" not in details["313"]["sections"].get("申請資格", ""):
        raise ValueError("Sydney (sn/313) GPA 3.30 verification failed")
    if "GPA 達3.30分以上" not in details["1109"]["sections"].get("申請資格", ""):
        raise ValueError("Monash (sn/1109) GPA 3.30 verification failed")
    if "歷年不得有不及格／不通過科目" not in details["1307"]["sections"].get("申請資格", ""):
        raise ValueError("UTS (sn/1307) no-failing-grade verification failed")
    if "限定交換第一學期人數 2 人" not in details["93"]["sections"].get("名額", ""):
        raise ValueError("ANU (sn/93) semester 1 headcount 2 verification failed")

    sfu_other = details["5"]["sections"].get("Exchange to SFU Info Session", "")
    if "November 3, 2026" not in sfu_other or "November 4, 2026" not in sfu_other:
        raise ValueError("SFU (sn/5) online info session verification failed")

    return data


def apply_oct21_partner_view(
    partners: list[PartnerUniversity],
    path: Path = SOURCE,
) -> list[PartnerUniversity]:
    """Return a copy of the 289 NTU partners with Oct 20 + Oct 21 list quotas and 28 detail updates applied."""
    base_partners = apply_oct20_partner_view(partners)
    data = load_oct21_update(path)
    quotas = {item["portal_id"]: item for item in data["newly_published_list_quotas"]}
    details = {item["portal_id"]: item for item in data["changed_detail_pages"]}

    out: list[PartnerUniversity] = []
    for p in base_partners:
        pid = p.source_url.rsplit("/", 1)[-1]
        if pid not in quotas and pid not in details:
            out.append(p)
            continue

        patch: dict = {}
        evidence = dict(p.field_evidence)
        ref_data = dict(p.reference_data)

        if q := quotas.get(pid):
            note = (
                f"臺大116-1／2027–28於2026-10-21填入列表名額：{q['quota_display']}。"
                "名額為學年名額單位，一學期計0.5；最多人數非保證錄取人數；選填系統開放及其他條件仍須確認。"
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
                quota_published_at_20261021=data["checked_at"],
                not_guaranteed_admission="true",
            )

        if d := details.get(pid):
            secs = d["sections"]
            elig_text = secs.get("申請資格", "")
            if d["second_exchange_marker_present"] and "第二次出國交換" not in elig_text:
                elig_text = "此校開放予第二次出國交換之同學選填。\n" + elig_text
            if pid in AUSTRALIA_PENDING_IDS:
                elig_text += (
                    "\n【待確認提醒（2026-10-21）】詳細頁仍標示「上述申請資格及名額尚待交換學校確認」，"
                    "且交換列表名額欄仍空白，不能當成正式開放。"
                )
            elif pid in JAPAN_DETAIL_CHANGED_IDS:
                elig_text += (
                    "\n【名額邊界提醒（2026-10-21）】日本合作校詳細頁異動不等同交換學校一覽表名額已定案（列表名額欄仍空白）。"
                )
            elif pid == "5":
                elig_text += (
                    "\n【說明會與附件邊界（2026-10-21）】已更新 2027–28 附件連結並新增線上說明會"
                    "（台灣時間 11/4 00:00–01:00、11/5 08:00–09:00）；新附件連結不代表內文已驗證，且該頁仍標示待接待校確認。"
                )
            patch["eligibility"] = elig_text
            if "名額" in secs:
                ref_data["portal_detail_quota_reference_20261021"] = secs["名額"]
            ref_data["portal_reference_checked_20261021"] = data["checked_at"]
            ref_data["second_exchange_marker_20261021"] = (
                "present" if d["second_exchange_marker_present"] else "not_stated"
            )
            if pid == "978":
                ref_data["hyogo_freshman_contradiction_resolved_20261021"] = data["hyogo_resolution_note"]
            if pid in AUSTRALIA_PENDING_IDS:
                ref_data["australia_pending_host_confirmation_20261021"] = "true"
            if pid in JAPAN_DETAIL_CHANGED_IDS:
                ref_data["japan_list_quota_finalized_20261021"] = "false"
            if pid == "5":
                ref_data["sfu_online_info_sessions_taipei_time_20261021"] = (
                    "2026-11-04 00:00-01:00; 2026-11-05 08:00-09:00"
                )
                ref_data["new_attachment_links_content_verified_20261021"] = "false"

            evidence["eligibility"] = ExchangeFieldEvidence(
                source_url=d["source_url"],
                checked_at=data["checked_at"],
                status="reference_only",
                note=(
                    data["hyogo_resolution_note"]
                    if pid == "978"
                    else "2026-10-21詳細頁調整仍標示尚待交換學校確認、列表名額仍空白，不能當成正式開放。"
                    if pid in AUSTRALIA_PENDING_IDS
                    else "2026-10-21詳細頁更新；日本詳頁異動不等同列表名額已定案。"
                    if pid in JAPAN_DETAIL_CHANGED_IDS
                    else "2026-10-21詳細頁更新；仍須依列表名額與臺大校級簡章共同資格核對。"
                ),
            )

        patch["field_evidence"] = evidence
        patch["reference_data"] = ref_data
        out.append(with_ntu_partner_summary(p.model_copy(update=patch)))
    return out


def apply_oct21_updates(bundle: Path, path: Path = SOURCE) -> dict:
    data = load_oct21_update(path)
    card_details = [
        "116-1／2027–28 一覽表 6 校原空白名額正式填入（依「學年名額單位／最多人數」，不是保證錄取人數）：巴黎高等師範學院（sn/1301：1／2）、里爾天主教大學（sn/392：3／6）、巴黎第十大學（sn/601：4／8）、特魯瓦科技大學（sn/67：3／6）、科諾伯勒阿爾卑斯大學（sn/63：1／2）、拉脫維亞大學（sn/535：1／2）。",
        "日本詳頁更新（列表名額仍空白，不等同列表名額已定案）：橫濱國立（sn/817）日語／一般組從不開放改為各第一學期 1 人；金澤（sn/824）一般組 1→0 本次不開放、日語組保留；長崎（sn/798）日語組 1→2 人，兩組均縮為僅第一學期；一橋（sn/1009）新增社科院保留日語／一般組各第一學期 1 人並允許第二次交換；兵庫縣立（sn/978）改回大二以上，修正昨天的大一／大二矛盾；立命館（sn/809）新增英語 RCE 組第一學期 1 人，兩組要求 GPA 3.00 且各科至少 B，並新增 2027 春起 SKP 學生須繳 5 萬日圓支援費；廣島（sn/927）明列每組最多 1 人、每週至少 10 小時及每學期至少 7 門課；名古屋外國語（sn/1004）新增每堂 90 分鐘、建議 10–12 門課；日本大學（sn/955）要求選相同學位層級及領域。",
        "法國詳頁更新：里爾天主教（sn/392）GPA 2.75→2.95；巴黎第十（sn/601）放寬年級、移除該頁 GPA 3.00 條款（惟臺大共同資格仍適用）、研究生法語提高至 B2；特魯瓦科技（sn/67）學年名額 1→3 並新增國際學院適用；科諾伯勒阿爾卑斯（sn/63）新增 GPA 2.80。",
        "多校補新制 TOEFL iBT：一橋（1009）、廣島（927）、名古屋外國語（1004）、立命館（809）、關西學院（816）、橫濱國立（817）、特魯瓦（67）、科諾伯勒（63）、拉脫維亞（535）為 4.0；長崎（798）、金澤一般組（824，仍不開放）、巴黎高師（1301）、里爾（392）、雷恩第一（818）為 4.5。舊制及其他替代資格仍須逐組確認，Home Edition 接受與否各校不同。",
        "澳洲 10 校詳頁調整（全部仍標示待接待校確認、列表名額仍空白，不能當正式開放）：雪梨（sn/313）／蒙納許（sn/1109）GPA 3.20→3.30；UTS（sn/1307）新增不得有不及格科目；阿德雷德（sn/206）限大二／大三；Deakin（sn/95）排除博士並分列大學部／研究所語言要求；Macquarie（sn/94）放寬年級；ANU（sn/93）第一學期 1→2 人；昆士蘭（sn/210）、Deakin（sn/95）、UNSW（sn/96）、墨爾本（sn/92）等移除舊年度不開放敘述，改列限定學期人數，仍待確認。",
        "加拿大與查核邊界：西門菲沙（sn/5）更新 2027–28 附件連結並新增線上說明會（台灣時間 11/4 00:00–01:00、11/5 08:00–09:00）。本次 289 詳頁均已讀到，但附件未完整重核，新附件連結不代表內文已驗證；報名期間 11/3 10:00～11/9 16:00 維持不變。",
    ]
    detail_urls = [
        f"https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/{pid}"
        for pid in [
            "1301", "392", "601", "67", "63", "535", "818",
            "817", "824", "798", "1009", "978", "809", "816", "927", "1004", "955",
            "313", "1109", "1307", "206", "95", "94", "93", "210", "96", "92", "5",
        ]
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
                    "title": "臺大交換學校一覽表與 28 校詳細頁（2026-10-21 查核）",
                    "source_url": LIST_URL,
                    "category": "partner_school",
                    "summary": "6 校列表名額填入、28 校詳細頁更新、261 校詳細頁未變；澳洲 10 校仍待確認不能當正式開放，日本詳頁異動不等同列表名額定案。",
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
            if line != EXCHANGE_INFO_BULLET and "2026-10-21 查核更新（116-1／2027–2028）" not in line
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
            published_at="2026-10-21T00:00:00Z",
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
        "list_sha256": data["source_manifest"]["ntu_school_list_20261021"]["sha256"],
        "formal_quota_changed": True,
        "application_open_confirmed": False,
        "new_attachment_links_imply_content_verified": False,
        "japan_detail_changes_mean_list_quota_finalized": False,
        "australia_detail_changes_treated_as_formally_open": False,
        "hyogo_freshman_contradiction_resolved": True,
        "hyogo_resolution_note": data["hyogo_resolution_note"],
        "list_newly_published_quota_schools": 6,
        "newly_published_quota_portal_ids": ["1301", "392", "601", "67", "63", "535"],
        "partner_detail_pages_checked": 289,
        "partner_detail_pages_changed": 28,
        "partner_detail_pages_unchanged": 261,
        "changed_detail_portal_ids": [item["portal_id"] for item in data["changed_detail_pages"]],
        "toefl_new_scale_additions": data["toefl_new_scale_additions"],
        "australia_pending_portal_ids": data["australia_pending_portal_ids"],
        "japan_detail_changed_portal_ids": data["japan_detail_changed_portal_ids"],
        "newly_published_list_quotas": data["newly_published_list_quotas"],
    }
    for filename in ("catalog-completeness.json", "import_provenance.json"):
        target_file = bundle / filename
        if target_file.exists():
            payload = json.loads(target_file.read_text(encoding="utf-8"))
            payload["source_update_20261021"] = meta
            target_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )

    for item in bundle.iterdir():
        if item.is_file():
            raw_bytes = item.read_bytes()
            if b"\r\n" in raw_bytes:
                item.write_bytes(raw_bytes.replace(b"\r\n", b"\n"))

    return {
        "list_newly_published_quota_schools": 6,
        "detail_pages_changed": 28,
        "detail_pages_unchanged": 261,
        "australia_detail_changes_treated_as_formally_open": False,
        "japan_detail_changes_mean_list_quota_finalized": False,
    }
