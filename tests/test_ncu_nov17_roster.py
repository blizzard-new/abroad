from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import hashlib
import json

from exchange_info.models import DestinationProfile, UniversityApplicationWorkflow
from exchange_info.ncu_student_view import build_ncu_student_dashboard, fetch_ncu_partner_universities

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ncu"
SOURCES = ROOT / "sources/ncu/2026-11-17"
PDF = "https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangeschoollist-1117.pdf"


def bundle(path, model):
    with (BUNDLE / path).open() as handle:
        return {row.school_name: row for row in (model.model_validate_json(line) for line in handle)}


def test_ncu_all_rows_and_well_scoped_options():
    rows = json.loads((SOURCES / "quota-116-1-rows.json").read_text())
    report = json.loads((BUNDLE / "catalog-completeness.json").read_text())
    assert hashlib.sha256((SOURCES / PDF.split("/")[-1]).read_bytes()).hexdigest() == report["current_list_sha256"]
    assert report["current_list_rows"] == len(rows) == 215
    partners = fetch_ncu_partner_universities()
    assert len(partners) == len({p.school_name for p in partners}) == 222
    assert Counter(p.availability_status for p in partners) == {"open":206,"fee_paying":8,"not_open":8}
    found = defaultdict(list)
    for p in partners:
        for pg in p.source_pages:
            found[pg].append(p)
        assert p.field_evidence["quota"].source_url.startswith(PDF)
        assert "預定2026/10/12" not in p.availability_note
        assert not p.nomination_deadline and not p.partner_application_deadline
    for row in rows:
        marker = f"第 {row['page']} 頁第 {row['table_row']} 列，"
        matches = [p for p in found[row["page"]] if marker in p.availability_note]
        assert len(matches) == 1
        p = matches[0]
        assert row["quota"] in p.quota
        if row["language"]:
            assert row["language"] in p.language_requirement
        assert row["notes"] in p.availability_note
    assert sum(bool(p.colleges) for p in partners) == 48
    assert sum(bool(p.degree_levels) for p in partners) == 25
    assert sum(bool(p.language_requirement) for p in partners) == 207
    mahidol = next(p for p in partners if "Mahidol" in p.school_name)
    assert "限機械系" in mahidol.colleges and "Communication Technology" in mahidol.colleges
    davis = next(p for p in partners if "UC Davis" in p.school_name)
    assert davis.availability_status == "fee_paying" and "大學部" in davis.degree_levels
    florida = next(p for p in partners if p.school_name.endswith("University of Florida"))
    assert florida.quota == "2" and "限電機系" in florida.colleges
    assert "限交換一學期" not in florida.availability_note
    assert "未列入" in next(p for p in partners if "EDHEC" in p.school_name).availability_note
    nanyang = next(p for p in partners if "Nanyang Technological" in p.school_name)
    assert [o.quota for o in nanyang.program_options] == ["6","6"]


def test_ncu_eight_new_school_cards_reach_a_real_home_workflow_and_living_source():
    living = json.loads((SOURCES / "incoming-resources.json").read_text())
    assert len(living) == 8
    partners = {p.school_name:p for p in fetch_ncu_partner_universities()}
    flows = bundle("application_workflows.jsonl", UniversityApplicationWorkflow)
    guides = bundle("destination_profiles.jsonl", DestinationProfile)
    assert set(partners) == set(flows) == set(guides)
    for name, ref in living.items():
        assert partners[name].website == ref["url"]
        flow = flows[name]
        by_id = {step.rule_id:step for step in flow.steps}
        assert PDF in by_id["ncu-116-1-home-1"].action_url
        assert by_id["ncu-116-1-home-2"].submission.portal_url == "https://beta.abroad.oia.ncu.edu.tw/"
        assert by_id["ncu-116-1-home-3"].document_requirements
        assert by_id["ncu-116-1-home-3"].submission.method == "paper"
        host = next(s for s in flow.steps if s.phase == "合作校申請")
        assert host.needs_confirmation and host.deadline_at is None
        assert any(ref["url"] in s.source_urls for s in guides[name].student_guide_sections)
        assert guides[name].campus_life_summary


def test_ncu_current_roster_keeps_school_and_host_windows_separate():
    for stamp, status in [("2026-11-16T08:59:59+08:00","upcoming"),("2026-11-16T09:00:00+08:00","open"),
                          ("2026-12-04T12:00:00+08:00","open"),("2026-12-04T12:00:01+08:00","closed")]:
        d = build_ncu_student_dashboard(reference_time=datetime.fromisoformat(stamp))
        assert d.application_periods[0].status.value == status
        assert {p.application_window_status for p in d.partner_universities if p.quota} == {status}
        assert all(p.application_window_status is None for p in d.partner_universities if not p.quota)
