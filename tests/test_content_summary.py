from exchange_info.content_summary import sanitize_summary_text


def test_sanitize_summary_text_removes_model_json_repair_chatter() -> None:
    value = (
        "學費為 1,028,000 日圓」] , <-- ERROR: malformed JSON due to stray "
        "characters. Need to fix. Let's recompose correctly. Sorry. I'll correct."
    )

    assert sanitize_summary_text(value) == "學費為 1,028,000 日圓。"


def test_sanitize_summary_text_keeps_student_facing_summary() -> None:
    assert sanitize_summary_text("宿舍距校園步行約三分鐘") == (
        "宿舍距校園步行約三分鐘。"
    )
