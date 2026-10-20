"""GET /experience-stories only publishes moderator-approved submissions and never exposes who wrote them."""
from datetime import timedelta

import pytest
from cgu_catalogue_fixture import fixed_cgu_catalogue
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import (
    CommunityIdentityMode,
    ExperienceSubmission,
    ModerationStatus,
    PartnerUniversity,
    utc_now,
)
from exchange_info.storage import ensure_data_dirs, save_experience_submissions

LINCOLN = "林肯大學 Lincoln University"
MEIJI = "明治大學 Meiji University"
PUBLIC_FIELDS = {
    "id", "school_name", "home_university", "title", "summary", "exchange_year", "themes", "display_name", "source_url",
}


def _partner(name: str) -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生", country="紐西蘭", school_name=name,
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def _story(title: str, *, school: str = LINCOLN, status=ModerationStatus.APPROVED, minutes_ago: int = 0, **extra):
    return ExperienceSubmission(
        school_name=school, home_university="長庚大學", title=title,
        summary="宿舍要在錄取後很短的時間內申請，出發前先確認繳費與入住日期。",
        exchange_year="2025", themes=["housing"], status=status,
        created_at=utc_now() - timedelta(minutes=minutes_ago), **extra,
    )


@pytest.fixture
def make_client(tmp_path, monkeypatch):
    def build(rows):
        ensure_data_dirs(tmp_path)
        save_experience_submissions(rows, tmp_path)
        monkeypatch.setattr(
            "exchange_info.api.create_cgu_catalogue", fixed_cgu_catalogue(lambda: [_partner(LINCOLN), _partner(MEIJI)]))
        return TestClient(create_app(tmp_path))
    return build


def test_only_approved_submissions_are_public_and_nobody_needs_to_log_in(make_client):
    client = make_client([
        _story("已通過審核", status=ModerationStatus.APPROVED),
        _story("還在審核", status=ModerationStatus.PENDING),
        _story("已被隱藏", status=ModerationStatus.HIDDEN),
    ])
    response = client.get("/experience-stories")
    assert response.status_code == 200
    assert [row["title"] for row in response.json()] == ["已通過審核"]


def test_nothing_is_published_when_there_are_no_approved_stories(make_client):
    client = make_client([_story("還在審核", status=ModerationStatus.PENDING)])
    assert client.get("/experience-stories").json() == []


def test_responses_are_never_cached_so_a_hidden_story_disappears_at_once(make_client):
    client = make_client([_story("已通過審核")])
    assert client.get("/experience-stories").headers["cache-control"] == "no-store"


def test_payload_has_no_author_or_moderation_fields(make_client):
    client = make_client([_story("已通過審核", author_id="account-secret-id", source_url="https://example.com/my-story")])
    [row] = client.get("/experience-stories").json()
    assert set(row) == PUBLIC_FIELDS
    assert "account-secret-id" not in client.get("/experience-stories").text
    assert row["source_url"] == "https://example.com/my-story"


def test_anonymous_authors_stay_anonymous_but_real_name_authors_keep_their_name(make_client):
    client = make_client([
        _story("匿名", identity_mode=CommunityIdentityMode.ANONYMOUS, display_name="陳小明", minutes_ago=2),
        _story("具名", identity_mode=CommunityIdentityMode.REAL_NAME, display_name="王小華", minutes_ago=1),
    ])
    names = {row["title"]: row["display_name"] for row in client.get("/experience-stories").json()}
    assert names == {"匿名": "匿名投稿者", "具名": "王小華"}


@pytest.mark.parametrize("stored", ["javascript:alert(1)", "data:text/html,hi", "ftp://example.com/x", ""])
def test_a_source_link_that_is_not_http_is_dropped(make_client, stored):
    client = make_client([_story("已通過審核", source_url=stored)])
    assert client.get("/experience-stories").json()[0]["source_url"] is None


def test_newest_first_with_school_filter_and_limit(make_client):
    client = make_client([
        _story("最舊", minutes_ago=30),
        _story("明治", school=MEIJI, minutes_ago=20),
        _story("較新", minutes_ago=10),
        _story("最新", minutes_ago=1),
    ])
    assert [row["title"] for row in client.get("/experience-stories").json()] == ["最新", "較新", "明治", "最舊"]
    assert [row["title"] for row in client.get("/experience-stories", params={"school": LINCOLN}).json()] == ["最新", "較新", "最舊"]
    assert [row["title"] for row in client.get("/experience-stories", params={"limit": 2}).json()] == ["最新", "較新"]
    assert client.get("/experience-stories", params={"school": "不存在的大學"}).json() == []


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 25}, {"school": "a"}])
def test_invalid_query_is_rejected(make_client, params):
    assert make_client([]).get("/experience-stories", params=params).status_code == 422
