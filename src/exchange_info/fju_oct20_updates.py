"""Verified 2026-10-20 morning FJU 116-1 (2027 Fall) application announcement updates.

Applies the official 2026-10-20 Fu Jen Catholic University (天主教輔仁大學) 116-1 / 2027 Fall
outbound exchange application announcement (`newsID=1062`, https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14)
and its 4 official PDF attachments:
- `file=1344` (`sources/fju/116_1_info_slides.pdf`): 39-page 116-1 briefing slides
- `file=1345` (`sources/fju/116_1_application_form.pdf`): 2-page 116-1 application form
- `file=1346` (`sources/fju/116_1_non_japanese_partners.pdf`): 4-page non-Japanese group partner table
- `file=1347` (`sources/fju/116_1_japanese_partners.pdf`): 5-page Japanese group partner table

Key verified rules & epistemic boundaries:
1. Title vs. Body Window: Although the announcement title states "即日起開始收件至12月24日16:30止!",
   the body text explicitly specifies that the online system (`http://outgoing.oie.fju.edu.tw/`,
   campus network IP restricted `有鎖校外IP連線`) and paper submission window is
   **2026/11/01 to 2026/12/24 16:30**.
2. November Rolling Partner/Quota Updates: Partner schools and quotas will continue to be updated
   throughout November (`名額及開放學校將於11月陸續由姊妹校提供`), and the attached tables (`file=1346`,
   `file=1347`) label the quota column `通常名額 (參考用)` — cannot be treated as final
   (`final_partner_list_and_quotas_confirmed = False`). Individual school Fact Sheets require
   Microsoft M365 login (`學號@m365.fju.edu.tw`) and were not audited.
3. Paper vs. Electronic Documents:
   - `A.紙本文件`: Only the double-sided typed application form (`赴姐妹校交換生申請表`, `file=1345`)
     with parent signature + seal and department/college/double-major/minor stamps, submitted to
     耕莘樓 A113 室 by 2026/12/24 16:30.
   - `B.電子文件` (each PDF <= 20MB, uploaded to `http://outgoing.oie.fju.edu.tw/`):
     1. 書審資料 PDF: Chinese resume (max 2 pages), Chinese study plan (Chinese only, no English version required, >= 500 characters, max 2 pages), other achievements / low-income proof.
     2. Official Chinese transcript PDF (including class rank through 114-2).
     3. Language proficiency certificate PDF (English test taken on/after 2024/12/24: TOEFL iBT 79 / new-scale 4.0, IELTS Academic 6.5, TOEIC 750; JLPT web score accepted initially with certificate due by 2027/01/31 and preference ranking notified by email in mid-January).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import (
    ExchangeInfo,
    PartnerUniversity,
    ProcessedPage,
    StudentDashboard,
    UniversityApplicationWorkflow,
)

ROOT = Path(__file__).resolve().parents[2]
FJU_BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "fju"
UPDATE_JSON_PATH = ROOT / "sources" / "fju" / "2026-10-20-official-update.json"

NEWS_1062_URL = "https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14"
SLIDES_1344_URL = "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1344"
FORM_1345_URL = "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1345"
NON_JP_1346_URL = "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1346"
JP_1347_URL = "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1347"
ONLINE_PORTAL_URL = "http://outgoing.oie.fju.edu.tw/"
CHECKED_AT_ISO = "2026-10-20T02:27:00Z"
CHECKED_DATE = "2026-10-20"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_fju_oct20_update_payload(update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    payload = json.loads(update_json_path.read_text(encoding="utf-8"))
    if payload.get("school_id") != "fju":
        raise ValueError("Invalid FJU Oct 20 update payload school_id")
    if payload.get("final_partner_list_and_quotas_confirmed") is not False:
        raise ValueError("FJU 116-1 partner list and quotas continue updating in November and must not be marked final")
    if payload.get("m365_login_required_partner_sheets_audited") is not False:
        raise ValueError("FJU M365-protected individual school Fact Sheets were not audited")
    if payload.get("online_system_campus_network_only") is not True:
        raise ValueError("FJU online application system must record campus network IP restriction")
    return payload


def validate_fju_oct20_update_snapshot(update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    payload = load_fju_oct20_update_payload(update_json_path)
    manifest = payload["source_manifest"]
    if len(manifest) != 5:
        raise ValueError(f"Expected 5 archived FJU Oct 20 source files, got {len(manifest)}")
    for key, meta in manifest.items():
        local_path = ROOT / meta["file"]
        if not local_path.exists():
            raise FileNotFoundError(f"Missing archived FJU Oct 20 source file for {key}: {local_path}")
        raw = local_path.read_bytes()
        if len(raw) != meta["bytes"]:
            raise ValueError(f"Byte count mismatch for {key}: expected {meta['bytes']}, got {len(raw)}")
        if _sha256_bytes(raw) != meta["sha256"]:
            raise ValueError(f"SHA256 mismatch for {key}: expected {meta['sha256']}")
    return payload


def apply_fju_oct20_updates(bundle: Path = FJU_BUNDLE, update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    payload = validate_fju_oct20_update_snapshot(update_json_path)
    manifest = payload["source_manifest"]

    # 1. Update import_provenance.json
    prov_path = bundle / "import_provenance.json"
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    existing_files = {s["file"] for s in prov.get("sources", [])}
    for meta in manifest.values():
        if meta["file"] not in existing_files:
            prov["sources"].append(
                {
                    "file": meta["file"],
                    "source_url": meta["source_url"],
                    "title": meta["title"],
                    "sha256": meta["sha256"],
                    "bytes": meta["bytes"],
                    "fetched_at": meta["fetched_at"],
                }
            )
    prov["generated_at"] = CHECKED_AT_ISO
    prov["active_cycle_note"] = (
        "116學年度第1學期（2027秋季班）赴姊妹校交換學生申請公告（newsID=1062）已於 2026-10-20 發布，"
        "雖標題寫即日起，正文載明線上申請系統（http://outgoing.oie.fju.edu.tw/，限校內網路連線）"
        "開放及紙本申請表收件期間為 2026/11/01 至 2026/12/24 16:30（送耕莘樓 A113 室）。"
        "名額及開放學校將於 11 月陸續由姊妹校提供並更新，目前公告附表（file=1346 非日語組、file=1347 日語組）"
        "標示為「通常名額（參考用）」，不能當成最終版；需 M365 登入之個別學校資料尚未查核。"
    )
    prov["source_update_20261020"] = {
        "checked_at": payload["checked_at"],
        "announcement_url": NEWS_1062_URL,
        "title_says_immediate_open": True,
        "actual_opens_at": payload["actual_system_and_submission_opens_at"],
        "actual_deadline_at": payload["actual_system_and_submission_deadline_at"],
        "online_system_url": ONLINE_PORTAL_URL,
        "online_system_campus_network_only": True,
        "final_partner_list_and_quotas_confirmed": False,
        "m365_login_required_partner_sheets_audited": False,
    }
    _write_json(prov_path, prov)

    # 2. Update exchange_info.json
    info_path = bundle / "exchange_info.json"
    info = json.loads(info_path.read_text(encoding="utf-8"))
    oct20_period_line = (
        "116學年度第1學期（2027秋季班）赴姊妹校交換學生申請公告（2026-10-20 發布，newsID=1062）："
        "標題雖寫即日起，正文載明線上申請系統（http://outgoing.oie.fju.edu.tw/，限校內網路使用）"
        "開放及紙本收件時間為 2026/11/01 至 2026/12/24 16:30（紙本送耕莘樓 A113 室）；"
        "名額及開放學校將於 11 月陸續更新，附表（file=1346、file=1347）為通常名額參考用，非最終版。"
    )
    info["application_period"] = [
        oct20_period_line,
        *[p for p in info["application_period"] if "newsID=1062" not in p],
    ]
    oct20_elig_line = (
        "116-1（2027秋季班）甄選評分標準（說明會簡報 file=1344 p.16）：50% 在校歷年平均成績 + 50% 語言能力；"
        "預計 2027 年 2 月公布非日語組校內獲推薦名單、2027 年 3 月公布日語組校內獲推薦名單。"
    )
    info["eligibility"] = [
        oct20_elig_line,
        *[e for e in info["eligibility"] if "file=1344" not in e],
    ]
    oct20_lang_line = (
        "116-1（2027秋季班）語測有效期限與日語組志願規定（newsID=1062、file=1344）："
        "英語檢定須為 2024/12/24 以後考取之有效成績（TOEFL iBT 舊制 79 / 2026年1月新制 4.0、IELTS 學術組 6.5、TOEIC 750）；"
        "日語檢定可先繳交網路成績，待 2027/01/31 前補齊成績證明後，於 1 月中旬以 Email 通知選填志願序"
        "（日語組申請時不用先選填志願；非日語組申請時至多選填 5 所志願）。"
    )
    info["language_requirement"] = [
        oct20_lang_line,
        *[l for l in info["language_requirement"] if "2024/12/24" not in l],
    ]
    info["required_documents"] = [
        "【A.紙本文件（唯一紙本）】天主教輔仁大學赴姐妹校交換生申請表（file=1345，A4 雙面列印、電腦打字輸入；須家長簽名＋蓋章，並經系/所秘書、主任、院長及雙主修／輔系／學程辦公室秘書、主任核可蓋章，2026/12/24 16:30 前送交耕莘樓 A113 室）",
        "【B.電子文件 1（上傳至 http://outgoing.oie.fju.edu.tw/，單檔勿超過 20MB）】書審資料合併單一 PDF：含中文簡歷（就學、工作及社團經驗，格式不拘，兩頁為限）、中文讀書計畫（只需繳交一份中文版、不需繳交英文版，至少 500 字，格式不拘，兩頁為限）、其他校內/外表現證明及清寒證明（無則免附）",
        "【B.電子文件 2】本校中文歷年成績單 PDF 電子檔（須含截至 114 學年度第 2 學期之歷年班級排名；碩一/博一須另附大學/碩士歷年成績單，轉學生須另附原就讀學校歷年成績單）",
        "【B.電子文件 3】語測證明 PDF 電子檔（英檢須為 2024/12/24 後考取；日檢可先交網路成績並於 2027/01/31 前補齊正式證明）",
    ]
    for url in (NEWS_1062_URL, SLIDES_1344_URL, FORM_1345_URL, NON_JP_1346_URL, JP_1347_URL):
        if url not in info["source_urls"]:
            info["source_urls"].append(url)
    info["last_checked"] = CHECKED_AT_ISO
    ExchangeInfo.model_validate(info)
    _write_json(info_path, info)

    # 3. Update student_dashboard.json
    dash_path = bundle / "student_dashboard.json"
    dash = json.loads(dash_path.read_text(encoding="utf-8"))
    dash["last_checked"] = CHECKED_AT_ISO
    if "selection_rules" in dash and isinstance(dash["selection_rules"], dict):
        dash["selection_rules"]["pending_quota_planning"] = True
        dash["selection_rules"]["partner_requirements_need_confirmation"] = True

    # Update application_periods[1] (116-1 校內收件) with verified exact dates
    for period in dash.get("application_periods", []):
        if period.get("academic_year") == "116" and "說明會" not in period.get("application_round", ""):
            period["title"] = "輔大 116-1（2027秋季班）校內甄選線上申請與紙本收件（11/1–12/24 16:30）"
            period["details"] = [
                "2026-10-20 官方公告（newsID=1062）：雖然公告標題寫「即日起開始收件至12月24日16:30止!」，正文載明線上申請系統開放及收件時間為 2026/11/01 至 2026/12/24 16:30。",
                "線上申請系統（http://outgoing.oie.fju.edu.tw/）有鎖校外 IP 連線，限校內網路使用；個別上傳 PDF 電子檔（書審資料、中文歷年成績單、語測證明）勿超過 20MB。",
                "紙本文件僅須繳交「赴姐妹校交換生申請表（A4 雙面列印、電腦打字輸入）」，完成家長簽章與系所／院／雙主修輔系學程核章後，於 2026/12/24 16:30 前送交耕莘樓 A113 室。",
                "名額及開放學校將於 11 月陸續由姊妹校提供並更新，目前附表（file=1346 非日語組、file=1347 日語組）標示為「通常名額 (參考用)」，不能當成最終版；需 M365 登入之個別學校資料未查。",
            ]
            period["source"] = {
                "title": "116學年度第1學期 (2027秋季班) 赴姊妹校交換學生申請公告（newsID=1062）",
                "source_url": NEWS_1062_URL,
                "category": "deadline",
                "summary": "系統開放及收件為 2026/11/01～12/24 16:30（限校內網路）；學校及名額於 11 月陸續更新，不能當成最終版。",
            }
            period["opens_at"] = "2026-11-01T00:00:00+08:00"
            period["deadline_at"] = "2026-12-24T16:30:00+08:00"
            period["date_status"] = "verified_exact"
            period["status"] = "upcoming"
            period["status_note"] = (
                "標題雖寫即日起，正文載明系統開放及收件為 2026/11/01～12/24 16:30（限校內網路）；"
                "學校與名額於 11 月陸續更新，目前名單不能當成最終版。"
            )
            period["deadline_note"] = "線上系統限校內網路（http://outgoing.oie.fju.edu.tw/）；紙本申請表送交耕莘樓 A113 室。"
            period["reminder_eligible"] = True
            period["checked_at"] = CHECKED_AT_ISO

    dash["program_overview"] = [
        {
            "title": "輔大 116-1（2027秋季班）申請公告與全球姊妹校交換計畫總覽（2026-10-20 核實）",
            "details": [
                "2026-10-20 新增 116-1（2027秋季班）申請公告（newsID=1062），提供甄選說明會簡報（file=1344）、申請表（file=1345）、非日語組（file=1346）及日語組（file=1347）姊妹校申請資格一覽表。",
                "雖然公告標題寫即日起，正文載明線上申請系統（http://outgoing.oie.fju.edu.tw/，限校內網路使用）開放及紙本申請表收件期間為 2026/11/01～12/24 16:30。",
                "重要邊界：學校及名額仍會在 11 月陸續更新（附表標示「通常名額 (參考用)」），不能當成最終版；需要 Microsoft 365（@m365.fju.edu.tw）登入的個別學校 Fact Sheet 資料尚未查核。",
            ],
            "source": {
                "title": "116學年度第1學期 (2027秋季班) 赴姊妹校交換學生申請公告（newsID=1062）",
                "source_url": NEWS_1062_URL,
                "category": "exchange_application",
                "summary": "2026-10-20 公告及 4 份 PDF 附件（file=1344、1345、1346、1347）已核實。",
            },
        }
    ]
    dash["required_documents"] = [
        {
            "title": "輔大 116-1（2027秋季班）紙本與電子上傳應備文件規範（newsID=1062、file=1345）",
            "details": [
                "A. 紙本文件（唯一須交紙本）：赴姐妹校交換生申請表（file=1345，A4 雙面列印，請以電腦打字輸入），須家長簽名＋蓋章，並經系/所秘書、主任、院長及雙主修、輔系、學程辦公室秘書、主任核可蓋章，送至耕莘樓 A113 室。",
                "B-1. 電子上傳—書審資料（合併為同一個 PDF 電子檔，勿超過 20MB）：含中文簡歷（就學、工作及社團經驗，格式不拘，兩頁為限）、中文讀書計畫（只需繳交一份中文版，不需繳交英文版，至少 500 字，格式不拘，兩頁為限）、其他校內/外表現證明及清寒證明（無則免附）。",
                "B-2. 電子上傳—中文歷年成績單 PDF（須含截至 114-2 之歷年班級排名；碩一/博一另附大學/碩士歷年成績單，轉學生另附原校歷年成績單）。",
                "B-3. 電子上傳—語測證明 PDF：英語成績須為 2024/12/24 以後考取（TOEFL iBT 舊制 79 / 新制 4.0、IELTS 學術組 6.5、TOEIC 750）；日語檢定可先交網路成績，待 2027/01/31 前補齊成績證明後，於 1 月中旬以 Email 通知選填志願序（日語組申請時不用先選填志願；非日語組至多選填 5 所）。",
            ],
            "source": {
                "title": "116學年度第1學期 (2027秋季班) 赴姊妹校交換學生申請公告（newsID=1062）",
                "source_url": NEWS_1062_URL,
                "category": "exchange_application",
                "summary": "116-1 紙本申請表與線上系統 PDF 電子檔上傳規定。",
            },
        }
    ]
    dash["document_explanations"] = [
        {
            "title": "116-1 赴姊妹校交換生申請表（file=1345）與線上書審資料規範",
            "summary": "116-1 採「線上系統上傳 3 項 PDF 電子檔＋紙本僅交雙面核章申請表」雙軌制；中文讀書計畫只需中文版（不需英文版），至少 500 字、兩頁為限。",
            "key_points": [
                "紙本申請表須以電腦打字輸入並以 A4 雙面列印，完成家長簽章及系所／院／雙主修輔系學程核章。",
                "中文簡歷（兩頁為限）與中文讀書計畫（至少 500 字、兩頁為限，不需英文版）合併為單一書審資料 PDF（<=20MB）上傳至 http://outgoing.oie.fju.edu.tw/（限校內網路）。",
            ],
            "applies_to": [],
            "source": {
                "title": "116-1（2027秋季班）赴姊妹校交換生申請表（file=1345）",
                "source_url": FORM_1345_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": FORM_1345_URL,
            "document_type": "official_document",
            "full_text_extracted": True,
        }
    ]
    existing_dash_urls = {s["source_url"] for s in dash.get("sources", [])}
    for meta_key, cat in [
        ("news_1062_116_1_apply", "deadline"),
        ("116_1_info_slides", "info_session"),
        ("116_1_application_form", "exchange_application"),
        ("116_1_non_japanese_partners", "partner_school"),
        ("116_1_japanese_partners", "partner_school"),
    ]:
        meta = manifest[meta_key]
        if meta["source_url"] not in existing_dash_urls:
            dash["sources"].append(
                {
                    "title": meta["title"],
                    "source_url": meta["source_url"],
                    "category": cat,
                    "summary": "2026-10-20 查核；116-1（2027秋季班）官方公告與附件（名單與名額於 11 月陸續更新，非最終版）。",
                }
            )
    StudentDashboard.model_validate(dash)
    _write_json(dash_path, dash)

    # 4. Update pages.jsonl
    pages_path = bundle / "pages.jsonl"
    pages = [
        json.loads(line)
        for line in pages_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    pages = [p for p in pages if p.get("source_url") != NEWS_1062_URL]
    oct20_page_text = (
        f"{payload['announcement_title']}\n"
        "系統開放及收件時間：2026/11/01 至 2026/12/24 16:30（雖標題寫即日起，正文載明系統開放及收件為 11/1～12/24 16:30）。\n"
        f"線上申請系統：{ONLINE_PORTAL_URL}（有鎖校外 IP 連線，限校內網路使用）。\n"
        f"名額更新說明：{payload['partner_list_november_rolling_update_note']}\n"
        "A. 紙本文件：" + "；".join(payload["paper_required_documents"]) + "\n"
        "B. 電子文件：\n" + "\n".join(payload["electronic_required_documents"]) + "\n"
        f"甄選評分標準：{payload['selection_scoring_formula']}"
    )
    oct20_page = {
        "title": "天主教輔仁大學：116學年度第1學期（2027秋季班）赴姊妹校交換學生申請公告（newsID=1062）",
        "source_url": NEWS_1062_URL,
        "published_at": "2026-10-20T00:00:00Z",
        "text": oct20_page_text,
        "summary": "116-1（2027秋）申請公告：正文載明系統開放及收件為 11/1～12/24 16:30（限校內網路）；學校及名額將在 11 月陸續更新，不能當成最終版。四份 PDF 已讀；需登入之個別學校資料未查。",
        "category": "exchange_application",
        "attachments": [
            {
                "url": SLIDES_1344_URL,
                "filename": "116_1_info_slides.pdf",
                "local_path": "sources/fju/116_1_info_slides.pdf",
                "content_type": "application/pdf",
            },
            {
                "url": FORM_1345_URL,
                "filename": "116_1_application_form.pdf",
                "local_path": "sources/fju/116_1_application_form.pdf",
                "content_type": "application/pdf",
            },
            {
                "url": NON_JP_1346_URL,
                "filename": "116_1_non_japanese_partners.pdf",
                "local_path": "sources/fju/116_1_non_japanese_partners.pdf",
                "content_type": "application/pdf",
            },
            {
                "url": JP_1347_URL,
                "filename": "116_1_japanese_partners.pdf",
                "local_path": "sources/fju/116_1_japanese_partners.pdf",
                "content_type": "application/pdf",
            },
        ],
        "crawled_at": CHECKED_AT_ISO,
        "content_hash": manifest["news_1062_116_1_apply"]["sha256"],
    }
    ProcessedPage.model_validate(oct20_page)
    pages.insert(0, oct20_page)
    _write_jsonl(pages_path, pages)

    # 5. Update home_rules.json, documents.json, catalog-completeness.json, verification_status.json
    home_rules_path = bundle / "home_rules.json"
    home_rules = json.loads(home_rules_path.read_text(encoding="utf-8"))
    home_rules["eligibility"] = dash["eligibility"]
    home_rules["application_periods"] = dash["application_periods"]
    home_rules["selection_weights_116_1_briefing"] = {"gpa": 0.50, "language": 0.50}
    home_rules["source_urls"] = info["source_urls"]
    home_rules["verified_at"] = CHECKED_DATE
    _write_json(home_rules_path, home_rules)

    docs_path = bundle / "documents.json"
    docs_payload = json.loads(docs_path.read_text(encoding="utf-8"))
    docs_payload["required_documents"] = dash["required_documents"]
    docs_payload["source_urls"] = info["source_urls"]
    _write_json(docs_path, docs_payload)

    comp_path = bundle / "catalog-completeness.json"
    comp = json.loads(comp_path.read_text(encoding="utf-8"))
    comp["active_term"] = (
        "116學年度第1學期（2027秋季班）申請公告（newsID=1062）已於 2026-10-20 發布，"
        "正文載明系統開放及收件期間為 2026/11/01～12/24 16:30（限校內網路）；"
        "學校及名額仍會在 11 月陸續更新，附表（file=1346、file=1347）為通常名額參考版，不能當成最終版。"
    )
    comp["verified_at"] = CHECKED_DATE
    comp["source_update_20261020"] = prov["source_update_20261020"]
    _write_json(comp_path, comp)

    ver_path = bundle / "verification_status.json"
    ver = json.loads(ver_path.read_text(encoding="utf-8"))
    ver["checked_at"] = CHECKED_AT_ISO
    ver["counts"] = comp
    _write_json(ver_path, ver)

    # 6. Update partners.jsonl and application_workflows.jsonl while preserving reference_only / agreement_only
    partners_path = bundle / "partners.jsonl"
    partners = [
        json.loads(line)
        for line in partners_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    new_deadline_str = (
        "116-1（2027秋季班）線上系統開放與紙本收件：2026/11/01 至 2026/12/24 16:30"
        "（標題雖寫即日起，正文載明為 11/1–12/24 16:30，線上系統限校內網路，紙本送耕莘樓 A113 室；"
        "學校及名額將於 11 月陸續更新，不能當成最終版）。"
    )
    for p in partners:
        p["application_deadline"] = new_deadline_str
        p["availability_note"] = (
            "輔大 116-1（2027秋季班）申請公告（newsID=1062）已發布，系統開放及收件為 2026/11/01～12/24 16:30；"
            "惟姊妹校開放名單與名額將於 11 月陸續更新（附表標示通常名額參考用，非最終版），目前維持參考狀態。"
        )
        if p.get("student_summary_zh"):
            p["student_summary_zh"]["application_deadline"] = new_deadline_str
        PartnerUniversity.model_validate(p)
    _write_jsonl(partners_path, partners)

    wf_path = bundle / "application_workflows.jsonl"
    workflows = [
        json.loads(line)
        for line in wf_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for wf in workflows:
        wf["applicability_note"] = (
            "輔大 116-1（2027秋季班）申請公告（newsID=1062）載明系統開放及收件為 2026/11/01～12/24 16:30（限校內網路）；"
            "名額及開放學校將於 11 月陸續更新，附表（file=1346、file=1347）不能當成最終版。"
        )
        if len(wf.get("steps", [])) >= 2:
            step2 = wf["steps"][1]
            step2["title"] = "於校內網路完成線上系統申請並繳交核章紙本申請表至耕莘樓 A113"
            step2["deadline_at"] = "2026-12-24T16:30:00+08:00"
            step2["deadline_status"] = "verified_exact"
            step2["deadline_source_url"] = NEWS_1062_URL
            step2["deadline_checked_at"] = CHECKED_AT_ISO
            step2["summary"] = (
                "116-1 系統開放及收件為 2026/11/01 至 2026/12/24 16:30（限校內網路 http://outgoing.oie.fju.edu.tw/）；"
                "紙本僅須繳交雙面列印核章之交換生申請表至耕莘樓 A113 室。"
            )
        UniversityApplicationWorkflow.model_validate(wf)
    _write_jsonl(wf_path, workflows)

    from .fju_oct21_updates import UPDATE_JSON_PATH as OCT21_SOURCE, apply_fju_oct21_updates
    if OCT21_SOURCE.exists():
        apply_fju_oct21_updates(bundle)

    return {
        "school_id": "fju",
        "sources_count": len(prov["sources"]),
        "partners_count": len(partners),
        "workflows_count": len(workflows),
    }
