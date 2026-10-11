from cgu_catalogue_fixture import fixed_cgu_catalogue
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_workflow_collector import (
    LINCOLN_INCOMING_URL,
    build_cgu_reference_workflow,
    collect_application_workflow,
    clean_official_page_title,
    discover_official_partner_pages,
    is_official_partner_url,
    normalize_official_url,
)
from exchange_info.models import (
    ApplicationApplicabilityStatus,
    ApplicationCopyType,
    ApplicationDeadlineStatus,
    ApplicationDocumentRequirement,
    ApplicationRuleScope,
    ApplicationSourceAuthority,
    ApplicationStep,
    ApplicationSubmissionDetails,
    ApplicationSubmissionMethod,
    ApplicationSupportStatus,
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowSource,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)
from exchange_info.storage import (
    ensure_data_dirs,
    load_application_workflows,
    replace_application_workflow,
)
from exchange_info.workflow_structuring import structure_application_workflow


def _partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生 / 自費研修",
        country="紐西蘭",
        school_name="林肯大學 Lincoln University",
        website="https://www.lincoln.ac.nz/",
        quota="2",
        eligibility="IELTS 6.0 overall, no band below 5.5.",
        application_deadline="Semester 1: 30 September; Semester 2: 30 March",
        application_info="由本校提名後，Lincoln 直接通知申請作業。",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def _workflow(
    school_name: str = "林肯大學 Lincoln University",
    title: str = "確認資格",
) -> UniversityApplicationWorkflow:
    return UniversityApplicationWorkflow(
        school_name=school_name,
        country="紐西蘭",
        steps=[
            ApplicationStep(
                order=1,
                phase="校內準備",
                title=title,
                responsible_party="學生",
                summary="核對資格。",
            )
        ],
        last_checked=datetime(2026, 7, 11, tzinfo=timezone.utc),
        coverage_status="official_verified",
    )


def test_legacy_workflow_populates_structured_document_requirements() -> None:
    step = ApplicationStep(
        order=1,
        phase="校內準備",
        title="繳交申請文件",
        responsible_party="學生",
        summary="依公告備妥文件。",
        required_documents=["申請表", "歷年成績單"],
        needs_confirmation=True,
    )

    assert [item.name for item in step.document_requirements] == [
        "申請表",
        "歷年成績單",
    ]
    assert step.support_status == ApplicationSupportStatus.NEEDS_CONFIRMATION
    assert step.submission.method == ApplicationSubmissionMethod.UNKNOWN


