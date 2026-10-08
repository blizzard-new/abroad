"""Conservative TKU adapter: current round and reference catalogue stay separate."""
from __future__ import annotations

from datetime import datetime, timezone

from .models import (ApplicationPeriodItem, ExchangeInfo, PartnerUniversity,
                     ProcessedPage, SourceReference, StudentDashboard, StudentInfoItem)
from .tku_data import BUNDLE, CHECKED_AT, HOME, load_tku_records, load_tku_rounds, load_tku_sources


def _source(source_id: str, summary: str | None = None) -> SourceReference:
    row = next(s for s in load_tku_sources() if s["id"] == source_id)
    return SourceReference(title=row.get("title",source_id), source_url=row["source_url"],
                           summary=summary or f"適用：{row['applicable_year']}；查核2026-10-08；{row['role']}")


def fetch_tku_partner_universities(*, reference_time: datetime | None = None) -> list[PartnerUniversity]:
    now = reference_time or datetime.now(timezone.utc)
    if now.utcoffset() is None: raise ValueError("reference_time needs timezone")
    current = load_tku_rounds()[0]
    opens = datetime.fromisoformat(current["opens_at"])
    deadline = datetime.fromisoformat(current["deadline_at"])
    # "open" means a current application window AND a verified positive quota.
    # Previous Japanese-round schools and the 124 old programme rows are not injected.
    rows=[]
    for record in load_tku_records():
        fields = record.fields
        value = lambda key: fields[key].value
        evidence = fields["quota"].evidence[0]
        status = "closed" if now > deadline else "quota_unconfirmed" if now < opens else "open"
        if status == "open" and (record.quota_status != "numeric" or not record.quota_number):
            status = "quota_unconfirmed"
        rows.append(PartnerUniversity(
            program_type=f"交換學生（{record.application_round}／{record.academic_year}）",
            availability_status=status,
            availability_note=f"{record.academic_year} {record.application_round}表列；2026/9/30 12:00校內申請截止，系所較早截止日需另查。" + ("已截止，僅已獲推薦者依外校期限辦理後續。" if status == "closed" else "申請期間與是否取得推薦須依官方規定。"),
            agreement_type="校級互惠交換", agreement_level="校級", country=value("country"),
            school_name=value("school_name"), website=value("website"), colleges=None,
            degree_levels=value("degree_levels"), study_period=value("study_period"),
            quota=value("quota"),
            eligibility="\n".join(str(value(k)) for k in ["home_eligibility","host_eligibility","department_scope"] if value(k)),
            # The shared partner table uses this column for the host application.
            # Exact home dates remain in the dashboard and availability_note.
            application_deadline=str(value("host_deadline") or "外校當期期限尚未核實；不能沿用其他學校日期"),
            application_info=f"{value('documents')} 外校期限：{value('host_deadline') or '未核實'}。矛盾項：{', '.join(record.conflicts)}；詳細來源見TKU evidence catalogue。",
            tuition_info=str(value("costs")), source_url=evidence.source_url,
        ))
    return rows


