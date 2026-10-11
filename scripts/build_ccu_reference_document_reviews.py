"""Keep readable reference-school documents and their actual year separate.

Labelled passages are historical/raw reference evidence, never parsed into
automatic eligibility, fees, deadlines or an apparently complete form set.
The independently reviewed Spring-2027 Ateneo fields supersede these passages.
"""
from __future__ import annotations

import json
import re

from fetch_ccu_completion_sources import BUNDLE as B, OUT
from build_ccu_completion_reviews import fact, from_receipt

YEARS = {
    "p113-reference-link-1": "正文2024更新；一般學校Fact Sheet，非2027接收簡章",
    "p116-reference-link-1": "正文Fact Sheet2025–26",
    "p13-reference-link-1": "正文2026秋季港澳台校際交流；2026-09-14至2027-01-15",
    "p13-reference-link-2": "正文2026秋季港澳台申請表；不是2027春",
    "p13-reference-link-3": "正文2026秋／2025–2027混載，費率為2026春；文末2026-01",
    "p22-reference-link-1": "上海大學港澳台來校指南；正文未標適用年度",
    "p31-reference-link-1": "東南大學一般介紹／進修等學科資料；未核實適用年度及台灣交換路徑",
    "p31-reference-link-2": "東南大學赴校交流注意事項；正文未標適用年度",
    "p40-reference-link-1": "正文2026 Spring Entrance，2025-07-29更新；非2027入學",
    "p40-reference-link-2": "本科科系可供exchange名單；正文未标适用年度",
    "p46-reference-link-1": "正文Hallym Exchange Student Program Factsheet2026",
    "p51-reference-link-1": "正文2026第一學期春季交換簡章；非2027",
    "p56-reference-link-1": "正文2025/26香港教育大學資訊",
    "p57-reference-link-1": "正文MUST Exchange Information Sheet2023–2024",
    "p66-reference-link-1": "正文UEL Academic Year2023–2024 CTP",
    "p81-reference-link-1": "正文AY2026–2027 Undergraduate Spring2027",
    "p81-reference-link-2": "正文AY2026–2027 Graduate Spring2027",
    "p91-reference-link-1": "正文Incoming Exchange Fact Sheet2025–2026",
    "p93-reference-link-1": "正文Academic Course2025/2026",
    "p21-reference-link-1-file-1": "DOCX本科專業一覽表正文未標年；公開檔名2023僅作參考",
    "p21-reference-link-1-file-2": "正文港澳台赴校交換表，年份202留空；未核實2027新版",
    "p69-reference-link-1-file-1": "正文Semester Exchange Factsheet2024",
    "p69-reference-link-2-file-1": "正文FPT semester exchange FAQ未標適用年度",
    "p96-reference-link-1-file-1": "正文LETI交換Fact Sheet；2024–2025公開檔名仍須按正文個別日期確認",
    "p97-reference-link-1-file-1": "正文ITMO exchange semester2024–2025",
}
PATTERNS = {
    "program_scope": r"(?i)exchange (?:program|students)|交換(?:學生|生)|校际交流",
    "language": r"(?i)language (?:prof|require)|TOEFL|IELTS|語言(?:要求|能力)|英语水平",
    "nomination_deadline": r"(?i)nomination (?:deadline|period)|deadline for nomination|提名(?:時間|日期|截止)|系统提名时间",
    "application_deadline": r"(?i)application (?:deadline|period)|deadline for application|申請(?:截止|期限|時間)|递交材料截止",
    "documents": r"(?i)required documents|application (?:documents|requirements)|所需申[請请]材料|申請文件",
    "academic_calendar": r"(?i)academic (?:calendar|schedule)|exam period|學期時間|学期时间",
    "housing": r"(?i)accommodation|housing|dormitor|住宿|宿舍",
    "costs": r"(?i)cost of living|living (?:expenses|cost)|住宿費|住宿费|生活費|生活费|costs per semester",
    "insurance": r"(?i)insurance|保險|保险",
    "visa": r"(?i)student visa|visa application|签证|簽證|居留",
    "arrival": r"(?i)orientation|arrival|迎新|抵達|接機|报到|報到",
    "host_tuition": r"(?i)tuition|學費|学费",
    "exchange_duration": r"(?i)duration of (?:exchange|study)|period of study|交換期|exchange period|one or two semesters",
}


def main():
    manual_path = B / "completion-manual-fields.json"
    manual = json.loads(manual_path.read_text())
    rows = {r["ccu_page"]: r for r in manual["schools"]}
    doc_reviews = []
    for sid, year in YEARS.items():
        path = OUT / (sid + ".parsed.json")
        if not path.exists():
            continue
        parsed = json.loads(path.read_text())
        receipt = json.loads((OUT / (sid + ".receipt.json")).read_text())
        page = receipt["ccu_page"]
        is_pdf = bool(parsed.get("attachment_file"))
        doc_reviews.append({"source_id": sid, "ccu_page": page, "applicability": year,
                            "checked_at": receipt["checked_at"], "page_count": len(parsed["text_pages"]) if is_pdf else None,
                            "source_url": receipt["source_url"], "content_hash": receipt["sha256"],
                            "review_result": "Spring2027本科／研究所個別欄已人工核實；母校本期未開放" if page == 81 else "歷史或未標年參考；尚未核實2027新版",
                            "attachment_file": parsed.get("attachment_file")})
        if page == 81:
            continue  # Manual current fields always retain both independent scopes.
        row = rows.setdefault(page, {"ccu_page": page, "host_fields": {}})
        for key, pattern in PATTERNS.items():
            if key in row["host_fields"]:
                continue
            for physical_page, content in enumerate(parsed["text_pages"], 1):
                text = re.sub(r"\s+", " ", content).strip()
                match = re.search(pattern, text)
                if not match:
                    continue
                quote = text[max(0, match.start() - 50):min(len(text), match.end() + 650)]
                ev = from_receipt(receipt, quote, year=year, pages=[physical_page] if is_pdf else [], status="reference_only")
                ev["application_round"] = "歷史／其他梯次參考；2027新版尚未核實"
                ev["bundled_attachment"] = parsed.get("attachment_file")
                if not is_pdf:
                    ev["location_in_source"] = "DOCX文字／表格順序，不冒充實體PDF頁碼"
                row["host_fields"][key] = fact("參考附件原文：" + quote, [ev],
                    "只保存已讀附件的此欄原文與原年度。來源可能有不同計畫／學制，未解析成2027申請條件、期限、費用或完整文件集；本期未開放。", "reference_only")
                break
    manual["schools"] = list(rows.values())
    manual_path.write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n")
    (B / "completion-reference-document-reviews.json").write_text(json.dumps(doc_reviews, ensure_ascii=False, indent=2) + "\n")
    print("readable document content reviews", len(doc_reviews))


if __name__ == "__main__":
    main()
