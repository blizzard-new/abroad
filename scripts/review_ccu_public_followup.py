"""Reproduce the explicitly read FGES/QUT public-source follow-up.

The faculty's year-stamped factsheet and its parent's inconsistent factsheet
remain separate evidence. A current fee page does not date every linked rule.
"""
from __future__ import annotations

import gzip
import json
import re

from bs4 import BeautifulSoup
from fetch_ccu_completion_sources import BUNDLE as B
from pypdf import PdfReader


def read(name):
    return json.loads((B / name).read_text())


def source(page, label):
    record = read(f"completion_sources/p{page}-{label}.receipt.json")
    assert record["http_status"] == 200 and record["tls_verify"] and not record.get("error")
    return record


def raw(record):
    path = B / record["bundled_file"]
    content = path.read_bytes()
    return gzip.decompress(content) if path.suffix == ".gz" else content


def evidence(page, label, quote, *, pages=(), year, status="verified_current"):
    record = source(page, label)
    if pages:
        contents = " ".join(PdfReader(B / record["bundled_file"]).pages[p - 1].extract_text() for p in pages)
    else:
        text_path = B / f"completion_sources/p{page}-{label}.txt"
        extracted = (text_path.read_bytes() if text_path.exists()
                     else gzip.decompress(text_path.with_suffix(".txt.gz").read_bytes()))
        contents = raw(record).decode(errors="replace") + " " + extracted.decode()
    assert re.sub(r"\s+", " ", quote) in re.sub(r"\s+", " ", contents), quote
    return {"source_id": record["source_id"], "source_url": record["source_url"],
            "source_pages": list(pages), "academic_year": year,
            "application_round": "2027春季接待規定另核；母校本期可選／期限不由此改變",
            "checked_at": record["checked_at"], "content_hash": record["sha256"], "status": status,
            "excerpt": quote}


def fact(value, ev, *, status="verified_current", reason="已讀所引原文、年度及計畫；未提供個人錄取、住宿或課程名額保證。", research_classification=None):
    result = {"value": value, "status": status, "reason": reason, "evidence": ev}
    if research_classification:
        result["research_classification"] = research_classification
    return result


