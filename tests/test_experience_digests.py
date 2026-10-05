"""Chinese write-ups of student experiences, and sorting sources by what kind of page they are."""
from __future__ import annotations

import copy
import json

import pytest
from fastapi.testclient import TestClient

from exchange_info import experience_digests
from exchange_info.api import create_app
from exchange_info.experience_digests import attach_digests, source_kind, validate_digests
from exchange_info.models import ExperienceSourceType, StudentExperienceSource
from exchange_info.storage import save_student_experiences

SCHOOL = "北京清華大學 Tsinghua University"
URL = "https://example.edu/blog/my-semester"


def make_source(url=URL, platform="Blog", source_type=ExperienceSourceType.ARTICLE, perspective="student_created", title="My semester at Tsinghua University"):
    return StudentExperienceSource(
        school_name=SCHOOL, country="大陸地區", title=title, source_url=url, source_type=source_type, platform=platform,
        language="en", summary="作者在清華大學交換一學期，住在國際生宿舍，分享課程與生活花費。", themes=["housing"],
        perspective=perspective, content_hash=str(abs(hash(url))),
    )


def digest_payload(**overrides) -> dict:
    digest = {
        "title_zh": "在清華大學交換一學期：住宿、課程與日常花費",
        "overview": "作者在清華大學交換一學期，住在學校提供的國際生宿舍，主要談宿舍條件、選課方式、每個月大約的花費，以及剛到時最容易卡關的幾件事。",
        "sections": [{"heading": "住宿", "points": ["宿舍是雙人房，浴室共用。", "網路需要另外申請。"]}],
        "tips": ["先在台灣綁好行動支付。"],
        "written_at": "2026-10-04",
    }
    digest.update(overrides)
    return {"version": 1, "digests": {URL: digest}, "sources": {URL: source_meta()}}


def source_meta(**overrides) -> dict:
    meta = {"school_name": SCHOOL, "country": "大陸地區", "title": "My semester at Tsinghua University", "platform": "Blog",
            "language": "en", "source_type": "article", "themes": ["housing", "academics"]}
    meta.update(overrides)
    return meta


@pytest.fixture
def bundled(tmp_path, monkeypatch):
    """Point the module at a temporary digests file; the returned function writes it."""
    path = tmp_path / "experience_digests_zh.json"
    monkeypatch.setattr(experience_digests, "DIGESTS_FILE", path)

    def write(payload):
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        experience_digests._load.cache_clear()

    write({"version": 1, "digests": {}})
    yield write
    experience_digests._load.cache_clear()


# ----------------------------------------------------------------------------- what kind of page it is


@pytest.mark.parametrize("url,platform,kind", [
    ("https://eduopinions.com/universities/x/student-reviews-1", "eduopinions.com", "review_collection"),
    ("https://www.studyabroad101.com/program/1", "studyabroad101.com", "review_collection"),
    ("https://unirank.org/vn/uni/van-lang-university", "unirank.org", "directory"),
    ("https://www.mastersportal.com/universities/1", "mastersportal.com", "directory"),
    ("https://www.reddit.com/r/malaysia/comments/1", "Reddit", "community_thread"),
    ("https://old.reddit.com/r/x/comments/2", "Reddit", "community_thread"),
    ("https://www.youtube.com/watch?v=1", "YouTube", "video"),
    ("https://someone.blogspot.com/2025/exchange.html", "someone.blogspot.com", "personal_story"),
    ("https://medium.com/@a/my-time-at-tsinghua", "Medium", "personal_story"),
])
def test_sources_are_sorted_by_what_kind_of_page_they_are(url, platform, kind):
    source_type = ExperienceSourceType.VIDEO if kind == "video" else ExperienceSourceType.COMMUNITY if kind == "community_thread" else ExperienceSourceType.ARTICLE
    assert source_kind(make_source(url=url, platform=platform, source_type=source_type)) == kind


def test_a_look_alike_host_is_not_mistaken_for_a_known_one():
    assert source_kind(make_source(url="https://noteduopinions.com/a")) == "personal_story"
    assert source_kind(make_source(url="https://eduopinions.com.evil.example/a")) == "personal_story"