def test_structured_workflow_captures_scope_submission_and_review_metadata() -> None:
    checked_at = datetime(2026, 7, 28, tzinfo=timezone.utc)
    workflow = UniversityApplicationWorkflow(
        workflow_id="ntpu-116-fall-round-1",
        home_university="國立臺北大學",
        school_name="交換合作校",
        academic_year="116",
        application_round="第一梯次",
        version=2,
        review_status=ApplicationWorkflowReviewStatus.PUBLISHED,
        published_at=checked_at,
        last_checked=checked_at,
        steps=[
            ApplicationStep(
                rule_id="ntpu-school-submit",
                order=1,
                phase="校內申請",
                title="送交系辦",
                responsible_party="學生",
                responsible_unit="所屬學系辦公室",
                summary="列印後親送系辦。",
                scope=ApplicationRuleScope(
                    home_universities=["國立臺北大學"],
                    departments=["資訊工程學系"],
                    academic_years=["116"],
                    application_rounds=["第一梯次"],
                ),
                submission=ApplicationSubmissionDetails(
                    method=ApplicationSubmissionMethod.PAPER,
                    office="資訊工程學系辦公室",
                    receiving_hours="週一至週五 09:00–16:30",
                    send_by_at=datetime(2026, 9, 27, 16, 30, tzinfo=timezone.utc),
                    arrival_deadline_at=datetime(
                        2026, 9, 30, 16, 30, tzinfo=timezone.utc
                    ),
                    deadline_note="以系辦實際收件時間為準。",
                ),
                document_requirements=[
                    ApplicationDocumentRequirement(
                        name="校內交換申請表",
                        copies=2,
                        copy_type=ApplicationCopyType.ORIGINAL_AND_COPY,
                        signatures=["本人", "系主任"],
                    )
                ],
                source_urls=["https://example.edu/official-notice"],
                checked_at=checked_at,
                support_status=ApplicationSupportStatus.VERIFIED,
            )
        ],
        sources=[
            ApplicationWorkflowSource(
                title="116 學年度交換甄選簡章",
                source_url="https://example.edu/official-notice",
                role="home_university",
                authority=ApplicationSourceAuthority.HOME_OFFICIAL_NOTICE,
                priority=1,
                effective_academic_year="116",
                application_round="第一梯次",
                checked_at=checked_at,
            )
        ],
    )

    workflow = structure_application_workflow(workflow)
    payload = workflow.model_dump(mode="json")
    assert payload["steps"][0]["submission"]["method"] == "paper"
    assert payload["steps"][0]["submission"]["send_by_at"] == "2026-09-27T16:30:00Z"
    assert (
        payload["steps"][0]["submission"]["arrival_deadline_at"]
        == "2026-09-30T16:30:00Z"
    )
    assert payload["steps"][0]["submission"]["deadline_note"] == "以系辦實際收件時間為準。"
    assert payload["steps"][0]["deadline_status"] == "verified_exact"
    assert payload["steps"][0]["deadline_reminder_eligible"] is True
    assert payload["steps"][0]["deadline_source_url"] == "https://example.edu/official-notice"
    assert payload["steps"][0]["deadline_checked_at"] == "2026-07-28T00:00:00Z"
    assert payload["steps"][0]["document_requirements"][0]["copies"] == 2
    assert payload["steps"][0]["scope"]["departments"] == ["資訊工程學系"]
    assert payload["sources"][0]["priority"] == 1
    assert payload["review_status"] == "published"
    assert workflow.applicability_status == ApplicationApplicabilityStatus.VERIFIED
    assert workflow.effective_application_rounds == ["第一梯次"]
    assert workflow.steps[0].deadline_status == ApplicationDeadlineStatus.VERIFIED_EXACT


def test_official_url_filter_rejects_third_party_hosts() -> None:
    official = "https://www.lincoln.ac.nz/"
    assert is_official_partner_url(LINCOLN_INCOMING_URL, official)
    assert not is_official_partner_url("https://example.com/lincoln-exchange", official)


def test_official_url_filter_distinguishes_thai_academic_domains() -> None:
    official = "https://www.tbs.tu.ac.th/"

    assert is_official_partner_url(
        "https://bba.tbs.tu.ac.th/incoming-exchange",
        official,
    )
    assert not is_official_partner_url(
        "https://som.ait.ac.th/exchange-program",
        official,
    )


def test_official_url_filter_distinguishes_polish_academic_domains() -> None:
    official = "https://www.sggw.edu.pl/en/"

    assert is_official_partner_url(
        "https://welcome.sggw.edu.pl/incoming-exchange",
        official,
    )
    assert not is_official_partner_url(
        "https://en.uw.edu.pl/education/exchange-and-guest-students/",
        official,
    )


def test_discovery_rejects_unrelated_program_pages_on_official_domain(
    monkeypatch,
) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="泰國",
        school_name="泰國法政大學商學院 Thammasat Business School",
        website="https://www.tbs.tu.ac.th/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            ("Master in Finance", "https://mif.tbs.tu.ac.th/"),
            (
                "Center for International Affairs",
                "https://bba.tbs.tu.ac.th/incoming-exchange/",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)

    assert any("incoming-exchange" in url for _, url in pages)
    assert all("mif.tbs.tu.ac.th" not in url for _, url in pages)


def test_discovery_requires_exchange_signal_not_generic_application(
    monkeypatch,
) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="德國",
        school_name="德國開姆尼茨工業大學 Chemnitz University of Technology",
        website="https://www.tu-chemnitz.de/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            (
                "Application | Advanced Manufacturing",
                "https://www.tu-chemnitz.de/mb/am/studiengang/application.php",
            ),
            (
                "Incoming exchange application",
                "https://www.tu-chemnitz.de/international/incoming/exchange.php",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)

    assert any("incoming/exchange" in url for _, url in pages)
    assert all("advanced" not in title.lower() for title, _ in pages)


def test_normalize_official_url_removes_tracking_query() -> None:
    assert normalize_official_url(
        "https://student.example.edu/exchange?semester=fall&gclid=abc&utm_source=test"
    ) == "https://student.example.edu/exchange?semester=fall"


