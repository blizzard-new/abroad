from datetime import date

from office.brand import BrandFacts, Briefing, NewsItem
from office.llm import OfflineWriter, _wrap
from office.models import PlanItem
from office.offline_bank import TOPICS
from office.rules import check_carousel, check_threads, check_video

FACTS = BrandFacts(university_count=33, partner_count=5730, universities=("臺大",), site_url="https://app.uniway-tw.com", source="test")
NEWS = NewsItem(school="淡江大學", summary="甄選說明會報名額滿，此為說明會額滿，不是交換名額額滿。仍可現場候補。", source_url="https://oia.tku.edu.tw/x", checked_date="2026-10-22")


def item(**kw):
    base = dict(channel="threads", format="text", pillar="value", angle="pain", topic=TOPICS[0].title, brief=TOPICS[0].key)
    base.update(kw)
    return PlanItem(**base)


def test_every_offline_topic_passes_review_in_every_format():
    writer = OfflineWriter()
    briefing = Briefing(day=date(2026, 10, 23), facts=FACTS)
    for topic in TOPICS:
        for angle in ("pain", "choice", "list", "story"):
            draft = writer.threads(item(topic=topic.title, brief=topic.key, angle=angle), briefing)
            assert check_threads(draft, FACTS) == [], (topic.key, angle)
        ig = item(channel="instagram", format="carousel", topic=topic.title, brief=topic.key)
        assert check_carousel(writer.carousel(ig, briefing), FACTS) == [], topic.key
        assert check_video(writer.video(ig, briefing, "short"), FACTS, "short") == [], topic.key


def test_news_post_cites_the_official_source():
    writer = OfflineWriter()
    briefing = Briefing(day=date(2026, 10, 23), facts=FACTS, news=[NEWS])
    draft = writer.threads(item(angle="news", source_url=NEWS.source_url, topic="淡江大學交換公告更新"), briefing)
    assert NEWS.source_url in draft.first_reply
    assert "http" not in draft.text
    assert check_threads(draft, FACTS, NEWS.source_url) == []


def test_plan_keeps_the_slot_layout_and_leads_with_news():
    writer = OfflineWriter()
    briefing = Briefing(day=date(2026, 10, 25), facts=FACTS, news=[NEWS])
    slots = [item(topic="", brief=""), item(topic="", brief=""), item(channel="instagram", format="reel", pillar="reach", topic="", brief=""),
             item(channel="youtube", format="long", topic="", brief="")]
    plan = writer.plan_day(briefing, slots)
    assert [(i.channel, i.format) for i in plan.items] == [(s.channel, s.format) for s in slots]
    assert plan.items[0].angle == "news" and plan.items[0].source_url == NEWS.source_url
    assert all(i.topic for i in plan.items)
    long = writer.video(plan.items[3], briefing, "long")
    assert check_video(long, FACTS, "long") == []


def test_weekly_long_video_names_its_sources():
    briefing = Briefing(day=date(2026, 10, 25), facts=FACTS, news=[NEWS])
    script = OfflineWriter().video(item(channel="youtube", format="long", angle="news", topic="本週", brief="weekly"), briefing, "long")
    assert NEWS.source_url in script.youtube_description
    assert any(scene.heading.startswith("淡江") for scene in script.scenes)


def test_caption_wrapping_breaks_at_punctuation_and_particles():
    assert _wrap("寫出課程、研究或環境的具體理由，不要只寫排名", 12) == ["寫出課程", "研究或環境的具體理由", "不要只寫排名"]
    assert _wrap("每間合作校接受的檢定與分數都不一樣", 12) == ["每間合作校接受的", "檢定與分數都不一樣"]
