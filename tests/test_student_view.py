from datetime import datetime, timezone

from exchange_info.models import (
    ApplicationPeriodDateStatus,
    ApplicationPeriodStatus,
    PartnerUniversity,
)
from exchange_info.student_view import (
    _departmental_reference_partners,
    _merge_partner_universities,
    build_student_dashboard,
    fetch_document_explanations,
    fetch_partner_universities,
    fetch_rule_explanations,
)


def test_cgu_dashboard_uses_verified_home_cycle_without_yearless_fallbacks() -> None:
    dashboard = build_student_dashboard(
        [],
        fetch_partner_sheets=False,
        fetch_regulation_rules=False,
        reference_time=datetime(2026, 7, 29, tzinfo=timezone.utc),
    )

    application, conditional_follow_up, fall_round = dashboard.application_periods
    assert application.title == "115學年度第2學期交換／雙聯校內申請"
    assert application.academic_year == "115"
    assert application.application_round == "第2學期"
    assert application.status == ApplicationPeriodStatus.CLOSED
    assert application.date_status == ApplicationPeriodDateStatus.VERIFIED_EXACT
    assert application.deadline_at.isoformat() == "2026-06-06T23:59:00+08:00"
    assert application.reminder_eligible is False
    assert "紙本" in (application.deadline_note or "")
    assert all("11/01-12/20" not in detail for detail in application.details)

    assert conditional_follow_up.status == ApplicationPeriodStatus.ACTION_REQUIRED
    assert conditional_follow_up.audience == "conditional_applicants"
    assert conditional_follow_up.deadline_at.isoformat() == "2026-09-21T17:00:00+08:00"
    assert conditional_follow_up.reminder_eligible is False
    assert "不能把這個日期當成申請截止日" in conditional_follow_up.status_note


def test_cgu_fall_round_is_announced_but_its_deadline_is_never_guessed() -> None:
    def fall(reference_time: datetime):
        return build_student_dashboard(
            [],
            fetch_partner_sheets=False,
            fetch_regulation_rules=False,
            reference_time=reference_time,
        ).application_periods[2]

    before = fall(datetime(2026, 10, 3, tzinfo=timezone.utc))
    assert before.title == "116學年度第1學期交換／雙聯校內申請（秋季班）"
    assert (before.academic_year, before.application_round) == ("116", "第1學期")
    assert before.opens_at.isoformat() == "2026-11-01T00:00:00+08:00"
    assert before.status == ApplicationPeriodStatus.UPCOMING
    assert before.date_status == ApplicationPeriodDateStatus.NEEDS_CONFIRMATION
    assert before.deadline_at is None and before.reminder_eligible is False
    assert "11/01–12/20" in " ".join(before.details) and "沒有標示年度與截止時刻" in " ".join(before.details)
    assert "不建立提醒" in (before.deadline_note or "")
    assert before.source.source_url.endswith("nodeId=15656")

    # After the announced opening day the system still does not declare it open.
    after = fall(datetime(2026, 11, 2, tzinfo=timezone.utc))
    assert after.status == ApplicationPeriodStatus.NEEDS_CONFIRMATION
    assert after.deadline_at is None


def test_cgu_home_cycle_status_changes_without_changing_verified_dates() -> None:
    upcoming = build_student_dashboard(
        [],
        fetch_partner_sheets=False,
        fetch_regulation_rules=False,
        reference_time=datetime(2026, 4, 1, tzinfo=timezone.utc),
    ).application_periods[0]
    open_period = build_student_dashboard(
        [],
        fetch_partner_sheets=False,
        fetch_regulation_rules=False,
        reference_time=datetime(2026, 5, 1, tzinfo=timezone.utc),
    ).application_periods[0]

    assert upcoming.status == ApplicationPeriodStatus.UPCOMING
    assert open_period.status == ApplicationPeriodStatus.OPEN
    assert upcoming.deadline_at == open_period.deadline_at


def test_partner_rows_for_same_school_are_merged_into_program_options() -> None:
    source = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554"
    rows = [
        PartnerUniversity(
            program_type="交換學生",
            country="新加坡",
            school_name="測試大學 Test University",
            colleges="四院皆可",
            degree_levels="大學部",
            quota="5",
            source_url=source,
        ),
        PartnerUniversity(
            program_type="雙學位",
            country="新加坡",
            school_name="測試大學 Test University",
            colleges="工學院",
            degree_levels="碩士班",
            quota="不限",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533",
        ),
    ]

    partners = _merge_partner_universities(rows)

    assert len(partners) == 1
    assert partners[0].program_type == "交換學生；雙學位"
    assert len(partners[0].program_options) == 2
    assert partners[0].program_options[1].degree_levels == "碩士班"


