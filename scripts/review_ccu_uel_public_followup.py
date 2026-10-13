"""Read UEL's undated factsheet, dated housing document and inconsistent 2026/27 calendar."""
from __future__ import annotations

import csv
import hashlib
import json
import re

from bs4 import BeautifulSoup
from fetch_ccu_completion_sources import BUNDLE as B
from pypdf import PdfReader
from review_ccu_public_followup import evidence, fact, raw, source


def main():
    manual = json.loads((B / "completion-manual-fields.json").read_text())
    previous = next(r for r in json.loads((B / "completion-reviewed-fields.json").read_text())["schools"]
                    if r["ccu_page"] == 66)["host_fields"]
    for field in previous.values():
        field["evidence"] = [ev for ev in field["evidence"]
                             if ev.get("source_id") != "p66-official-factsheet-pdf"]
    pdf_record = source(66, "official-factsheet-pdf")
    pages = PdfReader(B / pdf_record["bundled_file"]).pages
    assert len(pages) == 4
    assert not re.search(r"\b20\d{2}\b", " ".join(p.extract_text() for p in pages))

    def pdf(page, quote):
        return evidence(66, "official-factsheet-pdf", quote, pages=[page],
                        year="目前官方UEL短連結所列PDF4頁，正文未標學年度；不當成2027專屬版",
                        status="needs_confirmation")

    # Both actual PDFs use >= glyphs. Their text extractors lose the lower stroke.
    # Preserve the extracted string separately instead of changing the threshold.
    language_ev = pdf(1, "Minimum B2 level: IELTS > 6.0, TOEIC > 650 or equivalent")
    language_ev.update(extracted_excerpt=language_ev["excerpt"],
                       excerpt="Minimum B2 level: IELTS ≥ 6.0, TOEIC ≥ 650 or equivalent",
                       evidence_method="PDF page1 visually reviewed; extraction loses lower equality stroke",
                       visual_review_file="completion_sources/p66-visual-current-language.png")
    language_ev["visual_review_sha256"] = hashlib.sha256((B / language_ev["visual_review_file"]).read_bytes()).hexdigest()
    for ev in previous["language"]["evidence"]:
        if ev.get("source_id") == "p66-reference-link-1":
            ev.update(extracted_excerpt=ev.get("extracted_excerpt", ev["excerpt"]),
                      excerpt="At least B1 in English (IELTS ≥ 5.0, TOEIC ≥ 450 or equivalent)",
                      evidence_method="Historical PDF page3 visually reviewed; extraction loses lower equality stroke",
                      visual_review_file="completion_sources/p66-visual-historical-language.png")
            ev["visual_review_sha256"] = hashlib.sha256((B / ev["visual_review_file"]).read_bytes()).hexdigest()

    def incomplete(value, ev, *, classification="research_incomplete", reason=None):
        return fact(value, ev, status="needs_confirmation", research_classification=classification,
                    reason=reason or "官方目前連結PDF已讀，但正文未標年；尚未核實2027個人適用版本，母校本期未開放不變。")

    calendar = source(66, "academic-calendar-csv")
    cells = list(csv.reader(raw(calendar).decode().splitlines()))
    assert cells[0][8] == "2026-2027 ACADEMIC CALENDAR"
    assert cells[13][18] == "14/12/2026 - 27/03/2027"
    assert cells[13][26] == "15/03/2026 - 27/03/2027"
    assert cells[11][26] == "20/11/2025 - 01/12/2025"
    assert cells[15][18] == "12/04/2026 - 24/07/2026"
    assert cells[15][26] == "05/07/2027 - 24/07/2026"
    calendar_ev = {"source_id": calendar["source_id"], "source_url": calendar["source_url"],
                   "source_pages": [], "source_locator": "CSV row1 col9; row12/14/16 cols19,27; current first tab2026-2027",
                   "checked_at": calendar["checked_at"], "content_hash": calendar["sha256"],
                   "academic_year": "官方表格2026-2027頁籤；日期年份矛盾未改",
                   "application_round": "2027接待另核；中正本期未開放", "status": "conflict",
                   "excerpt": "2026-2027 ACADEMIC CALENDAR; Semester2 14/12/2026 - 27/03/2027; Finals 15/03/2026 - 27/03/2027; Semester3 12/04/2026 - 24/07/2026; Finals 05/07/2027 - 24/07/2026"}
    housing = source(66, "accommodation-public-text")
    housing_text = raw(housing).decode()
    assert "Updated to July 2026" in housing_text
    assert "USD 55 to USD 138 per 6 months" in housing_text
    housing_ev = {"source_id": housing["source_id"], "source_url": housing["source_url"],
                  "source_pages": [], "source_locator": "section1 VNUHCM Dormitory B; UTF-8 public text export",
                  "checked_at": housing["checked_at"], "content_hash": housing["sha256"],
                  "academic_year": "Updated to July2026；2027個人租約另核", "application_round": "2027接待參考",
                  "status": "conflict", "excerpt": "Updated to July 2026; USD 55 to USD 138 per 6 months; closes daily at 11 PM"}
    login = json.loads((B / "completion_sources/p66-official-ctp-application.receipt.json").read_text())
    assert login["http_status"] == 401
    login_text = BeautifulSoup(raw(login), "html.parser").get_text(" ", strip=True)
    assert "You must sign in to access this content" in login_text
    login_ev = {"source_id": login["source_id"], "source_url": login["source_url"],
                "source_pages": [], "checked_at": login["checked_at"], "content_hash": login["sha256"],
                "academic_year": "個人Google Forms入口，未讀到表單年份或題目", "application_round": "提名後學生申請入口",
                "status": "needs_confirmation", "excerpt": "Sign in to your Google Account. You must sign in to access this content"}
    host = {
        "program_scope": incomplete("UEL Credit Transfer Program(CTP)公開factsheet。母校提名→學生送件→錄取／簽證，不將Summer Camp、articulation或Erasmus funding當中正交換方案；PDF無年度。", [pdf(2, "UEL CTP Incoming Nomination Form")]),
        "eligibility": incomplete("目前連結但未標年PDF：partner全時在學生、母校至少完成2學期、每交換學期至少3門課。母校舊參考附件的管理／法律範圍仍須依中正有效協議，沒有擴成全部院系。", [pdf(1, "Must have completed at least 02 semesters of study at home institutions")]),
        "language": incomplete("目前未標年PDF視覺原文：minimum B2、IELTS ≥6.0或TOEIC ≥650／equivalent，母校英文證明也接受。舊2023–2024參考視覺原文為B1、IELTS ≥5.0／TOEIC ≥450；兩份純文字抽取均丟失等號而呈>，已按PDF第1／3頁實際符號核讀。不選舊較低門檻，也未宣稱新版2027已核實。", previous["language"]["evidence"] + [language_ev, pdf(1, "English certification from home institution is also accepted")]),
        "nomination_deadline": incomplete("未標年PDF：Semester1 June5、Semester2 September25、Semester3 February5。雖校曆另有2026–2027頁籤，不能替未標年提名日加2026／2027或把中正Spring一律套Semester2。", [pdf(1, "Nomination deadline   June 5   September 25   February 5")]),
        "application_deadline": incomplete("未標年PDF：Semester1 June15、Semester2 October5、Semester3 February15；舊2023–2024附件Semester2為October15。沒有核實2027個人截止，不套舊年或自行推年。", previous["application_deadline"]["evidence"] + [pdf(1, "Application deadline   June 15   October 5   February 15")]),
        "documents": incomplete("未標年PDF初申8項：CTP Application Form、成績單、提名信、英文CV、語言／母校英文證明、護照、Vietnam NA1 Visa Application Form、護照尺寸照片。錄取後才發Acceptance Letter、Learning Agreement、visa approval/guidelines；宿舍rental form/agreement與護照影本是住宿申請，不混入初申。", [pdf(2, "Vietnam NA1 Visa Application Form"), pdf(2, "UEL Learning Agreement")]),
        "application_forms": incomplete("目前官方CTP-OnlineApplication連結轉到Google Forms，實讀401回應正文You must sign in to access this content。須Google個人帳號才繼續，未登入、未讀题目／年度、未提交；不宣稱只有提名者有權限。未取得CTP application/nomination、NA1的2027版本，舊母校Drive表僅參考。", [pdf(2, "http://link.uel.edu.vn/CTP-OnlineApplication")], classification="personal_access_required", reason="依實際Google登入提示，不只依HTTP401分類；尚未核實帳號授權範圍或最新表單内容。"),
        "academic_calendar": fact("官方2026–2027第一頁籤／CSV：Semester1 2026-08-24→12-01；Semester2 2026-12-14→2027-03-27，Lunar New Year 2027-02-01→14。考試欄S1卻2025-11-20→12-01，S2開始2026-03-15到2027-03-27；S3semester寫2026-04-12→07-24、exam2027-07-05→2026-07-24。正文矛盾原樣保留，不替官方改年，精確個人考試／第三學期待確認。", [calendar_ev], status="conflict", research_classification="research_incomplete", reason="已讀2026-2027頁籤實際CSV儲存格；多項年份與區間矛盾，不只看文件名。"),
        "course_restrictions": incomplete("未標年PDF：每學期至少3門，英文授課；Economics／Business／Management／Law各faculty列示，跨faculty須符合母校最低學分。1Vietnamese credit=1.5ECTS為UEL/VNUHCM規則，不保證中正抵免；linked General Curriculum頁無學年，未核2027實際開課／容量／協議領域。", [pdf(1, "Must register for at least 03 courses per exchange semester"), pdf(2, "01 VC = 1.5 ECTS")]),
        "housing": fact("未標年factsheet p4稱VNUHCM Dormitory A/B USD55–138『monthly』；同官方連結住宿文UpdatedJuly2026 section1卻55–138『per6months』，計價單位矛盾未選定。DormB約500m、A約2km，23:00關閉；UEL協助rental application/agreement、1照片及護照影本，不保證2027床位。GuestHouse與私人公寓另列，不等同校內配額。", [pdf(4, "monthly rent (USD)"), housing_ev], status="conflict", research_classification="research_incomplete", reason="住宿文件正文明示July2026，但與未標年factsheet租金單位不同；保留兩者不擅改。"),
        "costs": fact("未標年factsheet p4估生活USD540–1030/月，住房300–600、飲食150–250、交通/data40–80、個人50–100；行政費USD150/semester另計，optional fieldtrip估30。宿舍55–138的monthly／per6months矛盾未解，2027個人費率未核，不把估算當總繳費保證。", [pdf(4, "Total cost 540 - 1,030"), pdf(4, "Mandatory administrative fee: USD 150/semester"), housing_ev], status="conflict", research_classification="research_incomplete", reason="一般估算文件未標學年；住宿單位矛盾，必繳行政費與可選旅遊費分開。"),
        "visa": incomplete("未標年factsheet p3：錄取審核後UEL向HCMC Immigration申請，估3–4週後發visa approval；學生到選定使領館領簽。不要在Acceptance Letter＋approval兩者到手前訂機票；提前旅遊入境可能須離境領學生簽再返。這是校方流程而非個人法律保證，未核2027台灣身分適用。", [pdf(3, "After 3-4 weeks"), pdf(3, "MUST NOT book a flight until they receive both the UEL Letter")]),
        "arrival": incomplete("未標年factsheet p4：BuddyUp1對1mentor與機場pickup，接機限registering for VNUHCM’s accommodations，不推所有住宿均有。抵達／機票遵循校方錄取及簽證approval提醒，未核2027個人接機表／時間。", [pdf(4, "airport pickup"), pdf(4, "if registering for VNUHCM’s accommodations")]),
        "host_tuition": incomplete("舊母校附件只作參考列母校繳學費。目前未標年PDF只明示USD150/semester行政費，沒有新的tuition waiver條文；不能把行政費當學費或由partner推免學費，2027個人tuition待確認。", previous["host_tuition"]["evidence"] + [pdf(4, "Mandatory administrative fee: USD 150/semester")]),
        "exchange_duration": incomplete("未標年PDF區分one-semester與one-year exchange；p3的180day／365day是visa validity，不能當授課期間或自動延長。三個semester依學程安排，個人交換長度與2027正確校曆另核。", [pdf(3, "One-semester"), pdf(3, "One-year exchange")]),
    }
    # The strict policy-source validator continues to require HTTP200. The login
    # body is separately archived access evidence, not an unread policy document.
    host["application_forms"]["access_requirement_evidence"] = [login_ev]
    manual["schools"] = [r for r in manual["schools"] if r["ccu_page"] != 66]
    manual["schools"].append({"ccu_page": 66, "host_fields": host})
    (B / "completion-manual-fields.json").write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n")
    print("Reviewed 15 UEL fields; undated policy, actual sign-in and calendar/rental-unit conflicts retained")


if __name__ == "__main__":
    main()
