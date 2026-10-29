"""The GitHub client opens one draft pull request with one proposal file, and refuses to do anything else."""

import base64
import json

import httpx
import pytest

from office.accounts import github_row, link_github
from office.config import Settings
from office.platforms.base import PlatformError
from office.platforms.github import PROPOSAL_FILE, GitHubClient
from office.store import Store

PATH = "sources/audit/proposals/2026-10-28-cgu-0a1b2c3d.json"
BRANCH = "office/2026-10-28-cgu-0a1b2c3d"
CONTENT = json.dumps({"school_id": "cgu"}) + "\n"
REPO_API = "/repos/blizzard-new/abroad"


def recorder(handler):
    calls = []

    def transport(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    return httpx.Client(transport=httpx.MockTransport(transport)), calls


def friendly(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if request.method == "GET" and path == f"{REPO_API}/git/ref/heads/main":
        return httpx.Response(200, json={"object": {"sha": "abc123"}})
    if request.method == "POST" and path == f"{REPO_API}/git/refs":
        return httpx.Response(201, json={})
    if request.method == "PUT" and path == f"{REPO_API}/contents/{PATH}":
        return httpx.Response(201, json={})
    if request.method == "POST" and path == f"{REPO_API}/pulls":
        return httpx.Response(201, json={"number": 7, "html_url": "https://github.com/blizzard-new/abroad/pull/7"})
    return httpx.Response(404, json={"message": "unexpected request"})


def client(http, **kwargs):
    return GitHubClient("blizzard-new/abroad", "github_pat_secret", dry_run=False, http=http, **kwargs)


def open_pr(github, **overrides):
    args = dict(branch=BRANCH, path=PATH, content=CONTENT, commit_message="office: 長庚大學 新公告提案", title="資料更新提案：長庚大學", body="內容")
    return github.open_draft_pr(**{**args, **overrides})


def test_opens_a_draft_pull_request_from_a_new_branch_with_one_file():
    http, calls = recorder(friendly)
    github = client(http)
    assert open_pr(github) == {"id": "7", "url": "https://github.com/blizzard-new/abroad/pull/7"}
    assert [(c.method, c.url.path.removeprefix(REPO_API)) for c in calls] == [
        ("GET", "/git/ref/heads/main"), ("POST", "/git/refs"), ("PUT", f"/contents/{PATH}"), ("POST", "/pulls")]
    branch, file, pull = (json.loads(c.content) for c in calls[1:])
    assert branch == {"ref": f"refs/heads/{BRANCH}", "sha": "abc123"}
    assert file["branch"] == BRANCH and base64.b64decode(file["content"]).decode() == CONTENT
    assert pull["draft"] is True and pull["head"] == BRANCH and pull["base"] == "main"
    assert all(c.headers["Authorization"] == "Bearer github_pat_secret" for c in calls)
    assert "github_pat_secret" not in json.dumps(github.calls)  # the recorded calls end up in var/outbox/


def test_it_cannot_merge_close_delete_or_touch_the_base_branch():
    http, calls = recorder(friendly)
    open_pr(client(http))
    assert {c.method for c in calls} <= {"GET", "POST", "PUT"}
    assert not any("merge" in c.url.path for c in calls)
    assert not [name for name in ("merge", "close", "delete", "delete_branch", "force_push") if hasattr(GitHubClient, name)]


@pytest.mark.parametrize("override", [
    {"branch": "main"}, {"branch": "feature/x"}, {"branch": "office/../main"}, {"branch": "office/x.lock"}, {"branch": "office/"},
    {"path": "README.md"}, {"path": ".github/workflows/quality.yml"}, {"path": "src/exchange_info/university_registry.py"},
    {"path": "sources/audit/proposals/../../../README.md"}, {"path": "sources/audit/proposals/notes.json"},
    {"path": "sources/audit/2026-10-28-cgu-0a1b2c3d.json"},
    {"content": "not json"}, {"content": "[1, 2]"}, {"content": json.dumps({"x": "a" * 50_000})},
    {"title": "  "}, {"body": "x" * 30_000},
])
def test_anything_outside_the_proposal_folder_is_refused_before_any_request(override):
    http, calls = recorder(friendly)
    with pytest.raises(PlatformError):
        open_pr(client(http), **override)
    assert calls == []


def test_the_proposal_file_name_rule_matches_what_the_office_builds():
    assert PROPOSAL_FILE.fullmatch(PATH)
    assert not PROPOSAL_FILE.fullmatch(PATH.replace("proposals/", "proposals/x/"))


def test_a_repeat_after_a_half_finished_try_picks_up_where_it_stopped():
    def handler(request):
        path = request.url.path
        if request.method == "POST" and path.endswith("/git/refs"):
            return httpx.Response(422, json={"message": "Reference already exists"})
        if request.method == "PUT":
            return httpx.Response(422, json={"message": "\"sha\" wasn't supplied."})
        if request.method == "GET" and path.endswith(f"/contents/{PATH}"):
            return httpx.Response(200, json={"content": base64.b64encode(CONTENT.encode()).decode()})
        if request.method == "POST" and path.endswith("/pulls"):
            return httpx.Response(422, json={"message": "A pull request already exists for blizzard-new:" + BRANCH})
        if request.method == "GET" and path.endswith("/pulls"):
            assert request.url.params["head"] == f"blizzard-new:{BRANCH}"
            return httpx.Response(200, json=[{"number": 5, "html_url": "https://github.com/blizzard-new/abroad/pull/5"}])
        return friendly(request)

    http, _ = recorder(handler)
    assert open_pr(client(http)) == {"id": "5", "url": "https://github.com/blizzard-new/abroad/pull/5"}


def test_a_file_already_on_the_branch_with_other_content_is_an_error():
    def handler(request):
        if request.method == "PUT":
            return httpx.Response(422, json={"message": "\"sha\" wasn't supplied."})
        if request.method == "GET" and request.url.path.endswith(f"/contents/{PATH}"):
            return httpx.Response(200, json={"content": base64.b64encode(b"{}").decode()})
        return friendly(request)

    http, _ = recorder(handler)
    with pytest.raises(PlatformError) as error:
        open_pr(client(http))
    assert error.value.status == 422


def test_a_rejected_token_is_an_error_with_the_status_and_never_shows_the_token():
    http, _ = recorder(lambda request: httpx.Response(401, json={"message": "Bad credentials"}))
    with pytest.raises(PlatformError) as error:
        open_pr(client(http))
    assert error.value.status == 401 and "github_pat_secret" not in str(error.value)


def test_dry_run_never_touches_the_network_and_records_the_calls():
    http, calls = recorder(lambda request: pytest.fail("dry run sent a request"))
    github = GitHubClient("blizzard-new/abroad", "", dry_run=True, http=http)
    result = open_pr(github)
    assert result["id"].startswith("dry-pr-") and result["url"] == ""
    assert [c["method"] for c in github.calls] == ["GET", "POST", "PUT", "POST"] and github.calls[-1]["json"]["draft"] is True
    assert calls == []


def test_a_wrong_repo_or_a_missing_token_stops_before_any_request():
    http, calls = recorder(friendly)
    with pytest.raises(PlatformError, match="擁有者/名稱"):
        open_pr(GitHubClient("not a repo", "t", dry_run=False, http=http))
    with pytest.raises(PlatformError, match="權杖"):
        open_pr(GitHubClient("blizzard-new/abroad", "", dry_run=False, http=http))
    assert calls == []


def repo_handler(push=True, user=True):
    def handler(request):
        path = request.url.path
        if path == "/user":
            return httpx.Response(200, json={"login": "blizzard-new"}) if user else httpx.Response(403, json={"message": "forbidden"})
        if path == REPO_API:
            return httpx.Response(200, json={"full_name": "blizzard-new/abroad", "private": False, "permissions": {"push": push}})
        if path == f"{REPO_API}/branches/main":
            return httpx.Response(200, json={"name": "main"})
        return httpx.Response(404, json={})

    return handler


def test_linking_stores_the_token_with_the_account_and_checks_it_can_push(tmp_path):
    settings = Settings.from_env(env={"OFFICE_HOME": str(tmp_path)})
    store = Store(settings.db_path)
    http, _ = recorder(repo_handler())
    found = link_github(settings, store, "github_pat_x", http)
    assert found["login"] == "blizzard-new" and found["can_push"] and found["classic"] is False
    assert store.get("github_token") == "github_pat_x" and store.get("handle:github") == "blizzard-new"
    assert link_github(settings, store, "ghp_classic", http)["classic"] is True

    read_only, _ = recorder(repo_handler(push=False))
    other = Store(tmp_path / "other.sqlite3")
    with pytest.raises(PlatformError, match="不能寫入"):
        link_github(settings, other, "github_pat_ro", read_only)
    assert other.get("github_token") is None


def test_check_rows_say_what_is_missing_and_warn_about_classic_tokens(tmp_path):
    settings = Settings.from_env(env={"OFFICE_HOME": str(tmp_path)})
    store = Store(settings.db_path)
    assert github_row(settings, store).ok is None and "auth github" in github_row(settings, store).detail

    store.set("github_token", "github_pat_x")
    http, _ = recorder(repo_handler(user=False))  # a token that cannot read /user still works
    row = github_row(settings, store, http)
    assert row.ok is True and "blizzard-new/abroad" in row.detail and "模擬" in row.detail

    store.set("github_token", "ghp_classic")
    assert github_row(settings, store, http).ok is None and "傳統權杖" in github_row(settings, store, http).detail

    denied, _ = recorder(lambda request: httpx.Response(401, json={"message": "Bad credentials"}))
    assert github_row(settings, store, denied).ok is False
