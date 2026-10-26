from datetime import date

from fastapi.testclient import TestClient

from office.config import Settings
from office.office import Office
from office.pipeline import run_day
from office.server import create_app


def client_for(tmp_path, **env):
    settings = Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0", **env})
    office = Office(settings)
    return TestClient(create_app(settings, clock=False, office=office)), office


def test_page_state_and_approval(tmp_path):
    client, office = client_for(tmp_path)
    assert client.get("/").status_code == 200
    assert "UniWay 行銷辦公室" in client.get("/").text
    run_day(office, date(2026, 10, 23))
    state = client.get("/api/state").json()
    assert [a["id"] for a in state["agents"]][:2] == ["strategist", "threads"]
    assert state["settings"]["dry_run"] is True
    draft = state["drafts"][0]
    approved = client.post(f"/api/drafts/{draft['id']}/approve", json={"now": False}).json()
    assert approved["status"] == "approved"
    assert client.post("/api/drafts/9999/approve", json={}).status_code == 404


def test_office_scripts_load_as_fresh_javascript(tmp_path):
    # Windows' registry can map .js to text/plain, and a cached old office.js leaves the 3D office stuck loading.
    client, _ = client_for(tmp_path)
    for name in ("office.js", "office-world.js", "vendor/three.module.min.js"):
        response = client.get(f"/static/{name}")
        assert response.headers["content-type"].startswith("text/javascript")
        assert response.headers["cache-control"] == "no-cache"


def test_access_token_guards_everything_but_media(tmp_path):
    client, office = client_for(tmp_path, OFFICE_ACCESS_TOKEN="open-sesame")
    (office.settings.media_dir / "x.jpg").write_bytes(b"jpg")
    assert client.get("/api/state").status_code == 401
    assert client.get("/media/x.jpg").status_code == 200
    assert client.get("/?token=open-sesame").status_code == 200
    assert client.get("/api/state").status_code == 200  # the cookie remembers the token


def test_media_paths_cannot_escape_the_media_folder(tmp_path):
    client, _ = client_for(tmp_path)
    assert client.get("/media/..%2Foffice.sqlite3").status_code == 404
