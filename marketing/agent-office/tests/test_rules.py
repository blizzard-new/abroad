from office.brand import BrandFacts
from office.models import CarouselDraft, Scene, Slide, ThreadsDraft, VideoScript
from office.rules import check_carousel, check_threads, check_video, display_width, threads_length

FACTS = BrandFacts(university_count=33, partner_count=5730, universities=("臺大",), site_url="https://app.uniway-tw.com", source="test")


def threads(text="交換生舉手 🙋\n\n1. 先查名額", reply="資料在 app.uniway-tw.com", tag="交換學生"):
    return ThreadsDraft(text=text, topic_tag=tag, first_reply=reply)


def test_clean_threads_post_passes():
    assert check_threads(threads(), FACTS) == []


def test_threads_keeps_links_out_of_the_main_post():
    issues = check_threads(threads(text="看這裡 https://app.uniway-tw.com"), FACTS)
    assert any("網址" in issue for issue in issues)


def test_threads_counts_emoji_as_bytes():
    assert threads_length("a🙋") == 1 + len("🙋".encode())
    assert any("500" in i for i in check_threads(threads(text="交" * 480 + "🙋" * 6), FACTS))


def test_threads_topic_tag_rules():
    assert any("topic tag" in i for i in check_threads(threads(tag="a.b"), FACTS))
    assert any("hashtag" in i for i in check_threads(threads(text="交換 #留學"), FACTS))


def test_first_reply_must_carry_the_site():
    assert any("第一則留言" in i for i in check_threads(threads(reply="快去看"), FACTS))


def test_claims_cannot_exceed_platform_numbers():
    issues = check_threads(threads(text="已支援 60 所大學、9,999 筆合作校"), FACTS)
    assert any("33 所大學" in i for i in issues)
    assert any("5,730" in i for i in issues)
    assert check_threads(threads(text="已支援 33 所大學、5,730 筆合作校資料"), FACTS) == []


def test_banned_phrases_and_unsourced_dates():
    assert any("保證錄取" in i for i in check_threads(threads(text="保證錄取的祕訣"), FACTS))
    assert any("日期" in i for i in check_threads(threads(text="11/15 截止"), FACTS))
    assert check_threads(threads(text="11/15 截止，以官方公告為準"), FACTS, source_url="https://oia.example.edu.tw") == []


def carousel(**changes):
    data = dict(
        slides=[Slide(kind="cover", title="封面", body=""), Slide(kind="point", title="重點", body="內容"), Slide(kind="cta", title="收藏", body="")],
        caption="說明欄，連結在主頁",
        hashtags=["#交換學生", "#出國交換"],
    )
    data.update(changes)
    return CarouselDraft(**data)


def test_carousel_shape_and_hashtag_cap():
    assert check_carousel(carousel(), FACTS) == []
    six = [f"#tag{i}" for i in range(6)]
    assert any("hashtag" in i for i in check_carousel(carousel(hashtags=six), FACTS))
    assert any("封面" in i for i in check_carousel(carousel(slides=list(reversed(carousel().slides))), FACTS))
    assert any("網址" in i for i in check_carousel(carousel(caption="去 app.uniway-tw.com 看"), FACTS))


def video(seconds=(3, 6, 6, 6, 5, 5), lines=("先抓校內截止",)):
    kinds = ["hook", "point", "point", "point", "stat", "cta"]
    scenes = [Scene(kind=k, heading="標題", lines=list(lines), seconds=s) for k, s in zip(kinds, seconds)]
    return VideoScript(title="t", scenes=scenes, caption="c", hashtags=["#交換學生"], youtube_title="t #Shorts", youtube_description="d")


def test_short_video_rules():
    assert check_video(video(), FACTS, "short") == []
    assert any("長度" in i for i in check_video(video(seconds=(3, 30, 30, 30, 5, 5)), FACTS, "short"))
    assert any("鉤子" in i for i in check_video(video(seconds=(6, 6, 6, 6, 5, 5)), FACTS, "short"))
    assert any("字幕" in i for i in check_video(video(lines=("這一行字幕真的寫得太長了根本看不完啦",)), FACTS, "short"))


def test_latin_text_counts_half_width():
    assert display_width("app.uniway-tw.com") < 16
    assert display_width("交換申請一站搞定") == 8
