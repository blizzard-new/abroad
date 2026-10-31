"""Copy that reads like a model wrote it is sent back, and the writers are told up front what to avoid."""

from datetime import date

from office import humanize
from office.brand import VOICE_GUIDE, BrandFacts, Briefing
from office.models import CarouselDraft, PlanItem, Scene, Slide, ThreadsDraft, VideoScript
from office.rules import check_carousel, check_threads, check_video

FACTS = BrandFacts(university_count=33, partner_count=5730, universities=("臺大",), site_url="https://app.uniway-tw.com", source="test")
REPLY = "整理好的在 app.uniway-tw.com"


def test_stock_phrases_are_named_so_the_author_knows_what_to_change():
    issues = humanize.check("總而言之，讓我們一起把交換申請準備好。")
    assert len(issues) == 1 and "總而言之" in issues[0] and "讓我們" in issues[0] and "口頭禪" in issues[0]


def test_sentence_frames_a_model_loves_are_caught():
    for text, frame in (
        ("交換不僅能看世界，更能認識自己", "不僅…更…"),
        ("交換不僅僅是出國玩，還是一段經歷", "不僅…更…"),
        ("這不只是一份清單，更是你的行前準備", "不只是…更是…"),
        ("在資訊爆炸的時代，找資料很累", "在…的時代"),
        ("隨著交換熱潮的發展，名額變搶手", "隨著…的發展"),
    ):
        assert any(frame in issue for issue in humanize.check(text)), text


def test_a_single_contrast_is_how_people_talk_but_a_pile_of_them_is_not():
    assert humanize.check("成績不是唯一，而是其中一項。") == []
    issues = humanize.check("不是成績，而是動機。不是語言，而是態度。")
    assert len(issues) == 1 and "2 次" in issues[0]


def test_dashes_are_limited_by_how_much_copy_there_is():
    two = "先查名額——再查語言——最後才投件"
    assert any("2 個" in issue for issue in humanize.check(two))
    assert humanize.check(two, max_dashes=humanize.PAGES_DASHES) == []
    assert humanize.check("先查名額，再查語言——最後才投件") == []
    assert humanize.check("——" * 1) == []  # a double dash is one dash, not two


def test_ordinary_student_talk_is_left_alone():
    post = (
        "交換生舉手 🙋 你是不是也卡在托福成績？\n\n"
        "我們整理了 33 所大學的語言門檻，有人要 80、有人只要 72。不是每間學校都看成績單，先查再說！\n\n"
        "你的學校要多少分？留言告訴我們 👇"
    )
    assert humanize.check(post) == []


def test_every_rule_in_the_check_is_also_in_the_guide_the_writers_read():
    assert humanize.guide() in VOICE_GUIDE
    for phrase in humanize.STOCK_PHRASES:
        assert phrase in VOICE_GUIDE
    assert "不僅…更…" in VOICE_GUIDE and "破折號" in VOICE_GUIDE


# ---- wired into the three kinds of draft ----
def threads(text):
    return ThreadsDraft(text=text, topic_tag="交換學生", first_reply=REPLY)


def test_a_threads_post_that_sounds_like_ai_does_not_pass():
    assert check_threads(threads("總而言之，交換前先查語言門檻。"), FACTS)[0].startswith("像 AI 寫的口頭禪")
    assert check_threads(threads("交換前先查語言門檻。"), FACTS) == []
    assert any("口頭禪" in i for i in check_threads(ThreadsDraft(text="先查門檻", topic_tag="交換學生", first_reply=REPLY + " 讓我們一起加油"), FACTS))


def test_a_carousel_and_a_video_script_are_checked_across_all_their_pages():
    slides = [Slide(kind="cover", title="交換前必看", body=""), Slide(kind="point", title="語言", body="值得注意的是門檻不同"), Slide(kind="cta", title="收藏", body="連結在主頁")]
    carousel = CarouselDraft(slides=slides, caption="先收藏\n\n連結在主頁", hashtags=["#交換學生"], art_prompt="x")
    assert any("值得注意的是" in i for i in check_carousel(carousel, FACTS))
    assert not any("口頭禪" in i for i in check_carousel(carousel.model_copy(update={"slides": [slides[0], slides[1].model_copy(update={"body": "門檻不同"}), slides[2]]}), FACTS))

    scenes = [Scene(kind="hook", heading="交換怎麼準備", lines=["三分鐘看懂"], seconds=3.0),
              Scene(kind="point", heading="先查語言", lines=["綜上所述要早點考"], seconds=20.0),
              Scene(kind="cta", heading="UniWay", lines=["app.uniway-tw.com"], seconds=7.0)]
    script = VideoScript(title="交換怎麼準備", scenes=scenes, caption="三分鐘看懂", hashtags=["#交換學生"], youtube_title="交換怎麼準備 #Shorts", youtube_description="app.uniway-tw.com")
    assert any("綜上所述" in i for i in check_video(script, FACTS, "short"))


def test_the_reviewer_sends_a_wordy_draft_back_once_and_then_leaves_it_for_the_boss(make_office):
    office = make_office()
    reviewer, author = office.staff["reviewer"], office.staff["threads"]
    item = PlanItem(channel="threads", format="text", pillar="value", angle="pain", topic="語言檢定", brief="language-test")
    briefing = Briefing(day=date(2026, 10, 23), facts=FACTS)
    draft = threads("在資訊爆炸的時代，讓我們一起搞定交換語言門檻。")
    kept, review, passed = reviewer.review("Threads 貼文", draft, item, briefing, lambda d: check_threads(d, FACTS), author=author)
    assert not passed and review["revisions"] == 1  # offline writers cannot rewrite, so it waits in the inbox with the reason
    assert any("口頭禪" in issue for issue in review["issues"])
    assert "像真人寫的" in reviewer.persona.duty or "AI 口頭禪" in reviewer.persona.duty
