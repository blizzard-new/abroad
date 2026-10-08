"""Build reviewed TKU programme records offline from bundled official evidence.

The four Japanese round-2 rows were reviewed against the rendered PDF. Historical
XLSX/DOCX rows preserve their native cells. This never promotes a new year or a
sister-school agreement into a current application choice.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.tku_data import BUNDLE, CHECKED_AT, TKUEvidence, TKUFact, TKUPartnerRecord, load_tku_sources, tku_integrity_report
from exchange_info.models import UniversityApplicationWorkflow, ApplicationStep, DestinationProfile, SourceReference
from exchange_info.workflow_structuring import structure_application_workflow, workflow_structure_issues
from exchange_info.tku_host_data import enrich_current, host_documents, document_requirement
from exchange_info.tku_life import build_tku_destination

SOURCES = {s["id"]: s for s in load_tku_sources()}
JP = "jp-2027-2028-round-2"
JP_YEAR = "2027-2028"
JP_ROUND = "日語組第二次甄選"
JP_GUIDE = "jp-revision-attachment-1"
JP_LIST = "jp-revision-attachment-2"
DOCUMENTS = ["申請表：線上填寫後列印，申請人及系主任親筆簽名", "本校中文歷年成績單正本；碩一另附大學四年成績單", "語文證明影本或網路成績列表，面試攜原本驗核", "授課老師推薦函一封（中文或日文）", "中文及日文自傳", "中文及日文研習計畫", "切結書（附件2，PDF第14頁）", "其他有助審查資料（有則附）"]


def fact(value, source_id, locator, year, round_name, *, status="verified", quote=""):
    source = SOURCES[source_id]
    return TKUFact(value=value, status=status, evidence=[TKUEvidence(
        source_id=source_id, source_url=source["source_url"], locator=locator,
        applicable_year=year, application_round=round_name,
        role=source["role"], checked_at=CHECKED_AT, quote=quote)])


def jp_fact(value, source=JP_LIST, locator="PDF p.1", **kwargs):
    year = SOURCES[source]["applicable_year"] if SOURCES[source]["role"] == "host_incoming" else JP_YEAR
    return fact(value, source, locator, year, JP_ROUND, **kwargs)


def current_rows():
    seeds = [
        ("ritsumeikan", "立命館大學 Ritsumeikan University", 1, "日文", "大學部、研究所（碩）", "JLPT N1；GPA 3.0以上；在母校至少讀過一學年", "https://en.ritsumei.ac.jp/skp/"),
        ("nagasaki", "長崎外國語大學 Nagasaki University of Foreign Studies", 2, "日文", "大學部、研究所（碩）", None, None),
        ("seikei", "成蹊大學 Seikei University", 1, "日文", "大學部、研究所（碩）", "GPA 2.5以上；在母校至少讀過一學期", "https://www.seikei.ac.jp/gakuen/siis/intl/incoming.html"),
        ("uec", "電氣通信大學 University of Electro-Communications", 3, "英文", None, "JUSST；學業平均80分；GPA3.0以上；表列英語iBT67以上及IELTS6.0以上（與外校可選語言證明規定差異待確認）", "https://www.fedu.uec.ac.jp/en/future_students/jusst/"),
    ]
    pdf = SOURCES[JP_LIST]["pages"][0]["text"]
    for index, (slug, name, quota, language, degree, host_rules, website) in enumerate(seeds, 1):
        assert name.split(" ")[0].replace("長", "⾧") in pdf or name.split(" ")[0] in pdf
        loc = f"PDF p.1 row {index}"
        fields = {
            "school_name": jp_fact(name, locator=loc), "country": jp_fact("日本", JP_GUIDE, "PDF p.1 title"),
            "website": jp_fact(website, locator=loc, status="verified" if website else "needs_confirmation"),
            "degree_levels": jp_fact(degree, locator=loc, status="verified" if degree else "missing_in_source"),
            "department_scope": jp_fact("電機系(所)、資工系(所)學生優先" if slug == "uec" else None, locator=loc,
                                        status="verified" if slug == "uec" else "missing_in_source"),
            "campus": jp_fact(None, locator=loc, status="missing_in_source"),
            "language": jp_fact(language, locator=loc), "quota": jp_fact(str(quota), locator=loc),
            "home_eligibility": jp_fact("本校大三、研究所一二年級；學業總平均75分以上；系所院推薦。附錄Q&A另載前40%替代條件，尚待確認是否適用本次。", JP_GUIDE, "PDF p.2 壹一; p.18 Q&A5", status="needs_confirmation"),
            "host_eligibility": jp_fact(host_rules, locator=loc, status="verified" if host_rules else "missing_in_source"),
            "home_deadline": jp_fact("2026-09-30T12:00:00+08:00", "jp-revision", "更正公告說明二"),
            "department_deadline": jp_fact(None, JP_GUIDE, "PDF p.3 貳二（一）各系所規定收件截止時間", status="missing_in_source"),
            "department_to_oicsa_deadline": jp_fact(None, "jp-revision", "更正公告未明示新的系所送國際處截止時間；原公告仍寫9/17", status="needs_confirmation"),
            "host_deadline": jp_fact(None, JP_GUIDE, "PDF p.6/p.7; no partner-specific exact dates", status="missing_in_source"),
            "study_period": jp_fact("2027.4–2028.3（一學年，實際依外校行事曆）", locator="PDF p.1 header; guide p.5 肆"),
            "documents": jp_fact("；".join(DOCUMENTS) + "。A4單面、不超過16頁、不裝訂、L型塑膠套；最多5個志願。", JP_GUIDE, "PDF p.3–4 貳二、三"),
            "housing": jp_fact("淡江及外校均不保證校內宿舍；須自行申請，未獲宿舍者自行安排外宿。", JP_GUIDE, "PDF p.9 玖七（三）"),
            "costs": jp_fact("交換期間繳淡江全額學雜費；外校主要學雜費免繳，可能有其他雜費；個人支出自付。", JP_GUIDE, "PDF p.8 玖五"),
            "course_restrictions": jp_fact("須自行確認適合系所及課程；學分採認依系所，不能保證全數抵免；不能要求變更外校核定校區、院系、學期。", JP_GUIDE, "PDF p.4–5 參二; p.9 玖六、七"),
            "scholarships": jp_fact(None, locator=loc, status="missing_in_source"),
        }
        # Retain home costs even when a verified host schedule supplies separate fees.
        fields["home_costs"] = fields["costs"].model_copy(deep=True)
        conflicts = ["jp-academic-rank-alternative", "jp-stale-dates", "jp-departure-before-start"]
        if slug == "ritsumeikan":
            fields["host_deadline"] = jp_fact("2027春季SKP：2026/11/2 09:00 JST截止（已獲淡江推薦者；10/2 10:00 JST開始）", "ritsumeikan-2027-guide", "PDF p.2 Schedule")
            fields["costs"] = jp_fact("2027春季起所有SKP學生（含交換生）繳JPY50,000 Student Support Fee；錄取後兩週內一次付清。自費生學費規定不當作淡江互惠交換生學費。", "ritsumeikan-2027-guide", "PDF p.4 Changes / Student Support Fee")
            fields["housing"] = jp_fact("SKP一般住宿頁：可申請I-House；依選定校區分配，不保證；私人租屋需自理押金、禮金、保證人等。2027床位與費率仍須確認。", "ritsumeikan-housing", "Accommodations / International Houses / Private Apartments", status="reference_only")
            fields["course_restrictions"] = jp_fact("必須先選study track及校區，核對可選學院及研究所；不能在申請後延長交換期間。", "ritsumeikan-2027-guide", "PDF p.3–7")
            fields["scholarships"] = jp_fact("RUSSES於2026秋季結束，2027春季起不再提供；JASSO須計畫獲資助及甄選，不能保證。", "ritsumeikan-2027-guide", "PDF p.4 Changes / Scholarships")
            fields["documents"] = jp_fact("；".join(DOCUMENTS) + "。外校另須線上SKP申請、各項證明及獨立COE程序；個人聲明、財務、健康、住宿意向依2027春季簡章清單。", "ritsumeikan-2027-guide", "PDF p.14–22; TKU documents guide p.3–4")
            fields["documents"].evidence.append(jp_fact("", JP_GUIDE, "PDF p.3–4").evidence[0])
        elif slug == "nagasaki":
            fields["website"] = jp_fact(None, locator=loc + "; printed URL points to jiu.ac.jp (Josai), not Nagasaki", status="needs_confirmation")
            conflicts.append("nagasaki-wrong-url")
        elif slug == "seikei":
            fields["host_deadline"] = jp_fact("2027春季：提名10/1；申請10/15；文件由母校交換承辦人寄送（未載時刻）", "seikei-2027-sheet", "PDF p.1–2 Application Deadlines and Procedures")
            fields["housing"] = jp_fact("至2027/8可住Dormy井之頭或國際交流會館；2027/9起校內住宿學生搬入International College MICHI，床位由外校安排。", "seikei-2027-sheet", "PDF p.3–4 Accommodation")
            fields["costs"] = jp_fact("2027/8前Dormy租金JPY93,000/月（含餐水電等）、押金93,000、寢具19,800/學期；會館93,000/月不含餐水電、押金93,000、寢具14,850/學期。2027/9起MICHI120,000/月（含餐寢具水電網路）、無押金；不可把前期價套全學年。", "seikei-2027-sheet", "PDF p.3–4 Fees")
            fields["course_restrictions"] = jp_fact("日語課為主，專業課須教師同意且不保證；學士課須N1程度，每學期至少6門課；體育、師資培育及部分限額課不開放。", "seikei-2027-sheet", "PDF p.2 Course information")
            fields["scholarships"] = jp_fact("校獎學金JPY40,000/月或深谷獎學金60,000/月，至多10月，名額及其他獎助限制依外校，不能保證。", "seikei-2027-sheet", "PDF p.5 Scholarships")
            fields["host_eligibility"].evidence.append(jp_fact("", "seikei-2027-sheet", "PDF p.1 Admission requirements").evidence[0])
        elif slug == "uec":
            fields["host_deadline"] = jp_fact("April入學：October31（一般規定，未核實2027專屬期限與時刻，須透過母校）", "uec-application", "Application / Schedule (updated 2025-10-28)", status="reference_only")
            fields["housing"] = jp_fact("JUSST一般網頁稱提供校內住宿，約JPY25,000（原頁未明示计費單位），不含水電且可變動；2027費率及床位仍需確認。", "uec-costs", "Living and Housing Information (updated 2025-09-25)", status="reference_only")
            fields["costs"] = jp_fact("JUSST一般規定合作校正式全職在學者免學費、無行政及設施費；指定保險約JPY26,000（可能年度調整），另須國民健康保險；未核實2027專屬價目。", "uec-costs", "Tuition Fees / Student Administration Fee and Insurance", status="reference_only")
            fields["course_restrictions"] = jp_fact("JUSST限資訊、科學、工程領域；入學時學士三四年級或研究生；畢業年級須母校證明交換結束後仍在學。TKU的電機／資工為優先，不能推成排他限制。", "uec-application", "Eligible Applicants / Student Status Conditions", status="reference_only")
            fields["documents"] = jp_fact("；".join(DOCUMENTS) + "。外校一般頁另列Form A/H/SP/RP、照片、成績單、護照、學生證、兩段3分鐘影片及條件式財務等文件；须透過母校送件，2027版表單未核實。", "uec-application", "Application Forms and Documents", status="reference_only")
            fields["documents"].evidence.append(jp_fact("", JP_GUIDE, "PDF p.3–4").evidence[0])
            conflicts.append("uec-language-conjunction")
        # The home document fact must contain ONLY the current TKU submission.
        fields['documents'] = jp_fact('；'.join(DOCUMENTS) + '。A4單面、不超過16頁、不裝訂、L型塑膠套；最多5個志願。', JP_GUIDE, 'PDF p.3–4 貳二、三')
        yield enrich_current(TKUPartnerRecord(id=f"{JP}-{slug}", round_id=JP, academic_year=JP_YEAR,
                               application_round=JP_ROUND, selection_status="listed", quota_status="numeric",
                               quota_number=quota, fields=fields, conflicts=conflicts))


def quota_state(raw):
    if raw is None or not raw.strip(): return "blank", None
    if re.fullmatch(r"\d+", raw.strip()): return ("zero" if int(raw) == 0 else "numeric"), int(raw)
    return "provisional", None


def reference_row(name, country, degree, language, quota, requirements, restrictions, source, locator, round_id, round_name, course_url=None):
    year = "115 (2026-2027)"
    def f(v, field, **kwargs):
        return fact(v, source, locator + "; " + field, year, round_name,
                    status=kwargs.pop("status", "reference_only" if v is not None else "missing_in_source"), **kwargs)
    english = round_id == "english-european-115"
    guide = "english-115-attachment-1" if english else "mainland-115-attachment-4"
    fields = {"school_name": f(name, "school"), "country": f(country, "country"),
              "degree_levels": f(degree, "degree"), "language": f(language, "language"),
              "quota": f(quota, "quota"), "host_eligibility": f(requirements, "requirements", quote=requirements or ""),
              "course_restrictions": f(restrictions, "remarks", quote=restrictions or ""),
              "website": f(None, "institution identity not separately verified"),
              "course_information_url": f(course_url, "course information URL in column I"),
              "department_scope": f(None, "see remarks for restrictions"), "campus": f(None, "not given")}
    fields["home_eligibility"] = fact("75分以上或系百分比前40%；二三年級及研究生，具體學制、排除條件依該語組舊期簡章", guide, "壹 申請資格", year, round_name, status="reference_only")
    fields["home_deadline"] = fact("2025-11-26T17:00:00+08:00" if english else "2026-03-02T17:00:00+08:00", guide, "貳 申請日期", year, round_name, status="reference_only")
    fields["study_period"] = fact("二年級申請者三年級出國一學年；三年級與碩士可秋季一學期或一學年" if english else "2026秋季或2027春季一學期；大三申請者僅大四上；澳門大學2027春季（與名額表114-2字樣矛盾）", guide, "肆 姊妹校交換期間", year, round_name, status="reference_only")
    for field,loc in [("documents","貳二 申請應繳文件"),("housing","其他注意事項 宿舍"),("costs","註冊繳費")]:
        value = {"documents":"依115簡章與其附件；舊版僅參考，不能作新版應繳文件。", "housing":"兩校不保證校內住宿，須自行申請；未核實新版。", "costs":"互惠交換繳淡江全額學雜費、外校主要學雜費免繳；個人支出自付；未核實新版。"}[field]
        fields[field] = fact(value, guide, loc, year, round_name, status="reference_only")
    fields["host_deadline"] = f(None, "no specific partner deadline")
    state, number = quota_state(quota)
    digest = hashlib.sha256((round_id + locator + name).encode()).hexdigest()[:12]
    conflicts = ["mainland-school-count"] if not english else []
    if name == "澳門大學": conflicts.append("macau-wrong-semester")
    return TKUPartnerRecord(id=f"{round_id}-{digest}", round_id=round_id, academic_year=year,
                            application_round=round_name, selection_status="reference_only", quota_status=state,
                            quota_number=number, fields=fields, conflicts=conflicts)


def reference_rows():
    src = SOURCES["english-115-partners"]
    for sheet in src["sheets"]:
        country_by_row = {}
        for merge in sheet.get("merged_cells", []):
            match = re.fullmatch(r"B(\d+):B(\d+)", merge)
            if match:
                start,end = map(int,match.groups())
                country = next((r.get(f"B{start}") for r in sheet["rows"] if r.get(f"B{start}")),None)
                country_by_row.update({r:country for r in range(start,end+1)})
        for cells in sheet["rows"]:
            row = {re.sub(r"\d", "", k): v for k,v in cells.items()}
            if not row.get("A", "").isdigit() or not row.get("C"): continue
            index = int(next(re.search(r"\d+", k).group() for k in cells))
            country = row.get("B") or country_by_row.get(index)
            country = country.split("\n")[0] if country else None
            # These two cells are unmerged blanks, but C12/C13 explicitly say 德國.
            # Extract the official name's literal prefix, never fill an unmerged blank by adjacency.
            if country is None and row["C"].startswith("德國"):
                country = "德國"
            yield reference_row(row["C"].replace("\n", " "),country,row.get("F"),row.get("E"),row.get("D"),row.get("G"),row.get("H"),
                                "english-115-partners",f"XLSX sheet '{sheet['name']}' row {index} (B:I; merged B ranges preserved)","english-european-115",sheet["name"] + "第一輪（舊期參考）",row.get("I"))
    table = SOURCES["mainland-115-attachment-1"]["tables"][0]
    for index,cells in enumerate(table[1:],2):
        if cells[0].startswith("合計"):continue
        name,quota,language,degree,remarks = cells
        country = "澳門" if "澳門" in name else "臺灣" if "金門" in name else "大陸地區"
        yield reference_row(name,country,degree,language,quota,None,remarks or None,"mainland-115-attachment-1",f"DOCX table 1 row {index}","mainland-macau-kinmen-115","中文組聯合甄選（舊期參考）")


def main():
    current = list(current_rows()); references = list(reference_rows())
    for filename, rows in [("partners_current.jsonl",current),("partners_reference.jsonl",references)]:
        (BUNDLE/filename).write_text("".join(row.model_dump_json() + "\n" for row in rows),encoding="utf-8")
    build_platform_data(current)
    from exchange_info.tku_completeness import write_tku_completeness_matrix
    write_tku_completeness_matrix(current + references)
    report = tku_integrity_report()
    (BUNDLE / "integrity.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False))
    if report["issues"]:raise SystemExit(1)


def build_platform_data(current):
    rounds = [
        {"id":JP,"title":"2027–2028日語第二次甄選（已截止）", "academic_year":JP_YEAR,"application_round":JP_ROUND,
         "source_id":"jp-revision","opens_at":"2026-09-23T09:00:00+08:00","deadline_at":"2026-09-30T12:00:00+08:00",
         "status_note":"更正公告為準；校內申請已截止，外校仍在辦理不代表校內重開。", "details":[
             "以9/16更正公告及其更新附件為準，4校7名；PDF p.3日期已修正，但流程圖p.6仍是9/17。",
             "各系所紙本截止可較早；新系所送國際處期限未明示，不能沿用原9/17 17:00。",
             "交換名額表寫2027.4–2028.3，簡章p.7又寫2027/3/31前出國，入境與課程開始關係須承辦確認。"]},
        {"id":"english-european-115","title":"115英歐語組舊期參考；2027–2028新版尚未核實", "academic_year":"115","application_round":"英歐語组第一輪（參考）",
         "source_id":"english-115","opens_at":None,"deadline_at":None,
         "status_note":"非本期申請文件，未核實新版不等於官方明示尚未公告。", "details":[
             "已核對2026–2027 DOCX內文與XLSX三分頁：英語70、法德10、西俄9，合計89計畫列。",
             "舊期申請2025/11/12 09:00至11/26 17:00；系所11/27 17:00送國際處；第二輪只開給第一輪未獲分發者，2025/12/24 17:00截止。",
             "學業75分或系前40%；二三年級、碩士（不含在職專班）；英語iBT70或學術IELTS5.5；各校可加嚴。",
             "已查官網首頁、完整公告索引及赴外頁，新版尚未核實；不能將Q&A一般時段變成新年度截止日。"]},
        {"id":"mainland-macau-kinmen-115","title":"115中文聯合甄選舊期參考；新版尚未核實", "academic_year":"115","application_round":"大陸／澳門／金門聯合甄選（參考）",
         "source_id":"mainland-115","opens_at":None,"deadline_at":None,
         "status_note":"校內甄選已截止；2027春季尚未出發不代表可新增申請。", "details":[
             "內文115學年度2026秋季或2027春季；系前40%或平均75；二三年級及研究所依外校規定。",
             "舊期系統2026/2/23 08:00至3/2 17:00；系所3/3 17:00送國際處；最多5志願；大三只可大四上出國。",
             "原表35校列、118名；合計文字寫大陸32（含澳門2）加臺灣1，與明細數量有疑點，逐列保存不刪除。",
             "澳門大學名額表写114-2，簡章正文明确115-2（2027春季），留待確認；國籍、專業、年級限制逐校保存。"]},
    ]
    conflicts = [
        ("jp-stale-dates",["jp-original","jp-revision",JP_GUIDE],"更正公告9/23 09:00–9/30 12:00；PDF p.3星期誤植，p.6流程仍9/17，p.3修正作業有2025日期，p.15修正表9/17；系所送件新截止未明示。","學生申請採更正公告；修改與系所送件期限待承辦確認。"),
        ("jp-academic-rank-alternative",[JP_GUIDE],"p.2正文總平均75；p.18 Q&A5為75或系前40%。","正文75保留，系前40%不能自動判通過；待確認本次適用範圍。"),
        ("jp-departure-before-start",[JP_GUIDE,JP_LIST],"p.7出國/取得入學許可限2027/3/31前；名額表2027.4–2028.3。","可能提前抵達，不能自行判為錯字；確認入境及錄取效力期限。"),
        ("nagasaki-wrong-url",[JP_LIST,'nagasaki-partners','nagasaki-nics-2027'],"p.1長崎外國語大學列https://www.jiu.ac.jp/lsc/abroad/detail/id=4537，為城西國際大學網域。","保留母校表誤連問題；已核實長崎官方合作名單列淡江及2027 NICS頁，NICS本輪提名對應仍待確認。"),
        ("uec-language-conjunction",[JP_LIST,"uec-application",JP_GUIDE],"TKU名額表iBT67及IELTS6.0、80分且GPA3.0；外校一般頁英語equivalent test scores、學業one of。正文研究所N1，英語課豁免只明示大學部。","各角色分開保存；不得自行把TKU及改成或；研究所英語課N1豁免待確認。"),
        ("mainland-school-count",["mainland-115-attachment-1"],"DOCX明細35列、名額相加118；合計說大陸32校含澳門2校及台灣1校，若按文字應33。","保存35明細；與承辦核對總數文字，不能為總數刪列。"),
        ("macau-wrong-semester",["mainland-115-attachment-1","mainland-115-attachment-4"],"表澳門大學114-2；簡章首頁及肆二115-2/2027春季。","標為舊期參考且保留原文，不選定其中一值作當期申請依據。"),
        ('nagasaki-photo-count',['nagasaki-nics-2027','nagasaki-form-a-guide'],'2027公告提出書類3說照片3張；目前直接連結的出願指南p.1說無法上傳NICS照片者2張。','數量不猜；照片上傳可免紙本，未上傳者確認張數。'),
        ('nagasaki-essay-translation',['nagasaki-nics-2027','nagasaki-form-b'],'公告要求日文Form B；DOCX日文為500–1,000字，英文為500–1,000 words且允許英日文。','依日語NICS公告保留日文規則，英譯差異待外校確認。'),
        ('nagasaki-study-period',[JP_LIST,'nagasaki-pledge','nagasaki-form-a-online'],'淡江表2027/4–2028/3；2027 Form A及誓約書全年選項為2027/3–2028/2。','保留兩方期間；確定實際提名、抵達、結束及返校日後辦理。'),
        ('nagasaki-programme-mapping',[JP_LIST,'nagasaki-partners','nagasaki-nics-2027'],'淡江列長崎及日語；長崎合作目錄列淡江，2027 NICS收合作校，但淡江本輪表未寫NICS。','NICS資訊依計畫範圍展示，最終提名track及研究所課程適用需承辦確認。'),
        ('ritsumeikan-budget-insurance',['ritsumeikan-2027-guide','ritsumeikan-fees'],'2027簡章p.4支援費含Gakkensai/Gakkenbai；一般生活預算另列academic/liability insurance，未明示預算年度。','保留一般預算供參考，確認保險重複及當期費用後才合計。'),
        ('uec-form-a-fall-label',['uec-jusst_form_A-rev9-pdf','uec-application-recheck'],'一般Form A p.8 Fall Semester Entry Process標題下寫April entry in Spring，p.1與官方一般頁為October入學4/30、April入學10/31。','記錄原文標籤矛盾；不以舊表錯標作2027精確期限，2027版待確認。'),
    ]
    (BUNDLE/"rounds.json").write_text(json.dumps(rounds,ensure_ascii=False,indent=2)+"\n")
    conflict_rows=[]
    for id,sources,basis,resolution in conflicts:
        conflict_rows.append({"id":id,"status":"needs_confirmation","basis":basis,"handling":resolution,
                              "source_urls":[SOURCES[s]["source_url"] for s in sources],"source_ids":sources,"checked_at":CHECKED_AT.isoformat()})
    (BUNDLE/"conflicts.json").write_text(json.dumps(conflict_rows,ensure_ascii=False,indent=2)+"\n")
    workflows=[];destinations=[];host_catalog=[]
    for record in current:
        fields=record.fields;name=str(fields["school_name"].value)
        slug=record.id.rsplit('-',1)[-1]
        host_items=host_documents(slug)
        host_catalog.append(dict(partner_id=record.id,school_name=name,home_academic_year=JP_YEAR,
            checked_at=CHECKED_AT.isoformat(),programme_mapping=fields['host_programme_mapping'].model_dump(mode='json'),documents=host_items))
        source_ids=list(dict.fromkeys(e.source_id for f in fields.values() for e in f.evidence))
        scope={"home_universities":["淡江大學"],"partner_universities":[name],"academic_years":[JP_YEAR],"application_rounds":[JP_ROUND]}
        specs=[
            ("確認校級計畫與甄選資格","資格確認","學生／所屬系所",[str(fields["home_eligibility"].value),str(fields["host_eligibility"].value or "外校特別資格未明示，須確認"),"校內已截止；以下供已獲推薦者查核及流程參考。"],[],None,JP_GUIDE,"needs_confirmation"),
            ("完成線上申請並列印簽名、送系所推薦","校內申請","學生／系所／學院",[str(fields["documents"].value),"校內9/30 12:00截止，系所另有較早期限；新系所送國際處截止未核實。"],DOCUMENTS,None,JP_GUIDE,"verified"),
            ("参加面試與確認校內推薦結果","校內甄選","國際處",["日語二甄以書審及面試合併計算；甄試70分為錄取標準，並非學業平均。時間個別Email通知。"],[],None,JP_GUIDE,"verified"),
            ("獲母校推薦後完成外校申請","外校申請","學生／國際處／外校",[str(fields["host_deadline"].value or "外校當期截止、送件方式尚未核實"),"母校錄取只是推薦，外校仍須審核。"],[],None,fields["host_deadline"].evidence[0].source_id,"needs_confirmation"),
            ("確認住宿、費用、保險與學分採認","行前","學生／系所／外校",[str(fields["housing"].value),str(fields["costs"].value),str(fields["course_restrictions"].value)],[],None,fields["housing"].evidence[0].source_id,"needs_confirmation"),
            ("按時返校並繳交換心得、辦理學分採認","返國","學生／系所／國際處",["返國一個月內送心得至國際處；學分採認依系所規定，不保證全數抵免。"],[],None,JP_GUIDE,"verified"),
        ]
        steps=[]
        for order,(title,phase,responsible,details,documents,deadline,source_id,support) in enumerate(specs,1):
            requirements=[]
            for index,doc in enumerate(documents):
                requirements.append({"name":doc,"copies":1 if index==3 else None,
                                     "copy_type":"original" if index in [0,1,3] else "copy" if index==2 else "unspecified",
                                     "signatures":["申請人","系主任"] if index==0 else ["申請人","家長（監護人）"] if index==6 else [],
                                     "official_form_url":SOURCES[JP_GUIDE]["source_url"]+"#page=14" if index==6 else None,
                                     "source_urls":[SOURCES[JP_GUIDE]["source_url"]],
                                     "stage":"student_application", "conditional":index==7,
                                     "condition":"有則附" if index==7 else "所有申請人；碩一另附大學四年成績單" if index==1 else "所有申請人",
                                     "official_form_verified":index==6,
                                     "applicability_status":"verified_current", "applicability_year":JP_YEAR,
                                     "applicability_note":"母校outbound；簡章PDF p.3–4（切結書p.14）；校內已截止，僅供流程與既有提名者準備查核。"})
            if order in [4,5]:
                selected=[item for item in host_items if item['step_order']==order]
                requirements=[document_requirement(item) for item in selected]
                documents=[r['name'] for r in requirements]
                details += [f"{item['name']}；適用：{item['condition']}；{item['applicable_year']}／{item['evidence']['locator']}；表單取得：{item['form_access']}" for item in selected]
                details += [str(fields[k].value or fields[k].reason) for k in
                    (['host_nomination_deadline','host_programme_mapping','latest_forms'] if order==4 else ['insurance','visa_residence','arrival_preparation','housing_application_deadline'])]
            extra={}
            if order==2:
                extra=dict(deadline_at='2026-09-30T12:00:00+08:00',deadline_status='verified_exact',
                    deadline_source_url=SOURCES['jp-revision']['source_url'],deadline_checked_at=CHECKED_AT)
            elif order==4 and slug=='ritsumeikan':
                extra=dict(deadline_at='2026-11-02T09:00:00+09:00',deadline_status='verified_exact',
                    deadline_source_url=SOURCES['ritsumeikan-2027-guide']['source_url']+'#page=2',deadline_checked_at=CHECKED_AT)
            else:extra=dict(deadline_status='reference_only' if slug=='uec' else 'needs_confirmation')
            if order==4:
                details.append({'ritsumeikan':'提名核准後取得SKP帳號，線上填寫並上傳文件；COE另依行政書士通知。',
                    'nagasaki':'NICS Form A必須線上填寫，其他文件依公告寄送；10/31以消印為準，先確認本輪提名track。',
                    'seikei':'所有文件由母校交換承辦Email送成蹊；COE線上表及財力文件細節另提供提名學生。',
                    'uec':'一般規定只接受母校IAO直接送件；一般Form A要求列印親簽後註冊快遞，2027程序待確認。'}[slug])
            form_urls=list(dict.fromkeys(r['official_form_url'] for r in requirements if r.get('official_form_url')))
            step_urls=list(dict.fromkeys([SOURCES[source_id]['source_url']]+[u for r in requirements for u in r['source_urls']]))
            submission={'method':'mixed' if order==2 else 'unknown',
                'portal_url':'https://exchange.web.tku.edu.tw/' if order==2 else None}
            action_url='https://exchange.web.tku.edu.tw/' if order==2 else None
            if order==4:
                submission.update(method={'ritsumeikan':'online','nagasaki':'mixed','seikei':'mixed','uec':'paper'}[slug],
                    office='母校交換承辦／外校國際處',deadline_note=str(fields['host_deadline'].value))
                if slug=='ritsumeikan':
                    action_url=SOURCES['ritsumeikan-howto-2027']['source_url']
                    submission['deadline_note']+='；正式申請連結與帳號提名核准後寄送。'
                elif slug=='nagasaki':
                    action_url=SOURCES['nagasaki-form-a-online']['source_url']
                    submission['portal_url']=action_url
                else:action_url=SOURCES[source_id]['source_url']
            steps.append(ApplicationStep(order=order,phase=phase,title=title,responsible_party=responsible,
                responsible_unit=responsible,summary=details[0],details=details,required_documents=documents,
                document_requirements=requirements,official_form_urls=form_urls,scope=scope,source_urls=step_urls,
                checked_at=CHECKED_AT,deadline_reminder_eligible=False,**extra,
                action_url=action_url,submission=submission,
                support_status=support,needs_confirmation=support=="needs_confirmation",
                confirmation_contact="淡江國際處交流組吳舒宇 分機3759" if support=="needs_confirmation" else None))
        wf=structure_application_workflow(UniversityApplicationWorkflow(home_university="淡江大學",school_name=name,
            country="日本",partner_website=fields["website"].value,program_type="交換學生",academic_year=JP_YEAR,
            application_round=JP_ROUND,steps=steps,last_checked=CHECKED_AT,review_status="legacy",coverage_status="partial_official",
            coverage_note="已核對校內2027–2028二甄；已截止且矛盾項待確認。外校證據適用期逐項保存；尚未經發布審查，不產生提醒。",
            sources=[{"title":SOURCES[s].get("title",s),"source_url":SOURCES[s]["source_url"],
                      "role":"partner_university" if SOURCES[s]["role"]=="host_incoming" else "home_university",
                      "checked_at":CHECKED_AT,"content_hash":SOURCES[s].get("sha256"),
                      'effective_academic_year':SOURCES[s]['applicable_year'],
                      'application_round':JP_ROUND if SOURCES[s]['role']=='home_outbound' else '2027春季／一般規則依來源適用期'}
                     for s in source_ids if SOURCES[s]['role']!='directory_reference']))
        assert not workflow_structure_issues(wf),workflow_structure_issues(wf)
        workflows.append(wf)
        destinations.append(build_tku_destination(record))
    (BUNDLE/'host_documents.json').write_text(json.dumps(host_catalog,ensure_ascii=False,indent=2)+'\n')
    for filename,rows in [("application_workflows.jsonl",workflows),("destination_profiles.jsonl",destinations)]:
        (BUNDLE/filename).write_text("".join(row.model_dump_json()+"\n" for row in rows))


if __name__ == "__main__": main()
