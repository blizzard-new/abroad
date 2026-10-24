import json

import httpx

from office.telegram import TelegramBridge

CHAT = 4242


class FakeTelegram:
    """Answers the Bot API like Telegram would and remembers every call."""

    def __init__(self, updates=()):
        self.updates = list(updates)
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        method = request.url.path.rsplit("/", 1)[-1]
        if request.headers.get("content-type", "").startswith("application/json"):
            params = json.loads(request.content or b"{}")
        else:
            params = {"multipart": True}
        self.calls.append((method, params))
        if method == "getMe":
            return httpx.Response(200, json={"ok": True, "result": {"username": "uniway_office_bot"}})
        if method == "getUpdates":
            updates, self.updates = self.updates, []
            return httpx.Response(200, json={"ok": True, "result": updates})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": len(self.calls)}})

    def sent(self, method="sendMessage"):
        return [params for name, params in self.calls if name == method]


def bridge_for(office, fake):
    return TelegramBridge(office, http=httpx.Client(transport=httpx.MockTransport(fake)), spawn=lambda fn, *args: fn(*args))


def message(update_id, text, chat=CHAT):
    return {"update_id": update_id, "message": {"chat": {"id": chat}, "from": {"username": "boss"}, "text": text}}


def test_pairing_needs_the_code_from_office_auth(make_office):
    office = make_office(TELEGRAM_BOT_TOKEN="123:abc")
    fake = FakeTelegram()
    bridge = bridge_for(office, fake)
    code = bridge.new_pairing_code()
    fake.updates = [message(1, "/start wrong-code", chat=999), message(2, f"/start {code}")]
    bridge.poll_once(timeout=0)
    assert bridge.chat_id == str(CHAT) and not bridge.pairing_open(code)
    assert office.store.get("handle:telegram") == "boss"
    welcome = fake.sent()
    assert len(welcome) == 1 and welcome[0]["chat_id"] == str(CHAT) and "已連上" in welcome[0]["text"]


def test_messages_from_the_phone_reach_the_chief_and_the_answer_comes_back(make_office):
    office = make_office(TELEGRAM_BOT_TOKEN="123:abc")
    office.store.set("telegram_chat_id", str(CHAT))
    fake = FakeTelegram([message(1, "今天進度如何？"), message(2, "開工", chat=999)])
    bridge = bridge_for(office, fake)
    office.bus.listen(bridge.on_event)
    bridge.poll_once(timeout=0)
    bridge.flush()
    chat = office.store.chat()
    assert [m["sender"] for m in chat] == ["boss", "chief"]  # the stranger's 開工 never reached the chief
    assert chat[0]["text"] == "今天進度如何？"
    replies = fake.sent()
    assert replies and replies[-1]["text"] == chat[1]["text"]


def test_a_draft_waiting_for_approval_can_be_approved_from_the_phone(make_office, monkeypatch):
    office = make_office(TELEGRAM_BOT_TOKEN="123:abc", OFFICE_URL="http://office-pc:8780")
    office.store.set("telegram_chat_id", str(CHAT))
    fake = FakeTelegram()
    bridge = bridge_for(office, fake)
    office.bus.listen(bridge.on_event)
    draft_id = office.store.add_draft(
        run_id=None, day="2026-10-24", channel="threads", format="text", title="語言檢定怎麼選",
        payload={"text": "語言檢定還沒考的看這裡", "first_reply": "app.uniway-tw.com"}, status="pending_approval",
        scheduled_at="2099-01-01T04:30:00+00:00",
    )
    office.draft_changed(draft_id)
    office.draft_changed(draft_id)  # the same status again is not a second notification
    bridge.flush()
    notes = fake.sent()
    assert len(notes) == 1
    assert "等你核准 #%d" % draft_id in notes[0]["text"] and "語言檢定還沒考的看這裡" in notes[0]["text"]
    assert "http://office-pc:8780" in notes[0]["text"]
    assert notes[0]["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == f"approve:{draft_id}"

    fake.updates = [{"update_id": 5, "callback_query": {
        "id": "q1", "data": f"approve:{draft_id}", "message": {"message_id": 7, "chat": {"id": CHAT}}}}]
    bridge.poll_once(timeout=0)
    assert office.store.draft(draft_id)["status"] == "approved"
    assert fake.sent("answerCallbackQuery")[0]["text"].startswith("已核准")
    assert fake.sent("editMessageReplyMarkup")[0]["message_id"] == 7

    # Someone else pressing an old button does nothing.
    other = office.store.add_draft(run_id=None, day="2026-10-24", channel="threads", format="text", title="x",
                                   payload={"text": "x"}, status="pending_approval")
    fake.updates = [{"update_id": 6, "callback_query": {"id": "q2", "data": f"reject:{other}", "message": {"message_id": 8, "chat": {"id": 999}}}}]
    bridge.poll_once(timeout=0)
    assert office.store.draft(other)["status"] == "pending_approval"


def test_published_and_failed_posts_are_reported(make_office):
    office = make_office(TELEGRAM_BOT_TOKEN="123:abc")
    office.store.set("telegram_chat_id", str(CHAT))
    fake = FakeTelegram()
    bridge = bridge_for(office, fake)
    office.bus.listen(bridge.on_event)
    draft_id = office.store.add_draft(run_id=None, day="2026-10-24", channel="instagram", format="carousel", title="交換預算",
                                      payload={"caption_full": "預算怎麼抓"}, status="approved")
    office.store.update_draft(draft_id, status="published", remote_url="https://www.instagram.com/p/x", note="模擬發佈（沒有真的送出）")
    office.draft_changed(draft_id)
    office.store.update_draft(draft_id, status="failed", error="Instagram 容器失敗")
    office.draft_changed(draft_id)
    bridge.flush()
    texts = [m["text"] for m in fake.sent()]
    assert texts[0].startswith("🚀 已發出") and "模擬發佈" in texts[0]
    assert texts[1].startswith("❌ 發佈失敗") and "Instagram 容器失敗" in texts[1]


def test_nothing_is_sent_before_a_phone_is_paired(make_office):
    office = make_office(TELEGRAM_BOT_TOKEN="123:abc")
    fake = FakeTelegram([message(1, "開工")])
    bridge = bridge_for(office, fake)
    office.bus.listen(bridge.on_event)
    office.chat("chief", "早安")
    bridge.poll_once(timeout=0)
    bridge.flush()
    assert fake.sent() == [] and office.store.chat()[-1]["text"] == "早安"