def test_partner_rows_merge_when_only_chinese_school_prefix_differs() -> None:
    rows = [
        PartnerUniversity(
            program_type="交換學生 / 自費研修",
            country="法國",
            school_name="法國諾歐商學院 NEOMA Business School",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
        ),
        PartnerUniversity(
            program_type="雙學位",
            country="法國",
            school_name="諾歐商學院 NEOMA Business School",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533",
        ),
    ]

    partners = _merge_partner_universities(rows)

    assert len(partners) == 1
    assert partners[0].school_name == "法國諾歐商學院 NEOMA Business School"
    assert partners[0].program_type == "交換學生 / 自費研修；雙學位"
    assert len(partners[0].program_options) == 2


def test_partner_rows_replace_known_misdirected_official_websites() -> None:
    source = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554"
    partners = _merge_partner_universities(
        [
            PartnerUniversity(
                program_type="交換學生 / 自費研修",
                country="波蘭",
                school_name="波蘭華沙醫學大學 Medical University of Warsaw",
                website="https://www.tue.nl/en/",
                source_url=source,
            ),
            PartnerUniversity(
                program_type="交換學生 / 自費研修",
                country="法國",
                school_name="法國ICD商學院 ICD Business School",
                website="https://www.iicd.ci/",
                source_url=source,
            ),
        ]
    )

    websites = {row.school_name: row.website for row in partners}
    assert websites["波蘭華沙醫學大學 Medical University of Warsaw"] == (
        "https://www.wum.edu.pl/en"
    )
    assert websites["法國ICD商學院 ICD Business School"] == (
        "https://www.icd-bs.com/"
    )


def test_departmental_reference_partners_are_explicitly_not_central_open() -> None:
    partners = _departmental_reference_partners()

    assert {row.school_name for row in partners} == {
        "法國艾克斯馬賽大學管理研究所 IAE Aix-Marseille Graduate School of Management",
        "雷恩商學院 Rennes School of Business",
    }
    assert all(row.availability_status == "departmental_reference" for row in partners)
    assert all(row.source_url.startswith("https://www.cgu.edu.tw/") for row in partners)
    assert all("id2.cgu.edu.tw" not in row.source_url for row in partners)
    assert all("中央" in (row.availability_note or "") for row in partners)
    assert all("確認" in (row.availability_note or "") for row in partners)


def test_partner_fetch_adds_missing_departmental_references_after_central_success(
    monkeypatch,
) -> None:
    def fake_fetch_sheet_rows(**kwargs) -> list[PartnerUniversity]:
        if kwargs["program_type"] == "交換學生 / 自費研修":
            return [
                PartnerUniversity(
                    program_type="交換學生 / 自費研修",
                    country="日本",
                    school_name="中央清單測試大學 Central Test University",
                    source_url=kwargs["source_url"],
                )
            ]
        return []

    monkeypatch.setattr(
        "exchange_info.student_view._fetch_sheet_rows",
        fake_fetch_sheet_rows,
    )

    partners = fetch_partner_universities()

    assert len(partners) == 3
    assert sum(row.availability_status == "open" for row in partners) == 1
    assert sum(
        row.availability_status == "departmental_reference" for row in partners
    ) == 2


def test_central_open_row_wins_over_same_departmental_reference(monkeypatch) -> None:
    rennes = _departmental_reference_partners()[1]

    def fake_fetch_sheet_rows(**kwargs) -> list[PartnerUniversity]:
        if kwargs["program_type"] == "交換學生 / 自費研修":
            return [
                PartnerUniversity(
                    program_type="交換學生 / 自費研修",
                    country="法國",
                    school_name=rennes.school_name,
                    source_url=kwargs["source_url"],
                )
            ]
        return []

    monkeypatch.setattr(
        "exchange_info.student_view._fetch_sheet_rows",
        fake_fetch_sheet_rows,
    )

    partners = fetch_partner_universities()
    matched = [row for row in partners if row.school_name == rennes.school_name]

    assert len(partners) == 2
    assert len(matched) == 1
    assert matched[0].availability_status == "open"


