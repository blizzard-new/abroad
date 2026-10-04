import json
from pathlib import Path

from exchange_info import school_content as content
from exchange_info import public_translation as translation
from exchange_info.models import DestinationProfile
from exchange_info.life_context import _profile_evidence


def test_supplements_are_scoped_and_do_not_overwrite_newer_content(monkeypatch, tmp_path):
    key = (content.school_identity_key("國立臺北大學"), content.school_identity_key("測試大學"), "德國")
    monkeypatch.setattr(content, "_supplements", lambda: {key: {"fields": [{
        "field": "housing_summary", "previous": "未公開住宿資訊", "summary_zh": "校方不提供宿舍。",
        "sources": [{"url": "https://example.edu/housing", "title_zh": "住宿資訊",
            "excerpt_zh": "校方不提供宿舍。"}]}]}})
    profile = DestinationProfile(home_university="國立臺北大學", school_name="測試大學", country="德國",
        housing_summary="未公開住宿資訊", coverage_status="official_verified")
    result = content.complete_destination_profile(profile, tmp_path)
    assert result.housing_summary == "校方不提供宿舍。"
    assert result.sources[0].source_url == "https://example.edu/housing"
    assert result.coverage_status == "official_partial" and "不代表真人" in result.coverage_note
    assert profile.housing_summary == "未公開住宿資訊"
    assert content.complete_destination_profile(profile.model_copy(update={"home_university": "長庚大學"}), tmp_path).housing_summary == profile.housing_summary
    assert content.complete_destination_profile(profile.model_copy(update={"housing_summary": "新版人工資料"}), tmp_path).housing_summary == "新版人工資料"


def test_life_additions_keep_their_specific_source_and_read_date(monkeypatch, tmp_path):
    key = (content.school_identity_key("國立臺北大學"), content.school_identity_key("測試大學"), "德國")
    source = {"url": "https://example.edu/housing", "title_zh": "住宿資訊",
        "excerpt_zh": "校方不提供宿舍。", "read_at": "2026-10-01T00:00:00+00:00"}
    monkeypatch.setattr(content, "_supplements", lambda: {key: {"fields": [{
        "field": "housing_summary", "previous": "未公開住宿資訊", "summary_zh": "校方不提供宿舍。", "sources": [source]}]}})
    profile = DestinationProfile(home_university="國立臺北大學", school_name="測試大學", country="德國",
        housing_summary="未公開住宿資訊", coverage_status="official_verified")
    evidence = _profile_evidence(content.complete_destination_profile(profile, tmp_path))
    assert evidence[0].sources[0].url == source["url"]
    assert evidence[0].checked_at.isoformat() == source["read_at"]


def test_bundled_translations_are_source_bound_machine_labelled_and_validated(monkeypatch, tmp_path):
    path = tmp_path / "translations.json"
    original = "Monthly rent is 500 EUR."
    path.write_text(json.dumps([
        {"original": original, "url": "https://example.edu/housing", "zh": "每月租金為 500 EUR。", "status": "machine"},
        {"original": "Rent is 50 EUR.", "url": "https://example.edu/housing", "zh": "租金為 500 EUR。", "status": "machine"}
    ]), encoding="utf-8")
    monkeypatch.setattr(translation, "BUNDLED_MACHINE_TRANSLATIONS", path)
    translation._bundled_machine_translations.cache_clear()
    try:
        assert translation.cached_translation(original, "https://example.edu/housing", tmp_path) == ("每月租金為 500 EUR。", "machine")
        assert translation.cached_translation(original, "https://another.example/housing", tmp_path) is None
        assert translation.cached_translation("Rent is 50 EUR.", "https://example.edu/housing", tmp_path) is None
    finally:
        translation._bundled_machine_translations.cache_clear()


def test_bilingual_technical_terms_do_not_hide_existing_chinese():
    for value in ["請依最新 fact sheet 確認住宿。", "先準備 SIM／eSIM 與 Wi-Fi。", "BTH 宿舍", "115_1003_f908ed3fae.pdf"]:
        assert not translation.needs_translation(value)
    assert translation.needs_translation("Monthly housing costs are 500 EUR.")
    assert not translation._valid_translation("Housing is not guaranteed.", "校方保證提供住宿。")
    assert translation._valid_translation("Housing is not guaranteed.", "校方不保證提供住宿。")
    assert not translation._valid_translation("The university does not provide accommodation.", "校方提供住宿。")
    assert translation._valid_translation("or", "或")
    assert translation._valid_translation("May, 2025", "2025 年五月")
    assert not translation._valid_translation("May, 2025", "2025 年六月")
    assert translation._valid_translation("November", "十一月")
    assert not translation._valid_translation("Students may apply.", "學生可於五月申請。")
    assert translation._valid_translation("Arrive in April.", "四月抵達。")
    assert translation._valid_translation("Arrive on 2026-07-01.", "2026 年 7 月 1 日抵達。")
    assert not translation._valid_translation("Arrive on 2026-07-01.", "2026 年 7 月 2 日抵達。")
    assert translation._valid_translation("Landlords' space", "房東專區")
    assert not translation._valid_translation("SPACE SE-B program", "交換計畫")
    assert translation._valid_translation("Oktober 2026", "2026 年 10 月")
    assert not translation._valid_translation("Postal code 080 01", "郵遞區號 80 1")
    assert translation._valid_translation("Sept-Jan", "九月至一月")
    assert not translation._valid_translation("Sept-Jan", "九月至二月")
    assert translation._valid_translation("CEFRB2", "CEFR B2") is False  # Chinese prose is still required.
    assert translation._valid_translation("Requires CEFRB2.", "須具備 CEFR B2。")
    assert translation._valid_translation("03 avril 2026", "2026 年四月03日")


def test_known_phrases_do_not_translate_addresses_or_person_names():
    original = "Contact incoming@utt.fr and see https://example.edu/incoming。請 email 國際處。"
    translated = translation.translate_display_phrases(original)
    assert "incoming@utt.fr" in translated and "https://example.edu/incoming" in translated
    assert "Karolína" == translation.translate_display_phrases("Karolína")
    assert translation.standardize_terms("https://example.edu/ielts?time=8am") == "https://example.edu/ielts?time=8am"
    assert not translation.needs_translation("學生生活 | iAgora.com | r/movingtojapan")
    assert translation.translate_display_phrases("Twenty Campus") == "Twenty Campus"
