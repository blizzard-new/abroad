import re
from functools import lru_cache
from pathlib import Path

import exchange_info
from pypdf import PdfReader
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates
from exchange_info.application_writing_guidance import WRITING_RULES
from exchange_info.models import ApplicationFieldType
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES


def _all_templates():
    for university in SUPPORTED_UNIVERSITIES:
        for template in all_application_templates(university.school_name):
            yield university, template


def test_recommended_ranges_are_ordered_and_fit_inside_every_field_limit() -> None:
    checked = 0
    for university, template in _all_templates():
        for field in template.fields:
            guidance = field.guidance
            if guidance is None or guidance.recommended_max_chars is None:
                continue
            checked += 1
            where = f"{university.id}/{template.id}/{field.id}"
            assert guidance.recommended_min_chars is not None, where
            assert guidance.recommended_min_chars <= guidance.recommended_max_chars, where
            if field.max_length:
                assert guidance.recommended_max_chars <= field.max_length, where
    assert checked > 0


def test_files_and_checkboxes_never_get_writing_guidance() -> None:
    for university, template in _all_templates():
        for field in template.fields:
            if field.field_type in (ApplicationFieldType.FILES, ApplicationFieldType.CHECKBOX):
                assert field.guidance is None, f"{university.id}/{template.id}/{field.id}"


def test_short_term_forms_do_not_inherit_exchange_study_plan_advice() -> None:
    by_id = {template.id: template for template in all_application_templates("長庚大學")}
    plan = {field.id: field for field in by_id["short-term-plan-2b0001002"].fields}
    assert "交換" not in plan["motivation"].guidance.summary
    assert plan["motivation"].guidance.recommended_max_chars is None
    assert "implementation" in plan and plan["implementation"].guidance is not None
    study = {field.id: field for field in by_id["study-plan"].fields}
    assert study["course_plan"].guidance.recommended_max_chars is None  # 修課清單只給格式，不給字數
    assert "交換" in study["motivation"].guidance.summary


OFFICIAL_DATA = Path(exchange_info.__file__).parent / "official_data"
# NTPU and CCU rules come from bundled PDFs, which are not stored as text.
PDF_BACKED = {"ntpu", "ccu"}


def _stored_official_text(university_id: str) -> str:
    parts = []
    for name in ("pages.jsonl", "documents.json", "application_workflows.jsonl"):
        path = OFFICIAL_DATA / university_id / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8").replace("\\n", "\n"))
    return "\n".join(parts)


def _quoted_as_a_word_limit(text: str, limit: int) -> bool:
    digits = f"{limit:,}".replace(",", ",?")
    return re.search(rf"(?<![\d,]){digits}(?!\d)[^。；\n]{{0,14}}字", text) is not None


def test_numeric_writing_limits_name_evidence_and_match_stored_school_text() -> None:
    """Internal consistency only; stored text and passing tests do not verify source facts."""

    templates = {
        (university.id, template.id): template for university, template in _all_templates()
    }
    assert set(WRITING_RULES) <= set(templates), "rule points at a template that does not exist"
    checked = 0
    for key, rules in WRITING_RULES.items():
        assert rules.verified and rules.evidence, f"{key}: name the document the rule was checked against"
        assert rules.min_chars is None or rules.max_chars is None or rules.min_chars <= rules.max_chars
        counted = {field.id: field for field in templates[key].fields}
        for field_id in rules.count_field_ids:
            assert counted[field_id].field_type == ApplicationFieldType.TEXTAREA, f"{key}/{field_id}"
        if rules.min_chars is not None or rules.max_chars is not None:
            assert rules.count_field_ids, f"{key}: a word limit needs fields to count"
            if key[0] in PDF_BACKED:
                continue
            text = _stored_official_text(key[0])
            assert text, f"{key}: no stored official text to check against"
            for limit in (rules.min_chars, rules.max_chars):
                if limit is not None:
                    checked += 1
                    assert _quoted_as_a_word_limit(text, limit), f"{key}: {limit} 字 is not in the stored official text"
    assert checked >= 8


