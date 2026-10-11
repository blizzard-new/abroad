"""Reproduce the explicitly reviewed second CCU completion batch.

Only source passages and photographs reviewed by this task are approved here.
Receiving policies do not change the mother's not_open or blank quota statuses.
"""
from __future__ import annotations

import gzip
import json
import re
from datetime import UTC, datetime

from fetch_ccu_completion_sources import BUNDLE as B
from fetch_ccu_completion_sources import OUT
from pypdf import PdfReader


def read(name):
    return json.loads((B / name).read_text())


def receipt(page, label):
    record = read(f"completion_sources/p{page}-{label}.receipt.json")
    assert record["http_status"] == 200 and record["tls_verify"] and not record.get("error")
    return record


def response_text(record):
    path = B / record["bundled_file"]
    content = path.read_bytes()
    if path.suffix == ".gz":
        content = gzip.decompress(content)
    return content.decode(errors="replace")


def append_evidence(photo, ev):
    photo["evidence"] = [old for old in photo["evidence"] if old.get("source_id") != ev["source_id"]] + [ev]


def evidence(page, label, quote, *, pages=(), year="一般校園身份與來源，查核2026-10-11；不是個人接收校區分配"):
    record = receipt(page, label)
    return {"source_id": record["source_id"], "source_url": record["source_url"], "source_pages": list(pages),
            "excerpt": quote, "academic_year": year, "application_round": "2027春季接待參考；中正本期未開放" if page == 72 else "一般校園參考",
            "checked_at": record["checked_at"], "content_hash": record["sha256"], "status": "verified_current"}


def fact(value, ev, *, status="verified_current", reason="正文及適用年度已核對；接待規則不改變中正本期未開放身份。"):
    return {"status": status, "value": value, "reason": reason, "evidence": [{**item, "status": status} for item in ev]}


