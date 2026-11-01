"""A Threads post with several pictures that swipe, like an Instagram carousel."""

import json
import time
from datetime import date

import httpx
import pytest

from office.brand import BrandFacts, Briefing
from office.llm import OfflineWriter
from office.models import ChiefAction, PlanItem, Slide, ThreadsAlbumDraft
from office.offline_bank import TOPICS
from office.platforms.base import PlatformError
from office.platforms.meta import ThreadsClient
from office.rules import check_threads_album
from test_render import chromium_available

needs_chromium = pytest.mark.skipif(not chromium_available(), reason="needs Chromium")
FACTS = BrandFacts(university_count=33, partner_count=5730, universities=("臺大",), site_url="https://app.uniway-tw.com", source="test")
DAY = date(2026, 10, 23)  # a Friday


def album_item(**kw):
    base = dict(channel="threads", format="carousel", pillar="value", angle="list", topic=TOPICS[1].title, brief=TOPICS[1].key)
    base.update(kw)
    return PlanItem(**base)


def good_album(**changes) -> ThreadsAlbumDraft:
    slides = [
        Slide(kind="cover", title="托福還是雅思？", body="先看這 3 件事"),
        Slide(kind="point", title="先看目標學校", body="每間接受的檢定與分數都不同"),
        Slide(kind="point", title="注意有效期限", body="成績多半有期限，以各校規定為準"),
        Slide(kind="cta", title="收藏起來慢慢看", body="UniWay 依語言檢定篩選合作校｜連結在第一則留言"),
    ]
    data = dict(text="語言檢定先考哪個？\n\n小編整理成三張圖，左右滑看 👉", topic_tag="交換學生", first_reply="整理好的在 app.uniway-tw.com", slides=slides)
    data.update(changes)
    return ThreadsAlbumDraft(**data)


# ---- what the day plans ----
def formats(office, **_):
    return [slot.format for slot in office.staff["strategist"].slots(DAY) if slot.channel == "threads"]


def test_the_latest_threads_post_of_the_day_is_the_multi_image_one(make_office):
    # Pictures are drawn and the (simulated) account has somewhere to fetch them from: the evening post is a carousel.
    assert formats(make_office(OFFICE_RENDER_MEDIA=1)) == ["text", "carousel"]
    assert formats(make_office(OFFICE_RENDER_MEDIA=1, OFFICE_THREADS_ALBUMS=0)) == ["text", "text"]
    assert formats(make_office(OFFICE_RENDER_MEDIA=1, OFFICE_THREADS_ALBUMS=2)) == ["carousel", "carousel"]
    assert formats(make_office(OFFICE_RENDER_MEDIA=1, OFFICE_THREADS_ALBUMS=9)) == ["carousel", "carousel"]  # never more than the day has
    assert formats(make_office(OFFICE_RENDER_MEDIA=1, OFFICE_THREADS_ALBUMS="lots")) == ["text", "carousel"]  # not a number: the default


def test_without_pictures_or_a_place_for_them_the_slot_stays_a_plain_post(make_office):
    assert formats(make_office(OFFICE_RENDER_MEDIA=0)) == ["text", "text"]  # nothing is drawn
    # Going out for real with no public address for the pictures: they could not reach Threads.
    assert formats(make_office(OFFICE_RENDER_MEDIA=1, OFFICE_DRY_RUN=0)) == ["text", "text"]
    assert formats(make_office(OFFICE_RENDER_MEDIA=1, OFFICE_DRY_RUN=0, OFFICE_MEDIA_HOST="supabase")) == ["text", "carousel"]


# ---- the words and the pages are checked together ----
def test_a_good_album_passes_and_the_page_rules_are_the_carousels():
    assert check_threads_album(good_album(), FACTS) == []
    two = good_album(slides=good_album().slides[:2])
    assert any("圖片 2 張" in issue for issue in check_threads_album(two, FACTS))
    no_cta = good_album(slides=good_album().slides[:-1])
    assert any("最後一張要是行動呼籲" in issue for issue in check_threads_album(no_cta, FACTS))


