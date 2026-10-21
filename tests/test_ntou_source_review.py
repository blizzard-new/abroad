from pathlib import Path
import json

from exchange_info.application_documents import all_application_templates
from exchange_info.ntou_eligibility import ntou_academic_check, ntou_language_check
from exchange_info.ntou_source_review import load_snapshot
from exchange_info.ntou_student_view import build_ntou_student_dashboard
from exchange_info.verified_window_deadlines import build_verified_window_deadline_catalog


def test_previous_semester_and_chosen_program_are_not_inferred_from_cumulative_inputs():
    for degree, score, gpa in [("學士班", None, 2.5), ("碩士班", None, 3.0), ("學士班", 80, 3.5)]:
        status, detail = ntou_academic_check(degree, score, gpa)
        assert status == "needs_confirmation" and "前一學期" in detail
    for test, score in [("toefl", 6), ("ielts", 5), ("jlpt", 3), ("delf", 1)]:
        assert ntou_language_check(test, score, partner_country="法國")[0] == "needs_confirmation"


def test_two_closed_windows_do_not_create_next_year_reminders():
    d = build_ntou_student_dashboard()
    deadlines = {p.deadline_at.isoformat() for p in d.application_periods if p.deadline_at}
    assert deadlines == {"2026-05-08T12:00:00+08:00", "2026-09-30T12:00:00+08:00"}
    assert not any(p.availability_status == "open" for p in d.partner_universities)
    assert sum(p.availability_status == "reference_only" for p in d.partner_universities) == 45
    card = next(c for c in build_verified_window_deadline_catalog().items if c.school_id == "ntou")
    assert card.primary_deadline_at is None and not card.subtasks


def test_shared_quota_and_paid_language_programs_are_distinguished():
    s = load_snapshot(Path(__file__).resolve().parents[1])
    assert len(s["table_matches"]) == 39 and len(s["mainland_matches"]) == 6
    assert not any(name.startswith("SRM") for name in s["table_matches"])
    d = build_ntou_student_dashboard()
    memorial = next(p for p in d.partner_universities if p.school_name.startswith("紐芬蘭"))
    assert "兩校區合計" in memorial.quota and "不能逐列相加" in memorial.quota
    assert "Level1先付加幣2930" in memorial.tuition_info
    west = next(p for p in d.partner_universities if p.school_name.startswith("西來大學"))
    assert "減免50%" in west.tuition_info and "4堂課" in west.tuition_info
    assert all("至少一門專業課程" in p.course_restrictions for p in d.partner_universities)
    shanghai = next(p for p in d.partner_universities if p.school_name.startswith("上海海事大學"))
    assert "僅商船學院與交通運輸學院" in shanghai.colleges


def test_document_language_choice_and_award_report_deadlines_are_preserved():
    templates = {t.id: t for t in all_application_templates("ntou")}
    application = templates["exchange-application-data"]
    assert "可選中文或英文一種" in application.description
    assert "未支持全部合併單一PDF" in application.description
    assert "大學部指導教授欄留白" in application.description
    plan = templates["study-plan"]
    assert "本輪未核實每篇1000–1500字" in plan.description
    report = templates["return-report"]
    assert "受獎生返國兩週" in report.description and "四週內完成核銷" in report.description
    assert "非學海受獎生可免影片" in report.description


def test_generated_story_text_does_not_become_personal_testimony():
    from exchange_info.experience_collector import build_experience_digest
    from exchange_info.models import StudentExperienceSource
    from exchange_info.life_context import LifeResearchSnapshot
    folder = Path(__file__).resolve().parents[1] / "src/exchange_info/official_data/ntou"
    stories = [StudentExperienceSource.model_validate_json(line)
        for line in (folder / "student_experiences.jsonl").read_text("utf8").splitlines()]
    assert len(stories) == 34
    for source in stories:
        assert source.content_status == "metadata_only"
        assert not source.theme_summaries and not source.theme_summaries_zh
        digest = build_experience_digest(source.school_name, source.country, [source])
        assert not digest.highlights and not digest.common_strengths and not digest.common_challenges
    for line in (folder / "student_life.jsonl").read_text("utf8").splitlines():
        raw = json.loads(line)
        entry = LifeResearchSnapshot.model_validate(raw)
        assert entry.status == "partial" and not entry.evidence
        assert raw["reference_data"]["evidence"]  # Preserve material for later source comparison.
