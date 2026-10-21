"""Historical programs must retain their term when exposed under a newer cycle."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PartnerUniversity
from exchange_info.ntnu_program_year_review import MANIFEST, apply_ntnu_program_year_review, load_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_program_year_mapping_matches_archived_generator_inputs():
    manifest = load_manifest(ROOT)
    terms = {}
    for source in manifest["sources"][:3]:
        raw = (ROOT / source["file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source["sha256"]
        terms[Path(source["file"]).stem.rsplit("_", 1)[1]] = json.loads(raw)
    for school in manifest["program_years"]:
        seen, expected = set(), Counter()
        for term, records in terms.items():
            for record in records:
                if record["school_no"] != school["school_no"]:
                    continue
                for program in record.get("programs") or []:
                    key = (record.get("contract_level", "校級"), record.get("organizer", "國際事務處"),
                           (program.get("program_name") or "一般學程").strip())
                    if key not in seen:
                        seen.add(key)
                        expected[term] += 1
        assert dict(expected) == school["program_counts_by_term"]
    waseda = next(r for r in manifest["program_years"] if r["school_no"] == "JP-007-WU")
    assert waseda["program_counts_by_term"] == {"1152": 5, "1151": 2}
    assert waseda["only_historical_programs"]
    assert manifest["latest_api_check"]["data_available"] is False
    assert manifest["latest_api_check"]["application_status"] == "S9910"


def test_replay_preserves_independent_changes_and_unaffected_schools(tmp_path):
    manifest = load_manifest(ROOT)
    (tmp_path / MANIFEST).parent.mkdir(parents=True)
    shutil.copy2(ROOT / MANIFEST, tmp_path / MANIFEST)
    scopes = {}
    for scope in manifest["rows"]:
        scopes.setdefault(scope["file"], []).append(scope)
    untouched = {}
    for relative, file_scopes in scopes.items():
        rows = [json.loads(line) for line in (ROOT / relative).read_text("utf8").splitlines()]
        by_name = {r["school_name"]: r for r in rows}
        for scope in file_scopes:
            row = by_name[scope["school_name"]]
            row.get("reference_data", {}).pop("source_review_round38", None)
            for patch in scope["patches"]:
                parent, key = pointer_parent(row, patch["pointer"])
                parent[key] = patch["expected_values"][0]
        if relative.endswith("/partners.jsonl"):
            by_name["早稻田大學 Waseda University"]["language_requirement"] = "Independent newer school confirmation"
        names = {s["school_name"] for s in file_scopes}
        untouched[relative] = {r["school_name"]: r for r in rows if r["school_name"] not in names}
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf8")
    assert apply_ntnu_program_year_review(tmp_path) == manifest["patch_count"] - 1
    before = {}
    for relative in scopes:
        path = tmp_path / relative
        before[relative] = path.read_bytes()
        rows = [json.loads(line) for line in path.read_text("utf8").splitlines()]
        for row in rows:
            if row["school_name"] in untouched[relative]:
                assert row == untouched[relative][row["school_name"]]
            if relative.endswith("/partners.jsonl"):
                PartnerUniversity.model_validate(row)
                if row["school_name"] == "早稻田大學 Waseda University":
                    assert row["language_requirement"] == "Independent newer school confirmation"
                    assert row["availability_status"] == "needs_confirmation"
                    assert row["quota_status"] == "not_published"
                    assert "2026/06/d52d923" in row["course_restrictions"]
    assert apply_ntnu_program_year_review(tmp_path) == 0
    assert all((tmp_path / path).read_bytes() == raw for path, raw in before.items())


def test_published_historical_fields_and_waseda_links_are_scoped():
    manifest = load_manifest(ROOT)
    from exchange_info.ntnu_quota_review import load_manifest as load_quota_review
    newer = {(s["file"], s["school_name"], p["pointer"]): p["value"]
             for s in load_quota_review(ROOT)["rows"] for p in s["patches"]}
    for scope in manifest["rows"]:
        rows = [json.loads(line) for line in (ROOT / scope["file"]).read_text("utf8").splitlines()]
        row = next(r for r in rows if r["school_name"] == scope["school_name"])
        for patch in scope["patches"]:
            parent, key = pointer_parent(row, patch["pointer"])
            assert parent[key] == newer.get((scope["file"], scope["school_name"], patch["pointer"]), patch["value"])
        if "Waseda University" not in scope["school_name"]:
            assert all(p["value"].startswith("【跨期資料待核對】") for p in scope["patches"])
    from exchange_info.ntnu_student_view import fetch_ntnu_partner_universities
    from exchange_info.qualification_scopes import partner_scope_needs_confirmation
    names = {r["school_name"] for r in manifest["rows"]}
    partners = [p for p in fetch_ntnu_partner_universities() if p.school_name in names]
    assert len(partners) == 144
    assert all(partner_scope_needs_confirmation(p, "degree_levels") for p in partners)
    builder = (ROOT / "scripts/build_ntnu_catalog.py").read_text("utf8")
    assert builder.index('round_id=21)') < builder.index('apply_ntnu_program_year_review(REPO_ROOT)')


def test_home_degree_pass_does_not_override_host_degree_requirements():
    from exchange_info.application_rules import build_personal_application_plan
    from exchange_info.models import PersonalApplicationPlanRequest
    for scope, expected in [("學士班", "fail"), ("碩士班", "pass"),
                            ("【跨期資料待核對】115-2 歷年學士班", "needs_confirmation")]:
        partner = PartnerUniversity(school_name="測試接待校", program_type="交換", country="日本",
                                    colleges="全校", degree_levels=scope, source_url="https://example.edu/notice")
        request = PersonalApplicationPlanRequest(home_school="國立臺灣師範大學", degree_level="碩士班",
            current_year="碩二", college="文學院", preferences=[{"rank": 1, "school_name": partner.school_name}])
        plan = build_personal_application_plan(request, [partner], [], academic_score_minimum=None)
        checks = {c.code: c for c in plan.choices[0].checks}
        assert checks["degree_level"].status == "pass"
        assert checks["partner_degree_level"].status == expected