def test_threads_rules_still_apply_to_the_post_itself(make_office):
    assert any("網址" in i for i in check_threads_album(good_album(text="看這裡 https://app.uniway-tw.com"), FACTS))
    assert any("500" in i for i in check_threads_album(good_album(text="交" * 520), FACTS))


def test_the_link_lives_in_the_first_reply_not_on_the_pictures():
    pages = good_album().slides
    wrong = [*pages[:-1], pages[-1].model_copy(update={"body": "UniWay 依語言檢定篩選合作校｜連結在主頁"})]
    assert any("連結在第一則留言" in i for i in check_threads_album(good_album(slides=wrong), FACTS))
    url = [*pages[:-1], pages[-1].model_copy(update={"body": "到 app.uniway-tw.com 查"})]
    assert any("不要放網址" in i for i in check_threads_album(good_album(slides=url), FACTS))


def test_claims_and_ai_phrases_on_the_pictures_are_caught_too():
    pages = good_album().slides
    banned = [pages[0], pages[1].model_copy(update={"body": "保證錄取的選法"}), *pages[2:]]
    assert any("保證錄取" in i for i in check_threads_album(good_album(slides=banned), FACTS))
    wordy = [pages[0], pages[1].model_copy(update={"body": "總而言之先看學校"}), *pages[2:]]
    assert any("口頭禪" in i for i in check_threads_album(good_album(slides=wordy), FACTS))


def test_every_offline_topic_makes_an_album_that_passes_review():
    writer, briefing = OfflineWriter(), Briefing(day=DAY, facts=FACTS)
    for topic in TOPICS:
        for angle in ("pain", "choice", "list", "story", "news"):
            album = writer.threads_album(album_item(topic=topic.title, brief=topic.key, angle=angle), briefing)
            assert check_threads_album(album, FACTS) == [], (topic.key, angle)
            assert "連結在第一則留言" in album.slides[-1].body and "連結在主頁" not in album.slides[-1].body


