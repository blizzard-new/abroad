"""Review Sungshin's actual Spring2027 announcement, documents and stale cells."""
from __future__ import annotations

import json
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from fetch_ccu_completion_sources import BUNDLE as B
from pypdf import PdfReader
from review_ccu_followup_batch import evidence, receipt, response_text
from review_ccu_followup_batch import fact as reviewed_fact

CALL = "official-spring2027-call"
ENG = "official-spring2027-attachment-113855"
KOR = "official-spring2027-attachment-113854"
DOCS = "official-spring2027-attachment-113856"
MANUAL = "official-spring2027-attachment-113950"
NOM = "official-spring2027-attachment-113951"
COURSES = "official-spring2027-attachment-113857"
COURSE_GUIDE = "official-spring2027-attachment-113949"
YEAR = "官方2026-09-16公告（09-18修改）的Spring2027附件；正文Spring2027/Fall2027，按Spring欄核實"
ROUND = "Spring2027接待Exchange；中正校內梯次另核"


def fact(value, ev, *, status="verified_current", reason="當期接待正文已核對；不改變中正校內名額、資格與已截止申請視窗。"):
    return reviewed_fact(value, ev, status=status, reason=reason)


def main():
    pdfs = {}
    for label, count in [(ENG, 9), (KOR, 8), (DOCS, 2), (MANUAL, 15)]:
        r = receipt(49, label)
        pdfs[label] = [re.sub(r"\s+", " ", p.extract_text() or "")
                       for p in PdfReader(B / r["bundled_file"]).pages]
        assert len(pdfs[label]) == count

    def pdf(label, page, quote):
        assert quote in pdfs[label][page - 1], (label, page, quote)
        ev = evidence(49, label, quote, pages=[page], year=YEAR)
        ev["application_round"] = ROUND
        return ev

    def call(quote):
        assert quote in response_text(receipt(49, CALL))
        ev = evidence(49, CALL, quote, year=YEAR)
        ev["application_round"] = ROUND
        return ev

    def sheet(label):
        r = receipt(49, label)
        with ZipFile(B / r["bundled_file"]) as z:
            ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            strings = ["".join(t.itertext()) for t in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si", ns)]
            root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
            return {c.get("r"): strings[int(c.find("s:v", ns).text)]
                    for c in root.findall(".//s:c", ns) if c.get("t") == "s"}

    stale = sheet(NOM)["V1"]
    assert "1 December 2025" in stale
    nom_ev = evidence(49, NOM, stale, year=YEAR)
    nom_ev["application_round"] = ROUND
    nom_ev["location_in_source"] = "XLSX Sheet1!V1; actual cell, not PDF page"
    nom_ev["note"] = nom_ev["location_in_source"]
    with ZipFile(B / receipt(49, COURSES)["bundled_file"]) as z:
        workbook = z.read("xl/workbook.xml").decode()
        assert 'name="2026 Spring"' in workbook and 'name="2026 Fall"' in workbook
    course_ev = evidence(49, COURSES, "2026 Spring; 2026 Fall", year="正文工作表及A3均為2026課表，2027課表尚未核實")
    course_ev["application_round"] = "2026課程參考；非2027可選課表"
    course_ev["location_in_source"] = "XLSX workbook sheet names; 2026 Spring!A3 / 2026 Fall!A3"
    course_ev["note"] = course_ev["location_in_source"]
    guide_pages = list(PdfReader(B / receipt(49, COURSE_GUIDE)["bundled_file"]).pages)
    assert len(guide_pages) == 9 and all("sugang.sungshin.ac.kr" in p.extract_text() for p in guide_pages)
    guide_ev = evidence(49, COURSE_GUIDE, "Course Registration Schedule For 2026-2 Semester",
                        pages=[1, 2, 6, 7, 8, 9], year="當期公告附的查課指南；實際截圖為2026-2，非2027課表")
    guide_ev["application_round"] = "2026-2操作參考；非2027可選課表"
    guide_ev["location_in_source"] = "PDF screenshots visually read: p1 2026-2 heading; p2 Year2026/2nd; p6 course name; p7-9 syllabus language"
    host = {
        "program_scope": fact("Spring2027校際Exchange，男女皆可；本科／研究生依原學制與相關科系登記。Soojung與Woonjung Green兩校區，付費Visiting與雙聯另列，不代表全學程均可申請。", [pdf(ENG, 4, "including male students"), pdf(ENG, 1, "Soojung Campus (Seoul, Donam)")]),
        "eligibility": fact("須母校正式提名、符合母校推薦成績標準；本科完成至少2學期、研究生至少1學期。此incoming條件不取代中正outbound至少2學期及年級門檻。", [pdf(ENG, 4, "at least one semester for graduate students"), pdf(ENG, 4, "academic standards required by their home university for nomination")]),
        "language": fact("當期接待簡章官方語言成績非必繳，建議TOPIK3或TOEFL iBT3.5；2026-01-20以前應試舊制建議59，沒有自行分數換算。英語課有限、課程可要求韓語；舊鏡像建議71與新版59不同，中正outbound數值門檻仍須分開確認。", [pdf(ENG, 4, "submission of an official language test score is not mandatory"), pdf(ENG, 4, "TOEFL iBT 3.5 / TOEFL iBT: 59 or above for tests taken by January 20, 2026.")], status="conflict", reason="最新接待正文與舊鏡像／中正要求分開；建議分數不能被當作母校必備或跨尺度自動判資格。"),
        "nomination_deadline": fact("Spring2027母校提名：2026-09-14至2026-10-23；官方公告與新PDF一致。提名由母校coordinator，候選不可超過協議quota；不是學生申請截止。", [call("Nomination Deadline: 23 October 2026"), pdf(ENG, 2, "October 23, 2026")]),
        "application_deadline": fact("學生線上申請2026-10-26至2026-11-23；母校彙整正本也須2026-11-23抵校，非寄出日。舊鏡像10/1起始由新PDF10/26取代。Fall2027欄仍寫2026正本／CoA年份，不能套Spring或自行修正。", [call("Application Deadline: 23 November 2026"), pdf(ENG, 2, "October 26, 2026"), pdf(ENG, 2, "November 23, 2026")]),
        "documents": fact("當期checklist共8項required＋1項optional：線上表副本、護照copy、英文成績、正式在學證明（未明定語言）、國際處長簽提名函、財力證明、自填Personal Medical Assessment、3.5×4.5照片（只線上）；語言成績optional。前7項線上＋母校彙整郵寄。Exchange財力USD5200/期或10400/年，Visiting付費額另制。公告明示本學期自填表取代Health Examination Form；factsheet仍留X光／醫師簽章及有健康状况才填舊段，與checklist必繳自填不一致，額外醫療文件適用待校方確認，不列X光為全體必繳。", [call("replacing the Health Examination Form starting this semester"), pdf(DOCS, 1, "Personal Medical Assessment (Self-check)"), pdf(DOCS, 2, "If you have any specific or significant health conditions"), pdf(ENG, 3, "$ 5,200 USD"), pdf(ENG, 4, "Chest X-ray result")], status="conflict", reason="已取得當期checklist和自填模板；保留舊醫療段矛盾及按情況追加文件，不能混作通用必備。"),
        "application_forms": fact("已開啟當期checklist／Medical Assessment兩頁PDF、15頁Online Application Manual、nomination XLSX。醫療表學生填性別／血型／生日、11項Yes/No/Remarks及日期／姓名／簽名，無通用醫師簽章格；額外重大健康文件個別提交。學生portal需email驗證、sign up/sign in、Save後還必須Final Submission；手冊範例不是已登入私有表完整必填集。Nomination XLSX的Sheet1!V1實際仍要求正本於2025-12-01到達，與2027公告的2026-11-23矛盾，不能把檔名Spring2027當內容正確；PDF及checklist短提名網址不同，官方最新公告長網址保留來源，未猜其相同表。", [pdf(DOCS, 2, "Personal Medical Assessment"), pdf(MANUAL, 11, "Enter your email and password"), pdf(MANUAL, 14, "Final Submission"), nom_ev], status="conflict", reason="公开当期附件可读，但提名表内旧年和提名网址差異待校方確認；個人portal最新字段需本人帳號。"),
        "academic_calendar": fact("Spring2027課程2027-03-02至6月底（15週），考試依課程在第7–8週及14–15週；選課暫定2027-02-17至19、第一週3月add/drop。新官方中英文PDF一致更正舊鏡像Spring2026與不存在的2/29。Fall年份錯誤與成績單July／Mid-August差異另存待核，不改Spring日期。", [pdf(ENG, 2, "March 2 ‒ Late June 2027"), pdf(ENG, 2, "February 17‒19, 2027")], reason="新版正文Spring欄一致且適用年明載；僅核Spring課程／選課／考試，不宣稱其他有誤欄已解。"),
        "course_restrictions": fact("本科最多19、碩士9；博士當期PDF p2寫研究生含博士9、p4表列博士12，兩份中英文PDF均保留矛盾，不選較寬上限。相關科系登記、容量先到先得，不保證英語課、跨校區連堂或選到特定課；隨附XLSX實際僅2026 Spring/Fall，2027課表將於開學前約1月提供，尚未核實新版。", [pdf(ENG, 2, "9 credits for graduate students (Master’s/Doctoral)"), pdf(ENG, 4, "Doctoral degree: Up to 12 credits"), pdf(ENG, 5, "approximately one month before the start of each semester"), course_ev], status="conflict", reason="博士學分上限內文矛盾；2026課表不能作2027開課保證。"),
        "housing": fact("線上申請選Yes預約住宿，2027年1月初Google Form再確認／取消；宿舍距校5–10分鐘、依人數隨機分房。External Agency、The House、Sungmiryo房型與管理不同，The House先到先得；沒有个人特定房型／床位保證。Spring住宿2027-02-23至06-30，冬夏續住需另申請。", [pdf(ENG, 8, "select “Yes” to reserve a spot in the dormitory"), pdf(ENG, 8, "Rooms are randomly assigned"), pdf(ENG, 2, "February 23 ‒ June 30, 2027")]),
        "housing_deadline": fact("Spring2027先在線上申請期勾住宿，2027年1月另外發確認／取消表與指示；新PDF未列最終確認的確切日。付款表載2/25–26，但住宿段說入住後1–2日（韓文2日內），不可逕自當取消期限。舊鏡像Spring2026-07-31／Fall2027-01-29取消日未見新版沿用，留歷史參考。", [pdf(ENG, 2, "January 2027"), pdf(ENG, 8, "Within 1‒2 days after moving into the dormitory"), pdf(ENG, 2, "February 25‒26, 2027")], status="needs_confirmation", reason="確認窗口已核，獨立確切截止與付款日期差異待校方通知；不是官方明示尚未公告。"),
        "costs": fact("Spring2027宿舍每期KRW：外包single2940000、double/triple1750000、quad1537500；The House double2097380；Sungmiryo double1857380/triple1487500/quad1115630，費率可變。生活估1050000–1330000 KRW/月（住宿400000/680000、餐400000、交通50000、個人200000），不把每期宿費重複加進月預算。財力USD5200是證明額、保險及韓語課另計。", [pdf(ENG, 8, "1,115,630"), pdf(ENG, 8, "2,940,000"), pdf(ENG, 8, "1,050,000 ~ 1,330,000 monthly")]),
        "insurance": fact("當期簡章韓國私人健康保險mandatory，約KRW80000/6月，確認付款才發CoA；NHIS於居留卡發出另納、約80000–100000/月。NHIS registration/fees詳情TBA僅此子項，不把整個保險欄標尚未公告；日本／法國國籍可個別申請免除。兩種保險與財力額不可當一次繳清。", [pdf(ENG, 7, "Private Health Insurance (Mandatory)"), pdf(ENG, 7, "Details about registration and fees are TBA.")]),
        "visa": fact("接待簡章要求D-2；收到校方CoA與Business Registration Certificate後向相關外交機構申請。Spring簡章列End of December（2026），原文件到達及保險付款是CoA前提；不沿用舊鏡像1月初中旬，也不保證個人簽證獲准／持居留卡後再入境程序。", [pdf(ENG, 7, "All incoming international students at Sungshin must obtain a D-2 student visa."), pdf(ENG, 7, "End of Dec"), pdf(ENG, 3, "can only be issued upon the arrival of the original documents")]),
        "arrival": fact("Spring2027線上orientation2/12、實體2/25，宿舍入住2/23–24，付款表2/25–26與段落入住後1–2日需依房間通知核對；沒有據此承諾接機或可延後入住。", [pdf(ENG, 2, "February 12, 2027"), pdf(ENG, 2, "February 23‒24, 2027"), pdf(ENG, 8, "Within 1‒2 days")]),
        "host_tuition": fact("當期Exchange Tuition Waiver；Visiting及Double-Degree是付費路徑。密集韓語課另制：本科一般課≤9／研究所≤3學分時韓語學費免，但申請及教材仍KRW160,000；達10／4學分時韓語學費800,000＋160,000，不能宣稱交換全免費。", [pdf(ENG, 3, "(Tuition Waiver)"), pdf(ENG, 6, "KRW 160,000"), pdf(ENG, 6, "KRW 800,000")]),
        "exchange_duration": fact("當期可選一學期或一學年；Spring一學期3–6月、Spring全年3–12月。實際到離校涵蓋住宿、orientation及個人考試，不以課程15週當簽證或住宿期間。", [pdf(ENG, 4, "One semester or a Full year")]),
    }
    host["application_forms"]["research_classification"] = "personal_access_required"
    host["course_restrictions"]["evidence"].append(guide_ev)
    host["course_restrictions"]["value"] += "；9頁查課指南已逐頁檢視，範例畫面仍是2026-2學期，僅作分類／科系／語言篩選及點課名看syllabus的操作參考，不是2027已開放課程。"
    manual = json.loads((B / "completion-manual-fields.json").read_text())
    manual["schools"] = [r for r in manual["schools"] if r["ccu_page"] != 49]
    manual["schools"].append({"ccu_page": 49, "expose_host_overrides": True, "host_fields": host})
    (B / "completion-manual-fields.json").write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n")
    docs = [
        ("線上申請表副本（完成Final Submission後列印）", None, [], True, False),
        ("護照個人頁彩色copy", None, [], True, False),
        ("正式英文成績單", None, [], True, False),
        ("母校正式在學證明（當期未明定語言）", None, [], True, False),
        ("母校國際處長簽名提名函（自由格式）", None, ["母校國際處長"], True, False),
        ("財力證明（Exchange USD5200/期或10400/年）", None, [], True, False),
        ("Personal Medical Assessment自填健康評估表", receipt(49, DOCS)["source_url"] + "#page=2", ["學生"], True, False),
        ("3.5×4.5cm證件照（只線上上傳、不郵寄）", None, [], False, False),
        ("語言能力證明（當期optional；中正要求另核）", None, [], False, True),
    ]
    records = []
    clauses = ["Online Application Form", "Passport copy", "Official Academic transcripts (English)",
               "Official Certificate of Enrollment", "Letter of Nomination", "Proof of Bank Statement",
               "Personal Medical Assessment", "ID Photo (3.5*4.5 cm)", "Language Proficiency Certificate"]
    for (name, url, signers, post, optional), clause in zip(docs, clauses, strict=True):
        ev = [pdf(DOCS, 1, clause)]
        if clause == "Proof of Bank Statement":
            ev.append(pdf(ENG, 3, "$ 5,200 USD"))
        elif clause == "Letter of Nomination":
            ev.append(pdf(ENG, 3, "Signed by the Director of International Office at Home University"))
        elif clause == "Personal Medical Assessment":
            ev.append(pdf(DOCS, 2, "Signature"))
        records.append({"requirement": {"name": name, "signatures": signers, "official_form_url": url,
                         "official_form_verified": bool(url), "source_urls": [receipt(49, CALL)["source_url"], receipt(49, DOCS)["source_url"]],
                         "stage": "student_application", "conditional": optional,
                         "condition": "語言成績接待端optional；母校出國語言要求與個別課語言仍須另核。" if optional else None,
                         "copy_type": "original_and_copy" if post else "digital", "needs_confirmation": "Medical" in name,
                         "applicability_status": "needs_confirmation" if "Medical" in name else "verified_current",
                         "applicability_year": "Spring2027", "applicability_note": "自填表為當期新模板；额外醫療文件適用差異待核。" if "Medical" in name else None},
                        "postal_original_required": post, "evidence": ev})
    partner = next(json.loads(line) for line in (B / "partners.jsonl").read_text().splitlines() if json.loads(line)["source_pages"][0] == 49)
    payload = {"ccu_page": 49, "school_name": partner["school_name"], "academic_year": "Spring2027", "checked_at": receipt(49, CALL)["checked_at"],
               "requirements": records, "evidence": [call("replacing the Health Examination Form starting this semester"), pdf(DOCS, 1, "Application Documents Checklist"), pdf(DOCS, 2, "Personal Medical Assessment")],
               "postal_address": "2, Bomun-ro 34da-gil, Seongbuk-gu, Seoul 02844 Republic of Korea; Office of International Affairs and Services, Soojung Campus, Sungshin Hall 1st floor",
               "review_note": host["documents"]["value"], "superseded_source_ids": ["p49-mirror"],
               "residual_conflicts": ["Nomination XLSX Sheet1!V1: 1 December 2025 vs Spring2027 originals 2026-11-23", "博士学分PDFp2:9 vs p4:12", "Medical self-check required vs factsheet conditional/X-ray/clinician legacy", "Fall2027原件到件及CoA年份仍寫2026", "成績單發出p2:July vs p6:Mid-August", "PDF/checklist/announcement的nomination短鏈與長鏈不同，未假設同一表"]}
    (B / "completion-sungshin-documents.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print("Sungshin Spring2027: all 17 fields reviewed, 9 document entries, stale years/cells preserved")


if __name__ == "__main__":
    main()