def build_tku_student_dashboard(*, partner_universities=None, reference_time: datetime | None = None) -> StudentDashboard:
    now = reference_time or datetime.now(timezone.utc)
    periods=[]
    for index, row in enumerate(load_tku_rounds()):
        source = _source(row["source_id"])
        verified = index == 0
        deadline = datetime.fromisoformat(row["deadline_at"]) if verified else None
        opens = datetime.fromisoformat(row["opens_at"]) if verified else None
        status = ("closed" if now > deadline else "upcoming" if now < opens else "open") if verified else "reference_only"
        periods.append(ApplicationPeriodItem(title=row["title"], details=row["details"], source=source,
            scope="home_application" if verified else "recurring_reference", program_types=["exchange"],
            academic_year=row["academic_year"], application_round=row["application_round"],
            opens_at=opens, deadline_at=deadline, date_status="verified_exact" if verified else "reference_only",
            status=status, status_note=row["status_note"], reminder_eligible=False, checked_at=CHECKED_AT))
    guide = _source("jp-revision-attachment-1", "2027–2028日語第二次甄選簡章；p.2資格、p.3–4文件、p.8–10費用住宿、p.14–15表格；2026-10-08核對全文。")
    return StudentDashboard(school_name=HOME, last_checked=CHECKED_AT,
        academic_score_minimum=75,
        academic_score_rule="僅2027–2028日語二甄：正文總平均75分；附錄Q&A另載系前40%替代條件，適用性待確認。甄試總成績70分為錄取標準，不能作學業平均門檻。",
        language_score_minimums={}, application_periods=periods,
        program_overview=[StudentInfoItem(title="目前資料範圍", details=[
            "最新校級日語二甄4校合計7名，已截止；只有已獲推薦者可依外校期限續辦。",
            "英歐及中文組2027–2028新版尚未核實，不能稱官方明示尚未公告。124筆115舊期計畫另存參考資料。",
            "大三出國由外語學院六系、國企、資工、觀光、政經等系辦理，與國際處互惠交換的學費及流程不同；不納入校級交換名單。",
        ], source=_source("jp-revision-attachment-1", "PDF p.17 Q&A3區分大三出國與國際處交換；並核對首頁、公告索引及赴外頁。"))],
        eligibility=[StudentInfoItem(title="日語第二次甄選資格與矛盾", details=[
            "正文限在學大三及研究所一、二年級；須系所院初選推薦。研究所一新生附大學四年成績單。",
            "正文要求在校學業總平均75；附錄Q&A另有系前40%替代條件，先標待確認，不能自行採較寬條件。",
            "電氣通信JUSST另要求平均80、GPA3.0；電機與資工系所優先；學制及專業須核對外校。",
        ],source=guide)],
        language_requirements=[StudentInfoItem(title="依學制、外校及課程判斷語言", details=[
            "大學部日語課程JLPT N2以上；研究所N1；立命館表列N1。不能將JLPT級別當可直接遞增的數字成績。",
            "電氣通信是英語JUSST；淡江表寫iBT67及IELTS6.0，外校一般頁可選等值證明，連接條件及2027適用性待確認。研究所英語授課是否豁免N1須確認。",
            "成蹊外校較低日語入門條件不能取代淡江校內N2/N1甄選條件。",
        ],source=guide)],
        required_documents=[StudentInfoItem(title="2027–2028日語二甄文件", details=[
            "線上申請表列印後申請人及系主任簽名；中文歷年成績單正本；語文證明；授課老師推薦函一封；中文及日文自傳、研習計畫；切結書；有則附其他證明。",
            "A4單面最多16頁，不裝訂，以L型套依序送系所；面試攜語文原本驗核；至多5個志願。",
            "切結書在官方PDF第14頁；修正申請表第15頁仍載9/17舊期日期，截止時間須向承辦人確認。",
        ],source=guide), StudentInfoItem(title="立命館2027春季外校期限",details=[
            "僅已獲推薦者：外校申請2026/10/2 10:00開始、11/2 09:00 JST截止；COE另辦。",
        ],source=_source("ritsumeikan-2027-guide","PDF p.2時程，p.20–22 COE與健康；2027 Spring；2026-10-08核對。")),
        StudentInfoItem(title="成蹊2027春季外校期限",details=[
            "提名10/1、申請10/15（未載時刻）；文件須由母校承辦人寄送。不能作校內新申請期限。",
        ],source=_source("seikei-2027-sheet","2027 Spring fact sheet PDF p.1–2，2026-10-08核對。"))],
        scholarship_info=[StudentInfoItem(title="費用、住宿與獎助",details=[
            "須繳淡江全額學雜費及註冊，外校主要學費互惠免繳，其他費用自付；不保證宿舍與獎學金。",
            "長崎的正確交換頁及2027期限、住宿價目尚未核實；電氣通信只有一般JUSST頁資料，2027專屬表單費率待確認。",
        ],source=guide), StudentInfoItem(title="立命館2027春季新增費用與獎助",details=[
            "所有SKP學生含交換生新增JPY50,000 Student Support Fee；RUSSES於2026秋季結束，JASSO不保證。",
        ],source=_source("ritsumeikan-2027-guide","2027 Spring PDF p.4 Changes，2026-10-08核對。")),
        StudentInfoItem(title="成蹊2027住宿分期費用",details=[
            "2027/8前Dormy及會館月租JPY93,000但費用包含不同；2027/9起校內住宿學生搬至MICHI，JPY120,000/月含餐寢具水電網路、無押金。",
        ],source=_source("seikei-2027-sheet","2027 Spring PDF p.3–4 Accommodation and cost of living，2026-10-08核對。"))],
        partner_universities=partner_universities if partner_universities is not None else fetch_tku_partner_universities(reference_time=now),
        sources=[_source(s) for s in ["jp-revision","jp-revision-attachment-1","jp-revision-attachment-2","ritsumeikan-2027-guide","seikei-2027-sheet","uec-application","uec-costs"]])


def tku_exchange_info(partners=None) -> ExchangeInfo:
    dashboard = build_tku_student_dashboard(partner_universities=partners)
    return ExchangeInfo(school_name=HOME, program_type=["校級互惠交換（日語第二次甄選）"], academic_year=["2027-2028"],
        application_period=["2026/9/23 09:00–9/30 12:00（台北時間；已截止）"],
        eligibility=[s for item in dashboard.eligibility for s in item.details],
        language_requirement=[s for item in dashboard.language_requirements for s in item.details],
        required_documents=[s for item in dashboard.required_documents for s in item.details],
        partner_universities=[p.school_name for p in dashboard.partner_universities],
        source_urls=[s.source_url for s in dashboard.sources], last_checked=CHECKED_AT)


def tku_processed_pages() -> list[ProcessedPage]:
    ids = {"jp-revision", "jp-revision-attachment-1", "jp-revision-attachment-2", "ritsumeikan-2027-guide", "seikei-2027-sheet"}
    result=[]
    for row in load_tku_sources():
        if row["id"] not in ids: continue
        text = row.get("text") or "\n".join(f"[PDF p.{p['page']}] {p['text']}" for p in row.get("pages",[]))
        result.append(ProcessedPage(title=f"淡江 {row.get('title',row['id'])}",source_url=row["source_url"],text=text,
            summary=f"{row['applicable_year']}，{row['role']}，查核2026-10-08；日語二甄校內已截止，不能拿外校期限取代。",
            category="exchange_application",crawled_at=CHECKED_AT,content_hash=row["sha256"]))
    return result


def load_tku_workflows():
    from .models import UniversityApplicationWorkflow
    return [UniversityApplicationWorkflow.model_validate_json(line) for line in
            (BUNDLE/"application_workflows.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