# ---- the Threads API call ----
def recorder(handler):
    calls = []

    def transport(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    return httpx.Client(transport=httpx.MockTransport(transport)), calls


def test_a_threads_carousel_is_one_container_per_picture_and_then_one_that_holds_them():
    made = []

    def handler(request):
        path = request.url.path
        if path.endswith("/threads"):
            made.append(request.url.params)
            return httpx.Response(200, json={"id": f"c{len(made)}"})
        if path.endswith("/threads_publish"):
            return httpx.Response(200, json={"id": "m1"})
        return httpx.Response(200, json={"status": "FINISHED", "permalink": "https://www.threads.com/@uniway/post/z"})

    http, calls = recorder(handler)
    client = ThreadsClient("42", "secret", dry_run=False, http=http)
    result = client.post_carousel(["https://cdn/1.jpg", "https://cdn/2.jpg", "https://cdn/3.jpg"], "左右滑看圖", topic_tag="交換學生")
    assert result == {"id": "m1", "url": "https://www.threads.com/@uniway/post/z"}
    *items, parent = made
    assert [p["image_url"] for p in items] == ["https://cdn/1.jpg", "https://cdn/2.jpg", "https://cdn/3.jpg"]
    assert all(p["media_type"] == "IMAGE" and p["is_carousel_item"] == "true" and "text" not in p for p in items)
    assert parent["media_type"] == "CAROUSEL" and parent["children"] == "c1,c2,c3" and parent["text"] == "左右滑看圖" and parent["topic_tag"] == "交換學生"
    publish = next(c for c in calls if c.url.path.endswith("/threads_publish"))
    assert publish.url.params["creation_id"] == "c4"  # the carousel container, not one of its pictures


def test_a_threads_carousel_takes_two_to_twenty_pictures():
    client = ThreadsClient("42", "secret", dry_run=True)
    for urls in (["https://cdn/1.jpg"], [f"https://cdn/{n}.jpg" for n in range(21)]):
        with pytest.raises(PlatformError, match="2～20"):
            client.post_carousel(urls, "x")
    assert client.post_carousel([f"https://cdn/{n}.jpg" for n in range(20)], "x")["id"].startswith("dry-")


# ---- the writer and the boss ----
def test_the_boss_can_ask_for_an_album_and_ask_to_rewrite_it(make_office):
    office = make_office()
    chief = office.staff["chief"]
    answer = chief.execute(ChiefAction(type="new_post", channel="threads", format="carousel", topic="語言檢定怎麼選", angle="list", instructions="用三張圖講清楚"))
    assert "阿脆" in answer  # the Threads writer makes it; Mori draws the pages
    end = time.time() + 10
    while time.time() < end and not [d for d in office.store.drafts() if d["format"] == "carousel"]:
        time.sleep(0.05)
    draft = next(d for d in office.store.drafts() if d["channel"] == "threads" and d["format"] == "carousel")
    assert draft["status"] == "pending_approval" and draft["payload"]["slides"][0]["kind"] == "cover" and draft["payload"]["first_reply"]

    note = chief._rewrite(draft, "threads", "主文再口語一點")
    after = office.store.draft(draft["id"])
    assert "改好了" in note and (after["channel"], after["format"]) == ("threads", "carousel") and len(after["payload"]["slides"]) == len(draft["payload"]["slides"])


# ---- the whole way, with real pictures ----
@needs_chromium
def test_an_album_is_drawn_by_mori_published_with_all_its_pictures_and_redrawn_on_request(make_office):
    office = make_office(OFFICE_RENDER_MEDIA=1, OFFICE_MEDIA_HOST="supabase", SUPABASE_URL="https://p.supabase.co")
    briefing = Briefing(day=DAY, facts=office.facts())
    draft_id = office.staff["threads"].produce(None, album_item(), briefing, office.at(DAY, __import__("datetime").time(21, 0)))
    draft = office.store.draft(draft_id)
    pages = draft["payload"]["slides"]
    assert (draft["channel"], draft["format"], draft["status"]) == ("threads", "carousel", "pending_approval")
    assert len(draft["media"]["images"]) == len(pages) >= 4
    assert all((office.settings.media_dir / ref).is_file() for ref in draft["media"]["images"]) and draft["payload"]["visual_plan"]

    published = office.staff["publisher"].publish(draft)
    assert published["status"] == "published"
    record = json.loads(next((office.settings.outbox_dir / "2026-10-23").glob(f"{draft_id:05d}-threads-carousel.json")).read_text(encoding="utf-8"))
    sent = [c["params"] for c in record["calls"] if c["url"].endswith("/threads")]
    children, parent, reply = sent[: len(pages)], sent[len(pages)], sent[len(pages) + 1]
    assert all(p["media_type"] == "IMAGE" and p["is_carousel_item"] == "true" for p in children)
    assert parent["media_type"] == "CAROUSEL" and parent["text"] == draft["payload"]["text"] and parent["topic_tag"] == "交換學生"
    assert len(parent["children"].split(",")) == len(pages)
    assert reply["text"] == draft["payload"]["first_reply"] and "reply_to_id" in reply  # the link goes in the first reply, as for any Threads post

    # "#N 的圖重做": the same words, new pictures
    fresh = office.store.add_draft(run_id=None, day="2026-10-23", channel="threads", format="carousel", title=draft["title"], payload=draft["payload"],
                                   media=draft["media"], status="rejected")
    note = office.staff["designer"].remake(office.store.draft(fresh), "封面標題更大")
    again = office.store.draft(fresh)
    assert "重新設計好了" in note and again["media"]["images"] != draft["media"]["images"] and again["payload"]["slides"] == pages
