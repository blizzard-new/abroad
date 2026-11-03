"""Comment keyword -> private message (autodm.py and Momo's scan)."""

import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from office import autodm, checkup
from office.agents.community import Community
from office.config import Settings
from office.llm import briefing_text
from office.models import ChiefAction
from office.office import Office
from office.platforms.base import PlatformError
from office.platforms.meta import InstagramClient
from office.scheduler import tick

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
MESSAGE = "雅思閱讀教材在這裡 👉 https://uniway-tw.com/ielts-reading"


def office_in(tmp_path, name, **env):
    """An office of its own (the make_office fixture shares one folder, so two of them would share their rules)."""
    base = {"OFFICE_HOME": str(tmp_path / name), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0"}
    return Office(Settings.from_env(env={**base, **{k: str(v) for k, v in env.items()}}))


def stamp(when: datetime) -> str:
    return when.strftime("%Y-%m-%dT%H:%M:%S+0000")


def meta_error(code: int, text: str, status: int = 400, subcode: int = 0) -> PlatformError:
    body = {"error": {"message": text, "type": "OAuthException", "code": code, **({"error_subcode": subcode} if subcode else {})}}
    return PlatformError(f"Instagram POST https://graph.instagram.com/v24.0/1/messages 失敗 {status}：{json.dumps(body)}", status)


class FakeInstagram:
    """What Meta would do: the comments there are, the private replies it takes, the ones it refuses."""

    def __init__(self, comments=(), refuse=None):
        self.comments, self.refuse = list(comments), refuse
        self.reads, self.messages, self.public = 0, [], []

    def username(self):
        return "uniway.tw"

    def recent_comments(self, media_id, limit=50):
        self.reads += 1
        return list(self.comments)

    def private_reply(self, comment_id, text):
        if self.refuse:
            error = self.refuse(comment_id) if callable(self.refuse) else self.refuse
            if error:
                raise error
        self.messages.append((comment_id, text))
        return {"id": f"m{len(self.messages)}", "recipient": "u"}

    def reply_comment(self, comment_id, message):
        self.public.append((comment_id, message))
        return {"id": "r", "url": ""}


@pytest.fixture
def live(make_office):
    """An office that is really posting, with one published Instagram carousel (#1) and a rule for the keyword 雅思."""
    office = make_office(OFFICE_DRY_RUN=0)
    draft = office.store.add_draft(run_id=None, day="2026-11-02", channel="instagram", format="carousel", title="雅思怎麼準備", payload={}, status="approved")
    office.store.update_draft(draft, status="published", published_at=(NOW - timedelta(hours=3)).isoformat(timespec="seconds"), remote_id="1789")
    return office, draft


def attach(office, instagram):
    office.staff["publisher"].clients = lambda: {"instagram": instagram}
    return office.staff["community"]


def comment(number, text, *, who="student", minutes_ago=5):
    return {"id": f"c{number}", "text": text, "username": who, "timestamp": stamp(NOW - timedelta(minutes=minutes_ago))}


# ---- the boss's rules ----
def test_a_rule_keeps_the_boss_words_and_numbers_itself(make_office):
    office = make_office()
    first = autodm.add(office.store, keywords=["雅思", "閱讀"], message=MESSAGE, public_reply="已私訊你，記得查看訊息 👀", offer="領雅思閱讀教材", now=NOW)
    second = autodm.add(office.store, keywords=["寫作"], message="Task 2 拆題架構 👉 https://uniway-tw.com/task2", now=NOW)
    assert (first["id"], second["id"]) == (1, 2) and first["message"] == MESSAGE and first["created"].startswith("2026-11-02T12:00")
    assert autodm.describe(first).startswith("D1｜留言 「雅思」、「閱讀」｜所有 IG 貼文") and "已私訊 0 位" in autodm.describe(first)
    assert autodm.hooks(office.store) == ["留言「雅思」領雅思閱讀教材"]  # only a rule with an offer gives the writers something to invite people to
    assert autodm.remove(office.store, 1)["id"] == 1 and [r["id"] for r in autodm.rules(office.store)] == [2]
    with pytest.raises(ValueError, match="沒有編號 D9"):
        autodm.remove(office.store, 9)


@pytest.mark.parametrize("keywords, why", [
    ([], "要用哪個關鍵字"), (["雅"], "太短"), (["我要"], "太普通"), (["OK"], "太普通"), (["雅思", "雅 思"], None),
    (["a", "b", "c", "d", "e", "f"], "太短"), (["雅思一", "雅思二", "雅思三", "雅思四", "雅思五", "雅思六"], "最多 5 個"),
])
def test_keywords_must_be_precise_enough_not_to_message_people_who_asked_for_nothing(make_office, keywords, why):
    if why is None:  # the same word typed twice, with a space, is one keyword
        assert autodm.clean_keywords(keywords) == ["雅思"]
        return
    with pytest.raises(ValueError, match=why):
        autodm.clean_keywords(keywords)


def test_the_messages_are_checked_before_a_rule_exists(make_office):
    store = make_office().store
    for message, public, why in [
        ("", "", "空的"), ("字" * 400, "", "太長"), ("保證錄取的教材", "", "保證錄取"), ("看 http://example.com/x", "", "https"),
        (MESSAGE, "連結在 https://uniway-tw.com", "公開回覆裡不要放連結"), (MESSAGE, "回" * 101, "公開回覆太長"),
    ]:
        with pytest.raises(ValueError, match=why):
            autodm.add(store, keywords=["雅思"], message=message, public_reply=public)
    assert autodm.add(store, keywords=["雅思"], message="字" * 333)["id"] == 1  # 999 bytes: just fits
    assert autodm.rules(store)[0]["sent"] == 0


def test_the_same_keyword_is_one_rule_per_post_and_a_post_rule_beats_the_general_one(make_office):
    office = make_office()
    general = autodm.add(office.store, keywords=["雅思"], message=MESSAGE, now=NOW)
    with pytest.raises(ValueError, match="已經是 D1"):
        autodm.add(office.store, keywords=["雅思"], message="別的內容")
    draft = office.store.add_draft(run_id=None, day="2026-11-02", channel="instagram", format="reel", title="r", payload={}, status="published")
    special = autodm.add(office.store, keywords=["雅思"], message="這支 Reels 專用", draft_id=draft, now=NOW)
    elsewhere = [r for r in autodm.rules(office.store) if r["draft_id"] in (0, draft + 100)]
    assert autodm.match(elsewhere, "我想要 雅思 教材！")["id"] == general["id"]  # a comment under some other post
    assert autodm.match([r for r in autodm.rules(office.store) if r["draft_id"] in (0, draft)], "雅思")["id"] == special["id"]
    thread = office.store.add_draft(run_id=None, day="2026-11-02", channel="threads", format="text", title="t", payload={}, status="published")
    with pytest.raises(ValueError, match="不是 IG 輪播或 Reels"):
        autodm.add(office.store, keywords=["寫作"], message=MESSAGE, draft_id=thread)  # Threads has no private messages
    with pytest.raises(ValueError, match="不是 IG 輪播或 Reels"):
        autodm.add(office.store, keywords=["寫作"], message=MESSAGE, draft_id=999)


def test_matching_ignores_case_spacing_punctuation_and_full_width_letters():
    rule = {"id": 1, "draft_id": 0, "keywords": ["IELTS", "雅思閱讀"]}
    for text in ("ielts", "我要 ＩＥＬＴＳ！！", "雅思 閱讀 教材～", "雅思、閱讀"):
        assert autodm.match([rule], text), text
    assert autodm.match([rule], "請問托福") is None


def test_the_rules_hold_at_most_ten(make_office):
    store = make_office().store
    for number in range(autodm.MAX_RULES):
        autodm.add(store, keywords=[f"關鍵字{number}"], message=MESSAGE)
    with pytest.raises(ValueError, match="最多 10 條"):
        autodm.add(store, keywords=["再一條"], message=MESSAGE)


# ---- what Meta answers ----
@pytest.mark.parametrize("error, kind", [
    (meta_error(10, "(#10) Application does not have permission for this action"), "permission"),
    (meta_error(200, "(#200) Requires instagram_business_manage_messages permission"), "permission"),
    (meta_error(190, "Invalid OAuth access token."), "token"),
    (meta_error(4, "Application request limit reached", 400), "limit"),
    (PlatformError("Instagram POST x 失敗 429：slow down", 429), "limit"),
    (meta_error(100, "Object with ID '17' does not exist", subcode=33), "gone"),
    (meta_error(100, "This message is sent outside of allowed window.", subcode=2534022), "gone"),
    (meta_error(1, "An unknown error occurred", 500), "other"),
])
def test_metas_errors_are_told_apart(error, kind):
    assert autodm.classify(error) == kind


# ---- the Instagram calls ----
def test_a_private_reply_is_one_post_with_the_comment_as_the_recipient():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"recipient_id": "55", "message_id": "mid.1"})

    client = InstagramClient("9", "secret", dry_run=False, http=httpx.Client(transport=httpx.MockTransport(handler)))
    assert client.private_reply("c1", "哈囉") == {"id": "mid.1", "recipient": "55"}
    request = seen[0]
    assert request.method == "POST" and request.url.path == "/v24.0/9/messages" and request.url.params["access_token"] == "secret"
    assert json.loads(request.content) == {"recipient": {"comment_id": "c1"}, "message": {"text": "哈囉"}}
    assert client.calls[0]["params"]["access_token"] == "***"  # the log never holds the token