def main():
    manual = read("completion-manual-fields.json")
    manual["schools"] = [r for r in manual["schools"] if r["ccu_page"] not in {88, 120}]
    originals = {r["ccu_page"]: r for r in read("overseas-reviewed-fields.json")}
    old = originals[88]["fields"]
    year = "母大學Lille Campus簡章封面／頁首2026–2027；部分期限內文2025，逐欄分開"

    def pdf(p, quote, *, status="verified_current"):
        return evidence(88, "followup-parent-2026-2027", quote, pages=[p], year=year, status=status)

    pdf_pages = PdfReader(B / source(88, "followup-parent-2026-2027")["bundled_file"]).pages
    assert len(pdf_pages) == 16
    assert "2026-2027" in pdf_pages[0].extract_text()
    assert "FGES" in pdf_pages[4].extract_text()
    assert "Spring 2027" in " ".join(read("overseas_sources/p88-mirror.json")["text_pages"])

    def comparison(key, value, ev):
        return fact(value, old[key]["evidence"] + ev, status="conflict",
                    reason="FGES學院專屬2026–2027簡章與母大學同年度簡章的原文不一致；保留兩者，未自行修正年份或選擇期限。",
                    research_classification="research_incomplete")

    host = {
        "eligibility": fact("母大學2026–2027交換簡章一般資格：本科／研究所、GPA至少2.75/4、至少18歲；p5明列FGES為接待院系。學院與有效協議的個別門檻仍須符合，沒有把此門檻改成中正outbound資格。", [pdf(5, "Undergraduate and/or Graduate – GPA 2.75/4 minimum – 18 years old minimum.")]),
        "language": comparison("language", "FGES學院2026–2027簡章：須語言證明、未限定證照，法／英B2為advised。母大學2026–2027 p5：法語授課須B2 minimum及教師推薦函；p7：partner英文授課無官方測驗要求、Erasmus+ ICM須B2證明。不能把FLSH心理學B2/C1或ISTC英語B2套給FGES；兩份對語言要求強度不同，待確認。", [pdf(5, "Students who wish to take courses in French will need a B2 level minimum"), pdf(7, "No official test is required for partner universities’ students")]),
        "nomination_deadline": comparison("nomination_deadline", "FGES學院Spring2027：2026-10-15；母大學2026–2027 p9卻寫Spring October10,2025（Fall April10,2025）。年度及日期矛盾，尚未核實正確提名截止，不能自行將2025改2026。", [pdf(9, "October 10, 2025", status="conflict")]),
        "application_deadline": comparison("application_deadline", "FGES學院Spring2027：2026-11-15；母大學2026–2027 p9卻寫Spring October15,2025（Fall April15,2025）。年度及日期矛盾，尚未核實正確學生申請截止，不能自行選較晚日期。", [pdf(9, "October 15, 2025", status="conflict")]),
        "documents": fact("不是完整附件清單：FGES學院須語言證明、未限定證照、法／英B2為advised；母大學p9另列有效護照、目前成績單（必要時法／英／西翻譯，官方或非官方接受），法語授課需教師推薦函或等級證書。ICM另加CV、cover letter、語言證明，不能當所有中正交換生必備。錄取後醫師填的Medical Form是註冊／到校階段，與初申分開。語言強度與完整個人表仍待確認。", old["documents"]["evidence"] + [pdf(9, "Copy of a valid passport"), pdf(13, "After your acceptance and to finalize your registration")], status="needs_confirmation", reason="並列FGES與母大學各自清單，不把有條件ICM文件與後續醫療表混入初申；語言要求差異見language欄。", research_classification="personal_access_required"),
        "application_forms": fact("公開母校Spring提名表不是學生申請表，原表未標年。母大學2026–2027 p9明示：提名核可後學生收到email以建立自己的帳號、在平台完成申請，院系可再要求個人附件。完整學生表及個人截止須用提名後個人入口取得；沒有登入或提交，未核最新個人表版本。", old["application_forms"]["evidence"] + [pdf(9, "the student will receive an email to create his/her account")], status="needs_confirmation", reason="官方正文明确提名後個人帳號，與HTTP468來源失敗分開。", research_classification="personal_access_required"),
        "academic_calendar": comparison("academic_calendar", "FGES學院Spring2027：1月第一／二週開課、本科及M1至4月中、M2至5–6月，重考本科6月／碩士7月。母大學p8 FGES專屬列Spring早1月至4月底、部分Master考試至6月中，年度Bachelor9月初至4月底／Master9月中至6月中。p8表格已目視核行；不是FD的1月初至5月中。時間粒度與分年級安排不同，精確個人課表待確認。", [pdf(8, "Spring semester: from early January to the end of April (for Master’s degree courses, some exams are happening until mid-June)")]),
        "course_restrictions": fact("僅FGES及中正有效協議所涵蓋領域，不能因母大學有其他院系就擴大選課。母大學p7容許必要時跨最多2院系，但須接待及母校核可；課程到校可能異動，須填provisional list，正常30ECTS／學期、建議至少20（尤其ICM），實際由母校決定。Apprenticeship／work-study不開放。p7指向25–26英文catalogue，未核2026–2027實際課程清單與容量。", old["course_restrictions"]["evidence"] + [pdf(7, "If necessary, exchange students are allowed to take classes in up to 2 faculties/schools"), pdf(7, "Catalogue_cours_anglais_A4_light_25_26.pdf")], status="needs_confirmation", reason="一般跨院規則、協議FGES範圍及尚未取得新版課單分開，沒有保證跨院錄取。", research_classification="research_incomplete"),
        "housing": fact("可選All大學宿舍或自行找房，須抵法前安排；All網上申請付270EUR行政費仍不保證住宿，依可用性分配，中正／UCLille國際處不負責分床。入住前至少15日取消academic exchange可退行政費；離宿至少提前1個月於個人帳號通知。未把附近住宿列表available解作Spring2027有保留床位。", [pdf(10, "these fees do not guarantee you to have an accommodation"), pdf(10, "at least 1 month before leaving the dorm via their personal web account")]),
        "housing_deadline": fact("2026–2027簡章p10標recommended：Spring1月開始交換建議11月15日前申請、10月12日開放；推導為2026-11-15／2026-10-12。仍可逾建議日申請且不保證床位。全年租約Spring從1月1日至12月31日、通知期結束後停止收租；不是要求交換生整年付費。", [pdf(10, "November 15 (application open on October 12)"), pdf(10, "Rent payments stop as soon as your notice period ends.")], reason="來源為2026–2027宿舍建議日期，沒有自行生成硬性截止或房間配額。"),
        "costs": fact("Lille2026–2027估算約EUR1,100/月；宿舍約550–650/月另charges/services。宿舍申請費270、contribution96、服務費105/月、住宿保險約30、deposit一個月租；費目逐項列，不誤算105為年費、不保證整體費用。交通31.50/月、餐廳3.30/餐為簡章估算，未替學生保證2027票價。", [pdf(11, "Total Around 1,100€/month"), pdf(11, "Services fees: 105 Euros per month")]),
        "insurance": fact("2026–2027接待簡章p13：錄取後醫師填Medical Form交CPSU；非EU學生在法超3月須免費註冊Sécurité Sociale；住房與民事責任保險mandatory，補充健康／旅遊保險recommended。法國健保不含境外旅行、遣返或民責，辦理可能數週。此為接待校要求，個人適用性與現行政府規定另核，不提供核保保證。", [pdf(13, "HOUSING AND CIVIL LIABILITY INSURANCE MANDATORY"), pdf(13, "spending more than 3 months in France to register")]),
        "visa": fact("接待簡章2026–2027 p12把Taiwan列於Études en France程序清單；須依Campus France／France-Visas辦學生簽證，未持學生簽證不接待。VLS-TS到法最遲3月內線上validate。這是學校公布流程，依國籍、停留與主管機關最新個人要求另核，不把台灣學生當免簽學期交換或保證簽證核准。", [pdf(12, "South Korea, Taiwan, Thailand"), pdf(12, "Students coming without a student visa will not be accepted."), pdf(12, "validate your visa within 3 months")]),
    }
    manual["schools"].append({"ccu_page": 88, "expose_host_overrides": True, "host_fields": host})

    provider = source(88, "followup-campus-provider")
    soup = BeautifulSoup(raw(provider), "html.parser")
    payloads = []
    for script in soup.find_all("script"):
        match = re.fullmatch(r'self\.__next_f\.push\(\[1,("(?:\\.|[^"\\])*")\]\)', script.string or "")
        if match:
            payloads.append(json.loads(match[1]))
    rsc = "".join(payloads)
    assert '"address":"60 bd Vauban, 59800 Lille","lat":50.63312,"lng":3.0439062,"establishment_id":5' in rsc
    assert '"name":"FGES Campus Vauban"' in rsc and '"position":{"lat":50.63312,"lng":3.0439062}' in rsc
    assert '"position":{"lat":50.63395,"lng":3.0199757}' in rsc and '"name":"FGES Campus WeNov (Euratechnologies)"' in rsc
    points = read("campus-coordinate-review.json")
    partner = next(json.loads(line) for line in (B / "partners.jsonl").read_text().splitlines() if json.loads(line)["source_pages"][0] == 88)
    marker_ev = evidence(88, "followup-campus-provider", "FGES Campus Vauban", year="一般FGES校區身份，查核2026-10-11；不是個人校區分配")
    marker_ev["excerpt"] = '公開SSR mapId=establishment-details-map，building31／establishment5：FGES Campus Vauban，60 bd Vauban, 59800 Lille，lat50.63312,lng3.0439062；另一marker32為FGES Campus WeNov，lat50.63395,lng3.0199757。'
    points["schools"]["88"] = {"decision": "accepted", "field": fact({
        "school_name": partner["school_name"], "country": partner["country"], "city": "Lille",
        "latitude": 50.63312, "longitude": 3.0439062, "geocode_status": "verified", "geocoded_at": provider["checked_at"],
        "source_url": provider["source_url"], "identity_source_url": "https://www.univ-catholille.fr/wp-content/uploads/Fact-Sheet-2026-27_digital.pdf",
        "precision": "representative", "note": "母大學當期簡章p10指定All為宿舍官方服務，該FGES公開地圖markers與building地址分別核實Vauban／WeNov。代表點選FGES Campus Vauban（business/economics/finance/life sciences），不能代替WeNov（其他領域）或個人接收校區；不是map viewport。"
    }, [pdf(10, "www.all-lacatho.fr/en/list-accommodation"), marker_ev], reason="FGES自己的公開地圖marker及building名稱地址一同核對，沒有借用母大學其他院系點。")}
    (B / "campus-coordinate-review.json").write_text(json.dumps(points, ensure_ascii=False, indent=2) + "\n")

    qyear = "QUT現行Study Abroad／Exchange公開頁，page updated2026-05-05；linked costs明示2027，非每段規定均標2027"

    def q(label, quote, *, status="verified_current", year=qyear):
        return evidence(120, "followup-" + label, quote, year=year, status=status)

    qhost = {
        "program_scope": fact("QUT現行Study Abroad與Exchange共用申請入口；交換須母校為partner且先提名，使用accepted nomination所附link。付費Study Abroad與MoU交換費用、獎助條件不同；中正名冊本期灰字未開放維持不變。", [q("apply", "If you are enrolled at one of our exchange partner institutions and applying for an exchange place, you'll need to be nominated by your home institution first.")]),
        "eligibility": fact("現行共用頁資格：至少18歲、非澳洲公民／永久居民；在認可機構至少一年全時學習、GPA2.5/4或等值，交換先由母校提名。這是接待條件，不能改為中正當期outbound資格或保證錄取。", [q("apply", "You must be 18 years or older and not hold Australian citizenship or permanent residency."), q("apply", "Hold a GPA of 2.5 on a 4-point scale (or equivalent)")]),
        "language": fact("現行2026-05-05更新頁：IELTS Academic／One Skill Retake總6.5各6；TOEFL iBT舊0–120刻度79（寫21／讀16／聽16／說18）；PTE58各50、CAE176各169、CPE C1。成績2年內；partner可能接受母校英文證明。官網未解釋2026新版TOEFL刻度及2027各考試日期適用，未自行換算；英文證明是否被接受仍須個案核。", [q("apply", "IELTS (Academic)/One Skill Retake: 6.5 overall, no sub-score below 6.0"), q("apply", "TOEFL iBT: 79 overall (minimum writing 21; reading 16; listening 16; speaking 18)")], status="needs_confirmation", research_classification="research_incomplete"),
        "application_deadline": fact("共用頁接受全年申請至semester start；exchange須先接受提名並用個人link。未另列2027 Exchange特定提名／學生截止，不把付費Study Abroad全年收件自動視為中正交換截止，未產生精確exchange日期。", [q("apply", "We accept applications year-round up to the semester start date.")], status="needs_confirmation", research_classification="research_incomplete"),
        "documents": fact("共用初申清單：最新英文官方成績、必要英文證明、有效至program結束後至少6個月的護照；申請列至少6門候選，母校須認可，先修評估可再要求既修課程詳細outline。未混入後續acceptance form、付款與CoE／簽證階段，沒有宣稱完整個人表已取得。", [q("apply", "A copy of your most recent official academic record (grades) in English."), q("apply", "Photocopy of your passport (valid for 6+ months after your program ends)")]),
        "application_forms": fact("QUT portal在線申請；exchange學生由accepted nomination所附link申請，acceptance of offer form是錄取後。已讀公開流程，未取得提名後學生個人表／欄位與版本；未登入、代填或付款。", [q("apply", "Applying via the link provided in your accepted nomination for an exchange place."), q("apply", "Complete the acceptance of offer form and details.")], status="needs_confirmation", reason="接待官網明示交換提名後個人link；不是下載失敗或官方明示尚未公告。", research_classification="personal_access_required"),
        "academic_calendar": fact("QUT 2027 Semester1：Welcome Week2027-02-15至02-19；semester02-22至06-19，teaching02-22至03-25及04-05至05-28，exams06-05至06-19。這對應中正2027春季赴南半球Semester1；不是北半球1月semester。Semester2及summer分開，不採summer欄混載的1月假期年份。", [q("calendar-2027", "Semester 1 Semester dates 22 February - 19 June", year="QUT明載2027 academic calendar／Semester1"), q("calendar-2027", "Welcome Week 15 February - 19 February", year="QUT2027／Semester1")]),
        "course_restrictions": fact("現行unit頁須核先修及所選年度可開課，PG不能選某些首年本科core／honours／capstone；Law本科不能讀PG，Law capstone與honours不開放，MBA另須GMAT／工作經驗。Arts可能作品集／audition，placement可另需費用或檢查。此頁仍含2022COVID條文，未把它當2027現行法律或已核准課單；個別unit2027供應／容量未核。", [q("units", "Undergraduate students cannot enrol in postgraduate units."), q("units", "From 23 January 2022")], status="needs_confirmation", reason="公開學制限制已讀，2027實際units與混載舊條文待核，不推定法律／課程當期適用。", research_classification="research_incomplete"),
        "costs": fact("2027官網按月列rent：student apartment AUD1600–2200／catered2400–2650／share house800–1600，另列utilities、food、phone和transport。原表Total2460–2795／2700–3095／1660–3545與逐項區間不一致（apartment列舉上界可達4095），保存原值待確認，未自創單一月費。Exchange不適用Study Abroad2027的AUD1000簽證獎助。", [q("costs", "In 2027:"), q("costs", "Total $2460-$2795 $2700-$3095 $1660-$3545"), q("costs", "does not apply to students enrolling as part of the student exchange program")], status="conflict", reason="已逐項核對原表數字；保存合計矛盾，不把學校估算變成個人預算保證。", research_classification="research_incomplete"),
        "insurance": fact("現行QUT 2027 costs頁：多數國際學生需有效OSHC，接受offer後經Medibank安排，部分國籍可豁免；境外旅行另須travel insurance。沒有推定中正學生豁免或個人保額，初申與錄取後購買分開。", [q("costs", "Most international students need valid OSHC"), q("costs", "Extra travel insurance is required for trips outside Australia.", year="QUT costs明示2027；OSHC現行服務說明")]),
        "visa": fact("QUT公開流程：接受錄取後若適用會收到CoE，取得CoE後才能申請Australian Student Visa；先核CoE資料、留簽證處理時間，由Home Affairs個案審。Study Abroad的簽證獎助明示排除exchange，不能用獎助推定交換簽證費免費。", [q("apply", "You will not be able to apply for your Australian student visa until you have received your CoE."), q("costs", "does not apply to students enrolling as part of the student exchange program")]),
        "arrival": fact("2027 Semester1 Welcome Week02-15至02-19，classes02-22開始；Study Abroad and Exchange Team有dedicated orientation。未載2027個人必到日、機場接送或服務免費，不把一般Welcome Week當所有exchange強制同日報到。", [q("calendar-2027", "Welcome Week 15 February - 19 February", year="QUT2027／Semester1"), q("life", "Study Abroad and Exchange Team will welcome you with a dedicated orientation session")]),
        "host_tuition": fact("QUT costs明載2027付費Study Abroad：3units/36cp/22.5ECTS AUD9900；4units/48cp/30ECTS AUD13200。若母校為exchange partner且提名，免QUT tuition；食宿、travel、books、OSHC及unit額外項目另付。中正本期未開放不能由這段取得exchange免學費資格；AUD1000 visa support scholarship明示排除exchange。", [q("costs", "3 units (36 credit points or 22.5 ECTS) is AU$9,900", year="QUT2027公開費率／付費StudyAbroad"), q("costs", "you won't need to pay any tuition fees.", year="QUT2027費用頁／partner提名Exchange免tuition條件")]),
    }
    manual["schools"].append({"ccu_page": 120, "host_fields": qhost})
    (B / "completion-manual-fields.json").write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n")
    print("Reviewed FGES 13 host fields, QUT 13 host fields and one FGES Vauban marker; all underlying attempts remain archived")


if __name__ == "__main__":
    main()
