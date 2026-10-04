from exchange_info.partner_localization import (
    build_partner_student_summary,
    localize_points,
    merge_student_summaries,
)


def test_bilingual_ntpu_conditions_keep_thresholds_in_chinese():
    points = localize_points("限大學部學生(For Undergraduate Students Only) IELTS minimum overall band score of 6.0 (no sub-score bellow 5.5)")
    result = " ".join(points)
    assert result.count("限大學部學生") == 1
    assert "6.0" in result and "各單項不得低於 5.5" in result
    assert "For Undergraduate" not in result and "minimum" not in result


def test_lincoln_summary_translates_deadline_scores_and_course_options() -> None:
    summary = build_partner_student_summary(
        study_period="1 semester",
        application_deadline=(
            "Semester 1 (February - June): 30 September of previous year "
            "Semester 2 (July - November): 30 March of current year"
        ),
        eligibility=(
            "1. 符合長庚大學辦理「領航者補助作業要點」之申請資格及校內甄選規定。 "
            "2. 語文要求： Option A Entry Requirements: IELTS 6.0 overall, "
            "with no individual band less than 5.5 or equivalent. Study Content: "
            "3 or 4 courses in undergraduate level (100 level recommended) "
            "Option B Entry Requirements: IELTS 5.5 overall, with no individual band "
            "less than 5.0 or equivalent. Study Content: 2 or 3 x 100 level courses."
        ),
        application_info="由本校向對方校提名。",
        tuition_info="免繳該校學雜費",
    )

    assert summary["study_period"] == "1 學期"
    assert summary["application_deadline"] == (
        "第一學期（2 月至 6 月）：前一年 9 月 30 日；"
        "第二學期（7 月至 11 月）：當年 3 月 30 日"
    )
    assert summary["eligibility_points"] == [
        "須先符合長庚大學「領航者補助作業要點」及校內甄選規定。",
        "方案 A 語言門檻：IELTS 總分 6.0，各單項不得低於 5.5（或同等英語成績）。",
        "方案 A 修課要求：選修 3 至 4 門大學部課程，建議以 100 級課程為主。",
        "方案 B 語言門檻：IELTS 總分 5.5，各單項不得低於 5.0（或同等英語成績）。",
        "方案 B 修課要求：選修 2 至 3 門 100 級課程。",
    ]


def test_application_documents_are_translated_and_urls_are_preserved() -> None:
    points = localize_points(
        "1. Official University Transcript "
        "2. Copy of passport (first page) "
        "3. A motivation letter (written in English - max. 400 words) "
        "申請入口：https://example.edu/apply"
    )

    assert any("正式大學成績單" in point for point in points)
    assert any("護照首頁影本" in point for point in points)
    assert any("英文動機信，最多 400 字" in point for point in points)
    assert any("https://example.edu/apply" in point for point in points)


def test_partner_restrictions_are_translated_to_concrete_points() -> None:
    points = localize_points(
        "The university does not offer modules from the Faculty of Dentistry, "
        "Medicine and Pharmacy for mobility program. Undergraduate students are not "
        "eligible to take postgraduate modules, but Postgraduate students are allowed "
        "to take both undergraduate and postgraduate modules."
    )

    assert any("不開放牙醫、醫學與藥學院課程" in point for point in points)
    assert any("大學部學生不得選修研究所課程" in point for point in points)


def test_merge_student_summaries_deduplicates_points() -> None:
    merged = merge_student_summaries(
        [
            {
                "study_period": "1 學期",
                "application_deadline": "4 月 1 日",
                "eligibility_points": ["IELTS 6.0 以上。"],
                "application_steps": ["先由長庚大學提名。"],
                "tuition_points": ["免繳合作校學雜費。"],
                "translated_from_english": True,
            },
            {
                "study_period": "1 學期",
                "application_deadline": "4 月 1 日",
                "eligibility_points": ["IELTS 6.0 以上。"],
                "application_steps": ["先由長庚大學提名。"],
                "tuition_points": [],
                "translated_from_english": False,
            },
        ]
    )

    assert merged["study_period"] == "1 學期"
    assert merged["eligibility_points"] == ["IELTS 6.0 以上。"]
    assert merged["translated_from_english"] is True
