"""Offline CCU catalogue, round-specific dashboard, search and home workflow.

Current and historical text are separated by the official PDF colour convention.
All three home rounds are closed as of the recorded check. Blank quotas are unknown.
"""

from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from .ccu_sources import *
from .models import (
    ApplicationPeriodItem,
    Attachment,
    ExchangeInfo,
    PageCategory,
    PartnerUniversity,
    ProcessedPage,
    RuleExplanation,
    SourceReference,
    StudentDashboard,
    StudentInfoItem,
    ApplicationStep,
    ApplicationDocumentRequirement,
    ApplicationWorkflowSource,
    ApplicationSubmissionDetails,
    ApplicationRuleScope,
    ApplicationCopyType,
    UniversityApplicationWorkflow,
)


def fetch_ccu_partner_universities() -> list[PartnerUniversity]:
    from .ccu_campus_assets import apply_campus_assets
    from .ccu_completion import apply_completion
    return [
        apply_completion(apply_campus_assets(PartnerUniversity.model_validate_json(line)))
        for line in (BUNDLE / "partners.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _source(title="中正大學2027春季校級薦外交換公告", url=ANNOUNCEMENT_URL):
    return SourceReference(
        title=title, source_url=url, category=PageCategory.EXCHANGE_APPLICATION
    )


def _item(title, details, url=GUIDELINES_URL):
    return StudentInfoItem(
        title=title, details=details, source=_source("中正大學2027春季簡章", url)
    )


DOCUMENTS = [
    ("2027春季交換申請表", "所有簽章完成；電腦繕打、兩吋證件照。", FORM_DOC_URL),
    ("中文及英文歷年成績單", "各一份，含系／班排名、GPA及教務處認證。", None),
    ("在學證明", "中英文在學證明一份。", None),
    ("外語檢定成績單／證書", "兩年內有效，符合所選計畫；可提供彩色影本。", None),
    ("履歷表", "學經歷、社團、課外活動、才藝與專長。", None),
    (
        "研修計畫書",
        "每個志願一份；中英皆可，含自傳、讀書計畫及申請動機，各約一頁A4，不限格式。",
        None,
    ),
    ("畢業資格審核表", "交換學期為學士班四年級者需繳交。", None),
    (
        "教師推薦函",
        "每個志願至少一封；親筆簽名並彌封，彌封處亦簽名，封面寫合作校英文名；北海道HUSTEP須用合作校格式。",
        None,
    ),
    ("其他有利審查資料", "選擇性，最多5頁。", None),
]


def build_ccu_student_dashboard(*, partner_universities=None, reference_time=None):
    now = reference_time or datetime.now(timezone.utc)
    periods = []
    for r, (online, paper) in ROUND_DEADLINES.items():
        schools = (
            "泰國法政大學"
            if r == 1
            else "南丹麥、北海道、總統大學、HCMUT、維爾特克"
            if r == 2
            else "其他已公告名額之姊妹校"
        )
        for channel, stamp in [("線上", online), ("紙本", paper)]:
            deadline = datetime.fromisoformat(stamp)
            periods.append(
                ApplicationPeriodItem(
                    title=f"{ROUND}第{r}梯次{channel}截止",
                    scope="home_application",
                    program_types=["exchange"],
                    academic_year=YEAR,
                    application_round=f"{ROUND}第{r}梯次",
                    deadline_at=deadline,
                    opens_at=None,
                    date_status="verified_exact",
                    status="closed" if now > deadline else "open",
                    status_note="校內收件已截止。"
                    if now > deadline
                    else "即日起受理；開始時刻未載。",
                    reminder_eligible=False,
                    checked_at=CHECKED_AT,
                    source=_source(),
                    details=[
                        schools,
                        f"線上 {online}；紙本 {paper}，兩項均須完成。",
                        "公告與簡章第2–3頁；不可把合作校期限當成校內期限。",
                    ],
                )
            )
    periods.append(
        ApplicationPeriodItem(
            title="下一季新版查核狀態",
            scope="recurring_reference",
            program_types=["exchange"],
            academic_year=None,
            application_round="2027秋季",
            date_status="needs_confirmation",
            status="needs_confirmation",
            status_note="尚未核實2027秋季新版；未查得官方明示尚未公告。",
            checked_at=CHECKED_AT,
            source=_source("赴外最新公告清單", NEWS_URL),
            details=[
                "目前核實最新版為2027春季。",
                "不沿用2026秋季或其他學校116學年度文件。",
            ],
        )
    )
    doc_details = [f"{name}：{text}（簡章第3–4頁）" for name, text, _ in DOCUMENTS]
    rules = [
        RuleExplanation(
            title="2027春季校級薦外交換簡章",
            summary="雙成績門檻、最多3志願、線上與紙本兩階段；當期三梯次均已截止。",
            key_points=[
                "GPA至少3.0且歷年總平均至少70分；須就讀滿兩學期。",
                "大學部二年級至大四上，碩博士班二年級以上；全程保留學籍。",
                "返國一個月內繳交心得。",
                "簡章第2頁時程標題誤留2026秋季，日期與公告均為2027春季，待承辦確認。",
            ],
            source=_source("2027春季校級薦外交換簡章", GUIDELINES_URL),
            document_url=GUIDELINES_URL,
            full_text_extracted=True,
        )
    ]
    return StudentDashboard(
        school_name=HOME,
        last_checked=CHECKED_AT,
        academic_score_minimum=70,
        academic_gpa_minimum=3.0,
        maximum_preferences=3,
        academic_score_rule="歷年在校GPA至少3.0，且歷年總平均至少70分；兩項均須符合（簡章第1頁）。",
        language_score_minimums={},
        application_periods=periods,
        program_overview=[
            _item(
                "校級與院級擇一，最多3志願",
                [
                    "不得同時申請校級及院級交換；最多3個志願（第1頁及申請表第1頁）。",
                    "校內通過與提名後始得申請合作校，最終錄取由合作校決定。",
                ],
            ),
            _item(
                "交換期間",
                [
                    "2027年1月至7月一學期；個別校曆與一學年名額另見學校資訊。",
                    "赴外交換或進修以一次為限，申請年限至多一年。",
                ],
            ),
            _item(
                "學費、住宿及修課",
                [
                    "繳交中正學雜費，合作校學費原則免繳；機票、生活、保險與個人開銷自付（第5頁）。",
                    "住宿與語言中心可能另付費，少數姊妹校免宿依各校規定，不能假定全部免費。",
                    "合作校未訂較高要求時，每學期至少2門課、4學分或8 ECTS（第5–6頁）。",
                ],
            ),
        ],
        eligibility=[
            _item(
                "校內成績與學籍",
                [
                    "GPA至少3.0且歷年總平均至少70分（第1頁），合作校更高要求從其規定。",
                    "在中正就讀滿兩學期，大學部二年級至大四上，碩博士二年級以上。",
                    "品行優良、無不良紀錄，交換期間不得休學、退學或畢業。",
                    "申請表的大四一學年專案欄位與簡章一般限制須承辦確認。",
                ],
            )
        ],
        language_requirements=[
            _item(
                "逐校、逐計畫的語言門檻",
                [
                    "中正未訂统一TOEIC門檻，以志願合作校及計畫為準。",
                    "檢定成績需在兩年內有效（簡章第3頁）。",
                    "北海道HUSTEP／SA／SRS與蘇黎世工學院學士／碩士門檻分開確認。",
                ],
            )
        ],
        required_documents=[
            _item("校內申請資料", doc_details),
            _item(
                "提交方式",
                [
                    "除校內申請表與彌封推薦函外，其餘電子檔先上傳校方系統。",
                    "所有紙本交國際事務處；語言檢定可彩色影本，其餘彩色正本。",
                    "錄取後依通知回覆意願並交家長同意書。",
                ],
                ANNOUNCEMENT_URL,
            ),
        ],
        scholarship_info=[
            _item(
                "補助版本需另外核實",
                [
                    "簡章第7頁仍引2026年2–3月學海申請期，僅作已過期參考。",
                    "2027補助公告、申請日期與當期文件尚未核實，不視為當期可申請。",
                ],
            )
        ],
        document_explanations=rules,
        rule_explanations=rules,
        partner_universities=partner_universities
        if partner_universities is not None
        else fetch_ccu_partner_universities(),
        sources=[
            _source(),
            _source("2027春季學校資訊（2026-09-17）", PARTNERS_URL),
            _source("2027春季簡章", GUIDELINES_URL),
        ],
    )


def ccu_exchange_info(partners=None):
    rows = partners if partners is not None else fetch_ccu_partner_universities()
    return ExchangeInfo(
        school_name=HOME,
        program_type=["校級薦外交換"],
        academic_year=["115學年度第二學期（2027春季）"],
        semester=["2027春季"],
        application_period=[
            "2027春季三梯次校內收件均已截止（2026/08/27、09/07、09/21）"
        ],
        eligibility=[
            "GPA至少3.0且歷年總平均至少70分",
            "就讀滿兩學期；大二至大四上／碩博士二年級以上",
        ],
        language_requirement=["兩年內有效成績；門檻依合作校及計畫"],
        required_documents=[n for n, _, _ in DOCUMENTS],
        partner_universities=[r.school_name for r in rows],
        source_urls=[ANNOUNCEMENT_URL, GUIDELINES_URL, PARTNERS_URL],
        last_checked=CHECKED_AT,
    )


def ccu_processed_pages():
    dashboard = build_ccu_student_dashboard(partner_universities=[])
    text = " ".join(
        d
        for row in [
            *dashboard.program_overview,
            *dashboard.eligibility,
            *dashboard.language_requirements,
            *dashboard.required_documents,
        ]
        for d in row.details
    )
    return [
        ProcessedPage(
            title="中正大學2027春季校級薦外交換公告與簡章",
            source_url=ANNOUNCEMENT_URL,
            published_at="2026-08-18",
            text=text,
            summary=text[:220],
            category=PageCategory.EXCHANGE_APPLICATION,
            attachments=[
                Attachment(
                    url=GUIDELINES_URL,
                    filename="2027春季校級薦外交換學生計畫簡章.pdf",
                    content_type="application/pdf",
                ),
                Attachment(
                    url=FORM_DOC_URL,
                    filename="2027春季交換申請表.doc",
                    content_type="application/msword",
                ),
            ],
            crawled_at=CHECKED_AT,
            content_hash=hashlib.sha256(text.encode()).hexdigest(),
        )
    ]


def build_ccu_workflow(partner: PartnerUniversity):
    r = home_round(partner.school_name)
    online, paper = ROUND_DEADLINES[r]
    scope = ApplicationRuleScope(academic_years=[YEAR], application_rounds=[ROUND])
    docs = [
        ApplicationDocumentRequirement(
            name=n,
            copies=1,
            copy_type="copy" if "檢定" in n else "original",
            source_urls=[GUIDELINES_URL],
            official_form_url=u,
            needs_confirmation=n in ("畢業資格審核表", "教師推薦函"),
        )
        for n, _, u in DOCUMENTS
    ]
    docs[0].signatures = ["申請人", "家長", "系所主管", "院長"]
    docs[0].stamps = ["教務處教學組審核"]
    docs[1].stamps = ["教務處認證"]
    docs[7].signatures = ["教師親筆簽名", "彌封處簽名"]
    steps = [
        ApplicationStep(
            order=1,
            phase="校內準備",
            title="核對中正雙成績、年級及3志願",
            responsible_party="學生／中正國際處",
            responsible_unit=HOME + "國際事務處",
            summary="GPA至少3.0且歷年平均至少70分，校級與院級交換擇一。",
            details=[
                "就讀滿兩學期；大二至大四上及碩博士二年級以上。",
                "所選計畫、科系與校區須逐校確認。",
            ],
            scope=scope,
            source_urls=[GUIDELINES_URL, PARTNERS_URL],
            checked_at=CHECKED_AT,
            support_status="verified",
        ),
        ApplicationStep(
            order=2,
            phase="校內申請",
            title="完成中正線上申請",
            responsible_party="學生",
            responsible_unit=HOME + "國際事務處",
            timing=f"{ROUND}第{r}梯次：{online}（已截止）",
            summary="先完成線上申請；校內申請表及彌封推薦函不須上傳。",
            required_documents=[
                d.name
                for d in docs
                if d.name not in ("2027春季交換申請表", "教師推薦函")
            ],
            document_requirements=[
                d.model_copy(update={"copy_type": ApplicationCopyType.DIGITAL})
                for d in docs
                if d.name not in ("2027春季交換申請表", "教師推薦函")
            ],
            scope=scope,
            submission=ApplicationSubmissionDetails(
                method="online", portal_url=PORTAL_URL
            ),
            action_url=PORTAL_URL,
            source_urls=[ANNOUNCEMENT_URL, GUIDELINES_URL],
            checked_at=CHECKED_AT,
            support_status="verified",
        ),
        ApplicationStep(
            order=3,
            phase="校內申請",
            title="繳交完整紙本申請",
            responsible_party="學生",
            responsible_unit=HOME + "國際事務處",
            timing=f"{ROUND}第{r}梯次：{paper}（已截止）",
            summary="所有簽章完成後交國際事務處；與線上截止分開。",
            details=[f"{n}：{text}" for n, text, _ in DOCUMENTS],
            required_documents=[d.name for d in docs],
            document_requirements=docs,
            official_form_urls=[FORM_DOC_URL, FORM_ODT_URL],
            scope=scope,
            submission=ApplicationSubmissionDetails(method="paper"),
            source_urls=[ANNOUNCEMENT_URL, GUIDELINES_URL, FORM_DOC_URL],
            checked_at=CHECKED_AT,
            support_status="verified",
        ),
        ApplicationStep(
            order=4,
            phase="錄取及提名",
            title="回覆交換意願並等待提名",
            responsible_party="學生／中正國際處",
            responsible_unit=HOME + "國際事務處",
            summary="2026/10/16公告最終校內結果；校內通過不等於合作校錄取。",
            required_documents=["家長同意書"],
            document_requirements=[
                ApplicationDocumentRequirement(
                    name="家長同意書",
                    official_form_url=GUARDIAN_URL,
                    signatures=["家長"],
                    source_urls=[ANNOUNCEMENT_URL, GUARDIAN_URL],
                )
            ],
            scope=scope,
            source_urls=[ANNOUNCEMENT_URL, GUARDIAN_URL],
            checked_at=CHECKED_AT,
            support_status="verified",
        ),
        ApplicationStep(
            order=5,
            phase="合作校申請",
            title="依提名信辦理合作校申請",
            responsible_party="學生／合作校",
            summary="合作校條件為接收中正學生之incoming條件，與中正outbound資格分开。",
            details=[
                partner.application_info
                or "當期第二階文件尚未核實，依提名信向合作校確認。",
                partner.partner_application_deadline or "當期合作校截止尚未核實。",
            ],
            timing=partner.partner_application_deadline,
            scope=scope,
            source_urls=[PARTNERS_URL],
            checked_at=CHECKED_AT,
            support_status="needs_confirmation",
            needs_confirmation=True,
            confirmation_contact="outbound@ccu.edu.tw",
        ),
        ApplicationStep(
            order=6,
            phase="行前與返國",
            title="完成學籍、住宿與返國心得",
            responsible_party="學生／系所／教務處",
            summary="在中正註冊繳費並保有學籍，合作校學費原則免繳，生活與住宿依個別校規。",
            details=[
                "返國一個月內交心得（簡章第4–5頁）。",
                "抵達後立即回報；申請表另載抵達及返國兩週內向教學組填送通知，兩種回報分開。",
                "依簡章第5–6頁期限辦理學分認定。",
            ],
            scope=scope,
            source_urls=[GUIDELINES_URL, FORM_ODT_URL],
            checked_at=CHECKED_AT,
            support_status="verified",
        ),
    ]
    sources = [
        ApplicationWorkflowSource(
            title=title,
            source_url=url,
            role="home_university",
            authority="home_official_notice",
            priority=1,
            effective_academic_year=YEAR,
            application_round=ROUND,
            checked_at=CHECKED_AT,
        )
        for title, url in [
            ("2027春季公告", ANNOUNCEMENT_URL),
            ("2027春季簡章", GUIDELINES_URL),
            ("2027春季學校資訊", PARTNERS_URL),
            ("2027春季申請表DOC", FORM_DOC_URL),
            ("2027春季申請表ODT", FORM_ODT_URL),
            ("家長同意書", GUARDIAN_URL),
        ]
    ]
    workflow = UniversityApplicationWorkflow(
        home_university=HOME,
        school_name=partner.school_name,
        partner_website=partner.website,
        country=partner.country,
        program_type=partner.program_type,
        academic_year=YEAR,
        application_round=ROUND,
        applicability_status="verified",
        applicability_note="官方使用2027春季；115第二學期為曆年換算。",
        review_status="legacy",
        steps=steps,
        sources=sources,
        last_checked=CHECKED_AT,
        coverage_status="official_partial",
        coverage_note="母校官方當期來源已讀；合作校附件尚未全部獨立查核，無雙人審核。精確期限僅顯示於dashboard，未開啟流程提醒。",
    )
    from .ccu_overseas import enrich_workflow
    return enrich_workflow(workflow, partner)