def test_recent_comments_ask_for_who_wrote_them_and_when():
    seen = []

    def handler(request):
        seen.append(request.url.params)
        return httpx.Response(200, json={"data": [{"id": "c1", "text": "雅思", "username": "a", "timestamp": "2026-11-02T11:55:00+0000"}, {"id": "c2"}]})

    client = InstagramClient("9", "secret", dry_run=False, http=httpx.Client(transport=httpx.MockTransport(handler)))
    assert [c["id"] for c in client.recent_comments("m1")] == ["c1"]  # a comment with no text is not a comment
    assert seen[0]["fields"] == "id,text,username,timestamp" and seen[0]["limit"] == "50"


def test_in_dry_run_nothing_leaves_the_machine():
    client = InstagramClient("9", "secret", dry_run=True)
    assert client.private_reply("c1", "哈囉")["id"].startswith("dry-") and client.calls[0]["json"]["recipient"] == {"comment_id": "c1"}


# ---- Momo's scan ----
def test_a_keyword_comment_gets_the_private_message_and_the_courtesy_reply_once(live):
    office, draft = live
    rule = autodm.add(office.store, keywords=["雅思"], message=MESSAGE, public_reply="已私訊你，記得查看訊息 👀", now=NOW - timedelta(hours=1))
    fake = FakeInstagram([comment(1, "我想要雅思教材！"), comment(2, "好實用"), comment(3, "雅思", who="uniway.tw")])
    momo = attach(office, fake)
    assert momo.auto_dm(NOW) == 1
    assert fake.messages == [("c1", MESSAGE)] and fake.public == [("c1", "已私訊你，記得查看訊息 👀")]
    assert autodm.rules(office.store)[0]["sent"] == 1 and autodm.sent_on(office.store, NOW.astimezone(office.settings.timezone).date()) == 1
    assert any("自動私訊了 1 位" in m["text"] and "D1" in m["text"] for m in office.store.chat())
    assert momo.auto_dm(NOW + timedelta(minutes=5)) == 0 and len(fake.messages) == 1  # the same comment is never answered twice
    assert autodm.handled(office.store, "c1") and not autodm.handled(office.store, "c2") and rule["id"] == 1


