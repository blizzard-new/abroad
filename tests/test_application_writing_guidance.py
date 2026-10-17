import re
from pathlib import Path

import exchange_info
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


def test_every_school_rule_is_backed_by_the_official_text_stored_for_that_school() -> None:
    """A word limit may only restate what the school's own stored page or guidelines say."""

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
    # Rules once drafted here that the stored official text does not support must stay out.
    assert ("yzu", "return-report") not in WRITING_RULES
    assert ("cycu", "return-report") not in WRITING_RULES
    assert ("ntust", "study-plan") not in WRITING_RULES
    assert not by_school["ntust"]["study-plan"].writing_rules.verified
    assert not by_school["cgu"]["study-plan"].writing_rules.verified


def test_writing_rules_are_attached_to_the_right_school_only() -> None:
    ntpu = {template.id: template for template in all_application_templates("國立臺北大學")}
    fju = {template.id: template for template in all_application_templates("輔仁大學")}

    assert ntpu["study-plan"].writing_rules.max_chars == 5000
    assert fju["return-report"].writing_rules.min_chars == 2000
    assert fju["study-plan"].writing_rules.max_chars is None  # 輔大以頁數規定，不以字數計
    assert ntpu["study-plan"].writing_rules is not fju["study-plan"].writing_rules


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
