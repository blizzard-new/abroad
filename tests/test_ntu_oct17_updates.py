"""Keep October 17 source revisions within their year, authority and conditions."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from fastapi.testclient import TestClient
from pypdf import PdfReader
import pytest

from exchange_info.api import create_app
from exchange_info.ntu_oct17_updates import IDS, UK_IDS, SOURCE, apply_updates, load_update
from exchange_info.ntu_student_view import fetch_ntu_partner_universities

BUNDLE = Path("src/exchange_info/official_data/ntu")


def partners():
    return {p.source_url.rsplit("/", 1)[-1]: p for p in fetch_ntu_partner_universities()}


def files(bundle):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir() if p.is_file()}


def test_reviewed_inventory_matches_archives_and_keeps_warning_scope():
    data = load_update()
    assert len(data["source_manifest"]) == 37
    assert {s["portal_id"] for s in data["schools"]} == IDS
    assert {s["portal_id"] for s in data["schools"] if not s["pending_warning_present"]} == UK_IDS
    assert all(s["formal_selection_quota"] is None and not s["whole_cycle_confirmed"] for s in data["schools"])
    assert len(data["unknown_original_attachments"]) == 6
    assert all(not a["original_restored"] for a in data["unknown_original_attachments"])
    assert data["parent_full_check"]["locally_reperformed_full_97_comparison"] is False


def test_untouched_rows_workflows_life_and_historical_sources_are_byte_preserved():
    data = load_update()
    rows = {json.loads(r)["source_url"].rsplit("/", 1)[-1]: hashlib.sha256(r.encode()).hexdigest()
            for r in (BUNDLE / "partners.jsonl").read_text().splitlines()}
    assert len(data["protected_partner_row_sha256"]) == 262
    assert data["review_corrections_20261017"]["uw_partner_before_sha256"]
    assert {pid: rows[pid] for pid in data["protected_partner_row_sha256"]} == data["protected_partner_row_sha256"]
    for name, expected in data["protected_bundle_sha256"].items():
        content = (BUNDLE / name).read_bytes()
        if name == "student_life.jsonl":
            # Round 23 later corrected USP. Restore only its pinned old values
            # in memory, then retain the full historical-file checksum check.
            from exchange_info.usp_source_review import load_manifest, pointer_parent
            scope = next(r for r in load_manifest(Path(__file__).resolve().parents[1])["rows"] if r["home_id"] == "ntu")
            life_rows = [json.loads(line) for line in content.splitlines()]
            for row in life_rows:
                if row["school_name"] != scope["school_name"]:
                    continue
                for patch in scope["patches"]:
                    parent, key = pointer_parent(row, patch["pointer"])
                    parent[key] = patch["expected_values"][0]
                archive = row.get("reference_data", {})
                archive.pop("source_review_round23", None)
                if not archive:
                    row.pop("reference_data", None)
            content = ("\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in life_rows) + "\n").encode()
        assert hashlib.sha256(content).hexdigest() == expected
    for name, key in [("2026-10-14-official-update.json", "prior_current_source_sha256"),
                      ("completion-2026-10-11.json", "legacy_completion_source_sha256")]:
        assert hashlib.sha256((SOURCE.parent / name).read_bytes()).hexdigest() == data[key]
    old = json.loads((SOURCE.parent / "completion-2026-10-11.json").read_text())
    current = partners()
    for school in old["schools"]:
        for observation in school["observations"]:
            assert observation["text_zh"] in current[school["portal_id"]].application_info


def test_reference_capacity_cannot_replace_the_formal_list():
    current = partners()
    assert len(current) == 289
    assert sum(p.quota_status == "published" for p in current.values()) == 20
    assert sum(p.quota is None for p in current.values()) == 262
    assert sum(p.quota == "0 名" for p in current.values()) == 7
    for pid in IDS:
        p = current[pid]
        assert p.quota is None and p.quota_status in (None, "not_published")
        assert p.availability_status != "open"
        assert p.application_window_status in (None, "needs_confirmation")
        assert "2026-11-09" in p.application_deadline
        assert p.field_evidence["eligibility"].status == "reference_only"
        assert p.field_evidence["language"].academic_year is None
    assert "4" in current["115"].reference_data["portal_detail_quota_reference_20261017"]
    assert "讀 4.5 聽 5.0 說 4.0 寫 4.5" in current["1"].eligibility


def test_warning_free_uk_pages_only_date_explicit_fields():
    current = partners()
    for pid in UK_IDS:
        assert current[pid].field_evidence["eligibility"].academic_year is None
    assert current["1291"].partner_exchange_details["calendar"].evidence[0].academic_year == "2027/2028"
    assert "2027" in current["1291"].partner_exchange_details["calendar"].value
    assert current["1093"].partner_exchange_details["calendar"].evidence[0].academic_year == "116-1"
    assert "Autumn Term" in current["1093"].study_period
    assert "對照" in current["4"].language_review_note
    assert "個別研究所課程" in current["1002"].language_review_note
    assert current["2"].reference_data["second_exchange_marker_20261017"] == "not_stated"


def test_receiving_references_retain_original_page_quotes_and_periods():
    data = load_update()
    refs = {r["portal_id"]: r for r in data["receiving_references"]}
    normalize = lambda text: re.sub(r"\s+", " ", text).strip()
    for ref in refs.values():
        source = Path(data["source_manifest"][ref["source_id"]]["local_file"])
        pdf = PdfReader(source) if ref["page_count"] else None
        for fact in ref["facts"]:
            raw = pdf.pages[fact["page"] - 1].extract_text() if pdf else source.read_text()
            assert normalize(fact["source_excerpt"]) in normalize(raw)
    current = partners()
    assert "2027/4/15" in current["974"].partner_exchange_details["deadlines"].value
    cover = current["974"].partner_exchange_details["documents"]
    assert "已核實" in cover.value and "Fact Sheet 2027" in cover.value
    assert cover.status == "reference_only" and cover.evidence[0].academic_year == "2027"
    assert cover.evidence[0].source_pages == [1]
    assert current["974"].partner_exchange_details["calendar"].evidence[0].academic_year == "2027"
    assert refs["115"]["mirror_equality_basis"]
    assert current["115"].partner_exchange_details["deadlines"].evidence[0].academic_year == "2027/2028"
    assert current["115"].partner_exchange_details["insurance_visa"].evidence[0].academic_year == "2026/2027"
    assert current["2"].partner_exchange_details["deadlines"].evidence[0].academic_year == "2026/2027"
    assert current["60"].partner_exchange_details["calendar"].evidence[0].source_pages == []
    assert "Sway" in refs["60"]["source_relation"]


def test_uw_document_nomination_quote_is_on_page_three_before_visa_page_four():
    current = json.loads((SOURCE.parent / "2026-10-14-official-update.json").read_text())
    uw = current["uw_update"]
    path = Path(current["source_manifest"][uw["source_id"]]["local_file"])
    pdf = PdfReader(path)
    normalize = lambda text: re.sub(r"\s+", " ", text).strip()
    assert "two weeks prior to student’s application deadlines" in normalize(pdf.pages[2].extract_text())
    assert "DS-2019" in pdf.pages[3].extract_text()
    evidence = partners()["7"].partner_exchange_details["documents"].evidence[0]
    assert evidence.source_pages == [3, 4] and evidence.status == "reference_only"
    assert evidence.academic_year == "2027/2028"


def test_colombia_conflict_and_conditional_housing_are_visible():
    current = partners()
    cost = current["1283"].partner_exchange_details["cost"]
    assert cost.status == "conflict" and len(cost.evidence) == 2
    assert "18,400,000–27,700,000" in cost.value and "17,100,000–25,300,000" in cost.value
    assert cost.evidence[0].academic_year == "2026/2027" and cost.evidence[1].academic_year is None
    assert "不蓋過臺大B2" in current["1283"].partner_exchange_details["language"].value
    for pid in ("326", "203"):
        housing = current[pid].partner_exchange_details["housing"]
        assert "期限前" in housing.value and "deadline" in housing.value.lower()
        assert housing.status == "reference_only"


def test_information_session_has_no_selection_deadline_or_reminder(tmp_path):
    data = load_update()
    event = data["event"]
    assert event["start"] == "2026-10-30T12:30:00+08:00"
    assert event["registration_deadline"] is None and not event["reminder_eligible"]
    assert event["parent_form_receipt"]["local_form_bytes_obtained"] is False
    assert "10/30" in partners()["1289"].application_info
    client = TestClient(create_app(tmp_path))
    deadlines = client.get("/deadlines", params={"school": "NTU"}).json()
    assert "2026-10-30" not in str(deadlines) and "哥廷根" not in str(deadlines)


def test_public_reference_renderer_names_ntu_and_exposes_its_fields():
    current = partners()
    script = r'''
    const assert=require('node:assert/strict'), fs=require('node:fs');
    const window={}; eval(fs.readFileSync(process.argv[1],'utf8'));
    const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
    const partners=JSON.parse(fs.readFileSync(0,'utf8'));
    const rendered=partners.map(p=>window.UniWayCcuDetails.render(p,escape,undefined,'國立臺灣大學'));
    for (const html of rendered) {
      assert.match(html,/臺大的校內資格/); assert.ok(!html.includes('中正的校內資格'));
      assert.ok(!html.includes('undefined')); assert.ok(!html.includes('已有當期依據'));
    }
    assert.match(rendered[0],/合作校提名與申請期限/); assert.match(rendered[0],/2027\/4\/15/);
    assert.match(rendered[0],/#page=7/); assert.match(rendered[1],/費用與生活預算/);
    assert.match(rendered[1],/來源矛盾，待確認/); assert.match(rendered[2],/2026\/2027/);
    assert.match(rendered[3],/校曆與考試/); assert.match(rendered[4],/期限前/);
    const original=window.UniWayCcuDetails.render(partners[0],escape);
    assert.match(original,/中正的校內資格/);
    '''
    result = subprocess.run(["node", "-e", script, str(Path("src/exchange_info/static/ccu-partner-details.js").resolve())],
                            input=json.dumps([current[pid].model_dump(mode="json") for pid in ("974", "1283", "115", "1093", "326")]),
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_reapplying_oct17_is_byte_idempotent(tmp_path):
    bundle = tmp_path / "bundle"
    shutil.copytree(BUNDLE, bundle)
    before = files(bundle)
    assert apply_updates(bundle) == {"updated_portals": 25, "receiving_references": 5,
                                     "information_sessions": 1, "formal_quota_changed": False}
    assert files(bundle) == before
    apply_updates(bundle)
    assert files(bundle) == before


@pytest.mark.parametrize("failure", ["quota", "archive", "qualification", "warning", "field_year", "old_price_year", "event", "open"])
def test_unreviewed_or_unscoped_batch_fails_before_any_write(tmp_path, failure):
    data = json.loads(SOURCE.read_text())
    if failure == "quota": data["list_receipt"]["rows"][0]["quota"] = "99 名"
    elif failure == "archive": next(iter(data["source_manifest"].values()))["sha256"] = "0" * 64
    elif failure == "qualification": data["schools"][0]["platform_after"]["eligibility"] = "unreviewed"
    elif failure == "warning": data["schools"][0]["pending_warning_present"] = False
    elif failure == "field_year": data["schools"][0]["calendar_academic_year"] = "2027/2028"
    elif failure == "old_price_year": data["receiving_references"][1]["facts"][1]["academic_year"] = "2027/2028"
    elif failure == "event": data["event"]["registration_deadline"] = "2026-10-30"
    else: data["application_open_confirmed"] = True
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(data))
    bundle = tmp_path / "bundle"
    shutil.copytree(BUNDLE, bundle)
    before = files(bundle)
    with pytest.raises(ValueError): apply_updates(bundle, path)
    assert files(bundle) == before