def main():
    partners = {row["source_pages"][0]: row for row in [json.loads(line) for line in (B / "partners.jsonl").read_text().splitlines()]}
    points = read("campus-coordinate-review.json")
    point_values = [
        (79, "Bhubaneswar", 20.3555462, 85.8161006, "followup-contact", "followup-official-map", "KIIT - Kalinga Institute of Industrial Technology", "!3d20.3555462!4d85.8161006", "官方Contact頁Patia地址連至此KIIT機構marker；不是@視窗值或KISS校區。"),
        (105, "Ankara（Ankara 主校）", 39.94273159999999, 32.8564133, "followup-contact-tr", "followup-official-map", "Social Sciences University of Ankara, Hacı Bayram, Ulus, Hükümet Meydani No:2", "[39.94273159999999,32.8564133]", "官方土耳其文İletişim頁所嵌地圖解析為Hükümet Meydani No:2校址marker；不採39.94340047942294／32.85319811498272視窗值，不套Northern Cyprus校區。"),
        (107, "Pardubice", 50.04816, 15.7693999, "campus_contact-1", "followup-google-map", "Univerzita Pardubice, Studentská 95, 532 10 Pardubice II", "[50.04816,15.7693999]", "官方Contacts頁嵌入的同一place ID地圖，正文marker為Studentská95；不採Mapy視窗或Google embed初始視窗座標。"),
    ]
    for page, city, latitude, longitude, primary_label, map_label, identity, marker, note in point_values:
        record = receipt(page, map_label)
        text = response_text(record)
        assert marker in text or marker in record["resolved_url"]
        assert identity in text or identity.replace(" ", "+") in record["resolved_url"]
        school = partners[page]
        ev = [evidence(page, primary_label, receipt(page, primary_label)["title"]), evidence(page, map_label, identity + " " + marker)]
        points["schools"][str(page)] = {"decision": "accepted", "field": fact({
            "school_name": school["school_name"], "country": school["country"], "city": city,
            "latitude": latitude, "longitude": longitude, "geocode_status": "verified", "geocoded_at": record["checked_at"],
            "source_url": record["source_url"], "identity_source_url": ev[0]["source_url"], "precision": "representative", "note": note,
        }, ev, reason=note)}
    (B / "campus-coordinate-review.json").write_text(json.dumps(points, ensure_ascii=False, indent=2) + "\n")

    photos = read("campus-photo-review.json")
    decisions = [
        (68, "followup-reviewed-campus", 48088400, "followup-photo-exact", "HCMUTE中央大樓校景，Commons作者Adoreplus、CC BY-SA4.0、2016-04-09。官方2025-12-26改名HCM-UTE與母校HCMUTE身份相同；舊照片不宣稱2027外觀。"),
        (77, "followup-reviewed-lab", 46251541, "followup-lab-exact", "Vel Tech University電子及塑膠廢棄物育成中心外觀，Commons作者Ghantajayaram、CC0、2015。官方大學首頁連至VelTechTBI，該頁列E-Waste & Plastic Waste設施；不是Vel Tech Multi Tech姊妹學院或人物活動照。"),
        (104, "followup-reviewed-campus", 197225656, "followup-commons-category", "FHNW Campus Brugg-Windisch共同校園主入口。官方校區頁正文Our schools明載School of Business；屬商學院所在的共同校區，非商學院專用建築。地圖代表點仍為Olten；照片不是Olten／Basel／Muttenz或個人分配證明。"),
    ]
    for page, artifact, pageid, label, note in decisions:
        photo_path = f"completion_sources/p{page}-{artifact}.json"
        photo = read(photo_path)
        if page == 68:
            append_evidence(photo, evidence(page, "followup-main", "Ngày 26/12/2025, Thủ tướng Chính phủ đã có Quyết định số 2809/QĐ-TTg", year="校名變更決定2025-12-26；不是2027外觀證明"))
        elif page == 77:
            quote = "E-Waste & Plastic Waste Recycling Facility"
            assert quote in (OUT / "p77-followup-tbi-official.txt").read_text()
            append_evidence(photo, evidence(page, "followup-tbi-official", quote))
            photo["campus_caption"] = "Vel Tech University電子／塑膠廢棄物技術育成中心外觀（Commons來源2015）；非主校門。"
        else:
            quote = "The School of Business, Computer Science and Information Technology, Education and Engineering and Environment"
            assert quote in (OUT / "p104-followup-brugg-business-campus.txt").read_text()
            append_evidence(photo, evidence(page, "followup-brugg-business-campus", quote))
            photo["campus_caption"] = "FHNW Campus Brugg-Windisch共同校園主入口；官方列School of Business在此校區。地圖為Olten代表點，照片不代表個人接收校區。"
        (B / photo_path).write_text(json.dumps(photo, ensure_ascii=False, indent=2) + "\n")
        prior = photos["selected"].get(str(page), {})
        reviewed_at = prior.get("visually_reviewed_at") if prior.get("reviewed_photo_record") == photo_path else datetime.now(UTC).isoformat()
        photos["selected"][str(page)] = {"source": "commons_alternatives", "metadata_label": label, "pageid": pageid, "artifact_label": artifact,
            "decision": "accepted", "reviewed_photo_record": photo_path, "visually_reviewed_at": reviewed_at,
            "campus_note": note, "identity_note": note, "visual_evidence_artifact": "Original Commons bytes viewed through view_image; source and campus content independently inspected"}
    photos["initial_exclusions"]["p77-followup-campus-vtu"] = "Campus-vtu.jpg標題雖稱校園，實際是多人擺拍且建築辨識不足；下載與原頁保留，未刊登。改核實E-waste-lab.jpg的實際校園建築外觀。"
    (B / "campus-photo-review.json").write_text(json.dumps(photos, ensure_ascii=False, indent=2) + "\n")

    manual = read("completion-manual-fields.json")
    manual["schools"] = [r for r in manual["schools"] if r["ccu_page"] != 72]
    source = receipt(72, "followup-factsheet-2026-2027")
    pages = [re.sub(r"\s+", " ", p.extract_text()) for p in PdfReader(B / source["bundled_file"]).pages]
    assert len(pages) == 5 and all("2026-2027" in p for p in pages)
    year = "接待校2026–2027學年Fact Sheet，Spring為2027；中正本期未開放參考"

    def pdf(page, quote):
        assert re.sub(r"\s+", " ", quote) in pages[page - 1], (page, quote)
        return evidence(72, "followup-factsheet-2026-2027", quote, pages=[page], year=year)

    def inbound(quote):
        assert quote in (OUT / "p72-followup-inbound.txt").read_text(), quote
        return evidence(72, "followup-inbound", quote, year="2026–2027當期Fact Sheet p3直接指定的Inbound文件／規定頁；頁面自身無年度標記")

    host = {
        "program_scope": fact("接待本科／雙聯、碩士及研究領域，訪問學生分MoU與Non-MoU；MoU接待依雙方有效協議。此接待校清單不表示中正本期可選。", [pdf(2, "Faculties offering exchange opportunities"), pdf(3, "Under Memorandum of Understanding (MoU) / Not under Memorandum of Understanding (Non MoU)")]),
        "eligibility": fact("須符合接待學程最低資格，滿足最低資格不保證錄取；MoU學生依雙方協議條款。未自行補GPA或年級門檻。", [pdf(3, "merely fulfilling the minimum eligibility criteria does not guarantee the selection")]),
        "language": fact("可提供英文授課證明或母校／英語教師／國家機構的高等教育英語能力證明；測驗選項iBT95且寫作20、IELTS總6.5且每項6、Duolingo115，成績通常2年內。官方另列legacy PBT／CBT數值，未換算新版考試。", [pdf(3, "For detailed information, kindly refer to: https://www.ir.iitb.ac.in/inbound-students"), inbound("The internet based test requires scores of at least 95 overall with a minimum score of 20 in writing.")]),
        "nomination_deadline": fact("2026–2027簡章指提名及申請文件寄Inbound Coordinator；未另列獨立提名日期，不能自行等同申請期限。", [pdf(3, "Nomination and application documents should be sent to Piyush Kumar")], status="needs_confirmation"),
        "application_deadline": fact("Spring2027課程交換：2026-09-30（簡章載每年9月30日）；Autumn課程：每年3月31日。Project申請全年受理但至少提前2個月，課程與研究計畫分開。", [pdf(3, "Spring Semester (Jan-Apr): 30 Sept (every year)"), pdf(3, "at least 2 months prior to the expected date")]),
        "documents": fact("11項初申要求：申請表、Foreign Scholars個人資料、CV、成績單及必要英文認證翻譯、SOP、Study／Project Plan、母校在學及同意證明（MoU提名須明載）、2封教師推薦信、英文能力證明、護照個人頁、自負費用承諾。Host Bonafide/FRRO表為到校後用途，與母校初申證明不同。", [pdf(3, "For detailed information, kindly refer to: https://www.ir.iitb.ac.in/inbound-students"), inbound("Two recommendation letters from the faculty members.")]),
        "application_forms": fact("已取得當期簡章所連Inbound頁的Visiting Students Application（3頁）、Personal Particulars（DOC）及Host Bonafide／FRRO（1頁，到校後）。表內學年留白、未標版本日期；active官網鏈結已核，最新表格版本日期仍無法独立核實。", [pdf(3, "For detailed information, kindly refer to: https://www.ir.iitb.ac.in/inbound-students"), evidence(72, "followup-form-1", "Academic year", pages=[1], year="表內學年留白；2026–2027簡章所連現行官網附件"), evidence(72, "followup-form-2", "PERSONAL PARTICULARS OF FOREIGN SCHOLARS COMING TO INDIA", year="DOC無年度標記；antiword正文解析"), evidence(72, "followup-form-3", "I require a Bonafide Certificate from IIT Bombay for my residence registration at the F.R.R.O.", pages=[1], year="到校後FRRO證明表；學年留白")], status="needs_confirmation"),
        "academic_calendar": fact("Spring2027：term為1月第1週至4月最後1週，orientation為1月第1週、課程至4月中、考試4月中末；精確日曆另依官方Academic Calendar，不自行產生日期。", [pdf(2, "1st week of January to last week of April")]),
        "course_restrictions": fact("每學期最少15、最多40 credits；建議交換15–30（通常3–5門）。申請時列偏好課程，抵達後人工註冊；不是所有院系、課程或容量已保證開放。", [pdf(3, "Minimum no. of credits to be taken in a semester – 15 credits"), pdf(3, "Maximum no. of credits to be taken in a semester – 40 credits")]),
        "housing": fact("到校後依床位可用性提供校內住宿；不是事前保證床位或特定宿舍。", [pdf(4, "Exchange students will be provided on-campus accommodation upon their arrival as per availability")]),
        "housing_deadline": fact("2026–2027簡章明示住宿依到校時可用性，但未列住宿申請獨立期限；尚未核實，不宣稱官方已明示尚未公告。", [pdf(4, "as per availability")], status="needs_confirmation"),
        "costs": fact("MoU與Non-MoU均需INR15,000／學期行政費、INR7,000／月住宿費；其他費用另見Inbound頁。此為2026–2027公布費率，未估整體生活費或保证未来费率。", [pdf(4, "INR 15,000 (Administration charge/semester)"), pdf(4, "INR 7,000 (Hostel charge/month)")]),
        "insurance": fact("交換生在校院醫院僅享Outpatient Department，抵達前須自備涵蓋疾病及意外的個人保險。", [pdf(4, "should obtain a personal insurance policy, covering sickness and accidents prior to arrival")]),
        "visa": fact("交換／訪問學生須辦Student Visa。當期Spring2026–2027首頁另明示Study in India註冊及提交為mandatory，SII-ID用於e-Student流程；未代學生提交或斷言個別簽證可獲核准。", [pdf(4, "students must apply for a “Student Visa”"), evidence(72, "followup-ir-home", "Registration and Submission on 'Study in India' portal is mandatory.", year="首頁正文2026–27 Spring semester Ph.D. & Exchange Applicants")]),
        "arrival": fact("欲使用IRO到校支援，提前2週通知抵達日期時間；支援包括機場接送、宿舍、FRRO、buddy等，未宣稱所有服務免費。", [pdf(5, "inform the Office of International Relations of your arrival date/time two weeks in advance")]),
        "host_tuition": fact("有效MoU類別的course/project fees免收；Non-MoU課程INR5,000／credit、project INR10,000／月。行政與住宿費仍需另付；中正本期未開放不能因此取得免學費資格。", [pdf(4, "Course work / Project work fees under MoU category"), pdf(4, "No Fees"), pdf(4, "Course work fees under non MoU category INR 5,000 per credit")]),
        "exchange_duration": fact("課程交換1學期，最多2學期；project work未設同樣期間上限，仍須依接待與有效MoU規定。", [pdf(3, "one semester or spend up to a maximum of two semesters")]),
    }
    website = fact("https://www.ir.iitb.ac.in/", [pdf(1, "Student Exchange Contact www.ir.iitb.ac.in"), evidence(72, "followup-ir-home", "Home | IIT International Relations - IIT Bombay")], reason="IIT Bombay官方國際處正文及2026–2027 Fact Sheet同時核實網站身份；主站503與國際處可讀分開保存。")
    location = fact("Room416，4th Floor，Rahul Bajaj Technology Innovation Center，Powai，Mumbai400076，India", [pdf(1, "Room 416, 4th Floor, Rahul Bajaj Technology Innovation Center, Powai")], reason="當期官方接待聯絡地址；不是宿舍或個人授課樓分配。")
    levels = fact("undergraduate／postgraduate；exchange列bachelor／double degree、master、research，個別學程須核資格。", [pdf(1, "IIT B provides undergraduate and postgraduate programs"), pdf(2, "master and research")], reason="接待校公開學制範圍，未擴大成全部博士／專業學程。")
    manual["schools"].append({"ccu_page": 72, "host_fields": host, "general_campus_fields": {"website": website, "location": location, "degree_levels": levels}, "profile_fields": {"website": website, "location": location, "degree_levels": levels}})
    (B / "completion-manual-fields.json").write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n")
    print("Approved 3 points, 3 photographs and reviewed all 17 IIT Bombay receiving fields; mother status unchanged")


if __name__ == "__main__":
    main()