def test_clean_official_page_title_removes_concatenated_results() -> None:
    assert clean_official_page_title(
        "Accommodation | Incoming | TU Chemnitz...English Department | Other Result"
    ) == "Accommodation | Incoming | TU Chemnitz..."


def test_discovery_rejects_outgoing_and_placeholder_paths(monkeypatch) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="波蘭",
        school_name="波蘭華沙理工大學Warsaw University of Technology",
        website="https://www.pw.edu.pl/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            (
                "Incoming exchange application",
                "https://www.pw.edu.pl/international/incoming-exchange",
            ),
            (
                "Outgoing students",
                "https://www.pw.edu.pl/international/outgoing-students",
            ),
            (
                "International students",
                "https://www.pw.edu.pl/asdfasdf/international-students",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)

    assert any("incoming-exchange" in url for _, url in pages)
    assert all("outgoing" not in url and "asdfasdf" not in url for _, url in pages)


def test_discovery_deduplicates_mirrored_page_titles(monkeypatch) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="大陸地區",
        school_name="武漢大學 Wuhan University",
        website="https://en.whu.edu.cn/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            (
                "Students Exchange Programs-Wuhan University",
                "https://en.whu.edu.cn/jzbf/International1/Students_Exchange_Programs.htm",
            ),
            (
                "Students Exchange Programs-Wuhan University",
                "https://en.whu.edu.cn/International1/Students_Exchange_Programs.htm",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)
    exchange_pages = [url for title, url in pages if "Exchange Programs" in title]

    assert exchange_pages == [
        "https://en.whu.edu.cn/International1/Students_Exchange_Programs.htm"
    ]


def test_discovery_prefers_english_locale_for_duplicate_title(monkeypatch) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="法國",
        school_name="歐洲知識經濟與管理學院 Skema Business School",
        website="https://www.skema.edu/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            ("Exchange students | SKEMA", "https://www.skema.edu/br/node/10256"),
            ("Exchange students | SKEMA", "https://www.skema.edu/en/exchange-students"),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)
    exchange_pages = [url for title, url in pages if "Exchange students" in title]

    assert exchange_pages == ["https://www.skema.edu/en/exchange-students"]


def test_discovery_rejects_exchange_event_news(monkeypatch) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="日本",
        school_name="日本順天堂大學Juntendo University",
        website="https://en.juntendo.ac.jp/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            (
                "International Student Exchange Event | Juntendo University",
                "https://en.juntendo.ac.jp/news/exchange-event.html",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)

    assert all("exchange-event" not in url for _, url in pages)


def test_lincoln_discovery_uses_incoming_official_pages() -> None:
    pages = discover_official_partner_pages(_partner(), max_pages=5)

    assert any(url == LINCOLN_INCOMING_URL for _, url in pages)
    assert all("lincoln.ac.nz" in url for _, url in pages)
    assert all("outbound" not in url for _, url in pages)


def test_lincoln_workflow_has_detailed_official_stages(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector.fetch_official_page_text",
        lambda *args, **kwargs: "",
    )
    workflow = collect_application_workflow(_partner(), rate_limit_seconds=0)

    assert len(workflow.steps) == 9
    assert any(step.responsible_party == "長庚國際處" for step in workflow.steps)
    assert any("護照" in document for step in workflow.steps for document in step.required_documents)
    assert any(step.needs_confirmation for step in workflow.steps)
    assert workflow.coverage_status == "official_verified"


def test_cgu_reference_workflow_stays_unpublished_and_confirmation_gated() -> None:
    checked_at = datetime(2026, 7, 29, tzinfo=timezone.utc)
    partner = PartnerUniversity(
        program_type="交換學生 / 自費研修",
        country="巴西",
        school_name="巴西聖保羅聯邦大學 Universidade Federal de São Paulo",
        website="https://www.unifesp.br/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    official_url = (
        "https://www.unifesp.br/world/images/arquivos/"
        "Undergraduate_students_Institutional_procedures.pdf"
    )

    workflow = build_cgu_reference_workflow(
        partner,
        partner_sources=[("UNIFESP institutional procedures", official_url)],
        partner_application_summary=(
            "由母校完成校際程序後，依 UNIFESP 官方說明以電子郵件送交申請文件。"
        ),
        partner_application_details=["各學期與文件版本仍須由兩校國際處確認。"],
        required_documents=["申請表", "英文或葡萄牙文歷年成績單"],
        submission_method=ApplicationSubmissionMethod.EMAIL,
        submission_email="international@unifesp.br",
        checked_at=checked_at,
    )

    assert len(workflow.steps) == 6
    assert workflow.review_status == ApplicationWorkflowReviewStatus.LEGACY
    assert workflow.published_at is None
    assert workflow.coverage_status == "official_partial"
    partner_step = workflow.steps[3]
    assert partner_step.submission.method == ApplicationSubmissionMethod.EMAIL
    assert partner_step.submission.email == "international@unifesp.br"
    assert partner_step.deadline_status == ApplicationDeadlineStatus.REFERENCE_ONLY
    assert not partner_step.deadline_reminder_eligible
    assert all(item.needs_confirmation for item in partner_step.document_requirements)
    assert all(official_url in item.source_urls for item in partner_step.document_requirements)