# ----------------------------------------------------------------------------- the validator


def test_a_good_digest_has_no_problems():
    assert validate_digests(digest_payload()) == []


def problems(**overrides):
    return validate_digests(digest_payload(**overrides))


def test_a_digest_no_better_than_the_old_filler_is_rejected():
    assert any("40 字" in p for p in problems(overview="這個來源主要談到住宿。"))
    assert any("分段" in p for p in problems(sections=[]))
    assert any("空的分段" in p for p in problems(sections=[{"heading": "", "points": ["x"]}]))
    assert any("空的分段" in p for p in problems(sections=[{"heading": "住宿", "points": []}]))


def test_a_digest_that_reproduces_the_source_is_rejected():
    long_points = ["這是整理過的一個要點，" * 12] * 25
    assert any("2600" in p for p in problems(sections=[{"heading": "住宿", "points": long_points}]))
    english = "The dormitory rooms are shared between two students and the bathroom is down the hall on every floor of the building"
    assert any("英文原文" in p for p in problems(tips=[english]))
    japanese = "寮は二人部屋でシャワーは共用ですがとても清潔でした"
    assert any("日文或韓文" in p for p in problems(tips=[japanese]))


def test_a_bad_date_key_or_shape_is_rejected():
    assert any("written_at" in p for p in problems(written_at="今天"))
    payload = digest_payload()
    payload["digests"]["not a url"] = payload["digests"].pop(URL)
    assert any("不是網址" in p for p in validate_digests(payload))
    assert validate_digests({"version": 2})


# ----------------------------------------------------------------------------- attaching


def test_attaching_adds_the_kind_and_only_the_matching_digest(bundled):
    bundled(digest_payload())
    other = make_source(url="https://eduopinions.com/universities/x/student-reviews-9", platform="eduopinions.com")
    first, second = attach_digests([make_source(), other])
    assert first.digest_zh.title_zh.startswith("在清華大學交換") and first.source_kind == "personal_story"
    assert second.digest_zh is None and second.source_kind == "review_collection"


def test_a_digest_that_fails_validation_stops_the_app_from_serving_it(bundled):
    bundled(digest_payload(overview="太短"))
    with pytest.raises(ValueError, match="無法通過驗證"):
        attach_digests([make_source()])


def test_the_bundled_digests_pass_the_validator():
    from pathlib import Path

    shipped = Path(experience_digests.__file__).parent / "official_data" / "experience_digests_zh.json"
    assert validate_digests(json.loads(shipped.read_text(encoding="utf-8"))) == []


def test_every_digest_needs_matching_usable_source_details():
    payload = digest_payload()
    payload["sources"].pop(URL)
    assert any("一一對應" in p for p in validate_digests(payload))
    assert any("缺少 sources" in p for p in validate_digests({"version": 1, "digests": {}}))
    for change, needle in (({"school_name": ""}, "缺少 school_name"), ({"source_type": "podcast"}, "source_type"), ({"themes": ["weather"]}, "未知主題")):
        bad = digest_payload()
        bad["sources"][URL] = source_meta(**change)
        assert any(needle in p for p in validate_digests(bad)), change


def test_curated_stories_are_added_for_their_school_even_when_nothing_was_crawled(bundled):
    from exchange_info.experience_collector import build_experience_digest
    from exchange_info.experience_digests import with_bundled_sources

    bundled(digest_payload())
    empty = build_experience_digest(SCHOOL, "大陸地區", [])
    filled = with_bundled_sources(empty, SCHOOL)
    assert [s.source_url for s in filled.sources] == [URL] and filled.total_sources == 1 and filled.article_count == 1
    assert filled.sources[0].summary.startswith("作者在清華大學交換一學期") and filled.sources[0].content_status == "full_text"
    assert with_bundled_sources(build_experience_digest("別的學校", "日本", []), "別的學校").sources == []
    again = with_bundled_sources(filled, SCHOOL)
    assert len(again.sources) == 1, "a story the crawl already found is not listed twice"


# ----------------------------------------------------------------------------- the API


