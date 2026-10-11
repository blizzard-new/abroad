from cgu_catalogue_fixture import fixed_cgu_catalogue
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from exchange_info import life_context as life
from exchange_info import life_sources as reader
from exchange_info.api import create_app
from exchange_info.content_summary import FetchedPageContent
from exchange_info.experience_collector import _candidate_to_source, build_experience_digest, build_experience_queries
from exchange_info.models import DestinationProfile, PartnerUniversity, SourceReference
from exchange_info.university_locations import UniversityLocation

NOW = datetime.now(timezone.utc)


def partner(name="Meiji University", country="日本"):
    return PartnerUniversity(school_name=name, country=country, program_type="交換學生",
                             source_url="https://home.example.edu/partners", website="https://www.meiji.ac.jp/")


def location(*, verified=True, latitude=35.698):
    return UniversityLocation(school_name="Meiji University", country="日本", city="Tokyo",
        latitude=latitude if verified else None, longitude=139.76 if verified else None,
        geocode_status="verified" if verified else "pending", geocoded_at=NOW if verified else None,
        source_url="https://www.meiji.ac.jp/access" if verified else None)


def evidence(kind="official", theme="food", checked_at=NOW):
    return life.LifeEvidence(theme=theme, kind=kind, text="Campus cafeteria at Liberty Tower.",
        sources=[life.LifeSource(title="University dining", url="https://www.meiji.ac.jp/cafeteria")], checked_at=checked_at)


def store(tmp_path, snapshot):
    path = life._cache_path(partner(), tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot.model_dump_json(), encoding="utf-8")


def test_verified_reference_and_foreign_student_are_distinct(tmp_path):
    for name in ("明治大學 (Meiji University) 無", "明治大學 Meiji University"):
        p = partner(name)
        students = life.reference_student_sources(p)
        digest = build_experience_digest(p.school_name, p.country, students)
        assert len(digest.sources) == 1
        assert digest.sources[0].language == "en"
        assert digest.sources[0].perspective == "official_student_story"
        context = life.build_life_context(p, DestinationProfile(school_name=name), location(), tmp_path)
        food = next(c for c in context.categories if c.theme == "food")
        assert "Sky Lounge" in food.evidence[0].text
        assert food.inference.method == "evidence_rules"
        assert set(food.inference.basis_urls) <= {s.url for e in food.evidence for s in e.sources}
        assert "代表座標" in context.location_note
    assert not life.reference_student_sources(partner(country="美國"))
    assert not life.reference_student_sources(partner("Meiji Gakuin University"))


def test_no_evidence_no_inference_and_no_made_up_budget(tmp_path):
    p = partner("Unknown University")
    context = life.build_life_context(p, DestinationProfile(school_name=p.school_name), location(verified=False), tmp_path)
    assert len(context.categories) == 10
    assert all(not c.evidence and c.inference is None for c in context.categories)
    assert "不以城市中心" in context.location_note
    assert "每月總額" in context.categories[1].next_step


def test_profile_requires_reviewed_status_and_source():
    profile = DestinationProfile(school_name="Example University", housing_summary="International students can apply for a residence.",
        coverage_status="official_partial", sources=[SourceReference(title="Residence", source_url="https://example.edu/housing")])
    assert life._profile_evidence(profile)[0].theme == "housing"
    assert not life._profile_evidence(profile.model_copy(update={"coverage_status": "not_found"}))
    assert not life._profile_evidence(profile.model_copy(update={"sources": []}))


def test_unknown_coordinates_never_search_nearby(monkeypatch):
    monkeypatch.setattr(life, "fetch_public_bytes", lambda *a, **kw: pytest.fail("unverified coordinate triggered network"))
    rows, _ = life._geographic_research(location(verified=False), NOW)
    assert rows == []