def test_replace_workflow_preserves_other_schools(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    replace_application_workflow(_workflow("其他大學 Other University"), tmp_path)
    replace_application_workflow(_workflow(title="更新後流程"), tmp_path)

    rows = load_application_workflows(tmp_path)
    assert {row.school_name for row in rows} == {
        "其他大學 Other University",
        "林肯大學 Lincoln University",
    }
    assert next(row for row in rows if row.school_name.startswith("林肯")).steps[0].title == "更新後流程"


def test_replace_workflow_consolidates_chinese_name_aliases(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    replace_application_workflow(
        _workflow("諾歐商學院 NEOMA Business School"), tmp_path
    )
    replace_application_workflow(
        _workflow("法國諾歐商學院 NEOMA Business School", title="交換與雙聯流程"),
        tmp_path,
    )

    rows = load_application_workflows(tmp_path)
    assert len(rows) == 1
    assert rows[0].school_name == "法國諾歐商學院 NEOMA Business School"
    assert rows[0].steps[0].title == "交換與雙聯流程"


def test_workflow_api_reads_cache_and_rejects_public_refresh(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    replace_application_workflow(_workflow(), tmp_path)
    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: [partner]))
    client = TestClient(create_app(tmp_path))

    cached = client.get("/application-workflow", params={"school": partner.school_name})
    assert cached.status_code == 200
    assert cached.json()["steps"][0]["title"] == "確認資格"

    refreshed = client.post(
        "/application-workflow/refresh", params={"school": partner.school_name}
    )
    assert refreshed.status_code == 401
    assert load_application_workflows(tmp_path)[0].steps[0].title == "確認資格"


def test_workflow_api_applies_department_override(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    workflow = _workflow().model_copy(
        update={
            "steps": [
                ApplicationStep(
                    rule_id="submit",
                    order=1,
                    phase="校內申請",
                    title="校級預設送件",
                    responsible_party="學生",
                    summary="依校級規定送件。",
                ),
                ApplicationStep(
                    overrides_rule_id="submit",
                    order=1,
                    phase="校內申請",
                    title="資工系紙本送件",
                    responsible_party="學生",
                    summary="送到資工系辦。",
                    scope=ApplicationRuleScope(departments=["資訊工程學系"]),
                ),
            ]
        }
    )
    replace_application_workflow(workflow, tmp_path)
    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: [partner]))
    client = TestClient(create_app(tmp_path))

    response = client.get(
        "/application-workflow",
        params={"school": partner.school_name, "department": "資訊工程學系"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [step["title"] for step in payload["steps"]] == ["資工系紙本送件"]
    assert payload["applied_context"]["department"] == "資訊工程學系"


def test_workflow_api_selects_the_requested_published_round(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    replace_application_workflow(
        _workflow(title="第一梯次流程").model_copy(
            update={"academic_year": "116", "application_round": "第一梯次"}
        ),
        tmp_path,
    )
    replace_application_workflow(
        _workflow(title="第二梯次流程").model_copy(
            update={"academic_year": "116", "application_round": "第二梯次"}
        ),
        tmp_path,
    )
    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: [partner]))
    client = TestClient(create_app(tmp_path))

    response = client.get(
        "/application-workflow",
        params={
            "school": partner.school_name,
            "academic_year": "116",
            "application_round": "第二梯次",
        },
    )

    assert response.status_code == 200
    assert response.json()["steps"][0]["title"] == "第二梯次流程"