def test_only_comments_written_after_the_rule_are_answered_and_only_one_message_per_person(live):
    office, draft = live
    autodm.add(office.store, keywords=["雅思"], message=MESSAGE, now=NOW - timedelta(minutes=30))
    fake = FakeInstagram([
        comment(1, "雅思！", minutes_ago=120),  # before the rule existed: not a request for this
        comment(2, "雅思", who="amy", minutes_ago=20), comment(3, "雅思雅思雅思", who="amy", minutes_ago=10),  # amy asks twice
        comment(4, "雅思", who="ben", minutes_ago=5),
    ])
    assert attach(office, fake).auto_dm(NOW) == 2
    assert [m[0] for m in fake.messages] == ["c2", "c4"]
    assert office.store.get("dm:c3") == "same person" and office.store.get("dm:c1") is None


def test_a_comment_close_to_the_seven_day_limit_is_left_alone(live):
    office, draft = live
    autodm.add(office.store, keywords=["雅思"], message=MESSAGE, now=NOW - timedelta(days=8))
    fake = FakeInstagram([comment(1, "雅思", minutes_ago=int(6.8 * 24 * 60)), comment(2, "雅思", who="b", minutes_ago=60)])
    assert attach(office, fake).auto_dm(NOW) == 1 and fake.messages[0][0] == "c2"
    assert office.store.get("dm:c1") == "too old"


