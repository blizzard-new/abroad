from __future__ import annotations

import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.ntnu_quota_review import MANIFEST, apply_ntnu_quota_review, load_manifest
from exchange_info.ntnu_student_view import fetch_ntnu_partner_universities

ROOT = Path(__file__).parents[1]
AS_OF = datetime.fromisoformat("2026-10-21T10:00:00+08:00")


def test_every_current_contract_is_bound_and_school_status_preserves_mixed_scopes():
    manifest = load_manifest(ROOT)
    assert [s["page"] for s in manifest["all_pages"]] == list(range(1, 30))
    current = json.loads((ROOT / "sources/ntnu/quotalist_1161.json").read_text("utf8"))
    key = lambda r: (r["school_no"], r["contract_level"], r["organizer"])
    reviewed = [r for s in manifest["schools"] for r in s["contract_rows"]]
    assert {key(r): r for r in current} == {key(r): r for r in reviewed}
    assert len(reviewed) == len({key(r) for r in reviewed}) == 285
    partners = fetch_ntnu_partner_universities(reference_time=AS_OF)
    assert Counter(p.quota_status for p in partners) == {"published": 85, "not_published": 150, "zero": 1}
    assert Counter(p.availability_status for p in partners) == {"open": 72, "needs_confirmation": 163, "zero_quota": 1}
    paris = next(p for p in partners if "Paris Cité" in p.school_name)
    assert paris.availability_status == "needs_confirmation"
    assert "0 名，本期不開放" in paris.quota and "名額待確認" in paris.quota
    kyushu = next(p for p in partners if "Kyushu University" in p.school_name)
    assert kyushu.availability_status == "needs_confirmation"
    assert "校級（國際事務處）名額待確認" in kyushu.quota
    assert "教育學院" in kyushu.quota and "藝術學院" in kyushu.quota
    assert "4 名" not in kyushu.quota  # two separately restricted quotas, not four shared seats
    linnaeus = next(p for p in partners if "Linnaeus" in p.school_name)
    assert linnaeus.quota_status == "zero" and linnaeus.availability_status == "zero_quota"


def test_window_is_recomputed_after_cache_and_does_not_extend_to_departmental_agreements():
    for when, expected in [("2026-10-31T23:59:59+08:00", "upcoming"),
                           ("2026-11-01T16:00:00+08:00", "needs_confirmation"),
                           ("2026-11-02T00:00:00+08:00", "open"),
                           ("2026-11-15T23:59:59+08:00", "open"),
                           ("2026-11-15T16:00:00+00:00", "closed")]:
        partners = fetch_ntnu_partner_universities(reference_time=datetime.fromisoformat(when))
        salzburg = next(p for p in partners if "The University of Salzburg" in p.school_name)
        assert salzburg.application_window_status == expected
        vienna = next(p for p in partners if "Music and Performing Arts Vienna" in p.school_name)
        assert vienna.application_window_status == "needs_confirmation"
        kyushu = next(p for p in partners if "Kyushu University" in p.school_name)
        assert kyushu.application_window_status == "needs_confirmation"


def test_replay_is_value_guarded_and_preserves_independent_quota_update(tmp_path):
    manifest = load_manifest(ROOT)
    (tmp_path / MANIFEST).parent.mkdir(parents=True)
    shutil.copy2(ROOT / MANIFEST, tmp_path / MANIFEST)
    by_file = {}
    for scope in manifest["rows"]:
        by_file.setdefault(scope["file"], []).append(scope)
    for relative, scopes in by_file.items():
        rows = [json.loads(s) for s in (ROOT / relative).read_text("utf8").splitlines()]
        by_name = {r["school_name"]: r for r in rows}
        for scope in scopes:
            r = by_name[scope["school_name"]]
            r.get("reference_data", {}).pop("source_review_round39", None)
            for patch in scope["patches"]:
                parent, key = pointer_parent(r, patch["pointer"])
                parent[key] = patch["expected_values"][0]
        if relative.endswith("/partners.jsonl"):
            rows[0]["quota"] = "Independent later confirmation"
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf8")
    assert apply_ntnu_quota_review(tmp_path) == manifest["patch_count"] - 1
    before = {p: (tmp_path / p).read_bytes() for p in by_file}
    assert apply_ntnu_quota_review(tmp_path) == 0
    assert all((tmp_path / p).read_bytes() == body for p, body in before.items())
    partner = json.loads((tmp_path / "src/exchange_info/official_data/ntnu/partners.jsonl").read_text("utf8").splitlines()[0])
    assert partner["quota"] == "Independent later confirmation"


def test_upcoming_is_visible_and_not_an_unqualified_application_pass():
    from exchange_info.application_rules import build_personal_application_plan
    from exchange_info.models import PersonalApplicationPlanRequest
    from exchange_info.seo import partner_details
    partner = next(p for p in fetch_ntnu_partner_universities(reference_time=AS_OF)
                   if "The University of Salzburg" in p.school_name)
    assert "尚未開始受理" in partner_details(partner)
    plan = build_personal_application_plan(
        PersonalApplicationPlanRequest(home_school="國立臺灣師範大學",
                                       degree_level="學士班", current_year="大二",
                                       preferences=[{"rank": 1, "school_name": partner.school_name}]),
        [partner], [], academic_score_minimum=None,
    )
    check = next(c for c in plan.choices[0].checks if c.code == "home_deadline")
    assert check.status == "needs_confirmation" and "尚未開始" in check.title
