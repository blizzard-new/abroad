"""Review current CZU/USJ public receiving rules without opening closed CCU rows."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from bs4 import BeautifulSoup
from pypdf import PdfReader
from review_ccu_public_followup import B, evidence, fact, raw, read, source


def main():
    manual = read("completion-manual-fields.json")
    manual["schools"] = [r for r in manual["schools"] if r["ccu_page"] not in {92, 112}]
    year = "CZU正文明示Academic year2026/2027；Erasmus與non-Erasmus exchange並列"

    def cz(label, quote, *, status="verified_current", applicable_year=year):
        return evidence(112, "public-" + label, quote, year=applicable_year, status=status)

    current = cz("current-2026-2027", "Academic Calendar and Basic Information 2026/2027")
    host = {
        "program_scope": fact("CZU2026/2027當期頁明載Erasmus與non-Erasmus交換，不能只套Erasmus／ICM獎助。當期course list限定7個faculty/institute，IVP僅限母校與該Institute有有效雙邊協議；合作校全校協議不自動擴大IVP可選範圍。中正本期灰字未開放維持不變。", [current, cz("current-courses", "The courses listed below will be offered to Erasmus and non-Erasmus exchange students.")]),
        "eligibility": fact("母校負責coordinator提名且有效對應協議；2026/2027公開申請表收集已修學期數，未在所讀正文列一般GPA／年齡門檻。Bachelor跨選Master課須至少大二，是選課條件而非所有交換申請者最低年級。完整個人／院系資格待核，不改中正outbound資格。", [cz("current-application", "Your nomination must be submitted by the responsible coordinator at your home university"), cz("current-courses", "Bachelor students may choose Master-level courses if they are at least in the second year of their Bachelor studies.")], status="needs_confirmation"),
        "language": fact("CZU2026/2027明載English B2、certificate required；UIS文件舉MyAcademy、TOEFL、IELTS或母校確認為例。未列檢定數字，不能自行把B2換成IELTS／TOEFL分數或擅定母校校內豁免。", [cz("current-2026-2027", "English B2 (certificate required)"), cz("current-application", "Document on language proficiency – for example MyAcademy, TOEFL, IELTS, or confirmation from your home university")]),
        "nomination_deadline": fact("CZU2026/2027第二學期提名15 October，即2026-10-15；僅母校coordinator用Online Nomination Form，email／EWP均不受理，逾期不接受。第一學期／全年15 May另列，不把它當Spring截止。未載日內時刻。", [current, cz("current-application", "15 October – summer semester"), cz("nomination", "Nominations submitted after the deadline are not taken into account")]),
        "application_deadline": fact("2026/2027申請頁只明載2026-06-12給first/winter及full year；OLA頁只明載2026-06-30簽LA。2027第二學期Spring的UIS／non-Erasmus LA個人截止尚未核實，不能直接複用6月日期或把提名10/15當學生申請日。", [cz("current-application", "Application deadline: 12 June, 2026 – for students coming in the first (winter) semester and full year"), cz("current-ola", "JUNE 30, 2026")], status="needs_confirmation", research_classification="research_incomplete"),
        "documents": fact("2026/2027 UIS需Transcript of Records、health insurance（EU EHIC／non-EU商業保險）、language proficiency proof；Master另附Bachelor成績，合成一個PDF；passport-style profile photo另上傳。護照號碼在personal details，不推定需護照掃描。non-Erasmus另用International Exchange Students Formular，完整個人表／Spring截止待核。", [cz("current-application", "Transcript of Records – official record of all passed courses at your home university"), cz("current-application", "If you study at Master level, upload also the results from your Bachelor studies."), cz("current-ola", "For non-Erasmus students only.")]),
        "application_forms": fact("先提名、確認後CZU UIS email發個人登入資訊，完整學生申請在UIS；non-Erasmus專用International Exchange Students Formular模板由email寄送，與Erasmus OLA／PDF LA分流。已讀公開操作，不登入、不提交；未取得non-Erasmus模板及個人版本，不能把公開Erasmus表當中正必備表。", [cz("current-application", "The email contains your UIS login credentials"), cz("current-ola", "The template will be sent to students by e-mail together with instructions.")], status="needs_confirmation", research_classification="personal_access_required"),
        "academic_calendar": fact("CZU2026/2027第二Summer學期交換期間2027-02-01至06-30；Welcome Week02-01至02-07，registration02-01/02-02，enrolment02-03或02-04，welcome02-05，teaching02-08。考試期間原文明示To be specified，僅該段官方未定；其他日期已核實。第一學期結束02-07與第二開始02-01重疊，照原文保留不自行平移。", [cz("current-2026-2027", "1 February – 30 June 2027"), cz("current-2026-2027", "To be specified Examination period")], status="needs_confirmation", reason="仅第二學期考試期間官方明示尚待指定，不把整份2026/2027校曆標成未公告。", research_classification="official_not_announced"),
        "course_restrictions": fact("CZU2026/2027只准當期交換course list；每學期最多30ECTS、超限LA拒收，校方無最低但母校可另訂。可跨faculty但主要faculty至少50%課程；大二以上Bachelor才可選Master，Master選Bachelor須母校同意。IVP另要院級有效協議。thesis/research须學生自己到校前找supervisor，容量有限不保證，不能當已錄取研究計畫。", [cz("current-courses", "All Learning Agreements exceeding this limit will be declined."), cz("current-courses", "At least 50% of your selected courses must come from that faculty."), cz("current-courses", "Acceptance, therefore, cannot be guaranteed.")]),
        "housing": fact("當期入口提供external dormitories Hloubětín／West／TVM，各自booking與條件；學生推薦列表CZU明示不背書／不核查，不保證床位。Hloubětín屬Praha9校外住宿，不借其GPS當Suchdol主校區點；表單後5工作日回覆依容量接受／拒絕，付款及確認信後才confirmed。", [cz("housing", "Each dormitory has its own booking system and conditions.", applicable_year="CZU2026/2027當期入口所連住宿頁；提供者條件未另標學期"), cz("linked-hloubetin", "depending on the current available capacity", applicable_year="校方住宿服務現行頁，價格欄另標自2026-01-01")]),
        "housing_deadline": fact("Hloubětín個別reservation成立後10日內付一個月租的deposit，另要ISKAM電子合約；這是個別訂房相對期限，不是CZU全校Spring住宿固定截止。2027入住的個人確認及他館期限未取得。", [cz("linked-hloubetin", "within 10 days of the reservation date", applicable_year="現行宿舍預訂流程，未另標2027個人日期")], status="needs_confirmation"),
        "costs": fact("Hloubětín租金表右欄From1January2026：單人studio CZK14700/月、雙人10500/人/月，含VAT、至少一月；旁欄14000/10000未標適用年，不混用。另可退deposit一月租，退房後最多一月退還；WiFi／laundry／parking另付。這是特定校外宿舍租金而非總生活費，2027個人合約費率待核。當期住宿獎助只述Czech銀行與追溯付款，無金額，不能從租金扣除。", [cz("linked-hloubetin", "14,700 CZK / month", applicable_year="Hloubětín右欄價格自2026-01-01；2027個人合約未核"), cz("linked-hloubetin", "10,500 CZK / person / month", applicable_year="同表右欄自2026-01-01"), cz("current-housing-scholarship", "Revolut is not considered a Czech bank account.")], status="needs_confirmation"),
        "insurance": fact("CZU當期UIS要health insurance證明，EU EHIC／non-EU商業保險分開。2026-05-04服務頁把90日內necessary/urgent travel cover與90日以上comprehensive分開，列400000EUR/claim；豁免依政府／計畫，不能推定中正台灣生適用EHIC或豁免。頁上within90days與簽證前proof的個人時序須按主管機關另核，非到校可無保險的承諾。", [cz("current-application", "Health insurance – EU students: EHIC card; non-EU students: commercial insurance contract"), cz("insurance", "minimum coverage limit of €400,000 per claim", applicable_year="CZU服務頁正文2026-05-04；接待要求與個人現行法律適用分開")], status="needs_confirmation"),
        "visa": fact("2026/2027接待流程按是否需要Czech visa分流：需要者原始紙本LoA寄郵件並另email說明；不需要者可於UIS下載。非Erasmus身分不等於免簽；國籍、停留與個人簽證／居留適用未從LoA推定，未把EU流程套台灣生。", [cz("current-acceptance", "will receive the original paper-based Letter of Acceptance by postal service.")], status="needs_confirmation"),
        "arrival": fact("第二Summer學期2027-02-01正式開始Erasmus與non-Erasmus交換；02-01/02-02 registration，02-05Official Welcome Session，02-08開始教學。01-25至01-29是optional Czech course時段，未把它當全員必到日或免費接機。校方要求依官方exchange dates安排旅行。", [cz("current-2026-2027", "1 February 2027 is the official start of the Erasmus and non-Erasmus exchange period for the second semester."), cz("current-2026-2027", "Please arrange your travel according to the official exchange dates stated above.")]),
        "exchange_duration": fact("2026/2027交換第二學期02-01至06-30、全年至06-30。公開extension截止2026-12-05是第一學期延長到同年度第二學期，須母校與CZU faculty批准及更新LA；不推定Spring2027可直接延長到2027秋季。中正雙邊交換期間／核准另符合。", [cz("current-2026-2027", "30 June 2027 Official end of the Erasmus and non-Erasmus exchange period for the second semester and the full academic year"), cz("current-extension", "Deadline for requesting an extension: 5 December 2026")]),
    }
    table = next(t for t in BeautifulSoup(raw(source(112, "public-linked-hloubetin")), "html.parser").find_all("table") if "14,700" in t.get_text())
    cells = [[c.get_text(" ", strip=True) for c in tr.find_all("td")] for tr in table.find_all("tr")]
    assert cells[0][2] == "From 1 st January, 2026"
    assert cells[1][2] == "14,700 CZK / month" and cells[2][2] == "10,500 CZK / person / month"
    manual["schools"].append({"ccu_page": 112, "host_fields": host})

    usjyear = "USJ Fact Sheet封面EXCHANGE STUDENTS2026–2027，當期接待；Erasmus／雙邊範圍逐欄另註"

    def pdf(p, quote, *, status="verified_current"):
        return evidence(92, "public-factsheet-pdf-2026-2027", quote, pages=[p], year=usjyear, status=status)

    def usj(label, quote, *, status="needs_confirmation"):
        applicable_year = ("USJ網頁正文2026/27 ACADEMIC YEAR" if label == "academic-calendar"
                           else "USJ現行incoming公開頁，旁連2026/27 Fact Sheet；此網頁段落未另標年")
        return evidence(92, "public-" + label, quote, year=applicable_year, status=status)

    pages = PdfReader(B / source(92, "public-factsheet-pdf-2026-2027")["bundled_file"]).pages
    assert len(pages) == 5 and "EXCHANGE STUDENTS 2026 - 2027" in pages[0].extract_text()
    form_record = source(92, "public-non-european-la")
    with ZipFile(B / form_record["bundled_file"]) as archive:
        form_text = " ".join(ET.fromstring(archive.read("word/document.xml")).itertext())
    form_quote = "Before the mobility"
    assert form_quote in form_text and "Universidad San Jorge" in form_text
    assert not re.search(r"202[0-9]", form_text)
    form_ev = {"source_id": form_record["source_id"], "source_url": form_record["source_url"], "source_pages": [],
               "academic_year": "公開non-European Before the Mobility DOCX，正文無適用學年／版本日", "application_round": "2027個人適用版本仍待提名後核", "checked_at": form_record["checked_at"], "content_hash": form_record["sha256"], "status": "needs_confirmation", "excerpt": form_quote + "；Universidad San Jorge；Table A／Table B及三方signature（Word正文，未虛構頁碼）", "bundled_attachment": form_record["bundled_file"]}
    host = {
        "program_scope": fact("USJ接待頁区分degree admission與一學期／一年exchange，含Erasmus、SEMP、雙邊、SICUE；中正走有效對應學科雙邊，不能借Erasmus獎助、SICUE西班牙國內方案或學位招生資格。當期Fact Sheet2026–2027列Villanueva de Gállego校區。", [usj("application-procedure", "specific exchange agreements signed between the home institution and our university"), pdf(2, "Campus Universitario de Villanueva de Gállego.")]),
        "eligibility": fact("交換生須在高等院校註冊，母校與USJ有效bilateral涵蓋所申學科、正式提名；接待公開頁未列所有學科的GPA／年級門檻，不能從Erasmus／學位招生套用。健康臨床及翻譯另有mandatory B2，見language。", [usj("application-procedure", "If your university has a bilateral agreement with San Jorge University that covers your area of study")], status="needs_confirmation"),
        "language": fact("USJ2026–2027主要Spanish授課，一般recommended B1 English／Spanish；不是全員B1硬性門檻。Health Sciences臨床mandatory SpanishB2，Translation and Intercultural Communication mandatory Spanish及／或EnglishB2；個別English module可要C1或同時ES/ENB2，未以一般B1替代。", [pdf(3, "The recommended language level is B1 in English and/or Spanish."), pdf(3, "mandatory B2 level in Spanish.")]),
        "nomination_deadline": fact("2026–2027 Spring提名15November，即2026-11-15；general bilateral頁與PDF日期一致，母校先正式提名。PDFp2的nomination敘述明寫Erasmus+，funding／身分不由日期一致推定；Fall/annual15May不是Spring。未列日內時刻。", [pdf(2, "15 November - Spring semester"), usj("application-procedure", "15th November for Spring semester mobilities")]),
        "application_deadline": fact("Exchange Students2026–2027 PDFp2列Spring15December，推導2026-12-15；完整個人流程在提名後發送，PDF提名段另明示Erasmus+，中正bilateral個人收件日與附件尚待核。Fall/annual15June不套Spring，不保證較晚截止。", [pdf(2, "15 December - Spring semester"), usj("application-procedure", "After the nomination, we will give you full information about the application process.")], status="needs_confirmation", research_classification="research_incomplete"),
        "documents": fact("公開申請頁要求學習協議及母校international coordinator簽名；nomination的姓名／DOB／國籍／email／degree/ISCED／年級／stay／母校聯絡是母校提名資料，不是全部學生初申附件。完整個人application附件在提名後通知，未把居留EX-18/EHIC/財力清單當所有台灣學生初申必繳。", [usj("application-procedure", "As part of the application procedure you will have a to complete a Learning Agreement")], status="needs_confirmation", research_classification="research_incomplete"),
        "application_forms": fact("已下載並讀公開Learning Agreement for Non European Students DOCX（Before the Mobility），內有USJ接待資訊、TableA/B、ES/EN自評及三方signature；正文无年度／版次，不能當已核2027最新個人表。Erasmus+／non-European／SICUE三種表分流，完整個人application提名後另發，未登入或提交。", [usj("application-procedure", "Learning Agreement for Non European Students"), form_ev], status="needs_confirmation", research_classification="research_incomplete"),
        "academic_calendar": fact("2026–2027 Spring Welcome2027-01-27/01-28（必須參加），teaching02-01至05-19、exams05-24至06-04、Easter03-25至04-02。重考結束矛盾：PDFp2 Spring列07-03，PDFFall列07-02，官網2026/27 resit列07-02；頁2已目視核列，不擅改07-03或省略重考風險。", [pdf(2, "14 June - 3 July", status="conflict"), usj("academic-calendar", "Friday 2nd of July 2027", status="conflict")], status="conflict", reason="同年度PDF Spring重考與網頁／PDF Fall原文日期不一致，個人重考安排待確認。", research_classification="research_incomplete"),
        "course_restrictions": fact("2026–2027 Fact Sheet課程須對照study area及語言；English modules頁未另標適用年，不能保證2027開課／座位。ICT Spring需OOP、networks、databases/SQL；部分research project limited seats且coordinator事前批准；Translation某課要求ES和EN兩者B2或EnglishC1。這些是不同學科／課程，不套全體中正交換生。", [pdf(3, "Courses offered in English: USJ website"), usj("english-modules", "networks, and databases/SQL."), usj("english-modules", "minimum of B2 level of Spanish and English required")], status="needs_confirmation"),
        "housing": fact("當期PDF提供找房協助，公開住宿頁列Zaragoza residences／外部平台；USJ明示不owner/manager/intermediary、無房源核查／供應保證，學生與provider自行簽約。Villanueva de Gállego接待校區與Zaragoza住宿城市分開，不推定到校宿舍保留床。", [pdf(3, "We provide assistance in finding accommodation for incoming students"), usj("accomodation-transport", "the University does not guarantee nor assume responsibility for the accuracy, availability")]),
        "costs": fact("2026–2027 PDFp3 university bus約EUR300/semester，這是交通單項不是房租或總月費；學期免費Spanish language courses由語言學院按程度分班。公開住宿頁無2027統一住宿／生活總費，與獨立provider合約分開，未從bus推定整體預算。", [pdf(3, "approximately €300 / semester."), pdf(3, "Free courses are offered throughout the semester")], status="needs_confirmation"),
        "insurance": fact("現行接待指南区分EU EHIC與non-EU：non-EU須入境前備涵蓋全stay的private health policy、Spain coverage並按visa條件；EU現地醫療啟用清單不自動套台灣生。頁面段落未標2027，個人保單／簽證適用待核，未提供核保或EHIC豁免保證。", [usj("health-assistance", "Non-European students must arrive in Spain with a private health insurance policy that covers the entire duration of their stay.")], status="needs_confirmation"),
        "visa": fact("現行USJ指南說non-European須赴西班牙前向Spanish Consulate办student visa、錄取後發LoA，welcome再說TIE；EU／雙籍另走流程。頁面同時把UK列European免簽清單，且未拆停留長度的TIE適用，2027個人主管機關規則未核，不能照搬整表或把EU EX-18四照片清單當台灣初申文件。", [usj("visas", "Non-European students must obtain a student visa before travelling to Spain."), usj("visas", "United Kingdom, Czech Republic")], status="needs_confirmation"),
        "arrival": fact("USJ2026–2027 Spring Welcome Sessions2027-01-27及01-28，公開頁要求international students參加；02-01開始課程。精確個人報到／住處安排依提名通知，不把約EUR300/semester university bus寫成免費機場接送。", [pdf(2, "Orientation Days: 27-28 January"), usj("academic-calendar", "International students are required to attend the Welcome Sessions")]),
        "exchange_duration": fact("USJ公開接待exchange為一學期或full academic year；2026–2027 Spring正課02-01至05-19、exam至06-04、重考最晚07-02／07-03矛盾另列。延長到下一學年／個人核准未載，不以學位admission替代中正雙邊期間。", [usj("application-procedure", "one semester or the full academic year"), pdf(2, "Examination Period: 24 May - 4 June")]),
    }
    manual["schools"].append({"ccu_page": 92, "host_fields": host})
    qut = next(r for r in manual["schools"] if r["ccu_page"] == 120)
    qut["host_fields"]["housing"] = fact("QUT StudyAbroad/Exchange現行生活頁更新2026-08-14，可用accommodation services協助選student complexes或independent rental；各provider條件另核。SiA段明示specifically for StudyAbroad，不把其utilities／resident-director套MoU Exchange。沒有2027個人保留床位或統一固定截止。", [evidence(120, "public-linked-living", "our dedicated accommodation services team can guide you.", year="QUT現行programme生活頁updated2026-08-14；未列2027個人床位／契約")], status="needs_confirmation")
    (B / "completion-manual-fields.json").write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n")
    print("Reviewed CZU16, USJ15 receiving fields and QUT housing; closed CCU statuses and missing fees remain unchanged")


if __name__ == "__main__":
    main()