def test_a_rule_for_one_post_does_nothing_under_another(live):
    office, draft = live
    other = office.store.add_draft(run_id=None, day="2026-11-02", channel="instagram", format="reel", title="r", payload={}, status="published")
    autodm.add(office.store, keywords=["雅思"], message=MESSAGE, draft_id=other, now=NOW - timedelta(hours=1))
    fake = FakeInstagram([comment(1, "雅思")])
    assert attach(office, fake).auto_dm(NOW) == 0 and fake.reads == 0  # the post is not even read


def test_posts_are_read_often_when_new_and_rarely_when_old(live):
    office, draft = live
    autodm.add(office.store, keywords=["雅思"], message=MESSAGE, now=NOW - timedelta(days=1))
    fake = FakeInstagram([])
    momo = attach(office, fake)
    momo.auto_dm(NOW)
    momo.auto_dm(NOW + timedelta(minutes=1))
    assert fake.reads == 1  # a post only hours old is read every 2 minutes
    momo.auto_dm(NOW + timedelta(minutes=3))
    assert fake.reads == 2
    office.store.update_draft(draft, published_at=(NOW - timedelta(days=5)).isoformat(timespec="seconds"))
    momo.auto_dm(NOW + timedelta(minutes=10))  # a post of five days is read every half hour (the last read was at minute 3)
    momo.auto_dm(NOW + timedelta(minutes=20))
    assert fake.reads == 2
    momo.auto_dm(NOW + timedelta(minutes=45))
    assert fake.reads == 3


def test_when_meta_has_not_given_the_permission_the_office_stops_says_so_once_and_tries_again_later(live):
    office, draft = live
    autodm.add(office.store, keywords=["雅思"], message=MESSAGE, now=NOW - timedelta(hours=1))
    fake = FakeInstagram([comment(1, "雅思", who="a"), comment(2, "雅思", who="b")],
                         refuse=meta_error(10, "(#10) Application does not have permission for this action"))
    momo = attach(office, fake)
    assert momo.auto_dm(NOW) == 0
    warnings = [m["text"] for m in office.store.chat() if "自動私訊先暫停" in m["text"]]
    assert len(warnings) == 1 and "instagram_business_manage_messages" in warnings[0] and "應用程式審核" in warnings[0]
    assert not autodm.handled(office.store, "c1") and autodm.blocked(office.store, NOW + timedelta(minutes=5))
    assert momo.auto_dm(NOW + timedelta(minutes=5)) == 0 and fake.reads == 1  # paused: not even reading comments
    assert "暫停中" in office.staff["chief"].state_text() or "instagram_business_manage_messages" in office.staff["chief"].state_text()

    fake.refuse = None  # the boss fixed the permission
    assert momo.auto_dm(NOW + timedelta(minutes=31)) == 2  # the same two comments, still inside the seven days
    assert [m[0] for m in fake.messages] == ["c1", "c2"]


def test_a_comment_that_cannot_be_answered_is_skipped_but_the_rest_still_are(live):
    office, draft = live
    autodm.add(office.store, keywords=["雅思"], message=MESSAGE, now=NOW - timedelta(hours=1))
    gone = meta_error(100, "Object with ID '17' does not exist", subcode=33)
    fake = FakeInstagram([comment(1, "雅思", who="a", minutes_ago=30), comment(2, "雅思", who="b", minutes_ago=20)],
                         refuse=lambda cid: gone if cid == "c1" else None)
    assert attach(office, fake).auto_dm(NOW) == 1
    assert [m[0] for m in fake.messages] == ["c2"] and office.store.get("dm:c1").startswith("failed: gone")
    assert autodm.rules(office.store)[0]["failed"] == 1 and not autodm.blocked(office.store, NOW)


def test_five_failures_nobody_can_explain_pause_the_scan(live):
    office, draft = live
    autodm.add(office.store, keywords=["雅思"], message=MESSAGE, now=NOW - timedelta(hours=1))
    fake = FakeInstagram([comment(n, "雅思", who=f"u{n}", minutes_ago=60 - n) for n in range(1, 9)], refuse=meta_error(1, "An unknown error occurred", 500))
    assert attach(office, fake).auto_dm(NOW) == 0
    assert autodm.blocked(office.store, NOW) and sum(office.store.get(f"dm:c{n}") is not None for n in range(1, 9)) == 5  # it stopped after five