def test_a_limit_that_covers_more_than_the_form_can_total_says_so() -> None:
    ntnu = WRITING_RULES[("ntnu", "study-plan")]
    assert "自傳" in ntnu.count_note, "NTNU counts the autobiography together with the study plan"
    assert "上限是否強制" in WRITING_RULES[("ncu", "return-report")].count_note
    assert WRITING_RULES[("ncu", "return-report")].max_chars is None, "「至少 800-1500 字」 is ambiguous; only the minimum is checked"


def test_schools_without_a_checked_rule_are_told_so_instead_of_shown_nothing() -> None:
    by_school = {
        university.id: {template.id: template for template in all_application_templates(university.school_name)}
        for university in SUPPORTED_UNIVERSITIES
        if university.id not in {"tku", "ccu"}
    }
    for school, templates in by_school.items():
        for template_id in ("study-plan", "return-report"):
            template = templates.get(template_id)
            if template is None:
                continue
            rules = template.writing_rules
            assert rules is not None, f"{school}/{template_id}"
            if (school, template_id) in WRITING_RULES:
                assert rules.verified
            else:
                assert not rules.verified and rules.min_chars is None and rules.max_chars is None
                assert not rules.count_field_ids and "不是學校規定" in " ".join(rules.rules)
    # A rule the stored official text does not support must stay out.
    assert ("cgu", "study-plan") not in WRITING_RULES
    assert ("ncu", "study-plan") not in WRITING_RULES
    assert not by_school["cgu"]["study-plan"].writing_rules.verified
    assert not by_school["ncu"]["study-plan"].writing_rules.verified


def test_writing_rules_are_attached_to_the_right_school_only() -> None:
    ntpu = {template.id: template for template in all_application_templates("國立臺北大學")}
    fju = {template.id: template for template in all_application_templates("輔仁大學")}

    assert ntpu["study-plan"].writing_rules.max_chars == 5000
    assert fju["return-report"].writing_rules.min_chars == 2000
    assert fju["study-plan"].writing_rules.max_chars is None  # 輔大以頁數規定，不以字數計
    assert ntpu["study-plan"].writing_rules is not fju["study-plan"].writing_rules


REPOSITORY = Path(exchange_info.__file__).resolve().parents[2]


@lru_cache(maxsize=None)
def _archived_pdf_text(relative_path: str) -> str:
    reader = PdfReader(REPOSITORY / relative_path)
    return re.sub(r"\s+", "", "".join(page.extract_text() or "" for page in reader.pages))


def test_yzu_report_does_not_invent_a_common_word_or_photo_requirement() -> None:
    rules = WRITING_RULES[("yzu", "return-report")]
    assert rules.min_chars is None and rules.max_chars is None
    text = " ".join(rules.rules)
    assert "未核實" in text and "大陸頁另列返國報告2000字以上" in text
    assert "返國14日" in text and "返國兩個月" in text
    template = next(t for t in all_application_templates("元智大學") if t.id == "return-report")
    assert template.writing_rules == rules


def test_other_schools_photo_field_is_unchanged_by_the_yzu_photo_limit() -> None:
    template = next(t for t in all_application_templates("中原大學") if t.id == "return-report")
    photos = next(field for field in template.fields if field.id == "activity_photos")
    assert photos.max_files == 4


def test_cycu_has_no_published_word_count_and_the_two_week_deadline_is_backed_by_the_archived_regulation() -> None:
    rules = WRITING_RULES[("cycu", "return-report")]
    assert rules.min_chars is None and rules.max_chars is None and not rules.count_field_ids
    assert not re.search(r"\d\s*字", " ".join(rules.rules)), "no word count may be invented for CYCU"
    assert "沒有公布心得報告的字數" in " ".join(rules.rules)
    regulation = _archived_pdf_text("sources/cycu/cycu_exchange_scholarship_rules_536_2.pdf")
    assert "領取助學金之學生須於返國後二周內提交研習成果報告書" in regulation
    assert "二週內" in rules.rules[0]