def test_map_records_require_valid_coordinates_and_supported_kind(monkeypatch):
    payload = {"elements": [
        {"type": "node", "id": 1, "lat": 35.6981, "lon": 139.76, "tags": {"name": "Test clinic", "amenity": "clinic"}},
        {"type": "way", "id": 2, "center": {"lat": 35.6982, "lon": 139.76}, "tags": {"name": "Test food", "shop": "supermarket"}},
        {"type": "node", "id": 3, "lat": 0, "lon": 0, "tags": {"name": "Far away", "amenity": "restaurant"}},
        {"type": "node", "id": 4, "lat": "nan", "lon": 139.76, "tags": {"name": "Bad", "amenity": "clinic"}},
        {"type": "node", "id": 5, "lat": 35.698, "lon": 139.76, "tags": {"name": "Unknown kind"}},
    ]}
    monkeypatch.setattr(life, "fetch_public_bytes", lambda *a, **kw: (json.dumps(payload).encode(), "https://overpass-api.de/", "application/json"))
    rows, note = life._geographic_research(location(), NOW)
    assert len(rows) == 2
    assert {r.theme for r in rows} == {"safety", "food"}
    assert all("直線約" in r.text and "不是步行" in r.scope for r in rows)
    assert all(r.sources[0].url.startswith("https://www.openstreetmap.org/") for r in rows)
    assert "ODbL" in note


def test_official_search_snippet_and_offsite_redirect_are_not_facts(monkeypatch):
    monkeypatch.setattr(life, "search_text", lambda *a, **kw: [
        {"href": "https://www.meiji.ac.jp/a", "body": "Free housing for everyone"},
        {"href": "https://www.meiji.ac.jp/b"},
        {"href": "https://www.meiji.ac.jp.evil.example/c"},
    ])
    def page(url):
        return FetchedPageContent(title="Official campus", text="International students can find the campus cafeteria in Liberty Tower.",
            final_url="https://evil.example/" if url.endswith("/a") else url, status="full_text")
    monkeypatch.setattr(life, "read_life_page", page)
    rows, _ = life._official_research(partner(), NOW)
    assert rows and all(r.original_excerpt for r in rows)
    assert all(r.sources[0].url.endswith("/b") for r in rows)
    assert "Free housing" not in " ".join(r.text for r in rows)


def test_official_excerpts_do_not_classify_train_as_rain_or_different_as_rent(monkeypatch):
    monkeypatch.setattr(life, "search_text", lambda *a, **kw: [{"href": "https://www.meiji.ac.jp/services"}])
    monkeypatch.setattr(life, "read_life_page", lambda url: FetchedPageContent(title="Student services",
        text="Two different organizations help students make friends.\nThe train takes students to the university station.\nThe campus cafeteria serves meals to students.", final_url=url, status="full_text"))
    rows, _ = life._official_research(partner(), NOW)
    assert "climate" not in {row.theme for row in rows}
    assert "cost" not in {row.theme for row in rows}
    assert "food" in {row.theme for row in rows}


def test_failed_refresh_preserves_old_facts_and_their_dates(tmp_path, monkeypatch):
    old = NOW - timedelta(days=3)
    store(tmp_path, life.LifeResearchSnapshot(school_name="Meiji University", country="日本", checked_at=old,
        evidence=[evidence(checked_at=old)], location_signature=life._location_signature(location())))
    monkeypatch.setattr(life, "_official_research", lambda *a: ([], "unavailable"))
    monkeypatch.setattr(life, "_geographic_research", lambda *a: ([], "unavailable"))
    result = life.refresh_life_research(partner(), location(), tmp_path)
    assert result.status == "unavailable" and result.evidence[0].checked_at == old
    monkeypatch.setattr(life, "_official_research", lambda *a: pytest.fail("fresh cache searched again"))
    assert life.refresh_life_research(partner(), location(), tmp_path).checked_at == result.checked_at


def test_changed_campus_invalidates_cached_nearby_places(tmp_path):
    store(tmp_path, life.LifeResearchSnapshot(school_name="Meiji University", country="日本", checked_at=NOW,
        status="ready", evidence=[evidence(kind="geographic")], location_signature=life._location_signature(location())))
    context = life.build_life_context(partner(), DestinationProfile(school_name="Meiji University"), location(latitude=34.0), tmp_path)
    assert context.can_refresh and context.research_status == "not_collected"
    assert not any(row.kind == "geographic" for c in context.categories for row in c.evidence)