def test_fetch_rule_explanations_builds_student_friendly_points(monkeypatch) -> None:
    def fake_pdf_text(url: str, **kwargs) -> str:
        if "fe589216" in url:
            return (
                "學海惜珠 勵學優秀學生 須具中華民國國籍，在臺灣地區設有戶籍。"
                "低收入戶 中低收入戶 學業及語文成績標準依領航者補助作業要點。"
                "不得同時或重複領取政府其他出國研修獎學金。家長或監護人同意書 師長推薦函。"
            )
        return (
            "補助學生出國修讀學分 學海飛颺 於本校就讀一學期以上。"
            "中華民國國籍 臺灣地區設有戶籍 學業成績平均達70分以上。"
            "多益700 TOEFLiBT IELTS 5.5 Duolingo 105 不得同時領取其他出國研修補助。"
            "75,000 150,000 前30% 壹萬元 返國後兩週內 心得。"
        )

    monkeypatch.setattr("exchange_info.student_view._fetch_pdf_text", fake_pdf_text)
    monkeypatch.setattr("exchange_info.student_view._document_links_from_page", lambda *args, **kwargs: [])

    rules = fetch_rule_explanations()

    assert len(rules) >= 5
    assert rules[0].title == "長庚大學領航者補助作業要點"
    assert any("70 分以上" in point for point in rules[0].key_points)
    assert any("多益 TOEIC 700" in point for point in rules[0].key_points)
    assert any("75,000" in point for point in rules[0].key_points)
    assert rules[0].document_url
    assert any("低收入戶" in point for point in rules[1].key_points)
    assert any("不得同時或重複" in point for point in rules[1].key_points)
    assert any(rule.title == "長庚大學學生赴境外學校進修交流作業要點" for rule in rules)


def test_fetch_document_explanations_includes_related_forms(monkeypatch) -> None:
    monkeypatch.setattr("exchange_info.student_view._fetch_pdf_text", lambda *args, **kwargs: "")
    monkeypatch.setattr(
        "exchange_info.student_view._document_links_from_page",
        lambda *args, **kwargs: [
            ("長庚大學補助學生參加境外短期學分課程作業要點.pdf", "https://www.cgu.edu.tw/regulation/ServerFile/Get/main"),
            ("2B0001001 長庚大學補助學生參加境外短期學分課程申請表.docx", "https://www.cgu.edu.tw/regulation/ServerFile/Get/form"),
            ("2B0001003 長庚大學補助學生參加境外短期學分課程家長或監護人同意書.docx", "https://www.cgu.edu.tw/regulation/ServerFile/Get/consent"),
        ],
    )

    docs = fetch_document_explanations()

    assert any(doc.document_type == "申請表" for doc in docs)
    assert any(doc.document_type == "同意書" for doc in docs)
    assert any("開啟" not in point for doc in docs for point in doc.key_points)


def test_repurposed_teep_page_is_not_shown_as_teep_rules() -> None:
    from exchange_info.models import PageCategory, ProcessedPage

    def page(text: str) -> ProcessedPage:
        return ProcessedPage(
            title="教育部TEEP計畫",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=19081",
            text=text, summary=text[:40], category=PageCategory.OTHER,
            crawled_at=datetime(2026, 10, 3, tzinfo=timezone.utc), content_hash="x",
        )

    def titles(text: str) -> list[str]:
        dashboard = build_student_dashboard(
            [page(text)], fetch_partner_sheets=False, fetch_regulation_rules=False,
            reference_time=datetime(2026, 10, 3, tzinfo=timezone.utc),
        )
        return [row.title for row in dashboard.program_overview] + [row.title for row in dashboard.scholarship_info]

    assert "TEEP 研究實習" in titles("重要規定\nTEEP期間不得從事與實習無關之有酬勞動")
    assert "TEEP 研究實習" not in titles("住宿查詢與繳費\n短期生住宿查詢")
    assert "TEEP 注意事項" not in titles("住宿查詢與繳費\n短期生住宿查詢")
    inbound_teep = (
        "教育部TEEP「全球優秀青年學子來臺蹲點計畫」\n"
        "歡迎在學外國學生或僑生透過此計畫申請來臺短期研究或實習。"
    )
    assert "TEEP 研究實習" not in titles(inbound_teep)
    assert "TEEP 注意事項" not in titles(inbound_teep)