def test_the_digest_endpoint_serves_a_written_digest_and_404s_otherwise(bundled, tmp_path):
    bundled(digest_payload())
    client = TestClient(create_app(tmp_path))
    found = client.get("/experience-digest", params={"source_url": URL})
    assert found.status_code == 200 and found.json()["sections"][0]["heading"] == "住宿"
    missing = client.get("/experience-digest", params={"source_url": "https://example.edu/none"})
    assert missing.status_code == 404 and "還沒有中文整理" in missing.json()["detail"]


def test_the_experience_list_carries_each_sources_kind_and_digest(bundled, tmp_path):
    bundled(digest_payload())
    rows = [make_source(), make_source(url="https://www.reddit.com/r/china/comments/1", platform="Reddit", source_type=ExperienceSourceType.COMMUNITY)]
    save_student_experiences(rows, tmp_path)
    response = TestClient(create_app(tmp_path)).get("/student-experiences", params={"school": SCHOOL, "home_school": "長庚大學"})
    assert response.status_code == 200
    by_url = {source["source_url"]: source for source in response.json()["sources"]}
    assert by_url[URL]["digest_zh"]["title_zh"].startswith("在清華大學") and by_url[URL]["source_kind"] == "personal_story"
    reddit = by_url["https://www.reddit.com/r/china/comments/1"]
    assert reddit["digest_zh"] is None and reddit["source_kind"] == "community_thread"


def test_a_school_with_no_crawled_data_still_lists_its_curated_story(bundled, tmp_path):
    bundled(digest_payload())
    response = TestClient(create_app(tmp_path)).get("/student-experiences", params={"school": SCHOOL, "home_school": "長庚大學"})
    sources = response.json()["sources"]
    assert [s["source_url"] for s in sources] == [URL]
    assert sources[0]["digest_zh"]["sections"] and sources[0]["source_kind"] == "personal_story"


def test_the_shipped_digests_describe_real_partner_schools_and_real_student_accounts():
    from pathlib import Path

    from exchange_info.experience_digests import THEME_KEYS

    base = Path(experience_digests.__file__).parent / "official_data"
    shipped = json.loads((base / "experience_digests_zh.json").read_text(encoding="utf-8"))
    schools = {json.loads(line)["school_name"] for line in (base / "university_locations.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
    assert len(shipped["digests"]) >= 15
    for url, meta in shipped["sources"].items():
        assert meta["school_name"] in schools, (url, meta["school_name"])
        assert set(meta["themes"]) <= THEME_KEYS
        source = StudentExperienceSource(
            school_name=meta["school_name"], country=meta["country"], title=meta["title"], source_url=url,
            source_type=ExperienceSourceType.ARTICLE, platform=meta["platform"], summary="x", content_hash="h",
            perspective="student_created",
        )
        assert source_kind(source) == "personal_story", f"{url} is not a student's own account"
    for url, digest in shipped["digests"].items():
        assert digest["written_at"] == "2026-10-04" and len(digest["overview"]) >= 40
        assert sum(len(p) for s in digest["sections"] for p in s["points"]) >= 60, f"{url} says too little to be worth opening"


def test_the_experience_tab_lists_stories_first_and_files_everything_else_as_a_reference():
    """A static contract on discovery-ui.js; the browser tests exercise the same rule end to end."""
    from pathlib import Path

    script = (Path(experience_digests.__file__).parent / "static" / "discovery-ui.js").read_text(encoding="utf-8")
    assert r'DISCOVERY_FILLER = /^(這個來源主要談到|這個公開來源|來源談到|\d+\s*個來源)/' in script
    assert 's.source_kind === "personal_story"' in script and "discoveryUsefulSummary(s)" in script
    assert "其他參考來源" in script and "還沒有中文整理，可以先看原文" in script
    assert 'fetchJson(`/experience-digest?source_url=' in script, "saved copies look their write-up up by address"
    collector = (Path(experience_digests.__file__).parent / "experience_collector.py").read_text(encoding="utf-8")
    assert "這個來源主要談到" in collector, "the filler template the UI hides is still the one the collector writes"
