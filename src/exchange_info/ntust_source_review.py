"""Bounded review of NTUST's 116-1 overseas and 115-2 mainland notices."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

CHECKED_AT = "2026-10-20T19:45:16+00:00"
GUIDELINES = "https://oia-r.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw"
MAINLAND = "https://oia-r.ntust.edu.tw/p/405-1060-143054,c9057.php?Lang=zh-tw"
PORTAL = "https://stu88.ntust.edu.tw/outboundstudent/index/index/puid/fall2027"
ACADEMIC = "116-1歐美亞澳組要求114-2學期班排名前70%，經系所審查通過者例外；不得以平均65分或GPA2.3替代。115-2大陸組要求大學部歷年總平均75分、研究所80分，該梯次已截止。"
PERIOD = "116-1（2027秋季）歐美亞澳組於2026/12/03 10:00至12/07 15:00線上申請；各接待校當期條件於申請期間才開放，既有名單不能自動當作116-1開放名額。"
HISTORICAL = "115-2大陸組於2026/06/27 10:00至07/03 17:00申請，已截止；116-1系統已公布共同時程，但大陸組新簡章及各校條件仍須確認。"
LANGUAGE = "母校基本語檢：TOEIC550、舊制TOEFL iBT57、IELTS學術組4.0或全民英檢中級複試；116-1歐美亞澳另列新制TOEFL iBT4、JLPT N2、歐語B1、TOPIK3。大陸組也須英語檢定，不能寫免語檢。"
DOCS = [
    "116-1歐美亞澳組一律線上填報及審查，不需另外繳紙本至國際處；送出前確認正確學期及文件，截止後不得要求修改或抽換。",
    "上傳未加密PDF：114-2正式中文及英文歷年成績單各一份；若尚未核發則以114-1為準，不接受線上成績查詢截圖。",
    "有效語檢成績掃描檔；多益自考試日起兩年內。截止前未收到正式語檢單可附考生資料與成績截圖，不能與學業成績截圖禁令混淆。",
    "中文及英文自傳各一份，每份約1至2頁，兩語合併一檔；中文及英文讀書計畫亦各約1至2頁、合併另一檔，這是篇幅指引而非硬性兩頁上限。",
    "課外表現證明須為目前學制期間取得，合併一個PDF；研究生另須指導教授已簽名之交換同意書。產學專班須贊助企業與專班主任書面同意。",
    "上述為母校初審文件，國際處不轉交接待校；接待校入學文件須另備，紙本寄送等要求依接待校或國際處個別通知。",
]
SCHOLARSHIPS = [
    "116-1申請交換獎學金須在系統勾選是；學海惜珠另行申請，不能把自費語檢門檻視為獎學金資格。",
    "獎助語言列TOEIC750、IELTS6、舊制iBT79、新制iBT3.5、全民英檢中高級複試、JLPT N2、歐語B1或TOPIK3；新制TOEFL報名門檻另列4分，兩段差異須確認。",
    "獎助限通過母校及選優會議審查者，名額依年度預算，符合申請資格不保證獲獎；非英語語檢申請者須赴該語言母語國。",
    "簡章列亞洲（不含中國）6萬元，非亞洲及指定新南向國家9萬元；弱勢亞洲9萬元、非亞洲13.5萬元。個別資格與指定國家範圍依簡章審核。",
    "獲獎者須至少三門專業課程及格才可領全額，自費交換至少兩門專業課程；接待校較高要求仍須符合。學海飛颺出國前80%、返國完成程序後餘款；選優原則返國審核後一次撥款。",
    "簡章9萬元與80%的條文，和示例預領75,000元不一致；不得直接用示例推算保證款額。退還、比例核算及其他政府獎助擇一領取，依實際核定辦理。",
]


def write_atomic(path: Path, value, lines=False):
    old = path.read_bytes()
    text = ("\n".join(json.dumps(x, ensure_ascii=False) for x in value) if lines else json.dumps(value, ensure_ascii=False, indent=2)) + "\n"
    body = (text.replace("\n", "\r\n") if b"\r\n" in old else text).encode("utf8")
    if body != old:
        temp = path.with_name(path.name + ".audit-tmp")
        assert not temp.exists()
        temp.write_bytes(body)
        os.replace(temp, path)


def item(title, details, url=GUIDELINES, category="exchange_application"):
    return {"title": title, "details": details, "source": {"title": title, "source_url": url, "category": category}}


def review_bundle(root: Path):
    sources = {'sources/ntust/reviewed_1161_overseas_20261021.pdf': '406ab94ad4708ba603606afafe25ccfd7f3b5fa74afeb64ecd41a9aca3d01cd4', 'sources/ntust/reviewed_1152_mainland_20261021.pdf': '2732e75acb1577e21bf6f5956b9f6e2011cd496ca62028d252c15bb94282e912', 'sources/ntust/reviewed_1152_mainland_schools_20261021.pdf': '16e12225089fae278921e00a860c342b31385bce8934eb8ad512b2ee487a0ac6'}
    for name, sha in sources.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != sha:
            raise ValueError("NTUST source generation changed; new review required")
    folder = root / "src/exchange_info/official_data/ntust"
    read = lambda name: json.loads((folder / name).read_text("utf8"))
    d = read("student_dashboard.json")
    d.update(last_checked=CHECKED_AT, academic_score_minimum=None, academic_gpa_minimum=None,
             academic_score_rule=ACADEMIC, language_score_minimums={})
    d["selection_rules"].update(partner_requirements_need_confirmation=True, academic_reference_year="116",
                                undergraduate_rank_maximum=None)
    d["program_overview"] = [item("適用梯次及名額範圍", [PERIOD, HISTORICAL, "116-1歐美亞澳至多10志願；115-2大陸至多8志願。不同組別不能共用上限。"])]
    d["eligibility"] = [item("資格及成績", [ACADEMIC, "在職班不得申請，產學專班須書面同意；交換期間持續在學，最後一學期不開放日本交換。研究生及特殊系所另核成績期間、指導教授同意及額外要求。"])]
    d["language_requirements"] = [item("語言門檻與版本", [LANGUAGE, "企管研究所另須多益750，電子系另須通過系所英文口試；接待校可另訂更高條件。"])]
    d["required_documents"] = [item("116-1母校線上文件", DOCS)]
    d["scholarship_info"] = [item("116-1交換獎助規定", [s], category="scholarship") for s in SCHOLARSHIPS]
    d["document_explanations"] = [{"title": "母校文件與接待校文件分開", "summary": DOCS[0], "key_points": DOCS, "source": item("116-1簡章", [])["source"]}]
    d["rule_explanations"] = [{"title": "資格適用範圍", "summary": ACADEMIC, "key_points": [ACADEMIC, LANGUAGE], "source": item("116-1簡章", [])["source"]}]
    base = {"scope": "home_application", "program_types": ["exchange"], "audience": "applicants",
            "date_status": "verified_exact", "checked_at": CHECKED_AT}
    d["application_periods"] = [
        {**base, **item("116-1歐美亞澳交換申請", [PERIOD, DOCS[0]], PORTAL, "deadline"),
         "academic_year": "116", "application_round": "116-1 歐美亞澳",
         "opens_at": "2026-12-03T10:00:00+08:00", "deadline_at": "2026-12-07T15:00:00+08:00",
         "status": "upcoming", "status_note": PERIOD, "deadline_note": DOCS[0], "reminder_eligible": True},
        {**base, **item("115-2大陸交換申請（歷史參考）", [HISTORICAL], MAINLAND, "deadline"),
         "academic_year": "115", "application_round": "115-2 中國大陸",
         "opens_at": "2026-06-27T10:00:00+08:00", "deadline_at": "2026-07-03T17:00:00+08:00",
         "status": "closed", "status_note": HISTORICAL, "deadline_note": "當期線上申請；錄取後確認及接待校表件另依通知。", "reminder_eligible": False},
    ]
    write_atomic(folder / "student_dashboard.json", d)
    h = read("home_rules.json")
    h.update(eligibility=d["eligibility"], application_periods=d["application_periods"], verified_at=None,
             review_status="partial_review", checked_at=CHECKED_AT)
    write_atomic(folder / "home_rules.json", h)
    x = read("exchange_info.json")
    x.update(application_period=[PERIOD, HISTORICAL], eligibility=d["eligibility"][0]["details"],
             language_requirement=[LANGUAGE], required_documents=DOCS, scholarship_info=SCHOLARSHIPS,
             academic_year=["116", "115"], last_checked=CHECKED_AT)
    write_atomic(folder / "exchange_info.json", x)
    write_atomic(folder / "documents.json", {"school_name": d["school_name"], "required_documents": d["required_documents"], "source_urls": [GUIDELINES]})
    write_atomic(folder / "scholarships.json", {"school_name": d["school_name"], "scholarships": d["scholarship_info"], "source_urls": [GUIDELINES]})
    pages = [json.loads(s) for s in (folder / "pages.jsonl").read_text("utf8").splitlines()]
    contents = [x["application_period"], x["eligibility"], x["language_requirement"], x["required_documents"], x["scholarship_info"]]
    assert len(pages) == len(contents)
    for p, values in zip(pages, contents, strict=True):
        p.update(text="\n".join(values), summary="\n".join(values), published_at=None, crawled_at=CHECKED_AT,
                 source_url=GUIDELINES)
        p["content_hash"] = hashlib.sha256(p["text"].encode("utf8")).hexdigest()
    write_atomic(folder / "pages.jsonl", pages, True)
    # Existing partner and workflow rows describe 115-2; no public per-school
    # 116-1 list was available in the reviewed source. Keep them as references.
    partners = [json.loads(s) for s in (folder / "partners.jsonl").read_text("utf8").splitlines()]
    for p in partners:
        mainland = p["country"] in {"中國大陸", "大陸地區"}
        reference = p.setdefault("reference_data", {})
        for key in ("application_deadline", "application_info", "language_requirement", "eligibility"):
            reference.setdefault(key, p.get(key))
        p.update(availability_status="reference_only", quota_status="reference_only",
                 application_window_status="closed",
                 availability_note="既有115-2名單僅歷史參考；116-1各接待校是否開放、名額及資格尚待重新核對。",
                 application_deadline=HISTORICAL if mainland else "既有115-2紀錄已非開放梯次。" + PERIOD,
                 application_info=HISTORICAL if mainland else PERIOD + " " + DOCS[0])
        if mainland:
            p["language_requirement"] = "115-2大陸簡章明列TOEIC550、舊制TOEFL iBT57、IELTS4或全民英檢中級複試；並非免語檢。當期已截止，新梯次另核。"
        p["eligibility"] = "本筆115-2資料僅歷史參考，不能認定符合116-1；" + ACADEMIC + " " + LANGUAGE
        ev = p.setdefault("field_evidence", {})
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period"):
            ev[key] = {"source_url": MAINLAND if mainland else GUIDELINES, "academic_year": "115",
                       "application_round": "115-2（歷史參考）", "checked_at": CHECKED_AT,
                       "status": "reference_only", "note": "未確認116-1逐校開放條件；保留原參考值，非整筆核實。"}
        summary = p.setdefault("student_summary_zh", {})
        summary.update(application_deadline=p["application_deadline"], eligibility_points=[p["eligibility"]],
                       application_steps=[p["application_info"]])
    write_atomic(folder / "partners.jsonl", partners, True)
    workflows = [json.loads(s) for s in (folder / "application_workflows.jsonl").read_text("utf8").splitlines()]
    for w in workflows:
        mainland = w["country"] in {"中國大陸", "大陸地區"}
        w.update(applicability_status="needs_confirmation", effective_application_rounds=["115-2"],
                 applicability_note="既有115-2流程僅參考；不可自動沿用為116-1逐校流程。",
                 coverage_status="official_partial", coverage_note="母校新公告已核對；個別接待校與其他內容仍待查核。")
        for s in w["steps"]:
            s.update(deadline_at=None, deadline_status="needs_confirmation", deadline_reminder_eligible=False,
                     support_status="needs_confirmation", needs_confirmation=True)
            s["scope"]["academic_years"] = ["115"]
            s["scope"]["application_rounds"] = ["115-2"]
        w["steps"][0].update(title="確認適用梯次及資格", summary=ACADEMIC, details=[LANGUAGE, HISTORICAL if mainland else PERIOD])
        w["steps"][1].update(title="依適用梯次完成線上申請", summary=HISTORICAL if mainland else DOCS[0],
                             details=["大陸組錄取後表件依個別通知，不能套用歐美亞澳初審清單。"] if mainland else DOCS,
                             document_requirements=[], submission={"method": "online", "portal_url": MAINLAND if mainland else PORTAL})
        # Remove copied dates from downstream steps without inventing host dates.
        w["steps"][2].update(summary="校內推薦及接待校審查分階段辦理，錄取確認日期依適用梯次公告。",
                             details=[HISTORICAL if mainland else PERIOD])
    write_atomic(folder / "application_workflows.jsonl", workflows, True)
    status = read("verification_status.json")
    status.update(status="partial_review", checked_at=CHECKED_AT,
                  note="母校指定條文已查核，個別合作校及全部衍生內容尚未完成。")
    write_atomic(folder / "verification_status.json", status)

    counts = read("catalog-completeness.json")
    counts.update(open_partners=0, reference_only_partners=237, whole_partner_records_verified=0,
                  active_term=PERIOD + " " + HISTORICAL, verified_at=None, checked_at=CHECKED_AT)
    write_atomic(folder / "catalog-completeness.json", counts)
    status["counts"] = counts
    write_atomic(folder / "verification_status.json", status)
    provenance = read("import_provenance.json")
    for name, sha in sources.items():
        if not any(r["file"] == name for r in provenance["sources"]):
            provenance["sources"].append({"file": name, "sha256": sha, "role": "reviewed_official_notice"})
    write_atomic(folder / "import_provenance.json", provenance)
