from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info import life_context as life
from exchange_info.models import PartnerUniversity, StudentDashboard
from exchange_info.university_locations import UniversityLocation
from scripts.research_ntu_destinations import identify, json_line, repair_utf8, Research


def registry(*, domain="example.edu", country="US", name="Example University"):
    return {"status": "active", "types": ["education"], "domains": [domain],
            "names": [{"value": name}], "locations": [{"geonames_details": {"country_code": country}}]}


def test_identity_rejects_country_conflicts_child_institutes_and_ambiguous_branches():
    row = {"school_name": "測試大學", "research_name": "Example University (EU)",
           "country": "美國", "official_website": "https://www.example.edu/"}
    university = registry()
    child = registry(domain="lab.example.edu", name="Different Institute")
    assert identify(row, [child, university]) == university
    assert identify(row, [registry(country="GB")]) is None
    assert identify(row, [registry(name="First University"), registry(name="Second University")]) is None
    faculty = row | {"school_name": "測試大學醫學院", "research_name": "Example University School of Medicine"}
    assert identify(faculty, [university]) is None
    # A registry explicitly describing that faculty can be used.
    assert identify(faculty, [registry(name=faculty["research_name"])])


def test_non_ascii_pages_and_jsonl_row_boundaries_survive():
    original = "臺灣學生住宿資訊 Universität"
    assert repair_utf8(original.encode().decode("latin-1")) == original
    lines = json_line({"text": "first\u2028second\u0085third"}) + json_line({"text": "fourth"})
    assert len(lines.splitlines()) == 2
    assert json.loads(lines.splitlines()[0])["text"] == "first\u2028second\u0085third"


def test_same_named_schools_use_their_own_country_photo(tmp_path, monkeypatch):
    from exchange_info import api
    path = tmp_path / "images.json"
    rows = [{"school_name": "City University", "country": country, "status": "verified",
             "local_path": "/static/" + code + ".jpg"} for country, code in (("美國", "us"), ("英國", "gb"))]
    path.write_text(json.dumps({"schools": rows}))
    monkeypatch.setattr(api, "SCHOOL_IMAGE_MANIFEST", path)
    partners = [PartnerUniversity(school_name="City University", country=c, program_type="交換學生",
                                  source_url="https://example.edu/partners") for c in ("美國", "英國", "法國")]
    result = api._attach_school_images(StudentDashboard(partner_universities=partners), base_url="https://example.org")
    assert [p.image_url for p in result.partner_universities] == ["https://example.org/static/us.jpg", "https://example.org/static/gb.jpg", None]
    monkeypatch.setattr(api, "fetch_ntu_partner_universities", lambda: partners)
    with TestClient(create_app(tmp_path / "runtime")) as client:
        coverage = client.get("/coverage", params={"school": "NTU"})
    assert coverage.status_code == 200
    assert coverage.json()["image_count"] == 2
    assert [p["image_status"] for p in coverage.json()["partners"]] == ["verified", "verified", "not_collected"]


def test_failed_retrieval_keeps_original_source_date_and_records_failed_attempt(tmp_path):
    previous = {"url": "https://example.edu/life", "checked_at": "2026-10-07T00:00:00+00:00", "text": "Original reference."}
    (tmp_path / "archive-sources.json.gz").write_bytes(gzip.compress(json.dumps({previous["url"]: previous}).encode()))
    research = Research(tmp_path, offline=True)
    result = research.prior_source(previous["url"], {"checked_at": "2026-10-08T00:00:00+00:00", "http_status": 503, "error": "Unavailable"})
    assert result["checked_at"] == previous["checked_at"]
    assert result["latest_attempt"]["http_status"] == 503
    assert result["text"] == previous["text"]


def test_location_change_keeps_official_references_but_removes_nearby_places(tmp_path):
    now = datetime.now(timezone.utc)
    row = life.LifeEvidence(theme="housing", kind="official", text="學校不保證住宿。",
                           sources=[life.LifeSource(title="Housing", url="https://example.edu/housing")])
    snapshot = life.LifeResearchSnapshot(school_name="Example University", checked_at=now, status="partial", evidence=[row])
    location = UniversityLocation(school_name="Example University")
    preserved = life._for_location(snapshot, location)
    assert preserved.checked_at == now and preserved.status == "partial"
    mixed = snapshot.model_copy(update={"evidence": [row, row.model_copy(update={"kind": "geographic"})]})
    invalidated = life._for_location(mixed, location)
    assert invalidated.checked_at is None
    assert [r.kind for r in invalidated.evidence] == ["official"]


