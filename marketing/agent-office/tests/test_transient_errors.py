"""Meta answers 500 "is_transient" now and then, sometimes after the post is already live.

The office used to mark such a post "發佈失敗": the post stayed on Threads with no id and no numbers, the link comment was
never posted, and approving the card again would have posted it twice.
"""

from datetime import datetime, timedelta, timezone

import httpx
import pytest

from office.platforms.base import PlatformError, says_transient
from office.platforms.meta import ThreadsClient

FAST = (0.0, 0.0)  # no real waiting in tests


def recorder(handler):
    calls = []

    def transport(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    return httpx.Client(transport=httpx.MockTransport(transport)), calls


def temporary_500():
    return httpx.Response(500, json={"error": {
        "message": "An unexpected error has occurred. Please retry your request later.",
        "type": "OAuthException", "is_transient": True, "code": 2,
    }})


def stamp(ago: timedelta = timedelta(0)) -> str:
    return (datetime.now(timezone.utc) - ago).strftime("%Y-%m-%dT%H:%M:%S+0000")


def listing(*items):
    return httpx.Response(200, json={"data": list(items)})


def made(text: str, ago: timedelta = timedelta(0), id: str = "live1") -> dict:
    return {"id": id, "text": text, "permalink": f"https://www.threads.com/@uniway/post/{id}", "timestamp": stamp(ago)}


def threads_client(handler):
    http, calls = recorder(handler)
    client = ThreadsClient("42", "secret", dry_run=False, http=http)
    client.retry_waits = FAST
    return client, calls


def publishes(calls):
    return [c for c in calls if c.url.path.endswith("/threads_publish")]


def containers(calls):
    return [c for c in calls if c.method == "POST" and c.url.path.endswith("/42/threads")]


class Meta:
    """A scriptable stand-in for the Threads API: each step is a list of answers used in turn (the last one repeats)."""

    def __init__(self, *, create=(), publish=(), posts=(), replies=()):
        self.create, self.publish, self.posts, self.replies = list(create), list(publish), list(posts), list(replies)
        self.made = 0

    @staticmethod
    def _next(answers):
        answer = answers.pop(0) if len(answers) > 1 else answers[0]
        if isinstance(answer, Exception):
            raise answer
        return answer

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and path.endswith("/42/threads"):
            if self.create:
                return self._next(self.create)
            self.made += 1
            return httpx.Response(200, json={"id": f"c{self.made}"})
        if path.endswith("/threads_publish"):
            return self._next(self.publish) if self.publish else httpx.Response(200, json={"id": "m1"})
        if path.endswith("/42/threads"):
            return self._next(self.posts) if self.posts else listing()
        if path.endswith("/42/replies"):
            return self._next(self.replies) if self.replies else listing()
        if path.split("/")[-1].startswith("c"):
            return httpx.Response(200, json={"status": "FINISHED"})
        return httpx.Response(200, json={"permalink": "https://www.threads.com/@uniway/post/m1"})


# ---- what counts as temporary ----
def test_a_server_error_or_metas_own_flag_is_temporary_and_a_plain_refusal_is_not():
    assert says_transient(httpx.Response(500, json={"error": {"is_transient": True}}))
    assert says_transient(httpx.Response(502, text="Bad Gateway"))
    assert says_transient(httpx.Response(400, json={"error": {"is_transient": True, "code": 2}}))
    assert not says_transient(httpx.Response(400, json={"error": {"message": "Invalid parameter", "code": 100}}))
    assert not says_transient(httpx.Response(401, json={"error": {"type": "OAuthException", "code": 190}}))
    assert not says_transient(httpx.Response(429, text="slow down"))


def test_the_error_carries_the_flag_for_a_500_and_for_no_answer_at_all():
    client, _ = threads_client(Meta(create=[temporary_500()]))
    with pytest.raises(PlatformError) as caught:
        client.post_text("哈囉")
    assert caught.value.status == 500 and caught.value.transient

    def silent(request):
        raise httpx.ConnectTimeout("no answer", request=request)

    client, _ = threads_client(silent)
    with pytest.raises(PlatformError) as caught:
        client.me()
    assert caught.value.status == 0 and "沒有回應" in str(caught.value)  # the network gave nothing: still a PlatformError


# ---- steps that are safe to repeat ----
def test_a_temporary_failure_making_a_container_is_simply_tried_again():
    meta = Meta(create=[temporary_500(), httpx.Response(200, json={"id": "c1"})])
    client, calls = threads_client(meta)
    assert client.post_text("哈囉")["id"] == "m1"
    assert len(containers(calls)) == 2 and len(publishes(calls)) == 1


def test_it_gives_up_after_three_tries_and_says_the_failure_was_temporary():
    meta = Meta(create=[temporary_500()])
    client, calls = threads_client(meta)
    with pytest.raises(PlatformError) as caught:
        client.post_text("哈囉")
    assert caught.value.transient and len(containers(calls)) == 3 and not publishes(calls)


def test_a_real_refusal_is_not_repeated():
    meta = Meta(create=[httpx.Response(400, json={"error": {"message": "Invalid parameter", "code": 100}})])
    client, calls = threads_client(meta)
    with pytest.raises(PlatformError) as caught:
        client.post_text("哈囉")
    assert not caught.value.transient and len(containers(calls)) == 1


# ---- the publish step: look before repeating ----
def test_a_publish_that_answered_500_but_went_live_is_found_and_not_posted_twice():
    # The case from the 12:30 post: Threads says "unexpected error" and the post is on the profile anyway.
    meta = Meta(publish=[temporary_500()], posts=[listing(made("選交換學校，先看這三件事", id="live1"))])
    client, calls = threads_client(meta)
    result = client.post_text("選交換學校，先看這三件事")
    assert result == {"id": "live1", "url": "https://www.threads.com/@uniway/post/live1"}
    assert len(publishes(calls)) == 1


def test_a_publish_that_really_failed_is_published_again():
    meta = Meta(publish=[temporary_500(), httpx.Response(200, json={"id": "m1"})], posts=[listing(made("別的貼文"))])
    client, calls = threads_client(meta)
    assert client.post_text("選交換學校")["id"] == "m1"
    assert len(publishes(calls)) == 2


def test_a_timeout_on_publish_is_treated_like_a_temporary_error():
    meta = Meta(publish=[httpx.ReadTimeout("slow", request=httpx.Request("POST", "https://graph.threads.net/x"))],
                posts=[listing(made("選交換學校"))])
    client, calls = threads_client(meta)
    assert client.post_text("選交換學校")["id"] == "live1" and len(publishes(calls)) == 1


def test_the_same_words_posted_long_ago_are_not_this_post():
    meta = Meta(publish=[temporary_500()], posts=[listing(made("選交換學校", ago=timedelta(days=2)))])
    client, calls = threads_client(meta)
    with pytest.raises(PlatformError) as caught:
        client.post_text("選交換學校")
    assert caught.value.transient and len(publishes(calls)) == 3


def test_matching_ignores_line_breaks_and_spacing():
    meta = Meta(publish=[temporary_500()], posts=[listing(made("選交換學校\n\n先看這三件事  "))])
    client, calls = threads_client(meta)
    assert client.post_text("選交換學校 先看這三件事")["id"] == "live1"


def test_a_reply_is_looked_for_among_the_replies_not_the_posts():
    meta = Meta(publish=[temporary_500()], posts=[listing(made("連結在 app.uniway-tw.com", id="wrong"))],
                replies=[listing(made("連結在 app.uniway-tw.com", id="reply1"))])
    client, calls = threads_client(meta)
    assert client.post_text("連結在 app.uniway-tw.com", reply_to_id="m0")["id"] == "reply1"
    assert any(c.url.path.endswith("/42/replies") for c in calls)


def test_a_refusal_when_publishing_is_not_second_guessed():
    meta = Meta(publish=[httpx.Response(400, json={"error": {"message": "The media is not ready", "code": 24}})])
    client, calls = threads_client(meta)
    with pytest.raises(PlatformError) as caught:
        client.post_text("選交換學校")
    assert not caught.value.transient and len(publishes(calls)) == 1
    assert not any(c.method == "GET" and c.url.path.endswith(("/42/threads", "/42/replies")) for c in calls)


def test_a_carousel_that_went_live_after_a_500_is_found_too():
    meta = Meta(publish=[temporary_500()], posts=[listing(made("三張圖看懂", id="album1"))])
    client, calls = threads_client(meta)
    result = client.post_carousel(["https://cdn/1.jpg", "https://cdn/2.jpg"], "三張圖看懂")
    assert result["id"] == "album1" and len(publishes(calls)) == 1


def test_nothing_is_looked_up_when_nothing_is_sent():
    client = ThreadsClient("42", "secret", dry_run=True)
    assert client.post_text("哈囉")["id"].startswith("dry-")
    assert [c["method"] for c in client.calls] == ["POST", "POST", "GET"]  # the container, the publish, the link: no lookup


# ---- the publisher: what the boss sees ----
def approved_draft(office, **payload):
    base = {"text": "選交換學校，先看這三件事", "topic_tag": "交換學生", "first_reply": "整理好的在 app.uniway-tw.com"}
    base.update(payload)
    return office.store.add_draft(run_id=None, day="2026-11-06", channel="threads", format="text", title="選交換學校", payload=base,
                                  status="approved", scheduled_at="2026-11-06T04:30:00+00:00")


def desk(make_office, meta):
    office = make_office()
    publisher = office.staff["publisher"]
    http, calls = recorder(meta)
    client = ThreadsClient("42", "secret", dry_run=False, http=http, log=publisher._log)
    client.retry_waits = FAST
    publisher.clients = lambda: {"threads": client}
    return office, publisher, calls


def test_a_post_that_went_live_despite_a_500_is_recorded_as_published_and_gets_its_link_comment(make_office):
    meta = Meta(publish=[temporary_500(), httpx.Response(200, json={"id": "m2"})],
                posts=[listing(made("選交換學校，先看這三件事", id="live1"))])
    office, publisher, calls = desk(make_office, meta)
    draft_id = approved_draft(office)
    done = publisher.publish(office.store.draft(draft_id))
    assert done["status"] == "published" and done["remote_id"] == "live1" and not done["error"]
    reply = containers(calls)[-1]
    assert reply.url.params["reply_to_id"] == "live1" and "app.uniway-tw.com" in reply.url.params["text"]


def test_if_only_the_link_comment_fails_the_post_still_counts_and_the_boss_is_told(make_office):
    # The post goes out; then every try to make the reply container is refused.
    refused = httpx.Response(400, json={"error": {"message": "Invalid parameter", "code": 100}})

    class FirstThenRefuse(Meta):
        def __call__(self, request):
            if request.method == "POST" and request.url.path.endswith("/42/threads") and self.made >= 1:
                return refused
            return super().__call__(request)

    office, publisher, calls = desk(make_office, FirstThenRefuse())
    draft_id = approved_draft(office)
    done = publisher.publish(office.store.draft(draft_id))
    assert done["status"] == "published" and done["remote_id"] == "m1"
    assert "第一則留言" in done["error"] and "手動補上" in done["error"]
    said = [m["text"] for m in office.store.chat() if "第一則留言" in m["text"]]
    assert said and "https://www.threads.com/@uniway/post/m1" in said[-1]


def test_a_post_that_really_failed_is_still_reported_as_failed_and_can_be_approved_again(make_office):
    meta = Meta(create=[httpx.Response(400, json={"error": {"message": "Invalid parameter", "code": 100}})])
    office, publisher, calls = desk(make_office, meta)
    draft_id = approved_draft(office)
    done = publisher.publish(office.store.draft(draft_id))
    assert done["status"] == "failed" and "Invalid parameter" in done["error"] and not done["remote_id"]
    assert office.approve(draft_id, publish_now=True)["status"] == "approved"


def test_a_plain_publish_still_works_and_has_no_error(make_office):
    office, publisher, calls = desk(make_office, Meta())
    done = publisher.publish(office.store.draft(approved_draft(office)))
    assert done["status"] == "published" and done["remote_id"] == "m1" and not done["error"]
    assert len(publishes(calls)) == 2  # the post and its link comment
