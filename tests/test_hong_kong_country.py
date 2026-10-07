"""Hong Kong universities are in 香港, not 大陸地區, so choosing mainland China does not list them."""
from __future__ import annotations

import json
from pathlib import Path

from exchange_info import student_view
from exchange_info.models import PartnerUniversity
from exchange_info.student_view import PARTNER_COUNTRY_CORRECTIONS, fetch_partner_universities

DATA = Path("src/exchange_info/official_data")
CUHK = "香港中文大學 The Chinese University of Hong Kong"
CITYU = "香港城市大學 City University of Hong Kong"


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _sheet(country_by_school: dict[str, str]):
    def fetch(**kwargs):
        if kwargs["program_type"].startswith("雙學位"):
            return []
        return [PartnerUniversity(program_type=kwargs["program_type"], country=country, school_name=name, source_url=kwargs["source_url"])
                for name, country in country_by_school.items()]
    return fetch


def test_cgu_sheet_files_two_hong_kong_universities_under_the_mainland_and_we_correct_it(monkeypatch) -> None:
    monkeypatch.setattr(student_view, "_fetch_sheet_rows", _sheet({
        CUHK: "大陸地區", CITYU: "大陸地區", "北京清華大學 Tsinghua University": "大陸地區", "日本九州大學 Kyushu University": "日本",
    }))
    by_name = {row.school_name: row.country for row in fetch_partner_universities()}
    assert by_name[CUHK] == "香港" and by_name[CITYU] == "香港"
    assert by_name["北京清華大學 Tsinghua University"] == "大陸地區", "the mainland ones stay"
    assert by_name["日本九州大學 Kyushu University"] == "日本"


def test_the_correction_is_by_name_so_a_mainland_campus_stays_in_the_mainland(monkeypatch) -> None:
    shenzhen = "香港中文大學（深圳） The Chinese University of Hong Kong, Shenzhen"
    monkeypatch.setattr(student_view, "_fetch_sheet_rows", _sheet({CUHK: "大陸地區", shenzhen: "大陸地區"}))
    by_name = {row.school_name: row.country for row in fetch_partner_universities()}
    assert by_name[CUHK] == "香港" and by_name[shenzhen] == "大陸地區"


def test_a_sheet_that_already_says_hong_kong_is_left_alone(monkeypatch) -> None:
    monkeypatch.setattr(student_view, "_fetch_sheet_rows", _sheet({CUHK: "香港"}))
    assert {row.school_name: row.country for row in fetch_partner_universities()}[CUHK] == "香港"


def test_the_corrections_are_just_these_two_schools() -> None:
    assert set(PARTNER_COUNTRY_CORRECTIONS.values()) == {"香港"} and len(PARTNER_COUNTRY_CORRECTIONS) == 2


def test_the_bundled_data_agrees_on_hong_kong() -> None:
    workflows = [row for row in _rows(DATA / "cgu" / "application_workflows.jsonl") if row["school_name"] in {CUHK, CITYU}]
    assert len(workflows) == 4 and {row["country"] for row in workflows} == {"香港"}
    profiles = {row["school_name"]: row["country"] for row in _rows(DATA / "cgu" / "destination_profiles.jsonl")}
    locations = {row["school_name"]: row["country"] for row in _rows(DATA / "university_locations.jsonl")}
    for name in (CUHK, CITYU):
        assert profiles[name] == locations[name] == "香港", name


def test_no_bundled_school_named_for_hong_kong_is_filed_under_the_mainland_except_a_mainland_campus() -> None:
    for path in (DATA / "cgu" / "application_workflows.jsonl", DATA / "ntpu" / "application_workflows.jsonl",
                 DATA / "university_locations.jsonl"):
        for row in _rows(path):
            name = row["school_name"]
            if (name.startswith("香港") or "of Hong Kong" in name) and "深圳" not in name and "Shenzhen" not in name:
                assert row["country"] == "香港", (path.name, name, row["country"])