def test_nccu_writing_rules_match_archived_outbound_and_mainland_guidelines() -> None:
    study = WRITING_RULES[("nccu", "study-plan")]
    assert study.min_chars is None and study.max_chars is None
    assert "不合併" in study.count_note
    assert "至少 500 字" in study.rules[0] and "2 頁為限" in study.rules[0]
    assert "1,000 字以內" in study.rules[1] and "3,000 字以內" in study.rules[1]
    outbound = _archived_pdf_text("sources/nccu/outbound_115_1_guidelines.pdf")
    mainland = _archived_pdf_text("sources/nccu/oic_mainland_guidelines_base.pdf")
    assert "每份文件字數至少五百字，以兩頁為限" in outbound
    assert "1000字以內" in mainland and "3000字以內" in mainland

    report = WRITING_RULES[("nccu", "return-report")]
    assert report.min_chars is None and report.max_chars is None and not report.count_field_ids
    assert "2 個月內" in report.rules[0] and "5,000" in report.rules[0]
    assert "沒有公布交換心得報告的字數下限" in report.rules[1]


def test_ncku_writing_rules_match_archived_116_1_guidelines_and_scholarship_rules() -> None:
    study = WRITING_RULES[("ncku", "study-plan")]
    assert study.min_chars is None and study.max_chars is None and not study.count_field_ids
    assert "第一志願" in study.rules[0] and "25%" in study.rules[0]
    assert "50MB" in study.rules[1]
    guidelines = _archived_pdf_text("sources/ncku/116-1-guidelines.pdf")
    assert "第一志願" in guidelines and "25%" in guidelines and "50MB" in guidelines

    report = WRITING_RULES[("ncku", "return-report")]
    assert report.min_chars is None and report.max_chars is None and not report.count_field_ids
    assert "2 個月內" in report.rules[0] and "Word 及 PDF" in report.rules[0]
    assert "8,000" in report.rules[0] and "2,000" in report.rules[0]
    assert "1 個月內" in report.rules[1]


def test_nsysu_writing_rules_match_archived_55th_guidelines_and_bilingual_report_word_limits() -> None:
    study = WRITING_RULES[("nsysu", "study-plan")]
    assert study.min_chars is None and study.max_chars is None and not study.count_field_ids
    assert "20%" in study.rules[0]
    assert "1 頁 A4" in study.rules[1] and "1–2 頁 A4" in study.rules[1]
    stored = _stored_official_text("nsysu")
    regulations = _archived_pdf_text("sources/nsysu/nsysu_exchange_selection_regulations.pdf")
    assert "1 頁 A4 為限" in stored and "1–2 頁 A4" in stored
    assert "研修計畫書佔20%" in regulations

    report = WRITING_RULES[("nsysu", "return-report")]
    assert report.min_chars == 1500 and report.max_chars == 2000
    assert "1,500–2,000 字" in report.rules[0] and "1,000–1,500 字" in report.rules[0]
    assert "4 張" in report.rules[0]
    assert "1,500–2,000 字" in stored and "1,000–1,500 字" in stored


def test_nchu_writing_rules_match_archived_2027_fall_guidelines_and_scholarship_slides() -> None:
    study = WRITING_RULES[("nchu", "study-plan")]
    assert study.min_chars is None and study.max_chars is None and not study.count_field_ids
    assert "至多 A4 大小三面" in study.rules[0] and "第一志願" in study.rules[0]
    assert "1,000–1,500 字" in study.rules[1] and "2MB" in study.rules[1]
    guidelines = _archived_pdf_text("sources/nchu/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf")
    slides = _archived_pdf_text("sources/nchu/115-2_Exchange_Scholarship.pdf")
    assert "至多A4大小三面" in guidelines
    assert "1000-1500字" in slides

    report = WRITING_RULES[("nchu", "return-report")]
    assert report.min_chars is None and report.max_chars is None and not report.count_field_ids
    assert "2 個月內" in report.rules[0] and "3 小時" in report.rules[0]
    assert "2 週內" in report.rules[1] and "4 張照片" in report.rules[1]


