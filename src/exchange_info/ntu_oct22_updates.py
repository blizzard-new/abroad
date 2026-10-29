"""Apply the reviewed October 22, 2026 NTU OIA school.list and partner detail-page updates.

Covers the 2026-10-22 full comparison of `https://oia.ntu.edu.tw/outgoing/school.list`
and all 289 partner detail pages (`sn/...`) for the 116-1 (2027/2028) selection cycle:
1. 5 schools with newly published formal selection quotas on `school.list` (bringing positive
   quota schools from 34 -> 39, blank from 248 -> 243, zero unchanged at 7; total academic
   year units 76.5, maximum persons 144):
   - sn/387 馬薩里克大學 (Masaryk University): blank -> 1 名 / 最多 2 名 (contract quota 2 unchanged);
     detail page also adds new-scale TOEFL iBT 4.0.
   - sn/61 哥本哈根大學 (University of Copenhagen): blank -> 3 名 / 最多 6 名; old TOEFL 80 -> 83,
     IELTS 6.0 -> 6.5, adds new-scale TOEFL iBT 4.5.
   - sn/921 查理士大學／查理大學 (Charles University): blank -> 1 名 / 最多 2 名; graduate eligibility
     changed from 碩一／二 -> 碩一以上, adds language test options and dormitory fee/deposit/early
     move-out deduction reminders.
   - sn/1042 華沙大學 (University of Warsaw): blank -> 1 名 / 最多 2 名; removes second-time
     exchange eligibility (`第二次出國交換`) and adds new-scale TOEFL iBT 4.0.
   - sn/1206 華沙理工大學 (Warsaw University of Technology): blank -> 1 名 / 最多 2 名; opens to
     second-time exchange (`此校開放予第二次出國交換之同學選填`), excludes PhD students (`不含博士生`),
     and adds new-scale TOEFL iBT 4.0. (Distinct from "第二輪志願".)
2. Confirmed detail-page updates on already-published or Japan/Europe pages:
   - sn/968 薩拉曼卡大學 (University of Salamanca): adds GPA 3.30; monthly living cost EUR 850 ->
     EUR 800–1,000/month.
   - Japan 38 schools (`JAPAN_TRANSCRIPT_REMINDER_IDS`, representative page sn/978 兵庫縣立大學):
     adds reminder that transcripts are typically issued ~4 weeks after the next semester starts
     following the exchange, which may affect credit transfer / graduation timing.
   - sn/38 岡山大學 (Okayama University): adds new-scale TOEFL iBT 4.0; EPOK study period updated
     to 2027/4–2028/2.
   - sn/1009 一橋大學 (Hitotsubashi University): non-reserved general group adds exclusion of
     College of Social Sciences (`社會科學院`).
3. Detail-page updates where `school.list` remains blank or 0 (especially North America pages
   still marked pending host confirmation — MUST NOT be treated as finalized quotas):
   - sn/1282 UT Austin: detail quota 2 -> 1, Computer Science changed from not guaranteed to not open.
   - sn/432 Temple University: GPA 3.20 -> 3.30.
   - sn/19 UIC: graduate eligibility 碩一以上 -> 僅碩一, adds 2nd preference round restriction;
     linked PDF remains 2026–27 (not relabeled as new year).
   - sn/420 Cornell University: adds 2nd preference round restriction and conditional
     cross-disciplinary course enrollment.
   - sn/863 UConn: GPA 3.20 -> 3.30, restricted to 大二/大三/大四, detail quota 0 -> 1 and adds
     2nd preference round restriction (does NOT represent formal reopening).
   - sn/13 NCSU: restricted to 大二/大三/碩一/碩二, excludes 生機所, detail quota 3 -> 2; linked PDF
     remains 2026–27.
   - sn/9 University of California (UC): detail quota 25 -> 20; old-scale TOEFL iBT 90 changed to
     NOT accept Home Edition while new-scale 5.0 still states Home Edition accepted (page internal
     contradiction noted as unresolved).
   - sn/599 Queen's University (Canada): still 0 quota; adds Smith School of Business course
     restriction and NTU College of Management exclusion.
   - sn/376 青山學院大學: changed to 1st semester only, 1 student.
   - sn/377 同志社大學: Japanese group 2 -> 1, General group 1 unchanged.
   - sn/616 康斯坦茨大學 (Konstanz): detail quota 2 -> 3.
   - sn/95 汀肯大學 (Deakin, AU/NZ representative): updates 2027 Fact Sheet link, housing, and
     semester notes.
4. Attachment coverage & correction:
   - Total linked documents across the 289 detail pages (including relative-URL forms and
     historical guidelines): 173 (95 succeeded, 78 incomplete/unreadable), superseding the prior
     150 / 94 / 56 count that omitted relative-URL links.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .models import (
    ExchangeFieldEvidence,
    ExchangeInfo,
    PartnerUniversity,
    ProcessedPage,
    StudentDashboard,
)
from .ntu_oct21_updates import apply_oct21_partner_view
from .ntu_partner_summary import with_ntu_partner_summary

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "sources/ntu/2026-10-22-official-update.json"
LIST_URL = "https://oia.ntu.edu.tw/outgoing/school.list"

QUOTA_PUBLISHED_IDS = {"387", "61", "921", "1042", "1206"}
DETAIL_CHANGED_IDS = {
    "387", "61", "968", "1042", "1206", "921",
    "978", "38", "1009", "376", "377",
    "1282", "432", "19", "420", "863", "13", "9", "599",
    "616", "95",
}
NORTH_AMERICA_PENDING_OR_ZERO_IDS = {"1282", "432", "19", "420", "863", "13", "9", "599"}
BLANK_LIST_DETAIL_CHANGED_IDS = {
    "978", "38", "1009", "376", "377",
    "1282", "432", "19", "420", "863", "13", "9",
    "616", "95",
}
JAPAN_TRANSCRIPT_REMINDER_IDS = {
    "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38",
    "103", "107", "108", "109", "376", "377", "394", "607", "798", "800", "809", "816", "817", "824",
    "927", "955", "978", "1004", "1009", "1187", "1198", "1293",
}

DASHBOARD_OVERVIEW_TITLE = (
    "116-1（2027–2028）校級交換列表 5 校名額填入、歐日北美澳紐詳頁更新與 173 份附件盤點修正（2026-10-22 查核）"
)
PAGE_TITLE = "國立臺灣大學：" + DASHBOARD_OVERVIEW_TITLE
EXCHANGE_INFO_BULLET = (
    "2026-10-22 查核更新（116-1／2027–2028）：正式列表與全部 289 校詳頁已比對；一覽表新增填入馬薩里克（sn/387：1／2，合約額 2 未變，補 TOEFL 4.0）、"
    "哥本哈根（sn/61：3／6，舊制 TOEFL 80→83、IELTS 6→6.5、補新制 TOEFL 4.5）、查理大學（sn/921：1／2，碩一／二→碩一以上，補語檢選項與宿舍訂金／搬離扣款提醒）、"
    "華沙大學（sn/1042：1／2，撤除第二次出國交換資格、補 TOEFL 4.0）、華沙理工（sn/1206：1／2，開放第二次出國交換但排除博士生、補 TOEFL 4.0，此與第二輪志願不同）；"
    "薩拉曼卡（sn/968）新增 GPA 3.30 及生活費 EUR 850→800–1,000／月；日本 38 校（代表頁 sn/978）新增成績單於交換後下一學期開學約 4 週後核發提醒；"
    "岡山（sn/38）補 TOEFL 4.0 且 EPOK 期間改為 2027/4–2028/2；一橋（sn/1009）非保留一般組補排除社科院；"
    "列表仍空白或 0 額之詳頁變更（北美頁仍標待接待校確認，不能當定案名額）：UT Austin（sn/1282：詳頁 2→1、資工改不開放）、Temple（sn/432：GPA 3.20→3.30）、"
    "UIC（sn/19：僅碩一、新增不開放第二輪志願，PDF 仍 2026–27）、Cornell（sn/420：新增第二輪限制與有條件跨領域選課）、"
    "UConn（sn/863：GPA 3.20→3.30、限大二至大四、詳頁 0→1 並加第二輪限制，不代表正式重開）、NCSU（sn/13：限大二／三與碩一／二、排除生機所、詳頁 3→2，PDF 仍 2026–27）、"
    "加州大學（sn/9：詳頁 25→20，舊制 TOEFL 90 列改不接受 Home Edition 但新制 5.0 列仍接受，頁內矛盾待釐清）、加拿大 Queen's（sn/599：仍 0 額，新增 Smith 商學課與臺大管院禁選限制）、"
    "青山（sn/376：改僅第一學期 1 人）、同志社（sn/377：日語組 2→1、一般組 1 不變）、Konstanz（sn/616：詳頁 2→3）及澳紐（Deakin sn/95 補 2027 Fact Sheet 等）；"
    "頁內連結文件含相對路徑表單與歷年簡章共 173 份（成功 95、未完成 78，取代前次漏計相對路徑之 150／94／56 統計）。"
)


def load_oct22_update(path: Path = SOURCE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        data.get("format_version") != 1
        or data.get("checked_date") != "2026-10-22"
        or data.get("target_round") != "116-1"
        or data.get("target_academic_year") != "2027/2028"
        or data.get("formal_quota_changed") is not True
        or any(
            data.get(key) is not False
            for key in (
                "application_open_confirmed",
                "all_current_cycle_fields_verified",
                "unverified_forms_and_attachments_treated_as_no_update",
                "blank_list_detail_quotas_treated_as_finalized",
                "uc_toefl_home_edition_contradiction_resolved",
            )
        )
    ):
        raise ValueError(
            "October 22 NTU update must preserve current-cycle, blank-list quota, attachment, and UC contradiction boundaries"
        )

    counts = data.get("counts", {})
    if counts != {
        "partners": 289,
        "detail_pages_checked": 289,
        "detail_pages_changed_key_sampled": 21,
        "japan_transcript_reminder_schools": 38,
        "list_newly_published_quota_schools": 5,
        "positive_quota_schools_total": 39,
        "blank_quota_schools_total": 243,
        "zero_quota_schools_total": 7,
        "academic_year_units_total": 76.5,
        "maximum_persons_total": 144,
    }:
        raise ValueError("Unexpected October 22 NTU counts")

    att = data.get("attachment_coverage", {})
    if (
        att.get("total_linked_documents") != 173
        or att.get("read_succeeded") != 95
        or att.get("incomplete_or_unreadable") != 78
        or att.get("previous_count_superseded", {}).get("total") != 150
        or att.get("previous_count_superseded", {}).get("succeeded") != 94
        or att.get("previous_count_superseded", {}).get("incomplete") != 56
        or att.get("new_or_replaced_fact_sheet_links_baseline_count") != 5
        or att.get("uic_and_ncsu_pdf_still_2026_2027") is not True
    ):
        raise ValueError("Unexpected October 22 NTU attachment coverage metadata")

    if (
        data.get("japan_transcript_reminder_count") != 38
        or set(data.get("japan_transcript_reminder_pids", [])) != JAPAN_TRANSCRIPT_REMINDER_IDS
    ):
        raise ValueError("Unexpected October 22 Japan 38-school transcript reminder set")

    manifest = data.get("source_manifest", {})
    expected_sids = {"ntu_school_list_20261022"} | {
        f"ntu_sn_{pid}_20261022" for pid in (QUOTA_PUBLISHED_IDS | DETAIL_CHANGED_IDS)
    }
    if set(manifest) != expected_sids:
        raise ValueError("Unexpected October 22 NTU source manifest")

    for sid, src in manifest.items():
        target = (ROOT / src["local_file"]).resolve()
        if (
            not target.is_relative_to((ROOT / "sources/ntu/2026-10-22-official").resolve())
            or src.get("source_id") != sid
            or src.get("http_status") != 200
            or not src.get("checked_at")
            or not str(src.get("url", "")).startswith("https://")
        ):
            raise ValueError(f"Invalid October 22 source archive entry: {sid}")
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != src["sha256"]:
            raise ValueError(f"October 22 source hash mismatch for {sid}")

    quotas = {item["portal_id"]: item for item in data.get("newly_published_list_quotas", [])}
    if set(quotas) != QUOTA_PUBLISHED_IDS or len(quotas) != 5:
        raise ValueError("Unexpected October 22 newly published quota school set")

    details = {item["portal_id"]: item for item in data.get("changed_detail_pages", [])}
    if set(details) != DETAIL_CHANGED_IDS or len(details) != 21:
        raise ValueError("Unexpected October 22 changed detail page set")

    # Spot-check key textual invariants from the 2026-10-22 audit
    if "TOEFL iBT 4.0" not in details["387"]["sections"].get("申請資格", "") or quotas["387"]["contract_quota"] != "2 名":
        raise ValueError("Masaryk (sn/387) verification failed")
    if (
        "TOEFL iBT 4.5" not in details["61"]["sections"].get("申請資格", "")
        or "TOEFL iBT 83" not in details["61"]["sections"].get("申請資格", "")
        or "IELTS 6.5" not in details["61"]["sections"].get("申請資格", "")
    ):
        raise ValueError("Copenhagen (sn/61) verification failed")
    if (
        "GPA 達3.30分以上" not in details["968"]["sections"].get("申請資格", "")
        or "€800 and €1000" not in details["968"]["sections"].get("實用資訊", "")
    ):
        raise ValueError("Salamanca (sn/968) verification failed")
    if (
        details["1042"]["second_exchange_marker_present"] is not False
        or "TOEFL iBT 4.0" not in details["1042"]["sections"].get("申請資格", "")
    ):
        raise ValueError("Warsaw University (sn/1042) verification failed")
    if (
        details["1206"]["second_exchange_marker_present"] is not True
        or "不含博士生" not in details["1206"]["sections"].get("申請資格", "")
        or "TOEFL iBT 4.0" not in details["1206"]["sections"].get("申請資格", "")
    ):
        raise ValueError("Warsaw University of Technology (sn/1206) verification failed")
    if (
        "碩一以上" not in details["921"]["sections"].get("申請資格", "")
        or "TOEFL iBT 4.0" not in details["921"]["sections"].get("申請資格", "")
    ):
        raise ValueError("Charles University (sn/921) verification failed")
    if "4週" not in details["978"]["sections"].get("日本區重要提醒", ""):
        raise ValueError("Hyogo (sn/978) 4-week transcript reminder verification failed")
    if (
        "TOEFL iBT 4.0" not in details["38"]["sections"].get("申請資格", "")
        or "2027 April" not in details["38"]["sections"].get("注意事項", "")
    ):
        raise ValueError("Okayama (sn/38) verification failed")
    if "社會科學院" not in details["1009"]["sections"].get("申請資格", ""):
        raise ValueError("Hitotsubashi (sn/1009) verification failed")
    if (
        details["1282"]["list_quota_after"] != ""
        or "全學年1名" not in details["1282"]["sections"].get("名額", "")
    ):
        raise ValueError("UT Austin (sn/1282) verification failed")
    if (
        details["9"]["list_quota_after"] != ""
        or "全學年20名" not in details["9"]["sections"].get("名額", "")
        or "TOEFL iBT 5.0 (接受 Home Edition)" not in details["9"]["sections"].get("申請資格", "")
        or "TOEFL iBT 90 (不接受 Home Edition)" not in details["9"]["sections"].get("申請資格", "")
    ):
        raise ValueError("UC (sn/9) Home Edition contradiction verification failed")
    if (
        details["599"]["list_quota_after"] != "0 名"
        or "不開放 Smith School of Business 課程" not in details["599"]["sections"].get("申請資格", "")
        or "管理學院" not in details["599"]["sections"].get("申請資格", "")
    ):
        raise ValueError("Queen's (sn/599) verification failed")

    return data


def apply_oct22_partner_view(
    partners: list[PartnerUniversity],
    path: Path = SOURCE,
) -> list[PartnerUniversity]:
    """Return a copy of the 289 NTU partners with the 2026-10-20, 2026-10-21, and 2026-10-22 updates applied."""
    base_partners = apply_oct21_partner_view(partners)
    data = load_oct22_update(path)
    quotas = {item["portal_id"]: item for item in data["newly_published_list_quotas"]}
    details = {item["portal_id"]: item for item in data["changed_detail_pages"]}
    out: list[PartnerUniversity] = []

    for p in base_partners:
        pid = p.source_url.rsplit("/", 1)[-1]
        if (
            pid not in quotas
            and pid not in details
            and pid not in JAPAN_TRANSCRIPT_REMINDER_IDS
        ):
            out.append(p)
            continue

        patch: dict = {}
        evidence = dict(p.field_evidence)
        ref_data = dict(p.reference_data)

        if q := quotas.get(pid):
            note = (
                f"臺大116-1／2027–28於2026-10-22公布列表名額：{q['quota_display']}。"
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
                quota_published_at_20261022=data["checked_at"],
                not_guaranteed_admission="true",
            )

        if d := details.get(pid):
            secs = d["sections"]
            elig_text = secs.get("申請資格", "")
            if d["second_exchange_marker_present"] and "第二次出國交換" not in elig_text:
                elig_text = "此校開放予第二次出國交換之同學選填。\n" + elig_text
            if d.get("second_round_restricted_present") and "不開放第二次志願選填" not in elig_text:
                elig_text += "\n【志願輪次限制】此名額不開放第二次志願選填（與「第二次出國交換」不同）。"
            if pid == "9":
                elig_text += f"\n【頁內矛盾待釐清（2026-10-22）】{data['uc_toefl_home_edition_contradiction_note']}"
            elif pid in NORTH_AMERICA_PENDING_OR_ZERO_IDS and pid != "599":
                elig_text += (
                    "\n【待確認提醒（2026-10-22）】北美詳細頁雖有調整，但正式總表名額欄仍空白且頁內標示待交換學校確認，"
                    "不能當成定案甄選名額。"
                )
            elif pid in BLANK_LIST_DETAIL_CHANGED_IDS:
                elig_text += (
                    "\n【名額邊界提醒（2026-10-22）】詳細頁異動不等同交換學校一覽表名額已定案（正式總表名額欄仍空白）。"
                )
            if pid in JAPAN_TRANSCRIPT_REMINDER_IDS:
                elig_text += f"\n【成績單核發提醒（2026-10-22）】{data['japan_transcript_reminder_note']}"

            patch["eligibility"] = elig_text
            if "名額" in secs:
                ref_data["portal_detail_quota_reference_20261022"] = secs["名額"]
            ref_data["portal_reference_checked_20261022"] = data["checked_at"]
            ref_data["second_exchange_marker_20261022"] = (
                "present" if d["second_exchange_marker_present"] else "not_stated"
            )
            if pid in BLANK_LIST_DETAIL_CHANGED_IDS:
                ref_data["list_quota_finalized_20261022"] = "false"
            if pid == "9":
                ref_data["uc_toefl_home_edition_contradiction_20261022"] = (
                    data["uc_toefl_home_edition_contradiction_note"]
                )
            if pid in ("19", "13"):
                ref_data["linked_pdf_academic_year_20261022"] = "2026/2027"

            evidence["eligibility"] = ExchangeFieldEvidence(
                source_url=d["source_url"],
                checked_at=data["checked_at"],
                status="conflict" if pid == "9" else "reference_only",
                note=(
                    data["uc_toefl_home_edition_contradiction_note"]
                    if pid == "9"
                    else "2026-10-22詳細頁調整仍標示尚待交換學校確認、正式總表名額仍空白，不能當成定案名額。"
                    if pid in BLANK_LIST_DETAIL_CHANGED_IDS
                    else "2026-10-22詳細頁更新；仍須依列表名額與臺大校級簡章共同資格核對。"
                ),
            )
        elif pid in JAPAN_TRANSCRIPT_REMINDER_IDS:
            elig_text = p.eligibility or ""
            if "成績單核發提醒（2026-10-22）" not in elig_text:
                elig_text = (
                    elig_text + f"\n【成績單核發提醒（2026-10-22）】{data['japan_transcript_reminder_note']}"
                ).strip()
            patch["eligibility"] = elig_text
            ref_data["japan_transcript_4week_reminder_20261022"] = "true"

        patch["field_evidence"] = evidence
        patch["reference_data"] = ref_data
        out.append(with_ntu_partner_summary(p.model_copy(update=patch)))
    return out


def apply_oct22_updates(bundle: Path, path: Path = SOURCE) -> dict:
    data = load_oct22_update(path)
    card_details = [
        "116-1／2027–28 正式總表（school.list）新增填入 5 校甄選名額（全表正數名額由 34→39 校、空白 248→243 校、0 名 7 校；總學年名額單位 76.5、最多人數 144）：馬薩里克大學（sn/387：1／2，合約額 2 未變，另補新制 TOEFL iBT 4.0）、哥本哈根大學（sn/61：3／6，舊制 TOEFL 80→83、IELTS 6→6.5，新增新制 TOEFL iBT 4.5）、查理大學（sn/921：1／2，碩一／二→碩一以上，補語檢選項及宿舍費、訂金與提前搬離扣款提醒）、華沙大學（sn/1042：1／2，撤除「第二次出國交換」資格，補 TOEFL iBT 4.0）、華沙理工大學（sn/1206：1／2，開放第二次出國交換但排除博士生，補 TOEFL iBT 4.0；此與「第二輪志願」不同）。",
        "已公布名額與日本詳頁更新：薩拉曼卡大學（sn/968）新增 GPA 3.30，生活費由 EUR 850 改為 EUR 800–1,000／月；日本 38 校（代表頁 sn/978 兵庫縣立大學）新增提醒「成績單通常於交換後下一學期開學約 4 週後核發，可能影響抵免／畢業安排」；岡山大學（sn/38）補 TOEFL iBT 4.0，EPOK 期間改為 2027/4–2028/2；一橋大學（sn/1009）非保留一般組補排除社科院。",
        "正式總表仍空白或 0 名之北美詳頁變更（北美頁仍標待接待校確認，不能當定案名額）：UT Austin（sn/1282）詳頁 2→1、資工從不保證改不開放；Temple（sn/432）GPA 3.20→3.30；UIC（sn/19）碩一以上→僅碩一、新增不開放第二輪志願（連結 PDF 仍為 2026–27）；Cornell（sn/420）新增第二輪限制及有條件跨領域選課；UConn（sn/863）GPA 3.20→3.30、限大二／三／四、詳頁 0→1 並加第二輪限制（不代表正式重開）；NCSU（sn/13）限大二／三與碩一／二、排除生機所、詳頁 3→2（連結 PDF 仍為 2026–27）；加州大學（sn/9）詳頁 25→20，舊制 TOEFL 90 列改不接受 Home Edition 但新制 5.0 列仍接受，頁內矛盾待釐清；加拿大 Queen's（sn/599）仍 0 額，新增 Smith 商學課及臺大管理院禁選限制。",
        "日本、德國與澳紐其他詳頁更新（列表名額仍空白）：青山學院大學（sn/376）改僅第一學期 1 人；同志社大學（sn/377）日語組 2→1、一般組 1 不變；康斯坦茨大學（sn/616）詳頁 2→3；澳紐（代表頁 sn/95 汀肯大學）補 2027 Fact Sheet、住宿及學期說明。",
        "附件盤點修正與報名時程：289 詳頁讀取完成不等於所有附件均已核；頁內連結文件含相對路徑表單與歷年簡章共 173 份（成功 95、未完成 78），取代前次漏計相對路徑之 150／94／56 統計；5 個新增／替換 Fact Sheet 連結因缺前次同檔僅建基準。報名維持 11/3 10:00–11/9 16:00（既有資訊）。",
    ]
    detail_urls = [
        f"https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/{pid}"
        for pid in [
            "387", "61", "968", "1042", "1206", "921",
            "978", "38", "1009", "376", "377",
            "1282", "432", "19", "420", "863", "13", "9", "599",
            "616", "95",
        ]
    ]

    # 1. student_dashboard.json
    sd_path = bundle / "student_dashboard.json"
    if sd_path.exists():
        sd = json.loads(sd_path.read_text(encoding="utf-8"))
        oct27_title = "116-1（2027–2028）OIA 正式列表與詳頁讀取異常保留基準說明（2026-10-27 查核）"
        overview = [
            item
            for item in sd.get("program_overview", [])
            if item.get("title") not in {DASHBOARD_OVERVIEW_TITLE, oct27_title}
        ]
        overview.append(
            {
                "title": DASHBOARD_OVERVIEW_TITLE,
                "details": card_details,
                "source": {
                    "title": "臺大交換學校一覽表與 289 校詳細頁比對（2026-10-22 查核）",
                    "source_url": LIST_URL,
                    "category": "partner_school",
                    "summary": "列表新增 5 校名額（正數名額共 39 校）、日本 38 校新增成績單提醒、北美與歐日澳紐詳頁更新；列表空白頁不當定案名額，頁內連結文件修正為 173 份（成功 95、未完成 78）。",
                },
            }
        )
        overview.append(
            {
                "title": oct27_title,
                "details": [
                    "OIA 首頁可讀，但正式中英交換列表（https://oia.ntu.edu.tw/outgoing/school.list）及 9 個舊候選詳頁於 2026/10/27 查核時仍回傳錯誤，不等於名額恢復；正式內容保留 2026/10/22 最後成功基準。",
                    "海外教育專區（https://studyabroad.ntu.edu.tw/exchange-student/how-to-apply/）三核心頁與既有版本相同，線上報名 2026/11/03 10:00–11/09 16:00、成績 12/02 公布、一階志願 12/07 截止為既有資訊（首頁哥廷根大學交換說明會及頁尾 2022 舊版系統維護彈窗 system_maintenance_20221030 已標示）。",
                    "既有追蹤之 173 份文件中，今日 150 份有效且均與各自最後成功版本相同、23 份缺口；此統計並非今日完整 OIA 附件清單，9 個候選差異仍未核實。",
                ],
                "source": {
                    "title": "臺大 OIA 交換列表與海外教育申請核心頁（2026-10-27 查核）",
                    "source_url": LIST_URL,
                    "category": "partner_school",
                    "summary": "正式列表及 9 個候選詳頁仍回傳錯誤，保留 10/22 成功基準（不等於名額恢復）；173 追蹤檔中 150 有效同舊、23 缺口。",
                },
            }
        )
        oct26_note = (
            "2026/10/26 巡查更新：116-1 甄選時程頁（https://studyabroad.ntu.edu.tw/exchange-student/how-to-apply/sem1-20272028ay-selection-timeline/）"
            "所列線上報名（115/11/3 10:00 至 11/9 16:00）、成績公布（12/2）與第一階段志願選填截止（12/7）與平台 116-1 校級甄選資料一致無衝突；"
            "首頁新見「德國哥廷根大學交換學生計畫說明會」開放報名（https://forms.gle/aDBxaTLB2yjZt5AK8，頁面未標活動日期）；"
            "另首頁頁尾「10/30（日）18:00 至 10/31（一）10:00 系統維護通知」（DOM id 為 #system_maintenance_20221030）經核實為 2022 年舊版遺留彈窗（2026/10/30 為週五），惟如遇該時段國際處維護仍建議避開。"
        )
        if overview and oct26_note not in overview[0].get("details", []):
            overview[0]["details"].append(oct26_note)
        sd["program_overview"] = overview
        oct26_sources = [
            {
                "title": "臺大 116 學年度第 1 學期出國交換學生甄選時程表",
                "source_url": "https://studyabroad.ntu.edu.tw/exchange-student/how-to-apply/sem1-20272028ay-selection-timeline/",
                "category": "deadline",
                "summary": "線上報名 115/11/3 10:00 至 11/9 16:00、成績 12/2 公布、第一階段志願選填截止 12/7；首頁另公告德國哥廷根大學交換說明會報名（https://forms.gle/aDBxaTLB2yjZt5AK8）。",
            },
            {
                "title": "德國哥廷根大學交換學生計畫說明會報名表單（臺大國際處首頁公告，頁面未列日期）",
                "source_url": "https://forms.gle/aDBxaTLB2yjZt5AK8",
                "category": "exchange_application",
                "summary": "臺大海外教育專區首頁最新消息開放德國哥廷根大學（University of Göttingen）交換學生計畫說明會報名。",
            },
        ]
        existing_sd_sources = sd.get("sources", [])
        existing_sd_urls = {s.get("source_url") for s in existing_sd_sources}
        for s_item in oct26_sources:
            if s_item["source_url"] not in existing_sd_urls:
                existing_sd_sources.append(s_item)
        sd["sources"] = existing_sd_sources
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
            if line != EXCHANGE_INFO_BULLET and "2026-10-22 查核更新（116-1／2027–2028）" not in line
        ]
        elig_lines.append(EXCHANGE_INFO_BULLET)
        ei["eligibility"] = elig_lines
        oct26_period_line = (
            "2026/10/26 巡查更新：116-1 甄選時程頁（https://studyabroad.ntu.edu.tw/exchange-student/how-to-apply/sem1-20272028ay-selection-timeline/）"
            "確認線上報名 115/11/3 10:00–11/9 16:00、成績 12/2 公布、第一階段志願選填截止 12/7；"
            "首頁新增「德國哥廷根大學交換學生計畫說明會」報名（https://forms.gle/aDBxaTLB2yjZt5AK8，頁面未寫日期）；"
            "首頁頁尾「10/30 18:00 至 10/31 10:00 系統維護公告」經核實為 #system_maintenance_20221030（2022 年舊版遺留彈窗，頁面未寫年份）。"
        )
        app_periods = [p for p in ei.get("application_period", []) if "德國哥廷根大學交換學生計畫說明會" not in p]
        app_periods.append(oct26_period_line)
        ei["application_period"] = app_periods
        src_urls = list(ei.get("source_urls", []))
        for u in [
            LIST_URL,
            *detail_urls,
            "https://studyabroad.ntu.edu.tw/exchange-student/how-to-apply/sem1-20272028ay-selection-timeline/",
            "https://forms.gle/aDBxaTLB2yjZt5AK8",
        ]:
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
        oct26_page_title = "國立臺灣大學：116-1 甄選時程頁核對、德國哥廷根大學交換說明會與系統維護公告年份查核（2026-10-26）"
        kept_pages = [p for p in existing_pages if p.title not in {PAGE_TITLE, oct26_page_title}]
        if kept_pages and kept_pages[0].title == "國立臺灣大學：116-1校級出國交換":
            p0_lines = [l for l in kept_pages[0].text.splitlines() if "德國哥廷根大學交換學生計畫說明會" not in l]
            p0_lines.append(oct26_note)
            p0_body = "\n".join(p0_lines)
            kept_pages[0] = kept_pages[0].model_copy(
                update={
                    "text": p0_body,
                    "summary": p0_body,
                    "content_hash": hashlib.sha256(p0_body.encode("utf-8")).hexdigest(),
                }
            )
        body_text = "\n".join(card_details) + "\n詳細來源：" + "；".join(detail_urls)
        new_page = ProcessedPage(
            title=PAGE_TITLE,
            source_url=LIST_URL,
            published_at="2026-10-22T00:00:00Z",
            text=body_text,
            summary=body_text,
            category="partner_school",
            attachments=[],
            crawled_at=data["checked_at"],
            content_hash=hashlib.sha256(body_text.encode("utf-8")).hexdigest(),
        )
        kept_pages.append(new_page)
        oct26_body = (
            "116-1 甄選時程頁（https://studyabroad.ntu.edu.tw/exchange-student/how-to-apply/sem1-20272028ay-selection-timeline/）"
            "所列線上報名 115/11/3 10:00 到 11/9 16:00、成績 12/2 公布、第一階段志願選填截止 12/7 與平台 116-1 校級甄選資料一致無衝突。\n"
            "首頁新公告「德國哥廷根大學交換學生計畫說明會」開放報名（https://forms.gle/aDBxaTLB2yjZt5AK8，頁面未寫日期）。\n"
            "首頁頁尾「10/30（日）18:00 到 10/31（一）10:00 系統維護公告」未寫年份，經查 HTML 元素為 #system_maintenance_20221030，屬 2022 年舊版遺留彈窗（2026/10/30 為週五）。"
        )
        kept_pages.append(
            ProcessedPage(
                title=oct26_page_title,
                source_url="https://studyabroad.ntu.edu.tw/exchange-student/how-to-apply/sem1-20272028ay-selection-timeline/",
                published_at="2026-10-26T00:00:00Z",
                text=oct26_body,
                summary=oct26_body,
                category="exchange_application",
                attachments=[],
                crawled_at="2026-10-26T00:00:00Z",
                content_hash=hashlib.sha256(oct26_body.encode("utf-8")).hexdigest(),
            )
        )
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
        "list_sha256": data["source_manifest"]["ntu_school_list_20261022"]["sha256"],
        "formal_quota_changed": True,
        "application_open_confirmed": False,
        "blank_list_detail_quotas_treated_as_finalized": False,
        "uc_toefl_home_edition_contradiction_resolved": False,
        "uc_toefl_home_edition_contradiction_note": data["uc_toefl_home_edition_contradiction_note"],
        "japan_transcript_reminder_count": 38,
        "japan_transcript_reminder_pids": data["japan_transcript_reminder_pids"],
        "attachment_coverage": data["attachment_coverage"],
        "list_newly_published_quota_schools": 5,
        "newly_published_quota_portal_ids": ["387", "61", "921", "1042", "1206"],
        "partner_detail_pages_checked": 289,
        "changed_detail_portal_ids": [item["portal_id"] for item in data["changed_detail_pages"]],
        "newly_published_list_quotas": data["newly_published_list_quotas"],
    }
    for filename in ("catalog-completeness.json", "import_provenance.json"):
        target_file = bundle / filename
        if target_file.exists():
            payload = json.loads(target_file.read_text(encoding="utf-8"))
            payload["source_update_20261022"] = meta
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
        "list_newly_published_quota_schools": 5,
        "detail_pages_changed_key_sampled": 21,
        "japan_transcript_reminder_schools": 38,
        "blank_list_detail_quotas_treated_as_finalized": False,
        "uc_toefl_home_edition_contradiction_resolved": False,
    }
