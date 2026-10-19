from datetime import datetime, timedelta, timezone

from exchange_info.models import ExchangeFieldEvidence, PartnerUniversity
from exchange_info.seo_changes import ContentChanges
from exchange_info.seo_quality import assess, audit_catalogues, digest, material_content
from exchange_info.university_registry import NTPU


def row(**kwargs):
    return PartnerUniversity(school_name="Example University", country="日本", program_type="交換",
                             source_url="https://oia.ntpu.edu.tw/exchange", **kwargs)


def test_reference_pages_keep_value_and_no_grade_changes_indexing():
    reference = row(eligibility="學業成績 GPA 3.0 以上", study_period="一學期或一學年交換", quota_status="not_published")
    result = assess([reference], NTPU.official_url)
    assert result["tier"] == "B"
    assert result["index_action"] == "keep_existing_pending_review"
    assert assess([row()], NTPU.official_url)["tier"] == "C"


def test_official_domain_and_verified_fields_are_required_for_a():
    evidence = ExchangeFieldEvidence(source_url="https://oia.ntpu.edu.tw/requirements",
                                     checked_at=datetime.now(timezone.utc), status="verified_current")
    partner = row(eligibility="學業成績 GPA 3.0 以上", study_period="一學期或一學年交換",
                  language_requirement="IELTS 6.5 overall", tuition_info="依協議免繳合作校學費",
                  field_evidence={"eligibility": evidence, "language_requirement": evidence})
    assert assess([partner], NTPU.official_url)["tier"] == "A"
    spoof = partner.model_copy(update={"source_url": "https://ntpu.edu.tw.attacker.example/test"})
    assert assess([spoof], NTPU.official_url)["tier"] == "C"


def test_identical_facts_are_only_review_candidates_with_separate_urls():
    first = row(eligibility="學業成績 GPA 3.0 以上", study_period="一學期或一學年交換")
    report = audit_catalogues([(NTPU, [first, first.model_copy(update={"school_name": "Another University"})])])
    assert report["page_count"] == 2
    assert len(report["duplicate_candidate_groups"][0]) == 2
    assert report["mode"] == "audit_only"


def test_material_hash_ignores_refresh_dates_and_record_order_but_not_facts():
    now = datetime.now(timezone.utc)
    evidence = ExchangeFieldEvidence(source_url="https://oia.ntpu.edu.tw/requirements", checked_at=now, status="verified_current")
    first = row(eligibility="GPA 3.0", checked_at=now, field_evidence={"eligibility": evidence})
    refreshed = first.model_copy(update={"checked_at": now + timedelta(days=1),
        "field_evidence": {"eligibility": evidence.model_copy(update={"checked_at": now + timedelta(days=1)})}})
    assert digest(material_content([first])) == digest(material_content([refreshed]))
    changed = first.model_copy(update={"eligibility": "GPA 3.5"})
    assert digest(material_content([first])) != digest(material_content([changed]))
    assert digest(material_content([first, changed])) == digest(material_content([changed, first]))


def test_lastmod_survives_restart_and_does_not_move_on_daily_refresh(tmp_path):
    day1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ledger = ContentChanges(tmp_path)
    assert ledger.observe({"/a": "baseline", "/b": "baseline"}, now=day1) == {}
    assert ledger.observe({"/a": "baseline"}, now=day1 + timedelta(days=1)) == {}
    result = ledger.observe({"/a": "changed", "/b": "baseline"}, now=day1 + timedelta(days=2))
    assert result == {"/a": "2026-01-03T00:00:00+00:00"}
    assert ContentChanges(tmp_path).observe({"/a": "changed"}, now=day1 + timedelta(days=5)) == result


def test_router_sitemap_changes_only_materially_changed_partner(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from exchange_info.seo import SeoSettings, create_seo_router, partner_id
    clock = [0.0]
    partners = [row(eligibility="GPA 3.0"), row().model_copy(update={"school_name": "Unchanged University"})]
    monkeypatch.setattr("exchange_info.seo.monotonic", lambda: clock[0])
    app = FastAPI()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), lambda _: (partners, None), ContentChanges(tmp_path)))
    with TestClient(app) as client:
        assert "lastmod" not in client.get("/sitemaps/ntpu.xml").text
        partners[0] = partners[0].model_copy(update={"eligibility": "GPA 3.5"})
        clock[0] = 61
        xml = client.get("/sitemaps/ntpu.xml").text
        assert xml.count("<lastmod>") == 1
        assert "GPA 3.5" in client.get(f"/schools/ntpu/partners/{partner_id(partners[0])}").text


def test_slow_home_refresh_does_not_block_other_homes():
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from exchange_info.seo import SeoSettings, create_seo_router
    entered, release = threading.Event(), threading.Event()
    def catalogue(home):
        if home.id == "ntpu":
            entered.set()
            assert release.wait(5)
        return [row()], None
    app = FastAPI()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), catalogue))
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=2) as pool:
        slow = pool.submit(client.get, "/sitemaps/ntpu.xml")
        try:
            assert entered.wait(2)
            fast = pool.submit(client.get, "/sitemaps/ntu.xml")
            assert fast.result(timeout=2).status_code == 200
        finally:
            release.set()
        assert slow.result(timeout=2).status_code == 200
