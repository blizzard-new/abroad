import json
from pathlib import Path

import httpx

from office.config import Settings
from office.platforms.media_host import MediaHost
from office.platforms.meta import InstagramClient, ThreadsClient
from office.platforms.youtube import YouTubeClient


def recorder(handler):
    calls = []

    def transport(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    return httpx.Client(transport=httpx.MockTransport(transport)), calls


def test_threads_post_creates_container_waits_and_publishes():
    def handler(request):
        path = request.url.path
        if path.endswith("/threads"):
            return httpx.Response(200, json={"id": "c1"})
        if path.endswith("/threads_publish"):
            return httpx.Response(200, json={"id": "m1"})
        if path.endswith("/c1"):
            return httpx.Response(200, json={"status": "FINISHED"})
        if path.endswith("/m1"):
            return httpx.Response(200, json={"permalink": "https://www.threads.com/@uniway/post/x"})
        return httpx.Response(404)

    http, calls = recorder(handler)
    client = ThreadsClient("42", "secret", dry_run=False, http=http)
    result = client.post_text("哈囉", topic_tag="交換學生")
    assert result == {"id": "m1", "url": "https://www.threads.com/@uniway/post/x"}
    create = calls[0]
    assert create.method == "POST" and create.url.path == "/v1.0/42/threads"
    assert create.url.params["media_type"] == "TEXT" and create.url.params["topic_tag"] == "交換學生"
    assert calls[2].url.params["creation_id"] == "c1"
    assert all(c["params"].get("access_token") == "***" for c in client.calls)


def test_threads_post_with_a_picture_uses_an_image_container():
    def handler(request):
        path = request.url.path
        if path.endswith("/threads"):
            return httpx.Response(200, json={"id": "c1"})
        if path.endswith("/threads_publish"):
            return httpx.Response(200, json={"id": "m1"})
        return httpx.Response(200, json={"status": "FINISHED", "permalink": "https://www.threads.com/@uniway/post/y"})

    http, calls = recorder(handler)
    ThreadsClient("42", "secret", dry_run=False, http=http).post_text("哈囉", image_url="https://cdn/threads.jpg")
    assert calls[0].url.params["media_type"] == "IMAGE" and calls[0].url.params["image_url"] == "https://cdn/threads.jpg"
    assert calls[0].url.params["text"] == "哈囉"


def test_instagram_carousel_flow(tmp_path: Path):
    ids = iter(["k1", "k2", "parent"])

    def handler(request):
        path = request.url.path
        if path.endswith("/media"):
            return httpx.Response(200, json={"id": next(ids)})
        if path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "post"})
        if path.endswith("/post"):
            return httpx.Response(200, json={"permalink": "https://www.instagram.com/p/x/"})
        return httpx.Response(200, json={"status_code": "FINISHED"})

    http, calls = recorder(handler)
    client = InstagramClient("7", "t", dry_run=False, http=http)
    result = client.post_carousel(["https://cdn/a.jpg", "https://cdn/b.jpg"], "說明欄")
    assert result["id"] == "post"
    parent = [c for c in calls if c.url.params.get("media_type") == "CAROUSEL"][0]
    assert parent.url.params["children"] == "k1,k2"
    assert calls[-2].url.path.endswith("/7/media_publish")


def test_instagram_story_retries_when_the_container_is_not_found_yet(monkeypatch):
    monkeypatch.setattr("office.platforms.meta.time.sleep", lambda seconds: None)
    answers = iter([
        httpx.Response(400, json={"error": {"message": "The requested resource does not exist", "code": 24, "error_subcode": 2207006}}),
        httpx.Response(200, json={"id": "story"}),
    ])

    def handler(request):
        path = request.url.path
        if path.endswith("/media"):
            return httpx.Response(200, json={"id": "c1"})
        if path.endswith("/media_publish"):
            return next(answers)
        if path.endswith("/story"):
            return httpx.Response(200, json={"permalink": "https://www.instagram.com/stories/x/"})
        return httpx.Response(200, json={"status_code": "FINISHED"})

    http, calls = recorder(handler)
    client = InstagramClient("7", "t", dry_run=False, http=http)
    assert client.post_story("https://cdn/story.jpg")["id"] == "story"
    assert sum(c.url.path.endswith("/media_publish") for c in calls) == 2


def test_youtube_resumable_upload(tmp_path: Path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"0" * 10)

    def handler(request):
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "ya29"})
        if request.method == "POST":
            body = json.loads(request.content)
            assert body["status"]["privacyStatus"] == "private"
            assert body["snippet"]["title"] == "標題 #Shorts"
            return httpx.Response(200, headers={"Location": "https://upload.example/session"})
        return httpx.Response(200, json={"id": "vid"})

    http, calls = recorder(handler)
    client = YouTubeClient("id", "secret", "refresh", dry_run=False, http=http)
    result = client.upload(video, title="標題 #Shorts", description="d", tags=["交換學生"], privacy="private")
    assert result == {"id": "vid", "url": "https://youtu.be/vid"}
    assert calls[-1].method == "PUT" and calls[-1].headers["Authorization"] == "Bearer ya29"


def test_dry_run_never_touches_the_network(tmp_path: Path):
    def handler(request):
        raise AssertionError("dry run sent a request")

    http, _ = recorder(handler)
    client = ThreadsClient("", "", dry_run=True, http=http)
    assert client.post_text("x")["id"].startswith("dry-")
    settings = Settings.from_env(env={"OFFICE_HOME": str(tmp_path), "OFFICE_MEDIA_HOST": "supabase", "SUPABASE_URL": "https://p.supabase.co"})
    image = settings.media_dir / "a.jpg"
    image.write_bytes(b"x")
    host = MediaHost(settings, dry_run=True, http=http)
    assert host.public_url(image) == "https://p.supabase.co/storage/v1/object/public/marketing-media/a.jpg"