def test_empty_refresh_cache_does_not_hide_bundled_sources(tmp_path, monkeypatch):
    partner = PartnerUniversity(school_name="Example University", country="美國",
                                program_type="交換學生", source_url="https://example.edu/partners")
    cached = life.LifeResearchSnapshot(school_name=partner.school_name, country=partner.country,
                                      status="unavailable", checked_at=datetime.now(timezone.utc))
    path = life._cache_path(partner, tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(cached.model_dump_json())
    evidence = life.LifeEvidence(theme="housing", kind="official", text="Accommodation is not guaranteed.",
                                sources=[life.LifeSource(title="Housing", url="https://example.edu/housing")])
    shipped = cached.model_copy(update={"status": "partial", "evidence": [evidence],
        "checked_at": datetime(2026, 10, 7, tzinfo=timezone.utc)})
    monkeypatch.setattr(life, "_bundled_ntu_research", lambda: {life._identity(partner): shipped})
    assert life.read_research(partner, tmp_path) == shipped
    # Without a bundled reference, retain the failed cache status.
    monkeypatch.setattr(life, "_bundled_ntu_research", lambda: {})
    assert life.read_research(partner, tmp_path) == cached


def test_all_ntu_destinations_have_reviewed_or_explicitly_missing_overlays():
    snapshot = json.loads(gzip.decompress(Path("sources/ntu/destinations-2026-10-08.json.gz").read_bytes()))
    names = {(r["school_name"], r["country"]) for r in snapshot["life"]}
    assert len(names) == 288
    for key in ("photos", "locations"):
        assert {(r["school_name"], r["country"]) for r in snapshot[key]} == names
    assert sum(r["status"] == "verified" for r in snapshot["photos"]) == 286
    assert sum(r["geocode_status"] == "verified" for r in snapshot["locations"]) == 269
    review = json.loads(Path("sources/ntu/photo-license-review-2026-10-09.json").read_text())
    pending = {(r["school_name"], r["country"]): r for r in review["rows"]}
    assert len(pending) == 20
    for row in snapshot["photos"]:
        if row["status"] == "verified":
            path = Path("src/exchange_info/static") / row["local_path"].split("?")[0].removeprefix("/static/")
            decision = pending.get((row["school_name"], row["country"]))
            if decision and decision.get("quarantine_file"):
                assert not path.exists()
                path = Path(decision["quarantine_file"])
            assert hashlib.sha256(path.read_bytes()).hexdigest() == row["content_hash"]
            if "commons.wikimedia.org" in row["official_page_url"]:
                assert row["license_name"]
                if row["license_name"].startswith("CC BY"):
                    assert row["artist"]
                    assert row["artist"].casefold() not in {"see below", "unknown", "n/a", "not provided"}
        else:
            assert row["local_path"] is None and row["note"]
    for row in snapshot["life"]:
        assert row["status"] != "ready"  # Partial source coverage is not a complete destination guide.
        for evidence in row["evidence"]:
            assert evidence["original_excerpt"] and evidence["sources"] and evidence["checked_at"]
            assert "116-1" in evidence["scope"]


def test_error_page_navigation_is_not_served_as_student_life_evidence():
    records = list(life._bundled_ntu_research().values())
    assert len(records) == 288
    assert sum(len(row.evidence) for row in records) == 1622
    akita = next(row for row in records if row.school_name == "秋田大學")
    assert akita.status == "partial" and akita.evidence
    assert not any("404" in source.url for row in akita.evidence for source in row.sources)
    assert any("已排除錯誤頁" in note for note in akita.notes)


def test_program_suffix_does_not_mix_distinct_universities_or_cache(tmp_path):
    names = ["夏威夷大學希羅分校", "奧瑞岡大學", "夏威夷大學瑪諾亞分校"]
    partners = [PartnerUniversity(school_name=name + "（E交換學生計畫、V訪問學生計畫）",
        country="美國", program_type="交換學生", source_url="https://oia.ntu.edu.tw/") for name in names]
    assert len({life._cache_path(partner, tmp_path) for partner in partners}) == 3
    for partner in partners:
        assert life.read_research(partner, tmp_path).school_name == partner.school_name


def test_ntu_public_api_serves_photos_locations_and_life_without_network(tmp_path, monkeypatch):
    import requests
    monkeypatch.setattr(requests.Session, "request", lambda *a, **k: (_ for _ in ()).throw(AssertionError("Unexpected network request")))
    with TestClient(create_app(tmp_path)) as client:
        response = client.get("/student-dashboard", params={"school": "NTU"})
        assert response.status_code == 200
        partners = response.json()["partner_universities"]
        assert len(partners) == 288
        assert sum(p["image_status"] == "verified" for p in partners) == 266
        pending = json.loads(Path("sources/ntu/photo-license-review-2026-10-09.json").read_text())["rows"]
        for row in pending:
            partner = next(p for p in partners if p["school_name"] == row["school_name"])
            assert partner["image_status"] == "needs_review" and not partner["image_url"]
        assert sum(p["location"]["geocode_status"] == "verified" for p in partners) == 269
        # The systems have no single destination point; no HQ marker is inserted.
        for p in partners:
            if p["school_name"] in {"加州大學", "加州州立大學"}:
                assert p["location"]["latitude"] is None
        context = client.get("/school-life-context", params={"school": "聖保羅大學", "home_school": "NTU"}).json()
        assert context["research_status"] == "partial" and context["source_count"] > 0
        assert any("USP iFriends" in e["text"] for c in context["categories"] for e in c["evidence"])
        assert any(e["translation_status"] == "translated" for c in context["categories"] for e in c["evidence"])