def test_the_daily_limit_stops_sending_until_tomorrow(make_office):
    office = make_office(OFFICE_DRY_RUN=0, OFFICE_AUTO_DM_LIMIT=2)
    draft = office.store.add_draft(run_id=None, day="2026-11-02", channel="instagram", format="reel", title="r", payload={}, status="approved")
    office.store.update_draft(draft, status="published", published_at=(NOW - timedelta(hours=3)).isoformat(timespec="seconds"), remote_id="1789")
    autodm.add(office.store, keywords=["雅思"], message=MESSAGE, now=NOW - timedelta(hours=1))
    fake = FakeInstagram([comment(n, "雅思", who=f"u{n}", minutes_ago=30 - n) for n in range(1, 5)])
    momo = attach(office, fake)
    assert momo.auto_dm(NOW) == 2 and len(fake.messages) == 2
    assert any("每日上限" in m["text"] for m in office.store.chat())
    assert momo.auto_dm(NOW + timedelta(hours=1)) == 0 and len(fake.messages) == 2
    tomorrow = (NOW + timedelta(days=1)).replace(hour=1)
    for n in range(1, 5):  # the other two comments are still inside the seven days
        fake.comments[n - 1]["timestamp"] = stamp(tomorrow - timedelta(minutes=30 - n))
    assert momo.auto_dm(tomorrow) == 2 and len(fake.messages) == 4


def test_the_switch_in_env_turns_it_off_and_the_clock_never_does_it_in_dry_run(tmp_path):
    off = office_in(tmp_path, "off", OFFICE_DRY_RUN=0, OFFICE_AUTO_DM=0)
    autodm.add(off.store, keywords=["雅思"], message=MESSAGE, now=NOW)
    assert off.staff["community"].auto_dm(NOW) == 0
    simulated = office_in(tmp_path, "simulated")
    autodm.add(simulated.store, keywords=["雅思"], message=MESSAGE, now=NOW)
    assert "dm" not in tick(simulated, NOW, background=False)  # simulation never reads or writes anything real


# ---- the boss talks to Leo ----
def test_leo_sets_up_and_removes_a_rule_and_the_writers_learn_what_to_invite(make_office):
    office = make_office()
    chief = office.staff["chief"]
    answer = chief.execute(ChiefAction(type="add_dm_rule", keywords=["雅思", "閱讀"], message=MESSAGE, public_reply="已私訊你 👀", offer="領雅思閱讀教材"))
    assert answer.startswith("設好了：D1｜留言 「雅思」、「閱讀」") and "模擬模式" in answer and "每人每天最多收一次" in answer and "領雅思閱讀教材" in answer
    text = chief.state_text()
    assert "IG 留言關鍵字自動私訊" in text and "D1｜留言" in text
    assert "留言「雅思」領雅思閱讀教材" in briefing_text(office.briefing_for_replies())
    assert chief.execute(ChiefAction(type="add_dm_rule", keywords=["我要"], message=MESSAGE)).startswith("沒辦法做：關鍵字「我要」太普通")
    assert chief.execute(ChiefAction(type="add_dm_rule", keywords=["寫作"], message="")).startswith("沒辦法做：私訊內容是空的")
    assert chief.execute(ChiefAction(type="remove_dm_rule", dm_id=1)).startswith("刪掉了：D1") and "（還沒有）" in chief.state_text()
    assert "留言「" not in briefing_text(office.briefing_for_replies())  # nothing to invite people to any more


# ---- office check ----
def check_row(tmp_path, name, transport, with_rule=False):
    office = office_in(tmp_path, name)
    if with_rule:
        autodm.add(office.store, keywords=["雅思"], message=MESSAGE)
    office.store.set("instagram_user_id", "9")
    office.store.set("instagram_token", "secret")
    return checkup.dm_rows(office.settings, office.store, httpx.Client(transport=httpx.MockTransport(transport)))[0]


def test_office_check_says_whether_meta_lets_the_account_message(tmp_path):
    ok = check_row(tmp_path, "a", lambda r: httpx.Response(200, json={"data": []}))
    assert ok.ok is True and "還沒有規則" in ok.detail and "模擬模式" in ok.detail
    refused = lambda r: httpx.Response(400, json={"error": {"message": "(#10) Application does not have permission for this action", "code": 10}})
    none_yet = check_row(tmp_path, "b", refused)
    assert none_yet.ok is None and "instagram_business_manage_messages" in none_yet.detail
    broken = check_row(tmp_path, "c", refused, with_rule=True)
    assert broken.ok is False and "已經設了 1 條規則，現在傳不出去" in broken.detail
    office = office_in(tmp_path, "d")
    assert checkup.dm_rows(office.settings, office.store)[0].ok is None  # Instagram is not connected yet
