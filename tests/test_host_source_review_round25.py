"""Admission-scope conflicts, independent edits and replay through public models."""
import json
import shutil
import subprocess
from pathlib import Path

from exchange_info.host_source_review_round25 import MANIFEST, apply_host_source_review, load_manifest, pointer_parent
from exchange_info.models import PartnerUniversity, UniversityApplicationWorkflow

ROOT = Path(__file__).resolve().parents[1]
SCHOOLS = ("scu", "cycu", "fju", "yuntech")


def historical_fixture(root):
    manifest = load_manifest(ROOT)
    (root / MANIFEST).parent.mkdir(parents=True)
    shutil.copy2(ROOT / MANIFEST, root / MANIFEST)
    for scope in manifest["rows"]:
        source = ROOT / scope["file"]
        rows = [json.loads(line) for line in source.read_text("utf8").splitlines()]
        row = next(r for r in rows if r["school_name"] == scope["school_name"])
        for patch in scope["patches"]:
            parent, key = pointer_parent(row, patch["pointer"], create=True)
            if patch["expected_missing"]:
                parent.pop(key, None)
            else:
                parent[key] = patch["expected_values"][0]
        row.get("reference_data", {}).pop("source_review_round25", None)
        target = root / scope["file"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf8")
    return manifest


def partner(root, school):
    filename = root / f"src/exchange_info/official_data/{school}/partners.jsonl"
    return next(json.loads(line) for line in filename.read_text("utf8").splitlines()
                if ("Kurume" if school == "scu" else "Pittsburg") in json.loads(line)["school_name"])


def test_scoped_corrections_preserve_mother_requirements_and_replay_bytes(tmp_path):
    manifest = historical_fixture(tmp_path)
    previous = {s: partner(tmp_path, s) for s in SCHOOLS}
    assert sum(apply_host_source_review(tmp_path, s) for s in SCHOOLS) == 49
    for school in SCHOOLS:
        p = partner(tmp_path, school)
        model = PartnerUniversity.model_validate(p)
        assert p["gpa_requirement"] == previous[school]["gpa_requirement"]
        assert p["quota"] == previous[school]["quota"]
        assert p["availability_status"] == previous[school]["availability_status"]
        assert isinstance(p["reference_data"]["source_review_round25"], str)
        if school == "scu":
            assert model.partner_exchange_details["program_scope"].status == "conflict"
            assert "不代表一般學部／研究所交換全部取消" in p["course_restrictions"]
            assert "全校各學院" not in p["colleges"]
        else:
            assert model.partner_exchange_details["application_fee"].status == "reference_only"
            assert "60美元" in model.partner_exchange_details["application_fee"].value
            assert model.partner_exchange_details["application_deadline"].value is None
    assert "未列Duolingo" in partner(tmp_path, "cycu")["language_requirement"]
    assert "79" in partner(tmp_path, "fju")["language_requirement"]
    assert "Quota for" not in partner(tmp_path, "yuntech")["housing_info"]
    for scope in manifest["rows"]:
        if scope["file"].endswith("destination_profiles.jsonl"):
            row = next(r for r in map(json.loads, (tmp_path / scope["file"]).read_text("utf8").splitlines())
                       if r["school_name"] == scope["school_name"])
            assert row["coverage_status"] == "official_partial"
            assert row["last_checked"] == manifest["reviewed_at"]
            assert {p["source_url"] for p in scope["patches"]} <= {s["source_url"] for s in row["sources"]}
        if scope["file"].endswith("application_workflows.jsonl"):
            for line in (tmp_path / scope["file"]).read_text("utf8").splitlines():
                UniversityApplicationWorkflow.model_validate(json.loads(line))
    before = {s["file"]: (tmp_path / s["file"]).read_bytes() for s in manifest["rows"]}
    assert sum(apply_host_source_review(tmp_path, s) for s in SCHOOLS) == 0
    assert before == {f: (tmp_path / f).read_bytes() for f in before}


def test_independent_host_advice_and_new_detail_survive(tmp_path):
    historical_fixture(tmp_path)
    path = tmp_path / "src/exchange_info/official_data/cycu/partners.jsonl"
    rows = [json.loads(line) for line in path.read_text("utf8").splitlines()]
    row = next(r for r in rows if "Pittsburg" in r["school_name"])
    row["language_requirement"] = "New independent department confirmation"
    row["partner_exchange_details"]["language"] = {"value": "Independent source", "status": "needs_confirmation", "reason": "Separate department"}
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf8")
    apply_host_source_review(tmp_path, "cycu")
    revised = partner(tmp_path, "cycu")
    assert revised["language_requirement"] == "New independent department confirmation"
    assert revised["partner_exchange_details"]["language"]["value"] == "Independent source"
    assert "application_fee" in revised["partner_exchange_details"]


def test_public_cards_identify_home_school_and_keep_undated_sources_scoped(tmp_path):
    historical_fixture(tmp_path)
    for school in SCHOOLS:
        apply_host_source_review(tmp_path, school)
    script = r'''
    const assert=require('node:assert/strict'),fs=require('node:fs');
    const window={};eval(fs.readFileSync(process.argv[1],'utf8'));
    const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
    const rows=JSON.parse(fs.readFileSync(0,'utf8'));
    for(const [home,partner] of rows) {
      const html=window.UniWayCcuDetails.render(partner,escape,undefined,home);
      assert.ok(html.includes(`${escape(home)}的校內資格`));
      assert.ok(!html.includes('中正的校內資格'));
      assert.ok(!html.includes('已有當期依據'));
      assert.ok(!html.includes('undefined'));
      assert.ok(!html.includes('<script>'));
    }
    assert.match(window.UniWayCcuDetails.render(rows[1][1],escape,undefined,rows[1][0]),/合作校申請費/);
    '''
    payload = [(home, partner(tmp_path, school)) for school, home in zip(SCHOOLS,
        ["東吳大學", "中原大學", "輔仁大學", "國立雲林科技大學<script>"])]
    result = subprocess.run(["node", "-e", script, str(ROOT / "src/exchange_info/static/ccu-partner-details.js")],
                            input=json.dumps(payload), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
