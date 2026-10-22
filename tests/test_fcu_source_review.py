from __future__ import annotations

import copy
from pathlib import Path

import pytest

from exchange_info.application_rules import _partner_language_threshold
from exchange_info.fcu_source_review import (
    SOURCE_FILE, apply_program_review, load_reviewed_programs, review_common_text,
)
from exchange_info.fcu_student_view import fetch_fcu_partner_universities
from exchange_info.models import PartnerUniversity

ROOT = Path(__file__).resolve().parents[1]


def test_distinct_programs_keep_their_own_degrees_fees_and_language_conditions():
    schools = {p.school_name: p for p in fetch_fcu_partner_universities()}
    temple = schools["天普大學 Temple University"]
    exchange, dual = temple.program_options
    assert "1151_1042" in exchange.program_type and "學費全免" in exchange.program_type
    assert "碩士班" in exchange.degree_levels and "IELTS 6.0" in exchange.eligibility
    assert "1151_A000" in dual.program_type and "學費全額" in dual.program_type
    assert dual.degree_levels == "大學部" and "IELTS 6.5" in dual.eligibility
    assert "不能套用交換一學期" in dual.study_period
    cincinnati = schools["辛辛那提大學 University of Cincinnati"]
    first, second = cincinnati.program_options
    assert "建築專業學院" in first.colleges and "建築專業學院" not in second.colleges
    assert "PTE 47" in first.eligibility and "PTE 59" in second.eligibility
    # An unresolved duplicate in the official source cannot silently sum quotas.
    guam = schools["關島大學 University of Guam"]
    assert len(guam.program_options) == 2
    assert [p.quota for p in guam.program_options] == ["1 名", "1 名"]


def test_unmatched_existing_school_is_preserved_without_inventing_eligibility():
    p = next(x for x in fetch_fcu_partner_universities() if x.school_name.startswith("北京理工大學 "))
    assert p.availability_status == "needs_confirmation"
    assert "5 名" in p.reference_data["quota"]
    assert "待確認" in p.quota
    assert "不能推論已終止合作" in p.availability_note
    assert not p.program_options


@pytest.mark.parametrize("status", ["reference_only", "needs_confirmation", "conflict", "missing"])
def test_source_review_hold_prevents_regex_score_from_becoming_current_threshold(status):
    p = PartnerUniversity(
        school_name="歷史方案", program_type="交換", source_url="https://example.edu/",
        eligibility="IELTS 5.0 或 TOEFL iBT 61",
        field_evidence={"language_requirement": {
            "source_url": "https://example.edu/", "checked_at": "2026-10-20T00:00:00Z",
            "status": status,
        }},
    )
    assert _partner_language_threshold(p, "ielts", "碩士班") is None
    assert _partner_language_threshold(p, "toefl", "學士班") is None


def test_review_transform_is_idempotent_and_snapshot_cannot_change_silently(tmp_path):
    rows = load_reviewed_programs(ROOT)
    assert len(rows) == 148  # Includes the home university placeholder, not a partner.
    p = fetch_fcu_partner_universities()[0].model_dump(mode="json")
    apply_program_review(p, rows)
    once = copy.deepcopy(p)
    apply_program_review(p, rows)
    assert p == once
    source = tmp_path / SOURCE_FILE
    source.parent.mkdir(parents=True)
    source.write_text('{"data": []}', encoding="utf8")
    with pytest.raises(ValueError, match="new scope review"):
        load_reviewed_programs(tmp_path)


def test_shared_grant_correction_does_not_rewrite_host_tuition_or_an_award_receipt():
    for text in (
        "出國研修獎助學金 NT$13,000（1名）",
        "Tuition: Approx. $9,000 USD per semester.",
    ):
        assert review_common_text(text) == text
    text = "逢甲大學出國研修獎助學金（初審自動納入審核）：國際地區系排前 10% NT$13,000。"
    revised = review_common_text(text)
    assert "不是按排名保證固定金額" in revised
    assert review_common_text(revised) == revised
