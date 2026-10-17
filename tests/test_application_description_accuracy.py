from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import pytest
from pypdf import PdfReader

from exchange_info.application_documents import all_application_templates

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "exchange_info" / "official_data"


def _template(school: str, template_id: str):
    return next(t for t in all_application_templates(school) if t.id == template_id)


@lru_cache(maxsize=None)
def _stored_text(school: str) -> str:
    pages = [
        json.loads(line)["text"]
        for line in (DATA / school / "pages.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    documents = (DATA / school / "documents.json").read_text(encoding="utf-8")
    return "\n".join(pages) + documents


@lru_cache(maxsize=None)
def _archived_pdf_text(relative_path: str) -> str:
    reader = PdfReader(ROOT / relative_path)
    return re.sub(r"\s+", "", "".join(page.extract_text() or "" for page in reader.pages))


def test_yzu_return_report_follows_the_official_deposit_page() -> None:
    template = _template("yzu", "return-report")
    stored = _stored_text("yzu")
    assert "2 週內繳交 1,500 字以上研修心得報告與 6 張照片" in stored
    assert "2 週內" in template.description
    assert "1,500 字以上" in template.description
    assert "6 張照片" in template.description
    for unsupported in ("2,000", "4 張", "二個月內，向全球事務處"):
        assert unsupported not in template.description
    assert "二個月" not in template.stage
    # 兩個月是返校期限（切結書第十條），不是心得報告期限。
    undertaking = _archived_pdf_text("sources/yzu/yzu_letter_of_undertaking_cf04.pdf")
    assert "交換期滿後兩個月內，應返回元智大學" in undertaking
    assert "回國後14日內繳交電子機票" in undertaking


def test_yzu_study_plan_is_not_the_cf02r3_application_form() -> None:
    template = _template("yzu", "study-plan")
    stored = _stored_text("yzu")
    assert "申請表（CF-02-R3" in stored
    assert "系排名成績 50%＋英文檢定成績 50%" in stored
    assert template.official_form_number is None
    assert "研修計畫書》（CF-02-R3）" not in template.description
    assert "《出國交換學生申請表》" in template.description
    assert "系排名 50%＋英文檢定 50%" in template.description
    assert "30%" not in template.description
    form = _archived_pdf_text("sources/yzu/yzu_application_form_cf02r3.pdf")
    assert "元智大學赴外交流學生報名表" in form


def test_yzu_scoring_text_is_consistent_across_the_adapter() -> None:
    application = _template("yzu", "exchange-application-data")
    assert "30%" not in application.description
    assert "40%" not in application.description
    assert "最多 5 所" not in application.description
    fields = {field.id: field for field in application.fields}
    for field_id in ("class_rank_percent", "language_test"):
        help_text = fields[field_id].help_text or ""
        assert "50%" in help_text
        assert "30%" not in help_text and "40%" not in help_text


def test_cycu_return_report_only_states_what_the_archived_rules_say() -> None:
    template = _template("cycu", "return-report")
    assert "1,500" not in _stored_text("cycu")
    for unsupported in ("1,500", "二個月", "照片授權"):
        assert unsupported not in template.description
    assert "二個月" not in template.stage
    assert "二週" in template.description and "二週" in template.stage
    rules = _archived_pdf_text("sources/cycu/cycu_exchange_scholarship_rules_536_2.pdf")
    assert "返國後二周內提交研習成果報告書" in rules


def test_cycu_study_plan_lists_only_stored_requirements() -> None:
    template = _template("cycu", "study-plan")
    stored = _stored_text("cycu")
    assert "中文及英文讀書計畫（Study Plan）" in stored
    assert "讀書計畫 20%" in stored
    assert "中文及英文讀書計畫" in template.description
    assert "中文及英文自傳" in template.description
    for unsupported in ("研究主題", "學涯", "學分規劃"):
        assert unsupported not in template.description


def test_ntust_study_plan_is_not_weighted_in_the_total_score() -> None:
    template = _template("ntust", "study-plan")
    stored = _stored_text("ntust")
    assert "課外表現與獲獎紀錄 20%" in stored
    assert "課外表現與讀書計畫" not in template.description
    assert "外語檢定 60%、在校學業 20%、課外表現證明 20%" in template.description
    guidelines = _archived_pdf_text("sources/ntust/ntust_115_2_intl_guidelines_20260317.pdf")
    assert "中、英文讀書計畫各一份" in guidelines
    assert "每份篇幅約1-2頁" in guidelines


def test_ntnu_study_plan_is_the_combined_autobiography_and_plan() -> None:
    template = _template("ntnu", "study-plan")
    stored = _stored_text("ntnu")
    assert "中英文合計須介於 500 至 5,000 字之間" in stored
    assert "自傳及出國學習計畫 20%" in stored
    assert "自傳與出國學習計畫" in template.description
    assert "500–5,000 字" in template.description
    assert "20%" in template.description
    for unsupported in ("研究主題", "返國後學術連結", "第一志願姊妹校"):
        assert unsupported not in template.description
    brochure = _archived_pdf_text("sources/ntnu/OE116-1_SPRING2027.pdf")
    assert "一千字以上之中文或外文自傳" in brochure
    assert "500至5000字之間" in brochure


def test_fcu_study_plan_follows_the_brochure_content_list() -> None:
    template = _template("fcu", "study-plan")
    brochure = _archived_pdf_text("sources/fcu/fcu_115_1_spring2027_guidelines.pdf")
    assert "至少1,000字" in brochure
    for required in ("個人自傳", "赴國外研修之動機", "出國前於本校之研修學習計畫", "赴國外大學之研修學習計畫"):
        assert required in brochure
        assert required in template.description
    assert "返國後學習連結" not in template.description