def test_multilingual_queries_and_pdf_candidate():
    queries = " ".join(q for q, _ in build_experience_queries(partner()))
    assert "Erfahrungsbericht" in queries and "filetype:pdf" in queries
    source = _candidate_to_source({"title": "Meiji University Japan exchange experience report", "href": "https://student.example.edu/meiji-exchange.pdf", "body": "My exchange semester at Meiji University Japan. Student dorm and cafeteria."}, partner())
    assert source is not None


def test_pdf_reader_extracts_body_and_html_ignores_navigation(monkeypatch):
    stream = BytesIO()
    pdf = canvas.Canvas(stream)
    for i in range(5):
        pdf.drawString(20, 700 - i * 30, "My exchange semester at Meiji University included courses and student housing.")
    pdf.save()
    monkeypatch.setattr(reader, "fetch_public_bytes", lambda *a, **kw: (stream.getvalue(), "https://example.edu/report.pdf", "application/pdf"))
    assert "student housing" in reader.read_life_page("https://example.edu/report.pdf").text
    html = ("<html><title>Life</title><nav>Misleading navigation</nav><main>" + "Campus cafeteria has a dining room. " * 10 + "</main></html>").encode()
    monkeypatch.setattr(reader, "fetch_public_bytes", lambda *a, **kw: (html, "https://example.edu/", "text/html"))
    assert "navigation" not in reader.read_life_page("https://example.edu/").text


@pytest.mark.parametrize("url", ["http://example.edu", "https://x:y@example.edu", "https://example.edu:8080", "javascript:alert(1)", "https://[bad"])
def test_page_reader_rejects_unsafe_url_shapes(url):
    assert not reader.public_https_url(url)


def test_context_api_reads_without_network_and_rejects_unknown_school(tmp_path, monkeypatch):
    import exchange_info.api as api
    import hashlib
    from datetime import timedelta
    from exchange_info.models import UserAccount, AccountSessionRecord, utc_now
    from exchange_info.storage import save_user_accounts, save_account_sessions
    monkeypatch.setenv("EXCHANGE_ACCOUNT_REPOSITORY", "jsonl")
    save_user_accounts([UserAccount(id="life-reader", display_name="隔離測試讀者", email_verified=True,
        student_status_verified=True, verified_university="長庚大學", home_university="長庚大學")], tmp_path)
    save_account_sessions([AccountSessionRecord(account_id="life-reader",
        token_hash=hashlib.sha256(b"life-reader-token").hexdigest(),
        expires_at=utc_now()+timedelta(days=1))], tmp_path)
    monkeypatch.setattr(api, 'create_cgu_catalogue', fixed_cgu_catalogue(lambda *a, **kw: [partner("明治大學 Meiji University")]))
    monkeypatch.setattr(life, "search_text", lambda *a, **kw: pytest.fail("GET triggered search"))
    client = TestClient(create_app(data_dir=tmp_path), headers={"Authorization": "Bearer life-reader-token"})
    result = client.get("/school-life-context", params={"school": "明治大學 Meiji University", "home_school": "長庚大學"})
    assert result.status_code == 200
    assert result.json()["source_count"] >= 3
    assert client.get("/school-life-context", params={"school": "unknown"}).status_code == 404
    digest = client.get("/student-experiences", params={"school": "明治大學 Meiji University", "home_school": "長庚大學"})
    assert digest.status_code == 200 and len(digest.json()["sources"]) == 1
    # A source already collected under another home university's school label
    # must not suppress the reference for this catalog entry.
    other_catalog_source = life.reference_student_sources(partner("明治大學 (Meiji University) 無"))
    monkeypatch.setattr(api, "load_student_experiences", lambda *a, **kw: other_catalog_source.copy())
    digest = client.get("/student-experiences", params={"school": "明治大學 Meiji University", "home_school": "長庚大學"})
    assert digest.status_code == 200 and len(digest.json()["sources"]) >= 1
