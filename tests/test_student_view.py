from exchange_info.models import PartnerUniversity
from exchange_info.student_view import (
    _merge_partner_universities,
    fetch_document_explanations,
    fetch_rule_explanations,
)


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
