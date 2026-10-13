"""Keep SDU's publicly readable factsheet and personal form access separate."""
from __future__ import annotations

import json
import re
from copy import deepcopy

from fetch_ccu_completion_sources import BUNDLE as B
from pypdf import PdfReader
from review_ccu_followup_batch import evidence, fact, receipt, response_text


def main():
    source = receipt(89, "current-factsheet-from-official-partners")
    pages = [re.sub(r"\s+", " ", p.extract_text() or "")
             for p in PdfReader(B / source["bundled_file"]).pages]
    assert len(pages) == 5
    assert not any(re.search(r"\b20(?:2[4-9]|3\d)\b", p) for p in pages)
    year = "現行官方partners頁所連5頁Fact Sheet；正文未標學年，2027春適用尚未核實"

    def pdf(page, quote):
        assert quote in pages[page - 1], (page, quote)
        return evidence(89, "current-factsheet-from-official-partners", quote, pages=[page], year=year)

    def html(label, quote):
        record = receipt(89, label)
        assert quote in response_text(record)
        return evidence(89, label, quote, year="現行官方公開正文，未標2027交換適用學年；一般接待參考")

    manual = json.loads((B / "completion-manual-fields.json").read_text())
    row = next((r for r in manual["schools"] if r["ccu_page"] == 89), None)
    if row is None:
        row = {"ccu_page": 89, "host_fields": {}, "expose_host_overrides": True}
        manual["schools"].append(row)
    host = row["host_fields"]
    note = "已讀公開正文及PDF頁碼，但未核實2027春適用；不把未標年度當當期規則或官方明示尚未公告。"
    host["program_scope"] = fact(
        "一般交換接待Bachelor／Master；Exchange須母校提名及有效相關協議。Guest／free mover是另一付費路徑，不以暑校或學位招生替代交換。",
        [pdf(4, "Undergraduate / Bachelor level"), pdf(4, "Postgraduate / Master level"),
         html("current-apply-from-official-index", "Your university and SDU have a relevant exchange agreement.")],
        status="needs_confirmation", reason=note)
    host["academic_calendar"] = fact(
        "未標年Fact Sheet：Spring課程2/1–5/31、一般考試6/1–6/30（部分5月）、補考8/1–8/31；迎新為開學前最後兩個工作日。Autumn課程9/1–12/31、一般考試1/1–1/31（部分12月）、補考2/1–2/28。未自動加上2027年份、未把考試排除在交換期外。",
        [pdf(4, "Classes: 1 February – 31 May"), pdf(4, "Re-exams: 1 August – 31 August"),
         pdf(4, "Orientation days: Last two weekdays prior to semester start")],
        status="needs_confirmation", reason=note)
    host["visa"] = fact(
        "一般到校指南明載Exchange／Guest錄取申請處理後由SDU International Office提供居留許可資訊。Non-EU/EEA多數需student residence permit；學位生先繳學費的程序不可套免學費Exchange，EU與Nordic程序另列。個人國籍適用、當期許可要求與費額仍須官方主管機關核實。",
        [html("public-prepare-from-official-exchange", "You will receive information about residence permit from SDU International Office when your application has been processed.")],
        status="needs_confirmation", reason=note)
    host["arrival"] = fact(
        "一般到校指引依錄取信指定校區提供個人arrival資訊，行政程序於抵達前確認。公開頁建議及時參加開學前introduction days，最遲於9/1或2/1開學日到達；未標2027及確切迎新日期，不保證接機。",
        [pdf(5, "Students will receive arrival information according to the campus stated in the enrolment letter."),
         html("public-prepare-from-official-exchange", "The semester starts 1 September and 1 February, so you should arrive no later than this.")],
        status="needs_confirmation", reason=note)
    original = next(r for r in json.loads((B / "overseas-reviewed-fields.json").read_text())
                    if r["ccu_page"] == 89)
    form = host.setdefault("application_forms", deepcopy(original["fields"]["application_forms"]))
    # Reproducing the review must not append the same note/evidence again.
    form["value"] = form["value"].split(" 現行官方Exchange申請入口實際為帳號申請頁")[0] + (
        " 現行官方Exchange申請入口實際為帳號申請頁，明示按send才寄個人username/password；"
        "未輸入email或送出，沒有取得私有表內問題與年度。Guest入口l=60與Exchange l=178分開。")
    form["evidence"] = [e for e in form["evidence"]
                        if e.get("source_id") != "p89-public-exchange-form-from-official-apply"]
    ev = html("public-exchange-form-from-official-apply", "you receive an e-mail with a username and password")
    ev["status"] = "needs_confirmation"
    form["evidence"].append(ev)
    form["research_classification"] = "personal_access_required"
    form["reason"] = "公开入口明确個人帳號寄送程序，只將私有申請表內容列為權限限制；公開語言模板與政策研究仍可繼續。"
    (B / "completion-manual-fields.json").write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n")
    print("SDU 4 empty receiving fields mapped with unverified-year status; private form access evidenced")


if __name__ == "__main__":
    main()
