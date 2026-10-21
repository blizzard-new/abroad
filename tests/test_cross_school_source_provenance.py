from __future__ import annotations

from types import SimpleNamespace

from bs4 import BeautifulSoup

from exchange_info import cross_school_partners as cross
from exchange_info.models import CrossSchoolHomeAgreement


def _agreement(home_id: str, name: str) -> CrossSchoolHomeAgreement:
    return CrossSchoolHomeAgreement(
        home_id=home_id, home_school_name=name + "大學", home_short_name=name,
        availability_label="參考紀錄", quota_summary="待確認", language_requirement_summary="未單獨列載",
        eligibility_summary="待確認", internal_online_deadline="母校申請期限",
        internal_paper_deadline="母校紙本期限", study_plan_limit="依母校規定",
        deadline_source_url=f"https://{home_id}.example/deadline", deadline_last_checked_at="2026-10-03",
        partner_source_url=f"https://{home_id}.example/partners",
    )


def test_fallback_does_not_invent_host_housing_or_borrow_deadline_review_date(monkeypatch):
    monkeypatch.setattr(cross, "load_bundled_experience_digests", lambda: ({}, {}))
    entity = cross.AggregatedPartnerEntity("japan", "日本", "example", "測試接待校", "Example University")
    agreements = [_agreement("ntu", "臺大"), _agreement("cgu", "長庚")]
    living, housing, courses, reports = cross._synthesize_cross_school_intelligence(entity, agreements)
    assert reports == []
    for points in (living, housing, courses):
        assert points[0].last_checked_at is None
        assert points[0].verification_status == "reference_only"
        assert [s.source_url for s in points[0].related_sources] == [a.partner_source_url for a in agreements]
    html = cross._render_structured_points_html(housing)
    assert "Nomination" not in html and "住宿代碼" not in html and "落地規範" not in html
    assert "目前沒有可對應本校" in html
    assert "2026-10-03" not in html and "尚待核實" in html
    assert len(BeautifulSoup(html, "html.parser").select(".cs-related-sources a")) == 2

    # A condition after the former 90/100-character cuts must remain visible.
    agreements[0].housing_info = "住宿表列事項；" * 20 + "但限第一學期且不保證宿位。"
    agreements[0].tuition_info = "交換費用表列事項；" * 20 + "但實驗及材料費另計。"
    living, housing, _, _ = cross._synthesize_cross_school_intelligence(entity, agreements)
    assert any(agreements[0].housing_info in text for text in housing[0].bullets)
    assert any(agreements[0].tuition_info in text for text in living[0].bullets)
    assert housing[0].last_checked_at is None


def test_story_date_is_not_claimed_as_a_fact_check_and_curated_content_is_retained(monkeypatch):
    url = "https://reports.example/one"
    digest = SimpleNamespace(title_zh="交換生活紀錄", overview="這是來源作者對於交換生活的經驗紀錄。", written_at="2024-01-02", sections=[], tips=[])
    monkeypatch.setattr(cross, "load_bundled_experience_digests", lambda: (
        {url: digest}, {url: {"school_name": "測試接待校", "country": "日本", "platform": "學生網誌"}}
    ))
    entity = cross.AggregatedPartnerEntity("japan", "日本", "example", "測試接待校", "Example University")
    points = cross._match_bundled_digests_for_entity(entity)
    assert len(points) == 1
    assert points[0].last_checked_at is None
    assert points[0].source_published_at == "2024-01-02"
    html = cross._render_structured_points_html(points)
    assert "來源日期：2024-01-02" in html and "查核日期：2024-01-02" not in html
    curated = cross.CURATED_SPECS[0]
    entity.curated = curated
    living, housing, courses, _ = cross._synthesize_cross_school_intelligence(entity, [])
    assert living == list(curated.living_cost_points)
    assert housing == list(curated.housing_points)
    assert courses == list(curated.course_points)
    assert "本輪待複核" in cross._render_structured_points_html(courses)


def test_reviewed_host_points_match_archived_scope_and_keep_remaining_gaps():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    latest = {}
    for name in ("round33-curated-host-source-review.json", "round34-waseda-financial-source-review.json"):
        manifest = json.loads((root / "docs/data-verification-20261021" / name).read_text("utf8"))
        assert manifest["whole_schools_verified"] == 0
        for row in manifest["rows"]:
            latest[(row["institution_slug"], row["field"])] = row["new_value"]
    specs = {spec.institution_slug: spec for spec in cross.CURATED_SPECS}
    for (slug, field), expected in latest.items():
        actual = getattr(specs[slug], field)[0]
        assert actual.model_dump(mode="json") == expected
        assert actual.verification_status == "verified_reference"
    tum = specs["technical-university-of-munich"]
    waseda = specs["waseda-university"]
    assert "至少 1,200" in tum.living_cost_points[0].title
    assert "不含休閒活動" in tum.living_cost_points[0].summary_zh
    assert "校級協議" in tum.housing_points[0].bullets[0]
    assert "不保證" in tum.housing_points[0].summary_zh
    assert "2026 秋季" in waseda.housing_points[0].origin_label
    assert "下一期日期仍待確認" in waseda.housing_points[0].bullets[-1]
    assert "超過 720,000" in waseda.living_cost_points[0].summary_zh
    assert "不是實際每月生活費" in waseda.living_cost_points[0].summary_zh
    assert tum.course_points[0].verification_status == "pending_review"
    course_review = json.loads((root / "docs/data-verification-20261021/round41-waseda-gsaps-review.json").read_text("utf8"))
    assert [p.model_dump(mode="json") for p in waseda.course_points] == course_review["new_course_points"]
    assert len(waseda.course_points) == 7
    graduate_review = json.loads((root / "docs/data-verification-20261021/round40-waseda-graduate-review.json").read_text("utf8"))
    assert len(graduate_review["school_rows"]) == 30
    assert "三年全職工作經驗" in " ".join(waseda.course_points[4].bullets)
    assert "整段交換期間最多 4 學分" in " ".join(waseda.course_points[5].bullets)
    assert "不給學分但有成績並列成績單" in " ".join(waseda.course_points[6].bullets)
    assert "14 學分，不含 CJL" in waseda.course_points[6].bullets[1]
    assert "博士不強制" in waseda.course_points[6].bullets[1]
    assert "交換生仍為零學分" in waseda.course_points[6].bullets[-1]
    assert "僅四月入學且須交換一年" in waseda.course_points[3].bullets[0]
    assert all(p.verification_status == "verified_reference" for p in waseda.course_points)
    assert "1–7" in " ".join(waseda.course_points[0].bullets)
    assert "最多 4 學分、2 門課" in " ".join(waseda.course_points[2].bullets)
    assert tum.experience_points == waseda.experience_points == ()
    experience_review = json.loads((root / "docs/data-verification-20261021/round36-curated-experience-source-review.json").read_text("utf8"))
    assert {r["institution_slug"] for r in experience_review["rows"]} == {tum.institution_slug, waseda.institution_slug}
    assert all(r["new_value"] == [] and len(r["old_value"]) == 1 for r in experience_review["rows"])