def test_ntut_writing_rules_match_archived_step1_and_step3_html_and_photo_limit_is_5() -> None:
    study = WRITING_RULES[("ntut", "study-plan")]
    assert study.min_chars is None and study.max_chars is None and not study.count_field_ids
    assert "1 頁 A4 內" in study.rules[0]
    assert "1,000–1,500 字" in study.rules[1]
    step1 = (REPOSITORY / "sources/ntut/step1_internal_selection.html").read_text(encoding="utf-8")
    assert "1頁A4內簡述申請目的與預期效益" in step1
    assert "1000-1500字" in step1

    report = WRITING_RULES[("ntut", "return-report")]
    assert report.min_chars == 2000 and report.max_chars is None
    assert "2 週內" in report.rules[0] and "5 張" in report.rules[0]
    assert "2,000 字以上" in report.rules[1] and "3,000 字以上" in report.rules[1]
    step3 = (REPOSITORY / "sources/ntut/step3_pre_post_departure.html").read_text(encoding="utf-8")
    assert "2000字以上" in step3 and "3,000字以上" in step3
    template = next(t for t in all_application_templates("國立臺北科技大學") if t.id == "return-report")
    photos = next(field for field in template.fields if field.id == "activity_photos")
    assert photos.max_files >= 5, "NTUT requires 5 photos, so the form must accept at least 5"


def test_ntust_writing_rules_match_archived_115_2_intl_and_mainland_guidelines() -> None:
    study = WRITING_RULES[("ntust", "study-plan")]
    assert study.min_chars is None and study.max_chars is None and not study.count_field_ids
    assert "每份篇幅約 1–2 頁" in study.rules[0]
    assert "60%" in study.rules[2] and "20%" in study.rules[2]
    guidelines = _archived_pdf_text("sources/ntust/ntust_115_2_intl_guidelines_20260317.pdf")
    assert "每份篇幅約1-2頁" in guidelines

    report = WRITING_RULES[("ntust", "return-report")]
    assert report.min_chars is None and report.max_chars is None and not report.count_field_ids
    assert "30 天（1 個月）內" in report.rules[0]
    assert "沒有公布研修心得報告的固定字數" in report.rules[1]
    assert "結束交換後30天內" in guidelines and "應返校辦理報到" in guidelines


def test_guidance_text_never_claims_to_be_an_official_rule() -> None:
    for _, template in _all_templates():
        for field in template.fields:
            guidance = field.guidance
            if guidance is None:
                continue
            assert guidance.summary.strip()
            assert len(guidance.tips) <= 6 and len(guidance.outline) <= 6
            assert "學校規定" not in guidance.summary, f"{template.id}/{field.id}"


def test_template_endpoint_serves_guidance_and_school_rules(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-center/templates", params={"school": "國立臺北大學"})

    assert response.status_code == 200
    study_plan = next(row for row in response.json() if row["id"] == "study-plan")
    assert study_plan["writing_rules"]["max_chars"] == 5000
    assert study_plan["writing_rules"]["rules"][0] == "計畫書以 A4 紙直式橫書，合計 5,000 字以內，格式自訂。"
    assert study_plan["writing_rules"]["evidence"].startswith("臺北大學 116 學年度赴外交換簡章")
    assert study_plan["writing_rules"]["verified"] is True
    motivation = next(field for field in study_plan["fields"] if field["id"] == "motivation")
    assert motivation["max_length"] == 1800
    assert motivation["guidance"]["recommended_min_chars"] == 300
    assert motivation["guidance"]["tips"]
    assert re.search(r"[一-鿿]", motivation["guidance"]["example"])
    english = next(field for field in study_plan["fields"] if field["id"] == "english_version")
    assert english["guidance"]["recommended_max_chars"] is None


def test_reviewed_conditional_rules_do_not_force_old_generic_limits() -> None:
    keys = [(school, template) for school in ("pccu", "wzu", "nkust", "yuntech", "ntou", "yzu")
        for template in ("study-plan", "return-report")]
    for key in keys:
        rule = WRITING_RULES[key]
        assert rule.min_chars is None and rule.max_chars is None, key
        assert rule.source_url and rule.last_checked_at == "2026-10-21"
    assert "免研修計畫" in " ".join(WRITING_RULES[("nkust", "study-plan")].rules)
    assert "合計A4五頁" in " ".join(WRITING_RULES[("wzu", "study-plan")].rules)
    ntou = " ".join(WRITING_RULES[("ntou", "study-plan")].rules)
    assert "可選中文或英文一種" in ntou and "未支持全部合併單一PDF" in ntou
    assert "受獎生返國兩週" in " ".join(WRITING_RULES[("ntou", "return-report")].rules)
